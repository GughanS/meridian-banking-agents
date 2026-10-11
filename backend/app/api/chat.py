import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.auth import get_current_customer_id
from app.db.models import ChatSession
from app.db.session import get_session
from app.graph.workflow import get_compiled_graph

router = APIRouter()
# We define a global limiter in main but use it here if needed

class ChatRequest(BaseModel):
    session_id: UUID
    message: str

@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest, 
    customer_id: UUID = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_session)
):
    chat_session = await db.get(ChatSession, req.session_id)
    if not chat_session:
        chat_session = ChatSession(id=req.session_id, customer_id=customer_id)
        db.add(chat_session)
        await db.commit()
    elif chat_session.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Unauthorized session")

    async def event_generator():
        try:
            graph = await get_compiled_graph()
            config = {"configurable": {"thread_id": str(req.session_id)}}
            state = {
                "messages": [{"role": "user", "content": req.message}],
                "customer_id": customer_id,
                "session_id": req.session_id
            }
            
            # Use stream mode to yield updates as they happen
            async for output in graph.astream(state, config=config, stream_mode="updates"):
                for node_name, updates in output.items():
                    if "messages" in updates:
                        for msg in updates["messages"]:
                            if msg["role"] == "model" and msg.get("content"):
                                yield {"data": json.dumps({"type": "message", "node": node_name, "content": msg["content"]})}
                            elif msg["role"] == "model" and msg.get("function_call"):
                                yield {"data": json.dumps({"type": "tool_call", "name": msg["function_call"]["name"]})}
                            elif msg["role"] == "tool" and msg.get("content"):
                                yield {"data": json.dumps({"type": "tool_response", "name": msg.get("tool_name"), "content": msg["content"]})}
            
            yield {"data": json.dumps({"type": "done"})}
        except Exception as e:
            yield {"data": json.dumps({"type": "error", "message": str(e)})}
            yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_generator())

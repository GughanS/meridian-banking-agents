import asyncio
import json
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.api.auth import get_current_customer_id
from app.events.bus import event_bus

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/stream/events")
async def system_events_stream(
    request: Request,
    customer_id: UUID = Depends(get_current_customer_id)
):
    async def event_publisher():
        queue = asyncio.Queue()
        topic = f"alert.{customer_id}"
        
        async def handler(payload):
            await queue.put(payload)
            
        event_bus.subscribe(topic, handler)
        
        # Ping task
        async def ping():
            while True:
                await asyncio.sleep(15)
                await queue.put({"type": "ping"})
                
        ping_task = asyncio.create_task(ping())
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                payload = await queue.get()
                yield {"data": json.dumps(payload)}
        finally:
            ping_task.cancel()

    return EventSourceResponse(event_publisher())

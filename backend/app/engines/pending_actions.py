from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, PendingAction


async def create_pending_action(db: AsyncSession, session_id: UUID | str, tool_name: str, payload: dict[str, Any], expiry_mins: int = 5) -> PendingAction:
    sid = UUID(str(session_id)) if not isinstance(session_id, UUID) else session_id
    
    chat_session = await db.get(ChatSession, sid)
    if not chat_session:
        from uuid import uuid4
        chat_session = ChatSession(id=sid, customer_id=uuid4())
        db.add(chat_session)
        await db.commit()

    action = PendingAction(
        session_id=sid,
        tool_name=tool_name,
        payload=payload,
        expires_at=datetime.now(UTC) + timedelta(minutes=expiry_mins),
        status="pending"
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return action

async def confirm_action(db: AsyncSession, action_id: UUID, customer_id: UUID) -> PendingAction:
    action = await db.get(PendingAction, action_id)
    if not action:
        raise ValueError("PendingAction not found")
        
    # Enforce Object-level authorization
    chat_session = await db.get(ChatSession, action.session_id)
    if not chat_session or chat_session.customer_id != customer_id:
        raise ValueError("Unauthorized to confirm this action")
    
    if action.status != "pending":
        raise ValueError(f"Action already in status {action.status}")
        
    if action.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        action.status = "expired"
        await db.commit()
        raise ValueError("Action expired")
        
    action.status = "confirmed"
    await db.commit()
    return action

async def cancel_action(db: AsyncSession, action_id: UUID, customer_id: UUID) -> PendingAction:
    action = await db.get(PendingAction, action_id)
    if not action:
        raise ValueError("PendingAction not found")
        
    chat_session = await db.get(ChatSession, action.session_id)
    if not chat_session or chat_session.customer_id != customer_id:
        raise ValueError("Unauthorized to cancel this action")
        
    if action.status == "cancelled":
        return action
        
    if action.status != "pending":
        raise ValueError(f"Action already in status {action.status}")
        
    action.status = "cancelled"
    await db.commit()
    return action

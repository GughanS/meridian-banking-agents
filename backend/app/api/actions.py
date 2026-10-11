from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_customer_id
from app.db.session import get_session
from app.engines.pending_actions import cancel_action, confirm_action

router = APIRouter()

@router.post("/actions/{action_id}/confirm")
async def api_confirm_action(
    action_id: UUID,
    customer_id: UUID = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_session)
):
    try:
        action = await confirm_action(db, action_id, customer_id)
        # using model_dump but converting datetime explicitly if needed
        data = action.model_dump()
        data["expires_at"] = data["expires_at"].isoformat()
        return {"status": "success", "action": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.post("/actions/{action_id}/cancel")
async def api_cancel_action(
    action_id: UUID,
    customer_id: UUID = Depends(get_current_customer_id),
    db: AsyncSession = Depends(get_session)
):
    try:
        action = await cancel_action(db, action_id, customer_id)
        data = action.model_dump()
        data["expires_at"] = data["expires_at"].isoformat()
        return {"status": "success", "action": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

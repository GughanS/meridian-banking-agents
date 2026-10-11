from uuid import UUID

from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import Dispute, FraudAlert
from app.engines.pending_actions import create_pending_action
from app.llm.registry import ToolContext, registry


class EmptyArgs(BaseModel):
    pass

@registry.register(
    name="get_fraud_alerts",
    description="Retrieve fraud alerts for the customer.",
    schema=EmptyArgs
)
async def get_fraud_alerts(ctx: ToolContext, **kwargs) -> list:
    statement = select(FraudAlert).where(FraudAlert.customer_id == ctx.customer_id)
    res = await ctx.db.exec(statement)
    return [a.model_dump() for a in res.all()]

@registry.register(
    name="get_disputes",
    description="Retrieve transaction disputes for the customer.",
    schema=EmptyArgs
)
async def get_disputes(ctx: ToolContext, **kwargs) -> list:
    statement = select(Dispute).where(Dispute.customer_id == ctx.customer_id)
    res = await ctx.db.exec(statement)
    return [d.model_dump() for d in res.all()]

class ProposeDisputeArgs(BaseModel):
    transaction_id: UUID = Field(..., description="The ID of the transaction to dispute")
    reason: str = Field(..., description="Reason for the dispute")

@registry.register(
    name="propose_dispute",
    description="Propose a dispute for a specific transaction. Must be confirmed by user.",
    schema=ProposeDisputeArgs
)
async def propose_dispute(ctx: ToolContext, transaction_id: UUID, reason: str) -> dict:
    payload = {"transaction_id": str(transaction_id), "reason": reason}
    action = await create_pending_action(ctx.db, ctx.session_id, "propose_dispute", payload)
    return {
        "message": f"A proposal to dispute transaction {transaction_id} has been created and awaits confirmation.",
        "action_id": str(action.id)
    }

class EscalateFraudArgs(BaseModel):
    alert_id: UUID = Field(..., description="The ID of the fraud alert to escalate")
    notes: str = Field(..., description="Additional notes for escalation")

@registry.register(
    name="escalate_fraud",
    description="Propose escalating a fraud alert to human analysts. Must be confirmed by user.",
    schema=EscalateFraudArgs
)
async def escalate_fraud(ctx: ToolContext, alert_id: UUID, notes: str) -> dict:
    payload = {"alert_id": str(alert_id), "notes": notes}
    action = await create_pending_action(ctx.db, ctx.session_id, "escalate_fraud", payload)
    return {
        "message": f"A proposal to escalate fraud alert {alert_id} has been created and awaits confirmation.",
        "action_id": str(action.id)
    }

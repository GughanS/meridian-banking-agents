from uuid import UUID

from pydantic import BaseModel, Field

from app.core_banking.client import CoreBankingClient
from app.engines.pending_actions import create_pending_action
from app.llm.registry import ToolContext, registry


class EmptyArgs(BaseModel):
    pass

@registry.register(
    name="get_customer_profile",
    description="Retrieve the customer's personal profile information.",
    schema=EmptyArgs
)
async def get_customer_profile(ctx: ToolContext, **kwargs) -> dict:
    client = CoreBankingClient()
    return await client.get_customer(ctx.customer_id)

@registry.register(
    name="get_accounts",
    description="Retrieve the customer's bank accounts and current balances.",
    schema=EmptyArgs
)
async def get_accounts(ctx: ToolContext, **kwargs) -> list:
    client = CoreBankingClient()
    return await client.get_accounts(ctx.customer_id)

class GetTransactionsArgs(BaseModel):
    account_id: UUID = Field(..., description="The ID of the account")
    limit: int = Field(50, description="Number of transactions to fetch")

@registry.register(
    name="get_transactions",
    description="Retrieve transaction history for a specific account.",
    schema=GetTransactionsArgs
)
async def get_transactions(ctx: ToolContext, account_id: UUID, limit: int) -> list:
    client = CoreBankingClient()
    accounts = await client.get_accounts(ctx.customer_id)
    if str(account_id) not in [str(a["id"]) for a in accounts]:
        raise ValueError("Unauthorized: Account does not belong to the current customer.")
    return await client.get_transactions(account_id, limit)

@registry.register(
    name="get_cards",
    description="Retrieve the customer's debit and credit cards.",
    schema=EmptyArgs
)
async def get_cards(ctx: ToolContext, **kwargs) -> list:
    client = CoreBankingClient()
    return await client.get_cards(ctx.customer_id)

class ProposeCardBlockArgs(BaseModel):
    card_id: UUID = Field(..., description="The ID of the card to block")
    reason: str = Field(..., description="Reason for blocking")

@registry.register(
    name="propose_card_block",
    description="Proposes blocking a customer's debit or credit card. Must be confirmed by the user.",
    schema=ProposeCardBlockArgs
)
async def propose_card_block(ctx: ToolContext, card_id: UUID, reason: str) -> dict:
    client = CoreBankingClient()
    cards = await client.get_cards(ctx.customer_id)
    if str(card_id) not in [str(c["id"]) for c in cards]:
        raise ValueError("Unauthorized: Card does not belong to the current customer.")
        
    payload = {"card_id": str(card_id), "action": "block", "reason": reason}
    action = await create_pending_action(ctx.db, ctx.session_id, "propose_card_block", payload)
    
    return {
        "message": f"A proposal to block card {card_id} has been created and awaits user confirmation.",
        "action_id": str(action.id)
    }

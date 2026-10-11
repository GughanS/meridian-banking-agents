from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core_banking.client import CoreBankingClient
from app.engines.pending_actions import create_pending_action
from app.llm.registry import ToolContext, registry


def _unwrap_data(val: Any) -> Any:
    if isinstance(val, dict) and "data" in val:
        return val["data"]
    return val

class EmptyArgs(BaseModel):
    pass

@registry.register(
    name="get_customer_profile",
    description="Retrieve the customer's personal profile information.",
    schema=EmptyArgs
)
async def get_customer_profile(ctx: ToolContext, **kwargs: Any) -> Any:
    client = CoreBankingClient()
    res = await client.get_customer(str(ctx.customer_id))
    return _unwrap_data(res)

@registry.register(
    name="get_accounts",
    description="Retrieve the customer's bank accounts and current balances.",
    schema=EmptyArgs
)
async def get_accounts(ctx: ToolContext, **kwargs: Any) -> Any:
    client = CoreBankingClient()
    res = await client.get_accounts(str(ctx.customer_id))
    return _unwrap_data(res)

class GetTransactionsArgs(BaseModel):
    account_id: UUID = Field(..., description="The ID of the account")
    limit: int = Field(50, description="Number of transactions to fetch")

@registry.register(
    name="get_transactions",
    description="Retrieve transaction history for a specific account.",
    schema=GetTransactionsArgs
)
async def get_transactions(ctx: ToolContext, account_id: UUID, limit: int) -> Any:
    client = CoreBankingClient()
    accounts_res = await client.get_accounts(str(ctx.customer_id))
    accounts_data = _unwrap_data(accounts_res)
    accounts = accounts_data if isinstance(accounts_data, list) else []
    
    valid_ids = [str(a.get("id") if isinstance(a, dict) else getattr(a, "id", a)) for a in accounts]
    if str(account_id) not in valid_ids:
        raise ValueError("Unauthorized: Account does not belong to the current customer.")
    tx_res = await client.get_transactions(str(account_id), {"limit": limit})
    return _unwrap_data(tx_res)

@registry.register(
    name="get_cards",
    description="Retrieve the customer's debit and credit cards.",
    schema=EmptyArgs
)
async def get_cards(ctx: ToolContext, **kwargs: Any) -> Any:
    client = CoreBankingClient()
    res = await client.get_cards(str(ctx.customer_id))
    return _unwrap_data(res)

class ProposeCardBlockArgs(BaseModel):
    card_id: UUID = Field(..., description="The ID of the card to block")
    reason: str = Field(..., description="Reason for blocking")

@registry.register(
    name="propose_card_block",
    description="Proposes blocking a customer's debit or credit card. Must be confirmed by the user.",
    schema=ProposeCardBlockArgs
)
async def propose_card_block(ctx: ToolContext, card_id: UUID, reason: str) -> dict[str, Any]:
    client = CoreBankingClient()
    cards_res = await client.get_cards(str(ctx.customer_id))
    cards_data = _unwrap_data(cards_res)
    cards = cards_data if isinstance(cards_data, list) else []
    
    valid_card_ids = [str(c.get("id") if isinstance(c, dict) else getattr(c, "id", c)) for c in cards]
    if str(card_id) not in valid_card_ids:
        raise ValueError("Unauthorized: Card does not belong to the current customer.")
        
    payload = {"card_id": str(card_id), "action": "block", "reason": reason}
    action = await create_pending_action(ctx.db, ctx.session_id, "propose_card_block", payload)
    
    return {
        "message": f"A proposal to block card {card_id} has been created and awaits user confirmation.",
        "action_id": str(action.id)
    }

from decimal import Decimal

from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import CreditProfile, LoanProduct
from app.engines.eligibility import evaluate_loan_eligibility
from app.engines.emi import calculate_emi
from app.engines.pending_actions import create_pending_action
from app.llm.registry import ToolContext, registry


class EmptyArgs(BaseModel):
    pass

@registry.register(
    name="get_credit_profile",
    description="Retrieves the customer's credit profile (score, income, obligations).",
    schema=EmptyArgs
)
async def get_credit_profile(ctx: ToolContext, **kwargs) -> dict:
    statement = select(CreditProfile).where(CreditProfile.customer_id == ctx.customer_id)
    res = await ctx.db.exec(statement)
    profile = res.first()
    if not profile:
        raise ValueError("Credit profile not found")
    return profile.model_dump()

@registry.register(
    name="get_loan_products",
    description="Retrieves available loan products from the bank.",
    schema=EmptyArgs
)
async def get_loan_products(ctx: ToolContext, **kwargs) -> list:
    statement = select(LoanProduct)
    res = await ctx.db.exec(statement)
    return [p.model_dump() for p in res.all()]

class CalculateLoanOptionsArgs(BaseModel):
    product_id: str = Field(..., description="The ID of the loan product")
    amount: float = Field(..., description="The requested loan amount")
    tenure_months: int = Field(..., description="The requested tenure in months")

@registry.register(
    name="calculate_loan_options",
    description="Calculates eligibility and EMI for a loan amount and tenure.",
    schema=CalculateLoanOptionsArgs
)
async def calculate_loan_options(ctx: ToolContext, product_id: str, amount: float, tenure_months: int) -> dict:
    statement = select(CreditProfile).where(CreditProfile.customer_id == ctx.customer_id)
    profile = (await ctx.db.exec(statement)).first()
    
    prod_stmt = select(LoanProduct).where(LoanProduct.id == product_id)
    product = (await ctx.db.exec(prod_stmt)).first()
    
    if not profile or not product:
        raise ValueError("Profile or product not found")
        
    eligibility = evaluate_loan_eligibility(profile, product, Decimal(str(amount)), tenure_months)
    
    if not eligibility.eligible:
        return {
            "eligible": False,
            "reasons": eligibility.reason_codes,
            "max_amount": float(eligibility.max_amount)
        }
        
    emi_details = calculate_emi(Decimal(str(amount)), eligibility.offered_rate, tenure_months)
    
    return {
        "eligible": True,
        "max_amount": float(eligibility.max_amount),
        "offered_rate": float(eligibility.offered_rate),
        "emi_details": {k: float(v) for k, v in emi_details.items()}
    }

class ProposeLoanApplicationArgs(BaseModel):
    product_id: str = Field(..., description="The ID of the loan product")
    amount: float = Field(..., description="The approved amount")
    tenure_months: int = Field(..., description="The tenure in months")
    rate: float = Field(..., description="The offered annual rate")

@registry.register(
    name="propose_loan_application",
    description="Proposes a loan application. Must be confirmed by user.",
    schema=ProposeLoanApplicationArgs
)
async def propose_loan_application(ctx: ToolContext, product_id: str, amount: float, tenure_months: int, rate: float) -> dict:
    payload = {
        "product_id": product_id,
        "amount": amount,
        "tenure_months": tenure_months,
        "rate": rate
    }
    action = await create_pending_action(ctx.db, ctx.session_id, "propose_loan_application", payload)
    return {
        "message": f"A proposal for a loan of {amount} has been created and awaits confirmation.",
        "action_id": str(action.id)
    }

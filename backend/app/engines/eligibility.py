from decimal import Decimal

from app.db.models import CreditProfile, LoanProduct


class EligibilityResult:
    def __init__(self, eligible: bool, max_amount: Decimal, reason_codes: list[str], offered_rate: Decimal | None = None):
        self.eligible = eligible
        self.max_amount = max_amount
        self.reason_codes = reason_codes
        self.offered_rate = offered_rate

def evaluate_loan_eligibility(
    profile: CreditProfile, 
    product: LoanProduct, 
    requested_amount: Decimal, 
    requested_tenure: int
) -> EligibilityResult:
    reasons = []
    eligible = True
    
    if profile.score < product.min_score:
        eligible = False
        reasons.append(f"Credit score {profile.score} below minimum {product.min_score}")
        
    if requested_tenure < product.min_tenure_months or requested_tenure > product.max_tenure_months:
        eligible = False
        reasons.append(f"Tenure {requested_tenure} outside allowed range {product.min_tenure_months}-{product.max_tenure_months}")
        
    if requested_amount > product.max_amount:
        eligible = False
        reasons.append(f"Amount {requested_amount} exceeds product maximum {product.max_amount}")
        
    max_by_income = profile.monthly_income * product.max_income_multiple
    if requested_amount > max_by_income:
        eligible = False
        reasons.append(f"Amount {requested_amount} exceeds income multiple limit {max_by_income}")
        
    if profile.monthly_income > 0:
        dti = profile.monthly_obligations / profile.monthly_income
        if dti > Decimal("0.60"):
            eligible = False
            reasons.append(f"Debt-to-income ratio {dti:.2f} exceeds 0.60 limit")

    if profile.recent_delinquency_dpd > 30:
        eligible = False
        reasons.append(f"Recent delinquency of {profile.recent_delinquency_dpd} days")
        
    max_amount = min(product.max_amount, max_by_income)
    
    offered_rate = None
    if eligible:
        rate_bump = Decimal(0)
        if profile.score < 700:
            rate_bump = Decimal("1.5")
        elif profile.score < 750:
            rate_bump = Decimal("0.5")
        offered_rate = product.base_rate + rate_bump

    return EligibilityResult(
        eligible=eligible,
        max_amount=max_amount,
        reason_codes=reasons,
        offered_rate=offered_rate
    )

from decimal import ROUND_HALF_UP, Decimal


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> dict[str, Decimal]:
    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than 0")
    if principal <= 0:
        raise ValueError("Principal must be greater than 0")
        
    if annual_rate == 0:
        emi = (principal / tenure_months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_payment = principal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_interest = Decimal("0.00")
    else:
        r = annual_rate / 12 / 100
        n = tenure_months
        factor = (1 + r) ** n
        raw_emi = principal * r * factor / (factor - 1)
        emi = raw_emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_payment = (emi * n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_interest = (total_payment - principal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "emi": emi,
        "total_payment": total_payment,
        "total_interest": total_interest,
    }

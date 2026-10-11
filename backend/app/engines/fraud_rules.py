from decimal import Decimal


def evaluate_fraud_rules(
    tx_amount: Decimal,
    tx_country: str,
    tx_mcc: str,
    velocity_24h_same_merchant: int,
    is_card_present: bool = False
) -> tuple[int, str, list[str]]:
    """
    Returns (score: 0-100, level: LOW/MEDIUM/HIGH, rules_triggered)
    """
    score = 0
    rules = []
    
    if tx_country != "IN" and not is_card_present:
        score += 40
        rules.append("FOREIGN_CNP")
        
    if tx_mcc in ["6051", "7995"]: # Quasi Cash, Gambling
        score += 50
        rules.append("HIGH_RISK_MCC")
        
    if velocity_24h_same_merchant >= 3:
        score += 30
        rules.append("VELOCITY_BURST")
        
    if tx_amount > Decimal(50000):
        score += 20
        rules.append("HIGH_AMOUNT")
        
    score = min(score, 100)
    
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    return score, level, rules

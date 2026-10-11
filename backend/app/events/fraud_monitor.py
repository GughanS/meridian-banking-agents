from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.db.models import FraudAlert
from app.db.session import SessionLocal
from app.engines.fraud_rules import evaluate_fraud_rules
from app.events.bus import event_bus

logger = structlog.get_logger(__name__)


async def on_transaction_created(payload: Any) -> None:
    tx_data = payload.get("transaction")
    customer_id = payload.get("customer_id")
    if not tx_data or not customer_id:
        return

    amount = Decimal(str(tx_data.get("amount", "0")))
    country = str(tx_data.get("country", "IN"))
    mcc = str(tx_data.get("mcc", "0000"))
    merchant = str(tx_data.get("merchant", "Unknown Merchant"))
    tx_id_raw = tx_data.get("id")
    tx_id = UUID(str(tx_id_raw)) if tx_id_raw else uuid4()
    cust_id = UUID(str(customer_id))

    score, level, rules = evaluate_fraud_rules(
        tx_amount=amount,
        tx_country=country,
        tx_mcc=mcc,
        velocity_24h_same_merchant=1,
        is_card_present=False,
    )

    if payload.get("is_anomaly") or level in ["HIGH", "MEDIUM"]:
        final_score = 95 if payload.get("is_anomaly") else score
        final_level = "HIGH" if payload.get("is_anomaly") else level
        final_rules = ["ANOMALY_OVERSEAS_SPIKE"] if payload.get("is_anomaly") else rules

        logger.warning(
            "Fraudulent transaction detected!",
            transaction_id=str(tx_id),
            score=final_score,
            level=final_level,
        )

        async with SessionLocal() as db:
            alert = FraudAlert(
                id=uuid4(),
                transaction_id=tx_id,
                customer_id=cust_id,
                score=final_score,
                level=final_level,
                rules_triggered=final_rules,
                created_at=datetime.now(UTC),
                status="open",
            )
            db.add(alert)
            await db.commit()

            await event_bus.publish(
                f"alert.{customer_id}",
                {
                    "type": "FRAUD_ALERT",
                    "id": str(alert.id),
                    "customer_id": str(customer_id),
                    "score": alert.score,
                    "level": alert.level,
                    "title": "Suspicious Transaction Alert",
                    "message": f"Detected suspicious charge of INR {amount} at {merchant}",
                    "rules": alert.rules_triggered,
                },
            )


def setup_fraud_monitor() -> None:
    event_bus.subscribe("transaction.created", on_transaction_created)
    logger.info("Fraud monitor subscribed to events")

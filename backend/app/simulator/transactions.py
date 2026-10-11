import asyncio
import random
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import structlog
from sqlmodel import select

from app.db.models import Account, Customer, Transaction
from app.db.session import SessionLocal
from app.events.bus import event_bus

logger = structlog.get_logger(__name__)

class TransactionSimulator:
    def __init__(self):
        self._task = None

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._run())
            logger.info("Transaction Simulator started")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Transaction Simulator stopped")

    async def inject_anomaly(self) -> None:
        """Used for UC8: injects a large fraudulent transaction"""
        async with SessionLocal() as db:
            result = await db.execute(select(Account).limit(1))
            account = result.scalar_one_or_none()
            if not account:
                return

            tx = Transaction(
                id=uuid.uuid4(),
                account_id=account.id,
                amount=Decimal("75000.00"),
                merchant="UNKNOWN_FOREIGN_MERCHANT",
                category="shopping",
                tx_type="debit",
                country="US",
                mcc="6051",
                timestamp=datetime.now(UTC)
            )
            db.add(tx)
            
            account.balance -= tx.amount
            db.add(account)
            await db.commit()

            cust = await db.get(Customer, account.customer_id)
            
            await event_bus.publish("transaction.created", {
                "transaction": tx.model_dump(),
                "customer_id": cust.id if cust else account.customer_id,
                "is_anomaly": True
            })
            logger.info("Injected anomaly transaction", transaction_id=str(tx.id))

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(random.randint(20, 60))
            try:
                async with SessionLocal() as db:
                    result = await db.execute(select(Account).order_by(Account.id))
                    accounts = result.scalars().all()
                    if not accounts:
                        continue
                    account = random.choice(accounts)
                    
                    amount_val = Decimal(str(round(random.uniform(500.0, 3000.0), 2)))
                    tx = Transaction(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        amount=amount_val,
                        merchant=random.choice(["Coffee House", "Supermart", "Cloud Service", "Metro Transit"]),
                        category="dining",
                        tx_type="debit",
                        country="IN",
                        mcc="5812",
                        timestamp=datetime.now(UTC)
                    )
                    db.add(tx)
                    account.balance -= tx.amount
                    db.add(account)
                    await db.commit()
                    
                    cust = await db.get(Customer, account.customer_id)
                    
                    await event_bus.publish("transaction.created", {
                        "transaction": tx.model_dump(),
                        "customer_id": cust.id if cust else account.customer_id,
                        "is_anomaly": False
                    })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Simulator error", error=str(e))

simulator = TransactionSimulator()

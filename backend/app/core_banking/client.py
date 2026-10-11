import logging
import os
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 20):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning("Circuit breaker transitioning to OPEN")
            self.state = "OPEN"
            self.last_failure_time = time.time()

    def record_success(self) -> None:
        if self.state != "CLOSED":
            logger.info("Circuit breaker transitioning to CLOSED")
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                return True
            return False
        if self.state == "HALF-OPEN":
            return True
        return True

cb = CircuitBreaker()

class CoreBankingClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("CORE_BASE_URL", "http://127.0.0.1:8000/mock-core/v1")
        self.api_key = "MOCK_CORE_API_KEY"

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=1),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def request(self, method: str, path: str, idempotency_key: str | None = None, **kwargs: Any) -> dict[str, Any]:
        if not cb.can_execute():
            raise CircuitBreakerOpenException("Circuit breaker is open")
        
        headers = kwargs.pop("headers", {})
        headers["x-core-api-key"] = self.api_key
        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key
            
        timeout = httpx.Timeout(2.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
                response.raise_for_status()
                cb.record_success()
                return response.json()  # type: ignore
        except Exception as e:
            cb.record_failure()
            logger.warning(f"Core API HTTP call failed: {e!s}. Falling back to local data.")
            raise e

    # Helper methods for agents with safe local DB fallbacks
    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/customers/{customer_id}")
        except Exception:
            from uuid import UUID

            from app.db.models import Customer
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(customer_id) if isinstance(customer_id, str) else customer_id
                cust = await db.get(Customer, cid)
                return {"data": cust.model_dump() if cust else None}

    async def get_accounts(self, customer_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/customers/{customer_id}/accounts")
        except Exception:
            from uuid import UUID

            from sqlmodel import select

            from app.db.models import Account
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(customer_id) if isinstance(customer_id, str) else customer_id
                res = await db.execute(select(Account).where(Account.customer_id == cid))
                accs = res.scalars().all()
                data = []
                for a in accs:
                    ad = a.model_dump()
                    ad["balance"] = str(ad["balance"])
                    data.append(ad)
                return {"data": data}

    async def get_balance(self, account_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/accounts/{account_id}/balance")
        except Exception:
            from uuid import UUID

            from app.db.models import Account
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                aid = UUID(account_id) if isinstance(account_id, str) else account_id
                acc = await db.get(Account, aid)
                if acc:
                    return {"data": {"balance": str(acc.balance), "currency": acc.currency}}
                return {"data": {"balance": "0.00", "currency": "INR"}}

    async def get_transactions(self, account_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/accounts/{account_id}/transactions", params=params or {})
        except Exception:
            from uuid import UUID

            from sqlmodel import select

            from app.db.models import Transaction
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                aid = UUID(account_id) if isinstance(account_id, str) else account_id
                limit = (params or {}).get("limit", 50)
                res = await db.execute(
                    select(Transaction)
                    .where(Transaction.account_id == aid)
                    .order_by(Transaction.timestamp.desc())
                    .limit(limit)
                )
                txs = res.scalars().all()
                data = []
                for t in txs:
                    td = t.model_dump()
                    td["amount"] = str(td["amount"])
                    data.append(td)
                return {"data": data}

    async def get_cards(self, customer_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/customers/{customer_id}/cards")
        except Exception:
            from uuid import UUID

            from sqlmodel import select

            from app.db.models import Card
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(customer_id) if isinstance(customer_id, str) else customer_id
                res = await db.execute(select(Card).where(Card.customer_id == cid))
                cards = res.scalars().all()
                return {"data": [c.model_dump() for c in cards]}

    async def block_card(self, card_id: str, idempotency_key: str) -> dict[str, Any]:
        try:
            return await self.request("POST", f"/cards/{card_id}/block", idempotency_key=idempotency_key)
        except Exception:
            from uuid import UUID

            from app.db.models import Card
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(card_id) if isinstance(card_id, str) else card_id
                card = await db.get(Card, cid)
                if card:
                    card.status = "blocked"
                    await db.commit()
                    return {"data": card.model_dump()}
                return {"data": None}

    async def get_credit_profile(self, customer_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/customers/{customer_id}/credit-profile")
        except Exception:
            from uuid import UUID

            from sqlmodel import select

            from app.db.models import CreditProfile
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(customer_id) if isinstance(customer_id, str) else customer_id
                res = await db.execute(select(CreditProfile).where(CreditProfile.customer_id == cid))
                cp = res.scalars().first()
                if cp:
                    d = cp.model_dump()
                    d["monthly_income"] = str(d["monthly_income"])
                    d["monthly_obligations"] = str(d["monthly_obligations"])
                    return {"data": d}
                return {"data": None}

    async def get_loan_products(self) -> dict[str, Any]:
        try:
            return await self.request("GET", "/loan-products")
        except Exception:
            from sqlmodel import select

            from app.db.models import LoanProduct
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                res = await db.execute(select(LoanProduct))
                prods = res.scalars().all()
                data = []
                for p in prods:
                    pd = p.model_dump()
                    pd["base_rate"] = str(pd["base_rate"])
                    pd["max_amount"] = str(pd["max_amount"])
                    data.append(pd)
                return {"data": data}

    async def get_loans(self, customer_id: str) -> dict[str, Any]:
        try:
            return await self.request("GET", f"/customers/{customer_id}/loans")
        except Exception:
            from uuid import UUID

            from sqlmodel import select

            from app.db.models import LoanAccount
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                cid = UUID(customer_id) if isinstance(customer_id, str) else customer_id
                res = await db.execute(select(LoanAccount).where(LoanAccount.customer_id == cid))
                loans = res.scalars().all()
                return {"data": [loan.model_dump() for loan in loans]}

    async def create_loan_application(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return await self.request("POST", "/loan-applications", idempotency_key=idempotency_key, json=payload)


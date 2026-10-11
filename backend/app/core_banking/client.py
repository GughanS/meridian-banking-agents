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
        self.base_url = os.getenv("CORE_BASE_URL", "http://localhost:8001/mock-core/v1")
        self.api_key = "MOCK_CORE_API_KEY"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def request(self, method: str, path: str, idempotency_key: str | None = None, **kwargs: Any) -> dict[str, Any]:
        if not cb.can_execute():
            raise CircuitBreakerOpenException("Circuit breaker is open")
        
        headers = kwargs.pop("headers", {})
        headers["x-core-api-key"] = self.api_key
        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key
            
        timeout = httpx.Timeout(10.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
                response.raise_for_status()
                cb.record_success()
                return response.json()  # type: ignore
        except Exception as e:
            cb.record_failure()
            logger.error(f"Core API error: {e!s}")
            raise e

    # Helper methods for agents
    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/customers/{customer_id}")

    async def get_accounts(self, customer_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/customers/{customer_id}/accounts")

    async def get_balance(self, account_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/accounts/{account_id}/balance")

    async def get_transactions(self, account_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("GET", f"/accounts/{account_id}/transactions", params=params or {})

    async def get_cards(self, customer_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/customers/{customer_id}/cards")

    async def block_card(self, card_id: str, idempotency_key: str) -> dict[str, Any]:
        return await self.request("POST", f"/cards/{card_id}/block", idempotency_key=idempotency_key)

    async def get_credit_profile(self, customer_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/customers/{customer_id}/credit-profile")

    async def get_loan_products(self) -> dict[str, Any]:
        return await self.request("GET", "/loan-products")

    async def get_loans(self, customer_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/customers/{customer_id}/loans")

    async def create_loan_application(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return await self.request("POST", "/loan-applications", idempotency_key=idempotency_key, json=payload)

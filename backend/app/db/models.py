from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, SQLModel


def utc_now():
    return datetime.now(UTC)

# Helper for JSON columns in SQLite
def JSONColumn():
    return Column(JSON)

class Customer(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    persona_id: str = Field(index=True)  # virat, rohit, mahi
    name: str
    email: str
    phone: str

class Account(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    account_type: str  # savings, checking, credit
    balance: Decimal = Field(default=0, max_digits=15, decimal_places=2)
    currency: str = Field(default="INR")

class Card(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    account_id: UUID = Field(foreign_key="account.id")
    card_type: str  # debit, credit
    last4: str
    status: str = Field(default="active")  # active, blocked

class Transaction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    account_id: UUID = Field(foreign_key="account.id")
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    currency: str = Field(default="INR")
    timestamp: datetime
    merchant: str
    category: str
    tx_type: str  # credit, debit
    country: str = Field(default="IN")
    mcc: str = Field(default="0000")

class CreditProfile(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    score: int
    monthly_income: Decimal = Field(max_digits=15, decimal_places=2)
    monthly_obligations: Decimal = Field(default=0, max_digits=15, decimal_places=2)
    employment_status: str
    months_employed: int
    recent_delinquency_dpd: int = Field(default=0)  # >30 implies recent delinquency

class LoanProduct(SQLModel, table=True):
    id: str = Field(primary_key=True)  # personal, auto, home
    name: str
    base_rate: Decimal = Field(max_digits=5, decimal_places=2)
    min_tenure_months: int
    max_tenure_months: int
    max_amount: Decimal = Field(max_digits=15, decimal_places=2)
    max_income_multiple: int
    min_score: int

class LoanAccount(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    product_id: str = Field(foreign_key="loanproduct.id")
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    tenure_months: int
    rate: Decimal = Field(max_digits=5, decimal_places=2)
    emi: Decimal = Field(max_digits=15, decimal_places=2)

class LoanApplication(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    product_id: str = Field(foreign_key="loanproduct.id")
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    tenure_months: int
    status: str  # APPROVED, DECLINED, REFER
    reason_codes: str = Field(default="")
    offered_rate: Decimal | None = Field(default=None, max_digits=5, decimal_places=2)

class FraudAlert(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    transaction_id: UUID = Field(foreign_key="transaction.id")
    customer_id: UUID = Field(foreign_key="customer.id")
    score: int
    level: str  # LOW, MEDIUM, HIGH
    rules_triggered: Any = Field(default={}, sa_column=JSONColumn())
    created_at: datetime = Field(default_factory=utc_now)
    status: str = Field(default="open")

class Dispute(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    transaction_id: UUID = Field(foreign_key="transaction.id")
    reason: str
    status: str = Field(default="pending")

# Orchestrator Models
class ChatSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="customer.id")
    created_at: datetime = Field(default_factory=utc_now)

class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chatsession.id")
    role: str
    content: str
    timestamp: datetime = Field(default_factory=utc_now)

class AgentTrace(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chatsession.id")
    trace_data: Any = Field(default={}, sa_column=JSONColumn())
    timestamp: datetime = Field(default_factory=utc_now)

class PendingAction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chatsession.id")
    tool_name: str
    payload: Any = Field(default={}, sa_column=JSONColumn())
    expires_at: datetime
    status: str = Field(default="pending")  # pending, confirmed, cancelled, executed, expired

class AuditLog(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action: str
    customer_id: UUID
    details: Any = Field(default={}, sa_column=JSONColumn())
    timestamp: datetime = Field(default_factory=datetime.utcnow)

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.db.models import ChatSession, CreditProfile, LoanProduct, PendingAction
from app.engines.auth import verify_ownership
from app.engines.eligibility import evaluate_loan_eligibility
from app.engines.emi import calculate_emi
from app.engines.fraud_rules import evaluate_fraud_rules
from app.engines.pending_actions import (
    cancel_action,
    confirm_action,
    create_pending_action,
)


# --- EMI Tests ---
def test_calculate_emi():
    res = calculate_emi(Decimal(1500000), Decimal("9.5"), 60)
    assert res["emi"] == Decimal("31502.79") # formula checks out
    assert res["total_payment"] == res["emi"] * 60
    assert res["total_interest"] == res["total_payment"] - Decimal(1500000)

    res_zero = calculate_emi(Decimal(100000), Decimal(0), 10)
    assert res_zero["emi"] == Decimal("10000.00")
    assert res_zero["total_interest"] == Decimal("0.00")

def test_calculate_emi_invalid():
    with pytest.raises(ValueError):
        calculate_emi(Decimal(10000), Decimal("5.0"), 0)
    with pytest.raises(ValueError):
        calculate_emi(Decimal(0), Decimal("5.0"), 12)

# --- Eligibility Tests ---
def test_eligibility_approved():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(500000), 36)
    assert res.eligible is True
    assert res.offered_rate == Decimal("10.0")

def test_eligibility_declined_score():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=650, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(500000), 36)
    assert res.eligible is False
    assert any("Credit score" in r for r in res.reason_codes)

def test_eligibility_declined_tenure():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(500000), 10)
    assert res.eligible is False
    assert any("Tenure" in r for r in res.reason_codes)

def test_eligibility_declined_amount():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(1500000), 36)
    assert res.eligible is False
    assert any("exceeds product maximum" in r for r in res.reason_codes)

def test_eligibility_declined_income_multiple():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(50000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(800000), 36)
    assert res.eligible is False
    assert any("income multiple" in r for r in res.reason_codes)

def test_eligibility_declined_dti():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(100000), monthly_obligations=Decimal(70000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(500000), 36)
    assert res.eligible is False
    assert any("Debt-to-income" in r for r in res.reason_codes)

def test_eligibility_declined_delinquency():
    profile = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=750, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=45)
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=700)
    
    res = evaluate_loan_eligibility(profile, product, Decimal(500000), 36)
    assert res.eligible is False
    assert any("Recent delinquency" in r for r in res.reason_codes)

def test_eligibility_rate_bump():
    product = LoanProduct(id="test", name="Test", base_rate=Decimal("10.0"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(1000000), max_income_multiple=10, min_score=600)
    
    profile1 = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=650, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    res1 = evaluate_loan_eligibility(profile1, product, Decimal(500000), 36)
    assert res1.offered_rate == Decimal("11.5")
    
    profile2 = CreditProfile(id=uuid.uuid4(), customer_id=uuid.uuid4(), score=720, monthly_income=Decimal(100000), monthly_obligations=Decimal(10000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
    res2 = evaluate_loan_eligibility(profile2, product, Decimal(500000), 36)
    assert res2.offered_rate == Decimal("10.5")

# --- Fraud Tests ---
def test_fraud_rules():
    score, level, rules = evaluate_fraud_rules(Decimal(100), "IN", "5812", 1, is_card_present=False)
    assert score == 0
    assert level == "LOW"
    assert len(rules) == 0

    score, level, rules = evaluate_fraud_rules(Decimal(60000), "US", "6051", 4, is_card_present=False)
    assert score == 100 
    assert level == "HIGH"
    assert "FOREIGN_CNP" in rules
    assert "HIGH_RISK_MCC" in rules
    assert "VELOCITY_BURST" in rules
    assert "HIGH_AMOUNT" in rules

    score, level, rules = evaluate_fraud_rules(Decimal(1000), "IN", "5812", 4, is_card_present=True)
    assert score == 30
    assert level == "LOW"
    assert "VELOCITY_BURST" in rules

    score, level, rules = evaluate_fraud_rules(Decimal(1000), "US", "5812", 1, is_card_present=False)
    assert score == 40
    assert level == "MEDIUM"
    assert "FOREIGN_CNP" in rules

# --- Auth Tests ---
def test_auth_verify():
    cid = uuid.uuid4()
    assert verify_ownership(cid, cid) is True
    assert verify_ownership(cid, uuid.uuid4()) is False

# --- Pending Actions Tests ---



@pytest_asyncio.fixture
async def memory_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as db:
        yield db

@pytest.mark.asyncio
async def test_pending_action_flow(memory_db):
    cid = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), customer_id=cid)
    memory_db.add(session)
    await memory_db.commit()

    action = await create_pending_action(memory_db, session.id, "test_tool", {"foo": "bar"})
    assert action.status == "pending"
    
    # Confirm
    confirmed = await confirm_action(memory_db, action.id, cid)
    assert confirmed.status == "confirmed"
    
    # Re-confirm fails
    with pytest.raises(ValueError, match="already in status"):
        await confirm_action(memory_db, action.id, cid)

@pytest.mark.asyncio
async def test_pending_action_auth_fail(memory_db):
    cid = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), customer_id=cid)
    memory_db.add(session)
    await memory_db.commit()

    action = await create_pending_action(memory_db, session.id, "test_tool", {"foo": "bar"})
    
    # Try confirm with wrong customer
    with pytest.raises(ValueError, match="Unauthorized"):
        await confirm_action(memory_db, action.id, uuid.uuid4())

@pytest.mark.asyncio
async def test_pending_action_expire(memory_db):
    cid = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), customer_id=cid)
    memory_db.add(session)
    await memory_db.commit()

    # Create expired
    action = PendingAction(
        id=uuid.uuid4(),
        session_id=session.id,
        tool_name="test_tool",
        payload={},
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        status="pending"
    )
    memory_db.add(action)
    await memory_db.commit()

    with pytest.raises(ValueError, match="expired"):
        await confirm_action(memory_db, action.id, cid)

@pytest.mark.asyncio
async def test_pending_action_cancel(memory_db):
    cid = uuid.uuid4()
    session = ChatSession(id=uuid.uuid4(), customer_id=cid)
    memory_db.add(session)
    await memory_db.commit()

    action = await create_pending_action(memory_db, session.id, "test_tool", {})
    cancelled = await cancel_action(memory_db, action.id, cid)
    assert cancelled.status == "cancelled"

    # Cancel auth fail
    action2 = await create_pending_action(memory_db, session.id, "test2", {})
    with pytest.raises(ValueError, match="Unauthorized"):
        await cancel_action(memory_db, action2.id, uuid.uuid4())
        
    # Cancel already cancelled (status shouldn't change)
    await cancel_action(memory_db, action.id, cid)
    
    # Missing action
    with pytest.raises(ValueError, match="not found"):
        await cancel_action(memory_db, uuid.uuid4(), cid)
    with pytest.raises(ValueError, match="not found"):
        await confirm_action(memory_db, uuid.uuid4(), cid)

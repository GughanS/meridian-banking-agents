from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.db.models import (
    Account,
    Card,
    CreditProfile,
    Customer,
    Dispute,
    FraudAlert,
    LoanAccount,
    LoanApplication,
    LoanProduct,
    Transaction,
)
from app.db.session import engine

mock_core_router = APIRouter(prefix="/mock-core/v1", tags=["Core Banking"])

async def get_db():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

def verify_api_key(x_core_api_key: str = Header(...)):
    if x_core_api_key != "MOCK_CORE_API_KEY":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@mock_core_router.get("/customers/{id}")
async def get_customer(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    customer = await db.get(Customer, id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"data": customer}

@mock_core_router.get("/customers/{id}/accounts")
async def get_customer_accounts(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(Account).where(Account.customer_id == id))
    return {"data": result.scalars().all()}

@mock_core_router.get("/accounts/{id}/balance")
async def get_account_balance(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    account = await db.get(Account, id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"data": {"balance": str(account.balance), "currency": account.currency}}

@mock_core_router.get("/accounts/{id}/transactions")
async def get_account_transactions(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key),
                                   date_from: str = None, date_to: str = None, category: str = None, 
                                   min_amount: float = None, limit: int = 50, cursor: int = 0):
    query = select(Transaction).where(Transaction.account_id == id)
    if category:
        query = query.where(Transaction.category == category)
    if min_amount:
        query = query.where(Transaction.amount >= min_amount)
    
    query = query.order_by(Transaction.timestamp.desc()).offset(cursor).limit(limit)
    result = await db.execute(query)
    txs = result.scalars().all()
    data = []
    for t in txs:
        tx_dict = t.model_dump()
        tx_dict["amount"] = str(tx_dict["amount"])
        data.append(tx_dict)
    return {"data": data, "next_cursor": cursor + limit if len(data) == limit else None}

@mock_core_router.get("/transactions/{id}")
async def get_transaction(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    tx = await db.get(Transaction, id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx_dict = tx.model_dump()
    tx_dict["amount"] = str(tx_dict["amount"])
    return {"data": tx_dict}

@mock_core_router.get("/customers/{id}/cards")
async def get_customer_cards(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(Card).where(Card.customer_id == id))
    return {"data": result.scalars().all()}

@mock_core_router.post("/cards/{id}/block")
async def block_card(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key), x_idempotency_key: str = Header(None)):
    card = await db.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "blocked"
    await db.commit()
    return {"data": card}

@mock_core_router.post("/cards/{id}/unblock")
async def unblock_card(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key), x_idempotency_key: str = Header(None)):
    card = await db.get(Card, id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "active"
    await db.commit()
    return {"data": card}

@mock_core_router.get("/customers/{id}/credit-profile")
async def get_credit_profile(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(CreditProfile).where(CreditProfile.customer_id == id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    data = profile.model_dump()
    data["monthly_income"] = str(data["monthly_income"])
    data["monthly_obligations"] = str(data["monthly_obligations"])
    return {"data": data}

@mock_core_router.get("/loan-products")
async def get_loan_products(db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(LoanProduct))
    products = result.scalars().all()
    data = []
    for p in products:
        d = p.model_dump()
        d["base_rate"] = str(d["base_rate"])
        d["max_amount"] = str(d["max_amount"])
        data.append(d)
    return {"data": data}

@mock_core_router.get("/customers/{id}/loans")
async def get_customer_loans(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(LoanAccount).where(LoanAccount.customer_id == id))
    loans = result.scalars().all()
    data = []
    for loan in loans:
        d = loan.model_dump()
        d["amount"] = str(d["amount"])
        d["rate"] = str(d["rate"])
        d["emi"] = str(d["emi"])
        data.append(d)
    return {"data": data}

@mock_core_router.post("/loan-applications")
async def create_loan_application(payload: dict, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key), x_idempotency_key: str = Header(None)):
    app = LoanApplication(
        customer_id=payload["customer_id"],
        product_id=payload["product_id"],
        amount=payload["amount"],
        tenure_months=payload["tenure_months"],
        status="PENDING_REVIEW"
    )
    db.add(app)
    await db.commit()
    return {"data": {"id": str(app.id), "status": app.status}}

@mock_core_router.get("/loan-applications/{id}")
async def get_loan_application(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    app = await db.get(LoanApplication, id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    d = app.model_dump()
    d["amount"] = str(d["amount"])
    d["offered_rate"] = str(d["offered_rate"]) if d["offered_rate"] else None
    return {"data": d}

@mock_core_router.get("/customers/{id}/fraud-alerts")
async def get_fraud_alerts(id: UUID, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    result = await db.execute(select(FraudAlert).where(FraudAlert.customer_id == id))
    return {"data": result.scalars().all()}

@mock_core_router.post("/disputes")
async def create_dispute(payload: dict, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key), x_idempotency_key: str = Header(None)):
    dispute = Dispute(
        transaction_id=payload["transaction_id"],
        reason=payload["reason"]
    )
    db.add(dispute)
    await db.commit()
    return {"data": {"id": str(dispute.id), "status": dispute.status}}

@mock_core_router.post("/simulator/inject")
async def inject_anomaly(payload: dict, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_api_key)):
    return {"data": {"injected": payload.get("type", "unknown")}}

@mock_core_router.get("/health")
async def core_health():
    return {"status": "ok"}

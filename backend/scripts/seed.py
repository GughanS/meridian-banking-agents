import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlmodel import SQLModel

from app.db.models import (
    Account,
    Card,
    CreditProfile,
    Customer,
    LoanAccount,
    LoanProduct,
    Transaction,
)
from app.db.session import engine

fake = Faker()
Faker.seed(42)
random.seed(42)

async def clear_data(session):
    # Idempotent approach: drop all tables and recreate, or clear rows.
    # Since it's MVP, we just drop and recreate all via engine.
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

def random_tx(account_id, tx_type, category, min_amount, max_amount, mcc, merchant, country="IN", days_ago=0):
    amount = Decimal(random.randint(min_amount, max_amount))
    ts = datetime.now(UTC) - timedelta(days=days_ago) + timedelta(minutes=random.randint(0, 1440))
    return Transaction(
        account_id=account_id, amount=amount, currency="INR", timestamp=ts,
        merchant=merchant, category=category, tx_type=tx_type, country=country, mcc=mcc
    )

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # We need a custom session maker without yield for script
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Products
        p1 = LoanProduct(id="personal", name="Personal Loan", base_rate=Decimal("10.5"), min_tenure_months=12, max_tenure_months=60, max_amount=Decimal(2500000), max_income_multiple=20, min_score=650)
        p2 = LoanProduct(id="auto", name="Auto Loan", base_rate=Decimal("9.0"), min_tenure_months=12, max_tenure_months=84, max_amount=Decimal(3000000), max_income_multiple=30, min_score=650)
        p3 = LoanProduct(id="home", name="Home Loan", base_rate=Decimal("8.5"), min_tenure_months=60, max_tenure_months=240, max_amount=Decimal(15000000), max_income_multiple=60, min_score=700)
        db.add_all([p1, p2, p3])
        await db.commit()

        # Persona 1: Virat Kohli (Prime / Salaried)
        virat = Customer(persona_id="virat", name="Virat Kohli", email="virat@example.com", phone="+919876543210")
        db.add(virat)
        await db.commit()
        
        virat_cp = CreditProfile(customer_id=virat.id, score=782, monthly_income=Decimal(180000), monthly_obligations=Decimal(35000), employment_status="Salaried", months_employed=84, recent_delinquency_dpd=0)
        db.add(virat_cp)
        
        virat_acc1 = Account(customer_id=virat.id, account_type="savings", balance=Decimal(1250000), currency="INR")
        virat_acc2 = Account(customer_id=virat.id, account_type="checking", balance=Decimal(45000), currency="INR")
        db.add_all([virat_acc1, virat_acc2])
        await db.commit()

        virat_dc = Card(customer_id=virat.id, account_id=virat_acc1.id, card_type="debit", last4="4521")
        virat_cc = Card(customer_id=virat.id, account_id=virat_acc2.id, card_type="credit", last4="9832")
        db.add_all([virat_dc, virat_cc])
        
        virat_loan = LoanAccount(customer_id=virat.id, product_id="auto", amount=Decimal(1500000), tenure_months=60, rate=Decimal("9.5"), emi=Decimal(31500))
        db.add(virat_loan)

        # Generate normal txs for Virat
        for _ in range(300):
            db.add(random_tx(virat_acc1.id, "debit", "dining", 500, 5000, "5812", fake.company(), days_ago=random.randint(1, 360)))

        # Persona 2: Rohit Sharma (Mid / Small Business)
        rohit = Customer(persona_id="rohit", name="Rohit Sharma", email="rohit@example.com", phone="+918765432109")
        db.add(rohit)
        await db.commit()

        rohit_cp = CreditProfile(customer_id=rohit.id, score=684, monthly_income=Decimal(75000), monthly_obligations=Decimal(15000), employment_status="Salaried", months_employed=36, recent_delinquency_dpd=0)
        db.add(rohit_cp)
        
        rohit_acc = Account(customer_id=rohit.id, account_type="savings", balance=Decimal(85000), currency="INR")
        db.add(rohit_acc)
        await db.commit()

        rohit_dc = Card(customer_id=rohit.id, account_id=rohit_acc.id, card_type="debit", last4="1122")
        db.add(rohit_dc)
        
        # Normal txs for Rohit
        for _ in range(200):
            db.add(random_tx(rohit_acc.id, "debit", "groceries", 200, 3000, "5411", fake.company(), days_ago=random.randint(5, 360)))

        # Suspicious Tx 1: Foreign card-not-present
        db.add(random_tx(rohit_acc.id, "debit", "shopping", 25000, 25000, "5999", "Steam Games", country="US", days_ago=1))
        
        # Suspicious Tx 2: High-risk MCC (Crypto)
        db.add(random_tx(rohit_acc.id, "debit", "transfer", 50000, 50000, "6051", "Binance", country="IE", days_ago=2))
        
        # Suspicious Tx 3: Velocity burst
        for _ in range(4):
            db.add(random_tx(rohit_acc.id, "debit", "entertainment", 1500, 1500, "7999", "Netflix", country="IN", days_ago=0))

        # Persona 3: Mahi (Student / Stretched)
        mahi = Customer(persona_id="mahi", name="Mahi", email="mahi@example.com", phone="+917654321098")
        db.add(mahi)
        await db.commit()

        mahi_cp = CreditProfile(customer_id=mahi.id, score=598, monthly_income=Decimal(40000), monthly_obligations=Decimal(32000), employment_status="Self-employed", months_employed=12, recent_delinquency_dpd=45)
        db.add(mahi_cp)
        
        mahi_acc = Account(customer_id=mahi.id, account_type="savings", balance=Decimal(12000), currency="INR")
        db.add(mahi_acc)
        await db.commit()

        mahi_dc = Card(customer_id=mahi.id, account_id=mahi_acc.id, card_type="debit", last4="3344")
        db.add(mahi_dc)

        for _ in range(100):
            db.add(random_tx(mahi_acc.id, "debit", "utilities", 500, 2000, "4900", fake.company(), days_ago=random.randint(1, 360)))
        
        await db.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())

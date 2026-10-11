import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel

from app.db.models import ChatSession, Customer, PendingAction
from app.db.session import SessionLocal, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        
    async with SessionLocal() as db:
        cust = Customer(
            id=uuid.uuid4(),
            persona_id="test_persona",
            first_name="Virat",
            last_name="Test",
            name="Virat Test",
            email="virat@example.com",
            phone="+919876543210"
        )
        db.add(cust)
        await db.commit()
    yield

@pytest.mark.asyncio
async def test_auth_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={"email": "virat@example.com"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        response_bad = await client.post("/auth/login", json={"email": "invalid@example.com"})
        assert response_bad.status_code == 401

@pytest.mark.asyncio
async def test_chat_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat/stream", json={"session_id": str(uuid.uuid4()), "message": "hello"})
        assert response.status_code == 401 # Missing Bearer token

@pytest.mark.asyncio
async def test_chat_authorized(monkeypatch):
    import os
    os.environ["LLM_PROVIDER"] = "mock"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/auth/login", json={"email": "virat@example.com"})
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        async with client.stream("POST", "/chat/stream", json={"session_id": str(uuid.uuid4()), "message": "hello"}, headers=headers) as response:
            assert response.status_code == 200
            chunk = await response.aread()
            assert b"data:" in chunk

@pytest.mark.asyncio
async def test_action_confirm():
    async with SessionLocal() as db:
        from sqlmodel import select
        res = await db.execute(select(Customer))
        cust = res.scalars().first()
        session = ChatSession(id=uuid.uuid4(), customer_id=cust.id)
        db.add(session)
        
        action = PendingAction(
            id=uuid.uuid4(),
            session_id=session.id,
            tool_name="test",
            payload={},
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            status="pending"
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/auth/login", json={"email": "virat@example.com"})
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post(f"/actions/{action.id}/confirm", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        
        res2 = await client.post(f"/actions/{action.id}/cancel", headers=headers)
        assert res2.status_code == 400

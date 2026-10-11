import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models import Customer
from app.db.session import get_session

SECRET_KEY = os.getenv("JWT_SECRET", "meridian-secret-key-super-secure-production-grade-32-bytes")
ALGORITHM = "HS256"

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: str

@router.post("/auth/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_session)):
    persona_key = req.email.split("@")[0].split(".")[0].lower()
    stmt = select(Customer).where(
        (Customer.email == req.email) | (Customer.persona_id == persona_key)
    )
    res = await db.execute(stmt)
    customer = res.scalars().first()
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid persona email")
        
    payload = {
        "sub": str(customer.id),
        "exp": datetime.now(UTC) + timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

async def get_current_customer_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return UUID(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

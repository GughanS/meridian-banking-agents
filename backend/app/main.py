from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.actions import router as actions_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.simulator import router as simulator_router
from app.api.stream import router as stream_router
from app.core.errors import MeridianError, meridian_exception_handler
from app.core.logging import setup_logging
from app.core_banking.api import mock_core_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    
    from app.events.bus import event_bus
    from app.events.fraud_monitor import setup_fraud_monitor
    from app.simulator.transactions import simulator
    
    event_bus.start()
    setup_fraud_monitor()
    await simulator.start()
    
    yield
    
    await simulator.stop()
    await event_bus.stop()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Meridian API", lifespan=lifespan)
app.state.limiter = limiter

app.add_exception_handler(MeridianError, meridian_exception_handler)  # type: ignore
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_core_router)
app.include_router(auth_router, tags=["auth"])
app.include_router(chat_router, tags=["chat"])
app.include_router(actions_router, tags=["actions"])
app.include_router(stream_router, tags=["stream"])
app.include_router(simulator_router, prefix="/simulator", tags=["simulator"])

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

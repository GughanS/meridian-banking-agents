import structlog
from fastapi import APIRouter

from app.simulator.transactions import simulator

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/inject")
async def inject_anomaly():
    """Injects a fraudulent transaction to trigger the fraud monitor and Risk Agent via the Event Bus"""
    logger.info("Injecting anomaly for UC8")
    await simulator.inject_anomaly()
    return {"status": "anomaly injected"}

from fastapi import FastAPI
from app.core.errors import setup_exception_handlers
from app.core.logging import setup_logging
import structlog

setup_logging()

app = FastAPI(title="Meridian Mock Core API", version="0.1.0")
setup_exception_handlers(app)

logger = structlog.get_logger()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

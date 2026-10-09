from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.code = code
        self.message = message
        self.status_code = status_code

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        logger.error("api_error", code=exc.code, message=exc.message, url=str(request.url))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", url=str(request.url))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}
        )

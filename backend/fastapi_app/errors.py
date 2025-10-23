from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error(f"Unhandled exception: {exc}\n{tb}")
        return JSONResponse(status_code=500, content={
            "error": "internal_server_error",
            "message": str(exc),
            "trace": tb if app.debug else None
        })

from __future__ import annotations

import logging
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except AppException as exc:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
            logger.log(
                log_level,
                f"Application error: {exc.code} — {exc.message}",
                extra={
                    "correlation_id": correlation_id,
                    "error_code": exc.code,
                    "status_code": exc.status_code,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                    "meta": {
                        "correlationId": correlation_id,
                        "timestamp": None,
                    },
                },
            )
        except StarletteHTTPException:
            raise
        except Exception as exc:
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.error(
                f"Unhandled exception: {exc}",
                extra={
                    "correlation_id": correlation_id,
                    "traceback": traceback.format_exc(),
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": [],
                    },
                    "meta": {
                        "correlationId": correlation_id,
                        "timestamp": None,
                    },
                },
            )

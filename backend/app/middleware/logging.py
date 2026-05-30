from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        extra = {
            "correlation_id": correlation_id,
            "durationMs": round(duration_ms, 2),
            "httpMethod": request.method,
            "httpUrl": str(request.url.path),
            "httpStatusCode": response.status_code,
        }

        if response.status_code >= 500:
            logger.error(
                f"{request.method} {request.url.path} {response.status_code} in {duration_ms:.1f}ms",
                extra=extra,
            )
        elif response.status_code >= 400:
            logger.warning(
                f"{request.method} {request.url.path} {response.status_code} in {duration_ms:.1f}ms",
                extra=extra,
            )
        else:
            logger.info(
                f"{request.method} {request.url.path} {response.status_code} in {duration_ms:.1f}ms",
                extra=extra,
            )

        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))
        return response

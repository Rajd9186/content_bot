from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.deps import get_db
from app.infrastructure.messaging.redis_client import redis_client
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness check",
    operation_id="checkLiveness",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptimeSeconds=time.time() - _start_time,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    operation_id="checkReadiness",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> ReadinessResponse:
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    if redis_client._client is not None:
        try:
            await redis_client.client.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"
    else:
        checks["redis"] = "not_configured"

    all_ok = all(v == "ok" or v == "not_configured" for v in checks.values())

    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        checks=checks,
    )

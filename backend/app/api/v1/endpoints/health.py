from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.deps import get_db
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

    all_ok = all(v == "ok" for v in checks.values())

    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        checks=checks,
    )

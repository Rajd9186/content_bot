from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.infrastructure.providers.provider_scheduler import scheduler

router = APIRouter(tags=["operations"])


@router.get(
    "/providers/stats",
    response_model=dict[str, Any],
    summary="Get all provider statistics",
    operation_id="getProviderStats",
)
async def get_provider_stats() -> dict[str, Any]:
    """
    Feature 9: Provider Dashboard data.
    Returns capacity, performance, and circuit state for all providers.
    """
    return await scheduler.get_all_provider_stats()

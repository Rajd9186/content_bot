from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.infrastructure.metrics.collector import metrics_collector

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus-compatible metrics",
    operation_id="getMetrics",
    response_class=PlainTextResponse,
)
async def get_metrics() -> PlainTextResponse:
    return PlainTextResponse(
        content=metrics_collector.format_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get(
    "/metrics/json",
    summary="JSON metrics summary",
    operation_id="getMetricsJson",
)
async def get_metrics_json() -> dict:
    return metrics_collector.get_stats()

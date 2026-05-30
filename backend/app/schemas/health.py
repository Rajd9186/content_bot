from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    uptimeSeconds: float


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]

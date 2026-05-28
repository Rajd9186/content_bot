from __future__ import annotations

from typing import Dict

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    uptimeSeconds: float


class ReadinessResponse(BaseModel):
    status: str
    checks: Dict[str, str]

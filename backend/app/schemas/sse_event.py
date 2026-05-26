from __future__ import annotations

from typing import Any
from pydantic import BaseModel, model_validator


class SSEEvent(BaseModel):
    id: str = ""
    workflow_id: str = ""
    type: str = ""
    agent: str = ""
    status: str = "running"
    message: str = ""
    progress: float = 0.0
    payload: dict[str, Any] = {}
    timestamp: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce_none(cls, values: Any) -> Any:
        if isinstance(values, dict):
            for field in ("id", "workflow_id", "type", "agent", "status", "message", "timestamp"):
                if values.get(field) is None:
                    values[field] = ""
            if values.get("progress") is None:
                values["progress"] = 0.0
            if values.get("payload") is None:
                values["payload"] = {}
        return values

    def to_sse_dict(self) -> dict:
        return self.model_dump()

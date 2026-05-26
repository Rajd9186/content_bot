from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ContradictionResponse(BaseModel):
    id: UUID
    project_id: UUID
    claim_text: str
    severity: str
    conflicting_sources: list
    explanation: str | None
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContradictionResolve(BaseModel):
    resolution: str

from datetime import datetime
from pydantic import BaseModel


class ContradictionResponse(BaseModel):
    id: str
    project_id: str
    claim_text: str
    severity: str
    conflicting_sources: list
    explanation: str | None
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContradictionResolve(BaseModel):
    resolution: str

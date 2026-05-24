import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ClaimResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    claim_text: str
    confidence: float | None
    status: str
    explanation: str | None
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimVerificationResponse(BaseModel):
    claims: list[ClaimResponse]
    total_claims: int
    verified_count: int
    unverified_count: int
    contradicted_count: int
    unsupported_count: int
    average_confidence: float

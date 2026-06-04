import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    claim_id: uuid.UUID | None
    source_id: uuid.UUID | None
    snippet: str
    relevance_score: float | None
    extracted_at: datetime
    source_url: str | None = None
    source_domain: str | None = None
    source_trust_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
    total_count: int
    average_relevance: float

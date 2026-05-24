import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ContentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    markdown: str
    summary: str | None
    word_count: int | None
    citations: list[dict]
    seo_metadata: dict | None
    overall_confidence: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentGenerateResponse(BaseModel):
    project_id: uuid.UUID
    content_id: uuid.UUID
    markdown: str
    summary: str
    word_count: int
    citations: list[dict]
    seo_metadata: dict
    overall_confidence: float
    claims: list[dict] = Field(default_factory=list)
    verification_summary: dict = Field(default_factory=dict)

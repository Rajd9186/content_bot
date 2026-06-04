import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(from_attributes=True)


class ContentGenerateResponse(BaseModel):
    project_id: uuid.UUID
    status: str = Field(default="completed")
    message: str | None = Field(default=None)
    content_id: uuid.UUID | None = Field(default=None)
    markdown: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    word_count: int | None = Field(default=None)
    citations: list[dict] | None = Field(default=None)
    seo_metadata: dict | None = Field(default=None)
    overall_confidence: float | None = Field(default=None)
    quality_score: float | None = Field(default=None)
    claims: list[dict] = Field(default_factory=list)
    verification_summary: dict = Field(default_factory=dict)


class ContentStatusResponse(BaseModel):
    """Response for /content/latest that can return either content or status."""

    status: str = Field(
        ...,
        description="One of: processing, completed, failed, not_found",
    )
    workflow_status: str | None = Field(
        default=None,
        description="Current workflow execution status: running, completed, failed",
    )
    current_node: str | None = Field(
        default=None,
        description="Current workflow node being executed",
    )
    progress: list[str] = Field(
        default_factory=list,
        description="List of completed workflow steps so far",
    )
    message: str | None = Field(default=None)
    content: ContentResponse | None = Field(default=None)

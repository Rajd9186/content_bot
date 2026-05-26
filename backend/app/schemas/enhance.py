import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class EnhancementJobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    workflow_id: uuid.UUID
    agent_name: str
    status: str
    progress: float | None = None
    result_data: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class EnhancementTriggerResponse(BaseModel):
    job_id: uuid.UUID
    agent_name: str
    status: str = "started"
    message: str


class ContentVersionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    version_number: int
    agent_name: str
    status: str
    markdown: str
    summary: str | None = None
    word_count: int | None = None
    citations: list[dict] = Field(default_factory=list)
    overall_confidence: float | None = None
    parent_version_id: uuid.UUID | None = None
    change_description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

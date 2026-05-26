import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SourceResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    url: str
    domain: str
    title: str | None
    trust_score: float | None
    author: str | None
    published_date: datetime | None
    snippet: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HyperlinkValidationResponse(BaseModel):
    id: UUID
    project_id: UUID
    url: str
    label: str | None
    status: str
    status_code: int | None
    error_message: str | None
    resolved_url: str | None
    is_verified: bool
    checked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HyperlinkValidationSummary(BaseModel):
    total: int
    verified: int
    broken: int
    pending: int
    verification_rate: float

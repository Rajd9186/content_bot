import uuid
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, BeforeValidator


def empty_to_none(v: str | None) -> str | None:
    if v == "":
        return None
    return v

OptionalString = Annotated[str | None, BeforeValidator(empty_to_none)]


class ProjectCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    title: OptionalString = Field(default=None, min_length=3, max_length=500)
    points_to_cover: list[str] = Field(default_factory=list)
    tone: str = Field(default="professional")
    content_type: str = Field(default="article")
    target_audience: OptionalString = Field(default=None, max_length=300)
    seo_keywords: list[str] = Field(default_factory=list)

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        allowed = {"professional", "academic", "conversational", "persuasive", "informative"}
        if v.lower() not in allowed:
            raise ValueError(f"Tone must be one of: {allowed}")
        return v.lower()

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        allowed = {"blog_post", "article", "research_paper", "report", "white_paper", "case_study"}
        if v.lower() not in allowed:
            raise ValueError(f"Content type must be one of: {allowed}")
        return v.lower()


class ProjectResponse(BaseModel):
    id: uuid.UUID
    topic: str
    title: str
    points_to_cover: list[str]
    tone: str
    content_type: str
    target_audience: str | None
    seo_keywords: list[str]
    status: str
    outline: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectQuickCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)


class ProjectStatusUpdate(BaseModel):
    status: str


class ProjectWorkflowStatus(BaseModel):
    """Lightweight workflow status returned with project info."""

    workflow_status: str | None = None
    current_node: str | None = None
    has_content: bool = False

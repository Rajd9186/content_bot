import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    title: str = Field(..., min_length=3, max_length=500)
    points_to_cover: list[str] = Field(default_factory=list)
    tone: str = Field(default="professional")
    content_type: str = Field(default="article")
    target_audience: str | None = Field(default=None, max_length=300)
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

    model_config = {"from_attributes": True}


class ProjectQuickCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)


class ProjectStatusUpdate(BaseModel):
    status: str

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
    tone: str = Field(default="PROFESSIONAL")
    content_type: str = Field(default="ARTICLE")
    target_audience: OptionalString = Field(default=None, max_length=300)
    seo_keywords: list[str] = Field(default_factory=list)

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v: str) -> str:
        allowed = {"professional", "academic", "conversational", "persuasive", "informative"}
        if v.lower() not in allowed:
            raise ValueError(f"Tone must be one of: {allowed}")
        return v.upper()

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        allowed = {"blog_post", "article", "research_paper", "research_article", "report", "white_paper", "case_study"}
        if v.lower() not in allowed:
            raise ValueError(f"Content type must be one of: {allowed}")
        return v.upper()


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


class ProjectSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    archived: bool = False
    total_outputs: int = 0
    total_memories: int = 0
    last_activity: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectQuickCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)


class ProjectStatusUpdate(BaseModel):
    status: str


class PinMemoryRequest(BaseModel):
    memory_id: str
    priority: int = 0
    """Lightweight workflow status returned with project info."""

    workflow_status: str | None = None
    current_node: str | None = None
    has_content: bool = False


class TimelineEntry(BaseModel):
    id: str
    event_type: str
    description: str
    created_at: datetime
    metadata: dict = {}

    model_config = ConfigDict(from_attributes=True, extra="allow")


class MemoryResponse(BaseModel):
    id: str
    memory_type: str
    content: str
    confidence_score: float = 0.0
    pinned: bool = False
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class OutputResponse(BaseModel):
    id: str
    title: str | None = None
    content: str | None = None
    content_type: str = ""
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ConversationResponse(BaseModel):
    id: str
    role: str = ""
    content: str = ""
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ContextAssemblyRequest(BaseModel):
    prompt: str
    top_k: int = 10
    similarity_threshold: float = 0.7


class ContextAssemblyResponse(BaseModel):
    project_context: dict = {}
    prompt: str = ""
    relevant_memories: list[MemoryResponse] = []
    pinned_memories: list[MemoryResponse] = []
    related_outputs: list[OutputResponse] = []
    related_prompts: list[ConversationResponse] = []

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ProjectDashboard(BaseModel):
    project: dict = {}
    total_outputs: int = 0
    total_memories: int = 0
    total_sources: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_activity: str | None = None
    recent_workflows: list[dict] = []

    model_config = ConfigDict(from_attributes=True, extra="allow")

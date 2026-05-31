from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    archived: bool | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    archived: bool = False
    owner_id: str
    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    archived: bool = False
    total_outputs: int = 0
    total_memories: int = 0
    last_activity: datetime | None = None


class ConversationResponse(BaseModel):
    id: str
    project_id: str
    prompt: str
    user_metadata: dict[str, Any] | None = None
    created_at: datetime


class OutputResponse(BaseModel):
    id: str
    project_id: str
    workflow_execution_id: str | None = None
    title: str | None = None
    content: str | None = None
    content_type: str = "article"
    created_at: datetime


class MemoryResponse(BaseModel):
    id: str
    project_id: str
    memory_type: str
    content: str
    confidence_score: float = 1.0
    pinned: bool = False
    priority: int = 0
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_type: str | None = None


class MemorySearchResponse(BaseModel):
    results: list[MemoryResponse]
    query: str
    total: int


class PinMemoryRequest(BaseModel):
    memory_id: str
    priority: int = 0


class TimelineEntry(BaseModel):
    id: str
    type: str  # "prompt", "output", "memory", "workflow"
    title: str
    description: str | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextAssemblyRequest(BaseModel):
    project_id: str
    prompt: str
    top_k: int = 10
    similarity_threshold: float = 0.0


class ContextAssemblyResponse(BaseModel):
    project_context: dict[str, Any]
    prompt: str
    relevant_memories: list[MemoryResponse] = Field(default_factory=list)
    pinned_memories: list[MemoryResponse] = Field(default_factory=list)
    related_outputs: list[OutputResponse] = Field(default_factory=list)
    related_prompts: list[ConversationResponse] = Field(default_factory=list)


class ProjectDashboard(BaseModel):
    project: ProjectResponse
    total_outputs: int = 0
    total_memories: int = 0
    total_sources: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_activity: datetime | None = None
    recent_workflows: list[dict[str, Any]] = Field(default_factory=list)

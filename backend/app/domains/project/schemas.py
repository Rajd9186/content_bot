from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    archived: Optional[bool] = None

class ProjectInDBBase(ProjectBase):
    id: UUID
    owner_id: UUID
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Project(ProjectInDBBase):
    pass

class ProjectDashboard(BaseModel):
    id: UUID
    name: str
    total_memories: int = 0
    total_outputs: int = 0
    total_tokens: int = 0
    last_activity: Optional[datetime] = None

class MemorySearchQuery(BaseModel):
    query: str
    limit: int = 10

class MemorySearchResponse(BaseModel):
    content: str
    score: float
    memory_type: str
    created_at: datetime

class MemoryPinRequest(BaseModel):
    priority: int = 0

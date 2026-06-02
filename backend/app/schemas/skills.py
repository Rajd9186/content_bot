from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    content_markdown: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(writing|research|seo|fact_check|compliance|brand_voice|youtube|finance|custom)$")
    created_by: str | None = None
    agent_targets: list[str] | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    content_markdown: str | None = None
    category: str | None = None
    active: bool | None = None
    agent_targets: list[str] | None = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    content_markdown: str
    category: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    active: bool = True
    agent_targets: list[str] = Field(default_factory=list)


class SkillVersionResponse(BaseModel):
    id: str
    skill_id: str
    version: int
    content_markdown: str
    created_at: datetime
    created_by: str | None = None


class ProjectSkillResponse(BaseModel):
    id: str
    project_id: str
    skill_id: str
    skill_name: str = ""
    skill_category: str = ""
    priority: int = 0
    enabled: bool = True


class ProjectSkillAssign(BaseModel):
    skill_id: str
    priority: int = 0


class SkillTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    skill_id: str


class SkillTestResult(BaseModel):
    prompt: str
    without_skill: str = ""
    with_skill: str = ""
    compliance_score: float = 0.0
    readability_diff: float = 0.0
    seo_diff: float = 0.0
    style_diff: float = 0.0


class SkillAnalyticsResponse(BaseModel):
    skill_id: str
    usage_count: int = 0
    average_compliance: float = 0.0
    average_rating: float = 0.0
    last_used: datetime | None = None


class ComplianceEvaluation(BaseModel):
    skill_id: str
    skill_name: str = ""
    compliance_score: float = 0.0
    violations: list[str] = Field(default_factory=list)


class SkillConflictResponse(BaseModel):
    id: str
    workflow_execution_id: str | None = None
    skill_a: str
    skill_b: str
    resolution: str | None = None
    created_at: datetime


class SkillTemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str | None = None
    content_markdown: str
    author: str | None = None
    downloads: int = 0
    created_at: datetime


class ActiveSkillPackage(BaseModel):
    active_skills: list[SkillResponse] = Field(default_factory=list)
    skill_priorities: dict[str, int] = Field(default_factory=dict)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)

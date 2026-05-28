from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowStage(str, Enum):
    INIT = "INIT"
    PLANNING = "PLANNING"
    RESEARCH = "RESEARCH"
    SYNTHESIS = "SYNTHESIS"
    OUTLINING = "OUTLINING"
    WRITING = "WRITING"
    VALIDATION = "VALIDATION"
    SEO = "SEO"
    FACT_CHECK = "FACT_CHECK"
    FINALIZATION = "FINALIZATION"
    PUBLISHED = "PUBLISHED"

    def is_terminal(self) -> bool:
        return self == WorkflowStage.PUBLISHED

    def is_failure(self) -> bool:
        return False  # terminal failure is a separate status

    @property
    def display_name(self) -> str:
        return self.value.title()


STAGE_ORDER: list[WorkflowStage] = [
    WorkflowStage.INIT,
    WorkflowStage.PLANNING,
    WorkflowStage.RESEARCH,
    WorkflowStage.SYNTHESIS,
    WorkflowStage.OUTLINING,
    WorkflowStage.WRITING,
    WorkflowStage.VALIDATION,
    WorkflowStage.SEO,
    WorkflowStage.FACT_CHECK,
    WorkflowStage.FINALIZATION,
    WorkflowStage.PUBLISHED,
]


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class StageResult(BaseModel):
    stage: WorkflowStage
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    checkpoint_id: Optional[str] = None


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        return self in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED)


class WorkflowRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str
    content_item_id: Optional[str] = None
    correlation_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_stage: WorkflowStage = WorkflowStage.INIT
    stage_results: Dict[str, StageResult] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        d = super().model_dump(**kwargs)
        d["status"] = self.status.value
        d["current_stage"] = self.current_stage.value
        d["stage_results"] = {
            k: v.model_dump() for k, v in self.stage_results.items()
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowRun":
        if isinstance(data.get("status"), str):
            data["status"] = WorkflowStatus(data["status"])
        if isinstance(data.get("current_stage"), str):
            data["current_stage"] = WorkflowStage(data["current_stage"])
        if isinstance(data.get("stage_results"), dict):
            parsed: Dict[str, StageResult] = {}
            for k, v in data["stage_results"].items():
                if isinstance(v, dict):
                    if "stage" in v and isinstance(v["stage"], str):
                        v["stage"] = WorkflowStage(v["stage"])
                    if "status" in v and isinstance(v["status"], str):
                        v["status"] = StageStatus(v["status"])
                    parsed[k] = StageResult(**v)
            data["stage_results"] = parsed
        return cls(**data)


STAGE_TRANSITIONS: Dict[WorkflowStage, set[WorkflowStage]] = {
    WorkflowStage.INIT: {WorkflowStage.PLANNING},
    WorkflowStage.PLANNING: {WorkflowStage.RESEARCH},
    WorkflowStage.RESEARCH: {WorkflowStage.SYNTHESIS},
    WorkflowStage.SYNTHESIS: {WorkflowStage.OUTLINING},
    WorkflowStage.OUTLINING: {WorkflowStage.WRITING},
    WorkflowStage.WRITING: {WorkflowStage.VALIDATION},
    WorkflowStage.VALIDATION: {WorkflowStage.SEO, WorkflowStage.FACT_CHECK},
    WorkflowStage.SEO: {WorkflowStage.FACT_CHECK, WorkflowStage.FINALIZATION},
    WorkflowStage.FACT_CHECK: {WorkflowStage.FINALIZATION},
    WorkflowStage.FINALIZATION: {WorkflowStage.PUBLISHED},
    WorkflowStage.PUBLISHED: set(),
}


def get_next_stage(current: WorkflowStage) -> Optional[WorkflowStage]:
    """Get the primary (first) next stage in the linear workflow."""
    allowed = STAGE_TRANSITIONS.get(current, set())
    ordered = [s for s in STAGE_ORDER if s in allowed]
    return ordered[0] if ordered else None


def can_transition_stage(from_stage: WorkflowStage, to_stage: WorkflowStage) -> bool:
    allowed = STAGE_TRANSITIONS.get(from_stage, set())
    return to_stage in allowed


def validate_transition(from_stage: WorkflowStage, to_stage: WorkflowStage) -> None:
    allowed = STAGE_TRANSITIONS.get(from_stage, set())
    if to_stage not in allowed:
        raise ValueError(
            f"Cannot transition from '{from_stage.value}' to '{to_stage.value}'. "
            f"Allowed targets from '{from_stage.value}': "
            f"{[s.value for s in allowed] if allowed else '<terminal>'}"
        )


STAGE_TIMEOUT_SECONDS: Dict[WorkflowStage, int] = {
    WorkflowStage.INIT: 30,
    WorkflowStage.PLANNING: 120,
    WorkflowStage.RESEARCH: 300,
    WorkflowStage.SYNTHESIS: 120,
    WorkflowStage.OUTLINING: 120,
    WorkflowStage.WRITING: 600,
    WorkflowStage.VALIDATION: 60,
    WorkflowStage.SEO: 60,
    WorkflowStage.FACT_CHECK: 120,
    WorkflowStage.FINALIZATION: 60,
    WorkflowStage.PUBLISHED: 10,
}


STAGE_MAX_RETRIES: Dict[WorkflowStage, int] = {
    WorkflowStage.INIT: 1,
    WorkflowStage.PLANNING: 3,
    WorkflowStage.RESEARCH: 3,
    WorkflowStage.SYNTHESIS: 3,
    WorkflowStage.OUTLINING: 3,
    WorkflowStage.WRITING: 3,
    WorkflowStage.VALIDATION: 2,
    WorkflowStage.SEO: 2,
    WorkflowStage.FACT_CHECK: 3,
    WorkflowStage.FINALIZATION: 2,
    WorkflowStage.PUBLISHED: 0,
}

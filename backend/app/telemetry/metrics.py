from __future__ import annotations

import time
from typing import Any
from dataclasses import dataclass, field


@dataclass
class StageTelemetry:
    stage: str = ""
    agent: str = ""
    duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retry_count: int = 0
    validation_score: float = 0.0
    error: str = ""
    success: bool = True


@dataclass
class WorkflowTelemetry:
    workflow_id: str = ""
    project_id: str = ""
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_retries: int = 0
    stages: list[StageTelemetry] = field(default_factory=list)
    final_quality_score: float = 0.0
    completed: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "total_tokens": self.total_tokens,
            "total_retries": self.total_retries,
            "stages": [
                {k: round(v, 2) if isinstance(v, float) else v for k, v in s.__dict__.items()}
                for s in self.stages
            ],
            "final_quality_score": round(self.final_quality_score, 3),
            "completed": self.completed,
            "error": self.error,
        }


class TelemetryCollector:
    def __init__(self):
        self._workflows: dict[str, WorkflowTelemetry] = {}

    def create(self, workflow_id: str, project_id: str) -> WorkflowTelemetry:
        t = WorkflowTelemetry(workflow_id=workflow_id, project_id=project_id)
        self._workflows[workflow_id] = t
        return t

    def add_stage(
        self,
        workflow_id: str,
        stage: str,
        agent: str,
        duration_ms: float,
        tokens: int = 0,
        retries: int = 0,
        validation_score: float = 0.0,
        error: str = "",
        success: bool = True,
    ) -> None:
        t = self._workflows.get(workflow_id)
        if not t:
            return
        st = StageTelemetry(
            stage=stage,
            agent=agent,
            duration_ms=duration_ms,
            total_tokens=tokens,
            retry_count=retries,
            validation_score=validation_score,
            error=error,
            success=success,
        )
        t.stages.append(st)
        t.total_duration_ms += duration_ms
        t.total_tokens += tokens
        t.total_retries += retries

    def set_final_quality(self, workflow_id: str, score: float) -> None:
        t = self._workflows.get(workflow_id)
        if t:
            t.final_quality_score = score

    def set_completed(self, workflow_id: str, error: str = "") -> None:
        t = self._workflows.get(workflow_id)
        if t:
            t.completed = True
            t.error = error

    def get_telemetry(self, workflow_id: str) -> WorkflowTelemetry | None:
        return self._workflows.get(workflow_id)


_telemetry = TelemetryCollector()


def get_telemetry_collector() -> TelemetryCollector:
    return _telemetry

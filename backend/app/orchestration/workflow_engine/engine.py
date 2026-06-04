from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.orchestration.state_machine.workflow_stage import (
    WorkflowStage,
    StageStatus,
    validate_transition,
    is_terminal,
    stage_display_name,
)
from app.log_config.logger import get_logger

logger = get_logger(__name__)


class WorkflowState(BaseModel):
    workflow_id: str = ""
    project_id: str = ""
    current_stage: WorkflowStage = WorkflowStage.INIT
    stage_statuses: dict[str, str] = {}
    stage_durations: dict[str, float] = {}
    errors: list[dict] = []
    retry_counts: dict[str, int] = {}
    metadata: dict = {}
    started_at: str = ""
    completed_at: str = ""
    is_complete: bool = False
    is_failed: bool = False



@dataclass
class StageTransition:
    stage: WorkflowStage
    from_stage: Optional[WorkflowStage]
    status: StageStatus
    timestamp: float
    duration_ms: float = 0.0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class WorkflowEngine:
    def __init__(self):
        self._workflows: dict[str, WorkflowState] = {}
        self._transitions: dict[str, list[StageTransition]] = {}
        self.logger = get_logger(self.__class__.__name__)

    def create_workflow(self, project_id: str) -> WorkflowState:
        workflow_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        state = WorkflowState(
            workflow_id=workflow_id,
            project_id=project_id,
            started_at=now,
            stage_statuses={WorkflowStage.INIT.value: StageStatus.PENDING.value},
        )
        self._workflows[workflow_id] = state
        self._transitions[workflow_id] = [
            StageTransition(
                stage=WorkflowStage.INIT,
                from_stage=None,
                status=StageStatus.PENDING,
                timestamp=time.time(),
            ),
        ]
        self.logger.info("Workflow created", extra={"workflow_id": workflow_id, "project_id": project_id})
        return state

    def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        return self._workflows.get(workflow_id)

    def get_transitions(self, workflow_id: str) -> list[StageTransition]:
        return self._transitions.get(workflow_id, [])

    def transition_to(
        self,
        workflow_id: str,
        next_stage: WorkflowStage,
        status: StageStatus = StageStatus.STARTED,
        error: Optional[str] = None,
        metadata: dict | None = None,
    ) -> WorkflowState:
        state = self._workflows.get(workflow_id)
        if not state:
            raise ValueError(f"Workflow {workflow_id} not found")

        current = state.current_stage

        if status in (StageStatus.COMPLETED, StageStatus.FAILED):
            try:
                validate_transition(current, next_stage)
            except ValueError as e:
                self.logger.warning("Invalid stage transition", extra={
                    "from": current.value, "to": next_stage.value, "error": str(e),
                })
                raise

        prev_stage = state.current_stage
        state.current_stage = next_stage
        state.stage_statuses[next_stage.value] = status.value

        if error:
            state.errors.append({"stage": next_stage.value, "error": error})

        if next_stage in (WorkflowStage.PUBLISHED,):
            state.is_complete = True
            state.completed_at = datetime.utcnow().isoformat()

        if next_stage == WorkflowStage.FAILED:
            state.is_failed = True
            state.completed_at = datetime.utcnow().isoformat()

        transition = StageTransition(
            stage=next_stage,
            from_stage=prev_stage if prev_stage != next_stage else None,
            status=status,
            timestamp=time.time(),
            error=error,
            metadata=metadata or {},
        )
        self._transitions[workflow_id].append(transition)

        self.logger.info(
            "Workflow transition: %s -> %s [%s]",
            stage_display_name(prev_stage) if prev_stage else "NONE",
            stage_display_name(next_stage),
            status.value,
            extra={
                "workflow_id": workflow_id,
                "from": prev_stage.value if prev_stage else "",
                "to": next_stage.value,
                "status": status.value,
                "error": error,
            },
        )

        return state

    def mark_stage_duration(self, workflow_id: str, stage: WorkflowStage, duration_ms: float) -> None:
        state = self._workflows.get(workflow_id)
        if state:
            state.stage_durations[stage.value] = duration_ms

    def increment_retry(self, workflow_id: str, stage: WorkflowStage) -> int:
        state = self._workflows.get(workflow_id)
        if state:
            key = stage.value
            state.retry_counts[key] = state.retry_counts.get(key, 0) + 1
            return state.retry_counts[key]
        return 0

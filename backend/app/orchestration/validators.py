from __future__ import annotations

import logging
from typing import Any

from app.orchestration.stages import (
    STAGE_ORDER,
    StageResult,
    StageStatus,
    WorkflowRun,
    WorkflowStage,
    validate_transition,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class StageValidator:
    """Validates workflow state before and after stage execution."""

    async def validate_pre_stage(
        self, run: WorkflowRun, stage: WorkflowStage,
    ) -> list[str]:
        """Run pre-execution validations. Returns list of warnings."""
        warnings: list[str] = []

        if run.status.is_terminal():
            raise ValidationError(
                f"Cannot execute stage '{stage.value}' on terminal workflow (status={run.status.value})"
            )

        if stage == WorkflowStage.INIT:
            pass
        elif stage == WorkflowStage.PLANNING:
            if not run.metadata.get("content_brief"):
                warnings.append("No content_brief found in metadata")
        elif stage == WorkflowStage.RESEARCH:
            if not run.stage_results.get(WorkflowStage.PLANNING.value):
                warnings.append("PLANNING stage has no recorded result")
        elif stage == WorkflowStage.WRITING:
            outline = run.stage_results.get(WorkflowStage.OUTLINING.value)
            if outline and outline.status != StageStatus.COMPLETED:
                warnings.append("OUTLINING stage not completed")
        elif stage == WorkflowStage.PUBLISHED:
            final = run.stage_results.get(WorkflowStage.FINALIZATION.value)
            if final and final.status != StageStatus.COMPLETED:
                warnings.append("FINALIZATION stage not completed")

        return warnings

    async def validate_post_stage(
        self, run: WorkflowRun, stage: WorkflowStage, result: StageResult,
    ) -> list[str]:
        """Run post-execution validations. Returns list of warnings."""
        warnings: list[str] = []

        if result.status == StageStatus.COMPLETED and not result.output:
            warnings.append(f"Stage '{stage.value}' completed with empty output")

        return warnings

    async def validate_transition(
        self, from_stage: WorkflowStage, to_stage: WorkflowStage,
    ) -> None:
        """Validate that a stage transition is allowed."""
        validate_transition(from_stage, to_stage)

    async def validate_workflow_completion(self, run: WorkflowRun) -> list[str]:
        """Validate that the workflow has completed all required stages."""
        warnings: list[str] = []

        for stage in STAGE_ORDER:
            result = run.stage_results.get(stage.value)
            if not result:
                warnings.append(f"Stage '{stage.value}' has no recorded result")
            elif result.status != StageStatus.COMPLETED:
                if stage == WorkflowStage.PUBLISHED:
                    warnings.append(f"Stage '{stage.value}' was not completed")

        return warnings


class WorkflowInputValidator:
    """Validates workflow creation inputs."""

    def validate_create(
        self,
        workspace_id: str,
        correlation_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        errors: list[str] = []
        if not workspace_id or not workspace_id.strip():
            errors.append("workspace_id is required")
        if not correlation_id or not correlation_id.strip():
            errors.append("correlation_id is required")
        return errors

    def validate_resume(
        self, run: WorkflowRun | None,
    ) -> list[str]:
        errors: list[str] = []
        if run is None:
            errors.append("Workflow run not found")
            return errors
        if run.status.is_terminal():
            errors.append(f"Cannot resume workflow in terminal state: {run.status.value}")
        return errors

    def validate_cancel(
        self, run: WorkflowRun | None,
    ) -> list[str]:
        errors: list[str] = []
        if run is None:
            errors.append("Workflow run not found")
            return errors
        if run.status.is_terminal():
            errors.append(f"Cannot cancel workflow in terminal state: {run.status.value}")
        return errors

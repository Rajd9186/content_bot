from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

import pytest

from app.orchestration.validators import (
    StageValidator, WorkflowInputValidator, ValidationError,
)
from app.orchestration.stages import (
    WorkflowStage, WorkflowStatus, WorkflowRun, StageResult, StageStatus,
)


class TestStageValidator:
    @pytest.fixture
    def validator(self) -> StageValidator:
        return StageValidator()

    async def test_validate_pre_stage_on_terminal_workflow_raises(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
        )
        with pytest.raises(ValidationError, match="terminal"):
            await validator.validate_pre_stage(run, WorkflowStage.INIT)

    async def test_validate_pre_stage_returns_warnings(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.RUNNING,
        )
        warnings = await validator.validate_pre_stage(run, WorkflowStage.PLANNING)
        assert len(warnings) > 0
        assert any("content_brief" in w for w in warnings)

    async def test_validate_post_stage_empty_output_warning(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        result = StageResult(stage=WorkflowStage.INIT, status=StageStatus.COMPLETED)
        warnings = await validator.validate_post_stage(run, WorkflowStage.INIT, result)
        assert len(warnings) > 0
        assert any("empty output" in w for w in warnings)

    async def test_validate_post_stage_with_output_no_warning(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        result = StageResult(
            stage=WorkflowStage.INIT,
            status=StageStatus.COMPLETED,
            output={"key": "value"},
        )
        warnings = await validator.validate_post_stage(run, WorkflowStage.INIT, result)
        assert len(warnings) == 0

    async def test_validate_transition_valid(self, validator: StageValidator) -> None:
        await validator.validate_transition(WorkflowStage.INIT, WorkflowStage.PLANNING)

    async def test_validate_transition_invalid_raises(self, validator: StageValidator) -> None:
        with pytest.raises(ValueError):
            await validator.validate_transition(WorkflowStage.INIT, WorkflowStage.PUBLISHED)

    async def test_validate_workflow_completion_all_complete(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        for stage in [
            WorkflowStage.INIT, WorkflowStage.PLANNING, WorkflowStage.RESEARCH,
            WorkflowStage.SYNTHESIS, WorkflowStage.OUTLINING, WorkflowStage.WRITING,
            WorkflowStage.VALIDATION, WorkflowStage.SEO, WorkflowStage.FACT_CHECK,
            WorkflowStage.FINALIZATION, WorkflowStage.PUBLISHED,
        ]:
            run.stage_results[stage.value] = StageResult(
                stage=stage, status=StageStatus.COMPLETED,
            )
        warnings = await validator.validate_workflow_completion(run)
        assert len(warnings) == 0

    async def test_validate_workflow_completion_missing_stages(
        self, validator: StageValidator,
    ) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        run.stage_results["INIT"] = StageResult(
            stage=WorkflowStage.INIT, status=StageStatus.COMPLETED,
        )
        warnings = await validator.validate_workflow_completion(run)
        assert len(warnings) > 1


class TestWorkflowInputValidator:
    @pytest.fixture
    def validator(self) -> WorkflowInputValidator:
        return WorkflowInputValidator()

    def test_validate_create_valid(self, validator: WorkflowInputValidator) -> None:
        errors = validator.validate_create("ws-1", "corr-1")
        assert errors == []

    def test_validate_create_missing_workspace(self, validator: WorkflowInputValidator) -> None:
        errors = validator.validate_create("", "corr-1")
        assert len(errors) > 0
        assert any("workspace_id" in e for e in errors)

    def test_validate_create_missing_correlation(self, validator: WorkflowInputValidator) -> None:
        errors = validator.validate_create("ws-1", "")
        assert len(errors) > 0
        assert any("correlation_id" in e for e in errors)

    def test_validate_resume_valid(self, validator: WorkflowInputValidator) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        errors = validator.validate_resume(run)
        assert errors == []

    def test_validate_resume_none(self, validator: WorkflowInputValidator) -> None:
        errors = validator.validate_resume(None)
        assert len(errors) > 0
        assert any("not found" in e for e in errors)

    def test_validate_resume_terminal(self, validator: WorkflowInputValidator) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
        )
        errors = validator.validate_resume(run)
        assert len(errors) > 0
        assert any("terminal" in e for e in errors)

    def test_validate_cancel_valid(self, validator: WorkflowInputValidator) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        errors = validator.validate_cancel(run)
        assert errors == []

    def test_validate_cancel_terminal(self, validator: WorkflowInputValidator) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
        )
        errors = validator.validate_cancel(run)
        assert len(errors) > 0
        assert any("terminal" in e for e in errors)

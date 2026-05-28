from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.orchestration.stages import (
    WorkflowStage, WorkflowStatus, WorkflowRun, StageResult, StageStatus,
    STAGE_ORDER, STAGE_TRANSITIONS, can_transition_stage,
    get_next_stage, validate_transition,
)


class TestWorkflowStage:
    def test_terminal_stage(self) -> None:
        assert WorkflowStage.PUBLISHED.is_terminal() is True
        assert WorkflowStage.INIT.is_terminal() is False

    def test_all_stages_in_order(self) -> None:
        expected = [
            "INIT", "PLANNING", "RESEARCH", "SYNTHESIS",
            "OUTLINING", "WRITING", "VALIDATION", "SEO",
            "FACT_CHECK", "FINALIZATION", "PUBLISHED",
        ]
        assert [s.value for s in STAGE_ORDER] == expected

    def test_display_name(self) -> None:
        assert WorkflowStage.INIT.display_name == "Init"
        assert WorkflowStage.FACT_CHECK.display_name == "Fact_Check"


class TestTransitionRules:
    def test_init_transitions(self) -> None:
        allowed = STAGE_TRANSITIONS[WorkflowStage.INIT]
        assert WorkflowStage.PLANNING in allowed
        assert WorkflowStage.RESEARCH not in allowed

    def test_validation_has_branching(self) -> None:
        allowed = STAGE_TRANSITIONS[WorkflowStage.VALIDATION]
        assert WorkflowStage.SEO in allowed
        assert WorkflowStage.FACT_CHECK in allowed

    def test_seo_has_branching(self) -> None:
        allowed = STAGE_TRANSITIONS[WorkflowStage.SEO]
        assert WorkflowStage.FACT_CHECK in allowed
        assert WorkflowStage.FINALIZATION in allowed

    def test_published_is_terminal(self) -> None:
        assert STAGE_TRANSITIONS[WorkflowStage.PUBLISHED] == set()

    def test_linear_transitions(self) -> None:
        for i, stage in enumerate(STAGE_ORDER[:-1]):
            next_stage = STAGE_ORDER[i + 1]
            assert can_transition_stage(stage, next_stage), (
                f"{stage.value} should transition to {next_stage.value}"
            )


class TestGetNextStage:
    def test_next_of_init_is_planning(self) -> None:
        assert get_next_stage(WorkflowStage.INIT) == WorkflowStage.PLANNING

    def test_next_of_writing_is_validation(self) -> None:
        assert get_next_stage(WorkflowStage.WRITING) == WorkflowStage.VALIDATION

    def test_next_of_seo_prefers_fact_check(self) -> None:
        assert get_next_stage(WorkflowStage.SEO) == WorkflowStage.FACT_CHECK

    def test_next_of_terminal_is_none(self) -> None:
        assert get_next_stage(WorkflowStage.PUBLISHED) is None


class TestValidateTransition:
    def test_valid_transition(self) -> None:
        validate_transition(WorkflowStage.INIT, WorkflowStage.PLANNING)

    def test_invalid_transition_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot transition"):
            validate_transition(WorkflowStage.INIT, WorkflowStage.PUBLISHED)

    def test_branching_transition(self) -> None:
        validate_transition(WorkflowStage.VALIDATION, WorkflowStage.SEO)
        validate_transition(WorkflowStage.VALIDATION, WorkflowStage.FACT_CHECK)

    def test_terminal_has_no_transitions(self) -> None:
        with pytest.raises(ValueError, match="<terminal>"):
            validate_transition(WorkflowStage.PUBLISHED, WorkflowStage.INIT)


class TestWorkflowRun:
    def test_create_defaults(self) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
        )
        assert run.status == WorkflowStatus.PENDING
        assert run.current_stage == WorkflowStage.INIT
        assert run.stage_results == {}
        assert run.id is not None
        assert run.version == 1

    def test_serialization_roundtrip(self) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.RUNNING,
            current_stage=WorkflowStage.RESEARCH,
            stage_results={
                WorkflowStage.INIT.value: StageResult(
                    stage=WorkflowStage.INIT,
                    status=StageStatus.COMPLETED,
                    output={"result": "ok"},
                ),
                WorkflowStage.PLANNING.value: StageResult(
                    stage=WorkflowStage.PLANNING,
                    status=StageStatus.COMPLETED,
                ),
            },
        )

        dumped = run.model_dump(mode="json")
        loaded = WorkflowRun.from_dict(json.loads(json.dumps(dumped)))

        assert loaded.id == run.id
        assert loaded.workspace_id == "ws-1"
        assert loaded.status == WorkflowStatus.RUNNING
        assert loaded.current_stage == WorkflowStage.RESEARCH
        assert loaded.stage_results[WorkflowStage.INIT.value].status == StageStatus.COMPLETED
        assert loaded.stage_results[WorkflowStage.INIT.value].output["result"] == "ok"

    def test_terminal_status_checks(self) -> None:
        assert WorkflowStatus.COMPLETED.is_terminal() is True
        assert WorkflowStatus.FAILED.is_terminal() is True
        assert WorkflowStatus.CANCELLED.is_terminal() is True
        assert WorkflowStatus.RUNNING.is_terminal() is False
        assert WorkflowStatus.PENDING.is_terminal() is False

    def test_from_dict_with_string_enums(self) -> None:
        data = {
            "id": str(uuid4()),
            "workspace_id": "ws-1",
            "correlation_id": "corr-1",
            "status": "running",
            "current_stage": "VALIDATION",
            "stage_results": {
                "INIT": {
                    "stage": "INIT",
                    "status": "completed",
                    "output": {},
                },
            },
            "metadata": {},
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        run = WorkflowRun.from_dict(data)
        assert run.status == WorkflowStatus.RUNNING
        assert run.current_stage == WorkflowStage.VALIDATION
        assert run.stage_results["INIT"].status == StageStatus.COMPLETED

    def test_stage_result_defaults(self) -> None:
        result = StageResult(stage=WorkflowStage.INIT)
        assert result.status == StageStatus.PENDING
        assert result.retry_count == 0
        assert result.output == {}
        assert result.error is None

    def test_stage_timestamps(self) -> None:
        result = StageResult(
            stage=WorkflowStage.PLANNING,
            status=StageStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at

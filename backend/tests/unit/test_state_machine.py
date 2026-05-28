from __future__ import annotations

import pytest

from app.domains.workflow.state_machine import (
    WorkflowStatus, StateMachine, TRANSITION_RULES,
)


class TestWorkflowStatus:
    def test_terminal_statuses(self) -> None:
        assert WorkflowStatus.COMPLETED.is_terminal is True
        assert WorkflowStatus.FAILED.is_terminal is True
        assert WorkflowStatus.CANCELED.is_terminal is True
        assert WorkflowStatus.DRAFT.is_terminal is False

    def test_active_statuses(self) -> None:
        assert WorkflowStatus.QUEUED.is_active is True
        assert WorkflowStatus.VALIDATING.is_active is True
        assert WorkflowStatus.PROCESSING.is_active is True
        assert WorkflowStatus.RETRYING.is_active is True
        assert WorkflowStatus.COMPLETED.is_active is False


class TestTransitionRules:
    def test_draft_can_submit(self) -> None:
        assert WorkflowStatus.QUEUED in TRANSITION_RULES[WorkflowStatus.DRAFT]

    def test_draft_can_cancel(self) -> None:
        assert WorkflowStatus.CANCELED in TRANSITION_RULES[WorkflowStatus.DRAFT]

    def test_terminal_has_no_transitions(self) -> None:
        assert TRANSITION_RULES[WorkflowStatus.COMPLETED] == set()
        assert TRANSITION_RULES[WorkflowStatus.CANCELED] == set()

    def test_failed_can_retry(self) -> None:
        assert WorkflowStatus.QUEUED in TRANSITION_RULES[WorkflowStatus.FAILED]

    def test_processing_can_complete_or_fail(self) -> None:
        allowed = TRANSITION_RULES[WorkflowStatus.PROCESSING]
        assert WorkflowStatus.COMPLETED in allowed
        assert WorkflowStatus.FAILED in allowed
        assert WorkflowStatus.RETRYING in allowed
        assert WorkflowStatus.PROCESSING in allowed


class TestStateMachine:
    @pytest.fixture
    def sm(self) -> StateMachine:
        return StateMachine()

    async def test_valid_transition(self, sm: StateMachine) -> None:
        ok, reason = await sm.can_transition(
            "DRAFT", "QUEUED", "job-1", "ws-1",
        )
        assert ok is True
        assert reason == ""

    async def test_invalid_transition(self, sm: StateMachine) -> None:
        ok, reason = await sm.can_transition(
            "DRAFT", "COMPLETED", "job-1", "ws-1",
        )
        assert ok is False
        assert "not allowed" in reason

    async def test_transition_from_terminal_fails(self, sm: StateMachine) -> None:
        ok, reason = await sm.can_transition(
            "COMPLETED", "PROCESSING", "job-1", "ws-1",
        )
        assert ok is False

    async def test_guard_blocks_transition(self, sm: StateMachine) -> None:
        async def guard(job_id: str, workspace_id: str,
                        to_status: str, context: dict) -> bool:
            return context.get("authorized") is True

        sm.add_guard("DRAFT", "QUEUED", guard)

        ok, reason = await sm.can_transition(
            "DRAFT", "QUEUED", "job-1", "ws-1", {},
        )
        assert ok is False

        ok, reason = await sm.can_transition(
            "DRAFT", "QUEUED", "job-1", "ws-1",
            {"authorized": True},
        )
        assert ok is True

    async def test_side_effect_runs_on_transition(self, sm: StateMachine) -> None:
        effects: list[str] = []

        async def effect(job_id: str, workspace_id: str,
                         to_status: str, context: dict) -> None:
            effects.append(f"{job_id}->{to_status}")

        sm.add_side_effect("DRAFT", "QUEUED", effect)
        await sm.transition("DRAFT", "QUEUED", "job-1", "ws-1")
        assert effects == ["job-1->QUEUED"]

    async def test_transition_raises_on_invalid(self, sm: StateMachine) -> None:
        with pytest.raises(ValueError, match="Transition rejected"):
            await sm.transition("DRAFT", "COMPLETED", "job-1", "ws-1")

    async def test_full_workflow(self, sm: StateMachine) -> None:
        path = [
            ("DRAFT", "QUEUED"),
            ("QUEUED", "VALIDATING"),
            ("VALIDATING", "PROCESSING"),
            ("PROCESSING", "COMPLETED"),
        ]
        for from_s, to_s in path:
            ok, reason = await sm.can_transition(from_s, to_s, "job-1", "ws-1")
            assert ok is True, f"{from_s}->{to_s}: {reason}"
            await sm.transition(from_s, to_s, "job-1", "ws-1")

    async def test_retry_then_process(self, sm: StateMachine) -> None:
        path = [
            ("DRAFT", "QUEUED"),
            ("QUEUED", "VALIDATING"),
            ("VALIDATING", "PROCESSING"),
            ("PROCESSING", "RETRYING"),
            ("RETRYING", "PROCESSING"),
            ("PROCESSING", "COMPLETED"),
        ]
        for from_s, to_s in path:
            ok, reason = await sm.can_transition(from_s, to_s, "job-1", "ws-1")
            assert ok is True, f"{from_s}->{to_s}: {reason}"

    async def test_singleton_available(self, sm: StateMachine) -> None:
        from app.domains.workflow.state_machine import workflow_state_machine
        assert workflow_state_machine is not None

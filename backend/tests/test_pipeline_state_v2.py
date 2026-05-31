from __future__ import annotations

from app.pipeline.state import (
    NodeResult,
    NodeStatus,
    PipelineState,
    HumanReview,
    ReviewAction,
)


class TestPipelineStateHasFailures:
    def test_no_failures_initially(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        assert state.has_failures() is False

    def test_no_failures_with_success_nodes(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        assert state.has_failures() is False

    def test_has_failures_with_failed_node(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.FAILED, error="Oops"))
        assert state.has_failures() is True

    def test_has_failures_with_errors_list(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.errors.append("Something went wrong")
        assert state.has_failures() is True

    def test_empty_errors_list_not_truthy(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        assert state.errors == []
        assert state.has_failures() is False

    def test_mixed_success_and_failed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        state.add_node_result("planner", NodeResult(node="planner", status=NodeStatus.FAILED, error="Failed"))
        assert state.has_failures() is True


class TestPipelineStateAllNodesCompleted:
    def test_no_nodes_completed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        assert state.all_nodes_completed() is True

    def test_all_success_nodes(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        state.add_node_result("planner", NodeResult(node="planner", status=NodeStatus.SUCCESS))
        assert state.all_nodes_completed() is True

    def test_skipped_nodes_count_as_completed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        state.add_node_result("planner", NodeResult(node="planner", status=NodeStatus.SKIPPED))
        assert state.all_nodes_completed() is True

    def test_failed_node_not_completed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        state.add_node_result("planner", NodeResult(node="planner", status=NodeStatus.FAILED))
        assert state.all_nodes_completed() is False

    def test_pending_node_not_completed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.PENDING))
        assert state.all_nodes_completed() is False

    def test_running_node_not_completed(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.RUNNING))
        assert state.all_nodes_completed() is False


class TestNodeStatusEnum:
    def test_no_completed_status(self) -> None:
        status_values = [s.value for s in NodeStatus]
        assert "completed" not in status_values
        assert "success" in status_values

    def test_all_expected_statuses(self) -> None:
        expected = {"pending", "running", "success", "failed", "skipped", "retrying", "paused", "cancelled"}
        actual = {s.value for s in NodeStatus}
        assert actual == expected


class TestPipelineStateErrorPropagation:
    def test_errors_list_tracks_failures(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.errors.append("research: API timeout")
        state.errors.append("writer: Content too short")
        assert len(state.errors) == 2
        assert state.has_failures() is True

    def test_errors_cleared_on_new_state(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        assert state.errors == []
        state2 = PipelineState(workflow_id="test2", topic="AI")
        assert state2.errors == []


class TestPipelineStateSerialization:
    def test_model_dump_includes_all_fields(self) -> None:
        state = PipelineState(
            workflow_id="test-123",
            topic="AI Technology",
            audience="developers",
            tone="technical",
        )
        data = state.model_dump()
        assert data["workflow_id"] == "test-123"
        assert data["topic"] == "AI Technology"

    def test_round_trip_serialization(self) -> None:
        state = PipelineState(workflow_id="test", topic="AI")
        state.add_node_result("research", NodeResult(node="research", status=NodeStatus.SUCCESS))
        data = state.model_dump()
        restored = PipelineState(**data)
        assert restored.workflow_id == state.workflow_id
        assert restored.has_failures() == state.has_failures()

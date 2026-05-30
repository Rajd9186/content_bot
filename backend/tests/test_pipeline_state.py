from __future__ import annotations

from app.pipeline.state import (
    NodeResult,
    NodeStatus,
    PipelineState,
    HumanReview,
    ReviewAction,
)


def test_pipeline_state_creation() -> None:
    state = PipelineState(
        workflow_id="test-123",
        workspace_id="ws-1",
        correlation_id="corr-1",
        topic="AI Technology",
    )
    assert state.workflow_id == "test-123"
    assert state.topic == "AI Technology"
    assert state.current_node == "research"
    assert state.node_results == {}
    assert state.errors == []


def test_pipeline_state_add_node_result() -> None:
    state = PipelineState(workflow_id="test-123", topic="Test")
    result = NodeResult(
        node="research",
        status=NodeStatus.SUCCESS,
        output={"summary": "Research complete"},
    )
    state.add_node_result("research", result)
    assert "research" in state.node_results
    assert state.node_results["research"].status == NodeStatus.SUCCESS


def test_pipeline_state_all_nodes_completed() -> None:
    state = PipelineState(workflow_id="test-123", topic="Test")
    state.add_node_result(
        "research", NodeResult(node="research", status=NodeStatus.SUCCESS)
    )
    assert state.all_nodes_completed() is True
    state.add_node_result(
        "planner", NodeResult(node="planner", status=NodeStatus.FAILED)
    )
    assert state.all_nodes_completed() is False


def test_pipeline_state_has_failures() -> None:
    state = PipelineState(workflow_id="test-123", topic="Test")
    assert state.has_failures() is False
    state.add_node_result(
        "research", NodeResult(node="research", status=NodeStatus.SUCCESS)
    )
    assert state.has_failures() is False
    state.add_node_result(
        "planner", NodeResult(node="planner", status=NodeStatus.FAILED, error="Failed")
    )
    assert state.has_failures() is True


def test_pipeline_state_human_review() -> None:
    state = PipelineState(workflow_id="test-123", topic="Test")
    assert state.human_review is None
    state.human_review = HumanReview(
        reviewer_id="user-1",
        action=ReviewAction.APPROVED,
        comments="Looks good",
    )
    assert state.human_review is not None
    assert state.human_review.action == ReviewAction.APPROVED


def test_pipeline_state_get_node_result() -> None:
    state = PipelineState(workflow_id="test-123", topic="Test")
    assert state.get_node_result("nonexistent") is None
    state.add_node_result(
        "research", NodeResult(node="research", status=NodeStatus.SUCCESS)
    )
    assert state.get_node_result("research") is not None


def test_pipeline_state_serialization() -> None:
    state = PipelineState(
        workflow_id="test-123",
        topic="AI Technology",
        audience="developers",
        tone="technical",
    )
    data = state.model_dump()
    assert data["workflow_id"] == "test-123"
    assert data["topic"] == "AI Technology"
    assert data["audience"] == "developers"
    assert data["tone"] == "technical"
    restored = PipelineState(**data)
    assert restored.workflow_id == state.workflow_id
    assert restored.topic == state.topic


def test_node_result_defaults() -> None:
    result = NodeResult(node="test")
    assert result.status == NodeStatus.PENDING
    assert result.output == {}
    assert result.error is None
    assert result.retry_count == 0
    assert result.tokens_used == 0
    assert result.latency_ms == 0.0


def test_human_review_rejected() -> None:
    review = HumanReview(
        reviewer_id="user-1",
        action=ReviewAction.REJECTED,
        comments="Not suitable for publication",
    )
    assert review.action == ReviewAction.REJECTED
    assert "Not suitable" in review.comments

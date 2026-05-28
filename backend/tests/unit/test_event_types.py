from app.events.event_types import (
    JobStartedEvent, JobCompletedEvent, JobFailedEvent,
    JobStageChangedEvent, AgentExecutionFailedEvent,
    EVENT_REGISTRY,
)


def test_event_type_registry() -> None:
    assert "workflow.job.started.v1" in EVENT_REGISTRY
    assert "workflow.job.completed.v1" in EVENT_REGISTRY
    assert "workflow.job.failed.v1" in EVENT_REGISTRY
    assert "workflow.stage.changed.v1" in EVENT_REGISTRY
    assert "agent.execution.failed.v2" in EVENT_REGISTRY


def test_job_started_event_defaults() -> None:
    event = JobStartedEvent(
        correlation_id="test-corr-id",
        subject="job-123",
        data={"workspace_id": "ws-1"},
    )
    assert event.type == "workflow.job.started.v1"
    assert event.source == "/domains/workflow"
    assert event.subject == "job-123"
    assert event.data["workspace_id"] == "ws-1"
    assert event.specversion == "1.0"
    assert event.id is not None


def test_job_completed_event() -> None:
    event = JobCompletedEvent(
        correlation_id="test-corr-id",
        subject="job-456",
    )
    assert event.type == "workflow.job.completed.v1"
    assert event.subject == "job-456"


def test_job_failed_event_with_error() -> None:
    event = JobFailedEvent(
        correlation_id="test-corr-id",
        subject="job-789",
        data={"error_code": "TIMEOUT", "error_message": "Agent timed out"},
    )
    assert event.type == "workflow.job.failed.v1"
    assert event.data["error_code"] == "TIMEOUT"
    assert event.data["error_message"] == "Agent timed out"


def test_stage_changed_event() -> None:
    event = JobStageChangedEvent(
        correlation_id="test-corr-id",
        subject="job-101",
        data={"from_stage": "VALIDATING", "to_stage": "PROCESSING"},
    )
    assert event.data["from_stage"] == "VALIDATING"
    assert event.data["to_stage"] == "PROCESSING"


def test_agent_execution_failed_v2() -> None:
    event = AgentExecutionFailedEvent(
        correlation_id="test-corr-id",
        subject="exec-001",
        data={"error_code": "RATE_LIMITED", "retryable": True},
    )
    assert event.type == "agent.execution.failed.v2"
    assert event.data["retryable"] is True


def test_event_to_stored_dict() -> None:
    event = JobStartedEvent(
        correlation_id="corr-1",
        subject="job-1",
        data={"workspace_id": "ws-1"},
        metadata={"origin": "test"},
    )
    stored = event.to_stored_dict()
    assert stored["event_type"] == "workflow.job.started.v1"
    assert stored["correlation_id"] == "corr-1"
    assert stored["aggregate_id"] == "job-1"
    assert stored["aggregate_type"] == "workflow"
    assert stored["data"]["workspace_id"] == "ws-1"
    assert stored["event_version"] == 1

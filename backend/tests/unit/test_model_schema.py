from __future__ import annotations

from app.db.models.workflow import (
    WorkflowJob, WorkflowStep, ExecutionLog, DeadLetterJob,
)
from app.db.models.content import ContentItem, ContentVersion, GeneratedContent
from app.db.models.agent import AgentConfig, AgentExecution, AgentCall
from app.db.models.event import StoredEvent
from app.db.models.telemetry import RetryRecord, TelemetryMetric, Checkpoint


def test_workflow_job_fields() -> None:
    assert hasattr(WorkflowJob, "id")
    assert hasattr(WorkflowJob, "workspace_id")
    assert hasattr(WorkflowJob, "status")
    assert hasattr(WorkflowJob, "version")
    assert hasattr(WorkflowJob, "correlation_id")
    assert hasattr(WorkflowJob, "created_by")
    assert hasattr(WorkflowJob, "steps")
    assert hasattr(WorkflowJob, "logs")


def test_workflow_step_fields() -> None:
    assert hasattr(WorkflowStep, "id")
    assert hasattr(WorkflowStep, "job_id")
    assert hasattr(WorkflowStep, "step_type")
    assert hasattr(WorkflowStep, "status")


def test_execution_log_fields() -> None:
    assert hasattr(ExecutionLog, "id")
    assert hasattr(ExecutionLog, "job_id")
    assert hasattr(ExecutionLog, "from_status")
    assert hasattr(ExecutionLog, "to_status")
    assert hasattr(ExecutionLog, "transition")
    assert hasattr(ExecutionLog, "triggered_by")


def test_dead_letter_job_fields() -> None:
    assert hasattr(DeadLetterJob, "id")
    assert hasattr(DeadLetterJob, "original_job_id")
    assert hasattr(DeadLetterJob, "error_code")
    assert hasattr(DeadLetterJob, "retry_attempts")


def test_content_item_fields() -> None:
    assert hasattr(ContentItem, "id")
    assert hasattr(ContentItem, "workspace_id")
    assert hasattr(ContentItem, "title")
    assert hasattr(ContentItem, "slug")
    assert hasattr(ContentItem, "status")
    assert hasattr(ContentItem, "version")


def test_content_version_fields() -> None:
    assert hasattr(ContentVersion, "id")
    assert hasattr(ContentVersion, "content_item_id")
    assert hasattr(ContentVersion, "version")
    assert hasattr(ContentVersion, "title")


def test_generated_content_fields() -> None:
    assert hasattr(GeneratedContent, "id")
    assert hasattr(GeneratedContent, "content_item_id")
    assert hasattr(GeneratedContent, "content_type")
    assert hasattr(GeneratedContent, "content")


def test_agent_config_fields() -> None:
    assert hasattr(AgentConfig, "id")
    assert hasattr(AgentConfig, "workspace_id")
    assert hasattr(AgentConfig, "name")
    assert hasattr(AgentConfig, "agent_type")
    assert hasattr(AgentConfig, "model")


def test_agent_execution_fields() -> None:
    assert hasattr(AgentExecution, "id")
    assert hasattr(AgentExecution, "job_id")
    assert hasattr(AgentExecution, "status")
    assert hasattr(AgentExecution, "tokens_used")
    assert hasattr(AgentExecution, "correlation_id")


def test_agent_call_fields() -> None:
    assert hasattr(AgentCall, "id")
    assert hasattr(AgentCall, "agent_execution_id")
    assert hasattr(AgentCall, "provider")
    assert hasattr(AgentCall, "model")
    assert hasattr(AgentCall, "total_tokens")
    assert hasattr(AgentCall, "latency_ms")


def test_stored_event_fields() -> None:
    assert hasattr(StoredEvent, "id")
    assert hasattr(StoredEvent, "sequence_number")
    assert hasattr(StoredEvent, "published")
    assert hasattr(StoredEvent, "event_type")
    assert hasattr(StoredEvent, "event_version")
    assert hasattr(StoredEvent, "source")
    assert hasattr(StoredEvent, "subject")
    assert hasattr(StoredEvent, "correlation_id")
    assert hasattr(StoredEvent, "aggregate_id")
    assert hasattr(StoredEvent, "aggregate_type")


def test_retry_record_fields() -> None:
    assert hasattr(RetryRecord, "id")
    assert hasattr(RetryRecord, "target_type")
    assert hasattr(RetryRecord, "target_id")
    assert hasattr(RetryRecord, "attempt_number")
    assert hasattr(RetryRecord, "status")


def test_telemetry_metric_fields() -> None:
    assert hasattr(TelemetryMetric, "id")
    assert hasattr(TelemetryMetric, "metric_name")
    assert hasattr(TelemetryMetric, "metric_type")
    assert hasattr(TelemetryMetric, "value")


def test_checkpoint_fields() -> None:
    assert hasattr(Checkpoint, "id")
    assert hasattr(Checkpoint, "aggregate_id")
    assert hasattr(Checkpoint, "aggregate_type")
    assert hasattr(Checkpoint, "checkpoint_type")
    assert hasattr(Checkpoint, "state")
    assert hasattr(Checkpoint, "version")

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventVersion(str, Enum):
    V1 = "1"


class EventSource(str, Enum):
    CONTENT_DOMAIN = "/domains/content"
    ANALYSIS_DOMAIN = "/domains/analysis"
    WORKFLOW_DOMAIN = "/domains/workflow"
    IDENTITY_DOMAIN = "/domains/identity"
    AGENT_DOMAIN = "/domains/agent"
    SYSTEM = "/system"


class BaseEvent(BaseModel):
    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str
    type: str
    subject: Optional[str] = None
    time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str
    datacontenttype: str = "application/json"
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_stored_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.type,
            "event_version": 1,
            "source": self.source,
            "subject": self.subject,
            "data": self.data,
            "extra_metadata": {
                "specversion": self.specversion,
                "time": self.time,
                **self.metadata,
            },
            "correlation_id": self.correlation_id,
            "aggregate_id": self.subject,
            "aggregate_type": self.source.split("/")[-1] if "/" in self.source else self.source,
        }


# ── Workflow Events ───────────────────────────────────
class JobStartedEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.job.started.v1"
    subject: Optional[str] = None  # job_id


class JobStageChangedEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.stage.changed.v1"
    subject: Optional[str] = None  # job_id
    data: dict[str, Any] = Field(default_factory=lambda: {
        "from_stage": "",
        "to_stage": "",
    })


class JobCompletedEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.job.completed.v1"
    subject: Optional[str] = None  # job_id


class JobFailedEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.job.failed.v1"
    subject: Optional[str] = None  # job_id
    data: dict[str, Any] = Field(default_factory=lambda: {
        "error_code": "",
        "error_message": "",
    })


class JobCanceledEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.job.canceled.v1"
    subject: Optional[str] = None  # job_id


class JobRetriedEvent(BaseEvent):
    source: str = EventSource.WORKFLOW_DOMAIN.value
    type: str = "workflow.job.retried.v1"
    subject: Optional[str] = None  # job_id
    data: dict[str, Any] = Field(default_factory=lambda: {
        "attempt": 1,
        "max_retries": 3,
    })


# ── Content Events ────────────────────────────────────
class ArticleCreatedEvent(BaseEvent):
    source: str = EventSource.CONTENT_DOMAIN.value
    type: str = "content.article.created.v1"
    subject: Optional[str] = None  # article_id


class ArticleUpdatedEvent(BaseEvent):
    source: str = EventSource.CONTENT_DOMAIN.value
    type: str = "content.article.updated.v1"
    subject: Optional[str] = None  # article_id


# ── Analysis Events ───────────────────────────────────
class InsightGeneratedEvent(BaseEvent):
    source: str = EventSource.ANALYSIS_DOMAIN.value
    type: str = "analysis.insight.generated.v1"
    subject: Optional[str] = None  # insight_id


# ── Agent Events ──────────────────────────────────────
class AgentExecutionStartedEvent(BaseEvent):
    source: str = EventSource.AGENT_DOMAIN.value
    type: str = "agent.execution.started.v1"
    subject: Optional[str] = None  # execution_id


class AgentExecutionCompletedEvent(BaseEvent):
    source: str = EventSource.AGENT_DOMAIN.value
    type: str = "agent.execution.completed.v1"
    subject: Optional[str] = None  # execution_id


class AgentExecutionFailedEvent(BaseEvent):
    source: str = EventSource.AGENT_DOMAIN.value
    type: str = "agent.execution.failed.v2"
    subject: Optional[str] = None  # execution_id
    data: dict[str, Any] = Field(default_factory=lambda: {
        "error_code": "",
        "retryable": True,
    })


# ── System Events ─────────────────────────────────────
class SystemErrorEvent(BaseEvent):
    source: str = EventSource.SYSTEM.value
    type: str = "system.error.v1"
    subject: Optional[str] = None


# Event registry for deserialization
EVENT_REGISTRY: dict[str, type[BaseEvent]] = {
    "workflow.job.started.v1": JobStartedEvent,
    "workflow.stage.changed.v1": JobStageChangedEvent,
    "workflow.job.completed.v1": JobCompletedEvent,
    "workflow.job.failed.v1": JobFailedEvent,
    "workflow.job.canceled.v1": JobCanceledEvent,
    "workflow.job.retried.v1": JobRetriedEvent,
    "content.article.created.v1": ArticleCreatedEvent,
    "content.article.updated.v1": ArticleUpdatedEvent,
    "analysis.insight.generated.v1": InsightGeneratedEvent,
    "agent.execution.started.v1": AgentExecutionStartedEvent,
    "agent.execution.completed.v1": AgentExecutionCompletedEvent,
    "agent.execution.failed.v2": AgentExecutionFailedEvent,
    "system.error.v1": SystemErrorEvent,
}

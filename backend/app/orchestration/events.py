from __future__ import annotations

from app.events.event_types import EVENT_REGISTRY, BaseEvent


class OrchestrationEvent(BaseEvent):
    """Base for all orchestration events."""


class WorkflowStartedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.workflow.started.v1"
    subject: str = ""  # workflow_id


class WorkflowStageStartedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.stage.started.v1"
    subject: str = ""  # workflow_id
    data: dict = {"stage": "", "workspace_id": ""}


class WorkflowStageCompletedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.stage.completed.v1"
    subject: str = ""  # workflow_id
    data: dict = {"stage": "", "workspace_id": ""}


class WorkflowStageFailedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.stage.failed.v1"
    subject: str = ""  # workflow_id
    data: dict = {"stage": "", "error": "", "error_code": "", "workspace_id": ""}


class WorkflowCompletedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.workflow.completed.v1"
    subject: str = ""  # workflow_id
    data: dict = {"workspace_id": ""}


class WorkflowFailedEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.workflow.failed.v1"
    subject: str = ""  # workflow_id
    data: dict = {"stage": "", "error": "", "workspace_id": ""}


class WorkflowCancelledEvent(OrchestrationEvent):
    source: str = "/system/orchestration"
    type: str = "orchestration.workflow.cancelled.v1"
    subject: str = ""  # workflow_id
    data: dict = {"stage": "", "reason": "", "workspace_id": ""}


ORCHESTRATION_EVENTS: dict[str, type[OrchestrationEvent]] = {
    "orchestration.workflow.started.v1": WorkflowStartedEvent,
    "orchestration.stage.started.v1": WorkflowStageStartedEvent,
    "orchestration.stage.completed.v1": WorkflowStageCompletedEvent,
    "orchestration.stage.failed.v1": WorkflowStageFailedEvent,
    "orchestration.workflow.completed.v1": WorkflowCompletedEvent,
    "orchestration.workflow.failed.v1": WorkflowFailedEvent,
    "orchestration.workflow.cancelled.v1": WorkflowCancelledEvent,
}

# Auto-register with global EVENT_REGISTRY at import time
EVENT_REGISTRY.update(ORCHESTRATION_EVENTS)

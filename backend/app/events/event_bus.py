from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field

from app.log_config.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowEvent:
    event_id: str = ""
    workflow_id: str = ""
    project_id: str = ""
    event_type: str = ""
    agent_name: str = ""
    status: str = ""
    message: str = ""
    progress_percent: float = 0.0
    payload: dict = field(default_factory=dict)
    timestamp: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "workflow_id": self.workflow_id,
            "project_id": self.project_id,
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "status": self.status,
            "message": self.message,
            "progress_percent": self.progress_percent,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }

    def to_sse_dict(self) -> dict:
        return {
            "id": self.event_id,
            "event": self.event_type,
            "data": json.dumps({
                "workflow_id": self.workflow_id,
                "project_id": self.project_id,
                "event_type": self.event_type,
                "agent_name": self.agent_name,
                "status": self.status,
                "message": self.message,
                "progress_percent": self.progress_percent,
                "payload": self.payload,
                "timestamp": self.timestamp,
            }),
        }


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._persisted_events: dict[str, list[WorkflowEvent]] = {}
        self.logger = get_logger(self.__class__.__name__)

    def subscribe(self, workflow_id: str) -> asyncio.Queue:
        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = []
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[workflow_id].append(queue)

        if workflow_id in self._persisted_events:
            for event in self._persisted_events[workflow_id]:
                queue.put_nowait(event)

        return queue

    def unsubscribe(self, workflow_id: str, queue: asyncio.Queue) -> None:
        if workflow_id in self._subscribers:
            self._subscribers[workflow_id] = [
                q for q in self._subscribers[workflow_id] if q is not queue
            ]

    async def publish(self, event: WorkflowEvent) -> None:
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        if not event.timestamp:
            event.timestamp = datetime.utcnow().isoformat()

        wf_id = event.workflow_id
        if wf_id not in self._persisted_events:
            self._persisted_events[wf_id] = []
        self._persisted_events[wf_id].append(event)

        max_events = 500
        if len(self._persisted_events[wf_id]) > max_events:
            self._persisted_events[wf_id] = self._persisted_events[wf_id][-max_events:]

        if wf_id in self._subscribers:
            dead_queues = []
            for queue in self._subscribers[wf_id]:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_queues.append(queue)
            for q in dead_queues:
                self._subscribers[wf_id].remove(q)

        self.logger.debug("Event published", extra={
            "workflow_id": wf_id,
            "event_type": event.event_type,
            "agent": event.agent_name,
            "status": event.status,
        })

    def get_events(self, workflow_id: str, after_event_id: Optional[str] = None) -> list[WorkflowEvent]:
        events = self._persisted_events.get(workflow_id, [])
        if after_event_id:
            found = False
            for i, ev in enumerate(events):
                if ev.event_id == after_event_id:
                    return events[i + 1:]
            return []
        return events

    async def publish_event(
        self,
        workflow_id: str,
        event_type: str,
        agent_name: str = "",
        status: str = "",
        message: str = "",
        progress_percent: float = 0.0,
        payload: dict | None = None,
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            event_type=event_type,
            agent_name=agent_name,
            status=status,
            message=message,
            progress_percent=progress_percent,
            payload=payload or {},
            timestamp=datetime.utcnow().isoformat(),
        )
        await self.publish(event)
        return event


event_bus = EventBus()

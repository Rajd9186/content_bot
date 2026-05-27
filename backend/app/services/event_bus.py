"""Event bus for real-time workflow events over SSE.

Persists events to PostgreSQL and broadcasts to active SSE subscribers.
Supports reconnect recovery by replaying recent events from the database.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, desc

from app.database import async_session_factory
from app.models.chat import WorkflowEventRecord
from app.schemas.sse_event import SSEEvent

logger = logging.getLogger("app.event_bus")

# Maximum events to keep per subscriber queue before dropping oldest
_MAX_QUEUE_SIZE = 512


class WorkflowEvent:
    """Structured workflow event for SSE consumption."""

    def __init__(
        self,
        workflow_id: str | UUID,
        event_type: str,
        agent_name: str = "",
        status: str = "running",
        message: str = "",
        progress_percent: float = 0.0,
        payload: dict | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ):
        self._event = SSEEvent(
            id=str(event_id) if event_id else "",
            workflow_id=str(workflow_id),
            type=event_type,
            agent=agent_name,
            status=status,
            message=message,
            progress=progress_percent,
            payload=payload or {},
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        )

    def to_sse_dict(self) -> dict:
        return self._event.to_sse_dict()


class WorkflowEventBus:
    """Async event bus that persists events to DB and broadcasts to SSE subscribers."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        logger.info("WorkflowEventBus initialized (DB + in-memory broadcast)")

    # ──────────────────────────────────────────────
    # Publish — persist + broadcast
    # ──────────────────────────────────────────────

    async def publish(
        self,
        workflow_id: str | UUID,
        event_type: str,
        agent_name: str = "",
        status: str = "running",
        message: str = "",
        progress_percent: float = 0.0,
        payload: dict | None = None,
        project_id: str | UUID | None = None,
    ) -> str:
        """Persist an event to the database and broadcast to active subscribers.

        Returns the event id string (generated UUID if DB persistence fails).
        """
        wid = str(workflow_id)
        event_id = str(uuid.uuid4())

        resolved_project_id: UUID | None = None
        if project_id is not None:
            try:
                resolved_project_id = UUID(str(project_id))
            except (ValueError, TypeError):
                pass
        elif payload and "project_id" in payload:
            try:
                resolved_project_id = UUID(str(payload["project_id"]))
            except (ValueError, TypeError):
                pass

        if resolved_project_id is None:
            logger.error(
                "Cannot persist event without project_id. "
                "Callers must provide project_id either as parameter or in payload. "
                "workflow_id=%s event_type=%s",
                wid, event_type,
            )
            sse_event = WorkflowEvent(
                workflow_id=wid, event_type=event_type,
                agent_name=agent_name, status=status,
                message=message, progress_percent=progress_percent,
                payload=payload, event_id=event_id,
            )
            await self._broadcast(wid, sse_event)
            return event_id

        try:
            async with async_session_factory() as session:
                db_event = WorkflowEventRecord(
                    workflow_id=UUID(wid),
                    project_id=resolved_project_id,
                    event_type=event_type,
                    agent_name=agent_name,
                    status=status,
                    message=message,
                    progress_percent=progress_percent,
                    payload_json=payload,
                )
                session.add(db_event)
                await session.commit()
                event_id = str(db_event.id)
                logger.debug("Persisted event %s: %s/%s", event_id, event_type, status)
        except Exception as e:
            logger.warning("Failed to persist workflow event, using generated UUID: %s", e)

        sse_event = WorkflowEvent(
            workflow_id=wid,
            event_type=event_type,
            agent_name=agent_name,
            status=status,
            message=message,
            progress_percent=progress_percent,
            payload=payload,
            event_id=event_id,
        )
        await self._broadcast(wid, sse_event)

        extra = {
            "workflow_id": wid,
            "agent": agent_name,
            "event": event_type,
            "status": status,
            "progress": progress_percent,
        }
        if payload:
            extra["payload"] = payload
        logger.info("[%s] %s/%s: %s (%.0f%%)", event_type, agent_name, status, message, progress_percent, extra=extra)

        return event_id

    async def _broadcast(self, workflow_id: str, event: WorkflowEvent) -> None:
        """Push event to all subscriber queues for this workflow."""
        async with self._lock:
            queues = list(self._subscribers.get(workflow_id, []))
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest to keep queue moving
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except asyncio.QueueEmpty:
                    pass
                logger.warning("Queue full for workflow %s, dropped oldest event", workflow_id)

    # ──────────────────────────────────────────────
    # Subscribe / Unsubscribe (for SSE connections)
    # ──────────────────────────────────────────────

    async def subscribe(self, workflow_id: str) -> asyncio.Queue:
        """Create a subscriber queue for a workflow. Returns the queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=_MAX_QUEUE_SIZE)
        async with self._lock:
            if workflow_id not in self._subscribers:
                self._subscribers[workflow_id] = []
            self._subscribers[workflow_id].append(q)
        logger.debug(
            "SSE subscriber added for workflow %s (total: %d)",
            workflow_id, len(self._subscribers[workflow_id]),
        )
        return q

    async def unsubscribe(self, workflow_id: str, q: asyncio.Queue) -> None:
        """Remove a subscriber queue."""
        async with self._lock:
            if workflow_id in self._subscribers:
                self._subscribers[workflow_id] = [sq for sq in self._subscribers[workflow_id] if sq is not q]
                if not self._subscribers[workflow_id]:
                    del self._subscribers[workflow_id]
        logger.debug(
            "SSE subscriber removed for workflow %s (remaining: %d)",
            workflow_id, len(self._subscribers.get(workflow_id, [])),
        )

    # ──────────────────────────────────────────────
    # Reconnect recovery — replay recent events
    # ──────────────────────────────────────────────

    async def get_recent_events(
        self,
        workflow_id: str | UUID,
        after_event_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Fetch recent events from the database for reconnect recovery.

        If after_event_id is provided, returns events after that one.
        Otherwise returns the most recent `limit` events.
        """
        wid = UUID(str(workflow_id)) if isinstance(workflow_id, str) else workflow_id
        try:
            async with async_session_factory() as session:
                stmt = (
                    select(WorkflowEventRecord)
                    .where(WorkflowEventRecord.workflow_id == wid)
                )

                if after_event_id:
                    subq = select(WorkflowEventRecord.created_at).where(
                        WorkflowEventRecord.id == UUID(after_event_id)
                    ).limit(1).scalar_subquery()
                    stmt = stmt.where(WorkflowEventRecord.created_at > subq)

                stmt = stmt.order_by(WorkflowEventRecord.created_at.asc()).limit(limit)
                result = await session.execute(stmt)
                events = result.scalars().all()
                return [e.to_sse_dict() for e in events]
        except Exception as e:
            logger.warning("Failed to fetch recent events: %s", e)
            return []


# Singleton instance
event_bus = WorkflowEventBus()

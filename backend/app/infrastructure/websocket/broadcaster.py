from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.events.event_types import BaseEvent
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.websocket.manager import WSMessage, connection_manager

logger = logging.getLogger(__name__)


class EventBroadcaster:
    async def broadcast_event(
        self,
        event: BaseEvent,
        workspace_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        message = WSMessage(
            type=event.type,
            data=event.data,
            correlation_id=event.correlation_id,
            timestamp=datetime.now(UTC).isoformat(),
        )

        if workspace_id:
            await connection_manager.broadcast_to_workspace(workspace_id, message)
        if user_id:
            await connection_manager.broadcast_to_user(user_id, message)

        try:
            await redis_client.publish_json(
                f"events:{workspace_id or 'global'}",
                message.model_dump(),
            )
        except Exception as e:
            logger.warning("Redis pub failed for event %s: %s", event.type, e)

    async def broadcast_stage_change(
        self,
        job_id: str,
        from_stage: str,
        to_stage: str,
        correlation_id: str,
        workspace_id: str,
    ) -> None:
        message = WSMessage(
            type="workflow.stage.changed",
            data={
                "job_id": job_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
            },
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await connection_manager.broadcast_to_workspace(workspace_id, message)

    async def broadcast_job_completed(
        self,
        job_id: str,
        status: str,
        correlation_id: str,
        workspace_id: str,
    ) -> None:
        message = WSMessage(
            type="workflow.job.completed",
            data={
                "job_id": job_id,
                "status": status,
            },
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC).isoformat(),
        )
        await connection_manager.broadcast_to_workspace(workspace_id, message)


event_broadcaster = EventBroadcaster()

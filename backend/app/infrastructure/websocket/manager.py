from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import WebSocket
from pydantic import BaseModel, Field

from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)


class WSMessage(BaseModel):
    type: str
    data: dict[str, Any] = {}
    correlation_id: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


GLOBAL_EVENTS_CHANNEL = "events:outbox:*"


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._user_connections: dict[str, set[WebSocket]] = {}
        self._redis_listener_task: Optional[asyncio.Task[None]] = None

    async def connect(self, websocket: WebSocket, workspace_id: str,
                      user_id: Optional[str] = None) -> None:
        await websocket.accept()

        if workspace_id not in self._connections:
            self._connections[workspace_id] = set()
        self._connections[workspace_id].add(websocket)

        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(websocket)

        logger.info(
            "WebSocket connected: workspace=%s user=%s",
            workspace_id, user_id or "anonymous",
        )

    async def disconnect(self, websocket: WebSocket, workspace_id: str,
                         user_id: Optional[str] = None) -> None:
        if workspace_id in self._connections:
            self._connections[workspace_id].discard(websocket)
            if not self._connections[workspace_id]:
                del self._connections[workspace_id]

        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(websocket)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        logger.info(
            "WebSocket disconnected: workspace=%s user=%s",
            workspace_id, user_id or "anonymous",
        )

    async def broadcast_to_workspace(
        self, workspace_id: str, message: WSMessage,
    ) -> None:
        connections = self._connections.get(workspace_id, set())
        payload = message.model_dump_json()
        dead = set()
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            connections.discard(ws)

    async def broadcast_to_user(
        self, user_id: str, message: WSMessage,
    ) -> None:
        connections = self._user_connections.get(user_id, set())
        payload = message.model_dump_json()
        dead = set()
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            connections.discard(ws)

    async def broadcast_all(self, message: WSMessage) -> None:
        payload = message.model_dump_json()
        for workspace_connections in self._connections.values():
            dead = set()
            for ws in workspace_connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                workspace_connections.discard(ws)

    async def start_redis_listener(self, channel_pattern: str = GLOBAL_EVENTS_CHANNEL) -> None:
        """Subscribe to Redis pub/sub for cross-node event broadcasting."""
        if self._redis_listener_task is not None and not self._redis_listener_task.done():
            logger.warning("Redis listener already running")
            return

        self._redis_listener_task = asyncio.create_task(
            self._redis_listen_loop(channel_pattern),
        )
        logger.info("Redis WS listener subscribed to %s", channel_pattern)

    async def stop_redis_listener(self) -> None:
        if self._redis_listener_task and not self._redis_listener_task.done():
            self._redis_listener_task.cancel()
            try:
                await self._redis_listener_task
            except asyncio.CancelledError:
                pass
            self._redis_listener_task = None
            logger.info("Redis WS listener stopped")

    async def _redis_listen_loop(self, channel_pattern: str) -> None:
        try:
            pubsub = redis_client.pubsub_client.pubsub()
            await pubsub.psubscribe(channel_pattern)
            logger.info("Redis listener subscribed to pattern: %s", channel_pattern)

            async for message in pubsub.listen():
                if message.get("type") not in ("pmessage", "message"):
                    continue

                try:
                    data = json.loads(message["data"])
                    ws_message = WSMessage(
                        type=data.get("type", "unknown"),
                        data=data.get("data", {}),
                        correlation_id=data.get("correlation_id"),
                    )
                    aggregate_type = data.get("aggregate_type", "")
                    await self._broadcast_cross_node(ws_message, aggregate_type)
                except Exception as e:
                    logger.warning("Redis listener parse error: %s", e)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Redis listener error: %s", e)

    async def _broadcast_cross_node(
        self, message: WSMessage, aggregate_type: str,
    ) -> None:
        workspace_id = message.data.get("workspace_id")
        if workspace_id and workspace_id in self._connections:
            await self.broadcast_to_workspace(workspace_id, message)
        elif aggregate_type == "workflow" or not workspace_id:
            await self.broadcast_all(message)

    @property
    def active_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


connection_manager = ConnectionManager()

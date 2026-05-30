from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Set

from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)

PIPELINE_EVENTS_CHANNEL = "pipeline:events"
PIPELINE_WORKFLOW_PREFIX = "pipeline:events:"
SSE_HEARTBEAT_INTERVAL = 15
SSE_MAX_CONNECTIONS = 200


class SSEConnectionManager:
    """Manages SSE connections and bridges Redis pub/sub to HTTP SSE streams.

    Design:
    - Clients connect via HTTP GET and receive a StreamingResponse
    - A single Redis pub/sub listener broadcasts to all connected clients
    - Heartbeat messages keep connections alive
    - Connection tracking via asyncio queues per workflow_id
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Set[asyncio.Queue[str]]] = {}
        self._total_connections = 0
        self._listener_task: Optional[asyncio.Task[None]] = None
        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        if redis_client._client is None:
            logger.warning("Redis not connected, SSE manager starting without Redis listener")
            self._running = True
            return
        self._running = True
        self._listener_task = asyncio.create_task(self._redis_listener())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("SSE connection manager started")

    async def stop(self) -> None:
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        for workflow_id, queues in self._connections.items():
            for q in queues:
                await q.put(": disconnected\n\n")
        self._connections.clear()
        self._total_connections = 0
        logger.info("SSE connection manager stopped")

    def add_connection(self, workflow_id: str) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=256)
        if workflow_id not in self._connections:
            self._connections[workflow_id] = set()
        self._connections[workflow_id].add(queue)
        self._total_connections += 1
        logger.debug(
            "SSE client connected: workflow=%s total=%d",
            workflow_id, len(self._connections[workflow_id]),
        )
        return queue

    def remove_connection(self, workflow_id: str, queue: asyncio.Queue[str]) -> None:
        if workflow_id in self._connections:
            self._connections[workflow_id].discard(queue)
            self._total_connections = max(0, self._total_connections - 1)
            if not self._connections[workflow_id]:
                del self._connections[workflow_id]

    async def broadcast(self, workflow_id: str, event_type: str, data: dict[str, Any]) -> None:
        message = json.dumps({"type": event_type, "workflow_id": workflow_id, **data})
        sse_data = f"data: {message}\n\n"

        if redis_client._client is not None:
            try:
                await redis_client.publish_json(
                    PIPELINE_WORKFLOW_PREFIX + workflow_id, {
                        "type": event_type,
                        "workflow_id": workflow_id,
                        **data,
                    }
                )
            except Exception as e:
                logger.warning("Redis publish failed for SSE: %s", e)

        queues = self._connections.get(workflow_id, set())
        dead_queues: list[asyncio.Queue[str]] = []
        for q in queues:
            try:
                q.put_nowait(sse_data)
            except asyncio.QueueFull:
                dead_queues.append(q)
        for q in dead_queues:
            self.remove_connection(workflow_id, q)

    async def broadcast_pipeline_event(
        self,
        workflow_id: str,
        event_type: str,
        node: str = "",
        status: str = "",
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
        **extra: Any,
    ) -> None:
        data: dict[str, Any] = {}
        if node:
            data["node"] = node
        if status:
            data["status"] = status
        if tokens_used:
            data["tokens_used"] = tokens_used
        if latency_ms:
            data["latency_ms"] = latency_ms
        if error:
            data["error"] = error
        data.update(extra)
        await self.broadcast(workflow_id, event_type, data)

    @property
    def total_connections(self) -> int:
        return self._total_connections

    @property
    def active_workflows(self) -> int:
        return len(self._connections)

    async def _redis_listener(self) -> None:
        try:
            pubsub = await redis_client.subscribe(PIPELINE_EVENTS_CHANNEL)
            try:
                async for message in pubsub.listen():
                    if not self._running:
                        break
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                        workflow_id = payload.get("workflow_id", "")
                        if workflow_id and workflow_id in self._connections:
                            await self.broadcast(
                                workflow_id,
                                payload.get("type", "unknown"),
                                {k: v for k, v in payload.items() if k not in ("type", "workflow_id")},
                            )
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning("SSE Redis message parse error: %s", e)
            finally:
                await pubsub.unsubscribe(PIPELINE_EVENTS_CHANNEL)
                await pubsub.close()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("SSE Redis listener error: %s", e)

    async def _heartbeat_loop(self) -> None:
        try:
            while self._running:
                await asyncio.sleep(SSE_HEARTBEAT_INTERVAL)
                for workflow_id, queues in list(self._connections.items()):
                    heartbeat = f": heartbeat {int(time.time())}\n\n"
                    dead: list[asyncio.Queue[str]] = []
                    for q in queues:
                        try:
                            q.put_nowait(heartbeat)
                        except asyncio.QueueFull:
                            dead.append(q)
                    for q in dead:
                        self.remove_connection(workflow_id, q)
        except asyncio.CancelledError:
            pass


sse_manager = SSEConnectionManager()

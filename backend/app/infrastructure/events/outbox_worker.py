from __future__ import annotations

import asyncio
import contextlib
import logging

from app.core.database import async_session_factory
from app.events.event_bus import event_bus
from app.events.event_types import EVENT_REGISTRY
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.models.event import StoredEvent
from app.infrastructure.repositories.event_repository import EventRepository
from app.infrastructure.websocket.manager import WSMessage

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 50
LOCK_TTL_MS = 10000
OUTBOX_CHANNEL = "events:outbox"


class OutboxWorker:
    """Transactional Outbox background worker.

    Polls stored_events for unpublished events and publishes them to:
    1. In-memory EventBus subscribers
    2. Redis Pub/Sub for cross-node broadcast
    3. Local WebSocket connections

    Uses Redlock to ensure only one node processes the outbox at a time.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("OutboxWorker started (poll interval=%ss, batch size=%s)",
                     POLL_INTERVAL_SECONDS, BATCH_SIZE)

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("OutboxWorker stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error("OutboxWorker poll error: %s", e)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _process_batch(self) -> None:
        lock = None
        try:
            lock = await redis_client.acquire_lock(
                "outbox:lock", ttl_ms=LOCK_TTL_MS,
            )
            if lock is None:
                return
        except Exception:
            return

        try:
            async with async_session_factory() as session:
                repo = EventRepository(session)
                events = await repo.get_unpublished(limit=BATCH_SIZE)
                if not events:
                    return

                for stored in events:
                    try:
                        await self._publish_event(stored, repo)
                    except Exception as e:
                        logger.error(
                            "Failed to publish event %s (%s): %s",
                            stored.id, stored.event_type, e,
                        )
        finally:
            with contextlib.suppress(Exception):
                await lock.release()

    async def _publish_event(
        self, stored: StoredEvent, repo: EventRepository,
    ) -> None:
        event_class = EVENT_REGISTRY.get(stored.event_type)
        if not event_class:
            logger.warning("Unknown event type in outbox: %s", stored.event_type)
            await repo.mark_published(stored.id)
            return

        try:
            event = event_class(
                id=stored.id,
                source=stored.source,
                type=stored.event_type,
                subject=stored.subject or "",
                correlation_id=stored.correlation_id,
                data=stored.data or {},
                extra_metadata=stored.extra_metadata or {},
            )
        except Exception as e:
            logger.warning("Failed to reconstruct event %s: %s", stored.id, e)
            await repo.mark_published(stored.id)
            return

        await event_bus.publish(event)

        try:
            WSMessage(
                type=event.type,
                data=event.data,
                correlation_id=event.correlation_id,
            )
            aggregate_type = stored.aggregate_type or ""
            await redis_client.publish_json(
                f"{OUTBOX_CHANNEL}:{aggregate_type}",
                {
                    "type": event.type,
                    "data": event.data,
                    "correlation_id": event.correlation_id,
                    "subject": event.subject,
                    "aggregate_type": aggregate_type,
                    "aggregate_id": stored.aggregate_id,
                },
            )
        except Exception as e:
            logger.warning("Redis publish failed for event %s: %s", stored.id, e)

        await repo.mark_published(stored.id)
        logger.debug("Outbox event published: %s [%s]", stored.id, stored.event_type)


outbox_worker = OutboxWorker()

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, Optional, TYPE_CHECKING

from app.infrastructure.models.event import StoredEvent
from app.events.event_types import BaseEvent, EVENT_REGISTRY

if TYPE_CHECKING:
    from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

EventHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]


class EventStore:
    async def save(self, uow: UnitOfWork, event: BaseEvent) -> StoredEvent:
        stored = StoredEvent(**event.to_stored_dict())
        await uow.events.store(stored)
        logger.info(
            "Event stored: %s [%s]",
            event.type, event.subject,
            extra={"correlation_id": event.correlation_id},
        )
        return stored

    async def get_by_type(
        self, uow: UnitOfWork, event_type: str, limit: int = 100, offset: int = 0,
    ) -> list[StoredEvent]:
        return await uow.events.get_by_type(event_type, limit, offset)

    async def get_by_aggregate(
        self, uow: UnitOfWork, aggregate_type: str, aggregate_id: str, limit: int = 100,
    ) -> list[StoredEvent]:
        return await uow.events.get_by_aggregate(aggregate_type, aggregate_id, limit)

    async def get_by_correlation_id(
        self, uow: UnitOfWork, correlation_id: str, limit: int = 100,
    ) -> list[StoredEvent]:
        return await uow.events.get_by_correlation_id(correlation_id, limit)

    async def replay(
        self,
        uow: UnitOfWork,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[BaseEvent]:
        if event_type:
            stored_events = await self.get_by_type(uow, event_type, limit)
        elif aggregate_type and aggregate_id:
            stored_events = await self.get_by_aggregate(
                uow, aggregate_type, aggregate_id, limit
            )
        else:
            return []

        deserialized: list[BaseEvent] = []
        for se in stored_events:
            event_class = EVENT_REGISTRY.get(se.event_type)
            if event_class:
                try:
                    event = event_class(
                        id=se.id,
                        source=se.source,
                        type=se.event_type,
                        subject=se.subject,
                        correlation_id=se.correlation_id,
                        data=se.data or {},
                        extra_metadata=se.extra_metadata or {},
                    )
                    deserialized.append(event)
                except Exception as e:
                    logger.warning("Failed to deserialize event %s: %s", se.id, e)
            else:
                logger.warning("Unknown event type: %s", se.event_type)

        return deserialized


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug("Subscribed to %s: %s", event_type, handler.__name__)

    def subscribe_all(self, handler: EventHandler) -> None:
        for event_type in EVENT_REGISTRY:
            self.subscribe(event_type, handler)

    async def publish(self, event: BaseEvent) -> None:
        handlers = self._subscribers.get(event.type, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "Handler %s failed for %s: %s",
                    handler.__name__, event.type, e,
                    extra={"correlation_id": event.correlation_id},
                )

    async def publish_and_store(
        self, uow: UnitOfWork, event: BaseEvent,
    ) -> StoredEvent:
        stored = await EventStore().save(uow, event)
        await self.publish(event)
        return stored

    async def store_atomic(
        self, uow: UnitOfWork, event: BaseEvent,
    ) -> StoredEvent:
        """Atomically store an event within a UOW transaction."""
        stored = await EventStore().save(uow, event)
        return stored

    def clear(self) -> None:
        self._subscribers.clear()


event_bus = EventBus()
event_store = EventStore()

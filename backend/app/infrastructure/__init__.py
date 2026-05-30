from app.infrastructure.models.base import Base, JSONBColumn, utcnow
from app.infrastructure.models.event import StoredEvent
from app.infrastructure.models.telemetry import RetryRecord, TelemetryMetric, Checkpoint
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.websocket.manager import ConnectionManager, WSMessage, connection_manager
from app.infrastructure.websocket.broadcaster import EventBroadcaster, event_broadcaster
from app.events.event_bus import EventBus, EventStore, event_bus, event_store
from app.events.event_types import BaseEvent, EVENT_REGISTRY
from app.infrastructure.database import async_session_factory, AsyncSession


def __getattr__(name: str):
    if name in ("UnitOfWork", "unit_of_work"):
        from app.infrastructure.unit_of_work import UnitOfWork, unit_of_work
        if name == "UnitOfWork":
            return UnitOfWork
        return unit_of_work
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Base", "JSONBColumn", "utcnow",
    "StoredEvent",
    "RetryRecord", "TelemetryMetric", "Checkpoint",
    "redis_client",
    "ConnectionManager", "WSMessage", "connection_manager",
    "EventBroadcaster", "event_broadcaster",
    "EventBus", "EventStore", "event_bus", "event_store",
    "BaseEvent", "EVENT_REGISTRY",
    "async_session_factory", "AsyncSession",
    "UnitOfWork", "unit_of_work",
]

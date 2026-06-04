from app.events.event_bus import EventBus, event_bus
from app.events.event_types import EVENT_REGISTRY, BaseEvent
from app.infrastructure.database import AsyncSession, async_session_factory
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.models.base import Base, JSONBColumn, utcnow
from app.infrastructure.models.event import StoredEvent
from app.infrastructure.models.telemetry import Checkpoint, RetryRecord, TelemetryMetric
from app.infrastructure.websocket.broadcaster import EventBroadcaster, event_broadcaster
from app.infrastructure.websocket.manager import ConnectionManager, WSMessage, connection_manager


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
    "EventBus", "event_bus",
    "BaseEvent", "EVENT_REGISTRY",
    "async_session_factory", "AsyncSession",
    "UnitOfWork", "unit_of_work",
]

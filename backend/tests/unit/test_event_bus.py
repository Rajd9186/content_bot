from __future__ import annotations

from uuid import uuid4

import pytest

from app.events.event_bus import EventBus, EventStore
from app.events.event_types import JobStartedEvent, JobCompletedEvent
from app.db.unit_of_work import UnitOfWork


class TestEventBus:
    async def test_publish_and_subscribe(self) -> None:
        bus = EventBus()
        received: list[JobStartedEvent] = []

        async def handler(event: JobStartedEvent) -> None:
            received.append(event)

        bus.subscribe("workflow.job.started.v1", handler)

        event = JobStartedEvent(
            correlation_id=str(uuid4()),
            subject="job-1",
        )
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].subject == "job-1"

    async def test_wildcard_subscribe(self) -> None:
        bus = EventBus()
        received: list = []

        async def handler(event: object) -> None:
            received.append(event)

        bus.subscribe("*", handler)

        await bus.publish(JobStartedEvent(correlation_id=str(uuid4())))
        await bus.publish(JobCompletedEvent(correlation_id=str(uuid4())))

        assert len(received) == 2

    async def test_handler_error_does_not_break_bus(self) -> None:
        bus = EventBus()

        async def failing_handler(event: object) -> None:
            raise ValueError("handler error")

        async def working_handler(event: object) -> None:
            pass

        bus.subscribe("workflow.job.started.v1", failing_handler)
        bus.subscribe("workflow.job.started.v1", working_handler)

        event = JobStartedEvent(correlation_id=str(uuid4()))
        await bus.publish(event)  # should not raise

    async def test_clear_subscribers(self) -> None:
        bus = EventBus()
        called = False

        async def handler(event: object) -> None:
            nonlocal called
            called = True

        bus.subscribe("workflow.job.started.v1", handler)
        bus.clear()

        await bus.publish(JobStartedEvent(correlation_id=str(uuid4())))
        assert called is False


class TestEventReplay:
    async def test_replay_deserializes_correctly(self) -> None:
        event = JobStartedEvent(
            correlation_id=str(uuid4()),
            subject="job-replay-1",
            data={"workspace_id": "ws-1"},
        )
        stored_data = event.to_stored_dict()

        assert stored_data["event_type"] == "workflow.job.started.v1"
        assert stored_data["aggregate_id"] == "job-replay-1"
        assert stored_data["data"]["workspace_id"] == "ws-1"

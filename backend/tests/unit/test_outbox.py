from __future__ import annotations

from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.db.models import Base, StoredEvent
from app.db.repositories.event import EventRepository
from app.db.unit_of_work import UnitOfWork
from app.events.event_bus import EventStore
from app.events.event_types import JobStartedEvent


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with session_factory() as sess:
        yield sess
    await engine.dispose()


@pytest.fixture
async def uow(session: AsyncSession) -> AsyncGenerator[UnitOfWork, None]:
    yield UnitOfWork(session)
    await session.rollback()


class TestSequenceNumber:
    async def test_auto_assigns_sequence_on_store(self, uow: UnitOfWork) -> None:
        repo = EventRepository(session=uow.session)
        event = StoredEvent(
            event_type="test.sequence.v1",
            source="/test",
            correlation_id=str(uuid4()),
        )
        stored = await repo.store(event)
        assert stored.sequence_number == 1

    async def test_sequence_increments(self, uow: UnitOfWork) -> None:
        repo = EventRepository(session=uow.session)
        for i in range(3):
            event = StoredEvent(
                event_type="test.sequence.v1",
                source="/test",
                correlation_id=str(uuid4()),
            )
            stored = await repo.store(event)
            assert stored.sequence_number == i + 1

    async def test_published_defaults_to_false(self, uow: UnitOfWork) -> None:
        repo = EventRepository(session=uow.session)
        event = StoredEvent(
            event_type="test.published.v1",
            source="/test",
            correlation_id=str(uuid4()),
        )
        stored = await repo.store(event)
        assert stored.published is False

    async def test_get_unpublished_returns_only_unpublished(
        self, uow: UnitOfWork,
    ) -> None:
        repo = EventRepository(session=uow.session)
        for i in range(3):
            event = StoredEvent(
                event_type="test.outbox.v1",
                source="/test",
                correlation_id=str(uuid4()),
                published=(i == 0),
            )
            await repo.store(event)

        unpublished = await repo.get_unpublished(limit=10)
        assert len(unpublished) == 2
        for ev in unpublished:
            assert ev.published is False

    async def test_mark_published(self, uow: UnitOfWork) -> None:
        repo = EventRepository(session=uow.session)
        event = StoredEvent(
            event_type="test.mark.v1",
            source="/test",
            correlation_id=str(uuid4()),
        )
        stored = await repo.store(event)
        assert stored.published is False

        await repo.mark_published(stored.id)
        await uow.session.refresh(stored)
        assert stored.published is True


class TestEventStoreAtomic:
    async def test_store_atomic_does_not_publish_in_memory(
        self, uow: UnitOfWork,
    ) -> None:
        from app.events.event_bus import EventBus

        bus = EventBus()
        received = []

        async def handler(event: object) -> None:
            received.append(event)

        bus.subscribe("workflow.job.started.v1", handler)

        event = JobStartedEvent(
            correlation_id=str(uuid4()),
            subject="job-atomic-1",
        )

        stored = await EventStore().save(uow, event)

        assert len(received) == 0

    async def test_store_atomic_returns_stored_event(
        self, uow: UnitOfWork,
    ) -> None:
        event = JobStartedEvent(
            correlation_id=str(uuid4()),
            subject="job-atomic-2",
        )

        stored = await EventStore().save(uow, event)
        assert stored is not None
        assert stored.event_type == "workflow.job.started.v1"
        assert stored.subject == "job-atomic-2"

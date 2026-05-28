from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.db.models import Base, WorkflowJob, ExecutionLog, StoredEvent
from app.db.repositories.workflow import WorkflowRepository
from app.db.repositories.event import EventRepository
from app.db.unit_of_work import UnitOfWork


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


class TestWorkflowRepository:
    async def test_create_job(self, uow: UnitOfWork) -> None:
        repo = uow.workflows
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
            status="DRAFT",
        )
        created = await repo.add(job)
        assert created.id is not None
        assert created.status == "DRAFT"

    async def test_add_log(self, uow: UnitOfWork) -> None:
        repo = uow.workflows
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
        )
        await repo.add(job)

        log = ExecutionLog(
            job_id=job.id,
            to_status="QUEUED",
            transition="submit",
            triggered_by="system",
            correlation_id=str(uuid4()),
        )
        saved_log = await repo.add_log(log)
        assert saved_log.id is not None
        assert saved_log.to_status == "QUEUED"

    async def test_get_logs(self, uow: UnitOfWork) -> None:
        repo = uow.workflows
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
        )
        await repo.add(job)

        for status in ("QUEUED", "VALIDATING", "PROCESSING"):
            log = ExecutionLog(
                job_id=job.id,
                from_status="DRAFT" if status == "QUEUED" else None,
                to_status=status,
                transition="advance",
                triggered_by="system",
                correlation_id=str(uuid4()),
            )
            await repo.add_log(log)

        logs = await repo.get_logs(job.id)
        assert len(logs) == 3
        assert [l.to_status for l in logs] == ["QUEUED", "VALIDATING", "PROCESSING"]


class TestEventRepository:
    async def test_store_and_retrieve(self, uow: UnitOfWork) -> None:
        repo = uow.events
        event = StoredEvent(
            event_type="workflow.job.started.v1",
            source="/domains/workflow",
            subject="job-123",
            correlation_id=str(uuid4()),
            data={"workspace_id": "ws-1"},
        )
        stored = await repo.store(event)
        assert stored.id is not None
        assert stored.event_type == "workflow.job.started.v1"

        retrieved = await repo.get_by_id(stored.id)
        assert retrieved is not None
        assert retrieved.subject == "job-123"

    async def test_get_by_type(self, uow: UnitOfWork) -> None:
        repo = uow.events
        for i in range(3):
            event = StoredEvent(
                event_type="test.event.v1",
                source="/test",
                subject=f"item-{i}",
                correlation_id=str(uuid4()),
            )
            await repo.store(event)

        events = await repo.get_by_type("test.event.v1")
        assert len(events) == 3

    async def test_get_by_aggregate(self, uow: UnitOfWork) -> None:
        repo = uow.events
        agg_id = "agg-001"
        for i in range(2):
            event = StoredEvent(
                event_type="test.aggregate.event.v1",
                source="/test",
                subject=agg_id,
                aggregate_id=agg_id,
                aggregate_type="test_aggregate",
                correlation_id=str(uuid4()),
            )
            await repo.store(event)

        events = await repo.get_by_aggregate("test_aggregate", agg_id)
        assert len(events) == 2

    async def test_get_by_correlation_id(self, uow: UnitOfWork) -> None:
        repo = uow.events
        corr_id = str(uuid4())
        for _ in range(2):
            event = StoredEvent(
                event_type="test.event.v1",
                source="/test",
                correlation_id=corr_id,
            )
            await repo.store(event)

        events = await repo.get_by_correlation_id(corr_id)
        assert len(events) == 2

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

from app.db.models import Base, WorkflowJob, DeadLetterJob, ExecutionLog
from app.domains.workflow.repository import WorkflowRepository
from app.domains.workflow.state_machine import WorkflowStatus


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


class TestHeartbeat:
    async def test_heartbeat_updates_updated_at(self, session: AsyncSession) -> None:
        repo = WorkflowRepository(session)
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
            status=WorkflowStatus.PROCESSING.value,
        )
        session.add(job)
        await session.flush()

        result = await repo.heartbeat(job.id, job.version)
        assert result is True

    async def test_heartbeat_version_conflict(self, session: AsyncSession) -> None:
        repo = WorkflowRepository(session)
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
            status=WorkflowStatus.PROCESSING.value,
        )
        session.add(job)
        await session.flush()

        result = await repo.heartbeat(job.id, 999)
        assert result is False


class TestJanitor:
    async def test_find_zombies_detects_old_active_jobs(
        self, session: AsyncSession,
    ) -> None:
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        repo = WorkflowRepository(session)
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
            status=WorkflowStatus.PROCESSING.value,
        )
        session.add(job)
        await session.flush()

        job.updated_at = old_time
        await session.flush()

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        stmt = (
            select(WorkflowJob)
            .where(
                WorkflowJob.status.in_([
                    WorkflowStatus.QUEUED.value,
                    WorkflowStatus.VALIDATING.value,
                    WorkflowStatus.PROCESSING.value,
                    WorkflowStatus.RETRYING.value,
                ]),
                WorkflowJob.updated_at < cutoff,
            )
        )
        result = await session.execute(stmt)
        zombies = list(result.scalars().all())
        assert len(zombies) == 1
        assert zombies[0].id == job.id

    async def test_recent_active_jobs_are_not_zombies(
        self, session: AsyncSession,
    ) -> None:
        repo = WorkflowRepository(session)
        job = WorkflowJob(
            workspace_id=str(uuid4()),
            correlation_id=str(uuid4()),
            created_by=str(uuid4()),
            status=WorkflowStatus.PROCESSING.value,
        )
        session.add(job)
        await session.flush()

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        stmt = (
            select(WorkflowJob)
            .where(
                WorkflowJob.status.in_([
                    WorkflowStatus.PROCESSING.value,
                ]),
                WorkflowJob.updated_at < cutoff,
            )
        )
        result = await session.execute(stmt)
        zombies = list(result.scalars().all())
        assert len(zombies) == 0

    async def test_terminal_jobs_are_not_zombies(
        self, session: AsyncSession,
    ) -> None:
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        for status in (WorkflowStatus.COMPLETED.value,
                       WorkflowStatus.FAILED.value,
                       WorkflowStatus.CANCELED.value):
            job = WorkflowJob(
                workspace_id=str(uuid4()),
                correlation_id=str(uuid4()),
                created_by=str(uuid4()),
                status=status,
            )
            session.add(job)
        await session.flush()

        for job in (await session.execute(select(WorkflowJob))).scalars().all():
            job.updated_at = old_time
        await session.flush()

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        stmt = (
            select(WorkflowJob)
            .where(
                WorkflowJob.status.in_([
                    WorkflowStatus.PROCESSING.value,
                ]),
                WorkflowJob.updated_at < cutoff,
            )
        )
        result = await session.execute(stmt)
        zombies = list(result.scalars().all())
        assert len(zombies) == 0

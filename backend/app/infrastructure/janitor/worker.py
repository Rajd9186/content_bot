from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, and_

from app.core.database import async_session_factory
from app.domains.workflow.models import WorkflowJob, DeadLetterJob, ExecutionLog
from app.domains.workflow.state_machine import WorkflowStatus
from app.domains.workflow.repository import WorkflowRepository
from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
ZOMBIE_TIMEOUT_MINUTES = 5
LOCK_TTL_MS = 15000
ACTIVE_STATUSES = [
    WorkflowStatus.QUEUED.value,
    WorkflowStatus.VALIDATING.value,
    WorkflowStatus.PROCESSING.value,
    WorkflowStatus.RETRYING.value,
]
ZOMBIE_ERROR_CODE = "ZOMBIE_DETECTED"
ZOMBIE_ERROR_MESSAGE = "Job detected as zombie: no heartbeat for {timeout_minutes} minutes"


class JanitorWorker:
    """Background worker that detects and recovers zombie workflow jobs.

    A zombie job is one that has been in an active status (PROCESSING,
    QUEUED, VALIDATING, RETRYING) longer than the configured timeout
    without any update. This can happen when a worker process crashes.

    The janitor moves zombie jobs to FAILED with a descriptive error
    and creates a dead-letter entry for later inspection.
    """

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._recovery_loop())
        logger.info(
            "JanitorWorker started (poll=%ss, timeout=%smin)",
            POLL_INTERVAL_SECONDS, ZOMBIE_TIMEOUT_MINUTES,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("JanitorWorker stopped")

    async def _recovery_loop(self) -> None:
        while self._running:
            try:
                await self._scan_and_recover()
            except Exception as e:
                logger.error("Janitor scan error: %s", e)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _scan_and_recover(self) -> None:
        lock = None
        try:
            lock = await redis_client.acquire_lock(
                "janitor:lock", ttl_ms=LOCK_TTL_MS,
            )
            if lock is None:
                return
        except Exception:
            return

        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=ZOMBIE_TIMEOUT_MINUTES)

            async with async_session_factory() as session:
                repo = WorkflowRepository(session)

                zombies = await self._find_zombies(session, repo, cutoff)
                if not zombies:
                    return

                logger.info("Janitor found %s zombie job(s)", len(zombies))
                for job in zombies:
                    await self._recover_job(session, repo, job)
        finally:
            try:
                await lock.release()
            except Exception:
                pass

    async def _find_zombies(
        self, session, repo: WorkflowRepository, cutoff: datetime,
    ) -> list[WorkflowJob]:
        stmt = (
            select(WorkflowJob)
            .where(
                and_(
                    WorkflowJob.status.in_(ACTIVE_STATUSES),
                    WorkflowJob.updated_at < cutoff,
                )
            )
            .order_by(WorkflowJob.updated_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _recover_job(
        self, session, repo: WorkflowRepository, job: WorkflowJob,
    ) -> None:
        try:
            updated = await repo.update_status(
                job.id, WorkflowStatus.FAILED.value, job.version,
            )
            if updated is None:
                logger.warning(
                    "Janitor skip job %s (version conflict)", job.id,
                )
                return

            log = ExecutionLog(
                id=str(uuid4()),
                job_id=job.id,
                from_status=job.status,
                to_status=WorkflowStatus.FAILED.value,
                transition="zombie_recovery",
                triggered_by="janitor",
                correlation_id=job.correlation_id,
            )
            await repo.add_log(log)

            dead = DeadLetterJob(
                id=str(uuid4()),
                original_job_id=job.id,
                error_code=ZOMBIE_ERROR_CODE,
                error_message=ZOMBIE_ERROR_MESSAGE.format(
                    timeout_minutes=ZOMBIE_TIMEOUT_MINUTES,
                ),
                retry_attempts=0,
            )
            await repo.add_dead_letter(dead)

            await session.commit()
            logger.info(
                "Janitor recovered zombie job %s (%s -> FAILED)",
                job.id, job.status,
            )
        except Exception as e:
            await session.rollback()
            logger.error("Janitor recovery failed for job %s: %s", job.id, e)


janitor_worker = JanitorWorker()

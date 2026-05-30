from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.database import async_session_factory
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.unit_of_work import UnitOfWork
from app.infrastructure.sse.manager import sse_manager

logger = logging.getLogger(__name__)

ZOMBIE_TIMEOUT_MINUTES = 5
RECOVERY_POLL_INTERVAL = 60


class RecoveryService:
    """Recovers incomplete pipeline workflows on startup and detects zombie runs.

    Recovery strategies:
    1. On startup: load all pipeline_runs with status in (pending, running)
    2. Zombie detection: runs with stale heartbeat_at (> timeout minutes)
    3. Action: mark zombie runs as failed, allow re-enqueue
    """

    async def recover_on_startup(self) -> int:
        recovered = 0
        try:
            async with async_session_factory() as session:
                uow = UnitOfWork(session)
                try:
                    active = await uow.pipelines.get_active_pipelines(limit=200)
                    for run in active:
                        logger.info(
                            "Recovering pipeline: workflow=%s status=%s node=%s",
                            run.workflow_id, run.status, run.current_node,
                        )
                        state = uow.pipelines.to_pipeline_state(run)
                        if state.has_failures():
                            await uow.pipelines.update_status(run.workflow_id, "failed")
                        elif state.all_nodes_completed():
                            await uow.pipelines.update_status(run.workflow_id, "completed")
                        else:
                            await uow.pipelines.update_status(run.workflow_id, "pending")
                            if redis_client._client is not None:
                                from app.infrastructure.workers.pipeline_worker import pipeline_worker
                                await pipeline_worker.enqueue(run.workflow_id)
                        recovered += 1
                    await uow.commit()
                except Exception as e:
                    await uow.rollback()
                    logger.error("Recovery scan failed: %s", e)
        except Exception as e:
            logger.error("Startup recovery failed: %s", e)
        if recovered > 0:
            logger.info("Recovered %d incomplete pipeline runs", recovered)
        return recovered

    async def detect_and_recover_zombies(self) -> int:
        recovered = 0
        try:
            async with async_session_factory() as session:
                uow = UnitOfWork(session)
                try:
                    zombies = await uow.pipelines.get_zombie_pipelines(
                        timeout_minutes=ZOMBIE_TIMEOUT_MINUTES,
                    )
                    for run in zombies:
                        logger.warning(
                            "Zombie pipeline detected: workflow=%s last_heartbeat=%s",
                            run.workflow_id,
                            run.heartbeat_at.isoformat() if run.heartbeat_at else "never",
                        )
                        await uow.pipelines.update_status(run.workflow_id, "failed")
                        await sse_manager.broadcast_pipeline_event(
                            run.workflow_id, "pipeline_recovered",
                            status="failed", error="Zombie pipeline recovered by janitor",
                        )
                        recovered += 1
                    await uow.commit()
                except Exception as e:
                    await uow.rollback()
                    logger.error("Zombie recovery failed: %s", e)
        except Exception as e:
            logger.error("Zombie detection error: %s", e)
        return recovered


recovery_service = RecoveryService()


class PipelineRecoveryWorker:
    """Background worker that periodically checks for zombie pipeline runs."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Pipeline recovery worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Pipeline recovery worker stopped")

    async def _loop(self) -> None:
        try:
            while self._running:
                await asyncio.sleep(RECOVERY_POLL_INTERVAL)
                count = await recovery_service.detect_and_recover_zombies()
                if count > 0:
                    logger.info("Pipeline recovery: %d zombies recovered", count)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Pipeline recovery worker error: %s", e)


pipeline_recovery_worker = PipelineRecoveryWorker()

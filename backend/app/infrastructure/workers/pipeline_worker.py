from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime

from app.core.database import async_session_factory
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.sse.manager import sse_manager
from app.infrastructure.unit_of_work import UnitOfWork
from app.pipeline.graph import WorkflowPipeline, pipeline
from app.pipeline.state import NodeResult

logger = logging.getLogger(__name__)

PIPELINE_QUEUE = "queue:pipeline:execute"
POLL_INTERVAL_SECONDS = 2
LOCK_TTL_MS = 30000
MAX_CONCURRENT_EXECUTIONS = 5


class PipelineWorker:
    """Background worker that consumes pipeline execution jobs from Redis queue.

    Design:
    - Enqueued via POST /pipeline/{id}/run
    - Consumes from Redis queue (BLPOP)
    - Executes pipeline with progress callbacks that broadcast SSE events
    - Persists state to PostgreSQL after each node via checkpointing
    - Heartbeat updates for zombie detection
    """

    def __init__(self, pipeline_instance: WorkflowPipeline | None = None) -> None:
        self._pipeline = pipeline_instance or pipeline
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._active_executions: dict[str, asyncio.Task[None]] = {}
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)

    async def start(self) -> None:
        if redis_client._client is None:
            logger.warning("Redis not connected, pipeline worker not starting")
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Pipeline worker started")

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        for _wf_id, task in list(self._active_executions.items()):
            if not task.done():
                task.cancel()
        self._active_executions.clear()
        logger.info("Pipeline worker stopped")

    async def enqueue(self, workflow_id: str, skip_human_review: bool = False) -> None:
        job = {
            "workflow_id": workflow_id,
            "skip_human_review": skip_human_review,
            "enqueued_at": datetime.now(UTC).isoformat(),
        }
        await redis_client.queue_push_json(PIPELINE_QUEUE, job)
        logger.info("Pipeline job enqueued: workflow=%s", workflow_id)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                job = await redis_client.queue_pop_json(PIPELINE_QUEUE, timeout=POLL_INTERVAL_SECONDS)
                if job is None:
                    continue
                workflow_id = job.get("workflow_id", "")
                if not workflow_id:
                    logger.warning("Pipeline job missing workflow_id: %s", job)
                    continue
                skip_review = job.get("skip_human_review", False)
                task = asyncio.create_task(
                    self._execute_pipeline(workflow_id, skip_review)
                )
                self._active_executions[workflow_id] = task
                task.add_done_callback(lambda t, wid=workflow_id: self._active_executions.pop(wid, None))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Pipeline worker poll error: %s", e)
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _execute_pipeline(self, workflow_id: str, skip_human_review: bool) -> None:
        async with self._semaphore:
            try:
                async with async_session_factory() as session:
                    uow = UnitOfWork(session)
                    try:
                        pipeline_run = await uow.pipelines.get_by_workflow_id(workflow_id)
                        if not pipeline_run:
                            logger.error("Pipeline run not found: %s", workflow_id)
                            return

                        state = uow.pipelines.to_pipeline_state(pipeline_run)
                        state.current_node = state.current_node or "research"

                        await uow.pipelines.update_status(workflow_id, "running", state.current_node)
                        await uow.commit()

                        await sse_manager.broadcast_pipeline_event(
                            workflow_id, "pipeline_started",
                            node=state.current_node, status="running",
                        )

                        async def on_progress(node: str, result: NodeResult) -> None:
                            await sse_manager.broadcast_pipeline_event(
                                workflow_id, "node_completed",
                                node=node, status=result.status.value,
                                tokens_used=result.tokens_used,
                                latency_ms=result.latency_ms,
                                error=result.error,
                            )
                            state_copy = state.model_copy()
                            state_copy.add_node_result(node, result)
                            try:
                                await uow.pipelines.save_pipeline_state(state_copy)
                                await uow.pipelines.heartbeat(workflow_id)
                                await uow.commit()
                            except Exception as e:
                                logger.warning("Checkpoint save failed for %s node %s: %s", workflow_id, node, e)
                                await uow.rollback()

                        self._pipeline.on_progress(on_progress)

                        async def heartbeat_loop():
                            while True:
                                await asyncio.sleep(30)
                                try:
                                    await uow.pipelines.heartbeat(workflow_id)
                                    await uow.commit()
                                except Exception:
                                    await uow.rollback()

                        hb_task = asyncio.create_task(heartbeat_loop())

                        try:
                            result_state = await self._pipeline.execute(state, skip_human_review=skip_human_review)
                        finally:
                            hb_task.cancel()
                            with contextlib.suppress(asyncio.CancelledError):
                                await hb_task

                        await uow.pipelines.save_pipeline_state(result_state)
                        await uow.commit()

                        final_status = "completed"
                        if result_state.has_failures():
                            final_status = "failed"
                        elif not result_state.all_nodes_completed():
                            final_status = "running"

                        await sse_manager.broadcast_pipeline_event(
                            workflow_id, "pipeline_completed",
                            status=final_status,
                            error_count=len(result_state.errors),
                        )

                        logger.info("Pipeline execution completed: %s status=%s", workflow_id, final_status)

                    except Exception as e:
                        await uow.rollback()
                        logger.exception("Pipeline execution failed: %s", workflow_id)
                        await sse_manager.broadcast_pipeline_event(
                            workflow_id, "pipeline_failed",
                            error=str(e),
                        )
                        try:
                            async with async_session_factory() as err_session:
                                err_uow = UnitOfWork(err_session)
                                await err_uow.pipelines.update_status(workflow_id, "failed")
                                await err_uow.commit()
                        except Exception:
                            pass
            except asyncio.CancelledError:
                logger.info("Pipeline execution cancelled: %s", workflow_id)
            except Exception as e:
                logger.exception("Pipeline worker critical error for %s: %s", workflow_id, e)

    @property
    def active_count(self) -> int:
        return len(self._active_executions)

    @property
    def is_running(self) -> bool:
        return self._running


pipeline_worker = PipelineWorker()

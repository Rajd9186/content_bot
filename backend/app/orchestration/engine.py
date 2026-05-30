from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from app.orchestration.retry_manager import RetryManager
from app.orchestration.stages import (
    STAGE_MAX_RETRIES,
    STAGE_ORDER,
    STAGE_TIMEOUT_SECONDS,
    STAGE_TRANSITIONS,
    StageResult,
    StageStatus,
    WorkflowRun,
    WorkflowStage,
    WorkflowStatus,
    get_next_stage,
)

logger = logging.getLogger(__name__)

StageExecutor = Callable[
    [WorkflowRun, WorkflowStage, dict[str, Any]],
    Coroutine[Any, Any, dict[str, Any]],
]


class WorkflowEngine:
    """Deterministic workflow engine that drives a workflow through its stages.

    Design:
    - No mutable hidden state: all state is in WorkflowRun
    - Checkpoint after each stage for resumability
    - Event-driven: publishes events at every transition
    - Retry-safe: each stage wrapped in retry logic
    """

    def __init__(
        self,
        executor: StageExecutor | None = None,
        checkpoint_fn: Callable[[WorkflowRun], Coroutine[Any, Any, None]] | None = None,
        publish_fn: Callable[[Any], Coroutine[Any, Any, None]] | None = None,
        retry_manager: RetryManager | None = None,
    ) -> None:
        self._executor = executor
        self._checkpoint_fn = checkpoint_fn
        self._publish_fn = publish_fn
        self._retry_manager = retry_manager

    async def run(self, run: WorkflowRun, context: dict[str, Any]) -> WorkflowRun:
        """Execute the workflow from its current stage through completion."""
        if run.status.is_terminal():
            logger.warning("Workflow %s already in terminal state: %s", run.id, run.status.value)
            return run

        start_idx = STAGE_ORDER.index(run.current_stage)

        for stage in STAGE_ORDER[start_idx:]:
            if run.status == WorkflowStatus.CANCELLED:
                break

            if stage == WorkflowStage.PUBLISHED:
                result = await self._execute_stage(run, stage, context)
                run.stage_results[stage.value] = result
                if result.status == StageStatus.COMPLETED:
                    run.status = WorkflowStatus.COMPLETED
                    run.current_stage = stage
                break

            next_stages = STAGE_TRANSITIONS.get(stage, set())

            if WorkflowStage.PUBLISHED in next_stages:
                result = await self._execute_stage(run, stage, context)
                run.stage_results[stage.value] = result
                if result.status == StageStatus.COMPLETED:
                    run.current_stage = stage
                continue

            primary = get_next_stage(stage)
            if primary:
                result = await self._execute_stage(run, stage, context)
                run.stage_results[stage.value] = result
                if result.status == StageStatus.COMPLETED:
                    run.current_stage = stage

            if result.status == StageStatus.FAILED:
                run.status = WorkflowStatus.FAILED
                run.error = result.error
                await self._publish(WorkflowFailedEvent(
                    correlation_id=run.correlation_id,
                    subject=run.id,
                    data={"stage": stage.value, "error": result.error, "workspace_id": run.workspace_id},
                ))
                break

        run.updated_at = datetime.now(UTC)
        run.version += 1

        if run.status == WorkflowStatus.COMPLETED:
            await self._publish(WorkflowCompletedEvent(
                correlation_id=run.correlation_id,
                subject=run.id,
                data={"workspace_id": run.workspace_id},
            ))

        await self._checkpoint(run)
        return run

    async def _execute_stage(
        self, run: WorkflowRun, stage: WorkflowStage, context: dict[str, Any],
    ) -> StageResult:
        result = StageResult(stage=stage, status=StageStatus.RUNNING)
        result.started_at = datetime.now(UTC)

        run.current_stage = stage
        await self._checkpoint(run)

        await self._publish(WorkflowStageStartedEvent(
            correlation_id=run.correlation_id,
            subject=run.id,
            data={"stage": stage.value, "workspace_id": run.workspace_id},
        ))

        max_retries = STAGE_MAX_RETRIES.get(stage, 3)
        timeout_s = STAGE_TIMEOUT_SECONDS.get(stage, 120)

        if self._retry_manager:
            success, output, error, retries = await self._retry_manager.execute_with_retry(
                stage=stage,
                executor=self._executor,
                run=run,
                context=context,
                max_retries=max_retries,
                timeout_s=timeout_s,
            )
        elif self._executor:
            try:
                output = await self._executor(run, stage, context)
                success, error, retries = True, None, 0
            except Exception as e:
                success, output, error, retries = False, {}, str(e), 0
        else:
            output, success, error, retries = {}, True, None, 0

        result.retry_count = retries

        if success:
            result.status = StageStatus.COMPLETED
            result.output = output
            result.completed_at = datetime.now(UTC)
            await self._publish(WorkflowStageCompletedEvent(
                correlation_id=run.correlation_id,
                subject=run.id,
                data={"stage": stage.value, "workspace_id": run.workspace_id},
            ))
        else:
            result.status = StageStatus.FAILED
            result.error = error
            result.completed_at = datetime.now(UTC)
            await self._publish(WorkflowStageFailedEvent(
                correlation_id=run.correlation_id,
                subject=run.id,
                data={
                    "stage": stage.value,
                    "error": error or "Unknown error",
                    "error_code": "STAGE_EXECUTION_FAILED",
                    "workspace_id": run.workspace_id,
                },
            ))

        await self._checkpoint(run)
        return result

    async def _checkpoint(self, run: WorkflowRun) -> None:
        if self._checkpoint_fn:
            await self._checkpoint_fn(run)

    async def _publish(self, event: Any) -> None:
        if self._publish_fn:
            await self._publish_fn(event)

    async def resume(self, run: WorkflowRun, context: dict[str, Any]) -> WorkflowRun:
        """Resume a workflow from its last checkpoint."""
        logger.info("Resuming workflow %s from stage %s", run.id, run.current_stage.value)
        return await self.run(run, context)

    async def cancel(self, run: WorkflowRun, reason: str = "manual") -> WorkflowRun:
        """Cancel a running workflow."""
        run.status = WorkflowStatus.CANCELLED
        run.error = reason
        run.updated_at = datetime.now(UTC)
        run.version += 1
        await self._checkpoint(run)
        await self._publish(WorkflowCancelledEvent(
            correlation_id=run.correlation_id,
            subject=run.id,
            data={"stage": run.current_stage.value, "reason": reason, "workspace_id": run.workspace_id},
        ))
        return run


class WorkflowFailedEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.workflow.failed.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()


class WorkflowCompletedEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.workflow.completed.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()


class WorkflowStageStartedEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.stage.started.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()


class WorkflowStageCompletedEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.stage.completed.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()


class WorkflowStageFailedEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.stage.failed.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()


class WorkflowCancelledEvent:
    def __init__(self, correlation_id: str, subject: str, data: dict) -> None:
        self.correlation_id = correlation_id
        self.subject = subject
        self.data = data
        self.type = "orchestration.workflow.cancelled.v1"
        self.source = "/system/orchestration"
        self.specversion = "1.0"
        self.id = subject
        self.time = datetime.now(UTC).isoformat()

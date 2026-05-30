from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import uuid4

from app.events.event_bus import event_bus
from app.orchestration.engine import StageExecutor, WorkflowEngine
from app.orchestration.events import (
    WorkflowStartedEvent,
)
from app.orchestration.retry_manager import RetryManager
from app.orchestration.stages import (
    STAGE_ORDER,
    StageResult,
    StageStatus,
    WorkflowRun,
    WorkflowStage,
    WorkflowStatus,
)
from app.orchestration.validators import StageValidator, ValidationError, WorkflowInputValidator

logger = logging.getLogger(__name__)


class Orchestrator:
    """High-level orchestrator that manages the full workflow lifecycle.

    Responsibilities:
    - Create workflow runs
    - Run/resume/cancel workflows
    - Persist checkpoints
    - Publish orchestration events
    - Coordinate stage execution via WorkflowEngine
    """

    def __init__(
        self,
        engine: WorkflowEngine | None = None,
        checkpoint_persister: Callable[[WorkflowRun], Coroutine[Any, Any, None]] | None = None,
        event_publisher: Callable[[Any], Coroutine[Any, Any, None]] | None = None,
        dead_letter_handler: Callable[[WorkflowRun, WorkflowStage, str, int], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self._stage_validator = StageValidator()
        self._input_validator = WorkflowInputValidator()
        self._retry_manager = RetryManager(dead_letter_fn=dead_letter_handler)
        self._checkpoint_persister = checkpoint_persister

        async def default_publisher(event: Any) -> None:
            await event_bus.publish(event)

        async def checkpoint_fn(run: WorkflowRun) -> None:
            if self._checkpoint_persister:
                await self._checkpoint_persister(run)

        self._engine = engine or WorkflowEngine(
            checkpoint_fn=checkpoint_fn,
            publish_fn=event_publisher or default_publisher,
            retry_manager=self._retry_manager,
        )

    async def create_workflow(
        self,
        workspace_id: str,
        correlation_id: str,
        content_item_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        """Create a new workflow run in INIT stage."""
        errors = self._input_validator.validate_create(workspace_id, correlation_id, metadata)
        if errors:
            raise ValidationError("; ".join(errors))

        run = WorkflowRun(
            id=str(uuid4()),
            workspace_id=workspace_id,
            content_item_id=content_item_id,
            correlation_id=correlation_id,
            status=WorkflowStatus.RUNNING,
            current_stage=WorkflowStage.INIT,
            metadata=metadata or {},
        )

        await self._persist_checkpoint(run)

        await self._engine._publish(WorkflowStartedEvent(
            correlation_id=correlation_id,
            subject=run.id,
            data={"workspace_id": workspace_id, "content_item_id": content_item_id},
        ))

        logger.info("Workflow created: %s [workspace=%s]", run.id, workspace_id)
        return run

    async def run_workflow(
        self,
        run: WorkflowRun,
        executor: StageExecutor,
        context: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        """Execute the workflow from its current stage through completion."""
        self._engine._executor = executor
        result = await self._engine.run(run, context or {})
        return result

    async def resume_workflow(
        self,
        run: WorkflowRun,
        executor: StageExecutor,
        context: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        """Resume a workflow from its last checkpointed stage."""
        errors = self._input_validator.validate_resume(run)
        if errors:
            raise ValidationError("; ".join(errors))

        self._engine._executor = executor
        return await self._engine.resume(run, context or {})

    async def cancel_workflow(
        self,
        run: WorkflowRun,
        reason: str = "manual",
    ) -> WorkflowRun:
        """Cancel a running or pending workflow."""
        errors = self._input_validator.validate_cancel(run)
        if errors:
            raise ValidationError("; ".join(errors))

        return await self._engine.cancel(run, reason)

    async def get_stage_result(
        self, run: WorkflowRun, stage: WorkflowStage,
    ) -> StageResult | None:
        """Get the result for a specific stage."""
        return run.stage_results.get(stage.value)

    async def get_completed_stages(self, run: WorkflowRun) -> list[WorkflowStage]:
        """Get list of completed stages in order."""
        completed: list[WorkflowStage] = []
        for stage in STAGE_ORDER:
            result = run.stage_results.get(stage.value)
            if result and result.status == StageStatus.COMPLETED:
                completed.append(stage)
        return completed

    async def is_workflow_complete(self, run: WorkflowRun) -> bool:
        """Check if the workflow has reached a terminal state."""
        return run.status.is_terminal()

    async def _persist_checkpoint(self, run: WorkflowRun) -> None:
        if self._checkpoint_persister:
            await self._checkpoint_persister(run)


orchestrator = Orchestrator()

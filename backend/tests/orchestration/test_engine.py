from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

import pytest

from app.orchestration.stages import (
    WorkflowStage, WorkflowStatus, WorkflowRun, StageResult, StageStatus,
    STAGE_ORDER,
)
from app.orchestration.engine import WorkflowEngine


class TestWorkflowEngine:
    @pytest.fixture
    def engine(self) -> WorkflowEngine:
        return WorkflowEngine()

    @pytest.fixture
    def run(self) -> WorkflowRun:
        return WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.RUNNING,
        )

    async def test_deterministic_execution(self, engine: WorkflowEngine, run: WorkflowRun) -> None:
        """Given the same inputs, engine produces the same outputs."""
        stages_run: List[str] = []

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            stages_run.append(stage.value)
            return {"result": f"{stage.value}_done"}

        engine._executor = executor
        result = await engine.run(run, {})

        assert result.status == WorkflowStatus.COMPLETED
        assert stages_run == [s.value for s in STAGE_ORDER]

    async def test_resume_from_checkpoint(self, engine: WorkflowEngine) -> None:
        """Workflow can resume from a partially-completed state."""
        stages_run: List[str] = []

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            stages_run.append(stage.value)
            return {"result": f"{stage.value}_done"}

        engine._executor = executor

        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.RUNNING,
            current_stage=WorkflowStage.SYNTHESIS,
            stage_results={
                WorkflowStage.INIT.value: StageResult(
                    stage=WorkflowStage.INIT, status=StageStatus.COMPLETED,
                ),
                WorkflowStage.PLANNING.value: StageResult(
                    stage=WorkflowStage.PLANNING, status=StageStatus.COMPLETED,
                ),
                WorkflowStage.RESEARCH.value: StageResult(
                    stage=WorkflowStage.RESEARCH, status=StageStatus.COMPLETED,
                ),
            },
            version=2,
        )

        result = await engine.run(run, {})

        assert result.status == WorkflowStatus.COMPLETED
        assert stages_run[0] == "SYNTHESIS"
        assert stages_run[-1] == "PUBLISHED"

    async def test_stage_failure_stops_workflow(self, engine: WorkflowEngine, run: WorkflowRun) -> None:
        """A stage failure stops the workflow and sets status to FAILED."""

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            if stage == WorkflowStage.RESEARCH:
                raise ValueError("Research failed")
            return {"result": "ok"}

        engine._executor = executor
        result = await engine.run(run, {})

        assert result.status == WorkflowStatus.FAILED
        assert result.stage_results[WorkflowStage.RESEARCH.value].status == StageStatus.FAILED
        assert result.current_stage == WorkflowStage.RESEARCH

    async def test_cancelled_workflow_stops(self, engine: WorkflowEngine, run: WorkflowRun) -> None:
        """A cancelled workflow stops executing further stages."""

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            if stage == WorkflowStage.WRITING:
                r.status = WorkflowStatus.CANCELLED
            return {"result": "ok"}

        engine._executor = executor
        result = await engine.run(run, {})

        assert result.status == WorkflowStatus.CANCELLED
        completed = [
            s for s in STAGE_ORDER
            if result.stage_results.get(s.value) and result.stage_results[s.value].status == StageStatus.COMPLETED
        ]
        assert WorkflowStage.SYNTHESIS in completed
        assert WorkflowStage.FINALIZATION not in completed

    async def test_checkpoint_called_after_each_stage(self) -> None:
        checkpoints: List[str] = []

        async def checkpoint_fn(run: WorkflowRun) -> None:
            checkpoints.append(run.current_stage.value)

        engine = WorkflowEngine(checkpoint_fn=checkpoint_fn)

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "ok"}

        engine._executor = executor
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1", status=WorkflowStatus.RUNNING)
        await engine.run(run, {})

        assert len(checkpoints) > 1
        assert checkpoints[0] == WorkflowStage.INIT.value
        assert checkpoints[-1] == WorkflowStage.PUBLISHED.value

    async def test_events_published_for_each_stage(self) -> None:
        events: List[str] = []

        async def publish_fn(event: Any) -> None:
            events.append(event.type)

        engine = WorkflowEngine(publish_fn=publish_fn)

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "ok"}

        engine._executor = executor
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1", status=WorkflowStatus.RUNNING)
        await engine.run(run, {})

        assert "orchestration.stage.started.v1" in events
        assert "orchestration.stage.completed.v1" in events
        assert "orchestration.workflow.completed.v1" in events

    async def test_run_idempotent_on_terminal(self, engine: WorkflowEngine) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
            current_stage=WorkflowStage.PUBLISHED,
        )
        result = await engine.run(run, {})
        assert result.status == WorkflowStatus.COMPLETED

    async def test_version_increments(self, engine: WorkflowEngine) -> None:
        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "ok"}

        engine._executor = executor
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1", status=WorkflowStatus.RUNNING)
        initial_version = run.version
        result = await engine.run(run, {})
        assert result.version == initial_version + 1

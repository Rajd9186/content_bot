from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4

import pytest

from app.orchestration.orchestrator import Orchestrator
from app.orchestration.stages import (
    WorkflowStage, WorkflowStatus, WorkflowRun, StageResult, StageStatus,
    STAGE_ORDER,
)
from app.orchestration.validators import ValidationError


class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self) -> Orchestrator:
        return Orchestrator()

    @pytest.fixture
    def run(self) -> WorkflowRun:
        return WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.RUNNING,
        )

    async def test_create_workflow(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1",
            correlation_id="corr-1",
            metadata={"source": "test"},
        )
        assert run.id is not None
        assert run.workspace_id == "ws-1"
        assert run.status == WorkflowStatus.RUNNING
        assert run.current_stage == WorkflowStage.INIT
        assert run.metadata["source"] == "test"

    async def test_create_workflow_validates_input(self, orchestrator: Orchestrator) -> None:
        with pytest.raises(ValidationError, match="workspace_id"):
            await orchestrator.create_workflow(workspace_id="", correlation_id="corr-1")

    async def test_run_workflow_happy_path(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1", correlation_id="corr-1",
        )
        stages_run: List[str] = []

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            stages_run.append(stage.value)
            return {"result": f"{stage.value}_done"}

        result = await orchestrator.run_workflow(run, executor)

        assert result.status == WorkflowStatus.COMPLETED
        assert stages_run == [s.value for s in STAGE_ORDER]

    async def test_run_workflow_with_context(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1", correlation_id="corr-1",
        )
        context: Dict[str, Any] = {"user_input": "test content"}

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"ctx_value": ctx.get("user_input", "")}

        orchestrator._engine._executor = executor
        result = await orchestrator.run_workflow(run, executor)
        assert result.status == WorkflowStatus.COMPLETED

    async def test_resume_workflow(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1", correlation_id="corr-1",
        )
        stages_run: List[str] = []

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            stages_run.append(stage.value)
            return {"result": "ok"}

        run.current_stage = WorkflowStage.WRITING
        run.stage_results = {
            s.value: StageResult(stage=s, status=StageStatus.COMPLETED)
            for s in [WorkflowStage.INIT, WorkflowStage.PLANNING,
                      WorkflowStage.RESEARCH, WorkflowStage.SYNTHESIS,
                      WorkflowStage.OUTLINING]
        }

        result = await orchestrator.resume_workflow(run, executor)
        assert result.status == WorkflowStatus.COMPLETED
        assert stages_run[0] == "WRITING"
        assert stages_run[-1] == "PUBLISHED"

    async def test_resume_terminal_workflow_raises(self, orchestrator: Orchestrator) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
        )
        async def executor(r: WorkflowRun, s: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {}
        with pytest.raises(ValidationError, match="terminal"):
            await orchestrator.resume_workflow(run, executor)

    async def test_cancel_workflow(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1", correlation_id="corr-1",
        )
        result = await orchestrator.cancel_workflow(run, reason="test cancellation")
        assert result.status == WorkflowStatus.CANCELLED
        assert "test cancellation" in (result.error or "")

    async def test_cancel_terminal_workflow_raises(self, orchestrator: Orchestrator) -> None:
        run = WorkflowRun(
            workspace_id="ws-1",
            correlation_id="corr-1",
            status=WorkflowStatus.COMPLETED,
        )
        with pytest.raises(ValidationError, match="terminal"):
            await orchestrator.cancel_workflow(run)

    async def test_cancel_none_workflow_raises(self, orchestrator: Orchestrator) -> None:
        with pytest.raises(ValidationError, match="not found"):
            await orchestrator.cancel_workflow(None)  # type: ignore

    async def test_get_stage_result(self, orchestrator: Orchestrator, run: WorkflowRun) -> None:
        run.stage_results["INIT"] = StageResult(
            stage=WorkflowStage.INIT, status=StageStatus.COMPLETED,
        )
        result = await orchestrator.get_stage_result(run, WorkflowStage.INIT)
        assert result is not None
        assert result.status == StageStatus.COMPLETED

        missing = await orchestrator.get_stage_result(run, WorkflowStage.PLANNING)
        assert missing is None

    async def test_get_completed_stages(self, orchestrator: Orchestrator, run: WorkflowRun) -> None:
        run.stage_results["INIT"] = StageResult(
            stage=WorkflowStage.INIT, status=StageStatus.COMPLETED,
        )
        run.stage_results["PLANNING"] = StageResult(
            stage=WorkflowStage.PLANNING, status=StageStatus.COMPLETED,
        )
        run.stage_results["RESEARCH"] = StageResult(
            stage=WorkflowStage.RESEARCH, status=StageStatus.FAILED,
        )
        completed = await orchestrator.get_completed_stages(run)
        assert completed == [WorkflowStage.INIT, WorkflowStage.PLANNING]
        assert WorkflowStage.RESEARCH not in completed

    async def test_is_workflow_complete(self, orchestrator: Orchestrator) -> None:
        run = WorkflowRun(workspace_id="ws-1", correlation_id="corr-1")
        assert await orchestrator.is_workflow_complete(run) is False

        run.status = WorkflowStatus.COMPLETED
        assert await orchestrator.is_workflow_complete(run) is True

    async def test_checkpoint_persister_called(self) -> None:
        checkpoints: List[WorkflowRun] = []

        async def persist(run: WorkflowRun) -> None:
            checkpoints.append(run)

        orch = Orchestrator(checkpoint_persister=persist)
        run = await orch.create_workflow(workspace_id="ws-1", correlation_id="corr-1")

        assert len(checkpoints) > 0
        assert checkpoints[-1].id == run.id

    async def test_full_lifecycle(self, orchestrator: Orchestrator) -> None:
        run = await orchestrator.create_workflow(
            workspace_id="ws-1",
            correlation_id="corr-1",
            metadata={"topic": "AI"},
        )

        async def executor(r: WorkflowRun, stage: WorkflowStage, ctx: Dict[str, Any]) -> Dict[str, Any]:
            return {"stage": stage.value, "topic": r.metadata.get("topic")}

        result = await orchestrator.run_workflow(run, executor)

        assert result.status == WorkflowStatus.COMPLETED
        assert result.current_stage == WorkflowStage.PUBLISHED
        assert await orchestrator.is_workflow_complete(result) is True

    async def test_singleton_available(self) -> None:
        from app.orchestration.orchestrator import orchestrator as orch
        assert orch is not None
        assert isinstance(orch, Orchestrator)

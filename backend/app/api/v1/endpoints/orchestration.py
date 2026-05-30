from __future__ import annotations

import contextlib
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_orchestrator
from app.infrastructure.unit_of_work import UnitOfWork
from app.orchestration.orchestrator import Orchestrator
from app.orchestration.stages import WorkflowRun, WorkflowStage, WorkflowStatus
from app.orchestration.validators import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["orchestration"])

_workflow_run_cache: dict[str, WorkflowRun] = {}


async def stub_executor(
    run: WorkflowRun, stage: WorkflowStage, context: dict[str, Any]
) -> dict[str, Any]:
    return {"result": f"{stage.value}_stub", "stage": stage.value}


async def _pipeline_adapter_executor(
    run: WorkflowRun, stage: WorkflowStage, context: dict[str, Any]
) -> dict[str, Any]:
    from app.pipeline.graph import pipeline as pipeline_instance

    state_map = {
        WorkflowStage.RESEARCH: "research",
        WorkflowStage.PLANNING: "planner",
        WorkflowStage.WRITING: "writer",
        WorkflowStage.SEO: "seo",
        WorkflowStage.FACT_CHECK: "fact_checker",
        WorkflowStage.FINALIZATION: "finalizer",
    }

    pipeline_node = state_map.get(stage)
    if not pipeline_node:
        return {"result": f"{stage.value}_skipped", "stage": stage.value}

    workflow_id = run.id
    try:
        from app.core.database import async_session_factory
        async with async_session_factory() as session:
            uow = UnitOfWork(session)
            try:
                pipeline_run = await uow.pipelines.get_by_workflow_id(workflow_id)
                if not pipeline_run:
                    return {"result": f"{stage.value}_no_pipeline", "stage": stage.value}

                state = uow.pipelines.to_pipeline_state(pipeline_run)

                node_handlers = {
                    "research": pipeline_instance.run_research,
                    "planner": pipeline_instance.run_planner,
                    "writer": pipeline_instance.run_writer,
                    "seo": pipeline_instance.run_seo,
                    "fact_checker": pipeline_instance.run_fact_check,
                    "finalizer": pipeline_instance.run_finalizer,
                }
                handler = node_handlers.get(pipeline_node)
                if handler:
                    state = await handler(state)

                await uow.pipelines.save_pipeline_state(state)
                await uow.commit()

                node_result = state.node_results.get(pipeline_node)
                return {
                    "result": pipeline_node,
                    "stage": stage.value,
                    "status": node_result.status.value if node_result else "success",
                    "tokens_used": node_result.tokens_used if node_result else 0,
                }
            except Exception:
                await uow.rollback()
                raise
    except Exception as e:
        logger.error("Pipeline adapter error for stage %s: %s", stage.value, e)
        raise


def _get_executor(use_pipeline: bool = False):
    if use_pipeline:
        return _pipeline_adapter_executor
    return stub_executor


@router.post(
    "/workflows",
    summary="Create a new orchestration workflow",
    operation_id="createOrchestrationWorkflow",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    workspace_id: str | None = None,
    correlation_id: str | None = None,
    content_item_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    if workspace_id is not None and not workspace_id.strip():
        raise HTTPException(status_code=400, detail="workspace_id must not be empty")
    if correlation_id is not None and not correlation_id.strip():
        raise HTTPException(status_code=400, detail="correlation_id must not be empty")
    try:
        run = await orchestrator.create_workflow(
            workspace_id=workspace_id or "default",
            correlation_id=correlation_id or str(uuid4()),
            content_item_id=content_item_id,
            metadata=metadata,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    uow = UnitOfWork(db)
    try:
        await uow.checkpoints.save_checkpoint(
            aggregate_id=run.id,
            aggregate_type="workflow",
            checkpoint_type="workflow_run",
            state=run.model_dump(),
            version=run.version,
        )
        await uow.commit()
    except Exception as e:
        await uow.rollback()
        logger.warning("Failed to persist workflow checkpoint: %s", e)

    _workflow_run_cache[run.id] = run
    return _run_to_response(run)


@router.post(
    "/workflows/{workflow_id}/run",
    summary="Run an orchestration workflow",
    operation_id="runOrchestrationWorkflow",
)
async def run_workflow(
    workflow_id: str,
    workspace_id: str | None = None,
    correlation_id: str | None = None,
    content_item_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    use_pipeline: bool = Query(False, description="Use real pipeline adapter instead of stub"),
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    uow = UnitOfWork(db)
    checkpoint = None
    with contextlib.suppress(Exception):
        checkpoint = await uow.checkpoints.get_latest_checkpoint(
            "workflow", workflow_id, "workflow_run"
        )

    if checkpoint and checkpoint.state:
        run = WorkflowRun.from_dict(checkpoint.state)
    else:
        cached = _workflow_run_cache.get(workflow_id)
        if cached:
            run = cached
        else:
            run = WorkflowRun(
                id=workflow_id,
                workspace_id=workspace_id or "default",
                correlation_id=correlation_id or str(uuid4()),
                content_item_id=content_item_id,
                status=WorkflowStatus.RUNNING,
                current_stage=WorkflowStage.INIT,
                metadata=metadata or {},
            )

    executor = _get_executor(use_pipeline)
    try:
        result = await orchestrator.run_workflow(run, executor)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await uow.checkpoints.save_checkpoint(
            aggregate_id=workflow_id,
            aggregate_type="workflow",
            checkpoint_type="workflow_run",
            state=result.model_dump(),
            version=result.version,
        )
        await uow.commit()
    except Exception as e:
        await uow.rollback()
        logger.warning("Failed to persist workflow result: %s", e)

    _workflow_run_cache[workflow_id] = result
    return _run_to_response(result)


@router.post(
    "/workflows/{workflow_id}/resume",
    summary="Resume an orchestration workflow",
    operation_id="resumeOrchestrationWorkflow",
)
async def resume_workflow(
    workflow_id: str,
    workspace_id: str | None = None,
    correlation_id: str | None = None,
    current_stage: WorkflowStage = WorkflowStage.INIT,
    content_item_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    use_pipeline: bool = Query(False, description="Use real pipeline adapter instead of stub"),
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    uow = UnitOfWork(db)
    checkpoint = None
    with contextlib.suppress(Exception):
        checkpoint = await uow.checkpoints.get_latest_checkpoint(
            "workflow", workflow_id, "workflow_run"
        )

    if checkpoint and checkpoint.state:
        run = WorkflowRun.from_dict(checkpoint.state)
    else:
        cached = _workflow_run_cache.get(workflow_id)
        if cached:
            run = cached
        else:
            run = WorkflowRun(
                id=workflow_id,
                workspace_id=workspace_id or "default",
                correlation_id=correlation_id or str(uuid4()),
                content_item_id=content_item_id,
                status=WorkflowStatus.RUNNING,
                current_stage=current_stage,
                metadata=metadata or {},
            )

    executor = _get_executor(use_pipeline)
    try:
        result = await orchestrator.resume_workflow(run, executor)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await uow.checkpoints.save_checkpoint(
            aggregate_id=workflow_id,
            aggregate_type="workflow",
            checkpoint_type="workflow_run",
            state=result.model_dump(),
            version=result.version,
        )
        await uow.commit()
    except Exception as e:
        await uow.rollback()
        logger.warning("Failed to persist workflow resume: %s", e)

    _workflow_run_cache[workflow_id] = result
    return _run_to_response(result)


@router.post(
    "/workflows/{workflow_id}/cancel",
    summary="Cancel an orchestration workflow",
    operation_id="cancelOrchestrationWorkflow",
)
async def cancel_workflow(
    workflow_id: str,
    workspace_id: str | None = None,
    correlation_id: str | None = None,
    reason: str = "manual",
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    uow = UnitOfWork(db)
    checkpoint = None
    with contextlib.suppress(Exception):
        checkpoint = await uow.checkpoints.get_latest_checkpoint(
            "workflow", workflow_id, "workflow_run"
        )

    if checkpoint and checkpoint.state:
        run = WorkflowRun.from_dict(checkpoint.state)
    else:
        cached = _workflow_run_cache.get(workflow_id)
        if cached:
            run = cached
        else:
            run = WorkflowRun(
                id=workflow_id,
                workspace_id=workspace_id or "default",
                correlation_id=correlation_id or str(uuid4()),
                status=WorkflowStatus.RUNNING,
            )

    try:
        result = await orchestrator.cancel_workflow(run, reason)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await uow.checkpoints.save_checkpoint(
            aggregate_id=workflow_id,
            aggregate_type="workflow",
            checkpoint_type="workflow_run",
            state=result.model_dump(),
            version=result.version,
        )
        await uow.commit()
    except Exception as e:
        await uow.rollback()
        logger.warning("Failed to persist workflow cancel: %s", e)

    _workflow_run_cache[workflow_id] = result
    return _run_to_response(result)


@router.get(
    "/workflows/{workflow_id}",
    summary="Get orchestration workflow status",
    operation_id="getOrchestrationWorkflow",
)
async def get_workflow(
    workflow_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    uow = UnitOfWork(db)

    checkpoint = None
    with contextlib.suppress(Exception):
        checkpoint = await uow.checkpoints.get_latest_checkpoint(
            "workflow", workflow_id, "workflow_run"
        )

    if checkpoint and checkpoint.state:
        run = WorkflowRun.from_dict(checkpoint.state)
        return _run_to_response(run)

    pipeline_run = None
    with contextlib.suppress(Exception):
        pipeline_run = await uow.pipelines.get_by_workflow_id(workflow_id)

    if pipeline_run:
        state = uow.pipelines.to_pipeline_state(pipeline_run)
        response = {
            "id": workflow_id,
            "workspace_id": state.workspace_id,
            "correlation_id": state.correlation_id,
            "status": "completed" if state.all_nodes_completed() else ("failed" if state.has_failures() else "running"),
            "current_stage": state.current_node,
            "version": 1,
            "error": "; ".join(state.errors) if state.errors else None,
            "stage_count": len(state.node_results),
            "workflow_type": "phase7_pipeline",
            "created_at": state.created_at,
            "updated_at": state.updated_at,
        }
        return response

    cached = _workflow_run_cache.get(workflow_id)
    if cached:
        return _run_to_response(cached)

    run = WorkflowRun(
        id=workflow_id,
        workspace_id="",
        correlation_id="",
        status=WorkflowStatus.FAILED,
    )
    return _run_to_response(run)


@router.get(
    "/workflows/{workflow_id}/stages",
    summary="Get completed stages for a workflow",
    operation_id="getOrchestrationCompletedStages",
)
async def get_completed_stages(
    workflow_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
):
    uow = UnitOfWork(db)

    pipeline_run = None
    with contextlib.suppress(Exception):
        pipeline_run = await uow.pipelines.get_by_workflow_id(workflow_id)

    if pipeline_run:
        state = uow.pipelines.to_pipeline_state(pipeline_run)
        stages = []
        for name, result in state.node_results.items():
            stages.append({
                "stage": name,
                "status": result.status.value,
                "retry_count": result.retry_count,
                "latency_ms": result.latency_ms,
                "error": result.error,
            })
        return {"workflow_id": workflow_id, "stages": stages, "stage_count": len(stages)}

    cached = _workflow_run_cache.get(workflow_id)
    if cached:
        stages = []
        for name, result in cached.stage_results.items():
            stages.append({
                "stage": name,
                "status": result.status.value,
                "retry_count": result.retry_count,
                "latency_ms": 0,
                "error": result.error,
            })
        return {"workflow_id": workflow_id, "stages": stages, "stage_count": len(stages)}

    return {"workflow_id": workflow_id, "message": "Workflow not found"}


def _run_to_response(run: WorkflowRun) -> dict:
    return {
        "id": run.id,
        "workspace_id": run.workspace_id,
        "correlation_id": run.correlation_id,
        "status": run.status.value,
        "current_stage": run.current_stage.value,
        "version": run.version,
        "error": run.error,
        "stage_count": len(run.stage_results),
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }

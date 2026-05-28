from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_orchestrator
from app.orchestration.orchestrator import Orchestrator
from app.orchestration.stages import WorkflowStage, WorkflowStatus, WorkflowRun, StageResult
from app.orchestration.validators import ValidationError

router = APIRouter(tags=["orchestration"])


async def stub_executor(
    run: WorkflowRun, stage: WorkflowStage, context: Dict[str, Any]
) -> Dict[str, Any]:
    return {"result": f"{stage.value}_stub", "stage": stage.value}


@router.post(
    "/workflows",
    summary="Create a new orchestration workflow",
    operation_id="createOrchestrationWorkflow",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    workspace_id: str,
    correlation_id: str,
    content_item_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    try:
        run = await orchestrator.create_workflow(
            workspace_id=workspace_id,
            correlation_id=correlation_id,
            content_item_id=content_item_id,
            metadata=metadata,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _run_to_response(run)


@router.post(
    "/workflows/{workflow_id}/run",
    summary="Run an orchestration workflow",
    operation_id="runOrchestrationWorkflow",
)
async def run_workflow(
    workflow_id: str,
    workspace_id: str,
    correlation_id: str,
    content_item_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    run = WorkflowRun(
        id=workflow_id,
        workspace_id=workspace_id,
        correlation_id=correlation_id,
        content_item_id=content_item_id,
        status=WorkflowStatus.RUNNING,
        current_stage=WorkflowStage.INIT,
        metadata=metadata or {},
    )
    try:
        result = await orchestrator.run_workflow(run, stub_executor)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _run_to_response(result)


@router.post(
    "/workflows/{workflow_id}/resume",
    summary="Resume an orchestration workflow",
    operation_id="resumeOrchestrationWorkflow",
)
async def resume_workflow(
    workflow_id: str,
    workspace_id: str,
    correlation_id: str,
    current_stage: WorkflowStage = WorkflowStage.INIT,
    content_item_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    run = WorkflowRun(
        id=workflow_id,
        workspace_id=workspace_id,
        correlation_id=correlation_id,
        content_item_id=content_item_id,
        status=WorkflowStatus.RUNNING,
        current_stage=current_stage,
        metadata=metadata or {},
    )
    try:
        result = await orchestrator.resume_workflow(run, stub_executor)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _run_to_response(result)


@router.post(
    "/workflows/{workflow_id}/cancel",
    summary="Cancel an orchestration workflow",
    operation_id="cancelOrchestrationWorkflow",
)
async def cancel_workflow(
    workflow_id: str,
    workspace_id: str,
    correlation_id: str,
    reason: str = "manual",
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    run = WorkflowRun(
        id=workflow_id,
        workspace_id=workspace_id,
        correlation_id=correlation_id,
        status=WorkflowStatus.RUNNING,
    )
    try:
        result = await orchestrator.cancel_workflow(run, reason)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _run_to_response(result)


@router.get(
    "/workflows/{workflow_id}",
    summary="Get orchestration workflow status",
    operation_id="getOrchestrationWorkflow",
)
async def get_workflow(
    workflow_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    return {"workflow_id": workflow_id, "message": "Workflow retrieval requires persistence layer"}


@router.get(
    "/workflows/{workflow_id}/stages",
    summary="Get completed stages for a workflow",
    operation_id="getOrchestrationCompletedStages",
)
async def get_completed_stages(
    workflow_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    return {"workflow_id": workflow_id, "message": "Stages retrieval requires persistence layer"}


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

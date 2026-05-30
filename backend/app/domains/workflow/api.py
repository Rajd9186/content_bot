from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_workflow_service
from app.domains.workflow.service import WorkflowService
from app.infrastructure.database import get_db

router = APIRouter(tags=["workflow"])


@router.post(
    "/jobs",
    summary="Create a new workflow job",
    operation_id="createWorkflowJob",
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    workspace_id: str,
    created_by: str,
    correlation_id: str,
    service: WorkflowService = Depends(get_workflow_service),
    db: None = Depends(get_db),
):
    job = await service.create_job(workspace_id, created_by, correlation_id)
    return {"id": job.id, "status": job.status}


@router.post(
    "/jobs/{job_id}/submit",
    summary="Submit a draft job for processing",
    operation_id="submitWorkflowJob",
)
async def submit_job(
    job_id: str,
    workspace_id: str,
    triggered_by: str,
    correlation_id: str,
    service: WorkflowService = Depends(get_workflow_service),
):
    job = await service.submit_job(job_id, workspace_id, triggered_by, correlation_id)
    return {"id": job.id, "status": job.status}


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel a workflow job",
    operation_id="cancelWorkflowJob",
)
async def cancel_job(
    job_id: str,
    workspace_id: str,
    triggered_by: str,
    correlation_id: str,
    service: WorkflowService = Depends(get_workflow_service),
):
    job = await service.cancel_job(job_id, workspace_id, triggered_by, correlation_id)
    return {"id": job.id, "status": job.status}


@router.get(
    "/jobs/{job_id}",
    summary="Get workflow job status",
    operation_id="getWorkflowJob",
)
async def get_job(
    job_id: str,
    service: WorkflowService = Depends(get_workflow_service),
):
    job = await service.repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "version": job.version,
        "workspace_id": job.workspace_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }

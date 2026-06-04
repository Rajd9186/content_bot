from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.content_orchestrator import ContentOrchestrator
from app.schemas.agent_outputs.finalizer import FinalizerOutput
from app.orchestration.state_machine.workflow_stage import WorkflowStage
from app.log_config.logger import get_logger
from app.repositories.project import ProjectRepository

logger = get_logger(__name__)
router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class PipelineStartRequest(BaseModel):
    project_id: str = ""
    topic: str = Field(..., min_length=3, max_length=500)
    title: str = Field(default="", max_length=500)
    content_type: str = Field(default="article")
    tone: str = Field(default="professional")
    target_audience: str = Field(default="general")
    points_to_cover: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)


class PipelineStatusResponse(BaseModel):
    workflow_id: str = ""
    project_id: str = ""
    current_stage: str = ""
    is_complete: bool = False
    is_failed: bool = False
    errors: list[dict] = Field(default_factory=list)
    telemetry: dict = Field(default_factory=dict)


@router.post("/start", response_model=PipelineStatusResponse)
async def start_pipeline(
    request: PipelineStartRequest,
    session: AsyncSession = Depends(get_session),
):
    orchestrator = ContentOrchestrator(session)

    project_id = request.project_id or str(uuid.uuid4())

    project_repo = ProjectRepository(session)
    if request.project_id:
        project = await project_repo.get(uuid.UUID(request.project_id))
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {request.project_id} not found")

    workflow = orchestrator.workflow_engine.create_workflow(project_id)

    return PipelineStatusResponse(
        workflow_id=workflow.workflow_id,
        project_id=project_id,
        current_stage=workflow.current_stage.value,
        is_complete=workflow.is_complete,
        is_failed=workflow.is_failed,
    )


@router.post("/run", response_model=PipelineStatusResponse)
async def run_pipeline(
    request: PipelineStartRequest,
    session: AsyncSession = Depends(get_session),
):
    orchestrator = ContentOrchestrator(session)

    project_id = request.project_id or str(uuid.uuid4())

    logger.info("Starting full pipeline", extra={
        "project_id": project_id,
        "topic": request.topic,
        "title": request.title,
    })

    try:
        output = await orchestrator.run_full_pipeline(
            project_id=project_id,
            topic=request.topic,
            title=request.title,
            content_type=request.content_type,
            tone=request.tone,
            target_audience=request.target_audience,
            points_to_cover=request.points_to_cover,
            seo_keywords=request.seo_keywords,
        )

        return PipelineStatusResponse(
            workflow_id="",
            project_id=project_id,
            current_stage="PUBLISHED",
            is_complete=True,
            errors=[],
        telemetry={
            "word_count": output.word_count,
            "citations": len(output.citations),
            "quality_score": output.overall_quality,
            "ready_for_publish": output.ready_for_publish,
        },
        )

    except Exception as e:
        logger.error("Pipeline failed", extra={"error": str(e)[:500]})
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)[:500]}")


@router.get("/status/{workflow_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(workflow_id: str):
    orchestrator = ContentOrchestrator()
    state = orchestrator.workflow_engine.get_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    telemetry = orchestrator.telemetry.get_telemetry(workflow_id)

    return PipelineStatusResponse(
        workflow_id=workflow_id,
        project_id=state.project_id,
        current_stage=state.current_stage.value,
        is_complete=state.is_complete,
        is_failed=state.is_failed,
        errors=state.errors,
        telemetry=telemetry.to_dict() if telemetry else {},
    )


@router.get("/telemetry/{workflow_id}")
async def get_pipeline_telemetry(workflow_id: str):
    orchestrator = ContentOrchestrator()
    telemetry = orchestrator.telemetry.get_telemetry(workflow_id)
    if not telemetry:
        raise HTTPException(status_code=404, detail=f"Telemetry for {workflow_id} not found")
    return telemetry.to_dict()

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session, async_session_factory
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.repositories.workflow import WorkflowExecutionRepository
from app.schemas.content import ContentResponse, ContentGenerateResponse, ContentStatusResponse
from app.services.content_generator import ContentGeneratorService
from app.services.orchestration_service import MultiAgentOrchestrator
from app.models.project import Project
from app.models.workflow import WorkflowExecution
from app.log_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_id}/content", tags=["Content"])


async def run_orchestrator(project_id: uuid.UUID):
    """Background task that runs the multi-agent workflow for a project.

    Opens its own session so the request session is not held during the
    potentially long-running orchestration.
    """
    async with async_session_factory() as session:
        try:
            orchestrator = MultiAgentOrchestrator(session)
            project_repo = ProjectRepository(session)
            project = await project_repo.get(project_id)
            if not project:
                logger.error(f"Project {project_id} not found during background orchestration")
                return

            logger.info("Starting background orchestration", extra={"project_id": str(project_id)})
            await orchestrator.generate(project)
            await session.commit()
            logger.info("Orchestration completed and committed", extra={"project_id": str(project_id)})
        except Exception as e:
            logger.error(
                f"Background orchestration failed for project {project_id}: {e}",
                exc_info=True,
            )
            try:
                await session.rollback()
                project_repo = ProjectRepository(session)
                await project_repo.update_status(project_id, "failed")
                await session.commit()
            except Exception:
                pass


@router.get("", response_model=list[ContentResponse])
async def get_content(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = ContentRepository(session)
    return await repo.get_by_project(project_id)


@router.get("/latest", response_model=ContentStatusResponse)
async def get_latest_content(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get the latest generated content for a project.

    Returns workflow status while content is being generated, avoiding
    404 errors that cause frontend polling to fail.
    """
    # Check project exists
    project_repo = ProjectRepository(session)
    project = await project_repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Check if content exists
    content_repo = ContentRepository(session)
    content = await content_repo.get_latest_by_project(project_id)
    if content is not None:
        return ContentStatusResponse(
            status="completed",
            workflow_status="completed",
            content=ContentResponse.model_validate(content),
        )

    # No content yet — check workflow status
    workflow_repo = WorkflowExecutionRepository(session)
    workflow = await workflow_repo.get_latest_by_project(project_id)

    if workflow is None:
        # No workflow and no content — project just created, not yet generating
        return ContentStatusResponse(
            status="not_found",
            message="No content has been generated for this project yet. Start generation first.",
        )

    if workflow.status == "running":
        return ContentStatusResponse(
            status="processing",
            workflow_status="running",
            current_node=workflow.current_node,
            message=f"Content generation is in progress. Current step: {workflow.current_node}",
        )

    if workflow.status == "failed":
        return ContentStatusResponse(
            status="failed",
            workflow_status="failed",
            current_node=workflow.current_node,
            message=f"Content generation failed at step: {workflow.current_node}. Error: {workflow.error or 'Unknown'}",
        )

    # Completed workflow but no content — edge case
    return ContentStatusResponse(
        status="not_found",
        workflow_status=workflow.status,
        message="Workflow completed but no content was generated.",
    )


@router.post("/generate", response_model=ContentGenerateResponse)
async def generate_content(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    mode: str = Query("v2", description="'v1' for linear pipeline, 'v2' for multi-agent workflow"),
):
    project_repo = ProjectRepository(session)
    project = await project_repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if mode == "v1":
        service = ContentGeneratorService(session)
        result = await service.generate_full_content(project)
        return result

    await project_repo.update_status(project_id, "planning")

    background_tasks.add_task(run_orchestrator, project_id)

    return ContentGenerateResponse(
        project_id=project_id,
        status="started",
        message="Content generation started in background",
    )

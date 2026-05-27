import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.repositories.workflow import WorkflowExecutionRepository
from app.schemas.content import ContentResponse, ContentGenerateResponse, ContentStatusResponse
from app.log_config.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_id}/content", tags=["Content"])


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
        progress_steps = [step.node_name for step in workflow.steps if step.status == "completed"] if workflow.steps else []
        return ContentStatusResponse(
            status="processing",
            workflow_status="running",
            current_node=workflow.current_node,
            progress=progress_steps,
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
    session: AsyncSession = Depends(get_session),
):
    from app.services.content_orchestrator import ContentOrchestrator

    project_repo = ProjectRepository(session)
    project = await project_repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if not project.topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project must have a topic before generating content",
        )

    orchestrator = ContentOrchestrator()
    output = await orchestrator.run_full_pipeline(
        project_id=str(project_id),
        topic=project.topic,
        title=project.title or project.topic,
        content_type=project.content_type or "article",
        tone=project.tone or "professional",
        target_audience=project.target_audience or "general",
        points_to_cover=project.points_to_cover or [],
        seo_keywords=project.seo_keywords or [],
    )

    return ContentGenerateResponse(
        project_id=project_id,
        status="completed",
        markdown=output.markdown,
        word_count=output.word_count,
        quality_score=output.quality_score,
        citations=output.citations,
        message=f"Content generated: {output.word_count} words, {len(output.citations)} citations",
    )

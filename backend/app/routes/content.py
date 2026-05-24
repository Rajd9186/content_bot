import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session, async_session_factory
from app.repositories.project import ProjectRepository
from app.repositories.content import ContentRepository
from app.schemas.content import ContentResponse, ContentGenerateResponse
from app.services.content_generator import ContentGeneratorService
from app.services.orchestration_service import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/content", tags=["Content"])


async def run_orchestrator(project_id: uuid.UUID):
    async with async_session_factory() as session:
        try:
            project_repo = ProjectRepository(session)
            project = await project_repo.get(project_id)
            if project:
                orchestrator = MultiAgentOrchestrator(session)
                await orchestrator.generate(project)
                await session.commit()
        except Exception as e:
            logger.error(f"Background orchestrator failed for project {project_id}: {e}", exc_info=True)

@router.get("", response_model=list[ContentResponse])
async def get_content(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = ContentRepository(session)
    contents = await repo.get_by_project(project_id)
    return contents


@router.get("/latest", response_model=ContentResponse)
async def get_latest_content(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = ContentRepository(session)
    content = await repo.get_latest_by_project(project_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No content generated yet for this project",
        )
    return content


@router.post("/generate", response_model=dict)
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

    # Update status to queued/planning before background task starts
    await project_repo.update_status(project_id, "planning")
    
    background_tasks.add_task(run_orchestrator, project_id)
    
    return {
        "project_id": str(project_id),
        "status": "started",
        "message": "Content generation started in background"
    }

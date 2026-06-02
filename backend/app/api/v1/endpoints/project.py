from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user_id, get_uow
from app.domains.project.models import Project
from app.domains.project.schemas import (
    ProjectCreate, 
    ProjectDashboard, 
    ProjectUpdate, 
    MemorySearchQuery, 
    MemorySearchResponse, 
    MemoryPinRequest
)
from app.infrastructure.unit_of_work import UnitOfWork
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])

@router.post(
    "/projects",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    operation_id="createProject",
)
async def create_project(
    project_in: ProjectCreate,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> Project:
    new_project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user_id,
    )
    project = await uow.projects.create(new_project)
    await uow.commit()
    return project

@router.get(
    "/projects",
    response_model=list[Project],
    summary="List projects for the current user",
    operation_id="listProjects",
)
async def list_projects(
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> list[Project]:
    projects = await uow.projects.get_by_owner(
        owner_id=current_user_id,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return projects

@router.get(
    "/projects/{project_id}",
    response_model=Project,
    summary="Get project details by ID",
    operation_id="getProjectDetails",
)
async def get_project_details(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> Project:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.put(
    "/projects/{project_id}",
    response_model=Project,
    summary="Update an existing project",
    operation_id="updateProject",
)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> Project:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    update_data = project_in.model_dump(exclude_unset=True)
    updated_project = await uow.projects.update(str(project_id), **update_data)
    await uow.commit()
    if not updated_project:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update project")
    return updated_project

@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    operation_id="deleteProject",
)
async def delete_project(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
):
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    deleted = await uow.projects.delete(str(project_id))
    await uow.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete project")
    return

@router.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboard,
    summary="Get project dashboard metrics",
    operation_id="getProjectDashboard",
)
async def get_project_dashboard(
    project_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ProjectDashboard:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Calculate real metrics
    from sqlalchemy import func, select
    from app.domains.project.models import ProjectMemory, ProjectOutput
    
    mem_count_stmt = select(func.count()).select_from(ProjectMemory).where(ProjectMemory.project_id == str(project_id))
    out_count_stmt = select(func.count()).select_from(ProjectOutput).where(ProjectOutput.project_id == str(project_id))
    
    mem_result = await uow.session.execute(mem_count_stmt)
    out_result = await uow.session.execute(out_count_stmt)
    
    return ProjectDashboard(
        id=project.id,
        name=project.name,
        total_memories=mem_result.scalar() or 0,
        total_outputs=out_result.scalar() or 0,
        total_tokens=0, # Token usage would require telemetry aggregation
        last_activity=project.updated_at,
    )

@router.post(
    "/projects/{project_id}/memory/search",
    response_model=list[MemorySearchResponse],
    summary="Semantic search project memories",
    operation_id="searchProjectMemories",
)
async def search_project_memories(
    project_id: UUID,
    query_in: MemorySearchQuery,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
    embedding_service: EmbeddingService = Depends(lambda: EmbeddingService()),
) -> list[MemorySearchResponse]:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    query_vector = await embedding_service.generate_embedding(query_in.query)
    results = await uow.projects.search_memories(
        project_id=str(project_id),
        query_vector=query_vector,
        limit=query_in.limit
    )
    
    return [
        MemorySearchResponse(
            content=mem.content,
            score=float(dist),
            memory_type=mem.memory_type,
            created_at=mem.created_at
        ) for mem, dist in results
    ]

@router.post(
    "/projects/{project_id}/memory/{memory_id}/pin",
    status_code=status.HTTP_200_OK,
    summary="Pin a project memory",
    operation_id="pinProjectMemory",
)
async def pin_memory(
    project_id: UUID,
    memory_id: UUID,
    pin_in: MemoryPinRequest,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    from app.domains.project.models import PinnedProjectMemory
    pin = PinnedProjectMemory(
        project_id=str(project_id),
        memory_id=str(memory_id),
        priority=pin_in.priority
    )
    uow.session.add(pin)
    await uow.commit()
    return

@router.delete(
    "/projects/{project_id}/memory/{memory_id}/pin",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unpin a project memory",
    operation_id="unpinProjectMemory",
)
async def unpin_memory(
    project_id: UUID,
    memory_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    project = await uow.projects.get_by_id(str(project_id))
    if not project or project.owner_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    from sqlalchemy import delete
    from app.domains.project.models import PinnedProjectMemory
    
    stmt = delete(PinnedProjectMemory).where(
        PinnedProjectMemory.project_id == str(project_id),
        PinnedProjectMemory.memory_id == str(memory_id)
    )
    await uow.session.execute(stmt)
    await uow.commit()
    return

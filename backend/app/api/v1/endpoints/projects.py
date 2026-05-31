from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.domains.project.service import ProjectService
from app.infrastructure.database import get_db
from app.schemas.project import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
    ConversationResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    OutputResponse,
    PinMemoryRequest,
    ProjectCreate,
    ProjectDashboard,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdate,
    TimelineEntry,
)
from app.services.context_assembly import ContextAssemblyEngine
from app.services.retrieval_metrics import retrieval_metrics
from app.services.semantic_retrieval import SemanticRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])


async def get_project_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectService:
    return ProjectService(db)


@router.post(
    "/projects",
    response_model=ProjectResponse,
    summary="Create a new project",
    operation_id="createProject",
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    user_id: str | None = Depends(get_current_user_id),
) -> Any:
    owner_id = user_id or "anonymous"
    project = await service.create_project(body.name, owner_id, body.description)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        archived=project.archived,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get(
    "/projects",
    response_model=list[ProjectSummary],
    summary="List all projects",
    operation_id="listProjects",
)
async def list_projects(
    include_archived: bool = Query(False),
    service: ProjectService = Depends(get_project_service),
    user_id: str | None = Depends(get_current_user_id),
) -> Any:
    owner_id = user_id or "anonymous"
    projects = await service.get_projects(owner_id, include_archived)
    result = []
    for p in projects:
        dash = await service.get_dashboard(p.id)
        result.append(ProjectSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            archived=p.archived,
            total_outputs=dash.get("total_outputs", 0),
            total_memories=dash.get("total_memories", 0),
            last_activity=dash.get("last_activity"),
        ))
    return result


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    operation_id="getProject",
)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        archived=project.archived,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    operation_id="updateProject",
)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    kwargs = body.model_dump(exclude_none=True)
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    project = await service.update_project(project_id, **kwargs)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        archived=project.archived,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    operation_id="deleteProject",
)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> None:
    deleted = await service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get(
    "/projects/{project_id}/timeline",
    response_model=list[TimelineEntry],
    summary="Get project timeline",
    operation_id="getProjectTimeline",
)
async def get_project_timeline(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_timeline(project_id, limit, offset)


@router.get(
    "/projects/{project_id}/memories",
    response_model=list[MemoryResponse],
    summary="Get project memories",
    operation_id="getProjectMemories",
)
async def get_project_memories(
    project_id: str,
    memory_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_memories(project_id, memory_type, limit, offset)


@router.get(
    "/projects/{project_id}/outputs",
    response_model=list[OutputResponse],
    summary="Get project outputs",
    operation_id="getProjectOutputs",
)
async def get_project_outputs(
    project_id: str,
    content_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_outputs(project_id, content_type, limit, offset)


@router.post(
    "/projects/{project_id}/memory/search",
    response_model=MemorySearchResponse,
    summary="Search project memories",
    operation_id="searchProjectMemories",
)
async def search_memories(
    project_id: str,
    body: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    retrieval = SemanticRetrievalService(db)
    import time as time_mod
    start = time_mod.monotonic()
    results = await retrieval.search_memories(
        project_id, body.query, body.top_k,
        body.similarity_threshold, body.memory_type,
    )
    latency = (time_mod.monotonic() - start) * 1000
    retrieval_metrics.record_retrieval(
        project_id, body.query, latency, len(results),
        [r.get("similarity", 0) for r in results],
    )
    return MemorySearchResponse(
        results=[MemoryResponse(**r) for r in results],
        query=body.query,
        total=len(results),
    )


@router.post(
    "/projects/{project_id}/memory/pin",
    response_model=dict,
    summary="Pin a memory",
    operation_id="pinMemory",
)
async def pin_memory(
    project_id: str,
    body: PinMemoryRequest,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    success = await service.pin_memory(project_id, body.memory_id, body.priority)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "pinned", "memory_id": body.memory_id}


@router.delete(
    "/projects/{project_id}/memory/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
    operation_id="deleteMemory",
)
async def delete_memory(
    project_id: str,
    memory_id: str,
    service: ProjectService = Depends(get_project_service),
) -> None:
    deleted = await service.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")


@router.post(
    "/projects/{project_id}/context",
    response_model=ContextAssemblyResponse,
    summary="Assemble project context for generation",
    operation_id="assembleProjectContext",
)
async def assemble_context(
    project_id: str,
    body: ContextAssemblyRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    engine = ContextAssemblyEngine(db)
    result = await engine.assemble(
        project_id, body.prompt, body.top_k, body.similarity_threshold,
    )
    memories = [
        MemoryResponse(**m) for m in result.get("relevant_memories", [])
    ]
    pinned = [
        MemoryResponse(**m) for m in result.get("pinned_memories", [])
    ]
    outputs = [
        OutputResponse(**o) for o in result.get("related_outputs", [])
    ]
    prompts = [
        ConversationResponse(**p) for p in result.get("related_prompts", [])
    ]
    return ContextAssemblyResponse(
        project_context=result.get("project_context", {}),
        prompt=result.get("prompt", body.prompt),
        relevant_memories=memories,
        pinned_memories=pinned,
        related_outputs=outputs,
        related_prompts=prompts,
    )


@router.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboard,
    summary="Get project dashboard",
    operation_id="getProjectDashboard",
)
async def get_project_dashboard(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    dash = await service.get_dashboard(project_id)
    if not dash:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectDashboard(**dash)

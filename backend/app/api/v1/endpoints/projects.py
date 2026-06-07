from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.deps import get_current_user_id
from app.domains.project.service import ProjectService
from app.infrastructure.database import get_db
from app.api.v1.deps import get_project_service
from app.jobs.memory_consolidation import memory_consolidation_job

from app.services.project_instructions import ProjectInstructionService
from app.services.context_assembly import ContextAssemblyEngine
from app.agents.project_copilot_agent import ProjectCopilotAgent

from app.schemas.project import (
    ContextAssemblyRequest,
    ContextAssemblyResponse,
    ConversationResponse,
    MemoryResponse,
    OutputResponse,
    PinMemoryRequest,
    ProjectDashboard,
    TimelineEntry,
)
from app.services.retrieval_metrics import retrieval_metrics
from app.services.semantic_retrieval import SemanticRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])


@router.post(
    "/projects/{project_id}/instructions",
    summary="Add project instruction",
    status_code=status.HTTP_201_CREATED,
)
async def add_instruction(
    project_id: str,
    title: str = Query(...),
    content: str = Query(...),
    priority: int = Query(0),
    service: ProjectInstructionService = Depends(lambda db=Depends(get_db): ProjectInstructionService(db)),
    user_id: str | None = Depends(get_current_user_id),
) -> Any:
    instruction = await service.create_instruction(
        project_id=project_id, title=title, content=content, 
        priority=priority, created_by=user_id
    )
    return {"status": "created", "instruction_id": instruction.id}

@router.get(
    "/projects/{project_id}/instructions",
    summary="Get project instructions",
)
async def get_instructions(
    project_id: str,
    enabled_only: bool = Query(True),
    service: ProjectInstructionService = Depends(lambda db=Depends(get_db): ProjectInstructionService(db)),
) -> Any:
    instructions = await service.get_instructions(project_id, enabled_only=enabled_only)
    return instructions

@router.put(
    "/projects/{project_id}/instructions/{instruction_id}",
    summary="Update project instruction",
)
async def update_instruction(
    instruction_id: str,
    enabled: bool | None = Query(None),
    priority: int | None = Query(None),
    service: ProjectInstructionService = Depends(lambda db=Depends(get_db): ProjectInstructionService(db)),
) -> Any:
    updated = await service.update_instruction(
        instruction_id, enabled=enabled, priority=priority
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Instruction not found")
    return {"status": "updated"}

@router.delete(
    "/projects/{project_id}/instructions/{instruction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_instruction(
    instruction_id: str,
    service: ProjectInstructionService = Depends(lambda db=Depends(get_db): ProjectInstructionService(db)),
) -> None:
    if not await service.delete_instruction(instruction_id):
        raise HTTPException(status_code=404, detail="Instruction not found")

@router.get(
    "/projects/{project_id}/source-policy",
    summary="Get project source governance policy",
)
async def get_source_policy(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    policy = await service.get_source_policy(project_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.put(
    "/projects/{project_id}/source-policy",
    summary="Update project source governance policy",
)
async def update_source_policy(
    project_id: str,
    enabled: bool = Query(True),
    policy_name: str | None = Query(None),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    policy = await service.update_source_policy(
        project_id, enabled=enabled, policy_name=policy_name
    )
    return policy

@router.get(
    "/projects/{project_id}/allowed-sources",
    summary="List allowed sources for project",
)
async def get_allowed_sources(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_allowed_sources(project_id)

@router.post(
    "/projects/{project_id}/allowed-sources",
    status_code=status.HTTP_201_CREATED,
    summary="Add allowed source",
)
async def add_allowed_source(
    project_id: str,
    name: str = Query(...),
    domain: str | None = Query(None),
    priority: int = Query(0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.add_allowed_source(project_id, name, domain, priority)

@router.delete(
    "/projects/{project_id}/allowed-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_allowed_source(
    source_id: str,
    service: ProjectService = Depends(get_project_service),
) -> None:
    if not await service.remove_allowed_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")

@router.get(
    "/projects/{project_id}/blocked-sources",
    summary="List blocked sources for project",
)
async def get_blocked_sources(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_blocked_sources(project_id)

@router.post(
    "/projects/{project_id}/blocked-sources",
    status_code=status.HTTP_201_CREATED,
    summary="Add blocked source",
)
async def add_blocked_source(
    project_id: str,
    name: str = Query(...),
    domain: str | None = Query(None),
    reason: str | None = Query(None),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.add_blocked_source(project_id, name, domain, reason)

@router.delete(
    "/projects/{project_id}/blocked-sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_blocked_source(
    source_id: str,
    service: ProjectService = Depends(get_project_service),
) -> None:
    if not await service.remove_blocked_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")

@router.get(
    "/projects/{project_id}/research-preferences",
    summary="Get project research preferences",
)
async def get_research_preferences(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
) -> Any:
    prefs = await service.get_research_preferences(project_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return prefs

@router.put(
    "/projects/{project_id}/research-preferences",
    summary="Update project research preferences",
)
async def update_research_preferences(
    project_id: str,
    freshness_mode: str | None = Query(None),
    trust_threshold: int | None = Query(None),
    allow_competitor_content: bool | None = Query(None),
    latest_only: bool | None = Query(None),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.update_research_preferences(
        project_id,
        freshness_mode=freshness_mode,
        trust_threshold=trust_threshold,
        allow_competitor_content=allow_competitor_content,
        latest_only=latest_only,
    )

@router.post(
    "/projects/migrate-fix",
    summary="TEMPORARY: Fix Alembic version mismatch",
    tags=["maintenance"],
)
async def fix_migration_version(
    db: AsyncSession = Depends(get_db),
) -> Any:
    try:
        await db.execute(text("UPDATE alembic_version SET version_num = '0009'"))
        await db.commit()
        return {"status": "success", "message": "Version reset to 0009. Please redeploy."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
    "/projects/{project_id}/chat/sessions",
    summary="Start a new project chat session",
)
async def start_chat_session(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    user_id: str | None = Depends(get_current_user_id),
) -> Any:
    session = await service.create_chat_session(project_id, user_id)
    return {"session_id": session.id}

@router.get(
    "/projects/{project_id}/chat/sessions",
    summary="List project chat sessions",
)
async def list_chat_sessions(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_chat_sessions(project_id, limit, offset)

@router.post(
    "/projects/{project_id}/chat/sessions/{session_id}/messages",
    summary="Send message to Project Copilot",
)
async def send_chat_message(
    project_id: str,
    session_id: str,
    content: str = Query(...),
    db: AsyncSession = Depends(get_db),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    # 1. Save user message
    await service.add_chat_message(session_id, "user", content)
    
    # 2. Get response from Copilot
    copilot = ProjectCopilotAgent(db)
    response = await copilot.answer_query(project_id, content)
    
    # 3. Save assistant message
    answer = response.get("answer", "I'm sorry, I encountered an error answering that.")
    await service.add_chat_message(session_id, "assistant", answer)
    
    return {
        "answer": answer,
        "context_used": response.get("context_used", {}),
        "status": response.get("status", "success")
    }

@router.get(
    "/projects/{project_id}/chat/sessions/{session_id}/messages",
    summary="Get chat history",
)
async def get_chat_history(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ProjectService = Depends(get_project_service),
) -> Any:
    return await service.get_chat_messages(session_id, limit, offset)

@router.delete(
    "/projects/{project_id}/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_chat_session(
    session_id: str,
    service: ProjectService = Depends(get_project_service),
) -> None:
    if not await service.delete_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

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
    response_model=None,
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


@router.post(
    "/projects/consolidate",
    summary="Trigger memory consolidation",
    operation_id="consolidateMemories",
)
async def trigger_consolidation() -> dict[str, Any]:
    stats = await memory_consolidation_job.run()
    return {"status": "ok", "stats": stats}

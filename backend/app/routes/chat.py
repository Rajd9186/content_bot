import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.chat import ChatRequest, ChatResponse, WorkflowEvent
from app.services.chat_service import ResearchCopilotService

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_with_copilot(
    project_id: uuid.UUID,
    request: ChatRequest,
    session: AsyncSession = Depends(get_session)
):
    service = ResearchCopilotService(session)
    try:
        response = await service.chat(project_id, request.message, request.history)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@router.get("/events", response_model=List[WorkflowEvent])
async def get_workflow_events(
    project_id: uuid.UUID,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    service = ResearchCopilotService(session)
    events = await service.get_events(project_id, limit=limit)
    return events

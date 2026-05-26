"""Human-in-the-loop agent execution endpoints.

POST /api/v1/workflows/{workflow_id}/run-agent
  Triggers a specific enhancement agent for a workflow that is in WAITING_FOR_USER
  or another valid pre-agent state.

POST /api/v1/workflows/{workflow_id}/approve
  Approves the current draft and marks workflow as COMPLETED.
"""

import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.workflow import WorkflowExecutionRepository
from app.repositories.project import ProjectRepository
from app.models.workflow import WorkflowStatus
from app.models.content_version import EnhancementJob
from app.engine.workflow_state import WorkflowStage, can_transition_to
from app.services.stage_orchestrator import StageOrchestrator
from app.services.event_bus import event_bus
from app.log_config.logger import get_logger
from app.utils.datetime_utils import utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflow Agents"])


class RunAgentRequest(BaseModel):
    agent: str


class RunAgentResponse(BaseModel):
    workflow_id: str
    agent: str
    status: str
    message: str
    job_id: str | None = None


@router.post("/{workflow_id}/run-agent", response_model=RunAgentResponse)
async def run_agent(
    workflow_id: uuid.UUID,
    body: RunAgentRequest,
    session: AsyncSession = Depends(get_session),
):
    """Trigger a specific agent for a workflow that is paused waiting for user input.

    Valid agents: critique, revision, verification, contradiction_detection, hyperlink_validation
    """
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    project_id = workflow.project_id
    agent = body.agent.lower()

    valid_agents = {"critique", "revision", "verification", "contradiction_detection", "hyperlink_validation"}
    if agent not in valid_agents:
        raise HTTPException(status_code=400, detail=f"Invalid agent '{agent}'. Valid: {valid_agents}")

    # Validate current workflow stage allows this agent
    current_stage = WorkflowStage(workflow.current_node) if workflow.current_node else WorkflowStage.CREATED
    target_stage = _agent_target_stage(agent)

    if not can_transition_to(current_stage, target_stage) and current_stage != target_stage:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run '{agent}' from stage '{current_stage.value}' (needs transition to '{target_stage.value}')",
        )

    # Create enhancement job
    job_id = uuid.uuid4()
    job = EnhancementJob(
        id=job_id,
        project_id=project_id,
        workflow_id=workflow_id,
        agent_name=agent,
        status="running",
    )
    session.add(job)
    await session.flush()

    await event_bus.publish(
        workflow_id, "agent_started", agent_name=agent, status="running",
        message=f"{agent.capitalize()} agent started",
        payload={"project_id": str(project_id), "stage": target_stage.value},
    )

    try:
        orch = StageOrchestrator(session)
        result = await _run_agent_method(orch, agent, project_id, workflow_id)
        job.status = "completed"
        job.result_data = result
        job.completed_at = utc_now()
        await session.flush()
        await event_bus.publish(
            workflow_id, "agent_completed", agent_name=agent, status="completed",
            message=f"{agent.capitalize()} agent completed",
            progress_percent=_calc_stage_complete_progress(target_stage),
            payload={"project_id": str(project_id), "stage": target_stage.value},
        )
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        if workflow:
            workflow.error = str(e)
        await session.commit()
        await event_bus.publish(
            workflow_id, "agent_failed", agent_name=agent, status="failed",
            message=f"{agent.capitalize()} agent failed: {str(e)[:200]}",
            payload={"project_id": str(project_id), "stage": target_stage.value, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail=str(e))

    await session.commit()
    return RunAgentResponse(
        workflow_id=str(workflow_id),
        agent=agent,
        status="completed",
        message=f"{agent.capitalize()} completed successfully",
        job_id=str(job_id),
    )


@router.post("/{workflow_id}/approve")
async def approve_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Approve the current draft and mark workflow as completed."""
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    current_stage = WorkflowStage(workflow.current_node) if workflow.current_node else WorkflowStage.CREATED
    if not can_transition_to(current_stage, WorkflowStage.COMPLETED) and current_stage != WorkflowStage.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve from stage '{current_stage.value}'",
        )

    workflow.status = WorkflowStatus.completed
    workflow.current_node = WorkflowStage.COMPLETED.value
    workflow.completed_at = utc_now()
    await session.flush()

    await event_bus.publish(
        workflow_id, "workflow_completed", agent_name="user", status="completed",
        message="Workflow approved and completed",
        progress_percent=100.0,
        payload={"project_id": str(workflow.project_id)},
    )

    await session.commit()
    return {"status": "completed", "workflow_id": str(workflow_id)}


@router.post("/{workflow_id}/regenerate")
async def regenerate_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Regenerate content from the writing stage. Resets workflow to WRITING."""
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    current_stage = WorkflowStage(workflow.current_node) if workflow.current_node else WorkflowStage.CREATED
    allowed_from = {WorkflowStage.DRAFT_READY, WorkflowStage.WAITING_FOR_USER, WorkflowStage.REVIEW_PENDING}
    if current_stage not in allowed_from:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot regenerate from stage '{current_stage.value}'",
        )

    workflow.current_node = WorkflowStage.WRITING.value
    await session.flush()

    await event_bus.publish(
        workflow_id, "workflow_restarted", agent_name="user", status="running",
        message="Content regeneration requested — restarting writer",
        payload={"project_id": str(workflow.project_id)},
    )

    # Run writer again in background
    asyncio.create_task(_background_regenerate(workflow.project_id, workflow_id))

    await session.commit()
    return {"status": "regenerating", "workflow_id": str(workflow_id), "stage": "WRITING"}


async def _background_regenerate(project_id: uuid.UUID, workflow_id: uuid.UUID):
    """Background task to regenerate content."""
    from app.database import async_session_factory
    from app.repositories.project import ProjectRepository

    async with async_session_factory() as session:
        try:
            project_repo = ProjectRepository(session)
            project = await project_repo.get(project_id)
            if not project:
                return
            orch = StageOrchestrator(session)
            state = {"outline": project.outline or {}, "research_tasks": [], "all_sources": []}
            new_state = await orch._run_writing(project, workflow_id, state)
            await orch._publish_draft(project_id, workflow_id, new_state)
            wf = await WorkflowExecutionRepository(session).get(workflow_id)
            if wf:
                wf.current_node = WorkflowStage.DRAFT_READY.value
            await session.commit()
        except Exception as e:
            logger.error(f"Background regeneration failed: {e}", exc_info=True)
            await session.rollback()


def _agent_target_stage(agent: str) -> WorkflowStage:
    mapping = {
        "critique": WorkflowStage.REVIEW_PENDING,
        "revision": WorkflowStage.REVISING,
        "verification": WorkflowStage.VERIFYING,
        "contradiction_detection": WorkflowStage.VERIFYING,
        "hyperlink_validation": WorkflowStage.VERIFYING,
    }
    return mapping.get(agent, WorkflowStage.REVIEW_PENDING)


def _calc_stage_complete_progress(stage: WorkflowStage) -> float:
    from app.config import settings
    weights = settings.stage_weights
    cumulative = 0.0
    for s, w in weights.items():
        cumulative += w
        if s == stage.value:
            break
    return cumulative


async def _run_agent_method(orch: StageOrchestrator, agent: str, project_id: uuid.UUID, workflow_id: uuid.UUID) -> dict:
    mapping = {
        "critique": orch.run_critique,
        "revision": orch.run_revision,
        "verification": orch.run_verification,
        "contradiction_detection": orch.run_contradiction_detection,
        "hyperlink_validation": orch.run_hyperlink_validation,
    }
    method = mapping.get(agent)
    if not method:
        raise ValueError(f"No method for agent: {agent}")
    return await method(project_id, workflow_id)

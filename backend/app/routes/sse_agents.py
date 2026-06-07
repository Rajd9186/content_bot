"""Human-in-the-loop agent execution endpoints.

POST /api/v1/workflows/{workflow_id}/run-agent
  Triggers a specific enhancement agent for a workflow in a valid pre-agent stage.

POST /api/v1/workflows/{workflow_id}/approve
  Approves the current draft and marks workflow as PUBLISHED.

POST /api/v1/workflows/{workflow_id}/regenerate
  Regenerates content from WRITING stage.
"""

from __future__ import annotations

import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.workflow import WorkflowExecutionRepository
from app.repositories.project import ProjectRepository
from app.models.workflow import WorkflowStatus
from app.models.content_version import EnhancementJob
from app.orchestration.state_machine.workflow_stage import (
    WorkflowStage,
    can_transition,
    stage_display_name,
)
from app.services.event_bus import event_bus
from app.log_config.logger import get_logger
from app.utils.datetime_utils import utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflow Agents"])

_STAGE_ALIASES: dict[str, WorkflowStage] = {
    # Engine enum values (old) -> Orchestration enum values (new)
    "CREATED": WorkflowStage.INIT,
    "PLANNING": WorkflowStage.PLANNING,
    "RESEARCHING": WorkflowStage.RESEARCH,
    "WRITING": WorkflowStage.WRITING,
    "DRAFT_READY": WorkflowStage.WRITING,
    "REVIEW_PENDING": WorkflowStage.VALIDATION,
    "REVISING": WorkflowStage.WRITING,
    "VERIFYING": WorkflowStage.FACT_CHECK,
    "COMPLETED": WorkflowStage.PUBLISHED,
    "FAILED": WorkflowStage.FAILED,
    "CANCELLED": WorkflowStage.FAILED,
    "WAITING_FOR_USER": WorkflowStage.BLOCKED,
    # Orchestration enum values (new) -> themselves
    "INIT": WorkflowStage.INIT,
    "RESEARCH": WorkflowStage.RESEARCH,
    "SYNTHESIS": WorkflowStage.SYNTHESIS,
    "OUTLINING": WorkflowStage.OUTLINING,
    "VALIDATION": WorkflowStage.VALIDATION,
    "SEO": WorkflowStage.SEO,
    "FACT_CHECK": WorkflowStage.FACT_CHECK,
    "FINALIZATION": WorkflowStage.FINALIZATION,
    "PUBLISHED": WorkflowStage.PUBLISHED,
    "BLOCKED": WorkflowStage.BLOCKED,
}


def safe_parse_stage(value: str | None) -> WorkflowStage:
    if not value:
        return WorkflowStage.INIT
    upper = value.upper()
    if upper in _STAGE_ALIASES:
        return _STAGE_ALIASES[upper]
    try:
        return WorkflowStage(upper)
    except ValueError:
        logger.warning("Unknown stage value '%s', defaulting to INIT", value)
        return WorkflowStage.INIT


class RunAgentRequest(BaseModel):
    agent: str


class RunAgentResponse(BaseModel):
    workflow_id: UUID
    agent: str
    status: str
    message: str
    job_id: UUID | None = None


class ApproveResponse(BaseModel):
    status: str
    workflow_id: str
    stage: str


@router.post("/{workflow_id}/run-agent", response_model=RunAgentResponse)
async def run_agent(
    workflow_id: uuid.UUID,
    body: RunAgentRequest,
    session: AsyncSession = Depends(get_session),
):
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    project_id = workflow.project_id
    agent = body.agent.lower()

    valid_agents = {"critique", "revision", "verification", "contradiction_detection", "hyperlink_validation"}
    if agent not in valid_agents:
        raise HTTPException(status_code=400, detail=f"Invalid agent '{agent}'. Valid: {valid_agents}")

    current_stage = safe_parse_stage(workflow.current_node)
    target_stage = _agent_target_stage(agent)

    if not can_transition(current_stage, target_stage) and current_stage != target_stage:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run '{agent}' from stage '{current_stage.value}' (needs transition to '{target_stage.value}')",
        )

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
        result = await _run_legacy_agent(agent, project_id, workflow_id)
        job.status = "completed"
        job.result_data = result
        job.completed_at = utc_now()
        await session.flush()
        await event_bus.publish(
            workflow_id, "agent_completed", agent_name=agent, status="completed",
            message=f"{agent.capitalize()} agent completed",
            progress_percent=100.0,
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
        workflow_id=workflow_id,
        agent=agent,
        status="completed",
        message=f"{agent.capitalize()} completed successfully",
        job_id=job_id,
    )


@router.post("/{workflow_id}/approve", response_model=ApproveResponse)
async def approve_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    current_stage = safe_parse_stage(workflow.current_node)
    if not can_transition(current_stage, WorkflowStage.PUBLISHED) and current_stage != WorkflowStage.PUBLISHED:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve from stage '{current_stage.value}'",
        )

    workflow.status = WorkflowStatus.COMPLETED
    workflow.current_node = WorkflowStage.PUBLISHED.value
    workflow.completed_at = utc_now()
    await session.flush()

    await event_bus.publish(
        workflow_id, "workflow_completed", agent_name="user", status="completed",
        message="Workflow approved and completed",
        progress_percent=100.0,
        payload={"project_id": str(workflow.project_id)},
    )

    await session.commit()
    return {"status": "completed", "workflow_id": str(workflow_id), "stage": "PUBLISHED"}


@router.post("/{workflow_id}/regenerate", response_model=ApproveResponse)
async def regenerate_workflow(
    workflow_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    wf_repo = WorkflowExecutionRepository(session)
    workflow = await wf_repo.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    current_stage = safe_parse_stage(workflow.current_node)
    allowed_from = {WorkflowStage.WRITING, WorkflowStage.VALIDATION, WorkflowStage.BLOCKED}
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

    await session.commit()
    return {"status": "regenerating", "workflow_id": str(workflow_id), "stage": "WRITING"}


def _agent_target_stage(agent: str) -> WorkflowStage:
    mapping = {
        "critique": WorkflowStage.VALIDATION,
        "revision": WorkflowStage.WRITING,
        "verification": WorkflowStage.FACT_CHECK,
        "contradiction_detection": WorkflowStage.FACT_CHECK,
        "hyperlink_validation": WorkflowStage.FACT_CHECK,
    }
    return mapping.get(agent, WorkflowStage.VALIDATION)


async def _run_legacy_agent(agent: str, project_id: uuid.UUID, workflow_id: uuid.UUID) -> dict:
    from app.database import async_session_factory
    from app.repositories.content import ContentRepository
    from app.repositories.project import ProjectRepository
    from app.repositories.source import SourceRepository
    from app.repositories.claim import ClaimRepository
    from app.repositories.contradiction import ContradictionRepository
    from app.repositories.hyperlink import HyperlinkValidationRepository
    from app.repositories.evidence import EvidenceRepository
    from app.agents.critique import CritiqueAgent
    from app.agents.revision import RevisionAgent
    from app.agents.verifier import VerificationAgent
    from app.agents.contradiction_detector import ContradictionDetectionAgent
    from app.agents.hyperlink_validator import HyperlinkValidationAgent
    from app.services.research_service import ResearchService

    async with async_session_factory() as db_session:
        if agent == "critique":
            critique = CritiqueAgent()
            content_repo = ContentRepository(db_session)
            latest = await content_repo.get_latest_by_project(project_id)
            return await critique.run(
                content={"markdown": latest.markdown, "citations": latest.citations} if latest else {},
                claims=[], outline={},
            )
        elif agent == "revision":
            revision = RevisionAgent()
            content_repo = ContentRepository(db_session)
            latest = await content_repo.get_latest_by_project(project_id)
            return await revision.run(
                content={"markdown": latest.markdown, "citations": latest.citations} if latest else {},
                critique={}, revision_number=1,
            )
        elif agent == "verification":
            verifier = VerificationAgent()
            claim_repo = ClaimRepository(db_session)
            claims = await claim_repo.get_by_project(project_id)
            return await verifier.run(
                research_data="\n".join(c.claim_text for c in claims),
                evidence_sources=[{"url": c.source_url, "content": c.claim_text} for c in claims if c.source_url],
            )
        elif agent == "contradiction_detection":
            detector = ContradictionDetectionAgent()
            claim_repo = ClaimRepository(db_session)
            claims = await claim_repo.get_by_project(project_id)
            contradiction_repo = ContradictionRepository(db_session)
            sources_repo = SourceRepository(db_session)
            sources = await sources_repo.get_by_project(project_id)
            result = await detector.run(
                claims=[{"claim_text": c.claim_text, "claim_id": str(c.id)} for c in claims],
                sources=[{"url": s.url, "content": s.snippet} for s in sources],
            )
            for c in result.get("contradictions", []):
                await contradiction_repo.create(
                    project_id=project_id, workflow_id=workflow_id,
                    claim_text=c.get("claim", ""), severity=c.get("severity", "medium"),
                    conflicting_sources=c.get("conflicting_sources", []), explanation=c.get("explanation", ""),
                )
            await db_session.commit()
            return result
        elif agent == "hyperlink_validation":
            hyperlink = HyperlinkValidationAgent()
            content_repo = ContentRepository(db_session)
            latest = await content_repo.get_latest_by_project(project_id)
            hyperlink_repo = HyperlinkValidationRepository(db_session)
            citations = latest.citations if latest else []
            markdown = latest.markdown if latest else ""
            result = await hyperlink.run(citations=citations, markdown=markdown)
            for hl in result.get("results", []):
                await hyperlink_repo.create(
                    project_id=project_id, url=hl.get("url", ""),
                    label=hl.get("label", ""), status=hl.get("status", "unknown"),
                    is_verified=hl.get("is_verified", False), error_message=hl.get("error_message"),
                )
            await db_session.commit()
            return result

        raise ValueError(f"No legacy agent implementation for: {agent}")

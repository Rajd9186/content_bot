import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.workflow import WorkflowExecutionRepository, WorkflowStepRepository
from app.repositories.contradiction import ContradictionRepository
from app.repositories.hyperlink import HyperlinkValidationRepository
from app.schemas.workflow import WorkflowExecutionResponse, WorkflowStepResponse, WorkflowTelemetry
from app.schemas.contradiction import ContradictionResponse, ContradictionResolve
from app.schemas.hyperlink import HyperlinkValidationResponse, HyperlinkValidationSummary


def register_workflow_routes(router: APIRouter) -> None:
    """Register workflow-related routes onto the given router.

    These are added to the projects router to avoid FastAPI issues with
    separate routers using path-parameter prefixes.
    """

    @router.get("/{project_id}/workflow")
    async def get_workflow(
        project_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
    ):
        repo = WorkflowExecutionRepository(session)
        workflow = await repo.get_latest_by_project(project_id)
        if workflow is None:
            return None
        steps_repo = WorkflowStepRepository(session)
        steps = await steps_repo.get_by_workflow(workflow.id)
        return WorkflowExecutionResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            status=workflow.status,
            current_node=workflow.current_node,
            error=workflow.error,
            telemetry=workflow.telemetry,
            started_at=workflow.started_at,
            completed_at=workflow.completed_at,
            steps=[WorkflowStepResponse.model_validate(s) for s in steps],
        )

    @router.get("/{project_id}/workflow/telemetry", response_model=WorkflowTelemetry)
    async def get_workflow_telemetry(
        project_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
    ):
        repo = WorkflowExecutionRepository(session)
        workflow = await repo.get_latest_by_project(project_id)
        if workflow is None or not workflow.telemetry:
            return WorkflowTelemetry(
                total_duration_ms=0, node_durations={}, total_retries=0,
                total_llm_calls=0, total_sources=0, total_claims=0,
                total_contradictions=0, revision_count=0,
                hyperlinks_checked=0, hyperlinks_valid=0,
                overall_quality_score=0.0,
            )
        t = workflow.telemetry
        return WorkflowTelemetry(
            total_duration_ms=t.get("total_duration_ms", 0),
            node_durations=t.get("node_durations", {}),
            total_retries=t.get("total_retries", 0),
            total_llm_calls=t.get("total_llm_calls", 0),
            total_sources=t.get("total_sources", 0),
            total_claims=t.get("total_claims", 0),
            total_contradictions=t.get("total_contradictions", 0),
            revision_count=t.get("revision_count", 0),
            hyperlinks_checked=t.get("hyperlinks_checked", 0),
            hyperlinks_valid=t.get("hyperlinks_valid", 0),
            overall_quality_score=t.get("overall_quality_score", 0.0),
        )

    @router.get("/{project_id}/workflow/contradictions", response_model=list[ContradictionResponse])
    async def list_contradictions(
        project_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
    ):
        repo = ContradictionRepository(session)
        contradictions = await repo.get_by_project(project_id)
        return [ContradictionResponse.model_validate(c) for c in contradictions]

    @router.post("/{project_id}/workflow/contradictions/{contradiction_id}/resolve", response_model=ContradictionResponse)
    async def resolve_contradiction(
        project_id: uuid.UUID,
        contradiction_id: str,
        payload: ContradictionResolve,
        session: AsyncSession = Depends(get_session),
    ):
        repo = ContradictionRepository(session)
        await repo.resolve(contradiction_id, payload.resolution)
        contradiction = await repo.get(contradiction_id)
        if contradiction is None:
            raise HTTPException(status_code=404, detail="Contradiction not found")
        return ContradictionResponse.model_validate(contradiction)

    @router.get("/{project_id}/workflow/hyperlinks", response_model=list[HyperlinkValidationResponse])
    async def list_hyperlinks(
        project_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
    ):
        repo = HyperlinkValidationRepository(session)
        hyperlinks = await repo.get_by_project(project_id)
        return [HyperlinkValidationResponse.model_validate(h) for h in hyperlinks]

    @router.get("/{project_id}/workflow/hyperlinks/summary", response_model=HyperlinkValidationSummary)
    async def hyperlink_summary(
        project_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
    ):
        repo = HyperlinkValidationRepository(session)
        summary = await repo.get_summary(project_id)
        return HyperlinkValidationSummary(**summary)

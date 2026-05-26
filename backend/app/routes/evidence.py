import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.evidence import EvidenceRepository
from app.repositories.project import ProjectRepository
from app.schemas.evidence import EvidenceResponse, EvidenceListResponse

router = APIRouter(prefix="/projects/{project_id}/evidence", tags=["Evidence"])


@router.get("", response_model=EvidenceListResponse)
async def get_evidence(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project_repo = ProjectRepository(session)
    project = await project_repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    repo = EvidenceRepository(session)
    evidence_items = await repo.get_by_project(project_id)
    avg_relevance = await repo.get_average_relevance(project_id)

    items = []
    for e in evidence_items:
        item = EvidenceResponse.model_validate(e)
        item.source_url = e.source.url if e.source else None
        item.source_domain = e.source.domain if e.source else None
        item.source_trust_score = e.source.trust_score if e.source else None
        items.append(item)

    return EvidenceListResponse(
        evidence=items,
        total_count=len(items),
        average_relevance=avg_relevance,
    )


@router.get("/claims/{claim_id}", response_model=list[EvidenceResponse])
async def get_evidence_by_claim(
    project_id: uuid.UUID,
    claim_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = EvidenceRepository(session)
    evidence_items = await repo.get_by_claim(claim_id)

    items = []
    for e in evidence_items:
        item = EvidenceResponse.model_validate(e)
        item.source_url = e.source.url if e.source else None
        item.source_domain = e.source.domain if e.source else None
        item.source_trust_score = e.source.trust_score if e.source else None
        items.append(item)
    return items

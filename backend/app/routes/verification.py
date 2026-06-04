import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.claim import ClaimRepository
from app.repositories.project import ProjectRepository
from app.repositories.source import SourceRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.content import ContentRepository
from app.schemas.claim import ClaimResponse, ClaimVerificationResponse

router = APIRouter(prefix="/projects/{project_id}/verification", tags=["Verification"])


@router.get("/claims", response_model=ClaimVerificationResponse)
async def get_verification_results(
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

    repo = ClaimRepository(session)
    claims = await repo.get_by_project(project_id)
    summary = await repo.get_verification_summary(project_id)

    claim_responses = [ClaimResponse.model_validate(c) for c in claims]

    return ClaimVerificationResponse(
        claims=claim_responses,
        **summary,
    )


@router.get("/sources", response_model=dict)
async def get_source_trust_metrics(
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

    source_repo = SourceRepository(session)
    sources = await source_repo.get_by_project(project_id)
    avg_trust = await source_repo.get_average_trust_score(project_id)

    return {
        "sources": [
            {
                "id": str(s.id),
                "url": s.url,
                "domain": s.domain,
                "title": s.title,
                "trust_score": s.trust_score,
                "author": s.author,
            }
            for s in sources
        ],
        "total_sources": len(sources),
        "average_trust_score": avg_trust,
    }


@router.get("/dashboard", response_model=dict)
async def get_verification_dashboard(
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

    claim_repo = ClaimRepository(session)
    source_repo = SourceRepository(session)
    evidence_repo = EvidenceRepository(session)
    content_repo = ContentRepository(session)

    claims = await claim_repo.get_by_project(project_id)
    sources = await source_repo.get_by_project(project_id)
    evidence_items = await evidence_repo.get_by_project(project_id)
    contents = await content_repo.get_by_project(project_id)

    claim_summary = await claim_repo.get_verification_summary(project_id)
    avg_trust = await source_repo.get_average_trust_score(project_id)
    avg_relevance = await evidence_repo.get_average_relevance(project_id)

    latest_content = contents[0] if contents else None

    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "topic": project.topic,
            "status": project.status,
            "tone": project.tone,
            "content_type": project.content_type,
        },
        "claims": {
            **claim_summary,
            "items": [
                {
                    "id": str(c.id),
                    "claim_text": c.claim_text,
                    "confidence": c.confidence,
                    "status": c.status,
                    "explanation": c.explanation,
                    "category": c.category,
                }
                for c in claims
            ],
        },
        "sources": {
            "total": len(sources),
            "average_trust_score": avg_trust,
            "items": [
                {
                    "id": str(s.id),
                    "url": s.url,
                    "domain": s.domain,
                    "trust_score": s.trust_score,
                    "title": s.title,
                }
                for s in sources
            ],
        },
        "evidence": {
            "total": len(evidence_items),
            "average_relevance": avg_relevance,
        },
        "content": {
            "has_content": latest_content is not None,
            "word_count": latest_content.word_count if latest_content else None,
            "overall_confidence": latest_content.overall_confidence if latest_content else None,
            "citations_count": len(latest_content.citations) if latest_content else 0,
        },
    }

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.repositories.base import BaseRepository
from app.models.claim import Claim


class ClaimRepository(BaseRepository[Claim]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Claim)

    async def get_by_project(self, project_id: UUID) -> list[Claim]:
        result = await self.session.execute(
            select(Claim)
            .where(Claim.project_id == project_id)
            .order_by(Claim.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_verification_summary(self, project_id: UUID) -> dict:
        claims = await self.get_by_project(project_id)
        total = len(claims)
        if total == 0:
            return {
                "total_claims": 0,
                "verified_count": 0,
                "unverified_count": 0,
                "contradicted_count": 0,
                "unsupported_count": 0,
                "average_confidence": 0.0,
            }
        verified = sum(1 for c in claims if c.status == "verified")
        unverified = sum(1 for c in claims if c.status == "unverified")
        contradicted = sum(1 for c in claims if c.status == "contradicted")
        unsupported = sum(1 for c in claims if c.status == "unsupported")
        confidences = [c.confidence for c in claims if c.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return {
            "total_claims": total,
            "verified_count": verified,
            "unverified_count": unverified,
            "contradicted_count": contradicted,
            "unsupported_count": unsupported,
            "average_confidence": round(avg_conf, 3),
        }

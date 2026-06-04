from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Integer

from app.repositories.base import BaseRepository
from app.models.hyperlink import HyperlinkValidation


class HyperlinkValidationRepository(BaseRepository[HyperlinkValidation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, HyperlinkValidation)

    async def get_by_project(self, project_id: UUID) -> list[HyperlinkValidation]:
        result = await self.session.execute(
            select(HyperlinkValidation)
            .where(HyperlinkValidation.project_id == project_id)
            .order_by(HyperlinkValidation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_summary(self, project_id: UUID) -> dict:
        result = await self.session.execute(
            select(
                func.count().label("total"),
                func.sum(
                    cast(HyperlinkValidation.is_verified, Integer)
                ).label("verified"),
            )
            .where(HyperlinkValidation.project_id == project_id)
        )
        row = result.one()
        total = row.total or 0
        verified = row.verified or 0
        result2 = await self.session.execute(
            select(func.count())
            .where(
                HyperlinkValidation.project_id == project_id,
                HyperlinkValidation.status == "broken",
            )
        )
        broken = result2.scalar() or 0
        return {
            "total": total,
            "verified": verified,
            "broken": broken,
            "pending": total - verified - broken,
            "verification_rate": round(verified / total, 3) if total > 0 else 0.0,
        }

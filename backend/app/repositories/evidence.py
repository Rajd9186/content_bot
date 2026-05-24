from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.repositories.base import BaseRepository
from app.models.evidence import Evidence
from app.models.source import Source


class EvidenceRepository(BaseRepository[Evidence]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Evidence)

    async def get_by_project(self, project_id: UUID) -> list[Evidence]:
        result = await self.session.execute(
            select(Evidence)
            .options(joinedload(Evidence.source))
            .where(Evidence.project_id == project_id)
            .order_by(Evidence.relevance_score.desc().nullslast())
        )
        return list(result.unique().scalars().all())

    async def get_by_claim(self, claim_id: UUID) -> list[Evidence]:
        result = await self.session.execute(
            select(Evidence)
            .options(joinedload(Evidence.source))
            .where(Evidence.claim_id == claim_id)
            .order_by(Evidence.relevance_score.desc().nullslast())
        )
        return list(result.unique().scalars().all())

    async def get_average_relevance(self, project_id: UUID) -> float:
        result = await self.session.execute(
            select(func.avg(Evidence.relevance_score))
            .where(Evidence.project_id == project_id)
        )
        avg = result.scalar()
        return round(avg, 3) if avg else 0.0

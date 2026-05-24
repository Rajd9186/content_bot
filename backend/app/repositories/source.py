from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.repositories.base import BaseRepository
from app.models.source import Source


class SourceRepository(BaseRepository[Source]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Source)

    async def get_by_project(self, project_id: UUID) -> list[Source]:
        result = await self.session.execute(
            select(Source)
            .where(Source.project_id == project_id)
            .order_by(Source.trust_score.desc().nullslast())
        )
        return list(result.scalars().all())

    async def get_average_trust_score(self, project_id: UUID) -> float:
        result = await self.session.execute(
            select(func.avg(Source.trust_score))
            .where(Source.project_id == project_id)
        )
        avg = result.scalar()
        return round(avg, 3) if avg else 0.0

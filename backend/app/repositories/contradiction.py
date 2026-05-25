from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.repositories.base import BaseRepository
from app.models.contradiction import Contradiction


class ContradictionRepository(BaseRepository[Contradiction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Contradiction)

    async def get_by_project(self, project_id: UUID) -> list[Contradiction]:
        result = await self.session.execute(
            select(Contradiction)
            .where(Contradiction.project_id == project_id)
            .order_by(Contradiction.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unresolved(self, project_id: UUID) -> list[Contradiction]:
        result = await self.session.execute(
            select(Contradiction)
            .where(
                Contradiction.project_id == project_id,
                Contradiction.resolved == False,
            )
            .order_by(Contradiction.severity.desc())
        )
        return list(result.scalars().all())

    async def resolve(self, contradiction_id: UUID, resolution: str) -> None:
        await self.session.execute(
            update(Contradiction)
            .where(Contradiction.id == contradiction_id)
            .values(resolved=True, resolution=resolution)
        )

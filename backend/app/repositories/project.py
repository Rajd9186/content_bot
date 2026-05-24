from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.repositories.base import BaseRepository
from app.models.project import Project


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)

    async def update_status(self, project_id: UUID, status: str) -> Project | None:
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(status=status)
            .returning(Project)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .where(Project.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

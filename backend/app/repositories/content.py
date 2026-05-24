from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.content import GeneratedContent


class ContentRepository(BaseRepository[GeneratedContent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, GeneratedContent)

    async def get_by_project(self, project_id: UUID) -> list[GeneratedContent]:
        result = await self.session.execute(
            select(GeneratedContent)
            .where(GeneratedContent.project_id == project_id)
            .order_by(GeneratedContent.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_by_project(self, project_id: UUID) -> GeneratedContent | None:
        result = await self.session.execute(
            select(GeneratedContent)
            .where(GeneratedContent.project_id == project_id)
            .order_by(GeneratedContent.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

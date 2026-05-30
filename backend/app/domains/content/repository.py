from __future__ import annotations

from sqlalchemy import func, select

from app.domains.content.models import ContentItem
from app.infrastructure.repositories.base import BaseRepository


class ContentRepository(BaseRepository[ContentItem]):
    async def get_by_id(self, item_id: str) -> ContentItem | None:
        return await self.session.get(ContentItem, item_id)

    async def get_by_workspace(
        self, workspace_id: str, status: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[ContentItem]:
        stmt = select(ContentItem).where(
            ContentItem.workspace_id == workspace_id
        )
        if status:
            stmt = stmt.where(ContentItem.status == status)
        stmt = stmt.order_by(ContentItem.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_workspace(self, workspace_id: str) -> int:
        stmt = select(func.count()).select_from(
            select(ContentItem)
            .where(ContentItem.workspace_id == workspace_id)
            .subquery()
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

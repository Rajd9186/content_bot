from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.content import ContentItem
from app.db.repositories import BaseRepository


class ContentRepository(BaseRepository[ContentItem]):
    async def get_by_id(self, item_id: str) -> Optional[ContentItem]:
        return await self.session.get(ContentItem, item_id)

    async def get_by_workspace(
        self, workspace_id: str, status: Optional[str] = None,
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

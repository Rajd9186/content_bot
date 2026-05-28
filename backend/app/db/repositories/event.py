from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import StoredEvent
from app.db.repositories import BaseRepository


class EventRepository(BaseRepository[StoredEvent]):
    async def store(self, event: StoredEvent) -> StoredEvent:
        if event.sequence_number is None:
            event.sequence_number = await self._next_sequence()
        self.session.add(event)
        await self.session.flush()
        return event

    async def _next_sequence(self) -> int:
        stmt = select(func.coalesce(func.max(StoredEvent.sequence_number), 0))
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) + 1

    async def get_by_id(self, event_id: str) -> Optional[StoredEvent]:
        return await self.session.get(StoredEvent, event_id)

    async def get_by_type(
        self, event_type: str, limit: int = 100, offset: int = 0,
    ) -> list[StoredEvent]:
        stmt = (
            select(StoredEvent)
            .where(StoredEvent.event_type == event_type)
            .order_by(StoredEvent.sequence_number.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_aggregate(
        self, aggregate_type: str, aggregate_id: str, limit: int = 100,
    ) -> list[StoredEvent]:
        stmt = (
            select(StoredEvent)
            .where(
                StoredEvent.aggregate_type == aggregate_type,
                StoredEvent.aggregate_id == aggregate_id,
            )
            .order_by(StoredEvent.sequence_number.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_correlation_id(
        self, correlation_id: str, limit: int = 100,
    ) -> list[StoredEvent]:
        stmt = (
            select(StoredEvent)
            .where(StoredEvent.correlation_id == correlation_id)
            .order_by(StoredEvent.sequence_number.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self, event_type: Optional[str] = None,
        from_time: Optional[str] = None, to_time: Optional[str] = None,
        limit: int = 100,
    ) -> list[StoredEvent]:
        stmt = select(StoredEvent)
        if event_type:
            stmt = stmt.where(StoredEvent.event_type == event_type)
        if from_time:
            stmt = stmt.where(StoredEvent.created_at >= from_time)
        if to_time:
            stmt = stmt.where(StoredEvent.created_at <= to_time)
        stmt = stmt.order_by(StoredEvent.sequence_number.asc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unpublished(
        self, limit: int = 50,
    ) -> list[StoredEvent]:
        stmt = (
            select(StoredEvent)
            .where(StoredEvent.published == False)  # noqa: E712
            .order_by(StoredEvent.sequence_number.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_published(self, event_id: str) -> None:
        event = await self.get_by_id(event_id)
        if event:
            event.published = True
            await self.session.flush()

    async def count_by_type(self, event_type: str) -> int:
        stmt = select(func.count()).select_from(
            select(StoredEvent).where(StoredEvent.event_type == event_type).subquery()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

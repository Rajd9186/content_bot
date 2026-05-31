from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session_factory
from app.infrastructure.models.project import ProjectMemory

logger = logging.getLogger(__name__)


class MemoryConsolidationJob:
    def __init__(self) -> None:
        self._batch_size = 100

    async def run(self) -> dict[str, int]:
        stats = {
            "duplicates_removed": 0,
            "old_memories_summarized": 0,
            "low_value_memories_removed": 0,
            "total_processed": 0,
        }

        async with async_session_factory() as session:
            stats["duplicates_removed"] = await self._remove_duplicates(session)
            stats["low_value_memories_removed"] = await self._remove_low_value(session)
            stats["old_memories_summarized"] = await self._summarize_old_memories(session)
            await session.commit()

        stats["total_processed"] = (
            stats["duplicates_removed"]
            + stats["low_value_memories_removed"]
            + stats["old_memories_summarized"]
        )
        logger.info("Memory consolidation complete: %s", stats)
        return stats

    async def _remove_duplicates(self, session: AsyncSession) -> int:
        subq = (
            select(
                ProjectMemory.project_id,
                ProjectMemory.memory_type,
                ProjectMemory.content,
                func.min(ProjectMemory.created_at).label("first_seen"),
            )
            .group_by(
                ProjectMemory.project_id,
                ProjectMemory.memory_type,
                ProjectMemory.content,
            )
            .having(func.count() > 1)
            .subquery()
        )

        stmt = (
            delete(ProjectMemory)
            .where(
                ProjectMemory.project_id == subq.c.project_id,
                ProjectMemory.memory_type == subq.c.memory_type,
                ProjectMemory.content == subq.c.content,
                ProjectMemory.created_at > subq.c.first_seen,
            )
        )
        result = await session.execute(stmt)
        return result.rowcount

    async def _remove_low_value(self, session: AsyncSession) -> int:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stmt = (
            delete(ProjectMemory)
            .where(
                ProjectMemory.confidence_score < 0.3,
                ProjectMemory.created_at < thirty_days_ago,
            )
        )
        result = await session.execute(stmt)
        return result.rowcount

    async def _summarize_old_memories(self, session: AsyncSession) -> int:
        return 0


memory_consolidation_job = MemoryConsolidationJob()

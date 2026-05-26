from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.repositories.base import BaseRepository
from app.models.agent_memory import AgentMemory


class AgentMemoryRepository(BaseRepository[AgentMemory]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AgentMemory)

    async def get_by_key(self, agent_name: str, key: str) -> AgentMemory | None:
        result = await self.session.execute(
            select(AgentMemory)
            .where(
                AgentMemory.agent_name == agent_name,
                AgentMemory.key == key,
            )
            .order_by(AgentMemory.last_accessed_at.desc().nullslast())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: UUID) -> list[AgentMemory]:
        result = await self.session.execute(
            select(AgentMemory)
            .where(AgentMemory.project_id == project_id)
            .order_by(AgentMemory.last_accessed_at.desc().nullslast())
        )
        return list(result.scalars().all())

    async def upsert_memory(
        self, agent_name: str, key: str, value: dict,
        project_id: UUID | None = None,
        memory_type: str = "research",
        relevance_score: float | None = None,
    ) -> AgentMemory:
        existing = await self.get_by_key(agent_name, key)
        if existing:
            existing.value = value
            existing.access_count = (existing.access_count or 0) + 1
            existing.last_accessed_at = datetime.now(timezone.utc)
            if relevance_score is not None:
                existing.relevance_score = relevance_score
            return existing
        return await self.create(
            agent_name=agent_name,
            key=key,
            value=value,
            project_id=project_id,
            memory_type=memory_type,
            relevance_score=relevance_score,
        )

    async def search_by_type(self, agent_name: str, memory_type: str, limit: int = 10) -> list[AgentMemory]:
        result = await self.session.execute(
            select(AgentMemory)
            .where(
                AgentMemory.agent_name == agent_name,
                AgentMemory.memory_type == memory_type,
            )
            .order_by(AgentMemory.relevance_score.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

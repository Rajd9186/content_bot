from __future__ import annotations

from sqlalchemy import func, select

from app.domains.agent.models import AgentConfig, AgentExecution
from app.infrastructure.repositories.base import BaseRepository


class AgentRepository(BaseRepository[AgentConfig]):
    async def get_by_id(self, config_id: str) -> AgentConfig | None:
        return await self.session.get(AgentConfig, config_id)

    async def get_by_workspace(
        self, workspace_id: str, active_only: bool = True,
    ) -> list[AgentConfig]:
        stmt = select(AgentConfig).where(
            AgentConfig.workspace_id == workspace_id
        )
        if active_only:
            stmt = stmt.where(AgentConfig.active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_executions_by_job(
        self, job_id: str, limit: int = 50,
    ) -> list[AgentExecution]:
        stmt = (
            select(AgentExecution)
            .where(AgentExecution.job_id == job_id)
            .order_by(AgentExecution.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_executions_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(
            select(AgentExecution)
            .where(AgentExecution.status == status)
            .subquery()
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

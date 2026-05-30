from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.domains.agent.repository import AgentRepository
    from app.domains.content.repository import ContentRepository
    from app.domains.workflow.repository import WorkflowRepository
    from app.infrastructure.repositories.event_repository import EventRepository
    from app.infrastructure.repositories.pipeline_repository import (
        CheckpointRepository,
        PipelineRepository,
    )


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def workflows(self) -> WorkflowRepository:
        from app.domains.workflow.repository import WorkflowRepository
        if not hasattr(self, "_workflows"):
            self._workflows = WorkflowRepository(self._session)
        return self._workflows

    @property
    def content(self) -> ContentRepository:
        from app.domains.content.repository import ContentRepository
        if not hasattr(self, "_content"):
            self._content = ContentRepository(self._session)
        return self._content

    @property
    def agents(self) -> AgentRepository:
        from app.domains.agent.repository import AgentRepository
        if not hasattr(self, "_agents"):
            self._agents = AgentRepository(self._session)
        return self._agents

    @property
    def events(self) -> EventRepository:
        from app.infrastructure.repositories.event_repository import EventRepository
        if not hasattr(self, "_events"):
            self._events = EventRepository(self._session)
        return self._events

    @property
    def pipelines(self) -> PipelineRepository:
        from app.infrastructure.repositories.pipeline_repository import PipelineRepository
        if not hasattr(self, "_pipelines"):
            self._pipelines = PipelineRepository(self._session)
        return self._pipelines

    @property
    def checkpoints(self) -> CheckpointRepository:
        from app.infrastructure.repositories.pipeline_repository import CheckpointRepository
        if not hasattr(self, "_checkpoints"):
            self._checkpoints = CheckpointRepository(self._session)
        return self._checkpoints

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


@asynccontextmanager
async def unit_of_work(session: AsyncSession) -> AsyncGenerator[UnitOfWork, None]:
    uow = UnitOfWork(session)
    try:
        yield uow
        await uow.commit()
    except Exception:
        await uow.rollback()
        raise

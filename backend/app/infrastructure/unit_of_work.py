from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workflow.repository import WorkflowRepository
from app.domains.content.repository import ContentRepository
from app.domains.agent.repository import AgentRepository
from app.infrastructure.repositories.event_repository import EventRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.workflows = WorkflowRepository(session)
        self.content = ContentRepository(session)
        self.agents = AgentRepository(session)
        self.events = EventRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def __enter__(self) -> "UnitOfWork":
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

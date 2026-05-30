from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.db.repositories.content import ContentRepository
from app.db.repositories.event import EventRepository
from app.db.repositories.workflow import WorkflowRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def workflows(self) -> WorkflowRepository:
        return WorkflowRepository(self.session)

    @property
    def events(self) -> EventRepository:
        return EventRepository(self.session)

    @property
    def content(self) -> ContentRepository:
        return ContentRepository(self.session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()


@asynccontextmanager
async def unit_of_work(session: AsyncSession | None = None) -> AsyncGenerator[UnitOfWork, None]:
    if session:
        yield UnitOfWork(session)
    else:
        async with async_session_factory() as sess:
            try:
                yield UnitOfWork(sess)
                await sess.commit()
            except Exception:
                await sess.rollback()
                raise
            finally:
                await sess.close()

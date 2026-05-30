from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def add_all(self, instances: list[T]) -> list[T]:
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def get_by_id(self, entity_id: Any) -> T | None:
        raise NotImplementedError

    async def exists(self, **filters: Any) -> bool:
        from sqlalchemy import exists as sa_exists
        from sqlalchemy import select

        stmt = sa_exists(
            select(self.__class__.__orig_bases__[0].__args__[0]).filter_by(**filters)
        ).select()
        result = await self.session.execute(stmt)
        return result.scalar() or False

    async def count(self, **filters: Any) -> int:
        from sqlalchemy import func, select

        query = select(func.count()).select_from(
            self.__class__.__orig_bases__[0].__args__[0]  # type: ignore
        )
        if filters:
            query = query.filter_by(**filters)
        result = await self.session.execute(query)
        return result.scalar() or 0

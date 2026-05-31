from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.project.repository import ProjectRepository
from app.infrastructure.models.project import Project

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def create_project(
        self, name: str, owner_id: str, description: str | None = None
    ) -> Project:
        return await self._repo.create(name, owner_id, description)

    async def get_project(self, project_id: str) -> Project | None:
        return await self._repo.get_by_id(project_id)

    async def get_projects(
        self, owner_id: str, include_archived: bool = False
    ) -> list[Project]:
        return await self._repo.get_by_owner(owner_id, include_archived)

    async def update_project(
        self, project_id: str, **kwargs: Any
    ) -> Project | None:
        return await self._repo.update(project_id, **kwargs)

    async def delete_project(self, project_id: str) -> bool:
        return await self._repo.delete(project_id)

    async def get_timeline(
        self, project_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        return await self._repo.get_timeline(project_id, limit, offset)

    async def get_memories(
        self, project_id: str, memory_type: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[dict[str, Any]]:
        memories = await self._repo.get_memories(
            project_id, memory_type, limit, offset
        )
        pinned_ids = {
            p.memory_id
            for p in await self._repo.get_pinned_memories(project_id)
        }
        return [
            {
                "id": m.id,
                "project_id": m.project_id,
                "memory_type": m.memory_type,
                "content": m.content,
                "confidence_score": m.confidence_score,
                "pinned": m.id in pinned_ids,
                "priority": next(
                    (p.priority for p in await self._repo.get_pinned_memories(project_id)
                     if p.memory_id == m.id),
                    0,
                ) if m.id in pinned_ids else 0,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]

    async def get_outputs(
        self, project_id: str, content_type: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[dict[str, Any]]:
        outputs = await self._repo.get_outputs(
            project_id, content_type, limit, offset
        )
        return [
            {
                "id": o.id,
                "project_id": o.project_id,
                "workflow_execution_id": o.workflow_execution_id,
                "title": o.title,
                "content": o.content,
                "content_type": o.content_type,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in outputs
        ]

    async def delete_memory(self, memory_id: str) -> bool:
        return await self._repo.delete_memory(memory_id)

    async def pin_memory(
        self, project_id: str, memory_id: str, priority: int = 0
    ) -> bool:
        result = await self._repo.pin_memory(project_id, memory_id, priority)
        return result is not None

    async def unpin_memory(self, memory_id: str) -> bool:
        return await self._repo.unpin_memory(memory_id)

    async def get_dashboard(self, project_id: str) -> dict[str, Any]:
        project = await self._repo.get_by_id(project_id)
        if not project:
            return {}
        stats = await self._repo.get_dashboard(project_id)
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "archived": project.archived,
                "owner_id": project.owner_id,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },
            **stats,
        }

    async def verify_ownership(self, project_id: str, owner_id: str) -> bool:
        project = await self._repo.get_by_id(project_id)
        if not project:
            return False
        return project.owner_id == owner_id

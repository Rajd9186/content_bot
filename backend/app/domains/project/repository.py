from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.project import (
    PinnedProjectMemory,
    Project,
    ProjectConversation,
    ProjectMemory,
    ProjectOutput,
)

logger = logging.getLogger(__name__)


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, owner_id: str, description: str | None = None) -> Project:
        project = Project(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        try:
            return await self._session.get(Project, project_id)
        except Exception:
            return None

    async def get_by_owner(self, owner_id: str, include_archived: bool = False) -> list[Project]:
        try:
            stmt = select(Project).where(text("owner_id = :owner_id")).params(owner_id=owner_id)
            if not include_archived:
                stmt = stmt.where(text("archived = false"))
            stmt = stmt.order_by(Project.updated_at.desc())
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.exception("get_by_owner failed for owner=%s include_archived=%s", owner_id, include_archived)
            raise

    async def update(self, project_id: str, **kwargs: Any) -> Project | None:
        project = await self.get_by_id(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.now()
        await self._session.flush()
        return project

    async def delete(self, project_id: str) -> bool:
        project = await self.get_by_id(project_id)
        if not project:
            return False
        await self._session.delete(project)
        await self._session.flush()
        return True

    async def get_conversations(
        self, project_id: str, limit: int = 50, offset: int = 0
    ) -> list[ProjectConversation]:
        stmt = (
            select(ProjectConversation)
            .where(ProjectConversation.project_id == project_id)
            .order_by(ProjectConversation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_outputs(
        self, project_id: str, content_type: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[ProjectOutput]:
        stmt = select(ProjectOutput).where(ProjectOutput.project_id == project_id)
        if content_type:
            stmt = stmt.where(ProjectOutput.content_type == content_type)
        stmt = stmt.order_by(ProjectOutput.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_memories(
        self, project_id: str, memory_type: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> list[ProjectMemory]:
        stmt = select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        if memory_type:
            stmt = stmt.where(ProjectMemory.memory_type == memory_type)
        stmt = stmt.order_by(ProjectMemory.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_memory(self, memory_id: str) -> bool:
        memory = await self._session.get(ProjectMemory, memory_id)
        if not memory:
            return False
        await self._session.delete(memory)
        await self._session.flush()
        return True

    async def pin_memory(
        self, project_id: str, memory_id: str, priority: int = 0,
    ) -> PinnedProjectMemory | None:
        existing = await self._get_pin(memory_id)
        if existing:
            existing.priority = priority
            await self._session.flush()
            return existing
        pin = PinnedProjectMemory(
            project_id=project_id,
            memory_id=memory_id,
            priority=priority,
        )
        self._session.add(pin)
        await self._session.flush()
        return pin

    async def unpin_memory(self, memory_id: str) -> bool:
        pin = await self._get_pin(memory_id)
        if not pin:
            return False
        await self._session.delete(pin)
        await self._session.flush()
        return True

    async def get_pinned_memories(self, project_id: str) -> list[PinnedProjectMemory]:
        stmt = (
            select(PinnedProjectMemory)
            .where(PinnedProjectMemory.project_id == project_id)
            .order_by(PinnedProjectMemory.priority.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_dashboard(self, project_id: str) -> dict[str, Any]:
        outputs_count = await self._session.scalar(
            select(func.count()).where(ProjectOutput.project_id == project_id)
        )
        memories_count = await self._session.scalar(
            select(func.count()).where(ProjectMemory.project_id == project_id)
        )
        conversations_count = await self._session.scalar(
            select(func.count()).where(ProjectConversation.project_id == project_id)
        )

        last_output = await self._session.scalar(
            select(ProjectOutput.created_at)
            .where(ProjectOutput.project_id == project_id)
            .order_by(ProjectOutput.created_at.desc())
            .limit(1)
        )
        last_conversation = await self._session.scalar(
            select(ProjectConversation.created_at)
            .where(ProjectConversation.project_id == project_id)
            .order_by(ProjectConversation.created_at.desc())
            .limit(1)
        )

        last_activity = None
        if last_output and last_conversation:
            last_activity = max(last_output, last_conversation)
        elif last_output:
            last_activity = last_output
        elif last_conversation:
            last_activity = last_conversation

        return {
            "total_outputs": outputs_count or 0,
            "total_memories": memories_count or 0,
            "total_sources": conversations_count or 0,
            "last_activity": last_activity,
        }

    async def get_timeline(
        self, project_id: str, limit: int = 50, offset: int = 0,
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []

        conv_result = await self._session.execute(
            select(ProjectConversation)
            .where(ProjectConversation.project_id == project_id)
            .order_by(ProjectConversation.created_at.desc())
            .limit(limit)
        )
        for conv in conv_result.scalars().all():
            entries.append({
                "id": conv.id,
                "type": "prompt",
                "title": "User Prompt",
                "description": conv.prompt[:200],
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "metadata": {"prompt": conv.prompt},
            })

        output_result = await self._session.execute(
            select(ProjectOutput)
            .where(ProjectOutput.project_id == project_id)
            .order_by(ProjectOutput.created_at.desc())
            .limit(limit)
        )
        for out in output_result.scalars().all():
            entries.append({
                "id": out.id,
                "type": "output",
                "title": out.title or f"{out.content_type} output",
                "description": (out.content or "")[:200],
                "created_at": out.created_at.isoformat() if out.created_at else None,
                "metadata": {
                    "content_type": out.content_type,
                    "workflow_execution_id": out.workflow_execution_id,
                },
            })

        mem_result = await self._session.execute(
            select(ProjectMemory)
            .where(ProjectMemory.project_id == project_id)
            .order_by(ProjectMemory.created_at.desc())
            .limit(limit)
        )
        for mem in mem_result.scalars().all():
            entries.append({
                "id": mem.id,
                "type": "memory",
                "title": f"Memory: {mem.memory_type}",
                "description": mem.content[:200],
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
                "metadata": {
                    "memory_type": mem.memory_type,
                    "confidence_score": mem.confidence_score,
                },
            })

        entries.sort(key=lambda e: e["created_at"] or "", reverse=True)
        return entries[offset:offset + limit]

    async def _get_pin(self, memory_id: str) -> PinnedProjectMemory | None:
        stmt = select(PinnedProjectMemory).where(
            PinnedProjectMemory.memory_id == memory_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.project.repository import ProjectRepository
from app.infrastructure.models.project import ProjectInstruction

logger = logging.getLogger(__name__)


class ProjectInstructionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProjectRepository(session)

    async def create_instruction(
        self, project_id: str, title: str, content: str, 
        priority: int = 0, created_by: str | None = None
    ) -> ProjectInstruction:
        return await self._repo.create_instruction(
            project_id=project_id, title=title, content=content, 
            priority=priority, created_by=created_by
        )

    async def get_instructions(self, project_id: str, enabled_only: bool = True) -> list[ProjectInstruction]:
        return await self._repo.get_instructions(project_id, enabled_only=enabled_only)

    async def update_instruction(self, instruction_id: str, **kwargs: Any) -> ProjectInstruction | None:
        return await self._repo.update_instruction(instruction_id, **kwargs)

    async def delete_instruction(self, instruction_id: str) -> bool:
        return await self._repo.delete_instruction(instruction_id)

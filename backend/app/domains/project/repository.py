from __future__ import annotations

<<<<<<< HEAD
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.project import (
    PinnedProjectMemory,
    Project,
    ProjectConversation,
    ProjectInstruction,
    ProjectMemory,
    ProjectOutput,
    ProjectAllowedSource,
    ProjectBlockedSource,
    ProjectChatMessage,
    ProjectChatSession,
    ProjectResearchPreference,
    ProjectSourcePolicy,
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
            stmt = select(Project).where(Project.owner_id == owner_id)
            if not include_archived:
                stmt = stmt.where(text("archived = false"))
            stmt = stmt.order_by(Project.updated_at.desc())
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception:
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

    async def create_instruction(
        self, project_id: str, title: str, content: str, 
        priority: int = 0, created_by: str | None = None
    ) -> ProjectInstruction:
        instruction = ProjectInstruction(
            project_id=project_id,
            title=title,
            instruction_content=content,
            priority=priority,
            created_by=created_by,
        )
        self._session.add(instruction)
        await self._session.flush()
        return instruction

    async def get_instructions(self, project_id: str, enabled_only: bool = True) -> list[ProjectInstruction]:
        stmt = select(ProjectInstruction).where(ProjectInstruction.project_id == project_id)
        if enabled_only:
            stmt = stmt.where(ProjectInstruction.enabled == True)
        stmt = stmt.order_by(ProjectInstruction.priority.desc(), ProjectInstruction.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_instruction(self, instruction_id: str, **kwargs: Any) -> ProjectInstruction | None:
        instruction = await self._session.get(ProjectInstruction, instruction_id)
        if not instruction:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(instruction, key):
                setattr(instruction, key, value)
        await self._session.flush()
        return instruction

    async def delete_instruction(self, instruction_id: str) -> bool:
        instruction = await self._session.get(ProjectInstruction, instruction_id)
        if not instruction:
            return False
        await self._session.delete(instruction)
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
        from app.infrastructure.models.pipeline import PipelineRun
        from app.infrastructure.models.project import ProjectInstruction, ProjectChatSession
        from app.infrastructure.models.skills import ProjectSkill

        outputs_count = await self._session.scalar(
            select(func.count()).where(ProjectOutput.project_id == project_id)
        )
        memories_count = await self._session.scalar(
            select(func.count()).where(ProjectMemory.project_id == project_id)
        )
        conversations_count = await self._session.scalar(
            select(func.count()).where(ProjectConversation.project_id == project_id)
        )
        instructions_count = await self._session.scalar(
            select(func.count()).where(ProjectInstruction.project_id == project_id)
        )
        skills_count = await self._session.scalar(
            select(func.count()).where(ProjectSkill.project_id == project_id)
        )
        allowed_count = await self._session.scalar(
            select(func.count()).where(ProjectAllowedSource.project_id == project_id)
        )
        blocked_count = await self._session.scalar(
            select(func.count()).where(ProjectBlockedSource.project_id == project_id)
        )
        chat_sessions_count = await self._session.scalar(
            select(func.count()).where(ProjectChatSession.project_id == project_id)
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

        workflow_ids_stmt = (
            select(ProjectOutput.workflow_execution_id)
            .where(ProjectOutput.project_id == project_id)
            .where(ProjectOutput.workflow_execution_id.isnot(None))
        )
        workflow_ids = [
            row[0] for row in
            (await self._session.execute(workflow_ids_stmt)).all()
        ]

        total_tokens = 0
        recent_workflows = []
        if workflow_ids:
            pipe_stmt = (
                select(PipelineRun)
                .where(PipelineRun.workflow_id.in_(workflow_ids))
                .order_by(PipelineRun.created_at.desc())
            )
            pipe_result = await self._session.execute(pipe_stmt)
            pipeline_runs = list(pipe_result.scalars().all())
            total_tokens = sum(
                p.total_tokens_used or 0 for p in pipeline_runs
            )
            recent_workflows = [
                {
                    "workflow_id": p.workflow_id,
                    "topic": p.topic,
                    "status": p.status,
                    "total_tokens_used": p.total_tokens_used or 0,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in pipeline_runs[:10]
            ]

        total_cost = total_tokens * 0.000002

        return {
            "total_outputs": outputs_count or 0,
            "total_memories": memories_count or 0,
            "total_sources": conversations_count or 0,
            "total_tokens_used": total_tokens,
            "total_cost": round(total_cost, 4),
            "last_activity": last_activity,
            "recent_workflows": recent_workflows,
            "instructions_count": instructions_count or 0,
            "skills_count": skills_count or 0,
            "allowed_sources_count": allowed_count or 0,
            "blocked_sources_count": blocked_count or 0,
            "chat_sessions_count": chat_sessions_count or 0,
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

    async def create_chat_session(self, project_id: str, created_by: str | None = None) -> ProjectChatSession:
        session = ProjectChatSession(
            project_id=project_id,
            created_by=created_by,
        )
        self._session.add(session)
        await self._session.flush()
        return session

    async def get_chat_session(self, session_id: str) -> ProjectChatSession | None:
        return await self._session.get(ProjectChatSession, session_id)

    async def get_chat_sessions(self, project_id: str, limit: int = 50, offset: int = 0) -> list[ProjectChatSession]:
        stmt = (
            select(ProjectChatSession)
            .where(ProjectChatSession.project_id == project_id)
            .order_by(ProjectChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_chat_message(self, session_id: str, role: str, content: str) -> ProjectChatMessage:
        message = ProjectChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_chat_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> list[ProjectChatMessage]:
        stmt = (
            select(ProjectChatMessage)
            .where(ProjectChatMessage.session_id == session_id)
            .order_by(ProjectChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_chat_session(self, session_id: str) -> bool:
        session = await self._session.get(ProjectChatSession, session_id)
        if not session:
            return False
        await self._session.delete(session)
        await self._session.flush()
        return True

    async def _get_pin(self, memory_id: str) -> PinnedProjectMemory | None:
        stmt = select(PinnedProjectMemory).where(
            PinnedProjectMemory.memory_id == memory_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_source_policy(self, project_id: str) -> ProjectSourcePolicy | None:
        return await self._session.get(ProjectSourcePolicy, project_id) # simplified if id == project_id or use select

    async def update_source_policy(self, project_id: str, **kwargs: Any) -> ProjectSourcePolicy | None:
        policy = await self.get_source_policy(project_id)
        if not policy:
            policy = ProjectSourcePolicy(project_id=project_id, policy_name="Default Policy")
            self._session.add(policy)
        for key, value in kwargs.items():
            if value is not None and hasattr(policy, key):
                setattr(policy, key, value)
        await self._session.flush()
        return policy

    async def get_allowed_sources(self, project_id: str) -> list[ProjectAllowedSource]:
        stmt = select(ProjectAllowedSource).where(ProjectAllowedSource.project_id == project_id)
        stmt = stmt.order_by(ProjectAllowedSource.priority.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_allowed_source(self, project_id: str, name: str, domain: str | None = None, priority: int = 0) -> ProjectAllowedSource:
        source = ProjectAllowedSource(project_id=project_id, source_name=name, source_domain=domain, priority=priority)
        self._session.add(source)
        await self._session.flush()
        return source

    async def remove_allowed_source(self, source_id: str) -> bool:
        source = await self._session.get(ProjectAllowedSource, source_id)
        if not source:
            return False
        await self._session.delete(source)
        await self._session.flush()
        return True

    async def get_blocked_sources(self, project_id: str) -> list[ProjectBlockedSource]:
        stmt = select(ProjectBlockedSource).where(ProjectBlockedSource.project_id == project_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_blocked_source(self, project_id: str, name: str, domain: str | None = None, reason: str | None = None) -> ProjectBlockedSource:
        source = ProjectBlockedSource(project_id=project_id, source_name=name, source_domain=domain, reason=reason)
        self._session.add(source)
        await self._session.flush()
        return source

    async def remove_blocked_source(self, source_id: str) -> bool:
        source = await self._session.get(ProjectBlockedSource, source_id)
        if not source:
            return False
        await self._session.delete(source)
        await self._session.flush()
        return True

    async def get_research_preferences(self, project_id: str) -> ProjectResearchPreference | None:
        stmt = select(ProjectResearchPreference).where(ProjectResearchPreference.project_id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_research_preferences(self, project_id: str, **kwargs: Any) -> ProjectResearchPreference | None:
        prefs = await self.get_research_preferences(project_id)
        if not prefs:
            prefs = ProjectResearchPreference(project_id=project_id)
            self._session.add(prefs)
        for key, value in kwargs.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        await self._session.flush()
        return prefs

=======
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.project.models import Project, ProjectMemory, PinnedProjectMemory
from app.infrastructure.repositories.base import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(
        self, 
        owner_id: str, 
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Project]:
        stmt = select(Project).where(Project.owner_id == owner_id)
        if not include_archived:
            stmt = stmt.where(Project.archived == False)
        stmt = stmt.order_by(Project.updated_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def update(self, project_id: str, **kwargs) -> Optional[Project]:
        if not kwargs:
            return await self.get_by_id(project_id)
        
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(**kwargs)
            .returning(Project)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, project_id: str) -> bool:
        project = await self.get_by_id(project_id)
        if project:
            await self.session.delete(project)
            return True
        return False

    async def search_memories(
        self, 
        project_id: str, 
        query_vector: List[float], 
        limit: int = 10
    ) -> List[Tuple[ProjectMemory, float]]:
        """
        Perform semantic search using cosine distance.
        Returns a list of (ProjectMemory, distance) tuples.
        """
        # The <=> operator in pgvector performs cosine distance
        stmt = (
            select(ProjectMemory, ProjectMemory.embedding.cosine_distance(query_vector).label("distance"))
            .where(ProjectMemory.project_id == project_id)
            .order_by("distance")
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_pinned_memories(self, project_id: str) -> List[ProjectMemory]:
        """Retrieve all memories pinned for a specific project, ordered by priority."""
        stmt = (
            select(ProjectMemory)
            .join(PinnedProjectMemory, ProjectMemory.id == PinnedProjectMemory.memory_id)
            .where(PinnedProjectMemory.project_id == project_id)
            .order_by(PinnedProjectMemory.priority.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
>>>>>>> 009b035 (Implement Phase 8: Project Intelligence Layer)

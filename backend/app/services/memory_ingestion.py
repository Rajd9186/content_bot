from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.project import (
    ProjectConversation,
    ProjectMemory,
    ProjectOutput,
)

logger = logging.getLogger(__name__)

MEMORY_TYPES = {
    "prompt",
    "output",
    "research",
    "fact",
    "user_preference",
    "decision",
    "summary",
}


class MemoryIngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ingest_prompt(
        self, project_id: str, prompt: str, metadata: dict[str, Any] | None = None,
        response: str | None = None,
    ) -> ProjectMemory:
        conversation = ProjectConversation(
            project_id=project_id,
            prompt=prompt,
            response=response,
            user_metadata=metadata,
        )
        self._session.add(conversation)

        memory = await self._create_memory(project_id, "prompt", prompt)
        return memory

    async def ingest_output(
        self,
        project_id: str,
        workflow_execution_id: str | None,
        title: str | None,
        content: str,
        content_type: str = "article",
    ) -> ProjectMemory:
        output = ProjectOutput(
            project_id=project_id,
            workflow_execution_id=workflow_execution_id,
            title=title,
            content=content,
            content_type=content_type,
        )
        self._session.add(output)

        text = f"{title or ''} {content}"
        memory = await self._create_memory(project_id, "output", text)
        return memory

    async def ingest_research(
        self, project_id: str, research_data: dict[str, Any]
    ) -> list[ProjectMemory]:
        memories = []
        for _key, value in research_data.items():
            text = str(value)
            if len(text) > 20:
                memory = await self._create_memory(project_id, "research", text[:5000])
                memories.append(memory)
        return memories

    async def ingest_fact_check(
        self, project_id: str, fact_results: dict[str, Any]
    ) -> list[ProjectMemory]:
        memories = []
        for claim, result in fact_results.items() if isinstance(fact_results, dict) else []:
            text = f"Claim: {claim} - Result: {result}"
            memory = await self._create_memory(project_id, "fact", text)
            memories.append(memory)
        return memories

    async def ingest_user_feedback(
        self, project_id: str, feedback: str
    ) -> ProjectMemory:
        memory = await self._create_memory(project_id, "user_preference", feedback)
        return memory

    async def ingest_decision(
        self, project_id: str, decision: str
    ) -> ProjectMemory:
        memory = await self._create_memory(project_id, "decision", decision)
        return memory

    async def ingest_workflow_completion(
        self,
        project_id: str,
        prompt: str,
        final_content: str | None,
        research_data: dict[str, Any] | None,
        fact_check_results: dict[str, Any] | None,
        workflow_execution_id: str | None = None,
        content_type: str = "article",
        title: str | None = None,
    ) -> list[ProjectMemory]:
        memories = []
        memories.append(await self.ingest_prompt(
            project_id, prompt,
            response=final_content[:5000] if final_content else None,
        ))
        if final_content:
            memories.append(
                await self.ingest_output(
                    project_id, workflow_execution_id, title, final_content, content_type
                )
            )
        if research_data:
            memories.extend(await self.ingest_research(project_id, research_data))
        if fact_check_results:
            memories.extend(await self.ingest_fact_check(project_id, fact_check_results))
        return memories

    async def _create_memory(
        self, project_id: str, memory_type: str, content: str
    ) -> ProjectMemory:
        from app.services.embedding import embedding_service
        embedding = await embedding_service.generate(content[:5000])
        memory = ProjectMemory(
            project_id=project_id,
            memory_type=memory_type,
            content=content[:10000],
            confidence_score=1.0,
            embedding=embedding,
        )
        self._session.add(memory)
        return memory

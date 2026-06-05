from __future__ import annotations

import logging
from typing import Any

from app.agents.provider.base import ProviderRequest, ProviderResponse
from app.agents.provider.factory import ProviderFactory
from app.domains.project.repository import ProjectRepository
from app.services.semantic_retrieval import SemanticRetrievalService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProjectCopilotAgent:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._project_repo = ProjectRepository(session)
        self._retrieval = SemanticRetrievalService(session)
        self._provider_factory = ProviderFactory()

    async def answer_query(
        self, project_id: str, query: str, user_id: str | None = None
    ) -> dict[str, Any]:
        logger.info("Project Copilot: answering query for project %s: %s", project_id, query)
        
        # 1. Retrieve Context
        # Memories
        memories = await self._retrieval.search_memories(project_id, query, top_k=10)
        # Outputs
        outputs = await self._project_repo.get_outputs(project_id, limit=10)
        # Instructions
        instructions = await self._project_repo.get_instructions(project_id)
        
        # 2. Build Prompt
        system_prompt = (
            "You are the Project Copilot, an expert AI assistant for this specific project. "
            "Your goal is to answer user questions based ONLY on the provided project context. "
            "If the information is not available in the context, state that you don't know. "
            "Be concise, factual, and professional."
        )
        
        context_parts = []
        if instructions:
            context_parts.append("PROJECT INSTRUCTIONS:\n" + "\n".join([i.instruction_content for i in instructions]))
        if memories:
            context_parts.append("RELEVANT MEMORIES:\n" + "\n".join([m["content"] for m in memories]))
        if outputs:
            context_parts.append("PREVIOUS OUTPUTS:\n" + "\n".join([f"Title: {o.title}\nContent: {o.content[:500]}..." for o in outputs]))
            
        context_text = '\n'.join(context_parts)
        user_prompt = f"Project Context:\n{context_text}\n\nUser Query: {query}"
        
        # 3. Execute via LLM
        provider = self._provider_factory.get_or_create("openai", "gpt-4o")
        request = ProviderRequest(
            model="gpt-4o",
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
            max_tokens=1000,
        )
        
        response = await provider.execute_with_retry(request)
        
        if not response.success:
            return {"error": response.error, "status": "failed"}
            
        return {
            "answer": response.content,
            "context_used": {
                "memories_count": len(memories),
                "outputs_count": len(outputs),
                "instructions_count": len(instructions),
            },
            "status": "success"
        }
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from app.domains.project.models import ProjectMemory, PinnedProjectMemory
from app.services.embedding_service import EmbeddingService
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

class ContextAssemblyEngine:
    """
    Engine responsible for assembling the final augmented prompt 
    by combining current context, semantic memories, and pinned knowledge.
    """
    def __init__(self, uow: UnitOfWork, embedding_service: EmbeddingService):
        self.uow = uow
        self.embedding_service = embedding_service

    async def assemble_context(self, project_id: str, user_prompt: str) -> Dict[str, Any]:
        """
        Retrieve all relevant project intelligence and package it for the LLM.
        """
        # 1. Generate embedding for the current prompt
        query_vector = await self.embedding_service.generate_embedding(user_prompt)

        # 2. Semantic Retrieval
        semantic_memories = await self.uow.projects.search_memories(
            project_id=project_id, 
            query_vector=query_vector, 
            limit=5
        )
        
        # 3. Pinned Knowledge Retrieval
        pinned_memories = await self.uow.projects.get_pinned_memories(project_id)

        # 4. Recent Project Outputs (for style/consistency)
        # Assume we get last 3 outputs
        recent_outputs = await self.uow.projects.get_recent_outputs(project_id, limit=3)

        # Build the context package
        context_package = {
            "semantic_memories": [m.content for m, dist in semantic_memories],
            "pinned_knowledge": [m.content for m in pinned_memories],
            "recent_context": [o.content[:500] for o in recent_outputs], # Snippets
            "raw_prompt": user_prompt
        }

        return context_package

    def format_as_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Convert the context package into a human-readable system prompt addition.
        """
        parts = ["### PROJECT KNOWLEDGE BASE"]
        
        if context["pinned_knowledge"]:
            parts.append("\n**CRITICAL PINNED KNOWLEDGE:**")
            parts.extend([f"- {k}" for k in context["pinned_knowledge"]])
            
        if context["semantic_memories"]:
            parts.append("\n**RELEVANT PAST FINDINGS:**")
            parts.extend([f"- {m}" for m in context["semantic_memories"]])
            
        if context["recent_context"]:
            parts.append("\n**RECENTLY GENERATED CONTENT (for style consistency):**")
            parts.extend([f"- {c}" for c in context["recent_context"]])
            
        return "\n".join(parts)

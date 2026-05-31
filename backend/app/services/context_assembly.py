from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.semantic_retrieval import SemanticRetrievalService

logger = logging.getLogger(__name__)


class ContextAssemblyEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._retrieval = SemanticRetrievalService(session)

    async def assemble(
        self,
        project_id: str,
        prompt: str,
        top_k: int = 10,
        similarity_threshold: float = 0.0,
    ) -> dict[str, Any]:
        memories = await self._retrieval.search_memories(
            project_id, prompt, top_k, similarity_threshold,
        )
        pinned = await self._retrieval.get_pinned_memories(project_id)
        related_outputs = await self._retrieval.search_related_outputs(
            project_id, prompt, top_k=5,
        )
        related_prompts = await self._retrieval.search_related_prompts(
            project_id, prompt, top_k=5,
        )

        project_context = {
            "relevant_memories": [
                {
                    "type": m["memory_type"],
                    "content": m["content"],
                    "similarity": m.get("similarity", 0),
                    "pinned": m.get("pinned", False),
                }
                for m in memories
            ],
            "pinned_knowledge": [
                {
                    "type": m["memory_type"],
                    "content": m["content"],
                    "priority": m.get("priority", 0),
                }
                for m in pinned
            ],
            "related_outputs": [
                {
                    "title": o.get("title"),
                    "content_type": o.get("content_type"),
                    "content_preview": o.get("content"),
                }
                for o in related_outputs
            ],
            "previous_prompts": [
                {"prompt": p["prompt"]} for p in related_prompts
            ],
        }

        enhanced_prompt = self._build_enhanced_prompt(prompt, project_context)

        return {
            "project_context": project_context,
            "prompt": enhanced_prompt,
            "relevant_memories": memories,
            "pinned_memories": pinned,
            "related_outputs": related_outputs,
            "related_prompts": related_prompts,
        }

    def _build_enhanced_prompt(
        self, original_prompt: str, context: dict[str, Any]
    ) -> str:
        parts = [original_prompt]
        pinned = context.get("pinned_knowledge", [])
        if pinned:
            pinned_text = "\n".join(
                f"- [{p['type']}] {p['content']}" for p in pinned
            )
            parts.append(f"\n\nPinned Knowledge:\n{pinned_text}")

        memories = context.get("relevant_memories", [])
        if memories:
            memory_text = "\n".join(
                f"- [{m['type']}] {m['content']}" for m in memories[:5]
            )
            parts.append(f"\n\nRelevant Context:\n{memory_text}")

        outputs = context.get("related_outputs", [])
        if outputs:
            parts.append(
                "\n\nPrevious outputs exist for this project. "
                "Ensure consistency with existing content."
            )

        return "\n".join(parts)

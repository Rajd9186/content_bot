from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.project import (
    PinnedProjectMemory,
    ProjectConversation,
    ProjectMemory,
    ProjectOutput,
)
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class SemanticRetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_memories(
        self,
        project_id: str,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.0,
        memory_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query_embedding = await embedding_service.generate(query)
        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        type_filter = ""
        params: dict[str, Any] = {
            "project_id": project_id,
            "threshold": similarity_threshold,
            "top_k": top_k,
        }
        if memory_type:
            type_filter = "AND memory_type = :memory_type"
            params["memory_type"] = memory_type

        sql = text(f"""
            SELECT id, project_id, memory_type, content, confidence_score, created_at,
                   1 - (embedding <=> :query_embedding::vector) AS similarity
            FROM project_memories
            WHERE project_id = :project_id
              AND embedding IS NOT NULL
              AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
              {type_filter}
            ORDER BY similarity DESC
            LIMIT :top_k
        """)
        import json as _json
        result = await self._session.execute(
            sql,
            {"query_embedding": embedding_str, **params},
        )
        rows = result.all()

        results = []
        for row in rows:
            pinned = await self._is_pinned(row.id)
            results.append({
                "id": row.id,
                "project_id": row.project_id,
                "memory_type": row.memory_type,
                "content": row.content,
                "confidence_score": row.confidence_score,
                "similarity": float(row.similarity) if row.similarity is not None else 0.0,
                "pinned": pinned,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

        return results[:top_k]

    async def get_pinned_memories(
        self, project_id: str
    ) -> list[dict[str, Any]]:
        stmt = (
            select(PinnedProjectMemory)
            .where(PinnedProjectMemory.project_id == project_id)
            .order_by(PinnedProjectMemory.priority.desc())
        )
        result = await self._session.execute(stmt)
        pinned_records = result.scalars().all()

        memories = []
        for pr in pinned_records:
            memory = await self._session.get(ProjectMemory, pr.memory_id)
            if memory:
                memories.append({
                    "id": memory.id,
                    "project_id": memory.project_id,
                    "memory_type": memory.memory_type,
                    "content": memory.content,
                    "confidence_score": memory.confidence_score,
                    "pinned": True,
                    "priority": pr.priority,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None,
                })
        return memories

    async def search_related_outputs(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(ProjectOutput)
            .where(ProjectOutput.project_id == project_id)
            .order_by(ProjectOutput.created_at.desc())
        )
        result = await self._session.execute(stmt)
        outputs = result.scalars().all()

        query_embedding = await embedding_service.generate(query)
        scored = []
        for output in outputs:
            text = f"{output.title or ''} {output.content or ''}"
            emb = await embedding_service.generate(text[:5000])
            sim = embedding_service.cosine_similarity(query_embedding, emb)
            scored.append((sim, output))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": o.id,
                "project_id": o.project_id,
                "workflow_execution_id": o.workflow_execution_id,
                "title": o.title,
                "content": o.content[:500] if o.content else None,
                "content_type": o.content_type,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for sim, o in scored[:top_k]
        ]

    async def search_related_prompts(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(ProjectConversation)
            .where(ProjectConversation.project_id == project_id)
            .order_by(ProjectConversation.created_at.desc())
        )
        result = await self._session.execute(stmt)
        conversations = result.scalars().all()

        query_embedding = await embedding_service.generate(query)
        scored = []
        for conv in conversations:
            emb = await embedding_service.generate(conv.prompt[:5000])
            sim = embedding_service.cosine_similarity(query_embedding, emb)
            scored.append((sim, conv))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": c.id,
                "project_id": c.project_id,
                "prompt": c.prompt,
                "user_metadata": c.user_metadata,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for sim, c in scored[:top_k]
        ]

    async def _is_pinned(self, memory_id: str) -> bool:
        stmt = select(PinnedProjectMemory).where(
            PinnedProjectMemory.memory_id == memory_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

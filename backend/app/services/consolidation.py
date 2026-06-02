from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session_factory
from app.infrastructure.models.project import Project, ProjectMemory
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)

SIMILARITY_DEDUP_THRESHOLD = 0.92
SIMILARITY_CLUSTER_THRESHOLD = 0.85


class ConsolidationService:

    async def deduplicate_memories(self, project_id: str) -> int:
        async with async_session_factory() as session:
            memories = await self._get_project_memories(session, project_id)
            if len(memories) < 2:
                return 0

            to_remove: set[str] = set()
            for i in range(len(memories)):
                if memories[i].id in to_remove:
                    continue
                emb_i = memories[i].embedding
                if not emb_i:
                    continue
                for j in range(i + 1, len(memories)):
                    if memories[j].id in to_remove:
                        continue
                    emb_j = memories[j].embedding
                    if not emb_j:
                        continue
                    sim = embedding_service.cosine_similarity(emb_i, emb_j)
                    if sim >= SIMILARITY_DEDUP_THRESHOLD:
                        to_remove.add(memories[j].id)

            for mem_id in to_remove:
                mem = await session.get(ProjectMemory, mem_id)
                if mem:
                    await session.delete(mem)

            await session.commit()
            removed = len(to_remove)
            if removed:
                logger.info("Deduplicated %d memories for project %s", removed, project_id)
            return removed

    async def summarize_research_thread(self, project_id: str) -> int:
        async with async_session_factory() as session:
            memories = await self._get_project_memories(session, project_id)
            if len(memories) < 3:
                return 0

            clusters: list[list[ProjectMemory]] = []
            assigned: set[str] = set()

            for i in range(len(memories)):
                if memories[i].id in assigned:
                    continue
                emb_i = memories[i].embedding
                if not emb_i:
                    continue
                cluster = [memories[i]]
                assigned.add(memories[i].id)
                for j in range(i + 1, len(memories)):
                    if memories[j].id in assigned:
                        continue
                    emb_j = memories[j].embedding
                    if not emb_j:
                        continue
                    sim = embedding_service.cosine_similarity(emb_i, emb_j)
                    if sim >= SIMILARITY_CLUSTER_THRESHOLD:
                        cluster.append(memories[j])
                        assigned.add(memories[j].id)
                if len(cluster) >= 3:
                    clusters.append(cluster)

            summaries_created = 0
            for cluster in clusters:
                combined = "\n".join(
                    f"[{m.memory_type}] {m.content[:200]}"
                    for m in cluster
                )
                summary_memory = ProjectMemory(
                    project_id=project_id,
                    memory_type="summary",
                    content=f"Consolidated Research Summary:\n{combined[:5000]}",
                    confidence_score=1.0,
                    embedding=await embedding_service.generate(combined[:5000]),
                )
                session.add(summary_memory)
                summaries_created += 1

            await session.commit()
            if summaries_created:
                logger.info("Created %d summary memories for project %s", summaries_created, project_id)
            return summaries_created

    async def consolidate_all_projects(self) -> dict[str, int]:
        async with async_session_factory() as session:
            result = await session.execute(select(Project.id))
            project_ids = [row[0] for row in result.all()]

        total_removed = 0
        total_summaries = 0
        for pid in project_ids:
            try:
                removed = await self.deduplicate_memories(pid)
                total_removed += removed
                summaries = await self.summarize_research_thread(pid)
                total_summaries += summaries
            except Exception as e:
                logger.error("Consolidation failed for project %s: %s", pid, e)

        return {"deduplicated": total_removed, "summaries_created": total_summaries}

    async def _get_project_memories(
        self, session: AsyncSession, project_id: str,
    ) -> list[ProjectMemory]:
        stmt = (
            select(ProjectMemory)
            .where(ProjectMemory.project_id == project_id)
            .where(ProjectMemory.embedding.isnot(None))
            .order_by(ProjectMemory.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


consolidation_service = ConsolidationService()

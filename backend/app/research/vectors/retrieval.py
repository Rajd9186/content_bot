from __future__ import annotations

import logging
from typing import Any, Optional

from app.research.models import ResearchSource
from app.research.vectors.embeddings import EmbeddingService, embedding_service

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Semantic retrieval using vector similarity"""
    
    def __init__(self) -> None:
        self._embeddings_service: EmbeddingService = embedding_service
        self._index: dict[str, list[float]] = {}
        self._sources: dict[str, ResearchSource] = {}

    async def index_source(self, source: ResearchSource) -> None:
        text = f"{source.title} {source.snippet}"
        embedding = await self._embeddings_service.generate(text)
        
        if embedding:
            source_id = source.content_hash or source.canonical_url
            self._index[source_id] = embedding
            self._sources[source_id] = source

    async def index_batch(self, sources: list[ResearchSource]) -> None:
        for source in sources:
            await self.index_source(source)

    async def search(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5,
    ) -> list[tuple[ResearchSource, float]]:
        query_embedding = await self._embeddings_service.generate(query)
        if not query_embedding:
            return []
        
        results = []
        for source_id, embedding in self._index.items():
            similarity = self._embeddings_service.similarity(
                query_embedding, embedding
            )
            
            if similarity >= min_similarity:
                source = self._sources.get(source_id)
                if source:
                    results.append((source, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def clear(self) -> None:
        self._index.clear()
        self._sources.clear()


vector_retriever = VectorRetriever()
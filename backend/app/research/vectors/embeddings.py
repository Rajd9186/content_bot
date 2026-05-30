from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Simple embedding service for research vectors"""

    def __init__(self) -> None:
        self._cache: dict[str, list[float]] = {}
        self._dimension = 384

    async def generate(self, text: str) -> list[float] | None:
        if text in self._cache:
            return self._cache[text]

        try:
            embedding = self._generate_mock_embedding(text)
            self._cache[text] = embedding
            return embedding
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            return None

    def _generate_mock_embedding(self, text: str) -> list[float]:
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = [
            (hash_bytes[i % len(hash_bytes)] / 255.0) * 2 - 1
            for i in range(self._dimension)
        ]
        return embedding

    async def generate_batch(
        self,
        texts: list[str],
    ) -> list[list[float] | None]:
        embeddings = []
        for text in texts:
            emb = await self.generate(text)
            embeddings.append(emb)
        return embeddings

    def similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        if len(embedding1) != len(embedding2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


embedding_service = EmbeddingService()

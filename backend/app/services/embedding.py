from __future__ import annotations

import hashlib
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        self._cache: dict[str, list[float]] = {}

    async def generate(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        embedding = self._generate_mock_embedding(text)
        self._cache[text] = embedding
        return embedding

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.generate(t) for t in texts]

    def _generate_mock_embedding(self, text: str) -> list[float]:
        hash_bytes = hashlib.sha256(text.encode()).digest()
        return [
            (hash_bytes[i % len(hash_bytes)] / 255.0) * 2 - 1
            for i in range(self._dimension)
        ]

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


embedding_service = EmbeddingService()

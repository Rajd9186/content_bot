from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

OPENAI_DIMENSION = 1536


class EmbeddingService:
    def __init__(self, dimension: int = OPENAI_DIMENSION) -> None:
        self._dimension = dimension
        self._cache: dict[str, list[float]] = {}
        self._openai_client: Any = None
        self._openai_available = self._init_openai()

    def _init_openai(self) -> bool:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.info("No OPENAI_API_KEY set, using mock embeddings")
            return False
        try:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI embedding client initialized")
            return True
        except Exception as e:
            logger.warning("Failed to init OpenAI client: %s", e)
            return False

    async def generate(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        if self._openai_available and self._openai_client:
            try:
                resp = await self._openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                embedding = resp.data[0].embedding
                self._cache[text] = embedding
                return embedding
            except Exception as e:
                logger.warning("OpenAI embedding failed, falling back to mock: %s", e)
        embedding = self._generate_mock_embedding(text)
        self._cache[text] = embedding
        return embedding

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        uncached_texts = [t for t in texts if t not in self._cache]
        if uncached_texts and self._openai_available and self._openai_client:
            try:
                resp = await self._openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=uncached_texts,
                )
                for i, text in enumerate(uncached_texts):
                    self._cache[text] = resp.data[i].embedding
            except Exception as e:
                logger.warning("OpenAI batch embedding failed, falling back: %s", e)
                for text in uncached_texts:
                    self._cache[text] = self._generate_mock_embedding(text)
        else:
            for text in uncached_texts:
                self._cache[text] = self._generate_mock_embedding(text)
        return [self._cache[t] for t in texts]

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _generate_mock_embedding(self, text: str) -> list[float]:
        hash_bytes = hashlib.sha256(text.encode()).digest()
        return [
            float((hash_bytes[i % len(hash_bytes)] / 255.0) * 2 - 1)
            for i in range(self._dimension)
        ]


embedding_service = EmbeddingService()

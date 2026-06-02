from __future__ import annotations

import hashlib
import logging

from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600

CACHEABLE_TASKS = frozenset({
    "seo_generation",
    "outline_generation",
    "topic_classification",
    "keyword_extraction",
    "meta_description",
    "heading_structure",
    "source_ranking",
})


def make_cache_key(prompt: str, task_type: str, provider: str | None = None) -> str:
    """
    Provider-independent cache key.

    Hash of prompt + task_type (provider not included so
    cache hits across providers).
    """
    content = f"{task_type}:{prompt.strip()}"
    h = hashlib.sha256(content.encode()).hexdigest()[:32]
    return f"llm:cache:{task_type}:{h}"


class LLMResponseCache:
    """
    Cache LLM responses for deterministic tasks.

    Cacheable task types (Feature 8):
    - seo_generation
    - outline_generation
    - topic_classification
    - keyword_extraction
    - meta_description
    - heading_structure
    - source_ranking
    """

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds

    async def get(self, prompt: str, task_type: str) -> str | None:
        """Get cached response if available."""
        if task_type not in CACHEABLE_TASKS:
            return None

        if not self._redis_ok():
            return None

        key = make_cache_key(prompt, task_type)
        try:
            val = await redis_client.cache_get(key)
            if val:
                logger.debug("Cache HIT for task=%s key=%s", task_type, key[:20])
                return val
            logger.debug("Cache MISS for task=%s key=%s", task_type, key[:20])
            return None
        except Exception as e:
            logger.warning("Cache get failed: %s", e)
            return None

    async def set(self, prompt: str, task_type: str, response: str) -> None:
        """Cache a response."""
        if task_type not in CACHEABLE_TASKS:
            return

        if not self._redis_ok():
            return

        key = make_cache_key(prompt, task_type)
        try:
            await redis_client.cache_set(key, response, ttl_seconds=self._ttl)
            logger.debug("Cache SET for task=%s key=%s ttl=%d", task_type, key[:20], self._ttl)
        except Exception as e:
            logger.warning("Cache set failed: %s", e)

    async def invalidate(self, prompt: str, task_type: str) -> None:
        """Remove a specific cached entry."""
        if not self._redis_ok():
            return
        key = make_cache_key(prompt, task_type)
        try:
            await redis_client.cache_delete(key)
        except Exception as e:
            logger.warning("Cache invalidate failed: %s", e)

    async def clear_task_type(self, task_type: str) -> None:
        """Clear all cached entries for a task type (use sparingly)."""
        if not self._redis_ok():
            return
        try:
            pattern = f"llm:cache:{task_type}:*"
            await redis_client.cache_delete_pattern(pattern)
        except Exception as e:
            logger.warning("Cache clear failed: %s", e)

    def _redis_ok(self) -> bool:
        return redis_client._client is not None


llm_cache = LLMResponseCache()

import uuid
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.log_config.logger import get_logger


class InMemoryCache:
    def __init__(self, max_size: int = 500):
        self._store: dict[str, Any] = {}
        self._accessed: dict[str, datetime] = {}
        self.max_size = max_size
        self.logger = get_logger(self.__class__.__name__)

    def get(self, key: str) -> Any | None:
        val = self._store.get(key)
        if val is not None:
            self._accessed[key] = datetime.now(timezone.utc)
        return val

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self.max_size:
            oldest = min(self._accessed, key=lambda k: self._accessed.get(k, datetime.min))
            del self._store[oldest]
            del self._accessed[oldest]
        self._store[key] = value
        self._accessed[key] = datetime.now(timezone.utc)

    def search(self, prefix: str) -> list[tuple[str, Any]]:
        return [(k, v) for k, v in self._store.items() if k.startswith(prefix)]

    def clear(self) -> None:
        self._store.clear()
        self._accessed.clear()


class AgentMemoryService:
    def __init__(self, memory_repo=None):
        self.cache = InMemoryCache()
        self.repo = memory_repo
        self.logger = get_logger(self.__class__.__name__)

    async def store(
        self,
        agent_name: str,
        key: str,
        value: dict,
        memory_type: str = "research",
        project_id: UUID | str | None = None,
        relevance_score: float | None = None,
    ) -> None:
        cache_key = f"{agent_name}:{key}"
        self.cache.set(cache_key, value)
        if self.repo:
            try:
                pid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
                await self.repo.upsert_memory(
                    agent_name=agent_name,
                    key=key,
                    value=value,
                    project_id=pid,
                    memory_type=memory_type,
                    relevance_score=relevance_score,
                )
            except Exception as e:
                self.logger.warning(f"Failed to persist memory: {e}")

    async def recall(self, agent_name: str, key: str) -> dict | None:
        cache_key = f"{agent_name}:{key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        if self.repo:
            try:
                entry = await self.repo.get_by_key(agent_name, key)
                if entry:
                    self.cache.set(cache_key, entry.value)
                    return entry.value
            except Exception as e:
                self.logger.warning(f"Failed to recall memory: {e}")
        return None

    async def search(self, agent_name: str, prefix: str) -> list[dict]:
        results = []
        cached = self.cache.search(f"{agent_name}:{prefix}")
        for cache_key, val in cached:
            results.append(val)
        if self.repo and not results:
            try:
                entries = await self.repo.search_by_type(agent_name, prefix)
                for entry in entries:
                    results.append(entry.value)
                    self.cache.set(f"{agent_name}:{entry.key}", entry.value)
            except Exception as e:
                self.logger.warning(f"Failed to search memory: {e}")
        return results

    async def remember_failed_search(self, agent_name: str, query: str) -> None:
        await self.store(
            agent_name=agent_name,
            key=f"failed_search:{query[:200]}",
            value={"query": query, "timestamp": datetime.now(timezone.utc).isoformat()},
            memory_type="failed_search",
        )

    async def was_search_tried(self, agent_name: str, query: str) -> bool:
        result = await self.recall(agent_name, f"failed_search:{query[:200]}")
        return result is not None

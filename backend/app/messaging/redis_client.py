from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
        self._pubsub = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._client.ping()
        logger.info("Connected to Redis at %s", settings.REDIS_URL)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
        if self._pubsub:
            await self._pubsub.close()

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis not connected")
        return self._client

    @property
    def pubsub_client(self) -> aioredis.Redis:
        if self._pubsub is None:
            raise RuntimeError("Redis not connected")
        return self._pubsub

    # ── Cache ─────────────────────────────────────────────────
    async def cache_get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def cache_get_json(self, key: str) -> Optional[Any]:
        val = await self.client.get(key)
        return json.loads(val) if val else None

    async def cache_set(
        self, key: str, value: str, ttl_seconds: int = 300,
    ) -> None:
        await self.client.setex(key, ttl_seconds, value)

    async def cache_set_json(
        self, key: str, value: Any, ttl_seconds: int = 300,
    ) -> None:
        await self.client.setex(key, ttl_seconds, json.dumps(value, default=str))

    async def cache_delete(self, key: str) -> None:
        await self.client.delete(key)

    async def cache_delete_pattern(self, pattern: str) -> None:
        cursor = 0
        while True:
            cursor, keys = await self.client.scan(cursor=cursor, match=pattern)
            if keys:
                await self.client.delete(*keys)
            if cursor == 0:
                break

    # ── Queue ─────────────────────────────────────────────────
    async def queue_push(self, queue: str, value: str) -> None:
        await self.client.rpush(queue, value)

    async def queue_push_json(self, queue: str, value: Any) -> None:
        await self.client.rpush(queue, json.dumps(value, default=str))

    async def queue_pop(
        self, queue: str, timeout: int = 5,
    ) -> Optional[str]:
        result = await self.client.blpop(queue, timeout=timeout)
        return result[1] if result else None

    async def queue_pop_json(
        self, queue: str, timeout: int = 5,
    ) -> Optional[Any]:
        result = await self.queue_pop(queue, timeout)
        return json.loads(result) if result else None

    async def queue_length(self, queue: str) -> int:
        return await self.client.llen(queue)

    # ── Pub/Sub ───────────────────────────────────────────────
    async def publish(self, channel: str, message: str) -> None:
        await self.pubsub_client.publish(channel, message)

    async def publish_json(self, channel: str, message: Any) -> None:
        await self.pubsub_client.publish(channel, json.dumps(message, default=str))

    async def subscribe(self, channel: str) -> aioredis.Redis:
        pubsub = self.pubsub_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


redis_client = RedisClient()

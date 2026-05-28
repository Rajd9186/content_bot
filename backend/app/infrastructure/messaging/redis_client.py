from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from typing import Any, Awaitable, Callable, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCK_SCRIPT = """
if redis.call("SET", KEYS[1], ARGV[1], "NX", "PX", ARGV[2]) then
    return 1
end
return 0
"""

UNLOCK_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""

EXTEND_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("PEXPIRE", KEYS[1], ARGV[2])
end
return 0
"""


class DistributedLock:
    """Redlock-compatible distributed lock using Redis SET NX PX.

    Implements the Redlock algorithm for safe distributed locking.
    Each lock instance generates a unique random value so that only
    the owner can release/extend the lock.
    """

    def __init__(
        self,
        redis_client: RedisClient,
        lock_key: str,
        ttl_ms: int = 30000,
        retry_delay_ms: int = 200,
        max_retries: int = 5,
        watchdog_interval_ms: int = 10000,
    ) -> None:
        self._redis = redis_client
        self._lock_key = lock_key
        self._ttl_ms = ttl_ms
        self._retry_delay_ms = retry_delay_ms
        self._max_retries = max_retries
        self._watchdog_interval_ms = watchdog_interval_ms
        self._lock_value = f"{os.getpid()}:{random.random()}:{time.time()}"
        self._watchdog_task: Optional[asyncio.Task[None]] = None
        self._acquired = False

    async def acquire(self) -> bool:
        """Acquire the distributed lock with retry logic."""
        for attempt in range(self._max_retries):
            acquired = await self._try_acquire()
            if acquired:
                self._acquired = True
                self._start_watchdog()
                return True
            if attempt < self._max_retries - 1:
                await asyncio.sleep(self._retry_delay_ms / 1000.0)
        return False

    async def _try_acquire(self) -> bool:
        try:
            result = await self._redis.client.eval(
                LOCK_SCRIPT, 1, self._lock_key, self._lock_value, str(self._ttl_ms),
            )
            return bool(result)
        except Exception as e:
            logger.warning("Lock acquire error for %s: %s", self._lock_key, e)
            return False

    async def release(self) -> bool:
        """Release the lock if we still own it."""
        self._stop_watchdog()
        if not self._acquired:
            return True
        try:
            result = await self._redis.client.eval(
                UNLOCK_SCRIPT, 1, self._lock_key, self._lock_value,
            )
            self._acquired = False
            return bool(result)
        except Exception as e:
            logger.warning("Lock release error for %s: %s", self._lock_key, e)
            self._acquired = False
            return False

    async def extend(self, ttl_ms: Optional[int] = None) -> bool:
        """Extend the lock TTL if we still own it."""
        ttl = ttl_ms or self._ttl_ms
        try:
            result = await self._redis.client.eval(
                EXTEND_SCRIPT, 1, self._lock_key, self._lock_value, str(ttl),
            )
            return bool(result)
        except Exception as e:
            logger.warning("Lock extend error for %s: %s", self._lock_key, e)
            return False

    def _start_watchdog(self) -> None:
        """Auto-extend the lock periodically to prevent expiry during long operations."""

        async def _watchdog_loop() -> None:
            while self._acquired:
                await asyncio.sleep(self._watchdog_interval_ms / 1000.0)
                if self._acquired:
                    await self.extend()

        self._watchdog_task = asyncio.create_task(_watchdog_loop())

    def _stop_watchdog(self) -> None:
        if self._watchdog_task and not self._watchdog_task.done():
            self._watchdog_task.cancel()

    async def __aenter__(self) -> DistributedLock:
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock: {self._lock_key}")
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.release()


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

    # ── Distributed Locking (Redlock) ────────────────────────
    def lock(
        self,
        lock_key: str,
        ttl_ms: int = 30000,
        retry_delay_ms: int = 200,
        max_retries: int = 5,
        watchdog_interval_ms: int = 10000,
    ) -> DistributedLock:
        """Create a distributed lock for the given key.

        Usage:
            async with redis_client.lock("job:123:lock"):
                # critical section
                pass

        Or manually:
            lock = redis_client.lock("job:123:lock")
            if await lock.acquire():
                try:
                    # critical section
                finally:
                    await lock.release()
        """
        return DistributedLock(
            self, lock_key, ttl_ms=ttl_ms, retry_delay_ms=retry_delay_ms,
            max_retries=max_retries, watchdog_interval_ms=watchdog_interval_ms,
        )

    async def acquire_lock(self, lock_key: str, ttl_ms: int = 30000) -> Optional[DistributedLock]:
        """Acquire a distributed lock. Returns None if acquisition fails."""
        lock = self.lock(lock_key, ttl_ms=ttl_ms)
        acquired = await lock.acquire()
        return lock if acquired else None

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

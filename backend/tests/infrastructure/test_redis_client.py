from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.messaging.redis_client import RedisClient


@pytest.fixture
def mock_redis() -> MagicMock:
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.close = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    client.delete = AsyncMock()
    client.rpush = AsyncMock()
    client.blpop = AsyncMock(return_value=None)
    client.llen = AsyncMock(return_value=0)
    client.scan = AsyncMock(return_value=(0, []))
    client.incrby = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.pipeline = MagicMock()
    pipe = AsyncMock()
    pipe.execute = AsyncMock(return_value=[1, True])
    client.pipeline.return_value = pipe
    return client


class TestRedisConnection:
    async def test_connect_success(self, mock_redis) -> None:
        rc = RedisClient()
        with patch("app.infrastructure.messaging.redis_client.aioredis") as mock_aioredis:
            mock_aioredis.from_url = MagicMock(return_value=mock_redis)
            await rc.connect()
            assert rc._client is not None

    async def test_disconnect(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        rc._pubsub = mock_redis
        await rc.disconnect()
        mock_redis.close.assert_called()


class TestRedisCache:
    async def test_cache_get_hit(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.get = AsyncMock(return_value="cached_value")
        result = await rc.cache_get("test_key")
        assert result == "cached_value"

    async def test_cache_get_miss(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.get = AsyncMock(return_value=None)
        result = await rc.cache_get("missing_key")
        assert result is None

    async def test_cache_set(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        await rc.cache_set("key", "value", ttl_seconds=60)
        mock_redis.setex.assert_called_once_with("key", 60, "value")

    async def test_cache_get_json(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.get = AsyncMock(return_value='{"key": "value"}')
        result = await rc.cache_get_json("json_key")
        assert result == {"key": "value"}

    async def test_cache_delete(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        await rc.cache_delete("key")
        mock_redis.delete.assert_called_once_with("key")


class TestRedisQueue:
    async def test_queue_push(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        await rc.queue_push("test_queue", "item")
        mock_redis.rpush.assert_called_once_with("test_queue", "item")

    async def test_queue_push_json(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        await rc.queue_push_json("test_queue", {"data": "value"})
        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        assert json.loads(call_args[0][1]) == {"data": "value"}

    async def test_queue_pop_empty(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.blpop = AsyncMock(return_value=None)
        result = await rc.queue_pop("test_queue", timeout=5)
        assert result is None

    async def test_queue_pop_item(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.blpop = AsyncMock(return_value=("test_queue", "item_value"))
        result = await rc.queue_pop("test_queue", timeout=5)
        assert result == "item_value"

    async def test_queue_length(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.llen = AsyncMock(return_value=5)
        result = await rc.queue_length("test_queue")
        assert result == 5


class TestRedisPubSub:
    async def test_publish(self, mock_redis) -> None:
        rc = RedisClient()
        rc._pubsub = mock_redis
        await rc.publish("channel", "message")
        mock_redis.publish.assert_called_once_with("channel", "message")

    async def test_publish_json(self, mock_redis) -> None:
        rc = RedisClient()
        rc._pubsub = mock_redis
        await rc.publish_json("channel", {"event": "test"})
        mock_redis.publish.assert_called_once()


class TestRedisDistributedLock:
    async def test_lock_creation(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        lock = rc.lock("test_lock", ttl_ms=10000)
        assert lock._lock_key == "test_lock"
        assert lock._ttl_ms == 10000

    async def test_lock_acquire_success(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.eval = AsyncMock(return_value=1)
        lock = rc.lock("test_lock", ttl_ms=10000, max_retries=1)
        acquired = await lock.acquire()
        assert acquired is True

    async def test_lock_acquire_failure(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.eval = AsyncMock(return_value=0)
        lock = rc.lock("test_lock", ttl_ms=10000, max_retries=1, retry_delay_ms=10)
        acquired = await lock.acquire()
        assert acquired is False

    async def test_lock_release(self, mock_redis) -> None:
        rc = RedisClient()
        rc._client = mock_redis
        mock_redis.eval = AsyncMock(side_effect=[1, 1])
        lock = rc.lock("test_lock", ttl_ms=10000, max_retries=1)
        await lock.acquire()
        result = await lock.release()
        assert result is True


class TestRedisClientNotConnected:
    def test_client_property_raises_when_not_connected(self) -> None:
        rc = RedisClient()
        with pytest.raises(RuntimeError, match="Redis not connected"):
            _ = rc.client

    def test_pubsub_property_raises_when_not_connected(self) -> None:
        rc = RedisClient()
        with pytest.raises(RuntimeError, match="Redis not connected"):
            _ = rc.pubsub_client

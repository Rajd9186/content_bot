from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.providers.task_profiles import PROVIDER_LIMITS

logger = logging.getLogger(__name__)


@dataclass
class ProviderCapacity:
    provider: str
    rpm_limit: int
    rpm_used: int = 0
    tpm_limit: int
    tpm_used: int = 0
    active_requests: int = 0
    queue_length: int = 0
    last_updated: float = field(default_factory=time.monotonic)


class ProviderCapacityManager:
    """Track provider capacity across all workers using Redis.

    Keys used (all with 60s TTL for auto-cleanup):
    - provider:rpm:{provider}    → current RPM count
    - provider:tpm:{provider}     → current TPM count
    - provider:active:{provider} → active request count
    """

    def __init__(self) -> None:
        self._cache_ttl = 60

    async def record_request_start(self, provider: str, tokens: int) -> None:
        """Record that a request has started (acquire capacity)."""
        if not self._redis_ok():
            return
        try:
            pipe = redis_client.client.pipeline()
            pipe.incr(f"provider:rpm:{provider}")
            pipe.expire(f"provider:rpm:{provider}", self._cache_ttl)
            pipe.incrby(f"provider:tpm:{provider}", tokens)
            pipe.expire(f"provider:tpm:{provider}", self._cache_ttl)
            pipe.incr(f"provider:active:{provider}")
            pipe.expire(f"provider:active:{provider}", 300)
            await pipe.execute()
        except Exception as e:
            logger.warning("Failed to record request start: %s", e)

    async def record_request_end(self, provider: str, tokens: int) -> None:
        """Record that a request has completed (release capacity)."""
        if not self._redis_ok():
            return
        try:
            pipe = redis_client.client.pipeline()
            pipe.decr(f"provider:active:{provider}")
            tpm_key = f"provider:tpm:{provider}"
            current = await redis_client.cache_get(tpm_key)
            if current:
                val = int(current) - tokens
                if val <= 0:
                    pipe.delete(tpm_key)
                else:
                    pipe.set(tpm_key, str(val))
                    pipe.expire(tpm_key, self._cache_ttl)
            await pipe.execute()
        except Exception as e:
            logger.warning("Failed to record request end: %s", e)

    async def get_capacity(self, provider: str) -> ProviderCapacity:
        """Get current capacity metrics for a provider."""
        limits = PROVIDER_LIMITS.get(provider, {"rpm": 500, "tpm": 500000})
        rpm_limit = limits["rpm"]
        tpm_limit = limits["tpm"]

        rpm_used = 0
        tpm_used = 0
        active = 0

        if self._redis_ok():
            try:
                rpm_key = f"provider:rpm:{provider}"
                tpm_key = f"provider:tpm:{provider}"
                active_key = f"provider:active:{provider}"

                pipe = redis_client.client.pipeline()
                pipe.get(rpm_key)
                pipe.get(tpm_key)
                pipe.get(active_key)
                results = await pipe.execute()

                rpm_used = max(0, int(results[0] or 0))
                tpm_used = max(0, int(results[1] or 0))
                active = max(0, int(results[2] or 0))
            except Exception as e:
                logger.warning("Failed to get capacity: %s", e)

        return ProviderCapacity(
            provider=provider,
            rpm_limit=rpm_limit,
            rpm_used=rpm_used,
            tpm_limit=tpm_limit,
            tpm_used=tpm_used,
            active_requests=active,
            last_updated=time.monotonic(),
        )

    async def can_accept_request(self, provider: str, estimated_tokens: int) -> bool:
        """Check if provider can accept another request (capacity check)."""
        cap = await self.get_capacity(provider)

        if cap.rpm_used >= cap.rpm_limit:
            return False
        if cap.tpm_used + estimated_tokens > cap.tpm_limit:
            return False
        if cap.active_requests >= limits["max_concurrent"] if (limits := PROVIDER_LIMITS.get(provider)) else False:
            return False

        return True

    def _redis_ok(self) -> bool:
        return redis_client._client is not None


capacity_manager = ProviderCapacityManager()

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)

METRICS_KEY = "provider:perf"


@dataclass
class ProviderMetrics:
    provider: str
    model: str
    total_calls: int = 0
    total_failures: int = 0
    total_latency_ms: float = 0.0
    last_updated: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return (self.total_calls - self.total_failures) / self.total_calls

    @property
    def average_latency(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls


class ProviderPerformanceTracker:
    """Track per-(provider, model) performance metrics in Redis."""

    def __init__(self) -> None:
        self._local: dict[str, ProviderMetrics] = {}
        self._flush_interval = 10.0
        self._last_flush = time.monotonic()

    async def record_call(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        success: bool,
    ) -> None:
        key = f"{provider}:{model}"
        if key not in self._local:
            self._local[key] = ProviderMetrics(provider=provider, model=model)

        m = self._local[key]
        m.total_calls += 1
        m.total_latency_ms += latency_ms
        if not success:
            m.total_failures += 1
        m.last_updated = time.time()

        if time.monotonic() - self._last_flush >= self._flush_interval:
            await self._flush_to_redis()

    async def _flush_to_redis(self) -> None:
        if not self._redis_ok() or not self._local:
            return
        try:
            data = {
                f"{m.provider}:{m.model}": {
                    "total_calls": m.total_calls,
                    "total_failures": m.total_failures,
                    "total_latency_ms": m.total_latency_ms,
                    "last_updated": m.last_updated,
                }
                for m in self._local.values()
            }
            await redis_client.cache_set_json(
                f"{METRICS_KEY}:{int(time.time() / 60)}",
                data,
                ttl_seconds=3600,
            )
            self._local.clear()
            self._last_flush = time.monotonic()
        except Exception as e:
            logger.warning("Failed to flush metrics: %s", e)

    async def get_metrics(self, provider: str, model: str) -> ProviderMetrics:
        """Get aggregated metrics for a provider+model."""
        key = f"{provider}:{model}"

        if self._redis_ok():
            try:
                current_minute = int(time.time() / 60)
                for offset in range(5):
                    mkey = f"{METRICS_KEY}:{current_minute - offset}"
                    raw = await redis_client.cache_get_json(mkey)
                    if raw and key in raw:
                        d = raw[key]
                        return ProviderMetrics(
                            provider=provider,
                            model=model,
                            total_calls=d["total_calls"],
                            total_failures=d["total_failures"],
                            total_latency_ms=d["total_latency_ms"],
                            last_updated=d["last_updated"],
                        )
            except Exception as e:
                logger.warning("Failed to get metrics from Redis: %s", e)

        if key in self._local:
            return self._local[key]

        return ProviderMetrics(provider=provider, model=model)

    async def get_all_metrics(self) -> dict[str, ProviderMetrics]:
        """Get metrics for all tracked providers."""
        result: dict[str, ProviderMetrics] = {}
        seen: set[str] = set()

        if self._redis_ok():
            try:
                current_minute = int(time.time() / 60)
                for offset in range(5):
                    mkey = f"{METRICS_KEY}:{current_minute - offset}"
                    raw = await redis_client.cache_get_json(mkey)
                    if raw:
                        for k, d in raw.items():
                            if k in seen:
                                continue
                            seen.add(k)
                            parts = k.split(":", 1)
                            result[k] = ProviderMetrics(
                                provider=parts[0],
                                model=parts[1] if len(parts) > 1 else "",
                                total_calls=d["total_calls"],
                                total_failures=d["total_failures"],
                                total_latency_ms=d["total_latency_ms"],
                                last_updated=d["last_updated"],
                            )
            except Exception as e:
                logger.warning("Failed to get all metrics: %s", e)

        for k, m in self._local.items():
            if k not in seen:
                result[k] = m

        return result

    def _redis_ok(self) -> bool:
        return redis_client._client is not None


performance_tracker = ProviderPerformanceTracker()

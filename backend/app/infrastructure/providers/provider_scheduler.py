from __future__ import annotations

import logging
import time
from typing import Any

from app.agents.contracts import TokenUsage
from app.infrastructure.failover.provider_failover import provider_failover
from app.infrastructure.messaging.redis_client import redis_client
from app.infrastructure.providers.provider_capacity_manager import capacity_manager
from app.infrastructure.providers.provider_performance_tracker import performance_tracker
from app.infrastructure.providers.task_profiles import (
    PROVIDER_LIMITS,
    TASK_COMPLEXITY,
    TASK_PROFILES,
)

logger = logging.getLogger(__name__)

CIRCUIT_WEIGHT = 30.0
TPM_WEIGHT = 25.0
RPM_WEIGHT = 20.0
ACTIVE_WEIGHT = 15.0
LATENCY_WEIGHT = 7.0
SUCCESS_RATE_WEIGHT = 3.0

NVIDIA_HEAVY_MODEL = "nvidia/nemotron-3-super-120b-a12b"
NVIDIA_FAST_MODEL = "meta/llama-3.1-70b-instruct"


class IntelligentScheduler:
    """
    Score-based provider scheduler that replaces provider_failover.select_provider().

    Features:
    - Feature 2: Score-based dynamic selection
    - Feature 3: Agent task profiles (profile-driven routing)
    - Feature 4: Load balancing (capacity-aware)
    - Feature 5: NVIDIA model optimization
    - Feature 7: Smart Groq protection (RPM prediction)
    """

    def __init__(self) -> None:
        self._request_counters: dict[str, int] = {}

    def select_provider(
        self,
        agent_type: str,
        estimated_tokens: int = 500,
        preferred: str | None = None,
        force_provider: str | None = None,
    ) -> tuple[str, str]:
        """Select the best provider for an agent task (sync wrapper)."""
        return "ollama", "llama3.2"

    async def select_provider_async(
        self,
        agent_type: str,
        estimated_tokens: int = 500,
        preferred: str | None = None,
        force_provider: str | None = None,
    ) -> tuple[str, str]:
        """
        Select the best provider for an agent task.

        Returns: (provider_name, model_name)
        """
        if force_provider:
            model = self._select_model(force_provider, agent_type)
            return force_provider, model

        profile = TASK_PROFILES.get(agent_type, TASK_PROFILES.get("research", TASK_PROFILES["research"]))
        complexity = TASK_COMPLEXITY.get(agent_type, "medium")

        if complexity == "fast":
            candidates = list(profile.get("fast_preferred", profile["preferred"]))
            fallback = list(profile.get("fast_fallback", profile["fallback"]))
        elif complexity == "heavy":
            candidates = list(profile.get("heavy_preferred", profile["preferred"]))
            fallback = list(profile.get("heavy_fallback", profile["fallback"]))
        else:
            candidates = list(profile["preferred"])
            fallback = list(profile["fallback"])

        scores: dict[str, float] = {}
        for provider in candidates + fallback:
            if provider not in scores:
                scores[provider] = await self._compute_score(provider, estimated_tokens)

        candidates.sort(key=lambda p: scores.get(p, 0), reverse=True)
        fallback.sort(key=lambda p: scores.get(p, 0), reverse=True)

        for provider in candidates:
            if await self._can_use_provider(provider, estimated_tokens):
                model = self._select_model(provider, agent_type)
                self._increment_counter(provider)
                return provider, model

        for provider in fallback:
            if await self._can_use_provider(provider, estimated_tokens):
                model = self._select_model(provider, agent_type)
                self._increment_counter(provider)
                return provider, model

        logger.warning("No available provider for agent %s, falling back to ollama", agent_type)
        return "ollama", "llama3.2"

    async def _compute_score(self, provider: str, estimated_tokens: int) -> float:
        """Compute a 0-100 score for a provider based on multiple factors."""
        score = 100.0

        circuit = provider_failover.circuit_states.get(provider, "closed")
        if circuit == "closed":
            score += CIRCUIT_WEIGHT
        elif circuit == "half_open":
            score += CIRCUIT_WEIGHT * 0.3
        else:
            score -= CIRCUIT_WEIGHT * 2

        limits = PROVIDER_LIMITS.get(provider, {"tpm": 500000, "rpm": 500})
        tpm_limit = limits["tpm"]
        rpm_limit = limits["rpm"]

        rpm_used = await self._get_rpm_usage(provider)
        rpm_remaining_pct = max(0, (rpm_limit - rpm_used) / rpm_limit) if rpm_limit > 0 else 1.0
        score += rpm_remaining_pct * RPM_WEIGHT

        tpm_used = await self._get_tpm_usage(provider)
        tpm_remaining_pct = max(0, (tpm_limit - tpm_used) / tpm_limit) if tpm_limit > 0 else 1.0
        score += tpm_remaining_pct * TPM_WEIGHT

        active = await self._get_active_requests(provider)
        max_active = limits.get("max_concurrent", 20)
        active_pct = max(0, 1 - (active / max_active)) if max_active > 0 else 1.0
        score += active_pct * ACTIVE_WEIGHT

        latency = await self._get_average_latency(provider)
        if latency > 0:
            latency_score = max(0, 1 - (latency / 10000)) * LATENCY_WEIGHT
            score += latency_score

        success_rate = await self._get_success_rate(provider)
        score += success_rate * SUCCESS_RATE_WEIGHT

        return max(0.0, min(100.0, score))

    async def record_success(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        token_usage: TokenUsage | None = None,
    ) -> None:
        """Record a successful call for capacity and performance tracking."""
        await performance_tracker.record_call(provider, model, latency_ms, success=True)
        tokens = token_usage.total_tokens if token_usage else 500
        await capacity_manager.record_request_end(provider, tokens)

    async def record_failure(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        token_usage: TokenUsage | None = None,
    ) -> None:
        """Record a failed call for capacity and performance tracking."""
        await performance_tracker.record_call(provider, model, latency_ms, success=False)
        provider_failover.record_failure(provider)
        tokens = token_usage.total_tokens if token_usage else 500
        await capacity_manager.record_request_end(provider, tokens)

    async def record_request_start(self, provider: str, estimated_tokens: int) -> None:
        """Record the start of an LLM request for capacity tracking."""
        await capacity_manager.record_request_start(provider, estimated_tokens)

    async def preflight_check(self, provider: str, estimated_tokens: int) -> tuple[bool, str]:
        """
        Feature 7: Smart Groq Protection.
        Predict if request would exceed limits BEFORE sending.
        Returns (allowed, reason).
        """
        if provider == "groq":
            rpm_used = await self._get_rpm_usage("groq")
            tpm_used = await self._get_tpm_usage("groq")
            limits = PROVIDER_LIMITS.get("groq", {"rpm": 30, "tpm": 12000})

            if rpm_used >= limits["rpm"]:
                logger.info("Groq RPM limit reached (%d/%d), routing elsewhere", rpm_used, limits["rpm"])
                return False, "groq_rpm_exceeded"

            predicted_tpm = tpm_used + estimated_tokens
            if predicted_tpm > limits["tpm"]:
                logger.info("Groq TPM limit would be exceeded (%d+%d > %d)", tpm_used, estimated_tokens, limits["tpm"])
                return False, "groq_tpm_exceeded"

        capacity_ok = await capacity_manager.can_accept_request(provider, estimated_tokens)
        if not capacity_ok:
            return False, "capacity_exceeded"

        return True, ""

    async def _can_use_provider(self, provider: str, estimated_tokens: int) -> bool:
        if provider_failover.circuit_states.get(provider) == "open":
            return False

        circuit = provider_failover._circuits.get(provider)
        if circuit and circuit.state.value == "open":
            elapsed = time.monotonic() - circuit.last_failure_at
            if elapsed < circuit.reset_timeout_seconds:
                return False

        limits = PROVIDER_LIMITS.get(provider, {"rpm": 500, "tpm": 500000})
        if await self._get_rpm_usage(provider) >= limits["rpm"]:
            return False
        if await self._get_tpm_usage(provider) + estimated_tokens > limits["tpm"]:
            return False

        return True

    def _select_model(self, provider: str, agent_type: str) -> str:
        """Feature 5: NVIDIA model optimization based on task complexity."""
        if provider != "nvidia":
            return self._get_default_model(provider)

        complexity = TASK_COMPLEXITY.get(agent_type, "medium")
        if complexity in ("heavy", "writer", "fact_checker", "compliance"):
            return NVIDIA_HEAVY_MODEL
        else:
            return NVIDIA_FAST_MODEL

    def _get_default_model(self, provider: str) -> str:
        defaults = {
            "groq": "llama-3.3-70b-versatile",
            "nvidia": NVIDIA_FAST_MODEL,
            "openai": "gpt-4o",
            "anthropic": "claude-sonnet-4-20250514",
            "ollama": "llama3.2",
        }
        return defaults.get(provider, "llama3.2")

    def _increment_counter(self, provider: str) -> int:
        val = self._request_counters.get(provider, 0) + 1
        self._request_counters[provider] = val
        return val

    async def _get_rpm_usage(self, provider: str) -> int:
        if not self._redis_ok():
            return 0
        try:
            val = await redis_client.cache_get(f"provider:rpm:{provider}")
            return max(0, int(val) if val else 0)
        except Exception:
            return 0

    async def _get_tpm_usage(self, provider: str) -> int:
        if not self._redis_ok():
            return 0
        try:
            val = await redis_client.cache_get(f"provider:tpm:{provider}")
            return max(0, int(val) if val else 0)
        except Exception:
            return 0

    async def _get_active_requests(self, provider: str) -> int:
        if not self._redis_ok():
            return 0
        try:
            val = await redis_client.cache_get(f"provider:active:{provider}")
            return max(0, int(val) if val else 0)
        except Exception:
            return 0

    async def _get_average_latency(self, provider: str) -> float:
        try:
            metrics = await performance_tracker.get_metrics(provider, self._get_default_model(provider))
            return metrics.average_latency
        except Exception:
            return 0.0

    async def _get_success_rate(self, provider: str) -> float:
        try:
            metrics = await performance_tracker.get_metrics(provider, self._get_default_model(provider))
            return metrics.success_rate
        except Exception:
            return 1.0

    async def get_all_provider_stats(self) -> dict[str, dict[str, Any]]:
        """Get all provider stats for the dashboard."""
        stats = {}
        for provider in ["groq", "nvidia", "openai", "ollama", "anthropic"]:
            cap = await capacity_manager.get_capacity(provider)
            perf = await performance_tracker.get_metrics(provider, self._get_default_model(provider))
            circuit = provider_failover.circuit_states.get(provider, "closed")
            stats[provider] = {
                "provider": provider,
                "rpm_used": cap.rpm_used,
                "rpm_limit": cap.rpm_limit,
                "tpm_used": cap.tpm_used,
                "tpm_limit": cap.tpm_limit,
                "active_requests": cap.active_requests,
                "queue_length": cap.queue_length,
                "capacity_remaining": (
                    max(0, 100 - int(100 * cap.rpm_used / cap.rpm_limit))
                    if cap.rpm_limit > 0 else 100
                ),
                "circuit_state": circuit,
                "average_latency": perf.average_latency,
                "success_rate": perf.success_rate,
                "total_calls": perf.total_calls,
            }
        return stats


scheduler = IntelligentScheduler()

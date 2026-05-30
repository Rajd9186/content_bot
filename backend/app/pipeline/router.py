from __future__ import annotations

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    PREMIUM = "premium"


@dataclass
class RoutingDecision:
    provider: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    routing_reason: str
    fallback_provider: str
    fallback_model: str
    execution_priority: int


AGENT_ROUTING: dict[str, str] = {
    "research": "ollama",
    "planner": "ollama",
    "writer": "groq",
    "seo": "ollama",
    "fact_checker": "ollama",
    "compliance": "ollama",
    "finalizer": "groq",
}

GROQ_MODELS: dict[TaskComplexity, list[str]] = {
    TaskComplexity.SMALL: ["llama-3.1-8b-instant"],
    TaskComplexity.MEDIUM: ["groq/compound"],
    TaskComplexity.PREMIUM: ["llama-3.3-70b-versatile"],
}

NVIDIA_MODELS: dict[TaskComplexity, list[str]] = {
    TaskComplexity.SMALL: ["nvidia/nemotron-3-super-120b-a12b"],
    TaskComplexity.MEDIUM: ["nvidia/nemotron-3-super-120b-a12b"],
    TaskComplexity.PREMIUM: ["nvidia/nemotron-3-super-120b-a12b"],
}

OLLAMA_PROVIDER = "gpt-oss"
OLLAMA_MODEL = "gpt-oss:120b"

CHAR_TO_TOKEN_RATIO = 0.25
TPM_LIMIT = 12000
MAX_CONCURRENT_PREMIUM = 2


class TokenBudgetTracker:
    def __init__(self, tpm_limit: int = TPM_LIMIT) -> None:
        self._tpm_limit = tpm_limit
        self._usage_log: deque[tuple[float, int]] = deque()
        self._concurrent_premium = 0

    def record_usage(self, tokens: int) -> None:
        now = time.monotonic()
        self._usage_log.append((now, tokens))
        self._purge(now)

    def remaining_tpm(self) -> int:
        now = time.monotonic()
        self._purge(now)
        used = sum(t for _, t in self._usage_log)
        return max(0, self._tpm_limit - used)

    def acquire_premium(self) -> bool:
        if self._concurrent_premium >= MAX_CONCURRENT_PREMIUM:
            return False
        self._concurrent_premium += 1
        return True

    def release_premium(self) -> None:
        self._concurrent_premium = max(0, self._concurrent_premium - 1)

    def _purge(self, now: float) -> None:
        while self._usage_log and now - self._usage_log[0][0] > 60:
            self._usage_log.popleft()


_token_tracker = TokenBudgetTracker()


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) * CHAR_TO_TOKEN_RATIO))


class ProviderRouter:
    def __init__(self) -> None:
        self._tracker = _token_tracker

    async def route(
        self,
        agent_type: str,
        system_prompt: str,
        user_prompt: str,
        state: Optional[dict[str, Any]] = None,
    ) -> RoutingDecision:
        estimated_input = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
        estimated_output = estimate_tokens(
            (state or {}).get("goals", "")
        ) + 500
        total_estimated = estimated_input + estimated_output
        preferred = AGENT_ROUTING.get(agent_type, "ollama")

        if preferred == "groq":
            return self._route_groq(
                agent_type, estimated_input, estimated_output, total_estimated,
            )
        if preferred == "nvidia":
            return self._route_nvidia(
                agent_type, estimated_input, estimated_output,
            )
        return self._route_ollama(
            agent_type, estimated_input, estimated_output,
        )

    async def get_fallback(
        self, agent_type: str, failed_provider: str, failed_model: str,
        error: str,
    ) -> RoutingDecision:
        if failed_provider == "groq":
            if self._is_rate_limit(error):
                remaining = self._tracker.remaining_tpm()
                if remaining > 1000:
                    smaller = self._next_smaller_model(failed_model)
                    return RoutingDecision(
                        provider="groq", model=smaller,
                        estimated_input_tokens=0, estimated_output_tokens=0,
                        routing_reason=f"Rate limit on {failed_model}, retrying with {smaller}",
                        fallback_provider="nvidia",
                        fallback_model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
                        execution_priority=1,
                    )
            return RoutingDecision(
                provider="nvidia", model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
                estimated_input_tokens=0, estimated_output_tokens=0,
                routing_reason=f"Groq {failed_model} failed: {error[:100]}, falling back to Nvidia",
                fallback_provider=OLLAMA_PROVIDER,
                fallback_model=OLLAMA_MODEL,
                execution_priority=1,
            )
        if failed_provider == "nvidia":
            return RoutingDecision(
                provider=OLLAMA_PROVIDER, model=OLLAMA_MODEL,
                estimated_input_tokens=0, estimated_output_tokens=0,
                routing_reason=f"Nvidia {failed_model} failed: {error[:100]}, falling back to Ollama",
                fallback_provider=OLLAMA_PROVIDER,
                fallback_model=OLLAMA_MODEL,
                execution_priority=1,
            )
        return RoutingDecision(
            provider=OLLAMA_PROVIDER, model=OLLAMA_MODEL,
            estimated_input_tokens=0, estimated_output_tokens=0,
            routing_reason=f"{failed_provider} failed, falling back to Ollama",
            fallback_provider=OLLAMA_PROVIDER,
            fallback_model=OLLAMA_MODEL,
            execution_priority=1,
        )

    def record_usage(self, provider: str, tokens: int) -> None:
        if provider == "groq":
            self._tracker.record_usage(tokens)

    def release_premium(self) -> None:
        self._tracker.release_premium()

    def _route_ollama(
        self, agent_type: str,
        estimated_input: int, estimated_output: int,
    ) -> RoutingDecision:
        return RoutingDecision(
            provider=OLLAMA_PROVIDER, model=OLLAMA_MODEL,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            routing_reason=f"Agent '{agent_type}' routed to Ollama by default",
            fallback_provider="nvidia",
            fallback_model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
            execution_priority=1,
        )

    def _route_nvidia(
        self, agent_type: str,
        estimated_input: int, estimated_output: int,
    ) -> RoutingDecision:
        return RoutingDecision(
            provider="nvidia", model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            routing_reason=f"Agent '{agent_type}' routed to Nvidia by default",
            fallback_provider=OLLAMA_PROVIDER,
            fallback_model=OLLAMA_MODEL,
            execution_priority=2,
        )

    def _route_groq(
        self, agent_type: str,
        estimated_input: int, estimated_output: int,
        total_estimated: int,
    ) -> RoutingDecision:
        remaining = self._tracker.remaining_tpm()
        exceeds_budget = total_estimated > remaining

        if estimated_input > 3000 or exceeds_budget:
            reason = (
                f"Input {estimated_input}t exceeds 3000 threshold"
                if estimated_input > 3000
                else f"Groq TPM remaining {remaining} insufficient for {total_estimated}t"
            )
            return RoutingDecision(
                provider=OLLAMA_PROVIDER, model=OLLAMA_MODEL,
                estimated_input_tokens=estimated_input,
                estimated_output_tokens=estimated_output,
                routing_reason=f"{reason}, routed to Ollama",
                fallback_provider="nvidia",
                fallback_model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
                execution_priority=2,
            )

        if not self._tracker.acquire_premium():
            return RoutingDecision(
                provider="nvidia", model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
                estimated_input_tokens=estimated_input,
                estimated_output_tokens=estimated_output,
                routing_reason="Max concurrent Groq executions reached, routed to Nvidia",
                fallback_provider=OLLAMA_PROVIDER,
                fallback_model=OLLAMA_MODEL,
                execution_priority=2,
            )

        complexity = self._determine_complexity(agent_type, total_estimated)
        model = GROQ_MODELS[complexity][0]

        priority = 3 if complexity == TaskComplexity.PREMIUM else 2
        return RoutingDecision(
            provider="groq", model=model,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            routing_reason=f"Agent '{agent_type}' routed to Groq ({model}) for {complexity.value} task",
            fallback_provider="nvidia",
            fallback_model=NVIDIA_MODELS[TaskComplexity.MEDIUM][0],
            execution_priority=priority,
        )

    def _determine_complexity(
        self, agent_type: str, total_estimated: int,
    ) -> TaskComplexity:
        if agent_type == "finalizer":
            return TaskComplexity.PREMIUM
        if agent_type == "writer" and total_estimated > 4000:
            return TaskComplexity.PREMIUM
        if total_estimated < 1500:
            return TaskComplexity.SMALL
        return TaskComplexity.MEDIUM

    def _next_smaller_model(self, current: str) -> str:
        all_models = (
            GROQ_MODELS[TaskComplexity.SMALL]
            + GROQ_MODELS[TaskComplexity.MEDIUM]
            + GROQ_MODELS[TaskComplexity.PREMIUM]
        )
        try:
            idx = all_models.index(current)
            if idx > 0:
                return all_models[idx - 1]
        except ValueError:
            pass
        return GROQ_MODELS[TaskComplexity.SMALL][0]

    def _is_rate_limit(self, error: str) -> bool:
        return bool(re.search(r"rate limit|tpm|tokens per minute|429", error, re.IGNORECASE))


provider_router = ProviderRouter()

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.infrastructure.messaging.redis_client import redis_client

logger = logging.getLogger(__name__)

CIRCUIT_OPEN_THRESHOLD = 5
CIRCUIT_RESET_SECONDS = 60
REDIS_TOKEN_KEY = "provider:tokens:groq"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    provider: str
    failure_threshold: int = CIRCUIT_OPEN_THRESHOLD
    reset_timeout_seconds: int = CIRCUIT_RESET_SECONDS
    failure_count: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_failure_at: float = 0.0

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_at = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPEN for provider %s after %d failures",
                self.provider, self.failure_count,
            )

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            elapsed = time.monotonic() - self.last_failure_at
            if elapsed >= self.reset_timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker HALF_OPEN for provider %s", self.provider)
                return True
            return False
        return True


FAILOVER_CHAIN = {
    "research": ["openai", "nvidia", "groq", "ollama"],
    "planner": ["openai", "nvidia", "groq", "ollama"],
    "writer": ["groq", "nvidia", "openai", "ollama"],
    "seo": ["openai", "nvidia", "groq", "ollama"],
    "fact_checker": ["openai", "nvidia", "groq", "ollama"],
    "compliance": ["openai", "nvidia", "groq", "ollama"],
    "finalizer": ["groq", "nvidia", "openai", "ollama"],
}


class ProviderFailover:
    """Provider failover chain: OpenAI -> Groq -> Ollama.

    Features:
    - Circuit breaker per provider (tracks consecutive failures)
    - Redis-based TPM tracking for cross-node coordination
    - Fallback to next provider in chain on failure
    - Automatic circuit recovery after timeout
    """

    def __init__(self) -> None:
        self._circuits: dict[str, CircuitBreaker] = {
            "openai": CircuitBreaker("openai"),
            "nvidia": CircuitBreaker("nvidia"),
            "groq": CircuitBreaker("groq"),
            "ollama": CircuitBreaker("ollama"),
        }

    def get_provider_chain(self, agent_type: str) -> list[str]:
        return FAILOVER_CHAIN.get(agent_type, ["openai", "groq", "ollama"])

    def can_use_provider(self, provider: str) -> bool:
        circuit = self._circuits.get(provider)
        if circuit is None:
            return True
        return circuit.can_execute()

    def record_success(self, provider: str) -> None:
        circuit = self._circuits.get(provider)
        if circuit:
            circuit.record_success()

    def record_failure(self, provider: str) -> None:
        circuit = self._circuits.get(provider)
        if circuit:
            circuit.record_failure()

    def get_circuit_state(self, provider: str) -> CircuitState:
        circuit = self._circuits.get(provider)
        return circuit.state if circuit else CircuitState.CLOSED

    async def acquire_tpm_budget(self, provider: str, estimated_tokens: int) -> bool:
        if provider != "groq":
            return True
        if redis_client._client is None:
            return True
        try:
            current = await redis_client.cache_get(REDIS_TOKEN_KEY)
            current_val = int(current) if current else 0
            if current_val + estimated_tokens > 12000:
                logger.info(
                    "Groq TPM budget exceeded: current=%d estimated=%d limit=12000",
                    current_val, estimated_tokens,
                )
                return False
            pipe = redis_client.client.pipeline()
            pipe.incrby(REDIS_TOKEN_KEY, estimated_tokens)
            pipe.expire(REDIS_TOKEN_KEY, 60)
            await pipe.execute()
            return True
        except Exception as e:
            logger.warning("Redis TPM check failed, allowing execution: %s", e)
            return True

    async def release_tpm_budget(self, provider: str, tokens: int) -> None:
        if provider != "groq" or redis_client._client is None:
            return
        try:
            current = await redis_client.cache_get(REDIS_TOKEN_KEY)
            current_val = int(current) if current else 0
            new_val = max(0, current_val - tokens)
            if new_val == 0:
                await redis_client.cache_delete(REDIS_TOKEN_KEY)
            else:
                await redis_client.cache_set(REDIS_TOKEN_KEY, str(new_val), ttl_seconds=60)
        except Exception as e:
            logger.warning("Redis TPM release failed: %s", e)

    def select_provider(self, agent_type: str, preferred: Optional[str] = None) -> str:
        chain = self.get_provider_chain(agent_type)
        if preferred and preferred in chain:
            circuit = self._circuits.get(preferred)
            if circuit and circuit.can_execute():
                return preferred
        for provider in chain:
            if self.can_use_provider(provider):
                return provider
        return "ollama"

    @property
    def circuit_states(self) -> dict[str, str]:
        return {p: c.state.value for p, c in self._circuits.items()}


provider_failover = ProviderFailover()

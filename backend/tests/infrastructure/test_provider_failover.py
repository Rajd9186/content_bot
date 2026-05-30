from __future__ import annotations

import pytest

from app.infrastructure.failover.provider_failover import (
    CircuitBreaker,
    CircuitState,
    ProviderFailover,
    FAILOVER_CHAIN,
)


@pytest.fixture
def failover() -> ProviderFailover:
    return ProviderFailover()


class TestCircuitBreaker:
    def test_initial_state(self) -> None:
        cb = CircuitBreaker("test_provider")
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_record_success(self) -> None:
        cb = CircuitBreaker("test_provider")
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_record_failure_below_threshold(self) -> None:
        cb = CircuitBreaker("test_provider", failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_record_failure_opens_circuit(self) -> None:
        cb = CircuitBreaker("test_provider", failure_threshold=5)
        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_can_execute_when_closed(self) -> None:
        cb = CircuitBreaker("test_provider")
        assert cb.can_execute() is True

    def test_can_execute_when_open(self) -> None:
        cb = CircuitBreaker("test_provider", failure_threshold=3, reset_timeout_seconds=9999)
        for _ in range(3):
            cb.record_failure()
        assert cb.can_execute() is False

    def test_can_execute_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker("test_provider", failure_threshold=3, reset_timeout_seconds=0)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        import time
        time.sleep(0.01)
        result = cb.can_execute()
        assert result is True
        assert cb.state == CircuitState.HALF_OPEN


class TestProviderFailover:
    def test_initial_circuits(self, failover: ProviderFailover) -> None:
        assert len(failover._circuits) == 4
        assert "openai" in failover._circuits
        assert "nvidia" in failover._circuits
        assert "groq" in failover._circuits
        assert "ollama" in failover._circuits

    def test_initial_state_all_closed(self, failover: ProviderFailover) -> None:
        for provider in ["openai", "nvidia", "groq", "ollama"]:
            assert failover.get_circuit_state(provider) == CircuitState.CLOSED

    def test_record_success_keeps_closed(self, failover: ProviderFailover) -> None:
        failover.record_success("openai")
        assert failover.get_circuit_state("openai") == CircuitState.CLOSED

    def test_record_failure_opens_after_threshold(self, failover: ProviderFailover) -> None:
        for _ in range(5):
            failover.record_failure("openai")
        assert failover.get_circuit_state("openai") == CircuitState.OPEN

    def test_record_failure_below_threshold_stays_closed(self, failover: ProviderFailover) -> None:
        for _ in range(4):
            failover.record_failure("groq")
        assert failover.get_circuit_state("groq") == CircuitState.CLOSED

    def test_get_provider_writer_chain(self, failover: ProviderFailover) -> None:
        chain = failover.get_provider_chain("writer")
        assert chain[0] == "groq"
        assert "openai" in chain
        assert "ollama" in chain

    def test_get_provider_research_chain(self, failover: ProviderFailover) -> None:
        chain = failover.get_provider_chain("research")
        assert chain[0] == "openai"
        assert "groq" in chain
        assert "ollama" in chain

    def test_get_provider_default_chain(self, failover: ProviderFailover) -> None:
        chain = failover.get_provider_chain("unknown_agent")
        assert chain == ["openai", "groq", "ollama"]

    def test_select_provider_closed(self, failover: ProviderFailover) -> None:
        provider = failover.select_provider("research")
        assert provider == "openai"

    def test_select_provider_writer_prefers_groq(self, failover: ProviderFailover) -> None:
        provider = failover.select_provider("writer")
        assert provider == "groq"

    def test_select_provider_falls_back_on_open_circuit(self, failover: ProviderFailover) -> None:
        for _ in range(5):
            failover.record_failure("openai")
        provider = failover.select_provider("research")
        assert provider != "openai"
        assert provider in ("nvidia", "groq", "ollama")

    def test_select_provider_with_preferred(self, failover: ProviderFailover) -> None:
        provider = failover.select_provider("research", preferred="groq")
        assert provider == "groq"

    def test_can_use_provider(self, failover: ProviderFailover) -> None:
        assert failover.can_use_provider("openai") is True
        for _ in range(5):
            failover.record_failure("openai")
        assert failover.can_use_provider("openai") is False

    def test_can_use_unknown_provider(self, failover: ProviderFailover) -> None:
        assert failover.can_use_provider("unknown") is True

    def test_circuit_states_property(self, failover: ProviderFailover) -> None:
        states = failover.circuit_states
        assert "openai" in states
        assert "nvidia" in states
        assert "groq" in states
        assert "ollama" in states
        assert all(v == "closed" for v in states.values())

    def test_failover_chain_defines_all_agent_types(self) -> None:
        expected = ["research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"]
        for agent_type in expected:
            assert agent_type in FAILOVER_CHAIN, f"Missing chain for {agent_type}"

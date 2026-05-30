from __future__ import annotations

import pytest

from app.pipeline.router import (
    AGENT_ROUTING,
    GROQ_MODELS,
    OLLAMA_MODEL,
    OLLAMA_PROVIDER,
    ProviderRouter,
    RoutingDecision,
    TaskComplexity,
    TokenBudgetTracker,
    estimate_tokens,
    provider_router,
)


@pytest.fixture
def router() -> ProviderRouter:
    r = ProviderRouter()
    r._tracker = TokenBudgetTracker(tpm_limit=12000)
    return r


def test_agent_routing_map_has_all_agents() -> None:
    expected = {"research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"}
    assert set(AGENT_ROUTING.keys()) == expected


def test_ollama_agents_by_default() -> None:
    for agent, target in AGENT_ROUTING.items():
        if agent in ("writer", "finalizer"):
            assert target == "groq", f"{agent} should route to groq"
        else:
            assert target == "ollama", f"{agent} should route to ollama (got {target})"


def test_groq_models_defined() -> None:
    assert TaskComplexity.SMALL in GROQ_MODELS
    assert TaskComplexity.MEDIUM in GROQ_MODELS
    assert TaskComplexity.PREMIUM in GROQ_MODELS
    assert len(GROQ_MODELS[TaskComplexity.SMALL]) >= 1
    assert len(GROQ_MODELS[TaskComplexity.MEDIUM]) >= 1
    assert len(GROQ_MODELS[TaskComplexity.PREMIUM]) >= 1


def test_ollama_model_constant() -> None:
    assert OLLAMA_PROVIDER == "gpt-oss"
    assert OLLAMA_MODEL == "gpt-oss:120b"


def test_estimate_tokens_empty() -> None:
    assert estimate_tokens("") == 1


def test_estimate_tokens_rough() -> None:
    tokens = estimate_tokens("Hello world, this is a test sentence with about fifty characters total")
    assert 5 <= tokens <= 30


def test_token_budget_tracker_init() -> None:
    tracker = TokenBudgetTracker(tpm_limit=12000)
    assert tracker.remaining_tpm() == 12000


def test_token_budget_record_usage() -> None:
    tracker = TokenBudgetTracker(tpm_limit=12000)
    tracker.record_usage(1000)
    remaining = tracker.remaining_tpm()
    assert remaining == 11000


def test_token_budget_remaining_non_negative() -> None:
    tracker = TokenBudgetTracker(tpm_limit=100)
    tracker.record_usage(200)
    assert tracker.remaining_tpm() == 0


def test_concurrent_premium_limit() -> None:
    tracker = TokenBudgetTracker()
    assert tracker.acquire_premium() is True
    assert tracker.acquire_premium() is True
    assert tracker.acquire_premium() is False  # max 2
    tracker.release_premium()
    assert tracker.acquire_premium() is True


def test_release_premium_no_negative() -> None:
    tracker = TokenBudgetTracker()
    tracker.release_premium()
    assert tracker._concurrent_premium == 0


async def test_route_ollama_agent(router) -> None:
    decision = await router.route("research", "system prompt", "user prompt")
    assert decision.provider == OLLAMA_PROVIDER
    assert decision.model == OLLAMA_MODEL
    assert "ollama" in decision.routing_reason.lower()


async def test_route_planner_goes_ollama(router) -> None:
    decision = await router.route("planner", "sys", "user")
    assert decision.provider == "gpt-oss"


async def test_route_writer_goes_groq(router) -> None:
    decision = await router.route("writer", "sys", "user")
    assert decision.provider == "groq"


async def test_route_finalizer_goes_groq(router) -> None:
    decision = await router.route("finalizer", "sys", "user")
    assert decision.provider == "groq"


async def test_route_writer_premium_when_large(router) -> None:
    large_prompt = "x" * 20000  # ~5000 tokens
    decision = await router.route("writer", large_prompt, "user")
    # Should route to Ollama because input > 3000 tokens
    assert decision.provider == "gpt-oss", f"Expected ollama for large input, got {decision.provider}: {decision.routing_reason}"


async def test_route_groq_small_model(router) -> None:
    decision = await router.route("writer", "short", "small")
    assert decision.provider == "groq"
    # Small prompt -> small model
    assert decision.model == GROQ_MODELS[TaskComplexity.SMALL][0]


async def test_route_groq_premium_for_finalizer(router) -> None:
    decision = await router.route("finalizer", "sys", "user")
    assert decision.provider == "groq"
    assert decision.model == GROQ_MODELS[TaskComplexity.PREMIUM][0]


async def test_fallback_rate_limit_uses_smaller_model(router) -> None:
    decision = await router.get_fallback(
        "writer", "groq", "llama-3.3-70b-versatile",
        "Rate limit reached for model llama-3.3-70b-versatile on tokens per minute",
    )
    # TPM budget available, so retry with smaller Groq model
    assert decision.provider == "groq"
    assert decision.model != "llama-3.3-70b-versatile"


async def test_fallback_rate_limit_exhausted_tpm_goes_nvidia() -> None:
    tracker = TokenBudgetTracker(tpm_limit=100)
    tracker.record_usage(100)
    router = ProviderRouter()
    router._tracker = tracker
    decision = await router.get_fallback(
        "writer", "groq", "llama-3.3-70b-versatile",
        "Rate limit reached for model llama-3.3-70b-versatile on tokens per minute",
    )
    assert decision.provider == "nvidia"


async def test_fallback_non_rate_limit_goes_nvidia(router) -> None:
    decision = await router.get_fallback(
        "writer", "groq", "llama-3.3-70b-versatile",
        "Internal server error",
    )
    assert decision.provider == "nvidia"


async def test_route_unknown_agent_defaults_ollama(router) -> None:
    decision = await router.route("unknown_agent", "sys", "user")
    assert decision.provider == "gpt-oss"


def test_routing_decision_dataclass() -> None:
    d = RoutingDecision(
        provider="groq", model="llama-3.3-70b-versatile",
        estimated_input_tokens=100, estimated_output_tokens=200,
        routing_reason="test", fallback_provider="gpt-oss",
        fallback_model="gpt-oss:120b", execution_priority=3,
    )
    assert d.provider == "groq"
    assert d.fallback_provider == "gpt-oss"
    assert d.execution_priority == 3


def test_route_ollama_response_format(router) -> None:
    decision = router._route_ollama("research", 50, 100)
    assert decision.provider == "gpt-oss"
    assert decision.estimated_input_tokens == 50
    assert decision.routing_reason


async def test_route_groq_exhausted_tpm_falls_back() -> None:
    tracker = TokenBudgetTracker(tpm_limit=100)
    tracker.record_usage(100)
    router = ProviderRouter()
    router._tracker = tracker
    decision = router._route_groq("writer", 50, 50, 100)
    assert decision.provider == "gpt-oss", f"Expected Ollama fallback on TPM exhaustion, got {decision.provider}"

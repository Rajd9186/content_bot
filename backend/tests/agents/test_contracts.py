from __future__ import annotations

import pytest

from app.agents.contracts import (
    AgentContract, AgentInput, AgentOutput, AgentStatus,
    RetryPolicy, TimeoutPolicy, TokenUsage, AgentTelemetry,
)


def test_agent_contract_creation() -> None:
    contract = AgentContract(
        name="test_agent",
        description="Test agent for contracts",
        version="1.0.0",
        retry_policy=RetryPolicy(max_retries=3),
        timeout_policy=TimeoutPolicy(execution_ms=60000),
    )
    assert contract.name == "test_agent"
    assert contract.description == "Test agent for contracts"
    assert contract.version == "1.0.0"
    assert contract.retry_policy.max_retries == 3
    assert contract.timeout_policy.execution_ms == 60000


def test_agent_input_creation() -> None:
    agent_input = AgentInput(
        correlation_id="test-123",
        workflow_id="workflow-456",
        metadata={"key": "value"}
    )
    assert agent_input.correlation_id == "test-123"
    assert agent_input.workflow_id == "workflow-456"
    assert agent_input.metadata == {"key": "value"}


def test_agent_output_creation() -> None:
    output = AgentOutput(
        success=True,
        data={"result": "test"},
        error=None
    )
    assert output.success is True
    assert output.data == {"result": "test"}
    assert output.error is None


def test_retry_policy_defaults() -> None:
    policy = RetryPolicy()
    assert policy.max_retries == 3
    assert policy.base_delay_ms == 1000.0
    assert policy.max_delay_ms == 30000.0
    assert "timeout" in policy.retryable_errors


def test_timeout_policy_defaults() -> None:
    policy = TimeoutPolicy()
    assert policy.execution_ms == 120000
    assert policy.prompt_construction_ms == 5000


def test_token_usage_creation() -> None:
    usage = TokenUsage(
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        provider="openai",
        model="gpt-4"
    )
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 200
    assert usage.total_tokens == 300
    assert usage.provider == "openai"
    assert usage.model == "gpt-4"


def test_agent_telemetry_creation() -> None:
    telemetry = AgentTelemetry(
        agent_name="test_agent",
        status=AgentStatus.COMPLETED,
        correlation_id="test-123",
        workflow_id="workflow-456"
    )
    assert telemetry.agent_name == "test_agent"
    assert telemetry.status == AgentStatus.COMPLETED
    assert telemetry.correlation_id == "test-123"
    assert telemetry.workflow_id == "workflow-456"

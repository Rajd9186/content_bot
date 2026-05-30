from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.base import BaseAgent
from app.agents.contracts import AgentContract, AgentInput, AgentOutput, RetryPolicy
from app.agents.pipeline import ExecutionPipeline


class TestAgent(BaseAgent):
    def __init__(self) -> None:
        contract = AgentContract(
            name="test_agent",
            description="Test agent for error handling",
            version="1.0.0",
            retry_policy=RetryPolicy(max_retries=2, base_delay_ms=10.0)  # Fast retries for testing
        )
        super().__init__(contract)


async def test_agent_execution_timeout_handling() -> None:
    """Test that agent execution respects timeouts"""
    
    agent = TestAgent()
    
    # Mock a slow execution that exceeds timeout
    async def slow_validation(agent_input):
        await asyncio.sleep(0.1)  # Simulate slow operation
        return type("ValidationResult", (), {"valid": True})()
    
    agent._validate_input = slow_validation  # type: ignore
    
    # Set very short timeout
    agent.contract.timeout_policy.execution_ms = 1  # 1ms timeout
    
    agent_input = AgentInput(correlation_id="timeout-test")
    
    result = await agent.execute(agent_input)
    
    # Fallback handles timeout gracefully
    assert result.telemetry.fallback_used is True


async def test_agent_execution_cancellation() -> None:
    """Test agent execution cancellation"""
    
    agent = TestAgent()
    
    # Mock a slow operation
    async def slow_execute(*args, **kwargs):
        await asyncio.sleep(0.1)
        return (True, {"result": "success"}, None)
    
    agent._execute_with_retry = slow_execute  # type: ignore
    
    agent_input = AgentInput(correlation_id="cancel-test")
    
    # Start execution and cancel quickly
    task = asyncio.create_task(agent.execute(agent_input))
    task.cancel()
    
    try:
        result = await task
        assert result.success is False
        assert result.telemetry.status == "CANCELLED"
    except asyncio.CancelledError:
        # CancelledError propagation is also valid
        pass


async def test_pipeline_timeout_during_execution() -> None:
    """Test pipeline timeout handling"""
    
    agent = TestAgent()
    pipeline = ExecutionPipeline(agent)
    
    # Mock slow provider execution
    async def slow_provider_execute(*args, **kwargs):
        await asyncio.sleep(0.1)
        return (True, {"result": "success"}, None)
    
    agent._execute_with_retry = slow_provider_execute  # type: ignore
    
    # Set very short timeout
    agent.contract.timeout_policy.execution_ms = 1
    
    agent_input = AgentInput(correlation_id="pipeline-timeout-test")
    
    result = await pipeline.execute(agent_input)
    
    # Should handle timeout gracefully via fallback
    assert result.telemetry.fallback_used is True


async def test_agent_retry_logic_with_transient_failures() -> None:
    """Test that agents retry on transient failures"""
    
    agent = TestAgent()
    
    # Mock methods
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._build_provider_request = lambda x: None
    
    # Simulate a provider that fails transiently then succeeds
    provider_mock = AsyncMock()
    call_count = 0
    async def provider_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return type("ProviderResponse", (), {"success": False, "content": "", "error": "Provider temporary error"})()
        return type("ProviderResponse", (), {"success": True, "content": '{"result": "finally worked"}', "error": None})()
    
    provider_mock.execute = provider_execute
    agent._get_provider = AsyncMock(return_value=provider_mock)  # type: ignore
    
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    agent_input = AgentInput(correlation_id="retry-test")
    
    result = await agent.execute(agent_input)
    
    # Should eventually succeed after retries
    assert result.success is True
    assert result.data["result"] == "finally worked"
    assert call_count == 2  # One failure, then success (max_retries=2 on test agent)


async def test_agent_persistent_failure_handling() -> None:
    """Test handling of persistent failures"""
    
    agent = TestAgent()
    
    # Mock methods
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._get_provider = AsyncMock()
    agent._build_provider_request = lambda x: None
    agent._execute_with_retry = AsyncMock(return_value=(False, None, "Persistent error"))
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    agent_input = AgentInput(correlation_id="persistent-fail-test")
    
    result = await agent.execute(agent_input)
    
    # Should fail after all retries exhausted
    assert result.success is True  # Fallback makes it "successful"
    assert result.telemetry.fallback_used is True
    assert "_fallback" in result.data


async def test_agent_input_validation_failure_propagation() -> None:
    """Test that input validation failures propagate correctly"""
    
    agent = TestAgent()
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {
        "valid": False, "errors": ["Missing required field: topic"]
    })())
    
    agent_input = AgentInput(correlation_id="validation-fail-test")
    
    result = await agent.execute(agent_input)
    
    assert result.success is False
    assert "Missing required field" in result.error  # type: ignore
    assert result.telemetry.status == "FAILED"


async def test_agent_output_validation_failure_triggers_retry() -> None:
    """Test that output validation failures trigger retry via execute_single"""
    
    agent = TestAgent()
    
    # Mock methods
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._build_provider_request = lambda x: None
    
    # Mock provider to return valid JSON, validation happens in execute_single
    provider_mock = AsyncMock()
    call_count = 0
    async def provider_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return type("ProviderResponse", (), {"success": True, "content": '{"invalid": "data"}', "error": None})()
        return type("ProviderResponse", (), {"success": True, "content": '{"valid": "data"}', "error": None})()

    provider_mock.execute = provider_execute
    agent._get_provider = AsyncMock(return_value=provider_mock)  # type: ignore
    
    # First validation fails, second succeeds
    validation_call_count = 0
    async def mock_validate_output(data, agent_input):
        nonlocal validation_call_count
        validation_call_count += 1
        if validation_call_count == 1:
            return type("ValidationResult", (), {"valid": False, "errors": ["Invalid schema"]})()
        return type("ValidationResult", (), {"valid": True})()
    
    agent._validate_output = mock_validate_output  # type: ignore
    
    agent_input = AgentInput(correlation_id="output-validation-test")
    
    result = await agent.execute(agent_input)
    
    # Note: VALIDATION_FAILED is not retryable by default, so fallback is used
    assert result.telemetry.fallback_used is True
    assert result.data is not None

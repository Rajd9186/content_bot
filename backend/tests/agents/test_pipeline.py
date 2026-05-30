from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.pipeline import ExecutionPipeline, PipelineStage
from app.agents.base import BaseAgent
from app.agents.contracts import AgentContract, AgentInput, AgentOutput, TokenUsage


class MockAgent(BaseAgent):
    def __init__(self) -> None:
        contract = AgentContract(
            name="mock_agent",
            description="Mock agent for pipeline testing",
            version="1.0.0"
        )
        super().__init__(contract)


async def test_execution_pipeline_creation() -> None:
    agent = MockAgent()
    pipeline = ExecutionPipeline(agent)
    
    assert pipeline._agent == agent
    assert len(pipeline._hooks) == 0


async def test_execution_pipeline_add_hook() -> None:
    agent = MockAgent()
    pipeline = ExecutionPipeline(agent)
    
    async def mock_hook(stage, agent_input, stage_data):
        pass
    
    pipeline.add_hook(mock_hook)
    assert len(pipeline._hooks) == 1


async def test_execution_pipeline_run_stage_success() -> None:
    agent = MockAgent()
    pipeline = ExecutionPipeline(agent)
    
    agent_input = AgentInput(correlation_id="test-123")
    stage_data = {}
    
    async def mock_stage_fn(agent_input, stage_data):
        return {"result": "success"}
    
    result = await pipeline._run_stage(
        PipelineStage.INPUT_VALIDATION,
        agent_input,
        stage_data,
        mock_stage_fn
    )
    
    assert result == {"result": "success"}


async def test_execution_pipeline_run_stage_exception() -> None:
    agent = MockAgent()
    pipeline = ExecutionPipeline(agent)
    
    agent_input = AgentInput(correlation_id="test-123")
    stage_data = {}
    
    async def failing_stage_fn(agent_input, stage_data):
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        await pipeline._run_stage(
            PipelineStage.INPUT_VALIDATION,
            agent_input,
            stage_data,
            failing_stage_fn
        )


async def test_execution_pipeline_execute_success() -> None:
    agent = MockAgent()
    
    # Mock the agent methods
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    # Simulate successful LLM execution through the pipeline
    mock_request = type("MockRequest", (), {"model": "test", "system_prompt": "", "messages": [], "temperature": 0.1, "max_tokens": 100, "timeout_ms": 1000})()
    mock_response = type("MockResponse", (), {"success": True, "content": '{"result": "success"}', "error": None, "token_usage": TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, provider="test", model="test"), "latency_ms": 0.0, "provider": "test", "model": "test"})()
    mock_provider = AsyncMock()
    mock_provider.execute.return_value = mock_response
    agent._get_provider = AsyncMock(return_value=mock_provider)  # type: ignore
    agent._build_provider_request = lambda x: mock_request
    
    pipeline = ExecutionPipeline(agent)
    agent_input = AgentInput(correlation_id="test-123")
    
    result = await pipeline.execute(agent_input)
    
    assert result.success is True
    assert result.data == {"result": "success"}


async def test_execution_pipeline_execute_input_validation_failure() -> None:
    agent = MockAgent()
    
    # Mock validation to fail
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {
        "valid": False, "errors": ["Invalid input"]
    })())
    
    pipeline = ExecutionPipeline(agent)
    agent_input = AgentInput(correlation_id="test-123")
    
    result = await pipeline.execute(agent_input)
    
    assert result.success is False
    assert "Invalid input" in result.error  # type: ignore


async def test_execution_pipeline_execute_with_hooks() -> None:
    agent = MockAgent()
    
    # Mock successful execution
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._get_provider = AsyncMock()
    agent._build_provider_request = lambda x: None
    agent._execute_with_retry = AsyncMock(return_value=(True, {"result": "success"}, None))
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    pipeline = ExecutionPipeline(agent)
    agent_input = AgentInput(correlation_id="test-123")
    
    hook_calls = []
    
    async def tracking_hook(stage, agent_input, stage_data):
        hook_calls.append((stage, agent_input.correlation_id))
    
    pipeline.add_hook(tracking_hook)
    
    result = await pipeline.execute(agent_input)
    
    assert result.success is True
    assert len(hook_calls) > 0
    assert hook_calls[0][1] == "test-123"  # correlation_id passed through


async def test_execution_pipeline_execute_provider_failure_triggers_fallback() -> None:
    agent = MockAgent()
    
    # Mock provider to fail
    mock_request = type("MockRequest", (), {"model": "test", "system_prompt": "", "messages": [], "temperature": 0.1, "max_tokens": 100, "timeout_ms": 1000})()
    mock_response = type("MockResponse", (), {"success": False, "content": "", "error": "Provider error", "token_usage": TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, provider="test", model="test"), "latency_ms": 0.0, "provider": "test", "model": "test"})()
    mock_provider = AsyncMock()
    mock_provider.execute.return_value = mock_response
    agent._get_provider = AsyncMock(return_value=mock_provider)  # type: ignore
    agent._build_provider_request = lambda x: mock_request
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    pipeline = ExecutionPipeline(agent)
    agent_input = AgentInput(correlation_id="test-123")
    
    result = await pipeline.execute(agent_input)
    
    assert result.success is True  # Fallback considered success
    assert result.telemetry.fallback_used is True


async def test_execution_pipeline_execute_cancellation() -> None:
    agent = MockAgent()
    
    # Mock provider with slow execution for cancellation testing
    mock_request = type("MockRequest", (), {"model": "test", "system_prompt": "", "messages": [], "temperature": 0.1, "max_tokens": 100, "timeout_ms": 1000})()
    mock_provider = AsyncMock()
    
    async def slow_execute(request):
        await asyncio.sleep(0.5)
        return type("MockResponse", (), {"success": True, "content": "{}", "error": None, "token_usage": TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, provider="test", model="test"), "latency_ms": 0.0, "provider": "test", "model": "test"})()
    
    mock_provider.execute = slow_execute
    agent._get_provider = AsyncMock(return_value=mock_provider)  # type: ignore
    agent._build_provider_request = lambda x: mock_request
    agent._validate_input = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    agent._build_prompt = AsyncMock()
    agent._validate_output = AsyncMock(return_value=type("ValidationResult", (), {"valid": True})())
    
    pipeline = ExecutionPipeline(agent)
    agent_input = AgentInput(correlation_id="test-123")
    
    # Start execution and cancel quickly
    task = asyncio.create_task(pipeline.execute(agent_input))
    task.cancel()
    
    try:
        result = await task
        assert result.success is False
        assert result.error == "Cancelled"
        assert result.telemetry.status == "CANCELLED"
    except asyncio.CancelledError:
        # CancelledError propagation is also valid
        pass

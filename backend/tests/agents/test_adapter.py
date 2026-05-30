from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.adapter import OrchestrationAgentAdapter
from app.agents.contracts import AgentOutput


async def test_adapter_execute_agent_success() -> None:
    adapter = OrchestrationAgentAdapter()
    
    # Mock successful agent execution
    mock_output = AgentOutput(
        success=True,
        data={"result": "test_content"},
        error=None
    )
    
    with patch("app.agents.adapter.agent_registry.get_or_create") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.name = "test_agent"
        mock_get_agent.return_value = mock_agent
        
        with patch("app.agents.adapter.ExecutionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = mock_output
            mock_pipeline_class.return_value = mock_pipeline
            
            result = await adapter.execute_agent(
                agent_name="test_agent",
                correlation_id="test-123",
                workflow_id="workflow-456",
                template_kwargs={"topic": "AI"}
            )
            
            assert result.success is True
            assert result.data["result"] == "test_content"
            mock_get_agent.assert_called_once()
            mock_pipeline.execute.assert_called_once()


async def test_adapter_execute_agent_with_pipeline_caching() -> None:
    adapter = OrchestrationAgentAdapter()
    
    mock_output = AgentOutput(success=True, data={"cached": True})
    
    with patch("app.agents.adapter.agent_registry.get_or_create") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.name = "cached_agent"
        mock_get_agent.return_value = mock_agent
        
        with patch("app.agents.adapter.ExecutionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = mock_output
            mock_pipeline_class.return_value = mock_pipeline
            
            # Execute twice with same agent
            await adapter.execute_agent("cached_agent", "test-123")
            await adapter.execute_agent("cached_agent", "test-123")
            
            # Should create pipeline once and reuse
            assert len(adapter._pipeline_cache) == 1
            mock_pipeline_class.assert_called_once()


async def test_adapter_execute_stage_mapping() -> None:
    adapter = OrchestrationAgentAdapter()
    
    mock_output = AgentOutput(success=True, data={"stage_result": "completed"})
    
    with patch.object(adapter, "execute_agent", AsyncMock(return_value=mock_output)) as mock_execute:
        context = {"title": "Test Article", "outline": "1. Intro\n2. Main"}
        
        result = await adapter.execute_stage(
            stage_name="WRITING",
            context=context,
            correlation_id="test-123",
            workflow_id="workflow-456"
        )
        
        assert result.success is True
        mock_execute.assert_called_once_with(
            agent_name="writer",  # Should map WRITING -> writer
            correlation_id="test-123",
            workflow_id="workflow-456",
            template_kwargs=context,
            provider_name="openai",
            model=None
        )


async def test_adapter_stage_to_agent_mapping() -> None:
    adapter = OrchestrationAgentAdapter()
    
    # Test various stage mappings
    mappings = {
        "PLANNING": "planner",
        "RESEARCH": "researcher", 
        "SYNTHESIS": "synthesizer",
        "OUTLINING": "outliner",
        "WRITING": "writer",
        "VALIDATION": "validator",
        "SEO": "seo",
        "FACT_CHECK": "fact_checker",
        "FINALIZATION": "finalizer",
    }
    
    for stage, expected_agent in mappings.items():
        mapped_agent = adapter._stage_to_agent(stage)
        assert mapped_agent == expected_agent


async def test_adapter_execute_agent_with_custom_provider() -> None:
    adapter = OrchestrationAgentAdapter()
    
    mock_output = AgentOutput(success=True, data={"provider": "anthropic"})
    
    with patch("app.agents.adapter.agent_registry.get_or_create") as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.name = "test_agent"
        mock_get_agent.return_value = mock_agent
        
        with patch("app.agents.adapter.ExecutionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline.execute.return_value = mock_output
            mock_pipeline_class.return_value = mock_pipeline
            
            result = await adapter.execute_agent(
                agent_name="test_agent",
                correlation_id="test-123",
                provider_name="anthropic",
                model="claude-2"
            )
            
            # Verify registry was called with custom provider
            mock_get_agent.assert_called_once_with(
                name="test_agent",
                provider_name="anthropic",
                model="claude-2"
            )

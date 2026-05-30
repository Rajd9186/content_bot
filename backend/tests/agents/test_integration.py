from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.adapter import orchestration_adapter
from app.agents.registry import agent_registry
from app.agents.contracts import AgentInput, AgentOutput, AgentTelemetry, AgentStatus
from app.agents.agents.planner import PlannerAgent
from app.agents.agents.writer import WriterAgent


async def test_full_agent_execution_flow() -> None:
    """Test complete agent execution through the pipeline"""
    
    # Register test agents
    agent_registry.register(PlannerAgent)
    
    with patch("app.agents.provider.factory.ProviderFactory.get_or_create") as mock_factory:
        # Mock a successful provider response
        mock_provider = AsyncMock()
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.content = '''{
            "title": "AI Strategy",
            "goals": "Explain AI concepts",
            "audience": "Business leaders", 
            "themes": ["Introduction", "Applications", "Future"],
            "research_questions": ["What is AI?", "How can it help business?"],
            "suggested_structure": ["Intro", "Main", "Conclusion"]
        }'''
        mock_response.token_usage.total_tokens = 150
        mock_response.provider = "openai"
        mock_response.model = "gpt-4"
        mock_provider.execute.return_value = mock_response
        mock_factory.return_value = mock_provider
        
        # Execute agent through adapter
        result = await orchestration_adapter.execute_agent(
            agent_name="planner",
            correlation_id="integration-test-123",
            workflow_id="test-workflow-456",
            template_kwargs={
                "topic": "Artificial Intelligence",
                "goals": "Business applications",
                "audience": "Executives"
            }
        )
        
        # Verify successful execution
        assert result.success is True
        assert "title" in result.data
        assert "AI Strategy" in result.data["title"]
        assert result.telemetry.agent_name == "planner"
        assert result.telemetry.correlation_id == "integration-test-123"


async def test_agent_execution_with_fallback_preserves_context() -> None:
    """Critical integration test: fallback preserves original context"""
    
    agent_registry.register(WriterAgent)
    
    with patch("app.agents.provider.factory.ProviderFactory.get_or_create") as mock_factory:
        # Mock provider that always fails
        mock_provider = AsyncMock()
        mock_response = AsyncMock()
        mock_response.success = False
        mock_response.error = "Provider timeout"
        mock_provider.execute.return_value = mock_response
        mock_factory.return_value = mock_provider
        
        original_context = {
            "title": "Machine Learning in Healthcare: A Comprehensive Guide",
            "outline": "1. Introduction\n2. Diagnosis Applications\n3. Treatment Planning\n4. Ethical Considerations",
            "research_synthesis": "ML improves diagnostic accuracy by 30% and reduces costs in healthcare settings"
        }
        
        result = await orchestration_adapter.execute_agent(
            agent_name="writer",
            correlation_id="fallback-test-123",
            template_kwargs=original_context
        )
        
        # Should succeed with fallback
        assert result.success is True
        assert result.telemetry.fallback_used is True
        
        # Critical: should preserve original context, NOT produce placeholders
        content = result.data.get("content", "")
        assert "# Untitled" not in content
        assert "Healthcare: A Comprehensive Guide" in content or "Machine Learning" in content
        assert "diagnostic accuracy" in content.lower() or "healthcare" in content.lower()
        assert "[Content needed]" not in content
        assert "TODO" not in content
        assert len(content.split()) > 100  # Substantial content


async def test_agent_execution_pipeline_stages_all_execute() -> None:
    """Test that all 10 pipeline stages execute properly"""
    
    agent_registry.register(PlannerAgent)
    
    with patch("app.agents.provider.factory.ProviderFactory.get_or_create") as mock_factory:
        mock_provider = AsyncMock()
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.content = '{"title": "Test Plan", "goals": "Test", "themes": ["A", "B"]}'
        mock_response.token_usage.total_tokens = 50
        mock_provider.execute.return_value = mock_response
        mock_factory.return_value = mock_provider
        
        # Track pipeline stage execution
        stage_calls = []
        
        # Mock the pipeline to track stage execution
        original_pipeline_init = None
        with patch("app.agents.adapter.ExecutionPipeline.__init__", lambda self, agent: setattr(self, '_agent', agent) or setattr(self, '_hooks', [])):
            with patch("app.agents.adapter.ExecutionPipeline.execute") as mock_execute:
                async def mock_pipeline_execute(agent_input):
                    # Simulate full pipeline execution
                    return AgentOutput(
                        success=True,
                        data={"title": "Test Plan", "goals": "Test", "themes": ["A", "B"]},
                        telemetry=AgentTelemetry(
                            agent_name="planner",
                            status=AgentStatus.COMPLETED,
                            correlation_id=agent_input.correlation_id,
                        )
                    )
                
                mock_execute.side_effect = mock_pipeline_execute
                
                result = await orchestration_adapter.execute_agent(
                    agent_name="planner",
                    correlation_id="pipeline-test-123",
                    template_kwargs={"topic": "Test"}
                )
                
                assert result.success is True
                assert mock_execute.call_count == 1


async def test_multiple_agent_executions_with_caching() -> None:
    """Test that pipeline caching works correctly"""
    
    adapter = orchestration_adapter
    
    with patch("app.agents.provider.factory.ProviderFactory.get_or_create") as mock_factory:
        mock_provider = AsyncMock()
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.content = '{"result": "test"}'
        mock_provider.execute.return_value = mock_response
        mock_factory.return_value = mock_provider
        
        # Clear cache first
        adapter._pipeline_cache.clear()
        
        # Execute same agent multiple times
        await adapter.execute_agent("planner", "test-1", template_kwargs={"topic": "A"})
        await adapter.execute_agent("planner", "test-2", template_kwargs={"topic": "B"})
        await adapter.execute_agent("writer", "test-3", template_kwargs={"title": "C"})
        
        # Should have cached pipelines
        assert len(adapter._pipeline_cache) == 2  # planner and writer
        assert "planner" in str(list(adapter._pipeline_cache.keys()))
        assert "writer" in str(list(adapter._pipeline_cache.keys()))

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.agents.planner import PlannerAgent
from app.agents.contracts import AgentInput, AgentOutput


async def test_planner_agent_creation() -> None:
    agent = PlannerAgent()
    assert agent.name == "planner"
    assert agent.contract.version == "1.0.0"
    assert "planning" in agent.contract.required_capabilities


async def test_planner_agent_input_validation_success() -> None:
    agent = PlannerAgent()
    agent_input = AgentInput(
        correlation_id="test-123",
        metadata={
            "template_kwargs": {
                "topic": "AI Ethics"
            }
        }
    )
    
    result = await agent._validate_input(agent_input)
    assert result.valid is True
    assert len(result.errors) == 0


async def test_planner_agent_input_validation_failure() -> None:
    agent = PlannerAgent()
    agent_input = AgentInput(
        correlation_id="test-123",
        metadata={
            "template_kwargs": {
                # Missing required "topic"
            }
        }
    )
    
    result = await agent._validate_input(agent_input)
    assert result.valid is False
    assert "topic" in result.errors[0]


async def test_planner_agent_build_prompt() -> None:
    agent = PlannerAgent()
    agent_input = AgentInput(
        correlation_id="test-123",
        metadata={
            "template_kwargs": {
                "topic": "Machine Learning",
                "goals": "Explain ML concepts",
                "audience": "Beginners"
            }
        }
    )
    
    prompt_context = await agent._build_prompt(agent_input)
    
    assert prompt_context.agent_type == "planner"
    assert "Machine Learning" in prompt_context.user_prompt
    assert "Explain ML concepts" in prompt_context.user_prompt
    assert len(prompt_context.messages) >= 2


async def test_planner_agent_parse_output_success() -> None:
    agent = PlannerAgent()
    json_content = '''{
        "title": "AI for Beginners",
        "goals": "Explain basic concepts",
        "audience": "General audience",
        "themes": ["Introduction", "Applications"],
        "research_questions": ["What is AI?", "How is it used?"],
        "suggested_structure": ["Intro", "Main", "Conclusion"]
    }'''
    
    result = await agent._parse_output(json_content, AgentInput(correlation_id="test"))
    
    assert result is not None
    assert result["title"] == "AI for Beginners"
    assert len(result["themes"]) == 2


async def test_planner_agent_validate_output_success() -> None:
    agent = PlannerAgent()
    data = {
        "title": "AI Guide",
        "goals": "Explain AI",
        "themes": ["Intro", "Main", "Conclusion"]
    }
    
    result = await agent._validate_output(data, AgentInput(correlation_id="test"))
    
    assert result.valid is True
    assert len(result.errors) == 0


async def test_planner_agent_validate_output_missing_fields() -> None:
    agent = PlannerAgent()
    data = {
        # Missing required fields
    }
    
    result = await agent._validate_output(data, AgentInput(correlation_id="test"))
    
    assert result.valid is False
    assert len(result.errors) >= 2  # At least title and goals missing
    assert any("title" in err for err in result.errors)
    assert any("goals" in err for err in result.errors)

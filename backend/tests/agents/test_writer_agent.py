from __future__ import annotations

import pytest

from app.agents.agents.writer import WriterAgent
from app.agents.contracts import AgentInput


async def test_writer_agent_creation() -> None:
    agent = WriterAgent()
    assert agent.name == "writer"
    assert "writing" in agent.contract.required_capabilities
    assert "content_generation" in agent.contract.required_capabilities


async def test_writer_agent_input_validation_success() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(
        correlation_id="test-123",
        metadata={
            "template_kwargs": {
                "title": "AI Ethics",
                "outline": "1. Intro\n2. Main\n3. Conclusion"
            }
        }
    )
    
    result = await agent._validate_input(agent_input)
    assert result.valid is True


async def test_writer_agent_input_validation_failure() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(
        correlation_id="test-123",
        metadata={
            "template_kwargs": {
                # Missing required title and outline
            }
        }
    )
    
    result = await agent._validate_input(agent_input)
    assert result.valid is False
    assert len(result.errors) >= 1


async def test_writer_agent_parse_markdown_success() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(correlation_id="test-123")
    
    markdown_content = """# AI Ethics Guide

This is a comprehensive guide to AI ethics that covers the fundamental principles and practical applications.

## Introduction

Artificial Intelligence ethics is a critical field that examines the moral implications of AI systems.

## Key Principles

1. Fairness and bias mitigation
2. Transparency and explainability
3. Privacy and data protection

## Conclusion

AI ethics is essential for responsible technology development."""
    
    # Mock the base class _parse_json_output to return markdown as if it were parsed
    agent._parse_json_output = lambda x: {"content": markdown_content}  # type: ignore
    
    result = await agent._parse_output(markdown_content, agent_input)
    
    assert result is not None
    assert "content" in result
    assert "AI Ethics Guide" in result["content"]
    assert result["word_count"] > 50


async def test_writer_agent_parse_markdown_detects_placeholders() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(correlation_id="test-123")
    
    placeholder_content = """# Untitled

[Content needed]

TODO: Write introduction here."""
    
    # Mock the base class _parse_json_output to return markdown as if it were parsed
    agent._parse_json_output = lambda x: {"content": placeholder_content}  # type: ignore
    
    result = await agent._parse_output(placeholder_content, agent_input)
    
    # Should return None for placeholder content
    assert result is None


async def test_writer_agent_validate_output_success() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(correlation_id="test-123")
    
    data = {
        "content": "# Valid Content\n\nThis is a well-written article with substantial content that meets all requirements. It covers multiple important topics and provides valuable insights for readers. The analysis is thorough and well-researched, drawing from authoritative sources to support each claim. Additionally, the article includes practical examples and actionable recommendations that readers can apply immediately. The structure is logical and easy to follow, making complex concepts accessible to a broad audience.",
        "title": "Valid Content",
        "word_count": 150
    }
    
    result = await agent._validate_output(data, agent_input)
    
    assert result.valid is True
    assert len(result.errors) == 0


async def test_writer_agent_validate_output_detects_untitled() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(correlation_id="test-123")
    
    data = {
        "content": "# Untitled\n\nThis content has an invalid title.",
        "title": "Untitled",
        "word_count": 100
    }
    
    result = await agent._validate_output(data, agent_input)
    
    assert result.valid is False
    assert any("Untitled" in err for err in result.errors)


async def test_writer_agent_validate_output_detects_short_content() -> None:
    agent = WriterAgent()
    agent_input = AgentInput(correlation_id="test-123")
    
    data = {
        "content": "# Title\n\nShort.",
        "title": "Short Content",
        "word_count": 3
    }
    
    result = await agent._validate_output(data, agent_input)
    
    assert result.valid is False
    assert any("too short" in err.lower() for err in result.errors)

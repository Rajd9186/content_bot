from __future__ import annotations

import pytest

from app.agents.prompt.engine import PromptEngine, PromptContext
from app.agents.prompt.builders import (
    PromptBuilder, ResearchPromptBuilder, WritingPromptBuilder,
)
from app.agents.prompt.templates import get_system_prompt, get_user_prompt


def test_prompt_context_creation() -> None:
    ctx = PromptContext(agent_type="test_agent", correlation_id="test-123")
    assert ctx.agent_type == "test_agent"
    assert ctx.correlation_id == "test-123"
    assert ctx.messages == []


def test_prompt_context_hash() -> None:
    ctx1 = PromptContext(agent_type="test_agent")
    ctx1.system_prompt = "System prompt 1"
    ctx1.user_prompt = "User prompt 1"
    
    ctx2 = PromptContext(agent_type="test_agent")
    ctx2.system_prompt = "System prompt 2"
    ctx2.user_prompt = "User prompt 2"
    
    assert ctx1.prompt_hash != ctx2.prompt_hash


def test_prompt_engine_build() -> None:
    engine = PromptEngine()
    ctx = engine.build_sync(
        agent_type="planner",
        correlation_id="test-123",
        template_kwargs={
            "topic": "AI",
            "goals": "Explain concepts",
            "audience": "Beginners",
            "context": "Explain AI concepts to beginners"
        }
    )
    
    assert ctx.agent_type == "planner"
    assert ctx.correlation_id == "test-123"
    assert len(ctx.messages) >= 2  # system + user
    assert ctx.system_prompt != ""
    assert "AI" in ctx.user_prompt


def test_planner_system_prompt_includes_no_placeholders() -> None:
    prompt = get_system_prompt("planner")
    assert "placeholders" in prompt
    assert "[Content needed]" in prompt  # warning against placeholders


def test_writer_system_prompt_includes_markdown_instructions() -> None:
    prompt = get_system_prompt("writer")
    assert "well-formatted markdown" in prompt
    assert "heading hierarchy" in prompt


def test_researcher_user_prompt_is_structured_not_dumps() -> None:
    prompt = get_user_prompt(
        "researcher",
        plan_summary="Test plan summary",
        research_questions="1. What is AI?\n2. Why is it important?",
        existing_knowledge="Prior knowledge"
    )
    
    # Should NOT be a dump of raw key:value pairs
    assert "plan_summary:" not in prompt
    assert "research_questions:" not in prompt
    assert "existing_knowledge:" not in prompt
    
    # Should be structured narrative
    assert "Research Request" in prompt
    assert "### Content Plan Summary" in prompt
    assert "### Research Questions" in prompt


def test_prompt_builder_with_researcher() -> None:
    builder = ResearchPromptBuilder()
    builder.with_plan({
        "title": "AI Research",
        "goals": "Understand AI",
        "themes": ["ML", "NLP", "Computer Vision"]
    }).with_existing_knowledge("Basic ML knowledge")
    
    kwargs = builder.build()
    assert "plan_summary" in kwargs
    assert "Title: AI Research" in kwargs["plan_summary"]
    assert "research_questions" in kwargs
    assert "ml knowledge" in kwargs["existing_knowledge"].lower()


def test_writing_prompt_builder_formats_outline_properly() -> None:
    builder = WritingPromptBuilder()
    builder.with_title("AI for Beginners").with_outline({
        "sections": [
            {"title": "Introduction", "key_points": ["What is AI?"]},
            {"title": "Applications", "key_points": ["Healthcare", "Finance"]}
        ]
    }).with_research_synthesis("AI is transforming industries")
    
    kwargs = builder.build()
    assert kwargs["title"] == "AI for Beginners"
    assert "Introduction" in kwargs["outline"]
    assert "What is AI?" in kwargs["outline"]
    assert "AI is transforming industries" in kwargs["research_synthesis"]

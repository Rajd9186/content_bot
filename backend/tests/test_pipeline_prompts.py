from __future__ import annotations

from app.pipeline.prompts import (
    SYSTEM_PROMPTS,
    build_system_prompt,
    build_research_prompt,
    build_planner_prompt,
    build_writer_prompt,
    build_seo_prompt,
    build_fact_check_prompt,
    build_compliance_prompt,
    build_finalizer_prompt,
    build_user_prompt,
)


def test_all_system_prompts_exist() -> None:
    required = {"research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"}
    assert required.issubset(SYSTEM_PROMPTS.keys())


def test_system_prompts_have_content() -> None:
    for agent_type, prompt in SYSTEM_PROMPTS.items():
        assert len(prompt) > 100, f"{agent_type} prompt too short"


def test_system_prompts_no_placeholders() -> None:
    for agent_type, prompt in SYSTEM_PROMPTS.items():
        assert "# Untitled" not in prompt, f"{agent_type} has placeholder"
        assert prompt.strip()[-1] != ":", f"{agent_type} ends with colon (incomplete)"
        # Check for template variables like {variable} or {{variable}}
        assert "{content" not in prompt.lower(), f"{agent_type} has template variable"


def test_build_system_prompt_default() -> None:
    prompt = build_system_prompt("unknown_type")
    assert "helpful AI assistant" in prompt


def test_research_prompt_contains_topic() -> None:
    state = {"topic": "Quantum Computing", "audience": "general", "goals": "Explain basics"}
    prompt = build_research_prompt(state)
    assert "Quantum Computing" in prompt
    assert "Research Request" in prompt


def test_planner_prompt_contains_research() -> None:
    state = {
        "topic": "AI",
        "research_data": {
            "summary": "AI is transforming industries",
            "key_points": ["Point 1", "Point 2"],
        },
    }
    prompt = build_planner_prompt(state)
    assert "AI is transforming" in prompt
    assert "Content Planning" in prompt


def test_writer_prompt_contains_outline() -> None:
    state = {
        "topic": "Test Topic",
        "audience": "developers",
        "tone": "technical",
        "research_data": {
            "summary": "Research summary",
            "key_points": ["Key finding"],
            "statistics": ["75% of developers"],
        },
        "plan": {},
        "outline": {
            "sections": [{"title": "Introduction", "key_points": ["Background"]}],
        },
    }
    prompt = build_writer_prompt(state)
    assert "Test Topic" in prompt
    assert "Introduction" in prompt
    assert "developers" in prompt


def test_seo_prompt_contains_content() -> None:
    state = {
        "draft_content": "# Article\n\nThis is the content to optimize.",
        "topic": "SEO Topic",
    }
    prompt = build_seo_prompt(state)
    assert "SEO Topic" in prompt
    assert "content to optimize" in prompt.lower()


def test_fact_check_prompt_contains_research() -> None:
    state = {
        "draft_content": "# Article\n\nFactual claim here.",
        "topic": "Test",
        "research_data": {
            "summary": "Research context for verification",
            "citations": ["Source 1", "Source 2"],
        },
    }
    prompt = build_fact_check_prompt(state)
    assert "Fact-Checking" in prompt
    assert "Research context" in prompt


def test_compliance_prompt_contains_topic() -> None:
    state = {"draft_content": "# Article\n\nContent here.", "topic": "Finance Topic"}
    prompt = build_compliance_prompt(state)
    assert "Finance Topic" in prompt
    assert "Compliance Review" in prompt


def test_finalizer_prompt() -> None:
    state = {
        "draft_content": "# Final\n\nContent.",
        "topic": "Final Topic",
        "seo_metadata": {"title": "SEO Title"},
        "fact_check_results": {"verified_claims": []},
        "compliance_results": {"compliance_status": "pass"},
    }
    prompt = build_finalizer_prompt(state)
    assert "Final Topic" in prompt
    assert "Content Assembly" in prompt


def test_build_user_prompt_unknown_type() -> None:
    prompt = build_user_prompt("unknown", {"topic": "Generic Topic"})
    assert "Generic Topic" in prompt


def test_build_user_prompt_known_types() -> None:
    for agent_type in ["research", "planner", "writer", "seo", "fact_checker", "compliance", "finalizer"]:
        prompt = build_user_prompt(agent_type, {"topic": "Test", "draft_content": "", "research_data": {}})
        assert len(prompt) > 50, f"{agent_type} prompt too short"

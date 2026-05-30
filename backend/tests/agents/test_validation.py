from __future__ import annotations

import pytest

from app.agents.validation.parser import ResponseParser
from app.agents.validation.schema import SchemaValidator
from app.agents.validation.recovery import FallbackGenerator


def test_response_parser_handles_valid_json() -> None:
    parser = ResponseParser()
    valid_json = '{"result": "test", "score": 95}'
    result, error = parser.parse_json(valid_json)
    assert result is not None
    assert result["result"] == "test"
    assert result["score"] == 95
    assert error is None


def test_response_parser_handles_json_in_code_blocks() -> None:
    parser = ResponseParser()
    with_code_block = "```json\n{\n  \"result\": \"test\"\n}\n```"
    result, error = parser.parse_json(with_code_block)
    assert result is not None
    assert result["result"] == "test"
    assert error is None


def test_response_parser_handles_malformed_json_recovery() -> None:
    parser = ResponseParser()
    malformed = '{"result": "test", "score": 95,}'  # trailing comma
    result, error = parser.parse_json(malformed)
    assert result is not None  # Should recover
    assert result["result"] == "test"
    assert error is None


def test_response_parser_detects_empty_content() -> None:
    parser = ResponseParser()
    content, error = parser.parse_markdown("# Untitled\n\n[Content needed]")
    assert content == ""
    assert error is not None
    assert "placeholder" in error.lower()


def test_response_parser_detects_placeholders() -> None:
    parser = ResponseParser()
    placeholders = parser._detect_placeholders("# Untitled\n\nTODO: Add content")
    assert "TODO" in placeholders
    assert "# Untitled" in placeholders


def test_response_parser_hallucinated_citations() -> None:
    parser = ResponseParser()
    content = "According to research [Source: Smith, 2023, AI Advances] but also [Source: Fake, 2025, NonExistent]"
    known_sources = ["Smith, 2023, AI Advances", "Johnson, 2022, ML Fundamentals"]
    hallucinated = parser.has_hallucinated_citations(content, known_sources)
    assert len(hallucinated) == 1
    assert "Fake, 2025, NonExistent" in hallucinated


def test_schema_validator_valid_data() -> None:
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        score: int
    
    validator = SchemaValidator()
    data = {"name": "test", "score": 95}
    result = validator.validate_data(data, TestModel)
    assert result.valid is True
    assert len(result.errors) == 0


def test_schema_validator_invalid_data() -> None:
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        score: int
    
    validator = SchemaValidator()
    data = {"name": "test", "score": "not_a_number"}
    result = validator.validate_data(data, TestModel)
    assert result.valid is False
    assert len(result.errors) > 0


def test_fallback_generator_preserves_original_kwargs() -> None:
    """CRITICAL TEST: Fallback must use ORIGINAL kwargs, NOT malformed LLM response"""
    generator = FallbackGenerator()
    
    # Original kwargs that should be preserved
    original_kwargs = {
        "title": "Original Title",
        "outline": "1. Intro\n2. Main\n3. Conclusion",
        "research_summary": "Original research findings on the topic"
    }
    
    fallback_data = generator.generate_fallback_output(
        agent_type="writer",
        original_kwargs=original_kwargs,
        error="LLM produced malformed JSON"
    )
    
    # Should preserve original title, NOT generate "# Untitled"
    assert "content" in fallback_data
    assert "# Original Title" in fallback_data["content"] or "Original Title" in fallback_data.get("title", "")
    assert "_fallback" in fallback_data
    assert fallback_data["_fallback"] is True


def test_fallback_generator_prevents_untitled_outputs() -> None:
    generator = FallbackGenerator()
    fallback_data = generator.generate_fallback_output(
        agent_type="writer",
        original_kwargs={"title": "AI Ethics"},
        error="Parse error"
    )
    
    # Should NOT produce "# Untitled"
    content = fallback_data.get("content", "")
    assert "# Untitled" not in content
    assert "AI Ethics" in content or fallback_data.get("title") == "AI Ethics"


def test_fallback_generator_for_planner_preserves_context() -> None:
    generator = FallbackGenerator()
    original_kwargs = {
        "topic": "Machine Learning",
        "goals": "Explain ML to beginners",
        "audience": "High school students"
    }
    
    fallback_data = generator.generate_fallback_output(
        agent_type="planner",
        original_kwargs=original_kwargs,
        error="Provider timeout"
    )
    
    assert "Machine Learning" in fallback_data.get("title", "")
    assert "beginners" in fallback_data.get("goals", "").lower()
    assert "students" in fallback_data.get("audience", "").lower()


def test_fallback_generator_for_researcher_produces_substantive_findings() -> None:
    generator = FallbackGenerator()
    original_kwargs = {
        "plan_summary": "ML for Education",
        "research_questions": "How is ML used in classrooms?"
    }
    
    fallback_data = generator.generate_fallback_output(
        agent_type="researcher",
        original_kwargs=original_kwargs,
        error="Malformed response"
    )
    
    assert "findings" in fallback_data
    findings = fallback_data["findings"]
    assert len(findings) > 0
    first_finding = findings[0]
    assert len(first_finding.get("finding", "").split()) > 20  # Substantive, not one-liner

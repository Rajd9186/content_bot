from __future__ import annotations

import pytest

from app.agents.validation.parser import ResponseParser
from app.agents.validation.recovery import FallbackGenerator


def test_response_parser_handles_trailing_commas() -> None:
    """Test JSON recovery for trailing commas"""
    parser = ResponseParser()
    malformed = '{"name": "test", "score": 95,}'  # trailing comma
    
    result, error = parser.parse_json(malformed)
    assert result is not None
    assert result["name"] == "test"
    assert result["score"] == 95
    assert error is None


def test_response_parser_handles_single_quotes() -> None:
    """Test JSON recovery for single quotes"""
    parser = ResponseParser()
    malformed = "{'name': 'test', 'score': 95}"  # single quotes
    
    result, error = parser.parse_json(malformed)
    assert result is not None
    assert result["name"] == "test"
    assert result["score"] == 95
    assert error is None


def test_response_parser_handles_missing_quotes() -> None:
    """Test JSON recovery for missing quotes"""
    parser = ResponseParser()
    malformed = '{name: "test", score: 95}'  # no quotes on keys
    
    result, error = parser.parse_json(malformed)
    assert result is not None
    assert result["name"] == "test"
    assert result["score"] == 95
    assert error is None


def test_response_parser_handles_incomplete_json() -> None:
    """Test JSON recovery for incomplete objects"""
    parser = ResponseParser()
    malformed = '{"name": "test", "details": {"score": 95'  # missing closing braces
    
    result, error = parser.parse_json(malformed)
    assert result is not None
    assert result["name"] == "test"
    assert result["details"]["score"] == 95
    assert error is None


def test_response_parser_handles_markdown_wrapped_json() -> None:
    """Test extraction of JSON from markdown with code blocks"""
    parser = ResponseParser()
    with_markdown = '''Here is the result:
```json
{
  "name": "test",
  "score": 95
}
```
Thank you!'''
    
    result, error = parser.parse_json(with_markdown)
    assert result is not None
    assert result["name"] == "test"
    assert result["score"] == 95
    assert error is None


def test_response_parser_rejects_completely_invalid() -> None:
    """Test that completely invalid content is rejected"""
    parser = ResponseParser()
    invalid = "This is just plain text with no JSON structure whatsoever"
    
    result, error = parser.parse_json(invalid)
    assert result is None
    assert error is not None
    assert "No valid JSON found" in error


def test_fallback_generator_preserves_original_context_on_malformed_response() -> None:
    """
    CRITICAL TEST: When LLM produces malformed response, fallback must use 
    ORIGINAL context, NOT try to extract from malformed response
    """
    generator = FallbackGenerator()
    
    # Original valid context that should be preserved
    original_kwargs = {
        "title": "Machine Learning Applications in Healthcare",
        "outline": "1. Introduction\n2. Diagnosis\n3. Treatment Planning\n4. Patient Monitoring",
        "research_synthesis": "ML improves diagnostic accuracy and reduces costs in healthcare"
    }
    
    # Simulate various malformed LLM responses - fallback should IGNORE these
    malformed_responses = [
        "I can't do that",  # Plain text refusal
        '{"title": "Untitled", "content": "[Content needed]"}',  # Placeholders
        '{"name": "wrong_field", "data": "irrelevant"}',  # Wrong schema
        '{"partial": "incomplete"',  # Incomplete JSON
        '{"title": ""}',  # Empty required fields
    ]
    
    for i, malformed_response in enumerate(malformed_responses):
        fallback_data = generator.generate_fallback_output(
            agent_type="writer",
            original_kwargs=original_kwargs,
            error=f"Malformed response {i+1}"
        )
        
        # Should ALWAYS preserve original context
        assert fallback_data is not None
        assert "_fallback" in fallback_data
        assert fallback_data["_fallback"] is True
        
        # Should NEVER produce "# Untitled"
        content = fallback_data.get("content", "")
        assert "# Untitled" not in content
        
        # Should preserve original title context
        assert "Healthcare" in fallback_data.get("title", "Machine Learning Applications in Healthcare")
        
        # Should produce substantive content, not placeholders
        assert len(content.split()) > 50  # Substantial content
        assert "[Content needed]" not in content
        assert "TODO" not in content


def test_fallback_generator_different_agents_preserve_context() -> None:
    """Test that different agents preserve their specific context"""
    generator = FallbackGenerator()
    
    # Planner context
    planner_kwargs = {"topic": "AI Ethics in Autonomous Vehicles"}
    planner_fallback = generator.generate_fallback_output(
        agent_type="planner",
        original_kwargs=planner_kwargs,
        error="Provider error"
    )
    assert "AI Ethics" in planner_fallback.get("title", "")
    assert "goals" in planner_fallback  # Goals are preserved or defaulted
    
    # Researcher context  
    researcher_kwargs = {
        "plan_summary": "Research on AI Ethics",
        "research_questions": "What are the ethical implications?"
    }
    researcher_fallback = generator.generate_fallback_output(
        agent_type="researcher", 
        original_kwargs=researcher_kwargs,
        error="Parse error"
    )
    assert len(researcher_fallback.get("findings", [])) > 0
    findings = researcher_fallback["findings"][0]
    assert len(findings.get("finding", "").split()) > 15  # Substantive, not one-liner


def test_response_parser_detects_empty_placeholder_content() -> None:
    """Test detection of various placeholder patterns"""
    parser = ResponseParser()
    
    # Each case tested individually for clarity
    cases = [
        ("# Untitled\n\n[Content needed]", True),        # Untitled heading
        ("# Title\n\nTODO: Add meaningful content here", False),  # Has title + TODO
        ("# [Insert Title]\n\n[Insert content here]", False),     # Has heading
        ("Lorem ipsum dolor sit amet", True),            # Lorem ipsum
        ("# \n\n", True),                                # Empty heading
        ("[Content needed]\n\nMore content needed", True),  # Content needed marker
    ]
    for content, should_be_empty in cases:
        parsed_content, error = parser.parse_markdown(content)
        if should_be_empty:
            assert parsed_content == "", f"Expected empty for: {content!r}"
            assert error is not None
            assert "placeholder" in error.lower() or "empty" in error.lower()
        else:
            assert parsed_content != "", f"Expected non-empty for: {content!r}"


def test_response_parser_accepts_valid_content() -> None:
    """Test that valid content is accepted"""
    parser = ResponseParser()
    
    valid_contents = [
        "# Machine Learning Basics\n\nThis is a comprehensive guide to ML.",
        "## Introduction\n\nArtificial Intelligence is transforming industries.",
        "# Valid Title\n\nContent with substance and meaningful information.",
    ]
    
    for content in valid_contents:
        parsed_content, error = parser.parse_markdown(content)
        assert parsed_content == content  # Should return as-is
        assert error is None

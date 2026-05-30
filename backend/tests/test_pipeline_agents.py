from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.pipeline.agents.base import PipelineAgent
from app.pipeline.agents.research_agent import ResearchAgent, extract_research_data
from app.pipeline.agents.planner_agent import PlannerAgent, extract_plan
from app.pipeline.agents.writer_agent import WriterAgent, extract_writer_output
from app.pipeline.agents.seo_agent import SEOAgent, extract_seo_output
from app.pipeline.agents.fact_checker_agent import FactCheckerAgent, extract_fact_check_output
from app.pipeline.agents.compliance_agent import ComplianceAgent, extract_compliance_output
from app.pipeline.agents.finalizer_agent import FinalizerAgent, extract_finalizer_output
from app.pipeline.router import RoutingDecision
from app.pipeline.state import NodeStatus, PipelineState


@pytest.fixture
def sample_state() -> PipelineState:
    return PipelineState(
        workflow_id="test-123",
        topic="Artificial Intelligence",
        audience="developers",
        tone="technical",
        goals="Explain AI concepts",
    )


def test_research_agent_class() -> None:
    agent = ResearchAgent()
    assert agent.agent_type == "research"


def test_planner_agent_class() -> None:
    agent = PlannerAgent()
    assert agent.agent_type == "planner"


def test_writer_agent_class() -> None:
    agent = WriterAgent()
    assert agent.agent_type == "writer"


def test_seo_agent_class() -> None:
    agent = SEOAgent()
    assert agent.agent_type == "seo"


def test_fact_checker_agent_class() -> None:
    agent = FactCheckerAgent()
    assert agent.agent_type == "fact_checker"


def test_compliance_agent_class() -> None:
    agent = ComplianceAgent()
    assert agent.agent_type == "compliance"


def test_finalizer_agent_class() -> None:
    agent = FinalizerAgent()
    assert agent.agent_type == "finalizer"


def test_extract_research_data_empty() -> None:
    result = extract_research_data({})
    assert result["summary"] == "Research completed."
    assert result["key_points"] == []
    assert result["statistics"] == []


def test_extract_research_data_full() -> None:
    data = {
        "summary": "AI research complete",
        "key_points": ["AI is evolving", "ML is key"],
        "statistics": ["75% adoption"],
        "citations": ["Source 2024"],
        "entities": ["OpenAI"],
        "risks": ["Bias"],
        "outline_suggestions": ["Start with basics"],
        "gaps": ["No data on X"],
        "contradictions": ["Conflicting study"],
    }
    result = extract_research_data(data)
    assert result["summary"] == "AI research complete"
    assert len(result["key_points"]) == 2
    assert len(result["statistics"]) == 1


def test_extract_plan() -> None:
    data = {
        "title": "AI Guide",
        "sections": [{"title": "Intro", "key_points": ["What is AI"]}],
        "goals": "Educate",
        "target_audience": "Beginners",
        "key_themes": ["Machine Learning"],
        "research_questions": ["How does AI work?"],
        "success_criteria": ["1000 words"],
        "estimated_word_count": 1500,
    }
    result = extract_plan(data)
    assert result["title"] == "AI Guide"
    assert len(result["sections"]) == 1


def test_extract_writer_output() -> None:
    data = {
        "content": "# Article\n\nContent here.",
        "title": "Test Article",
        "word_count": 500,
        "sections_written": ["Intro"],
        "citations_used": ["Source 1"],
    }
    content, metadata = extract_writer_output(data)
    assert content == "# Article\n\nContent here."
    assert metadata["title"] == "Test Article"
    assert metadata["word_count"] == 500


def test_extract_writer_output_fallback() -> None:
    data = {"title": "Test"}
    content, metadata = extract_writer_output(data)
    assert content == ""
    assert metadata["word_count"] == 0


def test_extract_seo_output() -> None:
    data = {
        "content": "# Optimized\n\nSEO content.",
        "title": "SEO Title",
        "meta_description": "Best guide",
        "url_slug": "ai-guide",
        "primary_keywords": ["AI", "ML"],
        "readability_score": 85,
    }
    content, metadata = extract_seo_output(data)
    assert content == "# Optimized\n\nSEO content."
    assert "AI" in metadata["primary_keywords"]
    assert metadata["readability_score"] == 85


def test_extract_fact_check_output() -> None:
    data = {
        "content": "# Verified\n\nCorrected content.",
        "verified_claims": ["Claim 1"],
        "unverified_claims": [],
        "overall_assessment": "Mostly accurate",
        "confidence_score": 0.9,
    }
    content, metadata = extract_fact_check_output(data)
    assert content == "# Verified\n\nCorrected content."
    assert metadata["confidence_score"] == 0.9


def test_extract_compliance_output() -> None:
    data = {
        "content": "# Compliant\n\nSafe content.",
        "compliance_status": "pass",
        "issues": [],
        "brand_safety_score": 95,
        "overall_verdict": "Approved",
    }
    content, metadata = extract_compliance_output(data)
    assert content == "# Compliant\n\nSafe content."
    assert metadata["compliance_status"] == "pass"


def test_extract_finalizer_output() -> None:
    data = {
        "final_content": "# Final\n\nPublished content.",
        "title": "Final Article",
        "excerpt": "Short summary",
        "word_count": 1000,
        "reading_time_minutes": 5,
        "metadata": {"author": "AI"},
        "citations_list": [],
        "change_log": ["Fixed typos"],
    }
    result = extract_finalizer_output(data)
    assert result["final_content"] == "# Final\n\nPublished content."
    assert result["word_count"] == 1000


def test_pipeline_agent_parse_json() -> None:
    agent = PipelineAgent("test")
    result = agent._parse_response('{"key": "value"}')
    assert result == {"key": "value"}


def test_pipeline_agent_parse_json_block() -> None:
    agent = PipelineAgent("test")
    result = agent._parse_response('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_pipeline_agent_parse_invalid() -> None:
    agent = PipelineAgent("test")
    result = agent._parse_response("not json")
    assert "raw_content" in result
    assert "parse_error" in result


@pytest.mark.asyncio
async def test_pipeline_agent_execute_with_mock_provider(sample_state) -> None:
    agent = PipelineAgent("research")

    with (
        patch.object(agent, "_provider_factory") as mock_factory,
        patch("app.pipeline.agents.base.provider_router") as mock_router,
    ):
        mock_router.route = AsyncMock(return_value=RoutingDecision(
            provider="mock", model="mock-model",
            estimated_input_tokens=100, estimated_output_tokens=100,
            routing_reason="test", fallback_provider="mock",
            fallback_model="mock-model", execution_priority=1,
        ))
        mock_provider = AsyncMock()
        mock_response = AsyncMock()
        mock_response.success = True
        mock_response.content = '{"summary": "Research complete", "key_points": ["Point 1"]}'
        mock_response.error = None
        mock_response.token_usage = None
        mock_provider.execute_with_retry.return_value = mock_response
        mock_factory.get_or_create.return_value = mock_provider

        result = await agent.execute(sample_state)

        assert result.status == NodeStatus.SUCCESS
        assert "summary" in result.output
        assert result.output["summary"] == "Research complete"

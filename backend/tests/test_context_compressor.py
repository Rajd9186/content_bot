from __future__ import annotations

from app.pipeline.context_compressor import (
    PROVIDER_TOKEN_LIMITS,
    ContextCompressor,
    PromptSizer,
    TokenBudgetManager,
)
from app.pipeline.output_validator import (
    AgentOutputValidator,
    ContentQualityValidator,
    ValidationResult,
)


class TestTokenBudgetManager:
    def test_calculate_budget_groq(self) -> None:
        manager = TokenBudgetManager()
        budget = manager.calculate_budget("research", "groq", "Short system prompt")
        assert budget > 0
        assert budget < PROVIDER_TOKEN_LIMITS["groq"]

    def test_calculate_budget_openai(self) -> None:
        manager = TokenBudgetManager()
        budget = manager.calculate_budget("research", "openai", "Short prompt")
        assert budget > 0
        assert budget > PROVIDER_TOKEN_LIMITS["groq"]

    def test_calculate_budget_unknown_provider(self) -> None:
        manager = TokenBudgetManager()
        budget = manager.calculate_budget("research", "unknown", "Short prompt")
        assert budget > 0

    def test_calculate_budget_with_long_system_prompt(self) -> None:
        manager = TokenBudgetManager()
        long_prompt = "x" * 10000
        budget = manager.calculate_budget("research", "groq", long_prompt)
        assert budget > 0

    def test_record_compression(self) -> None:
        manager = TokenBudgetManager()
        manager.record_compression("research", 5000, 2000)
        stats = manager.compression_stats
        assert "research" in stats
        assert stats["research"]["original_tokens"] == 5000
        assert stats["research"]["compressed_tokens"] == 2000
        assert stats["research"]["ratio"] == 0.4

    def test_record_compression_zero_original(self) -> None:
        manager = TokenBudgetManager()
        manager.record_compression("research", 0, 0)
        stats = manager.compression_stats
        assert stats["research"]["ratio"] == 0


class TestContextCompressor:
    def test_research_agent_gets_core_context(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI in Healthcare",
            "audience": "doctors",
            "tone": "professional",
            "goals": "Inform about AI trends",
            "research_data": {"summary": "Big research summary"},
            "plan": {"sections": ["intro", "body"]},
            "draft_content": "Long draft content here",
        }
        result = compressor.compress_for_agent("research", state, provider="groq")
        assert "topic" in result
        assert "audience" in result
        assert "research_data" not in result

    def test_planner_agent_gets_research(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "research_data": {
                "summary": "Research summary",
                "key_points": ["Point 1", "Point 2"],
                "statistics": ["Stat 1"],
            },
        }
        result = compressor.compress_for_agent("planner", state, provider="groq")
        assert "research_summary" in result
        assert "key_points" in result

    def test_writer_agent_gets_plan_and_research(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "research_data": {
                "summary": "Summary",
                "key_points": ["K1"],
                "statistics": ["S1"],
            },
            "plan": {"sections": [{"title": "Intro"}]},
            "outline": {"sections": [{"title": "Body"}]},
            "draft_content": "Existing draft",
        }
        result = compressor.compress_for_agent("writer", state, provider="groq")
        assert "plan_sections" in result
        assert "outline_sections" in result

    def test_seo_agent_gets_truncated_draft(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "draft_content": "x" * 10000,
        }
        result = compressor.compress_for_agent("seo", state, provider="groq")
        assert "draft_content" in result
        assert len(result["draft_content"]) <= 3000

    def test_fact_checker_agent_gets_research_context(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "draft_content": "Draft content",
            "research_data": {
                "summary": "Summary",
                "citations": ["Citation 1"],
            },
        }
        result = compressor.compress_for_agent("fact_checker", state, provider="groq")
        assert "research_summary" in result
        assert "citations" in result

    def test_compliance_agent_minimal_context(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "draft_content": "Content",
        }
        result = compressor.compress_for_agent("compliance", state, provider="groq")
        assert "topic" in result
        assert "draft_content" in result

    def test_finalizer_agent_gets_all_results(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "draft_content": "Draft",
            "seo_metadata": {"keywords": ["ai"]},
            "fact_check_results": {"verified": 5},
            "compliance_results": {"status": "ok"},
        }
        result = compressor.compress_for_agent("finalizer", state, provider="groq")
        assert "seo_metadata" in result
        assert "fact_check_results" in result
        assert "compliance_results" in result

    def test_unknown_agent_gets_core(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
        }
        result = compressor.compress_for_agent("unknown_agent", state, provider="groq")
        assert "topic" in result

    def test_compression_under_budget(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        small_state = {"topic": "AI", "audience": "general", "tone": "pro", "goals": ""}
        result = compressor.compress_for_agent("research", small_state, provider="openai")
        assert "topic" in result

    def test_compression_records_stats(self) -> None:
        manager = TokenBudgetManager()
        compressor = ContextCompressor(manager)
        state = {
            "topic": "AI",
            "audience": "general",
            "tone": "professional",
            "goals": "",
            "research_data": {"summary": "Summary"},
        }
        compressor.compress_for_agent("research", state, provider="groq")
        assert "research" in manager.compression_stats


class TestPromptSizer:
    def test_estimate_tokens(self) -> None:
        sizer = PromptSizer()
        tokens = sizer.estimate_tokens("Hello world")
        assert tokens > 0

    def test_estimate_tokens_empty(self) -> None:
        sizer = PromptSizer()
        tokens = sizer.estimate_tokens("")
        assert tokens == 1

    def test_estimate_state_tokens(self) -> None:
        sizer = PromptSizer()
        tokens = sizer.estimate_state_tokens({"key": "value"})
        assert tokens > 0

    def test_fits_budget_true(self) -> None:
        sizer = PromptSizer()
        fits = sizer.fits_budget("Short system", "Short user", "openai")
        assert fits is True

    def test_fits_budget_false_groq(self) -> None:
        sizer = PromptSizer()
        huge_prompt = "x" * 100000
        fits = sizer.fits_budget(huge_prompt, huge_prompt, "groq")
        assert fits is False


class TestAgentOutputValidator:
    def test_empty_output_fails(self) -> None:
        validator = AgentOutputValidator()
        result = validator.validate("research", {})
        assert not result
        assert len(result.errors) > 0

    def test_valid_research_output(self) -> None:
        validator = AgentOutputValidator()
        output = {
            "summary": "This is a comprehensive research summary about AI in healthcare.",
            "key_points": ["AI transforms diagnostics", "ML improves outcomes"],
            "citations": ["https://example.com/study1"],
        }
        result = validator.validate("research", output)
        assert result

    def test_research_missing_summary(self) -> None:
        validator = AgentOutputValidator()
        output = {"key_points": ["Point 1"], "citations": ["Citation"]}
        result = validator.validate("research", output)
        assert not result
        assert any("Summary" in e for e in result.errors)

    def test_research_short_summary(self) -> None:
        validator = AgentOutputValidator()
        output = {"summary": "Short", "citations": ["Citation"]}
        result = validator.validate("research", output)
        assert not result

    def test_valid_planner_output(self) -> None:
        validator = AgentOutputValidator()
        output = {
            "title": "AI in Healthcare Guide",
            "sections": [
                {"title": "Introduction"},
                {"title": "Current Applications"},
            ],
            "goals": "Inform readers",
        }
        result = validator.validate("planner", output)
        assert result

    def test_planner_missing_title(self) -> None:
        validator = AgentOutputValidator()
        output = {
            "sections": [{"title": "Intro"}, {"title": "Body"}],
            "goals": "Inform",
        }
        result = validator.validate("planner", output)
        assert not result

    def test_planner_too_few_sections(self) -> None:
        validator = AgentOutputValidator()
        output = {
            "title": "AI Guide",
            "sections": [{"title": "Only one section"}],
        }
        result = validator.validate("planner", output)
        assert not result

    def test_valid_writer_output(self) -> None:
        validator = AgentOutputValidator()
        content = " ".join(["word"] * 150)
        output = {"content": content, "title": "AI in Healthcare"}
        result = validator.validate("writer", output)
        assert result

    def test_writer_no_content(self) -> None:
        validator = AgentOutputValidator()
        output = {"title": "AI in Healthcare"}
        result = validator.validate("writer", output)
        assert not result

    def test_writer_short_content_warning(self) -> None:
        validator = AgentOutputValidator()
        output = {"content": "Too short", "title": "AI Guide"}
        result = validator.validate("writer", output)
        assert len(result.warnings) > 0

    def test_valid_finalizer_output(self) -> None:
        validator = AgentOutputValidator()
        content = " ".join(["word"] * 150)
        output = {"final_content": content, "title": "Final"}
        result = validator.validate("finalizer", output)
        assert result

    def test_finalizer_no_content(self) -> None:
        validator = AgentOutputValidator()
        output = {"title": "Final"}
        result = validator.validate("finalizer", output)
        assert not result

    def test_placeholder_detection_in_content(self) -> None:
        validator = AgentOutputValidator()
        content = " ".join(["word"] * 150) + " TODO: add more content"
        output = {"content": content, "title": "Draft"}
        result = validator.validate("writer", output)
        assert any("Placeholder" in w for w in result.warnings)

    def test_lorem_ipsum_detection(self) -> None:
        validator = AgentOutputValidator()
        content = " ".join(["word"] * 150) + " LOREM IPSUM dolor sit amet"
        output = {"content": content, "title": "Draft"}
        result = validator.validate("writer", output)
        assert any("Placeholder" in w for w in result.warnings)

    def test_seo_warnings(self) -> None:
        validator = AgentOutputValidator()
        output = {"meta_description": "A description"}
        result = validator.validate("seo", output)
        assert len(result.warnings) > 0

    def test_fact_checker_warnings(self) -> None:
        validator = AgentOutputValidator()
        output = {"overall_assessment": "Needs review"}
        result = validator.validate("fact_checker", output)
        assert len(result.warnings) > 0

    def test_compliance_warnings(self) -> None:
        validator = AgentOutputValidator()
        output = {"overall_verdict": "Pass"}
        result = validator.validate("compliance", output)
        assert len(result.warnings) > 0

    def test_unknown_agent_passes(self) -> None:
        validator = AgentOutputValidator()
        output = {"some_key": "some_value"}
        result = validator.validate("unknown_agent", output)
        assert result


class TestContentQualityValidator:
    def test_empty_content_fails(self) -> None:
        validator = ContentQualityValidator()
        result = validator.validate("", "Title")
        assert not result

    def test_no_title_fails(self) -> None:
        validator = ContentQualityValidator()
        content = " ".join(["word"] * 200)
        result = validator.validate(content, "")
        assert not result

    def test_valid_content_passes(self) -> None:
        validator = ContentQualityValidator()
        content = " ".join(["word"] * 200)
        result = validator.validate(content, "AI in Healthcare")
        assert result

    def test_short_content_fails(self) -> None:
        validator = ContentQualityValidator()
        result = validator.validate("Too short", "Title")
        assert not result

    def test_placeholder_content_fails(self) -> None:
        validator = ContentQualityValidator()
        content = " ".join(["word"] * 150) + " TODO: fill this in"
        result = validator.validate(content, "Title")
        assert not result

    def test_fake_citation_warning(self) -> None:
        validator = ContentQualityValidator()
        content = " ".join(["word"] * 150) + " [1] https://example.com/fake-source"
        result = validator.validate(content, "Title")
        assert any("fake citation" in w.lower() or "Fake" in w for w in result.warnings)


class TestValidationResult:
    def test_default_valid(self) -> None:
        result = ValidationResult()
        assert result
        assert result.valid is True

    def test_add_error(self) -> None:
        result = ValidationResult()
        result.add_error("Test error")
        assert not result
        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_warning(self) -> None:
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result
        assert "Test warning" in result.warnings

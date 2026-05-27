"""Tests for the new typed architecture: validation, state machine, retry engine, event bus, telemetry."""

import json
import uuid
import pytest
import asyncio
from datetime import datetime


# ── Validation Tests ──────────────────────────────────────────────────────────


class TestValidation:
    def test_validate_draft_valid(self):
        from app.validation import validate_draft
        paragraph = "This is a substantive paragraph with meaningful content about the topic at hand. It provides detailed analysis of key concepts and their implications for the broader field. " * 60
        markdown = f"# Test Article\n\n{paragraph}\n\n## Section 1\n\n{paragraph}\n\n## Section 2\n\n{paragraph}"
        citations = [{"id": 1, "text": "Claim", "source_url": "https://reuters.com/article"}]
        report = validate_draft(markdown, title="Test Article", citations=citations, headings_used=["Section 1", "Section 2"])
        assert report.is_valid
        assert report.word_count > 10
        assert report.citation_count == 1

    def test_validate_draft_empty(self):
        from app.validation import validate_draft
        report = validate_draft("", title="")
        assert not report.is_valid
        assert len(report.errors) >= 1

    def test_validate_draft_untitled(self):
        from app.validation import validate_draft
        markdown = "# Untitled\n\nSome content here."
        report = validate_draft(markdown, title="Untitled")
        assert not report.is_valid
        assert any("title" in e for e in report.errors)

    def test_validate_draft_placeholder(self):
        from app.validation import validate_draft
        markdown = "# Article\n\nLorem ipsum dolor sit amet."
        report = validate_draft(markdown, title="Article")
        assert not report.is_valid
        assert any("placeholder" in e for e in report.errors)

    def test_validate_draft_short(self):
        from app.validation import validate_draft
        markdown = "# Hi\n\nToo short."
        report = validate_draft(markdown, title="Hi", min_word_count=300)
        assert not report.is_valid
        assert any("word count" in e for e in report.errors)

    def test_validate_draft_missing_sections(self):
        from app.validation import validate_draft
        markdown = "# Article\n\nSome content."
        outline_sections = [
            {"heading": "Introduction"},
            {"heading": "Methodology"},
            {"heading": "Conclusion"},
        ]
        report = validate_draft(markdown, title="Article", headings_used=["Introduction"], outline_sections=outline_sections)
        assert any("methodology" in m.lower() for m in report.missing_sections)
        assert any("conclusion" in m.lower() for m in report.missing_sections)

    def test_validate_markdown_structure(self):
        from app.validation import validate_markdown_structure
        content = "# H1\n\n## H2\n\nThis is a longer paragraph with meaningful content to exceed the minimum length threshold for validation purposes. " * 5
        report = validate_markdown_structure(content)
        assert report.heading_count >= 2
        assert report.is_valid

    def test_validate_markdown_no_h1(self):
        from app.validation import validate_markdown_structure
        report = validate_markdown_structure("## H2 only\n\nNo H1 heading.")
        assert not report.is_valid or any("H1" in w for w in report.warnings)

    def test_validate_citations_missing_url(self):
        from app.validation import validate_citations
        citations = [{"id": 1, "text": "Claim", "source_url": ""}]
        report = validate_citations(citations)
        assert any("missing source_url" in w for w in report.warnings)

    def test_validate_citations_insufficient(self):
        from app.validation import validate_citations
        citations = []
        report = validate_citations(citations, min_required=1)
        assert any("only 0 citations" in w for w in report.warnings)

    def test_quality_scores(self):
        from app.validation import validate_draft
        citations = [{"id": i, "text": f"Claim {i}", "source_url": f"https://source{i}.com"} for i in range(1, 10)]
        report = validate_draft("# Valid Article\n\nContent " * 100, title="Valid Article", citations=citations)
        assert report.quality_score >= 0.5
        assert report.hallucination_risk <= 0.5
        assert report.completeness_score >= 0.5


# ── State Machine Tests ───────────────────────────────────────────────────────


class TestStateMachine:
    def test_valid_transitions(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition, can_transition,
        )
        validate_transition(WorkflowStage.INIT, WorkflowStage.PLANNING)
        validate_transition(WorkflowStage.PLANNING, WorkflowStage.RESEARCH)
        validate_transition(WorkflowStage.RESEARCH, WorkflowStage.SYNTHESIS)
        validate_transition(WorkflowStage.SYNTHESIS, WorkflowStage.OUTLINING)
        validate_transition(WorkflowStage.OUTLINING, WorkflowStage.WRITING)
        validate_transition(WorkflowStage.WRITING, WorkflowStage.VALIDATION)
        validate_transition(WorkflowStage.VALIDATION, WorkflowStage.SEO)
        validate_transition(WorkflowStage.SEO, WorkflowStage.FACT_CHECK)
        validate_transition(WorkflowStage.FACT_CHECK, WorkflowStage.FINALIZATION)
        validate_transition(WorkflowStage.FINALIZATION, WorkflowStage.PUBLISHED)
        assert can_transition(WorkflowStage.INIT, WorkflowStage.PLANNING)
        assert not can_transition(WorkflowStage.INIT, WorkflowStage.PUBLISHED)

    def test_illegal_transition(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition, IllegalTransitionError,
        )
        with pytest.raises(IllegalTransitionError):
            validate_transition(WorkflowStage.INIT, WorkflowStage.PUBLISHED)

    def test_failed_transition_allows_restart(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition,
        )
        validate_transition(WorkflowStage.FAILED, WorkflowStage.INIT)

    def test_is_terminal(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, is_terminal,
        )
        assert is_terminal(WorkflowStage.PUBLISHED)
        assert is_terminal(WorkflowStage.FAILED)
        assert not is_terminal(WorkflowStage.INIT)
        assert not is_terminal(WorkflowStage.WRITING)

    def test_stage_display_name(self):
        from app.orchestration.state_machine.workflow_stage import stage_display_name, WorkflowStage
        assert stage_display_name(WorkflowStage.FACT_CHECK) == "Fact Check"
        assert stage_display_name(WorkflowStage.WRITING) == "Writing"


# ── Retry Engine Tests ────────────────────────────────────────────────────────


class TestRetryEngine:
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        async def succeed():
            return "success"

        result = await execute_with_retry(succeed, config=RetryConfig(max_retries=2))
        assert result.success
        assert result.result == "success"
        assert len(result.attempts) == 1

    @pytest.mark.asyncio
    async def test_retry_eventually_succeeds(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        call_count = 0

        async def eventually_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "recovered"

        result = await execute_with_retry(
            eventually_succeed,
            config=RetryConfig(max_retries=3, base_delay=0.01, backoff_factor=1.0, jitter=False),
        )
        assert result.success
        assert result.result == "recovered"
        assert len(result.attempts) == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        async def always_fail():
            raise RuntimeError("persistent error")

        result = await execute_with_retry(
            always_fail,
            config=RetryConfig(max_retries=2, base_delay=0.01, backoff_factor=1.0, jitter=False),
        )
        assert not result.success
        assert "persistent error" in (result.error or "")
        assert len(result.attempts) == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_zero_retries(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        async def always_fail():
            raise ValueError("fail")

        result = await execute_with_retry(
            always_fail,
            config=RetryConfig(max_retries=0, base_delay=0.01),
        )
        assert not result.success
        assert len(result.attempts) == 1


# ── Event Bus Tests ────────────────────────────────────────────────────────────


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_and_replay(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        e1 = WorkflowEvent(workflow_id=wf_id, event_type="started", message="First")
        e2 = WorkflowEvent(workflow_id=wf_id, event_type="progress", message="Second")
        await bus.publish(e1)
        await bus.publish(e2)

        events = bus.get_events(wf_id)
        assert len(events) == 2
        assert events[0].message == "First"
        assert events[1].message == "Second"

    @pytest.mark.asyncio
    async def test_replay_after_event_id(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        events_sent = []
        for i in range(5):
            e = WorkflowEvent(workflow_id=wf_id, event_type=f"e{i}", message=f"Event {i}")
            await bus.publish(e)
            events_sent.append(e)

        after_id = events_sent[2].event_id
        replay = bus.get_events(wf_id, after_event_id=after_id)
        assert len(replay) == 2
        assert replay[0].message == "Event 3"
        assert replay[1].message == "Event 4"

    @pytest.mark.asyncio
    async def test_subscribe_receives_events(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        queue = bus.subscribe(wf_id)

        e = WorkflowEvent(workflow_id=wf_id, event_type="test", message="Hello")
        await bus.publish(e)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.message == "Hello"
        assert received.event_type == "test"

    @pytest.mark.asyncio
    async def test_subscribe_receives_past_events(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        e = WorkflowEvent(workflow_id=wf_id, event_type="past", message="Before subscribe")
        await bus.publish(e)

        queue = bus.subscribe(wf_id)
        past_event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert past_event.message == "Before subscribe"

    def test_publish_event_helper(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()

        async def test():
            event = await bus.publish_event(
                workflow_id="wf-1",
                event_type="agent_started",
                agent_name="writer",
                status="running",
                message="Generating",
                progress_percent=50.0,
            )
            assert event.workflow_id == "wf-1"
            assert event.event_type == "agent_started"
            assert event.agent_name == "writer"
            assert event.progress_percent == 50.0
            assert len(event.event_id) > 0

        asyncio.run(test())


# ── Telemetry Tests ────────────────────────────────────────────────────────────


class TestTelemetry:
    def test_create_and_record(self):
        from app.telemetry.metrics import TelemetryCollector

        tc = TelemetryCollector()
        wf = tc.create("wf-1", "proj-1")
        assert wf.workflow_id == "wf-1"
        assert wf.project_id == "proj-1"

        tc.add_stage("wf-1", "PLANNING", "planner", duration_ms=500.0, tokens=100)
        tc.add_stage("wf-1", "WRITING", "writer", duration_ms=2000.0, tokens=500, retries=2, validation_score=0.85)

        t = tc.get_telemetry("wf-1")
        assert t is not None
        assert len(t.stages) == 2
        assert t.total_duration_ms == 2500.0
        assert t.total_tokens == 600
        assert t.total_retries == 2

    def test_final_quality(self):
        from app.telemetry.metrics import TelemetryCollector

        tc = TelemetryCollector()
        tc.create("wf-2", "proj-2")
        tc.set_final_quality("wf-2", 0.92)
        t = tc.get_telemetry("wf-2")
        assert t.final_quality_score == 0.92

    def test_set_completed(self):
        from app.telemetry.metrics import TelemetryCollector

        tc = TelemetryCollector()
        tc.create("wf-3", "proj-3")
        tc.set_completed("wf-3", error="")
        t = tc.get_telemetry("wf-3")
        assert t.completed
        assert t.error == ""

    def test_telemetry_to_dict(self):
        from app.telemetry.metrics import TelemetryCollector

        tc = TelemetryCollector()
        tc.create("wf-4", "proj-4")
        tc.add_stage("wf-4", "RESEARCH", "research", duration_ms=1000.0, tokens=200)
        tc.set_final_quality("wf-4", 0.88)
        tc.set_completed("wf-4")

        d = tc.get_telemetry("wf-4").to_dict()
        assert d["workflow_id"] == "wf-4"
        assert d["total_duration_ms"] == 1000.0
        assert d["final_quality_score"] == 0.88
        assert d["completed"] is True
        assert len(d["stages"]) == 1


# ── Typed Schema Tests ─────────────────────────────────────────────────────────


class TestTypedSchemas:
    def test_planner_input(self):
        from app.schemas.agent_inputs.planner import PlannerInput
        inp = PlannerInput(topic="AI in Healthcare", tone="professional")
        assert inp.topic == "AI in Healthcare"
        assert inp.content_type == "article"
        assert inp.tone == "professional"

    def test_writer_input(self):
        from app.schemas.agent_inputs.writer import WriterInput
        from app.schemas.research_packet import ResearchPacket
        rp = ResearchPacket(executive_summary="Key findings here.")
        inp = WriterInput(
            title="Test Article",
            outline={"sections": [{"heading": "Intro"}]},
            research_packet=rp,
            verified_claims=[{"id": "1", "claim_text": "Claim", "confidence": 0.9}],
        )
        assert inp.title == "Test Article"
        assert len(inp.verified_claims) == 1
        assert inp.research_packet.executive_summary == "Key findings here."

    def test_writer_output(self):
        from app.schemas.agent_outputs.writer import WriterOutput
        out = WriterOutput(
            markdown="# Test\n\nContent.",
            word_count=3,
            citations=[{"id": 1, "text": "C", "source_url": "https://x.com"}],
            is_valid=True,
            quality_score=0.95,
        )
        assert out.markdown
        assert out.is_valid
        assert out.quality_score == 0.95
        assert out.word_count == 3

    def test_research_packet_empty(self):
        from app.schemas.research_packet import ResearchPacket
        rp = ResearchPacket.empty()
        assert rp.executive_summary == "No research sources available."
        assert rp.statistics["total_sources"] == 0

    def test_research_packet_full(self):
        from app.schemas.research_packet import ResearchPacket, SourceSummary
        ss = SourceSummary(url="https://example.com", domain="example.com", title="Example")
        rp = ResearchPacket(
            topic="AI",
            executive_summary="Summary",
            key_findings=["Finding 1"],
            source_summaries=[ss],
            statistics={"total_sources": 5},
        )
        assert rp.topic == "AI"
        assert len(rp.source_summaries) == 1
        assert rp.source_summaries[0].domain == "example.com"

    def test_planner_output(self):
        from app.schemas.agent_outputs.planner import PlannerOutput
        out = PlannerOutput(
            sections=[{"heading": "Intro"}],
            research_tasks=["query 1"],
        )
        assert len(out.sections) == 1
        assert len(out.research_tasks) == 1

    def test_research_output(self):
        from app.schemas.agent_outputs.research import ResearchOutput
        from app.schemas.research_packet import ResearchPacket
        out = ResearchOutput(
            research_packet=ResearchPacket(executive_summary="Results"),
            total_sources_found=10,
        )
        assert out.research_packet.executive_summary == "Results"
        assert out.total_sources_found == 10

    def test_validator_output(self):
        from app.schemas.agent_outputs.validator import ValidatorOutput
        out = ValidatorOutput(
            is_valid=True,
            word_count=500,
            citation_count=3,
            quality_score=0.9,
        )
        assert out.is_valid
        assert out.word_count == 500

    def test_writer_input_serialization(self):
        from app.schemas.agent_inputs.writer import WriterInput
        inp = WriterInput(title="Test", tone="conversational", seo_keywords=["ai", "health"])
        data = inp.model_dump()
        assert data["title"] == "Test"
        assert data["tone"] == "conversational"
        assert data["seo_keywords"] == ["ai", "health"]

    def test_agent_metrics(self):
        from app.agents.base import AgentMetrics
        m = AgentMetrics(
            agent_name="WriterAgent",
            duration_ms=1500.0,
            total_tokens=500,
            retry_count=2,
            validation_score=0.85,
        )
        assert m.agent_name == "WriterAgent"
        assert m.total_tokens == 500
        assert m.retry_count == 2


# ── Workflow Engine Tests ──────────────────────────────────────────────────────


class TestWorkflowEngine:
    def test_create_workflow(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-1")
        assert state.project_id == "proj-1"
        assert state.current_stage.value == "INIT"
        assert len(state.workflow_id) > 0

    def test_get_state(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-2")
        retrieved = engine.get_state(state.workflow_id)
        assert retrieved is not None
        assert retrieved.workflow_id == state.workflow_id

    def test_get_state_not_found(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        engine = WorkflowEngine()
        assert engine.get_state("nonexistent") is None

    def test_transition_to(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage, StageStatus
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-3")
        engine.transition_to(state.workflow_id, WorkflowStage.PLANNING, StageStatus.STARTED)
        updated = engine.get_state(state.workflow_id)
        assert updated.current_stage == WorkflowStage.PLANNING

    def test_full_workflow_path(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage, StageStatus
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-4")

        transitions = [
            (WorkflowStage.PLANNING, StageStatus.COMPLETED),
            (WorkflowStage.RESEARCH, StageStatus.COMPLETED),
            (WorkflowStage.SYNTHESIS, StageStatus.COMPLETED),
            (WorkflowStage.OUTLINING, StageStatus.COMPLETED),
            (WorkflowStage.WRITING, StageStatus.COMPLETED),
            (WorkflowStage.VALIDATION, StageStatus.COMPLETED),
            (WorkflowStage.SEO, StageStatus.COMPLETED),
            (WorkflowStage.FACT_CHECK, StageStatus.COMPLETED),
            (WorkflowStage.FINALIZATION, StageStatus.COMPLETED),
            (WorkflowStage.PUBLISHED, StageStatus.COMPLETED),
        ]

        for stage, status in transitions:
            engine.transition_to(state.workflow_id, stage, status)

        final = engine.get_state(state.workflow_id)
        assert final.current_stage == WorkflowStage.PUBLISHED
        assert final.is_complete

    def test_transitions_logged(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage, StageStatus
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-5")
        engine.transition_to(state.workflow_id, WorkflowStage.PLANNING, StageStatus.STARTED)
        transitions = engine.get_transitions(state.workflow_id)
        assert len(transitions) == 2
        assert transitions[0].stage == WorkflowStage.INIT
        assert transitions[1].stage == WorkflowStage.PLANNING

    def test_retry_increment(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-6")
        count = engine.increment_retry(state.workflow_id, WorkflowStage.WRITING)
        assert count == 1
        count = engine.increment_retry(state.workflow_id, WorkflowStage.WRITING)
        assert count == 2
        assert state.retry_counts["WRITING"] == 2

    def test_stage_duration(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-7")
        engine.mark_stage_duration(state.workflow_id, WorkflowStage.PLANNING, 500.0)
        assert state.stage_durations["PLANNING"] == 500.0

    def test_error_recording(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage, StageStatus
        engine = WorkflowEngine()
        state = engine.create_workflow("proj-8")
        engine.transition_to(state.workflow_id, WorkflowStage.FAILED, StageStatus.FAILED, error="Something broke")
        assert len(state.errors) == 1
        assert state.errors[0]["error"] == "Something broke"
        assert state.is_failed


# ── ResearchPacket Tests ───────────────────────────────────────────────────────


class TestResearchPacket:
    def test_source_summary(self):
        from app.schemas.research_packet import SourceSummary
        ss = SourceSummary(url="https://example.com/article", domain="example.com", title="Article", snippet="Content")
        assert ss.url == "https://example.com/article"
        assert ss.trust_score == 0.0

    def test_source_summary_with_trust(self):
        from app.schemas.research_packet import SourceSummary
        ss = SourceSummary(url="https://trusted.org", domain="trusted.org", title="Trusted", trust_score=0.95)
        assert ss.trust_score == 0.95

    def test_draft_validation_result(self):
        from app.schemas.research_packet import DraftValidationResult
        r = DraftValidationResult(is_valid=True, quality_score=0.9, completeness_score=0.85)
        assert r.is_valid
        assert r.quality_score == 0.9
        assert r.hallucination_risk == 0.0

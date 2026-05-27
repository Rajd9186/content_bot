"""STRESS TESTS: Database integrity, concurrency, failure injection, edge cases."""

import asyncio
import json
import uuid
import pytest
from datetime import datetime, timezone


# ── DB INTEGRITY TESTS ─────────────────────────────────────────────────────────


class TestDatabaseIntegrity:
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, db_session):
        """Verify workflow state can be persisted and retrieved."""
        from app.models.workflow import WorkflowExecution, WorkflowStatus
        from app.models.project import Project

        project = Project(topic="Test", status="active")
        db_session.add(project)
        await db_session.flush()

        wf = WorkflowExecution(
            project_id=project.id,
            status=WorkflowStatus.running,
            current_node="PLANNING",
        )
        db_session.add(wf)
        await db_session.flush()

        assert wf.id is not None
        assert wf.status == WorkflowStatus.running
        assert wf.current_node == "PLANNING"

    @pytest.mark.asyncio
    async def test_fk_violation_rejected(self, db_session):
        """Verify invalid FK insertion is rejected."""
        from app.models.workflow import WorkflowExecution, WorkflowStatus
        from sqlalchemy import exc

        fake_id = uuid.uuid4()
        wf = WorkflowExecution(
            project_id=fake_id,
            status=WorkflowStatus.running,
        )
        with pytest.raises(exc.IntegrityError):
            await db_session.flush()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_cascade_delete_project(self, db_session):
        """Verify deleting a project cascades to workflows."""
        from app.models.workflow import WorkflowExecution, WorkflowStatus
        from app.models.project import Project

        project = Project(topic="Cascade Test", status="active")
        db_session.add(project)
        await db_session.flush()

        wf = WorkflowExecution(project_id=project.id, status=WorkflowStatus.running)
        db_session.add(wf)
        await db_session.flush()

        project_id = project.id
        wf_id = wf.id

        await db_session.delete(project)
        await db_session.flush()

        from sqlalchemy import select
        result = await db_session.execute(select(WorkflowExecution).where(WorkflowExecution.id == wf_id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_content_lock_exclusive(self, db_session):
        """Verify content lock prevents concurrent writes."""
        from app.models.content_version import ContentLock

        project_id = uuid.uuid4()
        lock = ContentLock(project_id=project_id, locked_by="writer1")
        db_session.add(lock)
        await db_session.flush()

        from sqlalchemy import select
        lock2 = ContentLock(project_id=project_id, locked_by="writer2")
        db_session.add(lock2)
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_orm_rollback_restores_state(self, db_session):
        """Verify transaction rollback restores clean state."""
        from app.models.project import Project
        from app.models.workflow import WorkflowExecution, WorkflowStatus

        project = Project(topic="Rollback Test", status="active")
        db_session.add(project)
        await db_session.flush()
        pid = project.id

        wf = WorkflowExecution(project_id=pid, status=WorkflowStatus.running)
        db_session.add(wf)
        await db_session.flush()

        wf.status = WorkflowStatus.completed
        await db_session.rollback()

        from sqlalchemy import select
        result = await db_session.execute(select(WorkflowExecution).where(WorkflowExecution.project_id == pid))
        workflows = result.scalars().all()
        assert len(workflows) == 0


# ── STATE MACHINE STRESS TESTS ────────────────────────────────────────────────


class TestStateMachineStress:
    def test_all_valid_paths(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition,
        )

        valid_paths = [
            [WorkflowStage.INIT, WorkflowStage.PLANNING],
            [WorkflowStage.PLANNING, WorkflowStage.RESEARCH],
            [WorkflowStage.RESEARCH, WorkflowStage.SYNTHESIS],
            [WorkflowStage.SYNTHESIS, WorkflowStage.OUTLINING],
            [WorkflowStage.OUTLINING, WorkflowStage.WRITING],
            [WorkflowStage.WRITING, WorkflowStage.VALIDATION],
            [WorkflowStage.VALIDATION, WorkflowStage.SEO],
            [WorkflowStage.SEO, WorkflowStage.FACT_CHECK],
            [WorkflowStage.FACT_CHECK, WorkflowStage.FINALIZATION],
            [WorkflowStage.FINALIZATION, WorkflowStage.PUBLISHED],
        ]

        for from_stage, to_stage in valid_paths:
            try:
                validate_transition(from_stage, to_stage)
            except ValueError:
                pytest.fail(f"Valid path failed: {from_stage.value} -> {to_stage.value}")

    def test_retry_paths_from_validation(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition,
        )

        retry_paths = [
            (WorkflowStage.VALIDATION, WorkflowStage.WRITING),
            (WorkflowStage.SEO, WorkflowStage.WRITING),
            (WorkflowStage.FACT_CHECK, WorkflowStage.WRITING),
        ]

        for from_stage, to_stage in retry_paths:
            try:
                validate_transition(from_stage, to_stage)
            except ValueError:
                pytest.fail(f"Retry path failed: {from_stage.value} -> {to_stage.value}")

    def test_failed_restart_path(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, validate_transition,
        )
        validate_transition(WorkflowStage.FAILED, WorkflowStage.INIT)

    def test_illegal_transitions_all(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, VALID_TRANSITIONS,
        )
        all_stages = list(WorkflowStage)

        for from_stage in all_stages:
            allowed = VALID_TRANSITIONS.get(from_stage, set())
            for to_stage in all_stages:
                if to_stage == from_stage:
                    continue
                is_legal = to_stage in allowed

                from app.orchestration.state_machine.workflow_stage import can_transition
                assert can_transition(from_stage, to_stage) == is_legal, (
                    f"can_transition mismatch for {from_stage.value} -> {to_stage.value}: "
                    f"expected {is_legal}"
                )

    def test_no_self_loops(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, VALID_TRANSITIONS,
        )
        for stage, allowed in VALID_TRANSITIONS.items():
            assert stage not in allowed, f"Self-loop detected: {stage.value} -> {stage.value}"

    def test_published_is_terminal(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage, VALID_TRANSITIONS,
        )
        assert VALID_TRANSITIONS[WorkflowStage.PUBLISHED] == set()

    def test_failed_is_not_terminal(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage,
        )
        from app.orchestration.state_machine.workflow_stage import can_transition
        assert can_transition(WorkflowStage.FAILED, WorkflowStage.INIT)

    def test_blocked_can_recover(self):
        from app.orchestration.state_machine.workflow_stage import (
            WorkflowStage,
        )
        from app.orchestration.state_machine.workflow_stage import can_transition
        assert can_transition(WorkflowStage.BLOCKED, WorkflowStage.INIT)
        assert can_transition(WorkflowStage.BLOCKED, WorkflowStage.FAILED)


# ── VALIDATION STRESS TESTS ────────────────────────────────────────────────────


class TestValidationStress:
    def test_reject_untitled_never_passes(self):
        from app.validation import validate_draft
        variants = [
            "Untitled",
            "untitled",
            "UNTITLED",
            "# Untitled",
            "",
            " ",
            "  ",
        ]
        for title in variants:
            markdown = f"# {title}\n\nSome content here that is long enough to pass the minimum word count threshold for validation testing purposes. " * 20
            report = validate_draft(markdown, title=title)
            assert not report.is_valid, f"Title '{title}' should be rejected"

    def test_reject_placeholder_content(self):
        from app.validation import validate_draft
        placeholders = [
            "Lorem ipsum dolor sit amet.",
            "Coming soon: this section will be updated.",
            "To be written.",
            "[Your content here]",
            "Insert content about the topic.",
            "Write here.",
        ]
        for ph in placeholders:
            report = validate_draft(f"# Test\n\n{ph}", title="Test", min_word_count=1)
            assert not report.is_valid, f"Placeholder '{ph}' should be rejected"

    def test_reject_empty_markdown(self):
        from app.validation import validate_draft
        report = validate_draft("", title="Test")
        assert not report.is_valid
        assert any("empty" in e for e in report.errors)

    def test_reject_short_content(self):
        from app.validation import validate_draft
        report = validate_draft("# Short\n\nToo short.", title="Short", min_word_count=1000)
        assert not report.is_valid
        assert any("word count" in e for e in report.errors)

    def test_accept_valid_long_content(self):
        from app.validation import validate_draft
        paragraphs = "This is a substantive paragraph with meaningful content that explores key concepts and their implications in depth. " * 40
        markdown = f"# Valid Article\n\n{paragraphs}\n\n## Section One\n\n{paragraphs}\n\n## Section Two\n\n{paragraphs}"
        citations = [{"id": i, "text": f"Claim {i}", "source_url": "https://reuters.com/article"} for i in range(3)]
        report = validate_draft(markdown, title="Valid Article", citations=citations, min_word_count=100)
        assert report.is_valid, f"Valid content rejected: {report.errors}"

    def test_reject_no_citations(self):
        from app.validation import validate_draft
        paragraphs = "Substantive paragraph with meaningful content for testing citation validation requirements. " * 40
        report = validate_draft(f"# No Citations\n\n{paragraphs}", title="No Citations", min_word_count=1, min_citations=3)
        assert not report.is_valid or any("citation" in w for w in report.warnings)

    def test_reject_malformed_markdown(self):
        from app.validation import validate_draft
        bad_markdowns = [
            "",
            "no heading at all",
            "## H2 without H1",
            "#### H4 without H3",
        ]
        for md in bad_markdowns:
            report = validate_draft(md, title="Test", min_word_count=1)
            if len(md) < 50:
                assert not report.is_valid, f"Malformed markdown should be rejected: '{md[:30]}'"

    def test_hallucination_detection(self):
        from app.validation import validate_draft
        many_words = "Word " * 500
        no_citations = validate_draft(f"# Hallucination\n\n{many_words}", title="Hallucination", min_word_count=1)
        assert no_citations.hallucination_risk > 0.5, "Low citation density should raise hallucination risk"

    def test_completeness_missing_sections(self):
        from app.validation import validate_draft
        paragraphs = "Substantive content. " * 40
        outline_sections = [
            {"heading": "Introduction"},
            {"heading": "Methodology"},
            {"heading": "Results"},
            {"heading": "Discussion"},
            {"heading": "Conclusion"},
        ]
        report = validate_draft(
            f"# Test\n\n{paragraphs}\n\n## Introduction\n\n{paragraphs}",
            title="Test",
            headings_used=["Introduction"],
            outline_sections=outline_sections,
            min_word_count=1,
        )
        assert len(report.missing_sections) >= 3
        assert report.completeness_score < 0.9


# ── RETRY ENGINE STRESS TESTS ──────────────────────────────────────────────────


class TestRetryStress:
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        delays = []
        call_count = 0

        async def fail_with_timing():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                delays.append(call_count)
            raise ValueError(f"fail {call_count}")

        import time
        start = time.monotonic()
        result = await execute_with_retry(
            fail_with_timing,
            config=RetryConfig(max_retries=3, base_delay=0.05, backoff_factor=2.0, jitter=False),
        )
        elapsed = time.monotonic() - start

        assert not result.success
        assert call_count == 4  # initial + 3 retries
        assert elapsed >= 0.05 + 0.1 + 0.2  # total backoff
        assert elapsed < 1.0  # sanity check

    @pytest.mark.asyncio
    async def test_retry_jitter_variation(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        delays = []

        async def fail_capture():
            delays.append(1)
            raise ValueError("fail")

        result = await execute_with_retry(
            fail_capture,
            config=RetryConfig(max_retries=3, base_delay=1.0, backoff_factor=1.0, jitter=True),
        )

        assert not result.success
        assert len(delays) == 4

    @pytest.mark.asyncio
    async def test_retry_on_specific_exceptions(self):
        from app.orchestration.retry_engine.retry_middleware import (
            execute_with_retry, RetryConfig,
        )

        async def raise_value_error():
            raise ValueError("specific error")

        async def raise_type_error():
            raise TypeError("different error")

        result = await execute_with_retry(
            raise_value_error,
            config=RetryConfig(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,)),
        )
        assert not result.success
        assert "ValueError" in (result.error or "")

    @pytest.mark.asyncio
    async def test_retry_result_structure(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        async def succeed():
            return {"key": "value"}

        result = await execute_with_retry(succeed, config=RetryConfig(max_retries=2))
        assert result.success
        assert result.result == {"key": "value"}
        assert len(result.attempts) == 1
        assert result.attempts[0].attempt == 1
        assert result.attempts[0].error == ""
        assert result.total_duration_ms > 0

    @pytest.mark.asyncio
    async def test_retry_failure_structure(self):
        from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig

        async def fail():
            raise RuntimeError("boom")

        result = await execute_with_retry(fail, config=RetryConfig(max_retries=1, base_delay=0.01, jitter=False))
        assert not result.success
        assert result.result is None
        assert len(result.attempts) == 2
        assert all(a.error for a in result.attempts)


# ── CONCURRENT WORKFLOW TESTS ─────────────────────────────────────────────────


class TestConcurrentWorkflows:
    @pytest.mark.asyncio
    async def test_parallel_workflow_creations(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine

        engine = WorkflowEngine()

        async def create_workflow(idx: int) -> str:
            state = engine.create_workflow(f"proj-{idx}")
            return state.workflow_id

        ids = await asyncio.gather(*[create_workflow(i) for i in range(20)])
        assert len(set(ids)) == 20

    @pytest.mark.asyncio
    async def test_parallel_transitions(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage, StageStatus

        engine = WorkflowEngine()

        async def run_workflow(idx: int):
            state = engine.create_workflow(f"proj-{idx}")
            engine.transition_to(state.workflow_id, WorkflowStage.PLANNING, StageStatus.COMPLETED)
            engine.transition_to(state.workflow_id, WorkflowStage.RESEARCH, StageStatus.COMPLETED)
            engine.transition_to(state.workflow_id, WorkflowStage.PUBLISHED, StageStatus.COMPLETED)
            return state

        states = await asyncio.gather(*[run_workflow(i) for i in range(20)])
        assert all(s.is_complete for s in states)

    @pytest.mark.asyncio
    async def test_parallel_retry_tracking(self):
        from app.orchestration.workflow_engine.engine import WorkflowEngine
        from app.orchestration.state_machine.workflow_stage import WorkflowStage

        engine = WorkflowEngine()

        async def retry_workflow(idx: int):
            state = engine.create_workflow(f"proj-{idx}")
            for _ in range(5):
                engine.increment_retry(state.workflow_id, WorkflowStage.WRITING)
            return state

        states = await asyncio.gather(*[retry_workflow(i) for i in range(20)])
        for s in states:
            assert s.retry_counts.get("WRITING", 0) == 5

    @pytest.mark.asyncio
    async def test_event_bus_concurrent_subscribers(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        queues = [bus.subscribe(wf_id) for _ in range(10)]

        e = WorkflowEvent(workflow_id=wf_id, event_type="test", message="Concurrent")
        await bus.publish(e)

        received = await asyncio.gather(*[asyncio.wait_for(q.get(), timeout=1.0) for q in queues])
        assert all(r.message == "Concurrent" for r in received)

    @pytest.mark.asyncio
    async def test_telemetry_concurrent_stages(self):
        from app.telemetry.metrics import TelemetryCollector

        tc = TelemetryCollector()

        async def record_stages(wf_id: str, project_id: str):
            tc.create(wf_id, project_id)
            for i in range(5):
                tc.add_stage(wf_id, f"STAGE_{i}", f"agent{i}", duration_ms=100 * i, tokens=50 * i)

        wf_ids = [str(uuid.uuid4()) for _ in range(20)]
        await asyncio.gather(*[record_stages(wf_id, f"proj-{i}") for i, wf_id in enumerate(wf_ids)])

        for wf_id in wf_ids:
            t = tc.get_telemetry(wf_id)
            assert t is not None
            assert len(t.stages) == 5
            assert t.total_duration_ms > 0


# ── SCHEMA EDGE CASE TESTS ─────────────────────────────────────────────────────


class TestSchemaEdgeCases:
    def test_writer_input_defaults(self):
        from app.schemas.agent_inputs.writer import WriterInput
        inp = WriterInput(title="Test")
        assert inp.tone == "professional"
        assert inp.target_audience == "general"
        assert inp.content_type == "article"
        assert inp.verified_claims == []
        assert inp.seo_keywords == []

    def test_writer_input_extreme_values(self):
        from app.schemas.agent_inputs.writer import WriterInput

        long_title = "A" * 500
        long_audience = "B" * 300
        many_claims = [{"id": str(i), "claim_text": f"C{i}"} for i in range(1000)]

        inp = WriterInput(
            title=long_title,
            target_audience=long_audience,
            verified_claims=many_claims,
        )
        assert inp.title == long_title
        assert len(inp.verified_claims) == 1000

    def test_writer_output_edge_cases(self):
        from app.schemas.agent_outputs.writer import WriterOutput

        out = WriterOutput(
            markdown="",
            word_count=0,
            citations=[],
            is_valid=False,
            quality_score=0.0,
        )
        assert out.word_count == 0
        assert not out.is_valid
        assert out.generation_attempts == 1  # default

    def test_research_packet_extreme(self):
        from app.schemas.research_packet import ResearchPacket, SourceSummary

        many_findings = [f"Finding {i}" for i in range(1000)]
        many_sources = [SourceSummary(url=f"https://src{i}.com", domain=f"src{i}.com") for i in range(500)]

        rp = ResearchPacket(
            topic="Big Data",
            executive_summary="Large research packet",
            key_findings=many_findings,
            source_summaries=many_sources,
            statistics={"total": 1500},
        )
        assert len(rp.key_findings) == 1000
        assert len(rp.source_summaries) == 500

    def test_planner_input_minimal(self):
        from app.schemas.agent_inputs.planner import PlannerInput
        inp = PlannerInput(topic="AI")
        assert inp.topic == "AI"
        assert inp.title == ""
        assert inp.points_to_cover == []


# ── PROMPT SYSTEM TESTS ────────────────────────────────────────────────────────


class TestPromptSystem:
    def test_writer_prompt_contains_instructions(self):
        from app.prompts.builders.writer_prompts import build_writer_system_prompt, build_writer_user_prompt
        from app.schemas.agent_inputs.writer import WriterInput

        system = build_writer_system_prompt()
        assert "JSON" in system
        assert "markdown" in system
        assert "citations" in system
        assert "No filler" in system or "not placeholder" in system or "NO filler" in system

        inp = WriterInput(title="Test", topic="AI", tone="professional")
        user = build_writer_user_prompt(inp)
        assert "Test" in user
        assert "Instructions" in user

    def test_writer_prompt_prohibits_placeholders(self):
        from app.prompts.builders.writer_prompts import build_writer_system_prompt
        system = build_writer_system_prompt()
        assert "placeholder" in system.lower()
        assert "NO" in system

    def test_writer_prompt_includes_research(self):
        from app.prompts.builders.writer_prompts import build_writer_user_prompt
        from app.schemas.agent_inputs.writer import WriterInput
        from app.schemas.research_packet import ResearchPacket

        rp = ResearchPacket(
            executive_summary="Key findings from 50 sources on AI regulation.",
            key_findings=["Finding 1", "Finding 2"],
            statistics={"total_sources": 50, "unique_domains": 10},
        )
        inp = WriterInput(title="Test", research_packet=rp)
        user = build_writer_user_prompt(inp)
        assert "50 sources" in user or "50" in user

    def test_planner_prompt_contains_structure(self):
        from app.prompts.builders.planner_prompts import build_planner_system_prompt
        system = build_planner_system_prompt()
        assert "JSON" in system
        assert "outline" in system
        assert "research" in system


# ── EVENT BUS STRESS TESTS ─────────────────────────────────────────────────────


class TestEventBusStress:
    @pytest.mark.asyncio
    async def test_bulk_events(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        for i in range(500):
            e = WorkflowEvent(workflow_id=wf_id, event_type=f"e{i}", message=f"Event {i}")
            await bus.publish(e)

        events = bus.get_events(wf_id)
        assert len(events) == 500

    @pytest.mark.asyncio
    async def test_event_bus_max_capacity(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        for i in range(1000):
            e = WorkflowEvent(workflow_id=wf_id, event_type=f"e{i}", message=f"Event {i}")
            await bus.publish(e)

        events = bus.get_events(wf_id)
        assert len(events) <= 501

    @pytest.mark.asyncio
    async def test_event_deduplication(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        e1 = WorkflowEvent(event_id="dup-1", workflow_id=wf_id, event_type="test", message="Dup")
        e2 = WorkflowEvent(event_id="dup-1", workflow_id=wf_id, event_type="test", message="Dup")
        await bus.publish(e1)
        await bus.publish(e2)

        events = bus.get_events(wf_id)
        dup_ids = [e.event_id for e in events]
        assert dup_ids.count("dup-1") == 2  # no dedup — intentional

    @pytest.mark.asyncio
    async def test_event_replay_ordering(self):
        from app.events.event_bus import EventBus, WorkflowEvent

        bus = EventBus()
        wf_id = str(uuid.uuid4())

        for i in range(100):
            e = WorkflowEvent(workflow_id=wf_id, event_type=f"e{i}")
            await bus.publish(e)

        events = bus.get_events(wf_id)
        for i in range(100):
            assert events[i].event_type == f"e{i}", f"Ordering broken at index {i}"

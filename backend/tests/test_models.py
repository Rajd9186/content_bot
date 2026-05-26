"""Tests for SQLAlchemy model validation and datetime handling."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.chat import WorkflowEventRecord, ChatSession, ChatMessageModel
from app.models.workflow import WorkflowExecution, WorkflowStatus
from app.models.content_version import ContentVersion, ContentLock, EnhancementJob
from app.models.contradiction import Contradiction
from app.models.agent_memory import AgentMemory
from app.models.hyperlink import HyperlinkValidation
from app.utils.datetime_utils import utc_now


class TestWorkflowEventRecord:
    async def test_create_event(self, db_session):
        event = WorkflowEventRecord(
            project_id=uuid.uuid4(),
            workflow_id=uuid.uuid4(),
            event_type="agent_started",
            agent_name="planner",
            status="running",
            message="Planning started",
            progress_percent=10.0,
            payload_json={"key": "value"},
        )
        db_session.add(event)
        await db_session.flush()

        assert event.id is not None
        assert event.created_at is not None
        assert event.created_at.tzinfo == timezone.utc

    async def test_created_at_defaults_to_utc_now(self, db_session):
        event = WorkflowEventRecord(
            project_id=uuid.uuid4(),
            event_type="test",
        )
        db_session.add(event)
        await db_session.flush()

        now = utc_now()
        diff = abs((now - event.created_at).total_seconds())
        assert diff < 5.0  # Within 5 seconds

    async def test_to_sse_dict_uses_new_fields(self, db_session):
        event = WorkflowEventRecord(
            project_id=uuid.uuid4(),
            workflow_id=uuid.uuid4(),
            event_type="agent_completed",
            agent_name="writer",
            status="completed",
            message="Done",
            progress_percent=100.0,
            payload_json={"result": "ok"},
        )
        db_session.add(event)
        await db_session.flush()

        d = event.to_sse_dict()
        assert d["agent"] == "writer"
        assert d["type"] == "agent_completed"
        assert d["status"] == "completed"
        assert d["progress"] == 100.0
        assert d["payload"] == {"result": "ok"}
        assert d["timestamp"] != ""


class TestContentLock:
    async def test_create_lock(self, db_session):
        lock = ContentLock(
            project_id=uuid.uuid4(),
            locked_by="writer",
            expires_at=utc_now(),
        )
        db_session.add(lock)
        await db_session.flush()

        assert lock.locked_at is not None
        assert lock.locked_at.tzinfo == timezone.utc
        assert lock.expires_at is not None
        assert lock.expires_at.tzinfo == timezone.utc


class TestContradictionModel:
    async def test_create_contradiction(self, db_session):
        c = Contradiction(
            project_id=uuid.uuid4(),
            claim_text="Test claim",
            severity="high",
            conflicting_sources=["src1", "src2"],
            explanation="Test explanation",
        )
        db_session.add(c)
        await db_session.flush()

        assert c.created_at is not None
        assert c.created_at.tzinfo == timezone.utc


class TestAgentMemoryModel:
    async def test_create_memory(self, db_session):
        m = AgentMemory(
            project_id=uuid.uuid4(),
            agent_name="planner",
            memory_type="research",
            key="test_key",
            value={"data": "test"},
        )
        db_session.add(m)
        await db_session.flush()

        assert m.created_at is not None
        assert m.created_at.tzinfo == timezone.utc


class TestHyperlinkValidationModel:
    async def test_create_validation(self, db_session):
        h = HyperlinkValidation(
            project_id=uuid.uuid4(),
            url="https://example.com",
            label="Example",
            status="verified",
            is_verified=True,
        )
        db_session.add(h)
        await db_session.flush()

        assert h.created_at is not None
        assert h.created_at.tzinfo == timezone.utc


class TestWorkflowExecution:
    async def test_create_workflow(self, db_session):
        wf = WorkflowExecution(
            project_id=uuid.uuid4(),
            status=WorkflowStatus.running,
            current_node="planner",
        )
        db_session.add(wf)
        await db_session.flush()

        assert wf.started_at is not None
        assert wf.started_at.tzinfo == timezone.utc

    async def test_complete_workflow(self, db_session):
        wf = WorkflowExecution(
            project_id=uuid.uuid4(),
            status=WorkflowStatus.running,
        )
        db_session.add(wf)
        await db_session.flush()

        wf.status = WorkflowStatus.completed
        wf.completed_at = utc_now()
        await db_session.flush()

        assert wf.completed_at is not None
        assert wf.completed_at.tzinfo == timezone.utc


class TestSchemaValidation:
    async def test_workflow_event_record_has_no_node_name(self, db_session):
        """Ensure WorkflowEventRecord does NOT have node_name (caused Issue 2)."""
        event = WorkflowEventRecord(
            project_id=uuid.uuid4(),
            event_type="test",
        )
        db_session.add(event)
        await db_session.flush()

        # Accessing node_name should raise AttributeError
        with pytest.raises(AttributeError):
            _ = event.node_name

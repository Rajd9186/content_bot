"""Tests for serialization — ensuring no old-field-name crashes."""

import uuid
from datetime import datetime, timezone

from app.schemas.chat import WorkflowEvent, ChatMessage, ChatResponse, ChatRequest
from app.schemas.sse_event import SSEEvent
from app.utils.datetime_utils import utc_now


class TestWorkflowEventSchema:
    def test_create_with_new_fields(self):
        event = WorkflowEvent(
            project_id=str(uuid.uuid4()),
            event_type="agent_started",
            agent_name="planner",
            status="running",
            message="Starting",
            progress_percent=10.0,
            payload={"query": "test"},
            timestamp=utc_now().isoformat(),
        )
        assert event.agent_name == "planner"
        assert event.progress_percent == 10.0
        assert event.payload == {"query": "test"}

    def test_defaults(self):
        event = WorkflowEvent(
            project_id=str(uuid.uuid4()),
            event_type="test",
        )
        assert event.agent_name == ""
        assert event.status == "running"
        assert event.progress_percent == 0.0
        assert event.payload == {}

    def test_no_node_name_field(self):
        """Ensure node_name is not in the schema (caused Issue 2)."""
        event = WorkflowEvent(
            project_id=str(uuid.uuid4()),
            event_type="test",
        )
        assert not hasattr(event, "node_name")
        assert not hasattr(event, "data")

    def test_serialization_roundtrip(self):
        original = WorkflowEvent(
            project_id=str(uuid.uuid4()),
            event_type="agent_completed",
            agent_name="writer",
            status="completed",
        )
        d = original.model_dump()
        restored = WorkflowEvent.model_validate(d)
        assert restored.agent_name == original.agent_name
        assert restored.event_type == original.event_type
        assert restored.status == original.status


class TestSSEEventSchema:
    def test_create_with_all_fields(self):
        event = SSEEvent(
            id="test-id",
            workflow_id="wf-1",
            type="agent_progress",
            agent="writer",
            status="running",
            message="Writing...",
            progress=50.0,
            payload={"word_count": 100},
            timestamp=utc_now().isoformat(),
        )
        d = event.to_sse_dict()
        assert d["id"] == "test-id"
        assert d["workflow_id"] == "wf-1"
        assert d["type"] == "agent_progress"
        assert d["agent"] == "writer"
        assert d["progress"] == 50.0

    def test_none_coercion(self):
        """None values should be coerced to empty/default values."""
        event = SSEEvent.model_validate({
            "id": None,
            "workflow_id": None,
            "type": None,
            "agent": None,
            "status": None,
            "message": None,
            "progress": None,
            "payload": None,
            "timestamp": None,
        })
        assert event.id == ""
        assert event.workflow_id == ""
        assert event.type == ""
        assert event.agent == ""
        # When status is explicitly provided as None, it becomes ""
        # (the validator coerces None to ""; default is not applied for provided fields)
        assert event.status == ""
        assert event.progress == 0.0
        assert event.payload == {}


class TestChatMessageSchema:
    def test_create_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp.tzinfo == timezone.utc


class TestChatResponseSchema:
    def test_create_response(self):
        resp = ChatResponse(
            content="Response text",
            project_id=str(uuid.uuid4()),
        )
        assert resp.content == "Response text"
        assert "timestamp" in resp.metadata or not resp.metadata

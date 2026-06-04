"""Tests for UUID serialization across schemas, models, and API responses.

Verifies that UUID fields are properly handled at every layer to prevent
the Input should be a valid string / input_value=UUID(...) error.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.workflow import WorkflowStepResponse, WorkflowExecutionResponse
from app.schemas.contradiction import ContradictionResponse
from app.schemas.hyperlink import HyperlinkValidationResponse
from app.schemas.project import ProjectResponse
from app.schemas.content import ContentResponse
from app.schemas.claim import ClaimResponse
from app.schemas.evidence import EvidenceResponse
from app.schemas.source import SourceResponse
from app.schemas.enhance import EnhancementJobResponse, ContentVersionResponse


class TestUuidFieldTypes:
    """Verify every schema uses UUID (not str) for ID fields."""

    def test_workflow_step_response_uses_uuid(self):
        assert WorkflowStepResponse.model_fields["id"].annotation is uuid.UUID
        assert WorkflowStepResponse.model_fields["workflow_id"].annotation is uuid.UUID

    def test_workflow_execution_response_uses_uuid(self):
        assert WorkflowExecutionResponse.model_fields["id"].annotation is uuid.UUID
        assert WorkflowExecutionResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_contradiction_response_uses_uuid(self):
        assert ContradictionResponse.model_fields["id"].annotation is uuid.UUID
        assert ContradictionResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_hyperlink_response_uses_uuid(self):
        assert HyperlinkValidationResponse.model_fields["id"].annotation is uuid.UUID
        assert HyperlinkValidationResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_project_response_uses_uuid(self):
        assert ProjectResponse.model_fields["id"].annotation is uuid.UUID

    def test_content_response_uses_uuid(self):
        assert ContentResponse.model_fields["id"].annotation is uuid.UUID
        assert ContentResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_claim_response_uses_uuid(self):
        assert ClaimResponse.model_fields["id"].annotation is uuid.UUID
        assert ClaimResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_evidence_response_uses_uuid(self):
        assert EvidenceResponse.model_fields["id"].annotation is uuid.UUID
        assert EvidenceResponse.model_fields["project_id"].annotation is uuid.UUID
        assert EvidenceResponse.model_fields["claim_id"].annotation == uuid.UUID | None
        assert EvidenceResponse.model_fields["source_id"].annotation == uuid.UUID | None

    def test_source_response_uses_uuid(self):
        assert SourceResponse.model_fields["id"].annotation is uuid.UUID
        assert SourceResponse.model_fields["project_id"].annotation is uuid.UUID

    def test_enhancement_job_response_uses_uuid(self):
        assert EnhancementJobResponse.model_fields["id"].annotation is uuid.UUID
        assert EnhancementJobResponse.model_fields["project_id"].annotation is uuid.UUID
        assert EnhancementJobResponse.model_fields["workflow_id"].annotation is uuid.UUID


class TestUuidFromOrm:
    """Verify schemas with from_attributes=True accept UUID objects from ORM."""

    @pytest.mark.parametrize("schema_cls", [
        WorkflowStepResponse,
        WorkflowExecutionResponse,
        ContradictionResponse,
        HyperlinkValidationResponse,
        ProjectResponse,
        ContentResponse,
        ClaimResponse,
        EvidenceResponse,
        SourceResponse,
        EnhancementJobResponse,
        ContentVersionResponse,
    ])
    def test_all_schemas_have_from_attributes(self, schema_cls):
        assert schema_cls.model_config.get("from_attributes") is True, (
            f"{schema_cls.__name__} missing from_attributes=True"
        )

    def test_workflow_step_from_orm(self):
        class FakeOrm:
            id = uuid.uuid4()
            workflow_id = uuid.uuid4()
            node_name = "planner"
            agent_name = "planner"
            status = "completed"
            started_at = "2026-01-01T00:00:00"
            completed_at = None
            duration_ms = None
            input_data = None
            output_data = None
            error = None
            retry_count = 0

        result = WorkflowStepResponse.model_validate(FakeOrm())
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result.workflow_id, uuid.UUID)

    def test_contradiction_from_orm(self):
        class FakeOrm:
            id = uuid.uuid4()
            project_id = uuid.uuid4()
            claim_text = "Test"
            severity = "high"
            conflicting_sources = []
            explanation = None
            resolved = False
            created_at = "2026-01-01T00:00:00"

        result = ContradictionResponse.model_validate(FakeOrm())
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result.project_id, uuid.UUID)

    def test_hyperlink_from_orm(self):
        class FakeOrm:
            id = uuid.uuid4()
            project_id = uuid.uuid4()
            url = "https://example.com"
            label = None
            status = "pending"
            status_code = None
            error_message = None
            resolved_url = None
            is_verified = False
            checked_at = None
            created_at = "2026-01-01T00:00:00"

        result = HyperlinkValidationResponse.model_validate(FakeOrm())
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result.project_id, uuid.UUID)


class TestUuidSerializationToJson:
    """Verify UUID fields serialize as strings in JSON output."""

    def test_workflow_execution_serializes_uuid_as_string(self):
        class FakeOrm:
            id = uuid.uuid4()
            project_id = uuid.uuid4()
            status = "running"
            current_node = "planner"
            error = None
            telemetry = None
            started_at = "2026-01-01T00:00:00"
            completed_at = None

        result = WorkflowExecutionResponse.model_validate(FakeOrm())
        data = result.model_dump(mode="json")
        assert isinstance(data["id"], str)
        assert isinstance(data["project_id"], str)
        uuid.UUID(data["id"])
        uuid.UUID(data["project_id"])

    def test_evidence_response_extra_fields(self):
        class FakeOrm:
            id = uuid.uuid4()
            project_id = uuid.uuid4()
            claim_id = uuid.uuid4()
            source_id = uuid.uuid4()
            snippet = "test"
            relevance_score = 0.9
            extracted_at = "2026-01-01T00:00:00"

        result = EvidenceResponse.model_validate(FakeOrm())
        result.source_url = "https://example.com"
        result.source_domain = "example.com"
        data = result.model_dump(mode="json")
        assert isinstance(data["id"], str)
        assert data["source_url"] == "https://example.com"


class TestUuidRejectsInvalidInput:
    """Verify schemas reject invalid UUID inputs where appropriate."""

    def test_workflow_step_rejects_invalid_uuid(self):
        with pytest.raises(ValidationError):
            WorkflowStepResponse(
                id="not-a-uuid",
                workflow_id=uuid.uuid4(),
                node_name="test",
                status="running",
                started_at="2026-01-01T00:00:00",
            )

    def test_workflow_step_accepts_uuid_string(self):
        uid = str(uuid.uuid4())
        result = WorkflowStepResponse(
            id=uid,
            workflow_id=str(uuid.uuid4()),
            node_name="test",
            agent_name="test",
            status="running",
            started_at="2026-01-01T00:00:00",
            completed_at=None,
            duration_ms=None,
            input_data=None,
            output_data=None,
            error=None,
            retry_count=0,
        )
        assert isinstance(result.id, uuid.UUID)
        assert isinstance(result.workflow_id, uuid.UUID)

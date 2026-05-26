from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WorkflowStepResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    node_name: str
    agent_name: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    duration_ms: float | None
    input_data: dict | None
    output_data: dict | None
    error: str | None
    retry_count: int

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    current_node: str
    error: str | None
    telemetry: dict | None
    started_at: datetime
    completed_at: datetime | None
    steps: list[WorkflowStepResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WorkflowTelemetry(BaseModel):
    total_duration_ms: float
    node_durations: dict[str, float]
    total_retries: int
    total_llm_calls: int
    total_sources: int
    total_claims: int
    total_contradictions: int
    revision_count: int
    hyperlinks_checked: int
    hyperlinks_valid: int
    overall_quality_score: float

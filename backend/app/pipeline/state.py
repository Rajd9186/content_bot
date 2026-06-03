from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class NodeResult(BaseModel):
    node: str
    status: NodeStatus = NodeStatus.PENDING
    output: dict[str, Any] = Field(default_factory=dict)
    actions: list[dict[str, Any]] = Field(default_factory=list)  # Added to track agentic actions
    error: str | None = None
    retry_count: int = 0
    started_at: str | None = None
    completed_at: str | None = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class ReviewAction(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class HumanReview(BaseModel):
    reviewer_id: str | None = None
    action: ReviewAction | None = None
    comments: str = ""
    reviewed_at: str | None = None


class PipelineState(BaseModel):
    workflow_id: str
    workspace_id: str = ""
    correlation_id: str = ""
    content_item_id: str | None = None

    topic: str = ""
    audience: str = "general"
    tone: str = "professional"
    goals: str = ""

    research_data: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    outline: dict[str, Any] = Field(default_factory=dict)
    draft_content: str = ""
    seo_metadata: dict[str, Any] = Field(default_factory=dict)
    fact_check_results: dict[str, Any] = Field(default_factory=dict)
    compliance_results: dict[str, Any] = Field(default_factory=dict)
    vlog_links: list[dict[str, str] | str] = Field(default_factory=list)
    final_content: str = ""

    human_review: HumanReview | None = None
    node_results: dict[str, NodeResult] = Field(default_factory=dict)

    errors: list[str] = Field(default_factory=list)
    current_node: str = "research"
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def add_node_result(self, name: str, result: NodeResult) -> None:
        self.node_results[name] = result
        self.updated_at = datetime.now(UTC).isoformat()

    def get_node_result(self, name: str) -> NodeResult | None:
        return self.node_results.get(name)

    def all_nodes_completed(self) -> bool:
        return all(
            r.status in (NodeStatus.SUCCESS, NodeStatus.SKIPPED)
            for r in self.node_results.values()
        )

    def has_failures(self) -> bool:
        """Returns True only if there are actual failed node results or logged errors."""
        has_failed_nodes = any(
            r.status == NodeStatus.FAILED
            for r in self.node_results.values()
        )
        return has_failed_nodes or len(self.errors) > 0

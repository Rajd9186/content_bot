from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class NodeResult(BaseModel):
    node: str
    status: NodeStatus = NodeStatus.PENDING
    output: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0


class ReviewAction(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class HumanReview(BaseModel):
    reviewer_id: Optional[str] = None
    action: Optional[ReviewAction] = None
    comments: str = ""
    reviewed_at: Optional[str] = None


class PipelineState(BaseModel):
    workflow_id: str
    workspace_id: str = ""
    correlation_id: str = ""
    content_item_id: Optional[str] = None

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
    final_content: str = ""

    human_review: Optional[HumanReview] = None
    node_results: dict[str, NodeResult] = Field(default_factory=dict)

    errors: list[str] = Field(default_factory=list)
    current_node: str = "research"
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def add_node_result(self, name: str, result: NodeResult) -> None:
        self.node_results[name] = result
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_node_result(self, name: str) -> Optional[NodeResult]:
        return self.node_results.get(name)

    def all_nodes_completed(self) -> bool:
        return all(
            r.status == NodeStatus.SUCCESS
            for r in self.node_results.values()
        )

    def has_failures(self) -> bool:
        return any(
            r.status == NodeStatus.FAILED
            for r in self.node_results.values()
        )

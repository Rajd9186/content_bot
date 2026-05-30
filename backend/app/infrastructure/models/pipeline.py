import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.models.base import Base, JSONBColumn, utcnow


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workflow_id: Mapped[str] = mapped_column(
        "workflow_id", UUID(as_uuid=False), nullable=False, unique=True, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        "workspace_id", UUID(as_uuid=False), nullable=False, index=True
    )
    correlation_id: Mapped[str] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=False, index=True
    )
    content_item_id: Mapped[Optional[str]] = mapped_column(
        "content_item_id", UUID(as_uuid=False), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="pending", index=True
    )
    current_node: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="research"
    )

    topic: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    audience: Mapped[str] = mapped_column(String(128), nullable=False, server_default="general")
    tone: Mapped[str] = mapped_column(String(128), nullable=False, server_default="professional")
    goals: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    research_data: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    plan: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    outline: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    draft_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_metadata: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    fact_check_results: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    compliance_results: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    final_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    human_review: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True)
    node_results: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True, default=dict)
    errors: Mapped[Optional[dict]] = mapped_column(JSONBColumn, nullable=True, default=dict)

    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")

    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONBColumn, nullable=True, default=dict
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(
        "heartbeat_at", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("idx_pr_workflow", "workflow_id"),
        Index("idx_pr_workspace_status", "workspace_id", "status"),
        Index("idx_pr_status_heartbeat", "status", "heartbeat_at"),
    )

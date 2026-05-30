import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, JSONBColumn, utcnow


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        "workspace_id", UUID(as_uuid=False), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_type: Mapped[str] = mapped_column("agent_type", String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), default="gpt-4o")
    prompt_template: Mapped[str | None] = mapped_column(
        "prompt_template", Text, nullable=True
    )
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    max_tokens: Mapped[int] = mapped_column("max_tokens", Integer, default=2000)
    timeout_ms: Mapped[int] = mapped_column("timeout_ms", Integer, default=60000)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("idx_ac_workspace_type", "workspace_id", "agent_type"),
    )


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        "job_id", UUID(as_uuid=False),
        ForeignKey("workflow_jobs.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    agent_config_id: Mapped[str | None] = mapped_column(
        "agent_config_id", UUID(as_uuid=False),
        ForeignKey("agent_configs.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    input_payload: Mapped[dict | None] = mapped_column(
        "input_payload", JSONBColumn, nullable=True
    )
    output_payload: Mapped[dict | None] = mapped_column(
        "output_payload", JSONBColumn, nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column("tokens_used", Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    correlation_id: Mapped[str] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )


class AgentCall(Base):
    __tablename__ = "agent_calls"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_execution_id: Mapped[str] = mapped_column(
        "agent_execution_id", UUID(as_uuid=False),
        ForeignKey("agent_executions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    request_payload: Mapped[dict | None] = mapped_column(
        "request_payload", JSONBColumn, nullable=True
    )
    response_payload: Mapped[dict | None] = mapped_column(
        "response_payload", JSONBColumn, nullable=True
    )
    prompt_tokens: Mapped[int | None] = mapped_column("prompt_tokens", Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(
        "completion_tokens", Integer, nullable=True
    )
    total_tokens: Mapped[int | None] = mapped_column("total_tokens", Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column("latency_ms", Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )

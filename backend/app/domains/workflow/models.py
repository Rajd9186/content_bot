import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, JSONBColumn, utcnow


class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        "workspace_id", UUID(as_uuid=False), nullable=False, index=True
    )
    content_item_id: Mapped[str | None] = mapped_column(
        "content_item_id", UUID(as_uuid=False), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", index=True)
    processing_stage: Mapped[str | None] = mapped_column(
        "processing_stage", String(32), nullable=True
    )
    retry_count: Mapped[int] = mapped_column("retry_count", Integer, default=0)
    max_retries: Mapped[int] = mapped_column("max_retries", Integer, default=3)
    timeout_ms: Mapped[int] = mapped_column("timeout_ms", Integer, default=300000)
    error_code: Mapped[str | None] = mapped_column("error_code", String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(
        "error_message", Text, nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    correlation_id: Mapped[str] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        "created_by", UUID(as_uuid=False), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    steps = relationship("WorkflowStep", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wfj_status_created", "status", "created_at"),
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        "job_id", UUID(as_uuid=False), ForeignKey("workflow_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    step_type: Mapped[str] = mapped_column("step_type", String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(
        "started_at", DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        "completed_at", DateTime(timezone=True), nullable=True
    )
    output: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )

    job = relationship("WorkflowJob", back_populates="steps")

    __table_args__ = (
        Index("idx_wfs_job_type", "job_id", "step_type"),
    )


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        "job_id", UUID(as_uuid=False), ForeignKey("workflow_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column("from_status", String(32), nullable=True)
    to_status: Mapped[str] = mapped_column("to_status", String(32), nullable=False)
    transition: Mapped[str] = mapped_column(String(64), nullable=False)
    triggered_by: Mapped[str] = mapped_column("triggered_by", String(128), nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONBColumn, nullable=True, default=dict)
    correlation_id: Mapped[str] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )

    job = relationship("WorkflowJob", back_populates="logs")

    __table_args__ = (
        Index("idx_exl_job_created", "job_id", "created_at"),
    )


class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    original_job_id: Mapped[str] = mapped_column(
        "original_job_id", UUID(as_uuid=False), nullable=False, index=True
    )
    error_code: Mapped[str] = mapped_column("error_code", String(64), nullable=False)
    error_message: Mapped[str | None] = mapped_column("error_message", Text, nullable=True)
    retry_attempts: Mapped[int] = mapped_column("retry_attempts", Integer, default=0)
    payload: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True)
    failed_at: Mapped[datetime] = mapped_column(
        "failed_at", DateTime(timezone=True), default=utcnow
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        "resolved_at", DateTime(timezone=True), nullable=True
    )

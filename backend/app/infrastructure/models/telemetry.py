import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, JSONBColumn, utcnow


class RetryRecord(Base):
    __tablename__ = "retry_records"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    target_type: Mapped[str] = mapped_column("target_type", String(64), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(
        "target_id", UUID(as_uuid=False), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column("attempt_number", Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    error_code: Mapped[str | None] = mapped_column("error_code", String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column("error_message", Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(
        "scheduled_at", DateTime(timezone=True), nullable=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        "executed_at", DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )

    __table_args__ = (
        Index("idx_rr_target", "target_type", "target_id"),
    )


class TelemetryMetric(Base):
    __tablename__ = "telemetry_metrics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    metric_name: Mapped[str] = mapped_column("metric_name", String(128), nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column("metric_type", String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    labels: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    service_name: Mapped[str] = mapped_column("service_name", String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )

    __table_args__ = (
        Index("idx_tm_name_timestamp", "metric_name", "timestamp"),
    )


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    aggregate_id: Mapped[str] = mapped_column(
        "aggregate_id", String(64), nullable=False, index=True
    )
    aggregate_type: Mapped[str] = mapped_column("aggregate_type", String(64), nullable=False)
    checkpoint_type: Mapped[str] = mapped_column("checkpoint_type", String(64), nullable=False)
    state: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        UniqueConstraint("aggregate_type", "aggregate_id", "checkpoint_type",
                         name="uq_checkpoint_aggregate_type"),
    )

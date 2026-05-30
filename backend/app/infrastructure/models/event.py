from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, JSONBColumn


class StoredEvent(Base):
    __tablename__ = "stored_events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sequence_number: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, unique=True, index=True
    )
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    event_type: Mapped[str] = mapped_column("event_type", String(128), nullable=False, index=True)
    event_version: Mapped[int] = mapped_column("event_version", Integer, default=1)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    data: Mapped[dict | None] = mapped_column(JSONBColumn, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSONBColumn, nullable=True, default=dict)
    correlation_id: Mapped[str] = mapped_column(
        "correlation_id", UUID(as_uuid=False), nullable=False, index=True
    )
    aggregate_id: Mapped[str | None] = mapped_column(
        "aggregate_id", String(64), nullable=True, index=True
    )
    aggregate_type: Mapped[str | None] = mapped_column(
        "aggregate_type", String(64), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), default=datetime.now
    )

    __table_args__ = (
        Index("idx_se_type_created", "event_type", "created_at"),
        Index("idx_se_aggregate", "aggregate_type", "aggregate_id"),
    )

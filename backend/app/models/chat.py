import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class WorkflowEventRecord(Base):
    """Persistent workflow event record for SSE streaming and replay."""

    __tablename__ = "workflow_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    progress_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_sse_dict(self) -> dict:
        from app.schemas.sse_event import SSEEvent
        return SSEEvent(
            id=str(self.id),
            workflow_id=str(self.workflow_id) if self.workflow_id else "",
            type=self.event_type,
            agent=self.agent_name,
            status=self.status,
            message=self.message,
            progress=self.progress_percent,
            payload=self.payload_json or {},
            timestamp=self.created_at.isoformat() if self.created_at else "",
        ).to_sse_dict()

"""Add workflow execution, content version, enhancement, and memory tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- workflow_executions ---
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "cancelled", "waiting_user", name="workflow_status"),
            default="running",
        ),
        sa.Column("current_node", sa.String(100), default="planner"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("telemetry", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_workflow_executions_project_id", "workflow_executions", ["project_id"])

    # --- workflow_steps ---
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_name", sa.String(100), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), default="running"),
        sa.Column("started_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), default=0),
    )
    op.create_index("ix_workflow_steps_workflow_id", "workflow_steps", ["workflow_id"])

    # --- workflow_events ---
    op.create_table(
        "workflow_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(100), default=""),
        sa.Column("status", sa.String(20), default="running"),
        sa.Column("message", sa.Text(), default=""),
        sa.Column("progress_percent", sa.Float(), default=0.0),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), index=True, default=sa.func.now()),
    )
    op.create_index("ix_workflow_events_workflow_id", "workflow_events", ["workflow_id"])
    op.create_index("ix_workflow_events_project_id", "workflow_events", ["project_id"])
    op.create_index("ix_workflow_events_event_type", "workflow_events", ["event_type"])

    # --- content_versions ---
    op.create_table(
        "content_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "reviewing", "revised", "final", "archived", name="content_version_status"),
            default="draft",
        ),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("citations", sa.JSON(), default=list),
        sa.Column("seo_metadata", sa.JSON(), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("parent_version_id", sa.Uuid(), sa.ForeignKey("content_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("change_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_project_version", "content_versions", ["project_id", "version_number"])
    op.create_index("ix_content_versions_project_id", "content_versions", ["project_id"])

    # --- content_locks ---
    op.create_table(
        "content_locks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("locked_by", sa.String(100), nullable=False),
        sa.Column("locked_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )

    # --- enhancement_jobs ---
    op.create_table(
        "enhancement_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("progress", sa.Float(), default=0.0),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_enhancement_jobs_project_id", "enhancement_jobs", ["project_id"])

    # --- chat_sessions ---
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), default=sa.func.now()),
    )

    # --- chat_messages ---
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    # --- contradictions ---
    op.create_table(
        "contradictions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_executions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), default="medium"),
        sa.Column("conflicting_sources", sa.JSON(), default=list),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), default=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )

    # --- agent_memory ---
    op.create_table(
        "agent_memory",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("memory_type", sa.String(50), default="research"),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("value", sa.JSON(), default=dict),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("access_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
    )

    # --- hyperlink_validations ---
    op.create_table(
        "hyperlink_validations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_id", sa.Uuid(), sa.ForeignKey("generated_content.id", ondelete="SET NULL"), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("label", sa.String(300), nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("resolved_url", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("hyperlink_validations")
    op.drop_table("agent_memory")
    op.drop_table("contradictions")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("enhancement_jobs")
    op.drop_table("content_locks")
    op.drop_table("content_versions")
    op.drop_table("workflow_events")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_executions")
    op.execute("DROP TYPE IF EXISTS workflow_status")
    op.execute("DROP TYPE IF EXISTS content_version_status")

"""Initial schema: all domain models

Revision ID: 0001
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Workflow Domain ────────────────────────────────────────
    op.create_table(
        "workflow_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT", index=True),
        sa.Column("processing_stage", sa.String(32), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="300000"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_wfj_status_created", "workflow_jobs", ["status", "created_at"])

    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("workflow_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("step_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_wfs_job_type", "workflow_steps", ["job_id", "step_type"])

    op.create_table(
        "execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("workflow_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("transition", sa.String(64), nullable=False),
        sa.Column("triggered_by", sa.String(128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_exl_job_created", "execution_logs", ["job_id", "created_at"])

    op.create_table(
        "dead_letter_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("original_job_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("error_code", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Content Domain ────────────────────────────────────────
    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(250), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft", index=True),
        sa.Column("raw_body", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ci_workspace_status", "content_items", ["workspace_id", "status"])

    op.create_table(
        "content_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("raw_body", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "generated_content",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True, index=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Agent Domain ──────────────────────────────────────────
    op.create_table(
        "agent_configs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("agent_type", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False, server_default="gpt-4o"),
        sa.Column("prompt_template", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="60000"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ac_workspace_type", "agent_configs", ["workspace_id", "agent_type"])

    op.create_table(
        "agent_executions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("workflow_jobs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("agent_config_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("agent_configs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("input_payload", postgresql.JSONB(), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_calls",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("agent_execution_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Event System ──────────────────────────────────────────
    op.create_table(
        "stored_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False, index=True),
        sa.Column("event_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("subject", sa.String(256), nullable=True, index=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("aggregate_id", sa.String(64), nullable=True, index=True),
        sa.Column("aggregate_type", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_se_type_created", "stored_events", ["event_type", "created_at"])
    op.create_index("idx_se_aggregate", "stored_events", ["aggregate_type", "aggregate_id"])

    # ── Telemetry ─────────────────────────────────────────────
    op.create_table(
        "retry_records",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("target_type", sa.String(64), nullable=False, index=True),
        sa.Column("target_id", postgresql.UUID(as_uuid=False), nullable=False, index=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_rr_target", "retry_records", ["target_type", "target_id"])

    op.create_table(
        "telemetry_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("metric_name", sa.String(128), nullable=False, index=True),
        sa.Column("metric_type", sa.String(32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("labels", postgresql.JSONB(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("service_name", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_tm_name_timestamp", "telemetry_metrics", ["metric_name", "timestamp"])

    op.create_table(
        "checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("aggregate_id", sa.String(64), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("checkpoint_type", sa.String(64), nullable=False),
        sa.Column("state", postgresql.JSONB(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_checkpoint_aggregate_type", "checkpoints",
        ["aggregate_type", "aggregate_id", "checkpoint_type"]
    )


def downgrade() -> None:
    op.drop_table("checkpoints")
    op.drop_table("telemetry_metrics")
    op.drop_table("retry_records")
    op.drop_table("stored_events")
    op.drop_table("agent_calls")
    op.drop_table("agent_executions")
    op.drop_table("agent_configs")
    op.drop_table("generated_content")
    op.drop_table("content_versions")
    op.drop_table("content_items")
    op.drop_table("dead_letter_jobs")
    op.drop_table("execution_logs")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_jobs")

"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-05-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("points_to_cover", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("tone", sa.String(50), nullable=False, server_default="professional"),
        sa.Column("content_type", sa.String(50), nullable=False, server_default="article"),
        sa.Column("target_audience", sa.String(300), nullable=True),
        sa.Column("seo_keywords", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("outline", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(300), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("author", sa.String(300), nullable=True),
        sa.Column("published_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="unverified"),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "generated_content",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("seo_metadata", sa.JSON(), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_id", sa.Uuid(), sa.ForeignKey("claims.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_sources_project_id", "sources", ["project_id"])
    op.create_index("ix_claims_project_id", "claims", ["project_id"])
    op.create_index("ix_evidence_project_id", "evidence", ["project_id"])
    op.create_index("ix_generated_content_project_id", "generated_content", ["project_id"])


def downgrade() -> None:
    op.drop_table("evidence")
    op.drop_table("generated_content")
    op.drop_table("claims")
    op.drop_table("sources")
    op.drop_table("projects")

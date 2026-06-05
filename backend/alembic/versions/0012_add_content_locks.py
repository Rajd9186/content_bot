"""Add content_locks table for content version locking

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_locks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("locked_by", sa.String(100), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_content_locks_expires_at", "content_locks", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_content_locks_expires_at", table_name="content_locks")
    op.drop_table("content_locks")

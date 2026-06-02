"""Add vlog_links to pipeline_runs if missing

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("pipeline_runs")]
    if "vlog_links" not in columns:
        op.add_column("pipeline_runs", sa.Column("vlog_links", postgresql.JSONB(), nullable=True, server_default='[]'))


def downgrade() -> None:
    op.drop_column("pipeline_runs", "vlog_links")

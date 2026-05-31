"""Add vlog_links to pipeline_runs

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pipeline_runs", sa.Column("vlog_links", postgresql.JSONB(), nullable=True, server_default='[]'))


def downgrade() -> None:
    op.drop_column("pipeline_runs", "vlog_links")

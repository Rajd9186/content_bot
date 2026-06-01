"""Change projects.owner_id from UUID to VARCHAR

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "projects",
        "owner_id",
        type_=sa.String(255),
        existing_type=postgresql.UUID(as_uuid=False),
        nullable=False,
        postgresql_using="owner_id::varchar(255)",
    )


def downgrade() -> None:
    op.alter_column(
        "projects",
        "owner_id",
        type_=postgresql.UUID(as_uuid=False),
        existing_type=sa.String(255),
        nullable=False,
        postgresql_using="owner_id::uuid",
    )

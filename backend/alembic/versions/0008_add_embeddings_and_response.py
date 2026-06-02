"""Add embedding to project_memories and response to project_conversations

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "project_conversations",
        sa.Column("response", sa.Text(), nullable=True),
    )

    op.add_column(
        "project_memories",
        sa.Column("embedding", Vector(1536), nullable=True),
    )

    op.create_index(
        "idx_pm_embedding_hnsw",
        "project_memories",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 200},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_pm_embedding_hnsw", table_name="project_memories")
    op.drop_column("project_memories", "embedding")
    op.drop_column("project_conversations", "response")

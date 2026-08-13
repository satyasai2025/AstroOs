"""Add knowledge_embeddings table for RAG-grounded AI answers

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-13 00:00:00.000000

Stores one embedding vector per piece of knowledge-base text (verse
translations, rule interpretations, ...) — the retrieval index that lets
the AI engine's opt-in local-LLM backend (Phase IV.3) ground its answers
in AstroOS's own classical sources instead of the model's memory alone.

Generic/polymorphic (source_type + source_id), not a hard foreign key —
see KnowledgeEmbeddingModel's docstring in apps/api/models/astrology.py
for why.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_embeddings",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedded_text", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=False),
    )
    op.create_index(
        "ix_knowledge_embeddings_source_type",
        "knowledge_embeddings", ["source_type"],
    )
    op.create_index(
        "ix_knowledge_embeddings_source_id",
        "knowledge_embeddings", ["source_id"],
    )
    # One embedding per (source, model) — re-embedding with the same model
    # replaces the row (upsert) rather than accumulating duplicates.
    op.create_unique_constraint(
        "uq_knowledge_embeddings_source_model",
        "knowledge_embeddings", ["source_type", "source_id", "model_name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_knowledge_embeddings_source_model", "knowledge_embeddings", type_="unique")
    op.drop_index("ix_knowledge_embeddings_source_id", table_name="knowledge_embeddings")
    op.drop_index("ix_knowledge_embeddings_source_type", table_name="knowledge_embeddings")
    op.drop_table("knowledge_embeddings")

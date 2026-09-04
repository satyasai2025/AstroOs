"""Add datasets table + link to research_projects

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-17 00:00:00.000000

Tables added:
  datasets  — persisted metadata for imported datasets

Columns added:
  research_projects.dataset_id  — FK to datasets.id
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _trigger(conn, table: str) -> None:
    conn.execute(sa.text(
        f"CREATE TRIGGER trg_{table}_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))


def upgrade() -> None:
    conn = op.get_bind()

    # ── datasets table ──────────────────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("dataset_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source_file", sa.String(500), nullable=True),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("field_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("quality_tier", sa.String(10), nullable=True),
        sa.Column("lifecycle_stage", sa.String(20), nullable=False, server_default="Draft"),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # Indexes
    op.create_index("ix_datasets_dataset_id", "datasets", ["dataset_id"], unique=True)
    op.create_index("ix_datasets_created_by", "datasets", ["created_by"])
    op.create_index("ix_datasets_lifecycle_stage", "datasets", ["lifecycle_stage"])
    op.create_index("ix_datasets_deleted_at", "datasets", ["deleted_at"],
                    postgresql_where=sa.text("deleted_at IS NULL"))

    _trigger(conn, "datasets")

    # ── Add dataset_id to research_projects ─────────────────────────────────
    op.add_column(
        "research_projects",
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("datasets.id", ondelete="SET NULL"),
                  nullable=True),
    )
    op.create_index("ix_research_projects_dataset_id", "research_projects", ["dataset_id"])


def downgrade() -> None:
    # Remove FK + index from research_projects
    op.drop_index("ix_research_projects_dataset_id", table_name="research_projects")
    op.drop_column("research_projects", "dataset_id")

    # Drop datasets table
    op.execute("DROP TRIGGER IF EXISTS trg_datasets_updated_at ON datasets")
    op.drop_table("datasets")

"""Add Digital Twin tables for what-if chart simulation

Revision ID: 0013
Revises: 0012_snapshot_phase4
Create Date: 2026-07-24 00:00:00.000000

Tables added:
  digital_twins           — mutable chart twin with tracked modifications
  twin_modifications     — audit trail for individual modifications

Digital Twin stores modifications relative to an original birth_chart.
The actual twin chart state is computed on demand by applying
modifications to the original.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── digital_twins ─────────────────────────────────────────────────────
    op.create_table(
        "digital_twins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("original_chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("modifications_json", postgresql.JSONB, nullable=True),
        sa.Column("cached_chart_json", postgresql.JSONB, nullable=True),
        sa.Column("cached_strengths_json", postgresql.JSONB, nullable=True),
        sa.Column("cached_yoga_names", postgresql.JSONB, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        # Audit columns (inherited from AstroBase)
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Index for efficient queries: find all twins for a chart, or by user
    op.create_index("ix_digital_twins_user_id", "digital_twins", ["user_id"])
    op.create_index("ix_digital_twins_chart_id", "digital_twins", ["original_chart_id"])
    op.create_index("ix_digital_twins_status", "digital_twins", ["status"])

    # Composite index for common query pattern: user's active twins for a chart
    op.create_index(
        "ix_digital_twins_user_chart_status",
        "digital_twins",
        ["user_id", "original_chart_id", "status"],
    )

    # ── twin_modifications ────────────────────────────────────────────────
    op.create_table(
        "twin_modifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("twin_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("digital_twins.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("modification_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(100), nullable=False),
        sa.Column("old_value", postgresql.JSONB, nullable=True),
        sa.Column("new_value", postgresql.JSONB, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        # Audit columns
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Index for querying modifications by twin
    op.create_index("ix_twin_modifications_twin_id", "twin_modifications", ["twin_id"])
    op.create_index("ix_twin_modifications_type", "twin_modifications", ["modification_type"])


def downgrade() -> None:
    # Drop twin_modifications first (has FK to digital_twins)
    op.drop_index("ix_twin_modifications_type", table_name="twin_modifications")
    op.drop_index("ix_twin_modifications_twin_id", table_name="twin_modifications")
    op.drop_table("twin_modifications")

    op.drop_index("ix_digital_twins_user_chart_status", table_name="digital_twins")
    op.drop_index("ix_digital_twins_status", table_name="digital_twins")
    op.drop_index("ix_digital_twins_chart_id", table_name="digital_twins")
    op.drop_index("ix_digital_twins_user_id", table_name="digital_twins")
    op.drop_table("digital_twins")

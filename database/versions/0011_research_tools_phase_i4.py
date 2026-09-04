"""Add research tools tables for Phase I.4

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-19 00:00:00.000000

Tables added:
  research_mode_settings   — per-user research mode toggle
  research_query_logs      — query/action log for reproducibility
  hypothesis_validations   — hypothesis flagging/confirmation workflow
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── research_mode_settings ──────────────────────────────────────────────
    op.create_table(
        "research_mode_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, unique=True, index=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── research_query_logs ─────────────────────────────────────────────────
    op.create_table(
        "research_query_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("request_payload", sa.Text, nullable=False, server_default="{}"),
        sa.Column("response_summary", sa.String(500), nullable=False, server_default=""),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── hypothesis_validations ──────────────────────────────────────────────
    op.create_table(
        "hypothesis_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("hypothesis_id", sa.String(50), nullable=False, index=True),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("birth_charts.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("title", sa.String(300), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("domain", sa.String(50), nullable=False, server_default=""),
        sa.Column("hypothesis_data", sa.Text, nullable=False, server_default="{}"),
        sa.Column("ai_generated", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("hypothesis_validations")
    op.drop_table("research_query_logs")
    op.drop_table("research_mode_settings")

"""Add event_analyses and event_chart_snapshots tables

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-10 00:00:00.000000

The Event Analysis feature (event chart / muhurta consultation). An
event_analyses row is the aggregate root: it holds event-moment inputs
(subject birth_chart_id, event name/category/datetime/location, selected
analysis scope), lifecycle status, the compact report JSON + overall score,
and REFERENCES (ids) to generated artifact snapshots in
event_chart_snapshots (cast event D1, event-moment transit, active dasha
chain) rather than embedding large chart JSON blobs.

These tables live in models/astrology.py alongside the other chart tables.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── event_analyses (aggregate root) ──────────────────────────────────────
    op.create_table(
        "event_analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "birth_chart_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("birth_charts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_name", sa.String(300), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "event_datetime_utc",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("event_latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("event_longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("place_name", sa.String(300), nullable=True),
        sa.Column("timezone_iana", sa.String(100), nullable=True),
        sa.Column("scope", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("event_chart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transit_chart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dasha_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("analysis_report_json", postgresql.JSONB(), nullable=True),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
    )
    op.create_index("ix_event_analyses_user_id", "event_analyses", ["user_id"])
    op.create_index("ix_event_analyses_birth_chart_id", "event_analyses", ["birth_chart_id"])
    op.create_index("ix_event_analyses_event_datetime_utc", "event_analyses", ["event_datetime_utc"])

    # ── event_chart_snapshots (generated artifact snapshots) ──────────────────
    op.create_table(
        "event_chart_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("birth_chart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_type", sa.String(30), nullable=False),
        sa.Column("label", sa.String(300), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        "ix_event_chart_snapshots_birth_chart_id",
        "event_chart_snapshots",
        ["birth_chart_id"],
    )

    conn = op.get_bind()
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_event_analyses_updated_at
        BEFORE UPDATE ON event_analyses
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_event_chart_snapshots_updated_at
        BEFORE UPDATE ON event_chart_snapshots
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_event_chart_snapshots_updated_at ON event_chart_snapshots"
    ))
    conn.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_event_analyses_updated_at ON event_analyses"
    ))
    op.drop_table("event_chart_snapshots")
    op.drop_table("event_analyses")
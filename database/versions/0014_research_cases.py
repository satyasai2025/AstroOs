"""Add Research Case system tables (Module 27)

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-31 00:00:00.000000

Tables added (event-centric research pipeline):
  research_cases      — one research subject: birth data + research metadata
  life_events         — one recorded life event within a research case
  event_snapshots     — immutable astrological snapshot per event moment (versioned)
  attachments         — files/documents linked to a case or an event

Enums (canonical lowercase backend values, mirroring models/research_case.py):
  research_gender, research_birth_time_confidence, life_event_type,
  life_event_severity, life_event_confidence, attachment_type

Mirrors apps/api/models/research_case.py exactly. AstroBase audit columns
(id UUID gen_random_uuid, created_at/updated_at timestamptz, deleted_at)
are inlined per existing migration convention (see 0013_digital_twin.py).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    """AstroBase audit columns, matching AstroBase's DDL (see models/base.py)."""
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    # ── research_cases ─────────────────────────────────────────────────────
    op.create_table(
        "research_cases",
        *_audit_columns(),
        sa.Column("research_case_id", sa.String(50), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("person_name", sa.String(200), nullable=True),
        sa.Column("gender", sa.Enum("male", "female", "other", name="research_gender"),
                  nullable=False, server_default="other"),
        sa.Column("dob", sa.DateTime(timezone=False), nullable=False),
        sa.Column("tob", sa.String(10), nullable=True),
        sa.Column("place_of_birth", sa.String(300), nullable=False),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("data_source", sa.String(100), nullable=False),
        sa.Column("birth_time_confidence",
                  sa.Enum("high", "medium", "low", name="research_birth_time_confidence"),
                  nullable=False, server_default="medium"),
        sa.Column("ayanamsa", sa.String(50), nullable=False, server_default="lahiri"),
        sa.Column("house_system", sa.String(50), nullable=False, server_default="P"),
        sa.Column("divisional_charts", sa.Text, nullable=True),
        sa.Column("rectified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("rectification_notes", sa.Text, nullable=True),
        sa.Column("research_notes", sa.Text, nullable=True),
        sa.Column("source_batch", sa.String(200), nullable=True),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="passed"),
        sa.Column("import_job_id", sa.String(100), nullable=True),
    )
    op.create_index("ix_research_cases_research_case_id", "research_cases",
                    ["research_case_id"], unique=True)
    op.create_index("ix_research_cases_user_id", "research_cases", ["user_id"])

    # ── life_events ────────────────────────────────────────────────────────
    op.create_table(
        "life_events",
        *_audit_columns(),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_event_id", sa.String(50), nullable=True),
        sa.Column("event_type",
                  sa.Enum(
                      "marriage", "divorce", "promotion", "job_change", "accident",
                      "surgery", "hospitalization", "child_birth", "death_parent",
                      "death_spouse", "foreign_travel", "education", "property",
                      "vehicle", "finance", "business", "political", "spiritual",
                      "awards", "litigation", "health", "other",
                      name="life_event_type",
                  ),
                  nullable=False),
        sa.Column("severity",
                  sa.Enum("major", "moderate", "minor", name="life_event_severity"),
                  nullable=False, server_default="moderate"),
        sa.Column("category", sa.String(100), nullable=False, server_default="Other"),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("confidence",
                  sa.Enum("high", "medium", "low", name="life_event_confidence"),
                  nullable=False, server_default="medium"),
        sa.Column("source", sa.String(100), nullable=False, server_default="self-report"),
        sa.Column("event_date", sa.DateTime(timezone=False), nullable=False),
        sa.Column("event_time", sa.String(10), nullable=True),
        sa.Column("event_place", sa.String(300), nullable=True),
        sa.Column("event_window_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
    )
    op.create_index("ix_life_events_research_case_id", "life_events", ["research_case_id"])
    op.create_index("ix_life_events_event_type", "life_events", ["event_type"])
    op.create_index("ix_life_events_event_date", "life_events", ["event_date"])

    # ── event_snapshots ────────────────────────────────────────────────────
    op.create_table(
        "event_snapshots",
        *_audit_columns(),
        sa.Column("life_event_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("life_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=False), nullable=False),
        sa.Column("snapshot_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("mahadasha", sa.String(20), nullable=True),
        sa.Column("antardasha", sa.String(20), nullable=True),
        sa.Column("pratyantar", sa.String(20), nullable=True),
        sa.Column("transit_features", sa.Text, nullable=True),
        sa.Column("shadbala_values", sa.Text, nullable=True),
        sa.Column("active_yogas", sa.Text, nullable=True),
        sa.Column("varga_activations", sa.Text, nullable=True),
        sa.Column("nakshatra_activations", sa.Text, nullable=True),
        sa.Column("house_lord_statuses", sa.Text, nullable=True),
    )
    op.create_index("ix_event_snapshots_life_event_id", "event_snapshots", ["life_event_id"])

    # ── attachments ────────────────────────────────────────────────────────
    op.create_table(
        "attachments",
        *_audit_columns(),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("life_event_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("life_events.id", ondelete="CASCADE"), nullable=True),
        sa.Column("attachment_type",
                  sa.Enum("certificate", "image", "pdf", "notes", "other",
                          name="attachment_type"),
                  nullable=False, server_default="notes"),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
    )
    op.create_index("ix_attachments_research_case_id", "attachments", ["research_case_id"])
    op.create_index("ix_attachments_life_event_id", "attachments", ["life_event_id"])


def downgrade() -> None:
    # Drop tables in reverse FK dependency order, then the enum types
    op.drop_index("ix_attachments_life_event_id", table_name="attachments")
    op.drop_index("ix_attachments_research_case_id", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_event_snapshots_life_event_id", table_name="event_snapshots")
    op.drop_table("event_snapshots")

    op.drop_index("ix_life_events_event_date", table_name="life_events")
    op.drop_index("ix_life_events_event_type", table_name="life_events")
    op.drop_index("ix_life_events_research_case_id", table_name="life_events")
    op.drop_table("life_events")

    op.drop_index("ix_research_cases_user_id", table_name="research_cases")
    op.drop_index("ix_research_cases_research_case_id", table_name="research_cases")
    op.drop_table("research_cases")

    op.execute("DROP TYPE IF EXISTS attachment_type")
    op.execute("DROP TYPE IF EXISTS life_event_confidence")
    op.execute("DROP TYPE IF EXISTS life_event_severity")
    op.execute("DROP TYPE IF EXISTS life_event_type")
    op.execute("DROP TYPE IF EXISTS research_birth_time_confidence")
    op.execute("DROP TYPE IF EXISTS research_gender")

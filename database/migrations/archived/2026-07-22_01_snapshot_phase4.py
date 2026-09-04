# Alembic migration script: 2026-07-22_01_snapshot_phase4.py
# This file creates the core Phase IV tables for Snapshot, Provenance, and Entity History.
# Place it in database/versions/YYYY-MM-DD_HHMMSS_add_phase4_tables.py

"""
Revised migration for Phase IV snapshot infrastructure
Creates:
  - research_snapshots table
  - provenance_events table
  - entity_history table
  - enum types for event types
"""

from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
import uuid

# revision identifiers
revision = "2026-07-22_01_snapshot_phase4"
down_revision = "2026-07-21_00_initial_schema"
branch_labels = None
depends_on = None

target_metadata = None

def upgrade() -> None:
    # Create ENUM type for provenance events
    event_type_enum = sa.Enum(
        "event_type",
        "rule_created rule_updated rule_deprecated rule_executed rule_matched rule_skipped "
        "case_started case_completed validation_passed validation_failed "
        "snapshot_created snapshot_restored snapshot_deleted citation_added citation_verified "
        "experiment_started experiment_completed knowledge_approved engine_released config_changed "
        "metadata_updated",
        name="event_type_enum",
        create_type=True,
    )
    event_type_enum.create(bind=op.get_bind())

    # -----------------------------------------------------------------
    # 1️⃣  provenance_events table
    # -----------------------------------------------------------------
    op.create_table(
        "provenance_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.Enum(event_type_enum, name="event_type_enum"), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False, server_default=sa.text("'0'*64")),
        sa.Index("idx_provenance_timestamp", "timestamp")
    )

    # -----------------------------------------------------------------
    # 2️⃣  entity_history table
    # -----------------------------------------------------------------
    op.create_table(
        "entity_history",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(as_uuid=True), sa.ForeignKey("provenance_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False, index=True),
        sa.Column("entity_id", sa.String(), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Index("idx_entity_event", "event_id"),
        sa.Index("idx_entity_type_entity_id", "entity_type", "entity_id")
    )

    # -----------------------------------------------------------------
    # 3️⃣  research_snapshots table
    # -----------------------------------------------------------------
    op.create_table(
        "research_snapshots",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("snapshot_uuid", sa.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("research_case_id", sa.String(), nullable=False),
        sa.Column("rule_engine_version", sa.String(), nullable=False),
        sa.Column("knowledge_version", sa.String(), nullable=False),
        sa.Column("ephemeris_version", sa.String(), nullable=False),
        sa.Column("engine_version", sa.String(), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("snapshot_json", pg.JSONB(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.CheckConstraint("length(checksum) = 64", name="ck_checksum_len"),
        sa.Index("idx_snapshot_case", "research_case_id"),
        sa.Index("idx_snapshot_created_at", "created_at")
    )

def downgrade() -> None:
    op.drop_table("research_snapshots")
    op.drop_table("entity_history")
    op.drop_table("provenance_events")
    op.execute("DROP TYPE IF EXISTS event_type_enum")
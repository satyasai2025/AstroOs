"""Add Pattern Discovery persistence tables + research_cases.country (Module 27, Phase 3c)

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-31 00:00:00.000000

Tables added:
  pattern_discovery_runs — one row per /cases/patterns/discover invocation
                           (drives "Recent Significant Patterns" + per-pattern
                           confidence trend + which engine version ran)
  discovered_patterns     — persisted DiscoveredPattern results, upserted by
                           pattern_id on every discovery run

Columns added:
  research_cases.country — nullable free-text country/region field (new
                           imports only; existing rows are NULL, no backfill)

Mirrors apps/api/services/pattern_discovery.py's DiscoveredPattern dataclass
and apps/api/models/pattern.py exactly. AstroBase audit columns are inlined
per existing migration convention (see 0014_research_cases.py). JSON columns
use JSONB (not Text, unlike 0014's snapshot blobs) since pattern dimensions,
supporting/contradicting case IDs, and snapshot versions need to stay
queryable for reproducibility audits.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: Union[str, None] = "0014"
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
    # ── pattern_discovery_runs ────────────────────────────────────────────
    op.create_table(
        "pattern_discovery_runs",
        *_audit_columns(),
        sa.Column("event_type", sa.String(30), nullable=True,
                   comment="LOKPA event type this run targeted; null = all types."),
        sa.Column("total_cases", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_events", sa.Integer, nullable=False, server_default="0"),
        sa.Column("execution_time_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("algorithm_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("feature_version", sa.String(20), nullable=False, server_default="1.0.0"),
    )
    op.create_index("ix_pattern_discovery_runs_created_at", "pattern_discovery_runs", ["created_at"])
    op.create_index("ix_pattern_discovery_runs_event_type", "pattern_discovery_runs", ["event_type"])

    # ── discovered_patterns ────────────────────────────────────────────────
    op.create_table(
        "discovered_patterns",
        *_audit_columns(),
        sa.Column("pattern_id", sa.String(20), nullable=False,
                   comment="Stable sha1-derived ID, e.g. ptn-xxxxxxxxxx."),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("lift_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("dimensions_json", postgresql.JSONB, nullable=False,
                   comment="list[PatternDimension] — dimension/value/frequency/count/expected_by_chance/significance."),
        sa.Column("explanation", sa.Text, nullable=True,
                   comment="AI-generated explanation text; null until POST .../explain is called."),
        sa.Column("explanation_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classical_references_json", postgresql.JSONB, nullable=True,
                   comment="list[str] curated citations matched against this pattern's dimensions."),
        sa.Column("supporting_case_ids_json", postgresql.JSONB, nullable=False,
                   server_default=sa.text("'[]'::jsonb"),
                   comment="research_cases.research_case_id values whose data produced this pattern."),
        sa.Column("contradicting_case_ids_json", postgresql.JSONB, nullable=False,
                   server_default=sa.text("'[]'::jsonb"),
                   comment="Cases exhibiting every dimension/value pair but NOT this event_type."),
        sa.Column("snapshot_versions_json", postgresql.JSONB, nullable=False,
                   server_default=sa.text("'[]'::jsonb"),
                   comment="Distinct event_snapshots.snapshot_version values among supporting cases."),
        sa.Column("algorithm_version", sa.String(20), nullable=False, server_default="1.0.0",
                   comment="apps/api/services/pattern_discovery.py ALGORITHM_VERSION at discovery time."),
        sa.Column("feature_version", sa.String(20), nullable=False, server_default="1.0.0",
                   comment="apps/api/services/feature_extraction.py FEATURE_VERSION at discovery time."),
        sa.Column("discovery_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pattern_discovery_runs.id", ondelete="SET NULL"), nullable=True,
                  comment="Most recent run that (re)computed this pattern."),
    )
    op.create_index("ix_discovered_patterns_pattern_id", "discovered_patterns",
                     ["pattern_id"], unique=True)
    op.create_index("ix_discovered_patterns_event_type", "discovered_patterns", ["event_type"])
    op.create_index("ix_discovered_patterns_confidence_score", "discovered_patterns", ["confidence_score"])
    op.create_index("ix_discovered_patterns_discovery_run_id", "discovered_patterns", ["discovery_run_id"])

    # ── research_cases.country ────────────────────────────────────────────
    op.add_column("research_cases", sa.Column("country", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("research_cases", "country")

    op.drop_index("ix_discovered_patterns_discovery_run_id", table_name="discovered_patterns")
    op.drop_index("ix_discovered_patterns_confidence_score", table_name="discovered_patterns")
    op.drop_index("ix_discovered_patterns_event_type", table_name="discovered_patterns")
    op.drop_index("ix_discovered_patterns_pattern_id", table_name="discovered_patterns")
    op.drop_table("discovered_patterns")

    op.drop_index("ix_pattern_discovery_runs_event_type", table_name="pattern_discovery_runs")
    op.drop_index("ix_pattern_discovery_runs_created_at", table_name="pattern_discovery_runs")
    op.drop_table("pattern_discovery_runs")

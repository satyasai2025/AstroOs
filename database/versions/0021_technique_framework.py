"""Add the generic Technique Intelligence framework tables

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-12 00:00:00.000000

Creates three tables for the domain-agnostic Technique framework:
  techniques                 — versioned, provenance-tracked technique rows
                               (soft-append versioning, superseded_by, per the
                               0008 knowledge-versioning convention).
  technique_sources          — provenance lineage (which sources a technique
                               was extracted from).
  technique_validation_cases — per-rule / per-chart validation records.

The evaluable rules themselves are NOT stored here — they live in the existing
code rule_registry (domain/rules.py); `techniques.definition_json` references
them by rule_id. This deliberately avoids duplicating the Rule Engine / rule
storage.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "techniques",
        *_audit_columns(),
        sa.Column("technique_key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tradition", sa.String(50), nullable=False, server_default=""),
        sa.Column("objective", sa.String(100), nullable=False, server_default=""),
        sa.Column("provenance", sa.String(30), nullable=False, server_default="untested"),
        sa.Column("status", sa.String(20), nullable=False, server_default="research"),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("version_comment", sa.String(500), nullable=True),
        sa.Column(
            "superseded_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("techniques.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("definition_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_techniques_technique_key", "techniques", ["technique_key"])
    op.create_index("ix_techniques_objective", "techniques", ["objective"])
    op.create_index(
        "ix_techniques_key_version", "techniques", ["technique_key", "version"],
    )

    op.create_table(
        "technique_sources",
        *_audit_columns(),
        sa.Column(
            "technique_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("techniques.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("source_type", sa.String(40), nullable=False, server_default=""),
        sa.Column("reference", sa.String(500), nullable=False, server_default=""),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_technique_sources_technique_id", "technique_sources", ["technique_id"],
    )

    op.create_table(
        "technique_validation_cases",
        *_audit_columns(),
        sa.Column(
            "technique_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("techniques.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("rule_id", sa.String(80), nullable=False),
        sa.Column("chart_ref", sa.String(200), nullable=True),
        sa.Column("expected_result", sa.String(200), nullable=False, server_default=""),
        sa.Column("observed_result", sa.String(200), nullable=False, server_default=""),
        sa.Column("match_status", sa.String(20), nullable=False, server_default="untested"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_technique_validation_cases_technique_id",
        "technique_validation_cases", ["technique_id"],
    )
    op.create_index(
        "ix_technique_validation_cases_rule_id",
        "technique_validation_cases", ["rule_id"],
    )


def downgrade() -> None:
    op.drop_table("technique_validation_cases")
    op.drop_table("technique_sources")
    op.drop_index("ix_techniques_key_version", table_name="techniques")
    op.drop_index("ix_techniques_objective", table_name="techniques")
    op.drop_index("ix_techniques_technique_key", table_name="techniques")
    op.drop_table("techniques")

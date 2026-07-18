"""Add dedicated research_experiments and experiment_executions tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-18 00:00:00.000000

Tables added:
  research_experiments    — dedicated experiment table (replacing project-column hack)
  experiment_executions  — links experiments to snapshots with execution order

Previously, ResearchExperiment data was stored in research_projects columns
(hypothesis, methodology, conclusions), limiting one experiment per project.
This migration creates proper standalone tables.

research_experiments:
  id, project_id (FK->research_projects, CASCADE), title, hypothesis,
  methodology, status, findings, rule_registry_hash, dataset_id (FK->datasets),
  created_at, updated_at, deleted_at

experiment_executions:
  id, experiment_id (FK->research_experiments, CASCADE),
  snapshot_id (FK->research_snapshots, SET NULL), execution_order,
  notes, created_at
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── research_experiments ──────────────────────────────────────────────
    op.create_table(
        "research_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("methodology", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default=sa.text("'draft'")),
        sa.Column("findings", sa.Text, nullable=True),
        sa.Column("rule_registry_hash", sa.String(64), nullable=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("datasets.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_experiments_status", "research_experiments", ["status"])
    op.create_index("ix_experiments_project_id", "research_experiments", ["project_id"])

    # Attach updated_at trigger.
    op.execute(sa.text(
        "CREATE TRIGGER trg_research_experiments_updated_at "
        "BEFORE UPDATE ON research_experiments "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    ))

    # ── experiment_executions ─────────────────────────────────────────────
    op.create_table(
        "experiment_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_experiments.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_snapshots.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("execution_order", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_executions_experiment_id",
        "experiment_executions",
        ["experiment_id"],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DROP TRIGGER IF EXISTS trg_research_experiments_updated_at "
                "ON research_experiments")
    )
    op.drop_table("experiment_executions")
    op.drop_table("research_experiments")

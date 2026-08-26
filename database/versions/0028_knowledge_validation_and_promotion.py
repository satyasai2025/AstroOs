"""
0028 — Knowledge Validation & Controlled Promotion tables

New tables:
  - knowledge_validation_records:  governed validation decisions
  - knowledge_validation_audit_log: append-only audit trail

Revises: 0027
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── knowledge_validation_records ───────────────────────────────────────────
    op.create_table(
        "knowledge_validation_records",
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("knowledge_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_item_type", sa.String(20), nullable=False),
        sa.Column("validator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("validator_role", sa.String(50), nullable=False),
        sa.Column("validation_status", sa.String(30), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("source_identity_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("source_provenance_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("tradition_framework_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("passage_reference_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("text_integrity_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("interpretation_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("technique_applicability_verified", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("contradiction_conflict_status_checked", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("technique_framework", sa.String(50), nullable=False,
                  server_default="Parashari"),
        sa.Column("is_cross_technique", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("cross_technique_note", sa.Text(), nullable=False,
                  server_default=""),
        sa.Column("validation_notes", sa.Text(), nullable=False,
                  server_default=""),
        sa.Column("validation_decision", sa.Text(), nullable=False,
                  server_default=""),
        sa.Column("evidence_checks", postgresql.JSONB(), nullable=False,
                  server_default="[]"),
        sa.Column("is_eligible_for_promotion", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("eligible_promotion_targets", postgresql.JSONB(), nullable=False,
                  server_default="[]"),
        sa.Column("preserved_provenance", postgresql.JSONB(), nullable=False,
                  server_default="{}"),
        sa.Column("criteria_score", sa.Float(), nullable=False,
                  server_default="0"),
        sa.PrimaryKeyConstraint("validation_id"),
        sa.CheckConstraint(
            "knowledge_item_type IN ('document', 'chunk')",
            name="ck_validation_item_type",
        ),
        sa.CheckConstraint(
            "validation_status IN ('APPROVED', 'REJECTED', 'NEEDS_REVISION')",
            name="ck_validation_status",
        ),
        sa.UniqueConstraint(
            "knowledge_item_id", "knowledge_item_type",
            name="uq_validation_record_item",
        ),
    )
    op.create_index(
        "ix_validation_status",
        "knowledge_validation_records", ["validation_status"],
    )
    op.create_index(
        "ix_validation_technique",
        "knowledge_validation_records", ["technique_framework"],
    )
    op.create_index(
        "ix_validation_validator",
        "knowledge_validation_records", ["validator_id"],
    )

    # ── knowledge_validation_audit_log ────────────────────────────────────────
    op.create_table(
        "knowledge_validation_audit_log",
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("validation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_role", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("previous_state", sa.String(30), nullable=False,
                  server_default=""),
        sa.Column("new_state", sa.String(30), nullable=False,
                  server_default=""),
        sa.Column("reason", sa.Text(), nullable=False,
                  server_default=""),
        sa.Column("source_reference", sa.String(500), nullable=False,
                  server_default=""),
        sa.Column("metadata", postgresql.JSONB(), nullable=False,
                  server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
        sa.ForeignKeyConstraint(
            ["validation_id"],
            ["knowledge_validation_records.validation_id"],
            ondelete="CASCADE",
            name="fk_audit_validation_id",
        ),
    )
    op.create_index(
        "ix_audit_validation_id",
        "knowledge_validation_audit_log", ["validation_id"],
    )
    op.create_index(
        "ix_audit_actor",
        "knowledge_validation_audit_log", ["actor_id"],
    )
    op.create_index(
        "ix_audit_timestamp",
        "knowledge_validation_audit_log", ["timestamp"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_validation_audit_log")
    op.drop_table("knowledge_validation_records")
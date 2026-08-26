"""
0027 — Knowledge Ingestion & Reliability tables

New tables (matching existing ORM models exactly):
  ingested_documents
  ingested_chunks
  knowledge_source_reliabilities
  knowledge_rule_reliabilities
  knowledge_evidence_families
  knowledge_empirical_conflicts
  knowledge_validation_policies

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ingested_documents ───────────────────────────────────────────────────
    op.create_table(
        "ingested_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(300), nullable=True),
        sa.Column("edition", sa.String(300), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(50), nullable=False,
                  server_default="Sanskrit/English"),
        sa.Column("tradition", sa.String(100), nullable=True),
        sa.Column("content_hash_sha256", sa.String(64), nullable=True),
        sa.Column("status", sa.String(30), nullable=False,
                  server_default="RAW_UPLOADED"),
        sa.Column("doc_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("title", "edition",
                            name="uq_ingested_documents_title_edition"),
    )
    op.create_index("ix_ingested_documents_book_id",
                    "ingested_documents", ["book_id"])
    op.create_index("ix_ingested_documents_source_id",
                    "ingested_documents", ["source_id"])

    # ── ingested_chunks ──────────────────────────────────────────────────────
    op.create_table(
        "ingested_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chunk_id", sa.String(200), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("chapter_section", sa.String(500), nullable=False),
        sa.Column("page_location", sa.String(200), nullable=False),
        sa.Column("passage_reference", sa.String(500), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash_sha256", sa.String(64), nullable=False),
        sa.Column("technique_framework", sa.String(50), nullable=False,
                  server_default="Parashari"),
        sa.Column("lifecycle_state", sa.String(30), nullable=False,
                  server_default="DOCUMENTED"),
        sa.Column("evidence_level", sa.String(30), nullable=False,
                  server_default="UNVALIDATED"),
        sa.Column("evidence_family_id", sa.String(200), nullable=True),
        sa.Column("grahas", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("bhavas", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("rashis", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("nakshatras", postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column("yogas", postgresql.ARRAY(sa.String(200)), nullable=True),
        sa.Column("event_types", postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column("is_ai_extracted", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("extraction_metadata",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_model", sa.String(200), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.UniqueConstraint("chunk_id", name="uq_ingested_chunks_chunk_id"),
    )
    op.create_index("ix_ingested_chunks_document_id",
                    "ingested_chunks", ["document_id"])
    op.create_index("ix_ingested_chunks_source_id",
                    "ingested_chunks", ["source_id"])
    op.create_index("ix_ingested_chunks_technique_lifecycle",
                    "ingested_chunks", ["technique_framework", "lifecycle_state"])
    op.create_index("ix_ingested_chunks_evidence_level",
                    "ingested_chunks", ["evidence_level"])
    op.create_index("ix_ingested_chunks_grahas_gin",
                    "ingested_chunks", ["grahas"], postgresql_using="gin")
    op.create_index("ix_ingested_chunks_bhavas_gin",
                    "ingested_chunks", ["bhavas"], postgresql_using="gin")
    op.create_index("ix_ingested_chunks_search_vector_gin",
                    "ingested_chunks", ["search_vector"], postgresql_using="gin")

    # ── knowledge_source_reliabilities ───────────────────────────────────────
    # source_id is UUID here matching the ORM model
    op.create_table(
        "knowledge_source_reliabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False,
                  unique=True),
        sa.Column("source_name", sa.String(300), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False,
                  server_default="UNAUTHENTICATED"),
        sa.Column("provenance_json",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("scholarly_eval_json",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("review_status", sa.String(50), nullable=False,
                  server_default="UNREVIEWED"),
        sa.Column("empirical_citations",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("known_failures_or_contradictions",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("audit_log",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
    )
    op.create_index("ix_knowledge_source_reliabilities_source_id",
                    "knowledge_source_reliabilities", ["source_id"])

    # ── knowledge_rule_reliabilities ─────────────────────────────────────────
    op.create_table(
        "knowledge_rule_reliabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rule_id", sa.String(100), nullable=False, unique=True),
        sa.Column("rule_name", sa.String(300), nullable=False),
        sa.Column("technique_framework", sa.String(50), nullable=False,
                  server_default="Parashari"),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_family_id", sa.String(100), nullable=True),
        sa.Column("lifecycle_state", sa.String(30), nullable=False,
                  server_default="DOCUMENTED"),
        sa.Column("evidence_level", sa.String(30), nullable=False,
                  server_default="UNVALIDATED"),
        sa.Column("provenance_json",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'{}'")),
        sa.Column("validation_summary_json",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("conflict_ids",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("review_history",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("canonical_signoff_by", sa.String(100), nullable=True),
        sa.Column("canonical_signoff_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_knowledge_rule_reliabilities_rule_id",
                    "knowledge_rule_reliabilities", ["rule_id"])
    op.create_index("ix_knowledge_rule_reliabilities_source_id",
                    "knowledge_rule_reliabilities", ["source_id"])
    op.create_index("ix_knowledge_rule_reliabilities_lifecycle",
                    "knowledge_rule_reliabilities", ["lifecycle_state"])
    op.create_index("ix_knowledge_rule_reliabilities_evidence",
                    "knowledge_rule_reliabilities", ["evidence_level"])
    op.create_index("ix_knowledge_rule_reliabilities_family",
                    "knowledge_rule_reliabilities", ["evidence_family_id"])

    # ── knowledge_evidence_families ──────────────────────────────────────────
    op.create_table(
        "knowledge_evidence_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("family_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("underlying_principle", sa.Text(), nullable=False),
        sa.Column("tradition", sa.String(50), nullable=False),
        sa.Column("member_rule_ids",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("max_independent_dof", sa.Integer(), nullable=False,
                  server_default="1"),
    )
    op.create_index("ix_knowledge_evidence_families_family_id",
                    "knowledge_evidence_families", ["family_id"])

    # ── knowledge_empirical_conflicts ─────────────────────────────────────────
    op.create_table(
        "knowledge_empirical_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conflict_id", sa.String(100), nullable=False, unique=True),
        sa.Column("topic", sa.String(300), nullable=False),
        sa.Column("technique_framework", sa.String(50), nullable=False),
        sa.Column("supporting_sources",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("contradicting_sources",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("empirical_findings",
                  postgresql.JSONB(astext_type=sa.Text()), nullable=False,
                  server_default=sa.text("'[]'")),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default="ACTIVE_DISPUTE"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_knowledge_empirical_conflicts_conflict_id",
                    "knowledge_empirical_conflicts", ["conflict_id"])

    # ── knowledge_validation_policies ────────────────────────────────────────
    op.create_table(
        "knowledge_validation_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("policy_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("min_applicable_cases", sa.Integer(), nullable=False,
                  server_default="30"),
        sa.Column("min_holdout_cases", sa.Integer(), nullable=False,
                  server_default="100"),
        sa.Column("min_hit_rate", sa.Float(), nullable=False,
                  server_default="0.6"),
        sa.Column("max_brier_score", sa.Float(), nullable=False,
                  server_default="0.25"),
        sa.Column("max_counterexample_ratio", sa.Float(), nullable=False,
                  server_default="0.15"),
        sa.Column("require_independent_replication", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.Column("require_holdout_split", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
    )
    op.create_index("ix_knowledge_validation_policies_policy_id",
                    "knowledge_validation_policies", ["policy_id"])


def downgrade() -> None:
    op.drop_table("knowledge_validation_policies")
    op.drop_table("knowledge_empirical_conflicts")
    op.drop_table("knowledge_evidence_families")
    op.drop_table("knowledge_rule_reliabilities")
    op.drop_table("knowledge_source_reliabilities")
    op.drop_index("ix_ingested_chunks_search_vector_gin", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_bhavas_gin", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_grahas_gin", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_evidence_level", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_technique_lifecycle", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_source_id", "ingested_chunks")
    op.drop_index("ix_ingested_chunks_document_id", "ingested_chunks")
    op.drop_table("ingested_chunks")
    op.drop_index("ix_ingested_documents_source_id", "ingested_documents")
    op.drop_index("ix_ingested_documents_book_id", "ingested_documents")
    op.drop_table("ingested_documents")

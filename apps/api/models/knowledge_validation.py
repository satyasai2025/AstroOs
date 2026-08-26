"""
AstroOS — Knowledge Validation ORM Models

SQLAlchemy mapped models for governed validation decisions:
- knowledge_validation_records: the primary validation decisions
- knowledge_validation_audit_log: append-only audit trail

Lifecycle invariant:
  - Ephemeral validation state stored here, NOT in ingested_chunks/ingested_documents
  - The authoritative state is determined by querying this table + existing lifecycle

Anti-contamination invariant:
  - This table records WHO validated, WHAT they decided, WHY
  - It never auto-promotes — promotion requires a separate explicit gate
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class KnowledgeValidationRecord(AstroBase):
    """
    Governed validation decision for a knowledge item.

    Each record represents one validation event for one document or chunk.
    The latest validation record determines the item's validation status.
    """
    __tablename__ = "knowledge_validation_records"
    __table_args__ = (
        UniqueConstraint(
            "knowledge_item_id", "knowledge_item_type",
            name="uq_validation_record_item",
        ),
        Index("ix_validation_status", "validation_status"),
        Index("ix_technique_framework", "technique_framework"),
        Index("ix_validator_id", "validator_id"),
    )

    # Override AstroBase.id since table uses validation_id as primary key
    id = None

    # ── Core identity ─────────────────────────────────────────────────────
    validation_id: Mapped[uuid.UUID] = mapped_column(
        "validation_id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
        comment="Primary key for this validation record.",
    )

    knowledge_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="References the ingested_documents or ingested_chunks ID.",
    )

    knowledge_item_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Either 'document' or 'chunk'.",
    )

    # ── Validator identity ────────────────────────────────────────────────
    validator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="References the validator/actor performing this validation.",
    )

    validator_role: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Role of the validator at time of validation (e.g., 'validator', 'reviewer').",
    )

    # ── Validation outcome ────────────────────────────────────────────────
    validation_status: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="APPROVED, REJECTED, or NEEDS_REVISION.",
    )

    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="When the validation decision was made.",
    )

    # ── Criteria assessments ──────────────────────────────────────
    source_identity_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_provenance_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tradition_framework_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    passage_reference_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    text_integrity_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    interpretation_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    technique_applicability_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contradiction_conflict_status_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Technique classification ───────────────────────────────────────────
    technique_framework: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Parashari",
        comment="Applicable technique framework for this item.",
    )

    is_cross_technique: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cross_technique_note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Decision content ──────────────────────────────────────────────────
    validation_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    validation_decision: Mapped[str] = mapped_column(Text, nullable=False, default="")

    evidence_checks: Mapped[List[Any]] = mapped_column(
        JSONB, nullable=False, default=list,
        comment="Detailed per-criterion evidence records.",
    )

    # ── Promotability ──────────────────────────────────────────────────────
    is_eligible_for_promotion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    eligible_promotion_targets: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, default=list,
    )

    # ── Provenance preservation (never removed) ────────────────────────────
    preserved_provenance: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Frozen provenance snapshot — write-once, append-only.",
    )

    # ── Documented validation criteria summary ─────────────────────────────
    criteria_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="0.0-1.0 weighted criteria pass score.",
    )


class KnowledgeValidationAuditLog(AstroBase):
    """
    Append-only audit trail for all validation and promotion events.

    One row per event. IMMUTABLE after creation (no update endpoint).
    """
    __tablename__ = "knowledge_validation_audit_log"
    __table_args__ = (
        Index("ix_audit_validation_id", "validation_id"),
        Index("ix_audit_actor", "actor_id"),
        Index("ix_audit_timestamp", "timestamp"),
    )

    # Override AstroBase.id since table uses audit_id as primary key
    id = None

    audit_id: Mapped[uuid.UUID] = mapped_column(
        "audit_id",
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    validation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_validation_records.validation_id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the associated validation record.",
    )

    # ── Actor ──────────────────────────────────────────────────────────────
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Who performed the action.",
    )

    actor_role: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Role of the actor at time of action.",
    )

    # ── Action details ─────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g. validate, reject, promote, rollback.",
    )

    previous_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="",
    )

    new_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="",
    )

    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    source_reference: Mapped[str] = mapped_column(
        String(500), nullable=False, default="",
    )

    audit_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional structured data for the audit entry.",
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __init__(self, **kwargs: Any) -> None:
        if "metadata" in kwargs:
            kwargs["audit_metadata"] = kwargs.pop("metadata")
        super().__init__(**kwargs)
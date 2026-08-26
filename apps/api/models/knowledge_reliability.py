"""
AstroOS — Knowledge Reliability ORM Models

SQLAlchemy mapped models for:
- knowledge_source_reliabilities
- knowledge_rule_reliabilities
- knowledge_evidence_families
- knowledge_empirical_conflicts
- knowledge_validation_policies

All transactional tables inherit from AstroBase (UUID pk + audit timestamps).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class KnowledgeSourceReliabilityModel(AstroBase):
    """Multidimensional reliability metadata for a source text."""

    __tablename__ = "knowledge_source_reliabilities"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        doc="References the underlying book or source entity",
    )
    source_name: Mapped[str] = mapped_column(String(300), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNAUTHENTICATED"
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    scholarly_eval_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    review_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNREVIEWED"
    )
    empirical_citations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    known_failures_or_contradictions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    audit_log: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )


class KnowledgeRuleReliabilityModel(AstroBase):
    """Reliability, lifecycle state, provenance, and empirical validation status for a rule."""

    __tablename__ = "knowledge_rule_reliabilities"

    rule_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    rule_name: Mapped[str] = mapped_column(String(300), nullable=False)
    technique_framework: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Parashari"
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    evidence_family_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    lifecycle_state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="DOCUMENTED", index=True
    )
    evidence_level: Mapped[str] = mapped_column(
        String(30), nullable=False, default="UNVALIDATED", index=True
    )
    provenance_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    validation_summary_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    conflict_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    review_history: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    canonical_signoff_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    canonical_signoff_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class KnowledgeEvidenceFamilyModel(AstroBase):
    """Evidence family grouping derivative rules sharing the same root principle."""

    __tablename__ = "knowledge_evidence_families"

    family_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    underlying_principle: Mapped[str] = mapped_column(Text, nullable=False)
    tradition: Mapped[str] = mapped_column(String(50), nullable=False)
    member_rule_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    max_independent_dof: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )


class KnowledgeEmpiricalConflictModel(AstroBase):
    """Preserved doctrinal or empirical conflicts between sources/traditions."""

    __tablename__ = "knowledge_empirical_conflicts"

    conflict_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    technique_framework: Mapped[str] = mapped_column(String(50), nullable=False)
    supporting_sources: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    contradicting_sources: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    empirical_findings: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE_DISPUTE"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class KnowledgeValidationPolicyModel(AstroBase):
    """Configurable governance policies for empirical validation."""

    __tablename__ = "knowledge_validation_policies"

    policy_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    min_applicable_cases: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    min_holdout_cases: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100
    )
    min_hit_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.60)
    max_brier_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.25
    )
    max_counterexample_ratio: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.15
    )
    require_independent_replication: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    require_holdout_split: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

"""
AstroOS — Knowledge Reliability Domain Models

Defines domain contracts, multidimensional source reliability evaluations,
strict rule lifecycle state machines, traceable provenance chains,
anti-double-counting evidence families, conflict preservation structures,
and configurable validation policies.

Pure Python dataclasses — no ORM or framework dependencies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class SourceReliabilityTier(str, Enum):
    AUTHENTICATED_CLASSICAL = "AUTHENTICATED_CLASSICAL"
    SCHOLARLY_COMMENTARY = "SCHOLARLY_COMMENTARY"
    CONTEMPORARY_EMPIRICAL = "CONTEMPORARY_EMPIRICAL"
    INFORMAL_TRADITION = "INFORMAL_TRADITION"
    UNAUTHENTICATED = "UNAUTHENTICATED"


class ReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PEER_REVIEWED = "PEER_REVIEWED"
    DISPUTED = "DISPUTED"
    RETRACTED = "RETRACTED"


class EvidenceLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNVALIDATED = "UNVALIDATED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TechniqueFramework(str, Enum):
    PARASHARI = "Parashari"
    JAIMINI = "Jaimini"
    BHRIGU_NADI = "Bhrigu Nadi"
    KP_SYSTEM = "KP System"
    PRASHNA = "Prashna"
    RASHI_SUTRA = "Rashi Sutra"
    TAJIKA = "Tajika"
    CUSTOM = "Custom"


class RuleLifecycleState(str, Enum):
    UNKNOWN = "UNKNOWN"
    DOCUMENTED = "DOCUMENTED"
    UNVALIDATED = "UNVALIDATED"
    REVIEWED = "REVIEWED"
    VALIDATED = "VALIDATED"
    PROMOTED = "PROMOTED"
    CANONICAL = "CANONICAL"
    CONTRADICTED = "CONTRADICTED"

# ── Authoritative transition rules (governed, NOT automatic) ──────────────────
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "UNKNOWN": ["DOCUMENTED"],
    "DOCUMENTED": ["UNVALIDATED"],
    "UNVALIDATED": ["VALIDATED", "REJECTED"],
    "REJECTED": ["UNVALIDATED"],
    "VALIDATED": ["PROMOTED", "CONTRADICTED"],
    "PROMOTED": ["REVIEWED"],
    "REVIEWED": ["VALIDATED", "CONTRADICTED"],
    "CONTRADICTED": ["DOCUMENTED"],
    "CANONICAL": ["CONTRADICTED"],
}

# Only VALIDATED items may be promoted. No other state → PROMOTED allowed.
EXPECTED_PRE_PROMOTION_STATES: List[str] = ["VALIDATED"]


class ActorRole(str, Enum):
    AI_AGENT = "AI_AGENT"
    HUMAN_CURATOR = "HUMAN_CURATOR"
    HUMAN_EXPERT = "HUMAN_EXPERT"
    RESEARCH_ENGINE = "RESEARCH_ENGINE"
    GOVERNANCE_ADMIN = "GOVERNANCE_ADMIN"


class ConflictPreservationStatus(str, Enum):
    ACTIVE_DISPUTE = "ACTIVE_DISPUTE"
    DOCUMENTED_DIVERGENCE = "DOCUMENTED_DIVERGENCE"
    HISTORICAL_SCHISM = "HISTORICAL_SCHISM"


# ── Exceptions ────────────────────────────────────────────────────────────────

class KnowledgeReliabilityError(Exception):
    """Base exception for Knowledge Reliability Framework errors."""


class UnauthorizedLifecycleTransitionError(KnowledgeReliabilityError):
    """Raised when an actor lacks permission to trigger a lifecycle transition (e.g. AI attempting promotion to VALIDATED/CANONICAL)."""


class InvalidLifecycleTransitionError(KnowledgeReliabilityError):
    """Raised when an illegal lifecycle state transition is attempted."""


class ProvenanceIntegrityError(KnowledgeReliabilityError):
    """Raised when provenance information is incomplete or invalid."""


class ValidationPolicyViolationError(KnowledgeReliabilityError):
    """Raised when validation evidence fails to satisfy the specified ValidationPolicy."""


class TechniqueIsolationError(KnowledgeReliabilityError):
    """Raised when rules from incompatible technique frameworks are evaluated together without a registered adapter."""


# ── Domain Dataclasses ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceProvenance:
    """Bibliographic lineage and publication pedigree of an astrological source."""
    edition_title: str
    publisher: str
    publication_year: Optional[int] = None
    editor_or_translator: Optional[str] = None
    manuscript_lineage: Optional[str] = None
    is_critical_edition: bool = False


@dataclass(frozen=True)
class ScholarlyEvaluation:
    """Scholarly methodology and textual consistency assessment."""
    tradition: str
    methodology_clarity_notes: str = ""
    primary_commentaries: tuple[str, ...] = field(default_factory=tuple)
    known_disputed_passages: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SourceReliabilityRecord:
    """
    Multidimensional assessment of a knowledge source.
    Deliberately does NOT produce a single arbitrary truth score.
    """
    source_id: uuid.UUID
    source_name: str
    tier: SourceReliabilityTier
    provenance: SourceProvenance
    scholarly_eval: ScholarlyEvaluation
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED
    empirical_citations: tuple[str, ...] = field(default_factory=tuple)
    known_failures_or_contradictions: tuple[str, ...] = field(default_factory=tuple)
    audit_log: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RuleProvenanceChain:
    """
    Exact traceable lineage of an extracted rule:
    Source -> Passage -> Original Text -> Extraction Actor -> Rule Definition ID
    """
    source_id: uuid.UUID
    passage_reference: str
    original_text_excerpt: str
    extraction_method: str  # e.g., "AI_ASSISTED_EXTRACTION", "MANUAL_SCHOLARLY_TRANSCRIPTION"
    extracted_by_actor_id: str
    extracted_by_role: ActorRole
    rule_definition_id: str
    source_name: Optional[str] = None
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ValidationPolicy:
    """
    Configurable governance policy for validating rules empirically.
    Decoupled from hardcoded magic numbers.
    """
    policy_id: str
    name: str
    min_applicable_cases: int = 30
    min_holdout_cases: int = 100
    min_hit_rate: float = 0.60
    max_brier_score: float = 0.25
    max_counterexample_ratio: float = 0.15
    require_independent_replication: bool = True
    require_holdout_split: bool = True


@dataclass(frozen=True)
class RuleValidationSummary:
    """Empirical performance summary of a rule evaluated on research cases."""
    rule_id: str
    policy_id: str
    cases_tested: int
    applicable_cases: int
    supported_outcomes: int
    unsupported_outcomes: int
    indeterminate_cases: int
    counterexamples: tuple[str, ...] = field(default_factory=tuple)
    empirical_hit_rate: float = 0.0
    brier_score: Optional[float] = None
    dataset_id: str = ""
    dataset_version: str = "1.0.0"
    benchmark_experiment_id: Optional[str] = None
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validated_by_actor_id: str = "SYSTEM"


@dataclass(frozen=True)
class EvidenceFamily:
    """
    Groups derivative rules sharing the same root astrological principle
    to prevent double-counting in downstream reasoning.
    """
    family_id: str
    name: str
    underlying_principle: str
    tradition: TechniqueFramework
    member_rule_ids: tuple[str, ...] = field(default_factory=tuple)
    max_independent_dof: int = 1  # Maximum independent degrees of freedom


@dataclass(frozen=True)
class EmpiricalConflictRecord:
    """
    Preserves doctrinal or empirical conflicts across sources or traditions
    without resolving via majority voting or score averaging.
    """
    conflict_id: str
    topic: str
    technique_framework: TechniqueFramework
    supporting_sources: tuple[str, ...]
    contradicting_sources: tuple[str, ...]
    empirical_findings: tuple[str, ...] = field(default_factory=tuple)
    status: ConflictPreservationStatus = ConflictPreservationStatus.ACTIVE_DISPUTE
    notes: str = ""


@dataclass(frozen=True)
class RuleReliabilityRecord:
    """
    Complete reliability and lifecycle record for an astrological rule.
    Separates rule empirical validity from source prestige.
    """
    rule_id: str
    rule_name: str
    technique_framework: TechniqueFramework
    provenance: RuleProvenanceChain
    evidence_family_id: Optional[str] = None
    lifecycle_state: RuleLifecycleState = RuleLifecycleState.DOCUMENTED
    evidence_level: EvidenceLevel = EvidenceLevel.UNVALIDATED
    validation_summary: Optional[RuleValidationSummary] = None
    conflict_ids: tuple[str, ...] = field(default_factory=tuple)
    review_history: tuple[str, ...] = field(default_factory=tuple)
    canonical_signoff_by: Optional[str] = None
    canonical_signoff_at: Optional[datetime] = None

"""
AstroOS — Research Evidence Intake & Real-World Outcome Registry Domain Models (Priority 32)

Defines domain dataclasses, enums, verification hierarchies, append-only audit events,
and mandatory epistemic/health disclosures for real-world outcome observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.research_forensics import EvidenceOrigin

MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE = (
    "EVIDENCE_REGISTRY_DISCLOSURE: This registry records observed events and their "
    "verification provenance. An observed event does not establish astrological causation, "
    "predictive validity, or a physical mechanism."
)

MANDATORY_HEALTH_SAFETY_DISCLOSURE = (
    "HEALTH_SAFETY_DISCLOSURE: Health-related astrology is strictly an empirical inquiry "
    "into traditional vitality typologies and must NEVER be used for medical diagnosis, "
    "clinical prediction, treatment planning, or medical decision-making."
)

MANDATORY_EVIDENCE_DISTINCTION_DISCLOSURE = (
    "EVIDENCE_DISTINCTION_DISCLOSURE: Verified real-world evidence is distinguished from "
    "synthetic, simulated, classical-reference, and derived computational evidence."
)

PROHIBITED_HEALTH_CLINICAL_TERMS = (
    "disease prediction",
    "clinical outcome",
    "diagnosis",
    "treatment",
    "medical prognosis",
)


class OutcomeVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SELF_REPORTED = "SELF_REPORTED"
    DOCUMENTARY_VERIFIED = "DOCUMENTARY_VERIFIED"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    REJECTED = "REJECTED"


class TimestampPrecision(str, Enum):
    EXACT = "EXACT"
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class EvidenceSourceType(str, Enum):
    PARTICIPANT_SELF_REPORT = "PARTICIPANT_SELF_REPORT"
    PARTICIPANT_DOCUMENT = "PARTICIPANT_DOCUMENT"
    INDEPENDENT_DOCUMENT = "INDEPENDENT_DOCUMENT"
    AUTHORIZED_RESEARCHER_ENTRY = "AUTHORIZED_RESEARCHER_ENTRY"
    STRUCTURED_EXTERNAL_RECORD = "STRUCTURED_EXTERNAL_RECORD"
    OTHER_VERIFIED_SOURCE = "OTHER_VERIFIED_SOURCE"


class ControlledResearchDomain(str, Enum):
    MARRIAGE = "MARRIAGE"
    CAREER = "CAREER"
    WEALTH_FINANCE = "WEALTH_FINANCE"
    HEALTH_VITALITY = "HEALTH_VITALITY"
    EDUCATION = "EDUCATION"
    RELOCATION = "RELOCATION"
    FAMILY = "FAMILY"
    OTHER = "OTHER"


class ConsentStatus(str, Enum):
    NOT_RECORDED = "NOT_RECORDED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CONSENT_WITHDRAWN = "CONSENT_WITHDRAWN"


class AuditEventOperation(str, Enum):
    CREATED = "CREATED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    CORRECTED = "CORRECTED"
    SUPERSEDED = "SUPERSEDED"
    LINKED_TO_EXPERIMENT = "LINKED_TO_EXPERIMENT"


@dataclass(frozen=True)
class ObservedOutcomeRecord:
    """An individual governed, real-world outcome observation record."""
    outcome_id: str
    subject_reference: str                  # Pseudonymous subject identifier (e.g., "subj-anon-8821")
    domain: ControlledResearchDomain
    event_type: str                         # e.g., "MARRIAGE_VERIFIED_DATE", "CAREER_PROMOTION"
    event_description: str
    event_date: str                         # ISO format YYYY-MM-DD
    event_time: Optional[str]               # HH:MM:SS if available
    event_timezone: str
    timestamp_precision: TimestampPrecision
    observation_source_type: EvidenceSourceType
    evidence_origin: EvidenceOrigin         # Must be OBSERVED_REAL_WORLD_EVIDENCE for primary records
    verification_status: OutcomeVerificationStatus
    verification_method: str
    verifier_reference: str
    evidence_hash: str                      # Canonical SHA-256 hash of observation payload
    source_hash: str                        # Cryptographic digest of anonymized supporting source
    created_at: datetime
    updated_at: datetime
    prospective_rule_id: Optional[str] = None
    experiment_id: Optional[str] = None
    p11_snapshot_id: Optional[str] = None
    provenance_parent: Optional[str] = None
    consent_status: ConsentStatus = ConsentStatus.CONSENT_GRANTED
    privacy_classification: str = "PSEUDONYMOUS_RESEARCH_DATA"
    notes: str = ""
    non_causal_disclosure: str = MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE


@dataclass(frozen=True)
class EvidenceAuditEvent:
    """An immutable, append-only audit log entry for evidence mutations."""
    audit_event_id: str
    outcome_id: str
    operation: AuditEventOperation
    previous_hash: Optional[str]
    new_hash: str
    actor_type: str                         # e.g., "RESEARCHER", "VERIFIER", "SYSTEM"
    timestamp: datetime
    reason: str
    p11_snapshot_id: Optional[str] = None


@dataclass(frozen=True)
class EvidenceRegistrySnapshot:
    """Immutable, deterministic snapshot of the evidence registry state."""
    snapshot_id: str
    record_count: int
    verified_record_count: int
    rejected_record_count: int
    unverified_record_count: int
    source_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    timestamp_precision_distribution: Dict[str, int]
    canonical_payload_hash: str             # SHA-256 of canonical snapshot contents
    p11_parent_snapshot: Optional[str]
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_EVIDENCE_REGISTRY_NON_CAUSAL_DISCLOSURE
    health_safety_disclosure: str = MANDATORY_HEALTH_SAFETY_DISCLOSURE

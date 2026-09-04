"""
AstroOS — Research Publication & Cryptographic Audit Report Domain Models (Priority 30)

Defines domain dataclasses for:
  - Publication-ready research reports with complete methodology → data → formulas → results → audit
  - Cryptographic audit chain anchored to P11 snapshot DAG lineage
  - Non-causal epistemic language enforcement throughout
  - Mandatory reproducibility declarations and provenance seals
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


MANDATORY_PUBLICATION_NON_CAUSAL_DECLARATION = (
    "PUBLICATION_EPISTEMIC_DECLARATION: All findings in this report represent "
    "observed statistical associations in historical astrological data. No causal "
    "claims are made or implied. Results do not constitute medical, financial, or "
    "legal advice. Replication by independent researchers using the disclosed "
    "methodology is encouraged."
)


class PublicationStatus(str, Enum):
    DRAFT = "DRAFT"
    PEER_REVIEW_READY = "PEER_REVIEW_READY"
    PUBLISHED = "PUBLISHED"
    RETRACTED = "RETRACTED"


class ReportSectionType(str, Enum):
    ABSTRACT = "ABSTRACT"
    METHODOLOGY = "METHODOLOGY"
    DATA_GOVERNANCE = "DATA_GOVERNANCE"
    HYPOTHESIS_REGISTRY = "HYPOTHESIS_REGISTRY"
    STATISTICAL_FORMULAS = "STATISTICAL_FORMULAS"
    RESULTS = "RESULTS"
    REPRODUCIBILITY_AUDIT = "REPRODUCIBILITY_AUDIT"
    EPISTEMIC_LIMITATIONS = "EPISTEMIC_LIMITATIONS"
    CRYPTOGRAPHIC_SEAL = "CRYPTOGRAPHIC_SEAL"


@dataclass(frozen=True)
class ReportSection:
    """A single numbered section within the research publication report."""
    section_id: str
    section_type: ReportSectionType
    title: str
    content: str
    source_priority_refs: Tuple[str, ...]   # e.g. ("P15", "P19", "P22")
    is_non_causal_compliant: bool


@dataclass(frozen=True)
class CryptographicAuditEntry:
    """An immutable entry in the publication's cryptographic audit chain."""
    entry_id: str
    priority_ref: str                       # e.g. "P11", "P19"
    snapshot_id: str
    sha256_hash: str
    description: str
    recorded_at: datetime


@dataclass(frozen=True)
class ResearchPublicationReport:
    """
    A complete, reproducible, publication-grade research report.
    """
    report_id: str
    title: str
    target_objective: str
    status: PublicationStatus
    sections: Tuple[ReportSection, ...]
    cryptographic_audit_chain: Tuple[CryptographicAuditEntry, ...]
    p11_root_snapshot_id: str
    report_sha256_seal: str
    publication_non_causal_declaration: str
    total_pipeline_stages_covered: int      # should be 29 (P1→P29)
    generated_at: datetime

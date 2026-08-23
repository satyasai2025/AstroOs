"""
AstroOS — Research Forensic & Evidence Reconstruction Domain Models (Priority 31)

Defines domain dataclasses, enums, and mandatory epistemic disclosures for:
  - Independent forensic reconstruction of P1→P30 research results
  - Strict evidence origin classification (Observed Real-World vs Synthetic/Generated)
  - Provenance chain verification anchored to P11 snapshot DAG and P30 publication seal
  - Deterministic calculation replay and numerical/structural drift diagnosis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


MANDATORY_FORENSIC_NON_CAUSAL_DISCLOSURE = (
    "FORENSIC_EPISTEMIC_DISCLOSURE: Forensic reconstruction verifies computational "
    "reproducibility, evidence integrity, provenance continuity, and statistical "
    "consistency. It does not establish physical causation or mechanistic truth."
)

MANDATORY_SYNTHETIC_EPISTEMIC_DISCLOSURE = (
    "SYNTHETIC_DATA_DISCLOSURE: Synthetic or generated datasets are not equivalent "
    "to observed real-world evidence. Upstream evidence generated via probabilistic "
    "distribution models (e.g. rng.gauss) is strictly labeled SYNTHETIC_GENERATED_EVIDENCE."
)


class ForensicVerdict(str, Enum):
    FORENSICALLY_INTACT = "FORENSICALLY_INTACT"
    RECONSTRUCTED_WITH_ZERO_DRIFT = "RECONSTRUCTED_WITH_ZERO_DRIFT"
    MODIFIED_EVIDENCE_DETECTED = "MODIFIED_EVIDENCE_DETECTED"
    CALCULATION_DRIFT_DETECTED = "CALCULATION_DRIFT_DETECTED"
    PROVENANCE_BREAK = "PROVENANCE_BREAK"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    RECONSTRUCTION_FAILED = "RECONSTRUCTION_FAILED"


class EvidenceOrigin(str, Enum):
    OBSERVED_REAL_WORLD_EVIDENCE = "OBSERVED_REAL_WORLD_EVIDENCE"
    SYNTHETIC_GENERATED_EVIDENCE = "SYNTHETIC_GENERATED_EVIDENCE"
    CLASSICAL_REFERENCE_EVIDENCE = "CLASSICAL_REFERENCE_EVIDENCE"
    DERIVED_COMPUTATIONAL_EVIDENCE = "DERIVED_COMPUTATIONAL_EVIDENCE"
    UNKNOWN_ORIGIN = "UNKNOWN_ORIGIN"


class DriftClassification(str, Enum):
    ZERO_DRIFT = "ZERO_DRIFT"
    NUMERICAL_DRIFT = "NUMERICAL_DRIFT"
    STRUCTURAL_DRIFT = "STRUCTURAL_DRIFT"
    RECONSTRUCTION_FAILURE = "RECONSTRUCTION_FAILURE"


@dataclass(frozen=True)
class ForensicEvidenceItem:
    """An individual artifact collected from upstream P1→P30 pipeline execution."""
    evidence_id: str
    evidence_type: str                     # e.g. "EPHEMERIS_CHART", "COHORT_DATASET", "HYPOTHESIS_RULE", "P11_SNAPSHOT"
    origin: EvidenceOrigin
    source_priority: str                   # e.g. "P1", "P11", "P15", "P29", "P30"
    source_identifier: str                 # e.g. "ds-marriage-28", "snap-p11-publication-root"
    snapshot_hash: str
    content_hash: str                      # Canonical SHA-256 content hash
    timestamp: datetime
    provenance_parent: Optional[str] = None
    integrity_status: str = "VERIFIED_INTACT"


@dataclass(frozen=True)
class ForensicTraceStep:
    """A single step in the chronological forensic reconstruction timeline."""
    step_id: str
    priority: str                          # e.g. "P1", "P15", "P22", "P30", "P31"
    engine: str                            # e.g. "EphemerisEngine", "CohortValidationEngine", "PublicationEngine"
    input_hash: str
    configuration_hash: str
    formula_hash: str
    output_hash: str
    execution_timestamp: datetime
    status: str                            # e.g. "EXECUTED", "REPLAYED", "SKIPPED"
    drift_detected: bool = False


@dataclass(frozen=True)
class ForensicReconstructionResult:
    """The result of replaying a target result and auditing its provenance chain."""
    reconstruction_id: str
    target_result_id: str
    verdict: ForensicVerdict
    evidence_items: Tuple[ForensicEvidenceItem, ...]
    trace_steps: Tuple[ForensicTraceStep, ...]
    original_output_hash: str
    reconstructed_output_hash: str
    hash_match: bool
    numerical_drift: float                 # Absolute numeric difference
    relative_drift: float                  # Relative ratio difference
    drift_classification: DriftClassification
    provenance_intact: bool
    evidence_completeness: float            # Percentage (0-100%) of required pipeline evidence collected
    evidence_origin_summary: Dict[str, int] # Count by EvidenceOrigin
    failed_checks: Tuple[str, ...]
    warnings: Tuple[str, ...]
    p11_lineage_snapshot_id: str
    p30_publication_seal: Optional[str]
    non_causal_disclosure: str
    synthetic_data_disclosure: str


@dataclass(frozen=True)
class ForensicAuditReport:
    """Complete, publication-independent forensic audit report."""
    report_id: str
    target_objective: str
    verdict: ForensicVerdict
    reconstruction_status: str
    integrity_status: str
    evidence_integrity: bool
    calculation_integrity: bool
    provenance_integrity: bool
    evidence_origin_summary: Dict[str, int]
    timeline: Tuple[ForensicTraceStep, ...]
    p11_root_snapshot_id: str
    p30_publication_seal: Optional[str]
    p31_forensic_seal: str                  # SHA-256 forensic seal of P31
    generated_at: datetime
    non_causal_epistemic_declaration: str
    synthetic_data_epistemic_declaration: str

"""
AstroOS — Longitudinal Evidence Synthesis & Research Knowledge State Domain Models (Priority 36)

Defines domain dataclasses, enums, Knowledge State Machine (RKSM) transitions,
Meta-Analytic Evidence Weighting (MAEWE), Epistemic Certainty Scores, Evidence Grading,
and mandatory non-causal disclosures for Priority 36.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_KNOWLEDGE_STATE_NON_CAUSAL_DISCLOSURE = (
    "RESEARCH_KNOWLEDGE_STATE_DISCLOSURE: Research Knowledge State synthesizes longitudinal "
    "evidentiary weight, meta-analytic effect size, and replication history across pre-registered trials. "
    "It does not establish astrological causation, predictive validity, or a physical mechanism."
)

KNOWLEDGE_STATE_METHODOLOGY_VERSION = "P36-METHODOLOGY-1.0"


class KnowledgeState(str, Enum):
    UNSETTLED = "UNSETTLED"
    EMERGING_EVIDENCE = "EMERGING_EVIDENCE"
    METHODOLOGICALLY_SUPPORTED = "METHODOLOGICALLY_SUPPORTED"
    REPLICATED_KNOWLEDGE_STATE = "REPLICATED_KNOWLEDGE_STATE"
    FALSIFIED_KNOWLEDGE_STATE = "FALSIFIED_KNOWLEDGE_STATE"
    CONTRADICTED_KNOWLEDGE_STATE = "CONTRADICTED_KNOWLEDGE_STATE"
    SUPERSEDED_KNOWLEDGE_STATE = "SUPERSEDED_KNOWLEDGE_STATE"


class EvidenceGrade(str, Enum):
    GRADE_A = "GRADE_A"  # High certainty: Prospective, replicated, zero leakage, meta-analytic support
    GRADE_B = "GRADE_B"  # Moderate certainty: Methodologically valid, partial replication
    GRADE_C = "GRADE_C"  # Low certainty: Emerging evidence, limited sample/generalization
    GRADE_D = "GRADE_D"  # Very low certainty: Unsettled or high sensitivity
    GRADE_F = "GRADE_F"  # Falsified or contradicted knowledge state


class HeterogeneityLevel(str, Enum):
    LOW_HETEROGENEITY = "LOW_HETEROGENEITY"            # I^2 < 25%
    MODERATE_HETEROGENEITY = "MODERATE_HETEROGENEITY"  # 25% <= I^2 < 50%
    HIGH_HETEROGENEITY = "HIGH_HETEROGENEITY font"      # 50% <= I^2 < 75%
    EXTREME_HETEROGENEITY = "EXTREME_HETEROGENEITY"    # I^2 >= 75%


class KnowledgeStateAuditOperation(str, Enum):
    STATE_INITIALIZED = "STATE_INITIALIZED"
    STUDY_SYNTHESIZED = "STUDY_SYNTHESIZED"
    META_ANALYSIS_COMPUTED = "META_ANALYSIS_COMPUTED"
    STATE_TRANSITIONED = "STATE_TRANSITIONED"
    STATE_SUPERSEDED = "STATE_SUPERSEDED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"


@dataclass(frozen=True)
class StudyEvidenceEntry:
    study_id: str
    study_type: str                         # "P33_VALIDITY", "P34_REPLICATION", "P35_GENERALIZATION"
    title: str
    sample_size: int
    metric_name: str
    observed_metric: float
    variance: float
    is_prospective: bool
    is_independent: bool
    weight: float


@dataclass(frozen=True)
class MetaAnalysisResult:
    pooled_effect_size: float
    pooled_variance: float
    confidence_interval: Tuple[float, float]
    i_squared_heterogeneity: float          # Higgins I^2 (0% - 100%)
    heterogeneity_level: HeterogeneityLevel
    tau_squared: float                      # Between-study variance
    p_value: float
    total_samples: int
    forest_plot_data: Dict[str, Any]


@dataclass(frozen=True)
class KnowledgeStateTransition:
    transition_id: str
    from_state: KnowledgeState
    to_state: KnowledgeState
    trigger_study_id: str
    reason: str
    timestamp: datetime


@dataclass(frozen=True)
class ResearchKnowledgeStateRecord:
    state_id: str
    state_version: str                      # e.g., "v1.0", "v2.0"
    target_objective: str
    current_state: KnowledgeState
    evidence_grade: EvidenceGrade
    certainty_score: float                  # Normalized 0.0 -> 1.0
    meta_analysis: MetaAnalysisResult
    accumulated_studies: Tuple[StudyEvidenceEntry, ...]
    transitions: Tuple[KnowledgeStateTransition, ...]
    superseded_state_id: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class ResearchKnowledgeSnapshot:
    snapshot_id: str
    state_id: str
    state_version: str
    canonical_payload_hash: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_KNOWLEDGE_STATE_NON_CAUSAL_DISCLOSURE


@dataclass(frozen=True)
class KnowledgeStateAuditEvent:
    audit_event_id: str
    state_id: str
    operation: KnowledgeStateAuditOperation
    actor_type: str
    timestamp: datetime
    details_hash: str
    reason: str


@dataclass(frozen=True)
class KnowledgeStateSynthesisAssessment:
    assessment_id: str
    knowledge_state: ResearchKnowledgeStateRecord
    overall_verdict: KnowledgeState
    verdict_explanation: Tuple[str, ...]
    limitations: Tuple[str, ...]
    warnings: Tuple[str, ...]
    knowledge_state_fingerprint: str
    knowledge_snapshot_id: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_KNOWLEDGE_STATE_NON_CAUSAL_DISCLOSURE

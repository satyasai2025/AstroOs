"""
AstroOS — Research Knowledge Graph Domain Objects (Priority 24)

Connects Graha, Bhava, Dasha, Transit, Yoga, Varga, Hypotheses, Techniques, and Outcomes
into an Evidence-Weighted Research Knowledge Graph with strict observational/associational
epistemic boundaries and deterministic edge-weight computations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceRelationshipType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    AMPLIFIES = "AMPLIFIES"          # Strictly observational: observed positive interaction
    ATTENUATES = "ATTENUATES"        # Strictly observational: observed negative interaction
    REPLICATES = "REPLICATES"
    TEMPORAL_ACTIVATION = "TEMPORAL_ACTIVATION"
    COMPETING_HYPOTHESIS = "COMPETING_HYPOTHESIS"


class ResearchNodeType(str, Enum):
    GRAHA = "GRAHA"
    BHAVA = "BHAVA"
    DASHA = "DASHA"
    TRANSIT = "TRANSIT"
    YOGA = "YOGA"
    VARGA = "VARGA"
    HYPOTHESIS = "HYPOTHESIS"
    TECHNIQUE = "TECHNIQUE"
    EVENT_OUTCOME = "EVENT_OUTCOME"


class EpistemicClaimNature(str, Enum):
    ASSOCIATIONAL_OBSERVATIONAL = "ASSOCIATIONAL_OBSERVATIONAL"
    EMPIRICALLY_CORRELATED = "EMPIRICALLY_CORRELATED"
    STATISTICALLY_REPLICATED = "STATISTICALLY_REPLICATED"


@dataclass(frozen=True)
class ResearchGraphNode:
    """A research entity node in the knowledge graph."""
    node_id: str
    label: str
    node_type: ResearchNodeType
    epistemic_grade: str
    base_confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)
    contributing_priorities: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceWeightedEdge:
    """
    A typed, directed edge connecting two research entities with
    deterministic empirical weighting and strict non-causal disclosures.
    """
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: EvidenceRelationshipType
    evidence_weight: float           # Deterministically computed in [0.0, 1.0]
    empirical_lift: float            # From P19 / P20
    brier_score: float               # From P15 / P16
    prospective_supported: bool      # From P20
    reproducibility_score: float     # From P22 (0.0 to 100.0)
    is_causal_claimed: bool          # MUST be False (observational association only)
    claim_nature: EpistemicClaimNature
    epistemic_disclosure: str
    p11_lineage_snapshot_id: str
    provenance_hash: str


@dataclass(frozen=True)
class CrossHypothesisCluster:
    """Identifies overlapping or competing discovered hypotheses from P19."""
    cluster_id: str
    primary_hypothesis_id: str
    competing_hypothesis_ids: List[str]
    shared_feature_signatures: List[str]
    lift_divergence: float
    epistemic_arbitration_status: str


@dataclass(frozen=True)
class TechniqueInteractionItem:
    """Identifies recurring multi-technique synergistic combinations across cohorts."""
    interaction_id: str
    technique_ids: List[str]
    observed_joint_lift: float
    observed_standalone_max_lift: float
    synergy_delta: float
    co_occurrence_count: int
    epistemic_label: str  # e.g., 'OBSERVED_POSITIVE_CONFLUENCE'


@dataclass(frozen=True)
class ResearchKnowledgeGraph:
    """Full research knowledge graph container."""
    graph_id: str
    target_objective: str
    nodes: List[ResearchGraphNode]
    edges: List[EvidenceWeightedEdge]
    hypothesis_clusters: List[CrossHypothesisCluster]
    technique_interactions: List[TechniqueInteractionItem]
    total_nodes: int
    total_edges: int
    graph_density_score: float
    is_fully_non_causal: bool
    generated_at: str

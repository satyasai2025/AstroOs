"""
AstroOS — Research Knowledge Graph API Schemas (Priority 24)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphQueryRequest(BaseModel):
    target_objective: str = Field(default="marriage", description="Target research objective (marriage, career, health)")
    min_weight_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum evidence weight filter")
    node_type_filter: Optional[str] = Field(default=None, description="Optional node type filter")
    snapshot_id: str = Field(default="snap-p11-frozen-root", description="P11 Lineage snapshot ID")


class ResearchGraphNodeSchema(BaseModel):
    node_id: str
    label: str
    node_type: str
    epistemic_grade: str
    base_confidence: float
    properties: Dict[str, Any]
    contributing_priorities: List[str]


class EvidenceWeightedEdgeSchema(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    evidence_weight: float
    empirical_lift: float
    brier_score: float
    prospective_supported: bool
    reproducibility_score: float
    is_causal_claimed: bool
    claim_nature: str
    epistemic_disclosure: str
    p11_lineage_snapshot_id: str
    provenance_hash: str


class CrossHypothesisClusterSchema(BaseModel):
    cluster_id: str
    primary_hypothesis_id: str
    competing_hypothesis_ids: List[str]
    shared_feature_signatures: List[str]
    lift_divergence: float
    epistemic_arbitration_status: str


class TechniqueInteractionItemSchema(BaseModel):
    interaction_id: str
    technique_ids: List[str]
    observed_joint_lift: float
    observed_standalone_max_lift: float
    synergy_delta: float
    co_occurrence_count: int
    epistemic_label: str


class ResearchKnowledgeGraphResponse(BaseModel):
    graph_id: str
    target_objective: str
    nodes: List[ResearchGraphNodeSchema]
    edges: List[EvidenceWeightedEdgeSchema]
    hypothesis_clusters: List[CrossHypothesisClusterSchema]
    technique_interactions: List[TechniqueInteractionItemSchema]
    total_nodes: int
    total_edges: int
    graph_density_score: float
    is_fully_non_causal: bool
    generated_at: str

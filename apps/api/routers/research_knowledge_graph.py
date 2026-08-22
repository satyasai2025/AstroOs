"""
AstroOS — Research Knowledge Graph Router (Priority 24)

Endpoints for querying the evidence-weighted research knowledge graph,
exploring cross-hypothesis competition clusters, and inspecting multi-technique interactions.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.research_knowledge_graph import (
    CrossHypothesisClusterSchema,
    GraphQueryRequest,
    ResearchKnowledgeGraphResponse,
    TechniqueInteractionItemSchema,
)
from apps.api.services.research_knowledge_graph_engine import ResearchKnowledgeGraphEngine

router = APIRouter(
    prefix="/api/v1/research/knowledge-graph",
    tags=["Research Knowledge Graph"],
    dependencies=[Depends(require_authenticated)],
)


@router.post("/query", response_model=ResearchKnowledgeGraphResponse)
def query_research_knowledge_graph(request: GraphQueryRequest):
    """
    Query the complete or filtered Evidence-Weighted Research Knowledge Graph.
    """
    graph = ResearchKnowledgeGraphEngine.get_instance().build_research_knowledge_graph(
        target_objective=request.target_objective,
        min_weight_threshold=request.min_weight_threshold,
        snapshot_id=request.snapshot_id,
    )

    nodes = graph.nodes
    if request.node_type_filter:
        nodes = [n for n in nodes if n.node_type.value == request.node_type_filter]

    return ResearchKnowledgeGraphResponse(
        graph_id=graph.graph_id,
        target_objective=graph.target_objective,
        nodes=[
            {
                "node_id": n.node_id,
                "label": n.label,
                "node_type": n.node_type.value,
                "epistemic_grade": n.epistemic_grade,
                "base_confidence": n.base_confidence,
                "properties": n.properties,
                "contributing_priorities": n.contributing_priorities,
            }
            for n in nodes
        ],
        edges=[
            {
                "edge_id": e.edge_id,
                "source_node_id": e.source_node_id,
                "target_node_id": e.target_node_id,
                "relationship_type": e.relationship_type.value,
                "evidence_weight": e.evidence_weight,
                "empirical_lift": e.empirical_lift,
                "brier_score": e.brier_score,
                "prospective_supported": e.prospective_supported,
                "reproducibility_score": e.reproducibility_score,
                "is_causal_claimed": e.is_causal_claimed,
                "claim_nature": e.claim_nature.value,
                "epistemic_disclosure": e.epistemic_disclosure,
                "p11_lineage_snapshot_id": e.p11_lineage_snapshot_id,
                "provenance_hash": e.provenance_hash,
            }
            for e in graph.edges
        ],
        hypothesis_clusters=[
            {
                "cluster_id": c.cluster_id,
                "primary_hypothesis_id": c.primary_hypothesis_id,
                "competing_hypothesis_ids": c.competing_hypothesis_ids,
                "shared_feature_signatures": c.shared_feature_signatures,
                "lift_divergence": c.lift_divergence,
                "epistemic_arbitration_status": c.epistemic_arbitration_status,
            }
            for c in graph.hypothesis_clusters
        ],
        technique_interactions=[
            {
                "interaction_id": ti.interaction_id,
                "technique_ids": ti.technique_ids,
                "observed_joint_lift": ti.observed_joint_lift,
                "observed_standalone_max_lift": ti.observed_standalone_max_lift,
                "synergy_delta": ti.synergy_delta,
                "co_occurrence_count": ti.co_occurrence_count,
                "epistemic_label": ti.epistemic_label,
            }
            for ti in graph.technique_interactions
        ],
        total_nodes=len(nodes),
        total_edges=len(graph.edges),
        graph_density_score=graph.graph_density_score,
        is_fully_non_causal=graph.is_fully_non_causal,
        generated_at=graph.generated_at,
    )


@router.get("/clusters", response_model=List[CrossHypothesisClusterSchema])
def get_hypothesis_clusters(target_objective: str = Query("marriage")):
    """
    Get discovered cross-hypothesis competition and overlap clusters.
    """
    graph = ResearchKnowledgeGraphEngine.get_instance().build_research_knowledge_graph(target_objective=target_objective)
    return [
        CrossHypothesisClusterSchema(
            cluster_id=c.cluster_id,
            primary_hypothesis_id=c.primary_hypothesis_id,
            competing_hypothesis_ids=c.competing_hypothesis_ids,
            shared_feature_signatures=c.shared_feature_signatures,
            lift_divergence=c.lift_divergence,
            epistemic_arbitration_status=c.epistemic_arbitration_status,
        )
        for c in graph.hypothesis_clusters
    ]


@router.get("/interactions", response_model=List[TechniqueInteractionItemSchema])
def get_technique_interactions(target_objective: str = Query("marriage")):
    """
    Get multi-technique synergistic interactions discovered across cohorts.
    """
    graph = ResearchKnowledgeGraphEngine.get_instance().build_research_knowledge_graph(target_objective=target_objective)
    return [
        TechniqueInteractionItemSchema(
            interaction_id=ti.interaction_id,
            technique_ids=ti.technique_ids,
            observed_joint_lift=ti.observed_joint_lift,
            observed_standalone_max_lift=ti.observed_standalone_max_lift,
            synergy_delta=ti.synergy_delta,
            co_occurrence_count=ti.co_occurrence_count,
            epistemic_label=ti.epistemic_label,
        )
        for ti in graph.technique_interactions
    ]

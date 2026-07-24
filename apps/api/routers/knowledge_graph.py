"""
AstroOS — Knowledge Graph Router (Phase D, Module 12 Extension)

HTTP adapter layer over KnowledgeGraphEngine. No business logic lives here —
only request/response mapping and HTTP error translation.

The POST /analyze endpoint implements the Knowledge-Graph-to-Analytics bridge
(Phase III), wiring EntityLinker and GraphAnalytics together under a single
HTTP endpoint so researchers can correlate chart data against KG entities
and compute frequency distributions over research datasets.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from apps.api.dependencies import get_knowledge_graph_engine
from apps.api.domain.graph import Entity
from apps.api.schemas.knowledge_graph import (
    AnalyzeRequest,
    AnalyzeResponse,
    EntityCorrelationResponse,
    EntityFrequencyResponse,
    EntityResponse,
    FrequencyDistributionResponse,
    LinkedEntityResponse,
    NodeResponse,
    ProximityRelationshipResponse,
    RelationshipListResponse,
    RelationshipResponse,
)
from apps.api.services.entity_linking import EntityLinker
from apps.api.services.graph_analytics import GraphAnalytics
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


def _node_response(node) -> NodeResponse:
    return NodeResponse(
        id=node.id,
        label=node.label,
        type=node.type,
        metadata=dict(node.metadata),
    )


def _relationship_response(rel) -> RelationshipResponse:
    return RelationshipResponse(
        source_id=rel.source_id,
        target_id=rel.target_id,
        relationship_type=rel.relationship_type,
        metadata=dict(rel.metadata),
    )


def _linked_entity_response(le) -> LinkedEntityResponse:
    return LinkedEntityResponse(
        source_name=le.source_name,
        source_type=le.source_type,
        entity_id=le.entity_id,
        entity_label=le.entity_label,
        entity_type=le.entity_type,
        confidence=le.confidence,
        match_method=le.match_method,
        metadata=dict(le.metadata),
    )


def _proximity_response(pr) -> ProximityRelationshipResponse:
    return ProximityRelationshipResponse(
        source_id=pr.get("source_id", ""),
        relationship_type=pr.get("relationship_type", ""),
        target_id=pr.get("target_id", ""),
        metadata=pr.get("metadata", {}),
        via=pr.get("via", ""),
    )


def _correlation_response(c) -> EntityCorrelationResponse:
    return EntityCorrelationResponse(
        entity_id=c.entity_id,
        entity_label=c.entity_label,
        entity_type=c.entity_type,
        field_x=c.field_x,
        field_y=c.field_y,
        present_count=c.present_count,
        absent_count=c.absent_count,
        present_mean=c.present_mean,
        absent_mean=c.absent_mean,
        effect_size=c.effect_size,
        interpretation=c.interpretation,
    )


def _frequency_response(f) -> EntityFrequencyResponse:
    return EntityFrequencyResponse(
        entity_id=f.entity_id,
        entity_label=f.entity_label,
        entity_type=f.entity_type,
        count=f.count,
        proportion=f.proportion,
    )


@router.get("/entity/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str = Path(..., description="Ontology entity ID, e.g. GRAHA-SUN"),
    engine=Depends(get_knowledge_graph_engine),
) -> EntityResponse:
    """
    Return a single entity together with the relationships where it appears
    as subject or object.
    """
    entity: Entity | None = engine.get_entity(entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found in knowledge graph.",
        )
    return EntityResponse(
        node=_node_response(entity.node),
        relationships=[_relationship_response(r) for r in entity.relationships],
    )


@router.get("/relationships", response_model=RelationshipListResponse)
async def list_relationships(
    source_type: str | None = Query(
        None, description="Filter by source entity type (e.g. Graha, Rashi)"
    ),
    relationship_type: str | None = Query(
        None,
        description="Filter by relationship type (e.g. Owns, ExaltedIn)",
    ),
    engine=Depends(get_knowledge_graph_engine),
) -> RelationshipListResponse:
    """
    Return a list of relationships, optionally filtered by source entity
    type and/or relationship type.
    """
    rels = engine.get_relationships(source_type=source_type, relationship_type=relationship_type)
    return RelationshipListResponse(
        relationships=[_relationship_response(r) for r in rels],
        total=len(rels),
    )


# ── Knowledge-Graph-to-Analytics Bridge (Phase III) ──────────────────────────


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_bridge(
    body: AnalyzeRequest,
    engine: KnowledgeGraphEngine = Depends(get_knowledge_graph_engine),
) -> AnalyzeResponse:
    """
    Knowledge-Graph-to-Analytics bridge endpoint (Phase III).

    Accepts chart data and/or a research dataset, then:

    1. **Entity Linking** — links chart-level entities (planets, houses,
       signs) to Knowledge Graph entities by name and alias lookup.

    2. **Proximity Relationships** — surfaces relationships between any
       two linked entities that exist in the KG.

    3. **Entity Correlation** — for each linked entity present in the
       dataset, computes a Welch's t-test / Cohen's d against the
       specified numeric field.

    4. **Frequency Distribution** — counts how often each KG entity
       appears in the dataset's entity_field column.

    5. **Unlinked Reporting** — returns any chart/dataset entities that
       could not be matched to the KG.

    The endpoint is deterministic and pure-local — all computation uses
    the in-memory OntologyRegistry and StatisticalEngine (no external
    services, no LLM calls).
    """
    # ── Step 1: Entity Linking (if chart data provided) ────────────────
    linker = EntityLinker(engine)
    link_result = linker.link_chart_data(body.chart)

    linked_responses = [_linked_entity_response(le) for le in link_result.linked_entities]
    proximity_responses = [_proximity_response(pr) for pr in link_result.proximity_relationships]

    # ── Step 2: KG-to-Dataset Correlation (if dataset provided) ────────
    correlations: list[EntityCorrelationResponse] = []
    frequency: FrequencyDistributionResponse | None = None

    if body.dataset:
        analytics = GraphAnalytics(engine)

        # Correlate each linked entity against the dataset
        numeric_field = body.numeric_field
        entity_field = body.entity_field

        if numeric_field:
            entity_ids = [le.entity_id for le in link_result.linked_entities]
            raw_correlations = analytics.correlate_multiple(
                entity_ids=entity_ids,
                dataset=body.dataset,
                entity_field=entity_field,
                numeric_field=numeric_field,
            )
            correlations = [_correlation_response(c) for c in raw_correlations]

        # Frequency distribution across the dataset
        freq = analytics.entity_frequency(
            dataset=body.dataset,
            entity_field=entity_field,
            top_n=body.max_suggestions,
        )
        frequency = FrequencyDistributionResponse(
            entities=[_frequency_response(f) for f in freq.entities],
            total_records=freq.total_records,
            unique_entities=freq.unique_entities,
        )

    return AnalyzeResponse(
        linked_entities=linked_responses,
        proximity_relationships=proximity_responses,
        unlinked=link_result.unlinked,
        total_matched=link_result.total_matched,
        total_unmatched=link_result.total_unmatched,
        correlations=correlations,
        frequency=frequency,
        suggestions=[],  # Placeholder for future AI-suggested relationships
    )

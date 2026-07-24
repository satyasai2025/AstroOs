"""
AstroOS — Knowledge Graph API Schemas (Phase D + Bridge)

Pydantic response models for the graph HTTP surface and the
Knowledge-Graph-to-Analytics bridge endpoint. Mirrors the
domain GraphNode / GraphRelationship primitives.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NodeResponse(BaseModel):
    """Response payload describing node data."""
    id: str
    label: str
    type: str
    metadata: dict[str, Any] = {}


class RelationshipResponse(BaseModel):
    """Response payload describing relationship data."""
    source_id: str
    target_id: str
    relationship_type: str
    metadata: dict[str, Any] = {}


class EntityResponse(BaseModel):
    """An entity together with its direct relationships."""

    node: NodeResponse
    relationships: list[RelationshipResponse] = []


class RelationshipListResponse(BaseModel):
    """Response payload describing relationship list data."""
    relationships: list[RelationshipResponse] = []
    total: int = 0


# ── Knowledge-Graph-to-Analytics Bridge (Phase III) ──────────────────────────


class ChartEntity(BaseModel):
    """A single entity extracted from chart data for linking."""
    name: str
    sign: str | None = None
    house: int | None = None
    nakshatra: str | None = None
    metadata: dict[str, Any] = {}


class AnalyzeRequest(BaseModel):
    """Request payload for POST /knowledge-graph/analyze."""
    chart: dict[str, Any] = {
        "planets": [],
        "houses": {},
        "ascendant": {},
        "signs": [],
    }
    dataset: list[dict[str, Any]] = []
    entity_field: str = "entity_id"
    numeric_field: str | None = None
    max_suggestions: int = 5


class LinkedEntityResponse(BaseModel):
    """A chart entity matched to a KG entity."""
    source_name: str
    source_type: str
    entity_id: str
    entity_label: str
    entity_type: str
    confidence: float
    match_method: str
    metadata: dict[str, Any] = {}


class ProximityRelationshipResponse(BaseModel):
    """A KG relationship between two linked chart entities."""
    source_id: str
    relationship_type: str
    target_id: str
    metadata: dict[str, Any] = {}
    via: str = ""


class EntityCorrelationResponse(BaseModel):
    """Statistical correlation between a KG entity and a dataset field."""
    entity_id: str
    entity_label: str
    entity_type: str
    field_x: str
    field_y: str
    present_count: int
    absent_count: int
    present_mean: float
    absent_mean: float
    effect_size: float
    interpretation: str


class EntityFrequencyResponse(BaseModel):
    """Frequency count for one KG entity in a dataset."""
    entity_id: str
    entity_label: str
    entity_type: str
    count: int
    proportion: float


class FrequencyDistributionResponse(BaseModel):
    """Full frequency distribution response."""
    entities: list[EntityFrequencyResponse] = []
    total_records: int = 0
    unique_entities: int = 0


class AnalyzeResponse(BaseModel):
    """Response payload for POST /knowledge-graph/analyze."""
    linked_entities: list[LinkedEntityResponse] = []
    proximity_relationships: list[ProximityRelationshipResponse] = []
    unlinked: list[dict[str, Any]] = []
    total_matched: int = 0
    total_unmatched: int = 0
    correlations: list[EntityCorrelationResponse] = []
    frequency: FrequencyDistributionResponse | None = None
    suggestions: list[dict[str, Any]] = []

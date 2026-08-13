"""
AstroOS — Technique Intelligence API Schemas

Request/response models for /api/v1/techniques. Same DTO-boundary discipline as
schemas/event_analysis.py: these Pydantic models convert to/from the domain
objects (domain/technique.py) in the router layer and never leak into the
TechniqueEngine, TechniqueRepository, or the import pipeline.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from apps.api.schemas.prediction_evidence import PredictionEvidenceSchema


# ── shared ────────────────────────────────────────────────────────────────────


class RuleRefSchema(BaseModel):
    rule_id: str
    rule_version: str
    role: str
    provenance: str
    weight: float
    source_reference: str
    active: bool


class TechniqueSummary(BaseModel):
    technique_id: str
    name: str
    version: int
    tradition: str
    objective: str
    provenance: str
    status: str
    rule_count: int


class TechniqueDetail(TechniqueSummary):
    description: str
    source_references: list[str]
    required_inputs: list[str]
    dependencies: list[str]
    unresolved_inconsistencies: list[str]
    rules: list[RuleRefSchema]


class TechniqueListResponse(BaseModel):
    techniques: list[TechniqueSummary]


# ── import ────────────────────────────────────────────────────────────────────


class ValidationSampleSchema(BaseModel):
    """One validation case supplied with an import request."""
    label: str
    facts: dict[str, Any] = Field(
        description="fact_key -> value, e.g. {'planet.sun.house': 8}"
    )
    expect_triggered: Optional[bool] = None


class ValidationCaseSchema(BaseModel):
    label: str
    triggered_primary: bool
    match_status: str
    confidence: int


class TechniqueImportRequest(BaseModel):
    """Import a technique through the generic pipeline from a structured payload.

    `payload` is the RawTechnique JSON (technique_id, name, rules[], ...) — the
    same shape the StructuredTechniqueExtractor consumes. Free-text/LLM
    extraction is a separate future entry point; this endpoint is the
    deterministic, structured path.
    """
    source_type: str = "structured"
    reference: str = Field(min_length=1, max_length=500)
    excerpt: Optional[str] = None
    payload: dict[str, Any]
    persist: bool = True
    samples: list[ValidationSampleSchema] = Field(default_factory=list)


class TechniqueImportResponse(BaseModel):
    technique: TechniqueDetail
    persisted: bool
    persisted_id: Optional[uuid.UUID] = None
    validation: list[ValidationCaseSchema]


# ── execute ───────────────────────────────────────────────────────────────────


class TechniqueExecuteRequest(BaseModel):
    """Execute a technique against an explicit set of Facts.

    `facts` maps a Fact key to its value (e.g. {'planet.sun.house': 8,
    'dasha.current_lord': 'venus'}). Wiring a birth_chart_id -> FactBuilder is a
    later enhancement; explicit facts keep this endpoint decoupled and testable.
    """
    facts: dict[str, Any]
    version: Optional[int] = None


class TriggerSchema(BaseModel):
    rule_id: str
    rule_name: str
    role: str
    status: str
    provenance: str
    matched_conditions: list[str]
    failed_conditions: list[str]
    missing_facts: list[str]
    explanation: str


class InputAvailabilitySchema(BaseModel):
    fact_key: str
    availability: str


class TechniqueExecuteResponse(BaseModel):
    technique_id: str
    technique_version: int
    confidence: int
    confidence_basis: str
    triggers: list[TriggerSchema]
    inputs: list[InputAvailabilitySchema]
    evidence: list[str]
    unresolved_inconsistencies: list[str]
    prediction: PredictionEvidenceSchema = Field(
        description="The same result adapted onto the generic PredictionEvidence "
        "contract — the shape Jaimini yogas already return — for callers that "
        "want one prediction/evidence type across engines."
    )

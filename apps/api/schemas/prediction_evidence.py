"""
AstroOS — Prediction Evidence API Schemas

Pydantic mirror of domain/prediction_evidence.py — kept generic and
technique-agnostic (matching that module's own docstring) so any rule-
evaluating engine's API surface (Jaimini yogas, the generic Technique
framework, future dasha-triggered predictions, ...) serializes through the
same DTOs instead of each router inventing its own.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionReasonSchema(BaseModel):
    description: str
    matched_objects: list[str]
    is_satisfied: bool


class PredictionConfidenceSchema(BaseModel):
    score: int = Field(ge=0, le=100)
    satisfied_conditions: int
    total_conditions: int
    basis: str


class PredictionRuleSchema(BaseModel):
    rule_id: str
    name: str
    sutra_reference: str
    rule_version: str
    requires: list[str]


class PredictionEvidenceSchema(BaseModel):
    rule: PredictionRuleSchema
    is_matched: bool
    triggering_conditions: list[str]
    reasons: list[PredictionReasonSchema]
    confidence: PredictionConfidenceSchema
    explanation: str

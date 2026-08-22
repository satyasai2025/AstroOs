"""
AstroOS — Classical Rule Evidence Pydantic Schemas (Module 19, Phase 3)
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ClassicalSourceCitationSchema(BaseModel):
    book_title: str
    author: str
    chapter: int
    chapter_name: str
    sloka_range: str
    sanskrit_iast: str
    sanskrit_devanagari: str
    translation_english: str
    tradition: str
    commentary_notes: Optional[str] = None
    is_verified: bool = True


class ConditionRequirementSchema(BaseModel):
    condition_id: str
    description: str
    condition_type: str
    required_parameters: dict[str, Any] = Field(default_factory=dict)
    is_mandatory: bool = True


class ChartEvidenceItemSchema(BaseModel):
    condition_id: str
    is_satisfied: bool
    actual_chart_value: str
    notes: str = ""
    contributing_planets: list[str] = Field(default_factory=list)
    contributing_houses: list[int] = Field(default_factory=list)


class CancellationFactorSchema(BaseModel):
    factor_id: str
    description: str
    classical_reference: str
    is_active: bool
    impact_deduction: float


class RuleEvidenceChainSchema(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    brief_description: str
    citation: ClassicalSourceCitationSchema
    required_conditions: list[ConditionRequirementSchema]
    actual_evidence: list[ChartEvidenceItemSchema]
    status: str
    strength_score: float
    cancellation_factors: list[CancellationFactorSchema]
    fructification_summary: str
    audit_trace: list[str]


class ClassicalRuleExploreItemSchema(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    book_title: str
    author: str
    chapter_info: str
    tradition: str
    brief_description: str
    sanskrit_preview: str
    translation_preview: str
    is_verified: bool = True


class ClassicalRuleExploreResponse(BaseModel):
    total_rules: int
    rules: list[ClassicalRuleExploreItemSchema]


class EvaluateChartRuleEvidenceRequest(BaseModel):
    chart: dict[str, Any]
    rule_ids: Optional[list[str]] = None
    category_filter: Optional[str] = None


class EvaluateChartRuleEvidenceResponse(BaseModel):
    evaluated_chart_id: Optional[str] = None
    total_rules_evaluated: int
    satisfied_rules_count: int
    partially_satisfied_count: int
    cancelled_count: int
    evidence_chains: list[RuleEvidenceChainSchema]

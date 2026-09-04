"""
AstroOS — Explanation API Schemas (Phase D)

Pydantic response models for structured rule explanations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConditionExplanationResponse(BaseModel):
    """Response payload describing condition explanation data."""
    condition_text: str
    satisfied: bool
    fact_key: str
    actual_value: str
    expected_value: str
    operator: str


class ExplanationResponse(BaseModel):
    """Response payload describing explanation data."""
    rule_id: str
    rule_name: str
    rule_category: str
    summary: str
    matched: bool
    conditions: list[ConditionExplanationResponse] = []
    derived_facts: dict[str, Any] = {}
    derived_fact_sources: dict[str, str] = {}
    locked_facts: list[str] = []
    confidence: str = "medium"
    explanation_text: str = ""


class FailureAnalysisResponse(BaseModel):
    """Response payload describing failure analysis data."""
    rule_id: str
    rule_name: str
    summary: str
    failed_conditions: list[ConditionExplanationResponse] = []
    passed_conditions: list[ConditionExplanationResponse] = []
    suggested_conditions: list[str] = []

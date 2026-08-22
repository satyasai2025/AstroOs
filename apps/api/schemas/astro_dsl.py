"""
AstroOS — Priority 9: AstroDSL & Custom Technique Pydantic Schemas
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AstroDSLValidationRequest(BaseModel):
    dsl_source: str = Field(..., description="Raw AstroDSL string code")


class AstroDSLValidationResponse(BaseModel):
    is_valid: bool
    dsl_source: str
    error_message: Optional[str] = None
    ast_representation: Optional[str] = None


class CustomRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    dsl_source: str = Field(..., description="Raw AstroDSL code string")
    category: str = "custom_yoga"
    tags: List[str] = []


class CustomRuleResponse(BaseModel):
    rule_id: str
    name: str
    description: str
    dsl_source: str
    category: str
    tags: List[str]
    author: str
    version: str
    created_at: str


class TraceStepSchema(BaseModel):
    node_type: str
    expression: str
    result: Any


class RuleTestRequest(BaseModel):
    dsl_source: str
    chart_context: dict[str, Any] = Field(
        ...,
        description="Birth chart context containing planets and planet_strengths arrays",
    )


class RuleTestResponse(BaseModel):
    is_satisfied: bool
    evaluated_value: Any
    execution_time_ms: float
    trace: List[TraceStepSchema]
    error_message: Optional[str] = None


class BundleExportRequest(BaseModel):
    rule_ids: Optional[List[str]] = None


class BundleImportRequest(BaseModel):
    bundle_json: str

"""
AstroOS — Priority 9: Custom Techniques & AstroDSL API Router
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from apps.api.domain.astro_dsl import parse_astro_dsl, AstroDSLSyntaxError
from apps.api.schemas.astro_dsl import (
    AstroDSLValidationRequest,
    AstroDSLValidationResponse,
    BundleExportRequest,
    BundleImportRequest,
    CustomRuleCreateRequest,
    CustomRuleResponse,
    RuleTestRequest,
    RuleTestResponse,
    TraceStepSchema,
)
from apps.api.services.astro_dsl_evaluator import evaluate_astro_dsl
from apps.api.services.custom_technique_service import CustomTechniqueRegistry

router = APIRouter(prefix="/techniques/custom", tags=["Custom Techniques & AstroDSL"])


@router.post("/dsl/validate", response_model=AstroDSLValidationResponse)
def validate_astro_dsl(request: AstroDSLValidationRequest) -> AstroDSLValidationResponse:
    """Validate syntax and structure of an AstroDSL code string."""
    try:
        ast = parse_astro_dsl(request.dsl_source)
        return AstroDSLValidationResponse(
            is_valid=True,
            dsl_source=request.dsl_source,
            ast_representation=str(ast),
        )
    except AstroDSLSyntaxError as e:
        return AstroDSLValidationResponse(
            is_valid=False,
            dsl_source=request.dsl_source,
            error_message=str(e),
        )
    except Exception as e:
        return AstroDSLValidationResponse(
            is_valid=False,
            dsl_source=request.dsl_source,
            error_message=f"Validation error: {e}",
        )


@router.post("/dsl/test-evaluate", response_model=RuleTestResponse)
def test_evaluate_astro_dsl(request: RuleTestRequest) -> RuleTestResponse:
    """Test evaluate an AstroDSL rule string against a birth chart context in real-time."""
    try:
        eval_res = evaluate_astro_dsl(request.dsl_source, request.chart_context)
        trace_steps = [
            TraceStepSchema(node_type=t.node_type, expression=t.expression, result=t.result)
            for t in eval_res.trace
        ]
        return RuleTestResponse(
            is_satisfied=eval_res.is_satisfied,
            evaluated_value=eval_res.evaluated_value,
            execution_time_ms=eval_res.execution_time_ms,
            trace=trace_steps,
            error_message=eval_res.error_message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Evaluation failed: {e}",
        )


@router.get("", response_model=List[CustomRuleResponse])
@router.get("/", response_model=List[CustomRuleResponse])
def list_custom_rules(category: Optional[str] = None) -> List[CustomRuleResponse]:
    """List all registered custom AstroDSL rules."""
    registry = CustomTechniqueRegistry.get_instance()
    rules = registry.list_rules(category=category)
    return [
        CustomRuleResponse(
            rule_id=r.rule_id,
            name=r.name,
            description=r.description,
            dsl_source=r.dsl_source,
            category=r.category,
            tags=r.tags,
            author=r.author,
            version=r.version,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post("", response_model=CustomRuleResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CustomRuleResponse, status_code=status.HTTP_201_CREATED)
def create_custom_rule(request: CustomRuleCreateRequest) -> CustomRuleResponse:
    """Create and register a new AstroDSL custom rule."""
    try:
        registry = CustomTechniqueRegistry.get_instance()
        rule = registry.register_rule(
            dsl_source=request.dsl_source,
            name=request.name,
            description=request.description,
            category=request.category,
            tags=request.tags,
        )
        return CustomRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            dsl_source=rule.dsl_source,
            category=rule.category,
            tags=rule.tags,
            author=rule.author,
            version=rule.version,
            created_at=rule.created_at,
        )
    except AstroDSLSyntaxError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{rule_id}")
def delete_custom_rule(rule_id: str):
    """Delete a custom rule by ID."""
    registry = CustomTechniqueRegistry.get_instance()
    deleted = registry.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom rule '{rule_id}' not found",
        )
    return {"message": f"Rule '{rule_id}' deleted successfully"}


@router.post("/export")
def export_bundle(request: BundleExportRequest):
    """Export custom rules as a JSON bundle."""
    registry = CustomTechniqueRegistry.get_instance()
    bundle_json = registry.export_bundle(rule_ids=request.rule_ids)
    return {"bundle_json": bundle_json}


@router.post("/import", response_model=List[CustomRuleResponse])
def import_bundle(request: BundleImportRequest) -> List[CustomRuleResponse]:
    """Import custom rules from a JSON bundle string."""
    try:
        registry = CustomTechniqueRegistry.get_instance()
        imported = registry.import_bundle(request.bundle_json)
        return [
            CustomRuleResponse(
                rule_id=r.rule_id,
                name=r.name,
                description=r.description,
                dsl_source=r.dsl_source,
                category=r.category,
                tags=r.tags,
                author=r.author,
                version=r.version,
                created_at=r.created_at,
            )
            for r in imported
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {e}",
        )

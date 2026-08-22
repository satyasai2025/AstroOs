"""
AstroOS — Classical Rule Evidence API Router (Module 19, Phase 3)

Endpoints:
  GET  /api/v1/rules/explore
  GET  /api/v1/rules/{rule_id}/details
  POST /api/v1/rules/evaluate-chart
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.domain.classical_rule_evidence import RuleEvidenceChain
from apps.api.schemas.classical_rule_evidence import (
    CancellationFactorSchema,
    ChartEvidenceItemSchema,
    ClassicalRuleExploreItemSchema,
    ClassicalRuleExploreResponse,
    ClassicalSourceCitationSchema,
    ConditionRequirementSchema,
    EvaluateChartRuleEvidenceRequest,
    EvaluateChartRuleEvidenceResponse,
    RuleEvidenceChainSchema,
)
from apps.api.services.classical_rule_evidence_engine import (
    ClassicalRuleEvidenceEngine,
    ClassicalRuleRegistry,
)

router = APIRouter(prefix="/rules", tags=["Classical Rule Evidence Engine"])


def _to_schema_evidence_chain(chain: RuleEvidenceChain) -> RuleEvidenceChainSchema:
    cit = chain.citation
    return RuleEvidenceChainSchema(
        rule_id=chain.rule_id,
        rule_name=chain.rule_name,
        category=chain.category,
        brief_description=chain.brief_description,
        citation=ClassicalSourceCitationSchema(
            book_title=cit.book_title,
            author=cit.author,
            chapter=cit.chapter,
            chapter_name=cit.chapter_name,
            sloka_range=cit.sloka_range,
            sanskrit_iast=cit.sanskrit_iast,
            sanskrit_devanagari=cit.sanskrit_devanagari,
            translation_english=cit.translation_english,
            tradition=cit.tradition.value,
            commentary_notes=cit.commentary_notes,
            is_verified=cit.is_verified,
        ),
        required_conditions=[
            ConditionRequirementSchema(
                condition_id=req.condition_id,
                description=req.description,
                condition_type=req.condition_type,
                required_parameters=req.required_parameters,
                is_mandatory=req.is_mandatory,
            )
            for req in chain.required_conditions
        ],
        actual_evidence=[
            ChartEvidenceItemSchema(
                condition_id=ev.condition_id,
                is_satisfied=ev.is_satisfied,
                actual_chart_value=ev.actual_chart_value,
                notes=ev.notes,
                contributing_planets=ev.contributing_planets,
                contributing_houses=ev.contributing_houses,
            )
            for ev in chain.actual_evidence
        ],
        status=chain.status.value,
        strength_score=chain.strength_score,
        cancellation_factors=[
            CancellationFactorSchema(
                factor_id=c.factor_id,
                description=c.description,
                classical_reference=c.classical_reference,
                is_active=c.is_active,
                impact_deduction=c.impact_deduction,
            )
            for c in chain.cancellation_factors
        ],
        fructification_summary=chain.fructification_summary,
        audit_trace=chain.audit_trace,
    )


@router.get("/explore", response_model=ClassicalRuleExploreResponse)
async def explore_classical_rules(
    tradition: Optional[str] = Query(None, description="Filter by tradition: Parashari, Jaimini, Varahamihira, Mantreswara"),
    category: Optional[str] = Query(None, description="Filter by category: Raja Yoga, Pancha Mahapurusha, etc."),
    query: Optional[str] = Query(None, description="Search keyword"),
) -> ClassicalRuleExploreResponse:
    """
    Returns searchable catalog of canonical classical rules and yogas
    with Sanskrit citations from BPHS, Saravali, Jaimini, Brihat Jataka, and Phaladeepika.
    """
    raw_rules = ClassicalRuleRegistry.get_canonical_rules()
    items: list[ClassicalRuleExploreItemSchema] = []

    for r in raw_rules:
        cit = r["citation"]
        # Filters
        if tradition and tradition.lower() not in cit.tradition.value.lower():
            continue
        if category and category.lower() not in r["category"].lower():
            continue
        if query:
            q = query.lower()
            text_match = (
                q in r["rule_name"].lower()
                or q in r["brief_description"].lower()
                or q in cit.book_title.lower()
                or q in cit.translation_english.lower()
            )
            if not text_match:
                continue

        items.append(
            ClassicalRuleExploreItemSchema(
                rule_id=r["rule_id"],
                rule_name=r["rule_name"],
                category=r["category"],
                book_title=cit.book_title,
                author=cit.author,
                chapter_info=f"Ch. {cit.chapter} ({cit.chapter_name}), {cit.sloka_range}",
                tradition=cit.tradition.value,
                brief_description=r["brief_description"],
                sanskrit_preview=cit.sanskrit_devanagari,
                translation_preview=cit.translation_english[:140] + ("..." if len(cit.translation_english) > 140 else ""),
                is_verified=cit.is_verified,
            )
        )

    return ClassicalRuleExploreResponse(total_rules=len(items), rules=items)


@router.get("/{rule_id}/details")
async def get_rule_details(rule_id: str) -> dict[str, Any]:
    """
    Returns full classical citation, required conditions, and commentary for a specific rule.
    """
    raw_rules = ClassicalRuleRegistry.get_canonical_rules()
    matched = next((r for r in raw_rules if r["rule_id"] == rule_id), None)
    if not matched:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Classical rule {rule_id} not found.")

    cit = matched["citation"]
    return {
        "rule_id": matched["rule_id"],
        "rule_name": matched["rule_name"],
        "category": matched["category"],
        "brief_description": matched["brief_description"],
        "citation": {
            "book_title": cit.book_title,
            "author": cit.author,
            "chapter": cit.chapter,
            "chapter_name": cit.chapter_name,
            "sloka_range": cit.sloka_range,
            "sanskrit_iast": cit.sanskrit_iast,
            "sanskrit_devanagari": cit.sanskrit_devanagari,
            "translation_english": cit.translation_english,
            "tradition": cit.tradition.value,
            "commentary_notes": cit.commentary_notes,
            "is_verified": cit.is_verified,
        },
        "requirements": [
            {
                "condition_id": req.condition_id,
                "description": req.description,
                "condition_type": req.condition_type,
                "required_parameters": req.required_parameters,
                "is_mandatory": req.is_mandatory,
            }
            for req in matched["requirements"]
        ],
        "cancellation_factors": [
            {
                "factor_id": c.factor_id,
                "description": c.description,
                "classical_reference": c.classical_reference,
                "impact_deduction": c.impact_deduction,
            }
            for c in matched.get("cancellation_factors", [])
        ],
    }


@router.post("/evaluate-chart", response_model=EvaluateChartRuleEvidenceResponse)
async def evaluate_chart_rule_evidence(
    body: EvaluateChartRuleEvidenceRequest,
) -> EvaluateChartRuleEvidenceResponse:
    """
    Evaluates computed chart conditions against the classical rule catalog
    and outputs the deterministic 5-stage evidence chain for each rule.
    """
    engine = ClassicalRuleEvidenceEngine()
    chains = engine.evaluate_chart_evidence(
        chart_data=body.chart,
        rule_ids=body.rule_ids,
        category_filter=body.category_filter,
    )

    satisfied = sum(1 for c in chains if c.status.value == "SATISFIED")
    partial = sum(1 for c in chains if c.status.value == "PARTIALLY_SATISFIED")
    cancelled = sum(1 for c in chains if c.status.value == "CANCELLED_AFFLICTED")

    return EvaluateChartRuleEvidenceResponse(
        evaluated_chart_id=body.chart.get("id") or body.chart.get("chart_id"),
        total_rules_evaluated=len(chains),
        satisfied_rules_count=satisfied,
        partially_satisfied_count=partial,
        cancelled_count=cancelled,
        evidence_chains=[_to_schema_evidence_chain(c) for c in chains],
    )

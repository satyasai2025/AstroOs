"""
AstroOS — Research Knowledge & Evidence Intelligence Router (Priority 16)

Endpoints:
  - POST /api/v1/research/evidence/query
  - GET  /api/v1/research/evidence/synergies
  - GET  /api/v1/research/evidence/conditions
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.domain.evidence_intelligence import EvidenceGrade
from apps.api.schemas.evidence_intelligence import (
    CombinationSynergyItem,
    ContextualConditionRuleItem,
    EvidenceIntelligenceReportResponse,
    EvidenceQueryRequest,
    TechniqueEvidenceItem,
)
from apps.api.services.evidence_intelligence_engine import EvidenceIntelligenceEngine

router = APIRouter(prefix="/research/evidence", tags=["Research: Knowledge & Evidence Intelligence Engine"])


def _map_condition(c) -> ContextualConditionRuleItem:
    return ContextualConditionRuleItem(
        condition_id=c.condition_id,
        technique_id=c.technique_id,
        condition_expression=c.condition_expression,
        description=c.description,
        condition_type=c.condition_type,
        baseline_hit_rate=c.baseline_hit_rate,
        conditional_hit_rate=c.conditional_hit_rate,
        effect_delta_percent=c.effect_delta_percent,
        sample_size_n=c.sample_size_n,
        confidence_score=c.confidence_score,
    )


def _map_synergy(s) -> CombinationSynergyItem:
    return CombinationSynergyItem(
        synergy_id=s.synergy_id,
        target_objective=s.target_objective,
        technique_a_id=s.technique_a_id,
        technique_a_name=s.technique_a_name,
        technique_b_id=s.technique_b_id,
        technique_b_name=s.technique_b_name,
        technique_a_hit_rate=s.technique_a_hit_rate,
        technique_b_hit_rate=s.technique_b_hit_rate,
        joint_synergistic_hit_rate=s.joint_synergistic_hit_rate,
        synergy_multiplier=s.synergy_multiplier,
        statistical_lift_percent=s.statistical_lift_percent,
        sample_size_n=s.sample_size_n,
        p_value=s.p_value,
        is_synergy_confirmed=s.is_synergy_confirmed,
        explanation=s.explanation,
    )


@router.post("/query", response_model=EvidenceIntelligenceReportResponse, status_code=status.HTTP_200_OK)
def query_evidence_report(req: EvidenceQueryRequest) -> EvidenceIntelligenceReportResponse:
    """Executes a scientific query across the evidence knowledge layer."""
    engine = EvidenceIntelligenceEngine()
    grade_enum = None
    if req.min_confidence_grade:
        try:
            grade_enum = EvidenceGrade(req.min_confidence_grade.upper())
        except ValueError:
            grade_enum = None

    report = engine.query_evidence_report(
        target_objective=req.target_objective,
        min_confidence_grade=grade_enum,
    )

    return EvidenceIntelligenceReportResponse(
        report_id=report.report_id,
        target_objective=report.target_objective,
        timestamp=report.timestamp,
        total_techniques_evaluated=report.total_techniques_evaluated,
        grade_a_count=report.grade_a_count,
        grade_b_count=report.grade_b_count,
        grade_c_count=report.grade_c_count,
        grade_d_count=report.grade_d_count,
        ranked_techniques=[
            TechniqueEvidenceItem(
                technique_id=t.technique_id,
                technique_name=t.technique_name,
                target_objective=t.target_objective,
                historical_sample_size_n=t.historical_sample_size_n,
                empirical_hit_rate=t.empirical_hit_rate,
                baseline_rate=t.baseline_rate,
                odds_ratio=t.odds_ratio,
                p_value=t.p_value,
                brier_score=t.brier_score,
                roc_auc=t.roc_auc,
                confidence_grade=t.confidence_grade.value,
                amplifying_conditions=[_map_condition(c) for c in t.amplifying_conditions],
                attenuating_conditions=[_map_condition(c) for c in t.attenuating_conditions],
                classical_provenance=t.classical_provenance,
                epistemic_summary=t.epistemic_summary,
            )
            for t in report.ranked_techniques
        ],
        top_synergies=[_map_synergy(s) for s in report.top_synergies],
        key_condition_rules=[_map_condition(c) for c in report.key_condition_rules],
        epistemic_synthesis=report.epistemic_synthesis,
        methodological_provenance=report.methodological_provenance,
    )


@router.get("/synergies", response_model=list[CombinationSynergyItem], status_code=status.HTTP_200_OK)
def list_evidence_synergies(objective: Optional[str] = Query(default=None)) -> list[CombinationSynergyItem]:
    """Retrieves all pairwise cross-technique synergistic combinations and statistical lifts."""
    engine = EvidenceIntelligenceEngine()
    synergies = engine.list_all_synergies(target_objective=objective)
    return [_map_synergy(s) for s in synergies]


@router.get("/conditions", response_model=list[ContextualConditionRuleItem], status_code=status.HTTP_200_OK)
def list_contextual_conditions(objective: Optional[str] = Query(default=None)) -> list[ContextualConditionRuleItem]:
    """Retrieves all contextual condition rules (Amplifiers & Attenuators)."""
    engine = EvidenceIntelligenceEngine()
    conditions = engine.list_all_conditions(target_objective=objective)
    return [_map_condition(c) for c in conditions]

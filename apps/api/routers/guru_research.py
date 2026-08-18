"""
AstroOS — Guru Research Router

API endpoints for evaluating charts and retrieving partition rules
for the Guru Research Layer.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from apps.api.schemas.guru_research import (
    ChartEvaluationRequest,
    GuruChartEvaluationResponse,
    PlanetEvaluationResponse,
    GuruRulesRegistryResponse,
    GuruRuleResponse,
)
from apps.api.services.guru_research_engine import GuruResearchEngine

router = APIRouter(prefix="/research/guru-layer", tags=["Research / Guru Layer"])
_engine = GuruResearchEngine()


@router.get(
    "/rules",
    response_model=GuruRulesRegistryResponse,
    summary="Get all registered Guru Research Layer degree partition rules",
)
def get_guru_layer_rules() -> GuruRulesRegistryResponse:
    """Retrieve all current degree-slice rules for all 12 signs."""
    rules_dict = _engine.get_all_rules()
    formatted = {}
    for rashi, rlist in rules_dict.items():
        formatted[rashi] = [
            GuruRuleResponse(
                start_deg=r["start_deg"],
                end_deg=r["end_deg"],
                zone_type=r["zone_type"],
                ruling_planet=r["ruling_planet"],
                description=r["description"],
                strength_weight=r["strength_weight"],
            )
            for r in rlist
        ]
    return GuruRulesRegistryResponse(partitions=formatted)


@router.post(
    "/evaluate",
    response_model=GuruChartEvaluationResponse,
    summary="Evaluate planetary positions against the Guru Research Layer",
)
def evaluate_chart_guru_layer(
    request: ChartEvaluationRequest,
) -> GuruChartEvaluationResponse:
    """
    Evaluates a list of planetary positions against both classical Parashari
    dignities and the Guru Research Layer degree slices.
    """
    try:
        positions_raw = [
            {
                "planet": p.planet,
                "rashi": p.rashi,
                "degree_in_rashi": p.degree_in_rashi,
            }
            for p in request.positions
        ]
        result = _engine.evaluate_chart(positions_raw)

        evaluations_response = [
            PlanetEvaluationResponse(
                planet=e.planet,
                rashi=e.rashi,
                degree_in_rashi=e.degree_in_rashi,
                classical_dignity=e.classical_dignity,
                guru_zone_name=e.guru_zone_name,
                guru_zone_type=e.guru_zone_type.value,
                guru_zone_lord=e.guru_zone_lord,
                guru_zone_range=e.guru_zone_range,
                is_ruler_match=e.is_ruler_match,
                is_dignity_agreement=e.is_dignity_agreement,
                notes=e.notes,
            )
            for e in result.evaluations
        ]

        return GuruChartEvaluationResponse(
            evaluations=evaluations_response,
            agreements_count=result.agreements_count,
            deviations_count=result.deviations_count,
            summary_insights=result.summary_insights,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating chart under Guru Research Layer: {str(exc)}",
        )

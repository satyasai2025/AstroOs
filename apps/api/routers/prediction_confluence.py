"""
AstroOS — Unified Multi-System Prediction Confluence Router (Module 23, Priority 8)

API endpoints for:
- POST /api/v1/predictions/confluence/synthesize
- POST /api/v1/predictions/confluence/scan
- POST /api/v1/predictions/confluence/freeze-to-p7
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, HTTPException, status

from apps.api.domain.prediction_confluence import (
    ConfluenceMatrix,
    EmpiricalTrackRecord,
    SynthesizedTimingWindow,
    SynthesizedVerdict,
    SystemContribution,
    UnifiedPredictionSynthesis,
)
from apps.api.domain.prediction_validation import (
    PredictionCategory,
    TemporalSplitType,
)
from apps.api.schemas.prediction_confluence import (
    ConfluenceDomainScanRequest,
    ConfluenceDomainScanResponse,
    ConfluenceSynthesisRequest,
    ConfluenceSynthesisResponse,
    DomainScanItem,
    FreezeToP7Request,
    FreezeToP7Response,
    UnifiedPredictionSynthesisSchema,
)
from apps.api.services.prediction_confluence_engine import PredictionConfluenceEngine

router = APIRouter(prefix="/predictions/confluence", tags=["Prediction Confluence & Synthesis"])
_engine = PredictionConfluenceEngine()

# In-memory synthesis cache for quick retrieval and freeze
_synthesis_cache: dict[str, UnifiedPredictionSynthesis] = {}


def _get_or_create_chart_data(request_chart_data: dict[str, Any] | None, chart_id: str | None) -> dict[str, Any]:
    if request_chart_data:
        return request_chart_data
    # Fallback benchmark / test chart
    return {
        "chart_id": chart_id or "chart_benchmark_raman",
        "subject_name": "Dr. B.V. Raman",
        "birth_utc": "1912-08-08T19:35:00+00:00",
        "ascendant": {"rashi": "Aquarius", "longitude": 314.5, "rashi_degree": 14.5},
        "planets": [
            {"planet": "Sun", "rashi": "Cancer", "house_number": 6, "sidereal_longitude": 113.2, "is_retrograde": False},
            {"planet": "Moon", "rashi": "Taurus", "house_number": 4, "sidereal_longitude": 53.8, "is_retrograde": False},
            {"planet": "Mars", "rashi": "Leo", "house_number": 7, "sidereal_longitude": 141.4, "is_retrograde": False},
            {"planet": "Mercury", "rashi": "Leo", "house_number": 7, "sidereal_longitude": 134.1, "is_retrograde": False},
            {"planet": "Jupiter", "rashi": "Scorpio", "house_number": 10, "sidereal_longitude": 232.9, "is_retrograde": False},
            {"planet": "Venus", "rashi": "Virgo", "house_number": 8, "sidereal_longitude": 152.6, "is_retrograde": False},
            {"planet": "Saturn", "rashi": "Taurus", "house_number": 4, "sidereal_longitude": 40.2, "is_retrograde": False},
            {"planet": "Rahu", "rashi": "Pisces", "house_number": 2, "sidereal_longitude": 345.1, "is_retrograde": True},
            {"planet": "Ketu", "rashi": "Virgo", "house_number": 8, "sidereal_longitude": 165.1, "is_retrograde": True},
        ],
        "houses": [
            {"house_number": 1, "rashi": "Aquarius", "sign_lord": "Saturn", "cusp_longitude": 314.5},
            {"house_number": 2, "rashi": "Pisces", "sign_lord": "Jupiter", "cusp_longitude": 344.5},
            {"house_number": 3, "rashi": "Aries", "sign_lord": "Mars", "cusp_longitude": 14.5},
            {"house_number": 4, "rashi": "Taurus", "sign_lord": "Venus", "cusp_longitude": 44.5},
            {"house_number": 5, "rashi": "Gemini", "sign_lord": "Mercury", "cusp_longitude": 74.5},
            {"house_number": 6, "rashi": "Cancer", "sign_lord": "Moon", "cusp_longitude": 104.5},
            {"house_number": 7, "rashi": "Leo", "sign_lord": "Sun", "cusp_longitude": 134.5},
            {"house_number": 8, "rashi": "Virgo", "sign_lord": "Mercury", "cusp_longitude": 164.5},
            {"house_number": 9, "rashi": "Libra", "sign_lord": "Venus", "cusp_longitude": 194.5},
            {"house_number": 10, "rashi": "Scorpio", "sign_lord": "Mars", "cusp_longitude": 224.5},
            {"house_number": 11, "rashi": "Sagittarius", "sign_lord": "Jupiter", "cusp_longitude": 254.5},
            {"house_number": 12, "rashi": "Capricorn", "sign_lord": "Saturn", "cusp_longitude": 284.5},
        ],
    }


def _synthesis_to_schema(syn: UnifiedPredictionSynthesis) -> UnifiedPredictionSynthesisSchema:
    from apps.api.schemas.prediction_confluence import (
        ConfluenceMatrixSchema,
        EmpiricalTrackRecordSchema,
        SynthesizedTimingWindowSchema,
        SystemContributionSchema,
    )
    return UnifiedPredictionSynthesisSchema(
        synthesis_id=syn.synthesis_id,
        chart_id=syn.chart_id,
        subject_name=syn.subject_name,
        category=syn.category,
        synthesized_event_description=syn.synthesized_event_description,
        confluence_matrix=ConfluenceMatrixSchema(
            supporting_count=syn.confluence_matrix.supporting_count,
            veto_count=syn.confluence_matrix.veto_count,
            neutral_count=syn.confluence_matrix.neutral_count,
            total_systems=syn.confluence_matrix.total_systems,
            confluence_ratio=syn.confluence_matrix.confluence_ratio,
            active_vetoes=syn.confluence_matrix.active_vetoes,
            synthesized_verdict=syn.confluence_matrix.synthesized_verdict,
            verdict_rationale=syn.confluence_matrix.verdict_rationale,
        ),
        system_contributions=[
            SystemContributionSchema(
                system_id=c.system_id,
                system_name=c.system_name,
                support_status=c.support_status,
                provenance_type=c.provenance_type,
                primary_houses=c.primary_houses,
                active_significators=c.active_significators,
                rule_or_factor=c.rule_or_factor,
                rationale=c.rationale,
                veto_reason=c.veto_reason,
                evidence_snapshot=c.evidence_snapshot,
            )
            for c in syn.system_contributions
        ],
        synthesized_timing_window=SynthesizedTimingWindowSchema(
            window_start=syn.synthesized_timing_window.window_start,
            window_end=syn.synthesized_timing_window.window_end,
            peak_fructification_date=syn.synthesized_timing_window.peak_fructification_date,
            dasha_sub_period=syn.synthesized_timing_window.dasha_sub_period,
            transit_trigger=syn.synthesized_timing_window.transit_trigger,
            sbc_trigger_moment=syn.synthesized_timing_window.sbc_trigger_moment,
        ),
        empirical_track_record=EmpiricalTrackRecordSchema(
            historical_hit_rate=syn.empirical_track_record.historical_hit_rate,
            historical_precision=syn.empirical_track_record.historical_precision,
            sample_size=syn.empirical_track_record.sample_size,
            wilson_95_ci=syn.empirical_track_record.wilson_95_ci,
            sample_size_warning=syn.empirical_track_record.sample_size_warning,
            matched_cohort_name=syn.empirical_track_record.matched_cohort_name,
        ),
        provenance_breakdown=syn.provenance_breakdown,
        synthesis_timestamp=syn.synthesis_timestamp,
        synthesis_hash=syn.synthesis_hash,
    )


@router.post(
    "/synthesize",
    response_model=ConfluenceSynthesisResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize unified multi-system prediction for a chart and domain",
)
def synthesize_prediction(req: ConfluenceSynthesisRequest) -> ConfluenceSynthesisResponse:
    chart_data = _get_or_create_chart_data(req.chart_data, req.chart_id)
    synthesis = _engine.synthesize(
        chart_data=chart_data,
        category=req.category,
        target_datetime=req.target_datetime,
        horizon_months=req.horizon_months,
    )
    _synthesis_cache[synthesis.synthesis_id] = synthesis
    return ConfluenceSynthesisResponse(synthesis=_synthesis_to_schema(synthesis))


@router.post(
    "/scan",
    response_model=ConfluenceDomainScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan multi-system confluence across all canonical life domains",
)
def scan_domains(req: ConfluenceDomainScanRequest) -> ConfluenceDomainScanResponse:
    chart_data = _get_or_create_chart_data(req.chart_data, req.chart_id)
    domains = [
        PredictionCategory.CAREER,
        PredictionCategory.MARRIAGE,
        PredictionCategory.FINANCE,
        PredictionCategory.HEALTH,
    ]
    scanned_items: list[DomainScanItem] = []

    for dom in domains:
        syn = _engine.synthesize(
            chart_data=chart_data,
            category=dom,
            target_datetime=req.target_datetime,
            horizon_months=req.horizon_months,
        )
        _synthesis_cache[syn.synthesis_id] = syn
        scanned_items.append(
            DomainScanItem(
                category=syn.category,
                event_description=syn.synthesized_event_description,
                confluence_verdict=syn.confluence_matrix.synthesized_verdict,
                confluence_ratio=syn.confluence_matrix.confluence_ratio,
                supporting_count=syn.confluence_matrix.supporting_count,
                veto_count=syn.confluence_matrix.veto_count,
                active_vetoes=syn.confluence_matrix.active_vetoes,
                peak_timing=syn.synthesized_timing_window.peak_fructification_date,
            )
        )

    return ConfluenceDomainScanResponse(
        chart_id=chart_data.get("chart_id", "chart_default"),
        subject_name=chart_data.get("subject_name", "Dr. B.V. Raman"),
        scanned_domains=scanned_items,
        scan_timestamp=datetime.now(timezone.utc),
    )


@router.post(
    "/freeze-to-p7",
    response_model=FreezeToP7Response,
    status_code=status.HTTP_201_CREATED,
    summary="Freeze synthesized multi-system prediction into an immutable P7 validation snapshot",
)
def freeze_to_p7(req: FreezeToP7Request) -> FreezeToP7Response:
    synthesis = _synthesis_cache.get(req.synthesis_id)
    if not synthesis and req.synthesis_payload:
        # Reconstruct domain object from payload
        p = req.synthesis_payload
        matrix = ConfluenceMatrix(
            supporting_count=p.confluence_matrix.supporting_count,
            veto_count=p.confluence_matrix.veto_count,
            neutral_count=p.confluence_matrix.neutral_count,
            total_systems=p.confluence_matrix.total_systems,
            confluence_ratio=p.confluence_matrix.confluence_ratio,
            active_vetoes=p.confluence_matrix.active_vetoes,
            synthesized_verdict=p.confluence_matrix.synthesized_verdict,
            verdict_rationale=p.confluence_matrix.verdict_rationale,
        )
        contribs = [
            SystemContribution(
                system_id=c.system_id,
                system_name=c.system_name,
                support_status=c.support_status,
                provenance_type=c.provenance_type,
                primary_houses=c.primary_houses,
                active_significators=c.active_significators,
                rule_or_factor=c.rule_or_factor,
                rationale=c.rationale,
                veto_reason=c.veto_reason,
                evidence_snapshot=c.evidence_snapshot,
            )
            for c in p.system_contributions
        ]
        timing = SynthesizedTimingWindow(
            window_start=p.synthesized_timing_window.window_start,
            window_end=p.synthesized_timing_window.window_end,
            peak_fructification_date=p.synthesized_timing_window.peak_fructification_date,
            dasha_sub_period=p.synthesized_timing_window.dasha_sub_period,
            transit_trigger=p.synthesized_timing_window.transit_trigger,
            sbc_trigger_moment=p.synthesized_timing_window.sbc_trigger_moment,
        )
        emp = EmpiricalTrackRecord(
            historical_hit_rate=p.empirical_track_record.historical_hit_rate,
            historical_precision=p.empirical_track_record.historical_precision,
            sample_size=p.empirical_track_record.sample_size,
            wilson_95_ci=p.empirical_track_record.wilson_95_ci,
            sample_size_warning=p.empirical_track_record.sample_size_warning,
            matched_cohort_name=p.empirical_track_record.matched_cohort_name,
        )
        synthesis = UnifiedPredictionSynthesis(
            synthesis_id=p.synthesis_id,
            chart_id=p.chart_id,
            subject_name=p.subject_name,
            category=p.category,
            synthesized_event_description=p.synthesized_event_description,
            confluence_matrix=matrix,
            system_contributions=contribs,
            synthesized_timing_window=timing,
            empirical_track_record=emp,
            provenance_breakdown=p.provenance_breakdown,
            synthesis_timestamp=p.synthesis_timestamp,
        )

    if not synthesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis with ID '{req.synthesis_id}' not found in active session cache.",
        )

    snapshot = _engine.freeze_to_p7(synthesis, target_split_type=req.target_split_type)

    return FreezeToP7Response(
        prediction_id=snapshot.prediction_id,
        chart_id=snapshot.chart_id,
        subject_name=snapshot.subject_name,
        technique=snapshot.technique,
        category=snapshot.category,
        evidence_hash=snapshot.evidence_hash,
        frozen_timestamp=snapshot.prediction_timestamp,
        status="FROZEN_IMMUTABLE",
        message="Synthesized multi-system prediction successfully frozen into P7 validation registry with SHA-256 evidence integrity.",
    )

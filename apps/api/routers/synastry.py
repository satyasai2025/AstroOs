"""
AstroOS — Inter-Chart Synastry, Ashta-Kuta & Confluence Router (Priority 13)

Endpoints:
  - POST /api/v1/research/synastry/ashtakuta
  - POST /api/v1/research/synastry/matrix
  - GET  /api/v1/research/synastry/kutas
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.schemas.synastry import (
    AshtaKutaEvaluateRequest,
    AshtaKutaResponse,
    DoshaPariharaItem,
    InterChartAspectItem,
    JointConfluenceWindowItem,
    KutaEvaluationItem,
    CrossHouseOverlayItem,
    SynastryMatrixEvaluateRequest,
    SynastryMatrixResponse,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.synastry_engine import AshtaKutaEngine, SynastryEngine

router = APIRouter(prefix="/research/synastry", tags=["Research: Inter-Chart Synastry & Compatibility"])


@router.post("/ashtakuta", response_model=AshtaKutaResponse, status_code=status.HTTP_200_OK)
def evaluate_ashtakuta(req: AshtaKutaEvaluateRequest) -> AshtaKutaResponse:
    """Evaluate classical 36-Guna Ashta-Kuta with explicit dosha mitigations and provenance."""
    evals, pariharas = AshtaKutaEngine.evaluate(
        moon_a_rashi=req.partner_a_rashi,
        moon_a_nakshatra=req.partner_a_nakshatra,
        moon_a_pada=req.partner_a_pada,
        moon_b_rashi=req.partner_b_rashi,
        moon_b_nakshatra=req.partner_b_nakshatra,
        moon_b_pada=req.partner_b_pada,
    )

    total_pts = sum(k.obtained_points for k in evals)
    pct = (total_pts / 36.0) * 100.0

    eval_items = [
        KutaEvaluationItem(
            kuta=k.kuta.value,
            label=k.label,
            obtained_points=k.obtained_points,
            max_points=k.max_points,
            partner_a_attribute=k.partner_a_attribute,
            partner_b_attribute=k.partner_b_attribute,
            raw_relationship=k.raw_relationship,
            is_mitigated=k.is_mitigated,
            cancellation_reason=k.cancellation_reason,
            description=k.description,
            classical_source=k.classical_source,
        )
        for k in evals
    ]

    parihara_items = [
        DoshaPariharaItem(
            dosha_name=p.dosha_name,
            is_present=p.is_present,
            is_cancelled=p.is_cancelled,
            parihara_rule=p.parihara_rule,
            classical_reference=p.classical_reference,
            explanation=p.explanation,
        )
        for p in pariharas
    ]

    summary = (
        f"Ashta-Kuta Total Gunas: {total_pts:.1f}/36.0 ({pct:.1f}%). "
        f"Active Mitigations: {len([p for p in pariharas if p.is_cancelled])}. "
        "Evaluated with Brihat Parashara Hora Shastra and Muhurta Chintamani classical provenance."
    )

    return AshtaKutaResponse(
        evaluations=eval_items,
        total_guna_obtained=total_pts,
        max_guna_possible=36.0,
        guna_percentage=pct,
        dosha_pariharas=parihara_items,
        summary=summary,
    )


@router.post("/matrix", response_model=SynastryMatrixResponse, status_code=status.HTTP_200_OK)
def evaluate_synastry_matrix(
    req: SynastryMatrixEvaluateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> SynastryMatrixResponse:
    """Evaluate full inter-chart synastry matrix: Ashta-Kuta, aspects, overlays & joint confluence timing."""
    horoscope_engine = HoroscopeEngine(wrapper)
    dasha_engine = DashaEngine(wrapper)
    synastry_engine = SynastryEngine()

    # Build D1 Charts
    chart_a = horoscope_engine.generate_d1(
        req.chart_a_birth.datetime_utc,
        req.chart_a_birth.latitude,
        req.chart_a_birth.longitude,
        ayanamsa=req.chart_a_birth.ayanamsa,
    )
    chart_b = horoscope_engine.generate_d1(
        req.chart_b_birth.datetime_utc,
        req.chart_b_birth.latitude,
        req.chart_b_birth.longitude,
        ayanamsa=req.chart_b_birth.ayanamsa,
    )

    # Build Dasha Trees
    dasha_tree_a = dasha_engine.compute_vimshottari(
        req.chart_a_birth.datetime_utc,
        req.chart_a_birth.latitude,
        req.chart_a_birth.longitude,
        ayanamsa=req.chart_a_birth.ayanamsa,
        max_depth=3,
    )
    dasha_tree_b = dasha_engine.compute_vimshottari(
        req.chart_b_birth.datetime_utc,
        req.chart_b_birth.latitude,
        req.chart_b_birth.longitude,
        ayanamsa=req.chart_b_birth.ayanamsa,
        max_depth=3,
    )

    matrix = synastry_engine.evaluate_synastry(
        chart_a=chart_a,
        chart_b=chart_b,
        chart_a_name=req.chart_a_birth.name,
        chart_b_name=req.chart_b_birth.name,
        dasha_tree_a=dasha_tree_a,
        dasha_tree_b=dasha_tree_b,
        target_start=req.target_start_date,
        target_end=req.target_end_date,
        objective=req.objective,
    )

    eval_items = [
        KutaEvaluationItem(
            kuta=k.kuta.value,
            label=k.label,
            obtained_points=k.obtained_points,
            max_points=k.max_points,
            partner_a_attribute=k.partner_a_attribute,
            partner_b_attribute=k.partner_b_attribute,
            raw_relationship=k.raw_relationship,
            is_mitigated=k.is_mitigated,
            cancellation_reason=k.cancellation_reason,
            description=k.description,
            classical_source=k.classical_source,
        )
        for k in matrix.ashta_kuta_evaluations
    ]

    parihara_items = [
        DoshaPariharaItem(
            dosha_name=p.dosha_name,
            is_present=p.is_present,
            is_cancelled=p.is_cancelled,
            parihara_rule=p.parihara_rule,
            classical_reference=p.classical_reference,
            explanation=p.explanation,
        )
        for p in matrix.dosha_pariharas
    ]

    aspect_items = [
        InterChartAspectItem(
            planet_a=a.planet_a,
            planet_b=a.planet_b,
            longitude_a=a.longitude_a,
            longitude_b=a.longitude_b,
            angle_degrees=a.angle_degrees,
            aspect_type=a.aspect_type,
            orb_degrees=a.orb_degrees,
            is_harmonious=a.is_harmonious,
            interpretation=a.interpretation,
        )
        for a in matrix.inter_chart_aspects
    ]

    overlay_items = [
        CrossHouseOverlayItem(
            planet_a=o.planet_a,
            chart_a_house=o.chart_a_house,
            chart_b_house_occupied=o.chart_b_house_occupied,
            rashi_in_chart_b=o.rashi_in_chart_b,
            functional_impact=o.functional_impact,
        )
        for o in matrix.cross_house_overlays
    ]

    joint_window_items = [
        JointConfluenceWindowItem(
            start_date=w.start_date,
            end_date=w.end_date,
            chart_a_density_score=w.chart_a_density_score,
            chart_b_density_score=w.chart_b_density_score,
            joint_confluence_density=w.joint_confluence_density,
            chart_a_active_systems=list(w.chart_a_active_systems),
            chart_b_active_systems=list(w.chart_b_active_systems),
            objective=w.objective,
            synthesis_notes=w.synthesis_notes,
        )
        for w in matrix.joint_confluence_windows
    ]

    return SynastryMatrixResponse(
        chart_a_name=matrix.chart_a_name,
        chart_b_name=matrix.chart_b_name,
        evaluated_at=matrix.evaluated_at,
        ashta_kuta_evaluations=eval_items,
        total_guna_obtained=matrix.total_guna_obtained,
        max_guna_possible=matrix.max_guna_possible,
        guna_percentage=matrix.guna_percentage,
        dosha_pariharas=parihara_items,
        inter_chart_aspects=aspect_items,
        cross_house_overlays=overlay_items,
        joint_confluence_windows=joint_window_items,
        structural_summary=matrix.structural_summary,
        timing_summary=matrix.timing_summary,
        provenance_notes=matrix.provenance_notes,
    )


@router.get("/kutas", status_code=status.HTTP_200_OK)
def list_kuta_metadata() -> dict[str, Any]:
    """Lists the 8 classical Ashta-Kutas, their point allocations, and primary classical sources."""
    return {
        "ashta_kutas": [
            {"kuta": "varna", "max_points": 1.0, "category": "Work & Spiritual Egos", "source": "BPHS Ch. 73"},
            {"kuta": "vashya", "max_points": 2.0, "category": "Mutual Dominance & Magnetic Harmony", "source": "Muhurta Chintamani Sloka 12"},
            {"kuta": "tara", "max_points": 3.0, "category": "Longevity & Destiny Rhythm", "source": "BPHS Ch. 73 Sloka 10"},
            {"kuta": "yoni", "max_points": 4.0, "category": "Biological & Physical Affinity", "source": "Muhurta Chintamani Sloka 16"},
            {"kuta": "graha_maitri", "max_points": 5.0, "category": "Mental & Psychological Resonance", "source": "BPHS Ch. 73 Sloka 18"},
            {"kuta": "gana", "max_points": 6.0, "category": "Temperament & Behavioral Alignment", "source": "Muhurta Chintamani Sloka 22"},
            {"kuta": "bhakoot", "max_points": 7.0, "category": "Emotional Bonding & Family Prosperity", "source": "BPHS Ch. 73 Sloka 26"},
            {"kuta": "nadi", "max_points": 8.0, "category": "Physiology, Progeny & Genetic Health", "source": "Muhurta Chintamani Sloka 32"},
        ],
        "total_max_points": 36.0,
        "supported_dosha_mitigations": [
            "Nadi Dosha Parihara (Pada Difference, Common Rashi, Common Lord)",
            "Bhakoot Dosha Parihara (Same Planetary Lord, Mutual Planetary Friendship)",
            "Gana Dosha Parihara (Rashi Lord Friendship / Identity)",
        ],
    }

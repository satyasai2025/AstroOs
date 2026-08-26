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
    BirthInput,
    CompositeChartResponse,
    CompositePlanetSchema,
    CrossHouseOverlayItem,
    DasaKutaEvaluateRequest,
    DasaKutaItemSchema,
    DasaKutaResponse,
    DoshaPariharaItem,
    FullCompatibilityRequest,
    FullCompatibilityResponse,
    InterChartAspectItem,
    JointConfluenceWindowItem,
    KutaEvaluationItem,
    KujaDoshaComparisonSchema,
    KujaDoshaProfileSchema,
    NavamshaSynastrySchema,
    SynastryMatrixEvaluateRequest,
    SynastryMatrixResponse,
    UpapadaCompatibilitySchema,
)
from apps.api.services.composite_chart_engine import CompositeChartEngine
from apps.api.services.dasa_kuta_engine import DasaKutaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.jaimini_navamsha_synastry import JaiminiNavamshaSynastry
from apps.api.services.kuja_dosha_engine import KujaDoshaEngine
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


# ── 1. Kuja Dosha (Manglik) Endpoint ──────────────────────────────────────────


@router.post("/kuja-dosha", response_model=KujaDoshaComparisonSchema, status_code=status.HTTP_200_OK)
def evaluate_kuja_dosha_endpoint(
    req: SynastryMatrixEvaluateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> KujaDoshaComparisonSchema:
    """Evaluate Tri-Bhava Kuja Dosha (Lagna, Moon, Venus) and 10 Classical Pariharas."""
    horoscope = HoroscopeEngine(wrapper)
    chart_a = horoscope.generate_d1(req.chart_a_birth.datetime_utc, req.chart_a_birth.latitude, req.chart_a_birth.longitude, req.chart_a_birth.ayanamsa)
    chart_b = horoscope.generate_d1(req.chart_b_birth.datetime_utc, req.chart_b_birth.latitude, req.chart_b_birth.longitude, req.chart_b_birth.ayanamsa)

    comp = KujaDoshaEngine.compare_charts(chart_a, chart_b, req.chart_a_birth.name, req.chart_b_birth.name)

    return KujaDoshaComparisonSchema(
        partner_a=KujaDoshaProfileSchema(
            chart_name=comp.partner_a.chart_name,
            has_dosha=comp.partner_a.has_dosha,
            severity=comp.partner_a.severity,
            house_from_lagna=comp.partner_a.house_from_lagna,
            house_from_moon=comp.partner_a.house_from_moon,
            house_from_venus=comp.partner_a.house_from_venus,
            raw_dosha_points=comp.partner_a.raw_dosha_points,
            effective_dosha_score=comp.partner_a.effective_dosha_score,
            pariharas_applied=list(comp.partner_a.pariharas_applied),
            is_cancelled=comp.partner_a.is_cancelled,
            explanation=comp.partner_a.explanation,
        ),
        partner_b=KujaDoshaProfileSchema(
            chart_name=comp.partner_b.chart_name,
            has_dosha=comp.partner_b.has_dosha,
            severity=comp.partner_b.severity,
            house_from_lagna=comp.partner_b.house_from_lagna,
            house_from_moon=comp.partner_b.house_from_moon,
            house_from_venus=comp.partner_b.house_from_venus,
            raw_dosha_points=comp.partner_b.raw_dosha_points,
            effective_dosha_score=comp.partner_b.effective_dosha_score,
            pariharas_applied=list(comp.partner_b.pariharas_applied),
            is_cancelled=comp.partner_b.is_cancelled,
            explanation=comp.partner_b.explanation,
        ),
        is_balanced=comp.is_balanced,
        dosha_difference=comp.dosha_difference,
        compatibility_verdict=comp.compatibility_verdict,
        classical_mitigation_notes=comp.classical_mitigation_notes,
    )


# ── 2. Dasa Kuta (10 Poruthams) Endpoint ──────────────────────────────────────


@router.post("/dasa-kuta", response_model=DasaKutaResponse, status_code=status.HTTP_200_OK)
def evaluate_dasa_kuta_endpoint(req: DasaKutaEvaluateRequest) -> DasaKutaResponse:
    """Evaluate South Indian 10-Porutham compatibility system."""
    res = DasaKutaEngine.evaluate(
        girl_rashi=req.girl_rashi,
        girl_nakshatra=req.girl_nakshatra,
        boy_rashi=req.boy_rashi,
        boy_nakshatra=req.boy_nakshatra,
    )

    items = [
        DasaKutaItemSchema(
            name=it.name,
            label=it.label,
            is_compatible=it.is_compatible,
            obtained_score=it.obtained_score,
            max_score=it.max_score,
            partner_a_value=it.partner_a_value,
            partner_b_value=it.partner_b_value,
            description=it.description,
            classical_source=it.classical_source,
        )
        for it in res.items
    ]

    return DasaKutaResponse(
        items=items,
        total_score=res.total_score,
        max_total_score=res.max_total_score,
        compatibility_percentage=res.compatibility_percentage,
        is_rajju_compatible=res.is_rajju_compatible,
        is_vedha_compatible=res.is_vedha_compatible,
        is_mahendra_present=res.is_mahendra_present,
        is_stree_deergha_present=res.is_stree_deergha_present,
        verdict=res.verdict,
        summary=res.summary,
    )


# ── 3. Upapada & Navamsha Compatibility Endpoint ──────────────────────────────


@router.post("/upapada", response_model=UpapadaCompatibilitySchema, status_code=status.HTTP_200_OK)
def evaluate_upapada_endpoint(
    req: SynastryMatrixEvaluateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> UpapadaCompatibilitySchema:
    """Evaluate Jaimini Upapada Lagna (A12) alignment and 2nd house marital sustenance."""
    horoscope = HoroscopeEngine(wrapper)
    chart_a = horoscope.generate_d1(req.chart_a_birth.datetime_utc, req.chart_a_birth.latitude, req.chart_a_birth.longitude, req.chart_a_birth.ayanamsa)
    chart_b = horoscope.generate_d1(req.chart_b_birth.datetime_utc, req.chart_b_birth.latitude, req.chart_b_birth.longitude, req.chart_b_birth.ayanamsa)

    up = JaiminiNavamshaSynastry.evaluate_upapada_compatibility(chart_a, chart_b)
    return UpapadaCompatibilitySchema(
        ul_rashi_a=up.ul_rashi_a,
        ul_rashi_b=up.ul_rashi_b,
        lagna_rashi_a=up.lagna_rashi_a,
        lagna_rashi_b=up.lagna_rashi_b,
        moon_rashi_a=up.moon_rashi_a,
        moon_rashi_b=up.moon_rashi_b,
        alignment_type=up.alignment_type,
        is_harmonious=up.is_harmonious,
        second_from_ul_status_a=up.second_from_ul_status_a,
        second_from_ul_status_b=up.second_from_ul_status_b,
        jaimini_compatibility_score=up.jaimini_compatibility_score,
        explanation=up.explanation,
    )


@router.post("/navamsha", response_model=NavamshaSynastrySchema, status_code=status.HTTP_200_OK)
def evaluate_navamsha_endpoint(
    req: SynastryMatrixEvaluateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> NavamshaSynastrySchema:
    """Evaluate D9 Navamsha harmonic cross-chart synastry."""
    horoscope = HoroscopeEngine(wrapper)
    chart_a = horoscope.generate_d1(req.chart_a_birth.datetime_utc, req.chart_a_birth.latitude, req.chart_a_birth.longitude, req.chart_a_birth.ayanamsa)
    chart_b = horoscope.generate_d1(req.chart_b_birth.datetime_utc, req.chart_b_birth.latitude, req.chart_b_birth.longitude, req.chart_b_birth.ayanamsa)

    nav = JaiminiNavamshaSynastry.evaluate_navamsha_synastry(chart_a, chart_b)
    return NavamshaSynastrySchema(
        d9_lagna_a=nav.d9_lagna_a,
        d9_lagna_b=nav.d9_lagna_b,
        lagna_relationship=nav.lagna_relationship,
        d9_moon_a=nav.d9_moon_a,
        d9_moon_b=nav.d9_moon_b,
        d9_venus_a=nav.d9_venus_a,
        d9_venus_b=nav.d9_venus_b,
        mutual_d9_trines=list(nav.mutual_d9_trines),
        navamsha_harmony_score=nav.navamsha_harmony_score,
        verdict=nav.verdict,
        explanation=nav.explanation,
    )


# ── 4. Composite Chart Endpoint ───────────────────────────────────────────────


@router.post("/composite", response_model=CompositeChartResponse, status_code=status.HTTP_200_OK)
def evaluate_composite_chart_endpoint(
    req: SynastryMatrixEvaluateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> CompositeChartResponse:
    """Computes midpoint composite relationship chart."""
    horoscope = HoroscopeEngine(wrapper)
    chart_a = horoscope.generate_d1(req.chart_a_birth.datetime_utc, req.chart_a_birth.latitude, req.chart_a_birth.longitude, req.chart_a_birth.ayanamsa)
    chart_b = horoscope.generate_d1(req.chart_b_birth.datetime_utc, req.chart_b_birth.latitude, req.chart_b_birth.longitude, req.chart_b_birth.ayanamsa)

    comp = CompositeChartEngine.calculate_composite_chart(chart_a, chart_b, req.chart_a_birth.name, req.chart_b_birth.name)

    asc = CompositePlanetSchema(
        planet=comp.composite_ascendant.planet,
        sidereal_longitude=comp.composite_ascendant.sidereal_longitude,
        rashi=comp.composite_ascendant.rashi,
        rashi_degree=comp.composite_ascendant.rashi_degree,
        house_number=comp.composite_ascendant.house_number,
    )

    planets = [
        CompositePlanetSchema(
            planet=p.planet,
            sidereal_longitude=p.sidereal_longitude,
            rashi=p.rashi,
            rashi_degree=p.rashi_degree,
            house_number=p.house_number,
        )
        for p in comp.composite_planets
    ]

    return CompositeChartResponse(
        chart_a_name=comp.chart_a_name,
        chart_b_name=comp.chart_b_name,
        composite_ascendant=asc,
        composite_planets=planets,
        relationship_purpose_summary=comp.relationship_purpose_summary,
    )


# ── 5. Full Compatibility Bundle Endpoint ─────────────────────────────────────


@router.post("/full-compatibility", response_model=FullCompatibilityResponse, status_code=status.HTTP_200_OK)
def evaluate_full_compatibility_endpoint(
    req: FullCompatibilityRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> FullCompatibilityResponse:
    """Unified comprehensive compatibility evaluation combining all classical & modern systems."""
    horoscope = HoroscopeEngine(wrapper)
    chart_a = horoscope.generate_d1(req.chart_a_birth.datetime_utc, req.chart_a_birth.latitude, req.chart_a_birth.longitude, req.chart_a_birth.ayanamsa)
    chart_b = horoscope.generate_d1(req.chart_b_birth.datetime_utc, req.chart_b_birth.latitude, req.chart_b_birth.longitude, req.chart_b_birth.ayanamsa)

    moon_a = next((p for p in chart_a.planets if p.planet.lower() == "moon"), None)
    moon_b = next((p for p in chart_b.planets if p.planet.lower() == "moon"), None)

    r_a = moon_a.rashi if moon_a else "aries"
    n_a = moon_a.nakshatra if moon_a else "ashwini"
    p_a = moon_a.pada if moon_a else 1

    r_b = moon_b.rashi if moon_b else "aries"
    n_b = moon_b.nakshatra if moon_b else "ashwini"
    p_b = moon_b.pada if moon_b else 1

    # 1. Ashta-Kuta
    ashta_evals, ashta_pariharas = AshtaKutaEngine.evaluate(r_a, n_a, p_a, r_b, n_b, p_b)
    ashta_pts = sum(k.obtained_points for k in ashta_evals)
    ashta_pct = (ashta_pts / 36.0) * 100.0

    ashta_res = AshtaKutaResponse(
        evaluations=[
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
            for k in ashta_evals
        ],
        total_guna_obtained=ashta_pts,
        max_guna_possible=36.0,
        guna_percentage=ashta_pct,
        dosha_pariharas=[
            DoshaPariharaItem(
                dosha_name=p.dosha_name,
                is_present=p.is_present,
                is_cancelled=p.is_cancelled,
                parihara_rule=p.parihara_rule,
                classical_reference=p.classical_reference,
                explanation=p.explanation,
            )
            for p in ashta_pariharas
        ],
        summary=f"Ashta-Kuta: {ashta_pts:.1f}/36.0 Gunas ({ashta_pct:.1f}%).",
    )

    # 2. Dasa Kuta
    dasa_raw = DasaKutaEngine.evaluate(r_a, n_a, r_b, n_b)
    dasa_res = DasaKutaResponse(
        items=[
            DasaKutaItemSchema(
                name=it.name,
                label=it.label,
                is_compatible=it.is_compatible,
                obtained_score=it.obtained_score,
                max_score=it.max_score,
                partner_a_value=it.partner_a_value,
                partner_b_value=it.partner_b_value,
                description=it.description,
                classical_source=it.classical_source,
            )
            for it in dasa_raw.items
        ],
        total_score=dasa_raw.total_score,
        max_total_score=dasa_raw.max_total_score,
        compatibility_percentage=dasa_raw.compatibility_percentage,
        is_rajju_compatible=dasa_raw.is_rajju_compatible,
        is_vedha_compatible=dasa_raw.is_vedha_compatible,
        is_mahendra_present=dasa_raw.is_mahendra_present,
        is_stree_deergha_present=dasa_raw.is_stree_deergha_present,
        verdict=dasa_raw.verdict,
        summary=dasa_raw.summary,
    )

    # 3. Kuja Dosha
    kuja_raw = KujaDoshaEngine.compare_charts(chart_a, chart_b, req.chart_a_birth.name, req.chart_b_birth.name)
    kuja_res = KujaDoshaComparisonSchema(
        partner_a=KujaDoshaProfileSchema(
            chart_name=kuja_raw.partner_a.chart_name,
            has_dosha=kuja_raw.partner_a.has_dosha,
            severity=kuja_raw.partner_a.severity,
            house_from_lagna=kuja_raw.partner_a.house_from_lagna,
            house_from_moon=kuja_raw.partner_a.house_from_moon,
            house_from_venus=kuja_raw.partner_a.house_from_venus,
            raw_dosha_points=kuja_raw.partner_a.raw_dosha_points,
            effective_dosha_score=kuja_raw.partner_a.effective_dosha_score,
            pariharas_applied=list(kuja_raw.partner_a.pariharas_applied),
            is_cancelled=kuja_raw.partner_a.is_cancelled,
            explanation=kuja_raw.partner_a.explanation,
        ),
        partner_b=KujaDoshaProfileSchema(
            chart_name=kuja_raw.partner_b.chart_name,
            has_dosha=kuja_raw.partner_b.has_dosha,
            severity=kuja_raw.partner_b.severity,
            house_from_lagna=kuja_raw.partner_b.house_from_lagna,
            house_from_moon=kuja_raw.partner_b.house_from_moon,
            house_from_venus=kuja_raw.partner_b.house_from_venus,
            raw_dosha_points=kuja_raw.partner_b.raw_dosha_points,
            effective_dosha_score=kuja_raw.partner_b.effective_dosha_score,
            pariharas_applied=list(kuja_raw.partner_b.pariharas_applied),
            is_cancelled=kuja_raw.partner_b.is_cancelled,
            explanation=kuja_raw.partner_b.explanation,
        ),
        is_balanced=kuja_raw.is_balanced,
        dosha_difference=kuja_raw.dosha_difference,
        compatibility_verdict=kuja_raw.compatibility_verdict,
        classical_mitigation_notes=kuja_raw.classical_mitigation_notes,
    )

    # 4. Upapada
    up_raw = JaiminiNavamshaSynastry.evaluate_upapada_compatibility(chart_a, chart_b)
    up_res = UpapadaCompatibilitySchema(
        ul_rashi_a=up_raw.ul_rashi_a,
        ul_rashi_b=up_raw.ul_rashi_b,
        lagna_rashi_a=up_raw.lagna_rashi_a,
        lagna_rashi_b=up_raw.lagna_rashi_b,
        moon_rashi_a=up_raw.moon_rashi_a,
        moon_rashi_b=up_raw.moon_rashi_b,
        alignment_type=up_raw.alignment_type,
        is_harmonious=up_raw.is_harmonious,
        second_from_ul_status_a=up_raw.second_from_ul_status_a,
        second_from_ul_status_b=up_raw.second_from_ul_status_b,
        jaimini_compatibility_score=up_raw.jaimini_compatibility_score,
        explanation=up_raw.explanation,
    )

    # 5. Navamsha
    nav_raw = JaiminiNavamshaSynastry.evaluate_navamsha_synastry(chart_a, chart_b)
    nav_res = NavamshaSynastrySchema(
        d9_lagna_a=nav_raw.d9_lagna_a,
        d9_lagna_b=nav_raw.d9_lagna_b,
        lagna_relationship=nav_raw.lagna_relationship,
        d9_moon_a=nav_raw.d9_moon_a,
        d9_moon_b=nav_raw.d9_moon_b,
        d9_venus_a=nav_raw.d9_venus_a,
        d9_venus_b=nav_raw.d9_venus_b,
        mutual_d9_trines=list(nav_raw.mutual_d9_trines),
        navamsha_harmony_score=nav_raw.navamsha_harmony_score,
        verdict=nav_raw.verdict,
        explanation=nav_raw.explanation,
    )

    # 6. Composite Chart
    comp_raw = CompositeChartEngine.calculate_composite_chart(chart_a, chart_b, req.chart_a_birth.name, req.chart_b_birth.name)
    comp_res = CompositeChartResponse(
        chart_a_name=comp_raw.chart_a_name,
        chart_b_name=comp_raw.chart_b_name,
        composite_ascendant=CompositePlanetSchema(
            planet=comp_raw.composite_ascendant.planet,
            sidereal_longitude=comp_raw.composite_ascendant.sidereal_longitude,
            rashi=comp_raw.composite_ascendant.rashi,
            rashi_degree=comp_raw.composite_ascendant.rashi_degree,
            house_number=comp_raw.composite_ascendant.house_number,
        ),
        composite_planets=[
            CompositePlanetSchema(
                planet=p.planet,
                sidereal_longitude=p.sidereal_longitude,
                rashi=p.rashi,
                rashi_degree=p.rashi_degree,
                house_number=p.house_number,
            )
            for p in comp_raw.composite_planets
        ],
        relationship_purpose_summary=comp_raw.relationship_purpose_summary,
    )

    # Overall Combined Compatibility Index (Weighted 0-100)
    # Ashta-Kuta 35%, Dasa-Kuta 25%, Upapada 15%, D9 Navamsha 15%, Kuja Dosha Balance 10%
    kuja_balance_score = 100.0 if kuja_raw.is_balanced else max(30.0, 100.0 - kuja_raw.dosha_difference)
    overall_index = round(
        (ashta_pct * 0.35)
        + (dasa_raw.compatibility_percentage * 0.25)
        + (up_raw.jaimini_compatibility_score * 0.15)
        + (nav_raw.navamsha_harmony_score * 0.15)
        + (kuja_balance_score * 0.10),
        1,
    )

    if overall_index >= 75.0:
        overall_verdict = "EXCELLENT ALL-ROUND COMPATIBILITY"
    elif overall_index >= 60.0:
        overall_verdict = "GOOD MARITAL & PARTNERSHIP ALIGNMENT"
    elif overall_index >= 45.0:
        overall_verdict = "AVERAGE / MIXED RESIDUAL ENERGIES"
    else:
        overall_verdict = "COMPLEX KARMIC DYNAMICS (Remedies Advised)"

    exec_summary = (
        f"Overall Compatibility Index: {overall_index:.1f}/100 ({overall_verdict}). "
        f"Ashta-Kuta: {ashta_pts:.1f}/36 ({ashta_pct:.1f}%), Dasa-Kuta: {dasa_raw.total_score:.1f}/{dasa_raw.max_total_score:.1f} ({dasa_raw.compatibility_percentage:.1f}%), "
        f"Kuja Dosha: {'Balanced' if kuja_raw.is_balanced else 'Unbalanced'}, Jaimini Upapada: {up_raw.alignment_type}, "
        f"D9 Navamsha: {nav_raw.lagna_relationship}."
    )

    return FullCompatibilityResponse(
        chart_a_name=req.chart_a_birth.name,
        chart_b_name=req.chart_b_birth.name,
        ashta_kuta=ashta_res,
        dasa_kuta=dasa_res,
        kuja_dosha=kuja_res,
        upapada_compatibility=up_res,
        navamsha_synastry=nav_res,
        composite_chart=comp_res,
        overall_compatibility_index=overall_index,
        overall_verdict=overall_verdict,
        executive_summary=exec_summary,
    )

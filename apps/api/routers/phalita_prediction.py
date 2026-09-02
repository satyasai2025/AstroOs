"""
AstroOS — Phalita Prediction & Complete Shastric Consultation Router
====================================================================

Exposes REST endpoints for:
1. Deterministic 128-D TPhalitCore feature extraction
2. Prospective Future Window Scanning (1 to 5 years ahead)
3. 4-Tier Supervisory Adaptive Decision Consultation (Life Timeline)
4. Bhrigu Bindu (Destiny Trigger) & Sarvato-Bhadra Chakra (SBC) Vedhas
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.bhrigu_bindu_engine import BhriguBinduEngine, BhriguBinduReport
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.decision_engine import (
    PhalitaConsultationTimeline,
    PhalitaDecisionEngine,
)
from apps.api.services.phalita_core.forward_scanner_engine import (
    PhalitaForwardScanner,
    ProspectivePredictionWindow,
)
from apps.api.services.phalita_core.tphalit_core import TPhalitCore
from apps.api.services.phalita_core.varga_fusion_engine import (
    VargaFusionEngine,
    VargaFusionReport,
)
from apps.api.services.sapta_nadi_chakra_engine import (
    SaptaNadiChakraEngine,
    SaptaNadiReport,
)
from dataclasses import asdict

from apps.api.services.sarvato_bhadra_engine import SarvatoBhadraEngine, SarvatoBhadraReport
from apps.api.services.sudarshana_chakra_engine import (
    SudarshanaChakraEngine,
    SudarshanaChakraReport,
)
from apps.api.services.triple_dasha_confluence_engine import (
    TripleDashaConfluenceEngine,
    TripleDashaWindowConfluence,
)
from apps.api.services.shastric_story_synthesizer import ShastricStorySynthesizer
from apps.api.services.empirical_pattern_matcher import EmpiricalPatternMatcher
from apps.api.services.live_sky_transit_engine import LiveSkyTransitEngine
from apps.api.services.professional_archetype_engine import ProfessionalArchetypeEngine
from apps.api.services.shastric_qa_oracle import ShastricQAOracle

router = APIRouter(prefix="/api/v1/phalita", tags=["Phalita Prediction"])


class FeatureExtractionRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude (-180 to +180)")
    target_date_iso: Optional[str] = Field(None, description="Target evaluation date (YYYY-MM-DD)")


class ProspectiveScanRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude (-180 to +180)")
    scan_start_date_iso: Optional[str] = Field(None, description="Scan start date (YYYY-MM-DD), defaults to today")
    horizon_years: int = Field(3, ge=1, le=10, description="Number of years to scan ahead (1 to 10)")
    domain: str = Field("career", description="Target domain: career, marriage, finance, health")
    min_probability_threshold: float = Field(0.08, ge=0.0, le=1.0, description="Minimum calibrated probability threshold")


class ConsultationRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude (-180 to +180)")
    native_name: str = Field("Native", description="Name of the person / entity")
    scan_start_year: int = Field(2020, ge=1800, le=2200, description="Start year of life scan (1800 to 2200)")
    scan_end_year: int = Field(2035, ge=1800, le=2200, description="End year of life scan (1800 to 2200)")
    domain: str = Field("career", description="Target domain: career, marriage, finance, health")
    evaluation_target_date_iso: Optional[str] = Field(None, description="Specific target date for SBC and Bhrigu Bindu")


@router.post("/extract-vector")
def extract_feature_vector(req: FeatureExtractionRequest) -> Dict[str, Any]:
    """Generate 128-dimensional deterministic TPhalitCore feature vector."""
    try:
        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
        horoscope = HoroscopeEngine(wrapper)
        dasha_engine = DashaEngine(wrapper)
        core = TPhalitCore()

        chart = horoscope.generate_d1(birth_dt, req.latitude, req.longitude)
        tree = dasha_engine.compute_vimshottari(birth_dt, req.latitude, req.longitude)

        target_dt = date.fromisoformat(req.target_date_iso) if req.target_date_iso else date.today()
        vec = core.extract_full_vector(chart=chart, dasha_tree=tree, target_date=target_dt)

        return {
            "status": "SUCCESS",
            "domain_scores": vec.domain_scores,
            "active_yogas": [y.yoga_name for y in vec.yogas],
            "dasha": {
                "md": vec.dasha.mahadasha_lord if vec.dasha else "",
                "ad": vec.dasha.antardasha_lord if vec.dasha else "",
                "sadharmi_score": vec.dasha.sadharmi_relation if vec.dasha else 0.0,
            },
            "vector_dimension": len(vec.raw_vector),
            "feature_vector": vec.raw_vector,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/predict-future")
def predict_prospective_windows(req: ProspectiveScanRequest) -> Dict[str, Any]:
    """Scan prospective future event windows using calibrated PhalitaMoE."""
    try:
        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        start_d = date.fromisoformat(req.scan_start_date_iso) if req.scan_start_date_iso else date.today()

        scanner = PhalitaForwardScanner()
        windows: List[ProspectivePredictionWindow] = scanner.scan_prospective_windows(
            birth_dt=birth_dt,
            latitude=req.latitude,
            longitude=req.longitude,
            scan_start_date=start_d,
            scan_horizon_years=req.horizon_years,
            domain=req.domain,
            min_probability_threshold=req.min_probability_threshold,
        )

        return {
            "status": "SUCCESS",
            "domain": req.domain,
            "scan_window_start": start_d.isoformat(),
            "scan_horizon_years": req.horizon_years,
            "total_windows_detected": len(windows),
            "predicted_windows": [
                {
                    "window_start": w.window_start.isoformat(),
                    "window_end": w.window_end.isoformat(),
                    "peak_date": w.peak_date.isoformat(),
                    "calibrated_probability": w.calibrated_probability,
                    "confidence_tier": w.confidence_tier,
                    "mahadasha": w.active_mahadasha,
                    "antardasha": w.active_antardasha,
                    "classical_yogas": w.classical_yogas,
                    "router_attention": w.router_attention,
                    "rationale": w.astrological_rationale,
                }
                for w in windows
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/consultation")
def full_supervisory_consultation(req: ConsultationRequest) -> Dict[str, Any]:
    """
    Generate comprehensive Scholar-Grade Consultation Report:
    - 4-Tier Supervisory Adaptive Decision Timeline (Life Scan)
    - Bhrigu Bindu (Destiny Trigger) Calculation & Gochara Activation
    - Sarvato-Bhadra Chakra (28-Nakshatra SBC) Nadi Vedha Assessment
    """
    try:
        if req.scan_end_year < req.scan_start_year:
            raise HTTPException(
                status_code=422,
                detail="scan_end_year must be greater than or equal to scan_start_year",
            )
        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
        horoscope = HoroscopeEngine(wrapper)
        chart = horoscope.generate_d1(birth_dt, req.latitude, req.longitude)

        # 1. Timeline Scan
        decision_engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")
        timeline: PhalitaConsultationTimeline = decision_engine.scan_life_timeline(
            birth_datetime=birth_dt,
            latitude=req.latitude,
            longitude=req.longitude,
            native_name=req.native_name,
            scan_start_year=req.scan_start_year,
            scan_end_year=req.scan_end_year,
            domain=req.domain,
        )

        # 2. Bhrigu Bindu & SBC on Target Date
        target_d = date.fromisoformat(req.evaluation_target_date_iso) if req.evaluation_target_date_iso else date.today()
        bb_engine = BhriguBinduEngine(ephemeris_path="data/ephemeris")
        bb_rep: BhriguBinduReport = bb_engine.evaluate_transit(chart, target_date=target_d)

        sbc_engine = SarvatoBhadraEngine(ephemeris_path="data/ephemeris")
        sbc_rep: SarvatoBhadraReport = sbc_engine.evaluate_sbc(chart, target_date=target_d)

        arudha_engine = ArudhaEngine()
        arudha_res = arudha_engine.compute(chart)

        sc_engine = SudarshanaChakraEngine()
        sc_rep: SudarshanaChakraReport = sc_engine.evaluate_chart(
            chart=chart,
            birth_datetime=birth_dt,
            target_datetime=datetime.combine(target_d, datetime.min.time(), tzinfo=timezone.utc),
        )

        # 3. Varga Fusion & Sapta-Nadi Chakra
        varga_engine = VargaFusionEngine()
        varga_rep: VargaFusionReport = varga_engine.evaluate_vargas(chart)

        snc_engine = SaptaNadiChakraEngine()
        snc_rep: SaptaNadiReport = snc_engine.evaluate_chart(chart)

        # 4. Triple Dasha Confluence (Vimshottari + Sudarshana SCD + Jaimini Chara Dasha)
        confluence_engine = TripleDashaConfluenceEngine()
        target_conf: TripleDashaWindowConfluence = confluence_engine.evaluate_window_confluence(
            chart=chart,
            target_date=target_d,
            birth_dt=birth_dt,
            mahadasha_lord=timeline.windows[0].mahadasha_lord if timeline.windows else "sun",
            antardasha_lord=timeline.windows[0].antardasha_lord if timeline.windows else "jupiter",
            domain=req.domain,
        )

        # Map timeline windows with Confluence & Empirical Proofs
        moon_planet = next((p for p in chart.planets if p.planet.lower() == "moon"), None)
        moon_rashi_name = moon_planet.rashi if moon_planet else None
        lagna_rashi_name = chart.ascendant.rashi if chart.ascendant else None

        mapped_timeline_windows = []
        for w in timeline.windows:
            conf_win = confluence_engine.evaluate_window_confluence(
                chart=chart,
                target_date=w.window_start,
                birth_dt=birth_dt,
                mahadasha_lord=w.mahadasha_lord,
                antardasha_lord=w.antardasha_lord,
                domain=req.domain,
            )
            emp_match = EmpiricalPatternMatcher.match_window(
                event_domain=req.domain,
                mahadasha_lord=w.mahadasha_lord,
                lagna_rashi=lagna_rashi_name,
                moon_rashi=moon_rashi_name,
            )
            mapped_timeline_windows.append({
                "window_start": w.window_start.isoformat(),
                "window_end": w.window_end.isoformat(),
                "mahadasha": w.mahadasha_lord,
                "antardasha": w.antardasha_lord,
                "probability": w.raw_probability,
                "decision_tier": w.decision_tier,
                "confidence_level": w.confidence_level,
                "verdict": w.actionable_verdict,
                "polarity": w.polarity,
                "polarity_logic": w.polarity_logic,
                "varga_fusion_score": w.varga_fusion_score,
                "is_bhavottama_active": w.is_bhavottama_active,
                "scd_annual_house": w.scd_annual_house,
                "scd_composite_score": w.scd_composite_score,
                "sav_10th_bindus": w.sav_10th_bindus,
                "double_transit": w.double_transit,
                "amatyakaraka": w.amatyakaraka,
                "confluence_level": conf_win.confluence_level,
                "chara_dasha_rashi": conf_win.chara_dasha_rashi,
                "confluence_synthesis_hi": conf_win.actionable_synthesis_hi,
                "confluence_synthesis_en": conf_win.actionable_synthesis_en,
                "empirical_match": {
                    "is_matched": emp_match.is_matched,
                    "evidence_badge": emp_match.evidence_badge,
                    "sample_size": emp_match.sample_size,
                    "lift_ratio": emp_match.lift_ratio,
                    "confidence_percentage": emp_match.confidence_percentage,
                    "pattern_description": emp_match.pattern_description,
                } if emp_match else None,
            })

        # Synthesize zero-hallucination executive life story
        story = ShastricStorySynthesizer.synthesize_story(
            native_name=req.native_name,
            domain=req.domain,
            timeline_windows=mapped_timeline_windows,
            lagna_rashi=lagna_rashi_name,
            moon_rashi=moon_rashi_name,
        )

        # 5. Professional Archetypes & Wealth/Authority Discovery
        arch_eval = ProfessionalArchetypeEngine.evaluate_chart(
            chart=chart,
            amatyakaraka=timeline.windows[0].amatyakaraka if timeline.windows else None,
        )

        return {
            "status": "SUCCESS",
            "native_name": req.native_name,
            "domain": req.domain,
            "scan_horizon": f"{req.scan_start_year} to {req.scan_end_year}",
            "executive_story": asdict(story),
            "professional_archetypes": {
                "dominant_archetype_key": arch_eval.dominant_archetype_key,
                "dominant_title": arch_eval.dominant_title,
                "dominant_score": arch_eval.dominant_score,
                "dominant_badge": arch_eval.dominant_badge,
                "dominant_guidance": arch_eval.dominant_guidance,
                "total_yogas_verified": arch_eval.total_yogas_verified,
                "rajya_yogas_count": arch_eval.rajya_yogas_count,
                "dhana_yogas_count": arch_eval.dhana_yogas_count,
                "archetype_affinities": [
                    {
                        "archetype_key": a.archetype_key,
                        "title": a.title,
                        "domain": a.domain,
                        "affinity_score": a.affinity_score,
                        "empirical_lift": a.empirical_lift,
                        "confidence_score": a.confidence_score,
                        "p_value_text": a.p_value_text,
                        "evidence_badge": a.evidence_badge,
                        "matched_signatures": a.matched_signatures,
                        "key_planetary_drivers": a.key_planetary_drivers,
                        "rajya_dhana_yogas_active": a.rajya_dhana_yogas_active,
                        "strategic_career_guidance": a.strategic_career_guidance,
                    }
                    for a in arch_eval.archetype_affinities
                ],
            },
            "timeline_summary": {
                "total_windows_scanned": timeline.total_windows_scanned,
                "pratyaksha_events_count": timeline.pratyaksha_events_count,
                "latent_potential_count": timeline.latent_potential_count,
                "transient_triggers_count": timeline.transient_triggers_count,
            },
            "triple_dasha_confluence": {
                "confluence_level": target_conf.confluence_level,
                "confluence_score": target_conf.confluence_score,
                "is_infallible_landmark": target_conf.is_infallible_landmark,
                "vimshottari_md": target_conf.vimshottari_md,
                "vimshottari_ad": target_conf.vimshottari_ad,
                "scd_active_house": target_conf.scd_active_house,
                "chara_dasha_rashi": target_conf.chara_dasha_rashi,
                "synthesis_hi": target_conf.actionable_synthesis_hi,
                "synthesis_en": target_conf.actionable_synthesis_en,
            },
            "varga_fusion": {
                "overall_varga_harmony": varga_rep.overall_varga_harmony,
                "fused_domain_scores": varga_rep.fused_domain_scores,
                "bhavottama_planets": varga_rep.bhavottama_planets,
                "vargottama_planets": varga_rep.vargottama_planets,
            },
            "sapta_nadi_chakra": {
                "dominant_nadi": snc_rep.dominant_nadi,
                "cyclone_risk_score": snc_rep.cyclone_risk_score,
                "flood_risk_score": snc_rep.flood_risk_score,
                "weather_summary": snc_rep.weather_summary,
            },
            "bhrigu_bindu": {
                "degree_absolute": bb_rep.bb_degree_absolute,
                "rashi": bb_rep.bb_rashi,
                "rashi_degree": bb_rep.bb_rashi_degree,
                "nakshatra": bb_rep.bb_nakshatra,
                "pada": bb_rep.bb_nakshatra_pada,
                "house_from_lagna": bb_rep.bb_house_from_lagna,
                "transit_date": target_d.isoformat(),
                "activation_status": bb_rep.activation_status,
                "destiny_impact_score": bb_rep.destiny_impact_score,
                "planets_conjunct": bb_rep.transiting_planets_conjunct,
                "planets_aspecting": bb_rep.transiting_planets_aspecting,
            },
            "sarvato_bhadra_chakra": {
                "janma_nakshatra": sbc_rep.janma_nakshatra_28,
                "overall_transit_shield": sbc_rep.overall_transit_shield,
                "sbc_composite_score": sbc_rep.sbc_composite_score,
                "total_benefic_vedhas_count": sbc_rep.total_benefic_vedhas_count,
                "total_malefic_vedhas_count": sbc_rep.total_malefic_vedhas_count,
                "nadi_afflictions": {
                    k: {
                        "nakshatra": v.nakshatra_name,
                        "status": v.vedha_status,
                        "benefics": v.benefic_vedhas,
                        "malefics": v.malefic_vedhas,
                    }
                    for k, v in sbc_rep.nadi_nakshatras.items()
                },
            },
            "arudha_padas": {
                "AL": {"house": arudha_res.arudha_lagna.house_number, "rashi": arudha_res.arudha_lagna.rashi, "name": "Arudha Lagna (Means of Self-Manifestation)"},
                "UL": {"house": arudha_res.upapada_lagna.house_number, "rashi": arudha_res.upapada_lagna.rashi, "name": "Upapada Lagna (Marriage & Partner Sustenance)"},
                "A10": {"house": arudha_res.by_house(10).house_number, "rashi": arudha_res.by_house(10).rashi, "name": "Rajya Pada (Public Status & Career Authority)"},
                "all_padas": {
                    p.pada_name: {"house": p.house_number, "rashi": p.rashi} for p in arudha_res.padas
                },
            },
            "sudarshana_chakra": {
                "lagna_rashi": sc_rep.lagna_rashi,
                "moon_rashi": sc_rep.moon_rashi,
                "sun_rashi": sc_rep.sun_rashi,
                "tri_fold_harmony_score": sc_rep.tri_fold_harmony_score,
                "current_scd": {
                    "age_years": getattr(sc_rep.current_scd, "age_years", None) if sc_rep.current_scd else None,
                    "active_house": getattr(sc_rep.current_scd, "active_house_from_lagna", None) if sc_rep.current_scd else None,
                    "primary_theme": getattr(sc_rep.current_scd, "primary_theme", "") if sc_rep.current_scd else "",
                    "significations": getattr(sc_rep.current_scd, "house_significations", []) if sc_rep.current_scd else [],
                } if sc_rep.current_scd else None,

                "graha_alignments": [
                    {
                        "point_name": g.point_name,
                        "rashi": g.rashi,
                        "house_from_lagna": g.house_from_lagna,
                        "house_from_moon": g.house_from_moon,
                        "house_from_sun": g.house_from_sun,
                        "tri_fold_auspiciousness": g.tri_fold_auspiciousness,
                        "supporting_lagnas_count": g.supporting_lagnas_count,
                    }
                    for g in sc_rep.graha_alignments
                ],
            },
            "decision_timeline": mapped_timeline_windows,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/live-sky")
def get_live_sky_transits() -> dict[str, Any]:
    """
    Returns real-time celestial planetary positions and aspect alerts.
    """
    try:
        report = LiveSkyTransitEngine.compute_current_sky()
        return asdict(report)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class OracleQARequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Natural language question from user")
    birth_date_iso: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    native_name: Optional[str] = "Native"
    timeline_windows: Optional[List[Dict[str, Any]]] = None
    sudarshana_data: Optional[Dict[str, Any]] = None
    varga_data: Optional[Dict[str, Any]] = None
    arudha_padas: Optional[Dict[str, Any]] = None
    lang: Optional[str] = "en"


@router.post("/ask-oracle")
def ask_shastric_oracle(req: OracleQARequest) -> Dict[str, Any]:
    """
    Answers natural language user questions about life events strictly grounded
    in calculated chart metrics and dasha cycles without AI hallucination.
    """
    try:
        windows = req.timeline_windows or []
        
        # If birth details provided and no windows passed, compute timeline on the fly
        if not windows and req.birth_date_iso and req.latitude is not None and req.longitude is not None:
            birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
            domain = ShastricQAOracle.detect_domain(req.question)
            decision_engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")
            timeline = decision_engine.scan_life_timeline(
                birth_datetime=birth_dt,
                latitude=req.latitude,
                longitude=req.longitude,
                native_name=req.native_name or "Native",
                scan_start_year=max(1900, birth_dt.year + 10),
                scan_end_year=min(2100, birth_dt.year + 50),
                domain=domain if domain in ["career", "marriage", "finance", "health"] else "career",
            )
            windows = [
                {
                    "window_start": w.window_start.isoformat(),
                    "window_end": w.window_end.isoformat(),
                    "mahadasha": w.mahadasha_lord,
                    "antardasha": w.antardasha_lord,
                    "probability": w.raw_probability,
                    "decision_tier": w.decision_tier,
                }
                for w in timeline.windows
            ]

        resp = ShastricQAOracle.answer_question(
            question=req.question,
            timeline_windows=windows,
            sudarshana_data=req.sudarshana_data,
            varga_data=req.varga_data,
            arudha_padas=req.arudha_padas,
            native_name=req.native_name or "Native",
            lang=req.lang or "en"
        )
        return asdict(resp)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ── Production Endpoints for Canonical 9-Phase Architecture ─────────────────

class CanonicalSynthesisRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude (-180 to +180)")
    target_year: Optional[int] = Field(None, description="Target year for VPC Solar Return calculation")


class VPCTimelineRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude (-180 to +180)")
    start_year: int = Field(..., description="Start year for solar return calculation")
    end_year: int = Field(..., description="End year for solar return calculation")


class NoiseDiagnosticsRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    deterministic_score: float = Field(...)
    planet_block_total: float = Field(...)
    residual_error: float = Field(...)
    varga_opposition_index: Optional[float] = Field(0.0)


@router.post("/canonical-synthesis")
def get_canonical_synthesis(req: CanonicalSynthesisRequest) -> Dict[str, Any]:
    """
    Complete 3-Chart Synthesis (D1 Vishamabhava Bhaavachalita + Tri-Lagna Sudarshana
    Chakra + D10/D24 Vimshopaka + VPC Solar Returns + TPhalitCore Signed State).
    """
    try:
        from apps.api.services.bhavachalita_engine import VishamabhavaEngine
        from apps.api.services.divisional_synthesis_engine import DivisionalSynthesisEngine, VimshopakaScheme
        from apps.api.services.tphalit_core_engine import TPhalitCoreEngine
        from apps.api.services.vpc_engine import VPCEngine

        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")

        # 1. D1 Vishamabhava Bhaavachalita
        bhava_engine = VishamabhavaEngine(ephemeris_wrapper=wrapper)
        chart = bhava_engine.compute_bhavachalita(birth_datetime=birth_dt, latitude=req.latitude, longitude=req.longitude)

        # 2. Tri-Lagna Sudarshana Chakra
        b_ephem = wrapper.calculate(dt=birth_dt, latitude=req.latitude, longitude=req.longitude)
        sun_p = next(p for p in b_ephem.planet_positions if p.planet.lower() == "sun")
        moon_p = next(p for p in b_ephem.planet_positions if p.planet.lower() == "moon")
        sc_engine = SudarshanaChakraEngine(ephemeris_wrapper=wrapper)
        sc_rep = sc_engine.analyze(
            lagna_deg=chart.lagna_madhya,
            sun_deg=sun_p.sidereal_longitude,
            moon_deg=moon_p.sidereal_longitude,
        )

        # 3. D10 / D24 Vimshopaka Synthesis
        div_engine = DivisionalSynthesisEngine(ephemeris_wrapper=wrapper)
        d10_reports = {}
        for p in b_ephem.planet_positions:
            if p.planet.lower() in ["rahu", "ketu"]:
                continue
            rep = div_engine.synthesize_d1_vs_divisional(
                planet=p.planet,
                sidereal_lon=p.sidereal_longitude,
                target_varga=10,
                scheme=VimshopakaScheme.DASHAVARGA,
            )
            d10_reports[p.planet.capitalize()] = {
                "d1_dignity": rep.d1_strength.dignity_label,
                "d1_s_eff": rep.d1_strength.effective_strength,
                "d10_dignity": rep.divisional_strength.dignity_label,
                "d10_s_eff": rep.divisional_strength.effective_strength,
                "verdict": rep.verdict.value,
            }

        # 4. VPC Solar Return & SCD Progressed House + Varshaphal Tajika Engine
        vpc_engine = VPCEngine(ephemeris_wrapper=wrapper)
        target_yr = req.target_year or datetime.now(timezone.utc).year
        vpc_report = vpc_engine.compute_vpc(
            birth_datetime_utc=birth_dt,
            target_year=target_yr,
            latitude=req.latitude,
            longitude=req.longitude,
        )

        from apps.api.services.varshaphal_engine import VarshaphalEngine
        from apps.api.services.ephemeris_wrapper import jd_to_datetime
        from packages.shared.constants import SIGN_LORDS

        varsha_engine = VarshaphalEngine(wrapper=wrapper)
        varsha_year = max(1, target_yr - birth_dt.year)
        varsha_result = varsha_engine.calculate(
            birth_dt=birth_dt,
            latitude=req.latitude,
            longitude=req.longitude,
            varsha_year=varsha_year,
        )

        muntha_rashi = varsha_result.muntha.rashi.capitalize() if isinstance(varsha_result.muntha.rashi, str) else varsha_result.muntha.rashi
        muntha_lord = SIGN_LORDS.get(varsha_result.muntha.rashi.lower(), "Saturn").capitalize()

        varsha_chart = varsha_result.varsha_chart
        varsha_ascendant = {
            "rashi": varsha_chart.ascendant.rashi.capitalize() if isinstance(varsha_chart.ascendant.rashi, str) else varsha_chart.ascendant.rashi,
            "rashi_degree": varsha_chart.ascendant.rashi_degree,
            "longitude": varsha_chart.ascendant.longitude,
            "sidereal_longitude": varsha_chart.ascendant.sidereal_longitude,
            "nakshatra": varsha_chart.ascendant.nakshatra.replace("_", " ").title() if isinstance(varsha_chart.ascendant.nakshatra, str) else varsha_chart.ascendant.nakshatra,
            "pada": varsha_chart.ascendant.pada,
        }

        varsha_planets = [
            {
                "planet": p.planet.capitalize(),
                "rashi": p.rashi.capitalize() if isinstance(p.rashi, str) else p.rashi,
                "rashi_degree": p.rashi_degree,
                "house_number": p.house_number,
                "sidereal_longitude": p.sidereal_longitude,
                "is_retrograde": p.is_retrograde,
                "dignity": p.dignity.value if p.dignity else "sama",
            }
            for p in varsha_chart.planet_positions
        ]

        natal_planets = [
            {
                "planet": p.planet.capitalize(),
                "rashi": p.rashi.capitalize() if isinstance(p.rashi, str) else p.rashi,
                "rashi_degree": p.rashi_degree,
                "house_number": p.house_number,
                "sidereal_longitude": p.sidereal_longitude,
                "is_retrograde": p.is_retrograde,
                "dignity": p.dignity.value if p.dignity else "sama",
            }
            for p in b_ephem.planet_positions
        ]

        year_lord_data = {
            "selected": varsha_result.year_lord.selected.capitalize(),
            "selection_method": varsha_result.year_lord.selection_method,
            "candidates": [c.capitalize() for c in varsha_result.year_lord.candidates],
        }

        panchavargiya_bala = [
            {
                "planet": b.planet.capitalize(),
                "total_score": b.total_score,
                "visheshika_bala": b.visheshika_bala,
                "strength_category": b.strength_category,
            }
            for b in varsha_result.panchavargiya_bala
        ]

        sahams = [
            {
                "name": s.name,
                "rashi": s.rashi,
                "sidereal_longitude": s.sidereal_longitude,
            }
            for s in varsha_result.sahams
        ]

        solar_return_utc = jd_to_datetime(varsha_result.solar_return_jd).isoformat()

        # 5. TPhalitCore Signed State
        tphalit_engine = TPhalitCoreEngine(ephemeris_wrapper=wrapper)
        fv = tphalit_engine.extract_features(
            birth_datetime_utc=birth_dt,
            latitude=req.latitude,
            longitude=req.longitude,
        )

        return {
            "birth_datetime_utc": birth_dt.isoformat(),
            "lagna_madhya_deg": chart.lagna_madhya,
            "madhya_lagna_deg": chart.madhya_lagna,
            "natal_ascendant": {
                "rashi": b_ephem.ascendant.rashi.capitalize() if isinstance(b_ephem.ascendant.rashi, str) else b_ephem.ascendant.rashi,
                "rashi_degree": b_ephem.ascendant.rashi_degree,
                "sidereal_longitude": b_ephem.ascendant.sidereal_longitude,
                "nakshatra": b_ephem.ascendant.nakshatra.replace("_", " ").title() if isinstance(b_ephem.ascendant.nakshatra, str) else b_ephem.ascendant.nakshatra,
                "pada": b_ephem.ascendant.pada,
            },
            "natal_planets": natal_planets,
            "houses": [
                {
                    "house_number": h.house_number,
                    "start_sandhi": h.start_sandhi,
                    "madhya": h.madhya,
                    "end_sandhi": h.end_sandhi,
                    "primary_lord": h.primary_lord,
                    "primary_rashi": h.primary_rashi,
                    "secondary_lord": h.secondary_lord,
                    "secondary_rashi": h.secondary_rashi,
                    "total_span_deg": h.total_span_deg,
                }
                for h in chart.houses
            ],
            "sudarshana_chakra": {
                "lagna_rashi": sc_rep.lagna_rashi,
                "sun_rashi": sc_rep.sun_rashi,
                "moon_rashi": sc_rep.moon_rashi,
                "is_tri_lagna_active": sc_rep.is_tri_lagna_active,
                "sun_in_lagna": sc_rep.sun_in_lagna,
                "moon_in_lagna": sc_rep.moon_in_lagna,
                "profiles": {
                    k: {
                        "net_functional_score": v.net_functional_score,
                        "is_functional_benefic": v.is_functional_benefic,
                        "is_functional_malefic": v.is_functional_malefic,
                    }
                    for k, v in sc_rep.profiles.items()
                },
            },
            "divisional_synthesis_d10": d10_reports,
            "vpc_solar_return": {
                "target_year": vpc_report.target_year,
                "completed_years": varsha_year,
                "vpc_datetime_utc": solar_return_utc,
                "scd_annual_house": vpc_report.scd_annual_house,
                "sun_longitude_deg": sun_p.sidereal_longitude,
                "muntha": {
                    "rashi": muntha_rashi,
                    "rashi_index": varsha_result.muntha.rashi_index,
                    "house_number": varsha_result.muntha.house_number,
                    "lord": muntha_lord,
                },
                "year_lord": year_lord_data,
                "varsha_ascendant": varsha_ascendant,
                "varsha_planets": varsha_planets,
                "panchavargiya_bala": panchavargiya_bala,
                "sahams": sahams,
                "monthly_entries": [
                    {
                        "scd_house": m.scd_house,
                        "entry_datetime_utc": m.entry_datetime_utc.isoformat(),
                    }
                    for m in vpc_report.monthly_scd_entries
                ],
            },
            "tphalit_signed_state": {
                "deterministic_score": fv.DeterministicScore,
                "block_totals": fv.BlockTotals,
                "atomic_features": fv.AtomicFeatures,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/vpc-timeline")
def get_vpc_timeline(req: VPCTimelineRequest) -> Dict[str, Any]:
    """Generates multi-year Solar Return milestones and SCD Progressed Houses."""
    try:
        from apps.api.services.vpc_engine import VPCEngine
        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
        vpc_engine = VPCEngine(ephemeris_wrapper=wrapper)

        years_data = []
        for yr in range(req.start_year, req.end_year + 1):
            rep = vpc_engine.compute_vpc(
                birth_datetime_utc=birth_dt,
                target_year=yr,
                latitude=req.latitude,
                longitude=req.longitude,
            )
            years_data.append({
                "year": yr,
                "completed_age": rep.completed_years,
                "vpc_datetime_utc": rep.vpc_datetime_utc.isoformat(),
                "scd_annual_house": rep.scd_annual_house,
                "monthly_entries_count": len(rep.monthly_scd_entries),
            })

        return {
            "birth_datetime_utc": birth_dt.isoformat(),
            "solar_returns": years_data,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/noise-diagnostics")
def get_noise_diagnostics(req: NoiseDiagnosticsRequest) -> Dict[str, Any]:
    """Classifies dataset/inference point into the 4 Section 18 Noise categories."""
    try:
        from apps.api.services.ml.noise_diagnostic_engine import NoiseDiagnosticEngine
        rep = NoiseDiagnosticEngine.diagnose(
            latitude=req.latitude,
            longitude=req.longitude,
            deterministic_score=req.deterministic_score,
            planet_block_total=req.planet_block_total,
            residual_error=req.residual_error,
            varga_opposition_index=req.varga_opposition_index or 0.0,
        )
        return {
            "data_noise_score": rep.data_noise_score,
            "rules_noise_score": rep.rules_noise_score,
            "model_noise_score": rep.model_noise_score,
            "useful_noise_bandwidth": rep.useful_noise_bandwidth,
            "dominant_noise_category": rep.dominant_noise_category,
            "is_prediction_trustworthy": rep.is_prediction_trustworthy,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ─── Cognitive MoE & Shastric Event Prediction Endpoints (Phase 3) ────────────

class CognitiveEventPredictionRequest(BaseModel):
    birth_datetime: datetime = Field(..., description="Birth moment in ISO-8601 format (UTC recommended)")
    latitude: float = Field(..., description="Geographic latitude (-90 to +90)")
    longitude: float = Field(..., description="Geographic longitude (-180 to +180)")
    ayanamsa: str = Field("lahiri", description="Ayanamsa system (default: lahiri)")
    target_dasha: Optional[Dict[str, str]] = Field(
        None,
        description="Optional 5-level Dasha lords: {'md': '...', 'ad': '...', 'pd': '...', 'sk': '...', 'pr': '...'}"
    )


def _build_cognitive_context(
    req: CognitiveEventPredictionRequest,
) -> tuple[Any, Any]:
    from apps.api.services.upagraha_engine import UpagrahaEngine
    from apps.api.services.intelligence import (
        LinkedSystemBuilder,
        DashaPeriod5Level,
        extract_5level_periods_from_dasha_tree,
    )

    ephem = EphemerisWrapper(ephemeris_path="data/ephemeris")
    calc_res = ephem.calculate(
        dt=req.birth_datetime,
        latitude=req.latitude,
        longitude=req.longitude,
        ayanamsa=req.ayanamsa,
    )

    asc_lon = getattr(calc_res.ascendant, "sidereal_longitude", getattr(calc_res.ascendant, "longitude", 0.0))
    lagna_rashi_idx = int(asc_lon / 30.0) % 12
    graha_positions: Dict[str, int] = {}
    for pos_obj in calc_res.planet_positions:
        g_cap = pos_obj.planet.capitalize()
        g_lon = getattr(pos_obj, "sidereal_longitude", getattr(pos_obj, "longitude", 0.0))
        graha_positions[g_cap] = int(g_lon / 30.0) % 12



    # Canonical Upagrahas
    upagraha_engine = UpagrahaEngine(ephemeris_wrapper=ephem)
    upagraha_rep = upagraha_engine.compute_upagrahas(
        birth_datetime=req.birth_datetime,
        latitude=req.latitude,
        longitude=req.longitude,
        ayanamsa=req.ayanamsa,
    )

    # Linked Chart Graph
    graph = LinkedSystemBuilder.from_canonical_report(
        lagna_rashi_idx=lagna_rashi_idx,
        graha_positions=graha_positions,
        upagraha_report=upagraha_rep,
    )

    # 5-Level Dasha
    if req.target_dasha:
        dasha = DashaPeriod5Level.from_canonical_path(
            md_lord=req.target_dasha.get("md", "Sun"),
            ad_lord=req.target_dasha.get("ad", "Moon"),
            pd_lord=req.target_dasha.get("pd", "Mars"),
            sookshma_lord=req.target_dasha.get("sk", "Mercury"),
            praana_lord=req.target_dasha.get("pr", "Jupiter"),
        )
    else:
        dasha_engine = DashaEngine(ephemeris_wrapper=ephem)
        dasha_tree = dasha_engine.compute_vimshottari(
            birth_datetime_utc=req.birth_datetime,
            latitude=req.latitude,
            longitude=req.longitude,
            ayanamsa=req.ayanamsa,
            max_depth=5,
        )
        extracted = extract_5level_periods_from_dasha_tree(dasha_tree)
        dasha = extracted[0] if extracted else DashaPeriod5Level("Sun", "Sun", "Sun", "Sun", "Sun")

    return graph, dasha


@router.post("/moe/synthesize")
def synthesize_phalita_moe(
    req: CognitiveEventPredictionRequest,
    domain: str = "general",
) -> Dict[str, Any]:
    """
    Executes full Phalita Mixture of Experts (MoE) multi-expert consultation synthesis:
    1. Evaluates all 4 specialized Shastric experts (Structural, Divisional, Temporal, Upagraha)
    2. Computes Softmax Gating Attention weights
    3. Executes Evidence Fusion Matrix
    4. Arbitrates via Conflict Resolution Engine
    5. Returns 0 to 9 Cognitive Score with explainability
    """
    try:
        from apps.api.services.phalita_core import PhalitaMoEOrchestrator

        graph, dasha = _build_cognitive_context(req)
        verdict = PhalitaMoEOrchestrator.synthesize(graph, dasha, domain=domain)

        return {
            "domain": verdict.domain,
            "final_cognitive_score": verdict.final_cognitive_score,
            "is_probable": verdict.is_probable,
            "gating_weights": verdict.gating_weights,
            "expert_breakdown": {
                name: {
                    "expert_name": exp.expert_name,
                    "domain": exp.domain,
                    "expert_score": exp.expert_score,
                    "confidence": exp.confidence,
                    "key_findings": exp.key_findings,
                    "supporting_factors": exp.supporting_factors,
                    "afflicting_factors": exp.afflicting_factors,
                }
                for name, exp in verdict.expert_breakdown.items()
            },
            "conflict_resolution": {
                "has_conflict": verdict.conflict_resolution.has_conflict,
                "conflict_type": verdict.conflict_resolution.conflict_type,
                "precedence_rule_applied": verdict.conflict_resolution.precedence_rule_applied,
                "adjusted_score": verdict.conflict_resolution.adjusted_score,
                "resolution_narrative": verdict.conflict_resolution.resolution_narrative,
            },
            "consensus_summary": verdict.consensus_summary,
            "actionable_recommendation": verdict.actionable_recommendation,
            "rule_traces": verdict.rule_traces,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class DivisionalExploreRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    varga_number: int = Field(9, ge=1, le=60, description="Divisional chart divisor (1, 2, 3, 4, 7, 9, 10, 12, 24, 30, 60)")
    target_date_iso: Optional[str] = Field(None, description="Target date for active divisional dasha and dual dasha comparison")
    ayanamsa: str = Field("lahiri", description="Ayanamsa system")


@router.post("/divisional/explore")
def explore_divisional_chart(req: DivisionalExploreRequest) -> Dict[str, Any]:
    """
    Computes comprehensive multi-varga analysis, independent divisional Vimshottari dasha,
    Bhavottama badges, and dual dasha confluence comparison.
    """
    try:
        from apps.api.services.phalita_core.divisional_explorer_service import DivisionalExplorerService

        birth_dt = datetime.fromisoformat(req.birth_date_iso.replace("Z", "+00:00"))
        target_d = date.fromisoformat(req.target_date_iso) if req.target_date_iso else birth_dt.date()

        service = DivisionalExplorerService()
        res = service.explore_varga(
            birth_datetime=birth_dt,
            latitude=req.latitude,
            longitude=req.longitude,
            varga_number=req.varga_number,
            target_date=target_d,
            ayanamsa=req.ayanamsa,
        )

        return {
            "varga_code": res.varga_code,
            "varga_number": res.varga_number,
            "varga_name": res.varga_name,
            "significations": res.significations,
            "vimshopaka_weight": res.vimshopaka_weight,
            "ascendant_rashi": res.ascendant_rashi.capitalize() if isinstance(res.ascendant_rashi, str) else res.ascendant_rashi,
            "ascendant_rashi_idx": res.ascendant_rashi_idx,
            "ascendant_degree": res.ascendant_degree,
            "planets": [
                {
                    "planet": p.planet.capitalize(),
                    "rashi": p.rashi.capitalize() if isinstance(p.rashi, str) else p.rashi,
                    "rashi_index": p.rashi_index,
                    "rashi_degree": p.rashi_degree,
                    "house_number": p.house_number,
                    "is_bhavottama": p.is_bhavottama,
                    "bhavottama_type": p.bhavottama_type,
                    "dignity_label": p.dignity_label,
                    "dignity_score": p.dignity_score,
                    "final_varga_strength": p.final_varga_strength,
                    "is_debilitation_cancelled": p.is_debilitation_cancelled,
                }
                for p in res.planets
            ],
            "bhavottama_planets": list(res.bhavottama_planets),
            "active_divisional_dasha": {
                "varga_number": res.active_divisional_dasha.varga_number,
                "varga_code": getattr(res.active_divisional_dasha, "varga_code", None) or f"D{res.active_divisional_dasha.varga_number}",
                "target_date": (getattr(res.active_divisional_dasha, "target_date", None) or res.active_divisional_dasha.evaluation_date).isoformat(),
                "mahadasha_lord": res.active_divisional_dasha.mahadasha_lord,
                "antardasha_lord": res.active_divisional_dasha.antardasha_lord,
                "pratyantardasha_lord": res.active_divisional_dasha.pratyantardasha_lord,
                "md_start_date": (getattr(res.active_divisional_dasha, "md_start_date", None) or res.active_divisional_dasha.evaluation_date).isoformat(),
                "md_end_date": (getattr(res.active_divisional_dasha, "md_end_date", None) or res.active_divisional_dasha.evaluation_date).isoformat(),
                "ad_start_date": (getattr(res.active_divisional_dasha, "ad_start_date", None) or res.active_divisional_dasha.evaluation_date).isoformat(),
                "ad_end_date": (getattr(res.active_divisional_dasha, "ad_end_date", None) or res.active_divisional_dasha.evaluation_date).isoformat(),
            },
            "dual_dasha_comparison": {
                "domain": res.dual_dasha_comparison.domain,
                "target_varga": res.dual_dasha_comparison.target_varga,
                "d1_md_lord": res.dual_dasha_comparison.d1_md_lord,
                "d1_ad_lord": res.dual_dasha_comparison.d1_ad_lord,
                "div_md_lord": res.dual_dasha_comparison.div_md_lord,
                "div_ad_lord": res.dual_dasha_comparison.div_ad_lord,
                "d1_combined_strength": res.dual_dasha_comparison.d1_combined_strength,
                "div_combined_strength": res.dual_dasha_comparison.div_combined_strength,
                "is_divisional_supportive": res.dual_dasha_comparison.is_divisional_supportive,
                "siddhantic_verdict": res.dual_dasha_comparison.siddhantic_verdict,
            },
            "shastric_confluence_summary": res.shastric_confluence_summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))



@router.post("/cognitive/predict/marriage")
def predict_marriage_event(req: CognitiveEventPredictionRequest) -> Dict[str, Any]:
    """Cognitive Marriage Timing & Delay evaluation (7th house + Shukra + Mandi interference)."""
    try:
        from apps.api.services.intelligence.events.marriage import MarriagePredictor

        graph, dasha = _build_cognitive_context(req)
        res = MarriagePredictor.evaluate(graph, dasha)
        return {
            "event_type": res.event_type,
            "cognitive_score": res.cognitive_score,
            "is_probable": res.is_probable,
            "upagraha_modifier": res.upagraha_modifier,
            "reasoning_summary": res.reasoning_summary,
            "rule_traces": res.rule_traces,
            "level_assessments": [
                {
                    "level_name": a.level_name,
                    "lord": a.lord,
                    "is_house_lord": a.is_house_lord,
                    "is_occupant": a.is_occupant,
                    "aspect_strength": a.aspect_strength,
                    "dignity_score": a.dignity_score,
                    "level_score": a.level_score,
                    "reasons": a.reasons,
                }
                for a in res.level_assessments
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/cognitive/predict/career")
def predict_career_event(req: CognitiveEventPredictionRequest) -> Dict[str, Any]:
    """Cognitive Career & Status Elevation evaluation (10th house + Artha trikona + Gulika boost)."""
    try:
        from apps.api.services.intelligence.events.career import CareerPredictor

        graph, dasha = _build_cognitive_context(req)
        res = CareerPredictor.evaluate(graph, dasha)
        return {
            "event_type": res.event_type,
            "cognitive_score": res.cognitive_score,
            "is_probable": res.is_probable,
            "upagraha_modifier": res.upagraha_modifier,
            "reasoning_summary": res.reasoning_summary,
            "rule_traces": res.rule_traces,
            "level_assessments": [
                {
                    "level_name": a.level_name,
                    "lord": a.lord,
                    "is_house_lord": a.is_house_lord,
                    "is_occupant": a.is_occupant,
                    "aspect_strength": a.aspect_strength,
                    "dignity_score": a.dignity_score,
                    "level_score": a.level_score,
                    "reasons": a.reasons,
                }
                for a in res.level_assessments
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/cognitive/predict/health")
def predict_health_event(req: CognitiveEventPredictionRequest) -> Dict[str, Any]:
    """Cognitive Health Crisis & Illness evaluation (6th/8th house + Gulika 8th crisis weight)."""
    try:
        from apps.api.services.intelligence.events.health import HealthPredictor

        graph, dasha = _build_cognitive_context(req)
        res = HealthPredictor.evaluate(graph, dasha)
        return {
            "event_type": res.event_type,
            "cognitive_score": res.cognitive_score,
            "is_probable": res.is_probable,
            "upagraha_modifier": res.upagraha_modifier,
            "reasoning_summary": res.reasoning_summary,
            "rule_traces": res.rule_traces,
            "level_assessments": [
                {
                    "level_name": a.level_name,
                    "lord": a.lord,
                    "is_house_lord": a.is_house_lord,
                    "is_occupant": a.is_occupant,
                    "aspect_strength": a.aspect_strength,
                    "dignity_score": a.dignity_score,
                    "level_score": a.level_score,
                    "reasons": a.reasons,
                }
                for a in res.level_assessments
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/cognitive/predict/accident")
def predict_accident_event(req: CognitiveEventPredictionRequest) -> Dict[str, Any]:
    """Cognitive Accident & Sudden Trauma evaluation (8th house + Mars/Rahu + trauma indicators)."""
    try:
        from apps.api.services.intelligence.events.accident import AccidentPredictor

        graph, dasha = _build_cognitive_context(req)
        res = AccidentPredictor.evaluate(graph, dasha)
        return {
            "event_type": res.event_type,
            "cognitive_score": res.cognitive_score,
            "is_probable": res.is_probable,
            "upagraha_modifier": res.upagraha_modifier,
            "reasoning_summary": res.reasoning_summary,
            "rule_traces": res.rule_traces,
            "level_assessments": [
                {
                    "level_name": a.level_name,
                    "lord": a.lord,
                    "is_house_lord": a.is_house_lord,
                    "is_occupant": a.is_occupant,
                    "aspect_strength": a.aspect_strength,
                    "dignity_score": a.dignity_score,
                    "level_score": a.level_score,
                    "reasons": a.reasons,
                }
                for a in res.level_assessments
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class ShastricPipelineRequest(BaseModel):
    birth_datetime: str
    latitude: float
    longitude: float
    domain: str = "career"
    target_date: Optional[str] = None
    ayanamsa: str = "lahiri"


@router.post("/reasoning/pipeline")
def execute_shastric_reasoning_pipeline(req: ShastricPipelineRequest) -> Dict[str, Any]:
    """
    Executes the 6-stage Shastric Reasoning Pipeline:
    Canonical Facts -> Technique Resolver -> Rule Engine -> Evidence Aggregator -> Prediction Calibrator -> AI Explanation
    """
    try:
        from apps.api.services.phalita_core.shastric_reasoning_pipeline import ShastricReasoningPipeline

        dt = datetime.fromisoformat(req.birth_datetime)
        t_date = date.fromisoformat(req.target_date) if req.target_date else None

        pipeline = ShastricReasoningPipeline()
        res = pipeline.execute_pipeline(
            birth_datetime=dt,
            latitude=req.latitude,
            longitude=req.longitude,
            domain=req.domain,
            target_date=t_date,
            ayanamsa=req.ayanamsa,
        )

        return {
            "domain": res.domain,
            "target_date_iso": res.target_date_iso,
            "calibrated_signal_score": res.calibrated_prediction_verdict.calibrated_signal_score,
            "signal_tier": res.calibrated_prediction_verdict.signal_tier,
            "confidence_percentage": res.calibrated_prediction_verdict.confidence_percentage,
            "confidence_margin_delta": res.calibrated_prediction_verdict.confidence_margin_delta,
            "primary_promisers": res.calibrated_prediction_verdict.primary_shastric_promisers,
            "primary_inhibitors": res.calibrated_prediction_verdict.primary_inhibiting_factors,
            "evidence_provenance_id": res.calibrated_prediction_verdict.evidence_provenance_id,
            "executive_verdict": res.grounded_explanation.executive_verdict,
            "shastric_citations": res.grounded_explanation.shastric_classical_citations,
            "dasha_timing_synthesis": res.grounded_explanation.temporal_dasha_synthesis,
            "friction_analysis": res.grounded_explanation.friction_and_delay_analysis,
            "siddhantic_counsel": res.grounded_explanation.siddhantic_counsel,
            "full_markdown_report": res.grounded_explanation.full_markdown_report,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/validation/3tier-audit")
def get_3tier_validation_audit() -> Dict[str, Any]:
    """
    Executes the complete 3-Tier validation audit hierarchy:
    Tier 1 (N=5 Regression) -> Tier 2 (N=600 Generalization) -> Tier 3 (N=100 Holdout).
    """
    try:
        from apps.api.services.phalita_core.three_tier_validation_framework import ThreeTierValidationFramework

        framework = ThreeTierValidationFramework()
        audit = framework.run_full_3tier_audit()

        return {
            "timestamp_iso": audit.timestamp_iso,
            "overall_system_status": audit.overall_system_status,
            "tier1_regression": {
                "tier_name": audit.tier1_regression.tier_name,
                "total_cases": audit.tier1_regression.total_benchmark_cases,
                "passed_cases": audit.tier1_regression.passed_cases,
                "is_clean": audit.tier1_regression.is_regression_clean,
            },
            "tier2_generalization": {
                "tier_name": audit.tier2_generalization.tier_name,
                "total_cohort_charts": audit.tier2_generalization.total_cohort_charts,
                "total_evaluated_windows": audit.tier2_generalization.total_evaluated_windows,
                "precision": audit.tier2_generalization.precision,
                "recall_sensitivity": audit.tier2_generalization.recall_sensitivity,
                "false_positive_rate": audit.tier2_generalization.false_positive_rate,
                "specificity": audit.tier2_generalization.specificity,
                "roc_auc_score": audit.tier2_generalization.roc_auc_score,
                "pr_auc_score": audit.tier2_generalization.pr_auc_score,
                "brier_calibration_score": audit.tier2_generalization.brier_calibration_score,
                "is_statistically_robust": audit.tier2_generalization.is_statistically_robust,
                "domain_breakdown": audit.tier2_generalization.domain_breakdown,
            },
            "tier3_holdout": {
                "tier_name": audit.tier3_holdout.tier_name,
                "total_holdout_charts": audit.tier3_holdout.total_holdout_charts,
                "pre_freeze_hash": audit.tier3_holdout.pre_freeze_hash,
                "precision": audit.tier3_holdout.holdout_precision,
                "recall": audit.tier3_holdout.holdout_recall,
                "fpr": audit.tier3_holdout.holdout_fpr,
                "roc_auc": audit.tier3_holdout.holdout_roc_auc,
                "zero_leakage_verified": audit.tier3_holdout.zero_leakage_verified,
                "is_validation_passed": audit.tier3_holdout.is_validation_passed,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))





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
from apps.api.services.sarvato_bhadra_engine import SarvatoBhadraEngine, SarvatoBhadraReport

router = APIRouter(prefix="/api/v1/phalita", tags=["Phalita AI Prediction"])


class FeatureExtractionRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., description="Geographic latitude")
    longitude: float = Field(..., description="Geographic longitude")
    target_date_iso: Optional[str] = Field(None, description="Target evaluation date (YYYY-MM-DD)")


class ProspectiveScanRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., description="Geographic latitude")
    longitude: float = Field(..., description="Geographic longitude")
    scan_start_date_iso: Optional[str] = Field(None, description="Scan start date (YYYY-MM-DD), defaults to today")
    horizon_years: int = Field(3, description="Number of years to scan ahead (1 to 5)")
    domain: str = Field("career", description="Target domain: career, marriage, finance, health")
    min_probability_threshold: float = Field(0.08, description="Minimum calibrated probability threshold")


class ConsultationRequest(BaseModel):
    birth_date_iso: str = Field(..., description="ISO 8601 birth datetime (UTC)")
    latitude: float = Field(..., description="Geographic latitude")
    longitude: float = Field(..., description="Geographic longitude")
    native_name: str = Field("Native", description="Name of the person / entity")
    scan_start_year: int = Field(2020, description="Start year of life scan")
    scan_end_year: int = Field(2035, description="End year of life scan")
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

        return {
            "status": "SUCCESS",
            "native_name": req.native_name,
            "domain": req.domain,
            "scan_horizon": f"{req.scan_start_year} to {req.scan_end_year}",
            "timeline_summary": {
                "total_windows_scanned": timeline.total_windows_scanned,
                "pratyaksha_events_count": timeline.pratyaksha_events_count,
                "latent_potential_count": timeline.latent_potential_count,
                "transient_triggers_count": timeline.transient_triggers_count,
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
            "decision_timeline": [
                {
                    "window_start": w.window_start.isoformat(),
                    "window_end": w.window_end.isoformat(),
                    "mahadasha": w.mahadasha_lord,
                    "antardasha": w.antardasha_lord,
                    "probability": w.raw_probability,
                    "decision_tier": w.decision_tier,
                    "confidence_level": w.confidence_level,
                    "verdict": w.actionable_verdict,
                    "explanation_hi": w.explanation_hi,
                    "explanation_en": w.explanation_en,
                    "sav_10th_bindus": w.sav_10th_bindus,
                    "double_transit": w.double_transit,
                    "amatyakaraka": w.amatyakaraka,
                }
                for w in timeline.windows
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

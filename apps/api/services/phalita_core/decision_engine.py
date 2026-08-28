"""
AstroOS — Phalita Supervisory Adaptive Decision Governor (Phase 9)
===================================================================

Implements Layer 3 of the Self-Adaptive Decision Architecture:
Synthesizes data-driven Neural Mixture of Experts (Layer 2) with
deterministic Shastric Classical Confluence (Layer 1) to produce
interpretable, multi-tier scholar event classifications.

Self-Adaptive Supervisory Governor Principles:
- Native-Relative Peak Dynamic: Evaluates event probabilities relative to the native's own life baseline.
- 4-Tier Shastric Decision Categories:
  - TIER 1: PRATYAKSHA_PHALA (High-Certainty Landmark Manifestation)
    Top-quintile neural dasha fertility AND Classical Transit Sanction (Gochara + SAV >= 28).
  - TIER 2: SUSHUPTA_BEEJA (Latent Potential / High Dasha Fertility)
    Top-quintile neural dasha fertility, but Gochara double transit is absent/pending.
  - TIER 3: ALPA_PHALA (Transient Opportunity / Minor Trigger)
    Moderate relative neural confidence with active Gochara transit trigger.
  - TIER 4: SAMANYA_KAL (Baseline Routine Life)
    Standard background life slice.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
try:
    import torch
except ImportError:
    torch = None

from apps.api.domain.horoscope import D1Chart
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.classical_filter_engine import (
    ClassicalFilterEngine,
    ContinuousConfluenceReport,
)
from apps.api.services.phalita_core.tphalit_core import TPhalitCore
from apps.api.services.phalita_models.phalita_moe import PhalitaMoE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhalitaDecisionWindow:
    """Scholar-grade decision assessment for a single prospective time window."""
    window_start: date
    window_end: date
    mahadasha_lord: str
    antardasha_lord: str
    raw_probability: float
    decision_tier: str                  # "PRATYAKSHA_PHALA", "SUSHUPTA_BEEJA", "ALPA_PHALA", "SAMANYA_KAL"
    confidence_level: str               # "VERY_HIGH", "HIGH", "MODERATE", "LOW"
    actionable_verdict: str
    explanation_en: str
    explanation_hi: str
    sav_10th_bindus: int
    bav_md_bindus: int
    bav_ad_bindus: int
    jupiter_aspect: bool
    saturn_aspect: bool
    double_transit: bool
    amatyakaraka: str
    router_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class PhalitaConsultationTimeline:
    """Complete multi-year life scan with supervisory decision tiers."""
    native_name: str
    domain: str
    scan_start: date
    scan_end: date
    total_windows_scanned: int
    pratyaksha_events_count: int
    latent_potential_count: int
    transient_triggers_count: int
    windows: List[PhalitaDecisionWindow] = field(default_factory=list)


class PhalitaDecisionEngine:
    """Supervisory Adaptive Decision Governor combining MoE and Shastric principles."""

    def __init__(
        self,
        ephemeris_path: str = "data/ephemeris",
        moe_model: Optional[PhalitaMoE] = None,
    ):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.horoscope_engine = HoroscopeEngine(self.wrapper)
        self.dasha_engine = DashaEngine(self.wrapper)
        self.filter_engine = ClassicalFilterEngine(ephemeris_path=ephemeris_path)
        self.tphalit_core = TPhalitCore()
        self.moe_model = moe_model

    def evaluate_window(
        self,
        chart: D1Chart,
        slice_start: date,
        slice_end: date,
        mahadasha_lord: str,
        antardasha_lord: str,
        features: List[float],
        domain: str = "career",
        prob_percentile: float = 0.50,
    ) -> PhalitaDecisionWindow:
        """Evaluates a single Antardasha window through the self-adaptive supervisory governor."""
        # 1. Neural MoE Inference
        prob = 0.05
        router_weights = {"structural": 0.33, "divisional": 0.33, "temporal": 0.34}
        if self.moe_model is not None:
            self.moe_model.eval()
            x_t = torch.tensor([features], dtype=torch.float32)
            with torch.no_grad():
                logit, gate_w = self.moe_model(x_t)
                prob = float(torch.sigmoid(logit).item())
                router_weights = {
                    "structural": float(gate_w[0, 0].item()),
                    "divisional": float(gate_w[0, 1].item()),
                    "temporal": float(gate_w[0, 2].item()),
                }

        # 2. Classical Continuous Confluence Evaluation
        mid_days = (slice_end - slice_start).days // 2
        mid_date = slice_start + timedelta(days=mid_days)

        confl: ContinuousConfluenceReport = self.filter_engine.compute_continuous_confluence(
            chart=chart,
            target_date=mid_date,
            mahadasha_lord=mahadasha_lord,
            antardasha_lord=antardasha_lord,
            domain=domain,
        )

        jup_any = confl.jupiter_aspects_house or confl.jupiter_aspects_lord or confl.jupiter_aspects_amk
        sat_any = confl.saturn_aspects_house or confl.saturn_aspects_lord or confl.saturn_aspects_amk
        transit_sanction = (jup_any and sat_any) or (jup_any and confl.sav_bindus >= 28)

        # 3. Self-Adaptive 4-Tier Arbitration
        # Evaluates relative prominence (top quintile in native's life scan or absolute peak)
        is_peak_dasha = prob_percentile >= 0.70 or prob >= 0.0150
        is_moderate_dasha = prob_percentile >= 0.40 or prob >= 0.0080

        if is_peak_dasha and transit_sanction:
            tier = "PRATYAKSHA_PHALA"
            confidence = "VERY_HIGH"
            verdict = "Landmark Manifestation (Major Career Elevation / Landmark Event)"
            exp_en = (
                f"Exceptional alignment: High neural dasha fertility ({prob_percentile:.0%} percentile) supported by "
                f"Jupiter & Saturn transit sanction on 10H/10L and robust 10th Bhava SAV ({confl.sav_bindus} bindus)."
            )
            exp_hi = (
                f"Pratyaksha Phala: Uttam Dasha shakti (Top {100-prob_percentile*100:.0f}% me) ke sath Guru aur Shani ka 10th house/lord "
                f"par shubh Gochara drishti aur mazboot Ashtakavarga ({confl.sav_bindus} bindus) uplabdh hai."
            )
        elif is_peak_dasha and not transit_sanction:
            tier = "SUSHUPTA_BEEJA"
            confidence = "HIGH"
            verdict = "Latent Potential (Fertile Period; Awaiting Transit Trigger)"
            exp_en = (
                f"Strong internal dasha yoga ({prob_percentile:.0%} percentile), but transit sanction is incomplete. "
                f"Indicates intense groundwork, latent opportunities, or delayed recognition."
            )
            exp_hi = (
                f"Sushupta Beeja: Dasha me prabal kshamata hai, parantu Gochara transit trigger "
                f"sampoorn na hone ke karan falit me thoda vilamb ya prishthabhoomi taiyari rahegi."
            )
        elif is_moderate_dasha and (jup_any or sat_any):
            tier = "ALPA_PHALA"
            confidence = "MODERATE"
            verdict = "Transient Opportunity (Incremental Advancement / Minor Trigger)"
            exp_en = (
                f"Moderate dasha potential activated by active transit aspect. "
                f"Brings short-term role modifications or lateral career changes."
            )
            exp_hi = (
                f"Alpa Phala: Madhyam dasha par Gochara drishti ke asar se aakasmik "
                f"avsar ya sthan parivartan sambhav hai."
            )
        else:
            tier = "SAMANYA_KAL"
            confidence = "LOW"
            verdict = "Baseline Routine Period"
            exp_en = f"Standard background period with routine professional developments."
            exp_hi = f"Samanya Kal: Dasha aur Gochara samanya hain, niyamit dincharya rahegi."

        return PhalitaDecisionWindow(
            window_start=slice_start,
            window_end=slice_end,
            mahadasha_lord=mahadasha_lord.upper(),
            antardasha_lord=antardasha_lord.upper(),
            raw_probability=round(prob, 4),
            decision_tier=tier,
            confidence_level=confidence,
            actionable_verdict=verdict,
            explanation_en=exp_en,
            explanation_hi=exp_hi,
            sav_10th_bindus=confl.sav_bindus,
            bav_md_bindus=confl.md_bav_bindus,
            bav_ad_bindus=confl.ad_bav_bindus,
            jupiter_aspect=jup_any,
            saturn_aspect=sat_any,
            double_transit=(jup_any and sat_any),
            amatyakaraka=confl.amatyakaraka.upper(),
            router_weights=router_weights,
        )

    def scan_life_timeline(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        native_name: str = "Native",
        scan_start_year: int = 2000,
        scan_end_year: int = 2030,
        domain: str = "career",
    ) -> PhalitaConsultationTimeline:
        """Scans continuous Antardasha windows across a multi-year horizon with self-adaptive percentile ranking."""
        chart = self.horoscope_engine.generate_d1(birth_datetime, latitude, longitude)
        dasha_tree = self.dasha_engine.compute_vimshottari(birth_datetime, latitude, longitude)

        scan_start = date(scan_start_year, 1, 1)
        scan_end = date(scan_end_year, 1, 1)

        raw_windows_data = []

        # Pass 1: Extract vectors and raw probabilities for all prospective slices
        for md in dasha_tree.mahadashas:
            for ad in md.sub_periods:
                ad_start = ad.start_date.date() if isinstance(ad.start_date, datetime) else ad.start_date
                ad_end = ad.end_date.date() if isinstance(ad.end_date, datetime) else ad.end_date

                if ad_end < scan_start or ad_start > scan_end:
                    continue

                mid_days = (ad_end - ad_start).days // 2
                mid_date = ad_start + timedelta(days=mid_days)

                fv = self.tphalit_core.extract_full_vector(
                    chart=chart,
                    dasha_tree=dasha_tree,
                    target_date=mid_date,
                )

                prob = 0.05
                if self.moe_model is not None:
                    self.moe_model.eval()
                    x_t = torch.tensor([fv.raw_vector], dtype=torch.float32)
                    with torch.no_grad():
                        logit, _ = self.moe_model(x_t)
                        prob = float(torch.sigmoid(logit).item())

                raw_windows_data.append({
                    "ad_start": ad_start,
                    "ad_end": ad_end,
                    "md_lord": md.lord,
                    "ad_lord": ad.lord,
                    "features": fv.raw_vector,
                    "prob": prob,
                })

        if not raw_windows_data:
            return PhalitaConsultationTimeline(
                native_name=native_name,
                domain=domain,
                scan_start=scan_start,
                scan_end=scan_end,
                total_windows_scanned=0,
                pratyaksha_events_count=0,
                latent_potential_count=0,
                transient_triggers_count=0,
                windows=[],
            )

        # Pass 2: Calculate percentile distribution across native's own life
        probs_all = np.array([w["prob"] for w in raw_windows_data])
        windows: List[PhalitaDecisionWindow] = []
        p_count = 0
        s_count = 0
        a_count = 0

        for item in raw_windows_data:
            pct = float(np.mean(probs_all <= item["prob"]))
            dec_win = self.evaluate_window(
                chart=chart,
                slice_start=item["ad_start"],
                slice_end=item["ad_end"],
                mahadasha_lord=item["md_lord"],
                antardasha_lord=item["ad_lord"],
                features=item["features"],
                domain=domain,
                prob_percentile=pct,
            )

            if dec_win.decision_tier == "PRATYAKSHA_PHALA":
                p_count += 1
            elif dec_win.decision_tier == "SUSHUPTA_BEEJA":
                s_count += 1
            elif dec_win.decision_tier == "ALPA_PHALA":
                a_count += 1

            windows.append(dec_win)

        return PhalitaConsultationTimeline(
            native_name=native_name,
            domain=domain,
            scan_start=scan_start,
            scan_end=scan_end,
            total_windows_scanned=len(windows),
            pratyaksha_events_count=p_count,
            latent_potential_count=s_count,
            transient_triggers_count=a_count,
            windows=windows,
        )

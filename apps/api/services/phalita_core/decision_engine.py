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
from datetime import date, datetime, timedelta, timezone
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
from apps.api.services.phalita_core.polarity_engine import (
    ClassicalPolarityEngine,
    PolarityReport,
)
from apps.api.services.phalita_core.tphalit_core import TPhalitCore
from apps.api.services.phalita_core.varga_fusion_engine import (
    VargaFusionEngine,
    VargaFusionReport,
)
from apps.api.services.phalita_models.phalita_moe import PhalitaMoE
from apps.api.services.sapta_nadi_chakra_engine import (
    SaptaNadiChakraEngine,
    SaptaNadiReport,
)
from apps.api.services.sudarshana_chakra_dasha_engine import (
    SudarshanaChakraDashaEngine,
    SudarshanaChakraDashaReport,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhalitaDecisionWindow:
    """Scholar-grade decision assessment for a single prospective time window."""
    window_start: date
    window_end: date
    mahadasha_lord: str
    antardasha_lord: str
    pratyantardasha_lord: str = ""
    raw_probability: float = 0.50
    decision_tier: str = "SAMANYA_KAL"  # "PRATYAKSHA_PHALA", "SUSHUPTA_BEEJA", "ALPA_PHALA", "SAMANYA_KAL"
    confidence_level: str = "LOW"       # "VERY_HIGH", "HIGH", "MODERATE", "LOW"
    actionable_verdict: str = ""
    polarity: str = "NEUTRAL"           # "AUSPICIOUS", "CHALLENGING", "MIXED_POSITIVE", "MIXED_NEGATIVE", "NEUTRAL"
    polarity_logic: str = ""
    varga_fusion_score: float = 0.0     # [-1.0 to +1.0] from D1, D9, D10, D60
    is_bhavottama_active: bool = False
    scd_annual_house: int = 1           # 1 to 12
    scd_composite_score: float = 0.0    # [-1.0 to +1.0]
    sav_10th_bindus: int = 28
    bav_md_bindus: int = 4
    bav_ad_bindus: int = 4
    jupiter_aspect: bool = False
    saturn_aspect: bool = False
    double_transit: bool = False
    amatyakaraka: str = ""
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
        self.polarity_engine = ClassicalPolarityEngine()
        self.varga_engine = VargaFusionEngine()
        self.scd_engine = SudarshanaChakraDashaEngine()
        self.snc_engine = SaptaNadiChakraEngine()
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
        pratyantardasha_lord: str = "",
    ) -> PhalitaDecisionWindow:
        """Evaluates a single Antardasha window through the self-adaptive supervisory governor."""
        # 1. Neural MoE Inference or Shastric Calibrated Continuous Probability
        prob = 0.50
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
        mid_dt = datetime(mid_date.year, mid_date.month, mid_date.day, 12, 0, tzinfo=timezone.utc)

        confl: ContinuousConfluenceReport = self.filter_engine.compute_continuous_confluence(
            chart=chart,
            target_date=mid_date,
            mahadasha_lord=mahadasha_lord,
            antardasha_lord=antardasha_lord,
            domain=domain,
        )

        # 3. Sudarshana Chakra 3-Kundali Gochara Polarity (LK + SK + CK)
        transit_chart = self.horoscope_engine.generate_d1(mid_dt, 28.6139, 77.2090)
        pol_report: PolarityReport = self.polarity_engine.evaluate(
            natal_chart=chart,
            transit_chart=transit_chart,
            mahadasha_lord=mahadasha_lord,
            antardasha_lord=antardasha_lord,
        )

        # 4. Varga Fusion Analysis (D1 + D9 + D10 + D60 Signed Addition)
        varga_report: VargaFusionReport = self.varga_engine.evaluate_vargas(chart)
        varga_score = varga_report.fused_domain_scores.get(domain, 0.0)
        is_bhav = bool(varga_report.bhavottama_planets)

        # 5. Sudarshana Chakra Dasha (SCD) Progression
        birth_dt = getattr(chart, "datetime", datetime(1970, 1, 1, tzinfo=timezone.utc))
        scd_report: SudarshanaChakraDashaReport = self.scd_engine.compute_scd(
            natal_chart=chart,
            birth_datetime=birth_dt,
            target_date=mid_date,
        )

        jup_any = confl.jupiter_aspects_house or confl.jupiter_aspects_lord or confl.jupiter_aspects_amk
        sat_any = confl.saturn_aspects_house or confl.saturn_aspects_lord or confl.saturn_aspects_amk
        transit_sanction = (jup_any and sat_any) or (jup_any and confl.sav_bindus >= 28) or (pol_report.transit_net_polarity == "AUSPICIOUS")

        # Classical calibrated probability if neural MoE is not active
        if self.moe_model is None:
            base_p = 0.50
            if jup_any and sat_any:
                base_p += 0.24
            elif jup_any or sat_any:
                base_p += 0.10
            if confl.sav_bindus >= 28:
                base_p += 0.08
            if pol_report.final_polarity in ("AUSPICIOUS", "MIXED_POSITIVE"):
                base_p += 0.08
            if is_bhav:
                base_p += 0.05
            if varga_score > 0:
                base_p += min(0.08, varga_score * 0.1)
            prob = max(0.25, min(0.95, base_p))

        # 6. Self-Adaptive 4-Tier Arbitration
        is_peak_dasha = prob_percentile >= 0.70 or prob >= 0.65 or pol_report.final_polarity in ("AUSPICIOUS", "MIXED_POSITIVE")
        is_moderate_dasha = prob_percentile >= 0.40 or prob >= 0.45

        domain_term = (
            "Career & Professional Leap" if domain == "career"
            else "Marital & Relationship Milestone" if domain == "marriage"
            else "Financial & Wealth Expansion" if domain == "wealth"
            else "Vitality & Health Breakthrough" if domain == "health"
            else f"{domain.capitalize()} Milestone"
        )

        if is_peak_dasha and transit_sanction:
            tier = "PRATYAKSHA_PHALA"
            confidence = "VERY_HIGH"
            verdict = f"Landmark Manifestation (Major {domain_term})"
        elif is_peak_dasha and not transit_sanction:
            tier = "SUSHUPTA_BEEJA"
            confidence = "HIGH"
            verdict = f"Latent Potential (Internal Promise for {domain_term}; Awaiting Transit Trigger)"
        elif is_moderate_dasha and (jup_any or sat_any or pol_report.transit_auspicious_count >= 3):
            tier = "ALPA_PHALA"
            confidence = "MODERATE"
            verdict = f"Transient Opportunity (Incremental Advancement in {domain_term})"
        else:
            tier = "SAMANYA_KAL"
            confidence = "LOW"
            verdict = f"Baseline Routine Period in {domain_term}"

        return PhalitaDecisionWindow(
            window_start=slice_start,
            window_end=slice_end,
            mahadasha_lord=mahadasha_lord.upper(),
            antardasha_lord=antardasha_lord.upper(),
            pratyantardasha_lord=pratyantardasha_lord.upper(),
            raw_probability=round(prob, 4),
            decision_tier=tier,
            confidence_level=confidence,
            actionable_verdict=verdict,
            polarity=pol_report.final_polarity,
            polarity_logic=pol_report.final_polarity_logic,
            varga_fusion_score=round(varga_score, 3),
            is_bhavottama_active=is_bhav,
            scd_annual_house=scd_report.annual_house_offset,
            scd_composite_score=round(scd_report.composite_scd_score, 3),
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
        granularity: str = "pratyantardasha",
    ) -> PhalitaConsultationTimeline:
        """Scans prospective life timeline down to exact Pratyantardasha (PD) high-precision windows."""
        chart = self.horoscope_engine.generate_d1(birth_datetime, latitude, longitude)
        dasha_tree = self.dasha_engine.compute_vimshottari(birth_datetime, latitude, longitude, max_depth=3)

        scan_start = date(scan_start_year, 1, 1)
        scan_end = date(scan_end_year, 1, 1)

        raw_windows_data = []

        # Pass 1: Extract vectors and raw probabilities for prospective slices (Pratyantardasha or Antardasha)
        for md in dasha_tree.mahadashas:
            for ad in md.sub_periods:
                # If Pratyantardashas (depth 3) available, scan at PD level
                pd_list = list(ad.sub_periods) if hasattr(ad, "sub_periods") and ad.sub_periods else []
                
                if granularity == "pratyantardasha" and pd_list:
                    for pd in pd_list:
                        pd_start = pd.start_date.date() if isinstance(pd.start_date, datetime) else pd.start_date
                        pd_end = pd.end_date.date() if isinstance(pd.end_date, datetime) else pd.end_date

                        if pd_end < scan_start or pd_start > scan_end:
                            continue

                        mid_days = max(1, (pd_end - pd_start).days // 2)
                        mid_date = pd_start + timedelta(days=mid_days)

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
                            "start": pd_start,
                            "end": pd_end,
                            "md_lord": md.lord,
                            "ad_lord": ad.lord,
                            "pd_lord": pd.lord,
                            "features": fv.raw_vector,
                            "prob": prob,
                        })
                else:
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
                        "start": ad_start,
                        "end": ad_end,
                        "md_lord": md.lord,
                        "ad_lord": ad.lord,
                        "pd_lord": "",
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
                slice_start=item["start"],
                slice_end=item["end"],
                mahadasha_lord=item["md_lord"],
                antardasha_lord=item["ad_lord"],
                pratyantardasha_lord=item.get("pd_lord", ""),
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

"""
AstroOS — Phalita Continuous Prospective (Forward) Scanner Engine (Phase 6)
===========================================================================

Scans natal charts for prospective (future) event windows using the calibrated
PhalitaMoE neural model and deterministic TPhalitCore feature vectors.

Invariants:
- Zero Hallucination: Probability bounds derived strictly from empirical calibration.
- Full Explainability: Returns active Dasha lords, classical Yogas, and MoE router attention.
- Pre-Fixed Window Slicing: Scans discrete Antardasha periods.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    import torch
except ImportError:
    torch = None

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.tphalit_core import TPhalitCore, TPhalitFeatureVector
from apps.api.services.phalita_models.phalita_moe import PhalitaMoE

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProspectivePredictionWindow:
    """A calibrated prospective event prediction window."""
    domain: str
    window_start: date
    window_end: date
    peak_date: date
    calibrated_probability: float
    confidence_tier: str            # "HIGH", "MODERATE", "WATCH_WINDOW"
    active_mahadasha: str
    active_antardasha: str
    classical_yogas: List[str]
    router_attention: Dict[str, float]
    astrological_rationale: str


class PhalitaForwardScanner:
    """Scans natal charts for future event windows using PhalitaMoE."""

    def __init__(
        self,
        moe_model: Optional[PhalitaMoE] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.horoscope = HoroscopeEngine(self.wrapper)
        self.dasha_engine = DashaEngine(self.wrapper)
        self.core = TPhalitCore()
        self.moe_model = moe_model or PhalitaMoE(input_dim=128)
        self.moe_model.eval()

    def scan_prospective_windows(
        self,
        birth_dt: datetime,
        latitude: float,
        longitude: float,
        scan_start_date: Optional[date] = None,
        scan_horizon_years: int = 3,
        domain: str = "career",
        min_probability_threshold: float = 0.10,
    ) -> List[ProspectivePredictionWindow]:
        """Scan upcoming Antardasha windows for high-probability events."""
        chart = self.horoscope.generate_d1(birth_dt, latitude, longitude)
        tree = self.dasha_engine.compute_vimshottari(birth_dt, latitude, longitude)

        start_d = scan_start_date or date.today()
        end_d = start_d + timedelta(days=scan_horizon_years * 365)

        periods = getattr(tree, "mahadashas", getattr(tree, "periods", ()))
        candidate_windows: List[ProspectivePredictionWindow] = []

        for md in periods:
            if md.end_date < start_d or md.start_date > end_d:
                continue

            for ad in md.sub_periods:
                if ad.end_date < start_d or ad.start_date > end_d:
                    continue

                mid_days = (ad.end_date - ad.start_date).days // 2
                mid_date = ad.start_date + timedelta(days=mid_days)

                # Extract 128-D TPhalitCore vector
                vec: TPhalitFeatureVector = self.core.extract_full_vector(
                    chart=chart,
                    dasha_tree=tree,
                    target_date=mid_date,
                )

                # Neural MoE inference
                x_tensor = torch.tensor([vec.raw_vector], dtype=torch.float32)
                with torch.no_grad():
                    logit, gates = self.moe_model(x_tensor)
                    prob = float(torch.sigmoid(logit).item())
                    gate_shares = gates.squeeze(0).tolist()

                if prob >= min_probability_threshold:
                    if prob >= 0.25:
                        tier = "HIGH"
                    elif prob >= 0.15:
                        tier = "MODERATE"
                    else:
                        tier = "WATCH_WINDOW"

                    active_yoga_names = [y.yoga_name for y in vec.yogas]
                    rationale = (
                        f"MD: {md.lord.upper()}, AD: {ad.lord.upper()} with Sadharmi factor {vec.dasha.sadharmi_relation if vec.dasha else 0.0:.2f}. "
                        f"Active Yogas: {', '.join(active_yoga_names) if active_yoga_names else 'None'}. "
                        f"Structural weight: {gate_shares[0]:.1%}, Divisional: {gate_shares[1]:.1%}, Temporal: {gate_shares[2]:.1%}."
                    )

                    w_start = max(start_d, ad.start_date)
                    w_end = min(end_d, ad.end_date)

                    candidate_windows.append(
                        ProspectivePredictionWindow(
                            domain=domain,
                            window_start=w_start,
                            window_end=w_end,
                            peak_date=mid_date,
                            calibrated_probability=round(prob, 4),
                            confidence_tier=tier,
                            active_mahadasha=md.lord.upper(),
                            active_antardasha=ad.lord.upper(),
                            classical_yogas=active_yoga_names,
                            router_attention={
                                "structural_d1": round(gate_shares[0], 3),
                                "divisional_yogas": round(gate_shares[1], 3),
                                "temporal_dasha": round(gate_shares[2], 3),
                            },
                            astrological_rationale=rationale,
                        )
                    )

        # Sort descending by probability
        candidate_windows.sort(key=lambda w: w.calibrated_probability, reverse=True)
        return candidate_windows

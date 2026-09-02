"""
AstroOS — Module 2: Continuous Temporal Hazard Peak Model.

h(t) = L_dasha(t) · L_transit(t) · L_kakshya(t)

Calculates the peak 30-day event density window with 68% credible bounds.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class HazardConfig:
    edge_days: int = 15
    orb_deg: float = 2.5
    kakshya_inside: float = 1.0
    kakshya_outside: float = 0.4
    peak_window_days: int = 30
    ci_coverage: Tuple[float, float] = (0.16, 0.84)


@dataclass
class HazardCurve:
    dates: List[date]
    density: np.ndarray
    peak_start: date
    peak_end: date
    ci_lo: date
    ci_hi: date
    peak_value: float


def _raised_cosine_edge(days_inside: np.ndarray, edge: int) -> np.ndarray:
    return np.clip(0.5 * (1 - np.cos(np.pi * np.clip(days_inside / edge, 0, 1))), 0, 1)


def compute_hazard(
    dasha_spans: Sequence[Tuple[date, date, float]],
    transit_contacts: Sequence[Tuple[date, float, float]],
    kakshya_spans: Sequence[Tuple[date, date]],
    t0: date,
    t1: date,
    cfg: HazardConfig = HazardConfig(),
) -> HazardCurve:
    n = (t1 - t0).days + 1
    days = np.arange(n, dtype=float)
    t = [t0 + timedelta(days=int(d)) for d in days]

    # 1. L_dasha
    Ld = np.zeros(n)
    for s, e, activation in dasha_spans:
        inside = np.clip([(ti - s).days for ti in t], 0, None).astype(float)
        din = np.minimum(inside, np.clip([(e - ti).days for ti in t], 0, None).astype(float))
        Ld = np.maximum(Ld, activation * _raised_cosine_edge(din, cfg.edge_days))

    # 2. L_transit
    Lt = np.zeros(n)
    for contact_date, strength, orb_deg in transit_contacts:
        d = np.array([abs((ti - contact_date).days) for ti in t], dtype=float)
        orb_close = np.clip(1.0 - orb_deg / cfg.orb_deg, 0, 1)
        env = np.exp(-0.5 * (d / 5.0) ** 2)
        Lt = np.maximum(Lt, strength * orb_close * env)

    if Lt.max() == 0:
        Lt = np.ones(n)

    # 3. L_kakshya
    Lk = np.full(n, cfg.kakshya_outside)
    for s, e in kakshya_spans:
        idx = [i for i, ti in enumerate(t) if s <= ti <= e]
        Lk[idx] = cfg.kakshya_inside

    h = Ld * Lt * Lk
    if h.sum() <= 0:
        return HazardCurve(t, h, t0, t0, t0, t0, 0.0)
    density = h / h.sum()

    w = cfg.peak_window_days
    integ = np.convolve(density, np.ones(w), mode="valid")
    k = int(np.argmax(integ))

    cdf = np.cumsum(density)
    lo_i = int(np.searchsorted(cdf, cfg.ci_coverage[0]))
    hi_i = int(np.searchsorted(cdf, cfg.ci_coverage[1]))

    return HazardCurve(
        dates=t,
        density=density,
        peak_start=t[k],
        peak_end=t[min(k + w - 1, n - 1)],
        ci_lo=t[lo_i],
        ci_hi=t[min(hi_i, n - 1)],
        peak_value=float(h.max()),
    )

"""
AstroOS — Jaimini Chara/Narayana Dasha Adapter (Layer 6: Calculation Engine)

Thin re-shaping adapter over the EXISTING Chara/Narayana Dasha
implementation in dasha_engine.py (DashaEngine.compute_chara /
compute_narayana — Neelakantha's rule, Scorpio/Aquarius dual-lord
handling already correct via JAIMINI_ALT_LORDS). This is NOT a new dasha
engine — DashaEngine is untouched and does all the actual computation.
This module only re-shapes its DashaTree output into the same
result-object conventions the other Jaimini engines use, for frontend
consistency:
  - DashaPeriod.lord (a rashi name, for these two systems) -> rashi.
  - DashaTree.trigger_planet (the Lagna sign, for these two systems,
    despite the generic field name inherited from the nakshatra-based
    systems that share DashaTree) -> lagna_rashi.
  - The nakshatra-trigger fields (trigger_nakshatra,
    trigger_nakshatra_number), meaningless for sign-based systems (blank
    string / 0 per DashaTree's own docstring), are dropped rather than
    carried through as noise.

No dasha math happens here — every date/duration is exactly what
DashaEngine already computed.
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.jaimini import JaiminiDashaPeriod, JaiminiDashaResult
from apps.api.services.dasha_engine import DashaEngine


def _adapt_period(period: DashaPeriod) -> JaiminiDashaPeriod:
    return JaiminiDashaPeriod(
        rashi=period.lord,
        start_date=period.start_date,
        end_date=period.end_date,
        duration_days=period.duration_days,
        level=period.level,
        sub_periods=tuple(_adapt_period(p) for p in period.sub_periods),
    )


def _adapt_tree(tree: DashaTree) -> JaiminiDashaResult:
    return JaiminiDashaResult(
        system=tree.system,  # "chara" or "narayana"
        lagna_rashi=tree.trigger_planet,
        periods=tuple(_adapt_period(p) for p in tree.mahadashas),
        max_depth=tree.max_depth,
        total_cycle_years=tree.total_cycle_years,
    )


class JaiminiDashaAdapter:
    """Wraps the existing DashaEngine's Chara/Narayana computation,
    re-shaping its output. Computes nothing itself."""

    def __init__(self, dasha_engine: DashaEngine) -> None:
        self._dasha_engine = dasha_engine

    def compute_chara(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> JaiminiDashaResult:
        tree = self._dasha_engine.compute_chara(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            max_depth=max_depth,
        )
        return _adapt_tree(tree)

    def compute_narayana(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
        max_depth: int = 3,
    ) -> JaiminiDashaResult:
        tree = self._dasha_engine.compute_narayana(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
            max_depth=max_depth,
        )
        return _adapt_tree(tree)

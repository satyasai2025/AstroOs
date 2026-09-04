"""
AstroOS — Yoga Activation Timeline (Phase 2, v2.1.0)

Correlates detected yogas with Dasha periods to determine when each
yoga activates or peaks during a native's Mahadasha/Antardasha cycle.

A yoga "activates" when the ruling planet(s) of the yoga enter their
Mahadasha or Antardasha period. This is a simplified activation model —
the full classical model also considers transits and specific nakshatra
placements, which are tracked as Phase 3 deferrals.

Design notes:
  - Each yoga's involved_planets determine which dasha lord activates it.
  - For multi-planet yogas, activation occurs when ANY involved planet
    is the current Mahadasha or Antardasha lord.
  - The score is boosted during the activating period and reduced otherwise.
  - This module depends on the DashaTree structure from dasha_engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.yoga import YogaResult


_LEVEL_NAMES = {1: "Mahadasha", 2: "Antardasha", 3: "Pratyantar", 4: "Sookshma", 5: "Prana"}


@dataclass(frozen=True)
class YogaActivation:
    """
    One activation entry: a dasha period during which the yoga is active.

    Attributes:
        yoga_id: The yoga being activated.
        planet: Which involved planet's dasha is activating.
        period_name: Human-readable dasha period name (e.g. "Jupiter Mahadasha / Saturn Antardasha").
        period_level: Depth of the dasha period (1=Mahadasha, 2=Antardasha, etc.)
        start_date: Start of the activation period.
        end_date: End of the activation period.
        is_current: True if this period contains today's date.
    """
    yoga_id: str
    planet: str
    period_name: str
    period_level: int
    start_date: date
    end_date: date
    is_current: bool = False


@dataclass(frozen=True)
class YogaTimeline:
    """
    Complete activation timeline for one yoga across all dasha periods.
    """
    yoga_id: str
    yoga_name: str
    activations: tuple[YogaActivation, ...] = field(default_factory=tuple)
    current_activation: Optional[YogaActivation] = None


def _build_period_name(period: DashaPeriod) -> str:
    """Construct a human-readable period name from the lord and level."""
    level_name = _LEVEL_NAMES.get(period.level, f"Level-{period.level}")
    return f"{period.lord.capitalize()} {level_name}"


def _flatten_periods(
    period: DashaPeriod,
    involved_planets: set[str],
    today: date,
    max_depth: int = 3,
    ancestor_names: tuple[str, ...] = (),
) -> list[YogaActivation]:
    """
    Recursively flatten a DashaPeriod tree and extract activation entries
    for the involved planets. Only goes to Mahadasha (level 1) and
    Antardasha (level 2) by default for performance; Pratyantar can be
    requested via max_depth.

    ancestor_names tracks the chain of period names for composing full
    names like "Jupiter Mahadasha / Saturn Antardasha".
    """
    activations: list[YogaActivation] = []
    level = period.level
    current_name = _build_period_name(period)
    full_name = " / ".join((*ancestor_names, current_name)) if ancestor_names else current_name

    if level <= max_depth and period.lord in involved_planets:
        is_current = period.contains(today)
        activations.append(YogaActivation(
            yoga_id="",  # filled in by caller
            planet=period.lord,
            period_name=full_name,
            period_level=level,
            start_date=period.start_date,
            end_date=period.end_date,
            is_current=is_current,
        ))

    # Recurse into sub-periods only if we haven't hit max depth
    if level < max_depth and period.sub_periods:
        for sub in period.sub_periods:
            activations.extend(_flatten_periods(
                sub, involved_planets, today, max_depth,
                ancestor_names=(*ancestor_names, current_name),
            ))

    return activations


def build_yoga_timeline(
    yoga_result: YogaResult,
    dasha_tree: DashaTree,
    today: date,
    max_depth: int = 3,
) -> YogaTimeline:
    """
    Build an activation timeline for one yoga across a DashaTree.

    Args:
        yoga_result: The yoga result (must be is_present=True for meaningful activations).
        dasha_tree: The computed DashaTree for the native.
        today: Today's date (used to mark current activation).
        max_depth: Maximum dasha depth to search (1=Mahadasha only, 2=+Antardasha, 3=+Pratyantar).

    Returns:
        YogaTimeline with all activation periods and the current one (if any).
    """
    if not yoga_result.is_present or not yoga_result.involved_planets:
        return YogaTimeline(yoga_id=yoga_result.yoga_id, yoga_name=yoga_result.name)

    involved_planets = set(yoga_result.involved_planets)
    today_date = today.date() if hasattr(today, 'date') else today

    activations: list[YogaActivation] = []
    for period in dasha_tree.mahadashas:
        activations.extend(_flatten_periods(period, involved_planets, today_date, max_depth))

    # Sort by start date
    activations.sort(key=lambda a: a.start_date)

    # Fill in yoga_id and find current activation
    filled_activations: list[YogaActivation] = []
    current: Optional[YogaActivation] = None
    for act in activations:
        from dataclasses import replace
        filled = replace(act, yoga_id=yoga_result.yoga_id)
        filled_activations.append(filled)
        if filled.is_current:
            current = filled

    return YogaTimeline(
        yoga_id=yoga_result.yoga_id,
        yoga_name=yoga_result.name,
        activations=tuple(filled_activations),
        current_activation=current,
    )


def build_all_timelines(
    results: list[YogaResult],
    dasha_tree: DashaTree,
    today: date,
    max_depth: int = 3,
) -> list[YogaTimeline]:
    """
    Build activation timelines for all present yogas.
    """
    timelines: list[YogaTimeline] = []
    for r in results:
        if r.is_present:
            timelines.append(build_yoga_timeline(r, dasha_tree, today, max_depth))
    return timelines

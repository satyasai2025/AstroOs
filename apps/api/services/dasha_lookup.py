"""
AstroOS — Dasha-by-Date Lookup (Module 14, Phase 1)

The one genuinely new piece of logic the Event Engine design audit
introduces (§5/§7.1). NOT a calculation — a pure tree-walk over an
ALREADY-COMPUTED DashaTree (from DashaEngine), same category as
HouseEngine.get_house_lord() or the house.{N}.lord_house derivation in
Module 13's FactBuilder: it navigates a structure another engine
already built, it does not perform any astrology itself.

DashaEngine only ever builds full trees; nothing before this walked
one by an arbitrary date. This closes exactly that gap and nothing
more.
"""

from __future__ import annotations

from datetime import date

from apps.api.domain.dasha import DashaPeriod, DashaTree


def find_active_dasha_chain(tree: DashaTree, target_date: date) -> tuple[DashaPeriod, ...]:
    """
    Returns the chain of active DashaPeriods for `target_date`, from
    Mahadasha (level 1) down through whatever depth `tree` was
    actually built to (Antardasha, Pratyantar, Sookshma, Prana — as
    far as `sub_periods` goes for this tree).

    A period is active for `target_date` if
    `period.start_date <= target_date < period.end_date` — matching
    how DashaEngine itself builds contiguous, non-overlapping periods
    (each level's periods partition its parent's date range, with the
    final period at each level clamped to the exact parent end).

    Returns an empty tuple if `target_date` falls outside every
    Mahadasha in the tree (before the tree's start, or on/after its
    exact final end date — that boundary is exclusive, consistent with
    every other period boundary in the tree). This is a genuine
    reflection of the tree's own bounds, not an error — a caller asking
    about a date the tree wasn't built to cover gets an empty chain,
    not a fabricated one.
    """

    def _search(periods: tuple[DashaPeriod, ...]) -> tuple[DashaPeriod, ...]:
        for period in periods:
            if period.start_date <= target_date < period.end_date:
                return (period,) + _search(period.sub_periods)
        return ()

    return _search(tree.mahadashas)

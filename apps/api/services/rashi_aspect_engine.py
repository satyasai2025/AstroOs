"""
AstroOS — Jaimini Rashi Aspect Engine (Layer 6: Calculation Engine)

Stateless service computing Jaimini's sign-based aspect (Rashi Drishti)
— structurally different from Parashari Graha Drishti
(apps/api/services/aspect_engine.py, which aspects by HOUSE OFFSET from a
planet's exact longitude). Rashi Drishti aspects by sign NATURE and is
fixed for every chart — it never depends on planetary longitude, only on
which sign a planet occupies. No ephemeris/DB dependency.

The classical sutra (three clauses):
  1. Each Chara (movable) sign aspects all 4 Sthira (fixed) signs EXCEPT
     the one immediately following it zodiacally.
  2. Each Sthira sign aspects all 4 Chara signs EXCEPT the one
     immediately preceding it zodiacally.
  3. Each Dvisvabhava (dual) sign aspects the other 3 Dvisvabhava signs,
     with no exception — no two dual signs are ever zodiacally adjacent
     (the sign pattern always repeats Chara-Sthira-Dvisvabhava), so the
     "except the adjacent one" clause has no dual-sign case to apply to.

Clauses 1 and 2 are mutual: for every (Chara_i, Sthira_i) zodiacally-
adjacent pair, Chara_i excludes Sthira_i AND Sthira_i excludes Chara_i —
so the resulting aspect relation is fully symmetric (if A aspects B, B
always aspects A back), unlike Parashari Graha Drishti, which is not
symmetric in general.
"""

from __future__ import annotations

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import RashiAspect, RashiAspectResult
from apps.api.services.jaimini_shared import (
    RASHI_LIST,
    planets_in_rashi,
    sign_nature,
    signs_from,
)


def _targets_for(rashi: str) -> tuple[str, ...]:
    nature = sign_nature(rashi)

    if nature == "chara":
        excluded = signs_from(rashi, 1)  # the sthira sign immediately following
        return tuple(r for r in RASHI_LIST if sign_nature(r) == "sthira" and r != excluded)
    if nature == "sthira":
        excluded = signs_from(rashi, -1)  # the chara sign immediately preceding
        return tuple(r for r in RASHI_LIST if sign_nature(r) == "chara" and r != excluded)
    # dvisvabhava
    return tuple(r for r in RASHI_LIST if sign_nature(r) == "dvisvabhava" and r != rashi)


class RashiAspectEngine:
    """
    Stateless Jaimini sign-aspect calculator.

    The structural matrix (which sign aspects which) is chart-
    independent — compute_matrix() needs no chart at all — but compute()
    additionally annotates it with which real grahas occupy each sign,
    for a given D1Chart.
    """

    def compute_matrix(self) -> dict[str, tuple[str, ...]]:
        return {rashi: _targets_for(rashi) for rashi in RASHI_LIST}

    def compute(self, chart: D1Chart) -> RashiAspectResult:
        matrix = self.compute_matrix()
        aspects: list[RashiAspect] = []
        for from_rashi, targets in matrix.items():
            aspecting_planets = tuple(planets_in_rashi(chart, from_rashi))
            if not aspecting_planets:
                continue  # no graha occupies this sign — nothing casts this aspect
            for to_rashi in targets:
                aspects.append(
                    RashiAspect(
                        from_rashi=from_rashi,
                        to_rashi=to_rashi,
                        aspecting_planets=aspecting_planets,
                        aspected_planets=tuple(planets_in_rashi(chart, to_rashi)),
                    )
                )
        return RashiAspectResult(matrix=matrix, aspects=tuple(aspects))

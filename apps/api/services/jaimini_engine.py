"""
AstroOS — Jaimini Chara Karaka Engine (Layer 6: Calculation Engine)

Stateless service computing Chara Karaka rankings from an already-built
D1Chart. No Swiss Ephemeris or database dependency — same scope
discipline as YogaEngine/HouseEngine: this reads SiderealPosition's
already-computed rashi_degree and speed_deg_per_day (both produced by
EphemerisWrapper) and never touches the ephemeris layer directly.
Deliberately NOT wired into any router yet — wiring this into an
endpoint is a separate, later layer.

Chara Karaka source planets, by scheme:
  - sapta_karaka: sun, moon, mars, mercury, jupiter, venus, saturn.
  - ashta_karaka: the same 7 + rahu. Ketu is NEVER included in either
    scheme — see domain/jaimini.py's module docstring.

Ranking rule: descending karaka_degree (see _karaka_degree for Rahu's
special measurement). Ties are broken, in strict order, per the
classical Jaimini tie-breaking sutra:
  1. Higher absolute daily motion (speed_deg_per_day) wins the higher
     rank — the faster-moving graha is deemed to hold "more" degrees at
     sub-arcsecond precision than a same-degree slower one.
  2. If speeds are also identical, natural benefic/malefic hierarchy
     (Jupiter > Venus > Mercury > Moon > Sun > Saturn > Mars > Rahu)
     resolves it — the greater natural benefic always outranks.
Rule 2 is a total order over all 8 possible source planets, so the
overall sort key can never leave a genuine unresolved tie. In practice,
real ephemeris data essentially never produces an exact degree/minute/
second match between two grahas — both rules exist to handle synthetic
or deliberately-constructed test charts correctly rather than by luck.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import (
    KARAKA_NAMES_ASHTA,
    KARAKA_NAMES_SAPTA,
    CharaKaraka,
    CharaKarakaResult,
    CharaKarakaScheme,
)

_SAPTA_PLANETS: tuple[str, ...] = (
    "sun",
    "moon",
    "mars",
    "mercury",
    "jupiter",
    "venus",
    "saturn",
)
_ASHTA_PLANETS: tuple[str, ...] = _SAPTA_PLANETS + ("rahu",)

_NATURAL_BENEFIC_RANK: dict[str, int] = {
    # Lower = stronger natural benefic. Only ever consulted as the final
    # tie-breaker, after karaka_degree and speed have both tied exactly.
    "jupiter": 0,
    "venus": 1,
    "mercury": 2,
    "moon": 3,
    "sun": 4,
    "saturn": 5,
    "mars": 6,
    "rahu": 7,
}

_ARCSEC_SUBDIVISIONS = 100
"""Two karaka_degree values are considered equal only if they match to
this many subdivisions of an arc-second — tight enough that ordinary
floating-point noise from ephemeris math never false-triggers the
tie-breaker, while a genuinely identical (e.g. synthetic test) longitude
still ties correctly."""


def _karaka_degree(planet: str, rashi_degree: float) -> float:
    """
    The value actually ranked on. Rahu is always in apparent retrograde
    motion through the zodiac, so classical Jaimini measures its karaka
    degree as "how much of the sign remains" (30 - rashi_degree) rather
    than degrees already traversed — the same convention used by every
    major reference implementation (Classical Vedic System, Parashara's Light).
    Every other graha uses its rashi_degree directly.
    """
    if planet == "rahu":
        return 30.0 - rashi_degree
    return rashi_degree


def _arcsec_grid(karaka_degree: float) -> int:
    """Round to a fixed arc-second-fraction grid so float noise never
    creates or hides a tie; see _ARCSEC_SUBDIVISIONS."""
    return round(karaka_degree * 3600 * _ARCSEC_SUBDIVISIONS)


class CharaKarakaEngine:
    """Stateless Chara Karaka calculator — operates purely on an
    already-computed D1Chart, no ephemeris/DB dependency."""

    def compute(
        self, chart: D1Chart, scheme: CharaKarakaScheme = "sapta_karaka"
    ) -> CharaKarakaResult:
        source_planets = _SAPTA_PLANETS if scheme == "sapta_karaka" else _ASHTA_PLANETS
        karaka_names = KARAKA_NAMES_SAPTA if scheme == "sapta_karaka" else KARAKA_NAMES_ASHTA

        positions: dict[str, SiderealPosition] = {p.planet: p for p in chart.planets}
        missing = [p for p in source_planets if p not in positions]
        if missing:
            raise ValueError(f"Chart is missing required planet(s) for Chara Karaka: {missing}")

        candidates = [positions[p] for p in source_planets]
        ordered, tiebreak_by_planet = self._rank(candidates)

        karakas = tuple(
            CharaKaraka(
                rank=i + 1,
                karaka_name=karaka_names[i],
                planet=pos.planet,
                rashi=pos.rashi,
                rashi_degree=round(pos.rashi_degree, 6),
                karaka_degree=round(_karaka_degree(pos.planet, pos.rashi_degree), 6),
                speed_deg_per_day=pos.speed_deg_per_day,
                is_retrograde=pos.is_retrograde,
                tiebreak_rule=tiebreak_by_planet[pos.planet],
            )
            for i, pos in enumerate(ordered)
        )
        return CharaKarakaResult(scheme=scheme, karakas=karakas)

    @staticmethod
    def _rank(
        candidates: list[SiderealPosition],
    ) -> tuple[list[SiderealPosition], dict[str, Optional[str]]]:
        """
        Sort candidates by karaka_degree descending, applying the tie-break
        chain (speed, then natural-benefic hierarchy) wherever two or more
        karaka_degree values land on the same arc-second grid cell.

        A single 3-key sort — rather than iteratively re-resolving pairs —
        because Python's sort is stable and total-order comparison on
        tuples correctly handles arbitrarily long tie chains (3+ planets
        sharing a degree) in one pass.

        Returns (ordered_positions, tiebreak_rule_used_per_planet).
        """

        def sort_key(pos: SiderealPosition) -> tuple[int, float, int]:
            degree = _karaka_degree(pos.planet, pos.rashi_degree)
            return (
                -_arcsec_grid(degree),  # 1. degree, descending
                -abs(pos.speed_deg_per_day),  # 2. speed, descending
                _NATURAL_BENEFIC_RANK.get(pos.planet, 99),  # 3. benefic hierarchy
            )

        ordered = sorted(candidates, key=sort_key)

        # Provenance for the evidence panel: for each adjacent pair that
        # actually landed on the same degree grid cell, record which rule
        # separated them. Doesn't affect ordering, purely explanatory.
        tiebreak_rule: dict[str, Optional[str]] = {p.planet: None for p in ordered}
        for i in range(1, len(ordered)):
            prev, cur = ordered[i - 1], ordered[i]
            prev_grid = _arcsec_grid(_karaka_degree(prev.planet, prev.rashi_degree))
            cur_grid = _arcsec_grid(_karaka_degree(cur.planet, cur.rashi_degree))
            if prev_grid != cur_grid:
                continue  # no tie between this adjacent pair
            rule = (
                "speed"
                if abs(prev.speed_deg_per_day) != abs(cur.speed_deg_per_day)
                else "natural_benefic"
            )
            tiebreak_rule[prev.planet] = rule
            tiebreak_rule[cur.planet] = rule

        return ordered, tiebreak_rule

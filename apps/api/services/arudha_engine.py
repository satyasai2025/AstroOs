"""
AstroOS — Arudha Pada Engine (Layer 6: Calculation Engine)

Stateless service computing all 12 Arudha Padas (A1..A12) from an
already-built D1Chart, using WHOLE-SIGN houses counted from the Lagna —
the house system every Jaimini technique (Arudha, Argala, Rashi Drishti)
universally uses. No ephemeris/DB dependency — same scope discipline as
CharaKarakaEngine/YogaEngine.

Formula (BPHS / Jaimini Upadesa Sutras): for house N,
  1. Find the lord of the sign occupying house N.
  2. Count (inclusive) from house N's sign to the lord's occupied sign —
     call this count D (1-12).
  3. Count the SAME distance D again, starting from the lord's sign.
     The sign arrived at is the raw Arudha Pada.
  Equivalently: raw_AP_index = 2 * lord_sign_index - house_sign_index (mod 12).

Exception (the "falls on itself / 7th from itself" shift): if the raw
Arudha Pada lands in house N's own sign, or in the 7th sign from it, the
Pada is shifted to the 10th sign counted (inclusively) from the raw
position — i.e. +9 signs. This is the standard, universally-cited
version of the exception (matching Jagannatha Hora / Parashara's Light's
default behavior): without it, the Arudha would sit on top of or exactly
opposite its own house, which classical commentary treats as an invalid,
self-cancelling result.

Upapada Lagna (UL) is not a separate formula — it is, by definition, the
Arudha Pada of the 12th house (A12). Arudha Lagna (AL) is A1.

Uses the traditional (Parashari) sign-lord table,
packages.shared.constants.SIGN_LORDS — deliberately NOT
packages.shared.constants.JAIMINI_ALT_LORDS. The alternate Rahu/Ketu
lordship of Aquarius/Scorpio is a real, documented Jaimini convention,
but it is specific to Jaimini's Dasha systems (Chara/Narayana Dasha —
see dasha_engine.py), not to Arudha Pada computation, where every major
reference (BPHS, Jagannatha Hora, Parashara's Light) uses standard
planetary rulership.
"""

from __future__ import annotations

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import ArudhaPada, ArudhaResult
from apps.api.services.jaimini_shared import (
    house_count,
    rashi_at,
    rashi_index,
    signs_from,
    whole_sign_house_rashi,
)
from packages.shared.constants import SIGN_LORDS

_PADA_NAMES: tuple[str, ...] = tuple(f"A{n}" for n in range(1, 13))


class ArudhaEngine:
    """Stateless Arudha Pada calculator — operates purely on an
    already-computed D1Chart, no ephemeris/DB dependency."""

    def compute(self, chart: D1Chart) -> ArudhaResult:
        padas = tuple(self._compute_one(chart, house_number) for house_number in range(1, 13))
        return ArudhaResult(padas=padas)

    @staticmethod
    def _compute_one(chart: D1Chart, house_number: int) -> ArudhaPada:
        house_rashi = whole_sign_house_rashi(chart, house_number)
        lord = SIGN_LORDS[house_rashi]

        lord_positions = [p for p in chart.planets if p.planet == lord]
        if not lord_positions:
            raise ValueError(
                f"Chart is missing position data for {lord!r}, lord of house {house_number}."
            )
        lord_rashi = lord_positions[0].rashi

        distance = house_count(house_rashi, lord_rashi)  # 1-12, inclusive
        raw_rashi = signs_from(lord_rashi, distance - 1)

        house_idx = rashi_index(house_rashi)
        seventh_from_house = rashi_at(house_idx + 6)
        exception_applies = raw_rashi in (house_rashi, seventh_from_house)

        final_rashi = signs_from(raw_rashi, 9) if exception_applies else raw_rashi

        return ArudhaPada(
            house_number=house_number,
            pada_name=_PADA_NAMES[house_number - 1],
            rashi=final_rashi,
            raw_rashi=raw_rashi,
            lord=lord,
            lord_rashi=lord_rashi,
            exception_applied=exception_applies,
        )

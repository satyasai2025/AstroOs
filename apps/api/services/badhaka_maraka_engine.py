"""
AstroOS — Badhaka & Maraka House Engine

Classical "obstruction" and "death-inflicting" house analysis, computed
on WHOLE-SIGN houses counted from the Lagna — deliberately independent
of whatever house_system (Placidus, etc.) the chart itself was
requested with, same reasoning as yoga house-placement discussed
earlier in this project: Badhaka/Maraka sthana are a sign-counting
rule (BPHS), not a bhava-cusp rule, so mixing in Placidus cusps here
would silently reintroduce the same house-system ambiguity already
resolved for yogas.

Badhaka Sthana (BPHS Ch. 44-ish, standard across Parashari texts):
  - Chara (movable) Lagna  (Aries/Cancer/Libra/Capricorn)   -> 11th house
  - Sthira (fixed) Lagna   (Taurus/Leo/Scorpio/Aquarius)    -> 9th house
  - Dwiswabhava (dual) Lagna (Gemini/Virgo/Sagittarius/Pisces) -> 7th house
Badhaka lord = the ruler of that house's sign.

Maraka Sthana: the 2nd and 7th houses from Lagna (the two classical
"killer" houses) and their lords. Extended per common practice (and
cross-verified against PyJHora's jhora.horoscope.chart.house.marakas()):
any graha occupying the 2nd/7th house, OR occupying the same sign as
the 2nd/7th lord, also qualifies as a maraka graha — not just the two
house lords themselves.

Not present in PyJHora as a Badhaka function (checked — no `badhaka`
anywhere in that codebase), but the Chara/Sthira/Dwiswabhava -> 11/9/7
mapping is standard, uncontested BPHS material, not something that
needs a reference-implementation cross-check the way an Ahargana
epoch table or a Hora-lord formula does.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.domain.horoscope import D1Chart
from packages.shared.constants import SIGN_LORDS

_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_CHARA_SIGNS = {"aries", "cancer", "libra", "capricorn"}
_STHIRA_SIGNS = {"taurus", "leo", "scorpio", "aquarius"}
_DWISWABHAVA_SIGNS = {"gemini", "virgo", "sagittarius", "pisces"}


@dataclass(frozen=True)
class BadhakaMarakaResult:
    badhaka_house: int
    badhaka_sign: str
    badhaka_lord: str
    maraka_houses: tuple[int, int]
    maraka_signs: tuple[str, str]
    maraka_lords: tuple[str, ...]
    """2nd/7th lords plus any graha occupying those houses or their lords' sign — deduplicated."""


class BadhakaMarakaEngine:
    """Stateless — needs only an already-built D1Chart."""

    def _sign_at_house(self, asc_index: int, house_number: int) -> str:
        return _RASHI_ORDER[(asc_index + house_number - 1) % 12]

    def compute(self, chart: D1Chart) -> BadhakaMarakaResult:
        asc_rashi = chart.ascendant.rashi
        asc_index = _RASHI_ORDER.index(asc_rashi)

        if asc_rashi in _CHARA_SIGNS:
            badhaka_house = 11
        elif asc_rashi in _STHIRA_SIGNS:
            badhaka_house = 9
        else:
            badhaka_house = 7
        badhaka_sign = self._sign_at_house(asc_index, badhaka_house)
        badhaka_lord = SIGN_LORDS[badhaka_sign]

        second_sign = self._sign_at_house(asc_index, 2)
        seventh_sign = self._sign_at_house(asc_index, 7)
        second_lord = SIGN_LORDS[second_sign]
        seventh_lord = SIGN_LORDS[seventh_sign]

        maraka_lords: list[str] = [second_lord, seventh_lord]

        # Grahas occupying the 2nd/7th house, or conjunct the 2nd/7th
        # lord (occupying the same sign that lord is in), also qualify
        # as maraka grahas — matches PyJHora's marakas()/
        # marakas_from_planet_positions() extension beyond just the two
        # house lords themselves.
        lord_positions = {pl.planet: pl.rashi for pl in chart.planets}
        for p in chart.planets:
            if p.planet in ("rahu", "ketu") or p.planet in maraka_lords:
                continue
            occupies_maraka_house = p.rashi in (second_sign, seventh_sign)
            occupies_lord_sign = p.rashi in (
                lord_positions.get(second_lord), lord_positions.get(seventh_lord),
            )
            if occupies_maraka_house or occupies_lord_sign:
                maraka_lords.append(p.planet)

        return BadhakaMarakaResult(
            badhaka_house=badhaka_house,
            badhaka_sign=badhaka_sign,
            badhaka_lord=badhaka_lord,
            maraka_houses=(2, 7),
            maraka_signs=(second_sign, seventh_sign),
            maraka_lords=tuple(dict.fromkeys(maraka_lords)),
        )

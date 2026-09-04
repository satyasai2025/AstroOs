"""
AstroOS — Ojayugmarasyamsa Bala (SHADBALA-OJAYUGMA)

Sthana Bala's last sub-component. Graded by odd (oja) vs even (yugma)
sign placement in BOTH the D1 rashi and the D9 navamsha rashi, split
into two equal halves (15 Shashtiamsas each, 30 max):

    Male planets   (odd-sign favoring)  — full 15 per chart where sign is odd
    Female planets (even-sign favoring) — full 15 per chart where sign is even
    Mercury (neuter) — full 15 in both charts unconditionally

**A genuine classification difference from Drekkana Bala, documented
deliberately, not a copy-paste inconsistency.** Drekkana Bala classifies
Saturn as "neuter" (favoring the 3rd decanate). The commonly-cited
grouping for THIS component instead treats Saturn as "male" (odd-sign
favoring), grouped with Sun/Mars/Jupiter. Different classical Shadbala
sub-components legitimately use different traditional classifications
for the same planet — conflating them (reusing Drekkana's grouping here
"for consistency") would itself be the error. This is called out
explicitly since it's easy to assume gender classification should be a
single fixed table shared across every component, and it isn't.

**Explicitly an approximated point scale** — same honesty treatment as
every other non-trivial Shadbala component in this codebase. The 15/15
split and the male/female/neuter groupings are commonly cited but not
independently verified against a single primary source.

Same "needs more than the chart" dependency shape as Saptavargaja Bala
— needs a DivisionalEngine to compute D9.
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.divisional_engine import DivisionalEngine
from packages.shared.enums import Rashi

_COMPONENT_ID = "SHADBALA-OJAYUGMA"
_COMPONENT_NAME = "Ojayugmarasyamsa Bala"
_RULE_VERSION = "1.0"

_HALF_VALUE = 15.0

# Deliberately DIFFERENT from Drekkana Bala's grouping — see module docstring.
_MALE_PLANETS = {"sun", "mars", "jupiter", "saturn"}
_FEMALE_PLANETS = {"moon", "venus"}
# mercury: neuter, always scores full marks regardless of sign parity

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

_RASHI_LIST = [r.value for r in Rashi]


def _is_odd_sign(rashi: str) -> bool:
    """Aries=1st sign (odd), Taurus=2nd (even), etc. — classical 1-indexed odd/even."""
    return (_RASHI_LIST.index(rashi) + 1) % 2 == 1


def _score_for_chart(planet: str, rashi: str) -> tuple[float, str]:
    if planet == "mercury":
        return _HALF_VALUE, f"mercury (neuter) always scores full marks in {rashi}"

    is_odd = _is_odd_sign(rashi)
    if planet in _MALE_PLANETS:
        matched = is_odd
        rule = "male (odd-sign favoring)"
    else:  # _FEMALE_PLANETS
        matched = not is_odd
        rule = "female (even-sign favoring)"

    value = _HALF_VALUE if matched else 0.0
    parity = "odd" if is_odd else "even"
    return value, f"{planet} is {rule}, {rashi} is {parity} → {'match' if matched else 'no match'}"


class OjayugmarasyamsaBalaCalculator:
    """Needs a DivisionalEngine (to compute D9) — same dependency shape as Saptavargaja Bala."""

    def __init__(self, divisional_engine: DivisionalEngine) -> None:
        self._divisional_engine = divisional_engine

    def calculate(
        self,
        planet: str,
        d1_chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> BalaComponentResult:
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Ojayugmarasyamsa Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        trace: list[str] = []
        total = 0.0

        d1_position = next((p for p in d1_chart.planets if p.planet == planet), None)
        if d1_position is None:
            trace.append("D1: planet not found in chart — skipped")
        else:
            d1_value, d1_explanation = _score_for_chart(planet, d1_position.rashi)
            total += d1_value
            trace.append(f"D1: {d1_explanation} → {d1_value} points")

        d9_chart = self._divisional_engine.compute(
            birth_datetime_utc=birth_datetime_utc, latitude=latitude,
            longitude=longitude, varga="D9", ayanamsa=ayanamsa, house_system=house_system,
        )
        d9_position = next((p for p in d9_chart.planet_positions if p.planet == planet), None)
        if d9_position is None:
            trace.append("D9: planet not found in chart — skipped")
        else:
            d9_value, d9_explanation = _score_for_chart(planet, d9_position.varga_rashi)
            total += d9_value
            trace.append(f"D9: {d9_explanation} → {d9_value} points")

        trace.append(f"Final: D1 + D9 = {total:.4f} Shashtiamsas")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(total, 4), trace=tuple(trace),
        )

    def calculate_all(
        self,
        d1_chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> list[BalaComponentResult]:
        return [
            self.calculate(
                planet, d1_chart, birth_datetime_utc=birth_datetime_utc,
                latitude=latitude, longitude=longitude, ayanamsa=ayanamsa,
                house_system=house_system,
            )
            for planet in _CLASSICAL_SEVEN
        ]

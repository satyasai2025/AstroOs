"""
AstroOS — Tribhaga Bala (SHADBALA-TRIBHAGA)

Kala Bala's three-part day/night division sub-component. Day (sunrise
to sunset) and night (sunset to next sunrise) are each split into three
equal parts (6 "tribhaga" periods total), each with a fixed classical
lord:

    Day tribhaga 1   → Mercury
    Day tribhaga 2   → Sun
    Day tribhaga 3   → Saturn
    Night tribhaga 1 → Moon
    Night tribhaga 2 → Venus
    Night tribhaga 3 → Mars

Jupiter is never a tribhaga lord in this classical scheme — it always
scores 0 here, which is a real, deliberate feature of the rule, not a
gap.

**Explicitly an approximated scale, lord sequence commonly-cited but not
independently verified against a primary source** — same honesty
treatment as Drik/Chesta/Saptavargaja Bala. Full strength is taken as 60
Shashtiamsas (matching this codebase's other components' scale); some
classical sources may use a different individual maximum for this
specific sub-component.

Needs an EphemerisWrapper (to find the FOLLOWING sunrise, closing out
the night period) in addition to the birth chart's own sunrise/sunset —
a similar "needs more than just the chart" dependency shape as
Saptavargaja Bala.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_COMPONENT_ID = "SHADBALA-TRIBHAGA"
_COMPONENT_NAME = "Tribhaga Bala"
_RULE_VERSION = "1.0"

_MAX_VALUE = 60.0

_DAY_LORDS = ["mercury", "sun", "saturn"]
_NIGHT_LORDS = ["moon", "venus", "mars"]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class TribhagaBalaCalculator:
    """Needs an EphemerisWrapper (to find the following sunrise) plus the EphemerisResult."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def calculate(
        self,
        position: SiderealPosition,
        ephemeris_result: EphemerisResult,
        *,
        latitude: float,
        longitude: float,
    ) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Tribhaga Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        trace: list[str] = []
        sunrise = ephemeris_result.sunrise_jd
        sunset = ephemeris_result.sunset_jd
        birth_jd = ephemeris_result.julian_day

        if sunrise is None or sunset is None:
            trace.append("sunrise/sunset not computable at this latitude — skipping")
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=0.0, trace=tuple(trace),
            )

        is_day = ephemeris_result.is_daytime_birth
        trace.append(f"Step 1: sunrise={sunrise:.6f}, sunset={sunset:.6f}, is_daytime_birth={is_day}")

        if is_day:
            day_length = sunset - sunrise
            tribhaga_width = day_length / 3.0
            index = int((birth_jd - sunrise) / tribhaga_width)
            index = min(max(index, 0), 2)
            lord = _DAY_LORDS[index]
            trace.append(
                f"Step 2: daytime — day_length={day_length:.6f}, tribhaga {index + 1} of 3, lord={lord}"
            )
        else:
            # Night runs from this sunset to the FOLLOWING sunrise — search
            # starting well past this sunset, since get_sunrise_sunset()
            # always searches from (jd - 1.0) internally and naively
            # re-calling it with jd=sunset would just re-find the same
            # morning's sunrise that already happened.
            next_sunrise, _ = self._wrapper.get_sunrise_sunset(sunset + 0.5, latitude, longitude)
            if next_sunrise is None:
                trace.append("following sunrise not computable at this latitude — skipping")
                return BalaComponentResult(
                    component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                    rule_version=_RULE_VERSION, planet=planet,
                    value_shashtiamsas=0.0, trace=tuple(trace),
                )
            night_length = next_sunrise - sunset
            tribhaga_width = night_length / 3.0
            index = int((birth_jd - sunset) / tribhaga_width)
            index = min(max(index, 0), 2)
            lord = _NIGHT_LORDS[index]
            trace.append(
                f"Step 2: nighttime — next_sunrise={next_sunrise:.6f}, "
                f"night_length={night_length:.6f}, tribhaga {index + 1} of 3, lord={lord}"
            )

        is_match = planet == lord
        value = _MAX_VALUE if is_match else 0.0
        trace.append(f"Step 3: {planet} {'is' if is_match else 'is not'} this period's lord → {value}")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=value, trace=tuple(trace),
        )

    def calculate_all(
        self,
        planets: list[SiderealPosition],
        ephemeris_result: EphemerisResult,
        *,
        latitude: float,
        longitude: float,
    ) -> list[BalaComponentResult]:
        return [
            self.calculate(p, ephemeris_result, latitude=latitude, longitude=longitude)
            for p in planets if p.planet in _CLASSICAL_SEVEN
        ]

"""
AstroOS — Nathonnata Bala (SHADBALA-NATHONNATA)

Kala Bala's 4th sub-component. Graded by proximity to local noon vs
local midnight:

    Diurnal-favoring (more bala near local noon):     Sun, Jupiter, Venus
    Nocturnal-favoring (more bala near local midnight): Moon, Mars, Saturn
    Mercury: always scores full marks regardless of time of day

**Explicitly an approximated formula, not verified classical fidelity —
same honesty treatment as every other non-trivial Kala Bala/Sthana Bala
component.** Classical Nathonnata Bala's exact falloff shape (this uses
a linear scaling, some sources describe a different curve) and the
precise diurnal/nocturnal grouping vary somewhat across sources.

Local noon and local midnight are computed as the midpoints of the day
period (sunrise to sunset) and night period (sunset to the FOLLOWING
sunrise) respectively — same "needs the following sunrise" mechanism
already built and tested for Tribhaga Bala, including the same care
around not naively re-searching from the wrong starting point.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_COMPONENT_ID = "SHADBALA-NATHONNATA"
_COMPONENT_NAME = "Nathonnata Bala"
_RULE_VERSION = "1.0"

_MAX_VALUE = 60.0

_DIURNAL_FAVORING = {"sun", "jupiter", "venus"}
_NOCTURNAL_FAVORING = {"moon", "mars", "saturn"}
# mercury: always full marks, regardless of time of day

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class NathonnataBalaCalculator:
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
                f"Nathonnata Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        trace: list[str] = []

        if planet == "mercury":
            trace.append("mercury always scores full marks regardless of time of day")
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=_MAX_VALUE, trace=tuple(trace),
            )

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

        # Following sunrise closes out the night period, same mechanism
        # as Tribhaga Bala: search starting well past this sunset, since
        # get_sunrise_sunset() always searches from (jd - 1.0) internally
        # and naively re-calling it with jd=sunset would just re-find the
        # same morning's sunrise that already happened.
        next_sunrise, _ = self._wrapper.get_sunrise_sunset(sunset + 0.5, latitude, longitude)
        if next_sunrise is None:
            trace.append("following sunrise not computable at this latitude — skipping")
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=0.0, trace=tuple(trace),
            )

        local_noon = (sunrise + sunset) / 2.0
        local_midnight = (sunset + next_sunrise) / 2.0
        half_cycle = (next_sunrise - sunrise) / 2.0  # distance from noon to midnight

        trace.append(
            f"Step 1: local_noon={local_noon:.6f}, local_midnight={local_midnight:.6f}, "
            f"half_cycle={half_cycle:.6f}"
        )

        is_diurnal = planet in _DIURNAL_FAVORING
        reference_point = local_noon if is_diurnal else local_midnight
        distance = min(abs(birth_jd - reference_point), half_cycle)
        normalized = distance / half_cycle if half_cycle > 0 else 0.0
        value = _MAX_VALUE * (1.0 - normalized)
        value = max(0.0, min(_MAX_VALUE, value))

        trace.append(
            f"Step 2: {planet} is {'diurnal' if is_diurnal else 'nocturnal'}-favoring, "
            f"distance to reference = {distance:.6f}, normalized = {normalized:.4f}"
        )
        trace.append(f"Step 3: value = 60 * (1 - {normalized:.4f}) = {value:.4f} Shashtiamsas")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=tuple(trace),
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

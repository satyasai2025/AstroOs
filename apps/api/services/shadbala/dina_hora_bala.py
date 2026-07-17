"""
AstroOS — Dina-Hora Bala (SHADBALA-DINA-HORA)

Kala Bala's 5th sub-component is classically "Varsha-Masa-Dina-Hora
Bala" — four lordships (year, month, day, hour). **Only Dina (day/
weekday) and Hora (planetary hour) lordship are implemented here.**

Varsha (year) and Masa (month) lordship are NOT a coefficient-precision
question like every other approximated component in this codebase —
they need genuinely new capability this pass doesn't have: Varsha lord
requires finding the weekday of the most recent Mesha Sankranti (Sun's
sidereal ingress into Aries) before birth, and Masa lord needs an
equivalent lunar-month boundary search, both requiring backward
astronomical event-searching that isn't built, plus real definitional
variance across traditions on which reference event to use. This is a
scope gap, not a caveat — tracked explicitly as its own deferral,
separate from Dina-Hora's own approximation caveat below.

Named `SHADBALA-DINA-HORA`, not `SHADBALA-VARSHA-MASA-DINA-HORA`,
specifically so this partial coverage is never mistaken for the full
classical component in code, logs, or results.

  Dina (day) lord — the weekday's own ruling planet (already available
    from Panchanga; e.g. Sunday -> Sun). Full marks (15 Shashtiamsas) if
    the planet IS today's lord.
  Hora (hour) lord — the planetary hour, cycling through the classical
    Chaldean order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon),
    starting from the day's own Dina lord at hour 1 and continuing
    through all 24 hours (12 day-horas + 12 night-horas). Full marks
    (15 Shashtiamsas) if the planet IS the birth hour's lord.

**Explicitly an approximated point scale for what IS implemented** —
same honesty treatment as every other non-trivial Kala Bala component.
15+15=30 is half of the classical component's usual 60-Shashtiamsa
scale (the other 30 reserved for Varsha+Masa, not computed here) — a
defensible allocation, not independently verified against a primary
source.

Needs an EphemerisWrapper (to find the following sunrise, same
mechanism as Tribhaga/Nathonnata Bala) plus the EphemerisResult.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_COMPONENT_ID = "SHADBALA-DINA-HORA"
_COMPONENT_NAME = "Dina-Hora Bala"
_RULE_VERSION = "1.0"

_DINA_VALUE = 15.0
_HORA_VALUE = 15.0

# Classical Chaldean order, used for planetary-hour sequencing.
_CHALDEAN_ORDER = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class DinaHoraBalaCalculator:
    """Needs an EphemerisWrapper (to find the following sunrise) plus the EphemerisResult."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def _hora_lord(
        self, ephemeris_result: EphemerisResult, *, latitude: float, longitude: float,
    ):
        """Returns (hora_lord_or_None, trace_lines)."""
        trace: list[str] = []
        sunrise = ephemeris_result.sunrise_jd
        sunset = ephemeris_result.sunset_jd
        birth_jd = ephemeris_result.julian_day
        dina_lord = ephemeris_result.panchanga.vara.lord

        if sunrise is None or sunset is None:
            trace.append("sunrise/sunset not computable at this latitude — hora lord skipped")
            return None, trace

        start_index = _CHALDEAN_ORDER.index(dina_lord)
        trace.append(f"Step: dina lord ({dina_lord}) is Chaldean-order index {start_index}")

        if ephemeris_result.is_daytime_birth:
            day_length = sunset - sunrise
            hora_width = day_length / 12.0
            hora_number = int((birth_jd - sunrise) / hora_width)  # 0-indexed, 0-11
            hora_number = min(max(hora_number, 0), 11)
            trace.append(f"Step: daytime, hora {hora_number + 1} of 24 (day horas 1-12)")
        else:
            next_sunrise, _ = self._wrapper.get_sunrise_sunset(sunset + 0.5, latitude, longitude)
            if next_sunrise is None:
                trace.append("following sunrise not computable at this latitude — hora lord skipped")
                return None, trace
            night_length = next_sunrise - sunset
            hora_width = night_length / 12.0
            night_hora_number = int((birth_jd - sunset) / hora_width)  # 0-indexed, 0-11
            night_hora_number = min(max(night_hora_number, 0), 11)
            hora_number = 12 + night_hora_number  # continues the day's 24-hora cycle
            trace.append(f"Step: nighttime, hora {hora_number + 1} of 24 (night horas 13-24)")

        lord = _CHALDEAN_ORDER[(start_index + hora_number) % 7]
        trace.append(f"Step: hora lord -> {lord}")
        return lord, trace

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
                f"Dina-Hora Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        trace: list[str] = []
        total = 0.0

        dina_lord = ephemeris_result.panchanga.vara.lord
        is_dina_lord = planet == dina_lord
        if is_dina_lord:
            total += _DINA_VALUE
        trace.append(
            f"Dina: today's weekday lord is {dina_lord} -> "
            f"{'match' if is_dina_lord else 'no match'} ({_DINA_VALUE if is_dina_lord else 0.0} points)"
        )

        hora_lord, hora_trace = self._hora_lord(ephemeris_result, latitude=latitude, longitude=longitude)
        trace.extend(hora_trace)
        if hora_lord is not None:
            is_hora_lord = planet == hora_lord
            if is_hora_lord:
                total += _HORA_VALUE
            trace.append(
                f"Hora: this hour's lord is {hora_lord} -> "
                f"{'match' if is_hora_lord else 'no match'} ({_HORA_VALUE if is_hora_lord else 0.0} points)"
            )

        trace.append(
            f"Final: Dina + Hora = {total:.4f} Shashtiamsas "
            "(Varsha/Masa not computed — see module docstring)"
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(total, 4), trace=tuple(trace),
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

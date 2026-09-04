"""
AstroOS — Dina-Hora Bala (SHADBALA-DINA-HORA)

Kala Bala's 5th sub-component is classically "Varsha-Masa-Dina-Hora
Bala" — four lordships (year, month, day, hour). Dina (day/weekday) and
Hora (planetary hour) lordship are implemented here; Varsha (year) and
Masa (month) lordship are implemented separately in
varsha_masa_bala.py, via the classical Ahargana day-count method rather
than a Mesha Sankranti search — see that module's docstring.

Named `SHADBALA-DINA-HORA`, not `SHADBALA-VARSHA-MASA-DINA-HORA`,
since it's still its own tracked component alongside Abda/Masa Bala,
not a merged one — ShadbalaEngine sums all four into the full
classical Varsha-Masa-Dina-Hora Bala.

  Dina (day) lord — the weekday's own ruling planet (already available
    from Panchanga; e.g. Sunday -> Sun). Full marks (45 Shashtiamsas) if
    the planet IS today's lord.
  Hora (hour) lord — the planetary hour, cycling through the classical
    Chaldean order (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon),
    starting from the day's own Dina lord at hour 1 and continuing
    through all 24 hours (12 day-horas + 12 night-horas). Full marks
    (60 Shashtiamsas) if the planet IS the birth hour's lord.

Point scale (Abda 15 / Masa 30 / Dina 45 / Hora 60) cross-verified
against PyJHora's jhora.horoscope.chart.strength module and a real
JHora.exe Shadbala printout for the same birth chart — this was
previously 15/15 for Dina/Hora (an unverified assumption from before
Abda/Masa existed), corrected to match the verified reference.

Needs an EphemerisWrapper (to find the following sunrise, same
mechanism as Tribhaga/Nathonnata Bala) plus the EphemerisResult.
"""

from __future__ import annotations

import math
from datetime import timedelta

import swisseph as swe

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, jd_to_datetime

_COMPONENT_ID = "SHADBALA-DINA-HORA"
_COMPONENT_NAME = "Dina-Hora Bala"
_RULE_VERSION = "1.0"

_DINA_VALUE = 45.0
_HORA_VALUE = 60.0

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Hora-index (0-6) -> planet-index (0=Sun..6=Saturn). Cross-verified
# against PyJHora's jhora.horoscope.chart.strength._hora_bala() and
# const.hora_bala_hora_order for 1995-01-01 12:00 UTC, New Delhi
# (Mercury came out as hora lord both places). This REPLACES an earlier
# from-scratch "12 day-horas + 12 night-horas, Chaldean order starting
# from the Dina lord" implementation that produced a different (wrong)
# lord for the same chart — that method wasn't independently verified
# against a reference at the time it was written.
_HORA_ORDER = [6, 4, 2, 0, 5, 3, 1]

# `utc_offset_hours` defaults to IST (+5.5) — this component (like Abda/
# Masa Bala) needs the LOCAL civil clock, not just UTC + coordinates, to
# match PyJHora's own convention (see varsha_masa_bala.py's docstring).
# No timezone field exists yet in the request schemas that call this —
# defaulting to IST is a disclosed limitation matching this codebase's
# existing India-only assumption elsewhere (e.g. birth_chart_report_
# builder.py), not a silent one.
_DEFAULT_UTC_OFFSET_HOURS = 5.5


class DinaHoraBalaCalculator:
    """Needs an EphemerisWrapper (to find the following sunrise) plus the EphemerisResult."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def _hora_lord(
        self,
        ephemeris_result: EphemerisResult,
        *,
        latitude: float,
        longitude: float,
        utc_offset_hours: float,
    ):
        """
        Returns (hora_lord_or_None, trace_lines). Ported from PyJHora's
        _hora_bala(): civil (midnight-to-midnight) weekday of the LOCAL
        civil date, offset by elapsed local hours since local sunrise,
        indexed into a fixed 7-position lord cycle — deliberately NOT
        the same "24 planetary hours in Chaldean order" method used
        elsewhere in astrology software; this is the specific formula
        that matched the verified reference for this component.
        """
        trace: list[str] = []
        sunrise_jd_utc = ephemeris_result.sunrise_jd
        if sunrise_jd_utc is None:
            trace.append("sunrise not computable at this latitude — hora lord skipped")
            return None, trace

        birth_dt_utc = jd_to_datetime(ephemeris_result.julian_day)
        local_dt = birth_dt_utc + timedelta(hours=utc_offset_hours)
        local_hour = local_dt.hour + local_dt.minute / 60.0 + local_dt.second / 3600.0
        jd_local = swe.julday(local_dt.year, local_dt.month, local_dt.day, local_hour)
        day = int(math.ceil(jd_local + 1) % 7)  # 0=Sunday, civil (midnight-based) weekday

        sunrise_local_dt = jd_to_datetime(sunrise_jd_utc) + timedelta(hours=utc_offset_hours)
        sunrise_hour = sunrise_local_dt.hour + sunrise_local_dt.minute / 60.0 + sunrise_local_dt.second / 3600.0
        trace.append(f"Step: civil weekday index {day}, local sunrise at {sunrise_hour:.4f}h, birth at {local_hour:.4f}h")

        tobh = local_hour
        if tobh < sunrise_hour:
            day = (day - 1) % 7
            tobh += 24.0

        hora = (int(tobh - sunrise_hour) + day + 1) % 7
        lord = _CLASSICAL_SEVEN[_HORA_ORDER[hora]]
        trace.append(f"Step: hora index {hora} -> lord = {lord}")
        return lord, trace

    def calculate(
        self,
        position: SiderealPosition,
        ephemeris_result: EphemerisResult,
        *,
        latitude: float,
        longitude: float,
        utc_offset_hours: float = _DEFAULT_UTC_OFFSET_HOURS,
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

        hora_lord, hora_trace = self._hora_lord(
            ephemeris_result, latitude=latitude, longitude=longitude, utc_offset_hours=utc_offset_hours,
        )
        trace.extend(hora_trace)
        if hora_lord is not None:
            is_hora_lord = planet == hora_lord
            if is_hora_lord:
                total += _HORA_VALUE
            trace.append(
                f"Hora: this hour's lord is {hora_lord} -> "
                f"{'match' if is_hora_lord else 'no match'} ({_HORA_VALUE if is_hora_lord else 0.0} points)"
            )

        trace.append(f"Final: Dina + Hora = {total:.4f} Shashtiamsas")

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
        utc_offset_hours: float = _DEFAULT_UTC_OFFSET_HOURS,
    ) -> list[BalaComponentResult]:
        return [
            self.calculate(
                p, ephemeris_result, latitude=latitude, longitude=longitude,
                utc_offset_hours=utc_offset_hours,
            )
            for p in planets if p.planet in _CLASSICAL_SEVEN
        ]

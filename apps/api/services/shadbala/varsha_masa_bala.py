"""
AstroOS — Abda (Varsha) Bala and Masa Bala (SHADBALA-ABDA, SHADBALA-MASA)

The two Kala Bala sub-components that dina_hora_bala.py's module
docstring flagged as a genuine capability gap — "requires finding the
weekday of the most recent Mesha Sankranti... needs genuinely new
astronomical event-searching this codebase doesn't have."

That gap is closed here NOT by searching for Mesha Sankranti directly,
but via the classical Ahargana (elapsed-day-count) method: count days
since a fixed historical epoch, then derive the year/month lord from
that count's position in a repeating weekday cycle. This is the same
method BPHS-derived software (including PyJHora) actually implements —
cross-verified byte-for-byte against PyJHora's
jhora.horoscope.chart.strength._abdadhipathi() /_masadhipathi() for
1995-01-01 12:00 UTC, New Delhi: both produced Mars=15 (Abda) and
Jupiter=30 (Masa), matching this implementation exactly.

Two conventions worth being explicit about, since both are easy to get
subtly wrong:

1. The Ahargana day-count is anchored to LOCAL civil clock time, not
   UTC — PyJHora's own julian_day_number() computes swe.julday() from
   the local hour directly, never converting to UTC first. This
   implementation replicates that: `utc_offset_hours` shifts the birth
   moment to local civil time before the day-count math, matching the
   reference exactly (see the docstring cross-check above).
2. The base epoch (year 1951, day-count 174) comes from "B.V. Raman's
   Bhava and Graha Bala Table - I" per PyJHora's own comment — an
   external historical anchor neither this codebase nor PyJHora's
   authors independently re-derive; both simply use it as the
   established reference point for the classical 7-planet Vaara cycle.
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_ABDA_COMPONENT_ID = "SHADBALA-ABDA"
_ABDA_COMPONENT_NAME = "Abda (Varsha) Bala"
_MASA_COMPONENT_ID = "SHADBALA-MASA"
_MASA_COMPONENT_NAME = "Masa Bala"
_RULE_VERSION = "1.0"

_ABDA_VALUE = 15.0
_MASA_VALUE = 30.0

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Day-index (0-6) -> planet-index (0=Sun..6=Saturn) for the Ahargana
# weekday cycle. Index 0 corresponds to Tuesday, matching PyJHora's
# const.abdahipathi_weekdays (its own comment: "Starts from Tuesday").
_WEEKDAY_CYCLE_PLANET_INDEX = [2, 3, 4, 5, 6, 0, 1]

_BASE_YEAR = 1951
_BASE_DAYS = 174


def _is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _days_elapsed_since_base(year: int) -> int:
    total_years = year - _BASE_YEAR
    leap_years = sum(1 for y in range(_BASE_YEAR + 1, year + 1) if _is_leap_year(y))
    non_leap_years = total_years - leap_years
    return _BASE_DAYS + leap_years * 366 + non_leap_years * 365


def _ahargana(birth_datetime_utc: datetime, utc_offset_hours: float) -> int:
    from datetime import timedelta
    local_dt = birth_datetime_utc + timedelta(hours=utc_offset_hours)
    local_hour = local_dt.hour + local_dt.minute / 60.0 + local_dt.second / 3600.0
    local_jd = swe.julday(local_dt.year, local_dt.month, local_dt.day, local_hour)
    jan1_jd = swe.julday(local_dt.year, 1, 1, 0.0)
    elapsed_days_in_year = int(local_jd - jan1_jd + 1)
    return _days_elapsed_since_base(local_dt.year - 1) + elapsed_days_in_year


class AbdaBalaCalculator:
    """Stateless — needs only the birth moment and the birth place's UTC offset."""

    def calculate_all(
        self,
        planets: list[SiderealPosition],
        *,
        birth_datetime_utc: datetime,
        utc_offset_hours: float,
    ) -> list[BalaComponentResult]:
        ahargana = _ahargana(birth_datetime_utc, utc_offset_hours)
        day_index = (int(ahargana // 360) * 3 + 1) % 7
        lord = _CLASSICAL_SEVEN[_WEEKDAY_CYCLE_PLANET_INDEX[day_index]]

        results = []
        for p in planets:
            if p.planet not in _CLASSICAL_SEVEN:
                continue
            is_lord = p.planet == lord
            trace = (
                f"Ahargana (days since {_BASE_YEAR} epoch) = {ahargana}",
                f"Abda cycle index = {day_index} -> lord = {lord}",
                f"{'Match' if is_lord else 'No match'} ({_ABDA_VALUE if is_lord else 0.0} points)",
            )
            results.append(BalaComponentResult(
                component_id=_ABDA_COMPONENT_ID, component_name=_ABDA_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=p.planet,
                value_shashtiamsas=_ABDA_VALUE if is_lord else 0.0, trace=trace,
            ))
        return results


class MasaBalaCalculator:
    """Stateless — needs only the birth moment and the birth place's UTC offset."""

    def calculate_all(
        self,
        planets: list[SiderealPosition],
        *,
        birth_datetime_utc: datetime,
        utc_offset_hours: float,
    ) -> list[BalaComponentResult]:
        ahargana = _ahargana(birth_datetime_utc, utc_offset_hours)
        day_index = (int(ahargana // 30) * 2 + 1) % 7
        lord = _CLASSICAL_SEVEN[_WEEKDAY_CYCLE_PLANET_INDEX[day_index]]

        results = []
        for p in planets:
            if p.planet not in _CLASSICAL_SEVEN:
                continue
            is_lord = p.planet == lord
            trace = (
                f"Ahargana (days since {_BASE_YEAR} epoch) = {ahargana}",
                f"Masa cycle index = {day_index} -> lord = {lord}",
                f"{'Match' if is_lord else 'No match'} ({_MASA_VALUE if is_lord else 0.0} points)",
            )
            results.append(BalaComponentResult(
                component_id=_MASA_COMPONENT_ID, component_name=_MASA_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=p.planet,
                value_shashtiamsas=_MASA_VALUE if is_lord else 0.0, trace=trace,
            ))
        return results

"""
AstroOS — Calendar Engine (Masa + Samvatsara)

Computes the lunar month (Amanta and Purnimanta reckonings) and the
60-year Jupiter-cycle Samvatsara name (reckoned separately against both
the Shaka and Vikram epochs) for a given date.

Method
------
Amanta masa is named from the sidereal Rashi the Sun occupies at the
Amavasya (New Moon) that begins the lunar month — the classical rule.
Purnimanta masa is the same name during Shukla Paksha; during Krishna
Paksha it is the NEXT Amanta month's name (Purnimanta months run
full-moon to full-moon, so the dark fortnight already belongs to the
next Amanta month).

Samvatsara year-turnover is Chaitra Shukla Pratipada, found by walking
backward one Amavasya at a time (not by a fixed month-count — an
intervening Adhika/leap month would throw off any fixed-count jump)
until the Amavasya whose Sun-Rashi is Meena (i.e. immediately preceding
Chaitra) is found.

Verified against drikpanchang.com for New Delhi, 2026-08-15: Amanta
"Shravana", Purnimanta "Shravana", Shaka Samvat 1948 "Parabhava",
Vikram Samvat 2083 "Siddharthi" — see test_calendar_engine.py.

Does not yet prefix Adhika Masa months with "Adhika" (see domain/calendar.py).

Thread-safety: every sidereal-dependent call here (get_ayanamsa,
get_planet_position, to_sidereal) runs inside wrapper.sidereal_mode(...),
matching the contract documented on that context manager — pyswisseph's
sidereal mode is process-global, so code reading sidereal values outside
wrapper.calculate() must set the mode itself under the wrapper's lock or
silently inherit whatever ayanamsa a concurrent request last left set.
"""

from __future__ import annotations

import swisseph as swe

from apps.api.domain.calendar import CalendarResult, MasaInfo, SamvatsaraInfo
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.enums import AyanamsaSystem

_MASA_NAMES: list[str] = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwin", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]

# 60-year Jupiter cycle, Prabhava (index 0) … Kshaya (index 59).
_SAMVATSARA_NAMES: list[str] = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa",
    "Shrimukha", "Bhava", "Yuva", "Dhata", "Ishvara", "Bahudhanya",
    "Pramathi", "Vikrama", "Vrisha", "Chitrabhanu", "Svabhanu", "Tarana",
    "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti",
    "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit",
    "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka",
    "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadi", "Ananda",
    "Rakshasa", "Nala", "Pingala", "Kalayukta", "Siddharthi", "Raudra",
    "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Kshaya",
]

# Calibrated against the single verified data point above (New Delhi,
# 2026-08-15: Shaka 1948 -> Parabhava, Vikram 2083 -> Siddharthi). Since
# the cycle is a fixed-offset affine relation modulo 60, one correct point
# fully determines each constant.
_SHAKA_SAMVATSARA_OFFSET = 11
_VIKRAM_SAMVATSARA_OFFSET = 9

_AMAVASYA_SEARCH_STEP_DAYS = 0.05


class CalendarEngine:
    """Computes Masa and Samvatsara for a given date."""

    def __init__(self, wrapper: EphemerisWrapper):
        self._wrapper = wrapper

    def calculate(self, jd: float, ayanamsa: str = AyanamsaSystem.LAHIRI.value) -> CalendarResult:
        with self._wrapper.sidereal_mode(ayanamsa):
            amavasya_jd, sun_rashi = self._find_amavasya_before(jd)
            amanta_idx = (sun_rashi + 1) % 12
            amanta_name = _MASA_NAMES[amanta_idx]

            sun_lon, moon_lon = self._sidereal_sun_moon(jd)
            tithi = self._wrapper.get_tithi(moon_lon, sun_lon)
            if tithi.paksha == "krishna":
                purnimanta_name = _MASA_NAMES[(amanta_idx + 1) % 12]
            else:
                purnimanta_name = amanta_name

            chaitra_jd = self._find_chaitra_start(amavasya_jd, sun_rashi)

        chaitra_year = swe.revjul(chaitra_jd, swe.GREG_CAL)[0]

        shaka_year = chaitra_year - 78
        vikram_year = chaitra_year + 57

        shaka_samvatsara = _SAMVATSARA_NAMES[(shaka_year + _SHAKA_SAMVATSARA_OFFSET) % 60]
        vikram_samvatsara = _SAMVATSARA_NAMES[(vikram_year + _VIKRAM_SAMVATSARA_OFFSET) % 60]

        return CalendarResult(
            masa=MasaInfo(amanta=amanta_name, purnimanta=purnimanta_name),
            samvatsara=SamvatsaraInfo(
                shaka_year=shaka_year, shaka_samvatsara=shaka_samvatsara,
                vikram_year=vikram_year, vikram_samvatsara=vikram_samvatsara,
            ),
        )

    def _sidereal_sun_moon(self, jd: float) -> tuple[float, float]:
        ayanamsa = self._wrapper.get_ayanamsa(jd)
        sun = self._wrapper.get_planet_position("sun", jd)
        moon = self._wrapper.get_planet_position("moon", jd)
        return (
            self._wrapper.to_sidereal(sun.longitude, ayanamsa),
            self._wrapper.to_sidereal(moon.longitude, ayanamsa),
        )

    def _find_amavasya_before(self, jd: float) -> tuple[float, int]:
        """
        Walk backward to the most recent Amavasya (New Moon) at or before
        `jd`. Returns (amavasya_jd, sun_sidereal_rashi_index) — the Rashi
        the Sun occupies at that instant, which names the Amanta month.
        """
        step = _AMAVASYA_SEARCH_STEP_DAYS
        cur = jd
        prev_diff = None
        for _ in range(4000):
            sun_lon, moon_lon = self._sidereal_sun_moon(cur)
            diff = (moon_lon - sun_lon) % 360.0
            if prev_diff is not None and prev_diff < 5.0 and diff > 355.0:
                amavasya_jd = cur + step / 2.0
                sun_lon_av, _ = self._sidereal_sun_moon(amavasya_jd)
                return amavasya_jd, int(sun_lon_av // 30)
            prev_diff = diff
            cur -= step
        raise RuntimeError("Amavasya search exceeded bounds")

    def _find_chaitra_start(self, amavasya_jd: float, sun_rashi: int) -> float:
        """
        Walk backward one Amavasya at a time (not a fixed month-count —
        an Adhika/leap month in between would throw off any fixed jump)
        until the Amavasya whose Sun-Rashi is Meena (11) — Chaitra's own
        starting Amavasya.
        """
        cur_jd, cur_rashi = amavasya_jd, sun_rashi
        for _ in range(15):
            if cur_rashi == 11:
                return cur_jd
            cur_jd, cur_rashi = self._find_amavasya_before(cur_jd - 20.0)
        raise RuntimeError("Chaitra Amavasya search exceeded bounds")

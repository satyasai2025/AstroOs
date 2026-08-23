"""
AstroOS — Upagraha & Special Lagna Engine

Computes Gulika/Maandi and the Bhava/Hora/Ghati lagnas. Performs no
ephemeris work of its own beyond asking EphemerisWrapper for sunrise,
sunset and the ascendant at a given instant — all sidereal conversion
stays in the wrapper, same discipline as the other engines.

SCOPE — only 2 of the 8 classical Upagrahas are implemented: Gulika and
Maandi (the sunrise/sunset-eighth-part shadow points), plus the three
Special Lagnas. Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, and
Kaala (the Sun-longitude-derived Upagrahas) are NOT implemented anywhere
in AstroOS — this is a real, disclosed feature gap, not a bug in what
exists.

──────────────────────────────────────────────────────────────────────────
SUNRISE DEFINITION — deliberate, and it matters

These points are *entirely* defined by the sunrise/sunset frame, so the
rise/set convention is not cosmetic. Swiss Ephemeris defaults to the
upper limb with atmospheric refraction (what an observer sees). Classical
Vedic computation uses the **centre of the disc with no refraction**, and
so does Classical Vedic System.

On the benchmark chart the two differ by ~4 minutes at each end — enough
to move Gulika by about 1°. Verified against Classical Vedic (30-Jun-1971 04:57:40
IST, Vadodara), using Classical Vedic's own ayanamsa to isolate the method:

    Gulika   −20″      Maandi   −21″
    Bhava L. −53″      Hora L.  −31″      Ghati L. +36″

i.e. sub-arc-minute, the same residual every planet shows against Classical Vedic
(its Lahiri variant differs from SIDM_LAHIRI). With AstroOS's own default
ayanamsa the offset is ~−76″, which is the ayanamsa difference, not a
method error.
──────────────────────────────────────────────────────────────────────────

Gulika / Maandi
    The day (sunrise→sunset) or night (sunset→next sunrise) is divided
    into eight equal parts. Parts 1–7 are ruled by the seven grahas in
    weekday order starting from a weekday-dependent lord; the 8th is
    lordless (Brahma's part).

      day birth   → start from the lord of the weekday itself
      night birth → start from the lord of the 5th weekday onward

    Gulika is the ascendant at the START of Saturn's part; Maandi is the
    ascendant at its MIDPOINT. (Traditions differ — some treat the two as
    one point, some use the end of the part. The start/midpoint pair is
    what Classical Vedic produces and what is implemented here; see
    Settings-free `GULIKA_METHOD` note in the router docs.)

Special Lagnas
    All three progress from the Sun's sidereal longitude at sunrise,
    advancing linearly with time elapsed since sunrise:

      Bhava Lagna  30° per 2 hours   (15°/h)
      Hora Lagna   30° per 1 hour    (30°/h)
      Ghati Lagna  30° per ghati     (75°/h — a ghati is 24 minutes)
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from apps.api.domain.upagraha import (
    SpecialLagna,
    UpagrahaPosition,
    UpagrahaResult,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from packages.shared.rashi_offset import house_offset

# Classical weekday order — also the eighth-part rulership order.
_WEEKDAY_LORDS: tuple[str, ...] = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
)
_WEEKDAY_NAMES: tuple[str, ...] = (
    "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
)

# Centre of disc, no refraction — see the module docstring.
_RISE_FLAGS = swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION

# Degrees advanced per hour elapsed since sunrise.
_SPECIAL_LAGNA_RATES: dict[str, float] = {
    "bhava_lagna": 15.0,   # 30° / 2 h
    "hora_lagna": 30.0,    # 30° / 1 h
    "ghati_lagna": 75.0,   # 30° / ghati (24 min)
}

_RASHI_INDEX_OF_DEGREE = 30.0


class UpagrahaEngine:
    """Stateless — takes an EphemerisWrapper, holds no chart state."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    # ── sunrise/sunset frame ─────────────────────────────────────────────────

    def _rise(self, jd_start: float, lat: float, lon: float, rising: bool) -> float:
        flag = (swe.CALC_RISE if rising else swe.CALC_SET) | _RISE_FLAGS
        ret, data = swe.rise_trans(jd_start, swe.SUN, flag, (lon, lat, 0))
        if ret < 0 or not data:
            raise RuntimeError("Swiss Ephemeris rise/set calculation failed")
        return data[0]

    def _day_frame(
        self, jd: float, lat: float, lon: float
    ) -> tuple[bool, float, float, float]:
        """Return (is_daytime, period_start, period_end, vedic_day_sunrise).

        `vedic_day_sunrise` is the sunrise that began the Vedic day containing
        `jd` — for a pre-dawn birth that is the *previous* calendar day's
        sunrise, which is why such births carry the previous weekday.
        """
        # Search from well before jd so we always find the bracketing events.
        prev_sunrise = self._rise(jd - 1.2, lat, lon, rising=True)
        while True:
            nxt = self._rise(prev_sunrise + 0.01, lat, lon, rising=True)
            if nxt > jd:
                break
            prev_sunrise = nxt
        next_sunrise = self._rise(prev_sunrise + 0.01, lat, lon, rising=True)
        sunset = self._rise(prev_sunrise, lat, lon, rising=False)

        if prev_sunrise <= jd < sunset:
            return True, prev_sunrise, sunset, prev_sunrise
        # Night: from sunset to the next sunrise. The Vedic day is still the
        # one that began at prev_sunrise.
        return False, sunset, next_sunrise, prev_sunrise

    # ── helpers ──────────────────────────────────────────────────────────────

    def _sidereal_ascendant(self, jd: float, lat: float, lon: float, ayanamsa: str) -> float:
        trop, _cusps = self._wrapper.get_ascendant_and_cusps(jd, lat, lon, "W")
        return self._wrapper.to_sidereal(trop, self._wrapper.get_ayanamsa(jd))

    @staticmethod
    def _house_of(lon: float, asc_lon: float) -> int:
        return house_offset(
            int(asc_lon // _RASHI_INDEX_OF_DEGREE),
            int(lon // _RASHI_INDEX_OF_DEGREE),
        )

    def _describe(self, lon: float, asc_lon: float) -> dict:
        rashi, deg = longitude_to_rashi(lon)
        nak = longitude_to_nakshatra(lon)
        return {
            "sidereal_longitude": lon,
            "rashi": rashi,
            "rashi_degree": deg,
            "nakshatra": nak.nakshatra,
            "pada": nak.pada,
            "nakshatra_lord": nak.lord,
            "house_number": self._house_of(lon, asc_lon),
        }

    # ── public API ───────────────────────────────────────────────────────────

    def compute(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> UpagrahaResult:
        # pyswisseph's sidereal mode is process-global; sidereal_mode() takes
        # the wrapper's lock and activates `ayanamsa` for the whole
        # calculation. Without it these points silently inherit whatever
        # ayanamsa the previous caller left set — a constant offset on every
        # value (observed as -0.883 deg, i.e. Fagan-Bradley vs Lahiri, before
        # this was added).
        with self._wrapper.sidereal_mode(ayanamsa):
            return self._compute_locked(
                birth_datetime_utc, latitude, longitude, ayanamsa
            )

    def _compute_locked(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str,
    ) -> UpagrahaResult:
        jd = datetime_to_jd(birth_datetime_utc)
        is_day, start, end, vedic_sunrise = self._day_frame(jd, latitude, longitude)

        asc_lon = self._sidereal_ascendant(jd, latitude, longitude, ayanamsa)

        # Vedic weekday runs sunrise→sunrise. swe.day_of_week returns 0=Monday,
        # so shift to the 0=Sunday convention _WEEKDAY_LORDS uses.
        weekday_idx = (swe.day_of_week(vedic_sunrise) + 1) % 7

        # Eighth-part rulership start: the weekday lord by day, the lord of the
        # 5th weekday onward by night.
        start_idx = weekday_idx if is_day else (weekday_idx + 4) % 7
        part = (end - start) / 8.0

        # Saturn's part, if it falls within the seven ruled parts.
        upagrahas: list[UpagrahaPosition] = []
        saturn_offset = (_WEEKDAY_LORDS.index("saturn") - start_idx) % 7
        saturn_start = start + part * saturn_offset

        for name, moment in (
            ("gulika", saturn_start),
            ("maandi", saturn_start + part / 2.0),
        ):
            lon_ = self._sidereal_ascendant(moment, latitude, longitude, ayanamsa)
            upagrahas.append(UpagrahaPosition(name=name, **self._describe(lon_, asc_lon)))

        # Special lagnas — progressions of the Sun at the Vedic day's sunrise.
        sun_at_sunrise = self._wrapper.to_sidereal(
            self._wrapper.get_planet_position("sun", vedic_sunrise).longitude,
            self._wrapper.get_ayanamsa(vedic_sunrise),
        )
        elapsed_hours = (jd - vedic_sunrise) * 24.0

        special: list[SpecialLagna] = []
        for name, rate in _SPECIAL_LAGNA_RATES.items():
            lon_ = (sun_at_sunrise + elapsed_hours * rate) % 360.0
            special.append(SpecialLagna(name=name, **self._describe(lon_, asc_lon)))

        return UpagrahaResult(
            upagrahas=tuple(upagrahas),
            special_lagnas=tuple(special),
            is_daytime_birth=is_day,
            period_start_jd=start,
            period_end_jd=end,
            part_duration_hours=part * 24.0,
            weekday=_WEEKDAY_NAMES[weekday_idx],
            starting_lord=_WEEKDAY_LORDS[start_idx],
        )

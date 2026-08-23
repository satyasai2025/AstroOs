"""
AstroOS — Muhurta Engine

Computes Hora (planetary hours) and the three classical inauspicious
segments (Rahukalam, Gulikalam, Yamagandam) for a given date + location,
using actual sunrise/sunset (EphemerisWrapper.get_sunrise_sunset) rather
than clock time — this is what makes the result match Drik Panchang.

No business logic lives in the router — everything here.
"""

from __future__ import annotations

import swisseph as swe

from apps.api.domain.muhurta import (
    ChoghadiyaPeriod,
    HoraPeriod,
    InauspiciousPeriod,
    MuhurtaResult,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

# Chaldean order — descending planetary period, used for the Hora sequence.
# The first Hora of a weekday is ruled by that weekday's own lord; every
# subsequent Hora (day and night alike) advances through this same
# repeating 7-cycle.
_CHALDEAN_ORDER: list[str] = [
    "saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon",
]

# Index (0-based) of the 1/8-of-daylight segment used for each inauspicious
# period, keyed by weekday, Sunday=0 … Saturday=6 (matches
# EphemerisWrapper._VARA_LORDS ordering). Standard classical values used by
# Drik Panchang and every mainstream panchang reference.
_RAHUKALAM_SEGMENT = [7, 1, 6, 4, 5, 3, 2]
_GULIKAKALAM_SEGMENT = [6, 5, 4, 3, 2, 1, 0]
_YAMAGANDAM_SEGMENT = [4, 3, 2, 1, 0, 6, 5]

# Choghadiya — fixed 7-name cycle repeated to fill each 8-segment half-day.
# Amrit, Shubh, Labh, Chal are auspicious; Rog, Kaal, Udveg are inauspicious.
_CHOGHADIYA_CYCLE: list[str] = [
    "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog",
]
_CHOGHADIYA_NATURE: dict[str, str] = {
    "Amrit": "auspicious", "Shubh": "auspicious",
    "Labh": "auspicious", "Chal": "auspicious",
    "Rog": "inauspicious", "Kaal": "inauspicious", "Udveg": "inauspicious",
}

# Starting Choghadiya name per weekday, Sunday=0 … Saturday=6.
_DAY_CHOGHADIYA_START = ["Udveg", "Amrit", "Rog", "Labh", "Shubh", "Chal", "Kaal"]
_NIGHT_CHOGHADIYA_START = ["Shubh", "Chal", "Kaal", "Udveg", "Amrit", "Rog", "Labh"]


class MuhurtaEngine:
    """Computes Hora and inauspicious-period timings for a solar day."""

    def __init__(self, wrapper: EphemerisWrapper):
        self._wrapper = wrapper

    def calculate(
        self,
        jd: float,
        latitude: float,
        longitude: float,
    ) -> MuhurtaResult:
        sunrise_jd, sunset_jd = self._wrapper.get_sunrise_sunset(jd, latitude, longitude)
        if sunrise_jd is None or sunset_jd is None:
            raise ValueError(
                "Sunrise/sunset not computable at this latitude/date "
                "(polar day or night)."
            )
        # Search for the next sunrise starting exactly at sunset_jd, not via
        # EphemerisWrapper.get_sunrise_sunset (which looks back a day and
        # would just return today's own sunrise again).
        geopos = (longitude, latitude, 0.0)
        rise_result, rise_data = swe.rise_trans(sunset_jd, swe.SUN, swe.CALC_RISE, geopos)
        if rise_result != 0:
            raise ValueError(
                "Next sunrise not computable at this latitude/date "
                "(polar day or night)."
            )
        next_sunrise_jd = rise_data[0]

        vara = self._wrapper.get_vara(sunrise_jd)
        weekday = vara.number  # 0=Sunday … 6=Saturday

        horas = self._compute_horas(sunrise_jd, sunset_jd, next_sunrise_jd, vara.lord)
        choghadiya = self._compute_choghadiya(sunrise_jd, sunset_jd, next_sunrise_jd, weekday)
        rahukalam = self._compute_segment(
            "rahukalam", sunrise_jd, sunset_jd, _RAHUKALAM_SEGMENT[weekday]
        )
        gulikakalam = self._compute_segment(
            "gulikalam", sunrise_jd, sunset_jd, _GULIKAKALAM_SEGMENT[weekday]
        )
        yamagandam = self._compute_segment(
            "yamagandam", sunrise_jd, sunset_jd, _YAMAGANDAM_SEGMENT[weekday]
        )

        return MuhurtaResult(
            sunrise_jd=sunrise_jd,
            sunset_jd=sunset_jd,
            next_sunrise_jd=next_sunrise_jd,
            horas=horas,
            rahukalam=rahukalam,
            gulikalam=gulikakalam,
            yamagandam=yamagandam,
            choghadiya=choghadiya,
        )

    @staticmethod
    def _compute_segment(
        name: str, sunrise_jd: float, sunset_jd: float, segment_index: int
    ) -> InauspiciousPeriod:
        day_length = sunset_jd - sunrise_jd
        segment_length = day_length / 8.0
        start = sunrise_jd + segment_index * segment_length
        end = start + segment_length
        return InauspiciousPeriod(name=name, start_jd=start, end_jd=end)

    @staticmethod
    def _compute_choghadiya(
        sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, weekday: int
    ) -> list[ChoghadiyaPeriod]:
        day_length = (sunset_jd - sunrise_jd) / 8.0
        night_length = (next_sunrise_jd - sunset_jd) / 8.0

        periods: list[ChoghadiyaPeriod] = []

        day_start_idx = _CHOGHADIYA_CYCLE.index(_DAY_CHOGHADIYA_START[weekday])
        for i in range(8):
            name = _CHOGHADIYA_CYCLE[(day_start_idx + i) % 7]
            start = sunrise_jd + i * day_length
            periods.append(ChoghadiyaPeriod(
                index=i + 1, name=name, nature=_CHOGHADIYA_NATURE[name],
                start_jd=start, end_jd=start + day_length, is_day=True,
            ))

        night_start_idx = _CHOGHADIYA_CYCLE.index(_NIGHT_CHOGHADIYA_START[weekday])
        for i in range(8):
            # Night steps by -2 (not +1 like the day sequence) — cross-
            # verified against PyJHora's gauri_choghadiya_night_table.
            # The previous +1 step only matched PyJHora on segment 1
            # (the start); segments 2-8 were wrong for every weekday,
            # including flipping auspicious/inauspicious labels.
            name = _CHOGHADIYA_CYCLE[(night_start_idx - 2 * i) % 7]
            start = sunset_jd + i * night_length
            periods.append(ChoghadiyaPeriod(
                index=i + 1, name=name, nature=_CHOGHADIYA_NATURE[name],
                start_jd=start, end_jd=start + night_length, is_day=False,
            ))

        return periods

    @staticmethod
    def _compute_horas(
        sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, day_lord: str
    ) -> list[HoraPeriod]:
        day_hora_length = (sunset_jd - sunrise_jd) / 12.0
        night_hora_length = (next_sunrise_jd - sunset_jd) / 12.0

        start_idx = _CHALDEAN_ORDER.index(day_lord)
        horas: list[HoraPeriod] = []

        for i in range(12):
            lord = _CHALDEAN_ORDER[(start_idx + i) % 7]
            start = sunrise_jd + i * day_hora_length
            horas.append(HoraPeriod(
                index=i + 1, lord=lord,
                start_jd=start, end_jd=start + day_hora_length,
                is_day=True,
            ))

        for i in range(12):
            lord = _CHALDEAN_ORDER[(start_idx + 12 + i) % 7]
            start = sunset_jd + i * night_hora_length
            horas.append(HoraPeriod(
                index=i + 1, lord=lord,
                start_jd=start, end_jd=start + night_hora_length,
                is_day=False,
            ))

        return horas

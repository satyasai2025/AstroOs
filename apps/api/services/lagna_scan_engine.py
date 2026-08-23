"""
AstroOS — Lagna Scan Engine

Two questions professional software is expected to answer, both of which
matter for birth-time rectification (cf. Classical Vedic System's "When will
lagna change sign in Rasi" and "Change birthtime to move lagna to"):

  1. Where does the birth lagna sit, and how close is it to a boundary?
  2. What birth time would place the lagna in the previous/next rashi?

The ascendant advances ~360° per sidereal day, but NOT uniformly — the
rate depends on latitude and on which sign is rising (signs of long and
short ascension). So boundaries are found by bisection on the real
ascendant rather than by assuming ~2 hours per sign.

All sidereal reads run inside EphemerisWrapper.sidereal_mode(), since
pyswisseph's sidereal mode is process-global.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apps.api.domain.lagna_scan import (
    BoundaryDistance,
    LagnaInterval,
    LagnaScanResult,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)

_DEG_PER_RASHI = 30.0
_DEG_PER_NAKSHATRA = 360.0 / 27.0        # 13°20'
_DEG_PER_PADA = _DEG_PER_NAKSHATRA / 4.0  # 3°20'

# Bisection window, in days. MUST stay under one sidereal day (0.99727 solar
# days): the unwrapped ascendant advance is monotonic only within a single
# revolution, and a longer window wraps past 360° and breaks the bisection
# predicate — which is exactly how an earlier 1.05-day window returned the
# *previous* revolution's nakshatra boundary (24 h out instead of 27 min).
# 0.95 days still covers ~343° of advance, far more than the ≤30° any
# rashi/nakshatra/pada boundary needs.
_MAX_SEARCH_DAYS = 0.95

_BISECTION_ITERATIONS = 60  # ~1e-16 day resolution; far below a millisecond


def _jd_to_utc(jd: float) -> datetime:
    """Julian Day (UT) → timezone-aware UTC datetime."""
    import swisseph as swe

    year, month, day, hour = swe.revjul(jd)
    whole = int(hour)
    minute_f = (hour - whole) * 60.0
    minute = int(minute_f)
    second_f = (minute_f - minute) * 60.0
    second = int(second_f)
    micro = int(round((second_f - second) * 1e6))
    if micro >= 1_000_000:          # rounding can tip over
        micro -= 1_000_000
        second += 1
    base = datetime(year, month, day, whole, minute, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=second, microseconds=micro)


class LagnaScanEngine:
    """Stateless — holds only the shared EphemerisWrapper."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    # ── ascendant helpers ────────────────────────────────────────────────────

    def _asc(self, jd: float, lat: float, lon: float) -> float:
        trop, _ = self._wrapper.get_ascendant_and_cusps(jd, lat, lon, "W")
        return self._wrapper.to_sidereal(trop, self._wrapper.get_ayanamsa(jd))

    def _advance(self, jd0: float, jd: float, lat: float, lon: float) -> float:
        """Ascendant travelled since jd0, unwrapped to [0, 360)."""
        return (self._asc(jd, lat, lon) - self._asc(jd0, lat, lon)) % 360.0

    def _time_of_advance(
        self, jd0: float, target_deg: float, lat: float, lon: float
    ) -> float:
        """First jd > jd0 at which the ascendant has advanced `target_deg`.

        Bisects on the unwrapped advance, which is monotonic increasing over
        one revolution — this is why the search is capped at ~1 sidereal day.
        """
        lo, hi = jd0, jd0 + _MAX_SEARCH_DAYS
        for _ in range(_BISECTION_ITERATIONS):
            mid = (lo + hi) / 2.0
            if self._advance(jd0, mid, lat, lon) < target_deg:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    def _boundary_after(
        self, jd: float, lat: float, lon: float, span: float
    ) -> float:
        """jd of the next multiple-of-`span` boundary the lagna crosses."""
        cur = self._asc(jd, lat, lon)
        remaining = span - (cur % span)
        return self._time_of_advance(jd, remaining, lat, lon)

    def _time_of_regress(
        self, jd: float, target_deg: float, lat: float, lon: float
    ) -> float:
        """Last jd' < jd at which the ascendant was `target_deg` behind `jd`.

        Mirror of _time_of_advance. The backward advance (asc(jd) - asc(t))
        grows monotonically as t moves back, within one revolution — so the
        bisection is on t, not on elapsed degrees.
        """
        lo, hi = jd - _MAX_SEARCH_DAYS, jd
        for _ in range(_BISECTION_ITERATIONS):
            mid = (lo + hi) / 2.0
            if self._advance(mid, jd, lat, lon) > target_deg:
                lo = mid          # mid is too far back
            else:
                hi = mid
        return (lo + hi) / 2.0

    def _boundary_before(
        self, jd: float, lat: float, lon: float, span: float
    ) -> float:
        """jd at which the lagna entered its current `span`-sized division."""
        into = self._asc(jd, lat, lon) % span
        return self._time_of_regress(jd, into, lat, lon)

    # ── public API ───────────────────────────────────────────────────────────

    def scan(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        window_hours: float = 2.0,
    ) -> LagnaScanResult:
        with self._wrapper.sidereal_mode(ayanamsa):
            return self._scan_locked(
                birth_datetime_utc, latitude, longitude, window_hours
            )

    def _scan_locked(
        self,
        birth_datetime_utc: datetime,
        lat: float,
        lon: float,
        window_hours: float,
    ) -> LagnaScanResult:
        jd = datetime_to_jd(birth_datetime_utc)
        asc = self._asc(jd, lat, lon)
        rashi, rashi_deg = longitude_to_rashi(asc)
        nak = longitude_to_nakshatra(asc)

        # Sensitivity: measure over ±30 s and average, so a single-sided
        # difference near a boundary doesn't skew it.
        half = 30.0 / 86400.0
        moved = self._advance(jd - half, jd + half, lat, lon)
        arcmin_per_minute = moved * 60.0 / 1.0  # 60 s window → per minute

        boundaries: list[BoundaryDistance] = []
        for label, span in (
            ("rashi", _DEG_PER_RASHI),
            ("nakshatra", _DEG_PER_NAKSHATRA),
            ("pada", _DEG_PER_PADA),
        ):
            prev_jd = self._boundary_before(jd, lat, lon, span)
            next_jd = self._boundary_after(jd, lat, lon, span)
            into = asc % span
            boundaries.append(
                BoundaryDistance(
                    label=label,
                    minutes_since_previous=(jd - prev_jd) * 24.0 * 60.0,
                    minutes_until_next=(next_jd - jd) * 24.0 * 60.0,
                    degrees_since_previous=into,
                    degrees_until_next=span - into,
                )
            )

        # Rashi timeline across the window.
        win = window_hours / 24.0
        intervals: list[LagnaInterval] = []
        cursor = self._boundary_before(jd - win, lat, lon, _DEG_PER_RASHI)
        end_limit = jd + win
        while cursor < end_limit:
            nxt = self._boundary_after(cursor + 1e-9, lat, lon, _DEG_PER_RASHI)
            seg_rashi, _ = longitude_to_rashi(
                self._asc((cursor + nxt) / 2.0, lat, lon)
            )
            intervals.append(
                LagnaInterval(
                    rashi=seg_rashi,
                    start_utc=_jd_to_utc(cursor),
                    end_utc=_jd_to_utc(nxt),
                    duration_minutes=(nxt - cursor) * 24.0 * 60.0,
                    contains_birth=cursor <= jd < nxt,
                )
            )
            cursor = nxt

        return LagnaScanResult(
            sidereal_longitude=asc,
            rashi=rashi,
            rashi_degree=rashi_deg,
            nakshatra=nak.nakshatra,
            pada=nak.pada,
            arcmin_per_minute=arcmin_per_minute,
            boundaries=tuple(boundaries),
            intervals=tuple(intervals),
            window_start_utc=_jd_to_utc(jd - win),
            window_end_utc=_jd_to_utc(jd + win),
        )

    def birthtime_for_adjacent_sign(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        direction: str,
        ayanamsa: str = "lahiri",
    ) -> datetime:
        """Birth time that moves the lagna into the next/previous rashi.

        Mirrors Classical Vedic's "Change birthtime to move lagna to → the previous /
        the next sign". Returns the moment just inside the target sign: one
        second past the boundary going forward, one second before it going
        back, so the result is unambiguously in the intended rashi rather
        than sitting exactly on the cusp.
        """
        if direction not in ("next", "previous"):
            raise ValueError("direction must be 'next' or 'previous'")

        with self._wrapper.sidereal_mode(ayanamsa):
            jd = datetime_to_jd(birth_datetime_utc)
            one_second = 1.0 / 86400.0
            if direction == "next":
                boundary = self._boundary_after(jd, latitude, longitude, _DEG_PER_RASHI)
                return _jd_to_utc(boundary + one_second)
            # Previous: step back past the start of the current sign.
            start = self._boundary_before(jd, latitude, longitude, _DEG_PER_RASHI)
            return _jd_to_utc(start - one_second)

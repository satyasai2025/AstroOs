"""
AstroOS — Planet Sign-Change Engine

Finds when a graha entered its current rashi and when it will leave.

Why this is a scan and not arithmetic
─────────────────────────────────────
Planetary longitude is non-monotonic — retrograde loops mean a planet can
approach a boundary, reverse, and cross it much later or in the other
direction. So the engine steps forward/backward until the rashi index
actually changes, then bisects inside that bracket. The step is sized from
the planet's live speed (roughly 1° of travel per step, clamped), which
keeps a Moon scan a few dozen calls and a Saturn scan under a hundred.

Speed is re-read every step rather than assumed constant, so stations are
handled naturally: near a station the step widens, and the index simply
does not change until the planet genuinely crosses.

Ketu is derived, not computed: it is always exactly opposite Rahu, so its
sign changes at the same instants — the engine scans Rahu and mirrors.

All sidereal reads run inside EphemerisWrapper.sidereal_mode(), since
pyswisseph's sidereal mode is process-global.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import swisseph as swe

from apps.api.domain.sign_change import PlanetSignPeriod
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)

_DEG_PER_RASHI = 30.0
_BISECTION_ITERATIONS = 60

# Per-planet scan horizons, in days — comfortably more than one sign takes,
# including retrograde delay. Saturn is the slow case: ~2.5 years per sign,
# and a retrograde loop can stretch the observed tenancy well past that.
_SEARCH_DAYS: dict[str, float] = {
    "moon": 10.0,
    "sun": 90.0,
    "mercury": 200.0,
    "venus": 200.0,
    "mars": 800.0,
    "jupiter": 900.0,
    "saturn": 1600.0,
    "rahu": 900.0,
    "ketu": 900.0,
}
_DEFAULT_SEARCH_DAYS = 900.0

# Step sizing: aim for ~1° of travel, but never crawl and never leap so far
# that a whole sign could be skipped between samples.
_MIN_STEP_DAYS = 0.02
_MAX_STEP_DAYS = 15.0
_MIN_SPEED = 0.004  # deg/day floor, so a stationed planet still advances


def _jd_to_utc(jd: float) -> datetime:
    year, month, day, hour = swe.revjul(jd)
    whole = int(hour)
    minute_f = (hour - whole) * 60.0
    minute = int(minute_f)
    second_f = (minute_f - minute) * 60.0
    second = int(second_f)
    micro = int(round((second_f - second) * 1e6))
    if micro >= 1_000_000:
        micro -= 1_000_000
        second += 1
    base = datetime(year, month, day, whole, minute, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=second, microseconds=micro)


class SignChangeEngine:
    """Stateless — holds only the shared EphemerisWrapper."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    # ── raw reads ────────────────────────────────────────────────────────────

    def _pos(self, planet: str, jd: float) -> tuple[float, float]:
        """(sidereal longitude, speed deg/day) for `planet` at `jd`."""
        p = self._wrapper.get_planet_position(planet, jd)
        sid = self._wrapper.to_sidereal(p.longitude, self._wrapper.get_ayanamsa(jd))
        return sid, p.speed_deg_per_day

    @staticmethod
    def _index(lon: float) -> int:
        return int(lon // _DEG_PER_RASHI)

    # ── scanning ─────────────────────────────────────────────────────────────

    def _find_change(
        self, planet: str, jd0: float, direction: int, max_days: float
    ) -> Optional[float]:
        """First jd in `direction` (+1/-1) where the rashi index differs.

        Returns None if no change occurs within `max_days` — a real outcome
        for a slow planet, not an error.
        """
        idx0 = self._index(self._pos(planet, jd0)[0])
        t = jd0
        while abs(t - jd0) < max_days:
            speed = abs(self._pos(planet, t)[1])
            step = min(max(1.0 / max(speed, _MIN_SPEED), _MIN_STEP_DAYS), _MAX_STEP_DAYS)
            nxt = t + step * direction
            if self._index(self._pos(planet, nxt)[0]) != idx0:
                lo, hi = (t, nxt) if direction > 0 else (nxt, t)
                for _ in range(_BISECTION_ITERATIONS):
                    mid = (lo + hi) / 2.0
                    same = self._index(self._pos(planet, mid)[0]) == idx0
                    if same == (direction > 0):
                        lo = mid
                    else:
                        hi = mid
                return (lo + hi) / 2.0
            t = nxt
        return None

    # ── public API ───────────────────────────────────────────────────────────

    def sign_period(
        self,
        planet: str,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> PlanetSignPeriod:
        with self._wrapper.sidereal_mode(ayanamsa):
            return self._sign_period_locked(planet, birth_datetime_utc)

    def _sign_period_locked(
        self, planet: str, birth_datetime_utc: datetime
    ) -> PlanetSignPeriod:
        jd = datetime_to_jd(birth_datetime_utc)

        # Ketu is exactly opposite Rahu, so it turns sign at the same instants.
        scan_body = "rahu" if planet == "ketu" else planet
        max_days = _SEARCH_DAYS.get(planet, _DEFAULT_SEARCH_DAYS)

        lon, speed = self._pos(planet, jd)
        rashi, rashi_deg = longitude_to_rashi(lon)
        nak = longitude_to_nakshatra(lon)

        exit_jd = self._find_change(scan_body, jd, +1, max_days)
        entry_jd = self._find_change(scan_body, jd, -1, max_days)

        next_rashi = exits_retro = None
        if exit_jd is not None:
            # Sample just past the crossing so the reported sign is the one
            # actually entered — at the boundary itself it is ambiguous.
            after_lon, after_speed = self._pos(planet, exit_jd + 1e-4)
            next_rashi = longitude_to_rashi(after_lon)[0]
            exits_retro = after_speed < 0

        previous_rashi = None
        if entry_jd is not None:
            before_lon, _ = self._pos(planet, entry_jd - 1e-4)
            previous_rashi = longitude_to_rashi(before_lon)[0]

        return PlanetSignPeriod(
            planet=planet,
            sidereal_longitude=lon,
            rashi=rashi,
            rashi_degree=rashi_deg,
            nakshatra=nak.nakshatra,
            pada=nak.pada,
            is_retrograde=speed < 0,
            speed_deg_per_day=speed,
            entered_utc=_jd_to_utc(entry_jd) if entry_jd else None,
            exits_utc=_jd_to_utc(exit_jd) if exit_jd else None,
            days_since_entry=(jd - entry_jd) if entry_jd else None,
            days_until_exit=(exit_jd - jd) if exit_jd else None,
            previous_rashi=previous_rashi,
            next_rashi=next_rashi,
            exits_retrograde=exits_retro,
            search_limit_days=max_days,
        )

    def all_planets(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> list[PlanetSignPeriod]:
        """Sign tenancy for all nine grahas, in the conventional order."""
        order = ("sun", "moon", "mars", "mercury", "jupiter",
                 "venus", "saturn", "rahu", "ketu")
        with self._wrapper.sidereal_mode(ayanamsa):
            return [self._sign_period_locked(p, birth_datetime_utc) for p in order]

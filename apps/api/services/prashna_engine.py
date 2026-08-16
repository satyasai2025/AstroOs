"""
AstroOS — Prashna (Horary) Engine

Prashna Arudha is a pure table lookup — no ephemeris involved. The six
Sphutas require the Ascendant, Moon, Sun, Rahu and Gulika longitudes for the
query/birth moment, so this engine composes UpagrahaEngine (for Gulika)
rather than re-deriving the eighth-part day division itself.

Formulas (all mod 360, longitudes in sidereal degrees) — sourced verbatim
from PyJHora's `jhora/horoscope/chart/sphuta.py`:

    Trisphuta     = Lagna + Moon + Gulika
    Chatursphuta  = Trisphuta + Sun
    Panchasphuta  = Chatursphuta + Rahu
    Pranasphuta   = 5 * Lagna + Gulika
    Dehasphuta    = 8 * Moon + Gulika
    Mrityusphuta  = 7 * Gulika + Sun
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.prashna import (
    PRASHNA_PLANET_NAMES,
    PRASNA_KP_249_TABLE,
    PrashnaArudhaResult,
    PrashnaSphutaResult,
    SphutaPosition,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.upagraha_engine import UpagrahaEngine
from packages.shared.rashi_offset import house_offset

_RASHI_INDEX_OF_DEGREE = 30.0
_RASHI_NAMES: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)


class PrashnaEngine:
    """Stateless — takes an EphemerisWrapper, holds no chart state."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper
        self._upagraha = UpagrahaEngine(wrapper)

    # ── Prashna Arudha (seed 1-249, no ephemeris) ───────────────────────────

    def arudha_from_seed(self, seed_number: int) -> PrashnaArudhaResult:
        if not 1 <= seed_number <= 249:
            raise ValueError("Prashna seed number must be between 1 and 249")

        rashi_idx, nak_idx, start_deg, end_deg, sign_lord, star_lord, sub_lord = (
            PRASNA_KP_249_TABLE[seed_number - 1]
        )
        mid_deg = (start_deg + end_deg) / 2.0
        longitude = rashi_idx * _RASHI_INDEX_OF_DEGREE + mid_deg

        return PrashnaArudhaResult(
            seed_number=seed_number,
            sidereal_longitude=longitude,
            rashi=_RASHI_NAMES[rashi_idx],
            rashi_degree=mid_deg,
            nakshatra=longitude_to_nakshatra(longitude).nakshatra,
            sign_lord=PRASHNA_PLANET_NAMES[sign_lord],
            star_lord=PRASHNA_PLANET_NAMES[star_lord],
            sub_lord=PRASHNA_PLANET_NAMES[sub_lord],
            arc_start_degree=start_deg,
            arc_end_degree=end_deg,
        )

    # ── Sphutas (chart-dependent) ────────────────────────────────────────────

    def _sidereal_ascendant(self, jd: float, lat: float, lon: float, ayanamsa: str) -> float:
        trop, _cusps = self._wrapper.get_ascendant_and_cusps(jd, lat, lon, "W")
        return self._wrapper.to_sidereal(trop, self._wrapper.get_ayanamsa(jd))

    def _sidereal_planet(self, planet: str, jd: float) -> float:
        return self._wrapper.to_sidereal(
            self._wrapper.get_planet_position(planet, jd).longitude,
            self._wrapper.get_ayanamsa(jd),
        )

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

    def compute_sphutas(
        self,
        moment_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> PrashnaSphutaResult:
        with self._wrapper.sidereal_mode(ayanamsa):
            return self._compute_sphutas_locked(moment_utc, latitude, longitude, ayanamsa)

    def _compute_sphutas_locked(
        self,
        moment_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str,
    ) -> PrashnaSphutaResult:
        jd = datetime_to_jd(moment_utc)

        asc_lon = self._sidereal_ascendant(jd, latitude, longitude, ayanamsa)
        moon_lon = self._sidereal_planet("moon", jd)
        sun_lon = self._sidereal_planet("sun", jd)
        rahu_lon = self._sidereal_planet("rahu", jd)

        upagraha_result = self._upagraha.compute(moment_utc, latitude, longitude, ayanamsa)
        gulika_lon = next(
            u.sidereal_longitude for u in upagraha_result.upagrahas if u.name == "gulika"
        )

        tri = (asc_lon + moon_lon + gulika_lon) % 360.0
        chatur = (tri + sun_lon) % 360.0
        pancha = (chatur + rahu_lon) % 360.0
        prana = (5.0 * asc_lon + gulika_lon) % 360.0
        deha = (8.0 * moon_lon + gulika_lon) % 360.0
        mrityu = (7.0 * gulika_lon + sun_lon) % 360.0

        sphutas = tuple(
            SphutaPosition(name=name, **self._describe(lon_, asc_lon))
            for name, lon_ in (
                ("trisphuta", tri),
                ("chatursphuta", chatur),
                ("panchasphuta", pancha),
                ("pranasphuta", prana),
                ("dehasphuta", deha),
                ("mrityusphuta", mrityu),
            )
        )

        return PrashnaSphutaResult(
            sphutas=sphutas,
            ascendant_longitude=asc_lon,
            gulika_longitude=gulika_lon,
        )

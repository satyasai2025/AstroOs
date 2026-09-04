"""
AstroOS — Transit Engine (Module 11)

Compares a natal D1Chart against planetary positions at any other
moment ("transit date"). Genuinely different dependency shape from
every engine before it: needs both the natal chart AND
EphemerisWrapper, since it computes a second, independent set of
planetary positions rather than only reading from an already-built
chart.

Deliberately does NOT compute a "transit lagna" (a fresh ascendant for
the transit moment) — Gochara is conventionally read from the natal
Moon or natal Lagna, not a moment-of-transit ascendant, so no
latitude/longitude is needed for the transit moment itself (only for
the natal chart, already baked into the natal_chart argument).
house_from_natal_ascendant is the transiting planet's house counted
from the NATAL Lagna (an alternate classical reference point to Moon,
not a new chart).

Not wired into any router or persistence layer — same scope discipline
as every engine before it.
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from apps.api.services.gati_classifier import classify_gati
from apps.api.services.nakshatra_vedha_calculator import NakshatraVedhaCalculator
from apps.api.services.vedha_calculator import VedhaCalculator
from packages.shared.enums import Rashi
from packages.shared.rashi_offset import house_offset
from packages.shared.sarvatobhadra_grid import longitude_to_sbc_nakshatra

_RASHI_LIST = [r.value for r in Rashi]

_ALL_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
_ASHTAKAVARGA_ELIGIBLE = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}

_RULE_VERSION = "1.0"


def _house_from_reference(reference_rashi: str, target_rashi: str) -> int:
    """
    The house number (1-12) of `target_rashi`, counted cyclically from
    `reference_rashi` (reference itself = house 1). Inverse of the
    "rashi at offset" helpers used elsewhere in this codebase (Yoga's
    houses_from, Ashtakavarga's _rashi_at_offset) — here we have both
    rashis and want the offset between them.
    """
    reference_index = _RASHI_LIST.index(reference_rashi)
    target_index = _RASHI_LIST.index(target_rashi)
    return house_offset(reference_index, target_index)


class TransitEngine:
    """
    Needs an EphemerisWrapper (to compute transiting positions), an
    AshtakavargaEngine, and (since Module 11 Phase 2) a VedhaCalculator.
    """

    def __init__(
        self,
        wrapper: EphemerisWrapper,
        ashtakavarga_engine: AshtakavargaEngine | None = None,
        vedha_calculator: VedhaCalculator | None = None,
        nakshatra_vedha_calculator: NakshatraVedhaCalculator | None = None,
    ) -> None:
        self._wrapper = wrapper
        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()
        self._vedha_calculator = vedha_calculator or VedhaCalculator()
        self._nakshatra_vedha_calculator = nakshatra_vedha_calculator or NakshatraVedhaCalculator()

    def _transiting_rashi(self, planet: str, jd: float) -> str:
        tropical_position = self._wrapper.get_planet_position(planet, jd)
        ayanamsa_val = self._wrapper.get_ayanamsa(jd)
        sidereal_lon = self._wrapper.to_sidereal(tropical_position.longitude, ayanamsa_val)
        rashi, _ = longitude_to_rashi(sidereal_lon)
        return rashi

    def _transiting_position(self, planet: str, jd: float) -> tuple[str, float, bool, float]:
        """(rashi, sidereal_longitude, is_retrograde, speed_deg_per_day) at
        the transit moment — the sidereal longitude and retrograde state
        are what Nakshatra Vedha (SBC) needs on top of the rashi Gochara
        already uses; speed is additionally needed for Gati."""
        tropical_position = self._wrapper.get_planet_position(planet, jd)
        ayanamsa_val = self._wrapper.get_ayanamsa(jd)
        sidereal_lon = self._wrapper.to_sidereal(tropical_position.longitude, ayanamsa_val)
        rashi, _ = longitude_to_rashi(sidereal_lon)
        return rashi, sidereal_lon, tropical_position.is_retrograde, tropical_position.speed_deg_per_day

    def compute_transit(
        self,
        natal_chart: D1Chart,
        transit_datetime_utc: datetime,
    ) -> list[TransitPlanetResult]:
        """
        Gochara (transit) read for all 9 grahas at `transit_datetime_utc`,
        against `natal_chart`. Ashtakavarga bindu strength is looked up
        from the NATAL chart's Bhinnashtakavarga (computed once, from
        birth positions) — the transiting planet's *current* sign is
        checked against that natal reference table, which is the
        standard classical convention (Ashtakavarga tables are fixed at
        birth; only the transiting position that's looked up changes).

        Vedha/Vipreet Vedha (Module 11 Phase 2) needs every planet's
        house-from-Moon computed first — one planet's obstruction status
        depends on where every OTHER planet currently is — so this runs
        as a second pass after all 9 houses are known. Nakshatra Vedha
        (SBC, Module 11 Phase 3) needs the same two-pass shape, but keyed
        on each planet's 28-system SBC nakshatra instead of its house.
        """
        natal_moon = next(p for p in natal_chart.planets if p.planet == "moon")
        natal_moon_rashi = natal_moon.rashi
        natal_ascendant_rashi = natal_chart.ascendant.rashi

        jd = datetime_to_jd(transit_datetime_utc)

        natal_bhinnashtakavarga = {
            r.target_planet: r
            for r in self._ashtakavarga_engine.compute_bhinnashtakavarga(natal_chart)
        }

        # Pass 1: transiting rashi, house-from-Moon, SBC nakshatra and
        # retrograde state for all 9 planets.
        houses_from_moon: dict[str, int] = {}
        houses_from_ascendant: dict[str, int] = {}
        transit_rashis: dict[str, str] = {}
        transit_rashi_degrees: dict[str, float] = {}
        transit_nakshatras_sbc: dict[str, str] = {}
        transit_nakshatras: dict[str, str] = {}
        transit_padas: dict[str, int] = {}
        is_retrograde_by_planet: dict[str, bool] = {}
        speeds_by_planet: dict[str, float] = {}
        for planet in _ALL_PLANETS:
            transit_rashi, sidereal_lon, is_retrograde, speed = self._transiting_position(planet, jd)
            transit_rashis[planet] = transit_rashi
            _, rashi_degree = longitude_to_rashi(sidereal_lon)
            transit_rashi_degrees[planet] = rashi_degree
            houses_from_moon[planet] = _house_from_reference(natal_moon_rashi, transit_rashi)
            houses_from_ascendant[planet] = _house_from_reference(natal_ascendant_rashi, transit_rashi)
            transit_nakshatras_sbc[planet] = longitude_to_sbc_nakshatra(sidereal_lon)
            nak_info = longitude_to_nakshatra(sidereal_lon)
            transit_nakshatras[planet] = nak_info.nakshatra
            transit_padas[planet] = nak_info.pada
            is_retrograde_by_planet[planet] = is_retrograde
            speeds_by_planet[planet] = speed

        # Pass 2: assemble results, including both Vedha systems (each
        # needs all 9 planets' positions known first).
        results = []
        for planet in _ALL_PLANETS:
            transit_rashi = transit_rashis[planet]
            house_from_moon = houses_from_moon[planet]

            bindus = None
            if planet in _ASHTAKAVARGA_ELIGIBLE:
                bindus = natal_bhinnashtakavarga[planet].bindus_in_rashi(transit_rashi)

            is_sade_sati = planet == "saturn" and house_from_moon in (12, 1, 2)
            is_ashtama_shani = planet == "saturn" and house_from_moon == 8

            other_houses = {p: h for p, h in houses_from_moon.items() if p != planet}
            is_favorable = self._vedha_calculator.classify_house(planet, house_from_moon)
            has_vedha, has_vipreet_vedha, vedha_planet = self._vedha_calculator.check(
                planet, house_from_moon, other_houses,
            )

            other_nakshatras_sbc = {p: n for p, n in transit_nakshatras_sbc.items() if p != planet}
            has_nakshatra_vedha, nakshatra_vedha_planet, nakshatra_vedha_type, nakshatra_vedha_target = (
                self._nakshatra_vedha_calculator.check(
                    planet,
                    transit_nakshatras_sbc[planet],
                    is_retrograde_by_planet[planet],
                    other_nakshatras_sbc,
                )
            )

            results.append(TransitPlanetResult(
                planet=planet,
                transit_rashi=transit_rashi,
                house_from_natal_moon=house_from_moon,
                house_from_natal_ascendant=houses_from_ascendant[planet],
                ashtakavarga_bindus=bindus,
                is_sade_sati=is_sade_sati,
                is_ashtama_shani=is_ashtama_shani,
                is_favorable_house=is_favorable,
                has_vedha=has_vedha,
                has_vipreet_vedha=has_vipreet_vedha,
                vedha_planet=vedha_planet,
                transit_nakshatra_sbc=transit_nakshatras_sbc[planet],
                has_nakshatra_vedha=has_nakshatra_vedha,
                nakshatra_vedha_planet=nakshatra_vedha_planet,
                nakshatra_vedha_type=nakshatra_vedha_type,
                nakshatra_vedha_target=nakshatra_vedha_target,
                rule_version=_RULE_VERSION,
                transit_rashi_degree=transit_rashi_degrees[planet],
                transit_nakshatra=transit_nakshatras[planet],
                transit_pada=transit_padas[planet],
                is_retrograde=is_retrograde_by_planet[planet],
                speed_deg_per_day=speeds_by_planet[planet],
                gati=classify_gati(planet, speeds_by_planet[planet], is_retrograde_by_planet[planet]),
            ))

        return results

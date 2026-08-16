"""
AstroOS — Sarvatobhadra Chakra (SBC) Report Service

Computes a full-grid SBC snapshot at a given moment: which 28-system
(Abhijit-aware) nakshatra each of the 9 grahas currently occupies, plus
(optionally) the Vedha result onto a specified Janma element, using
sbc_vedha_engine.SBCVedhaEngine. Mirrors TransitEngine's pattern for
computing sidereal transiting positions (see
apps/api/services/transit_engine.py's `_transiting_position`), since
this needs the same raw (rashi, sidereal_longitude, is_retrograde,
speed_deg_per_day) tuple TransitEngine already derives, plus combustion
and Tithi on top — neither of which TransitPlanetResult currently
carries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apps.api.services.ephemeris_wrapper import EphemerisWrapper, datetime_to_jd, longitude_to_rashi
from apps.api.services.sbc_vedha_engine import SBCTransitPlanet, SBCVedhaEngine, SBCVedhaResult
from packages.shared.sarvatobhadra_grid import longitude_to_sbc_nakshatra
from packages.shared.sbc_cellnum_table import NAKSHATRA_TO_CELLNUM

PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


@dataclass
class SBCGridPlanetPosition:
    planet: str
    nakshatra: str  # 28-system (Abhijit-aware)
    cellnum: int
    rashi: str
    rashi_degree: float
    is_retrograde: bool
    is_combust: bool
    speed_deg_per_day: float


@dataclass
class SBCReport:
    moment_utc: datetime
    tithi_number: int
    positions: list[SBCGridPlanetPosition]
    vedha_result: Optional[SBCVedhaResult]
    janma_nakshatra: Optional[str]


class SBCReportService:
    def __init__(self, wrapper: EphemerisWrapper, vedha_engine: SBCVedhaEngine | None = None) -> None:
        self._wrapper = wrapper
        self._vedha_engine = vedha_engine or SBCVedhaEngine()

    def build_report(
        self,
        moment_utc: datetime,
        janma_nakshatra: Optional[str] = None,
    ) -> SBCReport:
        jd = datetime_to_jd(moment_utc)
        ayanamsa_val = self._wrapper.get_ayanamsa(jd)

        sidereal_lons: dict[str, float] = {}
        positions: list[SBCGridPlanetPosition] = []
        transit_planets: list[SBCTransitPlanet] = []

        sun_tropical = self._wrapper.get_planet_position("sun", jd)
        sun_sidereal = self._wrapper.to_sidereal(sun_tropical.longitude, ayanamsa_val)
        sidereal_lons["sun"] = sun_sidereal

        moon_sidereal: Optional[float] = None

        for planet in PLANETS:
            tropical = self._wrapper.get_planet_position(planet, jd)
            sidereal_lon = self._wrapper.to_sidereal(tropical.longitude, ayanamsa_val)
            sidereal_lons[planet] = sidereal_lon
            if planet == "moon":
                moon_sidereal = sidereal_lon

            rashi, rashi_degree = longitude_to_rashi(sidereal_lon)
            nakshatra_sbc = longitude_to_sbc_nakshatra(sidereal_lon)
            is_combust, _ = self._wrapper.is_combust(planet, sidereal_lon, sun_sidereal)

            positions.append(
                SBCGridPlanetPosition(
                    planet=planet,
                    nakshatra=nakshatra_sbc,
                    cellnum=NAKSHATRA_TO_CELLNUM[nakshatra_sbc],
                    rashi=rashi,
                    rashi_degree=rashi_degree,
                    is_retrograde=tropical.is_retrograde,
                    is_combust=is_combust,
                    speed_deg_per_day=tropical.speed_deg_per_day,
                )
            )

        tithi_info = self._wrapper.get_tithi(moon_sidereal, sun_sidereal)  # type: ignore[arg-type]

        for pos in positions:
            transit_planets.append(
                SBCTransitPlanet(
                    planet=pos.planet,
                    nakshatra=pos.nakshatra,
                    rashi=pos.rashi,
                    rashi_degree=pos.rashi_degree,
                    speed_deg_per_day=pos.speed_deg_per_day,
                    is_retrograde=pos.is_retrograde,
                    is_combust=pos.is_combust,
                    tithi=tithi_info.number if pos.planet == "moon" else None,
                )
            )

        vedha_result = None
        if janma_nakshatra is not None:
            vedha_result = self._vedha_engine.check(janma_nakshatra, transit_planets)

        return SBCReport(
            moment_utc=moment_utc,
            tithi_number=tithi_info.number,
            positions=positions,
            vedha_result=vedha_result,
            janma_nakshatra=janma_nakshatra,
        )

"""
AstroOS — Tarabala Report Service

Computes, at a given moment, for a given Janma Nakshatra (and
optionally a Lagna Nakshatra and an active dasha-lord chain):
- Natal Tarabala for each of the 9 grahas (their own birth nakshatra's
  Tara position — needs each planet's natal longitude at birth).
- Transit Tarabala for each of the 9 grahas (current nakshatra's Tara
  position).
- Lordship Tara for each dasha level, if a dasha chain is supplied
  (see packages/shared/tarabala.py's module docstring — mapping only,
  no computed "active" verdict, per the source's own caution).
- Multi-level convergence: how many of the supplied active dasha
  levels are currently in a favorable Tara (by lordship mapping).
- The yearly Tara cycle position currently running.
- Best-stars intersection if a Lagna Nakshatra is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
)
from packages.shared.tarabala import (
    LORDSHIP_TARA_POSITION,
    SPECIAL_POINTS_28,
    best_stars,
    is_favorable_tara_9,
    natal_tarabala,
    special_point_nakshatra,
    tara_name_9,
    transit_tarabala,
    yearly_tara,
)

PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


@dataclass
class PlanetTara:
    planet: str
    nakshatra: str
    position: int
    name: str
    is_favorable: bool


@dataclass
class LordshipTaraEntry:
    dasha_level: int  # 1 = Mahadasha, 2 = Antardasha, ...
    lord: str
    position_name: str
    is_favorable: bool


@dataclass
class SpecialPointEntry:
    name: str
    from_moon: str
    from_lagna: Optional[str]


@dataclass
class TarabalaReport:
    janma_nakshatra: str
    lagna_nakshatra: Optional[str]
    moment_utc: datetime
    natal_tarabala: list[PlanetTara]
    transit_tarabala: list[PlanetTara]
    lordship_tarabala: list[LordshipTaraEntry]
    favorable_level_count: int
    total_active_levels: int
    all_levels_favorable: bool
    yearly_age: Optional[int]
    yearly_position: Optional[int]
    yearly_name: Optional[str]
    best_stars: Optional[list[str]]
    special_points: list[SpecialPointEntry]


class TarabalaReportService:
    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def _nakshatra_of(self, planet: str, jd: float) -> str:
        tropical = self._wrapper.get_planet_position(planet, jd)
        ayanamsa_val = self._wrapper.get_ayanamsa(jd)
        sidereal_lon = self._wrapper.to_sidereal(tropical.longitude, ayanamsa_val)
        return longitude_to_nakshatra(sidereal_lon).nakshatra

    def build_report(
        self,
        janma_nakshatra: str,
        birth_datetime_utc: datetime,
        moment_utc: datetime,
        lagna_nakshatra: Optional[str] = None,
        dasha_chain: Optional[list[str]] = None,
    ) -> TarabalaReport:
        birth_jd = datetime_to_jd(birth_datetime_utc)
        moment_jd = datetime_to_jd(moment_utc)

        natal_list: list[PlanetTara] = []
        transit_list: list[PlanetTara] = []

        for planet in PLANETS:
            natal_nak = self._nakshatra_of(planet, birth_jd)
            pos, name, fav = natal_tarabala(janma_nakshatra, natal_nak)
            natal_list.append(PlanetTara(planet=planet, nakshatra=natal_nak, position=pos, name=name, is_favorable=fav))

            transit_nak = self._nakshatra_of(planet, moment_jd)
            t_pos, t_name, t_fav = transit_tarabala(janma_nakshatra, transit_nak)
            transit_list.append(PlanetTara(planet=planet, nakshatra=transit_nak, position=t_pos, name=t_name, is_favorable=t_fav))

        lordship_list: list[LordshipTaraEntry] = []
        favorable_count = 0
        chain = dasha_chain or []
        for level, lord in enumerate(chain, start=1):
            position_name = LORDSHIP_TARA_POSITION.get(lord)
            if position_name is None:
                continue
            fav = position_name in {"sampat", "kshema", "sadhaka", "mitra", "paramamitra"}
            if fav:
                favorable_count += 1
            lordship_list.append(
                LordshipTaraEntry(dasha_level=level, lord=lord, position_name=position_name, is_favorable=fav)
            )

        yearly_age = yearly_position = None
        yearly_name = None
        try:
            yearly_age, yearly_position, yearly_name = yearly_tara(janma_nakshatra, birth_datetime_utc, moment_utc)
        except ValueError:
            pass  # moment before birth — leave yearly fields unset rather than raising

        best = None
        if lagna_nakshatra is not None:
            best = sorted(best_stars(janma_nakshatra, lagna_nakshatra))

        special_points = [
            SpecialPointEntry(
                name=name,
                from_moon=special_point_nakshatra(janma_nakshatra, name),
                from_lagna=special_point_nakshatra(lagna_nakshatra, name) if lagna_nakshatra else None,
            )
            for name in SPECIAL_POINTS_28
        ]

        return TarabalaReport(
            janma_nakshatra=janma_nakshatra,
            lagna_nakshatra=lagna_nakshatra,
            moment_utc=moment_utc,
            natal_tarabala=natal_list,
            transit_tarabala=transit_list,
            lordship_tarabala=lordship_list,
            favorable_level_count=favorable_count,
            total_active_levels=len(lordship_list),
            all_levels_favorable=len(lordship_list) > 0 and favorable_count == len(lordship_list),
            yearly_age=yearly_age,
            yearly_position=yearly_position,
            yearly_name=yearly_name,
            best_stars=best,
            special_points=special_points,
        )

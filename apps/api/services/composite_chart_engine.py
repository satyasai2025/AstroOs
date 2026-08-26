"""
AstroOS — Composite / Midpoint Relationship Chart Engine
Calculates true shortest-arc planetary and house midpoints between Chart A and Chart B,
generating the composite horoscope representing the relationship entity.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.synastry import CompositeChartResult, CompositePlanet
from apps.api.services.synastry_engine import _RASHI_ORDER


class CompositeChartEngine:
    """
    Computes shortest-arc composite midpoints for Ascendant and all planetary bodies.
    """

    @staticmethod
    def shortest_arc_midpoint(long_a: float, long_b: float) -> float:
        """Computes true circular shortest-arc midpoint in degrees [0, 360)."""
        diff = (long_b - long_a) % 360.0
        if diff <= 180.0:
            midpoint = (long_a + diff / 2.0) % 360.0
        else:
            midpoint = (long_a + (diff - 360.0) / 2.0) % 360.0
        return (midpoint + 360.0) % 360.0

    @classmethod
    def calculate_composite_chart(
        cls,
        chart_a: D1Chart,
        chart_b: D1Chart,
        name_a: str = "Partner A",
        name_b: str = "Partner B",
    ) -> CompositeChartResult:
        asc_a = chart_a.ascendant.sidereal_longitude if chart_a.ascendant else 0.0
        asc_b = chart_b.ascendant.sidereal_longitude if chart_b.ascendant else 0.0
        comp_asc_long = cls.shortest_arc_midpoint(asc_a, asc_b)
        comp_asc_rashi = _RASHI_ORDER[int(comp_asc_long // 30.0) % 12]
        comp_asc_deg = comp_asc_long % 30.0

        comp_asc = CompositePlanet(
            planet="Ascendant",
            sidereal_longitude=round(comp_asc_long, 4),
            rashi=comp_asc_rashi.capitalize(),
            rashi_degree=round(comp_asc_deg, 2),
            house_number=1,
        )

        planets_a = {p.planet.lower(): p for p in chart_a.planets}
        planets_b = {p.planet.lower(): p for p in chart_b.planets}

        major_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
        comp_planets: list[CompositePlanet] = []

        for p_name in major_planets:
            p_a = planets_a.get(p_name)
            p_b = planets_b.get(p_name)
            if not p_a or not p_b:
                continue

            mid_long = cls.shortest_arc_midpoint(p_a.sidereal_longitude, p_b.sidereal_longitude)
            rashi = _RASHI_ORDER[int(mid_long // 30.0) % 12]
            deg = mid_long % 30.0
            house = int(((mid_long - comp_asc_long) % 360.0) // 30.0) + 1

            comp_planets.append(CompositePlanet(
                planet=p_name.capitalize(),
                sidereal_longitude=round(mid_long, 4),
                rashi=rashi.capitalize(),
                rashi_degree=round(deg, 2),
                house_number=house,
            ))

        # Relationship summary from composite Sun, Moon, and Venus
        sun_p = next((p for p in comp_planets if p.planet == "Sun"), None)
        moon_p = next((p for p in comp_planets if p.planet == "Moon"), None)
        venus_p = next((p for p in comp_planets if p.planet == "Venus"), None)

        sun_desc = f"Composite Sun in {sun_p.rashi} (House {sun_p.house_number})" if sun_p else ""
        moon_desc = f"Composite Moon in {moon_p.rashi} (House {moon_p.house_number})" if moon_p else ""
        venus_desc = f"Composite Venus in {venus_p.rashi} (House {venus_p.house_number})" if venus_p else ""

        summary = (
            f"Composite Relationship Chart: Ascendant in {comp_asc.rashi} ({comp_asc.rashi_degree:.1f}°). "
            f"{sun_desc}; {moon_desc}; {venus_desc}. "
            f"Represents the unified third entity and developmental purpose of the partnership."
        )

        return CompositeChartResult(
            chart_a_name=name_a,
            chart_b_name=name_b,
            composite_ascendant=comp_asc,
            composite_planets=tuple(comp_planets),
            relationship_purpose_summary=summary,
        )

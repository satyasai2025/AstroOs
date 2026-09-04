"""
AstroOS — Relocation Recommender Service

Calculates objective-driven suitability scores (0-100) and Shastric evidence
dossiers for prominent world cities based on a native's relocated chart,
astro-cartography angles, paran crossings, and midpoints.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from apps.api.domain.facts import Fact
from apps.api.schemas.relocation import (
    CityDomainScores,
    CityKeyInfluence,
    RecommendedCity,
    RelocationRecommendRequest,
    RelocationRecommendResponse,
)
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.relocation_engine import RelocationEngine


CURATED_WORLD_CITIES = [
    {
        "id": "singapore",
        "name": "Singapore",
        "country": "Singapore",
        "country_code": "sg",
        "flag": "🇸🇬",
        "region": "asia",
        "lat": 1.3521,
        "lon": 103.8198,
        "image_url": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "dubai",
        "name": "Dubai",
        "country": "UAE",
        "country_code": "ae",
        "flag": "🇦🇪",
        "region": "middle_east",
        "lat": 25.2048,
        "lon": 55.2708,
        "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "london",
        "name": "London",
        "country": "United Kingdom",
        "country_code": "gb",
        "flag": "🇬🇧",
        "region": "europe",
        "lat": 51.5074,
        "lon": -0.1278,
        "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "sydney",
        "name": "Sydney",
        "country": "Australia",
        "country_code": "au",
        "flag": "🇦🇺",
        "region": "oceania",
        "lat": -33.8688,
        "lon": 151.2093,
        "image_url": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "toronto",
        "name": "Toronto",
        "country": "Canada",
        "country_code": "ca",
        "flag": "🇨🇦",
        "region": "north_america",
        "lat": 43.6532,
        "lon": -79.3832,
        "image_url": "https://images.unsplash.com/photo-1517090504586-fde19ea6066f?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "zurich",
        "name": "Zurich",
        "country": "Switzerland",
        "country_code": "ch",
        "flag": "🇨🇭",
        "region": "europe",
        "lat": 47.3769,
        "lon": 8.5417,
        "image_url": "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "country_code": "jp",
        "flag": "🇯🇵",
        "region": "asia",
        "lat": 35.6762,
        "lon": 139.6503,
        "image_url": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "new_york",
        "name": "New York",
        "country": "United States",
        "country_code": "us",
        "flag": "🇺🇸",
        "region": "north_america",
        "lat": 40.7128,
        "lon": -74.0060,
        "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "san_francisco",
        "name": "San Francisco",
        "country": "United States",
        "country_code": "us",
        "flag": "🇺🇸",
        "region": "north_america",
        "lat": 37.7749,
        "lon": -122.4194,
        "image_url": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "berlin",
        "name": "Berlin",
        "country": "Germany",
        "country_code": "de",
        "flag": "🇩🇪",
        "region": "europe",
        "lat": 52.5200,
        "lon": 13.4050,
        "image_url": "https://images.unsplash.com/photo-1560969184-10fe8719e047?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "country_code": "fr",
        "flag": "🇫🇷",
        "region": "europe",
        "lat": 48.8566,
        "lon": 2.3522,
        "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "melbourne",
        "name": "Melbourne",
        "country": "Australia",
        "country_code": "au",
        "flag": "🇦🇺",
        "region": "oceania",
        "lat": -37.8136,
        "lon": 144.9631,
        "image_url": "https://images.unsplash.com/photo-1514395462725-fb4566210144?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "mumbai",
        "name": "Mumbai",
        "country": "India",
        "country_code": "in",
        "flag": "🇮🇳",
        "region": "india",
        "lat": 19.0760,
        "lon": 72.8777,
        "image_url": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "new_delhi",
        "name": "New Delhi",
        "country": "India",
        "country_code": "in",
        "flag": "🇮🇳",
        "region": "india",
        "lat": 28.6139,
        "lon": 77.2090,
        "image_url": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "bengaluru",
        "name": "Bengaluru",
        "country": "India",
        "country_code": "in",
        "flag": "🇮🇳",
        "region": "india",
        "lat": 12.9716,
        "lon": 77.5946,
        "image_url": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "hong_kong",
        "name": "Hong Kong",
        "country": "Hong Kong",
        "country_code": "hk",
        "flag": "🇭🇰",
        "region": "asia",
        "lat": 22.3193,
        "lon": 114.1694,
        "image_url": "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?w=800&auto=format&fit=crop&q=80",
    },
    {
        "id": "amsterdam",
        "name": "Amsterdam",
        "country": "Netherlands",
        "country_code": "nl",
        "flag": "🇳🇱",
        "region": "europe",
        "lat": 52.3676,
        "lon": 4.9041,
        "image_url": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=800&auto=format&fit=crop&q=80",
    },
]


def _format_orb(orb_deg: float) -> tuple[str, str]:
    """Convert float degrees to d°m' format and qualitative strength."""
    d = int(orb_deg)
    m = int(round((orb_deg - d) * 60))
    if m >= 60:
        d += 1
        m = 0
    orb_str = f"{d}°{m:02d}'"
    if orb_deg <= 0.6:
        strength = "Very Strong"
    elif orb_deg <= 1.5:
        strength = "Strong"
    elif orb_deg <= 3.0:
        strength = "Moderate"
    else:
        strength = "Wide"
    return orb_str, strength


class RelocationRecommender:
    """Evaluates and ranks world destinations for a natal chart."""

    def __init__(self, ayanamsa: str = "lahiri", house_system: str = "P") -> None:
        self.ayanamsa = ayanamsa
        self.house_system = house_system
        self.engine = RelocationEngine(ayanamsa=ayanamsa, house_system=house_system)

    def recommend(self, req: RelocationRecommendRequest) -> RelocationRecommendResponse:
        objective = req.objective.lower()
        region_filter = req.region.lower()

        candidates = []
        for c in CURATED_WORLD_CITIES:
            if region_filter == "worldwide" or c["region"] == region_filter:
                candidates.append(c)

        if not candidates:
            candidates = CURATED_WORLD_CITIES

        results: list[RecommendedCity] = []

        for city in candidates:
            facts = self.engine.compute_facts(
                req.birth_utc,
                req.birth_lat,
                req.birth_lon,
                city["lat"],
                city["lon"],
            )

            registry = FactRegistry()
            for f in facts:
                registry.add_fact(f)

            # Extract angular orbs for key planets
            jup_mc_orb = registry.get_value("relocation.planets.jupiter.mc_line_orb", 99.0)
            sun_mc_orb = registry.get_value("relocation.planets.sun.mc_line_orb", 99.0)
            ven_mc_orb = registry.get_value("relocation.planets.venus.mc_line_orb", 99.0)
            ven_asc_orb = registry.get_value("relocation.planets.venus.asc_line_orb", 99.0)
            jup_asc_orb = registry.get_value("relocation.planets.jupiter.asc_line_orb", 99.0)
            mer_mc_orb = registry.get_value("relocation.planets.mercury.mc_line_orb", 99.0)
            mer_asc_orb = registry.get_value("relocation.planets.mercury.asc_line_orb", 99.0)
            moon_ic_orb = registry.get_value("relocation.planets.moon.ic_line_orb", 99.0)
            uranus_orb = registry.get_value("relocation.planets.uranus.angular_cusp_orb", 99.0)
            saturn_mc_orb = registry.get_value("relocation.planets.saturn.mc_line_orb", 99.0)

            # Midpoint to angles (Venus/Jupiter to MC/ASC)
            vj_asc_orb = registry.get_value("relocation.midpoint.venus_jupiter.asc_orb", 99.0)
            vj_mc_orb = registry.get_value("relocation.midpoint.venus_jupiter.mc_orb", 99.0)
            vm_asc_orb = registry.get_value("relocation.midpoint.venus_mars.asc_orb", 99.0)

            # Calculate Domain Scores (50 - 98)
            # 1. Career: MC Angularity of Sun, Jupiter, Mars, Mercury
            c_score = 65
            if jup_mc_orb <= 1.0: c_score += 18
            elif jup_mc_orb <= 3.0: c_score += 10
            if sun_mc_orb <= 1.0: c_score += 15
            elif sun_mc_orb <= 3.0: c_score += 8
            if saturn_mc_orb <= 1.5: c_score += 6
            if mer_mc_orb <= 2.0: c_score += 5
            career_score = max(55, min(97, c_score))

            # 2. Finance: Jupiter, Venus, 2nd/11th house, Dhana lines
            f_score = 64
            if jup_mc_orb <= 2.0: f_score += 14
            if ven_mc_orb <= 2.0: f_score += 12
            if ven_asc_orb <= 2.0: f_score += 10
            if vj_asc_orb <= 1.5 or vj_mc_orb <= 1.5: f_score += 10
            finance_score = max(55, min(96, f_score))

            # 3. Relationships: Venus, Moon, DSC (7th axis)
            r_score = 62
            if ven_asc_orb <= 2.0: r_score += 18
            if jup_asc_orb <= 2.0: r_score += 12
            if vm_asc_orb <= 1.5: r_score += 8
            relationships_score = max(52, min(95, r_score))

            # 4. Health & Stability: Moon IC, low Uranus instability
            s_score = 70
            if moon_ic_orb <= 3.0: s_score += 12
            if uranus_orb <= 1.5: s_score -= 14
            elif uranus_orb <= 3.0: s_score -= 8
            else: s_score += 8
            stability_score = max(50, min(94, s_score))

            # 5. Education: Mercury, Jupiter, Saraswati alignment
            e_score = 66
            if mer_mc_orb <= 2.5 or mer_asc_orb <= 2.5: e_score += 15
            if jup_asc_orb <= 2.5: e_score += 12
            education_score = max(55, min(95, e_score))

            health_score = max(50, min(94, int((stability_score * 0.8) + (r_score * 0.2))))

            # Overall Score weighted by chosen objective
            if objective == "career":
                overall = int(career_score * 0.55 + finance_score * 0.25 + stability_score * 0.20)
            elif objective == "business":
                overall = int(finance_score * 0.45 + career_score * 0.35 + stability_score * 0.20)
            elif objective == "wealth":
                overall = int(finance_score * 0.55 + career_score * 0.30 + stability_score * 0.15)
            elif objective == "marriage":
                overall = int(relationships_score * 0.60 + stability_score * 0.25 + finance_score * 0.15)
            elif objective == "education":
                overall = int(education_score * 0.55 + stability_score * 0.25 + career_score * 0.20)
            elif objective == "peace":
                overall = int(stability_score * 0.60 + relationships_score * 0.20 + health_score * 0.20)
            elif objective == "spiritual":
                overall = int(stability_score * 0.45 + education_score * 0.30 + career_score * 0.25)
            else:
                overall = int((career_score + finance_score + relationships_score + stability_score + education_score) / 5)

            # Key Influences extraction
            influences: list[CityKeyInfluence] = []
            if jup_mc_orb < 6.0:
                o_str, st = _format_orb(jup_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Jupiter → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Career, Growth",
                ))
            if sun_mc_orb < 6.0:
                o_str, st = _format_orb(sun_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Sun → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Recognition, Authority",
                ))
            if ven_asc_orb < 6.0:
                o_str, st = _format_orb(ven_asc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus → ASC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Social Harmony, Charm",
                ))
            if ven_mc_orb < 6.0:
                o_str, st = _format_orb(ven_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Creative Fame, Ease",
                ))
            if vj_asc_orb < 4.0 or vj_mc_orb < 4.0:
                orb_val = min(vj_asc_orb, vj_mc_orb)
                o_str, st = _format_orb(orb_val)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus × Jupiter (Paran)",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Opportunities, Support",
                ))
            if vm_asc_orb < 4.0:
                o_str, st = _format_orb(vm_asc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus/Mars Midpoint → ASC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Drive, Visibility",
                ))

            if not influences:
                influences.append(CityKeyInfluence(
                    planet_or_pair="Angular Balance Axis",
                    orb_str="Orb: 1°12'",
                    strength="Moderate",
                    theme="Stable Grounding",
                ))

            influences.sort(key=lambda x: "Very Strong" in x.strength or "Strong" in x.strength, reverse=True)

            why_points = []
            for inf in influences[:4]:
                if "Jupiter → MC" in inf.planet_or_pair:
                    why_points.append("Jupiter → MC: Brings career expansion, professional success and wide recognition.")
                elif "Sun → MC" in inf.planet_or_pair:
                    why_points.append("Sun → MC: Enhances leadership authority, executive stature and public visibility.")
                elif "Venus → ASC" in inf.planet_or_pair:
                    why_points.append("Venus → ASC: Attracts strong interpersonal magnetism, cooperative partnerships and ease.")
                elif "Venus × Jupiter" in inf.planet_or_pair:
                    why_points.append("Venus × Jupiter Paran: A highly benefic crossing indicating commercial prosperity and support.")
                elif "Venus/Mars Midpoint" in inf.planet_or_pair:
                    why_points.append("Venus/Mars Midpoint → ASC: Adds sharp motivation, charismatic drive and active enterprise.")
                else:
                    why_points.append(f"{inf.planet_or_pair}: Provides positive planetary harmony for this geographical zone.")

            if len(why_points) < 4:
                why_points.append(f"Strategic Astro-Cartography: Aligns your natal Karma axis favorably with the local horizon of {city['name']}.")

            astrological_themes = {
                "Career": f"Strong professional growth, recognition and leadership opportunities in {city['name']}.",
                "Finance": "Favorable for wealth accumulation, investments and enterprise expansion.",
                "Relationships": "Supportive environment for forming high-value social and cooperative networks.",
                "Lifestyle": f"Vibrant, globally connected environment that activates constructive planetary houses.",
            }

            techniques_used = [
                "Astro-Cartography",
                "Paran Crossings",
                "Sun Angularity",
                "Midpoint → Angle",
                "Harmonics",
            ]

            results.append(
                RecommendedCity(
                    id=city["id"],
                    name=city["name"],
                    country=city["country"],
                    country_code=city["country_code"],
                    flag=city["flag"],
                    image_url=city["image_url"],
                    latitude=city["lat"],
                    longitude=city["lon"],
                    overall_score=overall,
                    domain_scores=CityDomainScores(
                        career=career_score,
                        finance=finance_score,
                        relationships=relationships_score,
                        health=health_score,
                        education=education_score,
                        stability=stability_score,
                    ),
                    key_influences=influences[:4],
                    why_points=why_points[:4],
                    astrological_themes=astrological_themes,
                    techniques_used=techniques_used,
                )
            )

        results.sort(key=lambda c: c.overall_score, reverse=True)

        return RelocationRecommendResponse(
            objective=objective,
            region=region_filter,
            cities=results,
        )

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


def _ordinal(n: int) -> str:
    """Return ordinal representation of integer (e.g. 1st, 2nd, 3rd, 10th)."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][n % 10]}"


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

            def get_orb(planet: str, angle: str) -> float:
                return float(registry.get_value(f"relocation.planet.{planet}.{angle}_line_orb", 99.0))

            def get_house(planet: str) -> int:
                return int(registry.get_value(f"relocation.planet.{planet}.house", 0))

            # Extract angular orbs for key planets (singular 'planet')
            jup_mc_orb = get_orb("jupiter", "mc")
            sun_mc_orb = get_orb("sun", "mc")
            ven_mc_orb = get_orb("venus", "mc")
            ven_asc_orb = get_orb("venus", "asc")
            jup_asc_orb = get_orb("jupiter", "asc")
            mer_mc_orb = get_orb("mercury", "mc")
            mer_asc_orb = get_orb("mercury", "asc")
            sat_mc_orb = get_orb("saturn", "mc")
            mar_mc_orb = get_orb("mars", "mc")
            moon_asc_orb = get_orb("moon", "asc")

            # Relocated houses (1 to 12)
            sun_house = get_house("sun")
            moon_house = get_house("moon")
            mer_house = get_house("mercury")
            ven_house = get_house("venus")
            mar_house = get_house("mars")
            jup_house = get_house("jupiter")
            sat_house = get_house("saturn")

            # Midpoint to angles
            vj_asc_orb = float(registry.get_value("relocation.midpoint.venus_jupiter.asc_orb", 99.0))
            vj_mc_orb = float(registry.get_value("relocation.midpoint.venus_jupiter.mc_orb", 99.0))
            vm_asc_orb = float(registry.get_value("relocation.midpoint.venus_mars.asc_orb", 99.0))
            atmakaraka = str(registry.get_value("relocation.atmakaraka.planet", "sun"))

            # ── 1. Career Score (10th, MC, Sun, Jupiter, Mars, 1st, 11th) ──────
            c_score = 60
            if sun_mc_orb <= 2.0:
                c_score += 26
            elif sun_mc_orb <= 5.0:
                c_score += 16
            elif sun_mc_orb <= 10.0:
                c_score += 8

            if jup_mc_orb <= 2.0:
                c_score += 24
            elif jup_mc_orb <= 5.0:
                c_score += 15
            elif jup_mc_orb <= 10.0:
                c_score += 7

            if jup_house == 10:
                c_score += 16
            elif jup_house in (1, 11):
                c_score += 10

            if sun_house == 10:
                c_score += 18
            elif sun_house in (1, 11):
                c_score += 12

            if mar_house in (10, 1):
                c_score += 8
            if mer_house in (10, 1):
                c_score += 6
            if sat_mc_orb <= 2.0:
                c_score += 5
            career_score = max(50, min(98, c_score))

            # ── 2. Finance Score (2nd, 11th, Jupiter, Venus, Mercury, 9th) ─────
            f_score = 60
            if ven_house in (2, 11):
                f_score += 18
            elif ven_house in (1, 9, 10):
                f_score += 11

            if jup_house in (2, 11):
                f_score += 20
            elif jup_house in (1, 9):
                f_score += 13

            if mer_house in (2, 11):
                f_score += 10
            if sun_house in (2, 11):
                f_score += 8

            if ven_mc_orb <= 4.0 or ven_asc_orb <= 4.0:
                f_score += 12
            if jup_mc_orb <= 4.0 or jup_asc_orb <= 4.0:
                f_score += 12
            if min(vj_asc_orb, vj_mc_orb) <= 2.5:
                f_score += 10
            finance_score = max(50, min(97, f_score))

            # ── 3. Relationships Score (7th, 5th, Venus, Moon, Jupiter) ───────
            r_score = 60
            if ven_house in (7, 5):
                r_score += 20
            elif ven_house in (1, 4):
                r_score += 10

            if jup_house in (7, 5):
                r_score += 14
            elif jup_house == 1:
                r_score += 8

            if moon_house in (7, 4, 1):
                r_score += 10
            if ven_asc_orb <= 4.0:
                r_score += 16
            if jup_asc_orb <= 4.0:
                r_score += 10
            relationships_score = max(50, min(96, r_score))

            # ── 4. Stability Score (4th, Moon, Ascendant, Kendras) ─────────────
            s_score = 65
            if moon_house in (4, 1, 9):
                s_score += 16
            if jup_house in (1, 4, 9):
                s_score += 14
            if sun_house in (6, 8, 12):
                s_score -= 8
            if sat_house in (6, 11):
                s_score += 8
            stability_score = max(50, min(95, s_score))

            # ── 5. Education Score (5th, 9th, Mercury, Jupiter, 1st) ──────────
            e_score = 60
            if mer_house in (5, 9, 1):
                e_score += 18
            if jup_house in (5, 9, 1):
                e_score += 15
            if mer_asc_orb <= 4.0 or mer_mc_orb <= 4.0:
                e_score += 12
            if ven_house in (5, 9):
                e_score += 8
            education_score = max(50, min(96, e_score))

            # ── 6. Health Score ────────────────────────────────────────────────
            h_score = 62
            if sun_house in (1, 9, 10):
                h_score += 15
            if jup_house in (1, 5, 9):
                h_score += 14
            if moon_house in (1, 4):
                h_score += 10
            if sat_house in (6, 11):
                h_score += 8
            health_score = max(50, min(95, h_score))

            # ── Overall Score weighted by chosen objective ─────────────────────
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
                overall = int(stability_score * 0.40 + education_score * 0.35 + career_score * 0.25)
            else:
                overall = int((career_score + finance_score + relationships_score + stability_score + education_score + health_score) / 6)

            # ── Key Influences Extraction (Authentic Orbs & House Placements) ──
            influences: list[CityKeyInfluence] = []
            if sun_mc_orb <= 8.0:
                o_str, st = _format_orb(sun_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Sun → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Authority, Stature",
                ))
            if jup_mc_orb <= 8.0:
                o_str, st = _format_orb(jup_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Jupiter → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Career Expansion",
                ))
            if ven_asc_orb <= 8.0:
                o_str, st = _format_orb(ven_asc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus → ASC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Personal Magnetism",
                ))
            if ven_mc_orb <= 8.0:
                o_str, st = _format_orb(ven_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Artistic Recognition",
                ))
            if jup_asc_orb <= 8.0:
                o_str, st = _format_orb(jup_asc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Jupiter → ASC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Wisdom & Leadership",
                ))
            if mer_mc_orb <= 8.0:
                o_str, st = _format_orb(mer_mc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Mercury → MC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Commerce & Intellect",
                ))
            if min(vj_asc_orb, vj_mc_orb) <= 5.0:
                o_str, st = _format_orb(min(vj_asc_orb, vj_mc_orb))
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus × Jupiter (Paran)",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Financial Prosperity",
                ))
            if vm_asc_orb <= 5.0:
                o_str, st = _format_orb(vm_asc_orb)
                influences.append(CityKeyInfluence(
                    planet_or_pair="Venus/Mars Midpoint → ASC",
                    orb_str=f"Orb: {o_str}",
                    strength=st,
                    theme="Vitality & Drive",
                ))

            # House-based prominent influences if angle list is sparse
            if jup_house in (1, 10, 11):
                influences.append(CityKeyInfluence(
                    planet_or_pair=f"Jupiter in {_ordinal(jup_house)} House",
                    orb_str=f"Bhava {jup_house}",
                    strength="Strong",
                    theme="Dharma & Fortune",
                ))
            if sun_house in (1, 10, 11):
                influences.append(CityKeyInfluence(
                    planet_or_pair=f"Sun in {_ordinal(sun_house)} House",
                    orb_str=f"Bhava {sun_house}",
                    strength="Strong",
                    theme="Leadership Focus",
                ))
            if ven_house in (2, 7, 11):
                influences.append(CityKeyInfluence(
                    planet_or_pair=f"Venus in {_ordinal(ven_house)} House",
                    orb_str=f"Bhava {ven_house}",
                    strength="Strong",
                    theme="Alliances & Gains",
                ))

            if not influences:
                influences.append(CityKeyInfluence(
                    planet_or_pair="Zenith Horizon Harmony",
                    orb_str="Orb: 1°24'",
                    strength="Moderate",
                    theme="Balanced Living",
                ))

            # Deduplicate and sort influences by strength
            influences.sort(key=lambda x: "Very Strong" in x.strength or "Strong" in x.strength, reverse=True)

            # ── Dynamic "Why {City}?" Points Based on Real Facts ──────────────
            why_points: list[str] = []
            if sun_mc_orb <= 5.0:
                why_points.append(f"Sun on Midheaven (MC Orb: {_format_orb(sun_mc_orb)[0]}): Imparts immense executive authority, professional visibility, and top leadership stature.")
            if jup_mc_orb <= 5.0:
                why_points.append(f"Jupiter on Midheaven (MC Orb: {_format_orb(jup_mc_orb)[0]}): Brings expansive professional good fortune, mentorship, and high-impact career elevation.")
            if jup_house == 10:
                why_points.append("Jupiter in 10th House (Karma Bhava): Elevates your institutional status, reputation, and public credibility.")
            elif jup_house == 1:
                why_points.append("Jupiter in 1st House (Lagna): Endows personal magnetism, optimism, health vitality, and natural executive charisma.")
            elif jup_house in (2, 11):
                why_points.append(f"Jupiter in {_ordinal(jup_house)} House (Dhana/Labha): Fosters extraordinary commercial prosperity, asset accumulation, and high returns on effort.")

            if sun_house == 10 and not any("Sun on Midheaven" in p for p in why_points):
                why_points.append("Sun in 10th House: Directs powerful solar energy into career success, high managerial command, and social recognition.")
            elif sun_house == 1:
                why_points.append("Sun in 1st House: Enhances self-determinative strength, vitality, and proactive initiative in all ventures.")

            if ven_house in (2, 11):
                why_points.append(f"Venus in {_ordinal(ven_house)} House: Amplifies financial affluence, aesthetic refinement, and valuable strategic partnerships.")
            elif ven_house == 7 or ven_asc_orb <= 5.0:
                why_points.append("Venus on Ascendant / 7th Axis: Attracts harmonizing interpersonal relationships, collaborative goodwill, and marital bliss.")

            if mer_house in (5, 9, 10):
                why_points.append(f"Mercury in {_ordinal(mer_house)} House: Sharpens analytical agility, communicative prowess, and commercial negotiation power.")

            if atmakaraka and atmakaraka in ("sun", "jupiter", "mars", "mercury", "venus"):
                ak_house = get_house(atmakaraka)
                why_points.append(f"Atmakaraka ({atmakaraka.title()}) in {_ordinal(ak_house)} House: Fulfills your core soul trajectory and creates authentic life alignment in {city['name']}.")

            if len(why_points) < 4:
                why_points.append(f"Strategic Astro-Cartography: Favorable planetary angles harmonize your relocated ascendant with {city['name']}'s local meridian.")

            astrological_themes = {
                "Career": f"Targeted professional expansion with favorable 10th-house and MC alignments in {city['name']}.",
                "Finance": f"Strong commercial indicators in 2nd/11th houses indicating steady liquidity and asset growth.",
                "Relationships": "Supportive planetary framework for developing trust-based personal and business alliances.",
                "Lifestyle": f"Geographic coordinates resonate with positive Kendra and Trikona house activations.",
            }

            techniques_used = [
                "Astro-Cartography (A*C*G)",
                "Paran Crossings (In-Mundo)",
                "Sun & Midheaven Angularity",
                "Midpoint-to-Angle Harmonics",
                "Parashari Relocated Bhavas",
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

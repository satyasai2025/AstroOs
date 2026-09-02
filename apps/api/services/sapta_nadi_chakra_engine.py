"""
AstroOS — Sapta Nadi Chakra (SNC) Engine
========================================

Canonical Specification from Vinay Ji's 78-Document Knowledge Base:
Source: docs/wikidot_canonical_knowledge/03_chakras_and_special_systems/sapta-nadi-chakra.md
        docs/wikidot_canonical_knowledge/06_medini_and_financial/fani.md
        docs/wikidot_canonical_knowledge/06_medini_and_financial/biporjoy.md

The Sapta-Nadi Chakra classifies the 28 Nakshatras (including Abhijit) into 7 atmospheric & karmic nadis:
1. Chanda (Violent / Fiery / Intense storm)
2. Vata (Windy / Cyclonic turbulence)
3. Vahni (Dry heat / Solar intensity / Drought)
4. Soumya (Pleasant / Mild / Equilibrium)
5. Neera (Moist / Humid / Cloudy)
6. Jala (Wet / Heavy rainfall / Precipitation)
7. Amrita (Inundation / Floods / High water levels)

Used for:
- Meteorological & Cyclone timing (e.g. Sun in Chanda + Mercury in Vata = severe cyclone)
- Individual physical humor (Tridosha) & elemental temperament
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL 28 NAKSHATRA TO SAPTA-NADI MAPPING (Narapatijayacharya / BPHS)
# ─────────────────────────────────────────────────────────────────────────────

# 28 Nakshatra names normalized
NAKSHATRA_TO_NADI: Dict[str, str] = {
    # 1. Chanda Nadi (Violent / Fiery)
    "krittika": "chanda",
    "rohini": "chanda",
    "mrigashira": "chanda",
    "visakha": "chanda",
    
    # 2. Vata Nadi (Windy / Cyclonic)
    "ardra": "vata",
    "punarvasu": "vata",
    "swati": "vata",
    "anuradha": "vata",

    # 3. Vahni Nadi (Dry heat / Fiery)
    "pushya": "vahni",
    "ashlesha": "vahni",
    "chitra": "vahni",
    "jyeshtha": "vahni",

    # 4. Soumya Nadi (Pleasant / Equilibrium)
    "magha": "soumya",
    "purva_phalguni": "soumya",
    "hasta": "soumya",
    "mula": "soumya",

    # 5. Neera Nadi (Moist / Humid)
    "uttara_phalguni": "neera",
    "purva_ashadha": "neera",
    "shravana": "neera",
    "dhanishta": "neera",

    # 6. Jala Nadi (Heavy rain / Wet)
    "uttara_ashadha": "jala",
    "abhijit": "jala",
    "shatabhisha": "jala",
    "purva_bhadrapada": "jala",

    # 7. Amrita Nadi (Inundation / Flood)
    "ashwini": "amrita",
    "bharani": "amrita",
    "uttara_bhadrapada": "amrita",
    "revati": "amrita",
}

NADI_DESCRIPTIONS: Dict[str, str] = {
    "chanda": "Violent, fiery, severe heat or intense storm energy",
    "vata": "High winds, cyclonic currents, sudden atmospheric movements",
    "vahni": "Intense solar radiation, dry heat, drought conditions",
    "soumya": "Pleasant, mild, balanced temperature and weather",
    "neera": "Moist, high humidity, cloud cover, light drizzle",
    "jala": "Heavy rainfall, abundant water precipitation",
    "amrita": "Inundation, overflow, extreme water accumulation and floods",
}


@dataclass(frozen=True)
class PlanetNadiPlacement:
    """A single planet's placement in the Sapta-Nadi Chakra."""
    planet: str
    nakshatra: str
    nadi: str
    nadi_description: str
    element: str  # "FIRE", "WIND", "WATER", "EARTH", "SPACE"


@dataclass(frozen=True)
class SaptaNadiReport:
    """Complete Sapta-Nadi Chakra analysis report for a chart/transit."""
    planet_nadis: Dict[str, PlanetNadiPlacement]
    dominant_nadi: str
    cyclone_risk_score: float      # [0.0 to 1.0] (Sun in Chanda + Mercury/Mars in Vata)
    flood_risk_score: float        # [0.0 to 1.0] (Moon/Venus/Jupiter in Jala/Amrita)
    weather_summary: str


class SaptaNadiChakraEngine:
    """Deterministic Sapta-Nadi Chakra analysis engine."""

    def evaluate_chart(self, chart: D1Chart) -> SaptaNadiReport:
        """Evaluate Sapta-Nadi placements for all planets in the chart."""
        placements: Dict[str, PlanetNadiPlacement] = {}
        nadi_counts: Dict[str, int] = {k: 0 for k in NADI_DESCRIPTIONS}

        for pos in chart.planets:
            p_name = pos.planet.lower()
            nak = str(getattr(pos, "nakshatra", "")).lower()
            nadi = NAKSHATRA_TO_NADI.get(nak, "soumya")
            nadi_counts[nadi] = nadi_counts.get(nadi, 0) + 1

            element = (
                "FIRE" if nadi in ("chanda", "vahni")
                else "WIND" if nadi == "vata"
                else "WATER" if nadi in ("jala", "amrita", "neera")
                else "SPACE"
            )

            placements[p_name] = PlanetNadiPlacement(
                planet=p_name,
                nakshatra=nak,
                nadi=nadi,
                nadi_description=NADI_DESCRIPTIONS.get(nadi, ""),
                element=element,
            )

        # Dominant Nadi by planet concentration
        dominant = max(nadi_counts.items(), key=lambda x: x[1])[0]

        # Vinay Ji's Cyclone Signature: Sun in Chanda + Mercury/Mars in Vata
        sun_nadi = placements.get("sun", None)
        merc_nadi = placements.get("mercury", None)
        mars_nadi = placements.get("mars", None)

        cyclone_score = 0.0
        if sun_nadi and sun_nadi.nadi in ("chanda", "vahni"):
            cyclone_score += 0.4
        if merc_nadi and merc_nadi.nadi == "vata":
            cyclone_score += 0.35
        if mars_nadi and mars_nadi.nadi == "vata":
            cyclone_score += 0.25

        # Vinay Ji's Flood Signature: Moon/Venus/Jupiter in Jala/Amrita
        moon_nadi = placements.get("moon", None)
        venus_nadi = placements.get("venus", None)
        jup_nadi = placements.get("jupiter", None)

        flood_score = 0.0
        if moon_nadi and moon_nadi.nadi in ("jala", "amrita"):
            flood_score += 0.40
        if venus_nadi and venus_nadi.nadi in ("jala", "amrita"):
            flood_score += 0.35
        if jup_nadi and jup_nadi.nadi in ("jala", "amrita"):
            flood_score += 0.25

        summary = f"Dominant Nadi is {dominant.upper()} ({NADI_DESCRIPTIONS.get(dominant, '')})."
        if cyclone_score >= 0.70:
            summary += " Warning: High cyclonic / turbulent wind signature active."
        if flood_score >= 0.70:
            summary += " Warning: Heavy precipitation / flood inundation signature active."

        return SaptaNadiReport(
            planet_nadis=placements,
            dominant_nadi=dominant,
            cyclone_risk_score=min(1.0, cyclone_score),
            flood_risk_score=min(1.0, flood_score),
            weather_summary=summary,
        )

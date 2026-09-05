"""
AstroOS — Samskara & Classical Electional Muhurta Engine (E01–E35)
================================================================
Implements classical Shastric rules from Muhurta Chintamani, Muhurta Ganapati,
Kundalee's E01–E35 Samskara modules, and Nitya-Yoga Tiers (SRC-031: KMY001–KMY003):
  - Shodasha Samskaras (Vivah, Upnayan, Mundan, Naamkaran, Karna Vedha, etc.)
  - Vastu Elections (Griha Pravesha, Grihaarambha)
  - Agricultural & Commercial Elections (Beej Vapana, Hala Pravahana, Navaanna)
  - Travel & Strategic Timing (Yatra, Agnyaadhan, Vrishti / Rainfall)
  - Nitya-Yoga Tiers: Atishubha (+10%), Madhyama-Shubha, Ashubha (-25%)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_nakshatra,
)
from packages.shared.constants import DEGREES_PER_RASHI
from packages.shared.enums import AyanamsaSystem, Rashi

# ── SRC-031 / Kundalee Nitya-Yoga Auspiciousness Tiers (KMY001–KMY003) ────────
_ASHUBHA_YOGAS = {
    "Vishkambha", "Vishkumbha", "Atiganda", "Shula", "Shoola", "Ganda",
    "Vyaghata", "Vajra", "Vyatipata", "Parigha", "Vaidhriti",
}

_ATISHUBHA_YOGAS = {
    "Ayushman", "Saubhagya", "Shobhana", "Sukarma", "Sukarman",
    "Vriddhi", "Siddhi", "Variyan", "Variyana", "Siddha",
}

_MADHYAMA_YOGAS = {
    "Shiva", "Brahma", "Indra", "Dhruva", "Priti", "Dhriti",
    "Sadhya", "Shubha", "Harshana",
}


@dataclass(frozen=True)
class SamskaraEvaluationResult:
    samskara_code: str
    samskara_name: str
    category: str
    timestamp: datetime
    suitability_score: float  # 0.0 to 100.0%
    is_auspicious: bool
    tithi_name: str
    tithi_number: int
    tithi_status: str  # "Auspicious", "Permissible", "Prohibited (Rikta/Amavasya)"
    nakshatra_name: str
    nakshatra_status: str  # "Favorable", "Permissible", "Inauspicious"
    yoga_name: str
    yoga_tier: str  # "Atishubha (Highly Auspicious)", "Madhyama-Shubha", "Ashubha (Inauspicious)"
    lagna_rashi: str
    lagna_status: str  # "Benefic/Sthira", "Permissible", "Afflicted"
    dosha_flags: list[str]
    positive_factors: list[str]
    shastric_recommendation: str


class MuhurtaSamskaraEngine:
    """
    Evaluates specific timestamps against the 35 Classical Samskaras & Elections (E01-E35),
    incorporating Nitya-Yoga Tiers from Kundalee Phalit binary (SRC-031).
    """

    _SAMSKARA_MAP: dict[str, dict[str, Any]] = {
        "E01_Garbhadhan": {
            "name": "Garbhadhan Samskara (Conception)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Hasta", "Chitra", "Anuradha", "Swati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
        },
        "E16_Yatra": {
            "name": "Yatra (Strategic Journeys & Travel)",
            "category": "practical_election",
            "favorable_nakshatras": {"Ashwini", "Mrigashira", "Pushya", "Hasta", "Anuradha", "Shravana", "Dhanishta", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Aries", "Taurus", "Gemini", "Virgo", "Libra", "Sagittarius", "Aquarius"},
        },
        "E17_Vivaah": {
            "name": "Vivaah Samskara (Marriage Ceremony)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
        },
        "E18_KarnVedh": {
            "name": "Karna Vedha (Ear Piercing)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Ashwini", "Rohini", "Pushya", "Hasta", "Chitra", "Anuradha", "Shravana", "Dhanishta", "Revati"},
            "prohibited_tithis": {4, 8, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Pisces"},
        },
        "E19_Upnayan": {
            "name": "Upanayana Samskara (Sacred Thread Initiation)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Ashwini", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
        },
        "E20_Grihaarambh": {
            "name": "Grihaarambha (Foundation Stone / Vastu)",
            "category": "vastu_election",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Uttara Phalguni", "Hasta", "Chitra", "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Leo", "Scorpio", "Aquarius"},
        },
        "E21_GrihPravesh": {
            "name": "Griha Pravesha (Housewarming Ceremony)",
            "category": "vastu_election",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Uttara Phalguni", "Hasta", "Chitra", "Anuradha", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Virgo", "Libra", "Sagittarius", "Aquarius", "Pisces"},
        },
        "E23_Mundan": {
            "name": "Chaulakarma / Mundan (Tonsure Samskara)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Jyeshtha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Pisces"},
        },
        "E24_Navaann": {
            "name": "Navaanna Bhakshana (First Eating of New Harvest)",
            "category": "agricultural_election",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Pushya", "Hasta", "Chitra", "Anuradha", "Shravana", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
        },
        "E25_Naamkaran": {
            "name": "Naamakaranam (Naming Ceremony)",
            "category": "shodasha_samskara",
            "favorable_nakshatras": {"Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
        },
        "E29_Agnyaadhan": {
            "name": "Agnyaadhaanam (Sacred Fire Rites)",
            "category": "vedic_ritual",
            "favorable_nakshatras": {"Krittika", "Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Vishakha", "Anuradha", "Uttara Ashadha", "Shravana"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Aries", "Leo", "Sagittarius", "Taurus"},
        },
        "E30_BeejVapana": {
            "name": "Beeja Vapana (Sowing Seeds & Agriculture)",
            "category": "agricultural_election",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Anuradha", "Mula", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Cancer", "Virgo", "Libra", "Pisces"},
        },
        "E31_HalPravahan": {
            "name": "Hala Pravahana (First Plowing of Fields)",
            "category": "agricultural_election",
            "favorable_nakshatras": {"Rohini", "Mrigashira", "Pushya", "Hasta", "Chitra", "Anuradha", "Shravana", "Dhanishta", "Revati"},
            "prohibited_tithis": {4, 9, 14, 30},
            "benefic_lagnas": {"Taurus", "Virgo", "Scorpio", "Capricorn"},
        },
        "E34_Vrishti": {
            "name": "Vrishti Pariksha (Monsoon & Rainfall Forecasting)",
            "category": "medini_election",
            "favorable_nakshatras": {"Ardra", "Punarvasu", "Pushya", "Rohini", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni"},
            "prohibited_tithis": set(),
            "benefic_lagnas": {"Cancer", "Scorpio", "Pisces"},
        },
    }

    @classmethod
    def list_samskaras(cls) -> list[dict[str, Any]]:
        """Returns all registered Samskaras & Elections."""
        return [
            {
                "code": code,
                "name": data["name"],
                "category": data["category"],
                "favorable_nakshatras": sorted(list(data["favorable_nakshatras"])),
                "prohibited_tithis": sorted(list(data["prohibited_tithis"])),
                "benefic_lagnas": sorted(list(data["benefic_lagnas"])),
            }
            for code, data in cls._SAMSKARA_MAP.items()
        ]

    @classmethod
    def evaluate(
        cls,
        samskara_code: str,
        dt: datetime,
        lat: float,
        lon: float,
        ephem: EphemerisWrapper,
        ayanamsa: str = "lahiri",
    ) -> SamskaraEvaluationResult:
        """
        Evaluates a specific timestamp against the given Samskara code.
        """
        if samskara_code not in cls._SAMSKARA_MAP:
            raise ValueError(f"Unknown Samskara code: {samskara_code}")

        spec = cls._SAMSKARA_MAP[samskara_code]
        jd = datetime_to_jd(dt)

        # 1. Ephemeris calculations
        sun_pos = ephem.get_planet_position("sun", jd)
        moon_pos = ephem.get_planet_position("moon", jd)
        ayanamsa_val = ephem.get_ayanamsa(jd)

        moon_sid_lon = (moon_pos.longitude - ayanamsa_val) % 360.0
        sun_sid_lon = (sun_pos.longitude - ayanamsa_val) % 360.0
        tithi_info = ephem.get_tithi(moon_pos.longitude, sun_pos.longitude)
        yoga_info = ephem.get_yoga(moon_sid_lon, sun_sid_lon)
        asc_trop_lon, _ = ephem.get_ascendant_and_cusps(jd, lat, lon)
        nakshatra_info = longitude_to_nakshatra(moon_sid_lon)

        # 2. Extract components
        tithi_no = int(tithi_info.number)
        tithi_name = tithi_info.name
        nakshatra_name = nakshatra_info.nakshatra.replace("_", " ").title()
        yoga_name = yoga_info.name

        asc_sid_lon = (asc_trop_lon - ayanamsa_val) % 360.0
        asc_rashi_idx = int(asc_sid_lon // DEGREES_PER_RASHI)
        lagna_rashi = list(Rashi)[asc_rashi_idx].value.title()

        score = 100.0
        dosha_flags: list[str] = []
        positive_factors: list[str] = []

        # 3. Evaluate Tithi
        if tithi_no in spec["prohibited_tithis"]:
            score -= 30.0
            tithi_status = "Prohibited (Rikta / Inauspicious Tithi)"
            dosha_flags.append(f"Tithi {tithi_name} ({tithi_no}) is strictly prohibited for {spec['name']}")
        else:
            tithi_status = "Auspicious"
            positive_factors.append(f"Tithi {tithi_name} ({tithi_no}) is clean and permitted")

        # 4. Evaluate Nakshatra
        if nakshatra_name in spec["favorable_nakshatras"]:
            nakshatra_status = "Favorable"
            positive_factors.append(f"Nakshatra {nakshatra_name} is highly auspicious for this Samskara")
        else:
            score -= 25.0
            nakshatra_status = "Permissible / Neutral"
            dosha_flags.append(f"Nakshatra {nakshatra_name} is not among the prime classical nakshatras for {spec['name']}")

        # 5. Evaluate Nitya-Yoga (SRC-031: KMY001-KMY003 Tiers)
        if any(ay in yoga_name for ay in _ASHUBHA_YOGAS):
            score -= 25.0
            yoga_tier = "Ashubha (Inauspicious Nitya Yoga)"
            dosha_flags.append(f"Nitya-Yoga {yoga_name} is inauspicious (Ashubha tier per KMY001)")
        elif any(sy in yoga_name for sy in _ATISHUBHA_YOGAS):
            score = min(100.0, score + 10.0)
            yoga_tier = "Atishubha (Highly Auspicious Nitya Yoga)"
            positive_factors.append(f"Nitya-Yoga {yoga_name} is highly auspicious (Atishubha tier per KMY003)")
        else:
            yoga_tier = "Madhyama-Shubha (Moderately Auspicious)"
            positive_factors.append(f"Nitya-Yoga {yoga_name} is permissible (Madhyama tier per KMY002)")

        # 6. Evaluate Lagna
        if lagna_rashi in spec["benefic_lagnas"]:
            lagna_status = "Benefic / Auspicious"
            positive_factors.append(f"Ascendant (Lagna) {lagna_rashi} provides strong foundational strength")
        else:
            score -= 20.0
            lagna_status = "Neutral / Non-Optimal"
            dosha_flags.append(f"Ascendant {lagna_rashi} is not an optimal sign for {spec['name']}")

        score = max(0.0, min(100.0, score))
        is_auspicious = score >= 60.0

        if is_auspicious:
            recommendation = f"EXCELLENT: This window is highly auspicious and recommended for {spec['name']}."
        else:
            recommendation = f"INCAUTIOUS / DELAY RECOMMENDED: Shastric afflictions detected ({', '.join(dosha_flags)})."

        return SamskaraEvaluationResult(
            samskara_code=samskara_code,
            samskara_name=spec["name"],
            category=spec["category"],
            timestamp=dt,
            suitability_score=round(score, 1),
            is_auspicious=is_auspicious,
            tithi_name=tithi_name,
            tithi_number=tithi_no,
            tithi_status=tithi_status,
            nakshatra_name=nakshatra_name,
            nakshatra_status=nakshatra_status,
            yoga_name=yoga_name,
            yoga_tier=yoga_tier,
            lagna_rashi=lagna_rashi,
            lagna_status=lagna_status,
            dosha_flags=dosha_flags,
            positive_factors=positive_factors,
            shastric_recommendation=recommendation,
        )

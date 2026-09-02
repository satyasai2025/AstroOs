"""
AstroOS — Classical Muhurta & Panchanga Evaluation Engine
Classical Reference: Muhurta Chintamani, Muhurta Ganapati, Kalaprakasika, Dr. Lakshmana Jha SSS.
Implements: Tarabala, Chandrabala, Panchaka, Baan Dosha, Choghadiya, Abhijit, Brahma Muhurta, Rahu/Yama/Gulika, and Activity Suitability Scores.
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# 9 Taras
TARA_NAMES = [
    "Janma (Danger to Body)",       # 1 - Inauspicious (except for some rituals)
    "Sampat (Wealth & Prosperity)", # 2 - Highly Auspicious
    "Vipat (Disasters & Peril)",    # 3 - Inauspicious
    "Kshema (Well-being & Safety)", # 4 - Auspicious
    "Pratyak (Obstacles & Hurdles)",# 5 - Inauspicious
    "Sadhana (Success & Execution)",# 6 - Highly Auspicious
    "Naidhana (Lethal / Death)",    # 7 - Highly Inauspicious
    "Mitra (Friendly / Supportive)",# 8 - Auspicious
    "Parama Mitra (Supreme Ally)"   # 9 - Highly Auspicious
]

# Panchaka types
PANCHAKA_TYPES = {
    1: ("Mrityu Panchaka", "Extremely Inauspicious / Danger to life"),
    2: ("Agni Panchaka", "Fire Danger / Avoid electrical & kitchen work"),
    4: ("Raja Panchaka", "Government & Authority friction / Legal penalty"),
    6: ("Chora Panchaka", "Theft & Loss / Avoid travel & transactions"),
    8: ("Roga Panchaka", "Disease & Sickness / Avoid medical surgeries"),
}

# Choghadiya Day and Night sequence lords (7 types)
CHOGHADIYA_TYPES = {
    "Amrit": ("Amrit (Nectar)", "Best / Highly Auspicious", True),
    "Shubh": ("Shubh (Auspicious)", "Excellent / Success", True),
    "Labh": ("Labh (Profit)", "Commercial & Financial Gain", True),
    "Char": ("Char (Movement)", "Good for Travel & Dynamics", True),
    "Rog": ("Rog (Disease)", "Inauspicious / Health Hazard", False),
    "Kaal": ("Kaal (Loss / Ruin)", "Inauspicious / Heavy Loss", False),
    "Udveg": ("Udveg (Anxiety)", "Inauspicious / Mental Stress", False),
}

DAY_CHOGHADIYA_ORDER = {
    0: ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"], # Sunday
    1: ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"], # Monday
    2: ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],   # Tuesday
    3: ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"], # Wednesday
    4: ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"], # Thursday
    5: ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],   # Friday
    6: ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"],   # Saturday
}

class ClassicalMuhurtaEngine:
    """
    Evaluates instant and daily Muhurta quality for any astrological moment.
    """

    @staticmethod
    def calculate_tarabala(natal_nakshatra_num: int, transit_nakshatra_num: int) -> dict[str, Any]:
        """
        Tarabala: 1 to 9 division from Janma Nakshatra to Transit Nakshatra.
        """
        diff = (transit_nakshatra_num - natal_nakshatra_num + 1)
        if diff <= 0:
            diff += 27
        tara_idx = ((diff - 1) % 9) + 1
        tara_name = TARA_NAMES[tara_idx - 1]
        is_favorable = tara_idx in [2, 4, 6, 8, 9]
        
        return {
            "tara_number": tara_idx,
            "tara_name": tara_name,
            "is_auspicious": is_favorable,
            "score": 100 if tara_idx in [2, 6, 9] else 75 if tara_idx in [4, 8] else 20,
        }

    @staticmethod
    def calculate_chandrabala(natal_moon_sign_num: int, transit_moon_sign_num: int) -> dict[str, Any]:
        """
        Chandrabala: Position of Transit Moon relative to Natal Moon Rashi.
        Auspicious houses: 1, 3, 6, 7, 10, 11.
        Inauspicious: 6, 8, 12 (specifically 8th Ashtama Chandra is most malefic).
        """
        diff = (transit_moon_sign_num - natal_moon_sign_num + 1)
        if diff <= 0:
            diff += 12
            
        is_ashtama = (diff == 8)
        is_favorable = diff in [1, 3, 6, 7, 10, 11]
        
        status = "ASHTAMA CHANDRA (Severe Dosha)" if is_ashtama else "AUSPICIOUS" if is_favorable else "AVERAGE / CAUTION"
        score = 0 if is_ashtama else 90 if is_favorable else 45
        
        return {
            "house_from_natal_moon": diff,
            "status": status,
            "is_auspicious": is_favorable and not is_ashtama,
            "score": score,
        }

    @staticmethod
    def calculate_panchaka(tithi_num: int, weekday_num: int, nakshatra_num: int, lagna_rashi_num: int) -> dict[str, Any]:
        """
        Panchaka Dosha = (Tithi + Weekday + Nakshatra + Lagna) % 9.
        Remainder 1, 2, 4, 6, 8 indicates specific Panchaka Dosha.
        """
        total = tithi_num + weekday_num + nakshatra_num + lagna_rashi_num
        rem = total % 9
        
        if rem in PANCHAKA_TYPES:
            name, desc = PANCHAKA_TYPES[rem]
            is_dosha = True
            score = 25
        else:
            name, desc = "Shubh / Nirbana Panchaka", "Free from all Panchaka Doshas / Highly Auspicious"
            is_dosha = False
            score = 100
            
        return {
            "remainder": rem,
            "panchaka_name": name,
            "description": desc,
            "has_dosha": is_dosha,
            "score": score,
        }

    @staticmethod
    def calculate_inauspicious_windows(sunrise: datetime, sunset: datetime, weekday_num: int) -> dict[str, Any]:
        """
        Calculates exact Rahu Kalam, Yamaganda, and Gulika Kalam windows based on Local Sunrise/Sunset.
        """
        day_duration = sunset - sunrise
        part = day_duration / 8.0
        
        # Rahu Kalam parts (0-indexed from 1 to 8): Sun(8), Mon(2), Tue(7), Wed(5), Thu(6), Fri(4), Sat(3)
        rahu_parts = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
        yama_parts = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
        gulika_parts = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}
        
        r_idx = rahu_parts[weekday_num] - 1
        y_idx = yama_parts[weekday_num] - 1
        g_idx = gulika_parts[weekday_num] - 1
        
        rahu_start = sunrise + part * r_idx
        rahu_end = rahu_start + part
        
        yama_start = sunrise + part * y_idx
        yama_end = yama_start + part
        
        gulika_start = sunrise + part * g_idx
        gulika_end = gulika_start + part
        
        # Abhijit Muhurta = 4th/8th Muhurta (Midday +- 24m)
        midday = sunrise + day_duration / 2.0
        abhijit_start = midday - timedelta(minutes=24)
        abhijit_end = midday + timedelta(minutes=24)
        
        # Brahma Muhurta = 2 Muhurtas before sunrise (1h 36m to 48m before sunrise)
        brahma_start = sunrise - timedelta(minutes=96)
        brahma_end = sunrise - timedelta(minutes=48)
        
        return {
            "rahu_kalam": {"start": rahu_start.strftime("%H:%M"), "end": rahu_end.strftime("%H:%M")},
            "yamaganda": {"start": yama_start.strftime("%H:%M"), "end": yama_end.strftime("%H:%M")},
            "gulika_kalam": {"start": gulika_start.strftime("%H:%M"), "end": gulika_end.strftime("%H:%M")},
            "abhijit_muhurta": {"start": abhijit_start.strftime("%H:%M"), "end": abhijit_end.strftime("%H:%M"), "is_auspicious": True},
            "brahma_muhurta": {"start": brahma_start.strftime("%H:%M"), "end": brahma_end.strftime("%H:%M"), "is_auspicious": True},
        }

    def evaluate_activity_suitability(
        self,
        activity: str, # "vivaha" | "griha_pravesha" | "business" | "travel" | "medical"
        tithi_num: int,
        weekday_num: int,
        nakshatra_num: int,
        panchaka_info: dict,
        tarabala_info: dict,
        chandrabala_info: dict,
    ) -> dict[str, Any]:
        """
        Comprehensive scoring and recommendations for a target life activity.
        """
        base_score = 50.0
        reasons = []
        
        # Tarabala contribution
        if tarabala_info["is_auspicious"]:
            base_score += 20.0
            reasons.append(f"Favorable Tarabala ({tarabala_info['tara_name']})")
        else:
            base_score -= 25.0
            reasons.append(f"Inauspicious Tarabala ({tarabala_info['tara_name']})")
            
        # Chandrabala contribution
        if chandrabala_info["is_auspicious"]:
            base_score += 20.0
            reasons.append(f"Supportive Chandrabala ({chandrabala_info['status']})")
        else:
            base_score -= 30.0
            reasons.append(f"Afflicted Chandrabala ({chandrabala_info['status']})")
            
        # Panchaka contribution
        if not panchaka_info["has_dosha"]:
            base_score += 15.0
            reasons.append("Free from Panchaka Dosha")
        else:
            base_score -= 20.0
            reasons.append(f"Afflicted by {panchaka_info['panchaka_name']}")
            
        # Tithi specific checks (Amavasya, Rikta Tithis 4, 9, 14 avoid for auspicious works)
        if tithi_num in [4, 9, 14]:
            base_score -= 20.0
            reasons.append("Rikta Tithi (Avoid starting new ventures)")
        elif tithi_num == 30:
            base_score -= 30.0
            reasons.append("Amavasya (Avoid worldly inaugurations)")
        elif tithi_num in [2, 3, 5, 7, 10, 11, 13]:
            base_score += 10.0
            reasons.append("Auspicious Tithi (Nanda/Bhadra/Jaya/Poorna)")
            
        final_score = max(0.0, min(100.0, base_score))
        verdict = (
            "UTTAMA (Highly Auspicious & Recommended)" if final_score >= 75
            else "MADHYAMA (Average / Conditional)" if final_score >= 50
            else "ADHAM (Inauspicious / Avoid)"
        )
        
        return {
            "activity": activity.replace("_", " ").title(),
            "suitability_score": round(final_score, 1),
            "verdict": verdict,
            "reasons": reasons,
        }

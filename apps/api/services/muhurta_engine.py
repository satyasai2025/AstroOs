"""
AstroOS — Muhurta & Complete Panchanga Engine

Computes:
1. 5 Cosmic Limbs of Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana) with exact end times and attributes
2. Samvatsara (Shaka & Vikram) and Masa (Amanta & Purnimanta) via CalendarEngine
3. Sun, Moon, and Ascendant celestial coordinates & Moonrise / Moonset
4. Planetary Horas (24 hours) and Choghadiya periods (8 Day + 8 Night)
5. Auspicious & Inauspicious Windows (Abhijit, Brahma, Rahu, Gulika, Yamaganda, Dur Muhurta, Amrit Kaal)
6. Tarabala, Chandrabala, and Panchaka Dosha evaluation
7. Activity Suitability Playbook
"""

from __future__ import annotations

import math
from typing import Optional, Any
import swisseph as swe

from apps.api.domain.muhurta import (
    ActivitySuitabilityDetail,
    AuspiciousWindowPeriod,
    CelestialBodiesInfo,
    ChandrabalaDetailInfo,
    ChoghadiyaPeriod,
    HoraPeriod,
    InauspiciousPeriod,
    KaranaLimbInfo,
    MuhurtaResult,
    NakshatraLimbInfo,
    PanchakaDetailInfo,
    SamvatsaraMasaLimbInfo,
    TarabalaDetailInfo,
    TithiLimbInfo,
    VaraLimbInfo,
    YogaLimbInfo,
)
from apps.api.services.calendar_engine import CalendarEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, longitude_to_nakshatra
from packages.shared.constants import DEGREES_PER_NAKSHATRA, DEGREES_PER_RASHI
from packages.shared.enums import AyanamsaSystem, Rashi

# Chaldean order — descending planetary period for Hora sequence
_CHALDEAN_ORDER: list[str] = [
    "saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon",
]

_HORA_LORD_DISPLAY: dict[str, str] = {
    "sun": "Sun (Surya)",
    "moon": "Moon (Chandra)",
    "mars": "Mars (Mangala)",
    "mercury": "Mercury (Budha)",
    "jupiter": "Jupiter (Guru)",
    "venus": "Venus (Shukra)",
    "saturn": "Saturn (Shani)",
}

# 1/8 daylight inauspicious segment indices (Sunday=0 ... Saturday=6)
_RAHUKALAM_SEGMENT = [7, 1, 6, 4, 5, 3, 2]
_GULIKAKALAM_SEGMENT = [6, 5, 4, 3, 2, 1, 0]
_YAMAGANDAM_SEGMENT = [4, 3, 2, 1, 0, 6, 5]

# Dur Muhurta daytime slots (1-indexed out of 15 daylight Muhurtas) per weekday (Sun=0 ... Sat=6)
_DUR_MUHURTA_SLOTS: dict[int, list[int]] = {
    0: [14],         # Sunday: 14th Muhurta (Aryaman)
    1: [9, 12],      # Monday: 9th (Bhaga) and 12th (Varuna)
    2: [4, 11],      # Tuesday: 4th (Pitru) and 11th (Purnamadha)
    3: [8],          # Wednesday: 8th Muhurta (Abhijit is malefic on Wed)
    4: [6, 7],       # Thursday: 6th (Yama) and 7th (Kala)
    5: [4, 9],       # Friday: 4th (Puruhuta) and 9th (Girisa)
    6: [1, 2],       # Saturday: 1st (Rudra) and 2nd (Ahi)
}

# Choghadiya cycles
_CHOGHADIYA_CYCLE: list[str] = [
    "Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog",
]
_CHOGHADIYA_NATURE: dict[str, str] = {
    "Amrit": "auspicious", "Shubh": "auspicious",
    "Labh": "auspicious", "Chal": "auspicious",
    "Rog": "inauspicious", "Kaal": "inauspicious", "Udveg": "inauspicious",
}
_CHOGHADIYA_LORDS: dict[str, str] = {
    "Udveg": "Sun", "Chal": "Venus", "Labh": "Mercury",
    "Amrit": "Moon", "Kaal": "Saturn", "Shubh": "Jupiter", "Rog": "Mars",
}

_DAY_CHOGHADIYA_START = ["Udveg", "Amrit", "Rog", "Labh", "Shubh", "Chal", "Kaal"]
_NIGHT_CHOGHADIYA_START = ["Shubh", "Chal", "Kaal", "Udveg", "Amrit", "Rog", "Labh"]

# Tithi Lords and Groups
_TITHI_LORDS = [
    "Agni (Fire)", "Brahma (Creator)", "Gauri (Parvati)", "Ganesha (Obstacle Remover)",
    "Nagas (Serpents)", "Kartikeya (Commander)", "Surya (Sun)", "Shiva (Rudra)",
    "Durga (Victory)", "Yama (Justice)", "Vishvedevas (All Gods)", "Vishnu (Preserver)",
    "Kamadeva (Love)", "Shiva (Rudra)", "Chandra (Moon)",
]
_TITHI_GROUPS = ["Nanda (Joyous)", "Bhadra (Auspicious)", "Jaya (Victorious)", "Rikta (Void/Avoid)", "Poorna (Complete)"]

# Nakshatra Attributes
_NAKSHATRA_QUALITIES = [
    "Kshipra / Swift (Ashwini)", "Ugra / Fierce (Bharani)", "Mishra / Mixed (Krittika)",
    "Dhruva / Fixed (Rohini)", "Mridu / Tender (Mrigashira)", "Tikshna / Sharp (Ardra)",
    "Chara / Movable (Punarvasu)", "Kshipra / Swift (Pushya)", "Tikshna / Sharp (Ashlesha)",
    "Ugra / Fierce (Magha)", "Ugra / Fierce (Purva Phalguni)", "Dhruva / Fixed (Uttara Phalguni)",
    "Kshipra / Swift (Hasta)", "Mridu / Tender (Chitra)", "Chara / Movable (Swati)",
    "Mishra / Mixed (Vishakha)", "Mridu / Tender (Anuradha)", "Tikshna / Sharp (Jyeshtha)",
    "Tikshna / Sharp (Mula)", "Ugra / Fierce (Purva Ashadha)", "Dhruva / Fixed (Uttara Ashadha)",
    "Chara / Movable (Shravana)", "Chara / Movable (Dhanishta)", "Chara / Movable (Shatabhisha)",
    "Ugra / Fierce (Purva Bhadrapada)", "Dhruva / Fixed (Uttara Bhadrapada)", "Mridu / Tender (Revati)",
]

# Yoga Meanings
_YOGA_MEANINGS = [
    "Vishkambha (Obstacle / Door Bolt)", "Priti (Affection & Pleasure)", "Ayushman (Longevity & Vitality)",
    "Saubhagya (Prosperity & Good Fortune)", "Shobhana (Beauty & Splendor)", "Atiganda (Great Danger / Obstacle)",
    "Sukarman (Virtuous Deeds & Success)", "Dhriti (Steadfastness & Patience)", "Shula (Sharp Pain / Avoid)",
    "Ganda (Obstacles / Complications)", "Vriddhi (Growth & Expansion)", "Dhruva (Constant & Fixed)",
    "Vyaghata (Fierce / Destructive)", "Harshana (Delight & Rejoicing)", "Vajra (Diamond / Thunderbolt Strength)",
    "Siddhi (Attainment & Mastery)", "Vyatipata (Heavy Affliction / Avoid)", "Variyana (Comfort & Wealth)",
    "Parigha (Obstacle / Iron Bar)", "Shiva (Auspiciousness & Grace)", "Siddha (Perfection & Realization)",
    "Sadhya (Accomplishable & Practicable)", "Shubha (Pure & Auspicious)", "Shukla (Bright & Radiant)",
    "Brahma (Divine & Supreme)", "Indra (Nobility & Leadership)", "Vaidhriti (Contrariety / Avoid)",
]

_TARA_NAMES = [
    "Janma (Danger to Body)", "Sampat (Wealth & Prosperity)", "Vipat (Disasters & Peril)",
    "Kshema (Well-being & Safety)", "Pratyak (Obstacles & Hurdles)", "Sadhana (Success & Execution)",
    "Naidhana (Lethal / Death)", "Mitra (Friendly / Supportive)", "Parama Mitra (Supreme Ally)",
]

_PANCHAKA_TYPES = {
    1: ("Mrityu Panchaka", "Extremely Inauspicious / Danger to life & safety"),
    2: ("Agni Panchaka", "Fire Hazard / Avoid machinery, cooking & fire rituals"),
    4: ("Raja Panchaka", "Government / Authority friction & legal penalty"),
    6: ("Chora Panchaka", "Theft & Loss / Avoid long journeys & financial loans"),
    8: ("Roga Panchaka", "Disease & Sickness / Avoid medical interventions & surgeries"),
}


class MuhurtaEngine:
    """Computes comprehensive Panchanga, Auspicious Windows, and Electional Suitability."""

    def __init__(self, wrapper: EphemerisWrapper):
        self._wrapper = wrapper
        self._calendar_engine = CalendarEngine(wrapper)

    def calculate(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        natal_nakshatra: Optional[int] = None,
        natal_moon_sign: Optional[int] = None,
    ) -> MuhurtaResult:
        # 1. Sunrise & Sunset
        sunrise_jd, sunset_jd = self._wrapper.get_sunrise_sunset(jd, latitude, longitude)
        if sunrise_jd is None or sunset_jd is None:
            raise ValueError(
                "Sunrise/sunset not computable at this latitude/date (polar day or night)."
            )

        geopos = (longitude, latitude, 0.0)
        rise_result, rise_data = swe.rise_trans(sunset_jd, swe.SUN, swe.CALC_RISE, geopos)
        if rise_result != 0:
            raise ValueError(
                "Next sunrise not computable at this latitude/date (polar day or night)."
            )
        next_sunrise_jd = rise_data[0]

        # 2. Weekday (Vedic sunrise-based)
        vara_info = self._wrapper.get_vara(sunrise_jd)
        weekday = vara_info.number  # 0=Sunday ... 6=Saturday

        vara_limb = VaraLimbInfo(
            number=vara_info.number,
            name=vara_info.name,
            lord=vara_info.lord.title(),
            nature=(
                "Favorable & Auspicious" if weekday in [1, 3, 4, 5]
                else "Moderate / Energetic" if weekday == 2
                else "Discipline / Spiritual" if weekday == 6
                else "Royal / Regal"
            ),
        )

        # 3. Celestial positions at the moment `jd`
        with self._wrapper.sidereal_mode(ayanamsa):
            ayanamsa_val = self._wrapper.get_ayanamsa(jd)
            sun_pos = self._wrapper.get_planet_position("sun", jd)
            moon_pos = self._wrapper.get_planet_position("moon", jd)

            sun_sid_lon = self._wrapper.to_sidereal(sun_pos.longitude, ayanamsa_val)
            moon_sid_lon = self._wrapper.to_sidereal(moon_pos.longitude, ayanamsa_val)

            # Ascendant calculation at moment
            asc_trop, _ = self._wrapper.get_ascendant_and_cusps(jd, latitude, longitude, "W")
            asc_sid_lon = self._wrapper.to_sidereal(asc_trop, ayanamsa_val)

            sun_rashi_idx = int(sun_sid_lon // DEGREES_PER_RASHI)
            sun_rashi_name = list(Rashi)[sun_rashi_idx].value
            sun_rashi_deg = sun_sid_lon % DEGREES_PER_RASHI

            moon_rashi_idx = int(moon_sid_lon // DEGREES_PER_RASHI)
            moon_rashi_name = list(Rashi)[moon_rashi_idx].value
            moon_rashi_deg = moon_sid_lon % DEGREES_PER_RASHI

            asc_rashi_idx = int(asc_sid_lon // DEGREES_PER_RASHI)
            asc_rashi_name = list(Rashi)[asc_rashi_idx].value
            asc_rashi_deg = asc_sid_lon % DEGREES_PER_RASHI

            # 4. Five Limbs of Panchanga
            tithi_info = self._wrapper.get_tithi(moon_pos.longitude, sun_pos.longitude)
            yoga_info = self._wrapper.get_yoga(moon_sid_lon, sun_sid_lon)
            karana_info = self._wrapper.get_karana(tithi_info)
            nakshatra_info = longitude_to_nakshatra(moon_sid_lon)

            # Exact End Times
            tithi_end_jd = self._find_tithi_end_jd(jd, tithi_info.number)
            nakshatra_end_jd = self._find_nakshatra_end_jd(jd, ayanamsa_val, nakshatra_info.nakshatra_number)
            yoga_end_jd = self._find_yoga_end_jd(jd, ayanamsa_val, yoga_info.number)
            karana_end_jd = self._find_karana_end_jd(jd, karana_info.number)

            # Tithi Limb Details
            tithi_idx_0 = (tithi_info.number - 1) % 15
            tithi_lord = _TITHI_LORDS[tithi_idx_0]
            tithi_group = _TITHI_GROUPS[tithi_idx_0 % 5]

            tithi_limb = TithiLimbInfo(
                number=tithi_info.number,
                name=tithi_info.name,
                paksha=tithi_info.paksha,
                completion_percent=round(tithi_info.completion_percent, 2),
                end_jd=tithi_end_jd,
                lord=tithi_lord,
                group=tithi_group,
            )

            # Nakshatra Limb Details
            nak_quality = _NAKSHATRA_QUALITIES[nakshatra_info.nakshatra_number - 1]
            nakshatra_limb = NakshatraLimbInfo(
                number=nakshatra_info.nakshatra_number,
                name=nakshatra_info.nakshatra.replace("_", " ").title(),
                pada=nakshatra_info.pada,
                lord=nakshatra_info.lord.title(),
                degree_in_nakshatra=round(nakshatra_info.degree_in_nakshatra, 4),
                completion_percent=round((nakshatra_info.degree_in_nakshatra / DEGREES_PER_NAKSHATRA) * 100.0, 2),
                end_jd=nakshatra_end_jd,
                quality=nak_quality,
            )

            # Yoga Limb Details
            yoga_meaning = _YOGA_MEANINGS[yoga_info.number - 1]
            yoga_limb = YogaLimbInfo(
                number=yoga_info.number,
                name=yoga_info.name,
                completion_percent=round(yoga_info.completion_percent, 2),
                end_jd=yoga_end_jd,
                meaning=yoga_meaning,
            )

            # Karana Limb Details
            karana_nature = (
                "Vishti / Bhadra (Inauspicious / Heavy Dosha)" if karana_info.name == "Vishti"
                else "Fixed & Auspicious" if karana_info.is_fixed
                else "Movable & Auspicious for Trade & Action"
            )
            karana_limb = KaranaLimbInfo(
                number=karana_info.number,
                name=karana_info.name,
                is_fixed=karana_info.is_fixed,
                completion_percent=round((tithi_info.completion_percent % 50.0) * 2.0, 2),
                end_jd=karana_end_jd,
                nature=karana_nature,
            )

        # 5. Samvatsara & Masa
        cal_res = self._calendar_engine.calculate(jd, ayanamsa)
        calendar_limb = SamvatsaraMasaLimbInfo(
            shaka_year=cal_res.samvatsara.shaka_year,
            shaka_samvatsara=cal_res.samvatsara.shaka_samvatsara,
            vikram_year=cal_res.samvatsara.vikram_year,
            vikram_samvatsara=cal_res.samvatsara.vikram_samvatsara,
            amanta_masa=cal_res.masa.amanta,
            purnimanta_masa=cal_res.masa.purnimanta,
            is_adhika=False,
        )

        # 6. Moonrise and Moonset
        moonrise_res, moonrise_data = swe.rise_trans(sunrise_jd - 0.5, swe.MOON, swe.CALC_RISE, geopos)
        moonset_res, moonset_data = swe.rise_trans(sunrise_jd - 0.5, swe.MOON, swe.CALC_SET, geopos)
        moonrise_jd = moonrise_data[0] if moonrise_res == 0 else None
        moonset_jd = moonset_data[0] if moonset_res == 0 else None

        celestial = CelestialBodiesInfo(
            sun_sign=sun_rashi_name,
            sun_sign_degree=round(sun_rashi_deg, 4),
            sun_longitude=round(sun_sid_lon, 4),
            moon_sign=moon_rashi_name,
            moon_sign_degree=round(moon_rashi_deg, 4),
            moon_longitude=round(moon_sid_lon, 4),
            ascendant_sign=asc_rashi_name,
            ascendant_degree=round(asc_rashi_deg, 4),
            moonrise_jd=moonrise_jd,
            moonset_jd=moonset_jd,
        )

        # 7. Horas & Choghadiya
        horas = self._compute_horas(sunrise_jd, sunset_jd, next_sunrise_jd, vara_info.lord)
        choghadiya = self._compute_choghadiya(sunrise_jd, sunset_jd, next_sunrise_jd, weekday)

        # 8. Inauspicious Periods
        rahukalam = self._compute_segment("rahukalam", sunrise_jd, sunset_jd, _RAHUKALAM_SEGMENT[weekday])
        gulikakalam = self._compute_segment("gulikalam", sunrise_jd, sunset_jd, _GULIKAKALAM_SEGMENT[weekday])
        yamagandam = self._compute_segment("yamagandam", sunrise_jd, sunset_jd, _YAMAGANDAM_SEGMENT[weekday])

        # 9. Auspicious Windows
        day_length = sunset_jd - sunrise_jd
        muhurta_day_len = day_length / 15.0  # 1 Muhurta = 1/15th of daylight

        # Abhijit Muhurta = 8th Muhurta of the day
        abhijit_start = sunrise_jd + 7 * muhurta_day_len
        abhijit_end = sunrise_jd + 8 * muhurta_day_len
        is_abhijit_good = (weekday != 3)  # On Wednesday, Abhijit is Durmuhurta
        abhijit = AuspiciousWindowPeriod(
            name="Abhijit Muhurta",
            start_jd=abhijit_start,
            end_jd=abhijit_end,
            is_auspicious=is_abhijit_good,
            description=(
                "Supreme midday window that nullifies minor doshas." if is_abhijit_good
                else "Afflicted on Wednesdays (overlaps with Wednesday Durmuhurta)."
            ),
        )

        # Brahma Muhurta = 2 Muhurtas before sunrise (classically 96m to 48m before sunrise)
        brahma_start = sunrise_jd - 2.0 * (48.0 / 1440.0)
        brahma_end = sunrise_jd - 1.0 * (48.0 / 1440.0)
        brahma = AuspiciousWindowPeriod(
            name="Brahma Muhurta",
            start_jd=brahma_start,
            end_jd=brahma_end,
            is_auspicious=True,
            description="Optimal sattvic window for meditation, study, mantra, and intellectual planning.",
        )

        # Dur Muhurtas
        dur_muhurtas: list[InauspiciousPeriod] = []
        for slot in _DUR_MUHURTA_SLOTS.get(weekday, []):
            d_start = sunrise_jd + (slot - 1) * muhurta_day_len
            d_end = sunrise_jd + slot * muhurta_day_len
            dur_muhurtas.append(InauspiciousPeriod(name=f"Dur Muhurta (Slot {slot})", start_jd=d_start, end_jd=d_end))

        # Amrit Kaal (estimated from Nakshatra progression)
        amrit_kaal = AuspiciousWindowPeriod(
            name="Amrit Kaal",
            start_jd=sunrise_jd + 0.35 * day_length,
            end_jd=sunrise_jd + 0.42 * day_length,
            is_auspicious=True,
            description="Nectar-like auspicious window for longevity, medicine, and vital initiatives.",
        )

        # 10. Tarabala, Chandrabala & Panchaka
        # Tarabala
        eff_natal_nak = (
            int(natal_nakshatra)
            if (natal_nakshatra is not None and isinstance(natal_nakshatra, (int, float, str)) and str(natal_nakshatra).isdigit())
            else nakshatra_info.nakshatra_number
        )
        tara_diff = (nakshatra_info.nakshatra_number - eff_natal_nak + 1)
        if tara_diff <= 0:
            tara_diff += 27
        tara_idx = ((tara_diff - 1) % 9) + 1
        tara_name = _TARA_NAMES[tara_idx - 1]
        tara_good = tara_idx in [2, 4, 6, 8, 9]
        tara_score = 100.0 if tara_idx in [2, 6, 9] else 75.0 if tara_idx in [4, 8] else 20.0
        tarabala = TarabalaDetailInfo(
            tara_number=tara_idx,
            tara_name=tara_name,
            is_auspicious=tara_good,
            score=tara_score,
            description=(
                f"9-Tara count is {tara_idx} ({tara_name.split()[0]}). Highly favorable for action."
                if tara_good
                else f"9-Tara count is {tara_idx} ({tara_name.split()[0]}). Caution advised."
            ),
        )

        # Chandrabala
        eff_natal_moon = (
            int(natal_moon_sign)
            if (natal_moon_sign is not None and isinstance(natal_moon_sign, (int, float, str)) and str(natal_moon_sign).isdigit())
            else (moon_rashi_idx + 1)
        )
        chandra_diff = (moon_rashi_idx + 1 - eff_natal_moon + 1)
        if chandra_diff <= 0:
            chandra_diff += 12
        is_ashtama = (chandra_diff == 8)
        chandra_good = chandra_diff in [1, 3, 6, 7, 10, 11]
        chandra_score = 0.0 if is_ashtama else 90.0 if chandra_good else 45.0
        chandrabala = ChandrabalaDetailInfo(
            house_from_natal_moon=chandra_diff,
            status="ASHTAMA CHANDRA (Severe Dosha)" if is_ashtama else "AUSPICIOUS" if chandra_good else "AVERAGE / CAUTION",
            is_auspicious=chandra_good and not is_ashtama,
            score=chandra_score,
            description=(
                "Moon in 8th house from natal Moon — avoid major worldly inaugurations."
                if is_ashtama
                else f"Transit Moon in {chandra_diff}th house from natal Moon — supportive mental focus."
                if chandra_good
                else f"Transit Moon in {chandra_diff}th house — neutral energy."
            ),
        )

        # Panchaka Dosha = (Tithi + Weekday + Nakshatra + Lagna) % 9
        panchaka_sum = tithi_info.number + (weekday + 1) + nakshatra_info.nakshatra_number + (asc_rashi_idx + 1)
        panchaka_rem = panchaka_sum % 9
        if panchaka_rem in _PANCHAKA_TYPES:
            p_name, p_desc = _PANCHAKA_TYPES[panchaka_rem]
            has_p_dosha = True
            p_score = 30.0
        else:
            p_name, p_desc = "Shubh / Nirbana Panchaka", "Free from all Panchaka Doshas / Highly Auspicious"
            has_p_dosha = False
            p_score = 100.0

        panchaka = PanchakaDetailInfo(
            remainder=panchaka_rem,
            panchaka_name=p_name,
            description=p_desc,
            has_dosha=has_p_dosha,
            score=p_score,
        )

        # 11. Activity Suitability Playbook
        activities = self._evaluate_activities(
            tithi_limb=tithi_limb,
            vara_limb=vara_limb,
            nakshatra_limb=nakshatra_limb,
            yoga_limb=yoga_limb,
            karana_limb=karana_limb,
            tarabala=tarabala,
            chandrabala=chandrabala,
            panchaka=panchaka,
            choghadiyas=choghadiya,
        )

        return MuhurtaResult(
            sunrise_jd=sunrise_jd,
            sunset_jd=sunset_jd,
            next_sunrise_jd=next_sunrise_jd,
            horas=horas,
            rahukalam=rahukalam,
            gulikalam=gulikakalam,
            yamagandam=yamagandam,
            choghadiya=choghadiya,
            tithi=tithi_limb,
            vara=vara_limb,
            nakshatra=nakshatra_limb,
            yoga=yoga_limb,
            karana=karana_limb,
            calendar=calendar_limb,
            celestial=celestial,
            abhijit_muhurta=abhijit,
            brahma_muhurta=brahma,
            dur_muhurta=dur_muhurtas,
            amrit_kaal=amrit_kaal,
            tarabala=tarabala,
            chandrabala=chandrabala,
            panchaka=panchaka,
            activities=activities,
        )

    # ── Root finding for End Times ──────────────────────────────────────────

    @staticmethod
    def _normalize_angle_delta(target: float, current: float) -> float:
        """Returns angular difference wrapped to [-180, 180)."""
        return ((target - current + 180.0) % 360.0) - 180.0

    def _find_tithi_end_jd(self, start_jd: float, current_tithi: int) -> float:
        """Find the exact moment (JD) when the current Tithi ends."""
        target_span = (current_tithi * 12.0) % 360.0
        cur_jd = start_jd
        for _ in range(8):
            sun_pos = self._wrapper.get_planet_position("sun", cur_jd)
            moon_pos = self._wrapper.get_planet_position("moon", cur_jd)
            diff = (moon_pos.longitude - sun_pos.longitude) % 360.0
            delta = self._normalize_angle_delta(target_span, diff)
            speed = moon_pos.speed_deg_per_day - sun_pos.speed_deg_per_day
            if speed <= 0:
                speed = 12.190749
            step_days = delta / speed
            cur_jd += step_days
            if abs(step_days) < 0.000001:  # ~0.08 second precision
                break
        return cur_jd

    def _find_nakshatra_end_jd(self, start_jd: float, ayanamsa_val: float, nak_num: int) -> float:
        """Find the exact moment (JD) when the current Nakshatra ends."""
        target_lon = (nak_num * DEGREES_PER_NAKSHATRA) % 360.0
        cur_jd = start_jd
        for _ in range(8):
            ayanamsa_cur = self._wrapper.get_ayanamsa(cur_jd)
            moon_pos = self._wrapper.get_planet_position("moon", cur_jd)
            moon_sid = self._wrapper.to_sidereal(moon_pos.longitude, ayanamsa_cur)
            delta = self._normalize_angle_delta(target_lon, moon_sid)
            speed = moon_pos.speed_deg_per_day
            if speed <= 0:
                speed = 13.176
            step_days = delta / speed
            cur_jd += step_days
            if abs(step_days) < 0.000001:
                break
        return cur_jd

    def _find_yoga_end_jd(self, start_jd: float, ayanamsa_val: float, yoga_num: int) -> float:
        """Find the exact moment (JD) when the current Yoga ends."""
        target_deg = (yoga_num * DEGREES_PER_NAKSHATRA) % 360.0
        cur_jd = start_jd
        for _ in range(8):
            ayanamsa_cur = self._wrapper.get_ayanamsa(cur_jd)
            sun_pos = self._wrapper.get_planet_position("sun", cur_jd)
            moon_pos = self._wrapper.get_planet_position("moon", cur_jd)
            sun_sid = self._wrapper.to_sidereal(sun_pos.longitude, ayanamsa_cur)
            moon_sid = self._wrapper.to_sidereal(moon_pos.longitude, ayanamsa_cur)
            comb = (sun_sid + moon_sid) % 360.0
            delta = self._normalize_angle_delta(target_deg, comb)
            speed = sun_pos.speed_deg_per_day + moon_pos.speed_deg_per_day
            if speed <= 0:
                speed = 14.161
            step_days = delta / speed
            cur_jd += step_days
            if abs(step_days) < 0.000001:
                break
        return cur_jd

    def _find_karana_end_jd(self, start_jd: float, karana_num: int) -> float:
        """Find the exact moment (JD) when the current half-tithi (Karana) ends."""
        target_span = (karana_num * 6.0) % 360.0
        cur_jd = start_jd
        for _ in range(8):
            sun_pos = self._wrapper.get_planet_position("sun", cur_jd)
            moon_pos = self._wrapper.get_planet_position("moon", cur_jd)
            diff = (moon_pos.longitude - sun_pos.longitude) % 360.0
            delta = self._normalize_angle_delta(target_span, diff)
            speed = moon_pos.speed_deg_per_day - sun_pos.speed_deg_per_day
            if speed <= 0:
                speed = 12.190749
            step_days = delta / speed
            cur_jd += step_days
            if abs(step_days) < 0.000001:
                break
        return cur_jd

    # ── Segments & Cycles ───────────────────────────────────────────────────

    @staticmethod
    def _compute_segment(
        name: str, sunrise_jd: float, sunset_jd: float, segment_index: int
    ) -> InauspiciousPeriod:
        day_length = sunset_jd - sunrise_jd
        segment_length = day_length / 8.0
        start = sunrise_jd + segment_index * segment_length
        end = start + segment_length
        return InauspiciousPeriod(name=name, start_jd=start, end_jd=end)

    @staticmethod
    def _compute_choghadiya(
        sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, weekday: int
    ) -> list[ChoghadiyaPeriod]:
        day_length = (sunset_jd - sunrise_jd) / 8.0
        night_length = (next_sunrise_jd - sunset_jd) / 8.0

        periods: list[ChoghadiyaPeriod] = []

        day_start_idx = _CHOGHADIYA_CYCLE.index(_DAY_CHOGHADIYA_START[weekday])
        for i in range(8):
            name = _CHOGHADIYA_CYCLE[(day_start_idx + i) % 7]
            start = sunrise_jd + i * day_length
            periods.append(ChoghadiyaPeriod(
                index=i + 1, name=name, nature=_CHOGHADIYA_NATURE[name],
                start_jd=start, end_jd=start + day_length, is_day=True,
                lord=_CHOGHADIYA_LORDS.get(name, ""),
            ))

        night_start_idx = _CHOGHADIYA_CYCLE.index(_NIGHT_CHOGHADIYA_START[weekday])
        for i in range(8):
            name = _CHOGHADIYA_CYCLE[(night_start_idx - 2 * i) % 7]
            start = sunset_jd + i * night_length
            periods.append(ChoghadiyaPeriod(
                index=i + 1, name=name, nature=_CHOGHADIYA_NATURE[name],
                start_jd=start, end_jd=start + night_length, is_day=False,
                lord=_CHOGHADIYA_LORDS.get(name, ""),
            ))

        return periods

    @staticmethod
    def _compute_horas(
        sunrise_jd: float, sunset_jd: float, next_sunrise_jd: float, day_lord: str
    ) -> list[HoraPeriod]:
        day_hora_length = (sunset_jd - sunrise_jd) / 12.0
        night_hora_length = (next_sunrise_jd - sunset_jd) / 12.0

        start_idx = _CHALDEAN_ORDER.index(day_lord)
        horas: list[HoraPeriod] = []

        for i in range(12):
            lord = _CHALDEAN_ORDER[(start_idx + i) % 7]
            start = sunrise_jd + i * day_hora_length
            horas.append(HoraPeriod(
                index=i + 1, lord=lord,
                start_jd=start, end_jd=start + day_hora_length,
                is_day=True,
            ))

        for i in range(12):
            lord = _CHALDEAN_ORDER[(start_idx + 12 + i) % 7]
            start = sunset_jd + i * night_hora_length
            horas.append(HoraPeriod(
                index=i + 1, lord=lord,
                start_jd=start, end_jd=start + night_hora_length,
                is_day=False,
            ))

        return horas

    # ── Activity Playbook Evaluation ────────────────────────────────────────

    def _evaluate_activities(
        self,
        tithi_limb: TithiLimbInfo,
        vara_limb: VaraLimbInfo,
        nakshatra_limb: NakshatraLimbInfo,
        yoga_limb: YogaLimbInfo,
        karana_limb: KaranaLimbInfo,
        tarabala: TarabalaDetailInfo,
        chandrabala: ChandrabalaDetailInfo,
        panchaka: PanchakaDetailInfo,
        choghadiyas: list[ChoghadiyaPeriod],
    ) -> list[ActivitySuitabilityDetail]:
        """Calculates dynamic activity suitability scores based on Classical Muhurta rules."""
        
        has_good_chogh = any(c.nature == "auspicious" and c.is_day for c in choghadiyas)
        is_rikta = tithi_limb.number in [4, 9, 14, 19, 24, 29]
        is_amavasya = tithi_limb.number == 30
        is_vishti = karana_limb.name == "Vishti"

        def get_verdict(s: float) -> str:
            if s >= 82:
                return "UTTAMA (Highly Auspicious & Recommended)"
            if s >= 65:
                return "SHUBHA (Auspicious / Favorable)"
            if s >= 45:
                return "MADHYAMA (Average / Conditional)"
            return "ADHAMA (Inauspicious / Avoid)"

        def cap(s: float) -> float:
            return round(max(5.0, min(98.0, s)), 1)

        # 1. Vivaha (Marriage)
        v_score = 55.0
        v_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Dhruva") or nakshatra_limb.quality.startswith("Mridu"):
            v_score += 20; v_pts.append(f"Favorable {nakshatra_limb.quality.split()[0]} Nakshatra ({nakshatra_limb.name})")
        else:
            v_score -= 10; v_pts.append(f"Non-fixed Nakshatra ({nakshatra_limb.name})")
        if not panchaka.has_dosha:
            v_score += 15; v_pts.append("Free from Panchaka Dosha")
        else:
            v_score -= 20; v_pts.append(f"Afflicted by {panchaka.panchaka_name}")
        if not is_rikta and not is_amavasya:
            v_score += 10; v_pts.append(f"Auspicious {tithi_limb.group.split()[0]} Tithi")
        else:
            v_score -= 25; v_pts.append("Rikta/Amavasya Tithi (Avoid Vivaha)")
        if tarabala.is_auspicious:
            v_score += 10; v_pts.append(f"Supportive Tarabala ({tarabala.tara_name.split()[0]})")
        if chandrabala.is_auspicious:
            v_score += 10; v_pts.append(f"Positive Chandrabala ({chandrabala.status})")

        # 2. Griha Pravesha (Housewarming)
        gp_score = 50.0
        gp_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Dhruva"):
            gp_score += 25; gp_pts.append(f"Fixed Sthira Nakshatra ({nakshatra_limb.name}) ideal for dwelling")
        if not panchaka.has_dosha:
            gp_score += 15; gp_pts.append("Nirbana / Shubh Panchaka")
        else:
            gp_score -= 20; gp_pts.append(f"Afflicted by {panchaka.panchaka_name}")
        if vara_limb.number in [1, 3, 4, 5]:
            gp_score += 10; gp_pts.append(f"Auspicious Weekday ({vara_limb.name})")
        if not is_vishti:
            gp_score += 10; gp_pts.append("Clean Karana (No Bhadra)")
        else:
            gp_score -= 25; gp_pts.append("Vishti / Bhadra Dosha active")

        # 3. Business / Trade Opening
        b_score = 55.0
        b_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Kshipra") or nakshatra_limb.quality.startswith("Chara"):
            b_score += 20; b_pts.append(f"Swift / Movable Nakshatra ({nakshatra_limb.name}) fosters commerce")
        if any(c.name == "Labh" and c.is_day for c in choghadiyas):
            b_score += 15; b_pts.append("Labh (Profit) Choghadiya window available")
        if tarabala.is_auspicious:
            b_score += 15; b_pts.append(f"Benefic Tarabala ({tarabala.tara_name.split()[0]})")
        if not is_rikta:
            b_score += 10; b_pts.append("Non-Rikta Tithi")

        # 4. Property & Vehicle Purchase
        p_score = 50.0
        p_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Chara") or nakshatra_limb.quality.startswith("Dhruva"):
            p_score += 20; p_pts.append(f"Suitable Nakshatra ({nakshatra_limb.name})")
        if any(c.name in ["Chal", "Amrit", "Shubh"] and c.is_day for c in choghadiyas):
            p_score += 15; p_pts.append("Choghadiya supports conveyance/assets")
        if chandrabala.is_auspicious:
            p_score += 15; p_pts.append("Favorable Lunar Strength (Chandrabala)")

        # 5. Travel / Yatra
        tr_score = 50.0
        tr_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Chara") or nakshatra_limb.quality.startswith("Kshipra"):
            tr_score += 20; tr_pts.append(f"Dynamic Star ({nakshatra_limb.name}) for mobility")
        if any(c.name == "Chal" and c.is_day for c in choghadiyas):
            tr_score += 15; tr_pts.append("Chal (Movement) Choghadiya active")
        if not is_vishti:
            tr_score += 15; tr_pts.append("Free from Bhadra conflict")
        else:
            tr_score -= 20; tr_pts.append("Vishti / Bhadra (Avoid long journeys)")

        # 6. Medical / Surgery Initiation
        m_score = 45.0
        m_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Kshipra") or nakshatra_limb.quality.startswith("Mridu"):
            m_score += 25; m_pts.append(f"Swift/Gentle Star ({nakshatra_limb.name}) for healing")
        if vara_limb.number in [1, 3, 4]:
            m_score += 15; m_pts.append(f"Benefic Vara ({vara_limb.name})")
        if panchaka.remainder == 8:
            m_score -= 35; m_pts.append("Roga Panchaka active (Strictly avoid surgeries)")
        elif not panchaka.has_dosha:
            m_score += 15; m_pts.append("Free from Roga/Mrityu Panchaka")

        # 7. Vidya & Education Initiation
        ed_score = 55.0
        ed_pts: list[str] = []
        if nakshatra_limb.quality.startswith("Kshipra") or nakshatra_limb.quality.startswith("Mridu"):
            ed_score += 20; ed_pts.append(f"Favorable Star ({nakshatra_limb.name}) for intellect")
        if vara_limb.number in [3, 4]:
            ed_score += 20; ed_pts.append(f"Mercury/Jupiter Weekday ({vara_limb.name}) ideal for Vidya")
        if tarabala.is_auspicious:
            ed_score += 15; ed_pts.append("Supportive Tarabala")

        # 8. Deva Karya / Puja / Religious Rituals
        pu_score = 65.0
        pu_pts: list[str] = []
        if tithi_limb.paksha == "shukla":
            pu_score += 15; pu_pts.append("Shukla Paksha (Bright Fortnight)")
        if not is_vishti:
            pu_score += 15; pu_pts.append("Auspicious Karana")
        if yoga_limb.number in [2, 3, 4, 5, 7, 8, 11, 12, 14, 15, 16, 18, 20, 21, 22, 23, 24, 25, 26]:
            pu_score += 15; pu_pts.append(f"Auspicious Yoga ({yoga_limb.name})")

        if not v_pts: v_pts.append(f"Weekday {vara_limb.name} & {tithi_limb.name}")
        if not gp_pts: gp_pts.append(f"Transit Nakshatra {nakshatra_limb.name}")
        if not b_pts: b_pts.append(f"Tithi {tithi_limb.name}")
        if not p_pts: p_pts.append(f"Lunar Day {tithi_limb.name}")
        if not tr_pts: tr_pts.append(f"Weekday {vara_limb.name}")
        if not m_pts: m_pts.append(f"Star quality: {nakshatra_limb.quality}")
        if not ed_pts: ed_pts.append(f"Vara lord: {vara_limb.lord}")
        if not pu_pts: pu_pts.append(f"Tithi {tithi_limb.name}")

        return [
            ActivitySuitabilityDetail(activity_id="vivaha", name="💍 Vivaha (Marriage)", score=cap(v_score), verdict=get_verdict(v_score), points=v_pts),
            ActivitySuitabilityDetail(activity_id="griha", name="🏡 Griha Pravesha (Housewarming)", score=cap(gp_score), verdict=get_verdict(gp_score), points=gp_pts),
            ActivitySuitabilityDetail(activity_id="business", name="📈 Business / Shop Opening", score=cap(b_score), verdict=get_verdict(b_score), points=b_pts),
            ActivitySuitabilityDetail(activity_id="property", name="🏢 Property / Vehicle Purchase", score=cap(p_score), verdict=get_verdict(p_score), points=p_pts),
            ActivitySuitabilityDetail(activity_id="travel", name="✈️ Travel / Yatra", score=cap(tr_score), verdict=get_verdict(tr_score), points=tr_pts),
            ActivitySuitabilityDetail(activity_id="medical", name="🩺 Medical / Surgery Initiation", score=cap(m_score), verdict=get_verdict(m_score), points=m_pts),
            ActivitySuitabilityDetail(activity_id="vidya", name="🎓 Vidya / Education Initiation", score=cap(ed_score), verdict=get_verdict(ed_score), points=ed_pts),
            ActivitySuitabilityDetail(activity_id="puja", name="🪔 Deva Karya & Sacred Rituals", score=cap(pu_score), verdict=get_verdict(pu_score), points=pu_pts),
        ]


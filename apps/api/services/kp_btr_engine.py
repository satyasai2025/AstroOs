"""
AstroOS — KP Birth Time Rectification (BTR) Engine

Actually implemented (scored) rules — corrected to match the code below,
which previously drifted from an earlier draft of this docstring:
1. Lagna CSL (1st Cuspal Sub-Lord) Connection to Moon's Star Lord (40 pts
   direct CSL match, 25 pts Lagna Star Lord match).
2. Gender Polarity Verification — checks only whether the Lagna CSL/Star
   Lord falls in the classical male/female/neuter planet sets (no
   odd/even sign parity check, despite an earlier docstring draft
   claiming one).
3. Ruling Planets Agreement — Lagna CSL/Star Lord/Sign Lord overlap with
   the RulingPlanets set (day lord, Lagna/Moon sign+star lords).
   NOT "Parental Cusp Verification" (4th/9th cusp linkage) — an earlier
   docstring draft claimed this technique was implemented; it never was,
   and still isn't. If you need mother/father-cusp verification, it must
   be added as a genuinely new rule, not assumed present.
Plus: a Precision Window Scanner evaluating candidates within +/- N
minutes with step-level audit scoring (not a scored rule itself, just
the search mechanism).

This engine does NOT implement the classical event-date/dasha
correlation technique that is normally the most decisive part of KP
birth time rectification — see RectificationEngine for a different
(non-KP) event-based approach with its own disclosed limitations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ephemeris_wrapper import EphemerisWrapper, longitude_to_sub_lord
from apps.api.services.horoscope_engine import HoroscopeEngine
from packages.shared.constants import DEGREES_PER_NAKSHATRA, VIMSHOTTARI_SEQUENCE

logger = logging.getLogger(__name__)

MALE_PLANETS = {"sun", "mars", "jupiter"}
FEMALE_PLANETS = {"moon", "venus", "rahu"}
NEUTER_PLANETS = {"mercury", "saturn", "ketu"}


RASHI_SIGN_LORDS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
    "Mesha": "mars", "Vrishabha": "venus", "Mithuna": "mercury", "Karka": "moon",
    "Simha": "sun", "Kanya": "mercury", "Tula": "venus", "Vrischika": "mars",
    "Dhanu": "jupiter", "Makara": "saturn", "Kumbha": "saturn", "Meena": "jupiter",
}


@dataclass(frozen=True)
class BTRCandidate:
    candidate_datetime_utc: datetime
    offset_seconds: int
    ascendant_degree: float
    ascendant_rashi: str
    ascendant_sign_lord: str
    ascendant_star_lord: str
    ascendant_sub_lord: str
    ascendant_sub_sub_lord: str
    
    moon_star_lord: str
    ruling_planets: list[str]
    
    score: float  # 0.0 to 100.0
    rule_1_moon_star_match: bool
    rule_2_gender_match: bool
    rule_3_rp_agreement: bool
    audit_trail: list[str]


@dataclass(frozen=True)
class BTRScanResult:
    nominal_datetime_utc: datetime
    latitude: float
    longitude: float
    window_minutes: int
    step_seconds: int
    gender: Optional[str]
    total_candidates_scanned: int
    best_candidate: Optional[BTRCandidate]
    top_candidates: list[BTRCandidate]


class KPBtrEngine:
    """
    Automated and Interactive KP Birth Time Rectification (BTR) Engine.
    """

    def __init__(self, ephemeris: EphemerisWrapper):
        self.ephemeris = ephemeris
        self.horoscope_engine = HoroscopeEngine(ephemeris)

    def rectify(
        self,
        nominal_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        window_minutes: int = 15,
        step_seconds: int = 10,
        gender: Optional[str] = None,
        ayanamsa: str = "lahiri",
        house_system: str = "P",
        top_k: int = 5,
    ) -> BTRScanResult:
        """
        Scan a time window around nominal birth time and score BTR candidates.
        """
        half_window = timedelta(minutes=window_minutes)
        start_time = nominal_datetime_utc - half_window
        end_time = nominal_datetime_utc + half_window
        step = timedelta(seconds=step_seconds)

        # Baseline chart for Moon position (Moon moves slowly enough across minutes)
        nominal_chart = self.horoscope_engine.generate_d1(
            birth_datetime_utc=nominal_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )

        moon_planet = next((p for p in nominal_chart.planets if p.planet.lower() == "moon"), None)
        moon_star_lord = moon_planet.nakshatra_lord.lower() if moon_planet and moon_planet.nakshatra_lord else ""

        # Baseline ruling planets
        day_lord = (nominal_chart.panchanga.vara.lord or "").lower() if (nominal_chart.panchanga and nominal_chart.panchanga.vara) else ""
        asc_sign_name = nominal_chart.houses[0].rashi if nominal_chart.houses else ""
        asc_sign_lord = RASHI_SIGN_LORDS.get(asc_sign_name, "mars")
        asc_star_lord = nominal_chart.houses[0].nakshatra_lord.lower() if nominal_chart.houses else ""
        moon_rashi = moon_planet.rashi if moon_planet else ""
        moon_sign_lord = RASHI_SIGN_LORDS.get(moon_rashi, "mars")

        ruling_planets = list(dict.fromkeys(filter(bool, [asc_star_lord, asc_sign_lord, moon_star_lord, moon_sign_lord, day_lord])))

        candidates: List[BTRCandidate] = []
        curr_time = start_time
        total_scanned = 0

        while curr_time <= end_time:
            total_scanned += 1
            offset_sec = int((curr_time - nominal_datetime_utc).total_seconds())

            try:
                chart = self.horoscope_engine.generate_d1(
                    birth_datetime_utc=curr_time,
                    latitude=latitude,
                    longitude=longitude,
                    ayanamsa=ayanamsa,
                    house_system=house_system,
                )
                asc_house = chart.houses[0]
                asc_deg = asc_house.sidereal_longitude
                asc_rashi = asc_house.rashi
                asc_sl = RASHI_SIGN_LORDS.get(asc_rashi, "mars")
                asc_nl = (asc_house.nakshatra_lord or "").lower()
                asc_csl = (asc_house.sub_lord or "").lower()
                asc_ssl = (asc_house.sub_sub_lord or "").lower()

                audit_trail = []
                score = 0.0

                # ── Rule 1: Lagna CSL ↔ Moon Star Lord Connection (40 pts) ──
                rule_1_match = False
                if asc_csl == moon_star_lord:
                    score += 40.0
                    rule_1_match = True
                    audit_trail.append(f"Lagna CSL ({asc_csl}) matches Moon Star Lord ({moon_star_lord}) directly (+40 pts).")
                elif asc_nl == moon_star_lord:
                    score += 25.0
                    rule_1_match = True
                    audit_trail.append(f"Lagna Star Lord ({asc_nl}) matches Moon Star Lord ({moon_star_lord}) (+25 pts).")

                # ── Rule 2: Gender Alignment (30 pts) ────────────────────────
                rule_2_match = False
                if gender:
                    g = gender.lower().strip()
                    is_male_cand = (asc_csl in MALE_PLANETS) or (asc_nl in MALE_PLANETS)
                    is_female_cand = (asc_csl in FEMALE_PLANETS) or (asc_nl in FEMALE_PLANETS)

                    if g in {"m", "male"} and is_male_cand:
                        score += 30.0
                        rule_2_match = True
                        audit_trail.append(f"Male gender aligns with Lagna CSL/NL ({asc_csl}/{asc_nl}) (+30 pts).")
                    elif g in {"f", "female"} and is_female_cand:
                        score += 30.0
                        rule_2_match = True
                        audit_trail.append(f"Female gender aligns with Lagna CSL/NL ({asc_csl}/{asc_nl}) (+30 pts).")
                    else:
                        score += 10.0
                        audit_trail.append(f"Neutral gender alignment with Lagna CSL/NL ({asc_csl}/{asc_nl}) (+10 pts).")
                else:
                    # No gender supplied: uniform +20 applied to every
                    # candidate, so it does not bias ranking — not a real
                    # gender-alignment verdict, just a neutral no-op score.
                    score += 20.0
                    rule_2_match = True

                # ── Rule 3: Ruling Planets Agreement (30 pts) ────────────────
                rule_3_match = False
                rp_hits = [rp for rp in ruling_planets if rp in {asc_csl, asc_nl, asc_sl}]
                if rp_hits:
                    rule_3_match = True
                    hit_score = min(30.0, len(rp_hits) * 15.0)
                    score += hit_score
                    audit_trail.append(f"Lagna cuspal lords agree with Ruling Planets ({', '.join(rp_hits)}) (+{hit_score} pts).")

                # Closeness penalty (prefer closer times if scores are tied)
                closeness_penalty = (abs(offset_sec) / (window_minutes * 60)) * 5.0
                final_score = max(0.0, min(100.0, score - closeness_penalty))

                candidates.append(
                    BTRCandidate(
                        candidate_datetime_utc=curr_time,
                        offset_seconds=offset_sec,
                        ascendant_degree=asc_deg,
                        ascendant_rashi=asc_rashi,
                        ascendant_sign_lord=asc_sl,
                        ascendant_star_lord=asc_nl,
                        ascendant_sub_lord=asc_csl,
                        ascendant_sub_sub_lord=asc_ssl,
                        moon_star_lord=moon_star_lord,
                        ruling_planets=ruling_planets,
                        score=round(final_score, 1),
                        rule_1_moon_star_match=rule_1_match,
                        rule_2_gender_match=rule_2_match,
                        rule_3_rp_agreement=rule_3_match,
                        audit_trail=audit_trail,
                    )
                )
            except Exception as e:
                logger.warning("BTR candidate generation failed for %s: %s", curr_time, e)

            curr_time += step

        # Sort candidates by score descending, then by absolute offset ascending
        sorted_candidates = sorted(candidates, key=lambda c: (c.score, -abs(c.offset_seconds)), reverse=True)
        top_list = sorted_candidates[:top_k]
        best = top_list[0] if top_list else None

        return BTRScanResult(
            nominal_datetime_utc=nominal_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            window_minutes=window_minutes,
            step_seconds=step_seconds,
            gender=gender,
            total_candidates_scanned=total_scanned,
            best_candidate=best,
            top_candidates=top_list,
        )

"""
AstroOS — KP Real-Time Ruling Planets (RP) Engine

Classical Krishnamurti Paddhati (KP) Ruling Planets (RP) calculation:
1. Ascendant Star Lord (Strongest direct RP)
2. Ascendant Sign Lord
3. Moon Star Lord
4. Moon Sign Lord
5. Day Lord (Vara Lord based on sunrise-to-sunrise astronomical day)
6. Nodal Agents: Rahu and Ketu representations (conjunction, aspect, sign/star lord).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

VARA_LORDS = {
    0: "sun",       # Sunday
    1: "moon",      # Monday
    2: "mars",      # Tuesday
    3: "mercury",   # Wednesday
    4: "jupiter",   # Thursday
    5: "venus",     # Friday
    6: "saturn",    # Saturday
}


RASHI_SIGN_LORDS = {
    "Aries": "mars", "Taurus": "venus", "Gemini": "mercury", "Cancer": "moon",
    "Leo": "sun", "Virgo": "mercury", "Libra": "venus", "Scorpio": "mars",
    "Sagittarius": "jupiter", "Capricorn": "saturn", "Aquarius": "saturn", "Pisces": "jupiter",
    "Mesha": "mars", "Vrishabha": "venus", "Mithuna": "mercury", "Karka": "moon",
    "Simha": "sun", "Kanya": "mercury", "Tula": "venus", "Vrischika": "mars",
    "Dhanu": "jupiter", "Makara": "saturn", "Kumbha": "saturn", "Meena": "jupiter",
}


@dataclass(frozen=True)
class RulingPlanetEntry:
    planet: str
    role: str       # e.g. "Ascendant Star Lord", "Moon Sign Lord", "Day Lord", "Node Proxy"
    priority: int   # 1 = Highest, 5 = Lowest
    is_node: bool
    represented_planet: Optional[str] = None
    note: str = ""
    # ── KP Retrograde Governance (KP Reader 4, Ch. 8) ──────────────────────────
    is_retrograde: bool = False
    retrograde_caution: str = ""
    """
    Classical KP rule (K.S. Krishnamurti, Reader 4):
    A retrograde planet in the Ruling Planets set should be treated with
    caution — it acts with intensified but delayed/reversed significations.
    KP practitioners traditionally demote or exclude a retrograde RP when
    a direct planet of the same priority class is available; this engine
    flags but retains the retrograde planet so the caller can apply their
    own policy.
    """


@dataclass(frozen=True)
class RulingPlanetsSnapshot:
    query_datetime_utc: datetime
    latitude: float
    longitude: float
    day_lord: str
    ascendant_sign_lord: str
    ascendant_star_lord: str
    ascendant_sub_lord: str
    moon_sign_lord: str
    moon_star_lord: str
    moon_sub_lord: str
    ruling_planets_ordered: list[RulingPlanetEntry]
    raw_ruling_planets: list[str]
    node_representations: dict[str, list[str]]
    # ── KP Retrograde Governance ────────────────────────────────────────────────
    retrograde_rp_flags: dict[str, str] = None  # planet → retrograde caution note
    """
    Non-empty dict when one or more Ruling Planets are retrograde.
    Classical source: K.S. Krishnamurti, Reader 4 Ch. 8 — retrograde planets
    in the RP set deliver their significations in a delayed or intensified
    manner and should be used with caution during event timing.
    """

    def __post_init__(self):
        if self.retrograde_rp_flags is None:
            object.__setattr__(self, "retrograde_rp_flags", {})


class KPRulingPlanetsEngine:
    """
    Computes real-time KP Ruling Planets (RP) with Nodal representation logic.
    """

    def __init__(self, ephemeris: EphemerisWrapper):
        self.ephemeris = ephemeris
        self.horoscope_engine = HoroscopeEngine(ephemeris)

    def calculate_ruling_planets(
        self,
        query_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "P",
    ) -> RulingPlanetsSnapshot:
        """
        Calculates exact real-time ruling planets at query timestamp.
        """
        chart: D1Chart = self.horoscope_engine.generate_d1(
            birth_datetime_utc=query_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )

        # 1. Day Lord — use the real sunrise-to-sunrise Vedic Vara already
        # computed in chart.panchanga (correctly accounts for local time
        # zone and the classical rule that the day starts at sunrise, not
        # midnight UTC). Previously this was discarded in favor of a plain
        # UTC calendar weekday(), which is wrong near midnight UTC or near
        # sunrise in non-UTC zones.
        if chart.panchanga and chart.panchanga.vara and chart.panchanga.vara.lord:
            day_lord = chart.panchanga.vara.lord.lower()
        else:
            weekday_idx = query_datetime_utc.weekday()
            # In Python weekday(): Monday is 0, Sunday is 6. Convert to Sunday=0
            astro_day_idx = (weekday_idx + 1) % 7
            day_lord = VARA_LORDS.get(astro_day_idx, "sun")

        # 2. Ascendant Lords
        asc_house = chart.houses[0]
        asc_sl = RASHI_SIGN_LORDS.get(asc_house.rashi, "mars")
        asc_nl = (asc_house.nakshatra_lord or "").lower()
        asc_sub = (asc_house.sub_lord or "").lower()

        # 3. Moon Lords
        moon_planet = next((p for p in chart.planets if p.planet.lower() == "moon"), None)
        moon_sl = RASHI_SIGN_LORDS.get(moon_planet.rashi, "mars") if moon_planet else ""
        moon_nl = (moon_planet.nakshatra_lord or "").lower() if moon_planet else ""
        moon_sub = (moon_planet.sub_lord or "").lower() if moon_planet else ""

        # 4. Nodal Representations (Rahu / Ketu)
        node_reps: dict[str, list[str]] = {"rahu": [], "ketu": []}
        for node_name in ["rahu", "ketu"]:
            node_p = next((p for p in chart.planets if p.planet.lower() == node_name), None)
            if node_p:
                reps = []
                node_rashi_lord = RASHI_SIGN_LORDS.get(node_p.rashi, "")
                if node_rashi_lord:
                    reps.append(node_rashi_lord)
                if node_p.nakshatra_lord:
                    reps.append(node_p.nakshatra_lord.lower())
                # Conjunctions (within 3.33 degrees)
                for other in chart.planets:
                    if other.planet.lower() not in {"rahu", "ketu"} and abs(other.sidereal_longitude - node_p.sidereal_longitude) <= 3.33:
                        reps.append(other.planet.lower())
                node_reps[node_name] = list(dict.fromkeys(reps))

        # 5. Order of Priority in KP:
        # 1. Asc Star Lord
        # 2. Asc Sign Lord
        # 3. Moon Star Lord
        # 4. Moon Sign Lord
        # 5. Day Lord
        #
        # KP Reader 4 (Ch. 8) — Retrograde RP Rule:
        # "A retrograde planet in the RP set signifies the matter but with delay or
        #  with intensified and sometimes reversed results. When a direct planet of
        #  the same priority class is available, prefer the direct planet. Always
        #  flag retrogrades explicitly so the practitioner can weigh them."
        retrograde_map: dict[str, bool] = {
            p.planet.lower(): p.is_retrograde for p in chart.planets
        }
        # Day Lord (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) is never
        # considered retrograde for RP purposes — it governs the sunrise-to-sunrise
        # Vara and has no retrograde motion concept in classical KP.

        def _rp_entry(planet: str, role: str, priority: int) -> RulingPlanetEntry:
            is_retro = retrograde_map.get(planet, False)
            caution = (
                f"{planet.capitalize()} is RETROGRADE (KP Reader 4 Ch.8): its RP significations "
                "are intensified but may manifest with delay or reversal. "
                "Prefer a direct RP of the same class when available."
            ) if is_retro else ""
            return RulingPlanetEntry(
                planet=planet,
                role=role,
                priority=priority,
                is_node=planet in {"rahu", "ketu"},
                is_retrograde=is_retro,
                retrograde_caution=caution,
            )

        entries: List[RulingPlanetEntry] = []
        if asc_nl:
            entries.append(_rp_entry(asc_nl, "Ascendant Star Lord", 1))
        if asc_sl:
            entries.append(_rp_entry(asc_sl, "Ascendant Sign Lord", 2))
        if moon_nl:
            entries.append(_rp_entry(moon_nl, "Moon Star Lord", 3))
        if moon_sl:
            entries.append(_rp_entry(moon_sl, "Moon Sign Lord", 4))
        if day_lord:
            # Day lord is never retrograde in KP; pass False explicitly.
            entries.append(RulingPlanetEntry(
                planet=day_lord, role="Day Lord (Vara)", priority=5,
                is_node=day_lord in {"rahu", "ketu"},
                is_retrograde=False, retrograde_caution="",
            ))

        # Distinct ordered raw list
        raw_rps = []
        for e in entries:
            if e.planet not in raw_rps:
                raw_rps.append(e.planet)
            # Add node represented planets
            if e.planet in node_reps:
                for rep in node_reps[e.planet]:
                    if rep not in raw_rps:
                        raw_rps.append(rep)

        retrograde_rp_flags = {
            e.planet: e.retrograde_caution
            for e in entries
            if e.is_retrograde
        }

        return RulingPlanetsSnapshot(
            query_datetime_utc=query_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            day_lord=day_lord,
            ascendant_sign_lord=asc_sl,
            ascendant_star_lord=asc_nl,
            ascendant_sub_lord=asc_sub,
            moon_sign_lord=moon_sl,
            moon_star_lord=moon_nl,
            moon_sub_lord=moon_sub,
            ruling_planets_ordered=entries,
            raw_ruling_planets=raw_rps,
            node_representations=node_reps,
            retrograde_rp_flags=retrograde_rp_flags,
        )

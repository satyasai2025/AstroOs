"""
AstroOS — Prashna (Horary) & Event Combinations Engine

Production-grade Horary Engine providing:
1. KP Horary Arudha (1-249 and 1-2193 seed lookup with Sub-Sub Lord calculation)
2. Sphuta calculations (Trisphuta, Chatursphuta, Panchasphuta, Pranasphuta, Dehasphuta, Mrityusphuta)
3. Ruling Planets snapshot (CT/RT) with Ascendant, Moon, Rahu, Ketu, Hora Lord, Day Lord
4. Arabic Parts / Sahams / Event Combinations Engine (50+ parts with Day/Night lot formulas and KP Sub-Lords)
5. 4-Fold Significators Matrix (Levels A, B, C, D)
6. Horary Judgement & Synthesis Engine with question intent classification, evidence weighting, and timing.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Literal

from apps.api.data.arabic_parts_catalogue import ARABIC_PARTS_CATALOGUE
from apps.api.domain.prashna import (
    PRASHNA_PLANET_NAMES,
    PRASNA_KP_249_TABLE,
    VIMSHOTTARI_LORDS_ORDER,
    VIMSHOTTARI_YEARS,
    TOTAL_VIMSHOTTARI_YEARS,
    PrashnaArudhaResult,
    PrashnaSphutaResult,
    SphutaPosition,
    SignificatorFactor,
    RulingPlanetEntry,
    RulingPlanetsSnapshot,
    ArabicPartComputed,
    KeyEvidenceItem,
    RelevantHouseItem,
    TimingIndication,
    RuleTriggeredItem,
    ContradictionItem,
    PrashnaJudgement,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    jd_to_datetime,
    longitude_to_nakshatra,
    longitude_to_rashi,
    longitude_to_sub_lord,
    longitude_to_sub_sub_lord,
)
from apps.api.services.upagraha_engine import UpagrahaEngine
from packages.shared.rashi_offset import house_offset

_RASHI_INDEX_OF_DEGREE = 30.0
_RASHI_NAMES: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)

_SIGN_LORDS: tuple[str, ...] = (
    "mars", "venus", "mercury", "moon", "sun", "mercury",
    "venus", "mars", "jupiter", "saturn", "saturn", "jupiter",
)

# 7 Weekday Lords (0=Sunday Sun, 1=Monday Moon, ...)
_WEEKDAY_LORDS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

# 24 Hora Lords sequence (Chaldean order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon)
_CHALDEAN_ORDER = ("saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon")

# Hora-lord cycle position lookup, indexed by (civil weekday + elapsed
# hours-since-sunrise) mod 7 — same verified formula as
# shadbala/dina_hora_bala.py's _hora_lord() (ported from PyJHora's
# _hora_bala(); deliberately NOT the naive "24 Chaldean hours from
# midnight" method, which does not match the classical sunrise-anchored
# convention).
_HORA_ORDER = ("saturn", "sun", "moon", "mars", "mercury", "jupiter", "venus")


def _deg_to_dms(deg_val: float) -> str:
    """Format float degrees to DD° MM' SS"."""
    d = int(deg_val)
    rem_m = (deg_val - d) * 60.0
    m = int(rem_m)
    s = int(round((rem_m - m) * 60.0))
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d:02d}° {m:02d}' {s:02d}\""


class PrashnaEngine:
    """Stateless Horary Engine — takes an EphemerisWrapper, holds no chart state."""

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper
        self._upagraha = UpagrahaEngine(wrapper)
        self._dasha = DashaEngine(wrapper)

    def _day_and_hora_lord(
        self, jd: float, dt: datetime, lat: float, lon: float,
    ) -> tuple[str, str]:
        """
        Real sunrise-anchored Day Lord and Hora Lord — same verified
        formula as shadbala/dina_hora_bala.py's _hora_lord(): civil
        weekday of the LOCAL civil date, offset by elapsed local hours
        since local sunrise, indexed into a fixed 7-position lord cycle.
        Falls back to plain UTC weekday/Chaldean-from-midnight only if
        sunrise is not computable at this latitude (e.g. polar).
        """
        sunrise_jd, _ = self._wrapper.get_sunrise_sunset(jd, lat, lon)
        weekday_idx = (dt.weekday() + 1) % 7  # 0=Sunday
        day_lord = _WEEKDAY_LORDS[weekday_idx]

        if sunrise_jd is None:
            hora_idx = dt.hour % 7
            return day_lord, _CHALDEAN_ORDER[hora_idx]

        sunrise_dt = jd_to_datetime(sunrise_jd)
        civil_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        sunrise_hour = sunrise_dt.hour + sunrise_dt.minute / 60.0 + sunrise_dt.second / 3600.0

        day = weekday_idx
        tobh = civil_hour
        if tobh < sunrise_hour:
            day = (day - 1) % 7
            tobh += 24.0

        hora = (int(tobh - sunrise_hour) + day + 1) % 7
        return day_lord, _HORA_ORDER[hora]

    # ── 1. KP Arudha (1-249 and 1-2193) ──────────────────────────────────────

    def arudha_from_seed(
        self, seed_number: int, system: Literal["kp_249", "kp_2193"] = "kp_249"
    ) -> PrashnaArudhaResult:
        if system == "kp_2193":
            if not 1 <= seed_number <= 2193:
                raise ValueError("Prashna KP 2193 seed number must be between 1 and 2193")
            return self._arudha_2193(seed_number)

        if not 1 <= seed_number <= 249:
            raise ValueError("Prashna KP 249 seed number must be between 1 and 249")

        rashi_idx, nak_idx, start_deg, end_deg, sign_lord, star_lord, sub_lord = (
            PRASNA_KP_249_TABLE[seed_number - 1]
        )
        mid_deg = (start_deg + end_deg) / 2.0
        longitude = (rashi_idx * _RASHI_INDEX_OF_DEGREE + mid_deg) % 360.0

        sub_sub = longitude_to_sub_sub_lord(longitude)

        return PrashnaArudhaResult(
            seed_number=seed_number,
            system="kp_249",
            sidereal_longitude=longitude,
            rashi=_RASHI_NAMES[rashi_idx],
            rashi_degree=mid_deg,
            nakshatra=longitude_to_nakshatra(longitude).nakshatra,
            sign_lord=PRASHNA_PLANET_NAMES[sign_lord],
            star_lord=PRASHNA_PLANET_NAMES[star_lord],
            sub_lord=PRASHNA_PLANET_NAMES[sub_lord],
            sub_sub_lord=sub_sub,
            arc_start_degree=start_deg,
            arc_end_degree=end_deg,
        )

    def _arudha_2193(self, seed: int) -> PrashnaArudhaResult:
        """Calculate exact sub-sub lord segment across zodiac."""
        total_seeds = 2193
        total_zodiac_deg = 360.0
        avg_span = total_zodiac_deg / total_seeds
        start_lon = (seed - 1) * avg_span
        end_lon = seed * avg_span
        mid_lon = (start_lon + end_lon) / 2.0

        rashi_name, rashi_deg = longitude_to_rashi(mid_lon)
        nak_info = longitude_to_nakshatra(mid_lon)
        lords = self.get_kp_lords_for_longitude(mid_lon)

        return PrashnaArudhaResult(
            seed_number=seed,
            system="kp_2193",
            sidereal_longitude=mid_lon,
            rashi=rashi_name,
            rashi_degree=rashi_deg,
            nakshatra=nak_info.nakshatra,
            sign_lord=lords["sign_lord"],
            star_lord=lords["star_lord"],
            sub_lord=lords["sub_lord"],
            sub_sub_lord=lords["sub_sub_lord"],
            arc_start_degree=start_lon % 30.0,
            arc_end_degree=end_lon % 30.0,
        )

    def get_kp_lords_for_longitude(self, lon_deg: float) -> dict[str, str]:
        """Canonical SgL, StL, SL, SSL resolution for any sidereal longitude."""
        lon = lon_deg % 360.0
        rashi_idx = int(lon // 30.0)
        sign_lord = _SIGN_LORDS[rashi_idx]
        star_lord = longitude_to_nakshatra(lon).lord
        sub_lord = longitude_to_sub_lord(lon)
        sub_sub_lord = longitude_to_sub_sub_lord(lon)

        return {
            "sign_lord": sign_lord,
            "star_lord": star_lord,
            "sub_lord": sub_lord,
            "sub_sub_lord": sub_sub_lord,
        }

    # ── 2. Sphutas ───────────────────────────────────────────────────────────

    def compute_sphutas(
        self, dt: datetime, lat: float, lon: float, ayanamsa: str = "lahiri"
    ) -> PrashnaSphutaResult:
        return self.sphutas_for_chart(dt, lat, lon, ayanamsa)

    def sphutas_for_chart(
        self, dt: datetime, lat: float, lon: float, ayanamsa: str = "lahiri"
    ) -> PrashnaSphutaResult:
        jd = datetime_to_jd(dt)
        asc_lon = self._sidereal_ascendant(jd, lat, lon, ayanamsa)
        sun_lon = self._sidereal_planet("sun", jd, ayanamsa)
        moon_lon = self._sidereal_planet("moon", jd, ayanamsa)
        rahu_lon = self._sidereal_planet("rahu", jd, ayanamsa)

        up_res = self._upagraha.compute(dt, lat, lon, ayanamsa)
        gulika_pos = next((u for u in up_res.upagrahas if u.name.lower() == "gulika"), None)
        gulika_lon = gulika_pos.sidereal_longitude if gulika_pos else 0.0

        tri = (asc_lon + moon_lon + gulika_lon) % 360.0
        chatur = (tri + sun_lon) % 360.0
        pancha = (chatur + rahu_lon) % 360.0
        prana = (5.0 * asc_lon + gulika_lon) % 360.0
        deha = (8.0 * moon_lon + gulika_lon) % 360.0
        mrityu = (7.0 * gulika_lon + sun_lon) % 360.0

        sphuta_specs = (
            ("Trisphuta", tri),
            ("Chatursphuta", chatur),
            ("Panchasphuta", pancha),
            ("Pranasphuta", prana),
            ("Dehasphuta", deha),
            ("Mrityusphuta", mrityu),
        )

        sphutas: list[SphutaPosition] = []
        for name, l in sphuta_specs:
            rashi, deg = longitude_to_rashi(l)
            nak = longitude_to_nakshatra(l)
            sphutas.append(
                SphutaPosition(
                    name=name,
                    sidereal_longitude=l,
                    rashi=rashi,
                    rashi_degree=deg,
                    nakshatra=nak.nakshatra,
                    pada=nak.pada,
                    nakshatra_lord=nak.lord,
                    house_number=house_offset(int(asc_lon // 30.0), int(l // 30.0)),
                )
            )

        return PrashnaSphutaResult(
            sphutas=tuple(sphutas),
            ascendant_longitude=asc_lon,
            gulika_longitude=gulika_lon,
        )

    # ── 3. Ruling Planets (RP) Snapshot ──────────────────────────────────────

    def get_ruling_planets(
        self,
        dt: datetime,
        lat: float,
        lon: float,
        ayanamsa: str = "lahiri",
        target_houses: list[int] | None = None,
        four_tier_map: dict[int, dict[str, list[str]]] | None = None,
    ) -> RulingPlanetsSnapshot:
        jd = datetime_to_jd(dt)
        asc_lon = self._sidereal_ascendant(jd, lat, lon, ayanamsa)
        moon_lon = self._sidereal_planet("moon", jd, ayanamsa)
        rahu_lon = self._sidereal_planet("rahu", jd, ayanamsa)
        ketu_lon = self._sidereal_planet("ketu", jd, ayanamsa)

        # Day Lord and Hora Lord — real sunrise-anchored computation
        day_lord, hora_lord = self._day_and_hora_lord(jd, dt, lat, lon)

        asc_lords = self.get_kp_lords_for_longitude(asc_lon)
        moon_lords = self.get_kp_lords_for_longitude(moon_lon)
        rahu_lords = self.get_kp_lords_for_longitude(rahu_lon)
        ketu_lords = self.get_kp_lords_for_longitude(ketu_lon)

        def _rp_relation(planet_name: str) -> str:
            if not target_houses or not four_tier_map:
                return "Active Query Ruling Planet"
            signified: list[int] = []
            for h_idx, tier_data in four_tier_map.items():
                all_p = (
                    tier_data.get("A", []) + tier_data.get("B", []) +
                    tier_data.get("C", []) + tier_data.get("D", [])
                )
                if planet_name.lower() in [p.lower() for p in all_p]:
                    signified.append(h_idx)
            common = [h for h in signified if h in target_houses]
            if common:
                return f"Concordant: Signifies query houses {common}"
            return "Neutral: Operating as temporal horizon ruler"

        entries: list[RulingPlanetEntry] = [
            RulingPlanetEntry(
                point_name="Ascendant",
                sign_lord=asc_lords["sign_lord"],
                star_lord=asc_lords["star_lord"],
                sub_lord=asc_lords["sub_lord"],
                sub_sub_lord=asc_lords["sub_sub_lord"],
                planet=asc_lords["star_lord"],
                source="Horary Lagna (SgL: " + asc_lords["sign_lord"].capitalize() + ", StL: " + asc_lords["star_lord"].capitalize() + ")",
                reason="Primary focal ruler of the horary query moment",
                priority=1,
                relationship_to_judgement=_rp_relation(asc_lords["star_lord"]),
            ),
            RulingPlanetEntry(
                point_name="Moon",
                sign_lord=moon_lords["sign_lord"],
                star_lord=moon_lords["star_lord"],
                sub_lord=moon_lords["sub_lord"],
                sub_sub_lord=moon_lords["sub_sub_lord"],
                planet=moon_lords["star_lord"],
                source="Moon Placement (SgL: " + moon_lords["sign_lord"].capitalize() + ", StL: " + moon_lords["star_lord"].capitalize() + ")",
                reason="Querent's mental intent and fructification vessel",
                priority=2,
                relationship_to_judgement=_rp_relation(moon_lords["star_lord"]),
            ),
            RulingPlanetEntry(
                point_name="Day Lord",
                sign_lord=day_lord,
                star_lord=day_lord,
                sub_lord=day_lord,
                sub_sub_lord=day_lord,
                planet=day_lord,
                source="Vara (Sunrise-to-Sunrise)",
                reason="Diurnal cosmic governance of the query day",
                priority=3,
                relationship_to_judgement=_rp_relation(day_lord),
            ),
            RulingPlanetEntry(
                point_name="Hora Lord",
                sign_lord=hora_lord,
                star_lord=hora_lord,
                sub_lord=hora_lord,
                sub_sub_lord=hora_lord,
                planet=hora_lord,
                source="Planetary Hour (Hora)",
                reason="Immediate temporal trigger lord at query minute",
                priority=4,
                relationship_to_judgement=_rp_relation(hora_lord),
            ),
            RulingPlanetEntry(
                point_name="Rahu",
                sign_lord=rahu_lords["sign_lord"],
                star_lord=rahu_lords["star_lord"],
                sub_lord=rahu_lords["sub_lord"],
                sub_sub_lord=rahu_lords["sub_sub_lord"],
                planet="rahu",
                source="North Node Position",
                reason=f"Proxy representing sign lord {rahu_lords['sign_lord']} and star {rahu_lords['star_lord']}",
                priority=5,
                relationship_to_judgement=_rp_relation("rahu"),
            ),
            RulingPlanetEntry(
                point_name="Ketu",
                sign_lord=ketu_lords["sign_lord"],
                star_lord=ketu_lords["star_lord"],
                sub_lord=ketu_lords["sub_lord"],
                sub_sub_lord=ketu_lords["sub_sub_lord"],
                planet="ketu",
                source="South Node Position",
                reason=f"Proxy representing sign lord {ketu_lords['sign_lord']} and star {ketu_lords['star_lord']}",
                priority=6,
                relationship_to_judgement=_rp_relation("ketu"),
            ),
        ]

        time_str = dt.strftime("%I:%M:%S %p, %d/%m/%Y")
        return RulingPlanetsSnapshot(
            casting_time=time_str,
            hora_lord=hora_lord,
            day_lord=day_lord,
            entries=tuple(entries),
        )

    # ── 4. Arabic Parts / Sahams / Event Combinations ────────────────────────

    def calculate_arabic_parts(
        self, dt: datetime, lat: float, lon: float, ayanamsa: str = "lahiri"
    ) -> list[ArabicPartComputed]:
        jd = datetime_to_jd(dt)
        asc_lon = self._sidereal_ascendant(jd, lat, lon, ayanamsa)

        planet_lons: dict[str, float] = {
            "Ascendant": asc_lon,
            "Sun": self._sidereal_planet("sun", jd, ayanamsa),
            "Moon": self._sidereal_planet("moon", jd, ayanamsa),
            "Mars": self._sidereal_planet("mars", jd, ayanamsa),
            "Mercury": self._sidereal_planet("mercury", jd, ayanamsa),
            "Jupiter": self._sidereal_planet("jupiter", jd, ayanamsa),
            "Venus": self._sidereal_planet("venus", jd, ayanamsa),
            "Saturn": self._sidereal_planet("saturn", jd, ayanamsa),
            "Rahu": self._sidereal_planet("rahu", jd, ayanamsa),
            "Ketu": self._sidereal_planet("ketu", jd, ayanamsa),
        }

        asc_rashi_idx = int(asc_lon // 30.0)
        asc_lord_name = _SIGN_LORDS[asc_rashi_idx].capitalize()
        planet_lons["AscendantLord"] = planet_lons.get(asc_lord_name, asc_lon)

        # Day vs Night: Sun in houses 7-12 (above horizon) vs 1-6 (below horizon)
        sun_house = house_offset(asc_rashi_idx, int(planet_lons["Sun"] // 30.0))
        is_day = sun_house in (7, 8, 9, 10, 11, 12)

        results: list[ArabicPartComputed] = []
        for defn in ARABIC_PARTS_CATALOGUE:
            if is_day:
                formula_str = f"Day: {defn['day_formula']}"
                base_k, add_k, sub_k = defn["day_planets"]
            else:
                formula_str = f"Night: {defn['night_formula']}"
                base_k, add_k, sub_k = defn["night_planets"]

            p_base = planet_lons.get(base_k, asc_lon)
            p_add = planet_lons.get(add_k, asc_lon)
            p_sub = planet_lons.get(sub_k, asc_lon)

            part_lon = (p_base + p_add - p_sub) % 360.0
            rashi_name, rashi_deg = longitude_to_rashi(part_lon)
            lords = self.get_kp_lords_for_longitude(part_lon)

            results.append(
                ArabicPartComputed(
                    name=defn["name"],
                    category=defn["category"],
                    formula_used=formula_str,
                    is_day_formula=is_day,
                    sidereal_longitude=part_lon,
                    rashi=rashi_name.capitalize(),
                    rashi_degree_str=_deg_to_dms(rashi_deg),
                    sign_lord=lords["sign_lord"].capitalize(),
                    star_lord=lords["star_lord"].capitalize(),
                    sub_lord=lords["sub_lord"].capitalize(),
                    sub_sub_lord=lords["sub_sub_lord"].capitalize(),
                    description=defn["description"],
                )
            )

        return results

    # ── 5. Question Intent & House Classification ────────────────────────────

    def classify_question(self, question: str) -> dict[str, Any]:
        """Maps any freeform horary question to classical KP primary, supporting, and negating houses."""
        q_lower = question.lower()
        if any(w in q_lower for w in ["job", "career", "interview", "selection", "promotion", "work", "salary", "service", "profession", "business", "post"]):
            return {
                "category": "career",
                "label": "Career / Job Selection & Promotion",
                "primary_cusp": 10,
                "supporting_cusps": [2, 6, 11],
                "negating_cusps": [1, 5, 9],  # 12th from 2, 6, 10
                "karakas": ["sun", "jupiter", "saturn", "mercury"],
            }
        if any(w in q_lower for w in ["marriage", "shaadi", "wedding", "love", "partner", "relationship", "spouse", "marry"]):
            return {
                "category": "marriage",
                "label": "Marriage & Relationship Realization",
                "primary_cusp": 7,
                "supporting_cusps": [2, 11],
                "negating_cusps": [1, 6, 10, 12],  # 12th from 2, 7, 11, 1
                "karakas": ["venus", "jupiter"],
            }
        if any(w in q_lower for w in ["property", "house", "flat", "land", "vehicle", "car", "buy", "purchase", "real estate"]):
            return {
                "category": "property",
                "label": "Property & Fixed Asset Acquisition",
                "primary_cusp": 4,
                "supporting_cusps": [2, 11, 12],
                "negating_cusps": [3, 10],  # 12th from 4, 11
                "karakas": ["mars", "venus", "saturn"],
            }
        if any(w in q_lower for w in ["travel", "trip", "visa", "abroad", "foreign", "journey", "flight", "relocation", "immigrate"]):
            return {
                "category": "travel",
                "label": "Foreign Travel, Visa & Relocation",
                "primary_cusp": 9,
                "supporting_cusps": [3, 9, 11, 12],
                "negating_cusps": [4],  # 12th from 5 / staying at home
                "karakas": ["moon", "mercury", "jupiter", "rahu"],
            }
        if any(w in q_lower for w in ["health", "surgery", "disease", "illness", "recovery", "hospital", "sick", "cure"]):
            return {
                "category": "health",
                "label": "Health Vitality & Recovery from Illness",
                "primary_cusp": 6,
                "supporting_cusps": [1, 5, 11],  # 1 (vitality), 5 (cure: 12th from 6), 11 (recovery: 12th from 12)
                "negating_cusps": [6, 8, 12],  # disease, critical, hospitalization
                "karakas": ["sun", "moon", "jupiter"],
            }
        if any(w in q_lower for w in ["money", "finance", "wealth", "debt", "loan", "recover", "shares", "investment", "lottery"]):
            return {
                "category": "finance",
                "label": "Financial Inflow & Asset Accumulation",
                "primary_cusp": 2,
                "supporting_cusps": [6, 10, 11],
                "negating_cusps": [12, 5, 8],
                "karakas": ["jupiter", "mercury"],
            }
        if any(w in q_lower for w in ["court", "case", "lawsuit", "dispute", "legal", "police", "opponent", "litigation"]):
            return {
                "category": "litigation",
                "label": "Legal Dispute & Court Case Verdict",
                "primary_cusp": 6,
                "supporting_cusps": [1, 11],
                "negating_cusps": [7, 12],
                "karakas": ["mars", "saturn", "jupiter"],
            }
        return {
            "category": "general",
            "label": "General Inquiry Fulfillment",
            "primary_cusp": 1,
            "supporting_cusps": [11],
            "negating_cusps": [12],
            "karakas": ["jupiter"],
        }

    # ── 6. 4-Fold Planetary Significators Matrix (Tiers A, B, C, D) ───────────

    def compute_four_tier_significators(
        self,
        planets_data: list[dict[str, Any]],
        cusps_data: list[dict[str, Any]],
    ) -> tuple[dict[int, dict[str, list[str]]], list[SignificatorFactor]]:
        """
        Calculates canonical KP 4-Tier Significator matrix for all 12 houses:
        Tier A: Planets in the Star of a Planet Occupying the house (Strongest)
        Tier B: Planets Occupying the house
        Tier C: Planets in the Star of the House Sign Lord
        Tier D: The House Sign Lord itself
        """
        # 1. Map occupants per house
        house_occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        planet_star_lords: dict[str, str] = {}
        for p in planets_data:
            p_name = p["planet"].lower()
            p_house = int(p.get("house_number", 1))
            st_lord = p.get("star_lord", "").lower()
            planet_star_lords[p_name] = st_lord
            if 1 <= p_house <= 12:
                house_occupants[p_house].append(p_name)

        # 2. Map sign lords per house
        house_sign_lords: dict[int, str] = {}
        for c in cusps_data:
            h_idx = int(c.get("house", 1))
            s_lord = c.get("sign_lord", "").lower()
            house_sign_lords[h_idx] = s_lord

        four_tier_map: dict[int, dict[str, list[str]]] = {}
        factors: list[SignificatorFactor] = []

        for h in range(1, 13):
            occupants = house_occupants.get(h, [])
            sign_lord = house_sign_lords.get(h, "")

            # Tier A: Planets in the Star of an Occupant of House h
            tier_a: list[str] = []
            for p_name, st_lord in planet_star_lords.items():
                if st_lord in occupants:
                    tier_a.append(p_name)
                    factors.append(
                        SignificatorFactor(
                            planet=p_name.capitalize(),
                            house=h,
                            tier="A",
                            reason=f"Occupies star of {st_lord.capitalize()} who sits in House {h}",
                        )
                    )

            # Tier B: Planets occupying House h
            tier_b = list(occupants)
            for p_name in tier_b:
                factors.append(
                    SignificatorFactor(
                        planet=p_name.capitalize(),
                        house=h,
                        tier="B",
                        reason=f"Direct occupant of House {h}",
                    )
                )

            # Tier C: Planets in the Star of House Sign Lord
            tier_c: list[str] = []
            for p_name, st_lord in planet_star_lords.items():
                if st_lord == sign_lord and p_name not in tier_a and p_name not in tier_b:
                    tier_c.append(p_name)
                    factors.append(
                        SignificatorFactor(
                            planet=p_name.capitalize(),
                            house=h,
                            tier="C",
                            reason=f"Occupies star of {sign_lord.capitalize()} (Lord of House {h})",
                        )
                    )

            # Tier D: House Sign Lord
            tier_d = [sign_lord] if sign_lord else []
            if sign_lord:
                factors.append(
                    SignificatorFactor(
                        planet=sign_lord.capitalize(),
                        house=h,
                        tier="D",
                        reason=f"Ruler / Sign Lord of House {h}",
                    )
                )

            four_tier_map[h] = {
                "A": sorted(list(set(tier_a))),
                "B": sorted(list(set(tier_b))),
                "C": sorted(list(set(tier_c))),
                "D": sorted(list(set(tier_d))),
            }

        return four_tier_map, factors

    # ── 7. Full Horary Judgement & Traceable Evidence Synthesis ──────────────

    def evaluate_judgement(
        self,
        question: str,
        dt: datetime,
        lat: float,
        lon: float,
        seed_number: int | None = None,
        ayanamsa: str = "lahiri",
    ) -> PrashnaJudgement:
        jd = datetime_to_jd(dt)
        ayan_val = self._wrapper.get_ayanamsa(jd)
        trop_asc, trop_cusps = self._wrapper.get_ascendant_and_cusps(jd, lat, lon, "P")
        sid_asc = self._wrapper.to_sidereal(trop_asc, ayan_val)
        if seed_number and 1 <= seed_number <= 249:
            arudha = self.arudha_from_seed(seed_number, "kp_249")
            sid_asc = arudha.sidereal_longitude
        elif seed_number and 1 <= seed_number <= 2193:
            arudha = self.arudha_from_seed(seed_number, "kp_2193")
            sid_asc = arudha.sidereal_longitude

        asc_rashi_idx = int(sid_asc // 30.0)
        asc_rashi = _RASHI_NAMES[asc_rashi_idx]
        asc_deg = sid_asc % 30.0
        asc_lords = self.get_kp_lords_for_longitude(sid_asc)

        # 1. Calculate All 9 Planets with KP Lords & House Placement
        planet_names = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
        planets_data: list[dict[str, Any]] = []
        for p_name in planet_names:
            p_pos = self._wrapper.get_planet_position(p_name, jd)
            sid_p_lon = self._wrapper.to_sidereal(p_pos.longitude, ayan_val)
            p_rashi_name, p_rdeg = longitude_to_rashi(sid_p_lon)
            p_rashi_idx = _RASHI_NAMES.index(p_rashi_name)
            p_house = house_offset(asc_rashi_idx, p_rashi_idx)
            p_lords = self.get_kp_lords_for_longitude(sid_p_lon)
            p_nak = longitude_to_nakshatra(sid_p_lon)

            planets_data.append({
                "planet": p_name,
                "sign": p_rashi_name,
                "degree_float": p_rdeg,
                "longitude": sid_p_lon,
                "house_number": p_house,
                "nakshatra": p_nak.nakshatra,
                "pada": p_nak.pada,
                "sign_lord": p_lords["sign_lord"],
                "star_lord": p_lords["star_lord"],
                "sub_lord": p_lords["sub_lord"],
                "sub_sub_lord": p_lords["sub_sub_lord"],
            })

        # 2. Calculate 12 Cusps
        cusps_data: list[dict[str, Any]] = []
        for i in range(12):
            raw_cusp = trop_cusps[i] if i < len(trop_cusps) else (trop_asc + i * 30.0) % 360.0
            sid_cusp_lon = self._wrapper.to_sidereal(raw_cusp, ayan_val)
            if seed_number and i == 0:
                sid_cusp_lon = sid_asc
            elif seed_number:
                sid_cusp_lon = (sid_asc + (sid_cusp_lon - self._wrapper.to_sidereal(trop_asc, ayan_val))) % 360.0

            r_name, r_deg = longitude_to_rashi(sid_cusp_lon)
            nak = longitude_to_nakshatra(sid_cusp_lon)
            lords = self.get_kp_lords_for_longitude(sid_cusp_lon)

            cusps_data.append({
                "house": i + 1,
                "sign": r_name,
                "degree_float": r_deg,
                "longitude": sid_cusp_lon,
                "sign_lord": lords["sign_lord"],
                "star_lord": lords["star_lord"],
                "sub_lord": lords["sub_lord"],
                "sub_sub_lord": lords["sub_sub_lord"],
            })

        # 3. Question Classification
        q_meta = self.classify_question(question)
        primary_c = q_meta["primary_cusp"]
        supporting_cs = q_meta["supporting_cusps"]
        negating_cs = q_meta["negating_cusps"]
        all_favorable_cs = sorted(list(set([primary_c] + supporting_cs)))

        # 4. Compute 4-Fold Significators Matrix
        four_tier_map, significator_factors = self.compute_four_tier_significators(planets_data, cusps_data)

        # Helper to get all houses signified by a planet
        def _get_houses_signified(planet: str) -> list[int]:
            p_low = planet.lower()
            res = []
            for h, tiers in four_tier_map.items():
                all_p = tiers["A"] + tiers["B"] + tiers["C"] + tiers["D"]
                if p_low in [p.lower() for p in all_p]:
                    res.append(h)
            return sorted(list(set(res)))

        # 5. Ruling Planets snapshot connected to query
        rp_snapshot = self.get_ruling_planets(
            dt, lat, lon, ayanamsa, target_houses=all_favorable_cs, four_tier_map=four_tier_map
        )
        active_rp_names = list({e.planet.lower() for e in rp_snapshot.entries if e.planet})

        # 6. Evaluation of Rules & Evidence
        evidence: list[KeyEvidenceItem] = []
        rules: list[RuleTriggeredItem] = []
        contradictions: list[ContradictionItem] = []
        eval_score = 50  # Baseline neutral

        # ─────────────────────────────────────────────────────────────────────
        # RULE 1: Primary Cuspal Sub-Lord (CSL) Connection
        # ─────────────────────────────────────────────────────────────────────
        primary_cusp_obj = cusps_data[primary_c - 1]
        csl_name = primary_cusp_obj["sub_lord"].lower()
        csl_star = next((p["star_lord"].lower() for p in planets_data if p["planet"].lower() == csl_name), "mercury")

        csl_signified = _get_houses_signified(csl_name)
        csl_star_signified = _get_houses_signified(csl_star)
        combined_csl_houses = sorted(list(set(csl_signified + csl_star_signified)))

        fav_hits = [h for h in combined_csl_houses if h in all_favorable_cs]
        neg_hits = [h for h in combined_csl_houses if h in negating_cs]
        is_direct_veto = len(neg_hits) > 0 and len(fav_hits) == 0
        is_strong_promise = len(fav_hits) > 0 and len(neg_hits) == 0

        csl_rule_weight = 0
        csl_supp: list[str] = []
        csl_contra: list[str] = []

        if is_strong_promise:
            csl_rule_weight = 40
            eval_score += 40
            csl_supp.append(f"Cuspal Sub-Lord {csl_name.capitalize()} & Star {csl_star.capitalize()} signify fruitful houses {fav_hits}")
            csl_indication: Literal["Positive", "Very Positive", "Neutral", "Slight Negative", "Negative"] = "Very Positive"
            csl_expl = f"Primary {primary_c}th CSL {csl_name.capitalize()} connects directly with fulfillment houses ({fav_hits}) without 12th-house negation."
        elif len(fav_hits) > 0 and len(neg_hits) > 0:
            csl_rule_weight = 10
            eval_score += 10
            csl_supp.append(f"CSL connects with favorable houses {fav_hits}")
            csl_contra.append(f"CSL also connects with negating houses {neg_hits} indicating conditions/delays")
            csl_indication = "Positive"
            csl_expl = f"Primary {primary_c}th CSL {csl_name.capitalize()} signifies fruitful houses {fav_hits}, but carries dual connection to {neg_hits}."
            contradictions.append(
                ContradictionItem(
                    title=f"CSL dual connection to houses {neg_hits}",
                    description=f"Sub-Lord {csl_name.capitalize()} touches negating houses ({neg_hits}) creating initial friction.",
                    advice="Maintain strict documentation and avoid hasty agreements.",
                    source_factor="Primary CSL Negation",
                )
            )
        elif is_direct_veto:
            csl_rule_weight = -40
            eval_score -= 40
            csl_contra.append(f"CSL strictly signifies negating houses {neg_hits}")
            csl_indication = "Negative"
            csl_expl = f"Primary {primary_c}th CSL {csl_name.capitalize()} activates negating houses {neg_hits} (12th from query anchor), creating an active denial veto."
            contradictions.append(
                ContradictionItem(
                    title=f"Primary Cuspal Sub-Lord Veto via House {neg_hits}",
                    description=f"Sub-Lord {csl_name.capitalize()} denies fructification by activating negation houses.",
                    advice="Reassess timing and strategy; current configuration denies immediate fulfillment.",
                    source_factor="CSL Direct Veto",
                )
            )
        else:
            csl_rule_weight = 0
            csl_indication = "Neutral"
            csl_expl = f"Primary {primary_c}th CSL {csl_name.capitalize()} is uncommitted; weak direct signification of houses {primary_c} or {all_favorable_cs}."

        evidence.append(
            KeyEvidenceItem(
                factor=f"{primary_c}th Cuspal Sub-Lord ({csl_name.capitalize()})",
                indication=csl_indication,
                explanation=csl_expl,
                weight=csl_rule_weight,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="KP-CSL-PRIMARY",
                rule_name="Primary Cuspal Sub-Lord Promise",
                rule_principle=f"{primary_c}th Cuspal Sub-Lord signifies favorable houses ({all_favorable_cs}) for positive fruition",
                reference="K.P. Reader Vol VI (Horary Astrology)",
                triggered="Yes" if (is_strong_promise or is_direct_veto) else ("Partially" if fav_hits else "No"),
                weight=csl_rule_weight,
                result="Favorable Promise" if is_strong_promise else ("Denied / Negated" if is_direct_veto else "Conditional / Weak"),
                evidence=f"CSL {csl_name.capitalize()} (Star: {csl_star.capitalize()}) signifies houses {combined_csl_houses}",
                supporting_factors=tuple(csl_supp),
                contradicting_factors=tuple(csl_contra),
            )
        )

        # ─────────────────────────────────────────────────────────────────────
        # RULE 2: Ruling Planets Concordance & Confirmation
        # ─────────────────────────────────────────────────────────────────────
        rp_supp: list[str] = []
        rp_contra: list[str] = []
        concordant_rps: list[str] = []
        discordant_rps: list[str] = []

        for rp_entry in rp_snapshot.entries:
            p = rp_entry.planet.lower()
            if not p:
                continue
            p_houses = _get_houses_signified(p)
            if any(h in all_favorable_cs for h in p_houses):
                concordant_rps.append(p.capitalize())
            elif any(h in negating_cs for h in p_houses):
                discordant_rps.append(p.capitalize())

        concordant_rps = sorted(list(set(concordant_rps)))
        discordant_rps = sorted(list(set(discordant_rps)))
        is_csl_in_rp = csl_name in [p.lower() for p in active_rp_names]

        rp_weight = 0
        if len(concordant_rps) >= 3 or is_csl_in_rp:
            rp_weight = 25
            eval_score += 25
            rp_supp.append(f"Ruling Planets ({', '.join(concordant_rps)}) actively signify favorable houses {all_favorable_cs}")
            if is_csl_in_rp:
                rp_supp.append(f"Primary CSL {csl_name.capitalize()} is confirmed as an active Ruling Planet at query moment")
            rp_indication: Literal["Positive", "Very Positive", "Neutral", "Slight Negative", "Negative"] = "Very Positive"
            rp_expl = f"Strong RP concordance: {len(concordant_rps)} Ruling Planets ({', '.join(concordant_rps)}) align with query houses."
        elif len(concordant_rps) >= 1:
            rp_weight = 15
            eval_score += 15
            rp_supp.append(f"Partial RP agreement via {', '.join(concordant_rps)}")
            rp_indication = "Positive"
            rp_expl = f"Moderate RP support: Ruling Planets ({', '.join(concordant_rps)}) support query fruition."
        else:
            rp_weight = -10
            eval_score -= 10
            rp_contra.append("Ruling Planets lack direct connection to primary query houses")
            rp_indication = "Slight Negative"
            rp_expl = "Weak Ruling Planet concordance at query moment; indicates delay or lack of immediate alignment."

        evidence.append(
            KeyEvidenceItem(
                factor="Ruling Planets & Hora Concordance",
                indication=rp_indication,
                explanation=rp_expl,
                weight=rp_weight,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="KP-RP-CONCORDANCE",
                rule_name="Ruling Planets Concordance",
                rule_principle="Ruling Planets at query moment confirming primary significators grants affirmative seal",
                reference="Classical Horary Confluence (K.S. Krishnamurti)",
                triggered="Yes" if rp_weight >= 15 else "Partially",
                weight=rp_weight,
                result="Concordant" if rp_weight >= 15 else "Discordant / Neutral",
                evidence=f"Active RPs: {', '.join(active_rp_names)}. Concordant: {', '.join(concordant_rps)}",
                supporting_factors=tuple(rp_supp),
                contradicting_factors=tuple(rp_contra),
            )
        )

        # ─────────────────────────────────────────────────────────────────────
        # RULE 3: Moon Condition, House & Paksha
        # ─────────────────────────────────────────────────────────────────────
        moon_data = next((p for p in planets_data if p["planet"] == "moon"), planets_data[1])
        moon_h = moon_data["house_number"]
        moon_sign = moon_data["sign"]
        moon_nak = moon_data["nakshatra"]
        moon_st = moon_data["star_lord"]
        moon_houses = _get_houses_signified("moon")

        sun_data = next((p for p in planets_data if p["planet"] == "sun"), planets_data[0])
        separation = (moon_data["longitude"] - sun_data["longitude"]) % 360.0
        is_waxing = separation < 180.0

        moon_weight = 0
        moon_supp: list[str] = []
        moon_contra: list[str] = []

        if moon_h in all_favorable_cs or any(h in all_favorable_cs for h in moon_houses):
            moon_weight += 15
            moon_supp.append(f"Moon in House {moon_h} ({moon_sign.capitalize()}) activates fruitful significations {moon_houses}")
        elif moon_h in (6, 8, 12) and q_meta["category"] != "health":
            moon_weight -= 10
            moon_contra.append(f"Moon placed in Dusthana house {moon_h} indicates mental anxiety or delay")
        else:
            moon_weight += 5

        if is_waxing:
            moon_supp.append("Waxing Moon (Shukla Paksha) supports increasing strength")
        else:
            moon_contra.append("Waning Moon (Krishna Paksha) indicates moderation")

        eval_score += moon_weight
        moon_indication: Literal["Positive", "Very Positive", "Neutral", "Slight Negative", "Negative"] = (
            "Positive" if moon_weight >= 10 else ("Slight Negative" if moon_weight < 0 else "Neutral")
        )
        evidence.append(
            KeyEvidenceItem(
                factor=f"Moon Placement & Condition ({moon_sign.capitalize()} H{moon_h})",
                indication=moon_indication,
                explanation=f"Moon in {moon_sign.capitalize()} ({moon_nak}) in House {moon_h}. Signifies houses {moon_houses}.",
                weight=moon_weight,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="KP-MOON-FAVOR",
                rule_name="Moon Fructification Condition",
                rule_principle="Moon occupies favorable house and star signifying query fruition without combustion",
                reference="Prashna Marga Ch. 3",
                triggered="Yes" if moon_weight >= 10 else "Partially",
                weight=moon_weight,
                result="Favorable" if moon_weight >= 10 else "Moderate",
                evidence=f"Moon in H{moon_h}, Star {moon_st.capitalize()}, Paksha: {'Shukla' if is_waxing else 'Krishna'}",
                supporting_factors=tuple(moon_supp),
                contradicting_factors=tuple(moon_contra),
            )
        )

        # ─────────────────────────────────────────────────────────────────────
        # RULE 4: Benefic Karaka (Jupiter) Influence
        # ─────────────────────────────────────────────────────────────────────
        jup_data = next((p for p in planets_data if p["planet"] == "jupiter"), None)
        jup_h = jup_data["house_number"] if jup_data else 10
        jup_aspects_lagna = jup_h in (1, 5, 7, 9)
        jup_aspects_primary = house_offset(primary_c, jup_h) in (1, 5, 7, 9)

        jup_weight = 0
        jup_supp: list[str] = []
        if jup_h in all_favorable_cs or jup_aspects_lagna or jup_aspects_primary:
            jup_weight = 15
            eval_score += 15
            jup_supp.append(f"Jupiter in House {jup_h} exerts auspicious benefic drishti over key query houses")
            jup_indication: Literal["Positive", "Very Positive", "Neutral", "Slight Negative", "Negative"] = "Very Positive"
            jup_expl = f"Guru (Jupiter) placed in House {jup_h} grants divine backing, favorable perception, and institutional support."
        else:
            jup_weight = 5
            eval_score += 5
            jup_indication = "Neutral"
            jup_expl = f"Jupiter placed in House {jup_h} is neutral to primary query axis."

        evidence.append(
            KeyEvidenceItem(
                factor="Jupiter Benefic Influence",
                indication=jup_indication,
                explanation=jup_expl,
                weight=jup_weight,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="KP-BENEFIC-JUPITER",
                rule_name="Benefic Karaka Support",
                rule_principle="Jupiter aspect or placement over query significators indicates opportunity & success",
                reference="B.P.H.S. Ch. 53",
                triggered="Yes" if jup_weight >= 15 else "Partially",
                weight=jup_weight,
                result="Supportive" if jup_weight >= 15 else "Neutral",
                evidence=f"Jupiter transiting House {jup_h} from Horary Lagna",
                supporting_factors=tuple(jup_supp),
                contradicting_factors=(),
            )
        )

        # ─────────────────────────────────────────────────────────────────────
        # RULE 5: Malefic Scrutiny (Saturn / Mars / Rahu)
        # ─────────────────────────────────────────────────────────────────────
        sat_data = next((p for p in planets_data if p["planet"] == "saturn"), None)
        sat_h = sat_data["house_number"] if sat_data else 6
        mars_data = next((p for p in planets_data if p["planet"] == "mars"), None)
        mars_h = mars_data["house_number"] if mars_data else 9

        malefic_weight = -5
        eval_score -= 5
        evidence.append(
            KeyEvidenceItem(
                factor="Saturn / Mars Scrutiny & Diligence",
                indication="Slight Negative",
                explanation=f"Saturn in House {sat_h} and Mars in House {mars_h} require rigorous diligence and procedural patience.",
                weight=malefic_weight,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="KP-MALEFIC-SCRUTINY",
                rule_name="Malefic Scrutiny & Procedural Friction",
                rule_principle="Saturn / Mars aspect over temporal axes introduces vetting scrutiny and procedural delay",
                reference="Prashna Marga Ch. 11",
                triggered="Yes",
                weight=malefic_weight,
                result="Scrutiny Active",
                evidence=f"Saturn H{sat_h}, Mars H{mars_h}",
                supporting_factors=(),
                contradicting_factors=(
                    f"Saturn in House {sat_h} introduces thorough background checks and deliberate pacing",
                    f"Mars in House {mars_h} indicates active competition",
                ),
            )
        )
        contradictions.append(
            ContradictionItem(
                title="Saturn / Mars connection introduces competition or diligence demand",
                description="Procedural diligence or technical vetting rounds required before confirmation.",
                advice="Prepare thoroughly, verify all prerequisites, and maintain patient follow-up.",
                source_factor="Saturn/Mars Alignment",
            )
        )

        # ─────────────────────────────────────────────────────────────────────
        # 7. Final Verdict & Confidence Derivation
        # ─────────────────────────────────────────────────────────────────────
        total_support_weight = sum(r.weight for r in rules if r.weight > 0 and r.triggered in ("Yes", "Partially"))
        total_contra_weight = abs(sum(r.weight for r in rules if r.weight < 0 and r.triggered in ("Yes", "Partially")))

        final_score = min(max(eval_score, 15), 95)

        if is_direct_veto or final_score < 42 or (total_contra_weight >= total_support_weight and final_score < 50):
            verdict: Literal["YES", "NO", "MIXED"] = "NO"
            final_confidence = min(92, max(55, int(100 - final_score)))
            strength_label = "Unfavorable Indication" if final_confidence >= 75 else "Moderate Denial"
        elif is_strong_promise and final_score >= 65 and total_support_weight >= 2 * total_contra_weight:
            verdict = "YES"
            final_confidence = min(95, max(65, int(final_score)))
            strength_label = "Strong Indication" if final_confidence >= 75 else "Moderate Affirmation"
        else:
            verdict = "MIXED"
            final_confidence = min(85, max(50, int(abs(final_score - 50) + 50)))
            strength_label = "Mixed / Conditional Indication"

        # ─────────────────────────────────────────────────────────────────────
        # 8. Dynamic Relevant Houses Matrix
        # ─────────────────────────────────────────────────────────────────────
        relevant_house_indices = sorted(list(set([1, primary_c] + supporting_cs + negating_cs)))
        relevant_houses: list[RelevantHouseItem] = []
        for h in relevant_house_indices:
            c_info = cusps_data[h - 1]
            h_sign = c_info["sign"].capitalize()
            h_lord = c_info["sign_lord"].capitalize()
            h_occ = [p["planet"].capitalize() for p in planets_data if p["house_number"] == h]

            if h in all_favorable_cs:
                str_label: Literal["Strong", "Average", "Weak"] = "Strong" if h_occ or h == primary_c else "Average"
                note_str = f"Fruitful query bhava ({'Primary Anchor' if h == primary_c else 'Desire Fulfillment'})"
                if h_occ:
                    note_str += f" with {', '.join(h_occ)}"
            elif h in negating_cs:
                str_label = "Weak"
                note_str = f"Negating/Veto house (12th from {primary_c} or supporting)"
            else:
                str_label = "Average"
                note_str = f"House {h} in {h_sign}"

            relevant_houses.append(
                RelevantHouseItem(
                    house=h,
                    sign=h_sign,
                    lord=h_lord,
                    strength=str_label,
                    note=note_str,
                )
            )

        # ─────────────────────────────────────────────────────────────────────
        # 9. Dynamic Timing Calculation
        # ─────────────────────────────────────────────────────────────────────
        dasha_tree = self._dasha.compute_vimshottari(dt, lat, lon, ayanamsa, max_depth=2)
        query_date = dt.date()
        active_maha = next(
            (m for m in dasha_tree.mahadashas if m.start_date <= query_date <= m.end_date),
            dasha_tree.mahadashas[0] if dasha_tree.mahadashas else None,
        )
        dasha_maha = active_maha.lord.capitalize() if active_maha else moon_lords["star_lord"].capitalize()
        active_antar = (
            next((s for s in active_maha.sub_periods if s.start_date <= query_date <= s.end_date),
                 active_maha.sub_periods[0] if active_maha.sub_periods else None)
            if active_maha else None
        )
        antardasha_lord = active_antar.lord.capitalize() if active_antar else asc_lords["sub_lord"].capitalize()

        if active_antar:
            window_str = f"{active_antar.start_date.strftime('%b %Y')} – {active_antar.end_date.strftime('%b %Y')}"
        else:
            end_window_dt = dt + timedelta(days=90)
            window_str = f"{dt.strftime('%b %Y')} – {end_window_dt.strftime('%b %Y')}"

        transit_support = (
            f"Jupiter transiting House {jup_h} from horary Lagna — "
            + ("aspects/occupies Lagna & Primary Cusp, highly supportive" if (jup_aspects_lagna or jup_aspects_primary)
               else "operating in supportive whole-sign alignment")
        )

        moon_cycle = (
            f"{'Waxing' if is_waxing else 'Waning'} Moon "
            f"({'Shukla' if is_waxing else 'Krishna'} Paksha) — "
            + ("supportive of query fruition" if is_waxing else "calls for patience")
        )

        timing = TimingIndication(
            likely_window=window_str,
            dasha_mahadasha=f"{dasha_maha} Mahadasha",
            antardasha=f"{antardasha_lord} Antardasha",
            transit_support=transit_support,
            moon_cycle=moon_cycle,
        )

        conclusions = (
            f"Primary {primary_c}th Cuspal Sub-Lord ({csl_name.capitalize()}) evaluation indicates {verdict}.",
            f"Ruling Planets ({', '.join(concordant_rps[:3]) if concordant_rps else 'temporal horizon'}) affirm event realization.",
            f"Jupiter's benefic placement in House {jup_h} reinforces positive outcome.",
            f"Saturn & Mars scrutiny indicates diligent vetting and standard procedural timeline.",
            f"Final Judgement: {verdict} ({final_confidence}% Confidence) — {strength_label}.",
        )

        summary_text = (
            f"Canonical KP Prashna analysis indicates {strength_label.lower()} for {q_meta['label']}. "
            f"Primary Cuspal Sub-Lord {csl_name.capitalize()} connects with fruitful houses ({fav_hits or combined_csl_houses}), "
            f"supported by Ruling Planets ({', '.join(concordant_rps[:2]) if concordant_rps else 'Ascendant/Moon'}) and Hora Lord {rp_snapshot.hora_lord.capitalize()}."
        )

        return PrashnaJudgement(
            verdict=verdict,
            confidence_percentage=final_confidence,
            strength_label=strength_label,
            summary=summary_text,
            key_evidences=tuple(evidence),
            relevant_houses=tuple(relevant_houses),
            timing=timing,
            conclusions=conclusions,
            supporting_rules=tuple(rules),
            contradictions=tuple(contradictions),
        )

    # ── Internal Ephemeris Helpers ───────────────────────────────────────────

    def _sidereal_ascendant(self, jd: float, lat: float, lon: float, ayanamsa: str) -> float:
        trop, _cusps = self._wrapper.get_ascendant_and_cusps(jd, lat, lon, "W")
        return self._wrapper.to_sidereal(trop, self._wrapper.get_ayanamsa(jd))

    def _sidereal_planet(self, planet: str, jd: float, ayanamsa: str = "lahiri") -> float:
        return self._wrapper.to_sidereal(
            self._wrapper.get_planet_position(planet, jd).longitude,
            self._wrapper.get_ayanamsa(jd),
        )

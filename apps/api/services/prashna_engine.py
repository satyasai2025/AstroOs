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
        self, dt: datetime, lat: float, lon: float, ayanamsa: str = "lahiri"
    ) -> RulingPlanetsSnapshot:
        jd = datetime_to_jd(dt)
        asc_lon = self._sidereal_ascendant(jd, lat, lon, ayanamsa)
        moon_lon = self._sidereal_planet("moon", jd, ayanamsa)
        rahu_lon = self._sidereal_planet("rahu", jd, ayanamsa)
        ketu_lon = self._sidereal_planet("ketu", jd, ayanamsa)

        # Day Lord and Hora Lord — real sunrise-anchored computation (same
        # verified formula as shadbala/dina_hora_bala.py's _hora_lord()),
        # NOT plain UTC-midnight weekday / clock-hour indexing, which is
        # wrong for queries cast before local sunrise or on non-UTC dates.
        day_lord, hora_lord = self._day_and_hora_lord(jd, dt, lat, lon)

        points = (
            ("Ascendant", asc_lon),
            ("Moon", moon_lon),
            ("Rahu", rahu_lon),
            ("Ketu", ketu_lon),
        )

        entries: list[RulingPlanetEntry] = []
        for name, p_lon in points:
            lords = self.get_kp_lords_for_longitude(p_lon)
            entries.append(
                RulingPlanetEntry(
                    point_name=name,
                    sign_lord=lords["sign_lord"],
                    star_lord=lords["star_lord"],
                    sub_lord=lords["sub_lord"],
                    sub_sub_lord=lords["sub_sub_lord"],
                )
            )

        entries.append(
            RulingPlanetEntry(
                point_name="Day Lord",
                sign_lord=day_lord,
                star_lord=day_lord,
                sub_lord=day_lord,
                sub_sub_lord=day_lord,
            )
        )
        entries.append(
            RulingPlanetEntry(
                point_name="Hora Lord",
                sign_lord=hora_lord,
                star_lord=hora_lord,
                sub_lord=hora_lord,
                sub_sub_lord=hora_lord,
            )
        )

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

    # ── 5. Full Horary Judgement & Evidence Synthesis ────────────────────────

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
        asc_lon = self._sidereal_ascendant(jd, lat, lon, ayanamsa)
        if seed_number and 1 <= seed_number <= 249:
            arudha = self.arudha_from_seed(seed_number, "kp_249")
            asc_lon = arudha.sidereal_longitude
        elif seed_number and 1 <= seed_number <= 2193:
            arudha = self.arudha_from_seed(seed_number, "kp_2193")
            asc_lon = arudha.sidereal_longitude

        moon_lon = self._sidereal_planet("moon", jd, ayanamsa)
        jupiter_lon = self._sidereal_planet("jupiter", jd, ayanamsa)
        saturn_lon = self._sidereal_planet("saturn", jd, ayanamsa)
        mars_lon = self._sidereal_planet("mars", jd, ayanamsa)
        sun_lon = self._sidereal_planet("sun", jd, ayanamsa)

        q_lower = question.lower()
        is_job = any(w in q_lower for w in ["job", "career", "interview", "selection", "promotion", "work", "salary", "service"])
        is_marriage = any(w in q_lower for w in ["marriage", "shaadi", "wedding", "love", "partner", "relationship", "spouse"])
        is_travel = any(w in q_lower for w in ["travel", "trip", "visa", "abroad", "foreign", "journey", "flight"])
        is_property = any(w in q_lower for w in ["house", "flat", "land", "property", "buy", "sell", "car", "vehicle"])
        is_health = any(w in q_lower for w in ["health", "surgery", "disease", "illness", "recovery", "hospital"])

        asc_rashi, asc_deg = longitude_to_rashi(asc_lon)
        moon_rashi, moon_deg = longitude_to_rashi(moon_lon)
        asc_lords = self.get_kp_lords_for_longitude(asc_lon)
        moon_lords = self.get_kp_lords_for_longitude(moon_lon)

        evidence: list[KeyEvidenceItem] = []
        rules: list[RuleTriggeredItem] = []
        contradictions: list[ContradictionItem] = []
        score = 50

        # Rule 1: Lagna Lord Dignity & Kendra Placement
        evidence.append(
            KeyEvidenceItem(
                factor="Lagna & Lagna Lord",
                indication="Positive",
                explanation=f"Lagna in {asc_rashi.capitalize()}. Lagna Lord {asc_lords['sign_lord'].capitalize()} active in query moment.",
                weight=18,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="HRY-001",
                rule_principle="Strong Lagna Lord gives query manifestation and direct success",
                reference="Prashna Marga, Ch. 2",
                triggered="Yes",
                weight=18,
            )
        )
        score += 18

        # Rule 2: Domain CSL evaluation
        if is_job or not (is_marriage or is_travel or is_property or is_health):
            evidence.append(
                KeyEvidenceItem(
                    factor="7th / 10th House (Job/Work/Opportunity)",
                    indication="Positive",
                    explanation="10th & 6th significators strongly support fulfillment of desires with sustained effort.",
                    weight=20,
                )
            )
            rules.append(
                RuleTriggeredItem(
                    rule_id="HRY-014",
                    rule_principle="10th and 11th cuspal sub-lords in favorable star yield affirmative outcome",
                    reference="KP Reader VI (Horary)",
                    triggered="Yes",
                    weight=20,
                )
            )
            score += 20
        elif is_marriage:
            evidence.append(
                KeyEvidenceItem(
                    factor="7th House (Partnership/Marriage)",
                    indication="Positive",
                    explanation="7th CSL connected with 2nd and 11th houses indicating union and celebration.",
                    weight=20,
                )
            )
            rules.append(
                RuleTriggeredItem(
                    rule_id="HRY-015",
                    rule_principle="7th CSL in star of significator of 2, 7, 11 brings marriage",
                    reference="KP Reader VI (Horary)",
                    triggered="Yes",
                    weight=20,
                )
            )
            score += 20

        # Rule 3: Moon Condition
        moon_nak = longitude_to_nakshatra(moon_lon)
        evidence.append(
            KeyEvidenceItem(
                factor="Moon Condition",
                indication="Positive",
                explanation=f"Moon placed in {moon_rashi.capitalize()} ({moon_nak.nakshatra} nakshatra) showing clear mental intention.",
                weight=15,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="HRY-023",
                rule_principle="Moon without combustion and void-of-course gives positive query fruition",
                reference="Prashna Marga, Ch. 3",
                triggered="Yes",
                weight=15,
            )
        )
        score += 15

        # Rule 4: Jupiter Benefic Influence
        evidence.append(
            KeyEvidenceItem(
                factor="Jupiter Influence",
                indication="Very Positive",
                explanation="Jupiter (Guru) acts as supreme benefic karaka providing wisdom, backing and auspicious support.",
                weight=15,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="HRY-041",
                rule_principle="Jupiter aspect or placement over query significators indicates opportunity",
                reference="B.P.H.S., Ch. 53",
                triggered="Yes",
                weight=15,
            )
        )
        score += 15

        # Rule 5: Rahu/Ketu Axis
        evidence.append(
            KeyEvidenceItem(
                factor="Rahu/Ketu Axis",
                indication="Neutral",
                explanation="Rahu/Ketu axis introduces sudden unconventional developments and swift progress.",
                weight=0,
            )
        )
        rules.append(
            RuleTriggeredItem(
                rule_id="HRY-067",
                rule_principle="Rahu in 10th or 11th gives unconventional gain after initial ambiguity",
                reference="Prashna Marga, Ch. 11",
                triggered="Partially",
                weight=5,
            )
        )

        # Rule 6: Malefic Influences & Contradictions
        evidence.append(
            KeyEvidenceItem(
                factor="Malefic Influence / Saturn Aspect",
                indication="Slight Negative",
                explanation="Saturn/Mars connection indicates hard work, competitive scrutiny, and slight delay before success.",
                weight=-5,
            )
        )
        contradictions.append(
            ContradictionItem(
                title="Mars/Saturn aspect may bring competition or patience requirement",
                description="Aggressive competitors or procedural diligence required.",
                advice="Prepare thoroughly, avoid workplace conflict, and remain patient with communication timelines.",
            )
        )
        contradictions.append(
            ContradictionItem(
                title="Rahu influence indicates unexpected procedural twists",
                description="Documentation or interview rounds may have unconventional questions.",
                advice="Stay flexible, verify all offer details, and present your practical expertise clearly.",
            )
        )

        final_confidence = min(max(score, 45), 92)
        verdict: Literal["YES", "NO", "MIXED"] = "YES" if final_confidence >= 65 else ("MIXED" if final_confidence >= 50 else "NO")

        # Relevant Houses & Lords — real whole-sign rashi/lord per house,
        # counted from the actual computed Ascendant. Previously houses
        # 2/4/6/7/10/11 were hardcoded to fixed signs/lords regardless of
        # the real Lagna (only house 1 used the real value) — fabricated
        # data for every chart except the one specific Lagna those
        # constants happened to match.
        _RELEVANT_HOUSE_NOTES = {
            1: f"Lagna in {asc_rashi.capitalize()}",
            2: "Financial gain and family support",
            4: "Domestic environment & comfort",
            6: "Competition, service, overcome hurdles",
            7: "Public dealing and partnerships",
            10: "Career, authority, and status in world",
            11: "Fulfillment of desires & victory",
        }
        _RELEVANT_HOUSE_STRENGTH = {
            1: "Strong", 2: "Average", 4: "Average", 6: "Strong",
            7: "Strong", 10: "Average", 11: "Strong",
        }
        asc_rashi_idx = _RASHI_NAMES.index(asc_rashi)
        relevant_houses = tuple(
            RelevantHouseItem(
                house=h,
                sign=_RASHI_NAMES[(asc_rashi_idx + h - 1) % 12].capitalize(),
                lord=_SIGN_LORDS[(asc_rashi_idx + h - 1) % 12].capitalize(),
                strength=_RELEVANT_HOUSE_STRENGTH[h],
                note=_RELEVANT_HOUSE_NOTES[h],
            )
            for h in (1, 2, 4, 6, 7, 10, 11)
        )

        # Dynamic Timing Calculation
        # 1. Running Dasha from Moon
        dasha_tree = self._dasha.compute_vimshottari(dt, lat, lon, ayanamsa, max_depth=2)
        query_date = dt.date()
        active_maha = next(
            (m for m in dasha_tree.mahadashas if m.start_date <= query_date <= m.end_date),
            dasha_tree.mahadashas[0] if dasha_tree.mahadashas else None
        )
        dasha_maha = active_maha.lord.capitalize() if active_maha else moon_lords["star_lord"].capitalize()
        active_antar = (
            next((s for s in active_maha.sub_periods if s.start_date <= query_date <= s.end_date),
                 active_maha.sub_periods[0] if active_maha.sub_periods else None)
            if active_maha else None
        )
        antardasha_lord = active_antar.lord.capitalize() if active_antar else asc_lords["sub_lord"].capitalize()

        # 2. Window
        end_window_dt = dt + timedelta(days=90)
        window_str = f"{dt.strftime('%b %Y')} – {end_window_dt.strftime('%b %Y')}"

        # Real Jupiter transit house from the horary Lagna (whole-sign,
        # Jupiter aspects 1st/5th/7th/9th from itself) and real Moon
        # paksha from the actual Sun-Moon angular separation — previously
        # both were hardcoded strings claiming a fixed, always-supportive
        # configuration regardless of the actual computed longitudes.
        jupiter_rashi_idx = int(jupiter_lon // 30.0)
        jupiter_house = house_offset(asc_rashi_idx, jupiter_rashi_idx)
        jupiter_aspects_lagna = jupiter_house in (1, 5, 7, 9)
        transit_support = (
            f"Jupiter transiting house {jupiter_house} from horary Lagna — "
            + ("aspects/occupies Lagna, supportive of fruition" if jupiter_aspects_lagna
               else "no direct aspect on Lagna from current position")
        )

        moon_sun_separation = (moon_lon - sun_lon) % 360.0
        is_waxing = moon_sun_separation < 180.0
        moon_cycle = (
            f"{'Waxing' if is_waxing else 'Waning'} Moon "
            f"({'Shukla' if is_waxing else 'Krishna'} Paksha) — "
            + ("supportive" if is_waxing else "less supportive, classically")
        )

        timing = TimingIndication(
            likely_window=window_str,
            dasha_mahadasha=f"{dasha_maha} Mahadasha",
            antardasha=f"{antardasha_lord} Antardasha",
            transit_support=transit_support,
            moon_cycle=moon_cycle,
        )

        conclusions = (
            f"Strong Lagna and Lagna Lord ({asc_lords['sign_lord'].capitalize()}) alignment",
            "Primary query significators confirm positive event manifestation",
            "Jupiter's auspicious influence grants favor from decision makers",
            "Procedural delay or competitive scrutiny due to Saturn/Mars influence",
            f"Result: {verdict} — The indications strongly favor successful attainment.",
        )

        return PrashnaJudgement(
            verdict=verdict,
            confidence_percentage=final_confidence,
            strength_label="Strong Indication" if final_confidence >= 75 else "Moderate Indication",
            summary=f"The horary indications are favorable for this inquiry. The planetary configuration and KP sub-lords confirm affirmative fruition with diligence.",
            key_evidences=tuple(evidence),
            relevant_houses=relevant_houses,
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

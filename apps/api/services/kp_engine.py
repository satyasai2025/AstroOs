"""
AstroOS — KP (Krishnamurti Paddhati) Analysis + Evidence Engine

The KP Analysis layer and its Evidence chain, promoted into the backend
so the pipeline is genuinely backend-driven:

    Swiss Ephemeris → Astronomy → Chart → KP Calculation → KP Analysis
    → KP Evidence → Frontend

This module is the pure port of the client-side KP analysis that used to
live in apps/web/src/lib (kpSignificators.ts, kpAnalysis.ts, kpTiming.ts).
It operates ONLY on the real, already-computed domain objects the chart
engine stamps with KP data:

  - D1Chart.planets[].house_number / rashi_house_number — Bhava Chalit
    (cuspal) house placement + rashi house
  - D1Chart.planets[].nakshatra_lord — each planet's Star Lord
  - D1Chart.planets[].sub_lord / sub_sub_lord — KP Sub / Sub-Sub Lord
  - D1Chart.houses[].rashi → sign's lord (the house's Sign Lord)
  - D1Chart.ascendant + D1Chart.panchanga.vara — Ruling Planets
  - DashaTree — the running Vimshottari period chain
  - list[TransitPlanetResult] + transit datetime — transit triggers

Classical rules implemented (per K.S. Krishnamurti's Sub Lord theory):

  A house's SIGNIFICATORS are graded in four tiers, strongest to weakest:
    A — planets in the Nakshatra (Star) of a planet OCCUPYING the house
    B — planets OCCUPYING the house
    C — planets in the Nakshatra (Star) of the house's Sign Lord
    D — the house's Sign Lord itself
  A single planet can hold more than one grade for the same house.

  Certain LIFE EVENTS are classically read off fixed house groupings (the
  four the founder specified — this list is deliberately not exhaustive).
  A planet that signifies MORE of an event's houses, and at a STRONGER
  grade, is a stronger candidate significator for that event.

  The Sub Lord "veto" (a significator's Sub Lord signifying the houses
  that would negate an outcome) is implemented only in its simplified,
  honestly-labeled form — sub_lord_dusthana_check() — as a caution flag,
  never a full verdict.

  Ruling Planets (RP) — Lagna/Moon sign+star lords + the weekday lord at
  the natal moment — are real, computed from the chart. RPs at the
  TRANSIT moment are limited to the transit Moon's sign/star/sub lords
  plus the transit weekday lord, because the transit snapshot doesn't
  carry an ascendant (the same honest limitation the frontend had).

Timing uses the full KP fructification system:
  1. DASHA LINK — walk the chart's real Vimshottari tree for the running
     period chain; report whether any level's lord is an event significator.
  2. TRANSIT TRIGGERS — KP's star/sub-lord transit rule: a trigger when a
     transit planet passes through the star or sub of an event
     significator, or when Guru (Jupiter) transits the event's primary
     cusp sign. Transit sub lords use the exact backend algorithm
     (longitude_to_sub_lord), so they agree with the chart's stamped subs.
  3. RULING PLANET TRIGGERS — the transit-moment RPs that coincide with
     an event significator.
  FRUCTIFICATION = OPEN (dasha running AND trigger active), PARTIAL
  (either alone), CLOSED (neither). All from real data — no synthesized
  verdicts.

NOTE on casing: the backend domain uses lowercase tokens ("sun",
"aries"); the frontend API client Title-cases them on receipt. This
engine therefore emits lowercase for planet/rashi/lord/sub_lord fields,
and only free-text prose (evidence / detail / summary / note) embeds
Title-cased names so the rendered sentences match the previous
client-side output exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.ephemeris import DignityType
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.ephemeris_wrapper import longitude_to_sub_lord
from packages.shared.constants import (
    DEGREES_PER_NAKSHATRA,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)

# ── Classical reference tables ─────────────────────────────────────────────────

DUSTHANA_HOUSES = [6, 8, 12]
KENDRA_HOUSES = [1, 4, 7, 10]
TRIKONA_HOUSES = [1, 5, 9]

HOUSE_SIGNIFICATIONS: dict[int, str] = {
    1: "Self, body, personality, life path",
    2: "Wealth, family, speech, savings",
    3: "Courage, siblings, communication, effort",
    4: "Home, mother, property, education",
    5: "Children, intelligence, creativity, romance",
    6: "Disease, debts, enemies, service",
    7: "Marriage, partnerships, spouse, business",
    8: "Longevity, occult, sudden events, inheritance",
    9: "Fortune, father, higher learning, dharma",
    10: "Career, profession, status, karma",
    11: "Gains, income, network, fulfillment",
    12: "Loss, foreign lands, isolation, expenditure",
}

# Lowercase-keyed rashi → ruling graha (matches the domain's lowercase tokens).
_RASHI_LORDS: dict[str, str] = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn",
    "pisces": "jupiter",
}

_RASHI_INDEX: dict[str, int] = {name: i for i, name in enumerate(_RASHI_LORDS)}

_RASHI_NAMES_TITLECASE = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Vara (weekday) lords — used for the day-lord ruling planet.
_VARA_LORDS: dict[str, str] = {
    "Sunday": "sun", "Monday": "moon", "Tuesday": "mars", "Wednesday": "mercury",
    "Thursday": "jupiter", "Friday": "venus", "Saturday": "saturn",
}

# Classical KP/astrological fertility classification of signs and planets.
_FERTILE_SIGNS = {"cancer", "scorpio", "pisces"}
_BARREN_SIGNS = {"aries", "gemini", "leo", "virgo"}
_FERTILE_PLANETS = {"moon", "venus", "jupiter", "mercury"}
_BARREN_PLANETS = {"sun", "mars", "saturn", "rahu", "ketu"}

# Event house groupings (deliberately only the four the founder specified).
KP_EVENT_HOUSE_GROUPS: dict[str, dict[str, Any]] = {
    "marriage": {"label": "Marriage", "houses": [2, 7, 11]},
    "career": {"label": "Career / Job", "houses": [2, 6, 10, 11]},
    "childbirth": {"label": "Childbirth", "houses": [2, 5, 11]},
    "disease": {"label": "Disease / Problems", "houses": [6, 8, 12]},
}

EVENT_PRIMARY_CUSP: dict[str, int] = {
    "marriage": 7,
    "career": 10,
    "childbirth": 5,
    "disease": 6,
}

DASHA_LEVEL_LABELS = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"]

# Significator grade strength (A strongest).
_GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


def _cap(token: str) -> str:
    """Title-case a lowercase planet/rashi/nakshatra token for prose
    (e.g. "purva_phalguni" → "Purva Phalguni"). Em-dash passthrough."""
    if not token or token == "—":
        return token
    return " ".join(w.capitalize() for w in token.replace("_", " ").split())


def _rashi_lord(rashi: str | None) -> str | None:
    return _RASHI_LORDS.get(rashi or "") if rashi else None


def _rashi_index(rashi: str | None) -> int:
    return _RASHI_INDEX.get(rashi or "", 0) if rashi else 0


def _star_lord_from_longitude(lon: float) -> str:
    """Star Lord (nakshatra lord) of a sidereal longitude, from the
    canonical 27-lord cycle — port of the client starLordFromLongitude."""
    deg = ((lon % 360) + 360) % 360
    nak_index = int(deg / DEGREES_PER_NAKSHATRA)
    return VIMSHOTTARI_SEQUENCE[nak_index % 9]


def _strongest_grade(grades: list[str]) -> str:
    best = grades[0]
    for g in grades[1:]:
        if _GRADE_RANK[g] > _GRADE_RANK[best]:
            best = g
    return best


# ── House significators (A/B/C/D grading) ──────────────────────────────────────


def compute_all_house_significators(chart: D1Chart) -> list[dict[str, Any]]:
    """Significators for every house (1-12) of the current chart, per the
    classical A/B/C/D grading above."""
    results: list[dict[str, Any]] = []
    houses = {h.house_number: h for h in chart.houses}

    for house_number in range(1, 13):
        house_cusp = houses.get(house_number)
        rashi = house_cusp.rashi if house_cusp else None
        lord = _rashi_lord(rashi)
        occupants = [p.planet for p in chart.planets if p.house_number == house_number]

        significators: list[dict[str, Any]] = []
        for p in chart.planets:
            grades: list[str] = []
            if p.nakshatra_lord and p.nakshatra_lord in occupants:
                grades.append("A")
            if p.house_number == house_number:
                grades.append("B")
            if lord and p.nakshatra_lord == lord:
                grades.append("C")
            if lord and p.planet == lord:
                grades.append("D")
            if grades:
                significators.append({"planet": p.planet, "grades": grades})

        significators.sort(
            key=lambda s: _GRADE_RANK[_strongest_grade(s["grades"])],
            reverse=True,
        )

        results.append({
            "houseNumber": house_number,
            "rashi": rashi,
            "lord": lord,
            "occupants": occupants,
            "significators": significators,
        })

    return results


def sub_lord_dusthana_check(
    chart: D1Chart,
    planet: str,
    all_house_significators: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    """For a given significator planet, check whether its own Sub Lord
    also signifies a dusthana house (6/8/12) — a simplified caution flag,
    not a full verdict."""
    p = next((pp for pp in chart.planets if pp.planet == planet), None)
    if not p:
        return None
    sub_lord = p.sub_lord or None
    if not sub_lord:
        return {"planet": planet, "subLord": None, "cautionFlag": False, "dusthanaHousesSignified": []}

    all_sigs = all_house_significators or compute_all_house_significators(chart)
    dusthana_signified = [
        h for h in DUSTHANA_HOUSES
        if any(s["planet"] == sub_lord for s in next(hs for hs in all_sigs if hs["houseNumber"] == h)["significators"])
    ]
    return {
        "planet": planet,
        "subLord": sub_lord,
        "cautionFlag": len(dusthana_signified) > 0,
        "dusthanaHousesSignified": dusthana_signified,
    }


# ── Cusp matrix ────────────────────────────────────────────────────────────────


def build_kp_cusps(chart: D1Chart) -> list[dict[str, Any]]:
    """Build the 12-cusp matrix. Each cusp's Star/Sub/Sub-Sub Lord come
    from the chart's house cusps (computed backend-side). The CSL's
    signified houses come from the shared significator engine."""
    all_house_sigs = compute_all_house_significators(chart)

    cusps: list[dict[str, Any]] = []
    for h in sorted(chart.houses, key=lambda hh: hh.house_number):
        csl = h.sub_lord or ""
        csl_signifies = (
            [hs["houseNumber"] for hs in all_house_sigs
             if any(s["planet"] == csl for s in hs["significators"])]
            if csl else []
        )
        cusps.append({
            "house_number": h.house_number,
            "longitude": h.sidereal_longitude,
            "rashi": h.rashi,
            "sign_lord": _rashi_lord(h.rashi),
            "star_lord": h.nakshatra_lord,
            "sub_lord": h.sub_lord,
            "sub_sub_lord": h.sub_sub_lord,
            "csl_signifies": csl_signifies,
            "csl_houses": csl_signifies,
            "interlinked_cusps": [],
        })

    # Cuspal interlinks — cusps that share the same Sub Lord.
    for c in cusps:
        if not c["sub_lord"]:
            continue
        c["interlinked_cusps"] = [
            o["house_number"] for o in cusps
            if o["house_number"] != c["house_number"] and o["sub_lord"] == c["sub_lord"]
        ]

    return cusps


# ── Planet KP profiles ─────────────────────────────────────────────────────────


def build_kp_planet_profiles(chart: D1Chart) -> list[dict[str, Any]]:
    """Build a reusable KP profile for every planet (9 bodies incl.
    Rahu/Ketu). Owned houses come from the sign-lord mapping; star/sub-
    lord connected houses come from cusps whose Star/Sub Lord equals this
    planet."""
    cusps = build_kp_cusps(chart)

    profiles: list[dict[str, Any]] = []
    for p in chart.planets:
        sign_lord = _rashi_lord(p.rashi)
        owned_houses = [c["house_number"] for c in cusps if c["sign_lord"] == p.planet]
        star_lord_houses = [c["house_number"] for c in cusps if c["star_lord"] == p.planet]
        sub_lord_houses = [c["house_number"] for c in cusps if c["sub_lord"] == p.planet]

        signifies = sorted(set([p.house_number, *owned_houses, *star_lord_houses]))

        profiles.append({
            "planet": p.planet,
            "rashi": p.rashi,
            "house_number": p.house_number,
            "rashi_house_number": p.rashi_house_number or p.house_number,
            "longitude": p.sidereal_longitude,
            "sign_lord": sign_lord,
            "star_lord": p.nakshatra_lord,
            "sub_lord": p.sub_lord,
            "sub_sub_lord": p.sub_sub_lord,
            "is_retrograde": p.is_retrograde,
            "is_combust": p.is_combust,
            "dignity": p.dignity.value if p.dignity else None,
            "occupied_house": p.house_number,
            "owned_houses": owned_houses,
            "star_lord_houses": star_lord_houses,
            "sub_lord_houses": sub_lord_houses,
            "signifies": signifies,
            "csl_of": [c["house_number"] for c in cusps if c["sub_lord"] == p.planet],
        })

    return profiles


# ── Ruling Planets ─────────────────────────────────────────────────────────────


def compute_ruling_planets(chart: D1Chart) -> list[dict[str, Any]]:
    """Ruling Planets (RP) from the natal moment: Lagna sign lord, Lagna
    Star Lord, Lagna Sub Lord, Moon sign lord, Moon Star Lord, Moon Sub
    Lord, and the weekday (Vara) lord from the Panchanga. Deduplicated,
    with source labels and a priority (founder's ordering: Lagna → Moon →
    Day)."""
    asc = chart.ascendant
    moon = next((p for p in chart.planets if p.planet == "moon"), None)
    vara = chart.panchanga.vara
    day_lord = _VARA_LORDS.get(vara.name, vara.lord)

    candidates: list[dict[str, str | int]] = [
        {"planet": _rashi_lord(asc.rashi) or "", "source": "Lagna Sign Lord", "priority": 1},
        {"planet": asc.nakshatra_lord, "source": "Lagna Star Lord", "priority": 2},
        {"planet": asc.sub_lord, "source": "Lagna Sub Lord", "priority": 3},
        {"planet": _rashi_lord(moon.rashi) if moon else "", "source": "Moon Sign Lord", "priority": 4},
        {"planet": moon.nakshatra_lord if moon else "", "source": "Moon Star Lord", "priority": 5},
        {"planet": moon.sub_lord if moon else "", "source": "Moon Sub Lord", "priority": 6},
        {"planet": day_lord, "source": "Day (Vara) Lord", "priority": 7},
    ]

    seen: set[str] = set()
    rps: list[dict[str, str | int]] = []
    for c in candidates:
        if not c["planet"] or c["planet"] in seen:
            continue
        seen.add(c["planet"])  # type: ignore[arg-type]
        rps.append(c)
    return rps  # type: ignore[return-value]


def compute_fruitful_significators(
    chart: D1Chart,
    houses: list[int],
) -> list[dict[str, Any]]:
    """Fruitful significators — the intersection of Ruling Planets and
    the significators of a set of houses. A planet that is both an RP and
    a house significator is classically read as the strongest candidate
    for that house's matters."""
    rps = compute_ruling_planets(chart)
    all_sigs = compute_all_house_significators(chart)

    per_planet: dict[str, dict[str, Any]] = {}
    for house_number in houses:
        hs = next((h for h in all_sigs if h["houseNumber"] == house_number), None)
        if not hs:
            continue
        for sig in hs["significators"]:
            entry = per_planet.setdefault(sig["planet"], {"rpSource": "", "housesSignified": []})
            entry["housesSignified"].append(house_number)

    fruitful: list[dict[str, Any]] = []
    for rp in rps:
        sig = per_planet.get(rp["planet"])  # type: ignore[arg-type]
        if sig:
            fruitful.append({
                "planet": rp["planet"],
                "rpSource": rp["source"],
                "housesSignified": sig["housesSignified"],
            })
    return fruitful


# ── CSL decision engine ────────────────────────────────────────────────────────


def evaluate_cusp_csl(
    chart: D1Chart,
    cusp_number: int,
    required_houses: list[int],
    prohibited_houses: Optional[list[int]] = None,
) -> dict[str, Any]:
    """CSL verdict for one cusp: how strongly the cusp's Sub Lord (CSL)
    ties to a set of required houses (and whether it also pulls in
    prohibited houses). STRONG = CSL signifies every required house;
    PARTIAL = some; WEAK = none."""
    prohibited = prohibited_houses or DUSTHANA_HOUSES
    cusps = build_kp_cusps(chart)
    cusp = next((c for c in cusps if c["house_number"] == cusp_number), None)
    if not cusp:
        return {
            "cusp": cusp_number,
            "csl": "",
            "csl_star_lord": "",
            "csl_signifies": [],
            "required_houses": required_houses,
            "prohibited_houses": prohibited,
            "verdict": "WEAK",
            "detail": "Cusp not found in chart.",
        }

    csl = cusp["sub_lord"]
    csl_planet = next((p for p in chart.planets if p.planet == csl), None)
    csl_star_lord = csl_planet.nakshatra_lord if csl_planet else ""

    matched = [h for h in required_houses if h in cusp["csl_signifies"]]
    violated = [h for h in prohibited if h in cusp["csl_signifies"]]

    verdict = "STRONG" if len(matched) == len(required_houses) else ("PARTIAL" if matched else "WEAK")

    detail = (
        f"{_cap(csl) or '—'} (Star Lord: {_cap(csl_star_lord) or '—'}) signifies "
        f"{', '.join(str(m) for m in matched) if matched else 'no'} of the required house(s) "
        f"[{', '.join(str(h) for h in required_houses)}]"
        + (f", but also signifies dusthana house(s) [{', '.join(str(v) for v in violated)}] — a caution flag." if violated else ".")
    )

    return {
        "cusp": cusp_number,
        "csl": csl,
        "csl_star_lord": csl_star_lord,
        "csl_signifies": cusp["csl_signifies"],
        "required_houses": required_houses,
        "prohibited_houses": prohibited,
        "verdict": verdict,
        "detail": detail,
    }


# ── Event engine ───────────────────────────────────────────────────────────────


def compute_event_promise(chart: D1Chart, event_key: str) -> dict[str, Any]:
    """Full event promise: CSL verdict on the event's primary cusp, plus
    the ranked significator list for the event's house group."""
    group = KP_EVENT_HOUSE_GROUPS[event_key]
    primary_cusp = EVENT_PRIMARY_CUSP[event_key]
    houses = group["houses"]

    csl_verdict = evaluate_cusp_csl(chart, primary_cusp, houses)

    all_sigs = compute_all_house_significators(chart)
    per_planet: dict[str, dict[str, Any]] = {}
    for house_number in houses:
        hs = next((h for h in all_sigs if h["houseNumber"] == house_number), None)
        if not hs:
            continue
        for sig in hs["significators"]:
            entry = per_planet.setdefault(sig["planet"], {"housesSignified": [], "grades": []})
            entry["housesSignified"].append(house_number)
            entry["grades"].extend(sig["grades"])

    significators = [
        {
            "planet": planet,
            "grade": "/".join(sorted(v["grades"])) or "—",
            "housesSignified": v["housesSignified"],
        }
        for planet, v in per_planet.items()
    ]
    significators.sort(
        key=lambda s: (len(s["housesSignified"]), s["grade"]),
        reverse=True,
    )

    promise = "POSITIVE" if csl_verdict["verdict"] == "STRONG" else ("PARTIAL" if csl_verdict["verdict"] == "PARTIAL" else "WEAK")

    return {
        "eventKey": event_key,
        "label": group["label"],
        "houses": houses,
        "primary_cusp": primary_cusp,
        "csl_verdict": csl_verdict,
        "significators": significators,
        "promise": promise,
    }


def compute_event_significators(
    chart: D1Chart,
    event_key: str,
    all_house_significators: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Combined significators for one of the fixed event-house-groupings —
    the planets most likely to 'carry' that event, per classical KP's own
    framing."""
    group = KP_EVENT_HOUSE_GROUPS[event_key]
    all_sigs = all_house_significators or compute_all_house_significators(chart)

    per_planet: dict[str, dict[str, Any]] = {}
    for house_number in group["houses"]:
        hs = next((h for h in all_sigs if h["houseNumber"] == house_number), None)
        if not hs:
            continue
        for sig in hs["significators"]:
            entry = per_planet.setdefault(sig["planet"], {"housesSignified": [], "grades": []})
            entry["housesSignified"].append(house_number)
            entry["grades"].extend(sig["grades"])

    planets = [
        {"planet": planet, "housesSignified": v["housesSignified"], "strongestGrade": _strongest_grade(v["grades"])}
        for planet, v in per_planet.items()
    ]
    planets.sort(
        key=lambda s: (-len(s["housesSignified"]), -_GRADE_RANK[s["strongestGrade"]]),
    )

    return {"eventKey": event_key, "label": group["label"], "houses": group["houses"], "planets": planets}


# ── Special factors ────────────────────────────────────────────────────────────


def compute_fortuna(chart: D1Chart) -> dict[str, Any]:
    """Part of Fortune (Fortuna) with day/night detection. Day births use
    Asc + Moon − Sun; night births use Asc + Sun − Moon. Day/night is
    derived from whether the Sun is above the horizon (sun house 7-12 =
    day)."""
    asc = chart.ascendant.sidereal_longitude
    moon = next((p for p in chart.planets if p.planet == "moon"), None)
    sun = next((p for p in chart.planets if p.planet == "sun"), None)
    moon_lon = moon.sidereal_longitude if moon else 0
    sun_lon = sun.sidereal_longitude if sun else 0
    sun_house = sun.house_number if sun else 7
    is_day = sun_house >= 7
    fortuna = ((asc + (moon_lon - sun_lon) if is_day else asc + (sun_lon - moon_lon)) % 360 + 360) % 360
    rashi = _RASHI_NAMES_TITLECASE[int(fortuna / 30) % 12]
    return {"longitude": fortuna, "rashi": rashi}


def compute_special_factors(chart: D1Chart) -> list[dict[str, Any]]:
    """Special factors (Fortuna, Fertile/Barren, tenant houses, retrograde,
    combustion, Rahu/Ketu, dusthana/kendra occupancy, cuspal interlinks,
    sub-sub lords, etc.) classified into CORE / EXTENDED / SUPPLEMENTARY so
    the UI can present them with honest authority levels."""
    factors: list[dict[str, Any]] = []
    cusps = build_kp_cusps(chart)
    profiles = build_kp_planet_profiles(chart)

    for p in chart.planets:
        if p.is_retrograde:
            factors.append({
                "name": f"{_cap(p.planet)} Retrograde",
                "category": "SUPPLEMENTARY",
                "value": "Retrograde",
                "status": "caution",
                "evidence": f"{_cap(p.planet)} is retrograde — its significations are read with intensified but delayed effects.",
            })
        if p.is_combust:
            orb = f" ({p.combustion_orb:.1f}°)" if p.combustion_orb is not None else ""
            factors.append({
                "name": f"{_cap(p.planet)} Combust",
                "category": "SUPPLEMENTARY",
                "value": "Combust",
                "status": "caution",
                "evidence": f"{_cap(p.planet)} is within combustion orb of the Sun{orb} — its strength is weakened.",
            })

    for p in chart.planets:
        if p.planet in ("rahu", "ketu"):
            profile = next((pp for pp in profiles if pp["planet"] == p.planet), None)
            factors.append({
                "name": f"{_cap(p.planet)} Node Analysis",
                "category": "EXTENDED KP",
                "value": f"In {_cap(p.rashi)} (house {p.house_number}) · Star {_cap(p.nakshatra_lord)} · Sub {_cap(p.sub_lord)}",
                "status": "neutral",
                "evidence": (
                    f"{_cap(p.planet)} behaves like its Star Lord {_cap(p.nakshatra_lord) or '—'} and signifies house(s) "
                    + (", ".join(str(h) for h in profile["signifies"]) if profile and profile["signifies"] else "—")
                    + "."
                ),
            })

    for c in cusps:
        if c["interlinked_cusps"]:
            factors.append({
                "name": f"Cuspal Interlink {c['house_number']}↔{'/'.join(str(i) for i in c['interlinked_cusps'])}",
                "category": "EXTENDED KP",
                "value": f"Shared Sub Lord: {_cap(c['sub_lord'])}",
                "status": "neutral",
                "evidence": (
                    f"House {c['house_number']} and house(s) {', '.join(str(i) for i in c['interlinked_cusps'])} share Sub Lord "
                    f"{_cap(c['sub_lord'])}, linking their significations."
                ),
            })

    kendra_occupants = [p for p in chart.planets if p.house_number in KENDRA_HOUSES]
    if kendra_occupants:
        factors.append({
            "name": "Kendra Occupancy",
            "category": "CORE KP",
            "value": ", ".join(f"{_cap(p.planet)} (H{p.house_number})" for p in kendra_occupants),
            "status": "positive",
            "evidence": f"{len(kendra_occupants)} planet(s) in kendra houses (1/4/7/10) strengthen the chart.",
        })

    dusthana_occupants = [p for p in chart.planets if p.house_number in DUSTHANA_HOUSES]
    if dusthana_occupants:
        factors.append({
            "name": "Dusthana Occupancy",
            "category": "CORE KP",
            "value": ", ".join(f"{_cap(p.planet)} (H{p.house_number})" for p in dusthana_occupants),
            "status": "caution",
            "evidence": f"{len(dusthana_occupants)} planet(s) occupy dusthana houses (6/8/12) — houses of loss, obstacles and expense.",
        })

    # Tenant houses — each planet is a "tenant" of the house it occupies.
    occupied_houses: dict[int, list[str]] = {}
    for p in chart.planets:
        occupied_houses.setdefault(p.house_number, []).append(p.planet)
    for h in range(1, 13):
        tenants = occupied_houses.get(h)
        if tenants:
            factors.append({
                "name": f"House {h} Tenants",
                "category": "CORE KP",
                "value": ", ".join(_cap(t) for t in tenants),
                "status": "neutral",
                "evidence": f"{len(tenants)} planet(s) tenant House {h}: {', '.join(_cap(t) for t in tenants)} — their significations colour this house's matters.",
            })
        else:
            factors.append({
                "name": f"House {h} Vacant",
                "category": "CORE KP",
                "value": "No tenants",
                "status": "caution",
                "evidence": (
                    f"No planet occupies House {h} — its matters rest on the Sign Lord ({_cap(cusps[h - 1]['sign_lord']) or '—'}) "
                    f"and the Cuspal Sub Lord ({_cap(cusps[h - 1]['sub_lord']) or '—'}) alone."
                ),
            })

    fertile_planets = [p for p in chart.planets if p.planet in _FERTILE_PLANETS]
    barren_planets = [p for p in chart.planets if p.planet in _BARREN_PLANETS]
    fertile_signs = [p for p in chart.planets if p.rashi in _FERTILE_SIGNS]
    barren_signs = [p for p in chart.planets if p.rashi in _BARREN_SIGNS]

    factors.append({
        "name": "Fertile Planets",
        "category": "SUPPLEMENTARY",
        "value": ", ".join(f"{_cap(p.planet)} ({_cap(p.rashi)})" for p in fertile_planets) if fertile_planets else "None",
        "status": "positive" if fertile_planets else "neutral",
        "evidence": "Classically fertile planets (Moon, Venus, Jupiter, Mercury) placed in the natal chart — supportive of childbirth and growth.",
    })
    factors.append({
        "name": "Barren Planets",
        "category": "SUPPLEMENTARY",
        "value": ", ".join(f"{_cap(p.planet)} ({_cap(p.rashi)})" for p in barren_planets),
        "status": "caution",
        "evidence": "Classically barren planets (Sun, Mars, Saturn, Rahu, Ketu) — their influence on fertility/matters is read as restrictive unless supported by fertile factors.",
    })
    factors.append({
        "name": "Fertile Sign Placements",
        "category": "SUPPLEMENTARY",
        "value": ", ".join(f"{_cap(p.planet)} in {_cap(p.rashi)}" for p in fertile_signs) if fertile_signs else "None",
        "status": "positive" if fertile_signs else "neutral",
        "evidence": f"Planets in the classically fertile signs (Cancer, Scorpio, Pisces) — {len(fertile_signs)} found in this chart.",
    })
    factors.append({
        "name": "Barren Sign Placements",
        "category": "SUPPLEMENTARY",
        "value": ", ".join(f"{_cap(p.planet)} in {_cap(p.rashi)}" for p in barren_signs) if barren_signs else "None",
        "status": "caution" if barren_signs else "neutral",
        "evidence": f"Planets in the classically barren signs (Aries, Gemini, Leo, Virgo) — {len(barren_signs)} found in this chart.",
    })

    fortuna = compute_fortuna(chart)
    sun = next((p for p in chart.planets if p.planet == "sun"), None)
    factors.append({
        "name": "Part of Fortune",
        "category": "SUPPLEMENTARY",
        "value": f"{fortuna['longitude']:.1f}° in {fortuna['rashi']}",
        "status": "neutral",
        "evidence": (
            f"Computed by the {'day' if (sun.house_number if sun else 7) >= 7 else 'night'} formula "
            "(Asc + Moon − Sun / Asc + Sun − Moon) based on the Sun's horizon position."
        ),
    })

    return factors


# ── Timing engine ──────────────────────────────────────────────────────────────


def _transit_positions(
    transit_results: list[TransitPlanetResult],
) -> list[dict[str, Any]]:
    """Compute the KP star/sub lords of every transit planet at the
    transit moment. Star lords come from the canonical 27-lord cycle;
    sub lords use the exact backend algorithm so the numbers agree with
    the chart's own stamped sub lords. Sidereal longitude is recovered as
    rashi_index*30 + degree_in_rashi (exact)."""
    positions: list[dict[str, Any]] = []
    for t in transit_results:
        longitude = _rashi_index(t.transit_rashi) * 30 + t.transit_rashi_degree
        positions.append({
            "planet": t.planet,
            "transit_rashi": t.transit_rashi,
            "transit_rashi_degree": t.transit_rashi_degree,
            "transit_nakshatra": t.transit_nakshatra,
            "is_retrograde": t.is_retrograde,
            "longitude": longitude,
            "star_lord": _star_lord_from_longitude(longitude),
            "sub_lord": longitude_to_sub_lord(longitude),
            "transit_rashi_house": None,
        })
    return positions


def _ruling_planets_at_moment(
    transit_results: list[TransitPlanetResult],
    transit_datetime_utc: datetime,
) -> list[dict[str, str | int]]:
    """Ruling Planets (RP) at the transit/judgment moment: the transit
    Moon's sign/star/sub lords plus the weekday (Vara) lord of the
    transit datetime. (A full RP set would also include the transit
    ascendant's sign/star/sub lords; the backend transit snapshot doesn't
    carry the ascendant, so those are deliberately omitted — the Moon +
    day lords are real, not synthesized.)"""
    moon = next((p for p in transit_results if p.planet == "moon"), None)
    moon_lon = _rashi_index(moon.transit_rashi) * 30 + moon.transit_rashi_degree if moon else None
    day_lord = _VARA_LORDS.get(transit_datetime_utc.strftime("%A"), "")

    candidates: list[dict[str, str | int]] = [
        {"planet": _rashi_lord(moon.transit_rashi) if moon else "", "source": "Transit Moon Sign Lord", "priority": 1},
        {"planet": _star_lord_from_longitude(moon_lon) if moon and moon_lon is not None else "", "source": "Transit Moon Star Lord", "priority": 2},
        {"planet": longitude_to_sub_lord(moon_lon) if moon and moon_lon is not None else "", "source": "Transit Moon Sub Lord", "priority": 3},
        {"planet": day_lord, "source": "Transit Day (Vara) Lord", "priority": 4},
    ]

    seen: set[str] = set()
    rps: list[dict[str, str | int]] = []
    for c in candidates:
        if not c["planet"] or c["planet"] == "?" or c["planet"] in seen:
            continue
        seen.add(c["planet"])  # type: ignore[arg-type]
        rps.append(c)
    return rps  # type: ignore[return-value]


def _get_active_chain(mahadashas: tuple, now: date) -> list[dict[str, Any]]:
    """Walk the dasha tree from the root, collecting the currently-active
    period at every level (the running chain)."""
    chain: list[dict[str, Any]] = []
    candidates = mahadashas
    level_idx = 0
    level_names = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshmadasha", "Pranadasha"]
    while candidates:
        active = next(
            (p for p in candidates if p.start_date <= now <= p.end_date),
            None,
        )
        if not active:
            break
        level_name = level_names[level_idx] if level_idx < len(level_names) else f"Level {level_idx + 1}"
        chain.append({
            "lord": active.lord,
            "level": level_name,
            "start_date": active.start_date,
            "end_date": active.end_date,
            "sub_periods": active.sub_periods,
        })
        candidates = active.sub_periods
        level_idx += 1
    return chain


def _find_next_significator_period(
    mahadashas: tuple,
    significators: list[str],
    now: date,
) -> Optional[dict[str, Any]]:
    """The next period (any level from the current Mahadasha onward) whose
    lord is one of `significators`. Walks the real dasha tree: the current
    Mahadasha's remaining sub-periods first, then subsequent Mahadashas."""
    sig_set = set(significators)

    def scan_periods(periods: tuple, level: int) -> Optional[dict[str, Any]]:
        if not periods:
            return None
        for p in periods:
            if p.start_date < now:
                continue
            if p.lord in sig_set:
                return {
                    "lord": p.lord,
                    "level": DASHA_LEVEL_LABELS[min(level, len(DASHA_LEVEL_LABELS) - 1)],
                    "start": p.start_date.isoformat(),
                    "end": p.end_date.isoformat(),
                }
            deeper = scan_periods(p.sub_periods, level + 1)
            if deeper:
                return deeper
        return None

    current_idx = next(
        (i for i, m in enumerate(mahadashas) if m.start_date <= now <= m.end_date),
        0,
    )

    from_current = scan_periods(mahadashas[current_idx:], 0)
    if from_current:
        return from_current

    return scan_periods(mahadashas, 0)


def compute_timing_analysis(
    chart: D1Chart,
    dasha_tree: DashaTree,
    transit_results: list[TransitPlanetResult],
    transit_datetime_utc: datetime,
) -> list[dict[str, Any]]:
    """Full KP timing analysis for every event: Dasha Link + Transit
    Triggers + Ruling Planet Triggers combined into a fructification
    verdict (OPEN / PARTIAL / CLOSED)."""
    transit_positions = _transit_positions(transit_results)
    moment_rps = _ruling_planets_at_moment(transit_results, transit_datetime_utc)
    cusps = sorted(chart.houses, key=lambda h: h.house_number)
    now = datetime.now(timezone.utc).date()

    analyses: list[dict[str, Any]] = []
    for event_key in KP_EVENT_HOUSE_GROUPS:
        promise = compute_event_promise(chart, event_key)
        significators = [s["planet"] for s in promise["significators"][:3]]
        sig_set = set(significators)
        primary_cusp_rashi = next(
            (c.rashi for c in cusps if c.house_number == EVENT_PRIMARY_CUSP[event_key]),
            None,
        )

        # ── 1. Dasha Link ───────────────────────────────────────────────
        chain = _get_active_chain(dasha_tree.mahadashas, now)
        significator_level: Optional[dict[str, Any]] = None
        for i in range(len(chain) - 1, -1, -1):
            if chain[i]["lord"] in sig_set:
                significator_level = {
                    "lord": chain[i]["lord"],
                    "level": DASHA_LEVEL_LABELS[min(i, len(DASHA_LEVEL_LABELS) - 1)],
                    "start": chain[i]["start_date"].isoformat(),
                    "end": chain[i]["end_date"].isoformat(),
                }
                break
        next_significator_period = _find_next_significator_period(dasha_tree.mahadashas, significators, now)

        # ── 2. Transit Triggers ─────────────────────────────────────────
        transit_triggers: list[dict[str, Any]] = []
        for tp in transit_positions:
            is_guru = tp["planet"] == "jupiter"
            if tp["star_lord"] in sig_set:
                transit_triggers.append({
                    "transit_planet": tp["planet"],
                    "transit_rashi": tp["transit_rashi"],
                    "transit_sub_lord": tp["sub_lord"],
                    "transit_star_lord": tp["star_lord"],
                    "type": "STAR",
                    "activated": tp["star_lord"],
                    "note": f"{_cap(tp['planet'])} is transiting the star of {_cap(tp['star_lord'])}, activating it for {promise['label']}.",
                })
            if tp["sub_lord"] in sig_set:
                transit_triggers.append({
                    "transit_planet": tp["planet"],
                    "transit_rashi": tp["transit_rashi"],
                    "transit_sub_lord": tp["sub_lord"],
                    "transit_star_lord": tp["star_lord"],
                    "type": "SUB",
                    "activated": tp["sub_lord"],
                    "note": f"{_cap(tp['planet'])} is transiting the sub of {_cap(tp['sub_lord'])}, activating it for {promise['label']}.",
                })
            if is_guru and primary_cusp_rashi and tp["transit_rashi"] == primary_cusp_rashi:
                transit_triggers.append({
                    "transit_planet": tp["planet"],
                    "transit_rashi": tp["transit_rashi"],
                    "transit_sub_lord": tp["sub_lord"],
                    "transit_star_lord": tp["star_lord"],
                    "type": "GURU",
                    "activated": "—",
                    "note": (
                        f"Guru (Jupiter) is transiting {_cap(tp['transit_rashi'])}, the sign of the {promise['label']} cusp "
                        f"(house {EVENT_PRIMARY_CUSP[event_key]})."
                    ),
                })

        # ── 3. Ruling Planet Triggers ───────────────────────────────────
        rp_triggers: list[dict[str, Any]] = []
        for rp in moment_rps:
            if rp["planet"] in sig_set:
                rp_triggers.append({
                    "rp": rp["planet"],
                    "rpSource": rp["source"],
                    "matched_significator": rp["planet"],
                    "note": f"{rp['source']} ({_cap(rp['planet'])}) is also a significator of {promise['label']} — an RP trigger.",
                })

        # ── 4. Fructification verdict ───────────────────────────────────
        has_dasha = significator_level is not None
        has_trigger = bool(transit_triggers) or bool(rp_triggers)
        if has_dasha and has_trigger:
            fructification = "OPEN"
            summary = (
                f"{_cap(significator_level['lord'])}'s {significator_level['level']} is running and "
                f"{len(transit_triggers) + len(rp_triggers)} trigger(s) are active — the {promise['label']} window is open."
            )
        elif has_dasha or has_trigger:
            fructification = "PARTIAL"
            if has_dasha:
                summary = (
                    f"{_cap(significator_level['lord'])}'s {significator_level['level']} is running but "
                    "no transit/RP trigger is active yet."
                )
            else:
                summary = "Transit/RP triggers are active but no event significator is running in the dasha chain."
        else:
            fructification = "CLOSED"
            summary = "No event significator is running in the dasha chain and no trigger is active."
            nsp = next_significator_period
            if nsp:
                summary += f" The next significator period is {_cap(nsp['lord'])}'s {nsp['level']} ({nsp['start'][:10]} → {nsp['end'][:10]})."

        analyses.append({
            "eventKey": event_key,
            "label": promise["label"],
            "promise": promise["promise"],
            "significators": significators,
            "dasha_link": {
                "active": bool(chain),
                "chain": [
                    {
                        "lord": c["lord"],
                        "level": DASHA_LEVEL_LABELS[min(i, len(DASHA_LEVEL_LABELS) - 1)],
                        "start": c["start_date"].isoformat(),
                        "end": c["end_date"].isoformat(),
                    }
                    for i, c in enumerate(chain)
                ],
                "significator_level": significator_level,
                "next_significator_period": next_significator_period,
            },
            "transit_triggers": transit_triggers,
            "rp_triggers": rp_triggers,
            "fructification": fructification,
            "summary": summary,
        })

    return analyses


# ── Evidence chain ─────────────────────────────────────────────────────────────


def compute_event_evidence(
    chart: D1Chart,
    dasha_tree: DashaTree,
    transit_results: list[TransitPlanetResult],
    transit_datetime_utc: datetime,
    event_key: str,
) -> dict[str, Any]:
    """The full evidence chain behind one event's verdict — required
    houses → primary cusp → CSL → CSL Star Lord → CSL significations →
    RP intersection → timing. This is the "every conclusion carries an
    evidence chain" layer."""
    promise = compute_event_promise(chart, event_key)
    houses = promise["houses"]
    primary_cusp = promise["primary_cusp"]
    csl_verdict = promise["csl_verdict"]

    fruitful = compute_fruitful_significators(chart, houses)
    rp_intersection = [f["planet"] for f in fruitful if f["planet"] == csl_verdict["csl"]]

    now = datetime.now(timezone.utc).date()
    chain = _get_active_chain(dasha_tree.mahadashas, now)
    top_significator = promise["significators"][0]["planet"] if promise["significators"] else None
    active_level = next((c for c in chain if c["lord"] == top_significator), None)

    steps = [
        {"label": "Required Houses", "value": ", ".join(str(h) for h in houses)},
        {"label": "Primary Cusp", "value": f"House {primary_cusp}"},
        {"label": "CSL (Sub Lord)", "value": _cap(csl_verdict["csl"]) or "—"},
        {"label": "CSL Star Lord", "value": _cap(csl_verdict["csl_star_lord"]) or "—"},
        {
            "label": "CSL Significations",
            "value": ", ".join(str(h) for h in csl_verdict["csl_signifies"]) if csl_verdict["csl_signifies"] else "—",
        },
        {
            "label": "Required ∩ CSL",
            "value": ", ".join(str(h) for h in csl_verdict["required_houses"] if h in csl_verdict["csl_signifies"]) or "—",
        },
        {"label": "RP Intersection", "value": ", ".join(_cap(p) for p in rp_intersection) if rp_intersection else "—"},
        {
            "label": "Timing (Dasha)",
            "value": (
                f"{_cap(active_level['lord'])} {active_level['level']} — active"
                if active_level and top_significator
                else "Not in active dasha period"
            ),
        },
    ]

    return {
        "eventKey": event_key,
        "label": promise["label"],
        "houses": houses,
        "primary_cusp": primary_cusp,
        "csl_verdict": csl_verdict,
        "significators": promise["significators"],
        "promise": promise["promise"],
        "top_significator": top_significator,
        "fruitful_rp_intersection": rp_intersection,
        "active_dasha_level": active_level["level"] if active_level else None,
        "steps": steps,
        "verdict_detail": csl_verdict["detail"],
    }


# ── Aggregate result ───────────────────────────────────────────────────────────


@dataclass
class KPAnalysisResult:
    """The complete KP analysis for one chart at one transit moment."""

    cusps: list[dict[str, Any]]
    planet_profiles: list[dict[str, Any]]
    house_significators: list[dict[str, Any]]
    ruling_planets: list[dict[str, Any]]
    event_promises: list[dict[str, Any]]
    special_factors: list[dict[str, Any]]
    timing: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    transit_positions: list[dict[str, Any]] = field(default_factory=list)


class KPEngine:
    """
    The KP Analysis + Evidence engine. Pure computation — takes the
    already-computed chart / dasha / transit domain objects (never
    recomputes astronomy) and produces the full KP analysis.
    """

    def analyze(
        self,
        chart: D1Chart,
        dasha_tree: DashaTree,
        transit_results: list[TransitPlanetResult],
        transit_datetime_utc: datetime,
    ) -> KPAnalysisResult:
        event_keys = list(KP_EVENT_HOUSE_GROUPS.keys())
        return KPAnalysisResult(
            cusps=build_kp_cusps(chart),
            planet_profiles=build_kp_planet_profiles(chart),
            house_significators=compute_all_house_significators(chart),
            ruling_planets=compute_ruling_planets(chart),
            event_promises=[compute_event_promise(chart, k) for k in event_keys],
            special_factors=compute_special_factors(chart),
            timing=compute_timing_analysis(chart, dasha_tree, transit_results, transit_datetime_utc),
            evidence=[
                compute_event_evidence(chart, dasha_tree, transit_results, transit_datetime_utc, k)
                for k in event_keys
            ],
            transit_positions=_transit_positions(transit_results),
        )

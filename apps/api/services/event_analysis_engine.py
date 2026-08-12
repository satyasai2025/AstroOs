"""
AstroOS — Event Analysis Engine

The event-moment orchestration for the Event Analysis workflow. Given a
saved natal chart (person) + a chosen event moment, it:

  1. Loads the natal chart's birth data (BirthChartRepository).
  2. Computes the one-time NatalSnapshot (yogas + shadbala + ashtakavarga)
     from the natal D1 — the reusable, date-invariant natal makeup.
  3. Casts the EVENT CHART at the event's exact datetime + location
     (HoroscopeEngine.generate_d1) — the muhurta chart.
  4. Computes the event-moment TRANSITS via EventEngine (which consumes
     TransitEngine) at that exact instant.
  5. Resolves the ACTIVE DASHA chain at the event date (DashaEngine +
     dasha_lookup).
  6. Scores the selected scope dimensions (deterministic heuristic) and
     composes the structured report (ReportEngine.build_event_report).

This engine is an assembly + correlation layer, not a calculation engine:
it delegates every calculation to the existing engines and reuses the
exact wiring proven in natal_bundle_stage.py / events_verification_stage.py.
It never writes to the DB — the router persists the returned
EventAnalysisResult.

The score is a REGISTERED, documented heuristic (descriptive, not
predictive) — same discipline as Arishta Yoga results (Module 8).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.event_analysis import EventAnalysisRecord, EventAnalysisResult
from apps.api.domain.events import EventRecord, NatalSnapshot
from apps.api.domain.horoscope import D1Chart, PlanetStrength
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.yoga import YogaResult
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.event_engine import EventEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.house_engine import HouseEngine
from apps.api.services.report_engine import ReportEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_SHASHTIAMSAS_PER_RUPA = 60.0
_DASHA_MAX_DEPTH = 5
_SCORE_BENCHMARK_RUPA = 13.0
_DASHA_LEVEL_NAMES = {1: "Mahadasha", 2: "Antardasha", 3: "Pratyantardasha", 4: "Sookshma", 5: "Prana"}

# ── Score breakdown (Event Analysis scope dimensions) ──────────────────────
# Weights sum to 100 — a selected subset is re-normalized to that subset's
# own weights (see _overall_score_from_breakdown), so the score stays 0-100
# regardless of how many dimensions the user selected.
_DIMENSION_WEIGHTS: dict[str, float] = {
    "natal_promise": 25.0,
    "dasha_support": 20.0,
    "transit_influence": 20.0,
    "planetary_strength": 15.0,
    "yogas_activated": 10.0,
    "muhurta": 10.0,
}
_DIMENSION_LABELS: dict[str, str] = {
    "natal_promise": "Natal Promise",
    "dasha_support": "Dasha Support",
    "transit_influence": "Transit Influence",
    "planetary_strength": "Planetary Strength",
    "yogas_activated": "Yogas Activated",
    "muhurta": "Muhurta",
}

# Classical primary significator house + natural karaka (relationship
# planet) per event category — the 7 Ontology categories this app already
# uses elsewhere (see domain/events.py's EventRecord.category docstring).
# One house/karaka per category is a deliberate simplification (real natal
# promise reads several houses together); it is a real classical starting
# point, not an invented rule, and every evidence line names exactly which
# house/planet it's reading so a reader can extend the analysis themselves.
_CATEGORY_SIGNIFICATOR_HOUSE: dict[str, int] = {
    "marriage": 7, "career": 10, "education": 4, "health": 6,
    "progeny": 5, "wealth": 2, "longevity": 8,
}
_CATEGORY_KARAKA: dict[str, str] = {
    "marriage": "venus", "career": "saturn", "education": "jupiter", "health": "sun",
    "progeny": "jupiter", "wealth": "jupiter", "longevity": "saturn",
}
_CATEGORY_ALIASES: dict[str, str] = {
    "wedding": "marriage", "engagement": "marriage",
    "job": "career", "business": "career", "promotion": "career", "startup": "career",
    "study": "education", "exam": "education", "degree": "education",
    "surgery": "health", "illness": "health", "medical": "health",
    "child": "progeny", "childbirth": "progeny", "pregnancy": "progeny",
    "finance": "wealth", "property": "wealth", "investment": "wealth", "purchase": "wealth",
}
_HOUSE_SHORT_LABELS: dict[int, str] = {
    1: "self", 2: "wealth/family", 3: "courage/siblings", 4: "home/mother",
    5: "progeny/intellect", 6: "obstacles/health", 7: "partnership/marriage",
    8: "longevity/transformation", 9: "fortune/dharma", 10: "career/status",
    11: "gains", 12: "loss/foreign",
}


# ── Serializers -------------------------------------------------------------
# Convert computed domain objects into compact, JSON-safe payloads stored in
# the `event_chart_snapshots` rows. The router imports these to persist the
# three artifact references (event chart / transit / dasha chain).


def _planet_to_dict(p) -> dict:
    dignity = p.dignity
    return {
        "planet": p.planet,
        "rashi": p.rashi,
        "house_number": p.house_number,
        "degree_in_rashi": p.rashi_degree,
        "nakshatra": p.nakshatra,
        "pada": p.pada,
        "retrograde": p.is_retrograde,
        "combust": p.is_combust,
        "dignity": getattr(dignity, "value", dignity),
    }


def serialize_event_chart(event_chart: D1Chart) -> dict:
    """Serialize the cast event D1 (muhurta chart) into a compact payload."""
    return {
        "type": "event_chart",
        "ayanamsa_system": event_chart.ayanamsa_system,
        "house_system": event_chart.house_system,
        "ascendant": {
            "rashi": event_chart.ascendant.rashi,
            "degree_in_rashi": event_chart.ascendant.rashi_degree,
            "nakshatra": event_chart.ascendant.nakshatra,
            "pada": event_chart.ascendant.pada,
        },
        "planets": [_planet_to_dict(p) for p in event_chart.planets],
        "houses": [{"number": h.house_number, "rashi": h.rashi} for h in event_chart.houses],
    }


def serialize_transits(transits: tuple[TransitPlanetResult, ...]) -> dict:
    return {
        "type": "transit",
        "transits": [
            {
                "planet": t.planet,
                "transit_rashi": t.transit_rashi,
                "house_from_natal_moon": t.house_from_natal_moon,
                "transit_rashi_degree": t.transit_rashi_degree,
                "transit_nakshatra": t.transit_nakshatra,
                "transit_pada": t.transit_pada,
                "retrograde": t.is_retrograde,
                "gati": t.gati,
                "is_sade_sati": t.is_sade_sati,
                "is_ashtama_shani": t.is_ashtama_shani,
                "is_favorable_house": t.is_favorable_house,
                "has_vedha": t.has_vedha,
                "has_vipreet_vedha": t.has_vipreet_vedha,
                "has_nakshatra_vedha": t.has_nakshatra_vedha,
            }
            for t in transits
        ],
        "count": len(transits),
    }


def serialize_dasha_chain(chain: tuple[DashaPeriod, ...]) -> dict:
    return {
        "type": "dasha",
        "chain": [
            {
                "lord": p.lord,
                "level": p.level,
                "start_date": p.start_date.isoformat(),
                "end_date": p.end_date.isoformat(),
                "duration_days": p.duration_days,
            }
            for p in chain
        ],
        "count": len(chain),
    }


class EventAnalysisEngine:
    """
    Constructed per-request with the process-wide EphemerisWrapper and a
    birth-chart repository, mirroring the engine-factory lifecycle in
    apps/api/services. Sub-engines are injected with the same process-wide
    EphemerisWrapper so they share the single pyswisseph instance (see
    get_ephemeris_wrapper's docstring about process-global state) — never
    their own.
    """

    def __init__(
        self,
        wrapper: EphemerisWrapper,
        *,
        birth_chart_repo: BirthChartRepository,
        horoscope_engine: Optional[HoroscopeEngine] = None,
        dasha_engine: Optional[DashaEngine] = None,
        yoga_engine: Optional[YogaEngine] = None,
        shadbala_engine: Optional[ShadbalaEngine] = None,
        ashtakavarga_engine: Optional[AshtakavargaEngine] = None,
        transit_engine: Optional[TransitEngine] = None,
        event_engine: Optional[EventEngine] = None,
        dasha_system: str = "vimshottari",
    ) -> None:
        self._wrapper = wrapper
        self._birth_chart_repo = birth_chart_repo
        self._dasha_system = dasha_system

        self._ashtakavarga_engine = ashtakavarga_engine or AshtakavargaEngine()
        self._horoscope_engine = horoscope_engine or HoroscopeEngine(wrapper)
        self._dasha_engine = dasha_engine or DashaEngine(wrapper)
        self._yoga_engine = yoga_engine or YogaEngine()
        self._shadbala_engine = shadbala_engine or ShadbalaEngine()
        self._transit_engine = (
            transit_engine or TransitEngine(wrapper, ashtakavarga_engine=self._ashtakavarga_engine)
        )
        self._event_engine = event_engine or EventEngine(transit_engine=self._transit_engine)

    # ── Natal snapshot (mirrors NatalBundleStage._compute_natal_bundle, one chart) ──

    def _build_natal_snapshot(self, chart_id: uuid.UUID, natal_chart: D1Chart) -> NatalSnapshot:
        yoga_results = self._yoga_engine.evaluate_all(natal_chart)
        shadbala_components = {
            **self._shadbala_engine.compute_phase1_components(natal_chart),
            **self._shadbala_engine.compute_phase2_components(natal_chart),
            **self._shadbala_engine.compute_sthana_bala_components(natal_chart),
        }
        bhinna = tuple(self._ashtakavarga_engine.compute_bhinnashtakavarga(natal_chart))
        sarva = self._ashtakavarga_engine.compute_sarvashtakavarga(natal_chart, bhinna)
        return NatalSnapshot(
            chart_id=chart_id,
            chart=natal_chart,
            yogas=tuple(yoga_results),
            shadbala_components=shadbala_components,
            bhinnashtakavarga=bhinna,
            sarvashtakavarga=sarva,
        )

    # ── Scoring (deterministic heuristic — NOT predictive) ──────────────────
    #
    # Each selected scope dimension is evaluated independently into a dict
    # (see _evaluate_* functions below) carrying its own sub_score (0-1),
    # weight, and EVIDENCE — the concrete natal/event facts the sub_score is
    # read off, not narrative interpretation. ReportEngine only formats
    # these dicts into sections; it does not compute anything itself.

    def _compute_dimension_results(
        self,
        record: EventAnalysisRecord,
        event_chart: D1Chart,
        transits: tuple[TransitPlanetResult, ...],
        dasha_chain: tuple[DashaPeriod, ...],
        natal_snapshot: NatalSnapshot,
    ) -> list[dict]:
        scope = record.scope
        dims: list[dict] = []
        if "natal_promise" in scope:
            dims.append(_evaluate_natal_promise(record.category, natal_snapshot.chart))
        if "dasha_support" in scope:
            dims.append(_evaluate_dasha_support(dasha_chain, natal_snapshot.chart, natal_snapshot.yogas))
        if "transit_influence" in scope:
            dims.append(_evaluate_transit_influence(record.category, transits))
        if "planetary_strength" in scope:
            dims.append(_evaluate_planetary_strength(natal_snapshot.shadbala_components))
        if "yogas_activated" in scope:
            dims.append(_evaluate_yogas_activated(natal_snapshot.yogas))
        if "muhurta" in scope:
            dims.append(_evaluate_muhurta(event_chart))
        return dims

    async def analyze(self, record: EventAnalysisRecord) -> EventAnalysisResult:
        """Run the full event-moment analysis for an already-created record."""
        birth_model = await self._birth_chart_repo.get_by_id(record.birth_chart_id)
        if birth_model is None:
            raise ValueError(f"Birth chart {record.birth_chart_id} not found.")

        birth_datetime_utc = birth_model.birth_datetime_utc
        birth_lat = float(birth_model.birth_latitude)
        birth_lon = float(birth_model.birth_longitude)
        ayanamsa = birth_model.ayanamsa
        house_system = birth_model.house_system

        # record.event_latitude/longitude come back from the DB as Decimal
        # (Numeric column), same as birth_model's — must be cast to float
        # before reaching pyswisseph, same as birth_lat/birth_lon above.
        event_lat = float(record.event_latitude) if record.event_latitude is not None else birth_lat
        event_lon = float(record.event_longitude) if record.event_longitude is not None else birth_lon
        event_dt = record.event_datetime_utc

        # 2. Natal D1 + reusable NatalSnapshot.
        natal_chart = await asyncio.to_thread(
            self._horoscope_engine.generate_d1,
            birth_datetime_utc, birth_lat, birth_lon, ayanamsa, house_system,
        )
        natal_snapshot = self._build_natal_snapshot(record.birth_chart_id, natal_chart)

        # 3. Event (muhurta) D1 at the event's exact datetime + location.
        event_chart = await asyncio.to_thread(
            self._horoscope_engine.generate_d1,
            event_dt, event_lat, event_lon, ayanamsa, house_system,
        )

        # 5. Active dasha at the event date, resolved over the natal DashaTree.
        dasha_compute_fn = getattr(self._dasha_engine, f"compute_{self._dasha_system}")
        dasha_tree: DashaTree = await asyncio.to_thread(
            dasha_compute_fn,
            birth_datetime_utc, birth_lat, birth_lon, ayanamsa, house_system,
            _DASHA_MAX_DEPTH,
        )
        dasha_chain = find_active_dasha_chain(dasha_tree, record.event_date)

        # 4. EventEngine runs the event-moment transit + assembles the context.
        event_record = EventRecord(
            id=record.id,
            chart_id=record.birth_chart_id,
            event_date=record.event_date,
            title=record.event_name,
            user_id=record.user_id,
            category=record.category,
        )
        analysis = self._event_engine.analyze(
            event_record,
            dasha_trees={self._dasha_system: dasha_tree},
            natal_snapshot=natal_snapshot,
            event_datetime_utc=event_dt,
        )

        transits = analysis.context.transits
        dimension_results = self._compute_dimension_results(
            record, event_chart, transits, dasha_chain, natal_snapshot,
        )
        overall_score = _overall_score_from_breakdown(dimension_results)
        report = ReportEngine.build_event_report(
            event_chart=event_chart,
            natal_snapshot=natal_snapshot,
            dimension_results=dimension_results,
            event_record=record,
            score=overall_score,
        )

        return EventAnalysisResult(
            event_record=record,
            natal_snapshot=natal_snapshot,
            event_chart=event_chart,
            transit_results=transits,
            dasha_tree=dasha_tree,
            dasha_chain=dasha_chain,
            event_analysis=analysis,
            report=report,
            overall_score=overall_score,
            scope=record.scope,
        )


# ── Sub-score helpers -----------------------------------------------------------


def _overall_score_from_breakdown(dims: list[dict]) -> Optional[float]:
    """
    Weighted 0-100 composite from each selected dimension's own points_earned
    / points_max — re-normalized to whichever subset of dimensions was
    selected, so the score always sits on a 0-100 scale regardless of how
    many dimensions the user asked for.
    """
    if not dims:
        return None
    total_earned = sum(d["points_earned"] for d in dims)
    total_max = sum(d["points_max"] for d in dims)
    if total_max == 0:
        return None
    return round(total_earned / total_max * 100, 1)


def _status_label(sub_score: float) -> str:
    if sub_score >= 0.66:
        return "supported"
    if sub_score >= 0.4:
        return "mixed"
    return "weak"


def _dimension_result(key: str, sub_score: Optional[float], evidence: list[str]) -> dict:
    """
    Uniform shape every _evaluate_* function returns. `sub_score` is None
    when the dimension is descriptive-only (no scoring heuristic exists yet,
    e.g. muhurta) — it still contributes a neutral 0.5 to the weighted total
    so selecting it doesn't silently distort the other dimensions' weight,
    but its `status` reads "descriptive" instead of a supported/mixed/weak
    verdict so the report doesn't imply a judgement that wasn't made.
    """
    weight = _DIMENSION_WEIGHTS[key]
    effective = sub_score if sub_score is not None else 0.5
    return {
        "key": key,
        "label": _DIMENSION_LABELS[key],
        "weight": weight,
        "sub_score": round(sub_score, 3) if sub_score is not None else None,
        "points_earned": round(effective * weight, 2),
        "points_max": weight,
        "status": _status_label(effective) if sub_score is not None else "descriptive",
        "evidence": evidence,
    }


def _resolve_significator(category: Optional[str]) -> tuple[int, Optional[str]]:
    """
    (house_number, karaka_planet) for an event category. Falls back to the
    1st house (self/Lagna) + Moon (universal, mind/general wellbeing) for an
    unrecognised category rather than guessing a specific life-area house.
    """
    key = (category or "").strip().lower()
    key = _CATEGORY_ALIASES.get(key, key)
    if key in _CATEGORY_SIGNIFICATOR_HOUSE:
        return _CATEGORY_SIGNIFICATOR_HOUSE[key], _CATEGORY_KARAKA.get(key)
    return 1, "moon"


def _find_planet_strength(chart: D1Chart, planet: str) -> Optional[PlanetStrength]:
    return next((ps for ps in chart.planet_strengths if ps.planet == planet), None)


def _placement_summary(ps: PlanetStrength) -> str:
    if ps.is_in_kendra:
        quadrant = "Kendra"
    elif ps.is_in_trikona:
        quadrant = "Trikona"
    elif ps.is_in_dusthana:
        quadrant = "Dusthana"
    else:
        quadrant = "neutral house"
    dignity = ps.dignity.value.capitalize() if ps.dignity else "Neutral"
    flags = []
    if ps.is_retrograde:
        flags.append("retrograde")
    if ps.is_combust:
        flags.append("combust")
    flag_str = f" ({', '.join(flags)})" if flags else ""
    return f"house {ps.house_number} — {dignity}, {quadrant}, strength {ps.strength_score:.1f}/10{flag_str}"


def _enum_val(x) -> str:
    return x.value if hasattr(x, "value") else str(x)


def _evaluate_natal_promise(category: Optional[str], natal_chart: D1Chart) -> dict:
    """
    Reads the natal chart's classical significator house + karaka for this
    event's category (see _CATEGORY_SIGNIFICATOR_HOUSE) — e.g. marriage
    reads the 7th house + Venus. This is a single-house reading, a
    deliberate simplification of full natal-promise analysis (which would
    also weigh D9/Navamsa and multiple supporting houses) — every evidence
    line names exactly which house/planet it's reading.
    """
    house_engine = HouseEngine()
    house_num, karaka = _resolve_significator(category)
    house_cusp = next((h for h in natal_chart.houses if h.house_number == house_num), None)
    if house_cusp is None:
        return _dimension_result("natal_promise", None, ["Natal house data unavailable."])

    evidence: list[str] = []
    scores: list[float] = []

    lord = house_engine.get_house_lord(house_cusp.rashi)
    house_label = _HOUSE_SHORT_LABELS.get(house_num, "")
    evidence.append(
        f"House {house_num} ({house_label}): {house_cusp.rashi.capitalize()} — ruled by {lord.capitalize()}"
    )

    lord_strength = _find_planet_strength(natal_chart, lord)
    if lord_strength:
        evidence.append(f"{lord.capitalize()} (house {house_num} lord), natal {_placement_summary(lord_strength)}")
        scores.append(lord_strength.strength_score / 10.0)

    if karaka and karaka != lord:
        karaka_strength = _find_planet_strength(natal_chart, karaka)
        if karaka_strength:
            evidence.append(f"{karaka.capitalize()} (natural karaka), natal {_placement_summary(karaka_strength)}")
            scores.append(karaka_strength.strength_score / 10.0)

    sub_score = (sum(scores) / len(scores)) if scores else None
    return _dimension_result("natal_promise", sub_score, evidence)


def _evaluate_dasha_support(
    chain: tuple[DashaPeriod, ...],
    natal_chart: D1Chart,
    yoga_results: tuple[YogaResult, ...],
) -> dict:
    if not chain:
        return _dimension_result("dasha_support", None, ["No active dasha period found for the event date."])

    evidence: list[str] = []
    scores: list[float] = []
    involved = {p for y in yoga_results if y.is_present for p in y.involved_planets}

    for period in chain:
        level_name = _DASHA_LEVEL_NAMES.get(period.level, f"Level {period.level}")
        ps = _find_planet_strength(natal_chart, period.lord)
        if ps:
            evidence.append(f"{level_name} — {period.lord.capitalize()}, natal {_placement_summary(ps)}")
            scores.append(ps.strength_score / 10.0)
        else:
            evidence.append(f"{level_name} — {period.lord.capitalize()}")
        if period.lord in involved:
            evidence.append(f"{period.lord.capitalize()} is also involved in an active natal yoga.")
            scores.append(0.8)

    sub_score = (sum(scores) / len(scores)) if scores else None
    return _dimension_result("dasha_support", sub_score, evidence)


def _evaluate_transit_influence(
    category: Optional[str],
    transits: tuple[TransitPlanetResult, ...],
) -> dict:
    if not transits:
        return _dimension_result("transit_influence", None, ["No transit data available for the event moment."])

    _, karaka = _resolve_significator(category)
    evidence: list[str] = []

    favorable = sum(1 for t in transits if t.is_favorable_house is True)
    unfavorable = sum(1 for t in transits if t.is_favorable_house is False)
    unclassified = len(transits) - favorable - unfavorable
    evidence.append(
        f"{favorable} of {len(transits)} transiting planets in a classically favorable house from natal Moon, "
        f"{unfavorable} unfavorable, {unclassified} not classified."
    )

    karaka_transit = next((t for t in transits if t.planet == karaka), None) if karaka else None
    if karaka_transit:
        if karaka_transit.is_favorable_house is True:
            verdict = "favorable"
        elif karaka_transit.is_favorable_house is False:
            verdict = "unfavorable"
        else:
            verdict = "no classical rule for this house"
        vedha = " (obstructed by Vedha)" if karaka_transit.has_vedha else ""
        evidence.append(
            f"{karaka.capitalize()} (natural karaka) transiting {karaka_transit.transit_rashi.capitalize()}, "
            f"house {karaka_transit.house_from_natal_moon} from natal Moon — {verdict}{vedha}."
        )

    saturn_transit = next((t for t in transits if t.planet == "saturn"), None)
    if saturn_transit and (saturn_transit.is_sade_sati or saturn_transit.is_ashtama_shani):
        label = "Sade Sati" if saturn_transit.is_sade_sati else "Ashtama Shani"
        evidence.append(f"Saturn transit: {label} is active at the event moment.")

    scored = [t for t in transits if t.is_favorable_house is not None]
    sub_score = (sum(1 for t in scored if t.is_favorable_house) / len(scored)) if scored else None
    return _dimension_result("transit_influence", sub_score, evidence)


def _evaluate_planetary_strength(components: dict) -> dict:
    totals: dict[str, float] = {}
    for component_results in components.values():
        for r in component_results:
            totals[r.planet] = totals.get(r.planet, 0.0) + r.value_shashtiamsas
    if not totals:
        return _dimension_result("planetary_strength", None, ["Shadbala components not available."])

    evidence: list[str] = []
    marks: list[float] = []
    for p in _CLASSICAL_SEVEN:
        if p not in totals:
            continue
        rupas = totals[p] / _SHASHTIAMSAS_PER_RUPA
        marks.append(min(1.0, rupas / _SCORE_BENCHMARK_RUPA))
        verdict = "meets" if rupas >= _SCORE_BENCHMARK_RUPA else "below"
        evidence.append(
            f"{p.capitalize()}: {rupas:.2f} rupas ({verdict} the {_SCORE_BENCHMARK_RUPA:.0f}-rupa classical benchmark)"
        )

    sub_score = (sum(marks) / len(marks)) if marks else None
    return _dimension_result("planetary_strength", sub_score, evidence)


def _evaluate_yogas_activated(yoga_results: tuple[YogaResult, ...]) -> dict:
    present = [y for y in yoga_results if y.is_present]
    if not present:
        return _dimension_result(
            "yogas_activated", 0.5,
            ["No classical yogas are present in this natal chart (from the yogas currently registered)."],
        )

    evidence: list[str] = []
    for y in present[:10]:
        planets = ", ".join(p.capitalize() for p in y.involved_planets) if y.involved_planets else "—"
        strength_label = _enum_val(y.strength) if y.strength else "unspecified"
        evidence.append(f"{y.name} ({y.category}) — strength: {strength_label}, planets: {planets}")
    if len(present) > 10:
        evidence.append(f"...and {len(present) - 10} more.")

    strong = sum(1 for y in present if y.strength in ("full", "partial"))
    sub_score = strong / len(present)
    return _dimension_result("yogas_activated", sub_score, evidence)


def _evaluate_muhurta(event_chart: D1Chart) -> dict:
    """
    Descriptive only: the raw panchanga facts at the event moment. Full
    Muhurta electional scoring (tithi/nakshatra/karana exclusion rules) is
    a distinct, not-yet-implemented body of rules — this reports what the
    moment actually was rather than fabricating a pass/fail verdict.
    """
    p = event_chart.panchanga
    evidence = [
        f"Tithi: {p.tithi.name.capitalize()} ({p.tithi.paksha}), {p.tithi.completion_percent:.0f}% complete",
        f"Nakshatra: {p.nakshatra.nakshatra.capitalize()}, pada {p.nakshatra.pada} (lord {p.nakshatra.lord.capitalize()})",
        f"Yoga: {p.yoga.name.capitalize()}",
        f"Karana: {p.karana.name.capitalize()}",
        f"Vara: {p.vara.name} (lord {p.vara.lord.capitalize()})",
        "Descriptive only — full Muhurta electional scoring is not yet implemented; "
        "these are the raw panchanga facts at the event moment, not a pass/fail verdict.",
    ]
    return _dimension_result("muhurta", None, evidence)
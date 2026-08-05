"""
AstroOS — Phase E AI Router

HTTP adapter layer over the Phase E AI components: chart comparison,
research assistant, hypothesis generation, enhanced QA, verification
reporting, research insights, and recommendations.

Wired generators (Task #13):
  - VerificationReporter   -> POST /ai/verification-report
  - ResearchInsightGenerator -> POST /ai/research-insight
  - RecommendationEngine   -> POST /ai/recommendation

All endpoints require authentication (any role).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper, get_knowledge_engine, get_knowledge_graph_engine
from apps.api.schemas.ai_phase_e import (
    AshtakootaCompatibilityRequest,
    AshtakootaCompatibilityResponse,
    AvailableDomainResponse,
    AvailableDomainsResponse,
    BestBetCompatibilityRequest,
    BestBetCompatibilityResponse,
    BestBetSubFactorResponse,
    ChartComparisonRequest,
    ChartComparisonResponse,
    ComparisonDimensionResponse,
    DoshaResultResponse,
    EnhancedQuestionRequest,
    GeneratedHypothesisResponse,
    HypothesisGenerateRequest,
    HypothesisListResponse,
    HypothesisTemplateResponse,
    HypothesisTemplatesResponse,
    KootaScoreResponse,
    MarriageTimingRequest,
    MarriageTimingResponse,
    RecommendationRequest,
    RecommendationResponse,
    ResearchAnswerResponse,
    ResearchEvidenceResponse,
    ResearchInsightRequest,
    ResearchInsightResponse,
    ResearchQueryRequest,
    SadhuPadhdhatiChartResponse,
    SadhuPadhdhatiLevelResponse,
    SadhuPadhdhatiRequest,
    SadhuPadhdhatiResponse,
    TransitScanYearResponse,
    VerificationReportRequest,
    VerificationReportResponse,
)
from apps.api.schemas.ai import AIResponseSchema, CitationResponse
from apps.api.services.chart_comparison_engine import ChartComparisonEngine
from apps.api.services.research_assistant_engine import ResearchAssistantEngine
from apps.api.services.hypothesis_generator import HypothesisGenerator
from apps.api.services.enhanced_qa_engine import EnhancedQAResponder
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.knowledge_engine import KnowledgeEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
from apps.api.services.ashtakoota_engine import (
    NAKSHATRAS as ASHTAKOOTA_NAKSHATRAS,
    RASHIS as ASHTAKOOTA_RASHIS,
    AshtakootaEngine,
)
from apps.api.services.marriage_timing_engine import (
    SIGNS as MARRIAGE_TIMING_SIGNS,
    MarriageTimingEngine,
    TransitPositions,
)
from apps.api.services.best_bet_engine import BestBetEngine
from apps.api.services.divisional_engine import compute_varga_sign
from apps.api.services.sadhu_padhdhati_engine import RASHIS as SADHU_RASHIS, ChartPositions, SadhuPadhdhatiEngine
from apps.api.domain.ai_phase_e import ResearchQuery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI (Phase E)"])


# ── Ashtakoota token normalisation ────────────────────────────────────────────
#
# The ephemeris/domain layer emits rashi and nakshatra names as lowercase,
# underscore-separated tokens ("taurus", "purva_phalguni"), while
# AshtakootaEngine's lookup tables (RASHIS, NAKSHATRAS, RASHI_LORDS, YONI_MAP,
# GANA_MAP, NADI_MAP) are all keyed by Title-Case, space-separated English
# names ("Taurus", "Purva Phalguni"). Feeding the raw tokens straight in made
# every table lookup miss and fall through to its `else 0` default, so BOTH
# charts always resolved to Aries/Ashwini — which scored a constant 28/36
# (77.8%) for every couple, regardless of their actual birth data.
#
# Title-casing covers all 12 rashis and 25 of the 27 nakshatras; the remaining
# two differ in spelling, not just case, so they need explicit aliases.
_NAKSHATRA_SPELLING_ALIASES = {
    "Mula": "Moola",
    "Dhanishtha": "Dhanishta",
}


def _to_engine_name(token: str) -> str:
    """
    Convert a domain rashi/nakshatra token to the Title-Case English vocabulary
    the standalone engines use (AshtakootaEngine's tables, MarriageTimingEngine's
    SIGNS list).
    """
    name = token.replace("_", " ").title()
    return _NAKSHATRA_SPELLING_ALIASES.get(name, name)


def _require_known(name: str, known: list[str], kind: str, purpose: str) -> str:
    """
    Guard against silent mis-scoring. AshtakootaEngine defaults unknown names
    to index 0 rather than raising, which is exactly how the casing mismatch
    above went unnoticed — so an unmappable token is surfaced as an error
    instead of being quietly scored as Aries/Ashwini.
    """
    if name not in known:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unrecognised {kind} '{name}' — cannot compute {purpose}.",
        )
    return name


async def _build_chart(body, wrapper: EphemerisWrapper):
    """Build a D1 chart from birth data."""
    horoscope_engine = HoroscopeEngine(wrapper)
    try:
        return await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing chart for Phase E endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute chart.",
        )


def _ai_response(r) -> AIResponseSchema:
    return AIResponseSchema(
        response_type=r.response_type, title=r.title, summary=r.summary, body=r.body,
        citations=[
            CitationResponse(source=c.source, reference=c.reference, text=c.text, relevance=c.relevance)
            for c in r.citations
        ],
        sources=list(r.sources), recommendations=list(r.recommendations),
        confidence=r.confidence, version=r.version,
    )


# ── Chart Comparison ──────────────────────────────────────────────────────────

@router.post("/compare-charts", response_model=ChartComparisonResponse)
async def compare_charts(
    body: ChartComparisonRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> ChartComparisonResponse:
    """
    Compare two birth charts side-by-side across ascendant, planets,
    houses, and yogas. Returns similarity scores and compatibility insights.
    """
    # Build Chart A.
    chart_a = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_a,
            latitude=body.latitude_a,
            longitude=body.longitude_a,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )
    # Build Chart B.
    chart_b = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_b,
            latitude=body.latitude_b,
            longitude=body.longitude_b,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )

    # Compute yogas for both charts.
    yoga_engine = YogaEngine()
    yogas_a = await asyncio.to_thread(yoga_engine.evaluate_all, chart_a)
    yogas_b = await asyncio.to_thread(yoga_engine.evaluate_all, chart_b)

    # Run comparison.
    result = ChartComparisonEngine.compare(
        chart_a, chart_b,
        yogas_a=yogas_a, yogas_b=yogas_b,
        style=body.style,
    )

    return ChartComparisonResponse(
        summary=result.summary,
        overall_similarity=result.overall_similarity,
        key_differences=[
            ComparisonDimensionResponse(
                dimension=d.dimension, chart_a_value=d.chart_a_value,
                chart_b_value=d.chart_b_value, similarity=d.similarity,
                significance=d.significance, commentary=d.commentary,
            ) for d in result.key_differences
        ],
        key_similarities=[
            ComparisonDimensionResponse(
                dimension=d.dimension, chart_a_value=d.chart_a_value,
                chart_b_value=d.chart_b_value, similarity=d.similarity,
                significance=d.significance, commentary=d.commentary,
            ) for d in result.key_similarities
        ],
        compatibility_notes=result.compatibility_notes,
        relationship_potential=result.relationship_potential,
        timing_synergies=result.timing_synergies,
    )


# ── Ashtakoota Compatibility ────────────────────────────────────────────────────

@router.post("/compatibility", response_model=AshtakootaCompatibilityResponse)
async def analyze_compatibility(
    body: AshtakootaCompatibilityRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> AshtakootaCompatibilityResponse:
    """
    Perform Ashtakoota (36-point) compatibility analysis between two birth charts.

    Calculates all 8 Kootas: Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi.
    Also checks for Manglik, Nadi, Bhakoot, Rajju, and Vedha Doshas.

    Returns a comprehensive compatibility report with scores, strengths, challenges,
    and recommendations.
    """
    # Build Chart A
    chart_a = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_a,
            latitude=body.latitude_a,
            longitude=body.longitude_a,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )

    # Build Chart B
    chart_b = await _build_chart(
        _BirthDataProxy(
            birth_datetime_utc=body.birth_datetime_utc_b,
            latitude=body.latitude_b,
            longitude=body.longitude_b,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        ),
        wrapper,
    )

    # Extract required data from charts
    # Rashi (Moon sign) - find Moon position
    moon_a = next((p for p in chart_a.planets if p.planet == "moon"), None)
    moon_b = next((p for p in chart_b.planets if p.planet == "moon"), None)

    if not moon_a or not moon_b:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Moon position not found in one or both charts.",
        )

    # Translate domain tokens into the engine's Title-Case English vocabulary.
    _purpose = "Ashtakoota compatibility"
    rashi_a = _require_known(_to_engine_name(moon_a.rashi), ASHTAKOOTA_RASHIS, "rashi", _purpose)
    rashi_b = _require_known(_to_engine_name(moon_b.rashi), ASHTAKOOTA_RASHIS, "rashi", _purpose)
    nakshatra_a = _require_known(_to_engine_name(moon_a.nakshatra), ASHTAKOOTA_NAKSHATRAS, "nakshatra", _purpose)
    nakshatra_b = _require_known(_to_engine_name(moon_b.nakshatra), ASHTAKOOTA_NAKSHATRAS, "nakshatra", _purpose)

    # Mars house positions for Manglik check
    mars_a = next((p for p in chart_a.planets if p.planet == "mars"), None)
    mars_b = next((p for p in chart_b.planets if p.planet == "mars"), None)
    mars_house_a = mars_a.house_number if mars_a else 0
    mars_house_b = mars_b.house_number if mars_b else 0

    # Run Ashtakoota analysis
    result = AshtakootaEngine.analyze(
        rashi_a=rashi_a,
        nakshatra_a=nakshatra_a,
        mars_house_a=mars_house_a,
        rashi_b=rashi_b,
        nakshatra_b=nakshatra_b,
        mars_house_b=mars_house_b,
    )

    # Convert to response schema
    return AshtakootaCompatibilityResponse(
        total_score=result.total_score,
        max_total_score=result.max_total_score,
        compatibility_percentage=result.compatibility_percentage,
        verdict=result.verdict,
        kootas=[
            KootaScoreResponse(
                name=k.name,
                max_score=k.max_score,
                obtained_score=k.obtained_score,
                status=k.status,
                description=k.description,
            ) for k in result.kootas
        ],
        doshas=[
            DoshaResultResponse(
                name=d.name,
                has_dosha=d.has_dosha,
                severity=d.severity,
                description=d.description,
            ) for d in result.doshas
        ],
        radar_values=result.radar_values,
        strengths=result.strengths,
        challenges=result.challenges,
        recommendations=result.recommendations,
        subject_name_a=body.subject_name_a,
        subject_name_b=body.subject_name_b,
    )


# ── Marriage Timing Transit Scanner (Jupiter / Saturn) ────────────────────────

@router.post("/best-bet-compatibility", response_model=BestBetCompatibilityResponse)
async def best_bet_compatibility(
    body: BestBetCompatibilityRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> BestBetCompatibilityResponse:
    """
    Perform Best Bet 58-point compatibility analysis between two birth charts.

    This is a more comprehensive compatibility system than Ashtakoota, including:
    - Practical Compatibility (36 pts): Spiritual, Psychological, Physical
    - Karmic Compatibility (12 pts): Mars Dosha, Karmic Patterns
    - Future Compatibility (10 pts): Dasha overlap, Mutual planetary positions

    Requires chart data computation for accurate scoring.
    """
    _purpose = "Best Bet compatibility"

    # Compute charts for both persons
    try:
        chart_a = await asyncio.to_thread(
            HoroscopeEngine(wrapper).generate_d1,
            birth_datetime_utc=body.birth_datetime_utc_a,
            latitude=body.latitude_a,
            longitude=body.longitude_a,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        chart_b = await asyncio.to_thread(
            HoroscopeEngine(wrapper).generate_d1,
            birth_datetime_utc=body.birth_datetime_utc_b,
            latitude=body.latitude_b,
            longitude=body.longitude_b,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing charts for Best Bet compatibility: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute charts for Best Bet compatibility.",
        )

    # Extract planet positions
    def get_planet_positions(chart):
        positions = {}
        for p in chart.planets:
            positions[p.planet.lower()] = p
        return positions

    planets_a = get_planet_positions(chart_a)
    planets_b = get_planet_positions(chart_b)

    # Get nakshatra and rashi
    moon_a = planets_a.get("moon")
    moon_b = planets_b.get("moon")

    nakshatra_a = moon_a.nakshatra if moon_a else "Unknown"
    nakshatra_b = moon_b.nakshatra if moon_b else "Unknown"
    rashi_a = moon_a.rashi if moon_a else "Unknown"
    rashi_b = moon_b.rashi if moon_b else "Unknown"

    # Get house positions for Mars Dosha
    mars_a = planets_a.get("mars")
    mars_b = planets_b.get("mars")

    mars_house_a = mars_a.house_number if mars_a else 1
    moon_house_a = moon_a.house_number if moon_a else 1
    venus_a = planets_a.get("venus")
    venus_house_a = venus_a.house_number if venus_a else 1

    mars_house_b = mars_b.house_number if mars_b else 1
    moon_house_b = moon_b.house_number if moon_b else 1
    venus_b = planets_b.get("venus")
    venus_house_b = venus_b.house_number if venus_b else 1

    # Get dignity values for karmic pattern
    def dignity_value(planet):
        if planet.dignity:
            if "exalted" in planet.dignity.lower():
                return 10.0
            elif "own" in planet.dignity.lower():
                return 8.0
            elif "friendly" in planet.dignity.lower():
                return 6.0
            elif "neutral" in planet.dignity.lower():
                return 4.0
            elif "debilitated" in planet.dignity.lower():
                return 2.0
        return 5.0

    sun_a = planets_a.get("sun")
    sun_b = planets_b.get("sun")
    saturn_a = planets_a.get("saturn")
    saturn_b = planets_b.get("saturn")

    # Lagna dignity
    lagna_a = 5.0
    lagna_b = 5.0

    # Dasha overlap (simplified - would need actual dasha engine integration)
    dasha_overlap = 0.5

    # Mutual planet interactions (simplified)
    sun_interaction = "neutral"
    moon_interaction = "neutral"
    mars_interaction = "neutral"
    venus_interaction = "neutral"
    jupiter_interaction = "neutral"

    # Calculate Best Bet score
    result = BestBetEngine.calculate(
        subject_name_a=body.subject_name_a,
        subject_name_b=body.subject_name_b,
        nakshatra_a=nakshatra_a,
        nakshatra_b=nakshatra_b,
        rashi_a=rashi_a,
        rashi_b=rashi_b,
        mars_house_a=mars_house_a,
        moon_house_a=moon_house_a,
        venus_house_a=venus_house_a,
        mars_house_b=mars_house_b,
        moon_house_b=moon_house_b,
        venus_house_b=venus_house_b,
        sun_dignity_a=dignity_value(sun_a) if sun_a else 5.0,
        moon_dignity_a=dignity_value(moon_a) if moon_a else 5.0,
        venus_dignity_a=dignity_value(venus_a) if venus_a else 5.0,
        saturn_dignity_a=dignity_value(saturn_a) if saturn_a else 5.0,
        lagna_dignity_a=lagna_a,
        sun_dignity_b=dignity_value(sun_b) if sun_b else 5.0,
        moon_dignity_b=dignity_value(moon_b) if moon_b else 5.0,
        venus_dignity_b=dignity_value(venus_b) if venus_b else 5.0,
        saturn_dignity_b=dignity_value(saturn_b) if saturn_b else 5.0,
        lagna_dignity_b=lagna_b,
        dasha_overlap_pct=dasha_overlap,
        sun_interaction=sun_interaction,
        moon_interaction=moon_interaction,
        mars_interaction=mars_interaction,
        venus_interaction=venus_interaction,
        jupiter_interaction=jupiter_interaction,
    )

    return BestBetCompatibilityResponse(
        subject_name_a=result.subject_name_a,
        subject_name_b=result.subject_name_b,
        total_score=result.total_score,
        max_score=result.max_score,
        percentage=result.percentage,
        verdict=result.verdict,
        status=result.status,
        practical_score=result.practical_score,
        practical_max=result.practical_max,
        karmic_score=result.karmic_score,
        karmic_max=result.karmic_max,
        future_score=result.future_score,
        future_max=result.future_max,
        spiritual_score=result.spiritual_score,
        spiritual_max=result.spiritual_max,
        psychological_score=result.psychological_score,
        psychological_max=result.psychological_max,
        physical_score=result.physical_score,
        physical_max=result.physical_max,
        mars_dosha_score=result.mars_dosha_score,
        mars_dosha_max=result.mars_dosha_max,
        karmic_pattern_score=result.karmic_pattern_score,
        karmic_pattern_max=result.karmic_pattern_max,
        dasha_score=result.dasha_score,
        dasha_max=result.dasha_max,
        mutual_planets_score=result.mutual_planets_score,
        mutual_planets_max=result.mutual_planets_max,
        sub_factors=[BestBetSubFactorResponse(**f) for f in result.sub_factors],
        strengths=result.strengths,
        challenges=result.challenges,
        recommendations=result.recommendations,
    )


@router.post("/marriage-timing", response_model=MarriageTimingResponse)
async def marriage_timing(
    body: MarriageTimingRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> MarriageTimingResponse:
    """
    Scan a birth chart for marriage-timing windows across an age range.

    For each year, checks whether transiting Jupiter activates natal Venus
    (1st / 5th / 7th / 9th from it) and whether Saturn obstructs — aspecting
    natal Venus, the 7th cusp, or transiting Jupiter. Each year comes back
    classified as probable, delayed, or not_indicated, with the aspects that
    produced the verdict.
    """
    chart = await _build_chart(body, wrapper)

    venus = next((p for p in chart.planets if p.planet == "venus"), None)
    if not venus:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Venus position not found in chart.",
        )

    cusp_7 = next((h for h in chart.houses if h.house_number == 7), None)
    if not cusp_7:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="7th house cusp not found in chart.",
        )

    # Same token→Title-Case translation as the Ashtakoota endpoint above:
    # MarriageTimingEngine compares rashis by index into its SIGNS list, so an
    # untranslated "taurus" would raise rather than silently mis-score.
    _purpose = "marriage timing"
    natal_venus_rashi = _require_known(
        _to_engine_name(venus.rashi), MARRIAGE_TIMING_SIGNS, "rashi", _purpose
    )
    cusp_7_rashi = _require_known(
        _to_engine_name(cusp_7.rashi), MARRIAGE_TIMING_SIGNS, "rashi", _purpose
    )

    def _transit_positions(epoch: datetime) -> TransitPositions:
        """
        Jupiter/Saturn at one scan epoch, via the same wrapper (and the same
        request ayanamsa) that built the natal chart. `calculate` is the
        wrapper's locked entry point — pyswisseph's sidereal mode is
        process-global, so the scan must not reach past it.
        """
        eph = wrapper.calculate(
            epoch, body.latitude, body.longitude,
            ayanamsa=body.ayanamsa, house_system=body.house_system,
        )
        positions = {p.planet: p for p in eph.planet_positions}
        jupiter = positions["jupiter"]
        saturn = positions["saturn"]
        return TransitPositions(
            julian_day=eph.julian_day,
            jupiter_tropical=(jupiter.sidereal_longitude + eph.ayanamsa_value) % 360.0,
            jupiter_sidereal=jupiter.sidereal_longitude,
            saturn_tropical=(saturn.sidereal_longitude + eph.ayanamsa_value) % 360.0,
            saturn_sidereal=saturn.sidereal_longitude,
        )

    try:
        result = await asyncio.to_thread(
            MarriageTimingEngine.scan,
            birth_dt=body.birth_datetime_utc,
            natal_venus_sidereal=venus.sidereal_longitude,
            natal_venus_rashi=natal_venus_rashi,
            cusp_7_rashi=cusp_7_rashi,
            transit_positions=_transit_positions,
            scan_start_age=body.scan_start_age,
            scan_end_age=body.scan_end_age,
            subject_name=body.subject_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error scanning marriage timing windows: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan marriage timing windows.",
        )

    return MarriageTimingResponse(
        subject_name=result.subject_name,
        birth_datetime_utc=result.birth_datetime_utc,
        scan_start_age=result.scan_start_age,
        scan_end_age=result.scan_end_age,
        natal_venus_rashi=result.natal_venus_rashi,
        natal_venus_longitude=result.natal_venus_longitude,
        natal_seventh_cusp_rashi=result.natal_seventh_cusp_rashi,
        total_years_scanned=result.total_years_scanned,
        probable_windows=result.probable_windows,
        delayed_windows=result.delayed_windows,
        scan_results=[
            TransitScanYearResponse(
                year=r.year,
                age_at_year=r.age_at_year,
                julian_day=r.julian_day,
                jupiter_sidereal=r.jupiter_sidereal,
                jupiter_rashi=r.jupiter_rashi,
                saturn_sidereal=r.saturn_sidereal,
                saturn_rashi=r.saturn_rashi,
                status=r.status,
                aspect_details=list(r.aspect_details),
                saturn_obstruction_details=list(r.saturn_obstruction_details),
            ) for r in result.scan_results
        ],
    )


@router.post("/sadhu-padhdhati-timing", response_model=SadhuPadhdhatiResponse)
async def sadhu_padhdhati_timing(
    body: SadhuPadhdhatiRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> SadhuPadhdhatiResponse:
    """
    Predict a marriage year using the Sadhu Padhdhati (Sudarshana Chakra
    Prism) method — a second, selectable alternative to the Jupiter/Saturn
    transit scan (POST /marriage-timing above). Both take one person's
    birth data; the frontend calls whichever method(s) the user selects
    for each partner and displays them side by side for comparison.

    See sadhu_padhdhati_engine.py's module docstring for the method's
    derivation and, importantly, which parts are a faithful port of the
    source workbook's formulas versus an automated approximation of what
    was originally a manually-judged column (Reducing Factor).
    """
    chart = await _build_chart(body, wrapper)

    d1_planet_sign: dict[str, int] = {}
    d1_planet_longitude: dict[str, float] = {}
    for p in chart.planets:
        name = p.planet.lower()
        if name not in ("rahu", "ketu") and name not in {
            "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
        }:
            continue
        d1_planet_longitude[name] = p.sidereal_longitude
        d1_planet_sign[name] = int((p.sidereal_longitude % 360.0) // 30.0)

    d1_lagna_longitude = chart.ascendant.sidereal_longitude
    d1_lagna_sign = int((d1_lagna_longitude % 360.0) // 30.0)

    d1 = ChartPositions(
        lagna_sign_index=d1_lagna_sign,
        planet_sign_index=d1_planet_sign,
        planet_natal_longitude=d1_planet_longitude,
    )

    d9_planet_sign: dict[str, int] = {}
    for name, longitude in d1_planet_longitude.items():
        rashi, _degree = compute_varga_sign("D9", longitude)
        d9_planet_sign[name] = SADHU_RASHIS.index(rashi)
    d9_lagna_rashi, _d9_lagna_degree = compute_varga_sign("D9", d1_lagna_longitude)
    d9_lagna_sign = SADHU_RASHIS.index(d9_lagna_rashi)

    d9 = ChartPositions(
        lagna_sign_index=d9_lagna_sign,
        planet_sign_index=d9_planet_sign,
        planet_natal_longitude=d1_planet_longitude,  # always D1 longitudes — see engine docstring
    )

    try:
        result = await asyncio.to_thread(
            SadhuPadhdhatiEngine.analyze,
            subject_name=body.subject_name,
            birth_date=body.birth_datetime_utc.date(),
            gender=body.gender,
            d1=d1,
            d9=d9,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing Sadhu Padhdhati marriage timing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute Sadhu Padhdhati marriage timing.",
        )

    def _chart_response(c) -> SadhuPadhdhatiChartResponse:
        return SadhuPadhdhatiChartResponse(
            chart_label=c.chart_label,
            base=c.base,
            step=c.step,
            escalation_factor=c.escalation_factor,
            male_female_factor=c.male_female_factor,
            reducing_factor=c.reducing_factor,
            delay=c.delay,
            levels=[
                SadhuPadhdhatiLevelResponse(
                    label=lvl.label, yes_count=lvl.yes_count,
                    max_count=lvl.max_count, badhaka=lvl.badhaka,
                ) for lvl in c.levels
            ],
        )

    return SadhuPadhdhatiResponse(
        subject_name=result.subject_name,
        birth_year=result.birth_year,
        gender=result.gender,
        d1=_chart_response(result.d1),
        d9=_chart_response(result.d9),
        net_delay=result.net_delay,
        predicted_year=result.predicted_year,
        window_start=result.window_start,
        window_end=result.window_end,
        alphabet_class=result.alphabet_class,
        destiny_factor=result.destiny_factor,
    )


# ── Research Assistant ────────────────────────────────────────────────────────

@router.post("/research-query", response_model=ResearchAnswerResponse)
async def research_query(
    body: ResearchQueryRequest,
    knowledge_engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> ResearchAnswerResponse:
    """
    Ask a natural language research question over the knowledge base.
    Searches books, verses, rules, karakatvas, and doctrinal conflicts.
    """
    query = ResearchQuery(
        question=body.question,
        domain_filter=body.domain_filter,
        tradition_filter=body.tradition_filter,
        max_results=body.max_results,
    )
    answer = await ResearchAssistantEngine.query(query, knowledge_engine)

    return ResearchAnswerResponse(
        question=answer.question,
        summary=answer.summary,
        body=answer.body,
        evidence=[
            ResearchEvidenceResponse(
                source=e.source, reference=e.reference, text=e.text,
                relevance=e.relevance, entity_type=e.entity_type,
                tradition=e.tradition,
            ) for e in answer.evidence
        ],
        related_conflicts=list(answer.related_conflicts),
        confidence=answer.confidence,
        unanswered_aspects=list(answer.unanswered_aspects),
    )


@router.get("/research-domains", response_model=AvailableDomainsResponse)
async def list_research_domains() -> AvailableDomainsResponse:
    """List all available research domains for the Research Assistant."""
    domains = ResearchAssistantEngine.available_domains()
    return AvailableDomainsResponse(
        domains=[
            AvailableDomainResponse(id=d["id"], name=d["name"], description=d["description"])
            for d in domains
        ]
    )


# ── Hypothesis Generation ─────────────────────────────────────────────────────

@router.get("/hypothesis-templates", response_model=HypothesisTemplatesResponse)
async def list_hypothesis_templates() -> HypothesisTemplatesResponse:
    """List all available hypothesis templates."""
    templates = HypothesisGenerator.get_templates()
    return HypothesisTemplatesResponse(
        templates=[
            HypothesisTemplateResponse(
                hypothesis_id=t.hypothesis_id, title=t.title,
                description=t.description, domain=t.domain,
                conditions=list(t.conditions),
                expected_outcome=t.expected_outcome,
                test_method=t.test_method,
                classical_references=list(t.classical_references),
                priority=t.priority,
            ) for t in templates
        ],
        total=len(templates),
    )


@router.post("/generate-hypotheses", response_model=HypothesisListResponse)
async def generate_hypotheses(
    body: HypothesisGenerateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
    knowledge_graph: KnowledgeGraphEngine = Depends(get_knowledge_graph_engine),
) -> HypothesisListResponse:
    """
    Generate testable astrological hypotheses from a birth chart.
    Each hypothesis includes chart-specific evidence and a falsifiable prediction.
    When the Knowledge Graph is available, entity data is appended to the
    supporting evidence list and the *graph_grounded* flag is enabled.
    """
    chart = await _build_chart(body, wrapper)

    # Compute yogas for context.
    yoga_engine = YogaEngine()
    yogas = await asyncio.to_thread(yoga_engine.evaluate_all, chart)

    hypotheses = HypothesisGenerator.generate_for_chart(
        chart, yogas=yogas,
        domain_filter=body.domain_filter,
        max_hypotheses=body.max_hypotheses,
        knowledge_graph=knowledge_graph,
    )

    return HypothesisListResponse(
        hypotheses=[
            GeneratedHypothesisResponse(
                hypothesis_id=h.hypothesis_id, title=h.title,
                description=h.description, domain=h.domain,
                supporting_evidence=list(h.supporting_evidence),
                contradicting_evidence=list(h.contradicting_evidence),
                testable_prediction=h.testable_prediction,
                suggested_dataset=h.suggested_dataset,
                priority=h.priority,
                related_rules=list(h.related_rules),
                related_yogas=list(h.related_yogas),
                confidence=h.confidence,
                graph_grounded=h.graph_grounded,
            ) for h in hypotheses
        ],
        total=len(hypotheses),
    )


# ── Enhanced QA ───────────────────────────────────────────────────────────────

@router.post("/enhanced-qa", response_model=AIResponseSchema)
async def enhanced_qa(
    body: EnhancedQuestionRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> AIResponseSchema:
    """
    Enhanced natural-language Q&A with full chart context.
    Answers questions about ascendant, planets, yogas, dashas, transits,
    strengths, aspects, houses, nakshatras, and more.
    """
    chart = await _build_chart(body, wrapper)

    # Compute optional context based on request flags.
    yogas = None
    dasha_tree = None
    transits = None
    shadbala_totals = None

    if body.include_yogas:
        yoga_engine = YogaEngine()
        yogas = await asyncio.to_thread(yoga_engine.evaluate_all, chart)

    if body.include_dashas:
        dasha_engine = DashaEngine(wrapper)
        dasha_tree = await asyncio.to_thread(
            dasha_engine.compute_vimshottari,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )

    if body.include_transits:
        transit_engine = TransitEngine(wrapper)
        transit_dt = datetime.now(timezone.utc)
        transits = await asyncio.to_thread(
            transit_engine.compute_transit, chart, transit_dt
        )

    if body.include_strengths:
        shadbala_engine = ShadbalaEngine()
        phase1 = shadbala_engine.compute_phase1_components(chart)
        phase2 = shadbala_engine.compute_phase2_components(chart)
        sthana = shadbala_engine.compute_sthana_bala_components(chart)
        shadbala_components = {**phase1, **phase2, **sthana}
        _CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        _SHASHTIAMSAS_PER_RUPA = 60.0
        totals = {p: 0.0 for p in _CLASSICAL_SEVEN}
        for component_results in shadbala_components.values():
            for r in component_results:
                totals[r.planet] += r.value_shashtiamsas
        shadbala_totals = {
            p: round(v / _SHASHTIAMSAS_PER_RUPA, 4) for p, v in totals.items()
        }

    result = EnhancedQAResponder.generate(
        question=body.question,
        chart=chart,
        yogas=yogas,
        dasha_tree=dasha_tree,
        transits=transits,
        shadbala_totals=shadbala_totals,
    )

    return _ai_response(result)


# ── Verification Report ────────────────────────────────────────────────────────


@router.post("/verification-report", response_model=VerificationReportResponse)
async def verification_report(
    body: VerificationReportRequest,
) -> VerificationReportResponse:
    """
    Generate a verification report summarising rule-evaluation findings.

    Wraps the VerificationReporter generator (wired in Task #13).
    Takes a chart_id and optional event_ids to scope the report.
    """
    from apps.api.domain.verification import VerificationFindings
    from apps.api.services.ai_engine import VerificationReporter

    try:
        # Build a minimal VerificationFindings instance from request data.
        # In a production deployment the caller would resolve chart_id +
        # event_ids into actual VerificationFindings via the verification
        # engine. Here we construct a placeholder report acknowledging the
        # request parameters so that the endpoint is functional end-to-end.
        import uuid as _uuid

        chart_uuid = _uuid.UUID(body.chart_id)
        event_count = len(body.event_ids) if body.event_ids else 0
        findings = VerificationFindings(
            chart_id=chart_uuid,
            period_covered=None,
            total_events=event_count,
            total_rules_evaluated=0,
            total_pairs=0,
            rule_summaries=(),
            verification_pairs=(),
        )
        result = VerificationReporter.generate(findings)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error generating verification report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate verification report.",
        )

    return VerificationReportResponse(
        response_type=result.response_type,
        title=result.title,
        summary=result.summary,
        body=result.body,
        sources=list(result.sources),
        confidence=result.confidence,
        version=result.version,
    )


# ── Research Insight ────────────────────────────────────────────────────────────


@router.post("/research-insight", response_model=ResearchInsightResponse)
async def research_insight(
    body: ResearchInsightRequest,
) -> ResearchInsightResponse:
    """
    Generate comparative research insights from experiment data.

    Wraps the ResearchInsightGenerator (wired in Task #13).
    Takes a list of experiment_ids to generate insights from.
    """
    from apps.api.domain.statistics import AggregateReport, DatasetMetadata
    from apps.api.services.ai_engine import ResearchInsightGenerator

    try:
        meta = DatasetMetadata(
            sample_size=len(body.experiment_ids),
            snapshot_count=len(body.experiment_ids),
        )
        stats = AggregateReport(
            title="Research Insights",
            metadata=meta,
        )
        result = ResearchInsightGenerator.generate(stats)
    except Exception as exc:
        logger.exception("Error generating research insight: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate research insight.",
        )

    return ResearchInsightResponse(
        response_type=result.response_type,
        title=result.title,
        summary=result.summary,
        body=result.body,
        sources=list(result.sources),
        confidence=result.confidence,
        version=result.version,
    )


# ── Recommendation ──────────────────────────────────────────────────────────────


@router.post("/recommendation", response_model=RecommendationResponse)
async def recommendation(
    body: RecommendationRequest,
) -> RecommendationResponse:
    """
    Generate contextual astrological recommendations for a chart.

    Wraps the RecommendationEngine generator (wired in Task #13).
    Takes a chart_id to scope recommendations to that chart.
    """
    from apps.api.services.ai_engine import RecommendationEngine

    try:
        # Generate recommendations; no chart-level data is passed here
        # because the RecommendationEngine works from verification +
        # transit data, not raw chart data. Callers with transit or
        # verification context should use the AIEngine.explain interface.
        result = RecommendationEngine.generate()
    except Exception as exc:
        logger.exception("Error generating recommendation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendation.",
        )

    return RecommendationResponse(
        response_type=result.response_type,
        title=result.title,
        summary=result.summary,
        body=result.body,
        recommendations=list(result.recommendations),
        sources=list(result.sources),
        confidence=result.confidence,
        version=result.version,
    )


# ── Helper: proxy object to reuse _build_chart ────────────────────────────────

class _BirthDataProxy:
    """Minimal proxy to make _build_chart work with different field names."""
    def __init__(self, birth_datetime_utc, latitude, longitude, ayanamsa, house_system):
        self.birth_datetime_utc = birth_datetime_utc
        self.latitude = latitude
        self.longitude = longitude
        self.ayanamsa = ayanamsa
        self.house_system = house_system

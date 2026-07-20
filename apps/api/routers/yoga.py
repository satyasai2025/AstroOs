"""
AstroOS — Yoga Router

Endpoints
---------
GET  /api/v1/yoga/catalog                       — List every registered yoga definition (no chart needed)
GET  /api/v1/yoga/catalog/by-category/{category} — Yoga definitions filtered by category
POST /api/v1/yoga/evaluate                      — Evaluate every registered yoga against a birth chart
POST /api/v1/yoga/evaluate/{yoga_id}            — Evaluate a single yoga by its stable ID
POST /api/v1/yoga/evaluate/with-strength        — Evaluate with 0-100 strength scores
POST /api/v1/yoga/evaluate/timeline             — Evaluate with Dasha activation timelines
POST /api/v1/yoga/evaluate/present-only         — Evaluate and return only present yogas

No business logic lives here. A D1 chart is built via HoroscopeEngine
(the same engine horoscope.py's /d1 endpoint uses) and handed to
YogaEngine, which evaluates every registered yoga against it (see
services/yoga_engine.py and services/yoga_registry.py).

YogaEngine deliberately has no persistence layer (see its docstring) —
same scope discipline as HouseEngine — so these endpoints compute and
return without saving anything. No repositories are constructed here
for that reason.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.yoga import YogaResult
from apps.api.schemas.yoga import (
    YogaActivationResponse,
    YogaCatalogResponse,
    YogaDefinitionResponse,
    YogaEvaluationRequest,
    YogaEvaluationResponse,
    YogaResultResponse,
    YogaTimelineEvaluationResponse,
    YogaTimelineResponse,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_registry import all_yogas, get_yoga
from apps.api.services.yoga_timeline import YogaActivation, YogaTimeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/yoga", tags=["Yoga"])


# ── DI ────────────────────────────────────────────────────────────────────────


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    """
    Build a HoroscopeEngine using the process-wide EphemerisWrapper
    singleton, to build the D1 chart yogas are evaluated against.

    Does NOT construct a new EphemerisWrapper — see get_ephemeris_wrapper's
    docstring for why that would reintroduce a global-state race condition.
    No repositories are passed in: this router never calls persist_d1,
    since Yoga evaluation only needs a chart, not a saved one.
    """
    return HoroscopeEngine(wrapper)


def _get_yoga_engine() -> YogaEngine:
    """
    YogaEngine is stateless and has no Swiss Ephemeris or database
    dependency (see services/yoga_engine.py) — it only needs an
    already-built D1Chart, supplied per-call by the endpoint below.
    """
    return YogaEngine()


def _get_dasha_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> DashaEngine:
    """
    Build a DashaEngine using the process-wide EphemerisWrapper singleton.

    Repositories are not needed here — we only compute a DashaTree for
    timeline correlation; we never persist it.
    """
    return DashaEngine(wrapper)


# ── Serialisation ──────────────────────────────────────────────────────────────


def _serialise_result(result: YogaResult) -> YogaResultResponse:
    return YogaResultResponse(
        yoga_id=result.yoga_id,
        name=result.name,
        category=result.category,
        source_text=result.source_text,
        rule_version=result.rule_version,
        is_present=result.is_present,
        strength=result.strength,
        involved_planets=list(result.involved_planets),
        involved_houses=list(result.involved_houses),
        satisfied=list(result.satisfied),
        missing=list(result.missing),
        trace=list(result.trace),
        strength_score=result.strength_score,
        counter_examples=list(result.counter_examples),
    )


def _serialise_activation(act: YogaActivation) -> YogaActivationResponse:
    """Convert a YogaActivation dataclass to its Pydantic response model."""
    return YogaActivationResponse(
        yoga_id=act.yoga_id,
        planet=act.planet,
        period_name=act.period_name,
        period_level=act.period_level,
        start_date=act.start_date,
        end_date=act.end_date,
        is_current=act.is_current,
    )


def _serialise_timeline(timeline: YogaTimeline) -> YogaTimelineResponse:
    """Convert a YogaTimeline dataclass to its Pydantic response model."""
    return YogaTimelineResponse(
        yoga_id=timeline.yoga_id,
        yoga_name=timeline.yoga_name,
        activations=[_serialise_activation(a) for a in timeline.activations],
        current_activation=(
            _serialise_activation(timeline.current_activation)
            if timeline.current_activation is not None
            else None
        ),
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/catalog",
    response_model=YogaCatalogResponse,
    summary="List every registered yoga definition",
    description=(
        "Returns the static catalog of every registered yoga rule "
        "(id, name, category, source, version, dependencies). No birth "
        "chart is computed or required for this endpoint."
    ),
)
async def list_yoga_catalog() -> YogaCatalogResponse:
    definitions = all_yogas()
    return YogaCatalogResponse(
        yogas=[
            YogaDefinitionResponse(
                yoga_id=d.yoga_id,
                name=d.name,
                category=d.category,
                source_text=d.source_text,
                rule_version=d.rule_version,
                requires=list(d.requires),
            )
            for d in definitions
        ],
        total=len(definitions),
    )


@router.get(
    "/catalog/by-category/{category}",
    response_model=YogaCatalogResponse,
    summary="List yoga definitions filtered by category",
    description=(
        "Returns registered yoga definitions filtered by a specific "
        "category (e.g. 'Chandra Yoga', 'Nabhasa Yoga'). No birth chart "
        "is required."
    ),
)
async def list_yoga_catalog_by_category(
    category: str = Path(..., description="Yoga category to filter by, e.g. 'Chandra Yoga'."),
) -> YogaCatalogResponse:
    """Return only yoga definitions that belong to the given category."""
    definitions = all_yogas()
    filtered = [d for d in definitions if d.category == category]
    return YogaCatalogResponse(
        yogas=[
            YogaDefinitionResponse(
                yoga_id=d.yoga_id,
                name=d.name,
                category=d.category,
                source_text=d.source_text,
                rule_version=d.rule_version,
                requires=list(d.requires),
            )
            for d in filtered
        ],
        total=len(filtered),
    )


@router.post(
    "/evaluate",
    response_model=YogaEvaluationResponse,
    summary="Evaluate every registered yoga against a birth chart",
    description=(
        "Builds a D1 chart from the given birth data and evaluates every "
        "registered yoga against it. Returns a result for every yoga by "
        "default — including ones that did not fire — unless only_present "
        "is set to true."
    ),
)
async def evaluate_all_yogas(
    body: YogaEvaluationRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    yoga_engine: YogaEngine = Depends(_get_yoga_engine),
) -> YogaEvaluationResponse:
    try:
        # Blocking pyswisseph call — offload to a worker thread so it does
        # not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale. evaluate_all is pure Python (no
        # ephemeris call) but is offloaded alongside it for consistency
        # and to keep this handler's shape identical to the other routers.
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        results = await asyncio.to_thread(yoga_engine.evaluate_all, chart)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error evaluating yogas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate yogas.",
        )

    total_evaluated = len(results)
    total_present = sum(1 for r in results if r.is_present)
    if body.only_present:
        results = [r for r in results if r.is_present]

    # Apply category filter if requested
    if body.category:
        results = [r for r in results if r.category == body.category]

    return YogaEvaluationResponse(
        results=[_serialise_result(r) for r in results],
        total_evaluated=total_evaluated,
        total_present=total_present,
    )


@router.post(
    "/evaluate/{yoga_id}",
    response_model=YogaResultResponse,
    summary="Evaluate a single yoga by its stable ID",
    description=(
        "Builds a D1 chart from the given birth data and evaluates one "
        "registered yoga (by yoga_id, e.g. 'BPHS-PM-001') against it. "
        "See GET /yoga/catalog for valid IDs."
    ),
)
async def evaluate_one_yoga(
    body: YogaEvaluationRequest,
    yoga_id: str = Path(..., description="Stable yoga ID, e.g. 'BPHS-PM-001'."),
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    yoga_engine: YogaEngine = Depends(_get_yoga_engine),
) -> YogaResultResponse:
    if get_yoga(yoga_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown yoga_id '{yoga_id}'. See GET /yoga/catalog for valid IDs.",
        )

    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        result = await asyncio.to_thread(yoga_engine.evaluate_one, chart, yoga_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error evaluating yoga %s: %s", yoga_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate yoga {yoga_id}.",
        )

    if result is None:
        # Evaluator ran but declined to produce a result for this chart
        # (distinct from "yoga_id not found", already handled above).
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yoga {yoga_id} evaluator returned no result.",
        )

    return _serialise_result(result)


# ── Phase 2: Strength-scored evaluation ───────────────────────────────────────


@router.post(
    "/evaluate/with-strength",
    response_model=YogaEvaluationResponse,
    summary="Evaluate yogas with 0-100 strength scores",
    description=(
        "Builds a D1 chart and evaluates every registered yoga, computing "
        "a 0-100 numerical strength score for each one based on planetary "
        "dignity, house placement, aspects, conjunctions, combustion, and "
        "retrograde status. Returns every yoga result with strength_score "
        "populated; non-present yogas receive a score of 0."
    ),
)
async def evaluate_yogas_with_strength(
    body: YogaEvaluationRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    yoga_engine: YogaEngine = Depends(_get_yoga_engine),
) -> YogaEvaluationResponse:
    """Evaluate all yogas and attach numerical strength scores."""
    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        results = await asyncio.to_thread(yoga_engine.evaluate_with_strength, chart)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error evaluating yogas with strength: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate yogas with strength scores.",
        )

    total_evaluated = len(results)
    total_present = sum(1 for r in results if r.is_present)
    if body.only_present:
        results = [r for r in results if r.is_present]

    # Apply category filter if requested
    if body.category:
        results = [r for r in results if r.category == body.category]

    return YogaEvaluationResponse(
        results=[_serialise_result(r) for r in results],
        total_evaluated=total_evaluated,
        total_present=total_present,
        strength_scored=True,
    )


# ── Phase 2: Dasha activation timeline ────────────────────────────────────────


@router.post(
    "/evaluate/timeline",
    response_model=YogaTimelineEvaluationResponse,
    summary="Evaluate yogas with Dasha activation timelines",
    description=(
        "Builds a D1 chart and correlates all present yogas with Dasha "
        "periods to determine when each yoga activates. A yoga activates "
        "when any of its involved planets rule the current Mahadasha or "
        "Antardasha period. Uses Vimshottari dasha by default."
    ),
)
async def evaluate_yogas_with_timeline(
    body: YogaEvaluationRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    yoga_engine: YogaEngine = Depends(_get_yoga_engine),
    dasha_engine: DashaEngine = Depends(_get_dasha_engine),
) -> YogaTimelineEvaluationResponse:
    """Evaluate yogas and return Dasha-based activation timelines."""
    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )

        # Compute the DashaTree for the requested system.
        # DashaEngine methods are synchronous; offload to a worker thread.
        dasha_compute = _DASHA_SYSTEM_MAP.get(body.dasha_system)
        if dasha_compute is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported dasha system: {body.dasha_system!r}",
            )
        dasha_tree = await asyncio.to_thread(
            dasha_compute,
            dasha_engine,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
            max_depth=body.max_depth,
        )

        today = date.today()
        timelines = await asyncio.to_thread(
            yoga_engine.get_activation_timeline,
            chart,
            dasha_tree,
            today,
            body.max_depth,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error building yoga timelines: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build yoga activation timelines.",
        )

    total_present = len(timelines)
    total_activated = sum(1 for t in timelines if t.activations)

    return YogaTimelineEvaluationResponse(
        timelines=[_serialise_timeline(t) for t in timelines],
        total_present=total_present,
        total_activated=total_activated,
        dasha_system=body.dasha_system,
    )


# Mapping from dasha_system string to the DashaEngine compute method.
_DASHA_SYSTEM_MAP = {
    "vimshottari": lambda engine, **kw: engine.compute_vimshottari(**kw),
    "yogini": lambda engine, **kw: engine.compute_yogini(**kw),
    "ashtottari": lambda engine, **kw: engine.compute_ashtottari(**kw),
    "kalachakra": lambda engine, **kw: engine.compute_kalachakra(**kw),
    "chara": lambda engine, **kw: engine.compute_chara(**kw),
    "narayana": lambda engine, **kw: engine.compute_narayana(**kw),
}


# ── Phase 2: Present-only evaluation ──────────────────────────────────────────


@router.post(
    "/evaluate/present-only",
    response_model=YogaEvaluationResponse,
    summary="Evaluate yogas and return only present (fired) results",
    description=(
        "Builds a D1 chart and evaluates every registered yoga, then "
        "returns only the yogas that are present (is_present=True). "
        "Equivalent to POST /evaluate with only_present=true, but offered "
        "as a dedicated endpoint for clarity."
    ),
)
async def evaluate_present_yogas(
    body: YogaEvaluationRequest,
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
    yoga_engine: YogaEngine = Depends(_get_yoga_engine),
) -> YogaEvaluationResponse:
    """Evaluate all yogas and return only the ones that fired."""
    try:
        chart = await asyncio.to_thread(
            horoscope_engine.generate_d1,
            birth_datetime_utc=body.birth_datetime_utc,
            latitude=body.latitude,
            longitude=body.longitude,
            ayanamsa=body.ayanamsa,
            house_system=body.house_system,
        )
        results = await asyncio.to_thread(yoga_engine.get_present_yogas, chart)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error evaluating present yogas: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate yogas.",
        )

    # Apply category filter if requested
    if body.category:
        results = [r for r in results if r.category == body.category]

    total_present = len(results)

    return YogaEvaluationResponse(
        results=[_serialise_result(r) for r in results],
        total_evaluated=total_present,
        total_present=total_present,
    )

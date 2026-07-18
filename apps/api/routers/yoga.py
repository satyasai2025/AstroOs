"""
AstroOS — Yoga Router

Endpoints
---------
GET  /api/v1/yoga/catalog            — List every registered yoga definition (no chart needed)
POST /api/v1/yoga/evaluate           — Evaluate every registered yoga against a birth chart
POST /api/v1/yoga/evaluate/{yoga_id} — Evaluate a single yoga by its stable ID

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

from fastapi import APIRouter, Depends, HTTPException, Path, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.domain.yoga import YogaResult
from apps.api.schemas.yoga import (
    YogaCatalogResponse,
    YogaDefinitionResponse,
    YogaEvaluationRequest,
    YogaEvaluationResponse,
    YogaResultResponse,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_registry import all_yogas, get_yoga

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

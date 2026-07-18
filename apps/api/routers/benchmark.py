"""
AstroOS — Benchmark Router (Phase C)

Endpoints:
  POST /api/v1/benchmark/validate        — validate one chart against GC-MASTER
  POST /api/v1/benchmark/validate/all    — validate all GC-MASTER references
"""

from __future__ import annotations

import asyncio
import functools
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.schemas.benchmark import (
    BenchmarkValidateAllRequest,
    BenchmarkValidateRequest,
    BenchmarkValidateResponse,
    BenchmarkSummaryResponse,
    BenchmarkDetailResponse,
    PlanetBenchmarkResultResponse,
    HouseCuspBenchmarkResponse,
    VargaBenchmarkResponse,
)
from apps.api.services.benchmark_engine import BenchmarkEngine
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


def _get_benchmark_engine() -> BenchmarkEngine:
    return BenchmarkEngine()


# ── Serializers ────────────────────────────────────────────────────────────────


def _serialize_summary(summary) -> BenchmarkSummaryResponse:
    details: list[BenchmarkDetailResponse] = []
    for r in summary.results:
        details.append(BenchmarkDetailResponse(
            reference_id=r.reference_id,
            reference_name=r.reference_name,
            calc_passed=r.passed,
            calc_mean_error=r.mean_error,
            calc_max_error=r.max_error,
        ))

    return BenchmarkSummaryResponse(
        total_charts=summary.total_charts,
        passed=summary.passed,
        failed=summary.failed,
        overall_mean_error=summary.overall_mean_error,
        family_summary=summary.family_summary,
        details=details,
        timestamp=summary.timestamp,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "/validate",
    response_model=BenchmarkValidateResponse,
    summary="Validate a chart against GC-MASTER golden reference",
)
async def validate_chart(
    body: BenchmarkValidateRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> BenchmarkValidateResponse:
    """Accept birth data, compute chart, and validate against GC-MASTER."""
    try:
        engine = _get_benchmark_engine()
        if not engine.is_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GC-MASTER data is not loaded.",
            )

        horoscope = HoroscopeEngine(wrapper)
        divisional = DivisionalEngine(wrapper)

        def _compute():
            # Compute chart with requested house system (primary).
            chart = horoscope.generate_d1(
                birth_datetime_utc=body.birth_datetime_utc,
                latitude=body.latitude, longitude=body.longitude,
                ayanamsa=body.ayanamsa, house_system=body.house_system,
            )
            vargas = None
            if body.include_vargas:
                vargas = divisional.compute_all(
                    birth_datetime_utc=body.birth_datetime_utc,
                    latitude=body.latitude, longitude=body.longitude,
                    ayanamsa=body.ayanamsa, house_system=body.house_system,
                )
            # Compute charts for each house system for house cusp validation.
            house_charts = {}
            if body.include_houses:
                for hs in ["W", "P", "K", "E"]:
                    house_charts[hs] = horoscope.generate_d1(
                        birth_datetime_utc=body.birth_datetime_utc,
                        latitude=body.latitude, longitude=body.longitude,
                        ayanamsa=body.ayanamsa, house_system=hs,
                    )
            return chart, vargas, house_charts

        chart, vargas, house_charts = await asyncio.to_thread(_compute)

        # Validate each house system against its own computed chart.
        house_results_list = []
        if body.include_houses and house_charts:
            for hs, hc in house_charts.items():
                hr = engine.validate_house_cusps(
                    hc, hs,
                    reference_id=body.reference_id,
                    subject_name=body.subject_name,
                )
                house_results_list.append(hr)

        # CALC + VARGA validate against primary chart.
        calc_result = engine.validate_chart(
            chart,
            reference_id=body.reference_id,
            subject_name=body.subject_name,
        )

        varga_results_list = []
        if body.include_vargas and vargas:
            for vc in sorted(vargas.keys()):
                vr = engine.validate_varga(
                    vargas[vc],
                    reference_id=body.reference_id,
                    subject_name=body.subject_name,
                )
                varga_results_list.append(vr)

        from datetime import datetime, timezone
        from apps.api.domain.benchmark import BenchmarkSummary

        total_passed = 1 if calc_result.passed else 0
        total_failed = 0 if calc_result.passed else 1

        all_house_passed = all(h.passed for h in house_results_list)
        all_varga_passed = all(v.failed == 0 for v in varga_results_list)

        if house_results_list:
            total_passed += (1 if all_house_passed else 0)
            total_failed += (0 if all_house_passed else 1)
        if varga_results_list:
            total_passed += (1 if all_varga_passed else 0)
            total_failed += (0 if all_varga_passed else 1)

        house_mean = sum(h.mean_error for h in house_results_list) / len(house_results_list) if house_results_list else 0.0
        family = {
            "calc": {"passed": 1 if calc_result.passed else 0, "failed": 0 if calc_result.passed else 1, "mean_error": calc_result.mean_error},
        }
        if house_results_list:
            family["house"] = {"passed": sum(1 for h in house_results_list if h.passed), "failed": sum(1 for h in house_results_list if not h.passed), "mean_error": round(house_mean, 4)}
        if varga_results_list:
            total_checks = sum(v.total_checks for v in varga_results_list)
            total_matched = sum(v.matched for v in varga_results_list)
            family["varga"] = {"passed": total_matched, "failed": sum(v.failed for v in varga_results_list), "total_checks": total_checks}

        summary = BenchmarkSummary(
            total_charts=1,
            passed=total_passed,
            failed=total_failed,
            results=(calc_result,),
            overall_mean_error=calc_result.mean_error,
            house_results=tuple(house_results_list),
            varga_results=tuple(varga_results_list),
            family_summary=family,
        )

        return BenchmarkValidateResponse(
            status="passed" if summary.failed == 0 else "failed",
            summary=_serialize_summary(summary),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Benchmark validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/validate/all",
    response_model=BenchmarkValidateResponse,
    summary="Validate all GC-MASTER references at once",
)
async def validate_all_references(
    body: BenchmarkValidateAllRequest,
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> BenchmarkValidateResponse:
    """Run full validation against every GC-MASTER reference chart."""
    try:
        engine = _get_benchmark_engine()
        if not engine.is_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GC-MASTER data is not loaded.",
            )

        horoscope = HoroscopeEngine(wrapper)
        divisional = DivisionalEngine(wrapper)

        def _compute_all():
            return engine.validate_all_references(
                horoscope, divisional,
                house_systems=["W", "P", "K", "E"] if body.include_houses else None,
                include_vargas=body.include_vargas,
            )

        summary = await asyncio.to_thread(_compute_all)

        return BenchmarkValidateResponse(
            status="passed" if summary.failed == 0 else "failed",
            summary=_serialize_summary(summary),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Benchmark validate/all failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

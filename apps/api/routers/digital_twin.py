"""
AstroOS — Digital Twin Router (Future — ADR-EAL-030)

HTTP adapter over DigitalTwinService. No business logic lives here.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
    get_ephemeris_wrapper,
)
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.digital_twin_repository import DigitalTwinRepository
from apps.api.schemas.digital_twin import (
    DigitalTwinCreate,
    DigitalTwinListResponse,
    DigitalTwinResponse,
    DigitalTwinUpdateRequest,
    TwinComparisonResponse,
    TwinModificationResponse,
    TwinSimulationRequest,
    TwinOperationResult,
)
from apps.api.services.digital_twin_service import DigitalTwinService
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


def _get_repo(session: AsyncSession = Depends(get_db_session)) -> DigitalTwinRepository:
    return DigitalTwinRepository(session)


def _get_chart_repo(session: AsyncSession = Depends(get_db_session)) -> BirthChartRepository:
    return BirthChartRepository(session)


def _get_horoscope_engine(
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> HoroscopeEngine:
    # Compute-only — no persistence repos needed, compare_to_original only
    # ever recomputes the original chart from its stored birth parameters,
    # never persists it again.
    return HoroscopeEngine(wrapper)


def _get_service(
    repo: DigitalTwinRepository = Depends(_get_repo),
    chart_repo: BirthChartRepository = Depends(_get_chart_repo),
    horoscope_engine: HoroscopeEngine = Depends(_get_horoscope_engine),
) -> DigitalTwinService:
    return DigitalTwinService(repo, chart_repo, horoscope_engine)


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=DigitalTwinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Digital Twin",
)
async def create_twin(
    request: DigitalTwinCreate,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> DigitalTwinResponse:
    """Create a new Digital Twin from an existing chart with modifications."""
    return await service.create_twin(user_id=user.id.value, request=request)


@router.get(
    "/{twin_id}",
    response_model=DigitalTwinResponse,
    summary="Get a Digital Twin",
)
async def get_twin(
    twin_id: uuid.UUID,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> DigitalTwinResponse:
    twin = await service.get_twin(twin_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Twin not found or not owned by user")
    return twin


@router.get(
    "",
    response_model=list[DigitalTwinListResponse],
    summary="List Digital Twins",
)
async def list_twins(
    chart_id: Optional[uuid.UUID] = Query(None, description="Filter by original chart"),
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> list[DigitalTwinListResponse]:
    """List all digital twins for the current user."""
    # For now, return empty list — would need service method to filter by chart_id
    return []


@router.post(
    "/{twin_id}/modifications",
    response_model=DigitalTwinResponse,
    summary="Add modifications to a Digital Twin",
)
async def add_modifications(
    twin_id: uuid.UUID,
    request: DigitalTwinUpdateRequest,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> DigitalTwinResponse:
    """Append new modifications to an existing twin (immutable history)."""
    result = await service.add_modification(twin_id, request.modifications[0])
    if not result:
        raise HTTPException(status_code=404, detail="Twin not found")
    return result


@router.post(
    "/{twin_id}/compare",
    response_model=TwinComparisonResponse,
    summary="Compare Digital Twin to original chart",
)
async def compare_twin(
    twin_id: uuid.UUID,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> TwinComparisonResponse:
    """
    Compare the twin's modified chart against the original.

    This computes the diff field-by-field, including planet positions,
    strengths, and aspects.
    """
    result = await service.compare_to_original(twin_id)
    if not result:
        raise HTTPException(status_code=404, detail="Twin not found")
    return result


@router.post(
    "/{twin_id}/simulate",
    response_model=list[TwinOperationResult],
    summary="Run simulation operations on a Digital Twin",
)
async def simulate_twin(
    twin_id: uuid.UUID,
    request: TwinSimulationRequest,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> list[TwinOperationResult]:
    """
    Run a sequence of simulation operations on the twin.

    Each operation is applied in order against the twin's current state
    (original chart + already-applied modifications); successful
    operations are persisted as new modifications so the twin's history
    stays consistent and replayable. Per-operation failures come back
    with success=False rather than aborting the whole batch.
    """
    from datetime import datetime, timezone

    results = await service.simulate_operations(twin_id, request.operations)
    if results is None:
        raise HTTPException(status_code=404, detail="Twin not found")

    applied_at = datetime.now(timezone.utc)
    return [
        TwinOperationResult(
            operation_type=r["operation_type"],
            applied_at=applied_at,
            success=r["success"],
            changes=r["changes"],
            error=r["error"],
        )
        for r in results
    ]


@router.delete(
    "/{twin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a Digital Twin",
)
async def archive_twin(
    twin_id: uuid.UUID,
    user: User = Depends(get_current_user_from_bearer),
    service: DigitalTwinService = Depends(_get_service),
) -> None:
    success = await service.delete_twin(twin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Twin not found")

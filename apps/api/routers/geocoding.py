"""
AstroOS — Geocoding Router (v2 Phase A Stabilization)

Endpoints
---------
GET /api/v1/geocode/search?query=...   — birth-place name search
GET /api/v1/geocode/timezone?...       — resolve IANA timezone + UTC
                                          offset + DST for a coordinate
                                          on a specific date

No business logic lives here — both endpoints delegate to
GeocodingService.
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
import httpx

from apps.api.dependencies import get_geocoding_service
from apps.api.schemas.geocoding import (
    PlaceResultResponse,
    PlaceSearchResponse,
    TimezoneResolutionResponse,
)
from apps.api.services.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/geocode", tags=["Geocoding"])


@router.get(
    "/search",
    response_model=PlaceSearchResponse,
    summary="Search for a birth place by name",
)
async def search_places(
    query: str = Query(..., min_length=2, description="e.g. 'Pune, Maharashtra'"),
    limit: int = Query(default=8, ge=1, le=20),
    service: GeocodingService = Depends(get_geocoding_service),
) -> PlaceSearchResponse:
    try:
        results = await service.search_places(query, limit=limit)
    except httpx.HTTPError as exc:
        logger.exception("Geocoding provider request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Place search is temporarily unavailable. Please try again.",
        )
    return PlaceSearchResponse(
        results=[
            PlaceResultResponse(
                display_name=r.display_name, latitude=r.latitude, longitude=r.longitude,
                country=r.country, state=r.state,
            )
            for r in results
        ]
    )


@router.get(
    "/timezone",
    response_model=TimezoneResolutionResponse,
    summary="Resolve IANA timezone, UTC offset, and DST state for a coordinate + date",
)
async def resolve_timezone(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    local_date: date = Query(..., description="Birth date in local time."),
    service: GeocodingService = Depends(get_geocoding_service),
) -> TimezoneResolutionResponse:
    try:
        resolution = service.resolve_timezone(latitude, longitude, local_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return TimezoneResolutionResponse(
        iana_name=resolution.iana_name,
        utc_offset_minutes=resolution.utc_offset_minutes,
        is_dst=resolution.is_dst,
    )

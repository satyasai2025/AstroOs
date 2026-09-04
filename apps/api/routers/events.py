"""
AstroOS — Events Router (Module 14, Phase 3)

HTTP adapter layer. Delegates all logic to EventRepository. No
business logic lives here — only request parsing, DTO<->schema
conversion, and HTTP error mapping, same convention as auth.py.

Does NOT touch EventEngine, domain/events.py, or dasha_lookup.py —
Phase 3 is persistence + API only, per explicit scope. This router
exposes CRUD for the EventRecord aggregate; it does not run
EventEngine.analyze()/analyze_batch() at all (that remains an
in-process service call for now — no "analyze" endpoint was in scope
for this phase).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from apps.api.dependencies import get_event_repo
from apps.api.domain.events import EventRecord
from apps.api.repositories.event_repository import EventRepository
from apps.api.schemas.events import (
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventUpdateRequest,
)

router = APIRouter(prefix="/events", tags=["Events"])


# ── DTO -> Schema converter (router's responsibility, not repository's) ──────


def _record_to_response(record: EventRecord) -> EventResponse:
    return EventResponse(
        id=record.id,
        chart_id=record.chart_id,
        user_id=record.user_id,
        event_date=record.event_date,
        title=record.title,
        description=record.description,
        category=record.category,
        is_verified=record.is_verified,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new life event.",
)
async def create_event(
    body: EventCreateRequest,
    repo: EventRepository = Depends(get_event_repo),
) -> EventResponse:
    try:
        record = await repo.create(
            chart_id=body.chart_id,
            event_date=body.event_date,
            title=body.title,
            user_id=body.user_id,
            description=body.description,
            category=body.category,
            is_verified=body.is_verified,
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid chart_id or user_id — referenced record does not exist.",
        ) from exc
    return _record_to_response(record)


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Retrieve one event by id.",
)
async def get_event(
    event_id: uuid.UUID,
    repo: EventRepository = Depends(get_event_repo),
) -> EventResponse:
    record = await repo.get_by_id(event_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return _record_to_response(record)


@router.get(
    "",
    response_model=EventListResponse,
    summary="List events for a chart.",
)
async def list_events(
    chart_id: uuid.UUID,
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    repo: EventRepository = Depends(get_event_repo),
) -> EventListResponse:
    records = await repo.list_for_chart(chart_id, category=category, limit=limit, offset=offset)
    return EventListResponse(events=[_record_to_response(r) for r in records], total=len(records))


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Partially update an event.",
)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdateRequest,
    repo: EventRepository = Depends(get_event_repo),
) -> EventResponse:
    # Only fields actually present in the request body are forwarded —
    # matches EventRepository.update()'s own _UNSET-vs-None distinction.
    provided_fields = body.model_dump(exclude_unset=True)
    record = await repo.update(event_id, **provided_fields)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return _record_to_response(record)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an event.",
)
async def delete_event(
    event_id: uuid.UUID,
    repo: EventRepository = Depends(get_event_repo),
) -> None:
    deleted = await repo.soft_delete(event_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

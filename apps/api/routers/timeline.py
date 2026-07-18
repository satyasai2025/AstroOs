"""
AstroOS — Timeline Router (Module 15 — HTTP surface)

Endpoints
---------
POST /api/v1/timeline/build — Build a chronological, Dasha-grouped,
cluster-annotated Timeline from the events already recorded for a chart.

Orchestrates (all in-process, no new engines invented):
  1. BirthChartRepository.get_or_create — resolve the same chart_id the
     events were recorded under (same dedup key as dasha/divisional).
  2. EventRepository.list_for_chart — fetch the events to timeline.
  3. HoroscopeEngine.generate_d1 + DashaEngine.compute_vimshottari +
     AshtakavargaEngine.compute_sarvashtakavarga — build a NatalSnapshot.
     yogas/shadbala_components/bhinnashtakavarga are left empty; nothing
     in TimelineEngine's aggregation logic reads those fields (only
     entry.analysis.context.active_dashas), same "don't compute what's
     never read" discipline as schemas/report.py.
  4. EventEngine().analyze_batch — build EventAnalysis per event (no
     TransitEngine/RuleEngine — those are optional and out of scope here).
  5. TimelineEngine.build_timeline / find_clusters.

No business logic beyond this orchestration lives here.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_ephemeris_wrapper
from apps.api.domain.events import NatalSnapshot
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.event_repository import EventRepository
from apps.api.schemas.timeline import (
    TemporalClusterResponse,
    TimelineBuildRequest,
    TimelineDashaPeriodSpanResponse,
    TimelineEntryResponse,
    TimelineResponse,
    TimelineSummaryResponse,
)
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.event_engine import EventEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.timeline_engine import TimelineEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["Timeline"])


def _serialise_entry(entry) -> TimelineEntryResponse:
    return TimelineEntryResponse(
        event_id=entry.event_id,
        event_date=entry.event_date,
        title=entry.title,
        category=entry.category,
        is_verified=entry.is_verified,
        active_dasha_systems=sorted(entry.analysis.context.active_dashas.keys()),
    )


def _serialise_span(span) -> TimelineDashaPeriodSpanResponse:
    return TimelineDashaPeriodSpanResponse(
        system=span.system,
        lord=span.lord,
        level=span.level,
        start_date=span.start_date,
        end_date=span.end_date,
        event_ids=list(span.event_ids),
        event_count=span.event_count,
    )


def _serialise_cluster(cluster) -> TemporalClusterResponse:
    return TemporalClusterResponse(
        start_date=cluster.start_date,
        end_date=cluster.end_date,
        center_date=cluster.center_date,
        event_ids=[e.event_id for e in cluster.events],
        event_count=cluster.event_count,
        density=cluster.density,
    )


@router.post(
    "/build",
    response_model=TimelineResponse,
    summary="Build a Timeline from a chart's recorded events",
    description=(
        "Fetches the events already recorded (via POST /events) for the "
        "chart identified by this birth data, then composes them into a "
        "chronological, Dasha-grouped, cluster-annotated Timeline."
    ),
)
async def build_timeline(
    body: TimelineBuildRequest,
    session: AsyncSession = Depends(get_db_session),
    wrapper: EphemerisWrapper = Depends(get_ephemeris_wrapper),
) -> TimelineResponse:
    birth_chart_repo = BirthChartRepository(session)
    event_repo = EventRepository(session)

    chart_id = await birth_chart_repo.get_or_create(
        birth_datetime_utc=body.birth_datetime_utc,
        latitude=body.latitude,
        longitude=body.longitude,
        ayanamsa=body.ayanamsa,
        house_system=body.house_system,
    )

    events = await event_repo.list_for_chart(
        chart_id, category=body.category, limit=body.limit, offset=body.offset
    )

    if not events:
        empty = TimelineEngine.build_timeline(())
        return TimelineResponse(
            chart_id=chart_id,
            entries=[],
            summary=TimelineSummaryResponse(
                total_events=0,
                date_range=empty.summary.date_range,
                events_per_category={},
                events_per_dasha_system={},
                verified_count=0,
                unverified_count=0,
            ),
            dasha_breakdown={},
            clusters=[],
            timeline_version=empty.timeline_version,
        )

    try:
        horoscope_engine = HoroscopeEngine(wrapper)
        dasha_engine = DashaEngine(wrapper)
        ashtakavarga_engine = AshtakavargaEngine()

        def _compute():
            d1_chart = horoscope_engine.generate_d1(
                birth_datetime_utc=body.birth_datetime_utc,
                latitude=body.latitude,
                longitude=body.longitude,
                ayanamsa=body.ayanamsa,
                house_system=body.house_system,
            )
            vimshottari_tree = dasha_engine.compute_vimshottari(
                birth_datetime_utc=body.birth_datetime_utc,
                latitude=body.latitude,
                longitude=body.longitude,
                ayanamsa=body.ayanamsa,
                house_system=body.house_system,
            )
            sarvashtakavarga = ashtakavarga_engine.compute_sarvashtakavarga(d1_chart)
            return d1_chart, vimshottari_tree, sarvashtakavarga

        # Blocking pyswisseph calls — offload to a worker thread so they
        # do not freeze the event loop. See horoscope.py's generate_d1_chart
        # for the full rationale.
        d1_chart, vimshottari_tree, sarvashtakavarga = await asyncio.to_thread(_compute)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Error computing natal data for timeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute natal chart data for timeline.",
        )

    natal_snapshot = NatalSnapshot(
        chart_id=chart_id,
        chart=d1_chart,
        yogas=(),
        shadbala_components={},
        bhinnashtakavarga=(),
        sarvashtakavarga=sarvashtakavarga,
    )

    try:
        batch_result = EventEngine().analyze_batch(
            list(events),
            dasha_trees={"vimshottari": vimshottari_tree},
            natal_snapshot=natal_snapshot,
        )
        timeline = TimelineEngine.build_timeline(tuple(batch_result.analyses))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    clusters = TimelineEngine.find_clusters(
        timeline, window_days=body.window_days, min_events=body.min_events
    )

    return TimelineResponse(
        chart_id=timeline.chart_id,
        entries=[_serialise_entry(e) for e in timeline.entries],
        summary=TimelineSummaryResponse(
            total_events=timeline.summary.total_events,
            date_range=timeline.summary.date_range,
            events_per_category=timeline.summary.events_per_category,
            events_per_dasha_system=timeline.summary.events_per_dasha_system,
            verified_count=timeline.summary.verified_count,
            unverified_count=timeline.summary.unverified_count,
        ),
        dasha_breakdown={
            system: [_serialise_span(s) for s in spans]
            for system, spans in timeline.dasha_breakdown.items()
        },
        clusters=[_serialise_cluster(c) for c in clusters],
        timeline_version=timeline.timeline_version,
    )

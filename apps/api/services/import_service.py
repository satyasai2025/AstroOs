"""
AstroOS — Research Case Import Service (Module 27, Phase 2)

Validates, snapshot-computes, and persists research cases for the
event-centric research pipeline. Operates on domain objects only
(apps/api/domain/research_case.py) — schemas never leak in here, same
DTO-boundary discipline as every other service. The router converts
schemas -> domain objects and runs schema-level validation
(apps/api/services/research_validation.py).

Snapshot computation is delegated to SnapshotComputer, a thin wrapper
over the existing chart/dasha/transit/yoga engines. Import never
re-implements an astrology calculation. The structural "compute once per
case, reuse per event" rule from EventEngine applies here too: the D1
chart, dasha tree, and natal yogas are computed once per case; then the
active dasha chain and transit positions are resolved per event date via
find_active_dasha_chain / TransitEngine.

Best-effort with explicit gaps: a per-event snapshot failure produces a
minimal snapshot (no silent data loss); a case-level chart failure is
recorded as an error on that case's result and the rest of the batch
still imports.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import date, datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.research_case import (
    CaseImportResult,
    DashaSnapshot,
    EventSnapshot,
    LifeEvent,
    PersonInfo,
    ResearchCase,
    SnapshotRebuildResult,
)
from apps.api.models.research_case import (
    AttachmentModel,
    EventSnapshotModel,
    LifeEventModel,
    ResearchCaseModel,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.house_engine import HouseEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.yoga_engine import YogaEngine

logger = logging.getLogger(__name__)

_NOON = time(12, 0)

# Bumped by hand whenever DashaEngine/TransitEngine/YogaEngine's output
# changes materially. New imports and Advanced Research > Snapshot Rebuild
# both stamp snapshots with this — per EventSnapshotModel's "append, never
# overwrite" contract, bumping it and rebuilding produces new snapshot rows
# alongside the old ones, never mutates history.
CURRENT_SNAPSHOT_VERSION = "1.1"


def _to_utc(d: date, t: Optional[str], tz_name: str) -> datetime:
    """Combine calendar date + HH:MM (or noon) in the IANA timezone -> UTC datetime."""
    hm = time.fromisoformat(t) if t else _NOON
    local = datetime.combine(d, hm).replace(tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc)


class SnapshotComputer:
    """
    Computes EventSnapshots for one research case.

    Natal work (D1 chart, dasha tree, natal yogas) is date-invariant and
    computed once per case; dasha chain + transit are date-dependent and
    resolved per event date.
    """

    def __init__(self, wrapper, dasha_system: str = "vimshottari") -> None:
        self._wrapper = wrapper
        self._dasha_system = dasha_system
        self._horoscope_engine = HoroscopeEngine(wrapper)
        self._dasha_engine = DashaEngine(wrapper)
        self._transit_engine = TransitEngine(wrapper)
        self._yoga_engine = YogaEngine()
        self._house_engine = HouseEngine()

    def compute_case(self, case: ResearchCase) -> list[tuple[LifeEvent, list[EventSnapshot]]]:
        """
        Return (event, snapshots) pairs for one case.

        Raises RuntimeError if the natal chart itself cannot be computed
        (a case-level failure — the caller records it on the case result).
        Per-event failures degrade to a minimal snapshot, never raise.
        """
        birth_utc = _to_utc(case.person.dob, case.person.tob, case.person.timezone)
        chart = self._horoscope_engine.generate_d1(
            birth_datetime_utc=birth_utc,
            latitude=case.person.latitude,
            longitude=case.person.longitude,
            ayanamsa=case.ayanamsa,
            house_system=case.house_system,
        )
        dasha_compute_fn = getattr(self._dasha_engine, f"compute_{self._dasha_system}")
        dasha_tree = dasha_compute_fn(
            birth_datetime_utc=birth_utc,
            latitude=case.person.latitude,
            longitude=case.person.longitude,
            ayanamsa=case.ayanamsa,
            house_system=case.house_system,
        )
        yoga_results = self._yoga_engine.evaluate_all(chart)
        active_yogas = [y.name for y in yoga_results if y.is_present]

        # House-lord dignity and natal nakshatra placements are, like
        # active_yogas above, date-invariant (derived from the D1 chart
        # alone) — computed once per case and reused for every event.
        house_summary = self._house_engine.build_house_summary(chart.houses, chart.planets)
        planets_by_name = {p.planet: p for p in chart.planets}
        house_lord_statuses: dict[str, str] = {}
        for house in house_summary:
            lord_position = planets_by_name.get(house.lord)
            dignity = lord_position.dignity if lord_position else None
            house_lord_statuses[str(house.house_number)] = dignity.value if dignity else "neutral"
        nakshatra_activations = [f"{p.planet}_{p.nakshatra}" for p in chart.planets]

        per_event: list[tuple[LifeEvent, list[EventSnapshot]]] = []
        for event in case.life_events:
            try:
                event_utc = _to_utc(event.event_date, event.event_time, case.person.timezone)
                chain = find_active_dasha_chain(dasha_tree, event.event_date)
                dasha: Optional[DashaSnapshot] = None
                if chain:
                    dasha = DashaSnapshot(
                        mahadasha=chain[0].lord,
                        antardasha=chain[1].lord if len(chain) > 1 else "",
                        pratyantar=chain[2].lord if len(chain) > 2 else None,
                    )
                transit_results = self._transit_engine.compute_transit(chart, event_utc)
                transit_features = {
                    f"{r.planet}_{r.transit_rashi}": True for r in transit_results
                }
                snapshot = EventSnapshot(
                    snapshot_date=event.event_date,
                    snapshot_version=CURRENT_SNAPSHOT_VERSION,
                    current_dasha=dasha,
                    transits=transit_features,
                    active_yogas=list(active_yogas),
                    nakshatra_activations=list(nakshatra_activations),
                    house_lord_statuses=dict(house_lord_statuses),
                )
            except Exception as exc:  # noqa: BLE001 — per-event best effort
                logger.warning(
                    "Snapshot computation failed for event %s: %s", event.id, exc
                )
                snapshot = EventSnapshot(snapshot_date=event.event_date)
            per_event.append((event, [snapshot]))
        return per_event


class ResearchCaseImportService:
    """Persists validated research cases (domain objects) with computed snapshots."""

    def __init__(self, session: AsyncSession, computer: SnapshotComputer) -> None:
        self._session = session
        self._computer = computer
        self._seq = 1

    async def import_cases(
        self,
        cases: list[ResearchCase],
        *,
        user_id: Optional[uuid.UUID] = None,
    ) -> list[CaseImportResult]:
        """Import all cases; each case gets its own result (errors never abort the batch)."""
        results: list[CaseImportResult] = []
        for case in cases:
            results.append(await self._import_one(case, user_id=user_id))
        await self._session.commit()
        return results

    async def _import_one(
        self,
        case: ResearchCase,
        *,
        user_id: Optional[uuid.UUID],
    ) -> CaseImportResult:
        # ── Cross-batch duplicate: research_case_id already in DB ─────────
        if case.id:
            existing = await self._session.execute(
                select(ResearchCaseModel.id).where(
                    ResearchCaseModel.research_case_id == case.id
                )
            )
            if existing.scalar_one_or_none() is not None:
                return CaseImportResult(
                    research_case_id=case.id,
                    person_name=case.person.name,
                    dob=case.person.dob,
                    total_events=len(case.life_events),
                    total_snapshots_created=0,
                    duplicate=True,
                    errors=["research_case_id already exists in the database"],
                )

        # Compute snapshots BEFORE adding anything to the session — compute
        # is pure (no DB), so a case-level failure contributes nothing and
        # never rolls back earlier successful cases in the same batch.
        try:
            # Natal compute is blocking pyswisseph work — run it in a thread.
            per_event = await asyncio.to_thread(self._computer.compute_case, case)
        except Exception as exc:  # noqa: BLE001 — case-level failure
            logger.warning("Case %s failed snapshot computation: %s", case.id, exc)
            return CaseImportResult(
                research_case_id=case.id or "",
                person_name=case.person.name,
                dob=case.person.dob,
                total_events=len(case.life_events),
                total_snapshots_created=0,
                errors=[f"snapshot computation failed: {exc}"],
            )

        case_model = ResearchCaseModel(
            research_case_id=case.id or self._generate_id(case.person.dob),
            user_id=user_id,
            person_name=case.person.name,
            gender=case.person.gender,
            dob=datetime.combine(case.person.dob, _NOON),
            tob=case.person.tob,
            place_of_birth=case.person.place,
            country=case.person.country,
            latitude=case.person.latitude,
            longitude=case.person.longitude,
            timezone=case.person.timezone,
            data_source=case.person.source,
            birth_time_confidence=case.person.birth_time_confidence,
            ayanamsa=case.ayanamsa,
            house_system=case.house_system,
            divisional_charts=json.dumps(case.divisional_charts),
            rectified=case.rectified,
            rectification_notes=case.rectification_notes,
            research_notes=case.research_notes,
            source_batch=case.source_batch,
            validation_status="passed",
        )
        self._session.add(case_model)

        # flush so case_model.id is populated (client-side uuid.uuid4 default)
        await self._session.flush()

        total_snapshots = 0
        for event, snapshots in per_event:
            event_model = LifeEventModel(
                research_case_id=case_model.id,
                external_event_id=event.id,
                event_type=event.type,
                severity=event.severity,
                category=event.category,
                verified=event.verified,
                confidence=event.confidence,
                source=event.source,
                event_date=datetime.combine(event.event_date, _NOON),
                event_time=event.event_time,
                event_place=event.event_place,
                event_window_days=event.event_window_days,
                description=event.description,
                notes=event.notes,
                tags=json.dumps(event.tags),
            )
            self._session.add(event_model)
            await self._session.flush()  # populate event_model.id

            for snap in snapshots:
                self._session.add(
                    EventSnapshotModel(
                        life_event_id=event_model.id,
                        snapshot_date=datetime.combine(snap.snapshot_date, _NOON),
                        snapshot_version=snap.snapshot_version,
                        mahadasha=snap.current_dasha.mahadasha if snap.current_dasha else None,
                        antardasha=snap.current_dasha.antardasha if snap.current_dasha else None,
                        pratyantar=snap.current_dasha.pratyantar if snap.current_dasha else None,
                        transit_features=json.dumps(snap.transits),
                        shadbala_values=json.dumps(snap.shadbala),
                        active_yogas=json.dumps(snap.active_yogas),
                        varga_activations=json.dumps(snap.varga_activations),
                        nakshatra_activations=json.dumps(snap.nakshatra_activations),
                        house_lord_statuses=json.dumps(snap.house_lord_statuses),
                    )
                )
                total_snapshots += 1

            for att in event.attachments:
                self._session.add(
                    AttachmentModel(
                        life_event_id=event_model.id,
                        attachment_type=att.type,
                        filename=att.filename,
                        url=att.url,
                        content_type=att.content_type,
                    )
                )

        for att in case.attachments:
            self._session.add(
                AttachmentModel(
                    research_case_id=case_model.id,
                    attachment_type=att.type,
                    filename=att.filename,
                    url=att.url,
                    content_type=att.content_type,
                )
            )

        return CaseImportResult(
            research_case_id=case_model.research_case_id,
            person_name=case.person.name,
            dob=case.person.dob,
            total_events=len(case.life_events),
            total_snapshots_created=total_snapshots,
            duplicate=False,
            errors=[],
        )

    def _generate_id(self, dob: date) -> str:
        seq = self._seq
        self._seq += 1
        return f"RC-{dob.year}-{seq:03d}"

    async def rebuild_all_snapshots(
        self, *, user_id: Optional[uuid.UUID] = None
    ) -> SnapshotRebuildResult:
        """Advanced Research tool: recompute snapshots for every already-
        imported, non-deleted case under CURRENT_SNAPSHOT_VERSION.

        ``user_id``, when given, restricts the rebuild to cases owned by
        that user — this is a write operation touching case data, so per
        the "owner-only write" policy it must not silently recompute (and
        thus create new snapshot rows for) cases belonging to other users.
        The router always passes the caller's own user_id.

        Per EventSnapshotModel's "append, never overwrite" contract, this
        ADDS new snapshot rows rather than mutating existing ones — prior
        snapshot versions remain in place for audit. Run this after an
        astrology engine fix, then Advanced Research > Evidence
        Recalculation to refresh existing patterns against the new data.
        """
        query = select(ResearchCaseModel).where(ResearchCaseModel.deleted_at.is_(None))
        if user_id is not None:
            query = query.where(ResearchCaseModel.user_id == user_id)
        case_models = (await self._session.execute(query)).scalars().all()

        cases_processed = 0
        snapshots_created = 0
        errors: list[str] = []
        for case_model in case_models:
            domain_case = _case_model_to_domain(case_model)
            try:
                per_event = await asyncio.to_thread(self._computer.compute_case, domain_case)
            except Exception as exc:  # noqa: BLE001 — case-level failure, rebuild continues
                errors.append(f"{case_model.research_case_id}: {exc}")
                continue

            for (_event, snapshots), event_model in zip(per_event, case_model.life_events):
                for snap in snapshots:
                    self._session.add(
                        EventSnapshotModel(
                            life_event_id=event_model.id,
                            snapshot_date=datetime.combine(snap.snapshot_date, _NOON),
                            snapshot_version=snap.snapshot_version,
                            mahadasha=snap.current_dasha.mahadasha if snap.current_dasha else None,
                            antardasha=snap.current_dasha.antardasha if snap.current_dasha else None,
                            pratyantar=snap.current_dasha.pratyantar if snap.current_dasha else None,
                            transit_features=json.dumps(snap.transits),
                            shadbala_values=json.dumps(snap.shadbala),
                            active_yogas=json.dumps(snap.active_yogas),
                            varga_activations=json.dumps(snap.varga_activations),
                            nakshatra_activations=json.dumps(snap.nakshatra_activations),
                            house_lord_statuses=json.dumps(snap.house_lord_statuses),
                        )
                    )
                    snapshots_created += 1
            cases_processed += 1

        await self._session.commit()
        return SnapshotRebuildResult(
            cases_processed=cases_processed,
            snapshots_created=snapshots_created,
            snapshot_version=CURRENT_SNAPSHOT_VERSION,
            errors=errors,
        )


def _case_model_to_domain(case_model: ResearchCaseModel) -> ResearchCase:
    """Reverse-map a persisted ResearchCaseModel (+ eagerly-loaded
    life_events) back into the domain ResearchCase so SnapshotComputer,
    which only knows domain objects, can recompute it unmodified.
    """
    dob = case_model.dob.date() if isinstance(case_model.dob, datetime) else case_model.dob
    person = PersonInfo(
        name=case_model.person_name,
        gender=case_model.gender,
        dob=dob,
        tob=case_model.tob,
        place=case_model.place_of_birth,
        latitude=case_model.latitude,
        longitude=case_model.longitude,
        timezone=case_model.timezone,
        source=case_model.data_source,
        birth_time_confidence=case_model.birth_time_confidence,
        country=case_model.country,
    )
    life_events = [
        LifeEvent(
            id=event.external_event_id,
            type=event.event_type,
            event_date=event.event_date.date() if isinstance(event.event_date, datetime) else event.event_date,
            event_time=event.event_time,
            event_place=event.event_place,
            severity=event.severity,
            category=event.category,
            verified=event.verified,
            confidence=event.confidence,
            source=event.source,
            description=event.description,
            tags=json.loads(event.tags) if event.tags else [],
            event_window_days=event.event_window_days,
            notes=event.notes,
        )
        for event in case_model.life_events
    ]
    return ResearchCase(
        id=case_model.research_case_id,
        person=person,
        ayanamsa=case_model.ayanamsa,
        house_system=case_model.house_system,
        divisional_charts=json.loads(case_model.divisional_charts) if case_model.divisional_charts else [],
        rectified=case_model.rectified,
        rectification_notes=case_model.rectification_notes,
        life_events=life_events,
        research_notes=case_model.research_notes,
        source_batch=case_model.source_batch,
    )

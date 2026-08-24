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
from apps.api.services.aspect_engine import AspectEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.badhaka_maraka_engine import BadhakaMarakaEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.dasha_lookup import find_active_dasha_chain
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.event_category_service import EventCategoryService
from apps.api.services.event_type_service import EventTypeService
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.functional_lordship_engine import FunctionalLordshipEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.house_engine import HouseEngine
from apps.api.services.nakshatra_vedha_calculator import NakshatraVedhaCalculator
from apps.api.services.research_validation import hash_case
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.vedha_calculator import VedhaCalculator
from apps.api.services.yoga_engine import YogaEngine

logger = logging.getLogger(__name__)

_NOON = time(12, 0)

# Bumped by hand whenever DashaEngine/TransitEngine/YogaEngine's output
# changes materially. New imports and Advanced Research > Snapshot Rebuild
# both stamp snapshots with this — per EventSnapshotModel's "append, never
# overwrite" contract, bumping it and rebuilding produces new snapshot rows
# alongside the old ones, never mutates history.
CURRENT_SNAPSHOT_VERSION = "1.2"


async def load_existing_case_hashes(session: AsyncSession) -> set[str]:
    """Hashes (person_name|dob|lat|lng, see research_validation.hash_case)
    for every already-persisted, non-deleted case — seed this into
    validate_research_case_batch's existing_hashes so duplicate detection
    catches a batch re-imported in a LATER request, not just repeats
    within one batch. Without this, re-posting the same JSON twice (e.g.
    a client retry after a partial failure) silently creates duplicate
    research cases with fresh auto-generated ids."""
    result = await session.execute(
        select(
            ResearchCaseModel.person_name,
            ResearchCaseModel.dob,
            ResearchCaseModel.latitude,
            ResearchCaseModel.longitude,
        ).where(ResearchCaseModel.deleted_at.is_(None))
    )
    return {
        hash_case(name or "anonymous", dob.date(), lat, lng)
        for name, dob, lat, lng in result
    }


def _to_utc(d: date, t: Optional[str], tz_name: str) -> datetime:
    """Combine calendar date + HH:MM (or noon) in the IANA timezone -> UTC datetime."""
    hm = time.fromisoformat(t) if t else _NOON
    local = datetime.combine(d, hm).replace(tzinfo=ZoneInfo(tz_name))
    return local.astimezone(timezone.utc)


class SnapshotComputer:
    """
    Computes EventSnapshots for one research case using FactBuilder as the
    single canonical engine boundary.

    Natal work (D1 chart, dasha tree, divisional charts) is date-invariant and
    computed once per case; dasha chain + transit are date-dependent and
    resolved per event date via FactBuilder.
    """

    def __init__(self, wrapper, dasha_system: str = "vimshottari") -> None:
        self._wrapper = wrapper
        self._dasha_system = dasha_system
        self._horoscope_engine = HoroscopeEngine(wrapper)
        self._dasha_engine = DashaEngine(wrapper)
        self._transit_engine = TransitEngine(wrapper)
        self._yoga_engine = YogaEngine()
        self._house_engine = HouseEngine()
        self._divisional_engine = DivisionalEngine(wrapper)
        self._shadbala_engine = ShadbalaEngine(
            divisional_engine=self._divisional_engine,
            ephemeris_wrapper=wrapper,
        )
        self._ashtakavarga_engine = AshtakavargaEngine()
        self._badhaka_maraka_engine = BadhakaMarakaEngine()
        self._aspect_engine = AspectEngine()
        self._functional_lordship_engine = FunctionalLordshipEngine()
        self._vedha_calculator = VedhaCalculator()
        self._nakshatra_vedha_calculator = NakshatraVedhaCalculator()

        self._fact_builder = FactBuilder(
            graha_engine=None,
            house_engine=self._house_engine,
            yoga_engine=self._yoga_engine,
            shadbala_engine=self._shadbala_engine,
            ashtakavarga_engine=self._ashtakavarga_engine,
            transit_engine=self._transit_engine,
            badhaka_maraka_engine=self._badhaka_maraka_engine,
            aspect_engine=self._aspect_engine,
            functional_lordship_engine=self._functional_lordship_engine,
            vedha_calculator=self._vedha_calculator,
            nakshatra_vedha_calculator=self._nakshatra_vedha_calculator,
        )

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

        # Compute divisional charts
        vargas = {}
        varga_codes = case.divisional_charts if case.divisional_charts else ["D9", "D10"]
        for code in varga_codes:
            try:
                vargas[code] = self._divisional_engine.compute(
                    birth_datetime_utc=birth_utc,
                    latitude=case.person.latitude,
                    longitude=case.person.longitude,
                    varga=code,
                    ayanamsa=case.ayanamsa,
                    house_system=case.house_system,
                )
            except Exception as exc:
                logger.warning("Failed to compute varga %s for case %s: %s", code, case.id, exc)

        per_event: list[tuple[LifeEvent, list[EventSnapshot]]] = []
        for event in case.life_events:
            try:
                event_utc = _to_utc(event.event_date, event.event_time, case.person.timezone)
                registry = self._fact_builder.build_facts(
                    chart=chart,
                    transit_datetime_utc=event_utc,
                    dasha_tree=dasha_tree,
                    vargas=vargas,
                )
                facts_list = registry.all_facts()

                # Derive backward-compatible views from registry/facts
                md = registry.get_value("dasha.current_lord")
                ad = registry.get_value("dasha.antardasha_lord", "")
                dasha: Optional[DashaSnapshot] = DashaSnapshot(mahadasha=md, antardasha=ad) if md else None

                transits = {
                    f"{p.planet}_{registry.get_value(f'transit.{p.planet}.rashi')}": True
                    for p in chart.planets
                    if registry.has_fact(f"transit.{p.planet}.rashi")
                }
                shadbala = {
                    p: registry.get_value(f"shadbala.{p}.total", 0.0)
                    for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
                    if registry.has_fact(f"shadbala.{p}.total")
                }
                active_yogas = [
                    f.key.split(".")[1]
                    for f in facts_list
                    if f.key.startswith("yoga.") and f.key.endswith(".present") and f.value is True
                ]
                varga_activations = {
                    f"{f.key.split('.')[2]}_{f.key.split('.')[1]}": str(f.value)
                    for f in facts_list
                    if f.key.startswith("varga.") and f.key.endswith(".rashi")
                }
                nakshatra_activations = [f"{p.planet}_{p.nakshatra}" for p in chart.planets]
                house_lord_statuses = {
                    str(i): (
                        next((p.dignity.value for p in chart.planets if p.planet == registry.get_value(f"house.{i}.lord")), "neutral")
                        if registry.has_fact(f"house.{i}.lord")
                        else "neutral"
                    )
                    for i in range(1, 13)
                }

                snapshot = EventSnapshot(
                    snapshot_date=event.event_date,
                    snapshot_version=CURRENT_SNAPSHOT_VERSION,
                    current_dasha=dasha,
                    transits=transits,
                    shadbala=shadbala,
                    active_yogas=active_yogas,
                    varga_activations=varga_activations,
                    nakshatra_activations=nakshatra_activations,
                    house_lord_statuses=house_lord_statuses,
                    facts=facts_list,
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
        # Per-year next-sequence cache for _generate_id, lazily seeded from
        # the DB's actual max existing seq for that year (see _generate_id)
        # — NOT a fixed 1-per-request counter, which previously produced
        # the exact same "RC-<year>-001" id on every fresh import request
        # and crashed the whole batch with an unhandled IntegrityError the
        # moment two separate import requests shared a birth year.
        self._year_seq_cache: dict[int, int] = {}
        self._categories = EventCategoryService(session)
        self._event_types = EventTypeService(session)

    async def import_cases(
        self,
        cases: list[ResearchCase],
        *,
        user_id: Optional[uuid.UUID] = None,
        update_existing: bool = False,
    ) -> list[CaseImportResult]:
        """Import all cases; each case gets its own result (errors never abort the batch).

        update_existing=True changes duplicate handling: instead of
        rejecting a case that matches an already-persisted one (by
        person_name + dob + tob), that existing research_cases row is
        reused and the new life_events are appended to it — this backs
        the bulk-import wizard's "Update existing cases" option. Without
        it, a matching case is always reported as a duplicate and skipped,
        same as before.
        """
        results: list[CaseImportResult] = []
        for case in cases:
            results.append(
                await self._import_one(case, user_id=user_id, update_existing=update_existing)
            )
        await self._session.commit()
        return results

    async def _import_one(
        self,
        case: ResearchCase,
        *,
        user_id: Optional[uuid.UUID],
        update_existing: bool = False,
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

        # ── Content match (person_name + dob + tob): reuse or reject ──────
        existing_case_model: Optional[ResearchCaseModel] = None
        content_match = await self._session.execute(
            select(ResearchCaseModel).where(
                ResearchCaseModel.person_name == case.person.name,
                ResearchCaseModel.dob == datetime.combine(case.person.dob, _NOON),
                ResearchCaseModel.tob == case.person.tob,
                ResearchCaseModel.deleted_at.is_(None),
            )
        )
        matched = content_match.scalars().first()
        if matched is not None:
            if not update_existing:
                return CaseImportResult(
                    research_case_id=matched.research_case_id,
                    person_name=case.person.name,
                    dob=case.person.dob,
                    total_events=len(case.life_events),
                    total_snapshots_created=0,
                    duplicate=True,
                    errors=["matching case (name + dob + tob) already exists"],
                )
            existing_case_model = matched

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

        research_case_id = (
            case.id
            or (existing_case_model.research_case_id if existing_case_model else None)
            or await self._generate_id(case.person.dob)
        )

        # Everything below is wrapped in a SAVEPOINT: any DB-level failure
        # here (e.g. a research_case_id collision under concurrent import
        # requests, or any other constraint violation) rolls back only this
        # case's writes and is reported as an error result — it must never
        # poison the outer transaction and abort the rest of the batch,
        # which is exactly what import_cases's docstring promises.
        try:
            async with self._session.begin_nested():
                if existing_case_model is not None:
                    # update_existing=True path: reuse the matched row,
                    # refresh its fields, append new life_events to it
                    # below rather than inserting a second research_cases
                    # row for the same person.
                    case_model = existing_case_model
                    case_model.gender = case.person.gender
                    case_model.place_of_birth = case.person.place
                    case_model.country = case.person.country
                    case_model.latitude = case.person.latitude
                    case_model.longitude = case.person.longitude
                    case_model.timezone = case.person.timezone
                    case_model.data_source = case.person.source
                    case_model.birth_time_confidence = case.person.birth_time_confidence
                    case_model.ayanamsa = case.ayanamsa
                    case_model.house_system = case.house_system
                    case_model.divisional_charts = json.dumps(case.divisional_charts)
                    case_model.source_batch = case.source_batch
                else:
                    case_model = ResearchCaseModel(
                        research_case_id=research_case_id,
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
                    category_value = event.category
                    category_id = None
                    if event.category_path:
                        category_node = await self._categories.resolve_or_create_category_path(
                            event.category_path,
                        )
                        category_id = category_node.id
                        # life_events.category is String(100) (legacy backward-compat
                        # mirror only) — the full path lives untruncated on the
                        # category_id-linked event_categories.path column.
                        category_value = category_node.path[:100]

                    event_type_value = event.type
                    event_type_id = None
                    event_type_label = "Other"
                    if event.event_type_path:
                        event_type_node = await self._event_types.resolve_or_create_event_type_path(
                            event.event_type_path,
                        )
                        event_type_id = event_type_node.id
                        # life_events.event_type_label is String(100) (mirrors
                        # `category`'s legacy-compat pattern) — the full path
                        # lives untruncated on event_type_id's event_types.path.
                        event_type_label = event_type_node.path[:100]
                        # Legacy closed enum column can't hold an open-tree
                        # value — mirrors how category-tag events already
                        # default type="other" there (explicit, documented gap).
                        event_type_value = "other"
                    elif event.type and event.type != "other":
                        event_type_label = event.type.replace("_", " ").title()

                    event_model = LifeEventModel(
                        research_case_id=case_model.id,
                        external_event_id=event.id,
                        event_type=event_type_value,
                        event_type_id=event_type_id,
                        event_type_label=event_type_label,
                        severity=event.severity,
                        category=category_value,
                        category_id=category_id,
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
                                facts_json=json.dumps([{"key": f.key, "value": f.value, "source": f.source} for f in snap.facts]) if snap.facts else None,
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
        except Exception as exc:  # noqa: BLE001 — case-level failure, see comment above
            logger.warning("Case %s failed to persist: %s", research_case_id, exc)
            return CaseImportResult(
                research_case_id=research_case_id,
                person_name=case.person.name,
                dob=case.person.dob,
                total_events=len(case.life_events),
                total_snapshots_created=0,
                errors=[f"persist failed: {exc}"],
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

    async def _generate_id(self, dob: date) -> str:
        year = dob.year
        if year not in self._year_seq_cache:
            existing = await self._session.execute(
                select(ResearchCaseModel.research_case_id).where(
                    ResearchCaseModel.research_case_id.like(f"RC-{year}-%")
                )
            )
            max_seq = 0
            for (rid,) in existing:
                suffix = rid.rsplit("-", 1)[-1]
                if suffix.isdigit():
                    max_seq = max(max_seq, int(suffix))
            self._year_seq_cache[year] = max_seq
        self._year_seq_cache[year] += 1
        return f"RC-{year}-{self._year_seq_cache[year]:03d}"

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
                            facts_json=json.dumps([{"key": f.key, "value": f.value, "source": f.source} for f in snap.facts]) if snap.facts else None,
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

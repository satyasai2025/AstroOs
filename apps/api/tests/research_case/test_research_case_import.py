"""
Tests for the Research Case import pipeline (Module 27):
apps/api/services/import_service.py + schema->domain conversion.

Self-contained — deliberately does NOT depend on the shared tests/conftest.py
(which is missing from the tree and currently breaks collection of the
existing unit/integration suites).

Three tiers, escalating dependencies:
  1. Pure: schema->domain to_domain() mapping + _to_utc() helper.
  2. Ephemeris: SnapshotComputer.compute_case() — skipped if the Swiss
     Ephemeris .se1 files are absent.
  3. Integration: full persist + read-back against a live database — skipped
     unless DATABASE_URL is set AND reachable. Excluded from a default run
     with `-m "not integration"`.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.domain.research_case import LifeEvent, PersonInfo, ResearchCase
from apps.api.models.research_case import (
    LifeEventModel,
    ResearchCaseModel,
)
from apps.api.schemas.research_case import (
    EventType,
    Gender,
    LifeEventCreateSchema,
    PersonInfoSchema,
    ResearchCaseCreateSchema,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.import_service import (
    ResearchCaseImportService,
    SnapshotComputer,
    _to_utc,
)

# Resolve the ephemeris dir from the repo root, not the process CWD (pytest
# may be invoked from anywhere).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_EPHE_DIR = str(_REPO_ROOT / "data" / "ephemeris")
_HAS_EPHE = all(
    os.path.exists(os.path.join(_EPHE_DIR, f))
    for f in ("sepl_18.se1", "seas_18.se1", "semo_18.se1")
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def make_schema_case(**overrides) -> ResearchCaseCreateSchema:
    defaults = dict(
        id="RC-1990-001",
        person=PersonInfoSchema(
            name="Test", gender=Gender.MALE, dob=date(1990, 6, 15), tob="10:30",
            place="Delhi", latitude=28.6139, longitude=77.209,
            timezone="Asia/Kolkata", source="Interview",
        ),
        life_events=[LifeEventCreateSchema(type=EventType.MARRIAGE, event_date=date(2012, 2, 14))],
    )
    defaults.update(overrides)
    return ResearchCaseCreateSchema(**defaults)


def make_domain_case(**overrides) -> ResearchCase:
    defaults = dict(
        id="RC-1990-001",
        person=PersonInfo(
            name="Test", gender="male", dob=date(1990, 6, 15), tob="10:30",
            place="Delhi", latitude=28.6139, longitude=77.209,
            timezone="Asia/Kolkata", source="Interview",
        ),
        ayanamsa="lahiri", house_system="P", divisional_charts=["D1"],
        rectified=False, rectification_notes=None,
        life_events=[
            LifeEvent(id="E1", type="marriage", event_date=date(2012, 2, 14)),
            LifeEvent(id="E2", type="promotion", event_date=date(2018, 5, 1)),
        ],
    )
    defaults.update(overrides)
    return ResearchCase(**defaults)


# ── Tier 1: pure conversion helpers ─────────────────────────────────────────


class TestToDomainConversion:
    def test_event_type_maps_to_backend_value(self):
        case = make_schema_case(
            life_events=[LifeEventCreateSchema(type=EventType.JOB_CHANGE, event_date=date(2018, 5, 1))]
        )
        domain = case.to_domain()
        assert domain.life_events[0].type == "job_change"

    def test_multi_word_event_type_maps_correctly(self):
        case = make_schema_case(
            life_events=[LifeEventCreateSchema(type=EventType.DEATH_PARENT, event_date=date(2020, 1, 1))]
        )
        assert case.to_domain().life_events[0].type == "death_parent"

    def test_gender_and_severity_lowercased(self):
        domain = make_schema_case().to_domain()
        assert domain.person.gender == "male"
        assert domain.life_events[0].severity == "moderate"
        assert domain.life_events[0].confidence == "medium"

    def test_default_divisional_charts_present(self):
        domain = make_schema_case().to_domain()
        assert "D1" in domain.divisional_charts and "D9" in domain.divisional_charts


class TestToUtcHelper:
    def test_combines_date_tob_and_timezone(self):
        dt = _to_utc(date(1986, 6, 15), "10:30", "Asia/Kolkata")
        assert dt.tzinfo is not None
        assert dt.utcoffset() is not None  # timezone-aware, not naive

    def test_missing_tob_defaults_to_noon(self):
        dt = _to_utc(date(1986, 6, 15), None, "Asia/Kolkata")
        assert dt.tzinfo is not None
        assert dt.hour in (6, 7)  # 12:00 IST ≈ 06:30 UTC (no DST in IST)

    def test_invalid_timezone_raises(self):
        with pytest.raises(Exception):
            _to_utc(date(2020, 1, 1), None, "Not/AZone")


# ── Tier 2: SnapshotComputer (requires Swiss Ephemeris) ─────────────────────


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_DIR)


@pytest.mark.skipif(not _HAS_EPHE, reason="Swiss Ephemeris .se1 files not present")
class TestSnapshotComputer:
    def test_snapshot_has_dasha_yogas_transits(self, wrapper):
        per_event = SnapshotComputer(wrapper).compute_case(make_domain_case())
        _event, snapshots = per_event[0]
        assert len(snapshots) == 1
        snap = snapshots[0]
        assert snap.current_dasha is not None
        assert snap.current_dasha.mahadasha
        assert snap.current_dasha.antardasha
        assert snap.active_yogas, "expected at least one active yoga"
        assert snap.transits, "expected transit features"

    def test_dasha_changes_across_event_dates(self, wrapper):
        per_event = SnapshotComputer(wrapper).compute_case(make_domain_case())
        dasha_a = per_event[0][1][0].current_dasha
        dasha_b = per_event[1][1][0].current_dasha
        # Two events ~6 years apart in different antardashas: the chain must
        # differ at some level — the date-dependence the whole design guarantees.
        assert (dasha_a.mahadasha, dasha_a.antardasha) != (
            dasha_b.mahadasha,
            dasha_b.antardasha,
        ) or dasha_a.antardasha != dasha_b.antardasha

    def test_invalid_timezone_raises_at_case_level(self, wrapper):
        bad = make_domain_case(person=PersonInfo(
            name="x", gender="male", dob=date(1990, 6, 15), tob="10:30",
            place="Delhi", latitude=28.6139, longitude=77.209,
            timezone="Not/AZone", source="x",
        ))
        with pytest.raises(Exception):
            SnapshotComputer(wrapper).compute_case(bad)


# ── Tier 3: full persist + read-back (live database) ────────────────────────


@pytest.mark.integration
class TestImportPersistence:
    async def test_import_persists_and_reads_back(self):
        url = os.environ.get("DATABASE_URL")
        if not url:
            pytest.skip("DATABASE_URL not set")
        engine = create_async_engine(url)
        try:
            async with engine.connect() as conn:
                await conn.execute(select(1))
        except Exception:
            await engine.dispose()
            pytest.skip("Test database unreachable")

        factory = async_sessionmaker(engine, expire_on_commit=False)
        wrapper = EphemerisWrapper(ephemeris_path=_EPHE_DIR)
        case = make_domain_case(id="RC-TEST-INT")
        try:
            async with factory() as session:
                results = await ResearchCaseImportService(
                    session, SnapshotComputer(wrapper)
                ).import_cases([case])
                assert len(results) == 1
                r = results[0]
                assert r.errors == []
                assert r.duplicate is False
                assert r.total_events == 2
                assert r.total_snapshots_created == 2

                # Read back and verify the aggregate persisted.
                row = (
                    await session.execute(
                        select(ResearchCaseModel).where(
                            ResearchCaseModel.research_case_id == "RC-TEST-INT"
                        )
                    )
                ).scalar_one()
                events = (
                    await session.execute(
                        select(LifeEventModel).where(
                            LifeEventModel.research_case_id == row.id
                        )
                    )
                ).scalars().all()
                assert len(events) == 2
        finally:
            # Cleanup — leave the DB pristine.
            async with factory() as session:
                await session.execute(
                    text("delete from research_cases where research_case_id = 'RC-TEST-INT'")
                )
                await session.commit()
            await engine.dispose()

    async def test_duplicate_research_case_id_is_rejected(self):
        url = os.environ.get("DATABASE_URL")
        if not url:
            pytest.skip("DATABASE_URL not set")
        engine = create_async_engine(url)
        try:
            async with engine.connect() as conn:
                await conn.execute(select(1))
        except Exception:
            await engine.dispose()
            pytest.skip("Test database unreachable")

        factory = async_sessionmaker(engine, expire_on_commit=False)
        wrapper = EphemerisWrapper(ephemeris_path=_EPHE_DIR)
        case = make_domain_case(id="RC-TEST-INT")
        try:
            async with factory() as session:
                svc = ResearchCaseImportService(session, SnapshotComputer(wrapper))
                first = await svc.import_cases([case])
                assert first[0].errors == []
                second = await svc.import_cases([case])
                assert second[0].duplicate is True
                assert "already exists" in second[0].errors[0]
        finally:
            async with factory() as session:
                await session.execute(
                    text("delete from research_cases where research_case_id = 'RC-TEST-INT'")
                )
                await session.commit()
            await engine.dispose()

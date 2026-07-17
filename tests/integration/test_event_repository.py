"""
Module 14 Phase 3 — EventRepository persistence tests.

Run against a REAL PostgreSQL 16 database (schema built from the
actual Alembic migrations 0001-0005) — not a mock, not SQLite. Verifies
real FK behavior, soft-delete semantics, ordering, and DB-managed
timestamps, none of which a stubbed session could meaningfully check.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from apps.api.domain.events import EventRecord
from apps.api.repositories.event_repository import EventRepository

pytestmark = pytest.mark.asyncio


class TestCreate:
    async def test_create_returns_event_record_with_generated_id(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        record = await repo.create(
            chart_id=birth_chart_id, event_date=date(2010, 5, 1), title="  Marriage  ",
            category="marriage", is_verified=True,
        )
        assert isinstance(record, EventRecord)
        assert record.id is not None
        assert record.chart_id == birth_chart_id
        assert record.category == "marriage"
        assert record.is_verified is True

    async def test_title_is_stripped(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        record = await repo.create(chart_id=birth_chart_id, event_date=date(2010, 5, 1), title="  Marriage  ")
        assert record.title == "Marriage"

    async def test_optional_fields_default_correctly(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        record = await repo.create(chart_id=birth_chart_id, event_date=date(2010, 5, 1), title="X")
        assert record.user_id is None
        assert record.description is None
        assert record.category is None
        assert record.is_verified is False

    async def test_invalid_chart_id_violates_real_fk_constraint(self, db_session):
        repo = EventRepository(db_session)
        with pytest.raises(IntegrityError):
            await repo.create(chart_id=uuid.uuid4(), event_date=date(2010, 5, 1), title="X")


class TestGetById:
    async def test_returns_created_event(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2010, 5, 1), title="X")
        fetched = await repo.get_by_id(created.id)
        assert fetched == created

    async def test_returns_none_for_unknown_id(self, db_session):
        repo = EventRepository(db_session)
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_returns_none_for_soft_deleted_event(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2010, 5, 1), title="X")
        await repo.soft_delete(created.id)
        assert await repo.get_by_id(created.id) is None


class TestListForChart:
    async def test_orders_by_event_date_ascending(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        await repo.create(chart_id=birth_chart_id, event_date=date(2015, 1, 1), title="Later")
        await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="Earlier")
        await repo.create(chart_id=birth_chart_id, event_date=date(2010, 1, 1), title="Middle")

        results = await repo.list_for_chart(birth_chart_id)
        assert [r.title for r in results] == ["Earlier", "Middle", "Later"]

    async def test_filters_by_category(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="A", category="career")
        await repo.create(chart_id=birth_chart_id, event_date=date(2010, 1, 1), title="B", category="marriage")

        results = await repo.list_for_chart(birth_chart_id, category="career")
        assert [r.title for r in results] == ["A"]

    async def test_excludes_soft_deleted_events(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        keep = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="Keep")
        gone = await repo.create(chart_id=birth_chart_id, event_date=date(2010, 1, 1), title="Gone")
        await repo.soft_delete(gone.id)

        results = await repo.list_for_chart(birth_chart_id)
        assert [r.id for r in results] == [keep.id]

    async def test_only_returns_events_for_the_given_chart(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        other_chart_id = birth_chart_id  # placeholder overwritten below

        from apps.api.models.astrology import BirthChartModel
        from datetime import datetime, timezone
        other_model = BirthChartModel(
            subject_name="Other Subject",
            birth_datetime_utc=datetime(1991, 2, 2, 6, 0, tzinfo=timezone.utc),
            birth_latitude=1.0, birth_longitude=1.0, timezone_offset_minutes=0,
        )
        db_session.add(other_model)
        await db_session.flush()

        await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="Mine")
        await repo.create(chart_id=other_model.id, event_date=date(2005, 1, 1), title="Not mine")

        results = await repo.list_for_chart(birth_chart_id)
        assert [r.title for r in results] == ["Mine"]

    async def test_respects_limit_and_offset(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        for i in range(5):
            await repo.create(chart_id=birth_chart_id, event_date=date(2000 + i, 1, 1), title=f"E{i}")

        page = await repo.list_for_chart(birth_chart_id, limit=2, offset=1)
        assert [r.title for r in page] == ["E1", "E2"]


class TestUpdate:
    async def test_updates_only_supplied_fields(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(
            chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="Original",
            description="Original desc", category="career",
        )
        updated = await repo.update(created.id, title="Updated")
        assert updated.title == "Updated"
        assert updated.description == "Original desc"  # untouched
        assert updated.category == "career"  # untouched

    async def test_can_explicitly_clear_a_nullable_field(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(
            chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X", description="Has a value",
        )
        updated = await repo.update(created.id, description=None)
        assert updated.description is None

    async def test_returns_none_for_unknown_id(self, db_session):
        repo = EventRepository(db_session)
        assert await repo.update(uuid.uuid4(), title="X") is None

    async def test_returns_none_for_soft_deleted_event(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        await repo.soft_delete(created.id)
        assert await repo.update(created.id, title="Y") is None

    async def test_no_fields_supplied_returns_current_state_unchanged(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        result = await repo.update(created.id)
        assert result == created

    async def test_title_is_stripped_on_update(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        updated = await repo.update(created.id, title="  Trimmed  ")
        assert updated.title == "Trimmed"

    async def test_can_update_category_only(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X", category="career")
        updated = await repo.update(created.id, category="marriage")
        assert updated.category == "marriage"
        assert updated.title == "X"  # untouched

    async def test_can_update_is_verified_only(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X", is_verified=False)
        updated = await repo.update(created.id, is_verified=True)
        assert updated.is_verified is True

    async def test_can_update_event_date_only(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        updated = await repo.update(created.id, event_date=date(2020, 12, 31))
        assert updated.event_date == date(2020, 12, 31)


class TestSoftDelete:
    async def test_returns_true_on_first_delete(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        assert await repo.soft_delete(created.id) is True

    async def test_returns_false_on_second_delete(self, db_session, birth_chart_id):
        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        await repo.soft_delete(created.id)
        assert await repo.soft_delete(created.id) is False

    async def test_returns_false_for_unknown_id(self, db_session):
        repo = EventRepository(db_session)
        assert await repo.soft_delete(uuid.uuid4()) is False

    async def test_row_remains_in_db_with_deleted_at_set(self, db_session, birth_chart_id):
        from sqlalchemy import select
        from apps.api.models.astrology import EventModel

        repo = EventRepository(db_session)
        created = await repo.create(chart_id=birth_chart_id, event_date=date(2005, 1, 1), title="X")
        await repo.soft_delete(created.id)

        result = await db_session.execute(select(EventModel).where(EventModel.id == created.id))
        row = result.scalar_one()
        assert row.deleted_at is not None

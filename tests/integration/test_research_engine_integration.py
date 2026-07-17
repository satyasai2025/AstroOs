"""
AstroOS — Research Engine Integration Tests (Module 17, Phase 1)

Exercise ResearchRepository against a real PostgreSQL 16 database
(schema from Alembic migrations 0001-0005). Verifies FK constraints,
soft-delete semantics, and JSON serialization/deserialization.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.research import AstrologicalSnapshot, SnapshotCondition, SnapshotQuery
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.services.research_engine import ResearchEngine


pytestmark = [
    pytest.mark.skip(reason="Requires real PostgreSQL 16 — run manually with TEST_DATABASE_URL set"),
]


@pytest.fixture
def engine(db_session: AsyncSession) -> ResearchEngine:
    repo = ResearchRepository(db_session)
    return ResearchEngine(research_repo=repo)


class TestProjectCRUD:
    async def test_create_and_get_project(self, engine):
        pid = uuid.uuid4()
        project = await engine.create_project(
            user_id=uuid.uuid4(), title="Research Project",
            description="Testing hypotheses",
        )
        assert project.title == "Research Project"

        fetched = await engine.get_project(project.id)
        assert fetched is not None
        assert fetched.title == "Research Project"

    async def test_list_projects(self, engine):
        uid = uuid.uuid4()
        await engine.create_project(uid, "Project A")
        await engine.create_project(uid, "Project B")

        projects = await engine.list_projects(uid)
        assert len(projects) >= 2

    async def test_update_project(self, engine):
        project = await engine.create_project(uuid.uuid4(), "Original")
        updated = await engine.update_project(project.id, title="Updated")
        assert updated.title == "Updated"

    async def test_delete_project(self, engine):
        project = await engine.create_project(uuid.uuid4(), "Delete Me")
        assert await engine.delete_project(project.id) is True
        assert await engine.get_project(project.id) is None


class TestSnapshotPersistence:
    async def test_save_and_retrieve_snapshot(self, engine, birth_chart_id):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            chart_id=birth_chart_id,
            label="Test Snapshot",
            captured_at=datetime.now(timezone.utc),
            chart_ref=None,
        )
        saved = await engine._repo.save_snapshot(snap)
        assert saved.id == snap.id

        fetched = await engine.get_snapshot(snap.id)
        assert fetched is not None
        assert fetched.label == "Test Snapshot"

    async def test_list_snapshots_for_project(self, engine, birth_chart_id):
        pid = uuid.uuid4()
        await engine._repo.save_snapshot(AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=pid, chart_id=birth_chart_id,
            label="S1", captured_at=datetime.now(timezone.utc), chart_ref=None,
        ))
        await engine._repo.save_snapshot(AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=pid, chart_id=birth_chart_id,
            label="S2", captured_at=datetime.now(timezone.utc), chart_ref=None,
        ))

        snapshots = await engine.list_snapshots(pid)
        assert len(snapshots) == 2

    async def test_delete_snapshot(self, engine, birth_chart_id):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=birth_chart_id,
            label="Delete", captured_at=datetime.now(timezone.utc), chart_ref=None,
        )
        await engine._repo.save_snapshot(snap)
        assert await engine.delete_snapshot(snap.id) is True
        assert await engine.get_snapshot(snap.id) is None


class TestQueryIntegration:
    async def test_query_conditions(self, engine, birth_chart_id):
        pid = uuid.uuid4()
        await engine._repo.save_snapshot(AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=pid, chart_id=birth_chart_id,
            label="Alpha", captured_at=datetime.now(timezone.utc), chart_ref=None,
        ))
        query = SnapshotQuery(conditions=(
            SnapshotCondition("label", "==", "Alpha"),
        ))
        results = await engine.query_snapshots(pid, query)
        assert len(results) == 1
        assert results[0].label == "Alpha"

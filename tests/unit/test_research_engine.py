"""
AstroOS — ResearchEngine Unit Tests (Module 17, Phase 1)

All persistence is mocked at the repository boundary. No real DB required.
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from apps.api.domain.research import (
    AstrologicalSnapshot,
    ResearchExperiment,
    ResearchProject,
    SnapshotCondition,
    SnapshotQuery,
)
from apps.api.services.research_engine import ResearchEngine


@pytest.fixture
def engine() -> ResearchEngine:
    repo = AsyncMock()
    repo.create_project = AsyncMock()
    repo.get_project = AsyncMock()
    repo.list_projects = AsyncMock()
    repo.update_project = AsyncMock()
    repo.delete_project = AsyncMock()
    repo.create_experiment = AsyncMock()
    repo.get_experiment = AsyncMock()
    repo.list_experiments = AsyncMock()
    repo.update_experiment = AsyncMock()
    repo.assign_snapshots_to_experiment = AsyncMock()
    repo.save_snapshot = AsyncMock()
    repo.get_snapshot = AsyncMock()
    repo.list_snapshots = AsyncMock()
    repo.delete_snapshot = AsyncMock()
    return ResearchEngine(research_repo=repo)


class TestProjectManagement:
    async def test_create_project(self, engine):
        engine._repo.create_project.return_value = ResearchProject(
            id=uuid.uuid4(), user_id=uuid.uuid4(), title="Test",
        )
        project = await engine.create_project(
            user_id=uuid.uuid4(), title="Test",
        )
        assert project.title == "Test"
        engine._repo.create_project.assert_called_once()

    async def test_get_project(self, engine):
        pid = uuid.uuid4()
        engine._repo.get_project.return_value = ResearchProject(
            id=pid, user_id=uuid.uuid4(), title="Found",
        )
        project = await engine.get_project(pid)
        assert project.title == "Found"

    async def test_get_project_not_found(self, engine):
        engine._repo.get_project.return_value = None
        result = await engine.get_project(uuid.uuid4())
        assert result is None

    async def test_list_projects(self, engine):
        engine._repo.list_projects.return_value = (
            ResearchProject(id=uuid.uuid4(), user_id=uuid.uuid4(), title="A"),
        )
        projects = await engine.list_projects(user_id=uuid.uuid4())
        assert len(projects) == 1

    async def test_update_project(self, engine):
        engine._repo.update_project.return_value = ResearchProject(
            id=uuid.uuid4(), user_id=uuid.uuid4(), title="Updated",
        )
        result = await engine.update_project(uuid.uuid4(), title="Updated")
        assert result.title == "Updated"

    async def test_delete_project(self, engine):
        engine._repo.delete_project.return_value = True
        assert await engine.delete_project(uuid.uuid4()) is True


class TestExperimentManagement:
    async def test_create_experiment(self, engine):
        engine._repo.create_experiment.return_value = ResearchExperiment(
            id=uuid.uuid4(), project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
        )
        exp = await engine.create_experiment(
            project_id=uuid.uuid4(), title="Exp",
            hypothesis="H", methodology="M",
        )
        assert exp.hypothesis == "H"

    async def test_get_experiment_not_found(self, engine):
        engine._repo.get_experiment.return_value = None
        result = await engine.get_experiment(uuid.uuid4())
        assert result is None

    async def test_complete_experiment(self, engine):
        eid = uuid.uuid4()
        engine._repo.update_experiment.return_value = ResearchExperiment(
            id=eid, project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
            status="completed", findings="Found evidence",
        )
        result = await engine.complete_experiment(eid, "Found evidence")
        assert result.status == "completed"
        assert result.findings == "Found evidence"


class TestSnapshotManagement:
    async def test_capture_snapshot(self, engine):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label="test", captured_at=None, chart_ref=None,
        )
        engine._repo.save_snapshot.return_value = snap

        result = await engine.capture_snapshot(
            project_id=uuid.uuid4(), chart_id=uuid.uuid4(), label="test",
            chart_ref=None,
        )
        assert result.label == "test"
        engine._repo.save_snapshot.assert_called_once()

    async def test_get_snapshot(self, engine):
        engine._repo.get_snapshot.return_value = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label="found", captured_at=None, chart_ref=None,
        )
        result = await engine.get_snapshot(uuid.uuid4())
        assert result.label == "found"

    async def test_list_snapshots(self, engine):
        engine._repo.list_snapshots.return_value = (
            AstrologicalSnapshot(
                id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
                label="A", captured_at=None, chart_ref=None,
            ),
        )
        results = await engine.list_snapshots(uuid.uuid4())
        assert len(results) == 1

    async def test_delete_snapshot(self, engine):
        engine._repo.delete_snapshot.return_value = True
        assert await engine.delete_snapshot(uuid.uuid4()) is True


class TestQuery:
    async def test_query_no_conditions_returns_all(self, engine):
        engine._repo.list_snapshots.return_value = (
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="A", captured_at=None, chart_ref=None),
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="B", captured_at=None, chart_ref=None),
        )
        results = await engine.query_snapshots(
            uuid.uuid4(), SnapshotQuery(),
        )
        assert len(results) == 2

    async def test_query_filters_by_condition(self, engine):
        # Mock returns snapshots; condition evaluation happens in-memory
        # This test verifies the engine delegates to the repo and accessor.
        engine._repo.list_snapshots.return_value = (
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="A", captured_at=None, chart_ref=None),
        )
        query = SnapshotQuery(conditions=(
            SnapshotCondition("label", "==", "A"),
        ))
        results = await engine.query_snapshots(uuid.uuid4(), query)
        assert len(results) == 1


class TestComparison:
    async def test_compare_snapshots_both_found(self, engine):
        sid_a = uuid.uuid4()
        sid_b = uuid.uuid4()
        engine._repo.get_snapshot.side_effect = [
            AstrologicalSnapshot(id=sid_a, project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="A", captured_at=None, chart_ref=None),
            AstrologicalSnapshot(id=sid_b, project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="B", captured_at=None, chart_ref=None),
        ]
        result = await engine.compare_snapshots(sid_a, sid_b)
        assert result is not None
        assert result.snapshot_a_id == sid_a
        assert result.snapshot_b_id == sid_b

    async def test_compare_snapshots_one_missing(self, engine):
        engine._repo.get_snapshot.side_effect = [None, None]
        result = await engine.compare_snapshots(uuid.uuid4(), uuid.uuid4())
        assert result is None

    async def test_compare_charts(self, engine):
        cid_a = uuid.uuid4()
        cid_b = uuid.uuid4()
        engine._repo.list_snapshots.return_value = (
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=cid_a, label="A", captured_at=None, chart_ref=None),
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=cid_b, label="B", captured_at=None, chart_ref=None),
        )
        result = await engine.compare_charts(cid_a, cid_b, uuid.uuid4())
        assert result is not None

    async def test_compare_charts_one_missing(self, engine):
        engine._repo.list_snapshots.return_value = (
            AstrologicalSnapshot(id=uuid.uuid4(), project_id=uuid.uuid4(),
                chart_id=uuid.uuid4(), label="A", captured_at=None, chart_ref=None),
        )
        result = await engine.compare_charts(
            uuid.uuid4(), uuid.uuid4(), uuid.uuid4(),
        )
        assert result is None

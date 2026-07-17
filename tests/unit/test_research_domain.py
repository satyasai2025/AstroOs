"""
AstroOS — Research Domain Model Unit Tests (Module 17, Phase 1)
"""

import dataclasses
import uuid
from datetime import date

import pytest

from apps.api.domain.research import (
    AstrologicalSnapshot,
    FieldDiff,
    ResearchExperiment,
    ResearchProject,
    SnapshotComparison,
    SnapshotCondition,
    SnapshotQuery,
)


class TestResearchProject:
    def test_is_frozen(self):
        p = ResearchProject(id=uuid.uuid4(), user_id=uuid.uuid4(), title="Test")
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.title = "Changed"

    def test_default_status(self):
        p = ResearchProject(id=uuid.uuid4(), user_id=uuid.uuid4(), title="Test")
        assert p.status == "active"

    def test_optional_description(self):
        p = ResearchProject(id=uuid.uuid4(), user_id=uuid.uuid4(), title="Test", description="A project")
        assert p.description == "A project"


class TestResearchExperiment:
    def test_is_frozen(self):
        e = ResearchExperiment(
            id=uuid.uuid4(), project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            e.status = "completed"

    def test_default_status_is_draft(self):
        e = ResearchExperiment(
            id=uuid.uuid4(), project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
        )
        assert e.status == "draft"

    def test_default_snapshot_ids_empty(self):
        e = ResearchExperiment(
            id=uuid.uuid4(), project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
        )
        assert e.snapshot_ids == ()

    def test_optional_findings(self):
        e = ResearchExperiment(
            id=uuid.uuid4(), project_id=uuid.uuid4(),
            title="Exp", hypothesis="H", methodology="M",
            findings="Conclusive evidence found",
        )
        assert e.findings == "Conclusive evidence found"


class TestAstrologicalSnapshot:
    def test_is_frozen(self):
        s = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label=None, captured_at=None, chart_ref=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.label = "Changed"

    def test_default_snapshot_version(self):
        s = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label=None, captured_at=None, chart_ref=None,
        )
        assert s.snapshot_version == "1.0"

    def test_all_fields_default_to_none(self):
        s = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label=None, captured_at=None, chart_ref=None,
        )
        assert s.yogas is None
        assert s.shadbala_components is None
        assert s.dasha_trees is None
        assert s.divisional_charts is None
        assert s.timeline_ref is None
        assert s.verification_ref is None


class TestSnapshotCondition:
    def test_default_description(self):
        c = SnapshotCondition(field="x", operator="==", value=1)
        assert c.description == ""

    def test_is_frozen(self):
        c = SnapshotCondition(field="x", operator="==", value=1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.value = 2


class TestSnapshotQuery:
    def test_empty_conditions(self):
        q = SnapshotQuery()
        assert q.conditions == ()

    def test_with_conditions(self):
        c1 = SnapshotCondition(field="a", operator="==", value=1)
        c2 = SnapshotCondition(field="b", operator=">", value=0)
        q = SnapshotQuery(conditions=(c1, c2))
        assert len(q.conditions) == 2


class TestFieldDiff:
    def test_is_frozen(self):
        d = FieldDiff(field="x", value_a=1, value_b=2)
        with pytest.raises(dataclasses.FrozenInstanceError):
            d.field = "y"

    def test_stores_both_values(self):
        d = FieldDiff(field="test", value_a="old", value_b="new")
        assert d.value_a == "old"
        assert d.value_b == "new"


class TestSnapshotComparison:
    def test_defaults(self):
        c = SnapshotComparison(
            snapshot_a_id=uuid.uuid4(), snapshot_b_id=uuid.uuid4(),
            chart_id_a=uuid.uuid4(), chart_id_b=uuid.uuid4(),
        )
        assert c.matching_fields == ()
        assert c.differing_fields == ()

    def test_is_frozen(self):
        c = SnapshotComparison(
            snapshot_a_id=uuid.uuid4(), snapshot_b_id=uuid.uuid4(),
            chart_id_a=uuid.uuid4(), chart_id_b=uuid.uuid4(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.matching_fields = ("x",)

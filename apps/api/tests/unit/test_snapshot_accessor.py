"""
AstroOS — SnapshotAccessor Unit Tests (Module 17, Phase 1)
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.research import (
    AstrologicalSnapshot,
    SnapshotCondition,
    SnapshotQuery,
)
from apps.api.domain.yoga import YogaResult
from apps.api.services.snapshot_accessor import SnapshotAccessor


def _minimal_snapshot(**overrides) -> AstrologicalSnapshot:
    """Minimal snapshot with a chart and yogas for accessor testing."""
    planet = SiderealPosition(
        planet="jupiter", sidereal_longitude=100.0, rashi="cancer",
        rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
        is_retrograde=False, is_combust=False, combustion_orb=None,
        dignity=DignityType.FRIENDLY,
    )
    sun = SiderealPosition(
        planet="sun", sidereal_longitude=0.0, rashi="aries",
        rashi_degree=0.0, house_number=1, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=False, combustion_orb=None,
        dignity=DignityType.OWN,
    )
    chart = D1Chart(
        ephemeris=None, ascendant=None, houses=[], planets=[sun, planet],
        aspects=[], planet_strengths=[], panchanga=None,
        ayanamsa_system="lahiri", house_system="W",
    )
    yoga = YogaResult(
        yoga_id="BPHS-PM-001", name="Ruchaka", category="Panch Mahapurusha",
        source_text="BPHS 46", rule_version="1.0", is_present=True, strength="full",
    )

    defaults = dict(
        id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
        label="test", captured_at=None, chart_ref=chart,
        yogas=(yoga,),
        sarvashtakavarga=None,
    )
    defaults.update(overrides)
    return AstrologicalSnapshot(**defaults)


class TestGet:
    def test_navigate_attribute(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.get("label") == "test"

    def test_navigate_nested_attribute(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.get("chart_ref.ayanamsa_system") == "lahiri"

    def test_navigate_list_index(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.get("chart_ref.planets.0.planet") == "sun"
        assert accessor.get("chart_ref.planets.1.house_number") == 5

    def test_navigate_dict(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        # yogas is a tuple accessed by index, then attribute
        assert accessor.get("yogas.0.yoga_id") == "BPHS-PM-001"
        assert accessor.get("yogas.0.is_present") is True

    def test_invalid_path_returns_none(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.get("nonexistent.field") is None

    def test_out_of_range_index_returns_none(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.get("chart_ref.planets.99.planet") is None

    def test_none_intermediate_returns_none(self):
        snap = _minimal_snapshot(chart_ref=None)
        accessor = SnapshotAccessor(snap)
        assert accessor.get("chart_ref.ayanamsa_system") is None


class TestMatches:
    def test_eq_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("label", "==", "test"))

    def test_eq_no_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert not accessor.matches(SnapshotCondition("label", "==", "other"))

    def test_ne_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("label", "!=", "other"))

    def test_gt_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("chart_ref.planets.1.house_number", ">", 3))

    def test_lt_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("chart_ref.planets.0.house_number", "<", 3))

    def test_gte_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("chart_ref.planets.1.house_number", ">=", 5))

    def test_in_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.matches(SnapshotCondition("yogas.0.yoga_id", "in", ["BPHS-PM-001", "BPHS-PM-002"]))

    def test_in_no_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert not accessor.matches(SnapshotCondition("yogas.0.yoga_id", "in", ["OTHER"]))

    def test_none_field_returns_false(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert not accessor.matches(SnapshotCondition("nonexistent", "==", None))

    def test_unknown_operator_returns_false(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert not accessor.matches(SnapshotCondition("label", "??", "test"))

    def test_type_error_returns_false(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert not accessor.matches(SnapshotCondition("label", ">", 42))


class TestSearch:
    def test_all_conditions_match(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        query = SnapshotQuery(conditions=(
            SnapshotCondition("label", "==", "test"),
            SnapshotCondition("yogas.0.is_present", "==", True),
        ))
        assert accessor.search(query) is True

    def test_one_condition_fails(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        query = SnapshotQuery(conditions=(
            SnapshotCondition("label", "==", "test"),
            SnapshotCondition("yogas.0.is_present", "==", False),
        ))
        assert accessor.search(query) is False

    def test_empty_query_returns_true(self):
        snap = _minimal_snapshot()
        accessor = SnapshotAccessor(snap)
        assert accessor.search(SnapshotQuery()) is True


class TestCompare:
    def test_identical_snapshots_no_diffs(self):
        snap = _minimal_snapshot()
        a = SnapshotAccessor(snap)
        b = SnapshotAccessor(snap)
        result = a.compare(b)
        assert result.snapshot_a_id == result.snapshot_b_id

    def test_different_labels_detected(self):
        snap_a = _minimal_snapshot(label="Project A")
        snap_b = _minimal_snapshot(label="Project B")
        a = SnapshotAccessor(snap_a)
        b = SnapshotAccessor(snap_b)
        result = a.compare(b)
        diffs = {d.field: d for d in result.differing_fields}
        assert "label" in diffs

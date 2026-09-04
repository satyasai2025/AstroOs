"""
AstroOS — Yoga Activation Timeline Unit Tests (Phase 2, v2.1.0)

Tests for apps.api.services.yoga_timeline:
  - build_yoga_timeline(): activation timeline for a single yoga
  - build_all_timelines(): batch timeline building for present yogas
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.yoga import YogaResult
from apps.api.services.yoga_timeline import (
    YogaActivation,
    YogaTimeline,
    build_all_timelines,
    build_yoga_timeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_period(
    lord: str,
    start: date,
    end: date,
    level: int,
    sub_periods: tuple[DashaPeriod, ...] = (),
) -> DashaPeriod:
    return DashaPeriod(
        lord=lord,
        start_date=start,
        end_date=end,
        duration_days=(end - start).days,
        level=level,
        sub_periods=sub_periods,
    )


def _make_dasha_tree(mahadashas: tuple[DashaPeriod, ...]) -> DashaTree:
    return DashaTree(
        system="vimshottari",
        birth_date=date(1990, 1, 1),
        trigger_planet="jupiter",
        trigger_nakshatra="punarvasu",
        trigger_nakshatra_number=7,
        mahadashas=mahadashas,
        max_depth=3,
        total_cycle_years=120,
    )


def _make_result(
    yoga_id: str = "BPHS-TEST-001",
    name: str = "Test Yoga",
    is_present: bool = True,
    involved_planets: tuple[str, ...] = ("jupiter",),
) -> YogaResult:
    return YogaResult(
        yoga_id=yoga_id,
        name=name,
        category="Test",
        source_text="BPHS",
        rule_version="2.0",
        is_present=is_present,
        strength="full" if is_present else None,
        involved_planets=involved_planets,
    )


# ---------------------------------------------------------------------------
# build_yoga_timeline tests
# ---------------------------------------------------------------------------

class TestBuildYogaTimeline:
    """Tests for build_yoga_timeline()."""

    def test_returns_yoga_timeline(self):
        """Must return a YogaTimeline instance."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result()
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert isinstance(timeline, YogaTimeline)

    def test_populates_yoga_id(self):
        """Timeline must carry the yoga_id from the result."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(yoga_id="BPHS-PM-001")
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert timeline.yoga_id == "BPHS-PM-001"

    def test_populates_yoga_name(self):
        """Timeline must carry the yoga name from the result."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(name="Ruchaka Yoga")
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert timeline.yoga_name == "Ruchaka Yoga"

    def test_not_present_returns_empty_timeline(self):
        """Absent yoga must return a timeline with no activations."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(is_present=False)
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert len(timeline.activations) == 0
        assert timeline.current_activation is None

    def test_no_involved_planets_returns_empty_timeline(self):
        """Yoga with no involved_planets must return empty timeline even if present."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(involved_planets=())
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert len(timeline.activations) == 0
        assert timeline.current_activation is None

    def test_matching_planet_produces_activations(self):
        """When involved planet matches a mahadasha lord, activations are produced."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
            _make_period("saturn", date(2016, 8, 12), date(2035, 9, 3), level=1),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert len(timeline.activations) >= 1
        assert any(a.planet == "jupiter" for a in timeline.activations)

    def test_non_matching_planet_no_activations(self):
        """When no involved planet matches any dasha lord, no activations."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
            _make_period("saturn", date(2016, 8, 12), date(2035, 9, 3), level=1),
        ))
        result = _make_result(involved_planets=("mars",))
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert len(timeline.activations) == 0

    def test_current_activation_flagged(self):
        """Today's date within a matching period marks is_current=True."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert timeline.current_activation is not None
        assert timeline.current_activation.is_current is True
        assert timeline.current_activation.planet == "jupiter"

    def test_no_current_activation_when_outside_range(self):
        """Today outside all matching periods means no current_activation."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2003, 1, 1), level=1),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2010, 1, 1))
        assert timeline.current_activation is None

    def test_antardasha_activation(self):
        """Involved planet matching an antardasha lord also produces activation."""
        antardashas = (
            _make_period("mars", date(2000, 1, 1), date(2003, 4, 1), level=2),
            _make_period("jupiter", date(2003, 4, 1), date(2005, 7, 1), level=2),
        )
        tree = _make_dasha_tree((
            _make_period("saturn", date(2000, 1, 1), date(2020, 1, 1), level=1, sub_periods=antardashas),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2004, 1, 1))
        assert len(timeline.activations) >= 1
        assert any(a.planet == "jupiter" and a.period_level == 2 for a in timeline.activations)

    def test_activations_sorted_by_start_date(self):
        """Activations must be sorted by start_date ascending."""
        antardashas = (
            _make_period("jupiter", date(2000, 1, 1), date(2003, 4, 1), level=2),
            _make_period("mars", date(2003, 4, 1), date(2005, 7, 1), level=2),
        )
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2005, 7, 1), level=1, sub_periods=antardashas),
            _make_period("saturn", date(2005, 7, 1), date(2025, 1, 1), level=1),
        ))
        result = _make_result(involved_planets=("jupiter", "mars"))
        timeline = build_yoga_timeline(result, tree, today=date(2004, 1, 1))
        dates = [a.start_date for a in timeline.activations]
        assert dates == sorted(dates)

    def test_all_activation_yoga_ids_match(self):
        """Every activation entry must carry the correct yoga_id."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(yoga_id="BPHS-CY-001")
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        for activation in timeline.activations:
            assert activation.yoga_id == "BPHS-CY-001"

    def test_activation_period_name_contains_lord(self):
        """Period name should include the capitalized planet name."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2005, 6, 15))
        assert len(timeline.activations) >= 1
        assert "Jupiter" in timeline.activations[0].period_name

    def test_multi_planet_yoga_multiple_activation_sources(self):
        """A multi-planet yoga should activate when either planet is the dasha lord."""
        antardashas_jup = (
            _make_period("mars", date(2000, 1, 1), date(2003, 4, 1), level=2),
        )
        antardashas_sat = (
            _make_period("jupiter", date(2016, 8, 12), date(2019, 10, 1), level=2),
        )
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1, sub_periods=antardashas_jup),
            _make_period("saturn", date(2016, 8, 12), date(2035, 9, 3), level=1, sub_periods=antardashas_sat),
        ))
        result = _make_result(involved_planets=("jupiter", "mars"))
        timeline = build_yoga_timeline(result, tree, today=date(2010, 1, 1))
        planets_found = {a.planet for a in timeline.activations}
        assert "jupiter" in planets_found
        assert "mars" in planets_found

    def test_max_depth_1_limits_to_mahadasha(self):
        """With max_depth=1, only mahadasha-level activations are returned."""
        antardashas = (
            _make_period("jupiter", date(2000, 1, 1), date(2003, 4, 1), level=2),
        )
        tree = _make_dasha_tree((
            _make_period("saturn", date(2000, 1, 1), date(2020, 1, 1), level=1, sub_periods=antardashas),
        ))
        result = _make_result(involved_planets=("jupiter",))
        timeline = build_yoga_timeline(result, tree, today=date(2001, 1, 1), max_depth=1)
        # Jupiter is only in antardasha (level 2), so max_depth=1 should find nothing
        assert len(timeline.activations) == 0


# ---------------------------------------------------------------------------
# build_all_timelines tests
# ---------------------------------------------------------------------------

class TestBuildAllTimelines:
    """Tests for build_all_timelines()."""

    def test_returns_list(self):
        """Must return a list."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [_make_result()]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        assert isinstance(timelines, list)

    def test_only_present_yogas_get_timelines(self):
        """Absent yogas must not appear in the output."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [
            _make_result(yoga_id="BPHS-PRESENT-001", is_present=True),
            _make_result(yoga_id="BPHS-ABSENT-001", is_present=False),
        ]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        ids = {t.yoga_id for t in timelines}
        assert "BPHS-PRESENT-001" in ids
        assert "BPHS-ABSENT-001" not in ids

    def test_empty_results_returns_empty(self):
        """Empty input list returns empty output."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        timelines = build_all_timelines([], tree, today=date(2005, 6, 15))
        assert timelines == []

    def test_all_absent_returns_empty(self):
        """All absent yogas returns empty list."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [
            _make_result(is_present=False),
            _make_result(yoga_id="BPHS-TEST-002", is_present=False),
        ]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        assert timelines == []

    def test_returns_timeline_per_present_yoga(self):
        """One timeline per present yoga in the results."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [
            _make_result(yoga_id=f"BPHS-TEST-{i:03d}", is_present=True)
            for i in range(5)
        ]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        assert len(timelines) == 5

    def test_timeline_yoga_ids_match_input(self):
        """Each timeline's yoga_id must match the corresponding input result."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [
            _make_result(yoga_id="BPHS-PM-001"),
            _make_result(yoga_id="BPHS-CY-005"),
        ]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        ids = {t.yoga_id for t in timelines}
        assert ids == {"BPHS-PM-001", "BPHS-CY-005"}

    def test_current_activation_propagated(self):
        """When today falls in a matching period, current_activation is set."""
        tree = _make_dasha_tree((
            _make_period("jupiter", date(2000, 1, 1), date(2016, 8, 12), level=1),
        ))
        results = [_make_result(involved_planets=("jupiter",))]
        timelines = build_all_timelines(results, tree, today=date(2005, 6, 15))
        assert len(timelines) == 1
        assert timelines[0].current_activation is not None
        assert timelines[0].current_activation.is_current is True

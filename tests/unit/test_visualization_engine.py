"""
AstroOS — VisualizationEngine Unit Tests (Module 22, Phase 1)
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.report import ReportContent
from apps.api.domain.statistics import Crosstab, Distribution
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.timeline import Timeline, TimelineEntry, TimelineSummary
from apps.api.domain.visualization import VisualizationRequest, VisualizationTheme
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.services.visualization_engine import (
    ChartVisualizer,
    CytoscapeAdapter,
    D3Adapter,
    ResearchVisualizer,
    StatisticsVisualizer,
    TimelineVisualizer,
    VisualizationEngine,
)


def _make_chart() -> D1Chart:
    from apps.api.domain.ephemeris import Ascendant, HouseCusp
    planets = [
        SiderealPosition(
            planet="sun", sidereal_longitude=10.0, rashi="aries",
            rashi_degree=10.0, house_number=1, nakshatra="ashwini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN,
        ),
        SiderealPosition(
            planet="moon", sidereal_longitude=40.0, rashi="taurus",
            rashi_degree=10.0, house_number=2, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY,
        ),
    ]
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi="aries",
                    rashi_degree=10.0, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n * 30),
                        sidereal_longitude=float(n * 30), rashi="") for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


def _make_timeline() -> Timeline:
    cid = uuid.uuid4()
    event = EventRecord(id=uuid.uuid4(), chart_id=cid, event_date=date(2005, 1, 1), title="E", category="career")
    context = EventAstrologicalContext(event_id=event.id, chart_id=cid, active_dashas={}, transits=(), natal_snapshot=None)
    analysis = EventAnalysis(event=event, context=context)
    entry = TimelineEntry(event_id=event.id, event_date=date(2005, 1, 1), title="E", category="career",
                          is_verified=True, sort_key="2005-01-01", analysis=analysis)
    return Timeline(
        chart_id=cid, entries=(entry,),
        summary=TimelineSummary(total_events=1, date_range=(date(2005,1,1), date(2005,1,1)),
                               events_per_category={"career": 1}, events_per_dasha_system={},
                               verified_count=1, unverified_count=0),
        dasha_breakdown={}, clusters=(),
    )


theme = VisualizationTheme()


class TestChartVisualizer:
    def test_renders_wheel_layout(self):
        chart = _make_chart()
        result = ChartVisualizer.render(chart, theme)
        assert result.visualization_type == "chart_wheel"
        assert result.renderer == "chart_visualizer"
        assert "layout" in result.data
        nodes = result.data["layout"]["nodes"]
        assert len(nodes) >= 2  # at least sun + moon

    def test_wheel_has_house_nodes(self):
        chart = _make_chart()
        result = ChartVisualizer.render(chart, theme)
        nodes = result.data["layout"]["nodes"]
        house_ids = [n["id"] for n in nodes if n["id"].startswith("house_")]
        assert len(house_ids) == 12


class TestTimelineVisualizer:
    def test_renders_timeline(self):
        tl = _make_timeline()
        result = TimelineVisualizer.render(tl, theme)
        assert result.visualization_type == "timeline"
        assert len(result.data["layout"]["nodes"]) == 1

    def test_empty_timeline(self):
        cid = uuid.uuid4()
        tl = Timeline(
            chart_id=cid, entries=(),
            summary=TimelineSummary(total_events=0, date_range=(date(2000,1,1), date(2000,1,1)),
                                   events_per_category={}, events_per_dasha_system={},
                                   verified_count=0, unverified_count=0),
            dasha_breakdown={}, clusters=(),
        )
        result = TimelineVisualizer.render(tl, theme)
        assert result.metadata["total_events"] == 0


class TestStatisticsVisualizer:
    def test_distribution_render(self):
        dist = Distribution(label="Houses", variable="planet.x.house",
                            bins=("1","2","3"), counts=(5,10,15), total=30)
        result = StatisticsVisualizer.render_distribution(dist, theme)
        assert result.visualization_type == "distribution"
        assert result.data["series"][0]["values"] == [5, 10, 15]

    def test_crosstab_render(self):
        ct = Crosstab(label="T", row_variable="r", column_variable="c",
                      row_labels=("a","b"), column_labels=("x","y"),
                      cells=((1,2),(3,4)), row_totals=(3,7))
        result = StatisticsVisualizer.render_crosstab(ct, theme)
        assert result.visualization_type == "crosstab"
        assert result.data["heatmap"]["cells"] == [[1,2],[3,4]]


class TestResearchVisualizer:
    def test_empty_comparison(self):
        result = ResearchVisualizer.render_comparison((), theme)
        assert result.visualization_type == "snapshot_comparison"
        assert result.metadata["snapshot_count"] == 0

    def test_comparison_with_snapshots(self):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label="S1", captured_at=None, chart_ref=_make_chart(),
        )
        result = ResearchVisualizer.render_comparison((snap,), theme)
        assert result.metadata["snapshot_count"] == 1

    def test_graph_render(self):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label="S1", captured_at=None, chart_ref=_make_chart(),
        )
        result = ResearchVisualizer.render_graph((snap,), theme)
        assert result.visualization_type == "relationship_graph"
        assert result.metadata["node_count"] > 0
        assert len(result.data["layout"]["nodes"]) > 0

    def test_empty_graph(self):
        result = ResearchVisualizer.render_graph((), theme)
        # Should still return a valid result.
        assert result.metadata.get("node_count", 0) >= 0


class TestD3Adapter:
    def test_adapts_result(self):
        chart = _make_chart()
        result = ChartVisualizer.render(chart, theme)
        adapted = D3Adapter.adapt(result)
        assert "d3" in adapted
        assert "nodes" in adapted["d3"]
        assert "series" in adapted["d3"]


class TestCytoscapeAdapter:
    def test_adapts_result(self):
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=uuid.uuid4(), chart_id=uuid.uuid4(),
            label="S1", captured_at=None, chart_ref=_make_chart(),
        )
        result = ResearchVisualizer.render_graph((snap,), theme)
        adapted = CytoscapeAdapter.adapt(result)
        assert "cytoscape" in adapted
        assert "elements" in adapted["cytoscape"]
        assert "layout" in adapted["cytoscape"]


class TestVisualizationEngine:
    def test_available_visualizations(self):
        available = VisualizationEngine.available_visualizations()
        types = [v["type"] for v in available]
        assert "chart_wheel" in types
        assert "timeline" in types
        assert "distribution" in types
        assert "crosstab" in types
        assert "snapshot_comparison" in types
        assert "relationship_graph" in types

    def test_visualize_chart_wheel(self):
        chart = _make_chart()
        req = VisualizationRequest(
            visualization_type="chart_wheel",
            source_data={"chart": chart},
        )
        result = VisualizationEngine.visualize(req)
        assert result.visualization_type == "chart_wheel"

    def test_visualize_timeline(self):
        tl = _make_timeline()
        req = VisualizationRequest(
            visualization_type="timeline",
            source_data={"timeline": tl},
        )
        result = VisualizationEngine.visualize(req)
        assert result.visualization_type == "timeline"

    def test_visualize_distribution(self):
        dist = Distribution(label="T", variable="x",
                            bins=("a",), counts=(5,), total=5)
        req = VisualizationRequest(
            visualization_type="distribution",
            source_data={"distribution": dist},
        )
        result = VisualizationEngine.visualize(req)
        assert result.visualization_type == "distribution"

    def test_visualize_crosstab(self):
        ct = Crosstab(label="T", row_variable="r", column_variable="c",
                      row_labels=("a",), column_labels=("x",),
                      cells=((1,),), row_totals=(1,))
        req = VisualizationRequest(
            visualization_type="crosstab",
            source_data={"crosstab": ct},
        )
        result = VisualizationEngine.visualize(req)
        assert result.visualization_type == "crosstab"

    def test_visualize_unknown_raises(self):
        req = VisualizationRequest(visualization_type="nonexistent")
        with pytest.raises(ValueError, match="Unknown visualization type"):
            VisualizationEngine.visualize(req)

    def test_visualize_chart_no_data_raises(self):
        req = VisualizationRequest(visualization_type="chart_wheel", source_data={})
        with pytest.raises(ValueError, match="requires source_data"):
            VisualizationEngine.visualize(req)

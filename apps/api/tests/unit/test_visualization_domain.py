"""
AstroOS — Visualization Domain Model Unit Tests (Module 22, Phase 1)
"""

import dataclasses

import pytest

from apps.api.domain.visualization import (
    SeriesData,
    VisualizationEdge,
    VisualizationLayout,
    VisualizationNode,
    VisualizationRequest,
    VisualizationResult,
    VisualizationTheme,
    get_theme,
)


class TestVisualizationTheme:
    def test_default_theme(self):
        t = VisualizationTheme()
        assert t.name == "light"
        assert t.colors["benefic"] == "#4CAF50"
        assert t.colors["malefic"] == "#f44336"
        assert "sun" in t.planet_colors
        assert "aries" in t.rashi_colors

    def test_get_theme(self):
        t = get_theme("light")
        assert t.name == "light"
        assert get_theme("nonexistent") is t  # fallback to light


class TestVisualizationNode:
    def test_is_frozen(self):
        n = VisualizationNode(id="n1", label="Sun", group="planet")
        with pytest.raises(dataclasses.FrozenInstanceError):
            n.x = 100

    def test_defaults(self):
        n = VisualizationNode(id="n1", label="Sun", group="planet")
        assert n.x == 0.0
        assert n.radius == 40.0
        assert n.color == "#999999"
        assert n.metadata == {}


class TestVisualizationEdge:
    def test_is_frozen(self):
        e = VisualizationEdge(source_id="a", target_id="b")
        with pytest.raises(dataclasses.FrozenInstanceError):
            e.weight = 5.0

    def test_defaults(self):
        e = VisualizationEdge(source_id="a", target_id="b")
        assert e.label == ""
        assert e.edge_type == "default"
        assert e.dashed is False


class TestVisualizationLayout:
    def test_defaults(self):
        l = VisualizationLayout(type="wheel")
        assert l.width == 800
        assert l.nodes == ()
        assert l.edges == ()


class TestSeriesData:
    def test_stores_data(self):
        s = SeriesData(
            label="Test", values=(1.0, 2.0), labels=("a", "b"), color="#000",
        )
        assert s.values == (1.0, 2.0)
        assert s.labels == ("a", "b")


class TestVisualizationRequest:
    def test_defaults(self):
        r = VisualizationRequest(visualization_type="chart_wheel")
        assert r.theme_name == "light"
        assert r.width == 800

    def test_theme_property(self):
        r = VisualizationRequest(visualization_type="chart_wheel")
        assert r.theme.name == "light"


class TestVisualizationResult:
    def test_is_frozen(self):
        r = VisualizationResult(
            visualization_type="chart_wheel",
            renderer="chart_visualizer",
            version="1.0",
            theme="light",
            data={},
            metadata={},
            generated_at="2026-07-14T12:00:00",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.version = "2.0"

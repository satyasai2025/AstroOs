"""
AstroOS — Visualization Domain Objects (Module 22, Phase 1)

Presentation-ready data structures for frontend rendering (D3.js,
Cytoscape.js). Pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class VisualizationTheme:
    """Visual styling parameters shared across all visualizers."""

    name: str = "light"
    colors: dict[str, str] = field(default_factory=lambda: {
        "benefic": "#4CAF50",
        "malefic": "#f44336",
        "neutral": "#9E9E9E",
        "background": "#FFFFFF",
        "text": "#333333",
        "accent": "#1976D2",
        "muted": "#BDBDBD",
    })
    planet_colors: dict[str, str] = field(default_factory=lambda: {
        "sun": "#FF5722", "moon": "#607D8B", "mars": "#f44336",
        "mercury": "#4CAF50", "jupiter": "#FFC107", "venus": "#E91E63",
        "saturn": "#3F51B5", "rahu": "#9C27B0", "ketu": "#795548",
    })
    rashi_colors: dict[str, str] = field(default_factory=lambda: {
        "aries": "#E91E63", "taurus": "#4CAF50", "gemini": "#FFC107",
        "cancer": "#607D8B", "leo": "#FF5722", "virgo": "#8BC34A",
        "libra": "#9C27B0", "scorpio": "#f44336", "sagittarius": "#FF9800",
        "capricorn": "#3F51B5", "aquarius": "#00BCD4", "pisces": "#E040FB",
    })
    font_family: str = "sans-serif"
    node_size: int = 40
    edge_width: float = 1.5


@dataclass(frozen=True)
class VisualizationNode:
    """A single node in a graph or chart."""

    id: str
    label: str
    group: str  # "planet" | "rashi" | "house" | "yoga" | "event" | "dasha"
    x: float = 0.0
    y: float = 0.0
    radius: float = 40.0
    color: str = "#999999"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VisualizationEdge:
    """A connection between two nodes."""

    source_id: str
    target_id: str
    label: str = ""
    edge_type: str = "default"
    weight: float = 1.0
    color: str = "#cccccc"
    dashed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VisualizationLayout:
    """Positioned nodes and edges forming a visual layout."""

    type: str  # "wheel" | "force" | "grid" | "timeline" | "radial"
    width: int = 800
    height: int = 600
    nodes: tuple[VisualizationNode, ...] = field(default_factory=tuple)
    edges: tuple[VisualizationEdge, ...] = field(default_factory=tuple)
    viewport: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class SeriesData:
    """A data series for bar/line charts."""

    label: str
    values: tuple[float, ...]
    labels: tuple[str, ...]
    color: str = "#999999"


@dataclass(frozen=True)
class VisualizationRequest:
    """What to visualize and how."""

    visualization_type: str
    source_data: dict[str, Any] = field(default_factory=dict)
    theme_name: str = "light"
    width: int = 800
    height: int = 600
    options: dict[str, Any] = field(default_factory=dict)

    @property
    def theme(self) -> VisualizationTheme:
        return _THEMES.get(self.theme_name, _THEMES["light"])


@dataclass(frozen=True)
class VisualizationResult:
    """Output of a visualization operation — JSON-serializable."""

    visualization_type: str
    renderer: str  # "chart_visualizer" | "timeline_visualizer" | "statistics_visualizer" | "research_visualizer"
    version: str
    theme: str  # theme name
    data: dict[str, Any]  # the visual data (layout + series)
    metadata: dict[str, Any]
    generated_at: str  # ISO datetime


# Built-in themes.
_THEMES: dict[str, VisualizationTheme] = {
    "light": VisualizationTheme(),
}


def get_theme(name: str = "light") -> VisualizationTheme:
    return _THEMES.get(name, _THEMES["light"])

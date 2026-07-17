"""
AstroOS — Visualization Engine (Module 22, Phase 1)

Transforms existing domain objects into presentation-ready data structures
for frontend rendering (D3.js, Cytoscape.js). Presentation-only — no
calculations, no DB access, no astrology.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.timeline import Timeline
from apps.api.domain.statistics import Distribution, Crosstab
from apps.api.domain.research import AstrologicalSnapshot
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

_ENGINE_VERSION = "1.0"
_RASHI_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# D3 Adapter
# ═══════════════════════════════════════════════════════════════════════════════


class D3Adapter:
    """Converts VisualizationResult to D3.js-friendly format."""

    @staticmethod
    def adapt(result: VisualizationResult) -> dict[str, Any]:
        return {
            "visualization_type": result.visualization_type,
            "renderer": result.renderer,
            "version": result.version,
            "theme": result.theme,
            "data": result.data,
            "metadata": result.metadata,
            "d3": {
                "nodes": result.data.get("layout", {}).get("nodes", []),
                "edges": result.data.get("layout", {}).get("edges", []),
                "series": result.data.get("series", []),
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Cytoscape Adapter
# ═══════════════════════════════════════════════════════════════════════════════


class CytoscapeAdapter:
    """Converts VisualizationResult to Cytoscape.js-friendly format."""

    @staticmethod
    def adapt(result: VisualizationResult) -> dict[str, Any]:
        layout_data = result.data.get("layout", {})
        nodes = layout_data.get("nodes", [])
        edges = layout_data.get("edges", [])

        elements: list[dict[str, Any]] = []
        for n in nodes:
            elements.append({
                "data": {"id": n["id"], "label": n["label"], "group": n["group"]},
                "position": {"x": n.get("x", 0), "y": n.get("y", 0)},
            })
        for e in edges:
            elements.append({
                "data": {
                    "id": f"{e['source_id']}-{e['target_id']}",
                    "source": e["source_id"],
                    "target": e["target_id"],
                    "label": e.get("label", ""),
                },
            })

        layout_type = layout_data.get("type", "force")
        cy_layout = {"name": "cose"} if layout_type == "force" else {"name": "concentric"}

        return {
            "visualization_type": result.visualization_type,
            "renderer": result.renderer,
            "version": result.version,
            "theme": result.theme,
            "data": result.data,
            "metadata": result.metadata,
            "cytoscape": {
                "elements": elements,
                "layout": cy_layout,
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Chart Visualizer
# ═══════════════════════════════════════════════════════════════════════════════


class ChartVisualizer:
    """Renders a D1Chart into a circular chart-wheel layout."""

    @staticmethod
    def render(
        chart: D1Chart,
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        cx, cy = width // 2, height // 2
        outer_r = min(cx, cy) - 60
        inner_r = outer_r - 80

        nodes: list[VisualizationNode] = []
        edges: list[VisualizationEdge] = []

        # House segments: place a node at the midpoint of each 30° arc.
        for house_num in range(1, 13):
            angle_deg = (house_num - 1) * 30 + 15  # midpoint of the house
            angle_rad = math.radians(angle_deg - 90)
            nx = cx + inner_r * math.cos(angle_rad)
            ny = cy + inner_r * math.sin(angle_rad)
            rashi = _RASHI_NAMES[house_num - 1] if house_num <= 12 else ""
            color = theme.rashi_colors.get(rashi, theme.colors["neutral"])
            nodes.append(VisualizationNode(
                id=f"house_{house_num}",
                label=f"H{house_num}",
                group="house",
                x=nx, y=ny,
                radius=24,
                color=color,
                metadata={"house_number": house_num, "rashi": rashi},
            ))

        # Planets: position at their rashi degree.
        for p in chart.planets:
            rashi_idx = _RASHI_NAMES.index(p.rashi) if p.rashi in _RASHI_NAMES else 0
            angle_deg = rashi_idx * 30 + p.rashi_degree
            angle_rad = math.radians(angle_deg - 90)
            px = cx + outer_r * math.cos(angle_rad)
            py = cy + outer_r * math.sin(angle_rad)
            color = theme.planet_colors.get(p.planet, theme.colors["neutral"])
            nodes.append(VisualizationNode(
                id=f"planet_{p.planet}",
                label=p.planet.capitalize(),
                group="planet",
                x=px, y=py,
                radius=36,
                color=color,
                metadata={
                    "planet": p.planet,
                    "rashi": p.rashi,
                    "house": p.house_number,
                    "dignity": p.dignity.value if p.dignity else None,
                    "retrograde": p.is_retrograde,
                },
            ))

        # Ascendant marker.
        if chart.ascendant:
            angle_rad = math.radians(-90)
            ax = cx + outer_r * math.cos(angle_rad)
            ay = cy + outer_r * math.sin(angle_rad)
            nodes.append(VisualizationNode(
                id="lagna",
                label="Lagna",
                group="rashi",
                x=ax, y=ay,
                radius=20,
                color=theme.colors["accent"],
                metadata={"rashi": chart.ascendant.rashi, "degree": chart.ascendant.rashi_degree},
            ))

        # Aspects as edges.
        for a in chart.aspects:
            edges.append(VisualizationEdge(
                source_id=f"planet_{a.from_planet}",
                target_id=f"planet_{a.to_planet}",
                label=a.aspect_type,
                edge_type="aspect",
                weight=max(0.5, 2.0 - a.orb_degrees / 5),
                color=theme.colors["muted"],
                metadata={"aspect_type": a.aspect_type, "orb": a.orb_degrees},
            ))

        layout = VisualizationLayout(
            type="wheel", width=width, height=height,
            nodes=tuple(nodes), edges=tuple(edges),
            viewport={"cx": cx, "cy": cy, "scale": 1.0},
        )

        return VisualizationResult(
            visualization_type="chart_wheel",
            renderer="chart_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={"layout": {
                "type": layout.type,
                "width": layout.width,
                "height": layout.height,
                "nodes": [_node_dict(n) for n in layout.nodes],
                "edges": [_edge_dict(e) for e in layout.edges],
                "viewport": layout.viewport,
            }},
            metadata={"planet_count": len(chart.planets), "house_count": 12},
            generated_at=_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Timeline Visualizer
# ═══════════════════════════════════════════════════════════════════════════════


class TimelineVisualizer:
    """Renders a Timeline into a chronological strip."""

    @staticmethod
    def render(
        timeline: Timeline,
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        nodes: list[VisualizationNode] = []
        edges: list[VisualizationEdge] = []

        if not timeline.entries:
            return VisualizationResult(
                visualization_type="timeline",
                renderer="timeline_visualizer",
                version=_ENGINE_VERSION,
                theme=theme.name,
                data={"layout": {"type": "timeline", "width": width, "height": height, "nodes": [], "edges": []}},
                metadata={"total_events": 0},
                generated_at=_now_iso(),
            )

        earliest = timeline.date_range[0]
        latest = timeline.date_range[1]
        total_days = (latest - earliest).days or 1
        margin = 60
        plot_w = width - 2 * margin

        # Event nodes positioned chronologically.
        for i, entry in enumerate(timeline.entries):
            days_from_start = (entry.event_date - earliest).days
            ex = margin + (days_from_start / total_days) * plot_w
            ey = height // 2 + (30 if i % 2 == 0 else -30)
            color = theme.colors["accent"] if entry.is_verified else theme.colors["neutral"]
            nodes.append(VisualizationNode(
                id=f"event_{entry.event_id}",
                label=entry.title,
                group="event",
                x=ex, y=ey,
                radius=12,
                color=color,
                metadata={
                    "date": entry.event_date.isoformat(),
                    "category": entry.category,
                    "verified": entry.is_verified,
                },
            ))

        # Density series.
        density = _compute_density(timeline)

        return VisualizationResult(
            visualization_type="timeline",
            renderer="timeline_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={
                "layout": {
                    "type": "timeline",
                    "width": width,
                    "height": height,
                    "nodes": [_node_dict(n) for n in nodes],
                    "edges": [_edge_dict(e) for e in edges],
                },
                "series": [{
                    "label": "Event Density",
                    "values": [d for _, d in density],
                    "labels": [d.isoformat() for d, _ in density],
                    "color": theme.colors["accent"],
                }],
            },
            metadata={
                "total_events": timeline.total_events,
                "date_range": [timeline.date_range[0].isoformat(), timeline.date_range[1].isoformat()],
                "categories": timeline.summary.events_per_category,
            },
            generated_at=_now_iso(),
        )


def _compute_density(
    timeline: Timeline,
    window_days: int = 365,
) -> list[tuple[Any, float]]:
    """Compute event density at each event date."""
    dates = [e.event_date for e in timeline.entries]
    n = len(dates)
    if n == 0:
        return []
    result: list[tuple[Any, float]] = []
    left = 0
    for right in range(n):
        while left < right and (dates[right] - dates[left]).days > window_days:
            left += 1
        count = right - left + 1
        density = (count / window_days) * 365.25
        result.append((dates[right], density))

    right = 0
    for left in range(n):
        while right < n and (dates[right] - dates[left]).days <= window_days:
            right += 1
        count = right - left
        density = (count / window_days) * 365.25
        if result:
            prev_density = result[left][1]
            result[left] = (dates[left], max(prev_density, density))

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics Visualizer
# ═══════════════════════════════════════════════════════════════════════════════


class StatisticsVisualizer:
    """Renders Distribution and Crosstab objects into bar/heatmap data."""

    @staticmethod
    def render_distribution(
        distribution: Distribution,
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        series = SeriesData(
            label=distribution.label,
            values=tuple(float(c) for c in distribution.counts),
            labels=distribution.bins,
            color=theme.colors["accent"],
        )
        return VisualizationResult(
            visualization_type="distribution",
            renderer="statistics_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={
                "series": [{
                    "label": series.label,
                    "values": list(series.values),
                    "labels": list(series.labels),
                    "color": series.color,
                }],
            },
            metadata={
                "variable": distribution.variable,
                "total": distribution.total,
                "bin_count": len(distribution.bins),
            },
            generated_at=_now_iso(),
        )

    @staticmethod
    def render_crosstab(
        crosstab: Crosstab,
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        return VisualizationResult(
            visualization_type="crosstab",
            renderer="statistics_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={
                "heatmap": {
                    "row_labels": list(crosstab.row_labels),
                    "column_labels": list(crosstab.column_labels),
                    "cells": [list(row) for row in crosstab.cells],
                    "row_totals": list(crosstab.row_totals),
                },
            },
            metadata={
                "row_variable": crosstab.row_variable,
                "column_variable": crosstab.column_variable,
                "rows": len(crosstab.row_labels),
                "columns": len(crosstab.column_labels),
            },
            generated_at=_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Research Visualizer
# ═══════════════════════════════════════════════════════════════════════════════


class ResearchVisualizer:
    """Renders AstrologicalSnapshot collections into comparison views."""

    @staticmethod
    def render_comparison(
        snapshots: tuple[AstrologicalSnapshot, ...],
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        if not snapshots:
            return VisualizationResult(
                visualization_type="snapshot_comparison",
                renderer="research_visualizer",
                version=_ENGINE_VERSION,
                theme=theme.name,
                data={"grid": {"rows": [], "columns": [], "cells": []}},
                metadata={"snapshot_count": 0},
                generated_at=_now_iso(),
            )

        # Build a grid: rows = snapshots, columns = planet house positions.
        planets_order = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        rows = []
        for snap in snapshots:
            row: dict[str, Any] = {"label": snap.label or "Unnamed", "chart_id": str(snap.chart_id)}
            planet_data: dict[str, int] = {}
            if snap.chart_ref:
                for p in snap.chart_ref.planets:
                    if p.planet in planets_order:
                        planet_data[p.planet] = p.house_number
            row["planets"] = planet_data
            rows.append(row)

        return VisualizationResult(
            visualization_type="snapshot_comparison",
            renderer="research_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={
                "grid": {
                    "rows": rows,
                    "columns": planets_order,
                    "snapshot_count": len(snapshots),
                },
            },
            metadata={"snapshot_count": len(snapshots)},
            generated_at=_now_iso(),
        )

    @staticmethod
    def render_graph(
        snapshots: tuple[AstrologicalSnapshot, ...],
        theme: VisualizationTheme,
        width: int = 800,
        height: int = 600,
    ) -> VisualizationResult:
        """Build a Cytoscape.js-compatible relationship graph."""
        nodes: list[VisualizationNode] = []
        edges: list[VisualizationEdge] = []

        for snap in snapshots:
            if not snap.chart_ref:
                continue
            chart = snap.chart_ref

            # Planet nodes.
            for p in chart.planets:
                pid = f"{snap.chart_id}_{p.planet}"
                color = theme.planet_colors.get(p.planet, theme.colors["neutral"])
                nodes.append(VisualizationNode(
                    id=pid, label=p.planet.capitalize(),
                    group="planet", color=color,
                    metadata={"planet": p.planet, "rashi": p.rashi, "house": p.house_number},
                ))

            # Rashi nodes for unique rashis.
            seen_rashis: set[str] = set()
            for p in chart.planets:
                if p.rashi and p.rashi not in seen_rashis:
                    seen_rashis.add(p.rashi)
                    rid = f"{snap.chart_id}_rashi_{p.rashi}"
                    color = theme.rashi_colors.get(p.rashi, theme.colors["neutral"])
                    nodes.append(VisualizationNode(
                        id=rid, label=p.rashi.capitalize(),
                        group="rashi", color=color,
                        metadata={"rashi": p.rashi},
                    ))

            # Planet-in-rashi edges.
            for p in chart.planets:
                if p.rashi:
                    edges.append(VisualizationEdge(
                        source_id=f"{snap.chart_id}_{p.planet}",
                        target_id=f"{snap.chart_id}_rashi_{p.rashi}",
                        label="in",
                        edge_type="placement",
                        color=theme.colors["muted"],
                    ))

        # De-duplicate nodes with same id.
        seen_ids: set[str] = set()
        unique_nodes: list[VisualizationNode] = []
        for n in nodes:
            if n.id not in seen_ids:
                seen_ids.add(n.id)
                unique_nodes.append(n)

        return VisualizationResult(
            visualization_type="relationship_graph",
            renderer="research_visualizer",
            version=_ENGINE_VERSION,
            theme=theme.name,
            data={
                "layout": {
                    "type": "force",
                    "width": width,
                    "height": height,
                    "nodes": [_node_dict(n) for n in unique_nodes],
                    "edges": [_edge_dict(e) for e in edges],
                },
            },
            metadata={"node_count": len(unique_nodes), "edge_count": len(edges)},
            generated_at=_now_iso(),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Serialization helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _node_dict(n: VisualizationNode) -> dict[str, Any]:
    return {
        "id": n.id, "label": n.label, "group": n.group,
        "x": n.x, "y": n.y, "radius": n.radius, "color": n.color,
        "metadata": n.metadata,
    }


def _edge_dict(e: VisualizationEdge) -> dict[str, Any]:
    return {
        "source_id": e.source_id, "target_id": e.target_id,
        "label": e.label, "edge_type": e.edge_type,
        "weight": e.weight, "color": e.color, "dashed": e.dashed,
        "metadata": e.metadata,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Visualization Engine
# ═══════════════════════════════════════════════════════════════════════════════


class VisualizationEngine:
    """Dispatches visualization requests to the correct visualizer."""

    _ENGINE_VERSION = _ENGINE_VERSION

    @staticmethod
    def available_visualizations() -> list[dict[str, Any]]:
        """Return metadata about all supported visualization types."""
        return [
            {
                "type": "chart_wheel",
                "renderer": "chart_visualizer",
                "description": "Circular chart wheel with houses, planets, and aspects",
                "required_source": ["chart"],
                "adapter": "d3",
            },
            {
                "type": "timeline",
                "renderer": "timeline_visualizer",
                "description": "Chronological event strip with density overlay",
                "required_source": ["timeline"],
                "adapter": "d3",
            },
            {
                "type": "distribution",
                "renderer": "statistics_visualizer",
                "description": "Bar chart for frequency distributions",
                "required_source": ["distribution"],
                "adapter": "d3",
            },
            {
                "type": "crosstab",
                "renderer": "statistics_visualizer",
                "description": "Heatmap for contingency tables",
                "required_source": ["crosstab"],
                "adapter": "d3",
            },
            {
                "type": "snapshot_comparison",
                "renderer": "research_visualizer",
                "description": "Grid comparison of astrological snapshots",
                "required_source": ["snapshots"],
                "adapter": "d3",
            },
            {
                "type": "relationship_graph",
                "renderer": "research_visualizer",
                "description": "Force-directed graph of astrological relationships",
                "required_source": ["snapshots"],
                "adapter": "cytoscape",
            },
        ]

    @staticmethod
    def visualize(request: VisualizationRequest) -> VisualizationResult:
        """Dispatch to the correct visualizer based on request type."""
        theme = get_theme(request.theme_name)

        if request.visualization_type == "chart_wheel":
            chart = request.source_data.get("chart")
            if not chart:
                raise ValueError("chart_wheel requires source_data['chart']")
            return ChartVisualizer.render(chart, theme, request.width, request.height)

        elif request.visualization_type == "timeline":
            timeline = request.source_data.get("timeline")
            if not timeline:
                raise ValueError("timeline requires source_data['timeline']")
            return TimelineVisualizer.render(timeline, theme, request.width, request.height)

        elif request.visualization_type == "distribution":
            dist = request.source_data.get("distribution")
            if not dist:
                raise ValueError("distribution requires source_data['distribution']")
            return StatisticsVisualizer.render_distribution(dist, theme, request.width, request.height)

        elif request.visualization_type == "crosstab":
            ct = request.source_data.get("crosstab")
            if not ct:
                raise ValueError("crosstab requires source_data['crosstab']")
            return StatisticsVisualizer.render_crosstab(ct, theme, request.width, request.height)

        elif request.visualization_type == "snapshot_comparison":
            snaps = request.source_data.get("snapshots", ())
            return ResearchVisualizer.render_comparison(tuple(snaps), theme, request.width, request.height)

        elif request.visualization_type == "relationship_graph":
            snaps = request.source_data.get("snapshots", ())
            return ResearchVisualizer.render_graph(tuple(snaps), theme, request.width, request.height)

        else:
            raise ValueError(f"Unknown visualization type: {request.visualization_type}")

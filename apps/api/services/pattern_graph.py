"""
AstroOS — Pattern Co-occurrence Network Graph (Module 27, Phase 3c)

Feeds apps/web/src/components/ui/KnowledgeGraph.tsx, which has no
force-directed layout of its own — every node needs an explicit x/y from
the caller. This module computes a simple, deterministic radial layout
instead of running a real simulation: dimension-values are grouped into
concentric rings by category (dasha, yoga, transit, shadbala, house, varga,
nakshatra), evenly spaced by angle within their ring. No collision physics,
no iterative relaxation — just trigonometry, which is enough to render a
readable, non-overlapping graph for the pattern counts this dataset
produces.

Pure computation over already-persisted pattern rows — no DB access here,
consistent with pattern_discovery.py's "engine has no DB access, router
owns reads" discipline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_RING_SPACING = 90.0
_CENTER = 260.0
_MIN_NODE_RADIUS = 10.0
_MAX_NODE_RADIUS = 28.0

# Ring order (innermost first) — arbitrary but stable, so repeated calls
# over the same data produce the same layout.
_CATEGORY_ORDER = ("dasha", "yoga", "house", "transit", "shadbala", "varga", "nakshatra", "other")


@dataclass(frozen=True)
class PatternGraphInput:
    """One persisted pattern's minimal shape needed to build the graph."""

    pattern_id: str
    dimensions: list[tuple[str, str]]  # (dimension, value) pairs


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    x: float
    y: float
    size: float
    category: str


@dataclass(frozen=True)
class GraphEdge:
    from_: str
    to: str


def infer_category(dimension: str) -> str:
    lower = dimension.lower()
    for category in _CATEGORY_ORDER[:-1]:  # "other" is the fallback, not a prefix to check
        if lower.startswith(category) or lower.startswith("active " + category):
            return category
    return "other"


def build_network_graph(
    patterns: list[PatternGraphInput],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """One node per distinct (category, dimension, value) across all given
    patterns, grouped into concentric rings by category; edges connect
    dimension-values that co-occur within the same pattern.
    """
    node_keys: dict[str, tuple[str, str, str]] = {}  # node_id -> (category, dimension, value)
    node_counts: dict[str, int] = {}
    edges: set[tuple[str, str]] = set()

    for pattern in patterns:
        ids_in_pattern: list[str] = []
        for dimension, value in pattern.dimensions:
            category = infer_category(dimension)
            node_id = f"{category}:{dimension}={value}"
            node_keys[node_id] = (category, dimension, value)
            node_counts[node_id] = node_counts.get(node_id, 0) + 1
            ids_in_pattern.append(node_id)
        for i in range(len(ids_in_pattern)):
            for j in range(i + 1, len(ids_in_pattern)):
                a, b = sorted((ids_in_pattern[i], ids_in_pattern[j]))
                edges.add((a, b))

    by_category: dict[str, list[str]] = {}
    for node_id, (category, _dimension, _value) in node_keys.items():
        by_category.setdefault(category, []).append(node_id)

    max_count = max(node_counts.values(), default=1)
    nodes: list[GraphNode] = []
    for ring_index, category in enumerate(_CATEGORY_ORDER):
        ids_in_ring = sorted(by_category.get(category, []))
        if not ids_in_ring:
            continue
        radius = _RING_SPACING * (ring_index + 1)
        for i, node_id in enumerate(ids_in_ring):
            angle = (2 * math.pi * i) / len(ids_in_ring)
            _category, dimension, value = node_keys[node_id]
            count = node_counts[node_id]
            size = _MIN_NODE_RADIUS + (_MAX_NODE_RADIUS - _MIN_NODE_RADIUS) * (count / max_count)
            nodes.append(
                GraphNode(
                    id=node_id,
                    label=f"{dimension}={value}",
                    x=round(_CENTER + radius * math.cos(angle), 1),
                    y=round(_CENTER + radius * math.sin(angle), 1),
                    size=round(size, 1),
                    category=category,
                )
            )

    graph_edges = [GraphEdge(from_=a, to=b) for a, b in sorted(edges)]
    return nodes, graph_edges

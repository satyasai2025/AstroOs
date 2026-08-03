"""
Unit tests for apps/api/services/pattern_graph.py (Module 27, Phase 3c) —
the radial network-graph layout feeding the Pattern Network visualisation.

Pure computation — no DB.
"""

from __future__ import annotations

import math

from apps.api.services.pattern_graph import PatternGraphInput, build_network_graph, infer_category


def test_infer_category_prefixes():
    assert infer_category("dasha_mahadasha") == "dasha"
    assert infer_category("transit_Ju_Makara") == "transit"
    assert infer_category("shadbala_Ve") == "shadbala"
    assert infer_category("house_7L") == "house"
    assert infer_category("varga_D9_Venus") == "varga"
    assert infer_category("nakshatra activation_Purva Phalguni") == "nakshatra"
    assert infer_category("active yoga_Gajakesari") == "yoga"
    assert infer_category("something_unrecognised") == "other"


def test_build_network_graph_node_and_edge_counts():
    patterns = [
        PatternGraphInput(pattern_id="ptn-1", dimensions=[("dasha_mahadasha", "Ju"), ("house_7L", "strong")]),
        PatternGraphInput(pattern_id="ptn-2", dimensions=[("dasha_mahadasha", "Ju")]),
    ]
    nodes, edges = build_network_graph(patterns)

    # Two distinct (dimension, value) pairs across both patterns -> two nodes.
    assert len(nodes) == 2
    node_ids = {n.id for n in nodes}
    assert any("dasha_mahadasha=Ju" in nid for nid in node_ids)
    assert any("house_7L=strong" in nid for nid in node_ids)

    # Only ptn-1 co-occurs two dimensions -> exactly one edge.
    assert len(edges) == 1

    # Repeated dasha_mahadasha=Ju node should be sized larger (count=2) than
    # the house node (count=1).
    ju_node = next(n for n in nodes if "dasha_mahadasha=Ju" in n.id)
    house_node = next(n for n in nodes if "house_7L=strong" in n.id)
    assert ju_node.size >= house_node.size


def test_build_network_graph_nodes_are_non_overlapping_within_a_ring():
    # Five distinct dasha values should be spread evenly around one ring —
    # no two nodes should land on the same (x, y).
    patterns = [
        PatternGraphInput(pattern_id=f"ptn-{i}", dimensions=[("dasha_mahadasha", f"P{i}")])
        for i in range(5)
    ]
    nodes, _edges = build_network_graph(patterns)
    assert len(nodes) == 5

    coordinates = [(n.x, n.y) for n in nodes]
    assert len(set(coordinates)) == len(coordinates), "expected distinct coordinates for every node"

    center = 260.0
    for n in nodes:
        radius = math.hypot(n.x - center, n.y - center)
        assert radius > 0


def test_build_network_graph_empty_input():
    nodes, edges = build_network_graph([])
    assert nodes == []
    assert edges == []

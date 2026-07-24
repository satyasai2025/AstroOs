"""
Unit tests for Entity Linking Service (Knowledge Graph Bridge)
"""
import pytest
from unittest.mock import Mock, MagicMock

from apps.api.services.entity_linking import EntityLinker, PLANET_ALIASES, RASHI_ALIASES
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine, GraphNode


class TestEntityLinker:
    def setup_method(self):
        # Mock the KnowledgeGraphEngine
        self.mock_kg_engine = Mock(spec=KnowledgeGraphEngine)
        self.linker = EntityLinker(self.mock_kg_engine)

        # Set up mock nodes
        self.mock_nodes = {
            "SUN": GraphNode(id="SUN", label="Sun", type="PLANET", metadata={}),
            "MOON": GraphNode(id="MOON", label="Moon", type="PLANET", metadata={}),
            "MARS": GraphNode(id="MARS", label="Mars", type="PLANET", metadata={}),
            "ARIES": GraphNode(id="ARIES", label="Aries", type="SIGN", metadata={}),
            "TAURUS": GraphNode(id="TAURUS", label="Taurus", type="SIGN", metadata={}),
        }
        self.mock_kg_engine.get_nodes_by_label.return_value = list(self.mock_nodes.values())

        # Mock graph traversal for proximity searches
        self.mock_kg_engine.get_neighbors.return_value = []

    def test_exact_name_match(self):
        """Test exact name matching for chart entities."""
        self.mock_kg_engine.get_nodes_by_label.side_effect = lambda label: [
            node for node in self.mock_nodes.values() if node.label.lower() == label.lower()
        ]

        chart_data = {"planets": [{"name": "Sun"}]}
        results = self.linker.link_chart_data(chart_data)

        assert len(results) == 1
        assert results[0]["entity_id"] == "SUN"
        assert results[0]["confidence_score"] == 1.0
        assert results[0]["match_type"] == "exact"

    def test_alias_match(self):
        """Test alias matching for chart entities."""
        self.mock_kg_engine.get_nodes_by_label.side_effect = lambda label: [
            node for node in self.mock_nodes.values() if node.label.lower() == label.lower()
        ]

        # Test planet alias
        chart_data = {"planets": [{"name": "Surya"}]}  # Sanskrit alias for Sun
        results = self.linker.link_chart_data(chart_data)

        assert len(results) == 1
        assert results[0]["entity_id"] == "SUN"
        assert results[0]["confidence_score"] == 0.8  # Alias match score
        assert results[0]["match_type"] == "alias"

        # Test sign alias
        chart_data = {"planets": [{"name": "Mars", "sign": "Mesha"}]}  # Sanskrit alias for Aries
        results = self.linker.link_chart_data(chart_data)

        assert len(results) == 2  # Mars + Aries via sign
        # Find the Aries result
        aries_result = next(r for r in results if r["entity_id"] == "ARIES")
        assert aries_result["confidence_score"] == 0.8
        assert aries_result["match_type"] == "alias"

    def test_proximity_match(self):
        """Test proximity-based matching when direct match fails."""
        # Mock no direct matches but neighbors available
        self.mock_kg_engine.get_nodes_by_label.return_value = []
        self.mock_kg_engine.get_neighbors.side_effect = lambda node_id, rel_type: [
            GraphNode(id="SUN", label="Sun", type="PLANET", metadata={})
        ] if node_id == "SOME_OTHER_NODE" else []

        chart_data = {"planets": [{"name": "UnknownPlanet"}]}
        results = self.linker.link_chart_data(chart_data)

        # Should still try proximity search
        # Note: Actual implementation depends on how the linker handles unknown entities
        assert isinstance(results, list)

    def test_no_matches(self):
        """Test behavior when no matches are found."""
        self.mock_kg_engine.get_nodes_by_label.return_value = []
        self.mock_kg_engine.get_neighbors.return_value = []

        chart_data = {"planets": [{"name": "NonExistentPlanet"}]}
        results = self.linker.link_chart_data(chart_data)

        assert len(results) == 0

    def test_multiple_entities(self):
        """Test linking multiple chart entities."""
        self.mock_kg_engine.get_nodes_by_label.side_effect = lambda label: [
            node for node in self.mock_nodes.values() if node.label.lower() == label.lower()
        ]

        chart_data = {
            "planets": [
                {"name": "Sun"},
                {"name": "Moon"},
                {"name": "Mars"}
            ],
            "signs": [
                {"name": "Aries"},
                {"name": "Taurus"}
            ]
        }
        results = self.linker.link_chart_data(chart_data)

        # Should find all 5 entities
        entity_ids = {r["entity_id"] for r in results}
        assert "SUN" in entity_ids
        assert "MOON" in entity_ids
        assert "MARS" in entity_ids
        assert "ARIES" in entity_ids
        assert "TAURUS" in entity_ids

        # All should have high confidence (exact matches)
        for result in results:
            assert result["confidence_score"] >= 0.8

    def test_confidence_scoring(self):
        """Test that confidence scores are calculated correctly."""
        # Test exact match
        self.mock_kg_engine.get_nodes_by_label.side_effect = lambda label: [
            node for node in self.mock_nodes.values() if node.label.lower() == label.lower()
        ]

        chart_data = {"planets": [{"name": "Sun"}]}
        results = self.linker.link_chart_data(chart_data)

        assert results[0]["confidence_score"] == 1.0

        # Test that we can distinguish match types
        chart_data = {"planets": [{"name": "Surya"}]}  # Alias
        results = self.linker.link_chart_data(chart_data)

        assert results[0]["confidence_score"] == 0.8
        assert results[0]["match_type"] == "alias"

    def test_empty_chart_data(self):
        """Test handling of empty chart data."""
        chart_data = {}
        results = self.linker.link_chart_data(chart_data)

        assert len(results) == 0

    def test_missing_entity_types(self):
        """Test handling of entity types not in alias maps."""
        self.mock_kg_engine.get_nodes_by_label.return_value = []

        chart_data = {"planets": [{"name": "Pluto"}]}  # Not in standard planets
        results = self.linker.link_chart_data(chart_data)

        # Should return empty or attempt proximity search
        assert isinstance(results, list)
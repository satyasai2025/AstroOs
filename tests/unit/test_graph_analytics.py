"""
Unit tests for Graph Analytics Service (Knowledge Graph Bridge)
"""
import pytest
from unittest.mock import Mock, MagicMock
from collections import Counter

from apps.api.services.graph_analytics import GraphAnalytics, EntityCorrelation, EntityFrequency
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
from apps.api.services.analytics_engine import StatisticalEngine, CohortQuery, FilterClause


class TestGraphAnalytics:
    def setup_method(self):
        # Mock the KnowledgeGraphEngine
        self.mock_kg_engine = Mock(spec=KnowledgeGraphEngine)
        self.graph_analytics = GraphAnalytics(self.mock_kg_engine)

    def test_entity_frequency_basic(self):
        """Test basic entity frequency calculation."""
        # Create mock dataset
        dataset = [
            {"entity_id": "SUN", "outcome": 10},
            {"entity_id": "MOON", "outcome": 15},
            {"entity_id": "SUN", "outcome": 20},
            {"entity_id": "MARS", "outcome": 5},
        ]

        frequencies = self.graph_analytics.entity_frequency(
            dataset=dataset,
            entity_field="entity_id"
        )

        assert isinstance(frequencies, list)
        assert len(frequencies) == 3

        # Check SUN frequency
        sun_freq = next(f for f in frequencies if f.entity_id == "SUN")
        assert sun_freq.count == 2
        assert sun_freq.proportion == 0.5

        # Check MOON frequency
        moon_freq = next(f for f in frequencies if f.entity_id == "MOON")
        assert moon_freq.count == 1
        assert moon_freq.proportion == 0.2

        # Check MARS frequency
        mars_freq = next(f for f in frequencies if f.entity_id == "MARS")
        assert mars_freq.count == 1
        assert mars_freq.proportion == 0.2

    def test_entity_frequency_empty_dataset(self):
        """Test entity frequency with empty dataset."""
        frequencies = self.graph_analytics.entity_frequency(
            dataset=[],
            entity_field="entity_id"
        )
        assert frequencies == []

    def test_entity_frequency_single_entity(self):
        """Test entity frequency with single entity type."""
        dataset = [
            {"entity_id": "SUN", "value": 10},
            {"entity_id": "SUN", "value": 20},
        ]

        frequencies = self.graph_analytics.entity_frequency(
            dataset=dataset,
            entity_column="entity_id"
        )

        assert len(frequencies) == 1
        assert frequencies[0].entity_id == "SUN"
        assert frequencies[0].count == 2
        assert frequencies[0].proportion == 1.0

    def test_correlate_entity_with_dataset(self):
        """Test correlation between entity presence and numeric field."""
        dataset = [
            {"entity_id": "SUN", "outcome": 10},
            {"entity_id": "MOON", "outcome": 15},
            {"entity_id": "SUN", "outcome": 20},
            {"entity_id": "MARS", "outcome": 5},
            {"entity_id": "SUN", "outcome": 12},
            {"entity_id": "MOON", "outcome": 18},
            {"entity_id": "MARS", "outcome": 8},
        ]

        correlation = self.graph_analytics.correlate_entity_with_dataset(
            dataset=dataset,
            entity_id="SUN",
            entity_column="entity_id",
            numeric_field="outcome"
        )

        assert isinstance(correlation, EntityCorrelation)
        assert correlation.entity_id == "SUN"
        assert correlation.field_x == "entity_id"
        assert correlation.field_y == "outcome"
        assert correlation.present_count == 3
        assert correlation.absent_count == 4

        # Present group mean: (10 + 20 + 12) / 3 = 14.0
        assert abs(correlation.present_mean - 14.0) < 0.01
        # Absent group mean: (15 + 5 + 18 + 8) / 4 = 11.5
        assert abs(correlation.absent_mean - 11.5) < 0.01

        # Effect size should be calculated
        assert isinstance(correlation.effect_size, float)
        assert correlation.effect_size >= 0

    def test_correlate_entity_not_in_dataset(self):
        """Test correlation when entity not present in dataset."""
        dataset = [
            {"entity_id": "MOON", "outcome": 15},
            {"entity_id": "MARS", "outcome": 5},
        ]

        correlation = self.graph_analytics.correlate_entity_with_dataset(
            dataset=dataset,
            entity_id="SUN",  # Not in dataset
            entity_column="entity_id",
            numeric_field="outcome"
        )

        assert correlation.present_count == 0
        assert correlation.absent_count == 2

    def test_correlate_entity_numeric_field_missing(self):
        """Test correlation with missing numeric field."""
        dataset = [
            {"entity_id": "SUN"},
            {"entity_id": "MOON"},
        ]

        correlation = self.graph_analytics.correlate_entity_with_dataset(
            dataset=dataset,
            entity_id="SUN",
            entity_column="entity_id",
            numeric_field="missing_field"
        )

        # Should handle gracefully
        assert correlation.absent_count + correlation.present_count == 2

    def test_correlation_interpretation(self):
        """Test that interpretation text is generated."""
        dataset = [
            {"entity_id": "SUN", "outcome": 10},
            {"entity_id": "SUN", "outcome": 12},
            {"entity_id": "MOON", "outcome": 15},
            {"entity_id": "MOON", "outcome": 18},
        ]

        correlation = self.graph_analytics.correlate_entity_with_dataset(
            dataset=dataset,
            entity_id="SUN",
            entity_column="entity_id",
            numeric_field="outcome"
        )

        assert isinstance(correlation.interpretation, str)
        assert len(correlation.interpretation) > 0

    def test_entity_frequency_with_different_column_name(self):
        """Test entity frequency with custom column name."""
        dataset = [
            {"planet": "SUN", "score": 10},
            {"planet": "MOON", "score": 15},
            {"planet": "SUN", "score": 20},
        ]

        frequencies = self.graph_analytics.entity_frequency(
            dataset=dataset,
            entity_column="planet"
        )

        assert len(frequencies) == 2
        sun_freq = next(f for f in frequencies if f.entity_id == "SUN")
        assert sun_freq.count == 2
        assert sun_freq.proportion == 2/3
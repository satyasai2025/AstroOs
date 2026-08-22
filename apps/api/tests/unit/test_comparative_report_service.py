"""
Unit tests for ComparativeReportService (Module 20, Phase 5)
"""

import pytest
from apps.api.services.comparative_report_service import ComparativeReportService


class TestComparativeReportService:
    @pytest.fixture
    def chart_a(self):
        return {
            "houses": [{"house_number": 1, "rashi": "Cancer"}],
            "planets": [
                {"planet": "Moon", "rashi": "Taurus"},
                {"planet": "Jupiter", "rashi": "Cancer"},
            ],
        }

    @pytest.fixture
    def chart_b(self):
        return {
            "houses": [{"house_number": 1, "rashi": "Capricorn"}],
            "planets": [
                {"planet": "Moon", "rashi": "Virgo"},
                {"planet": "Sun", "rashi": "Scorpio"},
            ],
        }

    def test_comparative_axis_and_synastry(self, chart_a, chart_b):
        service = ComparativeReportService()
        metrics = service.compare_charts(chart_a, chart_b, "Partner A", "Partner B")

        # Cancer (4) to Capricorn (10) -> 7th axis (Samasaptaka)
        assert "7-7" in metrics.lagna_relationship or "Samasaptaka" in metrics.lagna_relationship

        # Taurus (2) to Virgo (6) -> 5-9 Navapanchama harmonic trine
        assert "5-9" in metrics.moon_relationship or "Navapanchama" in metrics.moon_relationship

        # High Guna score for 5-9 lunar alignment
        assert metrics.ashtakoota_guna_score is not None
        assert metrics.ashtakoota_guna_score >= 28.0

        # Technical Evidence items
        assert len(metrics.evidence_items) == 2
        assert metrics.evidence_items[0].evidence_id == "EVID-COMP-LAGNA"
        assert metrics.evidence_items[1].evidence_id == "EVID-COMP-MOON"

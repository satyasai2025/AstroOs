"""
Unit tests for SBC 10-Sangya Vedha Ray Matrix Engine (Module 19, Phase 4)
"""

import pytest
from apps.api.domain.sbc_ray_matrix import SBCNature, VedhaRayDirection
from apps.api.services.sbc_ray_matrix_engine import SBCRayMatrixEngine


class TestSBCRayMatrixEngine:
    @pytest.fixture
    def sample_natal_chart(self):
        return {
            "planets": [
                {"planet": "Moon", "nakshatra": "Rohini", "longitude": 45.0, "house_number": 1},
                {"planet": "Jupiter", "nakshatra": "Pushya", "longitude": 105.0, "house_number": 4},
                {"planet": "Sun", "nakshatra": "Magha", "longitude": 125.0, "house_number": 5},
            ]
        }

    def test_complete_10_sangyas_generation(self, sample_natal_chart):
        engine = SBCRayMatrixEngine()
        sample_transits = [
            {"planet": "Jupiter", "nakshatra": "Rohini", "is_retrograde": False, "speed_deg_day": 0.12},
            {"planet": "Saturn", "nakshatra": "Purva Bhadrapada", "is_retrograde": True, "speed_deg_day": -0.04},
        ]
        report = engine.compute_complete_sangya_matrix(sample_natal_chart, transit_planets=sample_transits)

        assert report.natal_moon_nakshatra == "Rohini"
        assert len(report.sangya_statuses) == 10

        sangya_keys = [s.sangya_key for s in report.sangya_statuses]
        assert "janma" in sangya_keys
        assert "karma" in sangya_keys
        assert "sanghatika" in sangya_keys
        assert "samudayika" in sangya_keys
        assert "adhana" in sangya_keys
        assert "vainashika" in sangya_keys
        assert "manasa" in sangya_keys
        assert "jati" in sangya_keys
        assert "desha" in sangya_keys
        assert "abhisheka" in sangya_keys

        # Janma is 1st nakshatra -> Rohini
        janma = next(s for s in report.sangya_statuses if s.sangya_key == "janma")
        assert janma.natal_nakshatra == "Rohini"
        assert 0 <= janma.grid_coord.row <= 8
        assert 0 <= janma.grid_coord.col <= 8

    def test_missing_transit_planets_raises(self, sample_natal_chart):
        # No fabricated-data fallback: omitting real transit_planets must
        # fail loud, not silently substitute a hardcoded fake transit set.
        engine = SBCRayMatrixEngine()
        with pytest.raises(ValueError):
            engine.compute_complete_sangya_matrix(sample_natal_chart)

    def test_vedha_ray_casting_and_confluence(self, sample_natal_chart):
        engine = SBCRayMatrixEngine()
        custom_transits = [
            {"planet": "Jupiter", "nakshatra": "Anuradha", "is_retrograde": False, "speed_deg_day": 0.1},
            {"planet": "Saturn", "nakshatra": "Jyeshtha", "is_retrograde": True, "speed_deg_day": -0.05},
        ]
        report = engine.compute_complete_sangya_matrix(sample_natal_chart, transit_planets=custom_transits)

        assert len(report.all_ray_collisions) >= 2
        assert len(report.audit_trail) >= 3
        assert isinstance(report.overall_sbc_confluence_score, float)
        assert len(report.kp_cross_link_summary) > 10

        # Verify ray directions
        jup_hit = next(c for c in report.all_ray_collisions if c.transit_planet == "Jupiter")
        assert jup_hit.ray_direction == VedhaRayDirection.FRONT
        assert jup_hit.nature == SBCNature.NATURAL_BENEFIC

        sat_hit = next(c for c in report.all_ray_collisions if c.transit_planet == "Saturn")
        assert sat_hit.ray_direction == VedhaRayDirection.RIGHT  # Retrograde -> Right ray
        assert sat_hit.nature == SBCNature.NATURAL_MALEFIC

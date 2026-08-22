"""
Unit tests for KP Cuspal Sub-Lord Decision Tree Engine (Module 19, Phase 4)
"""

import pytest
from apps.api.domain.kp_decision_tree import KPDecisionVerdict, KPEventDomain
from apps.api.services.kp_decision_tree_engine import KPDecisionTreeEngine


class TestKPDecisionTreeEngine:
    @pytest.fixture
    def sample_chart(self):
        return {
            "planets": [
                {"planet": "Jupiter", "house_number": 1, "rashi": "Cancer", "sidereal_longitude": 104.5, "star_lord": "Saturn"},
                {"planet": "Moon", "house_number": 4, "rashi": "Libra", "sidereal_longitude": 195.2, "star_lord": "Rahu"},
                {"planet": "Sun", "house_number": 10, "rashi": "Aries", "sidereal_longitude": 15.8, "star_lord": "Venus"},
                {"planet": "Mercury", "house_number": 10, "rashi": "Aries", "sidereal_longitude": 22.4, "star_lord": "Venus"},
                {"planet": "Mars", "house_number": 10, "rashi": "Capricorn", "sidereal_longitude": 284.1, "star_lord": "Mars"},
                {"planet": "Venus", "house_number": 11, "rashi": "Taurus", "sidereal_longitude": 48.0, "star_lord": "Sun"},
                {"planet": "Saturn", "house_number": 7, "rashi": "Capricorn", "sidereal_longitude": 278.3, "star_lord": "Mars"},
                {"planet": "Rahu", "house_number": 6, "rashi": "Sagittarius", "sidereal_longitude": 254.0, "star_lord": "Venus"},
                {"planet": "Ketu", "house_number": 12, "rashi": "Gemini", "sidereal_longitude": 74.0, "star_lord": "Rahu"},
            ],
            "houses": [
                {"house_number": 1, "longitude": 95.0, "rashi": "Cancer", "sign_lord": "Moon", "star_lord": "Saturn", "sub_lord": "Jupiter"},
                {"house_number": 2, "longitude": 125.0, "rashi": "Leo", "sign_lord": "Sun", "star_lord": "Ketu", "sub_lord": "Venus"},
                {"house_number": 7, "longitude": 275.0, "rashi": "Capricorn", "sign_lord": "Saturn", "star_lord": "Mars", "sub_lord": "Jupiter"},
                {"house_number": 10, "longitude": 5.0, "rashi": "Aries", "sign_lord": "Mars", "star_lord": "Ketu", "sub_lord": "Sun"},
                {"house_number": 11, "longitude": 35.0, "rashi": "Taurus", "sign_lord": "Venus", "star_lord": "Sun", "sub_lord": "Mars"},
            ],
        }

    def test_four_tier_significator_matrix_structure(self, sample_chart):
        engine = KPDecisionTreeEngine()
        matrix = engine.compute_four_tier_matrix(sample_chart)
        assert len(matrix) == 12

        # House 1: Occupant is Jupiter. Jupiter's star lord is Saturn.
        h1 = next(m for m in matrix if m.house_number == 1)
        assert "Jupiter" in h1.tier_b_planets
        assert h1.tier_d_planets == ["Moon"]

        # House 10: Occupants are Sun, Mercury, Mars
        h10 = next(m for m in matrix if m.house_number == 10)
        assert "Sun" in h10.tier_b_planets
        assert "Mercury" in h10.tier_b_planets
        assert "Mars" in h10.tier_b_planets

    def test_cuspal_decision_nodes_calculation(self, sample_chart):
        engine = KPDecisionTreeEngine()
        nodes = engine.compute_cuspal_decision_nodes(sample_chart, house_numbers=[1, 7, 10])
        assert len(nodes) == 3

        # 10th Cusp (Career)
        c10 = next(n for n in nodes if n.house_number == 10)
        assert c10.sub_lord == "Sun"
        assert len(c10.audit_chain) >= 3
        assert isinstance(c10.verdict, KPDecisionVerdict)

        # 7th Cusp (Marriage)
        c7 = next(n for n in nodes if n.house_number == 7)
        assert c7.sub_lord == "Jupiter"
        assert len(c7.verdict_explanation) > 10

    def test_event_specific_decision_trees(self, sample_chart):
        engine = KPDecisionTreeEngine()
        events = engine.compute_event_decision_trees(sample_chart)
        assert len(events) == 4

        domains = {e.event_domain for e in events}
        assert KPEventDomain.CAREER in domains
        assert KPEventDomain.MARRIAGE in domains
        assert KPEventDomain.FINANCE in domains
        assert KPEventDomain.HEALTH in domains

        career_ev = next(e for e in events if e.event_domain == KPEventDomain.CAREER)
        assert career_ev.primary_cusp == 10
        assert 2 in career_ev.supporting_cusps
        assert 11 in career_ev.supporting_cusps
        assert len(career_ev.technical_calculation_steps) >= 4

"""
Unit tests — LEGAL/EDUCATION/POWER/TRANSFORMATION/ACHIEVEMENT Sangya domain extensions.
"""

from __future__ import annotations

import pytest

from packages.shared.disclosed_events import (
    LifeDomain,
    SANGYA_DOMAINS,
    domains_for_sangyas,
    match_events,
)


class TestLifeDomainEnumExtended:
    def test_power_domain_exists(self):
        assert LifeDomain.POWER == "power"

    def test_transformation_domain_exists(self):
        assert LifeDomain.TRANSFORMATION == "transformation"

    def test_achievement_domain_exists(self):
        assert LifeDomain.ACHIEVEMENT == "achievement"

    def test_legal_domain_exists(self):
        assert LifeDomain.LEGAL == "legal"

    def test_education_domain_exists(self):
        assert LifeDomain.EDUCATION == "education"

    def test_all_14_domains_present(self):
        """Enum now has 14 members (original 11 + POWER + TRANSFORMATION + ACHIEVEMENT)."""
        assert len(LifeDomain) == 14


class TestSangyaDomainMappings:
    def test_legal_reachable_via_adhana(self):
        domains = SANGYA_DOMAINS.get("adhana", frozenset())
        assert LifeDomain.LEGAL in domains, (
            "LEGAL domain must be mapped under adhana Sangya"
        )

    def test_education_reachable_via_karma(self):
        domains = SANGYA_DOMAINS.get("karma", frozenset())
        assert LifeDomain.EDUCATION in domains, (
            "EDUCATION domain must be mapped under karma Sangya"
        )

    def test_achievement_reachable_via_karma(self):
        domains = SANGYA_DOMAINS.get("karma", frozenset())
        assert LifeDomain.ACHIEVEMENT in domains, (
            "ACHIEVEMENT domain must be mapped under karma Sangya"
        )

    def test_power_reachable_via_abhisheka(self):
        domains = SANGYA_DOMAINS.get("abhisheka", frozenset())
        assert LifeDomain.POWER in domains, (
            "POWER domain must be mapped under abhisheka Sangya"
        )

    def test_transformation_reachable_via_sanghatika(self):
        domains = SANGYA_DOMAINS.get("sanghatika", frozenset())
        assert LifeDomain.TRANSFORMATION in domains, (
            "TRANSFORMATION domain must be mapped under sanghatika Sangya"
        )

    def test_original_mappings_unchanged(self):
        """Verify original 10 mappings are still present."""
        assert LifeDomain.HEALTH in SANGYA_DOMAINS["janma"]
        assert LifeDomain.CAREER in SANGYA_DOMAINS["karma"]
        assert LifeDomain.FINANCE in SANGYA_DOMAINS["sanghatika"]
        assert LifeDomain.FINANCE in SANGYA_DOMAINS["samudayika"]
        assert LifeDomain.RELOCATION in SANGYA_DOMAINS["adhana"]
        assert LifeDomain.FINANCE in SANGYA_DOMAINS["vainashika"]
        assert LifeDomain.MENTAL_WELLBEING in SANGYA_DOMAINS["manasa"]
        assert LifeDomain.FAMILY in SANGYA_DOMAINS["jati"]
        assert LifeDomain.RELOCATION in SANGYA_DOMAINS["desha"]
        assert LifeDomain.SPIRITUAL in SANGYA_DOMAINS["abhisheka"]


class TestDomainsForSangyas:
    def test_domains_for_karma_includes_education(self):
        result = domains_for_sangyas(["karma"])
        assert LifeDomain.EDUCATION in result

    def test_domains_for_adhana_includes_legal(self):
        result = domains_for_sangyas(["adhana"])
        assert LifeDomain.LEGAL in result

    def test_domains_for_abhisheka_includes_power(self):
        result = domains_for_sangyas(["abhisheka"])
        assert LifeDomain.POWER in result

    def test_domains_for_multiple_sangyas_union(self):
        result = domains_for_sangyas(["karma", "abhisheka"])
        assert LifeDomain.EDUCATION in result
        assert LifeDomain.POWER in result
        assert LifeDomain.CAREER in result

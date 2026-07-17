"""
AstroOS — Fact & FactRegistry Unit Tests (Module 13)
"""

import pytest

from apps.api.domain.facts import Fact
from apps.api.services.fact_registry import FactRegistry


def test_add_and_get_fact():
    registry = FactRegistry()
    fact = Fact(key="planet.jupiter.house", value=1, source="graha_engine")
    registry.add_fact(fact)
    assert registry.get_fact("planet.jupiter.house") == fact


def test_get_fact_missing_returns_none():
    registry = FactRegistry()
    assert registry.get_fact("nonexistent.key") is None


def test_get_value_returns_raw_value():
    registry = FactRegistry()
    registry.add_fact(Fact("shadbala.jupiter.total", 4.5, "shadbala_engine"))
    assert registry.get_value("shadbala.jupiter.total") == 4.5


def test_get_value_missing_returns_default():
    registry = FactRegistry()
    assert registry.get_value("nonexistent.key", default="fallback") == "fallback"
    assert registry.get_value("nonexistent.key") is None


def test_has_fact():
    registry = FactRegistry()
    registry.add_fact(Fact("a.b.c", True, "test"))
    assert registry.has_fact("a.b.c") is True
    assert registry.has_fact("x.y.z") is False


def test_add_fact_overwrites_same_key():
    registry = FactRegistry()
    registry.add_fact(Fact("planet.sun.house", 1, "graha_engine"))
    registry.add_fact(Fact("planet.sun.house", 5, "graha_engine"))
    assert registry.get_value("planet.sun.house") == 5


def test_all_facts_returns_everything():
    registry = FactRegistry()
    registry.add_fact(Fact("a", 1, "test"))
    registry.add_fact(Fact("b", 2, "test"))
    assert len(registry.all_facts()) == 2


def test_fact_count():
    registry = FactRegistry()
    registry.add_fact(Fact("a", 1, "test"))
    registry.add_fact(Fact("b", 2, "test"))
    assert registry.fact_count() == 2

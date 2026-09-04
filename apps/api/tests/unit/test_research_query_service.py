"""
AstroOS — Unit tests for ResearchQueryService and query builder logic
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.domain.facts import Fact
from apps.api.models.research_case import EventSnapshotModel
from apps.api.services.research_query_service import (
    QueryCondition,
    ResearchQueryService,
    _case_matches,
    _matches,
)


def test_matches_operator_equals():
    assert _matches("true", "equals", "true") is True
    assert _matches("True", "equals", "true") is True
    assert _matches(True, "equals", "true") is True
    assert _matches(10, "equals", "10") is True
    assert _matches("mars", "equals", "venus") is False


def test_matches_operator_not_equals():
    assert _matches("mars", "not_equals", "venus") is True
    assert _matches("mars", "not_equals", "mars") is False


def test_matches_operator_contains():
    assert _matches("saturn_aries", "contains", "saturn") is True
    assert _matches("saturn_aries", "contains", "jupiter") is False


def test_case_matches_all_conditions_satisfied():
    facts = [
        Fact(key="planet.saturn.retrograde", value=True, source="graha"),
        Fact(key="maraka.lord.saturn", value=True, source="badhaka_maraka"),
        Fact(key="planet.rahu.house", value=1, source="graha"),
    ]
    conditions = [
        QueryCondition(field="planet.saturn.retrograde", operator="equals", value="true"),
        QueryCondition(field="maraka.lord.saturn", operator="equals", value="true"),
        QueryCondition(field="planet.rahu.house", operator="equals", value="1"),
    ]
    assert _case_matches(facts, conditions) is True


def test_case_matches_fails_when_condition_not_met():
    facts = [
        Fact(key="planet.saturn.retrograde", value=True, source="graha"),
        Fact(key="maraka.lord.saturn", value=False, source="badhaka_maraka"),
    ]
    conditions = [
        QueryCondition(field="planet.saturn.retrograde", operator="equals", value="true"),
        QueryCondition(field="maraka.lord.saturn", operator="equals", value="true"),
    ]
    assert _case_matches(facts, conditions) is False


def test_case_matches_fails_when_field_missing():
    facts = [
        Fact(key="planet.saturn.retrograde", value=True, source="graha"),
    ]
    conditions = [
        QueryCondition(field="maraka.lord.saturn", operator="equals", value="true"),
    ]
    assert _case_matches(facts, conditions) is False

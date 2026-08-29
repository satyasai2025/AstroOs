"""
AstroOS — Relocation Technique Fixtures Integration Tests

Exercises the astro-cartography technique fixtures against facts produced
by the RelocationEngine for a real chart (Robert Redford: Santa Monica
-> Provo). Confirms:
  - every relocation technique is registered and references existing rules
  - missing mandatory facts produce INSUFFICIENT_DATA, never guesses
  - un-computed producers (geodetic, supportive/challenging) surface as
    INSUFFICIENT_DATA on their rules rather than fabricating evidence
"""

from __future__ import annotations

import datetime

import pytest

from apps.api.domain.technique import TriggerStatus
from apps.api.services.relocation_engine import RelocationEngine
from apps.api.services.rule_registry import get_rule
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_registry import get_technique
from apps.api.services.techniques import (  # noqa: F401
    line_type_hierarchy,
    major_minor_frequencies,
    map_line_reading,
    relocated_chart_evaluation,
)

REDFORD_BIRTH = datetime.datetime(1936, 8, 19, 3, 2, 0)  # 1936-08-18 8:02pm PDT
SANTA_MONICA = (34.0195, -118.4912)
PROVO = (40.2338, -111.6585)


@pytest.fixture(autouse=True)
def ensure_relocation_fixtures_registered():
    """Re-register idempotently: some suite modules clear the shared
    registries in-place (test_technique_framework_e2e.py), so import-time
    registration alone is not reliable across test files."""
    relocated_chart_evaluation.init_relocated_chart_evaluation()
    line_type_hierarchy.init_line_type_hierarchy()
    map_line_reading.init_map_line_reading()
    major_minor_frequencies.init_major_minor_frequencies()
    yield


def _registry(prefix="relocation"):
    eng = RelocationEngine(ayanamsa="tropical", house_system="P")
    return eng.build_fact_registry(REDFORD_BIRTH, SANTA_MONICA[0], SANTA_MONICA[1],
                                   PROVO[0], PROVO[1], prefix)


def _result(tech_id, facts):
    tech = get_technique(tech_id, 1)
    assert tech is not None
    return TechniqueEngine().execute(tech, facts)


@pytest.mark.parametrize("tech_id", [
    "relocated_chart_evaluation",
    "line_type_hierarchy",
    "map_line_reading",
    "major_minor_frequencies",
])
def test_relocation_techniques_registered_with_valid_rule_refs(tech_id):
    tech = get_technique(tech_id, 1)
    assert tech is not None
    for ref in tech.rule_refs:
        assert get_rule(ref.rule_id) is not None, ref.rule_id
        assert ref.provenance.value == "source_derived"


def test_relocated_chart_evaluation_triggers_on_provo():
    facts = _registry()
    result = _result("relocated_chart_evaluation", facts)
    assert any(t.status is TriggerStatus.TRIGGERED
               for t in result.triggers)
    # R1 foundation and R2 cusp-shift must fire for a moved location.
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["RELO-EVAL-001"] is TriggerStatus.TRIGGERED
    assert by_id["RELO-EVAL-002"] is TriggerStatus.TRIGGERED


def test_relocated_chart_evaluation_not_triggered_when_location_unchanged():
    eng = RelocationEngine(ayanamsa="tropical", house_system="P")
    facts = eng.build_fact_registry(REDFORD_BIRTH, SANTA_MONICA[0], SANTA_MONICA[1],
                                    SANTA_MONICA[0], SANTA_MONICA[1])
    result = _result("relocated_chart_evaluation", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Same place: no cusp shift (R2), though the foundation still holds.
    assert by_id["RELO-EVAL-002"] is TriggerStatus.NOT_TRIGGERED
    assert by_id["RELO-EVAL-001"] is TriggerStatus.TRIGGERED


def test_line_type_hierarchy_natal_dominance_requires_in_orb_lines():
    facts = _registry()
    result = _result("line_type_hierarchy", facts)
    # Provo is 6+ degrees of orb from every axial line → natal count 0.
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["LINE-HIER-001"] is TriggerStatus.NOT_TRIGGERED
    # Local-space / geodetic producers do not exist → INSUFFICIENT_DATA.
    assert by_id["LINE-HIER-002"] is TriggerStatus.INSUFFICIENT_DATA
    assert by_id["LINE-HIER-003"] is TriggerStatus.INSUFFICIENT_DATA


def test_map_line_reading_not_triggered_when_no_line_in_orb():
    facts = _registry()
    result = _result("map_line_reading", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["LINE-READ-001"] is TriggerStatus.NOT_TRIGGERED


def test_map_line_reading_triggers_on_a_line_in_orb():
    eng = RelocationEngine(ayanamsa="tropical", house_system="P",
                           line_orb_deg=10.0)  # widen orb to capture a line
    facts = eng.build_fact_registry(REDFORD_BIRTH, SANTA_MONICA[0], SANTA_MONICA[1],
                                    PROVO[0], PROVO[1])
    result = _result("map_line_reading", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["LINE-READ-001"] is TriggerStatus.TRIGGERED


def test_major_minor_frequencies_twin_map_rule_is_insufficient():
    facts = _registry()
    result = _result("major_minor_frequencies", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Twin-map rule needs geodetic facts (no producer) → INSUFFICIENT_DATA.
    assert by_id["FREQ-MAJ-001"] is TriggerStatus.INSUFFICIENT_DATA
    # Support/challenge classification also has no producer → INSUFFICIENT_DATA.
    assert by_id["FREQ-MAJ-002"] is TriggerStatus.INSUFFICIENT_DATA
    # Minor frequencies (local space / paran) are available → fire.
    assert by_id["FREQ-MIN-001"] is TriggerStatus.TRIGGERED


def test_missing_all_relocation_facts_reports_insufficient_data():
    from apps.api.domain.facts import Fact
    from apps.api.services.fact_registry import FactRegistry
    empty = FactRegistry()
    result = _result("relocated_chart_evaluation", empty)
    assert result.confidence == 0
    for t in result.triggers:
        assert t.status is TriggerStatus.INSUFFICIENT_DATA

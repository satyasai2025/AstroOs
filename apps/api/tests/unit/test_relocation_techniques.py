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

from apps.api.domain.facts import Fact
from apps.api.domain.technique import TriggerStatus
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.relocation_engine import RelocationEngine
from apps.api.services.rule_registry import get_rule
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_registry import get_technique
from apps.api.services.techniques import (  # noqa: F401
    comfort_zones,
    harmonic_interpretation,
    in_mundo_vs_longitude,
    line_type_hierarchy,
    location_energy_usage,
    major_minor_frequencies,
    map_line_reading,
    midpoints_to_angles,
    paran_crossings,
    relocated_chart_evaluation,
    sun_angular,
    uranus_instability,
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
    location_energy_usage.init_location_energy_usage()
    comfort_zones.init_comfort_zones()
    uranus_instability.init_uranus_instability()
    in_mundo_vs_longitude.init_in_mundo_vs_longitude()
    paran_crossings.init_paran_crossings()
    sun_angular.init_sun_angular()
    midpoints_to_angles.init_midpoints_to_angles()
    harmonic_interpretation.init_harmonic_interpretation()
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


# ── fixtures 05-08 ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tech_id", [
    "location_energy_usage",
    "comfort_zones",
    "uranus_instability",
    "in_mundo_vs_longitude",
])
def test_relocation_fixtures_05_to_08_registered(tech_id):
    tech = get_technique(tech_id, 1)
    assert tech is not None
    for ref in tech.rule_refs:
        assert get_rule(ref.rule_id) is not None, ref.rule_id


def test_location_energy_usage_requires_supportive_identification():
    # Without a supportive-location classifier, every rule is INSUFFICIENT_DATA.
    facts = _registry()
    result = _result("location_energy_usage", facts)
    for t in result.triggers:
        assert t.status is TriggerStatus.INSUFFICIENT_DATA


def test_location_energy_usage_live_mode_recommended():
    facts = _registry()
    facts.add_fact(Fact("relocation.supportive.identified", True, "context"))
    facts.add_fact(Fact("relocation.usage.live", True, "context"))
    facts.add_fact(Fact("relocation.usage.travel", False, "context"))
    facts.add_fact(Fact("relocation.usage.import", False, "context"))
    result = _result("location_energy_usage", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["USAGE-LIVE-001"] is TriggerStatus.TRIGGERED
    assert by_id["USAGE-TRAV-001"] is TriggerStatus.NOT_TRIGGERED


def test_comfort_zones_triggers_on_ninth_harmonic():
    # Honolulu (tropical): Moon is in 9th-harmonic relation to an angle.
    eng = RelocationEngine(ayanamsa="tropical", house_system="P")
    facts = eng.build_fact_registry(REDFORD_BIRTH, SANTA_MONICA[0], SANTA_MONICA[1],
                                    21.3069, -157.8583)
    assert facts.get_value("relocation.planet.moon.ninth_harmonic_to_angle") is True
    result = _result("comfort_zones", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["COMFORT-001"] is TriggerStatus.TRIGGERED
    assert by_id["COMFORT-004"] is TriggerStatus.TRIGGERED  # Moon flavor


def test_uranus_instability_flags_angular_uranus():
    facts = _registry()
    result = _result("uranus_instability", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Provo: Uranus is succedent (not angular) and Saturn-Uranus midpoint is
    # out of orb → neither risk rule fires; the softening rule needs context.
    assert by_id["URANUS-001"] is TriggerStatus.NOT_TRIGGERED
    assert by_id["URANUS-003"] is TriggerStatus.INSUFFICIENT_DATA


def test_in_mundo_vs_longitude_longitude_system_active():
    facts = _registry()
    result = _result("in_mundo_vs_longitude", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["SYS-001"] is TriggerStatus.TRIGGERED
    assert by_id["SYS-002"] is TriggerStatus.TRIGGERED
    assert by_id["SYS-003"] is TriggerStatus.TRIGGERED
    # R4 needs the caller's consistency preference.
    assert by_id["SYS-004"] is TriggerStatus.INSUFFICIENT_DATA


# ── fixtures 09-12 ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tech_id", [
    "paran_crossings",
    "sun_angular",
    "midpoints_to_angles",
    "harmonic_interpretation",
])
def test_relocation_fixtures_09_to_12_registered(tech_id):
    tech = get_technique(tech_id, 1)
    assert tech is not None
    for ref in tech.rule_refs:
        assert get_rule(ref.rule_id) is not None, ref.rule_id


def test_paran_crossings_provo_crossings_exist_but_out_of_orb():
    facts = _registry()
    assert facts.get_value("relocation.paran.count", 0) >= 1
    assert facts.get_value("relocation.lines.paran.count", 0) == 0
    result = _result("paran_crossings", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    assert by_id["PARAN-002"] is TriggerStatus.TRIGGERED
    assert by_id["PARAN-001"] is TriggerStatus.NOT_TRIGGERED
    # X-marks-the-spot needs a supportive-line classifier.
    assert by_id["PARAN-003"] is TriggerStatus.INSUFFICIENT_DATA


def test_sun_angular_not_angular_at_provo_but_trine_sextile():
    facts = _registry()
    result = _result("sun_angular", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Provo: Sun not conjunct an angle, but its trine/sextile relation holds.
    assert by_id["SUN-001"] is TriggerStatus.NOT_TRIGGERED
    assert by_id["SUN-003"] is TriggerStatus.NOT_TRIGGERED
    assert by_id["SUN-002"] is TriggerStatus.TRIGGERED


def test_midpoints_to_angles_detects_midpoint_in_orb():
    facts = _registry()
    result = _result("midpoints_to_angles", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Provo: at least one midpoint falls on an angle; count them to assert.
    asc = facts.get_value("relocation.midpoints.asc.count", 0)
    mc = facts.get_value("relocation.midpoints.mc.count", 0)
    assert asc + mc >= 1
    assert by_id["MID-001"] is TriggerStatus.TRIGGERED


def test_harmonic_interpretation_provo_is_seventh():
    facts = _registry()
    result = _result("harmonic_interpretation", facts)
    by_id = {t.rule_id: t.status for t in result.triggers}
    # Both Provo angle labels carry minutes → 7th-harmonic discipline.
    assert by_id["HARM-003"] is TriggerStatus.TRIGGERED
    assert by_id["HARM-001"] is TriggerStatus.NOT_TRIGGERED
    assert by_id["HARM-002"] is TriggerStatus.NOT_TRIGGERED

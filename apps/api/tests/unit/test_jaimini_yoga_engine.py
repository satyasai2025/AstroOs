"""
AstroOS — Jaimini Yoga Engine Unit Tests

Uses synthetic charts (jaimini_fixtures) run through the REAL Chara
Karaka / Arudha / Rashi Aspect / Karakamsa engines to build a genuine
JaiminiYogaContext, then evaluates it against the real registered yoga
rules (imported for their registration side effect, same pattern as
apps/api/services/jaimini_yogas/__init__.py's own docstring describes).
See tests/precision/test_jaimini_orchestrator_precision.py for coverage
against a real ephemeris-computed chart; this file isolates the engine
+ registry wiring against controlled synthetic input instead.
"""

from __future__ import annotations

import pytest

from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet

import apps.api.services.jaimini_yogas  # noqa: F401 — registers all 5 real rules
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_yoga_context import JaiminiYogaContext
from apps.api.services.jaimini_yoga_engine import JaiminiYogaEngine
from apps.api.services.rashi_aspect_engine import RashiAspectEngine

_ALL_RULE_IDS = {
    "JAIMINI-RY-001", "JAIMINI-ARY-001", "JAIMINI-KY-001",
    "JAIMINI-DUY-001", "JAIMINI-AKD-001",
}


@pytest.fixture
def synthetic_context() -> JaiminiYogaContext:
    # Atmakaraka/Amatyakaraka forced into mutual Kendra (Aries/Cancer,
    # 4th from each other) by giving Sun the highest karaka_degree in
    # Aries and Moon the second-highest in Cancer.
    planets = [
        make_planet("sun", "aries", rashi_degree=29.0),
        make_planet("moon", "cancer", rashi_degree=28.0),
        make_planet("mars", "leo", rashi_degree=10.0),
        make_planet("mercury", "virgo", rashi_degree=8.0),
        make_planet("jupiter", "libra", rashi_degree=5.0),
        make_planet("venus", "scorpio", rashi_degree=3.0),
        make_planet("saturn", "sagittarius", rashi_degree=1.0),
    ]
    d1 = make_d1_chart(lagna_rashi="aries", planets=planets)
    chara_karaka = CharaKarakaEngine().compute(d1, scheme="sapta_karaka")
    arudha = ArudhaEngine().compute(d1)
    rashi_aspect = RashiAspectEngine().compute(d1)
    return JaiminiYogaContext(
        d1_chart=d1, chara_karaka=chara_karaka, arudha=arudha,
        rashi_aspect=rashi_aspect, karakamsa=None,
    )


class TestJaiminiYogaEngine:
    def test_evaluates_all_five_registered_rules(self, synthetic_context):
        results = JaiminiYogaEngine().evaluate_all(synthetic_context)
        assert {r.rule.rule_id for r in results} == _ALL_RULE_IDS
        assert len(results) == 5

    def test_karakamsa_dependent_rules_report_not_matched_without_karakamsa(self, synthetic_context):
        results = JaiminiYogaEngine().evaluate_all(synthetic_context)
        ky = next(r for r in results if r.rule.rule_id == "JAIMINI-KY-001")
        assert ky.is_matched is False

    def test_atmakaraka_amatyakaraka_kendra_forces_raja_yoga_match(self, synthetic_context):
        # Sun (AK, Aries) and Moon (AmK, Cancer) are 4th from each other —
        # a Kendra by construction, so JAIMINI-RY-001 must match.
        ak = synthetic_context.chara_karaka.atmakaraka
        amk = synthetic_context.chara_karaka.by_name("Amatyakaraka")
        assert ak.planet == "sun"
        assert amk.planet == "moon"

        results = JaiminiYogaEngine().evaluate_all(synthetic_context)
        ry = next(r for r in results if r.rule.rule_id == "JAIMINI-RY-001")
        assert ry.is_matched is True
        assert ry.confidence.score > 0

    def test_every_result_is_evidence_shaped(self, synthetic_context):
        results = JaiminiYogaEngine().evaluate_all(synthetic_context)
        for r in results:
            assert isinstance(r.is_matched, bool)
            assert 0 <= r.confidence.score <= 100
            assert len(r.reasons) == r.confidence.total_conditions
            assert r.explanation

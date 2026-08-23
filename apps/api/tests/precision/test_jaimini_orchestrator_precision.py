"""
Jaimini Orchestrator precision tests.

Golden-value regression test against a real Swiss Ephemeris computation
(no mocking) — same philosophy as every other file in tests/precision/:
compare against real computed output captured once and pinned here, so
a future change to any of the 7 composed Jaimini engines that silently
shifts a result gets caught. Not a classical-accuracy verification (no
independent reference chart was cross-checked against another software
package) — a regression guard.

Birth data: 1990-06-15 08:30 UTC, 28.6139N 77.2090E (Delhi), Lahiri
ayanamsa, Whole Sign houses — arbitrary but fixed, matching the sample
used throughout this session's manual verification.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.config import get_settings
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.jaimini_orchestrator import JaiminiOrchestrator

_SETTINGS = get_settings()
_WRAPPER = EphemerisWrapper(ephemeris_path=_SETTINGS.EPHEMERIS_PATH)
_ORCHESTRATOR = JaiminiOrchestrator(_WRAPPER)

_BIRTH_DT = datetime(1990, 6, 15, 8, 30, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def bundle():
    return _ORCHESTRATOR.compute_bundle(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )


class TestCharaKaraka:
    def test_atmakaraka(self, bundle):
        ak = bundle.chara_karaka.atmakaraka
        assert ak.planet == "venus"
        assert ak.rashi == "aries"
        assert ak.karaka_degree == pytest.approx(24.8832, abs=1e-3)

    def test_darakaraka(self, bundle):
        dk = bundle.chara_karaka.darakaraka
        assert dk.planet == "sun"
        assert dk.rashi == "gemini"

    def test_seven_karakas_in_sapta_scheme(self, bundle):
        assert bundle.chara_karaka.scheme == "sapta_karaka"
        assert len(bundle.chara_karaka.karakas) == 7
        assert [k.rank for k in bundle.chara_karaka.karakas] == list(range(1, 8))


class TestArudha:
    def test_arudha_lagna(self, bundle):
        assert bundle.arudha.arudha_lagna.rashi == "capricorn"

    def test_upapada_lagna(self, bundle):
        assert bundle.arudha.upapada_lagna.rashi == "aries"

    def test_twelve_padas(self, bundle):
        assert len(bundle.arudha.padas) == 12
        assert [p.house_number for p in bundle.arudha.padas] == list(range(1, 13))


class TestKarakamsa:
    def test_karakamsa_rashi(self, bundle):
        assert bundle.karakamsa is not None
        assert bundle.karakamsa.karakamsa_rashi == "scorpio"

    def test_swamsa_rashi(self, bundle):
        assert bundle.karakamsa.swamsa_rashi == "cancer"

    def test_atmakaraka_matches_chara_karaka(self, bundle):
        assert bundle.karakamsa.atmakaraka == bundle.chara_karaka.atmakaraka.planet


class TestJaiminiDasha:
    def test_chara_dasha(self, bundle):
        assert bundle.chara_dasha.system == "chara"
        assert bundle.chara_dasha.lagna_rashi == "virgo"
        assert bundle.chara_dasha.total_cycle_years == 90
        assert len(bundle.chara_dasha.periods) == 12

    def test_narayana_dasha(self, bundle):
        assert bundle.narayana_dasha.system == "narayana"
        assert bundle.narayana_dasha.lagna_rashi == "cancer"
        assert bundle.narayana_dasha.total_cycle_years == 77
        assert len(bundle.narayana_dasha.periods) == 12


class TestJaiminiYogas:
    def test_five_yogas_evaluated(self, bundle):
        assert len(bundle.yogas) == 5
        assert {y.rule.rule_id for y in bundle.yogas} == {
            "JAIMINI-RY-001", "JAIMINI-ARY-001", "JAIMINI-KY-001",
            "JAIMINI-DUY-001", "JAIMINI-AKD-001",
        }

    def test_matched_yogas(self, bundle):
        matched = {y.rule.rule_id for y in bundle.yogas if y.is_matched}
        assert matched == {"JAIMINI-ARY-001", "JAIMINI-KY-001"}

    def test_every_evidence_is_internally_consistent(self, bundle):
        for y in bundle.yogas:
            assert len(y.reasons) == y.confidence.total_conditions
            assert y.confidence.satisfied_conditions == sum(1 for r in y.reasons if r.is_satisfied)


class TestArgala:
    def test_four_pairs_from_a_rashi_reference(self, bundle):
        argala = _ORCHESTRATOR.compute_argala(bundle.d1_chart, "aries")
        assert len(argala.pairs) == 4
        assert {p.argala_house for p in argala.pairs} == {2, 4, 5, 11}

    def test_planet_reference_resolves_to_its_own_rashi(self, bundle):
        moon = next(k for k in bundle.chara_karaka.karakas if k.planet == "moon")
        argala = _ORCHESTRATOR.compute_argala(bundle.d1_chart, "moon")
        assert argala.reference_rashi == moon.rashi

    def test_unknown_reference_raises(self, bundle):
        with pytest.raises(ValueError):
            _ORCHESTRATOR.compute_argala(bundle.d1_chart, "not-a-sign")


class TestComputeD1Chart:
    def test_matches_bundles_own_chart(self, bundle):
        d1 = _ORCHESTRATOR.compute_d1_chart(
            birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
        )
        assert d1.ascendant.rashi == bundle.d1_chart.ascendant.rashi
        assert d1.ascendant.sidereal_longitude == pytest.approx(
            bundle.d1_chart.ascendant.sidereal_longitude, abs=1e-6
        )

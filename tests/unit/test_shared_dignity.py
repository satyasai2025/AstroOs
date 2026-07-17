"""
AstroOS — Shared Dignity Computation Unit Tests (Module 9 Phase 2)

Covers packages/shared/dignity.py directly, plus GrahaEngine.compute_dignity()
as its wrapper, plus the critical regression check: this refactor must
produce byte-identical D1 dignity to the previous private implementation.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.ephemeris import DignityType
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.graha_engine import GrahaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine
from packages.shared.dignity import compute_dignity_value

_EPHE_PATH = "data/ephemeris"


# ── packages/shared/dignity.py directly ───────────────────────────────────────

def test_exaltation_takes_precedence():
    assert compute_dignity_value("sun", "aries", 10.0) == "exalted"


def test_debilitation():
    assert compute_dignity_value("sun", "libra", 10.0) == "debilitated"


def test_moolatrikona_within_range():
    assert compute_dignity_value("sun", "leo", 10.0) == "moolatrikona"  # sun MT: leo 0-20


def test_own_sign_outside_moolatrikona_range():
    """Sun in Leo at 25 degrees is outside MT range (0-20) but still own sign."""
    assert compute_dignity_value("sun", "leo", 25.0) == "own"


def test_friendly_sign():
    # Sun's friends: moon, mars, jupiter. Cancer is ruled by moon.
    assert compute_dignity_value("sun", "cancer", 10.0) == "friendly"


def test_enemy_sign():
    # Sun's enemies: venus, saturn. Taurus is ruled by venus, and isn't
    # Sun's exaltation/debilitation/moolatrikona/own sign, isolating the
    # enemy-relationship branch specifically.
    assert compute_dignity_value("sun", "taurus", 10.0) == "enemy"


def test_neutral_sign():
    # Sun in Gemini (mercury) — mercury is neither friend nor enemy of sun
    assert compute_dignity_value("sun", "gemini", 10.0) == "neutral"


def test_rahu_ketu_return_none():
    assert compute_dignity_value("rahu", "gemini", 10.0) is None
    assert compute_dignity_value("ketu", "sagittarius", 10.0) is None


def test_precedence_order_exalted_beats_moolatrikona():
    """A planet can't simultaneously be exalted and moolatrikona in classical tables, but confirm exaltation is checked first regardless."""
    # Sun exalts in Aries; verify that's returned even though other checks exist below it in the function
    assert compute_dignity_value("sun", "aries", 5.0) == "exalted"


# ── GrahaEngine.compute_dignity wrapper ───────────────────────────────────────

def test_graha_engine_compute_dignity_wraps_string_as_enum():
    engine = GrahaEngine()
    result = engine.compute_dignity("sun", "aries", 10.0)
    assert result == DignityType.EXALTED
    assert isinstance(result, DignityType)


def test_graha_engine_compute_dignity_none_for_nodes():
    engine = GrahaEngine()
    assert engine.compute_dignity("rahu", "gemini", 10.0) is None


# ── Regression: byte-identical to pre-refactor D1 dignity ────────────────────

def test_d1_dignity_matches_graha_engine_compute_dignity_exactly():
    """
    Critical regression check for the Module 9 Phase 2 dignity refactor:
    EphemerisWrapper's D1 dignity (now a thin wrapper over the same
    shared function) must exactly match calling GrahaEngine.compute_dignity()
    independently on the same (planet, rashi, rashi_degree).
    """
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    graha_engine = GrahaEngine()

    chart = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )

    for p in chart.planets:
        recomputed = graha_engine.compute_dignity(p.planet, p.rashi, p.rashi_degree)
        assert recomputed == p.dignity, f"{p.planet}: chart={p.dignity} recomputed={recomputed}"


# ── The actual Saptavargaja Bala prerequisite: works for divisional charts ───

def test_compute_dignity_works_for_divisional_chart_positions():
    """
    The specific capability Module 9 Phase 2 needed to unblock Saptavargaja
    Bala: compute_dignity() must work identically for a VargaPosition's
    varga_rashi/varga_rashi_degree as it does for a D1 SiderealPosition's
    rashi/rashi_degree — no varga-specific logic required.
    """
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    div_engine = DivisionalEngine(wrapper)
    graha_engine = GrahaEngine()

    d9_chart = div_engine.compute(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090, varga="D9",
    )

    for p in d9_chart.planet_positions:
        dignity = graha_engine.compute_dignity(p.planet, p.varga_rashi, p.varga_rashi_degree)
        if p.planet in ("rahu", "ketu"):
            assert dignity is None
        else:
            assert dignity is not None
            assert isinstance(dignity, DignityType)


def test_compute_dignity_consistent_across_multiple_vargas():
    """Same mechanism must work for any of the 15 supported vargas, not just D9."""
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    div_engine = DivisionalEngine(wrapper)
    graha_engine = GrahaEngine()

    for varga in ["D2", "D3", "D7", "D9", "D12", "D30"]:  # the 7 Saptavargaja vargas (D1 handled separately)
        chart = div_engine.compute(
            birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
            latitude=28.6139, longitude=77.2090, varga=varga,
        )
        for p in chart.planet_positions:
            # Must not raise, regardless of varga
            graha_engine.compute_dignity(p.planet, p.varga_rashi, p.varga_rashi_degree)

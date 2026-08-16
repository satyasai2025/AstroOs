"""
Unit tests for PrashnaEngine (Prashna Arudha seed lookup + the six Sphutas).

The 249-entry Arudha table and the sphuta formulas were taken verbatim from
PyJHora (github.com/naturalstupid/PyJHora) — see apps/api/domain/prashna.py's
module docstring. These tests check the table was transcribed correctly and
that the sphuta arithmetic matches the source formulas; they do NOT
independently re-verify the underlying classical formulas against a second
source (no JHora export for a Prashna chart is available yet).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.domain.prashna import PRASNA_KP_249_TABLE
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.prashna_engine import PrashnaEngine

_BIRTH = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)  # 04:57:40 IST 30-Jun-1971
_LAT, _LON = 22.3, 73.2


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture(scope="module")
def engine(wrapper: EphemerisWrapper) -> PrashnaEngine:
    return PrashnaEngine(wrapper)


# ── Table integrity ──────────────────────────────────────────────────────────

def test_table_has_249_entries():
    assert len(PRASNA_KP_249_TABLE) == 249


def test_table_arcs_are_contiguous_and_cover_full_zodiac():
    prev_global_end = 0.0
    for rashi_idx, _nak, start, end, *_ in PRASNA_KP_249_TABLE:
        global_start = rashi_idx * 30.0 + start
        global_end = rashi_idx * 30.0 + end
        assert global_start == pytest.approx(prev_global_end, abs=1e-6)
        assert global_end > global_start
        prev_global_end = global_end
    assert prev_global_end == pytest.approx(360.0, abs=1e-6)


# ── Prashna Arudha (chart-free lookup) ───────────────────────────────────────

def test_arudha_seed_1_is_start_of_ashwini_ruled_by_ketu(engine: PrashnaEngine):
    result = engine.arudha_from_seed(1)
    assert result.rashi == "aries"
    assert result.nakshatra == "ashwini"
    assert result.sign_lord == "mars"
    assert result.star_lord == "ketu"
    assert result.sub_lord == "ketu"  # first sub of a nakshatra is always its own lord
    assert 0.0 <= result.sidereal_longitude < 1.0


def test_arudha_seed_249_is_end_of_zodiac(engine: PrashnaEngine):
    result = engine.arudha_from_seed(249)
    assert result.rashi == "pisces"
    assert result.sign_lord == "jupiter"
    assert result.star_lord == "mercury"
    assert result.sub_lord == "saturn"
    assert 358.0 < result.sidereal_longitude < 360.0


@pytest.mark.parametrize("seed", [0, -1, 250, 1000])
def test_arudha_rejects_out_of_range_seed(engine: PrashnaEngine, seed: int):
    with pytest.raises(ValueError):
        engine.arudha_from_seed(seed)


# ── Sphutas (chart-dependent) ────────────────────────────────────────────────

def test_sphutas_are_all_valid_longitudes(engine: PrashnaEngine):
    result = engine.compute_sphutas(_BIRTH, _LAT, _LON, ayanamsa="lahiri")
    assert len(result.sphutas) == 6
    names = [s.name for s in result.sphutas]
    assert names == [
        "trisphuta", "chatursphuta", "panchasphuta",
        "pranasphuta", "dehasphuta", "mrityusphuta",
    ]
    for s in result.sphutas:
        assert 0.0 <= s.sidereal_longitude < 360.0


def test_trisphuta_equals_lagna_plus_moon_plus_gulika(engine: PrashnaEngine, wrapper: EphemerisWrapper):
    from apps.api.services.ephemeris_wrapper import datetime_to_jd
    from apps.api.services.upagraha_engine import UpagrahaEngine

    result = engine.compute_sphutas(_BIRTH, _LAT, _LON, ayanamsa="lahiri")
    tri = next(s for s in result.sphutas if s.name == "trisphuta")

    with wrapper.sidereal_mode("lahiri"):
        jd = datetime_to_jd(_BIRTH)
        moon_lon = wrapper.to_sidereal(
            wrapper.get_planet_position("moon", jd).longitude, wrapper.get_ayanamsa(jd)
        )
    expected = (result.ascendant_longitude + moon_lon + result.gulika_longitude) % 360.0
    assert tri.sidereal_longitude == pytest.approx(expected, abs=1e-6)

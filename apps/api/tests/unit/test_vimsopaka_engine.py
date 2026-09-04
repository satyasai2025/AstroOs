"""
AstroOS — Vimsopaka Engine Unit Tests

Verifies:
- Scheme weight sums (all 4 schemes sum to exactly 20.0)
- Vimsopaka category classification (Ati Purna, Purna, Madhya, Alpa)
- VimsopakaEngine compute_all execution and outputs for 7 classical planets
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.vimsopaka_engine import (
    SCHEME_WEIGHTS,
    VimsopakaEngine,
    classify_vimsopaka,
)

_EPHE_PATH = "data/ephemeris"


def test_vimsopaka_scheme_weights_sum_to_twenty():
    """Verify that every Parashari scheme's total weight is exactly 20.0."""
    for scheme_name, weights in SCHEME_WEIGHTS.items():
        total_weight = sum(weights.values())
        assert pytest.approx(total_weight, rel=1e-5) == 20.0, (
            f"Scheme '{scheme_name}' total weight is {total_weight}, expected 20.0"
        )


def test_classify_vimsopaka():
    """Verify classification bands."""
    assert classify_vimsopaka(18.5) == "Ati Purna"
    assert classify_vimsopaka(15.0) == "Ati Purna"
    assert classify_vimsopaka(14.99) == "Purna"
    assert classify_vimsopaka(10.0) == "Purna"
    assert classify_vimsopaka(9.99) == "Madhya"
    assert classify_vimsopaka(5.0) == "Madhya"
    assert classify_vimsopaka(4.99) == "Alpa"
    assert classify_vimsopaka(0.0) == "Alpa"


def test_vimsopaka_engine_compute_all():
    """Test full computation of Vimsopaka Bala for a sample birth chart."""
    ephemeris_wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(ephemeris_wrapper)
    birth_dt = datetime(1990, 5, 15, 12, 0, tzinfo=timezone.utc)
    lat = 28.6139
    lon = 77.2090

    d1_chart = horoscope_engine.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
    )

    engine = VimsopakaEngine(ephemeris_wrapper=ephemeris_wrapper)
    result = engine.compute_all(
        d1_chart,
        birth_datetime_utc=birth_dt,
        latitude=lat,
        longitude=lon,
    )

    assert len(result.planets) == 7
    planet_names = {p.planet for p in result.planets}
    assert planet_names == {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}

    for p in result.planets:
        # Check all 4 schemes exist for each planet
        for scheme in [p.shadvarga, p.saptavarga, p.dasavarga, p.shodasavarga]:
            assert 0.0 <= scheme.vimsopaka_score <= 20.0
            assert scheme.total_weight == 20.0
            assert scheme.category in {"Ati Purna", "Purna", "Madhya", "Alpa"}
            assert len(scheme.varga_breakdown) > 0

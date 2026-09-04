"""
Unit tests for Non-Luminous Upagrahas & Gulika/Mandi Engine.
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.upagraha_engine import UpagrahaEngine


def test_arkadosha_mathematical_closure():
    engine = UpagrahaEngine()
    dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    rep = engine.compute_upagrahas(
        birth_datetime=dt,
        latitude=22.30,
        longitude=73.18,
    )

    # BPHS Ch. 86 mathematical closure: Upaketu + 30° == Sun
    sun_lon = rep.sun_longitude
    upaketu_lon = rep.upaketu.longitude
    closure_diff = abs((upaketu_lon + 30.0) % 360.0 - sun_lon)
    assert closure_diff < 0.05, f"Arkadosha cycle does not close: {upaketu_lon}+30 vs {sun_lon}"

    # All 5 Arkadoshas must be generated
    assert rep.dhooma.longitude >= 0
    assert rep.vyatipata.longitude >= 0
    assert rep.parivesha.longitude >= 0
    assert rep.indrachapa.longitude >= 0
    assert rep.upaketu.longitude >= 0

    # Gulika must be generated with Upachaya flag
    assert 1 <= rep.gulika_house <= 12
    assert rep.gulika_is_upachaya == (rep.gulika_house in (3, 6, 10, 11))

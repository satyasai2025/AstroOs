"""
AstroOS — Unit Tests for Canonical Integration Spine
=====================================================
Validates the master integration pipeline:
  Single Birth Chart -> Complete Unified Execution Across ALL Platform Engines.
"""

from datetime import datetime, timezone
import pytest

from apps.api.domain.canonical_spine_schema import SpineBirthInput
from apps.api.services.canonical_spine import CanonicalIntegrationSpine


def test_canonical_integration_spine_end_to_end():
    """Verify that a single birth chart flows end-to-end through all engines with 100% invariant consistency."""
    spine = CanonicalIntegrationSpine()

    # Living birth chart: 1990-05-15 10:30:00 UTC, New Delhi (28.6139° N, 77.2090° E)
    birth_dt = datetime(1990, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
    target_dt = datetime(2026, 9, 4, 0, 0, 0, tzinfo=timezone.utc)

    inp = SpineBirthInput(
        native_id="native_delhi_1990",
        birth_datetime=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        target_query_datetime=target_dt,
    )

    response = spine.process_chart(inp)

    # 1. Ephemeris & Planets Verification
    assert len(response.planets) >= 7
    sun = next(p for p in response.planets if p.planet == "sun")
    assert 0.0 <= sun.sidereal_longitude < 360.0
    assert 1 <= sun.dignity_tier <= 7
    assert sun.main_strength_units in [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
    assert 1 <= sun.bhava_number <= 12

    # 2. Bhavachalita Houses Verification
    assert len(response.bhavachalita_houses) == 12
    for h in response.bhavachalita_houses:
        assert 1 <= h.house_number <= 12
        assert h.lord != ""
        assert 0.0 <= h.midpoint_deg < 360.0

    # 3. Active Dasha Verification
    assert len(response.active_dashas) > 0
    vims = response.active_dashas[0]
    assert vims.system_name == "vimshottari"
    assert "MD" in vims.active_levels
    assert "AD" in vims.active_levels

    # 4. Ashtakavarga & SAV 337 Invariant
    assert response.ashtakavarga.sav_grand_total == 337
    assert sum(response.ashtakavarga.sav_rashi_bindus.values()) == 337
    assert len(response.ashtakavarga.shodhya_pindas) == 7
    assert response.ashtakavarga.gochara_filter_tier in ["all_8_vargas", "seven_grahas", "six_slow_grahas"]

    # 5. Canonical Drishti Verification
    assert response.drishti.total_active_aspects > 0
    assert len(response.drishti.bhavesha_protection_map) == 12
    # Jha's 50% baseline rule: All houses must have at least 30.0 virupas of protection!
    for h_num, prot in response.drishti.bhavesha_protection_map.items():
        assert prot >= 30.0

    # 6. Maraka & Badhaka Verification
    assert response.maraka_badhaka.lagna_modality in ["chara", "sthira", "dvisvabhava"]
    assert response.maraka_badhaka.badhaka_house in [7, 9, 11]
    assert len(response.maraka_badhaka.primary_marakas) >= 1

    # 7. Cross-Engine Invariant Consistency
    assert response.cross_engine_consistency.sav_checksum_pass is True
    assert response.cross_engine_consistency.dasha_timeline_conservation is True
    assert response.cross_engine_consistency.invariant_status == "100% CANONICAL PASS"
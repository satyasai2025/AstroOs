"""
AstroOS — Unit Tests for Gochara Rekha Filter (Boundary Value Analysis)
=======================================================================
Validates Jha's exact duration-based transit Ashtakavarga filtering rules:
  "In Sarva-rekha, all 8 vargas are shown if number of days is <-48,
   else lagna-rekha is omitted upto number of days <1096,
   above which even Chandra-rekha is omitted in Sarva-rekha."

Boundary Tests:
  - Day 47:  < 48   -> Tier 1 (All 8 vargas, 386 bindus)
  - Day 48:  == 48  -> Tier 2 (Lagna-rekha omitted, 337 bindus)
  - Day 49:  > 48   -> Tier 2 (Lagna-rekha omitted, 337 bindus)
  - Day 1095: < 1096 -> Tier 2 (Lagna-rekha omitted, 337 bindus)
  - Day 1096: == 1096-> Tier 3 (Lagna and Moon omitted, 288 bindus)
  - Day 1097: > 1096 -> Tier 3 (Lagna and Moon omitted, 288 bindus)
"""

import pytest

from apps.api.services.ashtakavarga.gochara_rekha_filter import (
    GocharaRekhaFilter,
    RekhaFilterTier,
    TOTAL_8_VARGAS,
    TOTAL_6_VARGAS,
)
from packages.shared.ashtakavarga_bindu_table import EXPECTED_GRAND_TOTAL


def test_short_term_transit_boundary_day_47_and_48():
    """Boundary test at 48 days: 47 days gets 8 vargas (386 bindus), 48 days omits lagna-rekha (337 bindus)."""
    filter_svc = GocharaRekhaFilter()

    # 47 days: Short-term (< 48)
    res_47 = filter_svc.evaluate_transit_filter(duration_days=47)
    assert res_47.tier == RekhaFilterTier.ALL_8_VARGAS
    assert "lagna" in res_47.included_contributors
    assert "moon" in res_47.included_contributors
    assert len(res_47.included_contributors) == 8
    assert res_47.expected_total_bindus == 386
    assert res_47.omitted_contributors == []

    # 48 days: Medium-term boundary (48 <= d < 1096)
    res_48 = filter_svc.evaluate_transit_filter(duration_days=48)
    assert res_48.tier == RekhaFilterTier.SEVEN_GRAHAS_STANDARD
    assert "lagna" in res_48.omitted_contributors
    assert "moon" in res_48.included_contributors
    assert len(res_48.included_contributors) == 7
    assert res_48.expected_total_bindus == 337

    # 49 days: Just above 48
    res_49 = filter_svc.evaluate_transit_filter(duration_days=49)
    assert res_49.tier == RekhaFilterTier.SEVEN_GRAHAS_STANDARD
    assert res_49.expected_total_bindus == 337


def test_long_term_transit_boundary_day_1095_and_1096():
    """Boundary test at 1096 days: 1095 days has Moon included (337 bindus), 1096 days omits both Lagna and Moon (288 bindus)."""
    filter_svc = GocharaRekhaFilter()

    # 1095 days: Just below 1096
    res_1095 = filter_svc.evaluate_transit_filter(duration_days=1095)
    assert res_1095.tier == RekhaFilterTier.SEVEN_GRAHAS_STANDARD
    assert "moon" in res_1095.included_contributors
    assert "lagna" in res_1095.omitted_contributors
    assert res_1095.expected_total_bindus == 337

    # 1096 days: Long-term boundary (>= 1096)
    res_1096 = filter_svc.evaluate_transit_filter(duration_days=1096)
    assert res_1096.tier == RekhaFilterTier.SIX_SLOW_GRAHAS
    assert "lagna" in res_1096.omitted_contributors
    assert "moon" in res_1096.omitted_contributors
    assert len(res_1096.included_contributors) == 6
    assert res_1096.expected_total_bindus == 288

    # 1097 days: Just above 1096
    res_1097 = filter_svc.evaluate_transit_filter(duration_days=1097)
    assert res_1097.tier == RekhaFilterTier.SIX_SLOW_GRAHAS
    assert res_1097.expected_total_bindus == 288


def test_invalid_duration_days():
    """Verify that zero or negative duration raises ValueError."""
    filter_svc = GocharaRekhaFilter()
    with pytest.raises(ValueError, match="duration_days must be an integer > 0"):
        filter_svc.evaluate_transit_filter(duration_days=0)

    with pytest.raises(ValueError, match="duration_days must be an integer > 0"):
        filter_svc.evaluate_transit_filter(duration_days=-10)
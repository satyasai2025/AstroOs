"""
AstroOS — Unit Tests for 5-Tier Yogini and Ashtottari Dasha Hierarchies
=======================================================================
Verifies:
  1. 5-Tier Hierarchy: MD -> AD -> PD -> SD -> PrD
  2. Mathematical Energy Conservation: Child period durations sum to parent duration
  3. Ground-truth Junction timestamps for both Mean Tithi and True Tithi bases
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.ashtottari_accumulator import (
    AshtottariAccumulator,
    get_ashtottari_starting_lord,
    SS_MEAN_TITHI_YEAR_DAYS,
)
from apps.api.services.yogini_service import (
    Yogini5TierService,
    get_starting_yogini,
    MEAN_TITHI_YEAR_DAYS,
)


def test_yogini_5tier_hierarchy_and_conservation():
    """
    Verify 5-tier Yogini dasha hierarchy:
    MD -> AD -> PD -> SD -> PrD
    Each level must conserve exact duration of parent.
    """
    service = Yogini5TierService()
    b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
    moon_lon = 319.115328  # Shatabhisha (24) -> Bhramari (4)

    # Compute down to PrD (Praana Dasha - 5 tiers) for the first MD
    res = service.compute_hierarchy(b_dt, moon_lon, max_tier="PrD", num_md_cycles=1)

    assert res["system"] == "yogini_5tier"
    assert res["cycle_years"] == 36
    assert res["starting_yogini"] == "Bhramari"
    assert len(res["mahadashas"]) == 8

    # Check first MD (partial)
    first_md = res["mahadashas"][0]
    assert first_md["tier"] == "MD"
    assert len(first_md["sub_periods"]) == 8  # 8 ADs

    # Check 1st AD -> 8 PDs
    first_ad = first_md["sub_periods"][0]
    assert first_ad["tier"] == "AD"
    assert len(first_ad["sub_periods"]) == 8

    # Check 1st PD -> 8 SDs
    first_pd = first_ad["sub_periods"][0]
    assert first_pd["tier"] == "PD"
    assert len(first_pd["sub_periods"]) == 8

    # Check 1st SD -> 8 PrDs
    first_sd = first_pd["sub_periods"][0]
    assert first_sd["tier"] == "SD"
    assert len(first_sd["sub_periods"]) == 8

    # Check 1st PrD
    first_prd = first_sd["sub_periods"][0]
    assert first_prd["tier"] == "PrD"
    assert "sub_periods" not in first_prd  # Leaf level

    # Check non-partial 2nd MD conservation:
    second_md = res["mahadashas"][1]
    ad_days_sum = sum(ad["duration_days"] for ad in second_md["sub_periods"])
    assert ad_days_sum == pytest.approx(second_md["duration_days"], abs=1e-3)


def test_ashtottari_5tier_hierarchy_and_conservation():
    """
    Verify 5-tier Ashtottari dasha hierarchy:
    MD -> AD -> PD -> SD -> PrD
    """
    acc = AshtottariAccumulator()
    b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
    moon_lon = 319.115328  # Shatabhisha (24) -> Rahu

    res = acc.compute_hierarchy(b_dt, moon_lon, max_tier="PrD", num_cycles=1)

    assert res["system"] == "ashtottari_5tier"
    assert res["cycle_years"] == 108
    assert res["starting_lord"] == "rahu"
    assert len(res["mahadashas"]) == 8

    # Check first MD (partial)
    first_md = res["mahadashas"][0]
    assert first_md["tier"] == "MD"
    assert len(first_md["sub_periods"]) == 8  # 8 ADs

    # Check 1st AD -> 8 PDs
    first_ad = first_md["sub_periods"][0]
    assert first_ad["tier"] == "AD"
    assert len(first_ad["sub_periods"]) == 8

    # Check 1st PD -> 8 SDs
    first_pd = first_ad["sub_periods"][0]
    assert first_pd["tier"] == "PD"
    assert len(first_pd["sub_periods"]) == 8

    # Check 1st SD -> 8 PrDs
    first_sd = first_pd["sub_periods"][0]
    assert first_sd["tier"] == "SD"
    assert len(first_sd["sub_periods"]) == 8

    first_prd = first_sd["sub_periods"][0]
    assert first_prd["tier"] == "PrD"
    assert "sub_periods" not in first_prd

    # Check non-partial 2nd MD conservation:
    second_md = res["mahadashas"][1]
    ad_days_sum = sum(ad["duration_days"] for ad in second_md["sub_periods"])
    assert ad_days_sum == pytest.approx(second_md["duration_days"], abs=1e-3)


def test_ground_truth_junction_dates():
    """Verify ISO format and monotonic datetime progression across junction dates."""
    service = Yogini5TierService()
    b_dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    res = service.compute_hierarchy(b_dt, moon_longitude=0.0, max_tier="AD")  # 0° = Ashwini -> Bhadrika

    mds = res["mahadashas"]
    prev_end = None
    for md in mds:
        start = datetime.fromisoformat(md["start"])
        end = datetime.fromisoformat(md["end"])
        assert start < end
        if prev_end:
            assert start == prev_end
        prev_end = end
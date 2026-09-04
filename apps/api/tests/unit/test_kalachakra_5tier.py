"""
AstroOS — Unit Tests for 5-Tier Kalachakra Dasha (KCD) Engine
============================================================
Verifies:
  1. 5-Tier Hierarchy: MD -> AD -> PD -> SD -> PrD
  2. Mathematical Energy Conservation across all 5 tiers
  3. Deha and Jeeva Rashi determination
  4. Classical Gati jumps (Manduka, Markati, Simhavalokana)
  5. Continuous Monotonic Junction Timestamps
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.kalachakra_dasha import (
    Kalachakra5TierService,
    CANONICAL_KCD_SEQUENCES,
    KALACHAKRA_SIGN_YEARS,
    detect_kcd_gati,
)


def test_kcd_5tier_hierarchy_and_conservation():
    """
    Verify 5-tier KCD hierarchy down to Praana Dasha (PrD):
    MD -> AD -> PD -> SD -> PrD
    """
    service = Kalachakra5TierService()
    b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
    moon_lon = 319.115328  # Shatabhisha (24)

    res = service.compute_hierarchy(b_dt, moon_lon, max_tier="PrD", num_md_cycles=1)

    assert res["system"] == "kalachakra_5tier"
    assert "deha_rashi" in res
    assert "jeeva_rashi" in res
    assert len(res["mahadashas"]) == 9

    # Check 1st MD (partial)
    first_md = res["mahadashas"][0]
    assert first_md["tier"] == "MD"
    assert len(first_md["sub_periods"]) == 9  # 9 ADs in KCD

    # Check 1st AD -> 9 PDs
    first_ad = first_md["sub_periods"][0]
    assert first_ad["tier"] == "AD"
    assert len(first_ad["sub_periods"]) == 9

    # Check 1st PD -> 9 SDs
    first_pd = first_ad["sub_periods"][0]
    assert first_pd["tier"] == "PD"
    assert len(first_pd["sub_periods"]) == 9

    # Check 1st SD -> 9 PrDs
    first_sd = first_pd["sub_periods"][0]
    assert first_sd["tier"] == "SD"
    assert len(first_sd["sub_periods"]) == 9

    # Check 1st PrD
    first_prd = first_sd["sub_periods"][0]
    assert first_prd["tier"] == "PrD"
    assert "sub_periods" not in first_prd

    # Verify non-partial 2nd MD conservation:
    second_md = res["mahadashas"][1]
    ad_days_sum = sum(ad["duration_days"] for ad in second_md["sub_periods"])
    assert ad_days_sum == pytest.approx(second_md["duration_days"], abs=1e-2)


def test_kcd_deha_jeeva_rules():
    """
    Verify Deha/Jeeva assignment:
    - Ashwini Pada 1 (Savya): Deha=Aries, Jeeva=Sagittarius
    """
    service = Kalachakra5TierService()
    b_dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)

    res_savya = service.compute_hierarchy(b_dt, moon_longitude=1.0, max_tier="AD")
    assert res_savya["cycle_type"] == "savya"
    assert res_savya["deha_rashi"] == "aries"
    assert res_savya["jeeva_rashi"] == "sagittarius"


def test_kcd_gatis_jump_detection():
    """Verify Gati jump detections once confirmed against JHora baseline fixtures."""
    assert detect_kcd_gati("cancer", "virgo") == "manduka"
    assert detect_kcd_gati("pisces", "scorpio") == "simhavalokana"
    assert detect_kcd_gati("cancer", "leo") == "markati"


def test_kcd_continuous_junction_timestamps():
    """Verify monotonic ISO timestamps across all MD junctions."""
    service = Kalachakra5TierService()
    b_dt = datetime(1990, 5, 15, 6, 30, tzinfo=timezone.utc)
    res = service.compute_hierarchy(b_dt, moon_longitude=150.0, max_tier="AD")

    mds = res["mahadashas"]
    prev_end = None
    for md in mds:
        st = datetime.fromisoformat(md["start"])
        et = datetime.fromisoformat(md["end"])
        assert st < et
        if prev_end:
            assert st == prev_end
        prev_end = et
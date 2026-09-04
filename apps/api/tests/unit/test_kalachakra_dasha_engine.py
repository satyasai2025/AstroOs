"""
AstroOS — Unit Tests for Kalachakra Dasha (KCD) Canonical Engine
===============================================================
Verifies:
  1. Savya vs Apasavya classification
  2. Canonical 9-sign Navamsha sequences
  3. Deha and Jeeva determination
  4. Classical Gatis (Manduka, Markati, Simhavalokana)
  5. Antardasha duration conservation
  6. Golden Benchmark Builder KCD integration
"""

from datetime import datetime, timezone
import pytest

from apps.api.services.golden_benchmark_builder import GoldenBenchmarkBuilder
from apps.api.services.kalachakra_dasha_engine import (
    KalachakraDashaEngine,
    CANONICAL_KCD_SEQUENCES,
    SAVYA_NAKSHATRAS,
    APASAVYA_NAKSHATRAS,
    detect_gati,
)


def test_kcd_canonical_sequences_and_sign_counts():
    """Verify all 12 Navamsha sequences have exactly 9 signs."""
    assert len(CANONICAL_KCD_SEQUENCES) == 12
    for name, seq in CANONICAL_KCD_SEQUENCES.items():
        assert len(seq) == 9, f"Sequence for {name} must have 9 signs, got {len(seq)}"


def test_kcd_12_sign_years_sum_equals_100():
    """Verify classical 12-sign Kalachakra years sum exactly to 100 years."""
    from packages.shared.constants import KALACHAKRA_SIGN_YEARS
    assert sum(KALACHAKRA_SIGN_YEARS.values()) == 100
    assert KALACHAKRA_SIGN_YEARS["cancer"] == 16
    assert KALACHAKRA_SIGN_YEARS["pisces"] == 10
    assert KALACHAKRA_SIGN_YEARS["aries"] == 7


def test_kcd_gati_detection():
    """
    Verify classical Kalachakra Gatis (Leaps):
    - Manduka (Frog leap): Cancer -> Virgo, Leo -> Gemini
    - Markati (Monkey leap): Cancer -> Leo, Gemini -> Cancer
    - Simhavalokana (Lion's backward gaze): Pisces -> Scorpio, Sagittarius -> Aries
    """
    assert detect_gati("cancer", "virgo") == "manduka"
    assert detect_gati("virgo", "cancer") == "manduka"
    assert detect_gati("leo", "gemini") == "manduka"

    assert detect_gati("cancer", "leo") == "markati"

    assert detect_gati("pisces", "scorpio") == "simhavalokana"
    assert detect_gati("sagittarius", "aries") == "simhavalokana"

    # Regular progression has no special leap
    assert detect_gati("aries", "taurus") is None
    assert detect_gati("taurus", "gemini") is None


def test_kcd_deha_jeeva_and_savya_computation():
    """
    Verify KCD computation:
    For Ashwini (Nakshatra 1, Savya), Pada 1:
    - Navamsha: Mesha (Aries)
    - Sequence: Aries to Sagittarius (9 signs)
    - Deha Rashi = Aries (1st sign)
    - Jeeva Rashi = Sagittarius (9th sign)
    """
    engine = KalachakraDashaEngine()
    b_dt = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
    moon_lon = 1.0  # Ashwini Pada 1 (0° to 3°20')

    res = engine.compute_kalachakra_dasha(b_dt, moon_lon, num_cycles=1)

    assert res["system"] == "kalachakra"
    assert res["cycle_type"] == "savya"
    assert res["birth_nakshatra_number"] == 1
    assert res["pada"] == 1
    assert res["navamsha_sign"] == "mesha"
    assert res["deha_rashi"] == "aries"
    assert res["jeeva_rashi"] == "sagittarius"
    assert len(res["mahadashas"]) == 9

    # Verify Antardasha conservation for second MD
    second_md = res["mahadashas"][1]
    ad_days_sum = sum(ad["duration_days"] for ad in second_md["antardashas"])
    assert ad_days_sum == pytest.approx(second_md["duration_days"], abs=1e-2)


def test_golden_benchmark_builder_kcd_integration():
    """Verify GoldenBenchmarkBuilder outputs fully populated KCD."""
    builder = GoldenBenchmarkBuilder()
    rec = builder.build_native_record(
        native_id="D01",
        birth_date_str="1985-10-24",
        birth_time_str="14:30",
        lat=28.6139,
        lon=77.2090,
        tz_name="Asia/Kolkata",
    )

    kcd = rec["dashas"]["kcd"]
    assert "deha_rashi" in kcd
    assert "jeeva_rashi" in kcd
    assert "mahadasha" in kcd
    assert len(kcd["mahadasha"]) > 0
    assert kcd["deha_rashi"] != ""
    assert kcd["jeeva_rashi"] != ""
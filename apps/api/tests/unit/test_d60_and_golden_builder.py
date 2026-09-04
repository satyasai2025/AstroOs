"""
AstroOS — Unit Tests for D60 Deities, Yogini, Ashtottari, and Golden Benchmark Builder
"""

import pytest
from apps.api.services.ashtottari_dasha import (
    ASHTOTTARI_ORDER,
    TOTAL_ASHTOTTARI_YEARS,
    get_ashtottari_lord_by_nakshatra,
    compute_ashtottari_dasha_tree,
)
from apps.api.services.d60_deities import (
    get_d60_deity,
    evaluate_chart_d60_deities,
    BPHS_D60_DEITIES,
    JATAKA_PARIJATA_D60_DEITIES,
)
from apps.api.services.golden_benchmark_builder import GoldenBenchmarkBuilder
from apps.api.services.yogini_dasha import (
    TOTAL_YOGINI_YEARS,
    YOGINI_ORDER,
    get_yogini_by_nakshatra,
    compute_yogini_dasha_tree,
)


def test_d60_deity_counts_and_bphs_parijata_tables():
    """Verify both tables have exactly 60 deities."""
    assert len(BPHS_D60_DEITIES) == 60
    assert len(JATAKA_PARIJATA_D60_DEITIES) == 60

    assert BPHS_D60_DEITIES[0][2] == "Ghora"
    assert BPHS_D60_DEITIES[0][3] == "krura"
    assert JATAKA_PARIJATA_D60_DEITIES[0][2] == "Ghora"

    assert BPHS_D60_DEITIES[59][2] == "Chandrarekha"
    assert JATAKA_PARIJATA_D60_DEITIES[59][2] == "Indurekha"


def test_d60_deity_odd_even_signs():
    """Verify odd/even reverse order for D60."""
    d_odd_start = get_d60_deity(0.25, tradition="bphs")
    assert d_odd_start.shashtiamsa_number == 1
    assert d_odd_start.deity_name_english == "Ghora"
    assert d_odd_start.nature == "krura"

    d_odd_end = get_d60_deity(29.75, tradition="bphs")
    assert d_odd_end.shashtiamsa_number == 60
    assert d_odd_end.deity_name_english == "Chandrarekha"

    d_even_start = get_d60_deity(30.25, tradition="bphs")
    assert d_even_start.shashtiamsa_number == 60
    assert d_even_start.deity_name_english == "Chandrarekha"

    d_even_end = get_d60_deity(59.75, tradition="bphs")
    assert d_even_end.shashtiamsa_number == 1
    assert d_even_end.deity_name_english == "Ghora"


def test_yogini_dasha_formula_and_energy_conservation():
    """
    Verify Yogini formula:
    Yogini Index = ((Nakshatra_Index + 3) % 8) + 1
    Ashwini (1) -> Bhadrika (5)
    Mrigashira (5) -> Mangala (1)
    Pushya (8) -> Bhramari (4)
    Uttara Phalguni (12) -> Sankata (8)
    """
    assert get_yogini_by_nakshatra(1)[1] == "Bhadrika"
    assert get_yogini_by_nakshatra(5)[1] == "Mangala"
    assert get_yogini_by_nakshatra(8)[1] == "Bhramari"
    assert get_yogini_by_nakshatra(12)[1] == "Sankata"

    # Verify total years sum to 36
    assert sum(y[3] for y in YOGINI_ORDER) == TOTAL_YOGINI_YEARS == 36

    # Test full Yogini Dasha computation
    from datetime import datetime, timezone
    b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
    moon_lon = 319.115328  # Shatabhisha (Nakshatra 24)
    # Nakshatra 24: ((24 + 3) % 8) + 1 = (27 % 8) + 1 = 3 + 1 = 4 (Bhramari)
    assert get_yogini_by_nakshatra(24)[1] == "Bhramari"

    tree = compute_yogini_dasha_tree(b_dt, moon_lon, num_cycles=1)
    assert tree["starting_yogini"] == "Bhramari"
    assert len(tree["mahadashas"]) == 8

    # Verify Antardasha duration conservation in a non-partial MD
    second_md = tree["mahadashas"][1]
    ad_days_sum = sum(ad["duration_days"] for ad in second_md["antardashas"])
    assert ad_days_sum == pytest.approx(second_md["duration_days"], abs=1)


def test_ashtottari_dasha_order_and_groupings():
    """
    Verify Ashtottari 108 years and 28 nakshatras alternating 3 and 4:
    Sun (3 naks, 6 yrs), Moon (4 naks, 15 yrs), Mars (3 naks, 8 yrs), Mercury (4 naks, 17 yrs),
    Saturn (3 naks, 10 yrs), Jupiter (4 naks, 19 yrs), Rahu (3 naks, 12 yrs), Venus (4 naks, 21 yrs).
    """
    assert sum(e[1] for e in ASHTOTTARI_ORDER) == TOTAL_ASHTOTTARI_YEARS == 108

    # Krittika (3) -> Sun
    assert get_ashtottari_lord_by_nakshatra(3)[0] == "sun"
    # Ardra (6) -> Moon
    assert get_ashtottari_lord_by_nakshatra(6)[0] == "moon"
    # Hasta (13) -> Mercury
    assert get_ashtottari_lord_by_nakshatra(13)[0] == "mercury"
    # Anuradha (17) -> Saturn
    assert get_ashtottari_lord_by_nakshatra(17)[0] == "saturn"

    from datetime import datetime, timezone
    b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
    moon_lon = 319.115328  # Shatabhisha (Nakshatra 24) -> Rahu (group 23, 24, 25)
    tree = compute_ashtottari_dasha_tree(b_dt, moon_lon, num_cycles=1)
    assert tree["starting_lord"] == "rahu"
    assert len(tree["mahadashas"]) == 8


def test_golden_benchmark_builder_conforms_to_canonical_schema_with_jha_verified_flag():
    """Verify GoldenBenchmarkBuilder generates record matching user's canonical schema including jha_verified flag."""
    builder = GoldenBenchmarkBuilder()
    rec = builder.build_native_record(
        native_id="D01",
        birth_date_str="1985-10-24",
        birth_time_str="14:30",
        lat=28.6139,
        lon=77.2090,
        tz_name="Asia/Kolkata",
        source_offset=527600,
        jha_verified=False,
    )

    assert rec["native_id"] == "D01"
    assert rec["birth"]["date"] == "1985-10-24"
    assert rec["graha_longitudes"]["sun"] == 187.238869
    assert len(rec["bhava_positions"]) == 12

    # Vargas
    assert "D9" in rec["vargas"]
    assert "D60" in rec["vargas"]
    assert rec["vargas"]["D60"]["sun"]["deity_english"] == "Kala"

    # Dashas: Vimshottari, Ashtottari, and Yogini all computed!
    dashas = rec["dashas"]
    assert len(dashas["vimshottari"]["mahadasha"]) > 0
    assert len(dashas["ashtottari"]["mahadasha"]) > 0
    assert len(dashas["yogini"]["mahadasha"]) > 0
    assert dashas["yogini"]["starting_yogini"] == "Bhramari"
    assert dashas["ashtottari"]["starting_lord"] == "rahu"

    # Provenance governance: jha_verified must strictly be False
    assert rec["provenance"]["jha_verified"] is False
    assert rec["provenance"]["source_offset"] == 527600
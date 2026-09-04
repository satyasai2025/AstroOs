"""
AstroOS — Unit Tests for KCD JHora-7.66 SSS Ground Truth Fixtures
================================================================
Validates Kalachakra 5-tier Engine against the 4 golden JHora SSS test fixtures:
  - Savya direct
  - Savya with Simhavalokana (Pisces -> Scorpio) + Manduka + Markati
  - Savya with Simhavalokana (Sagittarius -> Aries)
  - Apasavya reverse with inverted Deha/Jeeva
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest

from apps.api.services.kalachakra_dasha import (
    Kalachakra5TierService,
    CANONICAL_KCD_SEQUENCES,
    detect_kcd_gati,
)


def load_fixtures():
    p = Path(r"tests/golden_fixtures/kcd_jhora_sss_fixtures.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)["cases"]


@pytest.mark.parametrize("case", load_fixtures(), ids=lambda c: c["case_id"])
def test_kcd_against_jhora_sss_fixtures(case):
    service = Kalachakra5TierService()
    b_dict = case["birth_details"]
    dt_str = f"{b_dict['date']}T{b_dict['time']}+00:00"
    b_dt = datetime.fromisoformat(dt_str)
    moon_lon = case["moon_longitude"]

    res = service.compute_hierarchy(b_dt, moon_lon, max_tier="AD")

    # 1. Cycle Type
    assert res["cycle_type"] == case["cycle_type"]

    # 2. Deha and Jeeva Rashis
    assert res["deha_rashi"] == case["deha_rashi"]
    assert res["jeeva_rashi"] == case["jeeva_rashi"]

    # 3. Sequence matching
    actual_seq = [md["rashi"] for md in res["mahadashas"]]
    assert actual_seq == case["expected_sequence"]

    # 4. Gatis validation
    for exp_gati in case["gatis_present"]:
        detected = detect_kcd_gati(exp_gati["from"], exp_gati["to"])
        assert detected == exp_gati["type"]
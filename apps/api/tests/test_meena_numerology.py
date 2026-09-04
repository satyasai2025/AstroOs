"""
Unit and Integration Tests for Meena's Numerology Engine in AstroOS.
Verifies arithmetic exactness, user-facing story responses, zero jargon/hallucination,
repeated numbers synchronicity scanner, and ensures no Mahadevi names are exposed to the frontend.
"""

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from apps.api.main import create_app
from apps.api.services.meena_numerology_engine import AstroOSMeenaEngine


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_meena_core_calculations_exactness():
    """Verifies core birth profile calculation precision."""
    day, month, year = 29, 7, 1976
    moolank, bhagyank = AstroOSMeenaEngine.calculate_core_numbers(day, month, year)

    # 29 -> 2+9=11 -> 2
    assert moolank == 2
    # 29 + 7 + 1976 = 2012 -> 5
    assert bhagyank == 5

    # Name numbers
    names = AstroOSMeenaEngine.calculate_name_metrics(
        full_name="Bhagia Meena Rajesh",
        public_name="Meena Bhagia",
        daily_name="Meena"
    )
    # Chaldean checks
    assert names["ch_daily"] == 2      # MEENA: 4+5+5+5+1 = 20 -> 2
    assert names["ch_pub"] == 6        # MEENA BHAGIA: 20 + 13 = 33 -> 6
    assert names["ch_full"] == 5       # BHAGIA MEENA RAJESH: 13 + 20 + 17 = 50 -> 5

    # Pythagorean checks
    assert names["py_full"] == 1       # Sum = 73 -> 1
    assert names["soul_num"] == 1      # Vowels sum = 28 -> 1
    assert names["personality_num"] == 9 # Consonants sum = 45 -> 9
    assert names["balance_num"] == 6   # Initials B(2)+M(4)+R(9) = 15 -> 6

    # Challenges & Pinnacles
    challenges, pinnacles = AstroOSMeenaEngine.calculate_challenges_and_pinnacles(day, month, year, bhagyank)
    assert challenges["c1"] == 5
    assert challenges["c2"] == 3
    assert challenges["primary_c3"] == 2
    assert challenges["c4"] == 2

    assert pinnacles[0]["num"] == 9
    assert pinnacles[0]["end"] == 31  # 36 - 5 = 31
    assert pinnacles[1]["num"] == 7
    assert pinnacles[1]["end"] == 40  # 31 + 9 = 40
    assert pinnacles[2]["num"] == 7
    assert pinnacles[2]["end"] == 49  # 40 + 9 = 49
    assert pinnacles[3]["num"] == 3
    assert pinnacles[3]["end"] is None


def test_personal_cycles_2026():
    """Verifies Personal Year 1, August (PM 9) and September (PM 1 with gateway dates 9, 18, 27)."""
    day, month = 29, 7

    # Year 2026: 29 + 7 + 2026 -> 1
    py, pm_aug, pd_aug = AstroOSMeenaEngine.calculate_personal_cycles(day, month, 2026, 8)
    assert py == 1
    assert pm_aug == 9
    assert pd_aug[9] == 9
    assert pd_aug[18] == 9
    assert pd_aug[27] == 9

    # September 2026 (Month 9): PM = 1 (Matches PY!)
    _, pm_sep, pd_sep = AstroOSMeenaEngine.calculate_personal_cycles(day, month, 2026, 9)
    assert pm_sep == 1
    # Gateway dates: PY=1, PM=1, PD=1
    assert pd_sep[9] == 1
    assert pd_sep[18] == 1
    assert pd_sep[27] == 1


def test_api_report_endpoint(client):
    """Verifies the /api/v1/numerology/meena/report endpoint and ensures no Mahadevi names are in response."""
    payload = {
        "day": 29,
        "month": 7,
        "year": 1976,
        "full_name": "Bhagia Meena Rajesh",
        "public_name": "Meena Bhagia",
        "daily_name": "Meena",
        "target_year": 2026,
        "target_month": 9
    }
    response = client.post("/api/v1/numerology/meena/report", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "core_nature_story" in data
    assert "life_purpose_story" in data
    assert "growth_blindspots" in data
    assert len(data["growth_blindspots"]) >= 2
    assert "life_chapters" in data
    assert "five_year_roadmap" in data
    assert len(data["five_year_roadmap"]) == 6  # Target year + 5 years
    assert data["five_year_roadmap"][0]["year"] == 2026
    assert data["five_year_roadmap"][0]["personal_year_number"] == 1
    assert data["five_year_roadmap"][1]["year"] == 2027
    assert data["five_year_roadmap"][1]["personal_year_number"] == 2

    # Ensure NO Mahadevi names leaked into user-facing response text
    forbidden_names = ["Kali", "Kālī", "Tara", "Tārā", "Tripurasundari", "Tripura Sundari",
                       "Bhuvaneshwari", "Bhuvaneśvarī", "Bhairavi", "Bhairavī", "Chhinnamasta",
                       "Chinnamastā", "Dhumavati", "Dhūmāvatī", "Bagalamukhi", "Bagalāmukhī",
                       "Matangi", "Mātaṅgī", "Kamala", "Kamalā"]

    full_response_text = str(data).lower()
    for name in forbidden_names:
        assert name.lower() not in full_response_text, f"Proprietary archetype '{name}' was found in user response!"


def test_api_five_year_limit_enforcement(client):
    """Verifies that requesting beyond the 5-year window triggers a friendly 400 error."""
    payload = {
        "day": 29,
        "month": 7,
        "year": 1976,
        "full_name": "Bhagia Meena Rajesh",
        "target_year": datetime.now().year + 10  # Beyond 5-year limit
    }
    response = client.post("/api/v1/numerology/meena/report", json=payload)
    assert response.status_code == 400
    assert "5-year window" in response.json()["detail"]


def test_api_activity_finder_endpoint(client):
    """Verifies activity-specific date finder."""
    payload = {
        "day": 29,
        "month": 7,
        "year": 1976,
        "target_year": 2026,
        "target_month": 9,
        "activity_category": "shopping_deals"
    }
    response = client.post("/api/v1/numerology/meena/activity-finder", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_dates" in data
    assert 4 in data["recommended_dates"] or 13 in data["recommended_dates"] or 22 in data["recommended_dates"]


def test_api_repeated_number_scanner(client):
    """Verifies Meena's Repetition Count Law (<3 no value, 3 good, 4+ overload)."""
    # Exactly 3 digits -> Auspicious
    res_3 = client.post("/api/v1/numerology/meena/scan-repeated-number", json={"sequence": "333"})
    assert res_3.status_code == 200
    d3 = res_3.json()
    assert d3["digit_count"] == 3
    assert d3["is_favorable"] is True
    assert "Auspicious" in d3["signal_status"]

    # 4 digits -> Overload / Not good
    res_4 = client.post("/api/v1/numerology/meena/scan-repeated-number", json={"sequence": "1111"})
    assert res_4.status_code == 200
    d4 = res_4.json()
    assert d4["digit_count"] == 4
    assert d4["is_favorable"] is False
    assert "Overload" in d4["signal_status"]

    # 2 digits -> No synchronicity value
    res_2 = client.post("/api/v1/numerology/meena/scan-repeated-number", json={"sequence": "22"})
    assert res_2.status_code == 200
    d2 = res_2.json()
    assert d2["digit_count"] == 2
    assert d2["is_favorable"] is False
    assert "< 3 Digits" in d2["signal_status"]


def test_api_help_endpoint(client):
    """Verifies the help concepts endpoint."""
    response = client.get("/api/v1/numerology/meena/help")
    assert response.status_code == 200
    data = response.json()
    assert "method_overview" in data
    assert len(data["concepts"]) >= 5


def test_moolank_formula_complete_reduction(client):
    """Day 29 must show full chain: Day 29 -> 2 + 9 = 11 -> 1 + 1 = 2"""
    payload = {
        "day": 29, "month": 7, "year": 1976,
        "full_name": "Bhagia Meena Rajesh",
        "target_year": 2026, "target_month": 9
    }
    data = client.post("/api/v1/numerology/meena/report", json=payload).json()
    formula = data["calculation_audit"]["moolank_formula"]
    assert "11" in formula and "-> 2" in formula


def test_february_never_recommends_invalid_dates(client):
    """Feb 2026 (28 days) must never recommend 29/30/31."""
    payload = {
        "day": 29, "month": 7, "year": 1976,
        "full_name": "Bhagia Meena Rajesh",
        "target_year": 2026, "target_month": 2
    }
    data = client.post("/api/v1/numerology/meena/report", json=payload).json()
    all_dates = (
        data["peak_launch_dates"]
        + [d for a in data["activity_guide"] for d in a["best_dates"]]
    )
    assert max(all_dates) <= 28


def test_invalid_target_month_rejected():
    """target_month=13 must fail schema validation, not crash."""
    from apps.api.schemas.meena_numerology import MeenaNumerologyRequest
    with pytest.raises(Exception):
        MeenaNumerologyRequest(
            day=29, month=7, year=1976,
            full_name="Bhagia Meena Rajesh",
            target_month=13
        )


def test_non_repeated_sequence_rejected():
    from apps.api.services.meena_numerology_engine import AstroOSMeenaEngine
    with pytest.raises(ValueError):
        AstroOSMeenaEngine.scan_repeated_number("abc")
    with pytest.raises(ValueError):
        AstroOSMeenaEngine.scan_repeated_number("1212")


def test_five_year_window_engine_guard():
    from apps.api.services.meena_numerology_engine import AstroOSMeenaEngine
    with pytest.raises(ValueError, match="5-year window"):
        AstroOSMeenaEngine.generate_story_report(
            day=29, month=7, year=1976,
            full_name="Bhagia Meena Rajesh",
            target_year=datetime.now().year + 10
        )


def test_activity_finder_february_dates(client):
    """Verify activity-finder in Feb 2026 never recommends dates > 28."""
    payload = {
        "day": 29, "month": 7, "year": 1976,
        "target_year": 2026, "target_month": 2,
        "activity_category": "shopping_deals"
    }
    res = client.post("/api/v1/numerology/meena/activity-finder", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert all(d <= 28 for d in data["recommended_dates"])


def test_api_invalid_sequence_returns_client_error(client):
    """Verify invalid sequence returns 422 (schema reject) or 400 (engine reject), never 500."""
    res1 = client.post("/api/v1/numerology/meena/scan-repeated-number", json={"sequence": "abc"})
    assert res1.status_code == 422  # Pydantic schema pattern validation
    res2 = client.post("/api/v1/numerology/meena/scan-repeated-number", json={"sequence": "1212"})
    assert res2.status_code == 400  # Engine non-identical sequence ValueError


def test_activity_finder_schema_rejection():
    """Verify ActivityFinderRequest rejects invalid day and month."""
    from apps.api.schemas.meena_numerology import ActivityFinderRequest
    from datetime import datetime
    
    with pytest.raises(Exception):
        ActivityFinderRequest(
            day=35, month=7, target_month=9, activity_category="shopping_deals"
        )
    with pytest.raises(Exception):
        ActivityFinderRequest(
            day=15, month=7, target_month=13, activity_category="shopping_deals"
        )


def test_schema_dynamic_default_year():
    """Verify MeenaNumerologyRequest defaults to current year dynamically."""
    from apps.api.schemas.meena_numerology import MeenaNumerologyRequest
    from datetime import datetime
    
    req = MeenaNumerologyRequest(
        day=29, month=7, year=1976, full_name="Bhagia Meena Rajesh"
    )
    assert req.target_year == datetime.now().year
    assert req.target_month == datetime.now().month


def test_chaldean_reduced_nine_maps_to_abundance_archetype(client):
    """Verify that a name reducing to 9 via Chaldean compound (e.g. 'Pi' -> 8+1=9) produces valid Chaldean 9 and full report."""
    payload = {
        "day": 5, "month": 5, "year": 1990,
        "full_name": "Pi",
        "target_year": 2026, "target_month": 9
    }
    res = client.post("/api/v1/numerology/meena/report", json=payload)
    assert res.status_code == 200
    data = res.json()
    
    # Check name vibrations
    name_vibs = data["name_vibrations"]
    full_vib = next(v for v in name_vibs if "Legal" in v["name_type"])
    assert full_vib["chaldean_reduced"] == 9
    assert full_vib["chaldean_compound"] == 9


def test_maturity_balance_and_hidden_passion(client):
    """Verify Maturity Number (Name+Destiny), Balance Number (Initials), and Hidden Passion (Most frequent digit)."""
    payload = {
        "day": 29, "month": 7, "year": 1976,
        "full_name": "Bhagia Meena Rajesh",
        "target_year": 2026, "target_month": 9
    }
    res = client.post("/api/v1/numerology/meena/report", json=payload)
    assert res.status_code == 200
    data = res.json()
    audit = data["calculation_audit"]

    # Name 1 + Destiny 5 = 6
    assert audit["maturity_number"] == 6
    assert "Maturity" in audit["maturity_formula"]

    # Initials B(2) + M(4) + R(9) = 15 -> 6
    assert audit["balance_number"] == 6
    assert "Initials" in audit["balance_formula"]

    # Most frequent letter digit in BHAGIA MEENA RAJESH is 1 (occurs 6 times: A, A, A, A, J, S)
    assert audit["hidden_passion_number"] == 1
    assert "Hidden" in audit["hidden_passion_formula"] or "frequent" in audit["hidden_passion_formula"]

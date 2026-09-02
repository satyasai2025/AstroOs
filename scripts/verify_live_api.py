"""
Live Verification Script for AstroOS Canonical API Endpoints.
"""

from datetime import datetime
import json
import sys
import httpx

sys.path.insert(0, ".")

from apps.api.security.jwt import create_access_token


def test_live_api():
    base_url = "http://127.0.0.1:8888"


    print("=" * 70)
    print("ASTROOS LIVE SERVER VERIFICATION")
    print("=" * 70)

    # 1. Generate valid test JWT token
    token, jti = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        role="PRACTITIONER",
        additional_claims={"email": "researcher@astroos.io"},
    )
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Generated Valid RS256 JWT Token (JTI: {jti[:8]}...)")

    # 2. Test Canonical Synthesis Endpoint
    payload = {
        "birth_date_iso": "1971-06-29T23:27:40Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "target_year": 2025,
    }
    print(f"\nCalling POST {base_url}/api/v1/phalita/canonical-synthesis...")
    r = httpx.post(f"{base_url}/api/v1/phalita/canonical-synthesis", json=payload, headers=headers, timeout=15.0)
    print(f"Status Code: {r.status_code}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    data = r.json()
    print("[OK] D1 Vishamabhava Lagna-Madhya:", round(data["lagna_madhya_deg"], 2), "deg")
    print("[OK] D1 Madhya-Lagna (MC):", round(data["madhya_lagna_deg"], 2), "deg")
    print("[OK] Houses Computed:", len(data["houses"]), "Bhavas")
    print("[OK] Sudarshana Chakra LK:", data["sudarshana_chakra"]["lagna_rashi"], "(Tri-Lagna Active:", data["sudarshana_chakra"]["is_tri_lagna_active"], ")")
    print("[OK] D10 Venus Synthesis:", data["divisional_synthesis_d10"]["Venus"]["verdict"])
    print("[OK] D10 Mars Synthesis :", data["divisional_synthesis_d10"]["Mars"]["verdict"])
    print("[OK] VPC Solar Return   :", data["vpc_solar_return"]["vpc_datetime_utc"])
    print("[OK] VPC SCD Progressed : House H" + str(data["vpc_solar_return"]["scd_annual_house"]))
    print("[OK] TPhalitCore Score  :", round(data["tphalit_signed_state"]["deterministic_score"], 4))

    # 3. Test VPC Timeline Endpoint
    vpc_payload = {
        "birth_date_iso": "1971-06-29T23:27:40Z",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "start_year": 2024,
        "end_year": 2027,
    }
    print(f"\nCalling POST {base_url}/api/v1/phalita/vpc-timeline (2024 to 2027)...")
    r2 = httpx.post(f"{base_url}/api/v1/phalita/vpc-timeline", json=vpc_payload, headers=headers, timeout=15.0)
    print(f"Status Code: {r2.status_code}")
    assert r2.status_code == 200
    vpc_data = r2.json()
    for s in vpc_data["solar_returns"]:
        print(f"  * Year {s['year']} (Age {s['completed_age']}): Solar Return = {s['vpc_datetime_utc']} | SCD House = H{s['scd_annual_house']}")

    # 4. Test Noise Diagnostics Endpoint
    noise_payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "deterministic_score": 2.5,
        "planet_block_total": 1.8,
        "residual_error": 0.3,
        "varga_opposition_index": 0.1,
    }
    print(f"\nCalling POST {base_url}/api/v1/phalita/noise-diagnostics...")
    r3 = httpx.post(f"{base_url}/api/v1/phalita/noise-diagnostics", json=noise_payload, headers=headers, timeout=10.0)
    print(f"Status Code: {r3.status_code}")
    assert r3.status_code == 200
    noise_data = r3.json()
    print("[OK] Dominant Noise Category:", noise_data["dominant_noise_category"])
    print("[OK] Trustworthy Prediction :", noise_data["is_prediction_trustworthy"])
    print("[OK] Useful Noise Bandwidth :", noise_data["useful_noise_bandwidth"])


    print("\n" + "=" * 70)
    print(">>> LIVE BACKEND API VERIFICATION PASSED (100% SUCCESS) <<<")
    print("=" * 70)


if __name__ == "__main__":
    test_live_api()

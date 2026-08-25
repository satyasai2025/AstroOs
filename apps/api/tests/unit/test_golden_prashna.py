"""
Golden Prashna Case and Independent Astronomical Verification.

Golden Case Specs:
Question: Will I get this job?
Date: 22 Aug 2026
Local Time: 12:22 PM
Location: Pune, Maharashtra, India (Lat: 18.5204, Lon: 73.8567)
Timezone: Asia/Kolkata (IANA) -> Instant: 2026-08-22T06:52:00.000Z
"""

from __future__ import annotations
import zoneinfo
from datetime import datetime, timezone
import uuid
import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.dependencies import get_current_user_from_bearer, get_ephemeris_wrapper
from apps.api.domain.user import User, UserId, UserRole, UserStatus
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    datetime_to_jd,
    longitude_to_rashi,
    longitude_to_nakshatra,
)
from apps.api.services.prashna_engine import PrashnaEngine, _deg_to_dms


@pytest.fixture(scope="module")
def ephemeris() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture(scope="module")
def engine(ephemeris: EphemerisWrapper) -> PrashnaEngine:
    return PrashnaEngine(ephemeris)


def test_timezone_conversion_exact():
    """Verify Asia/Kolkata 2026-08-22 12:22:00 maps strictly to 2026-08-22 06:52:00 UTC."""
    tz = zoneinfo.ZoneInfo("Asia/Kolkata")
    local_dt = datetime(2026, 8, 22, 12, 22, 0, tzinfo=tz)
    utc_dt = local_dt.astimezone(timezone.utc)

    assert utc_dt.year == 2026
    assert utc_dt.month == 8
    assert utc_dt.day == 22
    assert utc_dt.hour == 6
    assert utc_dt.minute == 52
    assert utc_dt.second == 0
    assert utc_dt.isoformat() == "2026-08-22T06:52:00+00:00"


def test_golden_case_astronomical_outputs(ephemeris: EphemerisWrapper, engine: PrashnaEngine):
    """Independently calculate and freeze Golden Case canonical facts."""
    utc_dt = datetime(2026, 8, 22, 6, 52, 0, tzinfo=timezone.utc)
    lat = 18.5204
    lon = 73.8567

    jd = datetime_to_jd(utc_dt)
    ayan_val = ephemeris.get_ayanamsa(jd)
    assert 24.0 <= ayan_val <= 25.0

    # 1. Ascendant
    trop_asc, trop_cusps = ephemeris.get_ascendant_and_cusps(jd, lat, lon, "P")
    sid_asc = ephemeris.to_sidereal(trop_asc, ayan_val)
    asc_rashi, asc_deg = longitude_to_rashi(sid_asc)
    asc_nak = longitude_to_nakshatra(sid_asc)
    asc_lords = engine.get_kp_lords_for_longitude(sid_asc)

    assert asc_rashi == "libra"
    assert asc_nak.nakshatra == "vishakha"
    assert asc_nak.pada == 3
    assert asc_lords["sign_lord"] == "venus"
    assert asc_lords["star_lord"] == "jupiter"
    assert asc_lords["sub_lord"] == "sun"
    assert pytest.approx(sid_asc, abs=1e-3) == 209.1406

    # 2. Moon
    moon_pos = ephemeris.get_planet_position("moon", jd)
    sid_moon = ephemeris.to_sidereal(moon_pos.longitude, ayan_val)
    moon_rashi, moon_deg = longitude_to_rashi(sid_moon)
    moon_nak = longitude_to_nakshatra(sid_moon)
    moon_lords = engine.get_kp_lords_for_longitude(sid_moon)

    assert moon_rashi == "scorpio"
    assert moon_nak.nakshatra == "jyeshtha"
    assert moon_nak.pada == 4
    assert moon_lords["sign_lord"] == "mars"
    assert moon_lords["star_lord"] == "mercury"
    assert moon_lords["sub_lord"] == "saturn"
    assert pytest.approx(sid_moon, abs=1e-3) == 238.7873

    # 3. Panchanga / Ruling Planets
    rp = engine.get_ruling_planets(utc_dt, lat, lon)
    assert rp.day_lord == "saturn"
    assert rp.hora_lord in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

    # 4. Judgement
    j = engine.evaluate_judgement("Will I get this job?", utc_dt, lat, lon)
    assert j.verdict in ("YES", "NO", "MIXED")
    assert j.confidence_percentage >= 50
    assert len(j.key_evidences) >= 5
    assert len(j.supporting_rules) >= 4
    assert len(j.contradictions) >= 1
    assert "–" in j.timing.likely_window


def test_golden_case_determinism_multiple_runs(engine: PrashnaEngine):
    """Execute the exact same calculation 3 times and assert deterministic equality."""
    utc_dt = datetime(2026, 8, 22, 6, 52, 0, tzinfo=timezone.utc)
    lat = 18.5204
    lon = 73.8567

    runs = []
    for _ in range(3):
        j = engine.evaluate_judgement("Will I get this job?", utc_dt, lat, lon)
        rp = engine.get_ruling_planets(utc_dt, lat, lon)
        sph = engine.sphutas_for_chart(utc_dt, lat, lon)
        runs.append((j, rp, sph))

    for i in range(1, 3):
        j0, rp0, sph0 = runs[0]
        ji, rpi, sphi = runs[i]

        # Exact categorical values
        assert j0.verdict == ji.verdict
        assert j0.confidence_percentage == ji.confidence_percentage
        assert j0.strength_label == ji.strength_label
        assert j0.timing.likely_window == ji.timing.likely_window
        assert j0.timing.dasha_mahadasha == ji.timing.dasha_mahadasha
        assert j0.timing.antardasha == ji.timing.antardasha
        assert rp0.day_lord == rpi.day_lord
        assert rp0.hora_lord == rpi.hora_lord

        # Rules equality
        assert len(j0.supporting_rules) == len(ji.supporting_rules)
        for r0, ri in zip(j0.supporting_rules, ji.supporting_rules):
            assert r0.rule_id == ri.rule_id
            assert r0.triggered == ri.triggered
            assert r0.weight == ri.weight

        # Evidence equality
        assert len(j0.key_evidences) == len(ji.key_evidences)
        for e0, ei in zip(j0.key_evidences, ji.key_evidences):
            assert e0.factor == ei.factor
            assert e0.indication == ei.indication
            assert e0.weight == ei.weight

        # Sphutas numerical tolerance
        assert len(sph0.sphutas) == len(sphi.sphutas)
        for s0, si in zip(sph0.sphutas, sphi.sphutas):
            assert s0.name == si.name
            assert pytest.approx(s0.sidereal_longitude, abs=1e-7) == si.sidereal_longitude


def test_api_contract_validation(ephemeris: EphemerisWrapper):
    """Validate full API endpoint contracts, schemas, error codes, and edge cases."""
    user = User(
        id=UserId(uuid.UUID("00000000-0000-0000-0000-000000000001")),
        email="test@astroos.local",
        display_name="Test User",
        hashed_password="mock_hashed_pw",
        role=UserRole.RESEARCHER,
        status=UserStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    app.dependency_overrides[get_current_user_from_bearer] = lambda: user
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: ephemeris

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Valid full calculate
    payload = {
        "name": "Querent",
        "gender": "Male",
        "question": "Will I get this job?",
        "moment_utc": "2026-08-22T06:52:00Z",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "place_name": "Pune, Maharashtra, India",
        "timezone_offset": 5.5,
        "horary_number": None,
        "horary_system": "kp_249",
        "ayanamsa": "lahiri",
    }
    r = client.post("/api/v1/prashna/calculate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["question"] == "Will I get this job?"
    assert len(data["planets"]) == 9
    assert len(data["cusps"]) == 12
    assert data["cusps"][0]["sign"] == "Libra"
    assert data["judgement"]["verdict"] in ("YES", "NO", "MIXED")

    # 2. Missing question field -> 422
    invalid_no_q = dict(payload)
    del invalid_no_q["question"]
    r = client.post("/api/v1/prashna/calculate", json=invalid_no_q)
    assert r.status_code == 422

    # 3. Invalid latitude (> 90) -> 422
    inv_lat = dict(payload, latitude=95.0)
    r = client.post("/api/v1/prashna/calculate", json=inv_lat)
    assert r.status_code == 422

    # 4. Invalid longitude (> 180) -> 422
    inv_lon = dict(payload, longitude=200.0)
    r = client.post("/api/v1/prashna/calculate", json=inv_lon)
    assert r.status_code == 422

    # 5. Invalid horary seed number -> 422
    r = client.get("/api/v1/prashna/arudha", params={"seed_number": 999, "system": "kp_249"})
    assert r.status_code == 422

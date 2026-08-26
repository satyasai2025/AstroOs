"""
AstroOS — Unit tests for KP Governance, Ayanamsa Validation, Retrograde RP & Evidence Provenance
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from apps.api.config import get_settings
from apps.api.dependencies import get_ephemeris_wrapper
from apps.api.routers.kp import router as kp_router
from apps.api.schemas.kp import KPAnalysisRequest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.kp_rp_engine import KPRulingPlanetsEngine, RulingPlanetEntry, RulingPlanetsSnapshot
from apps.api.services.kp_engine import KPEngine, compute_event_evidence
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.transit_engine import TransitEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.vedha_calculator import VedhaCalculator


@pytest.fixture(scope="module")
def ephemeris() -> EphemerisWrapper:
    settings = get_settings()
    return EphemerisWrapper(ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="krishnamurti")


def test_kp_ayanamsa_validation_warnings():
    # 1. Non-KP ayanamsa triggers governance warning
    req_lahiri = KPAnalysisRequest(
        birth_datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
        house_system="P",
    )
    warnings = req_lahiri.get_ayanamsa_warnings()
    assert len(warnings) == 1
    assert "AYANAMSA_NOT_KP" in warnings[0]
    assert "krishnamurti" in warnings[0]

    # 2. Non-Placidus house system triggers governance warning
    req_equal = KPAnalysisRequest(
        birth_datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="krishnamurti",
        house_system="W",
    )
    warnings_equal = req_equal.get_ayanamsa_warnings()
    assert len(warnings_equal) == 1
    assert "HOUSE_SYSTEM_NOT_PLACIDUS" in warnings_equal[0]

    # 3. Canonical KP settings yield zero warnings
    req_canonical = KPAnalysisRequest(
        birth_datetime_utc=datetime(1990, 1, 1, 12, 0, tzinfo=timezone.utc),
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="krishnamurti",
        house_system="P",
    )
    assert len(req_canonical.get_ayanamsa_warnings()) == 0


def test_kp_retrograde_ruling_planets_governance(ephemeris: EphemerisWrapper):
    rp_engine = KPRulingPlanetsEngine(ephemeris)
    # Pick a date/time where planets like Saturn/Jupiter might be retrograde or inspect structure
    query_dt = datetime(2025, 7, 15, 14, 30, 0, tzinfo=timezone.utc)
    res: RulingPlanetsSnapshot = rp_engine.calculate_ruling_planets(
        query_datetime_utc=query_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="krishnamurti",
    )

    assert isinstance(res.retrograde_rp_flags, dict)
    for entry in res.ruling_planets_ordered:
        assert hasattr(entry, "is_retrograde")
        assert hasattr(entry, "retrograde_caution")
        if entry.is_retrograde:
            assert entry.retrograde_caution != ""
            assert "RETROGRADE" in entry.retrograde_caution
            assert entry.planet in res.retrograde_rp_flags


def test_kp_evidence_classical_citations(ephemeris: EphemerisWrapper):
    horoscope_engine = HoroscopeEngine(ephemeris)
    dasha_engine = DashaEngine(ephemeris)
    transit_engine = TransitEngine(
        ephemeris,
        ashtakavarga_engine=AshtakavargaEngine(),
        vedha_calculator=VedhaCalculator(),
    )
    
    birth = datetime(1988, 6, 20, 7, 15, tzinfo=timezone.utc)
    chart = horoscope_engine.generate_d1(birth, 13.0827, 80.2707, ayanamsa="krishnamurti", house_system="P")
    dasha_tree = dasha_engine.compute_vimshottari(birth, 13.0827, 80.2707, ayanamsa="krishnamurti", house_system="P")
    transit_results = transit_engine.compute_transit(natal_chart=chart, transit_datetime_utc=datetime.now(timezone.utc))

    # Test evidence for marriage & career
    evidence_marriage = compute_event_evidence(chart, dasha_tree, transit_results, datetime.now(timezone.utc), "marriage")
    assert evidence_marriage["technique_framework"] == "KP System"
    assert "KP Reader 4" in evidence_marriage["classical_rule_citation"]
    assert "7th CSL" in evidence_marriage["classical_rule_citation"]

    evidence_career = compute_event_evidence(chart, dasha_tree, transit_results, datetime.now(timezone.utc), "career")
    assert evidence_career["technique_framework"] == "KP System"
    assert "KP Reader 3" in evidence_career["classical_rule_citation"]
    assert "10th CSL" in evidence_career["classical_rule_citation"]


@pytest.mark.asyncio
async def test_kp_analyze_api_governance_integration(ephemeris: EphemerisWrapper):
    app = FastAPI()
    app.dependency_overrides[get_ephemeris_wrapper] = lambda: ephemeris
    app.include_router(kp_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request with lahiri to verify warnings are surfaced in response
        resp = await client.post(
            "/api/v1/kp/analyze",
            json={
                "birth_datetime_utc": "1990-05-15T10:30:00Z",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "ayanamsa": "lahiri",
                "house_system": "P"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ayanamsa_used"] == "lahiri"
        assert len(data["ayanamsa_warnings"]) > 0
        assert "AYANAMSA_NOT_KP" in data["ayanamsa_warnings"][0]

        # Check evidence array contains classical citations and framework
        assert len(data["evidence"]) > 0
        for ev in data["evidence"]:
            assert ev["technique_framework"] == "KP System"
            assert len(ev["classical_rule_citation"]) > 0

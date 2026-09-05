"""
Unit tests for Master Astrologer Engine & Fact Synthesizer.
Verifies Shastric 10-step compliance, 7 Chara Karakas, log2 Main Strength,
and deterministic consultation generation.
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.astrologer_fact_synthesizer import AstrologerFactSynthesizer
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.master_astrologer_engine import MasterAstrologerEngine


@pytest.fixture
def sample_chart():
    wrapper = EphemerisWrapper("data/ephemeris")
    engine = HoroscopeEngine(wrapper)
    birth_dt = datetime(1990, 5, 15, 8, 30, tzinfo=timezone.utc)
    return engine.generate_d1(
        birth_datetime_utc=birth_dt,
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
    )


def test_fact_synthesizer_shastric_compliance(sample_chart):
    synthesizer = AstrologerFactSynthesizer()
    facts = synthesizer.synthesize(sample_chart, target_date=date(2026, 9, 5), subject_name="Test Native")

    # 1. Strictly 7 Chara Karakas (Never 8)
    assert len(facts.chara_karakas_7) == 7
    karaka_names = [k["karaka"] for k in facts.chara_karakas_7]
    assert "Atmakaraka" in karaka_names
    assert "Darakaraka" in karaka_names
    assert "Pitrukaraka" not in karaka_names  # 8th karaka rejected by Vinay Jha lineage

    # 2. Main Strength log2 scale check
    for planet, strength_data in facts.main_strength_log2.items():
        assert 1.0 <= strength_data["main_strength"] <= 256.0
        assert 1 <= strength_data["dignity_tier"] <= 9

    # 3. Active Vimshottari chain present
    assert facts.active_vimshottari["mahadasha"] != "None"
    assert facts.active_vimshottari["antardasha"] != "None"

    # 4. Dense grounding string contains critical sections
    assert "NATAL HOROSCOPE FACTS" in facts.dense_grounding_text
    assert "7 CHARA KARAKAS" in facts.dense_grounding_text
    assert "BHAVACHALITA HOUSE PLACEMENTS" in facts.dense_grounding_text


def test_master_astrologer_deterministic_consultation_hi(sample_chart):
    engine = MasterAstrologerEngine()
    result = engine.generate_consultation(
        chart=sample_chart,
        target_date=date(2026, 9, 5),
        subject_name="Ramesh",
        language="hi",
    )

    assert result.is_llm_enriched is False
    assert result.ai_provider_used == "deterministic_shastric_core"
    assert "संपूर्ण शास्त्रीय कुंडली परामर्श" in result.reading_markdown
    assert "आत्मकारक" in result.reading_markdown
    assert "विंशोत्तरी" in result.reading_markdown
    assert len(result.executive_summary) > 20


def test_master_astrologer_deterministic_consultation_en(sample_chart):
    engine = MasterAstrologerEngine()
    result = engine.generate_consultation(
        chart=sample_chart,
        target_date=date(2026, 9, 5),
        subject_name="John Doe",
        language="en",
    )

    assert result.is_llm_enriched is False
    assert "Master Astrologer Consultation Reading" in result.reading_markdown
    assert "7 Chara Karakas" in result.reading_markdown
    assert "Atmakaraka" in result.reading_markdown


@pytest.mark.asyncio
async def test_master_consultation_api_endpoint():
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app
    from apps.api.dependencies import require_authenticated

    app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_user"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {
                "birth_datetime_utc": "1990-05-15T08:30:00Z",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "ayanamsa": "lahiri",
                "house_system": "W",
                "subject_name": "Ramesh",
                "language": "hi",
            }
            res = await client.post("/api/v1/ai/master-consultation", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["subject_name"] == "Ramesh"
            assert "संपूर्ण शास्त्रीय कुंडली परामर्श" in data["reading_markdown"]
            assert len(data["dense_facts"]) > 100
            assert data["ai_provider_used"] in ("deterministic_shastric_core", "deterministic_shastric_fallback")
    finally:
        app.dependency_overrides.pop(require_authenticated, None)


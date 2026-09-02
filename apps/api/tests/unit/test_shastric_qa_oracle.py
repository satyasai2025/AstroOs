"""
AstroOS — Shastric Interactive Copilot & Zero-Hallucination Q&A Unit Tests
==========================================================================
Tests domain parsing, ethical anti-fatalism guardrails, and deterministic
Shastric answer synthesis across all core life domains.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.api.routers.phalita_prediction import router as phalita_router
from apps.api.services.shastric_qa_oracle import ShastricQAOracle, ShastricQAResponse

app = FastAPI()
app.include_router(phalita_router)
client = TestClient(app)

MOCK_TIMELINE_WINDOWS = [
    {
        "window_start": "2026-05-15",
        "window_end": "2027-08-20",
        "mahadasha": "jupiter",
        "antardasha": "mars",
        "probability": 0.88,
        "decision_tier": "PRATYAKSHA_PHALA",
    },
    {
        "window_start": "2027-08-21",
        "window_end": "2028-11-10",
        "mahadasha": "jupiter",
        "antardasha": "rahu",
        "probability": 0.65,
        "decision_tier": "SUSHUPTA_BEEJA",
    }
]


def test_domain_detection():
    """Verify natural language queries map to correct Shastric domains."""
    assert ShastricQAOracle.detect_domain("Meri job change kab hogi?") == "career"
    assert ShastricQAOracle.detect_domain("When will I get a promotion in my company?") == "career"
    assert ShastricQAOracle.detect_domain("Foreign travel aur videsh yatra ke yog kab hain?") == "foreign_travel"
    assert ShastricQAOracle.detect_domain("Will I get PR or visa abroad?") == "foreign_travel"
    assert ShastricQAOracle.detect_domain("Mera vivah aur shaadi kab hogi?") == "marriage"
    assert ShastricQAOracle.detect_domain("When will I meet my spouse?") == "marriage"
    assert ShastricQAOracle.detect_domain("Paisa aur dhan labh kab hoga?") == "wealth"
    assert ShastricQAOracle.detect_domain("Health issue aur swasthya kab theek hoga?") == "health"
    assert ShastricQAOracle.detect_domain("Naya ghar ya zameen lene ke yog kab hain?") == "property"
    assert ShastricQAOracle.detect_domain("Competitive exam aur college admission kab clear hoga?") == "education"


def test_guardrail_rejections():
    """Verify fatalistic, superstitious, or ungrounded queries are rejected."""
    # 1. Death fatalism
    resp = ShastricQAOracle.answer_question(
        question="Meri death kab hogi?",
        timeline_windows=MOCK_TIMELINE_WINDOWS
    )
    assert not resp.is_valid_query
    assert resp.guardrail_reason is not None
    assert "fatalistic" in resp.guardrail_reason.lower() or "death" in resp.guardrail_reason.lower()
    assert resp.faithfulness_score == 1.0

    # 2. Lottery / Gambling numbers
    resp_lottery = ShastricQAOracle.answer_question(
        question="Give me the exact lottery number prediction for tomorrow",
        timeline_windows=MOCK_TIMELINE_WINDOWS
    )
    assert not resp_lottery.is_valid_query
    assert "lottery" in resp_lottery.guardrail_reason.lower() or "gambling" in resp_lottery.guardrail_reason.lower()

    # 3. Black magic
    resp_magic = ShastricQAOracle.answer_question(
        question="Who did black magic or jaadu tona on me?",
        timeline_windows=MOCK_TIMELINE_WINDOWS
    )
    assert not resp_magic.is_valid_query


def test_career_qa_synthesis():
    """Verify career question produces deterministic timeline and Shastric grounds."""
    resp = ShastricQAOracle.answer_question(
        question="Meri job change aur promotion kab hoga?",
        timeline_windows=MOCK_TIMELINE_WINDOWS,
        native_name="Rajesh"
    )
    assert resp.is_valid_query
    assert resp.domain == "career"
    assert "2026-05-15 to 2027-08-20" in resp.probable_timing_window
    assert "Jupiter-Mars" in resp.answer_en
    assert "दशम भाव" in resp.answer_hi
    assert resp.confidence_tier == "HIGH"
    assert len(resp.shastric_rule_grounds) >= 2
    assert len(resp.recommended_remedies) >= 1
    assert resp.faithfulness_score == 1.0


def test_foreign_travel_qa_synthesis():
    """Verify foreign travel question generates 9th/12th house Shastric grounds."""
    resp = ShastricQAOracle.answer_question(
        question="When can I travel abroad for higher opportunities?",
        timeline_windows=MOCK_TIMELINE_WINDOWS
    )
    assert resp.is_valid_query
    assert resp.domain == "foreign_travel"
    assert any("12th House" in g or "9th House" in g for g in resp.shastric_rule_grounds)
    assert len(resp.planetary_triggers) >= 1


def test_marriage_qa_synthesis():
    """Verify marriage timing questions reference 7th house and Upapada Lagna."""
    resp = ShastricQAOracle.answer_question(
        question="Meri shaadi ka yog kab ban raha hai?",
        timeline_windows=MOCK_TIMELINE_WINDOWS
    )
    assert resp.is_valid_query
    assert resp.domain == "marriage"
    assert any("7th" in g or "Upapada" in g for g in resp.shastric_rule_grounds)


def test_ask_oracle_api_endpoint():
    """Tests the REST endpoint POST /api/v1/phalita/ask-oracle."""
    payload = {
        "question": "Mera promotion kab hoga?",
        "timeline_windows": MOCK_TIMELINE_WINDOWS,
        "native_name": "Test Native",
        "lang": "en"
    }
    response = client.post("/api/v1/phalita/ask-oracle", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["is_valid_query"] is True
    assert data["domain"] == "career"
    assert data["probable_timing_window"] == "2026-05-15 to 2027-08-20"
    assert data["confidence_tier"] == "HIGH"
    assert len(data["shastric_rule_grounds"]) > 0
    assert len(data["recommended_remedies"]) > 0

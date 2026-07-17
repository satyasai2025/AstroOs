"""
AstroOS — AI Domain Model Unit Tests (Module 24, Phase 1)
"""

import dataclasses

import pytest

from apps.api.domain.ai import AIResponse, Citation, ExplanationRequest


class TestCitation:
    def test_is_frozen(self):
        c = Citation(source="BPHS", reference="46.12", text="verse")
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.text = "other"

    def test_default_relevance(self):
        c = Citation(source="BPHS", reference="46.12", text="verse")
        assert c.relevance == 0.0


class TestAIResponse:
    def test_is_frozen(self):
        r = AIResponse(
            response_type="chart_summary", title="T",
            summary="S", body="B",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.title = "Other"

    def test_defaults(self):
        r = AIResponse(
            response_type="test", title="T",
            summary="S", body="B",
        )
        assert r.citations == ()
        assert r.sources == ()
        assert r.recommendations == ()
        assert r.confidence == "medium"
        assert r.version == "1.0"


class TestExplanationRequest:
    def test_defaults(self):
        r = ExplanationRequest(topic="chart_summary")
        assert r.style == "concise"
        assert r.max_length == 500
        assert r.source_data == {}

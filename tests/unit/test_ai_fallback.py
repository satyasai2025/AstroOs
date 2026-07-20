"""
AstroOS — AI Fallback Handler Unit Tests (Task #13)
"""

from __future__ import annotations

import pytest

from apps.api.domain.ai import AIResponse
from apps.api.services.ai_fallback import AIFallbackHandler, FallbackResult, FallbackSource


class TestFallbackResult:
    def test_defaults(self):
        r = FallbackResult(source=FallbackSource.AI)
        assert r.source == FallbackSource.AI
        assert r.data is None
        assert r.message == ""

    def test_factory(self):
        r = FallbackResult(
            source=FallbackSource.FALLBACK,
            data={"key": "value"},
            message="fallback used",
        )
        assert r.source == FallbackSource.FALLBACK
        assert r.data == {"key": "value"}
        assert r.message == "fallback used"


class TestAIFallbackHandler:
    def test_ai_success_high_confidence(self):
        """AI generator returns a high-confidence result — no fallback."""
        def ai_fn(**kwargs):
            return AIResponse(
                response_type="chart_summary",
                title="Chart Summary",
                summary="Test summary",
                body="Test body with content.",
                confidence="high",
            )

        def fallback_fn(**kwargs):
            return "fallback_data"

        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
        )

        assert result.source == FallbackSource.AI
        assert result.data is not None
        assert result.data.confidence == "high"

    def test_ai_low_confidence_triggers_fallback(self):
        """AI returns low confidence → fallback used."""
        def ai_fn(**kwargs):
            return AIResponse(
                response_type="chart_summary",
                title="Chart Summary",
                summary="Low confidence",
                body="Low confidence body.",
                confidence="low",
            )

        def fallback_fn(**kwargs):
            return "fallback_data"

        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
        )

        assert result.source == FallbackSource.FALLBACK
        assert result.data == "fallback_data"

    def test_both_fail_return_error(self):
        """Both AI and fallback fail → error result."""
        def ai_fn(**kwargs):
            raise ValueError("AI failure")

        def fallback_fn(**kwargs):
            raise RuntimeError("Fallback failure")

        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
        )

        assert result.source == FallbackSource.ERROR
        assert result.data is None
        assert "AI" in result.message
        assert "Fallback" in result.message

    def test_empty_body_triggers_fallback(self):
        """AI result with empty body → fallback used."""
        def ai_fn(**kwargs):
            return AIResponse(
                response_type="chart_summary",
                title="Empty",
                summary="",
                body="",
                confidence="high",
            )

        def fallback_fn(**kwargs):
            return "fallback_data"

        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
        )

        assert result.source == FallbackSource.FALLBACK

    def test_custom_checker(self):
        """Custom checker can override acceptance logic."""
        def ai_fn(**kwargs):
            return AIResponse(
                response_type="chart_summary",
                title="Test",
                summary="Test",
                body="Valid body content.",
                confidence="low",
            )

        def fallback_fn(**kwargs):
            return "fallback_data"

        # Custom checker that always accepts.
        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
            ai_result_checker=lambda r: True,
        )

        assert result.source == FallbackSource.AI

    def test_kwargs_passed_to_functions(self):
        """Keyword arguments are passed to both functions."""
        def ai_fn(**kwargs):
            assert kwargs.get("key") == "value"
            return AIResponse(
                response_type="test", title="T", summary="S",
                body="Body.", confidence="high",
            )

        def fallback_fn(**kwargs):
            assert kwargs.get("key") == "value"
            return "fallback"

        result = AIFallbackHandler.generate_with_fallback(
            ai_fn=ai_fn,
            fallback_fn=fallback_fn,
            ai_kwargs={"key": "value"},
            fallback_kwargs={"key": "value"},
        )

        assert result.source == FallbackSource.AI

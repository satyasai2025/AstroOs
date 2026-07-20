"""
AstroOS — AI Fallback to Rule-Based Mechanism (Task #13)

Provides the AIFallbackHandler class that wraps an AI engine call with a
deterministic fallback chain:

  1. Try the AI generator (template-based natural language).
  2. If the result is low-confidence or empty, fall back to a
     rule-based calculator (e.g. ShadbalaEngine, AshtakavargaEngine,
     YogaEngine, DashaEngine).
  3. If the fallback also fails, return a structural error result.

Usage:

    handler = AIFallbackHandler()
    result = handler.generate_with_fallback(
        ai_fn=my_ai_generator,
        fallback_fn=my_rule_based_calculator,
        ai_kwargs={"chart": chart},
        fallback_kwargs={"chart": chart},
        confidence_threshold="medium",
    )
    # result.source is "ai", "fallback", or "error"
    # result.data holds the AIResponse or calculator output
    # result.message has a trace message

Local-first: No external LLM/API calls. All code is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class FallbackSource(str, Enum):
    """Origin of a successfully generated result."""
    AI = "ai"
    FALLBACK = "fallback"
    ERROR = "error"


@dataclass(frozen=True)
class FallbackResult:
    """
    Result from the AIFallbackHandler chain.

    Attributes:
        source:  Which stage produced the result (ai / fallback / error).
        data:    The generated output (typically an AIResponse or calculator
                 domain object).
        message: Human-readable trace of what happened in the chain.
    """
    source: FallbackSource
    data: Any = None
    message: str = ""


# Default confidence values ranked.
_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def _meets_threshold(confidence: str, threshold: str) -> bool:
    return _CONFIDENCE_RANK.get(confidence, 0) >= _CONFIDENCE_RANK.get(threshold, 1)


class AIFallbackHandler:
    """
    Wraps an AI generator call with a deterministic fallback chain.

    The chain is:
        try AI -> low-confidence/empty -> fallback -> still fails -> error

    Typical calculator engines available for fallback:
      - ShadbalaEngine    (apps.api.services.shadbala_engine)
      - AshtakavargaEngine (apps.api.services.ashtakavarga_engine)
      - YogaEngine        (apps.api.services.yoga_engine)
      - DashaEngine       (apps.api.services.dasha_engine)

    These belong to the ``WorkerPool.calculator`` range; AI-specific
    workers belong to ``WorkerPool.ai``.
    """

    @staticmethod
    def generate_with_fallback(
        ai_fn: Callable[..., Any],
        fallback_fn: Callable[..., Any],
        ai_kwargs: dict[str, Any] | None = None,
        fallback_kwargs: dict[str, Any] | None = None,
        confidence_threshold: str = "medium",
        ai_result_checker: Callable[[Any], bool] | None = None,
    ) -> FallbackResult:
        """
        Execute the AI generator with rule-based fallback.

        Parameters
        ----------
        ai_fn:
            The AI generator function (e.g. ChartSummarizer.generate).
        fallback_fn:
            The rule-based calculator function (e.g. ShadbalaEngine).
        ai_kwargs:
            Keyword arguments to pass to *ai_fn*.
        fallback_kwargs:
            Keyword arguments to pass to *fallback_fn*.
        confidence_threshold:
            Minimum confidence level required to accept the AI result
            without falling back. One of ``"high"``, ``"medium"``,
            ``"low"``.
        ai_result_checker:
            Optional custom callable that receives the AI result and
            returns True if it is acceptable. When not provided, the
            built-in checker inspects the result's ``confidence`` and
            ``body`` fields.

        Returns
        -------
        FallbackResult
            With *source* set to the stage that produced the output.
        """
        ai_kwargs = ai_kwargs or {}
        fallback_kwargs = fallback_kwargs or {}

        # ── Step 1: Try the AI generator ──────────────────────────────────
        try:
            ai_result = ai_fn(**ai_kwargs)
        except Exception as exc:
            ai_result = None
            ai_error = str(exc)

        if ai_result is not None:
            # Determine whether the AI result is acceptable.
            if ai_result_checker is not None:
                acceptable = ai_result_checker(ai_result)
            else:
                acceptable = AIFallbackHandler._default_checker(
                    ai_result, confidence_threshold,
                )

            if acceptable:
                return FallbackResult(
                    source=FallbackSource.AI,
                    data=ai_result,
                    message="AI generator produced acceptable result.",
                )

        # ── Step 2: Fallback to rule-based calculator ─────────────────────
        try:
            fallback_result = fallback_fn(**fallback_kwargs)
            return FallbackResult(
                source=FallbackSource.FALLBACK,
                data=fallback_result,
                message=(
                    "AI result was rejected (confidence below threshold or "
                    "empty); rule-based fallback succeeded."
                ),
            )
        except Exception as fallback_exc:
            return FallbackResult(
                source=FallbackSource.ERROR,
                message=(
                    f"AI and fallback both failed. "
                    f"AI error: {ai_error if ai_result is None else 'low confidence / empty'}. "
                    f"Fallback error: {fallback_exc}."
                ),
            )

    @staticmethod
    def _default_checker(result: Any, threshold: str) -> bool:
        """Built-in check: confidence meets threshold AND body is non-empty."""
        confidence = getattr(result, "confidence", "low")
        body = getattr(result, "body", "")
        if not _meets_threshold(confidence, threshold):
            return False
        if not body or not body.strip():
            return False
        return True

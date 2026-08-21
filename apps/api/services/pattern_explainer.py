"""
AstroOS — Pattern AI Explanation Service (Module 27, Phase 3c)

Unlike apps/api/services/ai_engine.py (deliberately template-based, no
external LLM — see that module's docstring), this service makes a real
chat-completion call to generate a plain-language explanation of a
discovered pattern. This was an explicit user choice: pattern explanations
read better as genuinely generative text than as another template.

Uses the process-wide httpx.AsyncClient (see apps.api.main's lifespan /
apps.api.dependencies.get_geocoding_service for the same sharing pattern)
rather than opening a new connection per call. The actual provider/model/
key come from apps.api.services.ai_provider.resolve_provider — a per-user
BYOK setting (apps.api.services.ai_settings_service) if the caller has
one configured, else the server-wide Settings.OPENAI_* config. If neither
is configured, or the call fails, this raises rather than silently
falling back to a template, per explicit user direction ("real LLM call",
not a disguised deterministic generator).

Only ever invoked from POST /research/cases/patterns/{pattern_id}/explain
(single) or the bulk regenerate-all endpoint — never from a GET, so viewing
a pattern's detail never has a side effect or an external-network cost.

Post-generation fact check: the model is free-form generative (per the
"real LLM call" direction above — this deliberately does NOT constrain it
to rewriting a pre-built deterministic string), so a weak or poorly-
instruction-following BYOK model could still invent a number. Rather than
caging the model, _validate_numbers() checks every percentage/decimal the
model's response actually contains against the numbers present in the
source pattern (with rounding tolerance) after the call returns. A number
that matches nothing in the input is treated as fabricated and raises
PatternValidationError — loud failure, same "never silently substitute"
philosophy as the rest of this module, just applied to the output instead
of only to missing config.
"""

from __future__ import annotations

import re

import httpx

from apps.api.domain.research_case import DiscoveredPattern
from apps.api.services.ai_provider import AIProviderError, ResolvedAIProvider, call_chat_completion

_SYSTEM_PROMPT = (
    "You are an assistant explaining statistical findings from a Vedic "
    "astrology research dataset to a researcher. Given a discovered pattern "
    "(which astrological dimensions co-occur with a life event, at what "
    "frequency, vs. the base rate), write a concise (3-5 sentence) plain-"
    "language explanation of what the pattern shows and how strong the "
    "evidence is. Be precise about the statistics given — do not invent "
    "numbers or classical rules not implied by the data. Do not overstate "
    "causation; this is a correlational finding."
)

_NUMBER_TOLERANCE = 0.15  # absolute; covers rounding drift (e.g. model writing 42% for 41.95%)


class PatternExplanationError(RuntimeError):
    """Raised when an explanation cannot be generated (missing key, API failure)."""


class PatternValidationError(RuntimeError):
    """Raised when the model's response contains a number not present in the source pattern."""

    def __init__(self, bad_numbers: list[float], response: str) -> None:
        self.bad_numbers = bad_numbers
        self.response = response
        super().__init__(
            f"Response contains number(s) not present in source data: {bad_numbers}"
        )


def _extract_numbers(text: str) -> list[float]:
    """Every percentage/decimal figure literally written in the response."""
    return [float(m) for m in re.findall(r"-?\d+\.?\d*(?=%|\b)", text) if m not in ("", "-", ".")]


def _allowed_numbers(pattern: DiscoveredPattern) -> set[float]:
    allowed: set[float] = {
        round(pattern.confidence_score * 100, 1), round(pattern.confidence_score, 2),
        float(pattern.sample_size),
    }
    for d in pattern.dimensions:
        allowed.add(round(d.frequency * 100, 1))
        allowed.add(round(d.expected_by_chance * 100, 1))
        allowed.add(round(d.significance, 2))
    return allowed


def _validate_numbers(response: str, pattern: DiscoveredPattern) -> None:
    allowed = _allowed_numbers(pattern)
    bad = [
        n for n in _extract_numbers(response)
        if not any(abs(n - a) <= _NUMBER_TOLERANCE for a in allowed)
    ]
    if bad:
        raise PatternValidationError(bad, response)


class PatternExplainer:
    """Generates a natural-language explanation for one DiscoveredPattern."""

    def __init__(self, http_client: httpx.AsyncClient, resolved: ResolvedAIProvider) -> None:
        self._client = http_client
        self._resolved = resolved

    async def explain(self, pattern: DiscoveredPattern) -> str:
        dims = "; ".join(
            f"{d.dimension}={d.value} ({round(d.frequency * 100, 1)}% of cases vs "
            f"{round(d.expected_by_chance * 100, 1)}% base rate, significance "
            f"{d.significance:.2f})"
            for d in pattern.dimensions
        )
        user_prompt = (
            f"Event type: {pattern.event_type}\n"
            f"Pattern description: {pattern.description}\n"
            f"Dimensions: {dims}\n"
            f"Sample size: {pattern.sample_size} cases\n"
            f"Overall confidence score: {pattern.confidence_score:.2f}"
        )

        try:
            response = await call_chat_completion(self._client, self._resolved, _SYSTEM_PROMPT, user_prompt)
        except AIProviderError as exc:
            raise PatternExplanationError(str(exc)) from exc

        _validate_numbers(response, pattern)
        return response

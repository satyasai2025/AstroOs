"""
AstroOS — Pattern AI Explanation Service (Module 27, Phase 3c)

Unlike apps/api/services/ai_engine.py (deliberately template-based, no
external LLM — see that module's docstring), this service makes a real
OpenAI Chat Completions call to generate a plain-language explanation of a
discovered pattern. This was an explicit user choice: pattern explanations
read better as genuinely generative text than as another template.

Uses the process-wide httpx.AsyncClient (see apps.api.main's lifespan /
apps.api.dependencies.get_geocoding_service for the same sharing pattern)
rather than opening a new connection per call. Requires OPENAI_API_KEY to be
set (apps.api.config.Settings) — if it isn't, or the call fails, this raises
rather than silently falling back to a template, per explicit user
direction ("real LLM call", not a disguised deterministic generator).

Only ever invoked from POST /research/cases/patterns/{pattern_id}/explain
(single) or the bulk regenerate-all endpoint — never from a GET, so viewing
a pattern's detail never has a side effect or an external-network cost.
"""

from __future__ import annotations

import httpx

from apps.api.domain.research_case import DiscoveredPattern

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_REQUEST_TIMEOUT_SECONDS = 30.0

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


class PatternExplanationError(RuntimeError):
    """Raised when an explanation cannot be generated (missing key, API failure)."""


class PatternExplainer:
    """Generates a natural-language explanation for one DiscoveredPattern."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: str | None,
        model: str,
        base_url: str = _DEFAULT_BASE_URL,
    ) -> None:
        self._client = http_client
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def explain(self, pattern: DiscoveredPattern) -> str:
        if not self._api_key:
            raise PatternExplanationError(
                "OPENAI_API_KEY is not configured — set it in .env to enable "
                "AI-generated pattern explanations."
            )

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
            response = await self._client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                },
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PatternExplanationError(f"OpenAI request failed: {exc}") from exc

        body = response.json()
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise PatternExplanationError(
                f"Unexpected OpenAI response shape: {body!r}"
            ) from exc

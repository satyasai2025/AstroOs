"""
AstroOS — Natural-Language Pattern Query Assistant (Module 27, Phase 3d)

Lets a researcher ask a question in plain English ("what correlates with
Marriage?") and get back an answer grounded in the shared, already-
persisted discovered_patterns table — never a hallucinated statistic.
Same real-LLM-call, no-silent-template-fallback discipline as
pattern_explainer.py. The actual provider/model/key come from
apps.api.services.ai_provider.resolve_provider — a per-user BYOK setting
if the caller has one configured, else the server-wide Settings.OPENAI_*
config.

Two stages, kept deliberately narrow so the LLM can never fabricate a
finding:

  1. Parse — the LLM's ONLY job is to pick one event_type out of the
     fixed LOKPA list (or none). Its answer is validated against that
     real list server-side before it's ever used to query the database;
     an out-of-list answer is discarded, not trusted. The LLM never
     touches the database.
  2. Summarize — given the REAL patterns the router already fetched for
     that event type, the LLM writes a plain-language answer that may
     only quote the numbers it was handed. It cannot introduce a
     pattern, percentage, or astrological claim absent from that input.

Only ever invoked from POST /research/cases/patterns/ask — a read-only
endpoint. It never runs discovery and never persists anything.
"""

from __future__ import annotations

import json

import httpx

from apps.api.services.ai_provider import AIProviderError, ResolvedAIProvider, call_chat_completion

_PARSE_SYSTEM_PROMPT_TEMPLATE = (
    "You extract which life-event type a researcher's question is about, "
    "from this fixed list: {event_types}. Respond with ONLY a JSON object: "
    '{{"event_type": "<exact value from the list>"}} or '
    '{{"event_type": null}} if the question does not clearly name one of '
    "them. Never invent a value outside the list; never explain yourself."
)

_SUMMARIZE_SYSTEM_PROMPT = (
    "You are answering a researcher's question about a Vedic astrology "
    "research dataset using ONLY the discovered patterns listed below — "
    "real statistical findings already computed from real data. Write a "
    "concise (3-6 sentence) plain-language answer to the question. Quote "
    "the percentages/confidence scores given; do not invent numbers, "
    "patterns, or astrological rules that are not present in the list "
    "below. If the listed patterns don't fully answer the question, say "
    "so honestly rather than filling the gap with invented information."
)


class PatternQueryError(RuntimeError):
    """Raised when a question can't be answered (missing key, API failure)."""


class PatternQueryAssistant:
    """Answers plain-language questions grounded in already-fetched,
    real pattern data — see module docstring for the two-stage design."""

    def __init__(self, http_client: httpx.AsyncClient, resolved: ResolvedAIProvider) -> None:
        self._client = http_client
        self._resolved = resolved

    async def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        try:
            return await call_chat_completion(
                self._client, self._resolved, system, user, json_mode=json_mode
            )
        except AIProviderError as exc:
            raise PatternQueryError(str(exc)) from exc

    async def parse_event_type(self, question: str, valid_event_types: list[str]) -> str | None:
        """Extract a validated event_type from the question, or None if
        the question doesn't clearly name one from the real fixed list.

        Returning None is always safe: the caller then queries patterns
        across every event type rather than a filtered subset, so a parse
        failure degrades to a broader answer, never a wrong one.
        """
        system = _PARSE_SYSTEM_PROMPT_TEMPLATE.format(event_types=", ".join(valid_event_types))
        raw = await self._chat(system, question, json_mode=True)
        # Some OpenAI-compatible providers (notably Gemini's compat layer)
        # wrap JSON in a ```json fence even when asked for raw JSON.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1] if "```" in cleaned[3:] else cleaned[3:]
            if cleaned.lstrip().lower().startswith("json"):
                cleaned = cleaned.lstrip()[4:]
        try:
            parsed = json.loads(cleaned.strip())
        except (ValueError, TypeError):
            return None
        candidate = parsed.get("event_type") if isinstance(parsed, dict) else None
        return candidate if candidate in valid_event_types else None

    async def summarize(self, question: str, patterns: list[dict]) -> str:
        """Write a grounded natural-language answer from real,
        already-fetched pattern rows. Never queries anything itself."""
        if not patterns:
            return (
                "No statistically significant patterns were found for this "
                "in the shared dataset."
            )
        # 1 decimal place, matching exactly what the UI table shows beside
        # this answer — rounding to whole percent here made the generated
        # text say "93%" next to a table reading "92.7%", which reads as a
        # discrepancy even though nothing was actually invented.
        patterns_text = "\n".join(
            f"- {p['description']} (confidence {p['confidence_score']:.1%}, "
            f"support {p['sample_size']} cases)"
            for p in patterns
        )
        user_prompt = f"Question: {question}\n\nPatterns found:\n{patterns_text}"
        return await self._chat(_SUMMARIZE_SYSTEM_PROMPT, user_prompt)

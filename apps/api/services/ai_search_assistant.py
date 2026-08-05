"""
AstroOS — AI Search Assistant

Provides LLM-powered query expansion for Phase 9 Search. Follows the
PatternQueryAssistant pattern (httpx + openai-compatible endpoint, same
no-hallucination discipline): the LLM's only job is to expand a plain
user query ("marriage") into related astrological search terms
("marriage", "7th house", "venus", "kalatra bhava") that the router then
matches against real local rows — it never invents a result itself.

Design:
- expand_query() asks the LLM for a list of domain terms, validated
  server-side (only a list of short strings is trusted; an out-of-shape
  answer is discarded, not trusted).
- On ANY failure (missing key, API error, bad JSON) it degrades to
  returning just the original query — a broken LLM call must never break
  search. This mirrors the local-first / silent-fallback philosophy of
  the rest of the platform.
"""

from __future__ import annotations

import json

import httpx

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_REQUEST_TIMEOUT_SECONDS = 15.0

_EXPAND_SYSTEM_PROMPT = (
    "You are a Vedic Astrology search query expander. Given a user's search "
    "query, identify the core astrological concepts, houses, planets, or "
    "Sanskrit terms associated with it. Respond ONLY with a JSON object in "
    'this format: {"terms": ["term1", "term2"]}. Keep terms short (1-3 '
    "words), include the original concept, max 5 terms. Never explain "
    "yourself. Only output JSON."
)


class AISearchError(RuntimeError):
    """Raised when AI expansion fails or the API key is missing."""


class AISearchAssistant:
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

    @property
    def is_configured(self) -> bool:
        """True if the assistant has an API key and can be used."""
        return bool(self._api_key)

    async def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        if not self._api_key:
            raise AISearchError(
                "OPENAI_API_KEY is not configured — set it in .env to enable AI search."
            )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = await self._client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AISearchError(f"OpenAI request failed: {exc}") from exc

        body = response.json()
        try:
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AISearchError(f"Unexpected OpenAI response shape: {body!r}") from exc

    async def expand_query(self, query: str) -> list[str]:
        """
        Expand a plain-language query into related astrological search terms.

        Always returns at least the original query. On any failure (missing
        key, API error, unparsable JSON) it degrades to just the original
        query — so a broken LLM call never breaks search.
        """
        try:
            raw = await self._chat(_EXPAND_SYSTEM_PROMPT, query, json_mode=True)
            # Some OpenAI-compatible providers wrap JSON in a ```json fence.
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1] if "```" in cleaned[3:] else cleaned[3:]
                if cleaned.lstrip().lower().startswith("json"):
                    cleaned = cleaned.lstrip()[4:]
            parsed = json.loads(cleaned.strip())
            terms = parsed.get("terms", [])
            if not isinstance(terms, list):
                return [query.strip().lower()]
            valid = [str(t).strip().lower() for t in terms if t]
            original = query.strip().lower()
            if original not in valid:
                valid.insert(0, original)
            return valid[:6]
        except (ValueError, TypeError, AISearchError):
            return [query.strip().lower()]
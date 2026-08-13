"""
AstroOS — Local LLM Client (Phase IV, IV.3)

Optional, opt-in enrichment for AIEngine's deterministic template
output. Talks only to a locally-hosted, OpenAI-compatible model server
the user runs themselves (e.g. Ollama, LM Studio) — never a cloud API,
never called unless Settings.AI_BACKEND == "local_llm".

On any failure (server not running, timeout, bad response) this
returns None rather than raising — callers must treat None as "use the
template output as-is". That is what keeps AIEngine's deterministic-
fallback guarantee intact: enabling this backend can only ever add
richer phrasing on top of the template facts, never replace them with
something unavailable or broken.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You rewrite astrological chart summaries in clear, natural language "
    "for a general reader. Use ONLY the facts given to you below — do not "
    "invent new astrological claims, planet positions, or predictions not "
    "present in the source text. Keep it concise."
)


def enrich_narration(
    *,
    base_url: str,
    model: str,
    timeout_seconds: float,
    grounding_text: str,
    instruction: str = "Rewrite the following in clear, natural language.",
) -> Optional[str]:
    """
    Ask the local model to rewrite/expand `grounding_text` per
    `instruction`, grounded strictly in the facts it already contains.

    Returns None (never raises) if the local server is unreachable,
    times out, or returns an unexpected shape.
    """
    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"{instruction}\n\nSource facts:\n{grounding_text}",
                    },
                ],
                "temperature": 0.3,
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — any failure here must fall back silently, never raise
        logger.warning("Local LLM enrichment unavailable, using template output: %s", exc)
        return None

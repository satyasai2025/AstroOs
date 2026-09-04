"""
AstroOS — Embedding Client (Phase IV, IV.3.1 — RAG retrieval)

Converts text into an embedding vector (a list of numbers representing
its meaning) via the same locally-hosted, OpenAI-compatible model
server used by local_llm_client.py — e.g. Ollama's /v1/embeddings
endpoint. Never a cloud API call.

Same fallback contract as local_llm_client.py: any failure (server not
running, timeout, bad response) returns None rather than raising —
callers must treat None as "embedding unavailable," not crash the
request. This is what lets RAG-grounded search degrade gracefully to
"no retrieval, plain template answer" instead of a 500 error.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def embed_text(
    *,
    base_url: str,
    model: str,
    timeout_seconds: float,
    text: str,
) -> Optional[list[float]]:
    """
    Return the embedding vector for `text`, or None on any failure.

    Truncates nothing itself — very long text should be chunked by the
    caller before embedding (see knowledge_retrieval.py), since embedding
    models have their own context limits the caller knows better than
    this generic client does.
    """
    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/embeddings",
            json={"model": model, "input": text},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        embedding = data["data"][0]["embedding"]
        if not isinstance(embedding, list) or not embedding:
            return None
        return [float(x) for x in embedding]
    except Exception as exc:  # noqa: BLE001 — any failure here must fall back silently, never raise
        logger.warning("Embedding unavailable, retrieval will be skipped: %s", exc)
        return None

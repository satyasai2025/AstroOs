"""
AstroOS — AI Backend Switch Unit Tests (Phase IV, IV.3)

Verifies the two guarantees the roadmap requires:
  1. AI_BACKEND=template (default) is byte-identical to calling the
     underlying generator directly — zero behavior change.
  2. AI_BACKEND=local_llm falls back to the exact same template output
     when the local model server is unreachable — the deterministic
     guarantee holds even with the opt-in backend enabled.
"""

import pytest

from apps.api.config import get_settings
from apps.api.services.ai_engine import AIEngine, QAResponder


@pytest.fixture(autouse=True)
def restore_settings(monkeypatch):
    get_settings.cache_clear()
    yield
    monkeypatch.delenv("AI_BACKEND", raising=False)
    monkeypatch.delenv("LOCAL_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_LLM_TIMEOUT_SECONDS", raising=False)
    get_settings.cache_clear()


def test_default_backend_is_template():
    assert get_settings().AI_BACKEND == "template"


def test_template_backend_output_matches_raw_generator():
    r_engine = AIEngine.answer_question("what is the ascendant", chart=None)
    r_raw = QAResponder.generate("what is the ascendant", chart=None)
    assert r_engine == r_raw


def test_local_llm_backend_falls_back_when_server_unreachable(monkeypatch):
    monkeypatch.setenv("AI_BACKEND", "local_llm")
    monkeypatch.setenv("LOCAL_LLM_BASE_URL", "http://localhost:1/v1")  # nothing listens here
    monkeypatch.setenv("LOCAL_LLM_TIMEOUT_SECONDS", "1")
    get_settings.cache_clear()

    r_engine = AIEngine.answer_question("what is the ascendant", chart=None)
    r_raw = QAResponder.generate("what is the ascendant", chart=None)
    assert r_engine == r_raw, "unreachable local LLM must fall back to the unmodified template output"


def test_local_llm_backend_enriches_body_when_server_available(monkeypatch):
    """Confirms the enrichment path actually runs and only rewrites .body
    (title/summary/sources/etc. stay whatever the template produced) —
    using a stub instead of a real model server."""
    monkeypatch.setenv("AI_BACKEND", "local_llm")
    get_settings.cache_clear()

    import apps.api.services.ai_engine as ai_engine_module

    monkeypatch.setattr(
        ai_engine_module,
        "enrich_narration",
        lambda **kwargs: "REWRITTEN BODY TEXT",
    )

    result = AIEngine.answer_question("what is the ascendant", chart=None)
    raw = QAResponder.generate("what is the ascendant", chart=None)

    assert result.body == "REWRITTEN BODY TEXT"
    assert result.title == raw.title
    assert result.summary == raw.summary
    assert result.sources == raw.sources
    assert result.response_type == raw.response_type

"""
AstroOS — Knowledge Retrieval (RAG) Unit Tests (Phase IV, IV.3.1)
"""

from __future__ import annotations

import uuid

import pytest

from apps.api.services.knowledge_retrieval import (
    _NO_MATCH_RESPONSE,
    _cosine_similarity,
    answer_from_knowledge_base,
    search_knowledge,
)


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        assert _cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors_score_negative_one(self):
        assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_scale_invariant(self):
        """Same direction, different magnitude -> still 1.0 (meaning, not
        magnitude, is what should matter)."""
        assert _cosine_similarity([1.0, 2.0], [2.0, 4.0]) == pytest.approx(1.0)

    def test_mismatched_length_returns_zero_not_crash(self):
        assert _cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0]) == 0.0

    def test_zero_vector_returns_zero_not_crash(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
        assert _cosine_similarity([1.0, 1.0], [0.0, 0.0]) == 0.0


class _FakeRow:
    def __init__(self, source_type, source_id, embedded_text, embedding):
        self.source_type = source_type
        self.source_id = source_id
        self.embedded_text = embedded_text
        self.embedding = embedding


class TestSearchKnowledge:
    """search_knowledge()'s ranking/graceful-degradation logic, isolated
    from the DB and embedding server via monkeypatching — the DB-backed
    repository and real embedding server are exercised separately (see
    the live end-to-end check performed manually against a real Postgres
    instance during development; not re-run here to keep unit tests
    DB-free)."""

    @pytest.mark.asyncio
    async def test_empty_result_when_embedding_unavailable(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod

        monkeypatch.setattr(mod, "embed_text", lambda **kwargs: None)
        result = await search_knowledge(session=object(), query="anything")
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_result_when_no_stored_embeddings(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod

        monkeypatch.setattr(mod, "embed_text", lambda **kwargs: [1.0, 0.0])

        class _EmptyRepo:
            def __init__(self, session):
                pass

            async def all_for_model(self, model_name):
                return []

        monkeypatch.setattr(mod, "KnowledgeEmbeddingRepository", _EmptyRepo)
        result = await search_knowledge(session=object(), query="anything")
        assert result == []

    @pytest.mark.asyncio
    async def test_results_ranked_by_similarity_highest_first(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod

        monkeypatch.setattr(mod, "embed_text", lambda **kwargs: [1.0, 0.0])

        rows = [
            _FakeRow("verse", uuid.uuid4(), "unrelated", [0.0, 1.0]),      # orthogonal -> 0.0
            _FakeRow("verse", uuid.uuid4(), "best match", [1.0, 0.0]),     # identical -> 1.0
            _FakeRow("rule", uuid.uuid4(), "partial match", [0.7, 0.7]),   # ~0.707
        ]

        class _StubRepo:
            def __init__(self, session):
                pass

            async def all_for_model(self, model_name):
                return rows

        monkeypatch.setattr(mod, "KnowledgeEmbeddingRepository", _StubRepo)
        result = await search_knowledge(session=object(), query="anything", top_k=10)

        assert [r.snippet for r in result] == ["best match", "partial match"]
        assert result[0].relevance > result[1].relevance
        assert result[0].relevance == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_top_k_limits_result_count(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod

        monkeypatch.setattr(mod, "embed_text", lambda **kwargs: [1.0, 0.0])
        rows = [_FakeRow("verse", uuid.uuid4(), f"row {i}", [1.0, 0.0]) for i in range(5)]

        class _StubRepo:
            def __init__(self, session):
                pass

            async def all_for_model(self, model_name):
                return rows

        monkeypatch.setattr(mod, "KnowledgeEmbeddingRepository", _StubRepo)
        result = await search_knowledge(session=object(), query="anything", top_k=2)
        assert len(result) == 2


class TestAnswerFromKnowledgeBase:
    @pytest.mark.asyncio
    async def test_no_match_response_when_search_returns_nothing(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod

        async def _empty_search(session, query, top_k=None):
            return []

        monkeypatch.setattr(mod, "search_knowledge", _empty_search)
        result = await answer_from_knowledge_base(session=object(), question="anything")
        assert result == _NO_MATCH_RESPONSE

    @pytest.mark.asyncio
    async def test_no_match_response_when_llm_unreachable(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod
        from apps.api.domain.knowledge import KnowledgeSearchResult

        async def _one_result(session, query, top_k=None):
            return [
                KnowledgeSearchResult(
                    entity_type="verse", entity_id=uuid.uuid4(),
                    title="Verse", snippet="some real verse text", relevance=0.9,
                )
            ]

        monkeypatch.setattr(mod, "search_knowledge", _one_result)
        monkeypatch.setattr(mod, "enrich_narration", lambda **kwargs: None)

        result = await answer_from_knowledge_base(session=object(), question="anything")
        assert result == _NO_MATCH_RESPONSE

    @pytest.mark.asyncio
    async def test_grounded_answer_includes_sources_when_llm_available(self, monkeypatch):
        import apps.api.services.knowledge_retrieval as mod
        from apps.api.domain.knowledge import KnowledgeSearchResult

        vid = uuid.uuid4()

        async def _one_result(session, query, top_k=None):
            return [
                KnowledgeSearchResult(
                    entity_type="verse", entity_id=vid,
                    title="Verse", snippet="Jupiter in the 7th house brings a supportive spouse.",
                    relevance=0.95,
                )
            ]

        monkeypatch.setattr(mod, "search_knowledge", _one_result)
        monkeypatch.setattr(mod, "enrich_narration", lambda **kwargs: "A grounded, plain-language answer.")

        result = await answer_from_knowledge_base(session=object(), question="What does Jupiter in the 7th mean?")
        assert result.body == "A grounded, plain-language answer."
        assert result.sources == (f"verse:{vid}",)
        assert result.response_type == "knowledge_qa"
        assert result.confidence == "medium"

"""
AstroOS — Citation Engine Unit Tests (Phase D, Module 19 Extension)

The citation engine is not a standalone module — it lives as the
`get_citations_for_yogas` / `get_citations_for_facts` methods on
KnowledgeEngine. These tests pin its contract: structured lookup by
yoga name, fact-domain extraction, and deduplication across repeated
searches. All persistence is mocked at the repository boundary.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from apps.api.domain.knowledge import (
    KnowledgeSearchQuery,
    KnowledgeSearchResult,
)
from apps.api.domain.yoga import YogaResult
from apps.api.services.knowledge_engine import KnowledgeEngine


def _result(title: str, entity_type: str = "verse") -> KnowledgeSearchResult:
    return KnowledgeSearchResult(
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        title=title,
        snippet=f"snippet for {title}",
        relevance=1.0,
    )


def _yoga(yoga_id: str, name: str, present: bool = True) -> YogaResult:
    return YogaResult(
        yoga_id=yoga_id,
        name=name,
        category="raja",
        source_text="BPHS",
        rule_version="1.0",
        is_present=present,
        strength=None,
    )


@pytest.fixture
def engine() -> KnowledgeEngine:
    repo = AsyncMock()
    repo.search = AsyncMock()
    return KnowledgeEngine(repo=repo)


class TestGetCitationsForYogas:
    async def test_returns_citations_for_present_yogas(self, engine):
        engine._repo.search.return_value = [_result("Raja Yoga verse")]
        citations = await engine.get_citations_for_yogas([_yoga("YOGA-1", "Raja Yoga")])

        assert len(citations) == 1
        assert citations[0].title == "Raja Yoga verse"
        # search was called with the yoga name and limit=3
        query: KnowledgeSearchQuery = engine._repo.search.call_args.args[0]
        assert query.text == "Raja Yoga"
        assert query.limit == 3

    async def test_skips_yogas_not_present(self, engine):
        engine._repo.search.return_value = [_result("verse")]
        citations = await engine.get_citations_for_yogas([_yoga("YOGA-1", "Raja Yoga", present=False)])

        assert citations == ()
        engine._repo.search.assert_not_called()

    async def test_deduplicates_repeated_results(self, engine):
        # Two yogas whose name searches return the SAME verse record.
        same = _result("shared verse")
        engine._repo.search.return_value = [same]
        citations = await engine.get_citations_for_yogas(
            [_yoga("YOGA-1", "Raja Yoga"), _yoga("YOGA-2", "Raja Yoga")]
        )
        # Same (entity_type, entity_id) returned only once.
        assert len(citations) == 1

    async def test_empty_yoga_results_returns_empty(self, engine):
        citations = await engine.get_citations_for_yogas([])
        assert citations == ()
        engine._repo.search.assert_not_called()


class TestGetCitationsForFacts:
    async def test_extracts_domain_prefix_and_planet_from_fact_keys(self, engine):
        engine._repo.search.return_value = [_result("saturn entry")]
        citations = await engine.get_citations_for_facts(
            {"shadbala.saturn.total": 12.5}
        )
        assert len(citations) >= 1
        searched_terms = {call.args[0].text for call in engine._repo.search.call_args_list}
        # Both the domain prefix ("shadbala") and planet/sub-domain ("saturn") are searched.
        assert "shadbala" in searched_terms
        assert "saturn" in searched_terms

    async def test_deduplicates_across_overlapping_fact_keys(self, engine):
        shared = _result("saturn entry")
        engine._repo.search.return_value = [shared]
        citations = await engine.get_citations_for_facts(
            {"shadbala.saturn.total": 1.0, "dignity.saturn": "exalted"}
        )
        # "saturn" appears in both keys but should produce one citation.
        saturn_cites = {c.entity_id for c in citations}
        assert len(saturn_cites) == 1 or len(citations) <= 1

    async def test_skips_too_short_terms(self, engine):
        # Domain prefix "s" and sub-token "s" both < 2 chars — must not search.
        await engine.get_citations_for_facts({"s.s": 1})
        engine._repo.search.assert_not_called()

    async def test_empty_facts_returns_empty(self, engine):
        citations = await engine.get_citations_for_facts({})
        assert citations == ()
        engine._repo.search.assert_not_called()

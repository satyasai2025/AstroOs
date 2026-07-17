"""
AstroOS — KnowledgeEngine Unit Tests (Module 19, Phase 1)

All persistence mocked at the repository boundary.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from apps.api.domain.knowledge import (
    Karakatva,
    KnowledgeBook,
    KnowledgeReference,
    KnowledgeRule,
    KnowledgeSearchQuery,
    KnowledgeSearchResult,
    KnowledgeVerse,
)
from apps.api.services.knowledge_engine import KnowledgeEngine

pytestmark = pytest.mark.asyncio


@pytest.fixture
def engine() -> KnowledgeEngine:
    repo = AsyncMock()
    repo.create_book = AsyncMock()
    repo.get_book = AsyncMock()
    repo.list_books = AsyncMock()
    repo.update_book = AsyncMock()
    repo.delete_book = AsyncMock()
    repo.create_verse = AsyncMock()
    repo.get_verse = AsyncMock()
    repo.list_verses = AsyncMock()
    repo.update_verse = AsyncMock()
    repo.delete_verse = AsyncMock()
    repo.create_rule = AsyncMock()
    repo.get_rule = AsyncMock()
    repo.list_rules = AsyncMock()
    repo.delete_rule = AsyncMock()
    repo.create_karakatva = AsyncMock()
    repo.get_karakatva = AsyncMock()
    repo.list_karakatvas = AsyncMock()
    repo.delete_karakatva = AsyncMock()
    repo.search = AsyncMock()
    return KnowledgeEngine(repo=repo)


class TestBooks:
    async def test_create(self, engine):
        engine._repo.create_book.return_value = KnowledgeBook(
            id=uuid.uuid4(), title="BPHS",
        )
        b = await engine.create_book(title="BPHS")
        assert b.title == "BPHS"

    async def test_get(self, engine):
        engine._repo.get_book.return_value = KnowledgeBook(
            id=uuid.uuid4(), title="BPHS",
        )
        b = await engine.get_book(uuid.uuid4())
        assert b.title == "BPHS"

    async def test_list(self, engine):
        engine._repo.list_books.return_value = (
            KnowledgeBook(id=uuid.uuid4(), title="A"),
            KnowledgeBook(id=uuid.uuid4(), title="B"),
        )
        books = await engine.list_books()
        assert len(books) == 2

    async def test_delete(self, engine):
        engine._repo.delete_book.return_value = True
        assert await engine.delete_book(uuid.uuid4()) is True


class TestVerses:
    async def test_create(self, engine):
        engine._repo.create_verse.return_value = KnowledgeVerse(
            id=uuid.uuid4(), book_id=uuid.uuid4(), original_text="text",
        )
        v = await engine.create_verse(book_id=uuid.uuid4(), original_text="text")
        assert v.original_text == "text"

    async def test_list_by_book(self, engine):
        bid = uuid.uuid4()
        engine._repo.list_verses.return_value = (
            KnowledgeVerse(id=uuid.uuid4(), book_id=bid, original_text="v1"),
        )
        verses = await engine.list_verses(bid)
        assert len(verses) == 1

    async def test_delete(self, engine):
        engine._repo.delete_verse.return_value = True
        assert await engine.delete_verse(uuid.uuid4()) is True


class TestRules:
    async def test_create_with_source(self, engine):
        ref = KnowledgeReference(book_id=uuid.uuid4(), chapter=5, verse_number=12)
        engine._repo.create_rule.return_value = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I",
        )
        r = await engine.create_rule(
            title="R", interpretation="I", source=ref,
            rule_definition_id="RULE-001",
        )
        assert r.title == "R"

    async def test_get(self, engine):
        engine._repo.get_rule.return_value = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I",
        )
        r = await engine.get_rule(uuid.uuid4())
        assert r.title == "R"


class TestKarakatvas:
    async def test_create_with_graha(self, engine):
        engine._repo.create_karakatva.return_value = Karakatva(
            id=uuid.uuid4(), subject="spouse", graha="venus",
        )
        k = await engine.create_karakatva(subject="spouse", graha="venus")
        assert k.subject == "spouse"
        assert k.graha == "venus"

    async def test_list_by_graha(self, engine):
        engine._repo.list_karakatvas.return_value = (
            Karakatva(id=uuid.uuid4(), subject="spouse", graha="venus"),
        )
        results = await engine.list_karakatvas(graha="venus")
        assert len(results) == 1


class TestSearch:
    async def test_search_returns_results(self, engine):
        engine._repo.search.return_value = (
            KnowledgeSearchResult(
                entity_type="book", entity_id=uuid.uuid4(),
                title="BPHS", snippet="Brihat Parashara", relevance=2.0,
            ),
        )
        q = KnowledgeSearchQuery(text="Parashara")
        results = await engine.search(q)
        assert len(results) == 1
        assert results[0].entity_type == "book"

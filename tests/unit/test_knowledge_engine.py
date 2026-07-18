"""
AstroOS — KnowledgeEngine Unit Tests (Module 19, Phase B — Versioned)

All persistence mocked at the repository boundary.
Tests cover: CRUD, versioning (update creates new version rows),
citation validation, and search.
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


@pytest.fixture
def engine() -> KnowledgeEngine:
    repo = AsyncMock()
    repo.create_book = AsyncMock()
    repo.get_book = AsyncMock()
    repo.get_latest_book = AsyncMock()
    repo.list_books = AsyncMock()
    repo.update_book = AsyncMock()
    repo.delete_book = AsyncMock()
    repo.create_verse = AsyncMock()
    repo.get_verse = AsyncMock()
    repo.get_latest_verse = AsyncMock()
    repo.list_verses = AsyncMock()
    repo.update_verse = AsyncMock()
    repo.delete_verse = AsyncMock()
    repo.create_rule = AsyncMock()
    repo.get_rule = AsyncMock()
    repo.get_latest_rule = AsyncMock()
    repo.list_rules = AsyncMock()
    repo.update_rule = AsyncMock()
    repo.delete_rule = AsyncMock()
    repo.create_karakatva = AsyncMock()
    repo.get_karakatva = AsyncMock()
    repo.get_latest_karakatva = AsyncMock()
    repo.list_karakatvas = AsyncMock()
    repo.update_karakatva = AsyncMock()
    repo.delete_karakatva = AsyncMock()
    repo.search = AsyncMock()
    repo.reference_exists = AsyncMock()
    return KnowledgeEngine(repo=repo)


# ── Books ────────────────────────────────────────────────────────────────────


class TestBooks:
    async def test_create(self, engine):
        engine._repo.create_book.return_value = KnowledgeBook(
            id=uuid.uuid4(), title="BPHS", version=1,
        )
        b = await engine.create_book(title="BPHS")
        assert b.title == "BPHS"
        assert b.version == 1

    async def test_get(self, engine):
        book_id = uuid.uuid4()
        engine._repo.get_book.return_value = KnowledgeBook(
            id=book_id, title="BPHS", version=1,
        )
        b = await engine.get_book(book_id)
        assert b.title == "BPHS"

    async def test_list(self, engine):
        engine._repo.list_books.return_value = (
            KnowledgeBook(id=uuid.uuid4(), title="A", version=1),
            KnowledgeBook(id=uuid.uuid4(), title="B", version=1),
        )
        books = await engine.list_books()
        assert len(books) == 2

    async def test_update_creates_new_version(self, engine):
        original = KnowledgeBook(id=uuid.uuid4(), title="BPHS", version=1)
        updated = KnowledgeBook(id=uuid.uuid4(), title="BPHS v2", version=2)
        engine._repo.update_book.return_value = updated
        result = await engine.update_book(original.id, title="BPHS v2", version_comment="updated edition")
        assert result.version == 2
        assert result.title == "BPHS v2"

    async def test_get_latest(self, engine):
        book_id = uuid.uuid4()
        engine._repo.get_latest_book.return_value = KnowledgeBook(
            id=book_id, title="BPHS v2", version=2,
        )
        b = await engine.get_latest_book(book_id)
        assert b.version == 2

    async def test_delete(self, engine):
        engine._repo.delete_book.return_value = True
        assert await engine.delete_book(uuid.uuid4()) is True

    async def test_create_with_version_comment(self, engine):
        engine._repo.create_book.return_value = KnowledgeBook(
            id=uuid.uuid4(), title="BPHS", version=1, version_comment="Initial import",
        )
        b = await engine.create_book(title="BPHS", version_comment="Initial import")
        assert b.version_comment == "Initial import"


# ── Verses ───────────────────────────────────────────────────────────────────


class TestVerses:
    async def test_create(self, engine):
        engine._repo.create_verse.return_value = KnowledgeVerse(
            id=uuid.uuid4(), book_id=uuid.uuid4(), original_text="text", version=1,
        )
        v = await engine.create_verse(book_id=uuid.uuid4(), original_text="text")
        assert v.original_text == "text"

    async def test_list_by_book(self, engine):
        bid = uuid.uuid4()
        engine._repo.list_verses.return_value = (
            KnowledgeVerse(id=uuid.uuid4(), book_id=bid, original_text="v1", version=1),
        )
        verses = await engine.list_verses(bid)
        assert len(verses) == 1

    async def test_delete(self, engine):
        engine._repo.delete_verse.return_value = True
        assert await engine.delete_verse(uuid.uuid4()) is True

    async def test_update_creates_new_version(self, engine):
        original = KnowledgeVerse(id=uuid.uuid4(), book_id=uuid.uuid4(), original_text="old", version=1)
        updated = KnowledgeVerse(id=uuid.uuid4(), book_id=original.book_id, original_text="new", version=2)
        engine._repo.update_verse.return_value = updated
        result = await engine.update_verse(original.id, original_text="new", version_comment="fixed typo")
        assert result.version == 2
        assert result.original_text == "new"

    async def test_get_latest(self, engine):
        verse_id = uuid.uuid4()
        engine._repo.get_latest_verse.return_value = KnowledgeVerse(
            id=verse_id, book_id=uuid.uuid4(), original_text="new", version=2,
        )
        v = await engine.get_latest_verse(verse_id)
        assert v.version == 2


# ── Rules ────────────────────────────────────────────────────────────────────


class TestRules:
    async def test_create_with_source(self, engine):
        ref = KnowledgeReference(book_id=uuid.uuid4(), chapter=5, verse_number=12)
        engine._repo.create_rule.return_value = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I", version=1,
        )
        r = await engine.create_rule(
            title="R", interpretation="I", source=ref,
            rule_definition_id="RULE-001",
        )
        assert r.title == "R"

    async def test_create_with_source_validates_citation(self, engine):
        """Citation validation must check reference_exists before creating."""
        ref = KnowledgeReference(book_id=uuid.uuid4(), chapter=5, verse_number=12)
        engine._repo.reference_exists.return_value = True
        engine._repo.create_rule.return_value = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I", version=1,
        )
        r = await engine.create_rule(title="R", interpretation="I", source=ref)
        engine._repo.reference_exists.assert_called_once_with(ref)
        assert r.title == "R"

    async def test_create_with_bad_source_raises(self, engine):
        """Creating a rule with a non-existent reference must raise ValueError."""
        ref = KnowledgeReference(book_id=uuid.uuid4())
        engine._repo.reference_exists.return_value = False
        with pytest.raises(ValueError, match="non-existent"):
            await engine.create_rule(title="R", interpretation="I", source=ref)

    async def test_get(self, engine):
        engine._repo.get_rule.return_value = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I", version=1,
        )
        r = await engine.get_rule(uuid.uuid4())
        assert r.title == "R"

    async def test_update(self, engine):
        original = KnowledgeRule(id=uuid.uuid4(), title="R", interpretation="I", version=1)
        updated = KnowledgeRule(id=uuid.uuid4(), title="R2", interpretation="I2", version=2)
        engine._repo.update_rule.return_value = updated
        result = await engine.update_rule(original.id, title="R2", version_comment="refined")
        assert result.version == 2
        assert result.title == "R2"

    async def test_get_latest(self, engine):
        rule_id = uuid.uuid4()
        engine._repo.get_latest_rule.return_value = KnowledgeRule(
            id=rule_id, title="R2", interpretation="I2", version=2,
        )
        r = await engine.get_latest_rule(rule_id)
        assert r.version == 2


# ── Karakatvas ───────────────────────────────────────────────────────────────


class TestKarakatvas:
    async def test_create_with_graha(self, engine):
        engine._repo.create_karakatva.return_value = Karakatva(
            id=uuid.uuid4(), subject="spouse", graha="venus", version=1,
        )
        k = await engine.create_karakatva(subject="spouse", graha="venus")
        assert k.subject == "spouse"
        assert k.graha == "venus"

    async def test_list_by_graha(self, engine):
        engine._repo.list_karakatvas.return_value = (
            Karakatva(id=uuid.uuid4(), subject="spouse", graha="venus", version=1),
        )
        results = await engine.list_karakatvas(graha="venus")
        assert len(results) == 1

    async def test_create_with_source_validates_citation(self, engine):
        ref = KnowledgeReference(book_id=uuid.uuid4())
        engine._repo.reference_exists.return_value = True
        engine._repo.create_karakatva.return_value = Karakatva(
            id=uuid.uuid4(), subject="spouse", graha="venus", version=1,
        )
        k = await engine.create_karakatva(subject="spouse", source=ref)
        engine._repo.reference_exists.assert_called_once_with(ref)
        assert k.subject == "spouse"

    async def test_update(self, engine):
        original = Karakatva(id=uuid.uuid4(), subject="spouse", graha="venus", version=1)
        updated = Karakatva(id=uuid.uuid4(), subject="partner", graha="venus", version=2)
        engine._repo.update_karakatva.return_value = updated
        result = await engine.update_karakatva(original.id, subject="partner", version_comment="refined")
        assert result.version == 2
        assert result.subject == "partner"

    async def test_get_latest(self, engine):
        k_id = uuid.uuid4()
        engine._repo.get_latest_karakatva.return_value = Karakatva(
            id=k_id, subject="spouse", graha="venus", version=2,
        )
        k = await engine.get_latest_karakatva(k_id)
        assert k.version == 2

    async def test_validate_citation(self, engine):
        ref = KnowledgeReference(book_id=uuid.uuid4())
        engine._repo.reference_exists.return_value = True
        assert await engine.validate_citation(ref) is True
        engine._repo.reference_exists.assert_called_once_with(ref)


# ── Search ───────────────────────────────────────────────────────────────────


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

"""
AstroOS — Knowledge Domain Model Unit Tests (Module 19, Phase 1)
"""

import dataclasses
import uuid

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


class TestKnowledgeReference:
    def test_is_frozen(self):
        r = KnowledgeReference(book_id=uuid.uuid4())
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.chapter = 5

    def test_defaults(self):
        r = KnowledgeReference(book_id=uuid.uuid4())
        assert r.chapter is None
        assert r.verse_number is None
        assert r.edition is None
        assert r.translator is None


class TestKnowledgeBook:
    def test_is_frozen(self):
        b = KnowledgeBook(id=uuid.uuid4(), title="BPHS")
        with pytest.raises(dataclasses.FrozenInstanceError):
            b.title = "Other"


class TestKnowledgeVerse:
    def test_is_frozen(self):
        v = KnowledgeVerse(id=uuid.uuid4(), book_id=uuid.uuid4(), original_text="text")
        with pytest.raises(dataclasses.FrozenInstanceError):
            v.translation = "changed"

    def test_optional_fields(self):
        v = KnowledgeVerse(id=uuid.uuid4(), book_id=uuid.uuid4(), original_text="text")
        assert v.chapter is None
        assert v.translation is None


class TestKnowledgeRule:
    def test_is_frozen(self):
        r = KnowledgeRule(id=uuid.uuid4(), title="R", interpretation="I")
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.title = "Other"

    def test_optional_rule_definition_id(self):
        r = KnowledgeRule(
            id=uuid.uuid4(), title="R", interpretation="I",
            rule_definition_id="RULE-HOUSE-001",
        )
        assert r.rule_definition_id == "RULE-HOUSE-001"

    def test_optional_source(self):
        ref = KnowledgeReference(book_id=uuid.uuid4(), chapter=5, verse_number=12)
        r = KnowledgeRule(id=uuid.uuid4(), title="R", interpretation="I", source=ref)
        assert r.source.verse_number == 12


class TestKarakatva:
    def test_is_frozen(self):
        k = Karakatva(id=uuid.uuid4(), subject="wealth")
        with pytest.raises(dataclasses.FrozenInstanceError):
            k.subject = "changed"

    def test_optional_source(self):
        ref = KnowledgeReference(book_id=uuid.uuid4())
        k = Karakatva(id=uuid.uuid4(), subject="spouse", graha="venus", source=ref)
        assert k.graha == "venus"
        assert k.source is ref


class TestKnowledgeSearchQuery:
    def test_defaults(self):
        q = KnowledgeSearchQuery(text="test")
        assert q.limit == 50
        assert q.offset == 0
        assert q.entity_type is None


class TestKnowledgeSearchResult:
    def test_defaults(self):
        r = KnowledgeSearchResult(
            entity_type="book", entity_id=uuid.uuid4(),
            title="T", snippet="snip", relevance=1.0,
        )
        assert r.book_title is None
        assert r.tradition is None

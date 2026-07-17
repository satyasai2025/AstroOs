"""
AstroOS — Knowledge Engine (Module 19, Phase 1)

Manages the classical astrological knowledge base — books, verses,
interpretation rules, and karakatvas. CRUD + substring search.

Delegates all persistence to KnowledgeRepository.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from apps.api.domain.knowledge import (
    Karakatva,
    KnowledgeBook,
    KnowledgeReference,
    KnowledgeRule,
    KnowledgeSearchQuery,
    KnowledgeSearchResult,
    KnowledgeVerse,
)


class KnowledgeEngine:
    """Stateless — delegates to KnowledgeRepository for all persistence."""

    def __init__(self, repo=None) -> None:
        self._repo = repo

    # ── Books ─────────────────────────────────────────────────────────────

    async def create_book(
        self, title: str,
        author: str | None = None,
        language: str | None = None,
        period_ce: str | None = None,
        tradition: str | None = None,
        description: str | None = None,
    ) -> KnowledgeBook:
        return await self._repo.create_book(
            title=title, author=author, language=language,
            period_ce=period_ce, tradition=tradition,
            description=description,
        )

    async def get_book(self, book_id: uuid.UUID) -> KnowledgeBook | None:
        return await self._repo.get_book(book_id)

    async def list_books(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeBook, ...]:
        return await self._repo.list_books(tradition=tradition)

    async def update_book(
        self, book_id: uuid.UUID, **fields: Any,
    ) -> KnowledgeBook | None:
        return await self._repo.update_book(book_id, **fields)

    async def delete_book(self, book_id: uuid.UUID) -> bool:
        return await self._repo.delete_book(book_id)

    # ── Verses ────────────────────────────────────────────────────────────

    async def create_verse(
        self, book_id: uuid.UUID, original_text: str,
        chapter: int | None = None,
        verse_number: int | None = None,
        transliteration: str | None = None,
        translation: str | None = None,
        commentary: str | None = None,
    ) -> KnowledgeVerse:
        return await self._repo.create_verse(
            book_id=book_id, original_text=original_text,
            chapter=chapter, verse_number=verse_number,
            transliteration=transliteration, translation=translation,
            commentary=commentary,
        )

    async def get_verse(self, verse_id: uuid.UUID) -> KnowledgeVerse | None:
        return await self._repo.get_verse(verse_id)

    async def list_verses(
        self, book_id: uuid.UUID,
    ) -> tuple[KnowledgeVerse, ...]:
        return await self._repo.list_verses(book_id)

    async def update_verse(
        self, verse_id: uuid.UUID, **fields: Any,
    ) -> KnowledgeVerse | None:
        return await self._repo.update_verse(verse_id, **fields)

    async def delete_verse(self, verse_id: uuid.UUID) -> bool:
        return await self._repo.delete_verse(verse_id)

    # ── Rules ─────────────────────────────────────────────────────────────

    async def create_rule(
        self, title: str, interpretation: str,
        source: KnowledgeReference | None = None,
        rule_definition_id: str | None = None,
        tradition: str | None = None,
        confidence: float | None = None,
    ) -> KnowledgeRule:
        verse_id = source.book_id if source else None  # simplified mapping
        return await self._repo.create_rule(
            title=title, interpretation=interpretation,
            verse_id=verse_id,
            rule_definition_id=rule_definition_id,
            tradition=tradition, confidence=confidence,
        )

    async def get_rule(self, rule_id: uuid.UUID) -> KnowledgeRule | None:
        return await self._repo.get_rule(rule_id)

    async def list_rules(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeRule, ...]:
        return await self._repo.list_rules(tradition=tradition)

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        return await self._repo.delete_rule(rule_id)

    # ── Karakatvas ────────────────────────────────────────────────────────

    async def create_karakatva(
        self, subject: str,
        graha: str | None = None,
        sign_id: int | None = None,
        house_number: int | None = None,
        tradition: str | None = None,
        source: KnowledgeReference | None = None,
        description: str | None = None,
    ) -> Karakatva:
        verse_id = source.book_id if source else None
        return await self._repo.create_karakatva(
            subject=subject, graha=graha, sign_id=sign_id,
            house_number=house_number, tradition=tradition,
            source_verse_id=verse_id, description=description,
        )

    async def get_karakatva(
        self, karakatva_id: uuid.UUID,
    ) -> Karakatva | None:
        return await self._repo.get_karakatva(karakatva_id)

    async def list_karakatvas(
        self, graha: str | None = None,
        subject: str | None = None,
    ) -> tuple[Karakatva, ...]:
        return await self._repo.list_karakatvas(graha=graha, subject=subject)

    async def delete_karakatva(self, karakatva_id: uuid.UUID) -> bool:
        return await self._repo.delete_karakatva(karakatva_id)

    # ── Search ────────────────────────────────────────────────────────────

    async def search(
        self, query: KnowledgeSearchQuery,
    ) -> tuple[KnowledgeSearchResult, ...]:
        return await self._repo.search(query)

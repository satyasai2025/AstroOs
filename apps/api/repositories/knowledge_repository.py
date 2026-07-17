"""
AstroOS — Knowledge Repository (Module 19, Phase 1)

Persistence for books, verses, rules, and karakatvas using the existing
tables from migration 0002.

Returns domain objects, never ORM models — same convention as every
other repository in this codebase.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.knowledge import (
    Karakatva,
    KnowledgeBook,
    KnowledgeReference,
    KnowledgeRule,
    KnowledgeSearchQuery,
    KnowledgeSearchResult,
    KnowledgeVerse,
)
from apps.api.models.astrology import (
    BookModel,
    KarakatvaModel,
    RuleModel,
    VerseModel,
)


def _ref_from_verse(verse: VerseModel, book_id: uuid.UUID) -> KnowledgeReference:
    return KnowledgeReference(
        book_id=book_id,
        chapter=verse.chapter,
        verse_number=verse.verse_number,
    )


def _book_to_domain(m: BookModel) -> KnowledgeBook:
    return KnowledgeBook(
        id=m.id, title=m.title, author=m.author,
        language=m.language, period_ce=m.period_ce,
        tradition=m.tradition, description=m.description,
    )


def _verse_to_domain(m: VerseModel) -> KnowledgeVerse:
    return KnowledgeVerse(
        id=m.id, book_id=m.book_id, original_text=m.original_text,
        chapter=m.chapter, verse_number=m.verse_number,
        transliteration=m.transliteration, translation=m.translation,
        commentary=m.commentary,
    )


def _rule_to_domain(m: RuleModel) -> KnowledgeRule:
    ref = None
    if m.verse_id:
        ref = KnowledgeReference(book_id=uuid.UUID(int=0), verse_number=m.verse_id.int)
    return KnowledgeRule(
        id=m.id, title=m.title, interpretation=m.interpretation,
        source=ref, tradition=m.tradition,
        confidence=float(m.confidence) if m.confidence else None,
    )


def _karakatva_to_domain(m: KarakatvaModel) -> Karakatva:
    ref = None
    if m.source_verse_id:
        ref = KnowledgeReference(book_id=uuid.UUID(int=0), verse_number=m.source_verse_id.int)
    return Karakatva(
        id=m.id, subject=m.subject, graha=m.graha,
        sign_id=m.sign_id, house_number=m.house_number,
        tradition=m.tradition, source=ref, description=m.description,
    )


class KnowledgeRepository:
    """Data access for the classical knowledge base."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Books ─────────────────────────────────────────────────────────────

    async def create_book(
        self, title: str, author: str | None = None,
        language: str | None = None, period_ce: str | None = None,
        tradition: str | None = None, description: str | None = None,
    ) -> KnowledgeBook:
        m = BookModel(
            title=title, author=author, language=language,
            period_ce=period_ce, tradition=tradition, description=description,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _book_to_domain(m)

    async def get_book(self, book_id: uuid.UUID) -> Optional[KnowledgeBook]:
        stmt = select(BookModel).where(BookModel.id == book_id, BookModel.deleted_at.is_(None))
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _book_to_domain(row) if row else None

    async def list_books(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeBook, ...]:
        stmt = select(BookModel).where(BookModel.deleted_at.is_(None))
        if tradition:
            stmt = stmt.where(BookModel.tradition == tradition)
        stmt = stmt.order_by(BookModel.title)
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(_book_to_domain(r) for r in rows)

    async def update_book(
        self, book_id: uuid.UUID, **fields: Any,
    ) -> Optional[KnowledgeBook]:
        orm = {k: v for k, v in fields.items() if k in BookModel.__table__.columns}
        if not orm:
            return await self.get_book(book_id)
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id, BookModel.deleted_at.is_(None))
            .values(**orm).returning(BookModel.id)
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is None:
            return None
        return await self.get_book(book_id)

    async def delete_book(self, book_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id, BookModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(BookModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Verses ────────────────────────────────────────────────────────────

    async def create_verse(
        self, book_id: uuid.UUID, original_text: str,
        chapter: int | None = None, verse_number: int | None = None,
        transliteration: str | None = None, translation: str | None = None,
        commentary: str | None = None,
    ) -> KnowledgeVerse:
        m = VerseModel(
            book_id=book_id, original_text=original_text,
            chapter=chapter, verse_number=verse_number,
            transliteration=transliteration, translation=translation,
            commentary=commentary,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _verse_to_domain(m)

    async def get_verse(self, verse_id: uuid.UUID) -> Optional[KnowledgeVerse]:
        stmt = select(VerseModel).where(VerseModel.id == verse_id, VerseModel.deleted_at.is_(None))
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _verse_to_domain(row) if row else None

    async def list_verses(self, book_id: uuid.UUID) -> tuple[KnowledgeVerse, ...]:
        stmt = (
            select(VerseModel)
            .where(VerseModel.book_id == book_id, VerseModel.deleted_at.is_(None))
            .order_by(VerseModel.chapter, VerseModel.verse_number)
        )
        return tuple(_verse_to_domain(r) for r in (await self._session.execute(stmt)).scalars().all())

    async def update_verse(
        self, verse_id: uuid.UUID, **fields: Any,
    ) -> Optional[KnowledgeVerse]:
        orm = {k: v for k, v in fields.items() if k in VerseModel.__table__.columns}
        if not orm:
            return await self.get_verse(verse_id)
        stmt = (
            update(VerseModel)
            .where(VerseModel.id == verse_id, VerseModel.deleted_at.is_(None))
            .values(**orm).returning(VerseModel.id)
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is None:
            return None
        return await self.get_verse(verse_id)

    async def delete_verse(self, verse_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(VerseModel)
            .where(VerseModel.id == verse_id, VerseModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(VerseModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Rules ─────────────────────────────────────────────────────────────

    async def create_rule(
        self, title: str, interpretation: str,
        verse_id: uuid.UUID | None = None,
        rule_definition_id: str | None = None,
        tradition: str | None = None,
        confidence: float | None = None,
    ) -> KnowledgeRule:
        m = RuleModel(
            verse_id=verse_id, title=title, interpretation=interpretation,
            tradition=tradition, confidence=confidence,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _rule_to_domain(m)

    async def get_rule(self, rule_id: uuid.UUID) -> Optional[KnowledgeRule]:
        stmt = select(RuleModel).where(RuleModel.id == rule_id, RuleModel.deleted_at.is_(None))
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _rule_to_domain(row) if row else None

    async def list_rules(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeRule, ...]:
        stmt = select(RuleModel).where(RuleModel.deleted_at.is_(None))
        if tradition:
            stmt = stmt.where(RuleModel.tradition == tradition)
        stmt = stmt.order_by(RuleModel.title)
        return tuple(_rule_to_domain(r) for r in (await self._session.execute(stmt)).scalars().all())

    async def delete_rule(self, rule_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(RuleModel)
            .where(RuleModel.id == rule_id, RuleModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(RuleModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Karakatvas ────────────────────────────────────────────────────────

    async def create_karakatva(
        self, subject: str,
        graha: str | None = None,
        sign_id: int | None = None,
        house_number: int | None = None,
        tradition: str | None = None,
        source_verse_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> Karakatva:
        m = KarakatvaModel(
            subject=subject, graha=graha, sign_id=sign_id,
            house_number=house_number, tradition=tradition,
            source_verse_id=source_verse_id, description=description,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _karakatva_to_domain(m)

    async def get_karakatva(self, karakatva_id: uuid.UUID) -> Optional[Karakatva]:
        stmt = select(KarakatvaModel).where(
            KarakatvaModel.id == karakatva_id, KarakatvaModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _karakatva_to_domain(row) if row else None

    async def list_karakatvas(
        self, graha: str | None = None, subject: str | None = None,
    ) -> tuple[Karakatva, ...]:
        stmt = select(KarakatvaModel).where(KarakatvaModel.deleted_at.is_(None))
        if graha:
            stmt = stmt.where(KarakatvaModel.graha == graha)
        if subject:
            stmt = stmt.where(KarakatvaModel.subject.ilike(f"%{subject}%"))
        stmt = stmt.order_by(KarakatvaModel.subject)
        return tuple(_karakatva_to_domain(r) for r in (await self._session.execute(stmt)).scalars().all())

    async def delete_karakatva(self, karakatva_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(KarakatvaModel)
            .where(KarakatvaModel.id == karakatva_id, KarakatvaModel.deleted_at.is_(None))
            .values(deleted_at=now).returning(KarakatvaModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    # ── Search ────────────────────────────────────────────────────────────

    async def search(
        self, query: KnowledgeSearchQuery,
    ) -> tuple[KnowledgeSearchResult, ...]:
        """Substring search across all entity types with relevance scoring."""
        results: list[KnowledgeSearchResult] = []

        term = query.text.lower()

        # Search books.
        if not query.entity_type or query.entity_type == "book":
            stmt = select(BookModel).where(BookModel.deleted_at.is_(None))
            # Apply tradition filter.
            if query.tradition:
                stmt = stmt.where(BookModel.tradition == query.tradition)
            rows = (await self._session.execute(stmt)).scalars().all()
            for r in rows:
                score = 0.0
                if term in r.title.lower():
                    score += 2.0
                    snippet = r.title
                elif r.description and term in r.description.lower():
                    score += 1.0
                    snippet = r.description[:200]
                else:
                    continue
                results.append(KnowledgeSearchResult(
                    entity_type="book", entity_id=r.id, title=r.title,
                    snippet=snippet, relevance=score, tradition=r.tradition,
                ))

        # Search verses.
        if not query.entity_type or query.entity_type == "verse":
            stmt = select(VerseModel).where(VerseModel.deleted_at.is_(None))
            if query.book_id:
                stmt = stmt.where(VerseModel.book_id == query.book_id)
            rows = (await self._session.execute(stmt)).scalars().all()
            book_titles = {b.id: b.title for b in (
                await self._session.execute(
                    select(BookModel).where(BookModel.deleted_at.is_(None))
                )).scalars().all()}
            for r in rows:
                score = 0.0
                snippet = ""
                if term in r.original_text.lower():
                    score += 2.0
                    snippet = r.original_text[:200]
                elif r.translation and term in r.translation.lower():
                    score += 1.0
                    snippet = r.translation[:200]
                else:
                    continue
                title = f"Verse {r.chapter}.{r.verse_number}" if r.chapter else "Verse"
                results.append(KnowledgeSearchResult(
                    entity_type="verse", entity_id=r.id, title=title,
                    snippet=snippet, relevance=score,
                    book_title=book_titles.get(r.book_id),
                ))

        # Sort by relevance descending, apply pagination.
        results.sort(key=lambda x: x.relevance, reverse=True)
        paginated = results[query.offset:query.offset + query.limit]
        return tuple(paginated)

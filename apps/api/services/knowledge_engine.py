"""
AstroOS — Knowledge Engine (Module 19, Phase B — Versioned)

Manages the classical astrological knowledge base — books, verses,
interpretation rules, and karakatvas. Versioned CRUD + substring search +
citation validation.

Delegates all persistence to KnowledgeRepository.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
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
        version_comment: str | None = None,
    ) -> KnowledgeBook:
        return await self._repo.create_book(
            title=title, author=author, language=language,
            period_ce=period_ce, tradition=tradition,
            description=description,
            version_comment=version_comment,
        )

    async def get_book(self, book_id: uuid.UUID) -> KnowledgeBook | None:
        return await self._repo.get_book(book_id)

    async def get_latest_book(
        self, original_id: uuid.UUID,
    ) -> KnowledgeBook | None:
        return await self._repo.get_latest_book(original_id)

    async def list_books(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeBook, ...]:
        return await self._repo.list_books(tradition=tradition)

    async def update_book(
        self, book_id: uuid.UUID,
        version_comment: str | None = None,
        **fields: Any,
    ) -> KnowledgeBook | None:
        return await self._repo.update_book(
            book_id, version_comment=version_comment, **fields,
        )

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
        version_comment: str | None = None,
    ) -> KnowledgeVerse:
        return await self._repo.create_verse(
            book_id=book_id, original_text=original_text,
            chapter=chapter, verse_number=verse_number,
            transliteration=transliteration, translation=translation,
            commentary=commentary,
            version_comment=version_comment,
        )

    async def get_verse(self, verse_id: uuid.UUID) -> KnowledgeVerse | None:
        return await self._repo.get_verse(verse_id)

    async def get_latest_verse(
        self, original_id: uuid.UUID,
    ) -> KnowledgeVerse | None:
        return await self._repo.get_latest_verse(original_id)

    async def list_verses(
        self, book_id: uuid.UUID,
    ) -> tuple[KnowledgeVerse, ...]:
        return await self._repo.list_verses(book_id)

    async def update_verse(
        self, verse_id: uuid.UUID,
        version_comment: str | None = None,
        **fields: Any,
    ) -> KnowledgeVerse | None:
        return await self._repo.update_verse(
            verse_id, version_comment=version_comment, **fields,
        )

    async def delete_verse(self, verse_id: uuid.UUID) -> bool:
        return await self._repo.delete_verse(verse_id)

    # ── Rules ─────────────────────────────────────────────────────────────

    async def create_rule(
        self, title: str, interpretation: str,
        source: KnowledgeReference | None = None,
        rule_definition_id: str | None = None,
        tradition: str | None = None,
        confidence: float | None = None,
        version_comment: str | None = None,
    ) -> KnowledgeRule:
        """Create a knowledge rule, validating the source reference if provided."""
        if source is not None:
            if not await self._repo.reference_exists(source):
                raise ValueError(
                    f"Source reference points to non-existent book "
                    f"({source.book_id}) or verse"
                )
        verse_id = source.book_id if source else None
        return await self._repo.create_rule(
            title=title, interpretation=interpretation,
            verse_id=verse_id,
            rule_definition_id=rule_definition_id,
            tradition=tradition, confidence=confidence,
            version_comment=version_comment,
        )

    async def get_rule(self, rule_id: uuid.UUID) -> KnowledgeRule | None:
        return await self._repo.get_rule(rule_id)

    async def get_latest_rule(
        self, original_id: uuid.UUID,
    ) -> KnowledgeRule | None:
        return await self._repo.get_latest_rule(original_id)

    async def list_rules(
        self, tradition: str | None = None,
    ) -> tuple[KnowledgeRule, ...]:
        return await self._repo.list_rules(tradition=tradition)

    async def update_rule(
        self, rule_id: uuid.UUID,
        version_comment: str | None = None,
        **fields: Any,
    ) -> KnowledgeRule | None:
        return await self._repo.update_rule(
            rule_id, version_comment=version_comment, **fields,
        )

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
        version_comment: str | None = None,
    ) -> Karakatva:
        """Create a karakatva, validating the source reference if provided."""
        if source is not None:
            if not await self._repo.reference_exists(source):
                raise ValueError(
                    f"Source reference points to non-existent book "
                    f"({source.book_id}) or verse"
                )
        verse_id = source.book_id if source else None
        return await self._repo.create_karakatva(
            subject=subject, graha=graha, sign_id=sign_id,
            house_number=house_number, tradition=tradition,
            source_verse_id=verse_id, description=description,
            version_comment=version_comment,
        )

    async def get_karakatva(
        self, karakatva_id: uuid.UUID,
    ) -> Karakatva | None:
        return await self._repo.get_karakatva(karakatva_id)

    async def get_latest_karakatva(
        self, original_id: uuid.UUID,
    ) -> Karakatva | None:
        return await self._repo.get_latest_karakatva(original_id)

    async def list_karakatvas(
        self, graha: str | None = None,
        subject: str | None = None,
    ) -> tuple[Karakatva, ...]:
        return await self._repo.list_karakatvas(graha=graha, subject=subject)

    async def update_karakatva(
        self, karakatva_id: uuid.UUID,
        version_comment: str | None = None,
        **fields: Any,
    ) -> Karakatva | None:
        return await self._repo.update_karakatva(
            karakatva_id, version_comment=version_comment, **fields,
        )

    async def delete_karakatva(self, karakatva_id: uuid.UUID) -> bool:
        return await self._repo.delete_karakatva(karakatva_id)

    # ── Citation validation ───────────────────────────────────────────────

    async def validate_citation(self, ref: KnowledgeReference) -> bool:
        """Check if a KnowledgeReference points to a real book/verse in the DB."""
        return await self._repo.reference_exists(ref)

    # ── Citation Engine (Phase D) ─────────────────────────────────────────

    async def get_citations_for_yogas(
        self, yoga_results: list,
    ) -> tuple[KnowledgeSearchResult, ...]:
        """
        Structured citation lookup by yoga name and ID. Searches knowledge
        base for classical references matching detected yoga names.
        Uses the existing search infrastructure with yoga name as primary key.
        """
        seen: set[tuple[str, uuid.UUID]] = set()
        citations: list[KnowledgeSearchResult] = []

        for yoga in yoga_results:
            if not getattr(yoga, "is_present", False):
                continue
            name = getattr(yoga, "name", "") or getattr(yoga, "yoga_id", "")
            if not name:
                continue

            results = await self._repo.search(
                KnowledgeSearchQuery(text=name, limit=3)
            )
            for r in results:
                key = (r.entity_type, r.entity_id)
                if key not in seen:
                    seen.add(key)
                    citations.append(r)

        return tuple(citations)

    async def get_citations_for_facts(
        self, derived_facts: dict[str, Any],
    ) -> tuple[KnowledgeSearchResult, ...]:
        """
        Lookup by derived fact domains. Extracts domain prefixes from
        fact keys (e.g. 'shadbala' from 'shadbala.saturn.total'), searches
        knowledge base for relevant entries.
        """
        seen: set[tuple[str, uuid.UUID]] = set()
        citations: list[KnowledgeSearchResult] = []

        # Extract planet names and domain prefixes from fact keys.
        terms: set[str] = set()
        for key in derived_facts:
            parts = key.split(".")
            if len(parts) >= 2:
                terms.add(parts[1])  # planet name or sub-domain
            if len(parts) >= 1:
                terms.add(parts[0])  # domain prefix

        for term in terms:
            if len(term) < 2:
                continue
            results = await self._repo.search(
                KnowledgeSearchQuery(text=term, limit=2)
            )
            for r in results:
                key = (r.entity_type, r.entity_id)
                if key not in seen:
                    seen.add(key)
                    citations.append(r)

        return tuple(citations)

    # ── Search ────────────────────────────────────────────────────────────

    async def search(
        self, query: KnowledgeSearchQuery,
    ) -> tuple[KnowledgeSearchResult, ...]:
        return await self._repo.search(query)

    # ── Conflict Loading (Phase D) ────────────────────────────────────────

    def load_conflicts(self) -> list:
        """Load all doctrinal conflicts from YAML files in knowledge/conflicts/."""
        from apps.api.domain.conflict import (
            KnowledgeConflict, ConflictPosition, ConflictEvidence, ConflictResolution,
        )
        import yaml

        conflicts_dir = Path(__file__).parent.parent.parent.parent / "knowledge" / "conflicts"
        index_path = conflicts_dir / "_index.yaml"

        if not index_path.is_file():
            return []

        with open(index_path, encoding="utf-8") as f:
            index = yaml.safe_load(f) or {}

        conflicts: list = []
        for entry in index.get("entries", index.get("conflicts", [])):
            file_name = entry.get("file", "")
            conflict_path = conflicts_dir / file_name
            if not conflict_path.is_file():
                continue
            with open(conflict_path, encoding="utf-8") as cf:
                data = yaml.safe_load(cf) or {}
            conflict = self._parse_conflict_yaml(data)
            if conflict is not None:
                conflicts.append(conflict)
        return conflicts

    def load_conflict(self, conflict_id: str):
        """Load a single doctrinal conflict by ID."""
        from apps.api.domain.conflict import (
            KnowledgeConflict, ConflictPosition, ConflictEvidence, ConflictResolution,
        )
        import yaml

        conflicts_dir = Path(__file__).parent.parent.parent.parent / "knowledge" / "conflicts"
        index_path = conflicts_dir / "_index.yaml"

        if not index_path.is_file():
            return None

        with open(index_path, encoding="utf-8") as f:
            index = yaml.safe_load(f) or {}

        for entry in index.get("entries", index.get("conflicts", [])):
            if entry.get("id") == conflict_id:
                file_name = entry.get("file", "")
                conflict_path = conflicts_dir / file_name
                if not conflict_path.is_file():
                    return None
                with open(conflict_path, encoding="utf-8") as cf:
                    data = yaml.safe_load(cf) or {}
                return self._parse_conflict_yaml(data)
        return None

    def _parse_conflict_yaml(self, data: dict):
        """Convert a parsed YAML conflict dict into a KnowledgeConflict domain object."""
        from apps.api.domain.conflict import (
            KnowledgeConflict, ConflictPosition, ConflictEvidence, ConflictResolution,
        )

        positions: list = []
        for pos in data.get("positions", []):
            positions.append(ConflictPosition(
                tradition=pos.get("tradition", ""),
                source_ref=str(pos.get("source", {})),
                position=pos.get("position", ""),
                arguments=tuple(pos.get("arguments", [])),
                adherents=tuple(pos.get("adherents", [])),
            ))

        ev = data.get("evidence", {})
        evidence = ConflictEvidence(
            analysis=data.get("analysis", ev.get("analysis", "")),
            for_parashari=tuple(ev.get("for_parashari", [])),
            for_kp=tuple(ev.get("for_kp", [])),
            for_jaimini=tuple(ev.get("for_jaimini", [])),
        )

        resolution = ConflictResolution(
            status=data.get("resolution_status", "unresolved"),
            resolution=data.get("resolution", ""),
            recommended_position=data.get("recommended_position", ""),
            weight_of_evidence=data.get("weight_of_evidence", ""),
        )

        return KnowledgeConflict(
            id=data.get("id", ""),
            name=data.get("name", ""),
            topic=data.get("topic", ""),
            domain=data.get("domain", ""),
            status=data.get("status", "active"),
            confidence=data.get("confidence", "high"),
            last_verified=data.get("last_verified", ""),
            positions=tuple(positions),
            evidence=evidence,
            resolution=resolution,
            related_conflicts=tuple(data.get("related_conflicts", [])),
        )

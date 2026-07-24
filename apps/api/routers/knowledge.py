"""
AstroOS — Knowledge Router (Module 19, Phase B — Versioned)

HTTP adapter layer over KnowledgeEngine. No business logic lives here —
only request parsing, DTO<->schema conversion, and HTTP error mapping.

All endpoints plus versioning support: update creates new version rows,
responses carry version/version_comment/superseded_by.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session, get_knowledge_engine, require_researcher
from apps.api.domain.knowledge import KnowledgeSearchQuery
from apps.api.repositories.knowledge_repository import KnowledgeRepository
from apps.api.schemas.conflict import (
    ConflictDetailResponse,
    ConflictListResponse,
    ConflictSummaryResponse,
)
from apps.api.schemas.nakshatra import (
    NakshatraDeityResponse,
    NakshatraDetailResponse,
    NakshatraListResponse,
    NakshatraNatureResponse,
    NakshatraPadaResponse,
    NakshatraShaktiResponse,
    NakshatraSourceResponse,
    NakshatraSummaryResponse,
)
from apps.api.schemas.knowledge import (
    BookCreateRequest,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    KarakatvaCreateRequest,
    KarakatvaListResponse,
    KarakatvaResponse,
    KarakatvaUpdateRequest,
    KnowledgeReferenceResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResultResponse,
    RuleCreateRequest,
    RuleListResponse,
    RuleResponse,
    RuleUpdateRequest,
    VerseCreateRequest,
    VerseListResponse,
    VerseResponse,
    VerseUpdateRequest,
)
from apps.api.services.knowledge_engine import KnowledgeEngine

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


def _book_response(book) -> BookResponse:
    return BookResponse(**book.__dict__)


def _verse_response(verse) -> VerseResponse:
    return VerseResponse(**verse.__dict__)


def _reference_response(ref) -> KnowledgeReferenceResponse | None:
    if ref is None:
        return None
    return KnowledgeReferenceResponse(
        book_id=ref.book_id, chapter=ref.chapter, verse_number=ref.verse_number,
        edition=ref.edition, translator=ref.translator,
    )


def _rule_response(rule) -> RuleResponse:
    return RuleResponse(
        id=rule.id, title=rule.title, interpretation=rule.interpretation,
        source=_reference_response(rule.source),
        tradition=rule.tradition, confidence=rule.confidence,
        version=rule.version, version_comment=rule.version_comment,
        superseded_by=rule.superseded_by,
    )


def _karakatva_response(k) -> KarakatvaResponse:
    return KarakatvaResponse(
        id=k.id, subject=k.subject, graha=k.graha, sign_id=k.sign_id,
        house_number=k.house_number, tradition=k.tradition,
        source=_reference_response(k.source), description=k.description,
        version=k.version, version_comment=k.version_comment,
        superseded_by=k.superseded_by,
    )


# ── Books ─────────────────────────────────────────────────────────────────────


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    body: BookCreateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> BookResponse:
    book = await engine.create_book(**body.model_dump())
    return _book_response(book)


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: uuid.UUID, engine: KnowledgeEngine = Depends(get_knowledge_engine)
) -> BookResponse:
    book = await engine.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return _book_response(book)


@router.get("/books", response_model=BookListResponse)
async def list_books(
    tradition: str | None = None,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> BookListResponse:
    books = await engine.list_books(tradition=tradition)
    return BookListResponse(books=[_book_response(b) for b in books], total=len(books))


@router.patch("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: uuid.UUID,
    body: BookUpdateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> BookResponse:
    provided = body.model_dump(exclude_unset=True)
    version_comment = provided.pop("version_comment", None)
    book = await engine.update_book(book_id, version_comment=version_comment, **provided)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return _book_response(book)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: uuid.UUID,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> None:
    deleted = await engine.delete_book(book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")


# ── Verses ────────────────────────────────────────────────────────────────────


@router.post("/verses", response_model=VerseResponse, status_code=status.HTTP_201_CREATED)
async def create_verse(
    body: VerseCreateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> VerseResponse:
    verse = await engine.create_verse(**body.model_dump())
    return _verse_response(verse)


@router.get("/verses/{verse_id}", response_model=VerseResponse)
async def get_verse(
    verse_id: uuid.UUID, engine: KnowledgeEngine = Depends(get_knowledge_engine)
) -> VerseResponse:
    verse = await engine.get_verse(verse_id)
    if verse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verse not found.")
    return _verse_response(verse)


@router.get("/books/{book_id}/verses", response_model=VerseListResponse)
async def list_verses(
    book_id: uuid.UUID, engine: KnowledgeEngine = Depends(get_knowledge_engine)
) -> VerseListResponse:
    verses = await engine.list_verses(book_id)
    return VerseListResponse(verses=[_verse_response(v) for v in verses], total=len(verses))


@router.patch("/verses/{verse_id}", response_model=VerseResponse)
async def update_verse(
    verse_id: uuid.UUID,
    body: VerseUpdateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> VerseResponse:
    provided = body.model_dump(exclude_unset=True)
    version_comment = provided.pop("version_comment", None)
    verse = await engine.update_verse(verse_id, version_comment=version_comment, **provided)
    if verse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verse not found.")
    return _verse_response(verse)


@router.delete("/verses/{verse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verse(
    verse_id: uuid.UUID,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> None:
    deleted = await engine.delete_verse(verse_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verse not found.")


# ── Rules ─────────────────────────────────────────────────────────────────────


@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: RuleCreateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> RuleResponse:
    rule = await engine.create_rule(**body.model_dump())
    return _rule_response(rule)


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: uuid.UUID, engine: KnowledgeEngine = Depends(get_knowledge_engine)
) -> RuleResponse:
    rule = await engine.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found.")
    return _rule_response(rule)


@router.get("/rules", response_model=RuleListResponse)
async def list_rules(
    tradition: str | None = None,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> RuleListResponse:
    rules = await engine.list_rules(tradition=tradition)
    return RuleListResponse(rules=[_rule_response(r) for r in rules], total=len(rules))


@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    body: RuleUpdateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> RuleResponse:
    provided = body.model_dump(exclude_unset=True)
    version_comment = provided.pop("version_comment", None)
    rule = await engine.update_rule(rule_id, version_comment=version_comment, **provided)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found.")
    return _rule_response(rule)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: uuid.UUID,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> None:
    deleted = await engine.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found.")


# ── Karakatvas ────────────────────────────────────────────────────────────────


@router.post("/karakatvas", response_model=KarakatvaResponse, status_code=status.HTTP_201_CREATED)
async def create_karakatva(
    body: KarakatvaCreateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> KarakatvaResponse:
    k = await engine.create_karakatva(**body.model_dump())
    return _karakatva_response(k)


@router.get("/karakatvas/{karakatva_id}", response_model=KarakatvaResponse)
async def get_karakatva(
    karakatva_id: uuid.UUID, engine: KnowledgeEngine = Depends(get_knowledge_engine)
) -> KarakatvaResponse:
    k = await engine.get_karakatva(karakatva_id)
    if k is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Karakatva not found.")
    return _karakatva_response(k)


@router.get("/karakatvas", response_model=KarakatvaListResponse)
async def list_karakatvas(
    graha: str | None = None,
    subject: str | None = None,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> KarakatvaListResponse:
    karakatvas = await engine.list_karakatvas(graha=graha, subject=subject)
    return KarakatvaListResponse(
        karakatvas=[_karakatva_response(k) for k in karakatvas],
        total=len(karakatvas),
    )


@router.patch("/karakatvas/{karakatva_id}", response_model=KarakatvaResponse)
async def update_karakatva(
    karakatva_id: uuid.UUID,
    body: KarakatvaUpdateRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> KarakatvaResponse:
    provided = body.model_dump(exclude_unset=True)
    version_comment = provided.pop("version_comment", None)
    k = await engine.update_karakatva(karakatva_id, version_comment=version_comment, **provided)
    if k is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Karakatva not found.")
    return _karakatva_response(k)


@router.delete("/karakatvas/{karakatva_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_karakatva(
    karakatva_id: uuid.UUID,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
    _user=Depends(require_researcher),
) -> None:
    deleted = await engine.delete_karakatva(karakatva_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Karakatva not found.")


# ── Search ────────────────────────────────────────────────────────────────────


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    body: KnowledgeSearchRequest,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> KnowledgeSearchResponse:
    query = KnowledgeSearchQuery(**body.model_dump())
    results = await engine.search(query)
    return KnowledgeSearchResponse(
        results=[KnowledgeSearchResultResponse(**r.__dict__) for r in results],
        total=len(results),
    )


# ── Conflicts (Phase D) ────────────────────────────────────────────────────────

def _conflict_summary(c) -> ConflictSummaryResponse:
    res = c.resolution if hasattr(c, "resolution") and c.resolution else None
    return ConflictSummaryResponse(
        id=c.id, name=c.name, domain=c.domain,
        status=c.status,
        resolution_status=res.status if res else "unresolved",
    )


def _conflict_detail(c) -> ConflictDetailResponse:
    from apps.api.schemas.conflict import (
        ConflictPositionResponse, ConflictEvidenceResponse, ConflictResolutionResponse,
    )
    positions = [
        ConflictPositionResponse(
            tradition=p.tradition, source_ref=p.source_ref,
            position=p.position, arguments=list(p.arguments),
            adherents=list(p.adherents),
        ) for p in c.positions
    ]
    ev = c.evidence
    evidence = ConflictEvidenceResponse(
        analysis=ev.analysis if ev else "",
        for_parashari=list(ev.for_parashari) if ev and ev.for_parashari else [],
        for_kp=list(ev.for_kp) if ev and ev.for_kp else [],
        for_jaimini=list(ev.for_jaimini) if ev and ev.for_jaimini else [],
    ) if ev else None
    res = c.resolution
    resolution = ConflictResolutionResponse(
        status=res.status if res else "unresolved",
        resolution=res.resolution if res else "",
        recommended_position=res.recommended_position if res else "",
        weight_of_evidence=res.weight_of_evidence if res else "",
    ) if res else None
    return ConflictDetailResponse(
        id=c.id, name=c.name, topic=c.topic, domain=c.domain,
        status=c.status, confidence=c.confidence,
        positions=positions, evidence=evidence,
        resolution=resolution,
        related_conflicts=list(c.related_conflicts),
    )


@router.get("/conflicts", response_model=ConflictListResponse)
async def list_conflicts(
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> ConflictListResponse:
    """List all documented doctrinal conflicts."""
    conflicts = engine.load_conflicts()
    return ConflictListResponse(
        conflicts=[_conflict_summary(c) for c in conflicts],
        total=len(conflicts),
    )


@router.get("/conflicts/{conflict_id}", response_model=ConflictDetailResponse)
async def get_conflict(
    conflict_id: str,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> ConflictDetailResponse:
    """Get full conflict detail with positions, evidence, and resolution."""
    from fastapi import HTTPException, status
    conflict = engine.load_conflict(conflict_id)
    if conflict is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found.")
    return _conflict_detail(conflict)


# ── Nakshatra Knowledge Base (context-selector vision, Level 2) ────────────────

def _nakshatra_summary(n) -> NakshatraSummaryResponse:
    return NakshatraSummaryResponse(
        id=n.id, name=n.name, sequential=n.sequential,
        ruler=n.ruler, classical_name=n.classical_name,
    )


def _nakshatra_detail(n) -> NakshatraDetailResponse:
    deity = NakshatraDeityResponse(
        name=n.deity.name, description=n.deity.description,
        attributes=list(n.deity.attributes),
    ) if n.deity else None
    shakti = NakshatraShaktiResponse(
        name=n.shakti.name, meaning=n.shakti.meaning, power=n.shakti.power,
    ) if n.shakti else None
    nature = NakshatraNatureResponse(
        temperament=n.nature.temperament, guna=n.nature.guna,
        gana=n.nature.gana, yoni=n.nature.yoni, nadi=n.nature.nadi,
    ) if n.nature else None
    padas = [
        NakshatraPadaResponse(
            pada=p.pada, degrees=p.degrees, rashi=p.rashi,
            navamsha_rashi=p.navamsha_rashi,
        ) for p in n.padas
    ]
    sources = [
        NakshatraSourceResponse(ref=s.ref, claim=s.claim, confidence=s.confidence)
        for s in n.sources
    ]
    return NakshatraDetailResponse(
        id=n.id, name=n.name, sequential=n.sequential,
        aliases=list(n.aliases), classical_name=n.classical_name,
        devanagari=n.devanagari, meaning=n.meaning, ruler=n.ruler,
        starting_degree=n.starting_degree, ending_degree=n.ending_degree,
        rashi_span=list(n.rashi_span), padas=padas,
        deity=deity, shakti=shakti, nature=nature,
        karakatvas=list(n.karakatvas),
        compatible_nakshatras=list(n.compatible_nakshatras),
        incompatible_nakshatras=list(n.incompatible_nakshatras),
        sources=sources, notes=n.notes,
    )


@router.get("/nakshatras", response_model=NakshatraListResponse)
async def list_nakshatras(
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> NakshatraListResponse:
    """List all 27 nakshatras (summary only) in classical sequential order."""
    nakshatras = engine.load_nakshatras()
    return NakshatraListResponse(
        nakshatras=[_nakshatra_summary(n) for n in nakshatras],
        total=len(nakshatras),
    )


@router.get("/nakshatras/{nakshatra_id}", response_model=NakshatraDetailResponse)
async def get_nakshatra(
    nakshatra_id: str,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> NakshatraDetailResponse:
    """Full classical reference entry for one nakshatra (deity, shakti,
    nature, per-pada Navamsha mapping, karakatvas, sources). Accepts an id
    ('nakshatra.ashvini'), file slug ('ashvini'), or display name ('Ashvini')."""
    nakshatra = engine.load_nakshatra(nakshatra_id)
    if nakshatra is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nakshatra not found.")
    return _nakshatra_detail(nakshatra)

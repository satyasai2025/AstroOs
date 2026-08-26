"""
AstroOS — VedicAstrology.Wikidot Governed Ingestion Seed Script

Loads the curated YAML fixtures at knowledge/sources/vedicastrology_wikidot/
into the EXISTING governed knowledge-reliability and knowledge-ingestion
tables via:
  - apps/api/repositories/knowledge_reliability_repository.py
      (KnowledgeReliabilityRepository.save_source_reliability)
  - apps/api/repositories/knowledge_ingestion_repository.py
      (KnowledgeIngestionRepository.upsert_document / upsert_chunk)

This does NOT create a new Source Registry, Rule Engine, Technique Engine,
Knowledge Graph, RAG system, Citation Engine, or Benchmark Engine — it is
pure integration glue reusing infrastructure from
database/versions/0027_knowledge_ingestion_and_reliability.py and
0028_knowledge_validation_and_promotion.py.

Every item ingested here is deliberately left at:
  - SourceReliabilityTier.INFORMAL_TRADITION
  - ReviewStatus.UNREVIEWED
  - RuleLifecycleState.DOCUMENTED
  - EvidenceLevel.UNVALIDATED
No item is ever marked CANONICAL, SUPPORTED, or auto-promoted by this script.

Idempotent: source_id is deterministic (uuid5 of the source name), document_id
is deterministic (uuid5 of the page slug), and chunk_id is deterministic
(CHK-{doc_prefix}-{section_slug}-{index:04d}) — re-running this script updates
the same rows via the repositories' existing upsert-on-conflict logic rather
than duplicating them.

Usage (same environment / .env as the API server; DATABASE_URL must be set):

    python -m apps.api.scripts.seed_vedicastrology_wikidot

This script is NOT wired into app startup (apps/api/main.py does not import
it) — run manually whenever the YAML fixtures change.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

import yaml

from apps.api.dependencies import _async_session_factory  # noqa: E402
from apps.api.domain.knowledge_ingestion import (  # noqa: E402
    DocumentStatus,
    IngestedChunk,
    IngestedDocument,
)
from apps.api.domain.knowledge_reliability import (  # noqa: E402
    ReviewStatus,
    ScholarlyEvaluation,
    SourceProvenance,
    SourceReliabilityRecord,
    SourceReliabilityTier,
    TechniqueFramework,
)
from apps.api.repositories.knowledge_ingestion_repository import (  # noqa: E402
    KnowledgeIngestionRepository,
)
from apps.api.repositories.knowledge_reliability_repository import (  # noqa: E402
    KnowledgeReliabilityRepository,
)

# apps/api/scripts/seed_vedicastrology_wikidot.py -> ... -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FIXTURE_ROOT = _REPO_ROOT / "knowledge" / "sources" / "vedicastrology_wikidot"

# Deterministic namespace for uuid5-derived IDs so re-runs are idempotent.
_NAMESPACE = uuid.UUID("6f9a5a2e-6e6a-4a3e-9d0a-8b0a2f1c5e11")

_SOURCE_NAME = "VedicAstrology.Wikidot"
_SOURCE_ID = uuid.uuid5(_NAMESPACE, _SOURCE_NAME)

_TECHNIQUE_FRAMEWORK_MAP = {tf.value: tf for tf in TechniqueFramework}


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _build_source_reliability_record() -> SourceReliabilityRecord:
    fixture = _load_yaml(_FIXTURE_ROOT / "_source.yaml")
    reliability = fixture.get("reliability", {})
    provenance_raw = reliability.get("provenance", {})
    scholarly_raw = reliability.get("scholarly_eval", {})

    provenance = SourceProvenance(
        edition_title=provenance_raw.get("edition_title", fixture.get("name", _SOURCE_NAME)),
        publisher=provenance_raw.get("publisher", "Wikidot.com (self-published)"),
        publication_year=provenance_raw.get("publication_year"),
        editor_or_translator=provenance_raw.get("editor_or_translator"),
        manuscript_lineage=provenance_raw.get("manuscript_lineage"),
        is_critical_edition=bool(provenance_raw.get("is_critical_edition", False)),
    )
    scholarly_eval = ScholarlyEvaluation(
        tradition=scholarly_raw.get("tradition", "Mixed Parashari / personal methodology"),
        methodology_clarity_notes=scholarly_raw.get("methodology_clarity_notes", ""),
        primary_commentaries=tuple(scholarly_raw.get("primary_commentaries", []) or []),
        known_disputed_passages=tuple(scholarly_raw.get("known_disputed_passages", []) or []),
    )

    tier = SourceReliabilityTier(reliability.get("tier", "INFORMAL_TRADITION"))
    review_status = ReviewStatus(reliability.get("review_status", "UNREVIEWED"))
    assert tier == SourceReliabilityTier.INFORMAL_TRADITION, (
        "VedicAstrology.Wikidot must remain INFORMAL_TRADITION per governance constraints"
    )
    assert review_status == ReviewStatus.UNREVIEWED, (
        "VedicAstrology.Wikidot must remain UNREVIEWED until a human review occurs"
    )

    return SourceReliabilityRecord(
        source_id=_SOURCE_ID,
        source_name=fixture.get("name", _SOURCE_NAME),
        tier=tier,
        provenance=provenance,
        scholarly_eval=scholarly_eval,
        review_status=review_status,
        empirical_citations=tuple(reliability.get("empirical_citations", []) or []),
        known_failures_or_contradictions=tuple(
            reliability.get("known_failures_or_contradictions", []) or []
        ),
        audit_log=("Registered via seed_vedicastrology_wikidot.py",),
    )


def _page_fixture_files() -> List[Path]:
    """All per-page YAML fixtures except _source.yaml and validation_requirements.yaml."""
    excluded = {"_source.yaml", "validation_requirements.yaml"}
    return sorted(
        p for p in _FIXTURE_ROOT.glob("*.yaml") if p.name not in excluded
    )


def _build_document_and_chunks(fixture_path: Path) -> tuple[IngestedDocument, List[IngestedChunk]]:
    fixture = _load_yaml(fixture_path)
    page_title = fixture.get("page_title", fixture_path.stem)
    page_url = fixture.get("page_url", "")
    doc_slug = _slugify(page_title)
    document_id = uuid.uuid5(_NAMESPACE, f"document:{doc_slug}")

    document = IngestedDocument(
        document_id=document_id,
        source_id=_SOURCE_ID,
        title=f"VedicAstrology.Wikidot — {page_title}",
        author="Vinay Jha (site owner/maintainer)",
        edition=None,
        publication_year=None,
        language="English/Hindi",
        tradition="Parashari",
        content_hash_sha256=_sha256(f"{page_title}|{page_url}"),
        status=DocumentStatus.CHUNKED,
        metadata={
            "page_url": page_url,
            "technique_mapping": fixture.get("technique_mapping", {}),
            "is_canonical": False,
            "note": "INFORMAL_TRADITION source — not canonical.",
        },
    )

    doc_prefix = _slugify(page_title)[:20].upper().replace("-", "")
    chunks: List[IngestedChunk] = []
    for index, item in enumerate(fixture.get("items", []) or []):
        section = item.get("section", "general")
        section_slug = _slugify(section)[:40]
        chunk_id = f"CHK-{doc_prefix}-{section_slug}-{index:04d}"

        content_parts = [item.get("title", ""), item.get("claim", "")]
        if item.get("condition_summary"):
            content_parts.append(f"IF: {item['condition_summary']}")
        if item.get("conclusion_summary"):
            content_parts.append(f"THEN: {item['conclusion_summary']}")
        content = "\n\n".join(p for p in content_parts if p).strip()

        technique_framework = _TECHNIQUE_FRAMEWORK_MAP.get(
            item.get("technique_framework", "Parashari"),
            TechniqueFramework.PARASHARI,
        )

        extraction_metadata = {
            "item_type": item.get("item_type"),
            "verification_status": item.get("verification_status", "UNVERIFIED"),
            "referenced_classical_source": item.get("referenced_classical_source"),
            "requires_validation": item.get("requires_validation", False),
            "source_url": item.get("source_url", page_url),
        }

        chunks.append(
            IngestedChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                source_id=_SOURCE_ID,
                chapter_section=section,
                page_location=page_url,
                passage_reference=item.get("title", section),
                chunk_index=index,
                content=content,
                content_hash_sha256=_sha256(content),
                technique_framework=technique_framework,
                # RuleLifecycleState / EvidenceLevel default to DOCUMENTED / UNVALIDATED
                # (see IngestedChunk field defaults) — never overridden to CANONICAL/HIGH here.
                is_ai_extracted=True,
                extraction_metadata=extraction_metadata,
            )
        )

    return document, chunks


async def _run() -> dict[str, int]:
    if not _FIXTURE_ROOT.is_dir():
        print(f"ERROR: fixture directory not found at {_FIXTURE_ROOT}", file=sys.stderr)
        sys.exit(1)

    counts = {"sources": 0, "documents": 0, "chunks": 0}

    async with _async_session_factory() as session:
        try:
            reliability_repo = KnowledgeReliabilityRepository(session)
            ingestion_repo = KnowledgeIngestionRepository(session)

            source_record = _build_source_reliability_record()
            await reliability_repo.save_source_reliability(source_record)
            counts["sources"] += 1

            for fixture_path in _page_fixture_files():
                document, chunks = _build_document_and_chunks(fixture_path)
                await ingestion_repo.upsert_document(document)
                counts["documents"] += 1
                for chunk in chunks:
                    chunk.validate_provenance()
                    await ingestion_repo.upsert_chunk(chunk)
                    counts["chunks"] += 1

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return counts


def main() -> None:
    counts = asyncio.run(_run())
    print("VedicAstrology.Wikidot seed complete:")
    print(f"  sources upserted:   {counts['sources']}")
    print(f"  documents upserted: {counts['documents']}")
    print(f"  chunks upserted:    {counts['chunks']}")


if __name__ == "__main__":
    main()

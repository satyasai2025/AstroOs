"""
AstroOS — Seed technique records for the VedicAstrology.Wikidot corpus.

Applies the PROPOSED mapping in
knowledge/sources/vedicastrology_wikidot/technique_mapping.yaml by creating:

  1. One TechniqueModel row per proposed technique_key (the registry was empty)
  2. One TechniqueSourceModel row per ingested page, attaching that page to its
     technique with full provenance

Uses the EXISTING TechniqueRepository (create_version / add_source). No new
registry, no raw SQL, no parallel technique infrastructure.

GOVERNANCE INVARIANTS (do not weaken):
  - provenance = ProvenanceStatus.UNTESTED for every technique created here.
    These come from an INFORMAL_TRADITION / UNREVIEWED source. Marking them
    SOURCE_DERIVED would imply a classical text states them, which is exactly
    the claim this corpus has NOT established.
  - status = "research" — never "validated".
  - Attaching a source to a technique does NOT touch any ingested chunk's
    verification_status or lifecycle_state. Nothing is promoted.
  - source_type = "notes" (a community wiki is not a classical_text or book).

Idempotent: re-running skips any technique_key that already has a current
version, and skips a source reference already attached to that technique.

Usage (DATABASE_URL must be set, same env as the API):

    python -m apps.api.scripts.seed_wikidot_techniques
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from apps.api.dependencies import _async_session_factory
from apps.api.domain.technique import ProvenanceStatus, TechniqueDefinition
from apps.api.models.technique import TechniqueSourceModel
from apps.api.repositories.technique_repository import TechniqueRepository

from sqlalchemy import select

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FIXTURE_ROOT = _REPO_ROOT / "knowledge" / "sources" / "vedicastrology_wikidot"
_MAPPING_FILE = _FIXTURE_ROOT / "technique_mapping.yaml"

_SOURCE_NAME = "VedicAstrology.Wikidot"

# Human-readable names + objective keys for the proposed technique_keys.
# `objective` is the intent key a resolver matches on (see TechniqueDefinition).
_TECHNIQUE_META: Dict[str, Dict[str, str]] = {
    "graha_karakatva":  {"name": "Graha Karakatva",              "objective": "graha_significations"},
    "bhava_analysis":   {"name": "Bhava Analysis",               "objective": "house_significations"},
    "shodasha_varga":   {"name": "Shodasha Varga",               "objective": "divisional_chart_analysis"},
    "shadbala":         {"name": "Shadbala",                     "objective": "planetary_strength"},
    "ashtakavarga":     {"name": "Ashtakavarga",                 "objective": "bindu_strength"},
    "sudarshana_chakra":{"name": "Sudarshana Chakra",            "objective": "tri_lagna_analysis"},
    "yoga_analysis":    {"name": "Yoga Analysis",                "objective": "yoga_detection"},
    "medini_jyotisha":  {"name": "Medini Jyotisha (Mundane)",    "objective": "mundane_prediction"},
}


def _load_mappings() -> List[Dict[str, Any]]:
    with _MAPPING_FILE.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("mappings", []) or []


def _page_url(page_file: str) -> str:
    """Read the page_url straight from the page fixture, so the attached
    reference is the real source URL rather than a reconstructed guess."""
    p = _FIXTURE_ROOT / page_file
    if not p.exists():
        return ""
    with p.open("r", encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("page_url", "") or ""


def _keys_for(mapping: Dict[str, Any]) -> List[str]:
    keys = []
    for field in ("proposed_technique_key", "secondary_technique_key"):
        k = mapping.get(field)
        if k:
            keys.append(k)
    return keys


def _build_definition(key: str, tradition: str, source_refs: List[str]) -> TechniqueDefinition:
    meta = _TECHNIQUE_META.get(key, {"name": key.replace("_", " ").title(), "objective": ""})
    return TechniqueDefinition(
        technique_id=key,
        name=meta["name"],
        version=1,
        description=(
            f"Technique registry entry created to own {_SOURCE_NAME} corpus pages "
            f"mapped to '{key}'. Created from a mapping proposal, not from a "
            f"validated technique specification — it carries no rule bodies."
        ),
        tradition=tradition or "Parashari",
        objective=meta["objective"],
        source_references=tuple(source_refs),
        # UNTESTED, never SOURCE_DERIVED: the source is INFORMAL_TRADITION and
        # its claims are UNVERIFIED. See module docstring.
        provenance=ProvenanceStatus.UNTESTED,
        status="research",
    )


async def _run() -> Dict[str, int]:
    if not _MAPPING_FILE.exists():
        print(f"ERROR: mapping file not found at {_MAPPING_FILE}", file=sys.stderr)
        sys.exit(1)

    mappings = _load_mappings()
    counts = {"techniques_created": 0, "techniques_existing": 0,
              "sources_attached": 0, "sources_existing": 0}

    async with _async_session_factory() as session:
        try:
            repo = TechniqueRepository(session)

            # ── Pass 1: create one technique version per distinct key ────────
            key_to_id: Dict[str, Any] = {}
            for mapping in mappings:
                tradition = mapping.get("framework", "Parashari")
                for key in _keys_for(mapping):
                    if key in key_to_id:
                        continue
                    existing = await repo.get_current_model(key)
                    if existing is not None:
                        key_to_id[key] = existing.id
                        counts["techniques_existing"] += 1
                        print(f"  exists    technique '{key}'")
                        continue
                    refs = [u for u in (_page_url(mapping.get("page_file", "")),) if u]
                    model = await repo.create_version(
                        _build_definition(key, tradition, refs),
                        version_comment=(
                            f"Seeded from {_SOURCE_NAME} technique_mapping.yaml "
                            f"(proposed mapping applied)."
                        ),
                    )
                    key_to_id[key] = model.id
                    counts["techniques_created"] += 1
                    print(f"  created   technique '{key}'")

            # ── Pass 2: attach each page to its technique ────────────────────
            for mapping in mappings:
                page_file = mapping.get("page_file", "")
                url = _page_url(page_file)
                if not url:
                    print(f"  skip      no page_url for {page_file}")
                    continue
                for key in _keys_for(mapping):
                    tid = key_to_id.get(key)
                    if tid is None:
                        continue
                    dup = await session.execute(
                        select(TechniqueSourceModel).where(
                            TechniqueSourceModel.technique_id == tid,
                            TechniqueSourceModel.reference == url,
                        )
                    )
                    if dup.scalar_one_or_none() is not None:
                        counts["sources_existing"] += 1
                        continue
                    note_parts = [
                        f"Source tier: INFORMAL_TRADITION / UNREVIEWED — not canonical.",
                        f"Page fixture: knowledge/sources/vedicastrology_wikidot/{page_file}",
                        f"Rationale: {(mapping.get('rationale') or '').strip()}",
                    ]
                    if mapping.get("caution"):
                        note_parts.append(f"CAUTION: {mapping['caution'].strip()}")
                    await repo.add_source(
                        tid,
                        source_type="notes",   # community wiki, not book/classical_text
                        reference=url,
                        excerpt=None,
                        notes="\n\n".join(note_parts),
                    )
                    counts["sources_attached"] += 1
                    print(f"  attached  {page_file} -> {key}")

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return counts


def main() -> None:
    c = asyncio.run(_run())
    print("\nWikidot technique seed complete:")
    print(f"  techniques created:  {c['techniques_created']}")
    print(f"  techniques existing: {c['techniques_existing']}")
    print(f"  sources attached:    {c['sources_attached']}")
    print(f"  sources existing:    {c['sources_existing']}")


if __name__ == "__main__":
    main()

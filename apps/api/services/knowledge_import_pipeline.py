"""
AstroOS — Knowledge YAML Import Pipeline (Module 20, Phase B)

Reads the static YAML knowledge catalogue files in `knowledge/` and
imports them into the database via KnowledgeEngine. Idempotent: skips
records already imported (matched by canonical title).

Catalogue areas handled:
  - sources/texts/    → KnowledgeBook records
  - catalogues/grahas/    → Karakatva records
  - catalogues/karakatvas/ → Karakatva records
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from apps.api.services.knowledge_engine import KnowledgeEngine

_IMPORTED_TAG = "_imported_via_pipeline"

# Sanskrit YAML graha names -> English ENUM values expected by PostgreSQL.
_GRAHA_NAME_MAP = {
    "surya": "sun", "sun": "sun",
    "chandra": "moon", "moon": "moon",
    "mangala": "mars", "mars": "mars",
    "budha": "mercury", "mercury": "mercury",
    "guru": "jupiter", "brihaspati": "jupiter", "jupiter": "jupiter",
    "shukra": "venus", "venus": "venus",
    "shani": "saturn", "saturn": "saturn",
    "rahu": "rahu",
    "ketu": "ketu",
}


async def load_yaml_catalogue(
    engine: KnowledgeEngine,
    catalogue_root: str = "knowledge",
) -> dict[str, int]:
    """
    Load all YAML catalogue files into the knowledge database.

    Returns a dict with counts: {"books": N, "karakatvas": N, "skipped": N}.

    Idempotent: skips records whose title matches an existing active record.
    """
    root = Path(catalogue_root)
    counts: dict[str, int] = {"books": 0, "karakatvas": 0, "skipped": 0}

    # ── Sources → Books ─────────────────────────────────────────────────
    sources_dir = root / "sources" / "texts"
    if sources_dir.is_dir():
        for yaml_file in sorted(sources_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue
            imported = await _import_source_as_book(engine, yaml_file)
            if imported:
                counts["books"] += 1
            else:
                counts["skipped"] += 1

    # ── Karakatvas ──────────────────────────────────────────────────────
    for subdir in ("grahas", "karakatvas"):
        catalogue_dir = root / "catalogues" / subdir
        if catalogue_dir.is_dir():
            for yaml_file in sorted(catalogue_dir.glob("*.yaml")):
                if yaml_file.name == "_index.yaml":
                    continue
                imported = await _import_karakatva_from_yaml(engine, yaml_file)
                if imported:
                    counts["karakatvas"] += 1
                else:
                    counts["skipped"] += 1

    return counts


async def _import_source_as_book(
    engine: KnowledgeEngine,
    yaml_path: Path,
) -> bool:
    """Import a source YAML file as a KnowledgeBook. Returns True if created."""
    data = _safe_load_yaml(yaml_path)
    if not data or not data.get("name"):
        return False

    title = data["name"]
    # Check for existing book by title.
    existing = await engine.list_books()
    for book in existing:
        if book.title == title:
            return False  # skip — already imported

    period = str((data.get("date") or {}).get("approximate", ""))
    await engine.create_book(
        title=title,
        author=str(data.get("author", "")),
        language=str((data.get("language") or {}).get("original", "")),
        tradition=data.get("tradition"),
        period_ce=period[:50],  # truncate to fit VARCHAR(50)
        version_comment=f"Imported from {yaml_path.name}",
    )
    return True


async def _import_karakatva_from_yaml(
    engine: KnowledgeEngine,
    yaml_path: Path,
) -> bool:
    """Import a karakatva YAML file. Returns True if created."""
    data = _safe_load_yaml(yaml_path)
    if not data or not data.get("name"):
        return False

    subject = data.get("name", "")
    raw_graha = data.get("name", "").lower()
    graha_name = _GRAHA_NAME_MAP.get(raw_graha, data.get("graha"))

    # Check for existing karakatva by subject.
    existing = await engine.list_karakatvas()

    # Extract karakatva entries from the YAML structure.
    karakatvas_raw = data.get("karakatvas") or data.get("significations") or {}
    if isinstance(karakatvas_raw, dict):
        # Dict structure: {category: [strings], ...}
        entries: list[str] = []
        for key in ("classical", "traditional", "modern", "general"):
            items = karakatvas_raw.get(key, [])
            if isinstance(items, list):
                entries.extend(items)
    elif isinstance(karakatvas_raw, list):
        entries = [e if isinstance(e, str) else str(e) for e in karakatvas_raw]
    else:
        entries = []

    if not entries:
        # Create one karakatva from the subject name itself.
        already_exists = any(k.subject.lower() == subject.lower() for k in existing)
        if not already_exists:
            await engine.create_karakatva(
                subject=subject,
                graha=graha_name,
                description=data.get("description", ""),
                tradition=data.get("tradition"),
                version_comment=f"Imported from {yaml_path.name}",
            )
            return True
        return False

    created = False
    for entry_text in entries:
        entry_subject = str(entry_text).strip()
        if not entry_subject or len(entry_subject) > 200:
            continue  # skip entries too long for VARCHAR(200) column
        already_exists = any(k.subject.lower() == entry_subject.lower() for k in existing)
        if already_exists:
            continue

        await engine.create_karakatva(
            subject=entry_subject,
            graha=graha_name,
            tradition=data.get("tradition"),
            version_comment=f"Imported from {yaml_path.name}",
        )
        created = True

    return created


def _safe_load_yaml(path: Path) -> Optional[dict[str, Any]]:
    """Load a YAML file, returning None on parse failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

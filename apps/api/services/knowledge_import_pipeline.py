"""
AstroOS — Knowledge YAML Import Pipeline (Module 20, Phase B)

Reads the static YAML knowledge catalogue files in `knowledge/` and
imports them into the database via KnowledgeEngine. Idempotent: skips
karakatva records already imported, matched by a natural key of
(subject, graha, house_number) — case-insensitive on subject — and skips
book records already imported, matched by title (case-insensitive).

Catalogue areas handled:
  - sources/texts/*.yaml          → KnowledgeBook records
  - catalogues/grahas/*.yaml      → Karakatva records (flat
    classical/traditional/modern list-of-strings format, one file per
    graha, e.g. `mangala.yaml`)
  - catalogues/karakatvas/*.yaml  → Karakatva records (nested
    "significations" / "life_events" list-of-dicts format, one file per
    karaka type, e.g. `graha-karakatvas.yaml`, `house-significations.yaml`)

These two karakatva shapes are genuinely different on disk (confirmed by
reading the actual files, not assumed) — see `_extract_karakatva_entries`
for exactly how each is parsed. This module has no import-time side
effects and is not wired into app startup; it is driven manually by
apps/api/scripts/seed_knowledge.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from apps.api.services.knowledge_engine import KnowledgeEngine

# Sanskrit/alias names -> English enum values accepted by the PostgreSQL
# `graha` enum (sun, moon, mars, mercury, jupiter, venus, saturn, rahu,
# ketu). Keys are matched against the *last dot-segment* of a YAML ref
# (e.g. "graha.surya" -> "surya") or a bare name (e.g. "Mangala" ->
# "mangala"), lowercased.
_GRAHA_ALIASES: dict[str, str] = {
    "surya": "sun", "sun": "sun",
    "chandra": "moon", "moon": "moon",
    "mangala": "mars", "mars": "mars", "kuja": "mars",
    "angaraka": "mars", "bhauma": "mars",
    "budha": "mercury", "mercury": "mercury",
    "guru": "jupiter", "brihaspati": "jupiter", "jupiter": "jupiter",
    "shukra": "venus", "venus": "venus",
    "shani": "saturn", "saturn": "saturn",
    "rahu": "rahu",
    "ketu": "ketu",
}

_MAX_SUBJECT_LEN = 200  # karakatvas.subject is VARCHAR(200)

_DedupKey = tuple[str, Optional[str], Optional[int]]


def _normalize_graha(raw: Optional[str]) -> Optional[str]:
    """Map a YAML graha ref ('graha.surya') or bare name ('Mangala') to the
    English value the `karakatvas.graha` enum column accepts. Returns None
    for anything unrecognized rather than risk an invalid enum write."""
    if not raw or not isinstance(raw, str):
        return None
    key = raw.split(".")[-1].strip().lower()
    return _GRAHA_ALIASES.get(key)


def _house_number_from_ref(raw: Optional[str]) -> Optional[int]:
    """Map a bhava ref ('bhava.10') to an int house number 1-12."""
    if not raw or not isinstance(raw, str):
        return None
    try:
        n = int(raw.split(".")[-1])
    except (ValueError, IndexError):
        return None
    return n if 1 <= n <= 12 else None


def _tradition_from_data(data: dict[str, Any]) -> str:
    """Best-effort tradition label from a file's `source_primary` field
    (e.g. 'source.BPHS' -> 'BPHS'); falls back to 'BPHS' since every
    catalogue file inspected cites BPHS as primary or supplementary."""
    src = data.get("source_primary")
    if isinstance(src, str) and src:
        return src.split(".")[-1] or "BPHS"
    return "BPHS"


def _dedup_key(subject: str, graha: Optional[str], house_number: Optional[int]) -> _DedupKey:
    return (subject.strip().lower(), graha, house_number)


async def load_yaml_catalogue(
    engine: KnowledgeEngine,
    catalogue_root: str | Path = "knowledge",
) -> dict[str, int]:
    """
    Load all YAML catalogue files into the knowledge database.

    Returns a dict with counts: {"books": N, "karakatvas": N, "skipped": N}.

    Idempotent: skips records that already exist (see module docstring for
    the natural keys used), so this is safe to call repeatedly — e.g. after
    the YAML catalogues gain new entries.
    """
    root = Path(catalogue_root)
    counts: dict[str, int] = {"books": 0, "karakatvas": 0, "skipped": 0}

    # ── Sources → Books ─────────────────────────────────────────────────
    sources_dir = root / "sources" / "texts"
    if sources_dir.is_dir():
        existing_titles = {b.title.strip().lower() for b in await engine.list_books()}
        for yaml_file in sorted(sources_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue
            created = await _import_source_as_book(engine, yaml_file, existing_titles)
            counts["books" if created else "skipped"] += 1

    # ── Karakatvas ──────────────────────────────────────────────────────
    existing = await engine.list_karakatvas()
    seen: set[_DedupKey] = {
        _dedup_key(k.subject, k.graha, k.house_number) for k in existing
    }

    for subdir in ("grahas", "karakatvas"):
        catalogue_dir = root / "catalogues" / subdir
        if not catalogue_dir.is_dir():
            continue
        for yaml_file in sorted(catalogue_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue
            data = _safe_load_yaml(yaml_file)
            if not data:
                continue
            for entry in _extract_karakatva_entries(data):
                subject = entry["subject"][:_MAX_SUBJECT_LEN]
                key = _dedup_key(subject, entry.get("graha"), entry.get("house_number"))
                if key in seen:
                    counts["skipped"] += 1
                    continue
                await engine.create_karakatva(
                    subject=subject,
                    graha=entry.get("graha"),
                    house_number=entry.get("house_number"),
                    tradition=entry.get("tradition") or "BPHS",
                    description=entry.get("description"),
                    version_comment=f"Imported from {yaml_file.name}",
                )
                seen.add(key)
                counts["karakatvas"] += 1

    return counts


# ── Karakatva YAML parsing ──────────────────────────────────────────────────


def _extract_karakatva_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Normalize one parsed YAML file into a flat list of
    {subject, graha, house_number, description, tradition} dicts.

    Handles the three shapes actually present under knowledge/catalogues/
    (verified by reading the files, not assumed):

      1. catalogues/karakatvas/{graha,bhava,nakshatra}-karakatvas.yaml —
         top-level "significations": [
           {graha|bhava|nakshatra: <id>, name: <str>,
            karakatvas: [{concept, notes, bhava_link, confidence}, ...],
            ...},
           ...
         ]  with a top-level "karaka_type" of "graha" | "bhava" | "nakshatra"
         telling us which key on each item is the entity ref.

      2. catalogues/karakatvas/house-significations.yaml —
         top-level "life_events": [
           {event: <str>, primary_houses: ["bhava.N", ...],
            karaka: "graha.X", description: <str>, ...},
           ...
         ]

      3. catalogues/grahas/*.yaml — flat top-level "karakatvas": {
           classical: [<str>, ...], traditional: [...], modern: [...]
         }, keyed off a top-level "name" (e.g. "Mangala").
    """
    tradition = _tradition_from_data(data)

    significations = data.get("significations")
    if isinstance(significations, list):
        karaka_type = data.get("karaka_type")
        entries: list[dict[str, Any]] = []
        for item in significations:
            if isinstance(item, dict):
                entries.extend(_entries_from_signification_item(item, karaka_type, tradition))
        return entries

    life_events = data.get("life_events")
    if isinstance(life_events, list):
        entries = []
        for item in life_events:
            if not isinstance(item, dict):
                continue
            entry = _entry_from_life_event(item, tradition)
            if entry is not None:
                entries.append(entry)
        return entries

    flat = data.get("karakatvas")
    if isinstance(flat, dict):
        return _entries_from_flat_graha(data, flat, tradition)

    return []


def _entries_from_signification_item(
    item: dict[str, Any],
    karaka_type: Optional[str],
    tradition: str,
) -> list[dict[str, Any]]:
    """One item of a "significations" list -> its list of concept entries."""
    entries: list[dict[str, Any]] = []
    name = str(item.get("name") or "").strip()
    concepts = item.get("karakatvas")
    if not isinstance(concepts, list):
        return entries

    if karaka_type == "graha":
        graha = _normalize_graha(item.get("graha"))
        for c in concepts:
            if not isinstance(c, dict):
                continue
            concept = str(c.get("concept") or "").strip()
            if not concept:
                continue
            entries.append({
                "subject": concept,
                "graha": graha,
                "house_number": _house_number_from_ref(c.get("bhava_link")),
                "description": c.get("notes"),
                "tradition": tradition,
            })

    elif karaka_type == "bhava":
        house_number = _house_number_from_ref(item.get("bhava"))
        graha = _normalize_graha(item.get("karaka"))
        for c in concepts:
            if not isinstance(c, dict):
                continue
            concept = str(c.get("concept") or "").strip()
            if not concept:
                continue
            entries.append({
                "subject": concept,
                "graha": graha,
                "house_number": house_number,
                "description": c.get("notes"),
                "tradition": tradition,
            })

    elif karaka_type == "nakshatra":
        # Karakatva has no nakshatra_id column, so the nakshatra name is
        # folded into the subject/description for searchability instead
        # of being silently dropped.
        deity = item.get("deity")
        for c in concepts:
            if not isinstance(c, dict):
                continue
            concept = str(c.get("concept") or "").strip()
            if not concept:
                continue
            subject = f"{name}: {concept}" if name else concept
            notes = c.get("notes")
            if notes and deity:
                description = f"{notes} (Nakshatra: {name}, deity: {deity})"
            elif notes:
                description = notes
            elif deity:
                description = f"Nakshatra: {name}, deity: {deity}"
            else:
                description = None
            entries.append({
                "subject": subject,
                "graha": None,
                "house_number": None,
                "description": description,
                "tradition": tradition,
            })

    else:
        # Unrecognized karaka_type — still surface the content rather than
        # dropping it, just without graha/house linkage.
        for c in concepts:
            if not isinstance(c, dict):
                continue
            concept = str(c.get("concept") or "").strip()
            if not concept:
                continue
            subject = f"{name}: {concept}" if name else concept
            entries.append({
                "subject": subject,
                "graha": None,
                "house_number": None,
                "description": c.get("notes"),
                "tradition": tradition,
            })

    return entries


def _entry_from_life_event(item: dict[str, Any], tradition: str) -> Optional[dict[str, Any]]:
    """One item of a "life_events" list -> a single Karakatva entry."""
    event = str(item.get("event") or "").strip()
    if not event:
        return None
    subject = event.replace("-", " ").replace("_", " ").strip().title()

    primary_houses = item.get("primary_houses")
    house_number = None
    if isinstance(primary_houses, list) and primary_houses:
        house_number = _house_number_from_ref(primary_houses[0])

    graha = _normalize_graha(item.get("karaka"))
    description = item.get("description") or item.get("bhava_notes")

    return {
        "subject": subject,
        "graha": graha,
        "house_number": house_number,
        "description": description,
        "tradition": tradition,
    }


def _entries_from_flat_graha(
    data: dict[str, Any],
    flat: dict[str, Any],
    tradition: str,
) -> list[dict[str, Any]]:
    """The older catalogues/grahas/*.yaml flat dict-of-lists format:
    top-level "karakatvas": {classical: [str, ...], traditional: [...],
    modern: [...]}, keyed off a top-level "name" (e.g. "Mangala")."""
    graha = _normalize_graha(data.get("name"))
    display_name = str(data.get("name") or "").strip()
    entries: list[dict[str, Any]] = []
    for category in ("classical", "traditional", "modern", "general"):
        items = flat.get(category)
        if not isinstance(items, list):
            continue
        for concept in items:
            if not isinstance(concept, str) or not concept.strip():
                continue
            entries.append({
                "subject": concept.strip(),
                "graha": graha,
                "house_number": None,
                "description": (
                    f"{category.capitalize()} signification of {display_name}."
                    if display_name else None
                ),
                "tradition": tradition,
            })
    return entries


# ── Books ────────────────────────────────────────────────────────────────────


async def _import_source_as_book(
    engine: KnowledgeEngine,
    yaml_path: Path,
    existing_titles: set[str],
) -> bool:
    """Import a source YAML file as a KnowledgeBook. Returns True if created."""
    data = _safe_load_yaml(yaml_path)
    if not data or not data.get("name"):
        return False

    title = str(data["name"])
    if title.strip().lower() in existing_titles:
        return False  # already imported

    period = str((data.get("date") or {}).get("approximate", ""))
    await engine.create_book(
        title=title,
        author=str(data.get("author", "")) or None,
        language=str((data.get("language") or {}).get("original", "")) or None,
        tradition=data.get("tradition"),
        period_ce=(period[:50] or None),  # truncate to fit VARCHAR(50)
        version_comment=f"Imported from {yaml_path.name}",
    )
    existing_titles.add(title.strip().lower())
    return True


def _safe_load_yaml(path: Path) -> Optional[dict[str, Any]]:
    """Load a YAML file, returning None on parse failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

"""
AstroOS — Classical References Lookup (Module 27, Phase 3c)

A small, curated, hand-authored mapping from dimension/value keywords to
classical Vedic astrology citations — same shape and honesty level as
apps.api.services.hypothesis_generator.py's HypothesisTemplate.classical_references
tuples. This is NOT an exhaustive citations database; it covers the common
dimension categories the pattern discovery engine actually produces
(dasha, yoga, house, transit, shadbala, varga, nakshatra) and returns an
empty list when nothing matches rather than guessing.
"""

from __future__ import annotations

from apps.api.domain.research_case import DiscoveredPattern

# Keys are lowercase substrings matched against a pattern dimension's
# `dimension` name or `value`. Order matters only for iteration below, not
# for correctness (matches are deduped by reference string, not by key).
_REFERENCES: dict[str, tuple[str, ...]] = {
    # ── Dasha ────────────────────────────────────────────────────────────
    "dasha_mahadasha": ("BPHS Ch. 46 — Vimshottari Dasha",),
    "dasha_antardasha": ("BPHS Ch. 46 — Vimshottari Dasha (Antardasha)",),
    "dasha_pratyantar": ("BPHS Ch. 46 — Vimshottari Dasha (Pratyantardasha)",),

    # ── Yoga (matched against the dimension value, e.g. "Gajakesari") ──────
    "gajakesari": ("BPHS Ch. 36 — Gajakesari Yoga",),
    "raja yoga": ("BPHS Ch. 41 — Raja Yoga", "Jaimini Sutra 4.1"),
    "dhana yoga": ("Saravali Ch. 11 — Dhana Yoga",),
    "neecha bhanga": ("BPHS Ch. 6 — Neecha Bhanga Raja Yoga",),
    "chandra mangal": ("Saravali Ch. 12 — Chandra-Mangala Yoga",),

    # ── Houses ───────────────────────────────────────────────────────────
    "house_1": ("BPHS Ch. 17 — 1st House (Self)",),
    "house_2": ("BPHS Ch. 17 — 2nd House (Wealth, Family)",),
    "house_4": ("BPHS Ch. 17 — 4th House (Home, Mother)",),
    "house_7": ("BPHS Ch. 17 — 7th House (Marriage, Partnerships)",),
    "house_10": ("BPHS Ch. 17 — 10th House (Career, Status)",),

    # ── Transits / Shadbala / Varga / Nakshatra ─────────────────────────────
    "transit": ("BPHS Ch. 46 — Gochara (Transits)",),
    "shadbala": ("BPHS Ch. 27 — Shadbala",),
    "varga": ("BPHS Ch. 7 — Shodasavarga (Divisional Charts)",),
    "nakshatra": ("BPHS Ch. 4 — Nakshatra",),
}


def get_references_for_pattern(pattern: DiscoveredPattern) -> list[str]:
    """Curated citations matching this pattern's dimensions, deduplicated.

    Substring match against each dimension's ``dimension`` name and
    ``value``, case-insensitive. Returns an empty list if nothing matches —
    no reference is invented for a pattern this table doesn't cover.
    """
    matched: list[str] = []
    for dim in pattern.dimensions:
        haystack = f"{dim.dimension} {dim.value}".lower()
        for keyword, references in _REFERENCES.items():
            if keyword in haystack:
                for ref in references:
                    if ref not in matched:
                        matched.append(ref)
    return matched

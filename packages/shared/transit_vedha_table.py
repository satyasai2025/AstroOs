"""
AstroOS — Transit Vedha (Obstruction) Table (Module 11 Phase 2)

Classical Gochara Vedha: even when a transiting planet occupies a
favorable house from natal Moon, its good effect is obstructed if
another planet is simultaneously transiting the paired "Vedha house."
Vipreet Vedha is the reverse: a planet in an unfavorable house has its
bad effect neutralized if another planet occupies the paired house.

**Sourcing.** Transcribed from a document the user provided directly
(attributed to Dr. P.S. Sastri, via saptarishisastrology.com,
"Transit Influences" — https://saptarishisastrology.com/transit-influences-by-dr-p-s-sastri/),
a single complete, internally consistent listing covering all 7
classical grahas plus Rahu/Ketu. This is stronger footing than a
reconstruction from scattered fragments: independently corroborated
before this document was provided — two unrelated web sources matched
this same document's Sun table (3<->9, 6<->12, 4<->10, 5<->11, with the
Sun-Saturn mutual exception) and Mars table (3<->12, 6<->9, 5<->11)
exactly, which is what prompted asking the user for a better source in
the first place.

**Structure is directional, not symmetric pairs.** Most planets show a
clean symmetric structure (VEDHA[good_house] and VIPREET_VEDHA[bad_house]
reference the same house-pair from both directions), but two do not:
Mercury (house 8 is simultaneously one of its own good houses, with its
own Vedha source house 1, AND the Vedha source for good house 10) and
Venus (9 good houses but only 3 bad houses, so most good-house Vedha
entries have no Vipreet Vedha counterpart at all). Modeled as two
independent directional mappings per planet (VEDHA, VIPREET_VEDHA)
rather than assuming symmetric pairs throughout, to stay faithful to
the source rather than impose a simplifying assumption that happens to
be wrong for two of the nine grahas. Verified programmatically: 7 of 9
planets are symmetric, Mercury and Venus are not — matching the source
exactly in both cases, not a transcription error.

**Exceptions** — specific planets that never cause Vedha/Vipreet Vedha
to a given planet, per the source:
  - Sun and Saturn never obstruct each other (stated from both sides)
  - Moon and Mercury never obstruct each other (stated from both sides)
No exception is stated for Mars, Jupiter, Venus, Rahu, or Ketu — any
other planet occupying the paired house causes the obstruction/relief.

Not every house is covered for every planet — where the source gives no
rule for a given house, no Vedha/Vipreet Vedha applies there at all
(e.g. Sun has no stated rule for houses 1, 2, 7, or 8).
"""

from __future__ import annotations

VEDHA: dict[str, dict[int, int]] = {
    "sun": {3: 9, 6: 12, 10: 4, 11: 5},
    "moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "mars": {3: 12, 6: 9, 11: 5},
    "mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    "saturn": {3: 12, 6: 9, 11: 5},
    "rahu": {3: 12, 6: 9, 11: 5},
    "ketu": {3: 12, 6: 9, 11: 5},
}

VIPREET_VEDHA: dict[str, dict[int, int]] = {
    "sun": {4: 10, 5: 11, 9: 3, 12: 6},
    "moon": {2: 7, 4: 10, 5: 1, 8: 11, 9: 3, 12: 6},
    "mars": {5: 11, 9: 6, 12: 3},
    "mercury": {1: 8, 3: 4, 5: 2, 9: 6, 12: 11},
    "jupiter": {3: 7, 4: 5, 8: 11, 10: 9, 12: 2},
    "venus": {6: 12, 7: 2, 10: 4},
    "saturn": {5: 11, 9: 6, 12: 3},
    "rahu": {5: 11, 9: 6, 12: 3},
    "ketu": {5: 11, 9: 6, 12: 3},
}

NO_VEDHA_EXCEPTION: dict[str, str] = {
    "sun": "saturn",
    "saturn": "sun",
    "moon": "mercury",
    "mercury": "moon",
}

"""
AstroOS — Ashtakavarga Bindu Contribution Table

The classical Parashari bindu ("point") rules: for each of the 7 target
grahas, which houses — counted from each of the 8 contributors (7
grahas + Lagna) — receive a bindu.

**Sourcing and verification, stated plainly:**

This codebase does not have direct access to a primary source (a
Sanskrit critical edition or scholarly BPHS translation). The table
below was reconstructed from `kunjara/jyotish` (github.com/kunjara/
jyotish), a GPL-2 licensed, actively-used open-source Vedic astrology
library (204+ stars, 446+ commits, used as the calculation engine
behind at least one public API) whose source code cites exact BPHS
chapter/verse numbers for each planet's table (Chapter 66, verses
43-68). This is stronger sourcing than the many SEO/marketing sites
found during research (several of which contradicted each other on
individual entries), but it is still a secondary source, not a
verified primary one.

**Independent verification performed:** every one of the 7 per-planet
tables below was manually summed and cross-checked against the
per-planet bindu totals independently corroborated across multiple
unrelated sources during research (Sun=48, Moon=49, Mars=39,
Mercury=54, Jupiter=56, Venus=52, Saturn=39, summing to the classical
constant 337). All seven totals matched exactly. This is strong
evidence the table is correct — the odds of a wrong table coincidentally
producing all seven correct sums are low — but it cannot rule out two
individual house entries being transposed while the row total stays
right. `tests/unit/test_ashtakavarga_bindu_table.py` runs this same
checksum as an automated regression test.

The user was given the opportunity to spot-check specific entries
against a physical 1957 C.S. Patel & Aiyar edition they own, but the
relevant table pages could not be located in the scanned copy provided.
Revisit this table if a page reference or a discrepancy surfaces later.
"""

from __future__ import annotations

BINDU_TABLE: dict[str, dict[str, tuple[int, ...]]] = {
    "sun": {
        "sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "moon": (3, 6, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (3, 5, 6, 9, 10, 11, 12),
        "jupiter": (5, 6, 9, 11),
        "venus": (6, 7, 12),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "lagna": (3, 4, 6, 10, 11, 12),
    },
    "moon": {
        "sun": (3, 6, 7, 8, 10, 11),
        "moon": (1, 3, 6, 7, 9, 10, 11),
        "mars": (2, 3, 5, 6, 10, 11),
        "mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "jupiter": (1, 2, 4, 7, 8, 10, 11),
        "venus": (3, 4, 5, 7, 9, 10, 11),
        "saturn": (3, 5, 6, 11),
        "lagna": (3, 6, 10, 11),
    },
    "mars": {
        "sun": (3, 5, 6, 10, 11),
        "moon": (3, 6, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (3, 5, 6, 11),
        "jupiter": (6, 10, 11, 12),
        "venus": (6, 8, 11, 12),
        "saturn": (1, 4, 7, 8, 9, 10, 11),
        "lagna": (1, 3, 6, 10, 11),
    },
    "mercury": {
        "sun": (5, 6, 9, 11, 12),
        "moon": (2, 4, 6, 8, 10, 11),
        "mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "jupiter": (6, 8, 11, 12),
        "venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "lagna": (1, 2, 4, 6, 8, 10, 11),
    },
    "jupiter": {
        "sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "moon": (2, 5, 7, 9, 11),
        "mars": (1, 2, 4, 7, 8, 10, 11),
        "mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "venus": (2, 5, 6, 9, 10, 11),
        "saturn": (3, 5, 6, 12),
        "lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "venus": {
        "sun": (8, 11, 12),
        "moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "mars": (3, 4, 6, 9, 11, 12),
        "mercury": (3, 5, 6, 9, 11),
        "jupiter": (5, 8, 9, 10, 11),
        "venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "saturn": (3, 4, 5, 8, 9, 10, 11),
        "lagna": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "saturn": {
        "sun": (1, 2, 4, 7, 8, 10, 11),
        "moon": (3, 6, 11),
        "mars": (3, 5, 6, 10, 11, 12),
        "mercury": (6, 8, 9, 10, 11, 12),
        "jupiter": (5, 6, 11, 12),
        "venus": (6, 11, 12),
        "saturn": (3, 5, 6, 11),
        "lagna": (1, 3, 4, 6, 10, 11),
    },
}

EXPECTED_PLANET_TOTALS: dict[str, int] = {
    "sun": 48,
    "moon": 49,
    "mars": 39,
    "mercury": 54,
    "jupiter": 56,
    "venus": 52,
    "saturn": 39,
}
EXPECTED_GRAND_TOTAL = 337

CONTRIBUTORS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna"]
TARGET_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

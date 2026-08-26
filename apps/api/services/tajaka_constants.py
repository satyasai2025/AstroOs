"""
AstroOS — Classical Tajaka Constants & Hadda Table
Sources: Tajika Neelakanthi, Prasna Marga, PyJHora
"""

from __future__ import annotations

DEEPTAMSHA: dict[str, float] = {
    "sun": 15.0,
    "moon": 12.0,
    "mars": 8.0,
    "mercury": 7.0,
    "jupiter": 9.0,
    "venus": 7.0,
    "saturn": 9.0,
}

PLANET_SPEED_HIERARCHY: list[str] = [
    "moon",
    "mercury",
    "venus",
    "sun",
    "mars",
    "jupiter",
    "saturn",
]

DEEP_EXALTATION: dict[str, float] = {
    "sun": 10.0,       # Aries 10°
    "moon": 33.0,      # Taurus 3°
    "mars": 298.0,     # Capricorn 28°
    "mercury": 165.0,  # Virgo 15°
    "jupiter": 95.0,   # Cancer 5°
    "venus": 357.0,    # Pisces 27°
    "saturn": 200.0,   # Libra 20°
}

DEEP_DEBILITATION: dict[str, float] = {
    k: (v + 180.0) % 360.0 for k, v in DEEP_EXALTATION.items()
}

HADDA_TABLE: dict[int, list[tuple[float, str]]] = {
    0: [(6.0, "jupiter"), (12.0, "venus"), (20.0, "mercury"), (25.0, "mars"), (30.0, "saturn")],
    1: [(8.0, "venus"), (14.0, "mercury"), (22.0, "jupiter"), (27.0, "saturn"), (30.0, "mars")],
    2: [(6.0, "mercury"), (12.0, "jupiter"), (17.0, "venus"), (24.0, "mars"), (30.0, "saturn")],
    3: [(7.0, "mars"), (13.0, "venus"), (19.0, "mercury"), (26.0, "jupiter"), (30.0, "saturn")],
    4: [(6.0, "jupiter"), (11.0, "venus"), (18.0, "saturn"), (24.0, "mercury"), (30.0, "mars")],
    5: [(7.0, "mercury"), (17.0, "venus"), (21.0, "jupiter"), (28.0, "mars"), (30.0, "saturn")],
    6: [(6.0, "saturn"), (14.0, "mercury"), (21.0, "jupiter"), (28.0, "venus"), (30.0, "mars")],
    7: [(7.0, "mars"), (11.0, "venus"), (19.0, "mercury"), (24.0, "jupiter"), (30.0, "saturn")],
    8: [(12.0, "jupiter"), (17.0, "venus"), (21.0, "mercury"), (26.0, "saturn"), (30.0, "mars")],
    9: [(7.0, "mercury"), (14.0, "jupiter"), (22.0, "venus"), (26.0, "saturn"), (30.0, "mars")],
    10: [(7.0, "mercury"), (13.0, "venus"), (20.0, "jupiter"), (25.0, "mars"), (30.0, "saturn")],
    11: [(12.0, "venus"), (16.0, "jupiter"), (19.0, "mercury"), (28.0, "mars"), (30.0, "saturn")],
}

VIMSHOTTARI_YEARS: dict[str, float] = {
    "sun": 6.0,
    "moon": 10.0,
    "mars": 7.0,
    "rahu": 18.0,
    "jupiter": 16.0,
    "saturn": 19.0,
    "mercury": 17.0,
    "ketu": 7.0,
    "venus": 20.0,
}

VIMSHOTTARI_ORDER: list[str] = [
    "sun",
    "moon",
    "mars",
    "rahu",
    "jupiter",
    "saturn",
    "mercury",
    "ketu",
    "venus",
]

NAKSHATRA_LORDS: list[str] = [
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
]

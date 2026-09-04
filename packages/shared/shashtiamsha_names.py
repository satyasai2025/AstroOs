"""
AstroOS — Shashtiamsha (D60) Division Names

The 60 Shashtiamsha divisions (1/60th of each sign = 0.5 degrees each)
carry distinct classical Sanskrit names per Brihat Parashara Hora Shastra,
Chapter 6 (Shashtiamsha Phala Adhyaya).

Each of the 12 rashis is divided into 60 equal parts of 0.5 degrees (30' of arc).
The first division of Aries carries name 1 (Ghora), the second carries name 2,
and so on cyclically through all 60 names. The same 60-name cycle repeats for
every rashi.

Source: BPHS Chapter 6 — the 60 Shashtiamsha names are listed there. Translations
and Sanskrit romanisations follow the widely-used BPHS English translation
(N.N. Sharma / Girish Chand Sharma edition).

Usage note: "112-Amsa" most likely refers to this table. The classical system has
60 divisions per rashi (D60 = Shashtiamsha). Some extended systems compute
D108 (Ashtottaramsha) or D144, but the 60-name table is the canonical BPHS
reference for Amsa-level karma indicators.
"""

from __future__ import annotations

from typing import Final

# ── 60 Shashtiamsha Names (BPHS Ch. 6) ──────────────────────────────────────
#
# Index 0 = first Shashtiamsha (0.0–0.5 degrees of each rashi).
# Index 59 = sixtieth Shashtiamsha (29.5–30.0 degrees of each rashi).
#
# Classification column (favorable/unfavorable/neutral) follows the BPHS
# phala scheme: divisions ruled by benefic/neutral/malefic deities.

SHASHTIAMSHA_NAMES: Final[list[str]] = [
    "Ghora",           # 0  — inauspicious; cruel, fierce
    "Rakshasa",        # 1  — demonic; evil nature
    "Deva",            # 2  — divine; auspicious
    "Kubera",          # 3  — wealth god; prosperity
    "Yaksha",          # 4  — semi-divine; mixed
    "Kinnara",         # 5  — celestial musician; pleasant
    "Bhrashta",        # 6  — fallen; degraded
    "Kulaghna",        # 7  — destroyer of family; malefic
    "Garala",          # 8  — poisonous; cruel
    "Vahni",           # 9  — fire; fierce, active
    "Maya",            # 10 — illusion; deceitful
    "Purishaka",       # 11 — excremental; degraded
    "Apampathi",       # 12 — lord of waters; mixed
    "Marutwan",        # 13 — wind-lord; mobile, unstable
    "Kaala",           # 14 — death/time; inauspicious
    "Sarpa",           # 15 — serpent; fearful, hidden
    "Amrita",          # 16 — nectar; very auspicious
    "Indu",            # 17 — moon; nourishing, auspicious
    "Mridu",           # 18 — soft/gentle; pleasant
    "Komal",           # 19 — tender; agreeable
    "Heramba",         # 20 — Ganesha aspect; removes obstacles
    "Brahma",          # 21 — creator; very auspicious
    "Vishnu",          # 22 — preserver; highly auspicious
    "Maheswara",       # 23 — Shiva; auspicious, powerful
    "Deva",            # 24 — divine (second occurrence in cycle); auspicious
    "Ardra",           # 25 — Rudra's star; fierce, transformative
    "Kalinasana",      # 26 — destroyer of Kali; protective
    "Soumya",          # 27 — gentle/lunar; pleasant, agreeable
    "Mridu",           # 28 — soft (second occurrence); tender
    "Mrityu",          # 29 — death; malefic, fatal
    "Kala",            # 30 — dark/time; neutral to inauspicious
    "Davagni",         # 31 — forest fire; destructive
    "Ghora",           # 32 — cruel (second cycle start); inauspicious
    "Yama",            # 33 — lord of death; malefic
    "Kantaka",         # 34 — thorn/obstacle; troublesome
    "Sudha",           # 35 — nectar/purity; auspicious
    "Amrita",          # 36 — immortal nectar (second); very auspicious
    "Poornachandra",   # 37 — full moon; auspicious, complete
    "Vishadagdha",     # 38 — poison-burned; malefic
    "Kulanasana",      # 39 — family destroyer; malefic
    "Vamsakshaya",     # 40 — lineage extinguisher; malefic
    "Utpata",          # 41 — calamity/upheaval; malefic
    "Kaala",           # 42 — time/death (second); inauspicious
    "Saumya",          # 43 — auspicious/pleasant; benign
    "Komala",          # 44 — tender (variant); agreeable
    "Sheetala",        # 45 — cool/soothing; benign
    "Karaladamstra",   # 46 — with terrible fangs; fierce
    "Chandramukhi",    # 47 — moon-faced; pleasant
    "Praveena",        # 48 — expert/skilled; favorable
    "Kaalpavaka",      # 49 — time-cleansing fire; transformative
    "Dandayudha",      # 50 — staff-weapon bearer; authoritative
    "Nirmala",         # 51 — spotless/pure; auspicious
    "Saumya",          # 52 — pleasant (third); benign
    "Kroora",          # 53 — cruel; malefic
    "Atisheetala",     # 54 — very cool; benign
    "Amrita",          # 55 — nectar (third); auspicious
    "Payodhi",         # 56 — ocean of milk; nourishing
    "Brahma",          # 57 — creator (second); auspicious
    "Chandrarekha",    # 58 — moonbeam; gentle, auspicious
    "Vishnupada",      # 59 — Vishnu's foot/step; very auspicious
]

assert len(SHASHTIAMSHA_NAMES) == 60, (
    f"SHASHTIAMSHA_NAMES must have exactly 60 entries; got {len(SHASHTIAMSHA_NAMES)}"
)

# ── Classification ────────────────────────────────────────────────────────────

#: Shashtiamsha indices (0-based) considered auspicious / Deva-like.
#: Source: BPHS phala descriptions — divisions whose deities are benign.
AUSPICIOUS_INDICES: Final[frozenset[int]] = frozenset({
    2, 3, 5, 12, 16, 17, 18, 19, 20, 21, 22, 23, 24,
    26, 27, 28, 35, 36, 37, 43, 44, 45, 47, 48, 51, 52,
    54, 55, 56, 57, 58, 59,
})

#: Shashtiamsha indices considered inauspicious / Krura.
INAUSPICIOUS_INDICES: Final[frozenset[int]] = frozenset({
    0, 1, 6, 7, 8, 9, 10, 11, 14, 15, 25, 29, 30, 31,
    32, 33, 34, 38, 39, 40, 41, 42, 46, 49, 50, 53,
})


# ── Public API ────────────────────────────────────────────────────────────────


def shashtiamsha_index(longitude_in_sign: float) -> int:
    """Return the 0-based Shashtiamsha index (0–59) for a given degree within a sign.

    Args:
        longitude_in_sign: Degrees within the sign, 0.0 <= x < 30.0.

    Returns:
        Integer index 0–59 (each division = 0.5 degrees).

    Raises:
        ValueError: If longitude_in_sign is outside [0, 30).
    """
    if not (0.0 <= longitude_in_sign < 30.0):
        raise ValueError(
            f"longitude_in_sign must be in [0, 30); got {longitude_in_sign!r}"
        )
    return int(longitude_in_sign / 0.5)


def shashtiamsha_name(longitude_in_sign: float) -> str:
    """Return the classical Sanskrit name for the Shashtiamsha at the given degree.

    Args:
        longitude_in_sign: Degrees within the sign, 0.0 <= x < 30.0.

    Returns:
        Classical Sanskrit name string.
    """
    idx = shashtiamsha_index(longitude_in_sign)
    return SHASHTIAMSHA_NAMES[idx]


def shashtiamsha_is_auspicious(longitude_in_sign: float) -> bool:
    """True if the Shashtiamsha at the given degree is auspicious (Deva/Soumya class)."""
    return shashtiamsha_index(longitude_in_sign) in AUSPICIOUS_INDICES


def shashtiamsha_is_inauspicious(longitude_in_sign: float) -> bool:
    """True if the Shashtiamsha at the given degree is inauspicious (Krura/Rakshasa class)."""
    return shashtiamsha_index(longitude_in_sign) in INAUSPICIOUS_INDICES

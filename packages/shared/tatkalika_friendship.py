"""
AstroOS — Tatkalika (Temporary) and Panchadha (5-fold) Friendship Calculation

Classical Jyotish (BPHS Ch. 15 / Maitri Prakarana):
Natural (Naisargika) relationship combines with Temporary (Tatkalika)
relationship to produce the 5-fold compound relationship (Panchadha Maitri).

Temporary Friendship Rule:
- Grahas occupying the 2nd, 3rd, 4th, 10th, 11th, and 12th houses/rashis from
  a graha are its Temporary Friends (Tatkalika Mitra).
- Grahas occupying the 1st (same sign), 5th, 6th, 7th, 8th, and 9th houses/rashis
  are its Temporary Enemies (Tatkalika Shatru).

Panchadha (5-fold) Relationship Table:
- Friend + Friend   -> Adhi Mitra (Great Friend)
- Friend + Enemy    -> Sama (Neutral)
- Neutral + Friend  -> Mitra (Friend)
- Neutral + Enemy   -> Shatru (Enemy)
- Enemy + Friend    -> Sama (Neutral)
- Enemy + Enemy     -> Adhi Shatru (Great Enemy)
"""

from __future__ import annotations

from typing import Optional

from packages.shared.dignity import ENEMIES, FRIENDS

_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_RASHI_INDEX = {r: i for i, r in enumerate(_RASHI_ORDER)}

_TEMPORARY_FRIEND_OFFSETS = {2, 3, 4, 10, 11, 12}


def get_natural_friendship(planet_a: str, planet_b: str) -> str:
    """
    Returns the natural (Naisargika) relationship of planet_a toward planet_b:
    "friend", "enemy", or "neutral".
    """
    p_a = planet_a.lower()
    p_b = planet_b.lower()
    if p_b in FRIENDS.get(p_a, []):
        return "friend"
    if p_b in ENEMIES.get(p_a, []):
        return "enemy"
    return "neutral"


def compute_tatkalika_friendship(rashi_a: str, rashi_b: str) -> str:
    """
    Computes the temporary (Tatkalika) relationship from rashi_a to rashi_b:
    "friend" or "enemy".

    Counted inclusive from rashi_a (1-indexed house offset).
    """
    idx_a = _RASHI_INDEX.get(rashi_a.lower())
    idx_b = _RASHI_INDEX.get(rashi_b.lower())
    if idx_a is None or idx_b is None:
        raise ValueError(f"Unknown rashi pair: {rashi_a!r}, {rashi_b!r}")

    house_offset = ((idx_b - idx_a) % 12) + 1
    if house_offset in _TEMPORARY_FRIEND_OFFSETS:
        return "friend"
    return "enemy"


def compute_panchadha_friendship(natural: str, temporary: str) -> str:
    """
    Combines natural ("friend", "enemy", "neutral") and temporary ("friend", "enemy")
    into the classical 5-fold relationship:
    "adhi_mitra", "mitra", "sama", "shatru", "adhi_shatru".
    """
    nat = natural.lower()
    temp = temporary.lower()

    if nat == "friend":
        return "adhi_mitra" if temp == "friend" else "sama"
    if nat == "neutral":
        return "mitra" if temp == "friend" else "shatru"
    if nat == "enemy":
        return "sama" if temp == "friend" else "adhi_shatru"
    return "sama"


def compute_combined_friendship(
    planet_a: str,
    rashi_a: str,
    planet_b: str,
    rashi_b: str,
) -> tuple[str, str, str]:
    """
    Convenience helper returning (natural, temporary, panchadha) for planet_a toward planet_b.
    """
    natural = get_natural_friendship(planet_a, planet_b)
    temporary = compute_tatkalika_friendship(rashi_a, rashi_b)
    panchadha = compute_panchadha_friendship(natural, temporary)
    return natural, temporary, panchadha

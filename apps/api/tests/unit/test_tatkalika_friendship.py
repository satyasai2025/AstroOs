"""
AstroOS — Unit tests for Tatkalika & Panchadha Friendship calculations
"""

import pytest

from packages.shared.tatkalika_friendship import (
    compute_combined_friendship,
    compute_panchadha_friendship,
    compute_tatkalika_friendship,
    get_natural_friendship,
)


def test_natural_friendship_lookup():
    # Sun's natural friends: Moon, Mars, Jupiter
    assert get_natural_friendship("sun", "moon") == "friend"
    assert get_natural_friendship("sun", "mars") == "friend"
    assert get_natural_friendship("sun", "jupiter") == "friend"

    # Sun's natural enemies: Venus, Saturn
    assert get_natural_friendship("sun", "venus") == "enemy"
    assert get_natural_friendship("sun", "saturn") == "enemy"

    # Sun's natural neutral: Mercury
    assert get_natural_friendship("sun", "mercury") == "neutral"


def test_tatkalika_temporary_friendship():
    # Planets in 2nd, 3rd, 4th, 10th, 11th, 12th houses from each other are temporary friends
    # Aries to Taurus (2nd house) -> friend
    assert compute_tatkalika_friendship("aries", "taurus") == "friend"
    # Aries to Gemini (3rd house) -> friend
    assert compute_tatkalika_friendship("aries", "gemini") == "friend"
    # Aries to Cancer (4th house) -> friend
    assert compute_tatkalika_friendship("aries", "cancer") == "friend"
    # Aries to Capricorn (10th house) -> friend
    assert compute_tatkalika_friendship("aries", "capricorn") == "friend"
    # Aries to Aquarius (11th house) -> friend
    assert compute_tatkalika_friendship("aries", "aquarius") == "friend"
    # Aries to Pisces (12th house) -> friend
    assert compute_tatkalika_friendship("aries", "pisces") == "friend"

    # Same sign (1st house) -> enemy
    assert compute_tatkalika_friendship("aries", "aries") == "enemy"
    # 5th house (Leo) -> enemy
    assert compute_tatkalika_friendship("aries", "leo") == "enemy"
    # 6th house (Virgo) -> enemy
    assert compute_tatkalika_friendship("aries", "virgo") == "enemy"
    # 7th house (Libra) -> enemy
    assert compute_tatkalika_friendship("aries", "libra") == "enemy"
    # 8th house (Scorpio) -> enemy
    assert compute_tatkalika_friendship("aries", "scorpio") == "enemy"
    # 9th house (Sagittarius) -> enemy
    assert compute_tatkalika_friendship("aries", "sagittarius") == "enemy"


def test_panchadha_combinations():
    # Friend + Friend = Adhi Mitra
    assert compute_panchadha_friendship("friend", "friend") == "adhi_mitra"
    # Friend + Enemy = Sama
    assert compute_panchadha_friendship("friend", "enemy") == "sama"
    # Neutral + Friend = Mitra
    assert compute_panchadha_friendship("neutral", "friend") == "mitra"
    # Neutral + Enemy = Shatru
    assert compute_panchadha_friendship("neutral", "enemy") == "shatru"
    # Enemy + Friend = Sama
    assert compute_panchadha_friendship("enemy", "friend") == "sama"
    # Enemy + Enemy = Adhi Shatru
    assert compute_panchadha_friendship("enemy", "enemy") == "adhi_shatru"


def test_combined_friendship_sun_and_saturn():
    # Sun in Aries, Saturn in Taurus (2nd house -> temporary friend, natural enemy -> Sama)
    nat, temp, panch = compute_combined_friendship("sun", "aries", "saturn", "taurus")
    assert nat == "enemy"
    assert temp == "friend"
    assert panch == "sama"

    # Sun in Aries, Saturn in Libra (7th house -> temporary enemy, natural enemy -> Adhi Shatru)
    nat, temp, panch = compute_combined_friendship("sun", "aries", "saturn", "libra")
    assert nat == "enemy"
    assert temp == "enemy"
    assert panch == "adhi_shatru"

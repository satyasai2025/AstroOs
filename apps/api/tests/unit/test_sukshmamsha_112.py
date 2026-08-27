"""
Unit tests -- 112 Sukshmamsha (Pada-112) module.
"""

import pytest
from packages.shared.sukshmamsha_112 import (
    SUKSHMAMSHA_BY_INDEX,
    SUKSHMAMSHA_BY_NAK_PADA,
    SukshmamshaNature,
    get_sukshmamsha,
    get_sukshmamsha_by_nak_pada,
    is_auspicious_sukshmamsha,
    is_inauspicious_sukshmamsha,
)


def test_table_has_exact_112_entries():
    assert len(SUKSHMAMSHA_BY_INDEX) == 112


def test_first_entry_is_krittika_1():
    entry = get_sukshmamsha(1)
    assert entry.nakshatra == "Krittika"
    assert entry.pada == 1
    assert entry.nakshatra_pada == "Krittika-1"
    assert entry.name_sa == "धनांश"
    assert entry.name_en == "Dhanāṁśa"
    assert entry.nature == SukshmamshaNature.AUSPICIOUS


def test_last_entry_is_bharani_4():
    entry = get_sukshmamsha(112)
    assert entry.nakshatra == "Bharani"
    assert entry.pada == 4
    assert entry.nakshatra_pada == "Bharani-4"
    assert entry.name_sa == "शुभांश"
    assert entry.name_en == "Śubhāṁśa"
    assert entry.nature == SukshmamshaNature.AUSPICIOUS


def test_abhijit_entries_exist():
    # Abhijit is padas 77 to 80
    for idx in range(77, 81):
        entry = get_sukshmamsha(idx)
        assert entry.nakshatra == "Abhijit"
        assert entry.pada in (1, 2, 3, 4)


def test_lookup_by_nak_pada():
    entry = get_sukshmamsha_by_nak_pada("Rohini", 1)
    assert entry.index == 5
    assert entry.name_sa == "सेनांश"
    assert entry.name_en == "Senāṁśa"

    entry2 = get_sukshmamsha_by_nak_pada("Aswini", 2)
    assert entry2.index == 106
    assert entry2.nature == SukshmamshaNature.AUSPICIOUS
    assert entry2.name_sa == "भोग्यांश"


def test_krura_entry():
    entry = get_sukshmamsha(2) # Krittika-2 is Pāpāṁśa
    assert entry.name_sa == "पापांश"
    assert entry.nature == SukshmamshaNature.INAUSPICIOUS
    assert is_inauspicious_sukshmamsha(2) is True


def test_invalid_index_raises():
    with pytest.raises(ValueError):
        get_sukshmamsha(0)
    with pytest.raises(ValueError):
        get_sukshmamsha(113)


def test_invalid_nak_pada_raises():
    with pytest.raises(ValueError):
        get_sukshmamsha_by_nak_pada("NonExistent", 1)

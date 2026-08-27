"""
Unit tests — Shashtiamsha (D60) naming table.
"""

from __future__ import annotations

import pytest

from packages.shared.shashtiamsha_names import (
    AUSPICIOUS_INDICES,
    INAUSPICIOUS_INDICES,
    SHASHTIAMSHA_NAMES,
    shashtiamsha_index,
    shashtiamsha_is_auspicious,
    shashtiamsha_is_inauspicious,
    shashtiamsha_name,
)


class TestTableIntegrity:
    def test_exactly_60_names(self):
        assert len(SHASHTIAMSHA_NAMES) == 60

    def test_all_names_non_empty_strings(self):
        for i, name in enumerate(SHASHTIAMSHA_NAMES):
            assert isinstance(name, str) and name.strip(), (
                f"Index {i}: name must be non-empty string, got {name!r}"
            )

    def test_auspicious_and_inauspicious_disjoint(self):
        overlap = AUSPICIOUS_INDICES & INAUSPICIOUS_INDICES
        assert not overlap, f"Indices appear in both sets: {overlap}"

    def test_auspicious_indices_in_range(self):
        assert all(0 <= i < 60 for i in AUSPICIOUS_INDICES)

    def test_inauspicious_indices_in_range(self):
        assert all(0 <= i < 60 for i in INAUSPICIOUS_INDICES)


class TestIndexLookup:
    @pytest.mark.parametrize("degree, expected_idx", [
        (0.0, 0),
        (0.49, 0),
        (0.5, 1),
        (1.0, 2),
        (14.75, 29),
        (15.0, 30),
        (29.5, 59),
        (29.99, 59),
    ])
    def test_index_at_boundary(self, degree, expected_idx):
        assert shashtiamsha_index(degree) == expected_idx

    def test_first_name_is_ghora(self):
        assert shashtiamsha_name(0.0) == "Ghora"

    def test_index_16_is_amrita(self):
        # 16 * 0.5 = 8.0 degrees
        assert shashtiamsha_name(8.0) == "Amrita"

    def test_index_21_is_brahma(self):
        # 21 * 0.5 = 10.5 degrees
        assert shashtiamsha_name(10.5) == "Brahma"

    def test_index_22_is_vishnu(self):
        # 22 * 0.5 = 11.0 degrees
        assert shashtiamsha_name(11.0) == "Vishnu"

    def test_last_index_59_is_vishnupada(self):
        assert shashtiamsha_name(29.5) == "Vishnupada"


class TestValidation:
    def test_out_of_range_negative_raises(self):
        with pytest.raises(ValueError):
            shashtiamsha_index(-0.1)

    def test_out_of_range_30_raises(self):
        with pytest.raises(ValueError):
            shashtiamsha_index(30.0)

    def test_out_of_range_35_raises(self):
        with pytest.raises(ValueError):
            shashtiamsha_index(35.0)


class TestAuspiciousness:
    def test_deva_index_2_is_auspicious(self):
        # Index 2 = "Deva" — divine; auspicious
        assert shashtiamsha_is_auspicious(1.0)  # 1.0 / 0.5 = index 2

    def test_ghora_index_0_is_inauspicious(self):
        assert shashtiamsha_is_inauspicious(0.0)

    def test_vishnu_index_22_is_auspicious(self):
        assert shashtiamsha_is_auspicious(11.0)

    def test_auspicious_not_inauspicious(self):
        # For auspicious indices, inauspicious should be False
        for idx in AUSPICIOUS_INDICES:
            deg = idx * 0.5
            assert not shashtiamsha_is_inauspicious(deg), (
                f"Index {idx} ({SHASHTIAMSHA_NAMES[idx]}) should not be inauspicious"
            )

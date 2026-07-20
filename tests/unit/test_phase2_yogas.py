"""
AstroOS — Phase 2 (v2.1.0) Yoga Unit Tests

Covers:
  - Nabhasa Sankhya (Kedara, Pasha, Dama, Dhvaja, Gola, Yuga)
  - Nabhasa Akriti (Hala, Vajra, Yava, Kamala, Vapi, Dhanu)
  - Nabhasa Dala (Malavya, Sarala, Mukuta)
  - Chandra Phase 2 (Amavasya, Vyatipata)
  - Arishta Phase 2 (ARY-004 through ARY-011)
  - Composite Yogas (COMP-001 through COMP-007)
  - Yoga strength scoring
  - Yoga counter-examples
"""

from dataclasses import replace

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_strength import compute_yoga_strength_score

_ZODIAC = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _make_planet(planet, rashi="aries", house_number=1, is_retrograde=False, is_combust=False, dignity=None):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi=rashi, rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=is_retrograde, is_combust=is_combust, combustion_orb=None,
        dignity=dignity or DignityType.NEUTRAL,
    )


def _make_chart(planets, lagna_rashi="aries"):
    lagna_index = _ZODIAC.index(lagna_rashi)
    houses = [
        HouseCusp(
            house_number=i + 1, longitude=float(((lagna_index + i) % 12) * 30),
            sidereal_longitude=float(((lagna_index + i) % 12) * 30),
            rashi=_ZODIAC[(lagna_index + i) % 12],
        )
        for i in range(12)
    ]

    class _FakeChart:
        pass

    chart = _FakeChart()
    chart.houses = houses
    chart.planets = planets
    chart.aspects = []
    return chart


def _result(chart, yoga_id):
    return YogaEngine().evaluate_one(chart, yoga_id)


def _all_in(rashi_options):
    """Place all 7 classical grahas across the given rashi options, cycling."""
    return [
        _make_planet(planet, rashi_options[i % len(rashi_options)])
        for i, planet in enumerate(_CLASSICAL_SEVEN)
    ]


def _all_in_houses(house_list):
    """Place all 7 classical grahas in the given houses, cycling."""
    return [
        _make_planet(planet, house_number=house_list[i % len(house_list)])
        for i, planet in enumerate(_CLASSICAL_SEVEN)
    ]


# =========================================================================
# Nabhasa Yoga — Sankhya (count-based)
# =========================================================================

class TestNabhasaSankhya:

    def test_kedara_all_different_signs_present(self):
        """Kedara: each of 7 planets in a different sign (span=7)."""
        planets = [
            _make_planet(p, rashi=_ZODIAC[i % 12], house_number=1)
            for i, p in enumerate(_CLASSICAL_SEVEN)
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-004")
        assert result.is_present is True
        assert result.name == "Kedara Nabhasa"

    def test_kedara_absent_when_two_in_same_sign(self):
        """Kedara absent: duplicate sign."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo", "virgo", "aries"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-004")
        assert result.is_present is False

    def test_kedara_absent_insufficient_planets(self):
        chart = _make_chart([])
        result = _result(chart, "BPHS-NY-004")
        assert result.is_present is False

    def test_pasha_within_5_signs_present(self):
        """Pasha: all within 5 consecutive signs."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-005")
        assert result.is_present is True

    def test_pasha_spans_6_signs_absent(self):
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo", "virgo"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-005")
        assert result.is_present is False

    def test_dama_within_6_signs_present(self):
        """Dama: all within 6 consecutive signs."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo", "virgo"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-006")
        assert result.is_present is True

    def test_dama_spans_7_signs_absent(self):
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-006")
        assert result.is_present is False

    def test_dhvaja_within_4_signs_present(self):
        """Dhvaja: all within 4 consecutive signs."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-007")
        assert result.is_present is True

    def test_gola_within_2_signs_present(self):
        """Gola: all within 2 adjacent signs."""
        planets = _all_in(["aries", "taurus"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-008")
        assert result.is_present is True

    def test_gola_absent_spans_3_signs(self):
        planets = _all_in(["aries", "taurus", "gemini"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-008")
        assert result.is_present is False

    def test_yuga_opposite_signs_present(self):
        """Yuga: planets split between a sign and its 7th only."""
        planets = _all_in(["aries", "libra"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-009")
        assert result.is_present is True

    def test_yuga_absent_third_sign(self):
        planets = _all_in(["aries", "libra", "taurus"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-009")
        assert result.is_present is False

    def test_yuga_absent_when_planet_missing(self):
        chart = _make_chart([])
        result = _result(chart, "BPHS-NY-009")
        assert result.is_present is False


# =========================================================================
# Nabhasa Yoga — Akriti (shape-based)
# =========================================================================

class TestNabhasaAkriti:

    def test_hala_6_signs_present(self):
        """Hala: all within 6 consecutive signs."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo", "virgo"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-010")
        assert result.is_present is True

    def test_vajra_lagna_and_7th_only_present(self):
        """Vajra: all in lagna sign or its 7th."""
        planets = [_make_planet("sun", "aries"), _make_planet("moon", "libra"),
                   _make_planet("mars", "libra"), _make_planet("mercury", "aries"),
                   _make_planet("jupiter", "libra"), _make_planet("venus", "aries"),
                   _make_planet("saturn", "aries")]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-NY-011")
        assert result.is_present is True

    def test_vajra_absent_third_sign(self):
        planets = [_make_planet("sun", "aries"), _make_planet("moon", "libra"),
                   _make_planet("mars", "taurus"), _make_planet("mercury", "aries"),
                   _make_planet("jupiter", "libra"), _make_planet("venus", "aries"),
                   _make_planet("saturn", "aries")]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-NY-011")
        assert result.is_present is False

    def test_yava_two_pairs_present(self):
        """Yava: planets in 2 pairs of opposite signs."""
        planets = _all_in(["aries", "libra", "taurus", "scorpio"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-012")
        assert result.is_present is True

    def test_yava_absent_one_pair(self):
        planets = _all_in(["aries", "libra"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-012")
        assert result.is_present is False

    def test_kamala_all_in_kendra_present(self):
        """Kamala: all planets in kendra houses (1, 4, 7, 10)."""
        planets = _all_in_houses([1, 4, 7, 10])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-013")
        assert result.is_present is True

    def test_kamala_absent_non_kendra(self):
        planets = _all_in_houses([1, 4, 7, 10, 2])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-013")
        assert result.is_present is False

    def test_vapi_3_signs_present(self):
        """Vapi: all within 3 consecutive signs."""
        planets = _all_in(["aries", "taurus", "gemini"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-014")
        assert result.is_present is True

    def test_dhanu_10_plus_signs_present(self):
        """Dhanu: planets spread across 6+ different signs."""
        # With 7 planets, 6+ unique signs means at most 1 duplicate pair
        planets = [
            _make_planet("sun", "aries"),
            _make_planet("moon", "taurus"),
            _make_planet("mars", "gemini"),
            _make_planet("mercury", "cancer"),
            _make_planet("jupiter", "leo"),
            _make_planet("venus", "virgo"),
            _make_planet("saturn", "libra"),  # 7 different signs
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-015")
        assert result.is_present is True

    def test_dhanu_absent_fewer_than_6_signs(self):
        # Only 3 unique signs
        planets = _all_in(["aries", "taurus", "gemini"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-015")
        assert result.is_present is False


# =========================================================================
# Nabhasa Yoga — Dala (benefic/malefic concentration)
# =========================================================================

class TestNabhasaDala:

    def test_malavya_dala_present(self):
        """Malavya: all benefics in kendra."""
        planets = [
            _make_planet("jupiter", house_number=1),  # benefic, kendra
            _make_planet("venus", house_number=4),    # benefic, kendra
            _make_planet("mercury", house_number=7),  # benefic (conditional), kendra
            _make_planet("moon", house_number=10),    # benefic, kendra
            _make_planet("mars", house_number=2),     # malefic, doesn't affect
            _make_planet("sun", house_number=5),
            _make_planet("saturn", house_number=9),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-016")
        assert result.is_present is True

    def test_malavya_dala_absent_benefic_outside_kendra(self):
        planets = [
            _make_planet("jupiter", house_number=1),
            _make_planet("venus", house_number=5),  # benefic NOT in kendra
            _make_planet("mercury", house_number=7),
            _make_planet("moon", house_number=10),
            _make_planet("mars", house_number=2),
            _make_planet("sun", house_number=3),
            _make_planet("saturn", house_number=8),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-016")
        assert result.is_present is False

    def test_sarala_dala_present(self):
        """Sarala: all malefics in kendra."""
        planets = [
            _make_planet("sun", house_number=1),     # malefic, kendra
            _make_planet("mars", house_number=4),    # malefic, kendra
            _make_planet("saturn", house_number=7),  # malefic, kendra
            _make_planet("jupiter", house_number=2),  # benefic, doesn't affect
            _make_planet("venus", house_number=5),
            _make_planet("mercury", house_number=8),
            _make_planet("moon", house_number=10),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-017")
        assert result.is_present is True

    def test_sarala_dala_absent_malefic_outside_kendra(self):
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("mars", house_number=5),  # malefic NOT in kendra
            _make_planet("saturn", house_number=7),
            _make_planet("jupiter", house_number=2),
            _make_planet("venus", house_number=6),
            _make_planet("mercury", house_number=9),
            _make_planet("moon", house_number=10),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-017")
        assert result.is_present is False

    def test_mukuta_dala_present(self):
        """Mukuta: all planets in kendra or trikona (1/4/5/7/9/10)."""
        kendra_trikona = [1, 4, 5, 7, 9, 10]
        planets = _all_in_houses(kendra_trikona)
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-018")
        assert result.is_present is True

    def test_mukuta_dala_absent_non_kendra_trikona(self):
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("moon", house_number=6),  # dusthana
            _make_planet("mars", house_number=4),
            _make_planet("mercury", house_number=7),
            _make_planet("jupiter", house_number=9),
            _make_planet("venus", house_number=10),
            _make_planet("saturn", house_number=2),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-018")
        assert result.is_present is False


# =========================================================================
# Chandra Yoga — Phase 2 (Amavasya, Vyatipata)
# =========================================================================

class TestChandraPhase2:

    def test_amavasya_present_same_sign(self):
        """Amavasya: Sun and Moon in same sign."""
        planets = [
            _make_planet("sun", "aries", house_number=3),
            _make_planet("moon", "aries", house_number=3),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-007")
        assert result.is_present is True

    def test_amavasya_absent_different_sign(self):
        planets = [
            _make_planet("sun", "aries", house_number=3),
            _make_planet("moon", "taurus", house_number=4),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-007")
        assert result.is_present is False

    def test_amavasya_absent_moon_missing(self):
        chart = _make_chart([_make_planet("sun", "aries")])
        result = _result(chart, "BPHS-CY-007")
        assert result.is_present is False

    def test_amavasya_has_counter_examples_when_present(self):
        planets = [
            _make_planet("sun", "aries", house_number=3),
            _make_planet("moon", "aries", house_number=3),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-007")
        assert len(result.counter_examples) > 0

    def test_vyatipata_moon_8th_from_sun_present(self):
        """Vyatipata: Moon in 8th from Sun."""
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("moon", house_number=8),  # 8th from Sun
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-008")
        assert result.is_present is True

    def test_vyatipata_absent_wrong_house(self):
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("moon", house_number=3),  # not 8th from Sun
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-008")
        assert result.is_present is False

    def test_vyatipata_absent_sun_missing(self):
        chart = _make_chart([_make_planet("moon", house_number=1)])
        result = _result(chart, "BPHS-CY-008")
        assert result.is_present is False


# =========================================================================
# Arishta Yoga — Phase 2 (new malefic combinations)
# =========================================================================

class TestArishtaPhase2:

    def test_papakartari_moon_present(self):
        """Papakartari on Moon: malefics in 2nd and 12th from Moon."""
        planets = [
            _make_planet("moon", house_number=5),
            _make_planet("mars", house_number=6),   # 2nd from Moon
            _make_planet("saturn", house_number=4), # 12th from Moon
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-004")
        assert result.is_present is True

    def test_papakartari_moon_absent_only_one_side(self):
        planets = [
            _make_planet("moon", house_number=5),
            _make_planet("mars", house_number=6),   # 2nd from Moon
            _make_planet("venus", house_number=4),  # benefic, not malefic
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-004")
        assert result.is_present is False

    def test_mars_saturn_conjunction_present(self):
        """Mars-Saturn conjunction."""
        planets = [
            _make_planet("mars", house_number=3),
            _make_planet("saturn", house_number=3),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-005")
        assert result.is_present is True

    def test_mars_saturn_conjunction_absent(self):
        planets = [
            _make_planet("mars", house_number=3),
            _make_planet("saturn", house_number=7),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-005")
        assert result.is_present is False

    def test_malefics_in_kendras_present(self):
        """3+ malefics in kendras."""
        planets = [
            _make_planet("sun", house_number=1),    # malefic, kendra
            _make_planet("mars", house_number=4),   # malefic, kendra
            _make_planet("saturn", house_number=7), # malefic, kendra
            _make_planet("jupiter", house_number=5),
            _make_planet("venus", house_number=9),
            _make_planet("mercury", house_number=2),
            _make_planet("moon", house_number=10),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-006")
        assert result.is_present is True

    def test_malefics_in_kendras_absent_only_2(self):
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("mars", house_number=4),
            _make_planet("saturn", house_number=5),  # not kendra
            _make_planet("jupiter", house_number=9),
            _make_planet("venus", house_number=10),
            _make_planet("mercury", house_number=2),
            _make_planet("moon", house_number=11),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-006")
        assert result.is_present is False

    def test_benefics_in_dusthanas_present(self):
        """All benefics in 6th/8th/12th."""
        planets = [
            _make_planet("jupiter", house_number=6),   # benefic, dusthana
            _make_planet("venus", house_number=8),     # benefic, dusthana
            _make_planet("mercury", house_number=12),  # benefic, dusthana
            _make_planet("moon", house_number=8),      # benefic, dusthana
            _make_planet("mars", house_number=1),      # malefic, irrelevant
            _make_planet("sun", house_number=5),
            _make_planet("saturn", house_number=9),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-007")
        assert result.is_present is True

    def test_benefics_in_dusthanas_absent_benefic_outside(self):
        planets = [
            _make_planet("jupiter", house_number=6),
            _make_planet("venus", house_number=2),  # benefic OUTSIDE dusthana
            _make_planet("mercury", house_number=12),
            _make_planet("moon", house_number=8),
            _make_planet("mars", house_number=1),
            _make_planet("sun", house_number=5),
            _make_planet("saturn", house_number=9),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-007")
        assert result.is_present is False

    def test_lagna_lord_in_dusthana_present(self):
        """Lagna lord in 6th/8th/12th."""
        planets = [
            _make_planet("mars", "aries", house_number=6),  # lagna lord (mars for aries)
        ]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-ARY-008")
        assert result.is_present is True

    def test_lagna_lord_in_dusthana_absent(self):
        planets = [
            _make_planet("mars", "aries", house_number=1),
        ]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-ARY-008")
        assert result.is_present is False

    def test_debilitated_in_kendra_present(self):
        """Any planet debilitated in kendra."""
        planets = [
            _make_planet("jupiter", "capricorn", house_number=4, dignity=DignityType.DEBILITATED),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-009")
        assert result.is_present is True

    def test_debilitated_in_kendra_absent_debilitated_not_kendra(self):
        planets = [
            _make_planet("jupiter", "capricorn", house_number=6, dignity=DignityType.DEBILITATED),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-009")
        assert result.is_present is False

    def test_sun_saturn_conjunction_present(self):
        """Sun-Saturn conjunction."""
        planets = [
            _make_planet("sun", house_number=5),
            _make_planet("saturn", house_number=5),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-010")
        assert result.is_present is True

    def test_sun_saturn_conjunction_absent(self):
        planets = [
            _make_planet("sun", house_number=5),
            _make_planet("saturn", house_number=6),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-010")
        assert result.is_present is False

    def test_rahu_ketu_kendra_malefic_present(self):
        """Rahu in kendra aspected by malefic."""
        # Rahu in house 1 (kendra), Saturn aspects it
        class _ChartWithAspects:
            pass

        class _Aspect:
            def __init__(self, f, t):
                self.from_planet = f
                self.to_planet = t

        chart = _ChartWithAspects()
        chart.houses = [
            HouseCusp(house_number=i+1, longitude=float(i*30), sidereal_longitude=float(i*30), rashi=_ZODIAC[i])
            for i in range(12)
        ]
        chart.planets = [
            _make_planet("rahu", house_number=1),
            _make_planet("saturn", house_number=7),
        ]
        chart.aspects = [_Aspect("saturn", "rahu")]
        result = YogaEngine().evaluate_one(chart, "BPHS-ARY-011")
        assert result is not None
        assert result.is_present is True

    def test_rahu_ketu_kendra_malefic_no_aspect(self):
        """Rahu in kendra but no malefic aspect — not present."""
        class _ChartNoAspects:
            pass

        chart = _ChartNoAspects()
        chart.houses = [
            HouseCusp(house_number=i+1, longitude=float(i*30), sidereal_longitude=float(i*30), rashi=_ZODIAC[i])
            for i in range(12)
        ]
        chart.planets = [
            _make_planet("rahu", house_number=1),
            _make_planet("jupiter", house_number=2),  # benefic, not malefic
        ]
        chart.aspects = []
        result = YogaEngine().evaluate_one(chart, "BPHS-ARY-011")
        assert result is not None
        assert result.is_present is False


# =========================================================================
# Composite Yogas (multi-planet/house)
# =========================================================================

class TestCompositeYogas:

    def test_lakshmi_yoga_present(self):
        """9th lord in own sign + Venus in kendra."""
        # Aries lagna: 9th lord = Jupiter (Sagittarius ruler)
        # Venus in house 1 (kendra)
        planets = [
            _make_planet("jupiter", "sagittarius", house_number=9),  # 9th lord in own sign
            _make_planet("venus", house_number=1),                   # Venus in kendra
        ]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-COMP-001")
        assert result.is_present is True

    def test_lakshmi_yoga_absent_venus_not_kendra(self):
        planets = [
            _make_planet("jupiter", "sagittarius", house_number=9),
            _make_planet("venus", house_number=6),  # Venus NOT in kendra
        ]
        chart = _make_chart(planets, lagna_rashi="aries")
        result = _result(chart, "BPHS-COMP-001")
        assert result.is_present is False

    def test_saraswati_yoga_present(self):
        """Jupiter, Venus, Mercury all in kendra."""
        planets = [
            _make_planet("jupiter", house_number=1),
            _make_planet("venus", house_number=4),
            _make_planet("mercury", house_number=7),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-COMP-002")
        assert result.is_present is True

    def test_saraswati_yoga_absent_one_not_kendra(self):
        planets = [
            _make_planet("jupiter", house_number=1),
            _make_planet("venus", house_number=4),
            _make_planet("mercury", house_number=6),  # not kendra
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-COMP-002")
        assert result.is_present is False

    def test_harsha_yoga_present_pisces_lagna(self):
        """Pisces lagna: 6th house = Leo, ruled by Sun."""
        planets = [
            _make_planet("sun", house_number=6),  # Sun in 6th, ruler of 6th (Leo)
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-003")
        assert result.is_present is True

    def test_harsha_yoga_absent(self):
        """6th lord NOT in 6th."""
        planets = [
            _make_planet("sun", house_number=1),  # Sun in 1st, not 6th
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-003")
        assert result.is_present is False

    def test_sarala_yoga_present_8th_lord(self):
        """8th lord in 8th house."""
        # Pisces lagna: 8th house = Libra, ruled by Venus
        planets = [
            _make_planet("venus", house_number=8),
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-004")
        assert result.is_present is True

    def test_sarala_yoga_absent(self):
        planets = [
            _make_planet("venus", house_number=1),
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-004")
        assert result.is_present is False

    def test_vimala_yoga_present_12th_lord(self):
        """12th lord in 12th house."""
        # Pisces lagna: 12th house = Aquarius, ruled by Saturn
        planets = [
            _make_planet("saturn", house_number=12),
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-005")
        assert result.is_present is True

    def test_vimala_yoga_absent(self):
        planets = [
            _make_planet("saturn", house_number=7),
        ]
        chart = _make_chart(planets, lagna_rashi="pisces")
        result = _result(chart, "BPHS-COMP-005")
        assert result.is_present is False

    def test_dridha_yoga_present(self):
        """6th, 8th, 12th lords all in own houses."""
        # Gemini lagna: 6th=Scorpio(Mars), 8th=Capricorn(Saturn), 12th=Taurus(Venus)
        planets = [
            _make_planet("mars", house_number=6),
            _make_planet("saturn", house_number=8),
            _make_planet("venus", house_number=12),
        ]
        chart = _make_chart(planets, lagna_rashi="gemini")
        result = _result(chart, "BPHS-COMP-006")
        assert result.is_present is True

    def test_dridha_yoga_absent_one_wrong(self):
        planets = [
            _make_planet("mars", house_number=6),
            _make_planet("saturn", house_number=8),
            _make_planet("venus", house_number=1),  # not in 12th
        ]
        chart = _make_chart(planets, lagna_rashi="gemini")
        result = _result(chart, "BPHS-COMP-006")
        assert result.is_present is False

    def test_guru_mangala_present(self):
        """Jupiter-Mars association (conjunct)."""
        planets = [
            _make_planet("jupiter", house_number=3),
            _make_planet("mars", house_number=3),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-COMP-007")
        assert result is not None
        assert result.is_present is True  # conjunct in same house

    def test_guru_mangala_absent(self):
        chart = _make_chart([
            _make_planet("jupiter", house_number=3),
            _make_planet("mars", house_number=8),
        ])
        result = _result(chart, "BPHS-COMP-007")
        assert result is not None
        assert result.is_present is False


# =========================================================================
# Yoga Strength Scoring
# =========================================================================

class TestYogaStrength:

    def test_strength_zero_when_not_present(self):
        from apps.api.services.house_engine import HouseEngine
        from apps.api.services.yoga_predicates import YogaContext
        from apps.api.services.yoga_strength import compute_yoga_strength_score
        chart = _make_chart([])
        result = _result(chart, "BPHS-CY-001")
        ctx = YogaContext.build(chart, HouseEngine())
        score = compute_yoga_strength_score(ctx, result)
        assert score == 0

    def test_strength_nonzero_when_present(self):
        """evaluate_with_strength returns non-zero scores for present yogas."""
        planets = [
            _make_planet("moon", house_number=1),
            _make_planet("mars", house_number=2),  # Sunapha present
        ]
        chart = _make_chart(planets)
        results = YogaEngine().evaluate_with_strength(chart)
        sunapha = [r for r in results if r.yoga_id == "BPHS-CY-001"]
        assert len(sunapha) == 1
        assert sunapha[0].is_present is True
        assert sunapha[0].strength_score is not None
        assert sunapha[0].strength_score > 0

    def test_evaluate_with_strength_populates_score(self):
        planets = [
            _make_planet("moon", house_number=1),
            _make_planet("mars", house_number=2),
        ]
        chart = _make_chart(planets)
        results = YogaEngine().evaluate_with_strength(chart)
        for r in results:
            assert isinstance(r.strength_score, int) or r.strength_score is None
            if r.is_present:
                assert r.strength_score is not None
                assert r.strength_score >= 0
            else:
                assert r.strength_score == 0

    def test_strength_score_is_between_0_and_100(self):
        planets = [
            _make_planet("moon", house_number=1),
            _make_planet("mars", house_number=2),
        ]
        chart = _make_chart(planets)
        results = YogaEngine().evaluate_with_strength(chart)
        for r in results:
            if r.strength_score is not None:
                assert 0 <= r.strength_score <= 100, f"{r.yoga_id}: score={r.strength_score}"


# =========================================================================
# Yoga Counter-Examples
# =========================================================================

class TestYogaCounterExamples:

    def test_nabhasa_counter_examples_when_present(self):
        """Nabhasa Sankhya yogas provide counter-examples when present."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo"])
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-NY-005")  # Pasha (span <= 5)
        assert result.is_present is True
        assert len(result.counter_examples) > 0

    def test_arishta_counter_examples_when_present(self):
        """Arishta Phase 2 yogas provide counter-examples when present."""
        planets = [
            _make_planet("sun", house_number=1),
            _make_planet("mars", house_number=4),
            _make_planet("saturn", house_number=7),
            _make_planet("jupiter", house_number=5),
            _make_planet("venus", house_number=9),
            _make_planet("mercury", house_number=2),
            _make_planet("moon", house_number=10),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-ARY-006")
        assert result.is_present is True
        assert len(result.counter_examples) > 0

    def test_composite_counter_examples_when_present(self):
        """Composite yogas provide counter-examples when present."""
        planets = [
            _make_planet("jupiter", house_number=1),
            _make_planet("venus", house_number=4),
            _make_planet("mercury", house_number=7),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-COMP-002")
        assert result.is_present is True
        assert len(result.counter_examples) > 0

    def test_chandra_counter_examples_when_present(self):
        """Chandra Phase 2 yogas provide counter-examples when present."""
        planets = [
            _make_planet("sun", "aries", house_number=3),
            _make_planet("moon", "aries", house_number=3),
        ]
        chart = _make_chart(planets)
        result = _result(chart, "BPHS-CY-007")
        assert result.is_present is True
        assert len(result.counter_examples) > 0


# =========================================================================
# Yoga Registration — all new IDs present
# =========================================================================

class TestYogaRegistration:

    def test_all_new_nabhasa_yogas_registered(self):
        """All Sankhya, Akriti, Dala yogas exist in registry."""
        new_ids = [
            "BPHS-NY-004", "BPHS-NY-005", "BPHS-NY-006", "BPHS-NY-007",
            "BPHS-NY-008", "BPHS-NY-009", "BPHS-NY-010", "BPHS-NY-011",
            "BPHS-NY-012", "BPHS-NY-013", "BPHS-NY-014", "BPHS-NY-015",
            "BPHS-NY-016", "BPHS-NY-017", "BPHS-NY-018",
        ]
        from apps.api.services.yoga_registry import get_yoga
        for yoga_id in new_ids:
            definition = get_yoga(yoga_id)
            assert definition is not None, f"{yoga_id} not registered"

    def test_all_new_chandra_yogas_registered(self):
        """Amavasya and Vyatipata exist."""
        from apps.api.services.yoga_registry import get_yoga
        assert get_yoga("BPHS-CY-007") is not None
        assert get_yoga("BPHS-CY-008") is not None

    def test_all_new_arishta_yogas_registered(self):
        """New Arishta IDs exist."""
        from apps.api.services.yoga_registry import get_yoga
        for yoga_id in ["BPHS-ARY-004", "BPHS-ARY-005", "BPHS-ARY-006",
                        "BPHS-ARY-007", "BPHS-ARY-008", "BPHS-ARY-009",
                        "BPHS-ARY-010", "BPHS-ARY-011"]:
            assert get_yoga(yoga_id) is not None, f"{yoga_id} not registered"

    def test_all_composite_yogas_registered(self):
        """Composite yoga IDs exist."""
        from apps.api.services.yoga_registry import get_yoga
        for yoga_id in ["BPHS-COMP-001", "BPHS-COMP-002", "BPHS-COMP-003",
                        "BPHS-COMP-004", "BPHS-COMP-005", "BPHS-COMP-006",
                        "BPHS-COMP-007"]:
            assert get_yoga(yoga_id) is not None, f"{yoga_id} not registered"

    def test_present_yogas_include_phase2(self):
        """evaluate_all returns Phase 2 yogas too."""
        planets = _all_in(["aries", "taurus", "gemini", "cancer", "leo"])
        chart = _make_chart(planets)
        results = YogaEngine().evaluate_all(chart)
        ids = [r.yoga_id for r in results]
        assert "BPHS-NY-005" in ids  # Pasha
        assert "BPHS-COMP-003" in ids  # Harsha

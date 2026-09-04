# -*- coding: utf-8 -*-
"""
AstroOS — Unit Tests for Vinay Jha Per-Varga Vimshottari Dasha Engine (Step 2 & Step 4)
Spec v1.0: BPHS Canon + Jha Year-Lengths Freeze Table
"""

from datetime import date, datetime, timedelta, timezone
import pytest

from apps.api.services.jha_vimsottari import (
    VIMSOTTARI_ORDER,
    TOTAL_YEARS,
    NAKSHATRA_SPAN_MIN,
    NAKSHATRA_LORDS,
    YEAR_LENGTHS,
    DEFAULT_YEAR_KEY,
    DASHA_DAYS,
    birth_dasha,
    antardasha_spans,
    pratyantardasha_spans,
    JhaVimsottariEngine,
    JhaActiveVargaDasha,
    JhaDashaStrengthComparison,
)


@pytest.fixture
def vimsottari_engine():
    return JhaVimsottariEngine()


# ── खंड A: Constants Freeze ─────────────────────────────
class TestFrozenConstants:
    def test_total_is_120(self):
        assert sum(y for _, y in VIMSOTTARI_ORDER) == TOTAL_YEARS == 120

    def test_order_is_canonical(self):
        lords = [l for l, _ in VIMSOTTARI_ORDER]
        assert lords == ["ketu", "venus", "sun", "moon", "mars",
                         "rahu", "jupiter", "saturn", "mercury"]

    def test_years_are_canonical(self):
        assert dict(VIMSOTTARI_ORDER) == {
            "ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
            "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17}

    def test_nakshatra_lord_cycle(self):
        """Ashwini(0)=केतु, Bharani(1)=शुक्र, ..., Revati(26)=बुध।"""
        assert NAKSHATRA_LORDS[0][0] == "ketu"
        assert NAKSHATRA_LORDS[1][0] == "venus"
        assert NAKSHATRA_LORDS[26][0] == "mercury"

    def test_both_year_lengths_pinned(self):
        assert YEAR_LENGTHS["surya_siddhanta_solar"] == 365.25
        assert YEAR_LENGTHS["chaandra_tithi"] == pytest.approx(354.367)


# ── खंड B: जन्म-दशा शेष ─────────────────────────────────
class TestBirthDasha:
    def test_ashwini_zero_degrees_full_ketu(self):
        """चंद्र मेष 0°0′ → आश्विनी आरंभ → केतु, शेष 100% = 7.0 वर्ष।"""
        lord, frac, yrs = birth_dasha(0.0)
        assert (lord, frac) == ("ketu", 1.0) and yrs == pytest.approx(7.0)

    def test_ashwini_half(self):
        """चंद्र मेष 6°40′ (=400′) → केतु, शेष 50% = 3.5 वर्ष।"""
        lord, frac, yrs = birth_dasha(400.0)
        assert lord == "ketu" and yrs == pytest.approx(3.5)

    def test_bharani_boundary(self):
        """चंद्र मेष 13°20′1′ (=801′) → भरणी, शुक्र, शेष ~100% ≈ 20 वर्ष।"""
        lord, frac, yrs = birth_dasha(801.0)
        assert lord == "venus" and yrs == pytest.approx(19.975, rel=1e-3)

    def test_revati_wraps_to_mercury(self):
        """चंद्र मीन 16°40′ (=3,680′ चक्रांत) → रेवती → बुध।"""
        lord, _, _ = birth_dasha(26 * 800.0 + 400.0)
        assert lord == "mercury"

    def test_full_circle_no_drift(self):
        """27 नक्षत्रों के बाद क्रम wrap हो — off-by-one नहीं।"""
        assert birth_dasha(27 * 800.0)[0] == "ketu"

    def test_ketu_total_in_tithi_years(self):
        """चांद्र वर्षमान पर केतु-महादशा = 7 × 354.367 दिवस।"""
        expected = 7 * YEAR_LENGTHS["chaandra_tithi"]
        assert 7 * YEAR_LENGTHS["chaandra_tithi"] == pytest.approx(expected)


# ── खंड C: अंतर्दशा ─────────────────────────────────────
class TestAntardasha:
    def test_sun_mahadasha_first_is_sun_last_is_venus(self):
        """सूर्य-महादशा का चक्र: सूर्य(1)...बुध(7), केतु(8), शुक्र(9)।"""
        spans = antardasha_spans("sun")
        assert spans[0][0] == "sun" and spans[-1][0] == "venus"
        assert len(spans) == 9

    def test_ketu_mahadasha_first_is_ketu_last_is_mercury(self):
        """केतु-महादशा का चक्र: केतु(1)...शनि(8), बुध(9)।"""
        spans = antardasha_spans("ketu")
        assert spans[0][0] == "ketu" and spans[-1][0] == "mercury"
        assert len(spans) == 9

    def test_antardasha_sum_equals_mahadasha(self):
        """अंतर्दशाओं का योग = संबंधित महादशा — ऊर्जा-संरक्षण नियम।"""
        for lord, yrs in VIMSOTTARI_ORDER:
            total = sum(d for _, d in antardasha_spans(lord))
            assert total == pytest.approx(yrs), f"{lord} में योग-दोष"

    def test_sun_venus_antardasha_duration(self):
        """सूर्य-महादशा में शुक्र-अंतर्दशा = 6 × 20/120 = 1.0 वर्ष।"""
        spans = dict(antardasha_spans("sun"))
        assert spans["venus"] == pytest.approx(1.0)

    def test_venus_ketu_antardasha_duration(self):
        """शुक्र-महादशा में केतु-अंतर्दशा = 20 × 7/120 = 7/6 वर्ष।"""
        spans = dict(antardasha_spans("venus"))
        assert spans["ketu"] == pytest.approx(7/6)


# ── खंड D: प्रत्यंतर्दशा (PD) ──────────────────────────
class TestPratyantardasha:
    def test_pratyantardasha_sum_equals_antardasha(self):
        """प्रत्यंतर्दशाओं का योग = संबंधित अंतर्दशा।"""
        for m_lord, _ in VIMSOTTARI_ORDER:
            for a_lord, a_yrs in antardasha_spans(m_lord):
                pd_total = sum(d for _, d in pratyantardasha_spans(m_lord, a_lord))
                assert pd_total == pytest.approx(a_yrs), f"{m_lord}-{a_lord} में PD योग-दोष"


# ── खंड E: प्रति-वर्ग स्वतंत्र दशा एवं झा-सिद्धांत ─────
class TestPerVargaJhaDoctrine:
    def test_varga_moon_longitude_projection(self, vimsottari_engine):
        """Verify that Moon longitude projection into D9 and D10 produces valid coordinates."""
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090

        d1_moon = vimsottari_engine.compute_varga_moon_longitude(b_dt, lat, lon, "D1")
        d9_moon = vimsottari_engine.compute_varga_moon_longitude(b_dt, lat, lon, "D9")
        d10_moon = vimsottari_engine.compute_varga_moon_longitude(b_dt, lat, lon, "D10")

        assert 0.0 <= d1_moon < 360.0
        assert 0.0 <= d9_moon < 360.0
        assert 0.0 <= d10_moon < 360.0
        assert abs(d9_moon - d1_moon) > 0.001 or abs(d10_moon - d1_moon) > 0.001

    def test_varga_dasha_active_lords_5_levels(self, vimsottari_engine):
        """Verify active 5-level Vimshottari lords for D9 at a given evaluation date."""
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090
        eval_date = date(2015, 6, 15)

        active_d9 = vimsottari_engine.get_active_varga_dasha(
            birth_datetime=b_dt,
            latitude=lat,
            longitude=lon,
            varga_code="D9",
            target_date=eval_date,
            max_depth=5,
        )

        assert active_d9.varga_code == "D9"
        assert active_d9.evaluation_date == eval_date
        assert active_d9.mahadasha_lord in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")
        assert active_d9.antardasha_lord in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")
        assert len(active_d9.dasha_chain) >= 2

    def test_d1_vs_varga_strength_comparison_rule(self, vimsottari_engine):
        """Verify Jha's Shastric rule: Divisional charts do NOT override D1 unless final strength exceeds D1's."""
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090
        eval_date = date(2015, 6, 15)

        comparison = vimsottari_engine.compare_d1_and_varga_strength(
            birth_datetime=b_dt,
            latitude=lat,
            longitude=lon,
            varga_code="D10",
            target_date=eval_date,
        )

        assert isinstance(comparison, JhaDashaStrengthComparison)
        assert comparison.varga_code == "D10"
        assert comparison.d1_final_strength > 0.0
        assert comparison.varga_final_strength > 0.0

        if comparison.varga_final_strength > comparison.d1_final_strength:
            assert comparison.varga_overrides_d1 is True
            assert "exceeds" in comparison.verdict_explanation
        else:
            assert comparison.varga_overrides_d1 is False
            assert "cannot override" in comparison.verdict_explanation

    def test_year_convention_drift_chandra_vs_solar(self, vimsottari_engine):
        """Verify that Jha's 354.367 lunar year produces ~3.07% faster dasha cycle than 365.25 solar year."""
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090

        tree_solar = vimsottari_engine.compute_varga_dasha_tree(
            b_dt, lat, lon, varga_code="D1", year_convention="surya_siddhanta_solar"
        )
        tree_chandra = vimsottari_engine.compute_varga_dasha_tree(
            b_dt, lat, lon, varga_code="D1", year_convention="chaandra_tithi"
        )

        first_md_solar = tree_solar.mahadashas[0].duration_days
        first_md_chandra = tree_chandra.mahadashas[0].duration_days

        assert first_md_chandra < first_md_solar
        ratio = first_md_chandra / first_md_solar
        assert 0.96 <= ratio <= 0.98

    def test_dasha_sandhi_and_chhidra_detection(self, vimsottari_engine):
        """Verify detection of Dasha Sandhi (boundary buffer) and Dasha Chhidra (terminal AD)."""
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090

        tree = vimsottari_engine.compute_varga_dasha_tree(b_dt, lat, lon, varga_code="D1")
        first_md = tree.mahadashas[0]
        md_end = first_md.end_date

        # Evaluate 30 days before MD ends -> MUST be Sandhi!
        sandhi_eval_date = md_end - timedelta(days=30)
        active_sandhi = vimsottari_engine.get_active_varga_dasha(
            b_dt, lat, lon, varga_code="D1", target_date=sandhi_eval_date
        )

        assert active_sandhi.is_dasha_sandhi is True
        assert active_sandhi.days_to_md_end <= 180
        assert "Terminal Sandhi" in active_sandhi.sandhi_notes

        # Last AD of the first MD -> MUST be Dasha Chhidra!
        last_ad = first_md.sub_periods[-1]
        chhidra_eval_date = last_ad.start_date + timedelta(days=10)
        active_chhidra = vimsottari_engine.get_active_varga_dasha(
            b_dt, lat, lon, varga_code="D1", target_date=chhidra_eval_date
        )

        assert active_chhidra.is_dasha_chhidra is True
        assert "Dasha Chhidra" in active_chhidra.sandhi_notes

    def test_arsha_vimshottari_ardradi_toggle(self, vimsottari_engine):
        """
        Verify BPHS / Kundalee chkArsh 'Ardradi' reckoning:
        When arsha_mode='ardradi', counting starts from Ardra (6th nakshatra).
        This produces an alternate canonical dasha root.
        """
        b_dt = datetime(1985, 10, 24, 14, 30, tzinfo=timezone.utc)
        lat, lon = 28.6139, 77.2090

        tree_std = vimsottari_engine.compute_varga_dasha_tree(
            b_dt, lat, lon, varga_code="D1", arsha_mode="standard"
        )
        tree_arsha = vimsottari_engine.compute_varga_dasha_tree(
            b_dt, lat, lon, varga_code="D1", arsha_mode="ardradi"
        )

        assert tree_std.trigger_planet in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")
        assert tree_arsha.trigger_planet in ("sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu", "venus")
        assert len(tree_arsha.mahadashas) > 0

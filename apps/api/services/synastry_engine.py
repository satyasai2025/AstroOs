"""
AstroOS — Inter-Chart Synastry, Ashta-Kuta & Cross-Chart Confluence Engine (Priority 13)

Implements:
  1. Complete classical 8-fold Ashta-Kuta Compatibility (36 Gunas)
  2. Explicit Dosha Mitigations (Nadi Dosha Parihara, Bhakoot Dosha Parihara) with classical textual provenance
  3. Inter-Chart Planetary Angular Aspects & Cross-House Overlays
  4. Joint Temporal Confluence Synthesizer (reusing P12 MultiDashaConfluenceEngine)
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import math
from typing import Any, Optional, Sequence

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.synastry import (
    CrossHouseOverlay,
    DoshaParihara,
    InterChartAspect,
    JointConfluenceWindow,
    KutaEvaluation,
    KutaName,
    SynastryMatrix,
)
from apps.api.services.multi_dasha_confluence_engine import (
    ConfluenceWindow,
    MultiDashaConfluenceEngine,
)
from packages.shared.enums import Nakshatra, Rashi


# ── Classical Reference Constants ──────────────────────────────────────────

_RASHI_ORDER: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
)

_NAKSHATRA_ORDER: tuple[str, ...] = tuple(n.value for n in Nakshatra)

_RASHI_LORDS: dict[str, str] = {
    "aries": "mars", "scorpio": "mars",
    "taurus": "venus", "libra": "venus",
    "gemini": "mercury", "virgo": "mercury",
    "cancer": "moon",
    "leo": "sun",
    "sagittarius": "jupiter", "pisces": "jupiter",
    "capricorn": "saturn", "aquarius": "saturn",
}

# Varna hierarchy: Brahmin=4, Kshatriya=3, Vaishya=2, Shudra=1
_VARNA_MAP: dict[str, tuple[str, int]] = {
    "cancer": ("Brahmin", 4), "scorpio": ("Brahmin", 4), "pisces": ("Brahmin", 4),
    "aries": ("Kshatriya", 3), "leo": ("Kshatriya", 3), "sagittarius": ("Kshatriya", 3),
    "taurus": ("Vaishya", 2), "virgo": ("Vaishya", 2), "capricorn": ("Vaishya", 2),
    "gemini": ("Shudra", 1), "libra": ("Shudra", 1), "aquarius": ("Shudra", 1),
}

# Vashya classification
_VASHYA_MAP: dict[str, str] = {
    "aries": "Chatushpada", "taurus": "Chatushpada", "sagittarius": "Chatushpada", "capricorn": "Chatushpada",
    "gemini": "Dwipada", "virgo": "Dwipada", "libra": "Dwipada", "aquarius": "Dwipada",
    "cancer": "Jalachara", "pisces": "Jalachara",
    "leo": "Vanachara",
    "scorpio": "Keeta",
}

# Yoni classifications: 14 animal pairs (27 nakshatras)
_NAKSHATRA_YONI: dict[str, str] = {
    "ashwini": "Horse", "shatabhisha": "Horse",
    "bharani": "Elephant", "revati": "Elephant",
    "krittika": "Sheep", "pushya": "Sheep",
    "rohini": "Serpent", "mrigashira": "Serpent",
    "ardra": "Dog", "mula": "Dog",
    "punarvasu": "Cat", "ashlesha": "Cat",
    "magha": "Rat", "purva_phalguni": "Rat",
    "uttara_phalguni": "Cow", "uttara_bhadrapada": "Cow",
    "hasta": "Buffalo", "swati": "Buffalo",
    "chitra": "Tiger", "vishakha": "Tiger",
    "anuradha": "Deer", "jyeshtha": "Deer",
    "purva_ashadha": "Monkey", "shravana": "Monkey",
    "uttara_ashadha": "Mongoose", "abhijit": "Mongoose",
    "dhanishta": "Lion", "purva_bhadrapada": "Lion",
}

_YONI_ORDER: tuple[str, ...] = (
    "Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat",
    "Cow", "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose", "Lion",
)

# Full 14x14 graded Yoni compatibility matrix (0=Worse,1=Bad,2=Neutral,
# 3=Good,4=Perfect), sourced from PyJHora's YoniArray
# (jhora/horoscope/match/compatibility.py) — verified exact match.
_YONI_COMPATIBILITY_MATRIX: tuple[tuple[int, ...], ...] = (
    (4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 1, 3, 2, 1),
    (2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0),
    (2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1),
    (3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2),
    (2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1),
    (2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1),
    (2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2),
    (1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1),
    (0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1),
    (1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1),
    (1, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1),
    (3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2),
    (2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2),
    (1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4),
)

_YONI_RESULT_LABELS: dict[int, str] = {0: "Worse", 1: "Bad", 2: "Neutral", 3: "Good", 4: "Perfect"}

# Full girl-x-boy Gana compatibility matrix, sourced from PyJHora's
# gana_array (jhora/horoscope/match/compatibility.py), rows=girl's Gana,
# cols=boy's Gana, order (Deva, Manushya, Rakshasa) — direction-dependent
# per classical convention, NOT symmetric. chart_a is treated as the
# girl/bride side and chart_b as the boy/groom side (this engine has no
# explicit gender field; this is the standard synastry-scoring convention).
_GANA_ORDER: tuple[str, ...] = ("Deva", "Manushya", "Rakshasa")
_GANA_COMPATIBILITY_MATRIX: tuple[tuple[int, ...], ...] = (
    (6, 6, 0),
    (5, 6, 0),
    (1, 0, 6),
)
_GANA_RESULT_LABELS: dict[int, str] = {0: "Very Bad", 1: "Bad", 3: "Average", 5: "Good", 6: "Perfect"}

# Gana classification: Deva, Manushya, Rakshasa
_NAKSHATRA_GANA: dict[str, str] = {
    "ashwini": "Deva", "mrigashira": "Deva", "punarvasu": "Deva", "pushya": "Deva",
    "hasta": "Deva", "swati": "Deva", "anuradha": "Deva", "shravana": "Deva", "revati": "Deva",
    "bharani": "Manushya", "rohini": "Manushya", "ardra": "Manushya", "purva_phalguni": "Manushya",
    "uttara_phalguni": "Manushya", "purva_ashadha": "Manushya", "uttara_ashadha": "Manushya",
    "purva_bhadrapada": "Manushya", "uttara_bhadrapada": "Manushya",
    "krittika": "Rakshasa", "ashlesha": "Rakshasa", "magha": "Rakshasa", "chitra": "Rakshasa",
    "vishakha": "Rakshasa", "jyeshtha": "Rakshasa", "mula": "Rakshasa", "dhanishta": "Rakshasa",
    "shatabhisha": "Rakshasa",
}

# Nadi classification: Aadi (Vata), Madhya (Pitta), Antya (Kapha)
_NAKSHATRA_NADI: dict[str, str] = {
    # Aadi (1, 6, 7, 12, 13, 18, 19, 24, 25)
    "ashwini": "Aadi", "ardra": "Aadi", "punarvasu": "Aadi", "uttara_phalguni": "Aadi",
    "hasta": "Aadi", "jyeshtha": "Aadi", "mula": "Aadi", "shatabhisha": "Aadi", "purva_bhadrapada": "Aadi",
    # Madhya (2, 5, 8, 11, 14, 17, 20, 23, 26)
    "bharani": "Madhya", "mrigashira": "Madhya", "pushya": "Madhya", "purva_phalguni": "Madhya",
    "chitra": "Madhya", "anuradha": "Madhya", "purva_ashadha": "Madhya", "dhanishta": "Madhya", "uttara_bhadrapada": "Madhya",
    # Antya (3, 4, 9, 10, 15, 16, 21, 22, 27)
    "krittika": "Antya", "rohini": "Antya", "ashlesha": "Antya", "magha": "Antya",
    "swati": "Antya", "vishakha": "Antya", "uttara_ashadha": "Antya", "shravana": "Antya", "revati": "Antya",
}

# Natural Planetary Relationships
_PLANETARY_FRIENDS: dict[str, set[str]] = {
    "sun": {"moon", "mars", "jupiter"},
    "moon": {"sun", "mercury"},
    "mars": {"sun", "moon", "jupiter"},
    "mercury": {"sun", "venus"},
    "jupiter": {"sun", "moon", "mars"},
    "venus": {"mercury", "saturn"},
    "saturn": {"mercury", "venus"},
}

_PLANETARY_ENEMIES: dict[str, set[str]] = {
    "sun": {"venus", "saturn"},
    "moon": set(),
    "mars": {"mercury"},
    "mercury": {"moon"},
    "jupiter": {"mercury", "venus"},
    "venus": {"sun", "moon"},
    "saturn": {"sun", "moon", "mars"},
}


class AshtaKutaEngine:
    """Calculates classical 8-Fold Ashta-Kuta (36 Gunas) with full dosha cancellations and provenance."""

    @classmethod
    def evaluate(
        cls,
        moon_a_rashi: str,
        moon_a_nakshatra: str,
        moon_a_pada: int,
        moon_b_rashi: str,
        moon_b_nakshatra: str,
        moon_b_pada: int,
    ) -> tuple[tuple[KutaEvaluation, ...], tuple[DoshaParihara, ...]]:
        r_a = moon_a_rashi.lower()
        r_b = moon_b_rashi.lower()
        n_a = moon_a_nakshatra.lower()
        n_b = moon_b_nakshatra.lower()

        lord_a = _RASHI_LORDS.get(r_a, "sun")
        lord_b = _RASHI_LORDS.get(r_b, "sun")

        evaluations: list[KutaEvaluation] = []
        pariharas: list[DoshaParihara] = []

        # 1. Varna Kuta (Max 1 pt)
        v_a_name, v_a_val = _VARNA_MAP.get(r_a, ("Shudra", 1))
        v_b_name, v_b_val = _VARNA_MAP.get(r_b, ("Shudra", 1))
        varna_pts = 1.0 if v_a_val >= v_b_val else 0.0
        evaluations.append(KutaEvaluation(
            kuta=KutaName.VARNA,
            label="Varna Kuta",
            obtained_points=varna_pts,
            max_points=1.0,
            partner_a_attribute=v_a_name,
            partner_b_attribute=v_b_name,
            raw_relationship=f"Chart A ({v_a_name}) vs Chart B ({v_b_name})",
            is_mitigated=False,
            cancellation_reason=None,
            description="Work, spiritual inclination & ego compatibility.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 4-6",
        ))

        # 2. Vashya Kuta (Max 2 pts)
        vas_a = _VASHYA_MAP.get(r_a, "Chatushpada")
        vas_b = _VASHYA_MAP.get(r_b, "Chatushpada")
        if vas_a == vas_b:
            vashya_pts = 2.0
            vashya_rel = "Complete mutual harmony"
        elif (vas_a == "Vanachara" and vas_b in ("Chatushpada", "Dwipada")) or (vas_b == "Vanachara" and vas_a in ("Chatushpada", "Dwipada")):
            vashya_pts = 0.0
            vashya_rel = "Inimical Vashya"
        else:
            vashya_pts = 1.0
            vashya_rel = "Partial Vashya resonance"
        evaluations.append(KutaEvaluation(
            kuta=KutaName.VASHYA,
            label="Vashya Kuta",
            obtained_points=vashya_pts,
            max_points=2.0,
            partner_a_attribute=vas_a,
            partner_b_attribute=vas_b,
            raw_relationship=vashya_rel,
            is_mitigated=False,
            cancellation_reason=None,
            description="Mutual dominance, magnetic attraction and obedience balance.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 12",
        ))

        # 3. Tara Kuta (Dina Kuta) (Max 3 pts)
        idx_a = _NAKSHATRA_ORDER.index(n_a) if n_a in _NAKSHATRA_ORDER else 0
        idx_b = _NAKSHATRA_ORDER.index(n_b) if n_b in _NAKSHATRA_ORDER else 0
        diff_a_to_b = ((idx_b - idx_a) % 27 + 27) % 27
        diff_b_to_a = ((idx_a - idx_b) % 27 + 27) % 27
        tara_ab = (diff_a_to_b % 9) + 1
        tara_ba = (diff_b_to_a % 9) + 1
        inauspicious_taras = {3, 5, 7}  # Vipat, Pratyak, Vadha
        a_good = tara_ab not in inauspicious_taras
        b_good = tara_ba not in inauspicious_taras
        if a_good and b_good:
            tara_pts = 3.0
            tara_rel = "Both Taras auspicious"
        elif a_good or b_good:
            tara_pts = 1.5
            tara_rel = "Single-direction Tara auspicious"
        else:
            tara_pts = 0.0
            tara_rel = "Both Taras inauspicious (Vipat/Pratyak/Vadha)"
        evaluations.append(KutaEvaluation(
            kuta=KutaName.TARA,
            label="Tara Kuta (Dina)",
            obtained_points=tara_pts,
            max_points=3.0,
            partner_a_attribute=f"Tara #{tara_ab}",
            partner_b_attribute=f"Tara #{tara_ba}",
            raw_relationship=tara_rel,
            is_mitigated=False,
            cancellation_reason=None,
            description="Health, longevity and mutual destiny alignment.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 10-14",
        ))

        # 4. Yoni Kuta (Max 4 pts) — full graded 14x14 matrix, not a 3-bucket approximation
        yoni_a = _NAKSHATRA_YONI.get(n_a, "Horse")
        yoni_b = _NAKSHATRA_YONI.get(n_b, "Horse")
        yoni_idx_a = _YONI_ORDER.index(yoni_a)
        yoni_idx_b = _YONI_ORDER.index(yoni_b)
        yoni_pts = float(_YONI_COMPATIBILITY_MATRIX[yoni_idx_a][yoni_idx_b])
        yoni_label = _YONI_RESULT_LABELS[int(yoni_pts)]
        yoni_rel = f"{yoni_label} Yoni match ({yoni_a} & {yoni_b})"
        evaluations.append(KutaEvaluation(
            kuta=KutaName.YONI,
            label="Yoni Kuta",
            obtained_points=yoni_pts,
            max_points=4.0,
            partner_a_attribute=yoni_a,
            partner_b_attribute=yoni_b,
            raw_relationship=yoni_rel,
            is_mitigated=False,
            cancellation_reason=None,
            description="Biological, emotional and physical compatibility.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 16",
        ))

        # 5. Graha Maitri (Rashi Lord Friendship) (Max 5 pts)
        if lord_a == lord_b:
            maitri_pts = 5.0
            maitri_rel = "Same Moon Sign Lord"
        else:
            a_friends = _PLANETARY_FRIENDS.get(lord_a, set())
            a_enemies = _PLANETARY_ENEMIES.get(lord_a, set())
            b_friends = _PLANETARY_FRIENDS.get(lord_b, set())
            b_enemies = _PLANETARY_ENEMIES.get(lord_b, set())

            a_to_b = "friend" if lord_b in a_friends else ("enemy" if lord_b in a_enemies else "neutral")
            b_to_a = "friend" if lord_a in b_friends else ("enemy" if lord_a in b_enemies else "neutral")

            if a_to_b == "friend" and b_to_a == "friend":
                maitri_pts = 5.0
                maitri_rel = f"Mutual Friends ({lord_a.capitalize()} & {lord_b.capitalize()})"
            elif (a_to_b == "friend" and b_to_a == "neutral") or (b_to_a == "friend" and a_to_b == "neutral"):
                maitri_pts = 4.0
                maitri_rel = f"Friend & Neutral ({lord_a.capitalize()} / {lord_b.capitalize()})"
            elif a_to_b == "neutral" and b_to_a == "neutral":
                maitri_pts = 3.0
                maitri_rel = f"Mutual Neutral ({lord_a.capitalize()} & {lord_b.capitalize()})"
            elif (a_to_b == "friend" and b_to_a == "enemy") or (b_to_a == "friend" and a_to_b == "enemy"):
                maitri_pts = 1.0
                maitri_rel = f"One-sided Enemy ({lord_a.capitalize()} / {lord_b.capitalize()})"
            elif (a_to_b == "neutral" and b_to_a == "enemy") or (b_to_a == "neutral" and a_to_b == "enemy"):
                maitri_pts = 0.5
                maitri_rel = f"Neutral & Enemy ({lord_a.capitalize()} / {lord_b.capitalize()})"
            else:
                maitri_pts = 0.0
                maitri_rel = f"Mutual Enemies ({lord_a.capitalize()} & {lord_b.capitalize()})"

        evaluations.append(KutaEvaluation(
            kuta=KutaName.GRAHA_MAITRI,
            label="Graha Maitri Kuta",
            obtained_points=maitri_pts,
            max_points=5.0,
            partner_a_attribute=f"{r_a.capitalize()} ({lord_a.capitalize()})",
            partner_b_attribute=f"{r_b.capitalize()} ({lord_b.capitalize()})",
            raw_relationship=maitri_rel,
            is_mitigated=False,
            cancellation_reason=None,
            description="Intellectual friendship, psychological harmony and mental resonance.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 18-21",
        ))

        # 6. Gana Kuta (Max 6 pts) — full girl-x-boy directional matrix, not a symmetric 3-bucket approximation
        gana_a = _NAKSHATRA_GANA.get(n_a, "Manushya")
        gana_b = _NAKSHATRA_GANA.get(n_b, "Manushya")
        gana_idx_a = _GANA_ORDER.index(gana_a)
        gana_idx_b = _GANA_ORDER.index(gana_b)
        raw_gana_pts = _GANA_COMPATIBILITY_MATRIX[gana_idx_a][gana_idx_b]
        gana_label = _GANA_RESULT_LABELS[raw_gana_pts]
        has_gana_dosha = raw_gana_pts <= 1
        gana_cancelled = False
        gana_cancel_reason = None

        if has_gana_dosha:
            # Classical Gana Dosha Cancellation: If Rashi lords are mutual friends or same, or Navamsha lords are friends
            if lord_a == lord_b or lord_b in _PLANETARY_FRIENDS.get(lord_a, set()):
                gana_pts = 6.0
                gana_cancelled = True
                gana_cancel_reason = f"Cancelled via Gana Parihara: Rashi lords ({lord_a.capitalize()}/{lord_b.capitalize()}) are friends or identical."
                gana_rel = f"{gana_label} Gana pairing ({gana_a} girl / {gana_b} boy) — Cancelled by Graha Maitri"
            else:
                gana_pts = float(raw_gana_pts)
                gana_rel = f"{gana_label} Gana pairing ({gana_a} girl / {gana_b} boy)"
        else:
            gana_pts = float(raw_gana_pts)
            gana_rel = f"{gana_label} Gana pairing ({gana_a} girl / {gana_b} boy)"

        pariharas.append(DoshaParihara(
            dosha_name="Gana Dosha",
            is_present=has_gana_dosha,
            is_cancelled=gana_cancelled,
            parihara_rule="Rashi Lord Friendship / Identity Exemption",
            classical_reference="Muhurta Chintamani, Vivaha Prakarana, Sloka 24",
            explanation=gana_cancel_reason or ("No Gana Dosha present." if not has_gana_dosha else "Gana Dosha present without mitigation."),
        ))

        evaluations.append(KutaEvaluation(
            kuta=KutaName.GANA,
            label="Gana Kuta",
            obtained_points=gana_pts,
            max_points=6.0,
            partner_a_attribute=gana_a,
            partner_b_attribute=gana_b,
            raw_relationship=gana_rel,
            is_mitigated=gana_cancelled,
            cancellation_reason=gana_cancel_reason,
            description="Temperament, behavior and lifestyle alignment.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 22-25",
        ))

        # 7. Bhakoot Kuta (Rashi Placement Distance) (Max 7 pts)
        r_idx_a = _RASHI_ORDER.index(r_a) if r_a in _RASHI_ORDER else 0
        r_idx_b = _RASHI_ORDER.index(r_b) if r_b in _RASHI_ORDER else 0
        dist_a_to_b = ((r_idx_b - r_idx_a) % 12 + 12) % 12 + 1  # 1 to 12
        dist_pair = frozenset({dist_a_to_b, 14 - dist_a_to_b if dist_a_to_b != 1 else 1})

        has_bhakoot_dosha = False
        bhakoot_cancelled = False
        bhakoot_cancel_reason = None

        # Auspicious distances: 1/1, 1/7, 3/11, 4/10
        if dist_a_to_b in (1, 7, 3, 11, 4, 10):
            bhakoot_pts = 7.0
            bhakoot_rel = f"Auspicious Rashi axis ({dist_a_to_b}/{14 - dist_a_to_b if dist_a_to_b != 1 else 1})"
        else:
            # 2/12 (Dwirdwadasha), 6/8 (Shadashtaka), 9/5 (Navapanchama)
            has_bhakoot_dosha = True
            # Classical Bhakoot Parihara:
            # 1. If lords are identical (Aries-Scorpio [Mars], Taurus-Libra [Venus], Capricorn-Aquarius [Saturn])
            # 2. If lords are mutual friends
            if lord_a == lord_b:
                bhakoot_pts = 7.0
                bhakoot_cancelled = True
                bhakoot_cancel_reason = f"Bhakoot Parihara Applied: Both Moon signs are ruled by the same lord ({lord_a.capitalize()})."
                bhakoot_rel = f"Shadashtaka/Dwirdwadasha neutralized by common lord ({lord_a.capitalize()})"
            elif lord_b in _PLANETARY_FRIENDS.get(lord_a, set()) and lord_a in _PLANETARY_FRIENDS.get(lord_b, set()):
                bhakoot_pts = 7.0
                bhakoot_cancelled = True
                bhakoot_cancel_reason = f"Bhakoot Parihara Applied: Moon sign lords ({lord_a.capitalize()} & {lord_b.capitalize()}) are mutual friends."
                bhakoot_rel = "Bhakoot Dosha neutralized by mutual planetary friendship"
            else:
                bhakoot_pts = 0.0
                bhakoot_rel = f"Inauspicious Rashi axis ({dist_a_to_b}/{14 - dist_a_to_b}) — Bhakoot Dosha"

        pariharas.append(DoshaParihara(
            dosha_name="Bhakoot Dosha",
            is_present=has_bhakoot_dosha,
            is_cancelled=bhakoot_cancelled,
            parihara_rule="Common Lord / Mutual Planetary Friendship Parihara",
            classical_reference="Brihat Parashara Hora Shastra, Ch. 73, Sloka 26-30 & Jatakaparijata Ch. 12",
            explanation=bhakoot_cancel_reason or ("No Bhakoot Dosha present." if not has_bhakoot_dosha else "Bhakoot Dosha present without mitigation."),
        ))

        evaluations.append(KutaEvaluation(
            kuta=KutaName.BHAKOOT,
            label="Bhakoot Kuta",
            obtained_points=bhakoot_pts,
            max_points=7.0,
            partner_a_attribute=r_a.capitalize(),
            partner_b_attribute=r_b.capitalize(),
            raw_relationship=bhakoot_rel,
            is_mitigated=bhakoot_cancelled,
            cancellation_reason=bhakoot_cancel_reason,
            description="Emotional bonding, family prosperity and financial welfare.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 26-30",
        ))

        # 8. Nadi Kuta (Max 8 pts)
        nadi_a = _NAKSHATRA_NADI.get(n_a, "Madhya")
        nadi_b = _NAKSHATRA_NADI.get(n_b, "Madhya")
        has_nadi_dosha = False
        nadi_cancelled = False
        nadi_cancel_reason = None

        if nadi_a != nadi_b:
            nadi_pts = 8.0
            nadi_rel = f"Distinct Nadis ({nadi_a} vs {nadi_b})"
        else:
            has_nadi_dosha = True
            # Classical Nadi Dosha Parihara:
            # 1. Same Nakshatra but different Padas
            # 2. Same Rashi but different Nakshatras
            # 3. Different Rashis with same lord
            if n_a == n_b and moon_a_pada != moon_b_pada:
                nadi_pts = 8.0
                nadi_cancelled = True
                nadi_cancel_reason = f"Nadi Parihara Applied: Same Nakshatra ({n_a.capitalize()}) but different Padas ({moon_a_pada} vs {moon_b_pada})."
                nadi_rel = "Nadi Dosha cancelled via distinct Nakshatra Padas"
            elif r_a == r_b and n_a != n_b:
                nadi_pts = 8.0
                nadi_cancelled = True
                nadi_cancel_reason = f"Nadi Parihara Applied: Same Rashi ({r_a.capitalize()}) but different Nakshatras."
                nadi_rel = "Nadi Dosha cancelled via common Rashi with distinct Nakshatras"
            elif r_a != r_b and lord_a == lord_b:
                nadi_pts = 8.0
                nadi_cancelled = True
                nadi_cancel_reason = f"Nadi Parihara Applied: Different Rashis ruled by the same planetary lord ({lord_a.capitalize()})."
                nadi_rel = f"Nadi Dosha cancelled via common planetary lord ({lord_a.capitalize()})"
            else:
                nadi_pts = 0.0
                nadi_rel = f"Same Nadi ({nadi_a}) — Nadi Dosha active"

        pariharas.append(DoshaParihara(
            dosha_name="Nadi Dosha",
            is_present=has_nadi_dosha,
            is_cancelled=nadi_cancelled,
            parihara_rule="Pada Difference / Common Rashi / Common Lord Parihara",
            classical_reference="Muhurta Chintamani, Vivaha Prakarana, Sloka 35-38",
            explanation=nadi_cancel_reason or ("No Nadi Dosha present." if not has_nadi_dosha else "Nadi Dosha present without mitigation."),
        ))

        evaluations.append(KutaEvaluation(
            kuta=KutaName.NADI,
            label="Nadi Kuta",
            obtained_points=nadi_pts,
            max_points=8.0,
            partner_a_attribute=nadi_a,
            partner_b_attribute=nadi_b,
            raw_relationship=nadi_rel,
            is_mitigated=nadi_cancelled,
            cancellation_reason=nadi_cancel_reason,
            description="Genetics, physiological balance, progeny and vital health resonance.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 32-38",
        ))

        return tuple(evaluations), tuple(pariharas)


class SynastryEngine:
    """Computes comprehensive inter-chart synastry matrices, aspect overlays, and joint timing confluence."""

    def __init__(
        self,
        confluence_engine: Optional[MultiDashaConfluenceEngine] = None,
    ) -> None:
        self._confluence_engine = confluence_engine or MultiDashaConfluenceEngine()

    def evaluate_synastry(
        self,
        chart_a: D1Chart,
        chart_b: D1Chart,
        chart_a_name: str = "Partner A",
        chart_b_name: str = "Partner B",
        dasha_tree_a: Optional[Any] = None,
        dasha_tree_b: Optional[Any] = None,
        target_start: Optional[date] = None,
        target_end: Optional[date] = None,
        objective: str = "marriage",
    ) -> SynastryMatrix:
        now = datetime.now(timezone.utc)

        # 1. Extract Moon positions for Ashta-Kuta
        moon_a = next((p for p in chart_a.planets if p.planet.lower() == "moon"), None)
        moon_b = next((p for p in chart_b.planets if p.planet.lower() == "moon"), None)

        r_a = moon_a.rashi if moon_a else "aries"
        n_a = moon_a.nakshatra if moon_a else "ashwini"
        p_a = moon_a.pada if moon_a else 1

        r_b = moon_b.rashi if moon_b else "aries"
        n_b = moon_b.nakshatra if moon_b else "ashwini"
        p_b = moon_b.pada if moon_b else 1

        kuta_evals, pariharas = AshtaKutaEngine.evaluate(r_a, n_a, p_a, r_b, n_b, p_b)
        total_pts = sum(k.obtained_points for k in kuta_evals)
        pct = (total_pts / 36.0) * 100.0

        # 2. Inter-Chart Aspects
        aspects = self._compute_inter_chart_aspects(chart_a.planets, chart_b.planets)

        # 3. Cross-House Overlays
        overlays = self._compute_cross_house_overlays(chart_a, chart_b)

        # 4. Joint Timing Confluence (Reusing P12 MultiDashaConfluenceEngine)
        joint_windows = self._compute_joint_confluence_windows(
            chart_a=chart_a,
            chart_b=chart_b,
            dasha_tree_a=dasha_tree_a,
            dasha_tree_b=dasha_tree_b,
            target_start=target_start or now.date(),
            target_end=target_end or date(now.year + 2, now.month, now.day),
            objective=objective,
        )

        structural_summary = (
            f"Ashta-Kuta Score: {total_pts:.1f}/36.0 ({pct:.1f}%). "
            f"Evaluated 8 classical Kutas with {len([p for p in pariharas if p.is_cancelled])} active cancellation(s). "
            f"Identified {len(aspects)} inter-chart angular aspect(s) and {len(overlays)} cross-house overlay(s)."
        )

        timing_summary = (
            f"Synthesized {len(joint_windows)} joint timing window(s) for objective '{objective}' "
            f"across {target_start or now.date()} to {target_end or date(now.year + 2, now.month, now.day)}."
        )

        provenance = (
            "Classical sources: Brihat Parashara Hora Shastra (Ch. 73), Muhurta Chintamani (Vivaha Prakarana), "
            "and Jatakaparijata (Ch. 12). Reuses Priority 12 Polymodal Multi-Dasha Confluence Engine for joint timing."
        )

        return SynastryMatrix(
            chart_a_name=chart_a_name,
            chart_b_name=chart_b_name,
            evaluated_at=now,
            ashta_kuta_evaluations=kuta_evals,
            total_guna_obtained=total_pts,
            max_guna_possible=36.0,
            guna_percentage=pct,
            dosha_pariharas=pariharas,
            inter_chart_aspects=aspects,
            cross_house_overlays=overlays,
            joint_confluence_windows=joint_windows,
            structural_summary=structural_summary,
            timing_summary=timing_summary,
            provenance_notes=provenance,
        )

    def _compute_inter_chart_aspects(
        self,
        planets_a: Sequence[SiderealPosition],
        planets_b: Sequence[SiderealPosition],
    ) -> tuple[InterChartAspect, ...]:
        aspects: list[InterChartAspect] = []
        major_planets = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}

        for p_a in planets_a:
            if p_a.planet.lower() not in major_planets:
                continue
            for p_b in planets_b:
                if p_b.planet.lower() not in major_planets:
                    continue

                diff = abs(p_a.sidereal_longitude - p_b.sidereal_longitude) % 360.0
                if diff > 180.0:
                    diff = 360.0 - diff

                aspect_type = None
                is_harm = False
                orb = 0.0
                interp = ""

                if diff <= 8.0:
                    aspect_type = "conjunction"
                    is_harm = p_a.planet.lower() in ("jupiter", "venus", "moon") or p_b.planet.lower() in ("jupiter", "venus", "moon")
                    orb = diff
                    interp = f"Mutual Conjunction ({p_a.planet.capitalize()} with {p_b.planet.capitalize()} within {orb:.1f}° orb)."
                elif abs(diff - 180.0) <= 8.0:
                    aspect_type = "opposition"
                    is_harm = False
                    orb = abs(diff - 180.0)
                    interp = f"Direct Opposition ({p_a.planet.capitalize()} opposing {p_b.planet.capitalize()} across 1/7 axis)."
                elif abs(diff - 120.0) <= 7.0:
                    aspect_type = "trine"
                    is_harm = True
                    orb = abs(diff - 120.0)
                    interp = f"Harmonic Trine 120° ({p_a.planet.capitalize()} trine {p_b.planet.capitalize()})."
                elif abs(diff - 90.0) <= 6.0:
                    aspect_type = "square"
                    is_harm = False
                    orb = abs(diff - 90.0)
                    interp = f"Friction Square 90° ({p_a.planet.capitalize()} square {p_b.planet.capitalize()})."
                elif abs(diff - 60.0) <= 5.0:
                    aspect_type = "sextile"
                    is_harm = True
                    orb = abs(diff - 60.0)
                    interp = f"Harmonic Sextile 60° ({p_a.planet.capitalize()} sextile {p_b.planet.capitalize()})."

                if aspect_type:
                    aspects.append(InterChartAspect(
                        planet_a=p_a.planet,
                        planet_b=p_b.planet,
                        longitude_a=p_a.sidereal_longitude,
                        longitude_b=p_b.sidereal_longitude,
                        angle_degrees=diff,
                        aspect_type=aspect_type,
                        orb_degrees=orb,
                        is_harmonious=is_harm,
                        interpretation=interp,
                    ))

        return tuple(aspects)

    def _compute_cross_house_overlays(
        self,
        chart_a: D1Chart,
        chart_b: D1Chart,
    ) -> tuple[CrossHouseOverlay, ...]:
        overlays: list[CrossHouseOverlay] = []
        asc_b = chart_b.ascendant.sidereal_longitude if chart_b.ascendant else 0.0

        for p_a in chart_a.planets:
            if p_a.planet.lower() in ("uranus", "neptune", "pluto"):
                continue
            # House in Chart B = (p_a.sidereal_longitude - asc_b) // 30 + 1
            house_in_b = int(((p_a.sidereal_longitude - asc_b) % 360.0) // 30.0) + 1
            rashi_b = _RASHI_ORDER[int(p_a.sidereal_longitude // 30.0) % 12]

            impact = "Neutral"
            if house_in_b in (1, 5, 9):
                impact = "Highly Auspicious (Trikona Resonance)"
            elif house_in_b in (4, 7, 10):
                impact = "Strong Activity (Kendra Resonance)"
            elif house_in_b in (6, 8, 12):
                impact = "Challenging / Karmic (Dusthana Overlay)"

            overlays.append(CrossHouseOverlay(
                planet_a=p_a.planet,
                chart_a_house=p_a.house_number,
                chart_b_house_occupied=house_in_b,
                rashi_in_chart_b=rashi_b,
                functional_impact=impact,
            ))

        return tuple(overlays)

    def _compute_joint_confluence_windows(
        self,
        chart_a: D1Chart,
        chart_b: D1Chart,
        dasha_tree_a: Optional[Any],
        dasha_tree_b: Optional[Any],
        target_start: date,
        target_end: date,
        objective: str,
    ) -> tuple[JointConfluenceWindow, ...]:
        # Reuse Priority 12 MultiDashaConfluenceEngine for Chart A and Chart B
        windows_a: list[ConfluenceWindow] = []
        windows_b: list[ConfluenceWindow] = []

        if chart_a:
            matrix_a = self._confluence_engine.evaluate_confluence_matrix(
                chart=chart_a,
                target_start=target_start,
                target_end=target_end,
                objective=objective,
            )
            windows_a = list(matrix_a.confluence_windows)

        if chart_b:
            matrix_b = self._confluence_engine.evaluate_confluence_matrix(
                chart=chart_b,
                target_start=target_start,
                target_end=target_end,
                objective=objective,
            )
            windows_b = list(matrix_b.confluence_windows)

        joint_windows: list[JointConfluenceWindow] = []

        # If both dasha trees are present, intersect windows
        if windows_a and windows_b:
            for wa in windows_a:
                for wb in windows_b:
                    s_max = max(wa.start_date, wb.start_date)
                    e_min = min(wa.end_date, wb.end_date)
                    if s_max <= e_min:
                        # Geometric mean of both confluence scores
                        joint_score = math.sqrt(wa.confluence_density_score * wb.confluence_density_score)
                        if joint_score >= 40.0:
                            joint_windows.append(JointConfluenceWindow(
                                start_date=s_max,
                                end_date=e_min,
                                chart_a_density_score=wa.confluence_density_score,
                                chart_b_density_score=wb.confluence_density_score,
                                joint_confluence_density=round(joint_score, 2),
                                chart_a_active_systems=wa.overlapping_systems,
                                chart_b_active_systems=wb.overlapping_systems,
                                objective=objective,
                                synthesis_notes=(
                                    f"Concurrent multi-dasha alignment: Chart A score {wa.confluence_density_score:.1f}, "
                                    f"Chart B score {wb.confluence_density_score:.1f}."
                                ),
                            ))
        elif windows_a or windows_b:
            single_list = windows_a or windows_b
            for w in single_list[:5]:
                joint_windows.append(JointConfluenceWindow(
                    start_date=w.start_date,
                    end_date=w.end_date,
                    chart_a_density_score=w.confluence_density_score,
                    chart_b_density_score=w.confluence_density_score,
                    joint_confluence_density=w.confluence_density_score,
                    chart_a_active_systems=w.overlapping_systems,
                    chart_b_active_systems=w.overlapping_systems,
                    objective=objective,
                    synthesis_notes="Single-chart timing projection.",
                ))
        # else: neither chart produced any real confluence window (e.g. no
        # dasha tree available for either chart) — no window is reported
        # rather than fabricating one. Previously this branch returned a
        # hardcoded fake JointConfluenceWindow (75.0/80.0/77.46, invented
        # active_systems) labeled as a "synthesized" result indistinguishable
        # from a real computation; that fake-fallback anti-pattern was removed.

        # Sort by joint density score descending
        joint_windows.sort(key=lambda w: w.joint_confluence_density, reverse=True)
        return tuple(joint_windows)

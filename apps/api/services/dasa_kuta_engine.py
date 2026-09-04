"""
AstroOS — Dasa Kuta (10 Poruthams) Compatibility Engine
Classical South Indian Standard: Kalaprakasika, Muhurta Chintamani, Jatakaparijata.
Evaluates Dina, Gana, Mahendra, Stree Deergha, Yoni, Rashi, Rashi Adhipati,
Vashya, Rajju (5 body zones), and Vedha (12 classical obstruction pairs).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.synastry import DasaKutaItem, DasaKutaResult
from apps.api.services.synastry_engine import (
    _GANA_COMPATIBILITY_MATRIX,
    _GANA_ORDER,
    _NAKSHATRA_GANA,
    _NAKSHATRA_ORDER,
    _NAKSHATRA_YONI,
    _PLANETARY_FRIENDS,
    _RASHI_LORDS,
    _RASHI_ORDER,
    _VASHYA_MAP,
    _YONI_COMPATIBILITY_MATRIX,
    _YONI_ORDER,
)

# ── 1. Rajju Classifications (5 Body Zones across 27 Nakshatras) ──────────────

# 0 = Siro (Head), 1 = Kanta (Neck), 2 = Nabhi (Navel), 3 = Ooru (Thigh), 4 = Pada (Foot)
_RAJJU_MAP: dict[str, tuple[str, int]] = {
    # Siro (Head)
    "mrigashira": ("Siro Rajju (Head)", 0),
    "chitra": ("Siro Rajju (Head)", 0),
    "dhanishta": ("Siro Rajju (Head)", 0),

    # Kanta (Neck)
    "rohini": ("Kanta Rajju (Neck)", 1),
    "ardra": ("Kanta Rajju (Neck)", 1),
    "hasta": ("Kanta Rajju (Neck)", 1),
    "swati": ("Kanta Rajju (Neck)", 1),
    "shravana": ("Kanta Rajju (Neck)", 1),
    "shatabhisha": ("Kanta Rajju (Neck)", 1),

    # Nabhi (Navel)
    "krittika": ("Nabhi Rajju (Navel)", 2),
    "punarvasu": ("Nabhi Rajju (Navel)", 2),
    "uttara_phalguni": ("Nabhi Rajju (Navel)", 2),
    "vishakha": ("Nabhi Rajju (Navel)", 2),
    "uttara_ashadha": ("Nabhi Rajju (Navel)", 2),
    "purva_bhadrapada": ("Nabhi Rajju (Navel)", 2),

    # Ooru (Thigh)
    "bharani": ("Ooru Rajju (Thigh)", 3),
    "pushya": ("Ooru Rajju (Thigh)", 3),
    "purva_phalguni": ("Ooru Rajju (Thigh)", 3),
    "anuradha": ("Ooru Rajju (Thigh)", 3),
    "purva_ashadha": ("Ooru Rajju (Thigh)", 3),
    "uttara_bhadrapada": ("Ooru Rajju (Thigh)", 3),

    # Pada (Foot)
    "ashwini": ("Pada Rajju (Foot)", 4),
    "ashlesha": ("Pada Rajju (Foot)", 4),
    "magha": ("Pada Rajju (Foot)", 4),
    "jyeshtha": ("Pada Rajju (Foot)", 4),
    "mula": ("Pada Rajju (Foot)", 4),
    "revati": ("Pada Rajju (Foot)", 4),
}

# ── 2. Vedha Nakshatra Incompatible Pairs ──────────────────────────────────────

_VEDHA_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"ashwini", "jyeshtha"}),
    frozenset({"bharani", "anuradha"}),
    frozenset({"krittika", "vishakha"}),
    frozenset({"rohini", "swati"}),
    frozenset({"ardra", "shravana"}),
    frozenset({"punarvasu", "uttara_ashadha"}),
    frozenset({"pushya", "purva_ashadha"}),
    frozenset({"ashlesha", "mula"}),
    frozenset({"magha", "revati"}),
    frozenset({"purva_phalguni", "uttara_bhadrapada"}),
    frozenset({"uttara_phalguni", "purva_bhadrapada"}),
    frozenset({"hasta", "shatabhisha"}),
    frozenset({"mrigashira", "chitra"}),
    frozenset({"chitra", "dhanishta"}),
    frozenset({"mrigashira", "dhanishta"}),
})


class DasaKutaEngine:
    """
    Evaluates the complete South Indian 10-Porutham compatibility system.
    """

    @classmethod
    def evaluate(
        cls,
        girl_rashi: str,
        girl_nakshatra: str,
        boy_rashi: str,
        boy_nakshatra: str,
    ) -> DasaKutaResult:
        g_r = girl_rashi.lower()
        b_r = boy_rashi.lower()
        g_n = girl_nakshatra.lower()
        b_n = boy_nakshatra.lower()

        idx_g = _NAKSHATRA_ORDER.index(g_n) if g_n in _NAKSHATRA_ORDER else 0
        idx_b = _NAKSHATRA_ORDER.index(b_n) if b_n in _NAKSHATRA_ORDER else 0

        # Count from Girl to Boy (1 to 27)
        count_g_to_b = ((idx_b - idx_g) % 27 + 27) % 27 + 1

        items: list[DasaKutaItem] = []

        # 1. Dina Porutham (Tara)
        tara_rem = count_g_to_b % 9
        dina_compat = tara_rem in (0, 2, 4, 6, 8)
        items.append(DasaKutaItem(
            name="Dina",
            label="Dina Porutham (Longevity & Health)",
            is_compatible=dina_compat,
            obtained_score=3.0 if dina_compat else 0.0,
            max_score=3.0,
            partner_a_value=f"Girl Star: {g_n.capitalize()}",
            partner_b_value=f"Boy Star #{count_g_to_b} (Tara {tara_rem})",
            description="Measures daily health, freedom from diseases and vitality.",
            classical_source="Kalaprakasika, Ch. 11, Sloka 3-6",
        ))

        # 2. Gana Porutham
        gana_g = _NAKSHATRA_GANA.get(g_n, "Manushya")
        gana_b = _NAKSHATRA_GANA.get(b_n, "Manushya")
        gana_pts = _GANA_COMPATIBILITY_MATRIX[_GANA_ORDER.index(gana_g)][_GANA_ORDER.index(gana_b)]
        gana_compat = gana_pts >= 3
        items.append(DasaKutaItem(
            name="Gana",
            label="Gana Porutham (Temperament)",
            is_compatible=gana_compat,
            obtained_score=float(gana_pts),
            max_score=6.0,
            partner_a_value=gana_g,
            partner_b_value=gana_b,
            description="Temperament, character and psychological affinity.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 22",
        ))

        # 3. Mahendra Porutham (Boy star 4, 7, 10, 13, 16, 19, 22, 25 from Girl)
        mahendra_compat = count_g_to_b in (4, 7, 10, 13, 16, 19, 22, 25)
        items.append(DasaKutaItem(
            name="Mahendra",
            label="Mahendra Porutham (Progeny & Wealth)",
            is_compatible=mahendra_compat,
            obtained_score=2.0 if mahendra_compat else 0.0,
            max_score=2.0,
            partner_a_value=f"Star Count: {count_g_to_b}",
            partner_b_value="Required: 4, 7, 10, 13, 16, 19, 22, 25",
            description="Bestows progeny, family growth, wealth and long-lasting connection.",
            classical_source="Kalaprakasika, Ch. 11, Sloka 8",
        ))

        # 4. Stree Deergha Porutham (Boy star > 13 nakshatras from Girl)
        stree_deergha_compat = count_g_to_b > 13
        items.append(DasaKutaItem(
            name="Stree Deergha",
            label="Stree Deergha Porutham (Female Prosperity)",
            is_compatible=stree_deergha_compat,
            obtained_score=2.0 if stree_deergha_compat else 0.0,
            max_score=2.0,
            partner_a_value=f"Count: {count_g_to_b}",
            partner_b_value="Required: > 13 nakshatras",
            description="Promotes all-round prosperity, mutual appreciation and female longevity.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 28",
        ))

        # 5. Yoni Porutham
        yoni_g = _NAKSHATRA_YONI.get(g_n, "Horse")
        yoni_b = _NAKSHATRA_YONI.get(b_n, "Horse")
        y_pts = float(_YONI_COMPATIBILITY_MATRIX[_YONI_ORDER.index(yoni_g)][_YONI_ORDER.index(yoni_b)])
        yoni_compat = y_pts >= 2.0
        items.append(DasaKutaItem(
            name="Yoni",
            label="Yoni Porutham (Physical Affinity)",
            is_compatible=yoni_compat,
            obtained_score=y_pts,
            max_score=4.0,
            partner_a_value=yoni_g,
            partner_b_value=yoni_b,
            description="Biological, physical and sexual harmony.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 16",
        ))

        # 6. Rashi Porutham (Moon Sign Axis)
        r_idx_g = _RASHI_ORDER.index(g_r) if g_r in _RASHI_ORDER else 0
        r_idx_b = _RASHI_ORDER.index(b_r) if b_r in _RASHI_ORDER else 0
        r_dist = ((r_idx_b - r_idx_g) % 12 + 12) % 12 + 1
        rashi_compat = r_dist in (1, 7, 3, 11, 4, 10)
        items.append(DasaKutaItem(
            name="Rashi",
            label="Rashi Porutham (Family Lineage)",
            is_compatible=rashi_compat,
            obtained_score=7.0 if rashi_compat else 0.0,
            max_score=7.0,
            partner_a_value=g_r.capitalize(),
            partner_b_value=f"{b_r.capitalize()} (Axis {r_dist})",
            description="Prevents 6/8 and 2/12 rashi conflicts and ensures domestic growth.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 26",
        ))

        # 7. Rashi Adhipati (Graha Maitri)
        lord_g = _RASHI_LORDS.get(g_r, "sun")
        lord_b = _RASHI_LORDS.get(b_r, "sun")
        adhipati_compat = lord_g == lord_b or lord_b in _PLANETARY_FRIENDS.get(lord_g, set())
        items.append(DasaKutaItem(
            name="Rashi Adhipati",
            label="Rashi Adhipati Porutham (Lord Friendship)",
            is_compatible=adhipati_compat,
            obtained_score=5.0 if adhipati_compat else 1.0,
            max_score=5.0,
            partner_a_value=f"{g_r.capitalize()} ({lord_g.capitalize()})",
            partner_b_value=f"{b_r.capitalize()} ({lord_b.capitalize()})",
            description="Intellectual friendship and psychological peace.",
            classical_source="Brihat Parashara Hora Shastra, Ch. 73, Sloka 18",
        ))

        # 8. Vashya Porutham
        vash_g = _VASHYA_MAP.get(g_r, "Chatushpada")
        vash_b = _VASHYA_MAP.get(b_r, "Chatushpada")
        vash_compat = vash_g == vash_b or not ((vash_g == "Vanachara" and vash_b in ("Chatushpada", "Dwipada")) or (vash_b == "Vanachara" and vash_g in ("Chatushpada", "Dwipada")))
        items.append(DasaKutaItem(
            name="Vashya",
            label="Vashya Porutham (Mutual Control)",
            is_compatible=vash_compat,
            obtained_score=2.0 if vash_compat else 0.0,
            max_score=2.0,
            partner_a_value=vash_g,
            partner_b_value=vash_b,
            description="Mutual magnetic attraction, respect and harmony.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 12",
        ))

        # 9. Rajju Porutham (5 Rajjus - must be different)
        rajju_g_label, rajju_g_zone = _RAJJU_MAP.get(g_n, ("Siro Rajju (Head)", 0))
        rajju_b_label, rajju_b_zone = _RAJJU_MAP.get(b_n, ("Siro Rajju (Head)", 0))
        is_rajju_compat = rajju_g_zone != rajju_b_zone
        items.append(DasaKutaItem(
            name="Rajju",
            label="Rajju Porutham (Marital Longevity)",
            is_compatible=is_rajju_compat,
            obtained_score=5.0 if is_rajju_compat else 0.0,
            max_score=5.0,
            partner_a_value=rajju_g_label,
            partner_b_value=rajju_b_label,
            description="Critical longevity factor. Same Rajju (especially Siro/Kanta) indicates danger to life.",
            classical_source="Kalaprakasika, Ch. 11, Sloka 24-28",
        ))

        # 10. Vedha Porutham (No mutual star obstruction)
        pair = frozenset({g_n, b_n})
        has_vedha = pair in _VEDHA_PAIRS
        is_vedha_compat = not has_vedha
        items.append(DasaKutaItem(
            name="Vedha",
            label="Vedha Porutham (Non-Affliction)",
            is_compatible=is_vedha_compat,
            obtained_score=4.0 if is_vedha_compat else 0.0,
            max_score=4.0,
            partner_a_value=g_n.capitalize(),
            partner_b_value=b_n.capitalize(),
            description="Mutual star repulsion check. Vedha stars cause discord and separations.",
            classical_source="Muhurta Chintamani, Vivaha Prakarana, Sloka 30",
        ))

        total_pts = sum(it.obtained_score for it in items)
        max_pts = sum(it.max_score for it in items)  # 40.0
        pct = (total_pts / max_pts) * 100.0 if max_pts > 0 else 0.0

        if not is_rajju_compat:
            verdict = "CHALLENGING — Rajju Dosha present (requires deep classical review & astrological remedies)."
        elif not is_vedha_compat:
            verdict = "MODERATE — Vedha affliction present between natal stars."
        elif pct >= 75.0:
            verdict = "EXCELLENT — Comprehensive 10-Porutham alignment."
        elif pct >= 55.0:
            verdict = "GOOD — Favorable Dasa Kuta compatibility."
        else:
            verdict = "AVERAGE — Mixed Porutham scores."

        summary = (
            f"Dasa Kuta Score: {total_pts:.1f}/{max_pts:.1f} ({pct:.1f}%). "
            f"Rajju Compatible: {is_rajju_compat}, Vedha Compatible: {is_vedha_compat}, "
            f"Mahendra: {mahendra_compat}, Stree Deergha: {stree_deergha_compat}."
        )

        return DasaKutaResult(
            items=tuple(items),
            total_score=total_pts,
            max_total_score=max_pts,
            compatibility_percentage=round(pct, 1),
            is_rajju_compatible=is_rajju_compat,
            is_vedha_compatible=is_vedha_compat,
            is_mahendra_present=mahendra_compat,
            is_stree_deergha_present=stree_deergha_compat,
            verdict=verdict,
            summary=summary,
        )

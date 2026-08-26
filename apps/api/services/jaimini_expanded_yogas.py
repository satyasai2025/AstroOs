"""
AstroOS — Jaimini Expanded Classical Yogas Engine
Classical Reference: Jaimini Upadesha Sutras (Adhyayas 1 & 2), BPHS (Ch. 35 Jaimini Yogas).
Evaluates AK-PK, AmK-DK, Srimantah AL-A11, Vipareeta Arudha, and Karakamsha Moksha Yogas.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from apps.api.domain.divisional import VargaChart
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import (
    ArudhaResult,
    CharaKarakaResult,
    CharaKarakaScheme,
    JaiminiExpandedYoga,
    KarakamsaResult,
    RashiAspectResult,
)
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_shared import (
    house_count,
    is_kendra,
    is_trikona,
    rashi_at,
    rashi_index,
    signs_from,
)
from apps.api.services.karakamsa_engine import KarakamsaEngine
from apps.api.services.rashi_aspect_engine import RashiAspectEngine

_MALEFICS = {"saturn", "mars", "rahu", "ketu", "sun"}
_BENEFICS = {"jupiter", "venus", "mercury", "moon"}


class JaiminiExpandedYogaEngine:
    """
    Evaluates the full set of classical Jaimini Raja, Dhana, Arudha, and Moksha yogas.
    """

    def __init__(
        self,
        chara_karaka_engine: Optional[CharaKarakaEngine] = None,
        arudha_engine: Optional[ArudhaEngine] = None,
        rashi_aspect_engine: Optional[RashiAspectEngine] = None,
        karakamsa_engine: Optional[KarakamsaEngine] = None,
    ) -> None:
        self._karaka = chara_karaka_engine or CharaKarakaEngine()
        self._arudha = arudha_engine or ArudhaEngine()
        self._aspect = rashi_aspect_engine or RashiAspectEngine()
        self._karakamsa = karakamsa_engine or KarakamsaEngine(self._karaka)

    def evaluate_all(
        self,
        d1_chart: D1Chart,
        d9_chart: Optional[VargaChart] = None,
        scheme: CharaKarakaScheme = "sapta_karaka",
    ) -> tuple[JaiminiExpandedYoga, ...]:
        karakas = self._karaka.compute(d1_chart, scheme=scheme)
        arudhas = self._arudha.compute(d1_chart)
        aspects = self._aspect.compute(d1_chart)
        karakamsa_res = self._karakamsa.compute(d1_chart, d9_chart, scheme=scheme) if d9_chart else None

        yogas: list[JaiminiExpandedYoga] = []

        # 1. AK-PK Raja Yoga (JAIMINI-RY-002)
        ak = karakas.atmakaraka
        pk = karakas.by_name("Putrakaraka")
        is_k_or_t = is_kendra(ak.rashi, pk.rashi) or is_trikona(ak.rashi, pk.rashi)
        has_aspect = aspects.does_aspect(ak.rashi, pk.rashi) or aspects.does_aspect(pk.rashi, ak.rashi)
        ak_pk_present = is_k_or_t or has_aspect
        yogas.append(JaiminiExpandedYoga(
            yoga_name="Atmakaraka-Putrakaraka Scholastic Raja Yoga",
            rule_id="JAIMINI-RY-002",
            is_present=ak_pk_present,
            participating_elements=(f"AK: {ak.planet} ({ak.rashi})", f"PK: {pk.planet} ({pk.rashi})"),
            strength_score=85.0 if ak_pk_present else 0.0,
            classical_source="Jaimini Upadesha Sutras 1.2",
            description="Mutual Kendra/Trikona or Rashi Drishti between Atmakaraka and Putrakaraka grants intellectual eminence, noble counsel, and scholarly success.",
        ))

        # 2. AmK-DK Commerce & Prosperity Yoga (JAIMINI-RY-003)
        amk = karakas.by_name("Amatyakaraka")
        dk = karakas.darakaraka
        amk_dk_k = is_kendra(amk.rashi, dk.rashi) or (amk.rashi == dk.rashi)
        amk_dk_asp = aspects.does_aspect(amk.rashi, dk.rashi) or aspects.does_aspect(dk.rashi, amk.rashi)
        amk_dk_present = amk_dk_k or amk_dk_asp
        yogas.append(JaiminiExpandedYoga(
            yoga_name="Amatyakaraka-Darakaraka Commercial Prosperity Yoga",
            rule_id="JAIMINI-RY-003",
            is_present=amk_dk_present,
            participating_elements=(f"AmK: {amk.planet} ({amk.rashi})", f"DK: {dk.planet} ({dk.rashi})"),
            strength_score=80.0 if amk_dk_present else 0.0,
            classical_source="Jaimini Upadesha Sutras 1.2",
            description="Connection between Amatyakaraka (career) and Darakaraka (wealth/business) bestows continuous financial growth through partnerships.",
        ))

        # 3. Srimantah / Labhapada Arudha Yoga (JAIMINI-AY-001)
        al = arudhas.arudha_lagna  # A1
        a11 = arudhas.by_house(11)  # A11 (Labhapada)
        al_a11_same = (al.rashi == a11.rashi)
        al_a11_asp = aspects.does_aspect(al.rashi, a11.rashi) or aspects.does_aspect(a11.rashi, al.rashi)
        srimantah_present = al_a11_same or al_a11_asp
        yogas.append(JaiminiExpandedYoga(
            yoga_name="Srimantah Labhapada Arudha Yoga",
            rule_id="JAIMINI-AY-001",
            is_present=srimantah_present,
            participating_elements=(f"AL (A1): {al.rashi}", f"A11 (Labhapada): {a11.rashi}"),
            strength_score=90.0 if srimantah_present else 0.0,
            classical_source="Jaimini Upadesha Sutras 1.3.16-17",
            description="Conjunction or mutual Rashi Drishti between Arudha Lagna and 11th Pada (A11) produces abundant and uninterrupted wealth.",
        ))

        # 4. Vipareeta Arudha Yoga (JAIMINI-AY-002)
        h3_from_al = signs_from(al.rashi, 2)
        h6_from_al = signs_from(al.rashi, 5)
        malefics_in_3 = [p.planet for p in d1_chart.planets if p.rashi.lower() == h3_from_al and p.planet.lower() in _MALEFICS]
        malefics_in_6 = [p.planet for p in d1_chart.planets if p.rashi.lower() == h6_from_al and p.planet.lower() in _MALEFICS]
        vipareeta_present = (len(malefics_in_3) + len(malefics_in_6)) >= 1
        yogas.append(JaiminiExpandedYoga(
            yoga_name="Vipareeta Arudha Victory Yoga",
            rule_id="JAIMINI-AY-002",
            is_present=vipareeta_present,
            participating_elements=(f"3rd from AL: {malefics_in_3}", f"6th from AL: {malefics_in_6}"),
            strength_score=75.0 if vipareeta_present else 0.0,
            classical_source="Jaimini Upadesha Sutras 1.3.21",
            description="Natural malefics in 3rd or 6th from Arudha Lagna give tremendous valor, victory over rivals, and military/executive conquest.",
        ))

        # 5. Karakamsha Moksha Yoga (JAIMINI-KY-002)
        moksha_present = False
        moksha_details = "D9 chart required for Karakamsha analysis."
        if karakamsa_res:
            h12_entry = next((h for h in karakamsa_res.relative_houses if h.house_number == 12), None)
            if h12_entry and "ketu" in [p.lower() for p in h12_entry.planets]:
                moksha_present = True
                moksha_details = f"Ketu in 12th house ({h12_entry.rashi}) from Karakamsha."
            else:
                moksha_details = f"12th house from Karakamsha holds: {h12_entry.planets if h12_entry else 'None'}."

        yogas.append(JaiminiExpandedYoga(
            yoga_name="Karakamsha Ketu Kaivalya (Moksha) Yoga",
            rule_id="JAIMINI-KY-002",
            is_present=moksha_present,
            participating_elements=(moksha_details,),
            strength_score=95.0 if moksha_present else 0.0,
            classical_source="Jaimini Upadesha Sutras 1.2.69",
            description="Ketu in the 12th house from Karakamsha indicates final spiritual liberation, enlightenment, and detachment from worldly bondage.",
        ))

        return tuple(yogas)

"""
AstroOS — Jha 44 Kendra-Trikona Rajayoga with Badhaka Obstruction (JHA-RY-044)
=============================================================================
Provenance: Kundalee Binary frmYogaHelp (DevMithila Offset 1335524 - 1337474)

Classical and Siddhantic Axioms decoded verbatim:
  1. "केंद्रेश और त्रिकोणेश में परस्पर सम्बन्ध होने से राजयोग अथवा अत्यंत शुभयोग बनता है।"
  2. "एक ही ग्रह केंद्रेश और त्रिकोणेश दोनों हो तो राजयोगकारक होता है।"
  3. "राजयोग तभी कारगर होता है जब बाधक योग न हों!"
  4. केंद्रेश उत्तरोत्तर बली: 1 < 4 < 7 < 10 (सर्वाधिक बली राज्येश/दशमेश)।
  5. त्रिकोणेश उत्तरोत्तर बली: 1 < 5 < 9 (सर्वाधिक बली नवमेश)।
  6. 11 केंद्रेश-त्रिकोणेश युग्म x 4 सम्बन्ध = 44 प्रकार के राजयोग:
     - 1. परस्पर स्थान परिवर्तन (Parivartana) — सबसे बलवान सम्बन्ध।
     - 2. भावेश-दृष्टि सम्बन्ध (Bhavesha-Drishti) — ग्रह जिस राशि में हो, उसका स्वामी उसे देखे।
     - 3. युति सम्बन्ध (Conjunction) — एक ही भाव में वास।
     - 4. दृष्टि सम्बन्ध (Mutual Aspect) — परस्पर दृष्टि (पूर्ण दृष्टि युति से भी अधिक बलवान)।
  7. बाधक फ़िल्टर: यदि बाधकेश का इन योगकारक ग्रहों से सम्बन्ध हो, तो राजयोग निष्फल/अवरुद्ध होता है।
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from apps.api.domain.maraka import BadhakaConfig, LagnaModality
from apps.api.domain.yoga import YogaResult
from apps.api.services.maraka_engine import MarakaEngine
from apps.api.services.yoga_predicates import (
    KENDRA_HOUSES,
    TRIKONA_HOUSES,
    YogaContext,
    get_house,
    is_associated,
)
from apps.api.services.yoga_registry import register_yoga
from packages.shared.constants import SIGN_LORDS


# 11 Distinct Kendra-Trikona House Pairs
# Excluding 1-1 (vacuous identity)
KENDRA_TRIKONA_11_PAIRS: tuple[tuple[int, int], ...] = (
    (1, 5), (1, 9),
    (4, 1), (4, 5), (4, 9),
    (7, 1), (7, 5), (7, 9),
    (10, 1), (10, 5), (10, 9),
)


@register_yoga(
    yoga_id="JHA-RY-044",
    name="Jha 44 Kendra-Trikona Rajayoga with Badhaka Obstruction",
    category="Raja Yoga",
    source_text="kundalee-binary frmYogaHelp (DevMithila)",
    rule_version="1.0",
    requires=("D1", "HouseEngine", "AspectEngine", "BadhakaEngine"),
)
def evaluate_jha_rajayoga_badhaka(ctx: YogaContext) -> Optional[YogaResult]:
    maraka_svc = MarakaEngine()
    lagna_rashi = ctx.chart.ascendant.rashi.lower()
    badhaka_info = maraka_svc.get_badhaka_info(lagna_rashi)
    badhakesh = badhaka_info.badhakesh_planet.lower()

    trace: list[str] = [
        f"Lagna: {lagna_rashi.capitalize()} ({badhaka_info.lagna_modality.value}) -> Badhaka House {badhaka_info.badhaka_house} (Badhakesh: {badhakesh.capitalize()})."
    ]
    satisfied_yogas: list[str] = []
    missing_yogas: list[str] = []
    obstructed_yogas: list[str] = []
    involved_planets: set[str] = set()
    involved_houses: set[int] = set()

    for k_house, t_house in KENDRA_TRIKONA_11_PAIRS:
        k_lord = get_house(ctx, k_house).lord.lower()
        t_lord = get_house(ctx, t_house).lord.lower()

        if k_lord == t_lord:
            # Single planet ruling both Kendra and Trikona = Natural Yogakaraka!
            satisfied_yogas.append(
                f"Yogakaraka: {k_lord.capitalize()} rules both Kendra ({k_house}H) and Trikona ({t_house}H)."
            )
            involved_planets.add(k_lord)
            involved_houses.update({k_house, t_house})
            continue

        # Check association between k_lord and t_lord
        associated = is_associated(ctx, k_lord, t_lord)
        if associated:
            # Jha's Crucial Invariant: "राजयोग तभी कारगर होता है जब बाधक योग न हों!"
            badhaka_affliction = is_associated(ctx, k_lord, badhakesh) or is_associated(ctx, t_lord, badhakesh)

            yoga_label = (
                f"Kendra {k_house}H ({k_lord.capitalize()}) <-> Trikona {t_house}H ({t_lord.capitalize()}) Sambandha"
            )
            involved_planets.update({k_lord, t_lord})
            involved_houses.update({k_house, t_house})

            if badhaka_affliction:
                obstructed_yogas.append(f"{yoga_label} [OBSTRUCTED by Badhakesh {badhakesh.capitalize()}]")
                trace.append(f"  {yoga_label}: OBSTRUCTED by Badhakesh {badhakesh.capitalize()}!")
            else:
                satisfied_yogas.append(f"{yoga_label} [ACTIVE - Unobstructed]")
                trace.append(f"  {yoga_label}: ACTIVE (100% Shastric Effectiveness).")
        else:
            missing_yogas.append(f"Kendra {k_house}H ({k_lord}) <-> Trikona {t_house}H ({t_lord})")

    any_active = len(satisfied_yogas) > 0
    is_present = any_active or len(obstructed_yogas) > 0
    strength = "full" if any_active else ("weak" if is_present else None)

    trace.append(
        f"Summary: {len(satisfied_yogas)} Active Yogas, {len(obstructed_yogas)} Obstructed by Badhakesh."
    )

    return YogaResult(
        yoga_id="JHA-RY-044",
        name="Jha 44 Kendra-Trikona Rajayoga with Badhaka Obstruction",
        category="Raja Yoga",
        source_text="kundalee-binary frmYogaHelp (DevMithila)",
        rule_version="1.0",
        is_present=is_present,
        strength=strength,
        involved_planets=tuple(sorted(involved_planets)),
        involved_houses=tuple(sorted(involved_houses)),
        satisfied=tuple(satisfied_yogas + obstructed_yogas),
        missing=tuple(missing_yogas),
        trace=tuple(trace),
    )
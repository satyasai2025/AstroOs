"""
AstroOS - 16 Classical Tajika Yogas Engine (Shodasha Tajika Yogas)
Sources: Tajika Neelakanthi, Prasna Marga, PyJHora
"""

from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.ephemeris import EphemerisResult, SiderealPosition
from apps.api.domain.varshaphal import TajikaAspect, TajikaYoga
from apps.api.services.tajaka_constants import (
    DEEPTAMSHA,
    PLANET_SPEED_HIERARCHY,
)
from packages.shared.constants import DEGREES_PER_RASHI, SIGN_LORDS
from packages.shared.enums import Rashi

_RASHI_LIST: list[str] = [r.value for r in Rashi]
_TAJIKA_PLANETS: list[str] = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
_ASPECT_ANGLES: list[int] = [0, 60, 90, 120, 180]


class TajakaYogaEngine:
    """Evaluates all 16 Classical Tajika Yogas for a Varshaphal chart."""

    @staticmethod
    def get_deeptamsha_orb(planet_a: str, planet_b: str) -> float:
        """Average Deeptamsha (orb) of the two planets."""
        orb_a = DEEPTAMSHA.get(planet_a, 10.0)
        orb_b = DEEPTAMSHA.get(planet_b, 10.0)
        return (orb_a + orb_b) / 2.0

    @classmethod
    def evaluate_all_yogas(
        cls,
        varsha_chart: EphemerisResult,
        tajika_aspects: tuple[TajikaAspect, ...],
    ) -> tuple[TajikaYoga, ...]:
        positions = {p.planet: p for p in varsha_chart.planet_positions if p.planet in _TAJIKA_PLANETS}
        yogas: list[TajikaYoga] = []

        # 1. Ikabala Yoga & 2. Induvara Yoga
        houses = [p.house_number for p in positions.values() if p.house_number is not None]
        kendras_panaparas = {1, 4, 7, 10, 2, 5, 8, 11}
        apoklimas = {3, 6, 9, 12}

        if houses and all(h in kendras_panaparas for h in houses):
            yogas.append(TajikaYoga(
                yoga_name="Ikabala",
                category="BENEFIC",
                planets=tuple(positions.keys()),
                is_formed=True,
                description="All planets occupy Kendra (1,4,7,10) or Panapara (2,5,8,11) houses. Grants success and prosperity.",
                details={"houses": houses},
            ))

        if houses and all(h in apoklimas for h in houses):
            yogas.append(TajikaYoga(
                yoga_name="Induvara",
                category="MALEFIC",
                planets=tuple(positions.keys()),
                is_formed=True,
                description="All planets occupy Apoklima (3,6,9,12) houses. Causes disappointment and lack of support.",
                details={"houses": houses},
            ))

        # 3. Ithasala (Muthasila) Yoga
        ithasalas = [a for a in tajika_aspects if a.is_ithasala and a.within_deeptamsha]
        for a in ithasalas:
            sub_type = "Poorna" if a.current_orb_deg < 0.0166 else "Vartamana"
            yogas.append(TajikaYoga(
                yoga_name="Ithasala",
                category="BENEFIC",
                planets=(a.planet_a, a.planet_b),
                is_formed=True,
                description=f"{sub_type} Ithasala Yoga formed between {a.planet_a.title()} and {a.planet_b.title()} (angle: {a.aspect_angle}°). Ensures achievement of objectives.",
                details={"aspect_angle": a.aspect_angle, "orb": a.current_orb_deg, "sub_type": sub_type},
            ))

        # 4. Isharpha (Musaripha) Yoga
        isharphas = [a for a in tajika_aspects if a.is_isharpha and a.within_deeptamsha]
        for a in isharphas:
            yogas.append(TajikaYoga(
                yoga_name="Isharpha",
                category="MALEFIC",
                planets=(a.planet_a, a.planet_b),
                is_formed=True,
                description=f"Isharpha Yoga between {a.planet_a.title()} and {a.planet_b.title()} (separating aspect). Indicates past opportunities or missed timing.",
                details={"aspect_angle": a.aspect_angle, "orb": a.current_orb_deg},
            ))

        # 5. Nakta Yoga (Transfer of light by faster intermediary, e.g. Moon)
        for (name_a, pos_a), (name_b, pos_b) in itertools.combinations(positions.items(), 2):
            has_direct_ithasala = any(
                a.is_ithasala and ((a.planet_a == name_a and a.planet_b == name_b) or (a.planet_a == name_b and a.planet_b == name_a))
                for a in tajika_aspects
            )
            if not has_direct_ithasala:
                for name_c, pos_c in positions.items():
                    if name_c in (name_a, name_b):
                        continue
                    speed_c = abs(pos_c.speed_deg_per_day)
                    speed_a = abs(pos_a.speed_deg_per_day)
                    speed_b = abs(pos_b.speed_deg_per_day)
                    if speed_c > speed_a and speed_c > speed_b:
                        asp_ca = next((a for a in tajika_aspects if a.is_ithasala and ((a.planet_a == name_c and a.planet_b == name_a) or (a.planet_a == name_a and a.planet_b == name_c))), None)
                        asp_cb = next((a for a in tajika_aspects if a.is_ithasala and ((a.planet_a == name_c and a.planet_b == name_b) or (a.planet_a == name_b and a.planet_b == name_c))), None)
                        if asp_ca and asp_cb:
                            yogas.append(TajikaYoga(
                                yoga_name="Nakta",
                                category="BENEFIC",
                                planets=(name_a, name_b, name_c),
                                is_formed=True,
                                description=f"Nakta Yoga: {name_c.title()} acts as a faster intermediary transferring light between {name_a.title()} and {name_b.title()}.",
                                details={"intermediary": name_c},
                            ))
                            break

        # 6. Yamaya Yoga (Connecting two planets through slower intermediary)
        for (name_a, pos_a), (name_b, pos_b) in itertools.combinations(positions.items(), 2):
            has_direct_ithasala = any(
                a.is_ithasala and ((a.planet_a == name_a and a.planet_b == name_b) or (a.planet_a == name_b and a.planet_b == name_a))
                for a in tajika_aspects
            )
            if not has_direct_ithasala:
                for name_c, pos_c in positions.items():
                    if name_c in (name_a, name_b):
                        continue
                    speed_c = abs(pos_c.speed_deg_per_day)
                    speed_a = abs(pos_a.speed_deg_per_day)
                    speed_b = abs(pos_b.speed_deg_per_day)
                    if speed_c < speed_a and speed_c < speed_b:
                        asp_ac = next((a for a in tajika_aspects if a.is_ithasala and ((a.planet_a == name_a and a.planet_b == name_c) or (a.planet_a == name_c and a.planet_b == name_a))), None)
                        asp_bc = next((a for a in tajika_aspects if a.is_ithasala and ((a.planet_a == name_b and a.planet_b == name_c) or (a.planet_a == name_c and a.planet_b == name_b))), None)
                        if asp_ac and asp_bc:
                            yogas.append(TajikaYoga(
                                yoga_name="Yamaya",
                                category="BENEFIC",
                                planets=(name_a, name_b, name_c),
                                is_formed=True,
                                description=f"Yamaya Yoga: {name_c.title()} acts as a slower intermediary joining {name_a.title()} and {name_b.title()}.",
                                details={"intermediary": name_c},
                            ))
                            break

        # 7. Manahoo Yoga (Ithasala interrupted by Mars/Saturn)
        for a in ithasalas:
            for malefic in ("mars", "saturn"):
                if malefic not in (a.planet_a, a.planet_b):
                    interfering = next((
                        m for m in tajika_aspects
                        if m.is_ithasala and (
                            (m.planet_a == malefic and m.planet_b in (a.planet_a, a.planet_b)) or
                            (m.planet_b == malefic and m.planet_a in (a.planet_a, a.planet_b))
                        ) and (m.days_to_exact or 999) < (a.days_to_exact or 999)
                    ), None)
                    if interfering:
                        yogas.append(TajikaYoga(
                            yoga_name="Manahoo",
                            category="MALEFIC",
                            planets=(a.planet_a, a.planet_b, malefic),
                            is_formed=True,
                            description=f"Manahoo Yoga: {malefic.title()} intervenes before Ithasala between {a.planet_a.title()} and {a.planet_b.title()} perfects, causing obstruction.",
                            details={"interfering_malefic": malefic},
                        ))

        # 8. Kamboola Yoga & 9. Gairi Kamboola Yoga (Moon joining an Ithasala)
        for a in ithasalas:
            if "moon" not in (a.planet_a, a.planet_b):
                moon_ithasala = next((
                    m for m in ithasalas
                    if ("moon" in (m.planet_a, m.planet_b)) and (
                        a.planet_a in (m.planet_a, m.planet_b) or a.planet_b in (m.planet_a, m.planet_b)
                    )
                ), None)
                if moon_ithasala:
                    moon_pos = positions.get("moon")
                    is_gairi = moon_pos and (moon_pos.rashi in ("taurus", "cancer"))
                    y_name = "Gairi Kamboola" if is_gairi else "Kamboola"
                    desc = f"{y_name} Yoga: Moon strengthens the Ithasala between {a.planet_a.title()} and {a.planet_b.title()}."
                    if is_gairi:
                        desc += " Moon is exalted/own sign, making this exceptionally powerful."
                    yogas.append(TajikaYoga(
                        yoga_name=y_name,
                        category="BENEFIC",
                        planets=(a.planet_a, a.planet_b, "moon"),
                        is_formed=True,
                        description=desc,
                        details={"is_gairi": is_gairi, "moon_rashi": moon_pos.rashi if moon_pos else ""},
                    ))

        # 10. Khallasara Yoga (Lagna lord without aspect, Moon weak)
        varsha_lagna = varsha_chart.ascendant.rashi
        lagna_lord = SIGN_LORDS[varsha_lagna]
        has_benefic_aspect_on_lagna_lord = any(
            a.within_deeptamsha and lagna_lord in (a.planet_a, a.planet_b) and
            a.aspect_angle in (60, 120) and any(b in (a.planet_a, a.planet_b) for b in ("jupiter", "venus"))
            for a in tajika_aspects
        )
        moon_pos = positions.get("moon")
        if not has_benefic_aspect_on_lagna_lord and moon_pos and (moon_pos.house_number in (6, 8, 12) or moon_pos.is_combust):
            yogas.append(TajikaYoga(
                yoga_name="Khallasara",
                category="MALEFIC",
                planets=(lagna_lord, "moon"),
                is_formed=True,
                description=f"Khallasara Yoga: Lagna Lord ({lagna_lord.title()}) lacks benefic aspects and Moon is afflicted/weak.",
                details={"lagna_lord": lagna_lord},
            ))

        # 11. Radda Yoga (Ithasala spoiled by retrograde / combustion / debility)
        for a in ithasalas:
            pos_a = positions.get(a.planet_a)
            pos_b = positions.get(a.planet_b)
            spoil_a = pos_a and (pos_a.is_retrograde or pos_a.is_combust)
            spoil_b = pos_b and (pos_b.is_retrograde or pos_b.is_combust)
            if spoil_a or spoil_b:
                yogas.append(TajikaYoga(
                    yoga_name="Radda",
                    category="MALEFIC",
                    planets=(a.planet_a, a.planet_b),
                    is_formed=True,
                    description=f"Radda Yoga: Ithasala between {a.planet_a.title()} and {a.planet_b.title()} is spoiled due to retrogradation/combustion.",
                    details={"spoiled_by": [p for p, s in [(a.planet_a, spoil_a), (a.planet_b, spoil_b)] if s]},
                ))

        # 12. Dupparikutha Yoga (Exalted/own sign planet in Ithasala afflicted)
        for a in ithasalas:
            pos_a = positions.get(a.planet_a)
            pos_b = positions.get(a.planet_b)
            strong_a = pos_a and (pos_a.rashi == SIGN_LORDS[pos_a.rashi])
            strong_b = pos_b and (pos_b.rashi == SIGN_LORDS[pos_b.rashi])
            if (strong_a and pos_a.house_number in (6, 8, 12)) or (strong_b and pos_b.house_number in (6, 8, 12)):
                yogas.append(TajikaYoga(
                    yoga_name="Dupparikutha",
                    category="MALEFIC",
                    planets=(a.planet_a, a.planet_b),
                    is_formed=True,
                    description=f"Dupparikutha Yoga: Strong planet placed in 6th/8th/12th house weakens the mutual assistance.",
                    details={"aspect_angle": a.aspect_angle},
                ))

        # 13. Duttavira Yoga (Mutual Reception / Exchanging signs)
        for (name_a, pos_a), (name_b, pos_b) in itertools.combinations(positions.items(), 2):
            lord_a = SIGN_LORDS[pos_a.rashi]
            lord_b = SIGN_LORDS[pos_b.rashi]
            if lord_a == name_b and lord_b == name_a:
                yogas.append(TajikaYoga(
                    yoga_name="Duttavira",
                    category="BENEFIC",
                    planets=(name_a, name_b),
                    is_formed=True,
                    description=f"Duttavira Yoga: {name_a.title()} and {name_b.title()} are in mutual sign reception (Parivartana).",
                    details={"reception_type": "rashi"},
                ))

        # 14. Thambira Yoga (Planet at 29°-30° boundary of sign)
        for name, pos in positions.items():
            if pos.rashi_degree >= 29.0:
                yogas.append(TajikaYoga(
                    yoga_name="Thambira",
                    category="NEUTRAL",
                    planets=(name,),
                    is_formed=True,
                    description=f"Thambira Yoga: {name.title()} is in Sandhi (at {pos.rashi_degree:.2f}°), ready to cross into the next sign.",
                    details={"rashi_degree": pos.rashi_degree},
                ))

        # 15. Kuttha Yoga (Strong planet in Kendra aspecting afflicted planet)
        for name_a, pos_a in positions.items():
            if pos_a.house_number in (1, 4, 7, 10) and not pos_a.is_combust and not pos_a.is_retrograde:
                for name_b, pos_b in positions.items():
                    if name_a != name_b and (pos_b.is_combust or pos_b.house_number in (6, 8, 12)):
                        asp = next((a for a in tajika_aspects if a.within_deeptamsha and ((a.planet_a == name_a and a.planet_b == name_b) or (a.planet_a == name_b and a.planet_b == name_a)) and a.aspect_angle in (60, 120)), None)
                        if asp:
                            yogas.append(TajikaYoga(
                                yoga_name="Kuttha",
                                category="BENEFIC",
                                planets=(name_a, name_b),
                                is_formed=True,
                                description=f"Kuttha Yoga: Strong Kendra planet {name_a.title()} casts benefic aspect on afflicted {name_b.title()}, granting relief.",
                                details={"supporting_planet": name_a, "afflicted_planet": name_b},
                            ))

        # 16. Durupha Yoga (Dusthana 6/8/12 afflicted planets)
        dusthana_afflicted = [
            p.planet for p in positions.values()
            if p.house_number in (6, 8, 12) and (p.is_combust or p.is_retrograde or p.planet in ("mars", "saturn"))
        ]
        if dusthana_afflicted:
            yogas.append(TajikaYoga(
                yoga_name="Durupha",
                category="MALEFIC",
                planets=tuple(dusthana_afflicted),
                is_formed=True,
                description=f"Durupha Yoga: Planets ({', '.join(p.title() for p in dusthana_afflicted)}) in 6th/8th/12th houses are afflicted.",
                details={"afflicted_planets": dusthana_afflicted},
            ))

        return tuple(yogas)

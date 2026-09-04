"""
AstroOS — Linked System (Lagna & Chandra Centric Cognitive Graph)

Implements Vinay Jha's 'Linked System' paradigm:
"A computer program that merely outputs isolated planetary statistics without
synthesizing them into a singular relational network is an Artificial Checker.
To predict life events with authentic intelligence, every planetary placement,
house lordship, drishti, and upagraha must be linked directly back to the
Lagna (physical existence) and Chandra Lagna (mental/experiential realization)."

The Linked System builds a unified graph mapping:
- Direct Lagna Relations (Kendra/Trikona, Functional Benefic/Malefic, Badhaka/Maraka)
- Chandra Lagna Overlay (Sudarshana synthesis)
- Inter-planetary bonds (Sambandha: Mutual Drishti, Conjunction, Parivartana)
- Upagraha links (Gulika/Mandi attachments to key functional lords)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from apps.api.services.intelligence.strength_model import StrengthModel, DignityScore
from apps.api.services.intelligence.drishti_model import DrishtiModel
from apps.api.services.intelligence.upagraha_rules import UpagrahaRulesEngine, UpagrahaInterference


@dataclass
class GrahaNode:
    graha: str
    rashi_idx: int          # 0..11
    house_from_lagna: int   # 1..12
    house_from_chandra: int # 1..12
    owned_houses: List[int] # Houses ruled from Lagna
    dignity: DignityScore
    log_strength: float
    is_functional_benefic: bool
    is_maraka: bool
    aspects_cast: List[Tuple[int, float]] = field(default_factory=list) # (target_house, strength)
    aspects_received: List[Tuple[str, float]] = field(default_factory=list) # (source_graha, strength)
    conjoined_grahas: List[str] = field(default_factory=list)
    has_gulika_contact: bool = False
    has_mandi_contact: bool = False


@dataclass
class LinkedChartGraph:
    lagna_rashi_idx: int
    chandra_rashi_idx: int
    nodes: Dict[str, GrahaNode]
    upagraha_interferences: List[UpagrahaInterference]
    gulika_house: int
    mandi_house: int

    def get_node(self, graha: str) -> Optional[GrahaNode]:
        return self.nodes.get(graha)

    def get_house_lord(self, house: int) -> Optional[str]:
        """
        Returns the graha that rules the specified house (1..12) from Lagna.
        """
        for graha, node in self.nodes.items():
            if house in node.owned_houses:
                return graha
        return None

    def get_house_significators(self, house: int) -> List[str]:
        """
        Returns all grahas linked to a house:
        1. Occupants (Grahas in the house)
        2. Lord of the house
        3. Grahas casting aspect on the house
        """
        significators: Set[str] = set()
        lord = self.get_house_lord(house)
        if lord:
            significators.add(lord)

        for graha, node in self.nodes.items():
            if node.house_from_lagna == house:
                significators.add(graha)
            for target_h, str_val in node.aspects_cast:
                if target_h == house and str_val >= 0.5:
                    significators.add(graha)
        return list(significators)


class LinkedSystemBuilder:
    """
    Constructs the interconnected cognitive graph from raw chart coordinates.
    """

    RASHI_LORDS: Dict[int, str] = {
        0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
        4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
        8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter"
    }

    @classmethod
    def build_graph(
        cls,
        lagna_rashi_idx: int,
        graha_positions: Dict[str, int],  # graha -> rashi_idx (0..11)
        gulika_rashi_idx: int,
        mandi_rashi_idx: int,
    ) -> LinkedChartGraph:
        chandra_rashi_idx = graha_positions.get("Moon", lagna_rashi_idx)

        # 1. Compute houses from Lagna and Chandra
        graha_houses_lagna: Dict[str, int] = {}
        graha_houses_chandra: Dict[str, int] = {}

        for graha, rashi in graha_positions.items():
            graha_houses_lagna[graha] = ((rashi - lagna_rashi_idx) % 12) + 1
            graha_houses_chandra[graha] = ((rashi - chandra_rashi_idx) % 12) + 1

        gulika_house = ((gulika_rashi_idx - lagna_rashi_idx) % 12) + 1
        mandi_house = ((mandi_rashi_idx - lagna_rashi_idx) % 12) + 1

        # 2. Determine house ownership for each graha
        graha_owned_houses: Dict[str, List[int]] = {g: [] for g in graha_positions}
        for house in range(1, 13):
            house_rashi = (lagna_rashi_idx + house - 1) % 12
            lord = cls.RASHI_LORDS.get(house_rashi)
            if lord and lord in graha_owned_houses:
                graha_owned_houses[lord].append(house)

        seventh_lord = None
        eighth_lord = None
        for lord, houses in graha_owned_houses.items():
            if 7 in houses:
                seventh_lord = lord
            if 8 in houses:
                eighth_lord = lord

        # 3. Evaluate Upagraha Interferences
        interferences = UpagrahaRulesEngine.evaluate_upagrahas(
            gulika_house=gulika_house,
            mandi_house=mandi_house,
            graha_houses=graha_houses_lagna,
            seventh_lord=seventh_lord,
            eighth_lord=eighth_lord,
        )

        # 4. Build Graha Nodes
        nodes: Dict[str, GrahaNode] = {}
        for graha, rashi in graha_positions.items():
            h_lagna = graha_houses_lagna[graha]
            h_chandra = graha_houses_chandra[graha]
            owned = graha_owned_houses.get(graha, [])

            dignity = StrengthModel.get_dignity_score(graha, rashi)
            log_str = StrengthModel.calculate_log_strength(dignity)

            # Functional Beneficence from Lagna: Lords of Trikona (1, 5, 9) or Kendra
            is_func_benefic = any(h in (1, 5, 9) for h in owned)
            is_maraka = any(h in (2, 7) for h in owned)

            # Aspect cast on all 12 houses
            aspects_cast = []
            for target_h in range(1, 13):
                asp_str = DrishtiModel.get_aspect_strength(graha, h_lagna, target_h)
                if asp_str > 0.0:
                    aspects_cast.append((target_h, asp_str))

            # Conjunctions with other grahas
            conjoined = [
                other for other, other_h in graha_houses_lagna.items()
                if other != graha and other_h == h_lagna
            ]

            has_gulika = (h_lagna == gulika_house)
            has_mandi = (h_lagna == mandi_house)

            nodes[graha] = GrahaNode(
                graha=graha,
                rashi_idx=rashi,
                house_from_lagna=h_lagna,
                house_from_chandra=h_chandra,
                owned_houses=owned,
                dignity=dignity,
                log_strength=log_str,
                is_functional_benefic=is_func_benefic,
                is_maraka=is_maraka,
                aspects_cast=aspects_cast,
                conjoined_grahas=conjoined,
                has_gulika_contact=has_gulika,
                has_mandi_contact=has_mandi,
            )

        # 5. Populate aspects received
        for graha, node in nodes.items():
            received = []
            for other_graha, other_node in nodes.items():
                if other_graha == graha:
                    continue
                for target_h, asp_str in other_node.aspects_cast:
                    if target_h == node.house_from_lagna:
                        received.append((other_graha, asp_str))
            node.aspects_received = received

        return LinkedChartGraph(
            lagna_rashi_idx=lagna_rashi_idx,
            chandra_rashi_idx=chandra_rashi_idx,
            nodes=nodes,
            upagraha_interferences=interferences,
            gulika_house=gulika_house,
            mandi_house=mandi_house,
        )

    @classmethod
    def from_canonical_report(
        cls,
        lagna_rashi_idx: int,
        graha_positions: Dict[str, int],
        upagraha_report: Any,  # UpagrahaReport from canonical upagraha_engine
    ) -> LinkedChartGraph:
        """
        Directly consumes canonical UpagrahaReport output from upagraha_engine.py
        without duplicating any ephemeris calculations.
        """
        gulika_rashi = getattr(upagraha_report.gulika, "rashi_idx", lagna_rashi_idx)
        # In BPHS / canonical upagraha engine, Mandi is identical or adjacent to Gulika
        mandi_rashi = getattr(upagraha_report, "mandi_rashi_idx", gulika_rashi)

        return cls.build_graph(
            lagna_rashi_idx=lagna_rashi_idx,
            graha_positions=graha_positions,
            gulika_rashi_idx=gulika_rashi,
            mandi_rashi_idx=mandi_rashi,
        )


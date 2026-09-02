"""
AstroOS — Cognitive Reasoner (5-Level Dasha & Linked Synthesis Engine)

Implements Vinay Jha's Cognitive Reasoner:
1. 5-Level Dasha Analysis:
   - MD (Macro Theme / Context)
   - AD (Environmental Activation)
   - PD (Operational Readiness)
   - Sookshma (Precise Time-Window Alignment)
   - Praana (Moment of Precipitation)

2. Synthesizes at each level:
   - House lordship relative to target event (e.g., 7th/2nd/11th for Marriage; 10th/1st/5th/9th for Career; 6th/8th/12th/Maraka for Health/Accident)
   - Base-2 Exponential Strength Mapping (Dignity 1 to 9)
   - Conjunction & Drishti aspects cast on the target house
   - Upagraha (Gulika & Mandi) cognitive modifiers

3. Generates a calibrated 0 to 9 Cognitive Score with
   full rule attribution and diagnostic telemetry.
"""


from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from apps.api.services.intelligence.linked_system import LinkedChartGraph
from apps.api.services.intelligence.upagraha_rules import UpagrahaRulesEngine


@dataclass
class DashaPeriod5Level:
    mahadasha: str
    antardasha: str
    pratyantardasha: str
    sookshma: str
    praana: str
    start_jd: Optional[float] = None
    end_jd: Optional[float] = None

    @classmethod
    def from_canonical_path(
        cls,
        md_lord: str,
        ad_lord: str,
        pd_lord: str,
        sookshma_lord: str,
        praana_lord: str,
        start_jd: Optional[float] = None,
        end_jd: Optional[float] = None,
    ) -> "DashaPeriod5Level":
        return cls(
            mahadasha=md_lord.capitalize(),
            antardasha=ad_lord.capitalize(),
            pratyantardasha=pd_lord.capitalize(),
            sookshma=sookshma_lord.capitalize(),
            praana=praana_lord.capitalize(),
            start_jd=start_jd,
            end_jd=end_jd,
        )


def extract_5level_periods_from_dasha_tree(dasha_tree: Any) -> List[DashaPeriod5Level]:
    """
    Traverses canonical DashaTree (from dasha_engine.py / domain.dasha) and extracts
    5-level active dasha tuples for cognitive evaluation without recalculating anything.
    """
    results: List[DashaPeriod5Level] = []
    periods = getattr(dasha_tree, "mahadashas", getattr(dasha_tree, "periods", []))

    for md in periods:
        md_lord = md.lord
        for ad in getattr(md, "sub_periods", []):
            ad_lord = ad.lord
            for pd in getattr(ad, "sub_periods", []):
                pd_lord = pd.lord
                for sk in getattr(pd, "sub_periods", []):
                    sk_lord = sk.lord
                    for pr in getattr(sk, "sub_periods", []):
                        pr_lord = pr.lord
                        results.append(
                            DashaPeriod5Level.from_canonical_path(
                                md_lord=md_lord,
                                ad_lord=ad_lord,
                                pd_lord=pd_lord,
                                sookshma_lord=sk_lord,
                                praana_lord=pr_lord,
                            )
                        )
    return results




@dataclass
class DashaLevelAssessment:
    level_name: str          # "MD", "AD", "PD", "Sookshma", "Praana"
    lord: str
    is_house_lord: bool
    is_occupant: bool
    aspect_strength: float
    dignity_score: int       # 1..9
    level_score: float       # Contribution to final score (0.0 to 2.0)
    reasons: List[str]


@dataclass
class CognitivePredictionResult:
    event_type: str
    cognitive_score: float    # 0.0 to 9.0 Cognitive Score
    is_probable: bool         # True if score >= 5.0 (at least 3 of 5 levels align)
    level_assessments: List[DashaLevelAssessment]
    upagraha_modifier: float
    reasoning_summary: str
    rule_traces: List[str]

    @property
    def probability_score(self) -> float:
        """Alias for cognitive_score."""
        return self.cognitive_score



class CognitiveReasoner:
    """
    Synthesizes Linked Chart Graph with 5-Level Dasha periods for predictive reasoning.
    """

    EVENT_HOUSES: Dict[str, Dict[str, List[Any]]] = {
        "health": {
            "primary": [1],
            "supporting": [5, 9, 8, 10],
            "karakas": ["Sun", "Mars"],
            "adverse": [6, 8, 12],
        },
        "wealth": {
            "primary": [2],
            "supporting": [11, 5, 9, 1, 4],
            "karakas": ["Jupiter", "Venus", "Mercury"],
            "adverse": [6, 8, 12],
        },
        "siblings": {
            "primary": [3],
            "supporting": [11, 6, 1, 9],
            "karakas": ["Mars"],
            "adverse": [8, 12],
        },
        "property": {
            "primary": [4],
            "supporting": [1, 2, 10, 11, 9],
            "karakas": ["Mars", "Venus", "Moon"],
            "adverse": [6, 8, 12],
        },
        "children": {
            "primary": [5],
            "supporting": [1, 2, 9, 11],
            "karakas": ["Jupiter"],
            "adverse": [6, 8, 12],
        },
        "legal": {
            "primary": [6],
            "supporting": [8, 12, 3, 10, 11],
            "karakas": ["Mars", "Saturn"],
            "adverse": [8, 12],
        },
        "marriage": {
            "primary": [7],
            "supporting": [2, 11, 5, 9, 8],
            "karakas": ["Venus", "Jupiter", "Moon"],
            "adverse": [6, 12],
        },
        "accident": {
            "primary": [8],
            "supporting": [6, 12, 2, 7],
            "karakas": ["Mars", "Rahu", "Saturn", "Ketu"],
            "adverse": [1, 9],
        },
        "father": {
            "primary": [9],
            "supporting": [1, 5, 10, 11, 2],
            "karakas": ["Sun", "Jupiter"],
            "adverse": [6, 8, 12],
        },
        "career": {
            "primary": [10],
            "supporting": [1, 5, 9, 11, 2, 7],
            "karakas": ["Sun", "Saturn", "Mercury", "Jupiter", "Mars"],
            "adverse": [8, 12],
        },
        "gains": {
            "primary": [11],
            "supporting": [2, 5, 9, 10, 1],
            "karakas": ["Jupiter", "Mercury"],
            "adverse": [6, 8, 12],
        },
        "foreign": {
            "primary": [12],
            "supporting": [9, 3, 8, 4],
            "karakas": ["Saturn", "Rahu", "Ketu", "Jupiter"],
            "adverse": [2, 4],
        },
    }

    # Weights assigned to the 5 Dasha levels (Total sum = 6.0 raw base)
    LEVEL_WEIGHTS = {
        "MD": 1.75,
        "AD": 1.50,
        "PD": 1.25,
        "Sookshma": 0.85,
        "Praana": 0.65,
    }


    @classmethod
    def evaluate_event_dasha(
        cls,
        graph: LinkedChartGraph,
        dasha: DashaPeriod5Level,
        event_type: str,
    ) -> CognitivePredictionResult:
        """
        Main cognitive reasoning pipeline for evaluating event potential during a 5-level Dasha.
        """
        event_cfg = cls.EVENT_HOUSES.get(event_type.lower(), cls.EVENT_HOUSES["marriage"])
        primary_houses = event_cfg["primary"]
        supporting_houses = event_cfg["supporting"]
        karakas = event_cfg["karakas"]

        levels = [
            ("MD", dasha.mahadasha),
            ("AD", dasha.antardasha),
            ("PD", dasha.pratyantardasha),
            ("Sookshma", dasha.sookshma),
            ("Praana", dasha.praana),
        ]

        total_raw_score = 0.0
        assessments: List[DashaLevelAssessment] = []
        rule_traces: List[str] = []

        for lvl_name, lord in levels:
            node = graph.get_node(lord)
            lvl_weight = cls.LEVEL_WEIGHTS[lvl_name]
            reasons = []

            if not node:
                assessments.append(
                    DashaLevelAssessment(
                        level_name=lvl_name,
                        lord=lord,
                        is_house_lord=False,
                        is_occupant=False,
                        aspect_strength=0.0,
                        dignity_score=4,
                        level_score=0.0,
                        reasons=[f"Lord {lord} not found in chart node graph."],
                    )
                )
                continue

            # 1. House Ownership Check
            rules_primary = any(h in node.owned_houses for h in primary_houses)
            rules_supporting = any(h in node.owned_houses for h in supporting_houses)

            # 2. Placement Check from Lagna & Chandra Lagna (Sudarshana Synthesis)
            is_in_primary = (node.house_from_lagna in primary_houses) or (node.house_from_chandra in primary_houses)
            is_in_supporting = (node.house_from_lagna in supporting_houses) or (node.house_from_chandra in supporting_houses)
            is_karaka = lord in karakas

            # 3. Aspect on primary houses
            aspect_str = 0.0
            for h in primary_houses:
                for target_h, asp_val in node.aspects_cast:
                    if target_h == h and asp_val > aspect_str:
                        aspect_str = asp_val

            # Compute Level Contribution Score
            score_factor = 0.0
            if rules_primary:
                score_factor += 0.55
                reasons.append(f"Rules primary house {primary_houses}")
            if rules_supporting:
                score_factor += 0.30
                reasons.append(f"Rules supporting house {supporting_houses}")
            if is_in_primary:
                score_factor += 0.45
                reasons.append(f"Occupies primary house (Lagna:{node.house_from_lagna}/Chandra:{node.house_from_chandra})")
            elif is_in_supporting:
                score_factor += 0.25
                reasons.append(f"Occupies supporting house (Lagna:{node.house_from_lagna}/Chandra:{node.house_from_chandra})")
            if aspect_str > 0.0:
                score_factor += 0.35 * aspect_str
                reasons.append(f"Casts {aspect_str:.2f} aspect on primary house")
            if is_karaka:
                score_factor += 0.35
                reasons.append(f"Is natural Naisargika Karaka for {event_type}")

            # Dignity multiplier from Base-2 Exponential Strength
            dignity_val = int(node.dignity)
            dignity_multiplier = 0.70 + (0.075 * (dignity_val - 1))
            level_contrib = score_factor * lvl_weight * dignity_multiplier


            total_raw_score += level_contrib
            rule_traces.extend([f"[{lvl_name}:{lord}] {r}" for r in reasons])

            assessments.append(
                DashaLevelAssessment(
                    level_name=lvl_name,
                    lord=lord,
                    is_house_lord=rules_primary or rules_supporting,
                    is_occupant=is_in_primary or is_in_supporting,
                    aspect_strength=aspect_str,
                    dignity_score=dignity_val,
                    level_score=round(level_contrib, 3),
                    reasons=reasons,
                )
            )

        # 4. Upagraha Interference Modifier
        upagraha_mod = UpagrahaRulesEngine.get_domain_modifier(
            domain=event_type.lower(),
            interferences=graph.upagraha_interferences,
        )

        for inf in graph.upagraha_interferences:
            if inf.target_domain in (event_type.lower(), "general"):
                rule_traces.append(f"[UPAGRAHA:{inf.rule_name}] {inf.description} (Δ={inf.weight_delta:+.2f})")

        # 5. Final Cognitive Probability Score (Clamped to 0.0 to 9.0)
        final_score = total_raw_score + upagraha_mod
        final_score = max(0.0, min(9.0, final_score))
        final_score = round(final_score, 2)

        # Event is considered probable if score >= 5.0 (typically 3+ levels aligning)
        is_probable = final_score >= 5.0

        summary = (
            f"Cognitive Prediction for {event_type.upper()}: Score {final_score}/9.0. "
            f"Active levels: {sum(1 for a in assessments if a.level_score > 0.3)}/5. "
            f"Upagraha Modifier: {upagraha_mod:+.2f}."
        )

        return CognitivePredictionResult(
            event_type=event_type,
            cognitive_score=final_score,
            is_probable=is_probable,
            level_assessments=assessments,
            upagraha_modifier=upagraha_mod,
            reasoning_summary=summary,
            rule_traces=rule_traces,
        )


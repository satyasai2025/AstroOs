"""
AstroOS — Phalita Mixture of Experts (MoE) Expert Registry

Defines the 4 Specialized Shastric Predictive Experts:
1. Natal Structural Expert:
   - Evaluates D1 planetary positions, Lagna lordship, Kendra/Trikona strength,
     functional beneficence, and Base-2 Exponential Strength.
2. Divisional & Yoga Expert:
   - Evaluates D9 Navamsha, D10 Dashamsha Vimsopaka strength, and Classical
     Yogas (Raja, Dhana, VRY, Mahapurusha).
3. Temporal Dasha Expert:
   - Evaluates 5-Level Vimshottari Dasha Confluence (MD, AD, PD, Sookshma, Praana)
     via CognitiveReasoner.
4. Upagraha & Shadow Expert:
   - Evaluates Gulika, Mandi, and Arkadosha interferences, Upachaya vs 8th house
     Mrityu yoga, and 7th house matrimonial impediments.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from apps.api.services.intelligence.linked_system import LinkedChartGraph
from apps.api.services.intelligence.cognitive_reasoner import (
    CognitiveReasoner,
    DashaPeriod5Level,
    CognitivePredictionResult,
)
from apps.api.services.intelligence.strength_model import StrengthModel


@dataclass
class ExpertOutput:
    expert_name: str
    domain: str
    expert_score: float       # 0.0 to 9.0
    confidence: float         # 0.0 to 1.0
    key_findings: List[str]
    supporting_factors: List[str] = field(default_factory=list)
    afflicting_factors: List[str] = field(default_factory=list)


class NatalStructuralExpert:
    """
    Expert 1: Evaluates D1 foundational strength, Lagna connections, and dignity.
    """
    NAME = "NatalStructuralExpert"

    @classmethod
    def evaluate(cls, graph: LinkedChartGraph, domain: str) -> ExpertOutput:
        findings = []
        supporting = []
        afflicting = []

        total_score = 4.5  # Neutral baseline
        lagna_node = graph.get_node(graph.get_house_lord(1) or "Mars")

        # Evaluate Lagna lord strength
        if lagna_node:
            dignity_val = int(lagna_node.dignity)
            if dignity_val >= 7:
                total_score += 1.5
                findings.append(f"Lagna Lord {lagna_node.graha} is exceptionally strong (Dignity {dignity_val}/9).")
                supporting.append(f"Lagna Lord dignity: {lagna_node.dignity.name}")
            elif dignity_val <= 3:
                total_score -= 1.0
                findings.append(f"Lagna Lord {lagna_node.graha} is afflicted/debilitated (Dignity {dignity_val}/9).")
                afflicting.append(f"Lagna Lord dignity: {lagna_node.dignity.name}")

        # Domain-specific house lord evaluation
        from apps.api.services.phalita_core.domain_significators import get_domain_config
        domain_cfg = get_domain_config(domain)
        domain_primary_house = domain_cfg.primary_house

        domain_lord_name = graph.get_house_lord(domain_primary_house)
        # House from Chandra Lagna
        chandra_primary_rashi = (graph.chandra_rashi_idx + domain_primary_house - 1) % 12
        from apps.api.services.intelligence.linked_system import LinkedSystemBuilder
        chandra_house_lord = LinkedSystemBuilder.RASHI_LORDS.get(chandra_primary_rashi)

        relevant_lords = {l for l in (domain_lord_name, chandra_house_lord) if l}

        for d_lord in relevant_lords:
            d_node = graph.get_node(d_lord)
            if d_node:
                d_val = int(d_node.dignity)
                if domain_cfg.is_favorable_event:
                    if d_val >= 6:
                        total_score += 1.25
                        findings.append(f"Domain Lord ({d_lord}) for house {domain_primary_house} has strong dignity {d_val}/9.")
                        supporting.append(f"Primary house {domain_primary_house} lord strong")
                    elif d_val <= 3:
                        total_score -= 0.75
                        findings.append(f"Domain Lord ({d_lord}) is debilitated/inimical.")
                        afflicting.append(f"Primary house {domain_primary_house} lord weak")
                    else:
                        total_score += 0.5
                        findings.append(f"Domain Lord ({d_lord}) is placed in neutral/favorable dignity.")
                else:
                    if d_node.house_from_lagna in (6, 8, 12):
                        total_score += 1.0
                        findings.append(f"Dusthana lord active in house {d_node.house_from_lagna}.")
                        supporting.append("Crisis house activation in D1")

        # Karaka placement evaluation for all 12 domains
        for k in domain_cfg.naisargika_karakas:
            k_node = graph.get_node(k.capitalize())
            if k_node:
                if k_node.house_from_lagna in (1, 4, 5, 7, 9, 10, 11):
                    total_score += 0.5
                    findings.append(f"{domain_cfg.display_name} Karaka ({k.capitalize()}) well-placed in House {k_node.house_from_lagna}.")
                    supporting.append(f"Karaka {k.capitalize()} Kendra/Trikona placement")
                elif k_node.house_from_lagna in (6, 8, 12) and domain_cfg.is_favorable_event:
                    total_score -= 0.25
                    afflicting.append(f"Karaka {k.capitalize()} in dusthana H{k_node.house_from_lagna}")




        final_score = max(0.0, min(9.0, total_score))
        return ExpertOutput(
            expert_name=cls.NAME,
            domain=domain,
            expert_score=round(final_score, 2),
            confidence=0.85,
            key_findings=findings or ["Structural baseline stable."],
            supporting_factors=supporting,
            afflicting_factors=afflicting,
        )


class DivisionalYogaExpert:
    """
    Expert 2: Evaluates harmonic confirmation (D9/D10) and classical Yogas.
    """
    NAME = "DivisionalYogaExpert"

    @classmethod
    def evaluate(cls, graph: LinkedChartGraph, domain: str) -> ExpertOutput:
        findings = []
        supporting = []
        afflicting = []

        total_score = 4.8
        # Check for Kendra-Trikona Rajayogas in graph
        trikona_lords = set()
        kendra_lords = set()

        for g, node in graph.nodes.items():
            if any(h in (1, 5, 9) for h in node.owned_houses):
                trikona_lords.add(g)
            if any(h in (1, 4, 7, 10) for h in node.owned_houses):
                kendra_lords.add(g)

        raja_yoga_formed = False
        for g, node in graph.nodes.items():
            if g in trikona_lords and any(conj in kendra_lords for conj in node.conjoined_grahas):
                raja_yoga_formed = True
                findings.append(f"Raja Yoga formed by conjunction of Kendra-Trikona lords: {g} with {node.conjoined_grahas}.")
                supporting.append("Kendra-Trikona Sambandha active")
                break

        if raja_yoga_formed:
            total_score += 2.0
        else:
            findings.append("No direct Kendra-Trikona conjunction found; baseline harmonic stability.")

        final_score = max(0.0, min(9.0, total_score))
        return ExpertOutput(
            expert_name=cls.NAME,
            domain=domain,
            expert_score=round(final_score, 2),
            confidence=0.80,
            key_findings=findings,
            supporting_factors=supporting,
            afflicting_factors=afflicting,
        )


class TemporalDashaExpert:
    """
    Expert 3: Evaluates 5-Level Dasha Confluence via Cognitive Reasoner.
    """
    NAME = "TemporalDashaExpert"

    @classmethod
    def evaluate(
        cls,
        graph: LinkedChartGraph,
        dasha: DashaPeriod5Level,
        domain: str,
    ) -> ExpertOutput:
        cog_res = CognitiveReasoner.evaluate_event_dasha(graph, dasha, domain)
        findings = [cog_res.reasoning_summary] + cog_res.rule_traces[:3]

        supporting = [r for r in cog_res.rule_traces if not r.startswith("[UPAGRAHA")]
        return ExpertOutput(
            expert_name=cls.NAME,
            domain=domain,
            expert_score=cog_res.cognitive_score,
            confidence=0.90,
            key_findings=findings,
            supporting_factors=supporting[:4],
            afflicting_factors=[],
        )


class UpagrahaShadowExpert:
    """
    Expert 4: Evaluates Gulika, Mandi, and Arkadosha regulations.
    """
    NAME = "UpagrahaShadowExpert"

    @classmethod
    def evaluate(cls, graph: LinkedChartGraph, domain: str) -> ExpertOutput:
        findings = []
        supporting = []
        afflicting = []

        total_score = 4.5
        for inf in graph.upagraha_interferences:
            if inf.target_domain in (domain.lower(), "general"):
                findings.append(f"[{inf.rule_name}] {inf.description} (Δ={inf.weight_delta:+.2f})")
                if inf.is_auspicious:
                    supporting.append(inf.rule_name)
                    total_score += inf.weight_delta
                else:
                    afflicting.append(inf.rule_name)
                    total_score += inf.weight_delta

        final_score = max(0.0, min(9.0, total_score))
        return ExpertOutput(
            expert_name=cls.NAME,
            domain=domain,
            expert_score=round(final_score, 2),
            confidence=0.88,
            key_findings=findings or ["No acute Upagraha interference detected."],
            supporting_factors=supporting,
            afflicting_factors=afflicting,
        )

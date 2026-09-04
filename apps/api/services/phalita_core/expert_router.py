"""
AstroOS — Phalita Mixture of Experts (MoE) Dynamic Expert Router

Implements the Attention / Gating mechanism across the 4 Shastric Experts:
1. Structural Expert Weight (\alpha_1)
2. Divisional/Yoga Expert Weight (\alpha_2)
3. Temporal Dasha Expert Weight (\alpha_3)
4. Upagraha/Shadow Expert Weight (\alpha_4)

Applies domain-adaptive softmax routing distribution:
- Marriage Queries: High weight on Temporal Dasha & Upagraha (Mandi delay factor).
- Career Queries: High weight on Divisional/Yogas (Rajayogas) & Temporal Dasha.
- Health/Accident Queries: Heavy weight on Upagraha (Gulika 8th Mrityu) & Temporal Dasha.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import math


from apps.api.services.phalita_core.domain_significators import get_domain_config


@dataclass
class GatingWeights:
    structural: float
    divisional: float
    temporal: float
    upagraha: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "NatalStructuralExpert": round(self.structural, 4),
            "DivisionalYogaExpert": round(self.divisional, 4),
            "TemporalDashaExpert": round(self.temporal, 4),
            "UpagrahaShadowExpert": round(self.upagraha, 4),
        }


class ExpertRouter:
    """
    Computes normalized gating weights for a given domain and chart context across all 12 domains.
    """

    @classmethod
    def route(cls, domain: str) -> GatingWeights:
        cfg = get_domain_config(domain)
        logits = cfg.router_logits

        # Softmax normalization: exp(l_i) / sum(exp(l_j))
        exp_struct = math.exp(logits.get("structural", 1.4))
        exp_div = math.exp(logits.get("divisional", 1.5))
        exp_temp = math.exp(logits.get("temporal", 2.0))
        exp_upa = math.exp(logits.get("upagraha", 1.5))


        total_exp = exp_struct + exp_div + exp_temp + exp_upa

        return GatingWeights(
            structural=exp_struct / total_exp,
            divisional=exp_div / total_exp,
            temporal=exp_temp / total_exp,
            upagraha=exp_upa / total_exp,
        )

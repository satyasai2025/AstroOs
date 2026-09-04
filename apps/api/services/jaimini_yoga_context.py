"""
AstroOS — Jaimini Yoga Context (Layer 6: Calculation Engine)

Bundles every already-computed Jaimini result one yoga rule might need,
assembled once per evaluation rather than per rule — mirrors
yoga_predicates.YogaContext's role for Parashari yogas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import ArudhaResult, CharaKarakaResult, KarakamsaResult, RashiAspectResult


@dataclass(frozen=True)
class JaiminiYogaContext:
    """
    Everything one chart's Jaimini yoga evaluation needs.

    karakamsa is Optional because it requires a D9 chart the caller may
    not have computed — rules that need it must check for None and
    report themselves as not-matched rather than crash the whole
    evaluation run over one missing optional input (see
    jaimini_yogas/karakamsa_yoga.py for the pattern).
    """

    d1_chart: D1Chart
    chara_karaka: CharaKarakaResult
    arudha: ArudhaResult
    rashi_aspect: RashiAspectResult
    karakamsa: Optional[KarakamsaResult] = None

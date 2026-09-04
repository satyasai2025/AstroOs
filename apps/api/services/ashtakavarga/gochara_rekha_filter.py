"""
AstroOS — Gochara Rekha Filter (Jha Ashtakavarga Transit Framework)
===================================================================
Source: Vinay Jha's Kundalee (Phalit.kkk - frmAshtakvargDetail @ 1380142)

Exact Shastric Tooltip:
  "In Sarva-rekha, all 8 vargas are shown if number of days is <-48,
   else lagna-rekha is omitted upto number of days <1096,
   above which even Chandra-rekha is omitted in Sarva-rekha."

Rules:
  Tier 1 (Short-term Gochara / Daily Transits): days < 48
    - All 8 vargas included (7 classical grahas + Lagna).
    - Grand total: 386 bindus (337 + 49).
    - Fast planetary transit sensitivity (Moon, Mercury, Venus, Sun).

  Tier 2 (Medium-term Gochara / Seasonal Transits): 48 <= days < 1096 (~3 years)
    - Lagna-rekha is omitted.
    - Standard 7 classical grahas included (Sun to Saturn).
    - Grand total: 337 bindus.
    - Medium planetary transit sensitivity (Mars, Sun, Venus, Jupiter).

  Tier 3 (Long-term Gochara / Major Ingresses): days >= 1096 (~3+ years)
    - Both Lagna-rekha AND Chandra-rekha are omitted.
    - Only slow-moving grahas (6 grahas: Sun, Mars, Mercury, Jupiter, Venus, Saturn).
    - Grand total: 288 bindus (337 - 49 Moon bindus).
    - Long-term structural transit sensitivity (Jupiter, Saturn, Rahu/Ketu).

Method Note on Boundary Ambiguity:
  In the binary tooltip, "<-48" and "<1096" leave it ambiguous whether days 48
  and 1096 are strictly inclusive or exclusive in practice.
  The unit tests pin both sides (47, 48, 49 and 1095, 1096, 1097), and final
  inclusive/exclusive boundary parity is queued for JHora chart verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from packages.shared.ashtakavarga_bindu_table import EXPECTED_GRAND_TOTAL, EXPECTED_PLANET_TOTALS

LAGNA_BAV_TOTAL = 49
TOTAL_8_VARGAS = EXPECTED_GRAND_TOTAL + LAGNA_BAV_TOTAL  # 386
TOTAL_6_VARGAS = EXPECTED_GRAND_TOTAL - EXPECTED_PLANET_TOTALS["moon"]  # 337 - 49 = 288

SHORT_TERM_DAYS_LIMIT = 48
MEDIUM_TERM_DAYS_LIMIT = 1096


class RekhaFilterTier(str, Enum):
    ALL_8_VARGAS = "all_8_vargas"              # days < 48 (386 bindus)
    SEVEN_GRAHAS_STANDARD = "seven_grahas"      # 48 <= days < 1096 (337 bindus)
    SIX_SLOW_GRAHAS = "six_slow_grahas"        # days >= 1096 (288 bindus)


@dataclass(frozen=True)
class GocharaRekhaFilterResult:
    duration_days: int
    tier: RekhaFilterTier
    included_contributors: list[str]
    omitted_contributors: list[str]
    expected_total_bindus: int
    bav_lagna_option: int                       # 1=Natal Graha, 2=Natal Lagna (default), 3=Gochara Graha
    trace: str


class GocharaRekhaFilter:
    """Filters Ashtakavarga rekhas dynamically based on transit window duration."""

    def evaluate_transit_filter(
        self,
        duration_days: int,
        bav_lagna_option: int = 2,
    ) -> GocharaRekhaFilterResult:
        if duration_days <= 0:
            raise ValueError(f"duration_days must be an integer > 0, got {duration_days}")

        if duration_days < SHORT_TERM_DAYS_LIMIT:
            tier = RekhaFilterTier.ALL_8_VARGAS
            included = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna"]
            omitted = []
            expected_total = TOTAL_8_VARGAS  # 386
            trace = f"Duration {duration_days}d < 48d: All 8 vargas included (7 Grahas + Lagna, Total = 386 bindus)."

        elif duration_days < MEDIUM_TERM_DAYS_LIMIT:
            tier = RekhaFilterTier.SEVEN_GRAHAS_STANDARD
            included = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
            omitted = ["lagna"]
            expected_total = EXPECTED_GRAND_TOTAL  # 337
            trace = f"Duration {duration_days}d (48 <= d < 1096): Lagna-rekha omitted (Canonical 337 bindus)."

        else:
            tier = RekhaFilterTier.SIX_SLOW_GRAHAS
            included = ["sun", "mars", "mercury", "jupiter", "venus", "saturn"]
            omitted = ["lagna", "moon"]
            expected_total = TOTAL_6_VARGAS  # 288
            trace = f"Duration {duration_days}d >= 1096d: Both Lagna-rekha and Chandra-rekha omitted (6 slow grahas, Total = 288 bindus)."

        return GocharaRekhaFilterResult(
            duration_days=duration_days,
            tier=tier,
            included_contributors=included,
            omitted_contributors=omitted,
            expected_total_bindus=expected_total,
            bav_lagna_option=bav_lagna_option,
            trace=trace,
        )
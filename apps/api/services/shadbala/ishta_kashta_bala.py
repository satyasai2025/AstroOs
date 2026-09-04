"""
AstroOS — Ishta/Kashta Bala (SHADBALA-ISHTA / SHADBALA-KASHTA)

Classical formula (BPHS, and universally cited across later texts):
    Ishta Bala  = sqrt(Uchcha Bala x Chesta Bala)
    Kashta Bala = 60 - Ishta Bala

Both source values are already computed elsewhere in this codebase
(UchchaBalaCalculator, ChestaBalaCalculator), each in Shashtiamsas
(0-60), so the geometric mean is also guaranteed to land in [0, 60] —
same units, no rescaling needed.

Scope note: Chesta Bala in this codebase is only computed for the 5
non-luminary grahas (Mars, Mercury, Jupiter, Venus, Saturn) — see
chesta_bala.py's module docstring for why Sun/Moon are excluded (they
use a different classical treatment this codebase doesn't compute).
Ishta/Kashta Bala therefore inherits that same 5-planet scope here
rather than fabricating a Chesta Bala figure for Sun/Moon to force a
7-planet result.
"""

from __future__ import annotations

import math

from apps.api.domain.shadbala import BalaComponentResult

_ISHTA_ID = "SHADBALA-ISHTA"
_ISHTA_NAME = "Ishta Bala"
_KASHTA_ID = "SHADBALA-KASHTA"
_KASHTA_NAME = "Kashta Bala"
_RULE_VERSION = "1.0"

_MAX_SHASHTIAMSA = 60.0


class IshtaKashtaBalaCalculator:
    """
    Stateless — derives Ishta/Kashta Bala from already-computed Uchcha
    Bala and Chesta Bala results (does not recompute either itself).
    """

    def calculate_all(
        self,
        uchcha_results: list[BalaComponentResult],
        chesta_results: list[BalaComponentResult],
    ) -> tuple[list[BalaComponentResult], list[BalaComponentResult]]:
        """Returns (ishta_bala_results, kashta_bala_results), one entry per
        planet present in BOTH input lists (see module docstring on scope)."""
        uchcha_by_planet = {r.planet: r for r in uchcha_results}
        chesta_by_planet = {r.planet: r for r in chesta_results}
        shared_planets = [p for p in uchcha_by_planet if p in chesta_by_planet]

        ishta_results: list[BalaComponentResult] = []
        kashta_results: list[BalaComponentResult] = []

        for planet in shared_planets:
            uchcha = uchcha_by_planet[planet].value_shashtiamsas
            chesta = chesta_by_planet[planet].value_shashtiamsas
            ishta = math.sqrt(max(0.0, uchcha) * max(0.0, chesta))
            kashta = _MAX_SHASHTIAMSA - ishta

            ishta_trace = (
                f"Step 1: Uchcha Bala for {planet} = {uchcha:.4f} Shashtiamsas",
                f"Step 2: Chesta Bala for {planet} = {chesta:.4f} Shashtiamsas",
                f"Step 3: Ishta Bala = sqrt({uchcha:.4f} * {chesta:.4f}) = {ishta:.4f}",
            )
            kashta_trace = (
                f"Step 1: Ishta Bala for {planet} = {ishta:.4f} Shashtiamsas",
                f"Step 2: Kashta Bala = 60 - {ishta:.4f} = {kashta:.4f}",
            )

            ishta_results.append(BalaComponentResult(
                component_id=_ISHTA_ID, component_name=_ISHTA_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=round(ishta, 4), trace=ishta_trace,
            ))
            kashta_results.append(BalaComponentResult(
                component_id=_KASHTA_ID, component_name=_KASHTA_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=round(kashta, 4), trace=kashta_trace,
            ))

        return ishta_results, kashta_results

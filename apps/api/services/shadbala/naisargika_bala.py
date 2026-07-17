"""
AstroOS — Naisargika Bala (SHADBALA-NAISARGIKA)

Natural/innate strength — a fixed, chart-independent ranking. This is
the simplest Shadbala component: pure constant lookup, zero dependencies
on chart data, built first per the Design Audit's Phase 1 ordering.

Classical values (BPHS Ch. 27) divide 60 Shashtiamsas among the 7
classical grahas in a fixed descending arithmetic sequence — n * 60/7
for n = 7..1, assigned in order Sun > Moon > Venus > Jupiter > Mercury >
Mars > Saturn. Not chart-dependent, so there's no "trace" of arithmetic
performed on the birth data — the trace here documents the lookup
itself for consistency with every other component's auditability.
"""

from __future__ import annotations

from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-NAISARGIKA"
_COMPONENT_NAME = "Naisargika Bala"
_RULE_VERSION = "1.0"

# n * 60/7 Shashtiamsas, n=7..1, in fixed classical order.
_NAISARGIKA_ORDER = ["sun", "moon", "venus", "jupiter", "mercury", "mars", "saturn"]
_NAISARGIKA_VALUES: dict[str, float] = {
    planet: (7 - i) * 60.0 / 7.0 for i, planet in enumerate(_NAISARGIKA_ORDER)
}


class NaisargikaBalaCalculator:
    """Stateless — pure lookup table, no chart dependency at all."""

    def calculate(self, planet: str) -> BalaComponentResult:
        if planet not in _NAISARGIKA_VALUES:
            raise ValueError(
                f"Naisargika Bala is only defined for the 7 classical grahas, got {planet!r}"
            )

        value = _NAISARGIKA_VALUES[planet]
        trace = (
            f"Step 1: {planet} classical natural-strength rank → "
            f"{_NAISARGIKA_ORDER.index(planet) + 1} of 7 (Sun strongest, Saturn weakest)",
            f"Step 2: value = (7 - rank_index) * 60/7 = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(self) -> list[BalaComponentResult]:
        return [self.calculate(planet) for planet in _NAISARGIKA_ORDER]

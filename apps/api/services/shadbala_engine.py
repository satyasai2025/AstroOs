"""
AstroOS — Shadbala Engine (Module 9)

Orchestrates the Shadbala component calculators against a D1 chart.

Status: Naisargika, Dig, and Drik Bala (Phase 1) are complete. **Sthana
Bala is now fully complete (5 of 5 sub-components: Uchcha, Kendradi,
Saptavargaja, Drekkana, Ojayugmarasyamsa).** **Kala Bala is now
effectively complete too**, except for one genuine, explicitly tracked
scope gap: Paksha, Tribhaga, Ayana, Nathonnata, Dina-Hora, and Yuddha
Bala are all implemented — only Varsha/Masa lord (half of the classical
"Varsha-Masa-Dina-Hora Bala"; Dina+Hora lord ARE implemented) remains,
and that's a genuine capability gap (needs backward astronomical
event-searching this codebase doesn't have), not a coefficient caveat
like the approximations used throughout the rest of Shadbala.

Four components have a genuinely different dependency shape from the
rest — they need more than just the already-built D1 chart:
  - Saptavargaja Bala and Ojayugmarasyamsa Bala each need to COMPUTE
    additional divisional charts (Saptavargaja: D2/D3/D7/D9/D12/D30;
    Ojayugmarasyamsa: D9 only) — both need a `divisional_engine`.
  - Tribhaga Bala, Nathonnata Bala, and Dina-Hora Bala all need to find
    the FOLLOWING sunrise (to close out a nighttime birth's night
    period, locate local midnight, or continue the hora cycle into the
    night) — needs the process-wide `EphemerisWrapper` itself, plus
    latitude/longitude.
Their compute_*() methods take extra parameters accordingly, unlike
every other compute_*() method here — an honest reflection of the real
dependency, not a design inconsistency.

Deliberately NOT exposing a "total Shadbala" sum here — with components
still partial or entirely missing, a sum would misrepresent an
incomplete result as a complete one. Each compute_*() method returns its
own components separately; `not_yet_implemented_components()` makes
every remaining gap explicit by name rather than letting a caller
assume completeness.

Not wired into any router or persistence layer — same scope discipline
as every engine before it (HouseEngine, YogaEngine).
"""

from __future__ import annotations

from datetime import datetime

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.shadbala.ayana_bala import AyanaBalaCalculator
from apps.api.services.shadbala.chesta_bala import ChestaBalaCalculator
from apps.api.services.shadbala.dig_bala import DigBalaCalculator
from apps.api.services.shadbala.dina_hora_bala import DinaHoraBalaCalculator
from apps.api.services.shadbala.drekkana_bala import DrekkanaBalaCalculator
from apps.api.services.shadbala.drik_bala import DrikBalaCalculator
from apps.api.services.shadbala.kendradi_bala import KendradiBalaCalculator
from apps.api.services.shadbala.naisargika_bala import NaisargikaBalaCalculator
from apps.api.services.shadbala.nathonnata_bala import NathonnataBalaCalculator
from apps.api.services.shadbala.ojayugmarasyamsa_bala import OjayugmarasyamsaBalaCalculator
from apps.api.services.shadbala.paksha_bala import PakshaBalaCalculator
from apps.api.services.shadbala.saptavargaja_bala import SaptavargajaBalaCalculator
from apps.api.services.shadbala.tribhaga_bala import TribhagaBalaCalculator
from apps.api.services.shadbala.uchcha_bala import UchchaBalaCalculator
from apps.api.services.shadbala.yuddha_bala import YuddhaBalaCalculator


class ShadbalaEngine:
    """
    Orchestrator for every implemented Shadbala component/sub-component
    so far. See module docstring for exactly what is and isn't covered.

    `divisional_engine` and `ephemeris_wrapper` are both optional at
    construction (default None) — only required if the caller will use
    `compute_saptavargaja_bala()` / `compute_tribhaga_bala()`
    respectively; every other compute_*() method works without them.
    """

    def __init__(
        self,
        naisargika_calculator: NaisargikaBalaCalculator | None = None,
        dig_calculator: DigBalaCalculator | None = None,
        drik_calculator: DrikBalaCalculator | None = None,
        chesta_calculator: ChestaBalaCalculator | None = None,
        ayana_calculator: AyanaBalaCalculator | None = None,
        paksha_calculator: PakshaBalaCalculator | None = None,
        uchcha_calculator: UchchaBalaCalculator | None = None,
        kendradi_calculator: KendradiBalaCalculator | None = None,
        drekkana_calculator: DrekkanaBalaCalculator | None = None,
        yuddha_calculator: YuddhaBalaCalculator | None = None,
        divisional_engine: DivisionalEngine | None = None,
        ojayugmarasyamsa_calculator: OjayugmarasyamsaBalaCalculator | None = None,
        ephemeris_wrapper: EphemerisWrapper | None = None,
    ) -> None:
        self._naisargika = naisargika_calculator or NaisargikaBalaCalculator()
        self._dig = dig_calculator or DigBalaCalculator()
        self._drik = drik_calculator or DrikBalaCalculator()
        self._chesta = chesta_calculator or ChestaBalaCalculator()
        self._ayana = ayana_calculator or AyanaBalaCalculator()
        self._paksha = paksha_calculator or PakshaBalaCalculator()
        self._uchcha = uchcha_calculator or UchchaBalaCalculator()
        self._kendradi = kendradi_calculator or KendradiBalaCalculator()
        self._drekkana = drekkana_calculator or DrekkanaBalaCalculator()
        self._yuddha = yuddha_calculator or YuddhaBalaCalculator()
        self._saptavargaja = (
            SaptavargajaBalaCalculator(divisional_engine) if divisional_engine is not None else None
        )
        self._ojayugmarasyamsa = (
            ojayugmarasyamsa_calculator if ojayugmarasyamsa_calculator is not None
            else (OjayugmarasyamsaBalaCalculator(divisional_engine) if divisional_engine is not None else None)
        )
        self._tribhaga = (
            TribhagaBalaCalculator(ephemeris_wrapper) if ephemeris_wrapper is not None else None
        )
        self._dina_hora = (
            DinaHoraBalaCalculator(ephemeris_wrapper) if ephemeris_wrapper is not None else None
        )
        self._nathonnata = (
            NathonnataBalaCalculator(ephemeris_wrapper) if ephemeris_wrapper is not None else None
        )

    def compute_phase1_components(
        self, chart: D1Chart
    ) -> dict[str, list[BalaComponentResult]]:
        """Naisargika + Dig + Drik Bala — see module docstring for what's NOT here."""
        return {
            "naisargika_bala": self._naisargika.calculate_all(),
            "dig_bala": self._dig.calculate_all(chart.planets, chart.houses),
            "drik_bala": self._drik.calculate_all(chart.aspects),
        }

    def compute_phase2_components(
        self, chart: D1Chart
    ) -> dict[str, list[BalaComponentResult]]:
        """Chesta + Paksha + Ayana + Yuddha Bala (Kala Bala sub-components) — see module docstring."""
        return {
            "chesta_bala": self._chesta.calculate_all(chart.planets),
            "paksha_bala": self._paksha.calculate_all(chart.planets),
            "ayana_bala": self._ayana.calculate_all(chart.planets),
            "yuddha_bala": self._yuddha.calculate_all(chart.planets),
        }

    def compute_sthana_bala_components(
        self, chart: D1Chart
    ) -> dict[str, list[BalaComponentResult]]:
        """
        Uchcha + Kendradi + Drekkana Bala — 3 of Sthana Bala's 5
        sub-components that need only the already-built D1 chart.
        Saptavargaja Bala and Ojayugmarasyamsa Bala (the other 2) are
        separate — see compute_saptavargaja_bala() and
        compute_ojayugmarasyamsa_bala() — since both need more than
        just this chart. Sthana Bala is fully implemented across these
        3 methods combined.
        """
        return {
            "uchcha_bala": self._uchcha.calculate_all(chart.planets),
            "kendradi_bala": self._kendradi.calculate_all(chart.planets),
            "drekkana_bala": self._drekkana.calculate_all(chart.planets),
        }

    def compute_saptavargaja_bala(
        self,
        chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> list[BalaComponentResult]:
        """
        Sthana Bala's cross-varga sub-component. Requires this engine to
        have been constructed with a `divisional_engine` — raises
        RuntimeError otherwise, so a missing wiring mistake fails loudly.
        """
        if self._saptavargaja is None:
            raise RuntimeError(
                "ShadbalaEngine.compute_saptavargaja_bala() requires a "
                "divisional_engine to be provided at construction time."
            )
        return self._saptavargaja.calculate_all(
            chart, birth_datetime_utc=birth_datetime_utc, latitude=latitude,
            longitude=longitude, ayanamsa=ayanamsa, house_system=house_system,
        )

    def compute_ojayugmarasyamsa_bala(
        self,
        chart: D1Chart,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
        house_system: str = "W",
    ) -> list[BalaComponentResult]:
        """
        Sthana Bala's last sub-component (D1 + D9 odd/even sign check).
        Requires this engine to have been constructed with a
        `divisional_engine` — raises RuntimeError otherwise.
        """
        if self._ojayugmarasyamsa is None:
            raise RuntimeError(
                "ShadbalaEngine.compute_ojayugmarasyamsa_bala() requires a "
                "divisional_engine to be provided at construction time."
            )
        return self._ojayugmarasyamsa.calculate_all(
            chart, birth_datetime_utc=birth_datetime_utc, latitude=latitude,
            longitude=longitude, ayanamsa=ayanamsa, house_system=house_system,
        )

    def compute_tribhaga_bala(
        self, chart: D1Chart, *, latitude: float, longitude: float,
    ) -> list[BalaComponentResult]:
        """
        Kala Bala's three-part day/night sub-component. Requires this
        engine to have been constructed with an `ephemeris_wrapper` —
        raises RuntimeError otherwise.
        """
        if self._tribhaga is None:
            raise RuntimeError(
                "ShadbalaEngine.compute_tribhaga_bala() requires an "
                "ephemeris_wrapper to be provided at construction time."
            )
        return self._tribhaga.calculate_all(
            chart.planets, chart.ephemeris, latitude=latitude, longitude=longitude,
        )

    def compute_nathonnata_bala(
        self, chart: D1Chart, *, latitude: float, longitude: float,
    ) -> list[BalaComponentResult]:
        """
        Kala Bala's noon/midnight proximity sub-component. Requires this
        engine to have been constructed with an `ephemeris_wrapper` —
        raises RuntimeError otherwise. Same dependency shape as
        compute_tribhaga_bala() — both need the following sunrise.
        """
        if self._nathonnata is None:
            raise RuntimeError(
                "ShadbalaEngine.compute_nathonnata_bala() requires an "
                "ephemeris_wrapper to be provided at construction time."
            )
        return self._nathonnata.calculate_all(
            chart.planets, chart.ephemeris, latitude=latitude, longitude=longitude,
        )

    def compute_dina_hora_bala(
        self, chart: D1Chart, *, latitude: float, longitude: float,
    ) -> list[BalaComponentResult]:
        """
        Kala Bala's day/hour lordship sub-component — the Dina+Hora half
        of the classical "Varsha-Masa-Dina-Hora Bala" (Varsha/Masa lord
        are a separate, tracked deferral — see dina_hora_bala.py's
        module docstring). Requires this engine to have been constructed
        with an `ephemeris_wrapper` — raises RuntimeError otherwise. Same
        dependency shape as compute_tribhaga_bala()/compute_nathonnata_bala()
        — all three need the following sunrise.
        """
        if self._dina_hora is None:
            raise RuntimeError(
                "ShadbalaEngine.compute_dina_hora_bala() requires an "
                "ephemeris_wrapper to be provided at construction time."
            )
        return self._dina_hora.calculate_all(
            chart.planets, chart.ephemeris, latitude=latitude, longitude=longitude,
        )

    def implemented_components(self) -> list[str]:
        """Which components/sub-components this engine can currently compute."""
        return [
            "naisargika_bala", "dig_bala", "drik_bala",
            "chesta_bala", "kala_bala.paksha_bala", "kala_bala.tribhaga_bala", "kala_bala.ayana_bala",
            "kala_bala.nathonnata_bala", "kala_bala.dina_hora_bala", "kala_bala.yuddha_bala",
            "sthana_bala.uchcha_bala", "sthana_bala.kendradi_bala",
            "sthana_bala.drekkana_bala", "sthana_bala.saptavargaja_bala",
            "sthana_bala.ojayugmarasyamsa_bala",
        ]

    def not_yet_implemented_components(self) -> list[str]:
        """
        The one remaining gap. Sthana Bala is fully implemented, and Kala
        Bala's Yuddha Bala is now done too — only Varsha/Masa lord (the
        other half of the classical "Varsha-Masa-Dina-Hora Bala"; Dina+
        Hora lord ARE implemented, see kala_bala.dina_hora_bala above)
        remains: it needs backward astronomical event-searching (most
        recent Mesha Sankranti, lunar month boundary) this codebase
        doesn't have, plus real definitional variance across traditions
        on which reference event to use — a genuine scope gap, not a
        coefficient caveat like everywhere else in Shadbala. Explicit,
        so callers never have to guess what's missing.
        """
        return [
            "kala_bala.varsha_masa_lord",
        ]

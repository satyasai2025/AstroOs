"""
AstroOS — Report assembler.

One entry point that turns (birth moment, report_type) into the context dict a
report template renders. It is the seam the spec describes:

    Canonical snapshot -> domain facts -> report builder -> template -> PDF

The assembler calls canonical engines and reshapes their output. It computes
nothing astrological itself, and it holds no subscription logic — entitlement
is declared on the ReportDefinition and enforced by the router, so a builder
can never be the place a paywall is accidentally bypassed or duplicated.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from apps.api.domain.report_registry import (
    ReportDefinition,
    ReportDomain,
    get_report,
)
from apps.api.services.birth_chart_report_builder import BirthChartReportBuilder
from apps.api.services.domain_analysis_builder import (
    DOMAIN_SPECS,
    DomainAnalysisBuilder,
)
from apps.api.services.jhora_style_report_builder import JHoraStyleReportBuilder
from apps.api.services.varga_grid_builder import VargaGridBuilder

# Divisional charts shown on the Detailed report's planetary page. The full
# Shodashavarga set is deliberately NOT printed: the client's reference sheets
# show a handful of vargas, and sixteen charts cannot be rendered at a legible
# size inside a fixed five-page budget.
DETAILED_VARGAS: tuple[str, ...] = ("D3", "D7", "D10", "D12")


class ReportAssembler:
    """Builds the render context for any registry-declared report."""

    def __init__(self, wrapper: Any) -> None:
        self._wrapper = wrapper
        self._chart_builder = BirthChartReportBuilder(wrapper)
        self._jhora = JHoraStyleReportBuilder(wrapper)
        self._vargas = VargaGridBuilder(wrapper)
        self._domains = DomainAnalysisBuilder(wrapper)

    def assemble(
        self,
        *,
        report_type: str,
        chart: Any,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        subject_name: str = "Subject",
        gender: str = "",
        place_name: str = "",
        ayanamsa: str = "lahiri",
        ayanamsa_name: str = "Lahiri (CHITRAPAKSHA)",
        house_system_code: str = "Whole Sign",
    ) -> dict[str, Any]:
        """
        Return the template context for `report_type`.

        Raises KeyError for an unknown report_type and NotImplementedError for
        one that is declared in the registry but has no builder yet — a
        declared-but-unbuilt report must fail loudly rather than silently
        render an empty document.
        """
        definition: ReportDefinition = get_report(report_type)
        if not definition.implemented:
            raise NotImplementedError(
                f"{report_type} is declared in the report registry but not yet "
                f"implemented (template={definition.template_name!r})"
            )

        data = self._chart_builder.build_report_data(
            chart=chart,
            subject_name=subject_name,
            gender=gender,
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            place_name=place_name or "—",
            ayanamsa_name=ayanamsa_name,
            house_system_code=house_system_code,
            ayanamsa=ayanamsa,
        )

        # Body table: grahas first, then the derived points, with a rule drawn
        # between the two groups.
        grahas = self._jhora.decorate_graha_rows(data["planets"])
        derived = self._jhora.build_derived_rows(
            birth_datetime_utc=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        if derived:
            derived[0] = {**derived[0], "first_derived": True}
        data["body_rows"] = grahas + derived

        if report_type == "BIRTH_CHART_DETAILED":
            data["varga_charts"] = self._vargas.build(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                vargas=DETAILED_VARGAS,
                ayanamsa=ayanamsa,
            )
            # Divisional info is presented as a placement TABLE rather than
            # more chart diagrams. Four charts alongside the 15-row body table
            # overflowed the page by ~42mm; the table covers the same four
            # vargas in roughly a quarter of the height and is easier to read
            # off than four small kundalis.
            data["varga_table"] = self._varga_placement_table(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
            )
        else:
            data["varga_charts"] = []
            data["varga_table"] = {"vargas": [], "rows": []}

        if definition.domain is ReportDomain.ANALYSIS:
            spec = DOMAIN_SPECS.get(definition.report_type)
            if spec is None:
                # The registry declares a domain report the builder has no
                # spec for. Failing here is deliberate: rendering the two-part
                # template with an empty spec would produce a premium document
                # asserting a verdict over zero houses and zero karakas.
                raise NotImplementedError(
                    f"{definition.report_type} is an ANALYSIS report but "
                    f"DOMAIN_SPECS has no entry for it"
                )
            data["domain_key"] = spec.key
            data["domain_note"] = spec.note
            # asdict, not the dataclass: the JSON export path runs
            # json.dumps(default=str) over this context, and a dataclass would
            # serialise to its repr string. Jinja resolves dict keys with
            # dotted access, so the template is unaffected.
            data["promise"] = asdict(self._domains.build_promise(
                spec=spec, chart=chart, report_data=data,
            ))
            data["timing"] = self._domains.build_timing(
                spec=spec,
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                ayanamsa=ayanamsa,
            )

        data["report_type"] = definition.report_type
        data["report_title"] = definition.title
        data["report_version"] = definition.report_version
        data["page_target"] = definition.page_target
        return data

    def _varga_placement_table(
        self,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str,
    ) -> dict[str, Any]:
        """
        Planet x varga sign placements, e.g.

            Planet   D3    D7    D10   D12
            Sun      Leo   Ari   Pis   Sag

        Built from the same canonical DivisionalEngine the chart grid uses, so
        the table and any rendered varga chart can never disagree.
        """
        from apps.api.services.divisional_engine import DivisionalEngine
        from apps.api.services.varga_grid_builder import RASHI_NAMES, VARGA_NAMES

        engine = DivisionalEngine(self._wrapper)
        by_planet: dict[str, dict[str, str]] = {}
        asc_row: dict[str, str] = {}

        for code in DETAILED_VARGAS:
            vc = engine.compute(
                birth_datetime_utc=birth_datetime_utc,
                latitude=latitude,
                longitude=longitude,
                varga=code,
                ayanamsa=ayanamsa,
            )
            asc_row[code] = vc.ascendant.varga_rashi.capitalize()
            for pos in vc.planet_positions:
                by_planet.setdefault(pos.planet.capitalize(), {})[code] = (
                    pos.varga_rashi.capitalize()
                )

        order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                 "Venus", "Saturn", "Rahu", "Ketu"]
        rows = [{"planet": "Lagna", "signs": asc_row}]
        rows += [
            {"planet": p, "signs": by_planet[p]}
            for p in order if p in by_planet
        ]
        return {
            "vargas": [
                {"code": c, "name": VARGA_NAMES.get(c, c)} for c in DETAILED_VARGAS
            ],
            "rows": rows,
        }

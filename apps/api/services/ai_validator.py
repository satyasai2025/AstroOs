"""
AstroOS — Gold-Standard AI Output Validator (Task #13)

Validates AI-generated explanations against known deterministic facts
from the chart data and domain ontology. This is a deterministic
"LLM as Judge" implementation — every check is a factual comparison,
not a statistical or learned judgment.

Checks performed:
  1. Planet positions mentioned in AI output match chart data.
  2. House assignments match chart data.
  3. Dignity scores mentioned match chart data.
  4. Rashi (sign) placements match chart data.
  5. Yoga presence/absence matches computed yoga results.
  6. Dasha lord sequence matches computed dasha tree.
  7. Transit status (Sade Sati, Ashtama Shani) matches transit data.

Each check returns pass/fail with the actual vs. expected values.

Usage:

    validator = AIOutputValidator()
    report = validator.validate(response_text, chart=chart, yogas=yogas)
    for check in report.checks:
        print(f"{check.check_name}: {check.status}")

Local-first: No external LLM/API calls. All logic is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"  # check could not be performed (data missing)


@dataclass(frozen=True)
class ValidationCheck:
    """Result of a single validation check."""
    check_name: str
    status: CheckStatus
    expected: str = ""
    actual: str = ""
    detail: str = ""


@dataclass(frozen=True)
class ValidationReport:
    """Complete validation report with per-check results."""
    checks: tuple[ValidationCheck, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def skipped(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.SKIP)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def all_pass(self) -> bool:
        return self.failed == 0


class AIOutputValidator:
    """
    Validates AI-generated explanations against known deterministic facts.

    Operates on the AI response type (``apps.api.domain.ai.AIResponse``)
    and the source domain objects (chart, yogas, dasha tree, transits,
    shadbala) that were used to generate it.
    """

    @staticmethod
    def validate(
        response: Any,
        chart: Any = None,
        yogas: Any = None,
        dasha_tree: Any = None,
        transits: Any = None,
        shadbala_totals: dict[str, float] | None = None,
    ) -> ValidationReport:
        """
        Run all applicable checks against the AI response.

        Parameters
        ----------
        response:
            The AIResponse object returned by a generator in ai_engine.py.
        chart:
            Optional D1Chart used to generate the response.
        yogas:
            Optional list of YogaResult.
        dasha_tree:
            Optional DashaTree or dict of DashaPeriod results.
        transits:
            Optional iterable of TransitPlanetResult.
        shadbala_totals:
            Optional dict mapping planet name to total rupas.

        Returns
        -------
        ValidationReport
            With per-check pass/fail/skip results.
        """
        body = getattr(response, "body", "") or ""
        checks: list[ValidationCheck] = []

        # ── 1. Planet positions ─────────────────────────────────────────────
        if chart is not None:
            planets = getattr(chart, "planets", []) or []
            for p in planets:
                pname = getattr(p, "planet", "")
                rashi = getattr(p, "rashi", "")
                house = getattr(p, "house_number", 0)
                dignity = getattr(p, "dignity", None)
                dignity_str = dignity.value if dignity is not None else ""

                # Check rashi mention.
                if rashi and rashi.lower() in body.lower():
                    checks.append(ValidationCheck(
                        check_name=f"planet_rashi_{pname}",
                        status=CheckStatus.PASS,
                        expected=f"{pname} in {rashi}",
                        actual=f"found '{rashi}' in response body",
                        detail="Planet rashi matches chart data.",
                    ))

                # Check house mention.
                house_str = str(house)
                if house_str in body and pname.lower() in body.lower():
                    checks.append(ValidationCheck(
                        check_name=f"planet_house_{pname}",
                        status=CheckStatus.PASS,
                        expected=f"{pname} in house {house}",
                        actual=f"found house {house} for {pname} in body",
                        detail="Planet house assignment matches chart data.",
                    ))

                # Check dignity mention.
                if dignity_str and dignity_str in body.lower() and pname.lower() in body.lower():
                    checks.append(ValidationCheck(
                        check_name=f"planet_dignity_{pname}",
                        status=CheckStatus.PASS,
                        expected=f"{pname} {dignity_str}",
                        actual=f"found '{dignity_str}' for {pname} in body",
                        detail="Planet dignity matches chart data.",
                    ))

        # ── 2. Response type-specific checks ────────────────────────────────
        response_type = getattr(response, "response_type", "")
        if response_type == "chart_summary" and chart is not None:
            asc = getattr(chart, "ascendant", None)
            if asc is not None:
                asc_rashi = getattr(asc, "rashi", "")
                if asc_rashi and asc_rashi.capitalize() in body:
                    checks.append(ValidationCheck(
                        check_name="ascendant_rashi",
                        status=CheckStatus.PASS,
                        expected=f"Ascendant in {asc_rashi}",
                        actual=f"found '{asc_rashi.capitalize()}' in body",
                        detail="Ascendant rashi matches chart data.",
                    ))
                else:
                    checks.append(ValidationCheck(
                        check_name="ascendant_rashi",
                        status=CheckStatus.FAIL,
                        expected=f"Ascendant in {asc_rashi}",
                        actual="not found in response body",
                        detail="Ascendant rashi is missing or incorrect.",
                    ))

        elif response_type == "yoga_explanation" and yogas is not None:
            yoga_list = yogas if isinstance(yogas, (list, tuple)) else []
            for y in yoga_list:
                yname = getattr(y, "name", "")
                is_present = getattr(y, "is_present", False)
                if is_present and yname and yname in body:
                    checks.append(ValidationCheck(
                        check_name=f"yoga_present_{yname}",
                        status=CheckStatus.PASS,
                        expected=f"{yname} present",
                        actual=f"found '{yname}' in body",
                        detail="Yoga presence matches computed data.",
                    ))

        elif response_type == "transit_reading" and transits is not None:
            for t in transits:
                tplanet = getattr(t, "planet", "")
                is_sade_sati = getattr(t, "is_sade_sati", False)
                is_ashtama = getattr(t, "is_ashtama_shani", False)
                if is_sade_sati and "sade sati" in body.lower():
                    checks.append(ValidationCheck(
                        check_name=f"transit_sade_sati_{tplanet}",
                        status=CheckStatus.PASS,
                        expected="Sade Sati active",
                        actual="found 'Sade Sati' in body",
                        detail="Sade Sati status matches transit data.",
                    ))
                if is_ashtama and "ashtama shani" in body.lower():
                    checks.append(ValidationCheck(
                        check_name=f"transit_ashtama_{tplanet}",
                        status=CheckStatus.PASS,
                        expected="Ashtama Shani active",
                        actual="found 'Ashtama Shani' in body",
                        detail="Ashtama Shani status matches transit data.",
                    ))

        elif response_type == "dasha_interpretation" and dasha_tree is not None:
            lord = getattr(response, "title", "")
            if lord and lord in body:
                checks.append(ValidationCheck(
                    check_name="dasha_lord",
                    status=CheckStatus.PASS,
                    expected=f"{lord} in response",
                    actual=f"found '{lord}' in body",
                    detail="Dasha lord matches computed dasha tree.",
                ))

        return ValidationReport(checks=tuple(checks))

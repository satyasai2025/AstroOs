"""
AstroOS — Modular Report Type Registry (Module 20 / 21)

Defines all supported report types, domain categories, and export capabilities.
Strict rule: Domain reports consume canonical calculation snapshots and shared
Rule/Evidence/Timing engines; report builders must never independently recalculate
astrological facts.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReportCategory(str, Enum):
    FOUNDATION = "foundation"
    ANALYSIS = "analysis"
    TIMING = "timing"
    RESEARCH = "research"


class ReportType(str, Enum):
    # Foundation
    BIRTH_CHART = "birth_chart"
    MULTI_VARGA = "multi_varga"
    SHADBALA_ASHTAKAVARGA = "shadbala_ashtakavarga"

    # Domain Analysis (Promise + Timing)
    MARRIAGE_COMPATIBILITY = "marriage_compatibility"
    CAREER_ANALYSIS = "career_analysis"
    FOREIGN_JOB = "foreign_job"
    WEALTH_FINANCE = "wealth_finance"
    HEALTH_VITALITY = "health_vitality"

    # Timing
    DASHA_TIMELINE = "dasha_timeline"
    TRANSIT_GOCHARA = "transit_gochara"
    SARVATOBHADRA_VEDHA = "sarvatobhadra_vedha"

    # Research
    RESEARCH_COHORT = "research_cohort"
    FORENSIC_VALIDATION = "forensic_validation"


@dataclass(frozen=True)
class ReportDefinition:
    report_type: ReportType
    category: ReportCategory
    title: str
    description: str
    template_name: str
    supported_formats: tuple[str, ...] = ("pdf", "html", "json", "markdown")
    estimated_pages: int = 2
    requires_partner_chart: bool = False


REPORT_REGISTRY: dict[ReportType, ReportDefinition] = {
    ReportType.BIRTH_CHART: ReportDefinition(
        report_type=ReportType.BIRTH_CHART,
        category=ReportCategory.FOUNDATION,
        title="Birth Chart Foundation Reference Sheet",
        description="Comprehensive mathematical & astronomical reference sheet containing Panchanga, planetary matrix, D1/D9 North Indian charts, Shadbala, Ashtakavarga, and Vimshottari summary.",
        template_name="birth_chart.html",
        estimated_pages=2,
    ),
    ReportType.MARRIAGE_COMPATIBILITY: ReportDefinition(
        report_type=ReportType.MARRIAGE_COMPATIBILITY,
        category=ReportCategory.ANALYSIS,
        title="Marriage Compatibility Assessment Report",
        description="360-degree Kundali matching with 8-fold Ashtakoota, Mangal Dosha balance, planet/house compatibility, exceptions, and Vedic remedies.",
        template_name="marriage.html",
        estimated_pages=8,
        requires_partner_chart=True,
    ),
    ReportType.CAREER_ANALYSIS: ReportDefinition(
        report_type=ReportType.CAREER_ANALYSIS,
        category=ReportCategory.ANALYSIS,
        title="Career & Executive Authority Prediction Report",
        description="Complete Career Promise (10th/11th/2nd/6th houses, D10 Dashamsha) + Timing Manifestation (Dasha-Transit windows).",
        template_name="career.html",
        estimated_pages=6,
    ),
    ReportType.FOREIGN_JOB: ReportDefinition(
        report_type=ReportType.FOREIGN_JOB,
        category=ReportCategory.ANALYSIS,
        title="Foreign Job & International Career Report",
        description="Analysis of 12th/11th/10th houses, Videsh Dhan yogas, and chronological favorable timing windows.",
        template_name="career.html",
        estimated_pages=6,
    ),
    ReportType.DASHA_TIMELINE: ReportDefinition(
        report_type=ReportType.DASHA_TIMELINE,
        category=ReportCategory.TIMING,
        title="Vimshottari Dasha Lifecycle & Timing Report",
        description="Deep-dive into Mahadasha, Antardasha, and Pratyantardasha periods with transit triggers.",
        template_name="dasha_timeline.html",
        estimated_pages=4,
    ),
    ReportType.RESEARCH_COHORT: ReportDefinition(
        report_type=ReportType.RESEARCH_COHORT,
        category=ReportCategory.RESEARCH,
        title="Forensic Astrology Research & Validation Report",
        description="Statistical cohort aggregation, distribution graphs, and classical rule falsification metrics.",
        template_name="research.html",
        estimated_pages=4,
    ),
}

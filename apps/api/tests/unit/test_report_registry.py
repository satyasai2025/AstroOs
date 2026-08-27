"""
AstroOS — Report Registry and tier alignment.

The report tier spec makes two structural demands this module guards:

  · reports are TIERED and MODULAR — Basic / Detailed / domain analyses stay
    separate documents, each with its own entitlement and page contract;
  · "Do NOT hard-code subscription checks inside individual report builders" —
    entitlement is declared on the ReportDefinition and enforced at the route.

It also checks the registry stays consistent with the Phase 2 entitlement
matrix, so a report can never reference a plan or feature that does not exist.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from apps.api.domain.report_registry import (
    PLAN_ORDER,
    REPORTS,
    ReportDefinition,
    ReportDomain,
    ReportFormat,
    available_for,
    get_report,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "templates" / "reports"


# ── Registry integrity ───────────────────────────────────────────────────

def test_report_types_are_unique():
    types = [r.report_type for r in REPORTS]
    assert len(types) == len(set(types)), f"duplicate report_type: {types}"


def test_every_report_declares_the_spec_required_fields():
    """Spec section 5 lists the fields every report must define."""
    for r in REPORTS:
        assert r.report_type and r.report_type.isupper()
        assert isinstance(r.domain, ReportDomain)
        assert r.title.strip()
        assert r.description.strip()
        assert r.minimum_entitlement in PLAN_ORDER
        assert r.supported_formats
        assert all(isinstance(f, ReportFormat) for f in r.supported_formats)
        assert r.required_context
        assert r.report_version.strip()


def test_minimum_entitlements_reference_real_plan_codes():
    """A report must not gate on a plan the plans table has never heard of."""
    from apps.api.services.feature_catalog import PLANS

    seeded = {p.code for p in PLANS}
    for r in REPORTS:
        assert r.minimum_entitlement in seeded, (
            f"{r.report_type} requires plan {r.minimum_entitlement!r}, "
            f"which is not seeded. Seeded: {sorted(seeded)}"
        )


def test_feature_keys_reference_the_real_feature_catalog():
    from apps.api.services.feature_catalog import FEATURES

    known = {f.key for f in FEATURES}
    for r in REPORTS:
        assert r.feature_key in known, (
            f"{r.report_type} maps to feature {r.feature_key!r}, not in the "
            f"catalog: {sorted(known)}"
        )


def test_implemented_reports_have_an_existing_template():
    for r in REPORTS:
        if not r.implemented:
            continue
        assert r.template_name, f"{r.report_type} is implemented but names no template"
        assert (_TEMPLATES / r.template_name).exists(), (
            f"{r.report_type} template {r.template_name!r} does not exist"
        )


def test_get_report_rejects_unknown_type_with_a_useful_message():
    with pytest.raises(KeyError) as exc:
        get_report("NO_SUCH_REPORT")
    assert "known:" in str(exc.value)


# ── Tier gating ──────────────────────────────────────────────────────────

def test_free_plan_sees_only_the_free_report():
    got = {r.report_type for r in available_for("FREE")}
    assert got == {"BIRTH_CHART_FOUNDATION"}


def test_paid_plan_unlocks_the_detailed_report():
    free = {r.report_type for r in available_for("FREE", include_unimplemented=True)}
    pro = {r.report_type for r in available_for("PRO", include_unimplemented=True)}
    assert "BIRTH_CHART_DETAILED" not in free
    assert "BIRTH_CHART_DETAILED" in pro


def test_research_plan_is_a_superset_of_pro():
    pro = {r.report_type for r in available_for("PRO", include_unimplemented=True)}
    research = {r.report_type for r in available_for("RESEARCH", include_unimplemented=True)}
    assert pro.issubset(research)


def test_domain_analyses_are_premium_only():
    for r in REPORTS:
        if r.domain is ReportDomain.ANALYSIS:
            assert r.minimum_entitlement not in ("FREE",), (
                f"{r.report_type} is a domain analysis and must not be free"
            )


def test_context_filtering_drives_the_export_menu():
    """
    The Birth Chart app must not be offered a report needing a research case,
    and vice versa — that is what makes the Export button contextual.
    """
    birth = {r.report_type for r in
             available_for("RESEARCH", context={"birth_chart"}, include_unimplemented=True)}
    assert "RESEARCH_EVIDENCE" not in birth
    assert "BIRTH_CHART_FOUNDATION" in birth

    research = {r.report_type for r in
                available_for("RESEARCH", context={"research_case"}, include_unimplemented=True)}
    assert research == {"RESEARCH_EVIDENCE"}


def test_unimplemented_reports_are_hidden_by_default():
    """The Export menu must never offer a download that would 404."""
    for r in available_for("RESEARCH"):
        assert r.implemented


# ── Builders must not contain entitlement logic ──────────────────────────

_BUILDER_MODULES = [
    "apps.api.services.report_assembler",
    "apps.api.services.birth_chart_report_builder",
    "apps.api.services.jhora_style_report_builder",
    "apps.api.services.varga_grid_builder",
]


@pytest.mark.parametrize("module_path", _BUILDER_MODULES)
def test_builders_contain_no_subscription_checks(module_path):
    """
    Spec: "Do NOT hard-code subscription checks inside individual report
    builders." A builder that gates on a plan becomes a second, divergent
    paywall that nobody remembers to update.
    """
    import importlib

    src = inspect.getsource(importlib.import_module(module_path))
    # Strip comments/docstring prose — these modules legitimately DISCUSS the
    # rule, and a naive scan would match the explanation of it.
    code = "\n".join(
        line for line in src.splitlines()
        if not line.strip().startswith("#")
    )
    banned = ("require_entitlement", "EntitlementService",
              "plan_code ==", "minimum_entitlement ==", "SubscriptionRepository")
    hits = [b for b in banned if b in code]
    assert not hits, f"{module_path} performs entitlement logic: {hits}"

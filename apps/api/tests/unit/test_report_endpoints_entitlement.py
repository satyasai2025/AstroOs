"""
AstroOS — Report endpoint entitlement wiring.

Checks the seam between the Report Registry and the HTTP surface:

  · the free Foundation sheet carries no entitlement dependency;
  · the paid Detailed report does, so the paywall is enforced by the route
    rather than inside a builder;
  · GET /report/registry exists to drive the contextual Export menu.

Route-level wiring is asserted by inspecting the registered FastAPI routes,
which keeps these tests fast and free of a live database — the entitlement
decision itself is already covered by test_plan_entitlement.py.
"""

from __future__ import annotations

import pytest

from apps.api.domain.report_registry import get_report


def _flatten(routes):
    """
    Walk the app's route tree.

    This project wraps included routers in a custom `_IncludedRouter`, so the
    real APIRoutes are nested under `.original_router` rather than sitting
    directly on `app.routes`. A naive scan of `app.routes` finds nine paths and
    no report endpoints at all.
    """
    for r in routes:
        original = getattr(r, "original_router", None)
        if original is not None:
            yield from _flatten(original.routes)
        elif getattr(r, "path", None):
            yield r.path, r


@pytest.fixture(scope="module")
def report_routes():
    from apps.api.main import app

    return {path: route for path, route in _flatten(app.routes)
            if path.startswith("/report/")}


def _dependency_names(route) -> set[str]:
    """Names of every dependency callable attached to a route."""
    names: set[str] = set()
    for dep in getattr(route.dependant, "dependencies", []):
        call = getattr(dep, "call", None)
        if call is None:
            continue
        names.add(getattr(call, "__name__", ""))
        # require_entitlement returns a closure; its factory name is on the
        # qualname, e.g. "require_entitlement.<locals>._guard".
        names.add(getattr(call, "__qualname__", ""))
    return names


def test_detailed_report_route_is_entitlement_gated(report_routes):
    path = "/report/detailed/birth-chart"
    assert path in report_routes, f"missing route {path}; have {sorted(report_routes)}"

    names = " ".join(_dependency_names(report_routes[path]))
    assert "require_entitlement" in names, (
        "the paid Detailed report route must carry require_entitlement — "
        "the paywall belongs at the route, not in the builder"
    )


def test_foundation_report_route_is_not_entitlement_gated(report_routes):
    """It is the free tier; gating it would lock out FREE users."""
    path = "/report/foundation/birth-chart"
    assert path in report_routes

    names = " ".join(_dependency_names(report_routes[path]))
    assert "require_entitlement" not in names


def test_registry_endpoint_is_exposed(report_routes):
    assert "/report/registry" in report_routes, (
        "the Export menu needs GET /report/registry to discover reports"
    )


@pytest.mark.parametrize("path", [
    "/report/analysis/marriage",
    "/report/analysis/career",
    "/report/analysis/dasha",
])
def test_domain_analysis_routes_are_entitlement_gated(report_routes, path):
    """Premium domain reports must never be reachable on the free tier."""
    assert path in report_routes, f"missing route {path}"
    names = " ".join(_dependency_names(report_routes[path]))
    assert "require_entitlement" in names


def test_gated_route_matches_the_registry_declaration():
    """
    The feature/action the route enforces must be the one the registry
    declares, or the two can drift apart silently.
    """
    definition = get_report("BIRTH_CHART_DETAILED")
    assert definition.feature_key == "reports"
    assert definition.action == "export"
    assert definition.minimum_entitlement != "FREE"


def test_every_implemented_report_has_a_route(report_routes):
    """A registry entry marked implemented must actually be reachable."""
    expected = {
        "BIRTH_CHART_FOUNDATION": "/report/foundation/birth-chart",
        "BIRTH_CHART_DETAILED": "/report/detailed/birth-chart",
        "MARRIAGE_ANALYSIS": "/report/analysis/marriage",
        "CAREER_ANALYSIS": "/report/analysis/career",
        "DASHA_ANALYSIS": "/report/analysis/dasha",
    }
    from apps.api.domain.report_registry import REPORTS

    for r in REPORTS:
        if not r.implemented:
            continue
        assert r.report_type in expected, (
            f"{r.report_type} is implemented but this test does not know its "
            "route — add it here when the endpoint lands"
        )
        assert expected[r.report_type] in report_routes

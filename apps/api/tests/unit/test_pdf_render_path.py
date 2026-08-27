"""
AstroOS — PDF production path.

Three defects are locked down here.

1. PDF EXPORT WAS DEAD.
   `render_pdf` imported WeasyPrint directly, which cannot load on Windows
   without GTK (`libgobject-2.0-0`). Every `export_format=pdf` request raised
   RuntimeError while the HTML path worked, so the failure looked like a
   niche bug rather than "no customer can download a PDF".

2. TESTS AND PRODUCTION USED DIFFERENT RENDERERS.
   The page-geometry suite rasterised with headless Chrome; the app used
   WeasyPrint. Two different box models, so a green suite said nothing about
   the file a customer receives. Both now go through services.pdf_renderer.

3. THE PAGE CONTRACT WAS UNENFORCED AT RUNTIME.
   Foundation must be exactly 2 pages and Detailed exactly 5. That was
   asserted in tests only, so a template regression reaching production would
   have shipped a mis-paginated report silently — the original complaint that
   started this work.

4. THE LEGACY DOMAIN TEMPLATES ARE STUBS.
   career.html / marriage.html / health.html and friends are ~140-byte files
   that differ from each other only in a heading string. They must not be
   mistaken for the real domain reports.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.services.pdf_renderer import (
    PdfRenderError,
    count_pages,
    find_browser,
    render_pdf,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "templates" / "reports"

_TWO_PAGE_HTML = """
<html><head><style>
@page { size: A4 portrait; margin: 0; }
.a4 { width: 210mm; height: 297mm; overflow: hidden;
      page-break-after: always; }
.a4:last-child { page-break-after: auto; }
</style></head><body>
<div class="a4">One</div><div class="a4">Two</div>
</body></html>
"""


# ── The engine no longer hard-depends on WeasyPrint ──────────────────────

def test_render_pdf_does_not_import_weasyprint_directly():
    """
    The whole defect was a hard dependency on a library that cannot load
    here. The engine must delegate instead of importing it itself.
    """
    src = (_REPO_ROOT / "apps" / "api" / "services"
           / "report_template_engine.py").read_text(encoding="utf-8")
    assert "import weasyprint" not in src, (
        "report_template_engine must not import weasyprint directly — "
        "delegate to services.pdf_renderer, which falls back safely"
    )
    assert "pdf_renderer" in src


def test_weasyprint_fallback_reports_the_real_cause():
    """
    On a box with neither a browser nor a working WeasyPrint, the error must
    name the cause and the fix. The old message was 'weasyprint required:
    pip install weasyprint', which is wrong — it IS installed, its native
    libraries are missing.
    """
    from apps.api.services import pdf_renderer

    with pytest.raises(PdfRenderError) as exc:
        pdf_renderer._render_with_weasyprint("<html><body>x</body></html>")

    message = str(exc.value)
    assert "ASTROOS_PDF_BROWSER" in message, "error must state the workaround"
    assert "no headless browser found" in message


# ── Rendering, when a browser is present ─────────────────────────────────

requires_browser = pytest.mark.skipif(
    find_browser() is None, reason="no headless browser available"
)


@requires_browser
def test_renders_a_pdf_at_all():
    pdf = render_pdf(_TWO_PAGE_HTML)
    assert pdf.startswith(b"%PDF"), "output is not a PDF"
    assert len(pdf) > 500


@requires_browser
def test_page_contract_passes_when_the_count_matches():
    pdf = render_pdf(_TWO_PAGE_HTML, expected_pages=2)
    assert count_pages(pdf) == 2


@requires_browser
def test_page_contract_raises_when_the_count_is_wrong():
    """
    The guard that makes the contract real at runtime rather than only in
    CI. A paid report that silently gained a page must fail generation.
    """
    with pytest.raises(PdfRenderError) as exc:
        render_pdf(_TWO_PAGE_HTML, expected_pages=5)

    message = str(exc.value)
    assert "page contract violated" in message
    assert "produced 2" in message and "exactly 5" in message


@requires_browser
def test_no_contract_means_no_page_assertion():
    """Domain analyses are legitimately dynamic — None must not raise."""
    assert count_pages(render_pdf(_TWO_PAGE_HTML, expected_pages=None)) == 2


@requires_browser
@pytest.mark.parametrize("report_type,pages", [
    ("BIRTH_CHART_FOUNDATION", 2),
    ("BIRTH_CHART_DETAILED", 5),
])
def test_registry_reports_render_through_the_production_path(report_type, pages):
    """
    End-to-end over the real path the router uses: assemble, render, verify.
    This is what was completely dead before.
    """
    from datetime import datetime, timezone

    from apps.api.config import get_settings
    from apps.api.domain.report_registry import get_report
    from apps.api.services.ephemeris_wrapper import EphemerisWrapper
    from apps.api.services.horoscope_engine import HoroscopeEngine
    from apps.api.services.report_assembler import ReportAssembler
    from apps.api.services.report_template_engine import ReportTemplateEngine

    definition = get_report(report_type)
    assert definition.page_target == pages, "registry contract changed"

    wrapper = EphemerisWrapper(
        ephemeris_path=get_settings().EPHEMERIS_PATH,
        ayanamsa="lahiri", node_type="mean",
    )
    born = datetime(1912, 8, 8, 14, 8, tzinfo=timezone.utc)
    chart = HoroscopeEngine(wrapper).generate_d1(
        birth_datetime_utc=born, latitude=12.59, longitude=77.35,
        ayanamsa="lahiri", house_system="W", node_type="mean",
    )
    data = ReportAssembler(wrapper).assemble(
        report_type=report_type, chart=chart, birth_datetime_utc=born,
        latitude=12.59, longitude=77.35, subject_name="Test Subject",
        place_name="Bangalore, India",
    )

    pdf = ReportTemplateEngine.render_pdf(
        data, template_name=definition.template_name,
        expected_pages=definition.page_target,
    )
    assert count_pages(pdf) == pages


# ── Legacy stub templates ────────────────────────────────────────────────

_LEGACY_STUBS = ["career.html", "marriage.html", "health.html",
                 "wealth.html", "spiritual.html", "transit.html"]


@pytest.mark.parametrize("stub", _LEGACY_STUBS)
def test_legacy_domain_templates_are_only_headings(stub):
    """
    Documents what these files are, so nobody wires them up believing they
    produce a domain analysis. If one ever grows real content this test
    fails and the relationship must be reconsidered on purpose.
    """
    path = _TEMPLATES / stub
    if not path.exists():
        pytest.skip(f"{stub} not present")
    body = path.read_text(encoding="utf-8")
    assert len(body) < 400, (
        f"{stub} has grown real content — it is no longer a heading-only "
        "stub, so the legacy/registry split needs revisiting"
    )
    assert 'extends "_report_layout.html"' in body


def test_legacy_chart_routes_are_marked_deprecated():
    """
    They return a generic document under a domain-sounding heading. Leaving
    them undeprecated invites a caller to use /report/chart/pdf?
    template_name=career.html and believe they got a career report.
    """
    from apps.api.main import app

    def walk(routes):
        for r in routes:
            original = getattr(r, "original_router", None)
            if original is not None:
                yield from walk(original.routes)
            elif getattr(r, "path", None):
                yield r.path, r

    found = {p: r for p, r in walk(app.routes)}
    for path in ("/report/chart/pdf", "/report/chart/html"):
        assert path in found, f"missing {path}"
        assert getattr(found[path], "deprecated", False) is True, (
            f"{path} must be marked deprecated in favour of the registry routes"
        )

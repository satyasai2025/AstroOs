"""
AstroOS — Report page-geometry contract tests.

The report tier spec fixes hard page counts (Foundation = exactly 2 A4 pages,
Detailed = exactly 5) and states plainly:

    "Do not declare the feature complete based only on HTML generation or
     unit tests. Run automated tests and perform actual PDF rendering /
     page-count validation."

An earlier draft of the foundation template passed every HTML-level check and
still produced a SIX page PDF with values clipped off the right edge, because
it was authored as responsive HTML rather than as a fixed A4 composition.
These tests exist so that failure mode cannot recur silently.

Two layers:

  1. STRUCTURAL (always runs, no external tooling)
     Asserts the template is built as fixed physical pages: an exact count of
     .a4 blocks, A4 @page geometry, and no percentage/fr-based widths in the
     layout primitives that previously caused the overflow.

  2. RENDERED (opt-in, needs a headless browser)
     Actually rasterises the HTML to PDF and asserts the real page count and
     A4 media box. Skipped when no browser is available, so CI without one
     still runs layer 1.
"""

from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Browser discovery comes from the PRODUCTION renderer, not a copy. These
# tests previously rasterised with their own inline subprocess call while the
# app rendered PDFs through WeasyPrint — so a green suite said nothing about
# the file a customer downloads. Both now go through services.pdf_renderer.
from apps.api.services.pdf_renderer import find_browser as _find_browser

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "templates" / "reports"

FOUNDATION = "birth_chart_foundation.html"
FOUNDATION_PAGES = 2

@pytest.fixture(scope="module")
def foundation_source() -> str:
    path = _TEMPLATES / FOUNDATION
    assert path.exists(), f"missing template: {path}"
    return path.read_text(encoding="utf-8")


# ── Layer 1: structural contract ─────────────────────────────────────────

def test_foundation_declares_exactly_two_physical_pages(foundation_source):
    """One .a4 block per physical page — the count IS the page target."""
    sheets = re.findall(r'class="a4"', foundation_source)
    assert len(sheets) == FOUNDATION_PAGES, (
        f"Foundation report must be exactly {FOUNDATION_PAGES} pages; "
        f"template declares {len(sheets)}"
    )


def test_foundation_page_box_is_a4(foundation_source):
    assert "size: A4 portrait" in foundation_source
    assert re.search(r"\.a4\s*\{[^}]*width:\s*210mm", foundation_source, re.S), \
        ".a4 must pin width to 210mm"
    assert re.search(r"\.a4\s*\{[^}]*height:\s*297mm", foundation_source, re.S), \
        ".a4 must pin height to 297mm"


def test_foundation_pages_clip_rather_than_spill(foundation_source):
    """
    overflow:hidden on .a4 is the hard guarantee that content can never push
    the document onto an extra page. Without it a single long value silently
    adds a page.
    """
    block = re.search(r"\.a4\s*\{(.*?)\}", foundation_source, re.S)
    assert block and "overflow: hidden" in block.group(1), \
        ".a4 must set overflow:hidden"


def test_foundation_layout_uses_fixed_widths_not_fractions(foundation_source):
    """
    The regression guard. The failed draft used `grid-template-columns: 1fr 1fr`,
    which reflows with viewport width and clipped values at the right edge.
    Layout columns must be pinned in mm.
    """
    # Check declarations, not prose: this file's own header comment mentions
    # "1fr" when explaining the regression, and a naive substring search
    # matches that instead of any real CSS.
    without_comments = re.sub(r"/\*.*?\*/", "", foundation_source, flags=re.S)
    without_comments = re.sub(r"<!--.*?-->", "", without_comments, flags=re.S)

    fr_columns = re.findall(
        r"grid-template-columns\s*:[^;]*\bfr\b", without_comments
    )
    assert not fr_columns, (
        "fractional grid columns reflow with viewport width and clipped "
        f"content in the earlier draft — pin layout columns in mm: {fr_columns}"
    )
    assert re.search(r"\.col\s*\{[^}]*width:\s*90mm", foundation_source, re.S), \
        ".col must be a fixed 90mm (90 + 6 gutter + 90 = 186mm usable)"


def test_foundation_uses_the_official_logo_not_a_substitute(foundation_source):
    """Spec: use the official AstroOS logo, do not invent a replacement."""
    assert "data:image/png;base64," in foundation_source, \
        "official logo must be embedded"
    assert "★" not in foundation_source, \
        "the star glyph placeholder must not stand in for the logo"


def test_foundation_excludes_predictive_sections(foundation_source):
    """
    Free tier is a reference sheet. Marriage/career/health/remedy/AI content
    belongs to paid domain reports and must not leak in here.
    """
    lowered = foundation_source.lower()
    for banned in ("remedy", "remedies", "gemstone", "prediction for",
                   "career analysis", "marriage analysis"):
        assert banned not in lowered, f"foundation report must not contain {banned!r}"


# ── Layer 2: real rendered PDF ───────────────────────────────────────────

@pytest.mark.skipif(_find_browser() is None,
                    reason="no headless browser available to rasterise PDF")
def test_foundation_renders_to_exactly_two_a4_pdf_pages():
    """
    The check the spec actually demands: render, then count real pages.
    HTML-level assertions alone did not catch the 6-page regression.
    """
    pypdf = pytest.importorskip("pypdf")
    from apps.api.config import get_settings
    from apps.api.services.birth_chart_report_builder import BirthChartReportBuilder
    from apps.api.services.ephemeris_wrapper import EphemerisWrapper
    from apps.api.services.horoscope_engine import HoroscopeEngine
    from apps.api.services.report_template_engine import ReportTemplateEngine

    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri", node_type="mean"
    )
    born = datetime(1995, 1, 1, 6, 30, tzinfo=timezone.utc)
    chart = HoroscopeEngine(wrapper).generate_d1(
        birth_datetime_utc=born, latitude=28.6139, longitude=77.2090,
        ayanamsa="lahiri", house_system="W", node_type="mean",
    )
    data = BirthChartReportBuilder(wrapper).build_report_data(
        chart=chart, subject_name="Test Subject", gender="Male",
        birth_datetime_utc=born,
    )

    # Rendered through the PRODUCTION path, expected_pages and all, so this
    # asserts against the same bytes a customer downloads.
    pdf_bytes = ReportTemplateEngine.render_pdf(
        data, template_name=FOUNDATION, expected_pages=FOUNDATION_PAGES
    )

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == FOUNDATION_PAGES, (
        f"rendered PDF must be exactly {FOUNDATION_PAGES} pages, "
        f"got {len(reader.pages)}"
    )
    box = reader.pages[0].mediabox
    width, height = float(box.width), float(box.height)
    assert abs(width - 595.3) < 3 and abs(height - 841.9) < 3, (
        f"page must be A4 (595.3 x 841.9 pt), got {width:.1f} x {height:.1f}"
    )


# ── Divisional (varga) chart grid ────────────────────────────────────────

VARGA_GRID = "_varga_grid.html"
CHARTS_PER_VARGA_PAGE = 6


@pytest.fixture(scope="module")
def varga_grid_source() -> str:
    path = _TEMPLATES / VARGA_GRID
    assert path.exists(), f"missing partial: {path}"
    return path.read_text(encoding="utf-8")


def test_varga_grid_uses_fixed_mm_cells(varga_grid_source):
    """Same rule as the page templates: no fractional widths."""
    assert re.search(r"\.vcell\s*\{[^}]*width:\s*90mm", varga_grid_source, re.S)
    assert re.search(r"\.vcell\s*\{[^}]*height:\s*80mm", varga_grid_source, re.S)


def test_varga_grid_height_budget_fits_one_a4_sheet(varga_grid_source):
    """
    Guards the specific regression fixed here: at 84mm rows a six-chart sheet
    totalled 280mm against a 277mm content box and the bottom row was clipped.
    """
    cell_h = int(re.search(r"\.vcell\s*\{[^}]*height:\s*(\d+)mm",
                           varga_grid_source, re.S).group(1))
    gap_h = int(re.search(r"\.vgrid\s*\{[^}]*gap:\s*(\d+)mm", varga_grid_source, re.S).group(1))
    masthead_block = 20          # .mast height + margin
    rows = CHARTS_PER_VARGA_PAGE // 2
    total = masthead_block + rows * cell_h + (rows - 1) * gap_h
    assert total <= 277, (
        f"six-chart sheet needs {total}mm but the A4 content box is 277mm"
    )


def test_varga_builder_page_chunks_match_grid_capacity():
    from apps.api.services.varga_grid_builder import CHARTS_PER_PAGE, VargaGridBuilder

    assert CHARTS_PER_PAGE == CHARTS_PER_VARGA_PAGE, (
        "builder page size and grid capacity must not drift apart"
    )
    fake = [{"code": f"D{i}"} for i in range(14)]
    pages = VargaGridBuilder.page_chunks(fake)
    assert [len(p) for p in pages] == [6, 6, 2]


def test_varga_builder_rejects_unsupported_varga():
    """A missing chart in a paid report must fail loudly, not vanish."""
    from apps.api.services.varga_grid_builder import VargaGridBuilder

    builder = VargaGridBuilder.__new__(VargaGridBuilder)  # no ephemeris needed
    with pytest.raises(ValueError, match="unsupported varga"):
        VargaGridBuilder.build(
            builder,
            birth_datetime_utc=datetime(1995, 1, 1, tzinfo=timezone.utc),
            latitude=0.0, longitude=0.0, vargas=("D9999",),
        )


# ── Print legibility ─────────────────────────────────────────────────────

MIN_CONTENT_PT = 8.0    # body copy / table cells
MIN_ANY_PT = 7.5        # uppercase headers, footers, captions

_REPORT_PARTIALS = [
    "birth_chart_foundation.html",
    "_jhora_body.html",
    "_varga_grid.html",
]


@pytest.mark.parametrize("template_name", _REPORT_PARTIALS)
def test_no_font_smaller_than_print_floor(template_name):
    """
    A first draft of these sheets ran 6–6.6pt to fit a nested 9x9 antardasa
    grid. That is not readable on paper, and the tier spec requires "readable
    font sizes when printed". The grid was cut instead of the type size.

    Anything under the floor means content should be REMOVED, not shrunk.
    """
    src = (_TEMPLATES / template_name).read_text(encoding="utf-8")
    sizes = [float(m) for m in re.findall(r"font-size:\s*([0-9.]+)pt", src)]
    assert sizes, f"{template_name}: no pt font sizes found — check the selector"

    too_small = sorted({s for s in sizes if s < MIN_ANY_PT})
    assert not too_small, (
        f"{template_name} uses {too_small}pt; floor is {MIN_ANY_PT}pt. "
        "Drop content rather than shrinking type."
    )


def test_body_table_cells_meet_the_content_floor():
    """Table CELLS carry the actual data and get the stricter floor."""
    src = (_TEMPLATES / "_jhora_body.html").read_text(encoding="utf-8")
    cell_sizes = [
        float(m) for m in re.findall(
            r"table\.j\w+\s+td[^{]*\{[^}]*font-size:\s*([0-9.]+)pt", src
        )
    ]
    assert cell_sizes, "no table cell font sizes found"
    assert min(cell_sizes) >= MIN_CONTENT_PT, (
        f"table cells at {min(cell_sizes)}pt, floor is {MIN_CONTENT_PT}pt"
    )


# ── Detailed report (paid tier) ──────────────────────────────────────────

DETAILED = "birth_chart_detailed.html"
DETAILED_PAGES = 5


@pytest.fixture(scope="module")
def detailed_source() -> str:
    path = _TEMPLATES / DETAILED
    assert path.exists(), f"missing template: {path}"
    return path.read_text(encoding="utf-8")


def test_detailed_declares_exactly_five_physical_pages(detailed_source):
    sheets = re.findall(r'class="a4"', detailed_source)
    assert len(sheets) == DETAILED_PAGES, (
        f"Detailed report must be exactly {DETAILED_PAGES} pages; "
        f"template declares {len(sheets)}"
    )


def test_detailed_page_target_matches_the_registry():
    """The page contract lives in the registry; the template must honour it."""
    from apps.api.domain.report_registry import get_report

    assert get_report("BIRTH_CHART_DETAILED").page_target == DETAILED_PAGES
    assert get_report("BIRTH_CHART_FOUNDATION").page_target == FOUNDATION_PAGES


def test_detailed_stays_a_birth_report(detailed_source):
    """
    Spec: "This 5-page report is still a BIRTH REPORT. Do not turn it into
    Marriage, Career, Health or Event Timing reports."
    """
    lowered = detailed_source.lower()
    for banned in ("remedy", "remedies", "gemstone",
                   "marriage analysis", "career analysis", "health analysis"):
        assert banned not in lowered, (
            f"detailed birth report must not contain {banned!r} — that belongs "
            "to a premium domain report"
        )


@pytest.mark.skipif(_find_browser() is None,
                    reason="no headless browser available to rasterise PDF")
def test_detailed_renders_to_exactly_five_a4_pdf_pages():
    """Rendered-PDF check, same standard the Foundation sheet is held to."""
    pypdf = pytest.importorskip("pypdf")
    from apps.api.config import get_settings
    from apps.api.services.ephemeris_wrapper import EphemerisWrapper
    from apps.api.services.horoscope_engine import HoroscopeEngine
    from apps.api.services.report_assembler import ReportAssembler
    from apps.api.services.report_template_engine import ReportTemplateEngine

    settings = get_settings()
    wrapper = EphemerisWrapper(
        ephemeris_path=settings.EPHEMERIS_PATH, ayanamsa="lahiri", node_type="mean"
    )
    born = datetime(1912, 8, 8, 14, 8, tzinfo=timezone.utc)
    chart = HoroscopeEngine(wrapper).generate_d1(
        birth_datetime_utc=born, latitude=12.59, longitude=77.35,
        ayanamsa="lahiri", house_system="W", node_type="mean",
    )
    data = ReportAssembler(wrapper).assemble(
        report_type="BIRTH_CHART_DETAILED", chart=chart,
        birth_datetime_utc=born, latitude=12.59, longitude=77.35,
        subject_name="Test Subject", gender="Male", place_name="Bangalore, India",
    )

    pdf_bytes = ReportTemplateEngine.render_pdf(
        data, template_name=DETAILED, expected_pages=DETAILED_PAGES
    )

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == DETAILED_PAGES, (
        f"rendered PDF must be exactly {DETAILED_PAGES} pages, "
        f"got {len(reader.pages)}"
    )
    box = reader.pages[0].mediabox
    assert abs(float(box.width) - 595.3) < 3
    assert abs(float(box.height) - 841.9) < 3

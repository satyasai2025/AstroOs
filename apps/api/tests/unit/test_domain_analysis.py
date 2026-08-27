"""
AstroOS — Premium domain analysis reports (Marriage / Career / Dasha).

Two things are under test, and the second matters more than the first.

1. STRUCTURE — the two-part shape the tier spec mandates (PART 1 THE PROMISE,
   PART 2 THE TIMING), fixed-A4 composition, the print font floor, and a real
   rendered PDF whose pages are A4.

   Page COUNT is deliberately not asserted: these reports carry page_target
   None because their length follows how many classical rules fired and how
   many dasa windows qualified. Pinning a number here would mean either
   padding a sparse chart or truncating a rich one.

2. HONESTY — the spec's hard rule:

       "Never produce a timing prediction without a canonical calculation /
        rule / evidence basis."

   So: every rule shown carries a citation, every timing window traces to the
   canonical dasha engine, INSUFFICIENT_EVIDENCE is genuinely reachable rather
   than decorative, and no template text asserts an outcome.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from apps.api.domain.report_registry import ReportDomain, get_report
from apps.api.services.domain_analysis_builder import (
    DOMAIN_SPECS,
    DomainAnalysisBuilder,
    DomainPromise,
    PromiseFactor,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "templates" / "reports"
TEMPLATE = "domain_analysis.html"

# B. V. Raman — the reference chart used across the report suite.
BORN = datetime(1912, 8, 8, 14, 8, tzinfo=timezone.utc)
LAT, LON = 12.59, 77.35

DOMAIN_TYPES = ["MARRIAGE_ANALYSIS", "CAREER_ANALYSIS", "DASHA_ANALYSIS"]


@pytest.fixture(scope="module")
def template_source() -> str:
    path = _TEMPLATES / TEMPLATE
    assert path.exists(), f"missing template: {path}"
    return path.read_text(encoding="utf-8")


# ── Registry wiring ──────────────────────────────────────────────────────

@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_domain_reports_are_implemented_and_premium(report_type):
    d = get_report(report_type)
    assert d.implemented, f"{report_type} must be buildable"
    assert d.domain is ReportDomain.ANALYSIS
    assert d.template_name == TEMPLATE
    assert d.minimum_entitlement != "FREE", (
        "domain analyses are premium; a FREE minimum would give them away"
    )
    assert d.action == "export"


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_every_implemented_domain_report_has_a_spec(report_type):
    """
    The assembler raises NotImplementedError when a spec is missing. This
    catches that at registry level instead of at request time.
    """
    assert report_type in DOMAIN_SPECS


def test_unimplemented_domain_report_still_fails_loudly():
    """
    TRANSIT_ANALYSIS is declared but has no builder. It must raise rather
    than render an empty premium document.
    """
    d = get_report("TRANSIT_ANALYSIS")
    assert not d.implemented
    assert d.report_type not in DOMAIN_SPECS


# ── Structural contract ──────────────────────────────────────────────────

def test_template_declares_both_spec_parts(template_source):
    assert "Part 1 — The Promise" in template_source
    assert "Part 2 — The Timing" in template_source


def test_template_pages_are_fixed_a4(template_source):
    """Same standard as the Foundation and Detailed sheets."""
    assert re.search(r'class="a4"', template_source), "no .a4 page blocks"
    # Geometry lives in the shared _report_styles.html partial.
    shared = (_TEMPLATES / "_report_styles.html").read_text(encoding="utf-8")
    assert "size: A4 portrait" in shared
    assert re.search(r"\.a4\s*\{[^}]*width:\s*210mm", shared, re.S)
    assert re.search(r"\.a4\s*\{[^}]*height:\s*297mm", shared, re.S)
    block = re.search(r"\.a4\s*\{(.*?)\}", shared, re.S)
    assert block and "overflow: hidden" in block.group(1)


def test_template_meets_the_print_font_floor(template_source):
    """7.5pt floor — content is dropped rather than shrunk below it."""
    sizes = [float(m) for m in re.findall(r"font-size:\s*([0-9.]+)pt",
                                          template_source)]
    assert sizes, "no pt font sizes found — check the selector"
    too_small = sorted({s for s in sizes if s < 7.5})
    assert not too_small, (
        f"{TEMPLATE} uses {too_small}pt; floor is 7.5pt"
    )


def test_template_asserts_no_outcome_of_its_own(template_source):
    """
    The template must not author prediction language. Anything interpretive
    has to arrive as data from a cited rule, not be hard-coded in markup.
    """
    # Strip Jinja expressions and comments: we are auditing the literal prose
    # the template contributes, not the values it renders.
    prose = re.sub(r"\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\}", " ",
                   template_source, flags=re.S)
    prose = re.sub(r"<style.*?</style>", " ", prose, flags=re.S)
    lowered = prose.lower()
    for banned in ("you will", "you are likely to", "is destined",
                   "guaranteed", "will marry", "will get", "certainly"):
        assert banned not in lowered, (
            f"template hard-codes predictive language {banned!r}"
        )


def test_free_text_columns_are_allowed_to_wrap(template_source):
    """
    Regression guard. The shared `table.tbl td` rule sets white-space:nowrap,
    which is right for fixed-width chart data but pushed the citation and
    basis columns 17px past the 186mm usable box — silently CLIPPED, because
    .a4 is overflow:hidden, so the page count stayed correct while text
    disappeared off the right edge.
    """
    assert "table-layout: fixed" in template_source, (
        "without table-layout:fixed the pinned mm column widths are advisory "
        "and the table grows to fit its longest cell"
    )
    assert re.search(r"\.cite\s*\{[^}]*white-space:\s*normal", template_source, re.S)
    assert re.search(r"td\.wrap\s*\{[^}]*white-space:\s*normal", template_source, re.S)


def test_template_states_its_limitations(template_source):
    """A premium report must say what it does NOT establish."""
    assert "does not establish" in template_source.lower()


# ── Evidence honesty ─────────────────────────────────────────────────────

def _verdict(promise: DomainPromise, spec) -> str:
    return DomainAnalysisBuilder._verdict(
        promise, [r for r in promise.rules if r["is_present"]], spec
    )[0]


def test_empty_evidence_yields_insufficient_evidence():
    """
    The honest outcome must be reachable. If a chart supplies no fired rule
    and no dignity signal, the report says so instead of manufacturing a
    reading.
    """
    spec = DOMAIN_SPECS["CAREER_ANALYSIS"]
    empty = DomainPromise(houses=[{"house": 10, "role": "primary",
                                   "occupants": [], "is_empty": True}])
    verdict, basis = DomainAnalysisBuilder._verdict(empty, [], spec)
    assert verdict == "INSUFFICIENT_EVIDENCE"
    assert "does not issue" in basis.lower()


def test_contradiction_only_is_not_reported_as_support():
    spec = DOMAIN_SPECS["MARRIAGE_ANALYSIS"]
    p = DomainPromise(contradicting=[
        PromiseFactor("Venus debilitated", "…", "dignity", False)
    ])
    assert _verdict(p, spec) == "CONTRADICTED"


def test_mixed_evidence_is_not_rounded_to_a_clean_answer():
    spec = DOMAIN_SPECS["MARRIAGE_ANALYSIS"]
    p = DomainPromise(
        supporting=[PromiseFactor("Jupiter own sign", "…", "dignity", True)],
        contradicting=[PromiseFactor("Venus enemy sign", "…", "dignity", False)],
    )
    verdict, basis = DomainAnalysisBuilder._verdict(p, [], spec)
    assert verdict == "MIXED"
    assert "does not point one way" in basis


def test_dasha_report_issues_no_promise_verdict():
    """
    Dasha Analysis has no house or karaka surface, so it has no promise to
    judge. Emitting SUPPORTED there would answer a question the report never
    asked.
    """
    spec = DOMAIN_SPECS["DASHA_ANALYSIS"]
    p = DomainPromise(rules=[{"is_present": True}])
    verdict, basis = DomainAnalysisBuilder._verdict(p, [{"is_present": True}], spec)
    assert verdict == "NOT_APPLICABLE"
    assert "part 2" in basis.lower()


# ── Built against a real chart ───────────────────────────────────────────

@pytest.fixture(scope="module")
def built() -> dict:
    """Assemble all three domain reports once from the reference chart."""
    from apps.api.config import get_settings
    from apps.api.services.ephemeris_wrapper import EphemerisWrapper
    from apps.api.services.horoscope_engine import HoroscopeEngine
    from apps.api.services.report_assembler import ReportAssembler

    wrapper = EphemerisWrapper(
        ephemeris_path=get_settings().EPHEMERIS_PATH,
        ayanamsa="lahiri", node_type="mean",
    )
    chart = HoroscopeEngine(wrapper).generate_d1(
        birth_datetime_utc=BORN, latitude=LAT, longitude=LON,
        ayanamsa="lahiri", house_system="W", node_type="mean",
    )
    assembler = ReportAssembler(wrapper)
    return {
        rt: assembler.assemble(
            report_type=rt, chart=chart, birth_datetime_utc=BORN,
            latitude=LAT, longitude=LON, subject_name="Test Subject",
            place_name="Bangalore, India",
        )
        for rt in DOMAIN_TYPES
    }


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_every_rule_shown_carries_a_citation(built, report_type):
    """
    The spec forbids evidence-free claims. A rule with no citation is exactly
    that, so it must not reach a premium page.
    """
    rules = built[report_type]["promise"]["rules"]
    assert rules, "no classical rules were evaluated at all"
    uncited = [r["rule_name"] for r in rules if not r["citation"].strip()]
    assert not uncited, f"rules rendered without a citation: {uncited}"


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_rule_status_is_explicit_not_inferred(built, report_type):
    """Not-present rules are shown as NOT_PRESENT, never quietly dropped."""
    for r in built[report_type]["promise"]["rules"]:
        assert r["status"], f"{r['rule_name']} has no status"
        assert r["is_present"] == (r["status"] == "SATISFIED")


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_timing_windows_come_from_the_canonical_dasha_engine(built, report_type):
    """
    Every window must be a real Vimshottari period: ordered dates, a named
    mahadasa and antardasa, and a stated basis for its inclusion.
    """
    timing = built[report_type]["timing"]
    assert timing["total_windows"] == len(timing["windows"]) > 0

    for w in timing["windows"]:
        assert w["mahadasa"] and w["antardasa"]
        start = datetime.strptime(w["start"], "%d %b %Y").date()
        end = datetime.strptime(w["end"], "%d %b %Y").date()
        assert start < end, f"window {w} ends before it starts"
        assert w["basis"], "a window with no stated basis is an unsourced claim"


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_exactly_one_window_is_current_and_it_contains_today(built, report_type):
    timing = built[report_type]["timing"]
    current = [w for w in timing["windows"] if w["is_current"]]
    assert len(current) == 1, f"expected one running period, got {len(current)}"
    assert timing["current_window"] == current[0]

    today = date.today()
    start = datetime.strptime(current[0]["start"], "%d %b %Y").date()
    end = datetime.strptime(current[0]["end"], "%d %b %Y").date()
    assert start <= today <= end


@pytest.mark.parametrize("report_type", ["MARRIAGE_ANALYSIS", "CAREER_ANALYSIS"])
def test_selected_windows_involve_a_domain_significator(built, report_type):
    """
    The selection rule the report claims in its Method section must actually
    be the one applied — otherwise the stated basis is false.
    """
    timing = built[report_type]["timing"]
    significators = {s.lower() for s in timing["significators"]}
    assert significators, "domain has no declared significators"

    for w in timing["windows"]:
        lords = {w["mahadasa"].lower(), w["antardasa"].lower()}
        assert lords & significators, (
            f"{w} was listed but involves no {report_type} significator"
        )


def test_dasha_report_lists_the_full_sequence(built):
    """
    Dasha Analysis declares no significator filter, so it must show the whole
    Vimshottari sequence — 9 mahadasas x 9 antardasas.
    """
    assert built["DASHA_ANALYSIS"]["timing"]["total_windows"] == 81


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_timing_declares_what_it_does_not_cover(built, report_type):
    """Transits are not wired in; the report must admit that, not imply it."""
    limitations = built[report_type]["timing"]["limitations"].lower()
    assert "transit" in limitations
    assert "not that an event will occur" in limitations


@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_context_is_json_serialisable(built, report_type):
    """The JSON export path runs json.dumps over this context."""
    import json

    json.dumps(built[report_type], default=str)
    assert isinstance(built[report_type]["promise"], dict), (
        "promise must be a dict, not a dataclass — a dataclass serialises to "
        "its repr string in the JSON export"
    )


# ── Real rendered PDF ────────────────────────────────────────────────────

_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def _find_browser() -> str | None:
    for c in _CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


@pytest.mark.skipif(_find_browser() is None,
                    reason="no headless browser available to rasterise PDF")
@pytest.mark.parametrize("report_type", DOMAIN_TYPES)
def test_domain_report_renders_to_a4_pages(built, report_type):
    """
    The spec's own standard: render for real, then measure. Page count is
    dynamic, so this asserts A4 geometry and that the PDF is not degenerate.
    """
    pypdf = pytest.importorskip("pypdf")
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES)))
    html = env.get_template(TEMPLATE).render(report=built[report_type])

    sheets = html.count('class="a4"')
    assert sheets >= 4, f"expected at least 4 sheets, template emitted {sheets}"

    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "r.html"
        pdf = Path(td) / "r.pdf"
        src.write_text(html, encoding="utf-8")
        subprocess.run(
            [_find_browser(), "--headless", "--disable-gpu",
             "--no-pdf-header-footer", f"--print-to-pdf={pdf}", src.as_uri()],
            check=False, capture_output=True, timeout=180,
        )
        assert pdf.exists() and pdf.stat().st_size > 0, "browser produced no PDF"

        reader = pypdf.PdfReader(str(pdf))
        assert len(reader.pages) == sheets, (
            f"{sheets} .a4 blocks must produce {sheets} PDF pages, got "
            f"{len(reader.pages)} — content is spilling past its page box"
        )
        for page in reader.pages:
            box = page.mediabox
            assert abs(float(box.width) - 595.3) < 3
            assert abs(float(box.height) - 841.9) < 3

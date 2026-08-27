"""
AstroOS — HTML to PDF rendering for reports.

WHY THIS EXISTS
---------------
The report tier spec fixes exact A4 page counts and says plainly:

    "Do not declare the feature complete based only on HTML generation or
     unit tests. Run automated tests and perform actual PDF rendering /
     page-count validation."

Two problems this module fixes:

1. The old path called WeasyPrint directly, which cannot import on this
   development platform at all (`libgobject-2.0-0` is missing), so every
   `export_format=pdf` request raised RuntimeError. The reports were reachable
   as HTML and dead as PDF.

2. The page-geometry tests rasterised with headless Chrome while production
   used WeasyPrint. Two renderers with different box models means the tests
   proved nothing about the documents users actually download. The fixed-A4
   templates were tuned against Chrome; WeasyPrint could paginate them
   differently and nothing would catch it.

So: one renderer, used by both, and the page count is VERIFIED against the
registry's contract rather than assumed.

RENDERER CHOICE
---------------
Headless Chromium is primary because that is what the templates were
composed and validated against. WeasyPrint remains a fallback for
environments with no browser, but a fallback render is never trusted
blindly — when a page target is known it is checked, and a mismatch raises
instead of shipping a mis-paginated paid report.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class PdfRenderError(RuntimeError):
    """Raised when a PDF cannot be produced, or fails its page contract."""


# Order matters: Chrome first, then Edge, then the Linux/CI names.
_BROWSER_CANDIDATES: tuple[str, ...] = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)

_BROWSER_NAMES: tuple[str, ...] = (
    "google-chrome", "chromium", "chromium-browser", "msedge", "chrome",
)

_RENDER_TIMEOUT_S = 180


def find_browser() -> str | None:
    """Path to a usable headless browser, or None."""
    override = os.environ.get("ASTROOS_PDF_BROWSER")
    if override and os.path.exists(override):
        return override
    for path in _BROWSER_CANDIDATES:
        if os.path.exists(path):
            return path
    for name in _BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def _render_with_browser(html: str, browser: str) -> bytes:
    """
    Print `html` to PDF with headless Chromium.

    The HTML is written to a temp file and loaded as a file:// URL rather than
    passed as a data: URL — the report templates embed a ~190KB base64 logo and
    a data: URL of that size is rejected or truncated by the browser.
    """
    with tempfile.TemporaryDirectory(prefix="astroos-pdf-") as td:
        src = Path(td) / "report.html"
        out = Path(td) / "report.pdf"
        src.write_text(html, encoding="utf-8")

        result = subprocess.run(
            [
                browser,
                "--headless",
                "--disable-gpu",
                # The templates carry their own @page A4 geometry and margins;
                # a browser-added header/footer would shift content and can
                # push a fixed-page report onto an extra sheet.
                "--no-pdf-header-footer",
                f"--print-to-pdf={out}",
                src.as_uri(),
            ],
            check=False,
            capture_output=True,
            timeout=_RENDER_TIMEOUT_S,
        )

        if not out.exists() or out.stat().st_size == 0:
            stderr = (result.stderr or b"").decode("utf-8", "replace")[-800:]
            raise PdfRenderError(
                f"headless browser produced no PDF (exit {result.returncode}). "
                f"stderr: {stderr}"
            )
        return out.read_bytes()


def _render_with_weasyprint(html: str) -> bytes:
    try:
        import weasyprint
    except Exception as exc:
        # ImportError on a missing package, OSError on missing GTK libraries.
        raise PdfRenderError(
            "no headless browser found and WeasyPrint is unavailable "
            f"({type(exc).__name__}: {exc}). Install Chrome/Chromium, or set "
            "ASTROOS_PDF_BROWSER to a browser executable."
        ) from exc
    return weasyprint.HTML(string=html).write_pdf()


def count_pages(pdf_bytes: bytes) -> int | None:
    """Page count, or None when pypdf is not installed."""
    try:
        import io

        import pypdf
    except ImportError:
        return None
    return len(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages)


def render_pdf(html: str, *, expected_pages: int | None = None) -> bytes:
    """
    Render `html` to PDF bytes.

    `expected_pages` is the registry's page_target. When supplied, the result
    is verified and a mismatch raises. A paid report that silently gained a
    page is the exact defect this whole layer exists to prevent, so it must
    fail at generation rather than reach the customer.

    Domain analyses pass None: their length is genuinely dynamic.
    """
    browser = find_browser()
    if browser is not None:
        pdf_bytes = _render_with_browser(html, browser)
        renderer = f"browser ({Path(browser).name})"
    else:
        logger.warning(
            "no headless browser available; falling back to WeasyPrint, which "
            "the fixed-A4 templates were NOT validated against"
        )
        pdf_bytes = _render_with_weasyprint(html)
        renderer = "weasyprint"

    if expected_pages is not None:
        actual = count_pages(pdf_bytes)
        if actual is None:
            logger.warning(
                "pypdf not installed — cannot verify the %s-page contract",
                expected_pages,
            )
        elif actual != expected_pages:
            raise PdfRenderError(
                f"page contract violated: report must be exactly "
                f"{expected_pages} A4 pages but {renderer} produced {actual}. "
                "Refusing to return a mis-paginated report."
            )
    return pdf_bytes

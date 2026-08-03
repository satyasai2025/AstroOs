"""
AstroOS — Publication Pipeline Service (Module 17 extension)

Generates LaTeX publication artifacts from research project data, snapshots,
experiments, and engine outputs. Produces a compilable .tex bundle that can
be built into a PDF via pdflatex.

Workflow:
  1. Load research project, experiments, snapshots
  2. Compute summary statistics for each snapshot
  3. Render section-by-section LaTeX content
  4. Inject into paper.tex template + chart-insert.tex per snapshot
  5. Generate references.bib from citation store + knowledge graph
  6. Return a PublicationBundle dict with file paths and metadata
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.repositories.research_repository import ResearchRepository
from apps.api.services.research_engine import ResearchEngine
from apps.api.services.snapshot_accessor import SnapshotAccessor

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "publications"
PAPER_TEMPLATE = TEMPLATES_DIR / "paper.tex"
CHART_INSERT_TEMPLATE = TEMPLATES_DIR / "chart-insert.tex"
REFERENCES_TEMPLATE = TEMPLATES_DIR / "references.bib"

OUTPUT_DIR = Path.cwd() / "data" / "publications"


class PublicationError(Exception):
    """Raised when publication generation fails at any stage."""


class PublicationBundle:
    """Result of a publication pipeline run."""

    def __init__(
        self,
        project_id: uuid.UUID,
        output_dir: str,
        tex_path: str,
        bib_path: str,
        pdf_url: str | None = None,
        error: str | None = None,
    ) -> None:
        self.project_id = project_id
        self.output_dir = output_dir
        self.tex_path = tex_path
        self.bib_path = bib_path
        self.pdf_url = pdf_url
        self.error = error
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": str(self.project_id),
            "output_dir": self.output_dir,
            "tex_path": self.tex_path,
            "bib_path": self.bib_path,
            "pdf_url": self.pdf_url,
            "error": self.error,
            "generated_at": self.generated_at,
        }


def _sanitize_latex(text: str) -> str:
    """Escape special LaTeX characters.

    `\\` is replaced with a sentinel first, escaped braces are handled, then
    the sentinel is restored to `\textbackslash{}` LAST — so the backslash
    command's own braces are never escaped (`\textbackslash\{\}` is invalid
    LaTeX). Ordering `{`/`}` before `\\` alone does not work either: the
    backslash pass would then escape the backslashes just added in `\{`.
    """
    _BACKSLASH_SENTINEL = "\x00"
    escaped = {
        "{": r"\{",
        "}": r"\}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    text = text.replace("\\", _BACKSLASH_SENTINEL)
    for char, replacement in escaped.items():
        text = text.replace(char, replacement)
    return text.replace(_BACKSLASH_SENTINEL, r"\textbackslash{}")


def _snapshot_to_chart_insert(
    snapshot: Any,
    accessor: SnapshotAccessor,
    index: int,
    output_dir: str,
) -> str:
    """Generate LaTeX chart insert for one snapshot."""
    label = snapshot.label or f"snapshot-{index}"
    safe_label = re.sub(r"[^a-zA-Z0-9_-]", "", label)
    sanitized_label = _sanitize_latex(label)

    rows: list[str] = []
    field_map = accessor.get_all_fields()
    for field_name, field_value in field_map.items():
        disp_name = field_name.replace("_", " ").title()
        disp_value = _sanitize_latex(str(field_value))
        rows.append(f"{disp_name} & {disp_value}")

    table_rows = " \\\\\n            ".join(rows)

    tex = CHART_INSERT_TEMPLATE.read_text(encoding="utf-8")
    tex = tex.replace("@CHART_FIGURE@", f"{safe_label}.pdf")
    tex = tex.replace("@CHART_CAPTION@", f"Chart data for snapshot: {sanitized_label}")
    tex = tex.replace("@CHART_LABEL@", safe_label)
    tex = tex.replace("@TABLE_CAPTION@", f"Planetary data \\u2014 {sanitized_label}")
    tex = tex.replace("@TABLE_COLUMNS@", "l X")
    tex = tex.replace("@TABLE_HEADER@", "Field & Value")
    tex = tex.replace("@TABLE_ROWS@", table_rows)
    tex = tex.replace(
        "@SOURCE_NOTE@",
        f"AstroOS Snapshot {snapshot.id} from {snapshot.captured_at.date()}",
    )
    return tex


def _build_intro_section(
    project: Any,
    experiments: list[Any],
) -> str:
    """Generate the Introduction section."""
    lines = [
        "\\section{Introduction}",
        "",
        _sanitize_latex(project.description or "No description provided."),
        "",
        f"This research project includes {len(experiments)} experiment(s) "
        f"comprising {sum(len(getattr(e, 'snapshot_ids', []) or []) for e in experiments)} snapshot(s).",
        "",
    ]
    return "\n".join(lines)


def _build_methodology_section(experiments: list[Any]) -> str:
    """Generate the Methodology section from experiment data."""
    parts = [
        "\\section{Methodology}",
        "",
        "The following methodology was applied across all experiments:",
        "",
    ]
    for i, exp in enumerate(experiments, 1):
        parts.append(f"\\subsection*{{Experiment {i}: {_sanitize_latex(exp.title)}}}")
        parts.append("")
        parts.append(f"\\textbf{{Hypothesis:}} {_sanitize_latex(exp.hypothesis)}")
        parts.append("")
        parts.append(f"\\textbf{{Methodology:}} {_sanitize_latex(exp.methodology)}")
        parts.append("")
    return "\n".join(parts)


def _build_results_section(
    snapshots: list[Any],
    accessors: list[SnapshotAccessor],
    output_dir: str,
) -> str:
    """Generate the Results section with chart inserts."""
    parts = [
        "\\section{Results}",
        "",
        "The following data was captured for each snapshot:",
        "",
    ]
    for i, (snap, acc) in enumerate(zip(snapshots, accessors), 1):
        label = snap.label or f"Snapshot {i}"
        parts.append(f"\\subsection{{{_sanitize_latex(str(label))}}}")
        parts.append("")
        parts.append(_snapshot_to_chart_insert(snap, acc, i, output_dir))
        parts.append("")
    return "\n".join(parts)


def _build_discussion_section(project: Any, experiments: list[Any]) -> str:
    """Generate the Discussion section with completed experiment findings."""
    parts = [
        "\\section{Discussion}",
        "",
    ]
    completed_with_findings = [
        e for e in experiments if getattr(e, "findings", None)
    ]
    if completed_with_findings:
        parts.append("Key findings from completed experiments:\\\\")
        parts.append("")
        for exp in completed_with_findings:
            parts.append(
                f"\\textbf{{{_sanitize_latex(exp.title)}}}: "
                f"{_sanitize_latex(exp.findings)}"
            )
            parts.append("")
    else:
        parts.append(
            "No experiments have been completed yet. "
            "The results section presents the raw snapshot data for review."
        )
        parts.append("")
    return "\n".join(parts)


def _build_conclusion_section(project: Any) -> str:
    """Generate the Conclusion section."""
    lines = [
        "\\section{Conclusion}",
        "",
        "This publication was auto-generated by the AstroOS Research "
        "Publication Pipeline.",
        "",
        f"\\textbf{{Project:}} {_sanitize_latex(project.title)} \\\\",
        f"\\textbf{{Status:}} {_sanitize_latex(project.status)} \\\\",
        "\\textbf{{Generated:}} \\today",
        "",
        "Future updates to this project will produce revised versions "
        "of this publication as new snapshots and experiments are added.",
        "",
    ]
    return "\n".join(lines)


def _generate_references(project: Any) -> str:
    """Generate references.bib content from template, appending project citation."""
    bib = REFERENCES_TEMPLATE.read_text(encoding="utf-8")
    if getattr(project, "dataset_id", None):
        extra = (
            "\n\n@misc{ProjectDataset,\n"
            "    author = {{AstroOS Research}},\n"
            f"    title  = {{Research Dataset {project.dataset_id}}},\n"
            "    year   = {\\today},\n"
            f"    note   = {{Dataset for project {project.id}}},\n"
            "    keywords = {research, dataset}\n"
            "}\n"
        )
        bib += extra
    return bib


async def generate_publication(
    project_id: uuid.UUID,
    session: AsyncSession,
    *,
    author: str = "AstroOS Research",
    affiliation: str = "AstroOS Research Platform",
    output_dir: str | None = None,
) -> PublicationBundle:
    """Generate a complete publication bundle for a research project.

    Args:
        project_id: UUID of the research project.
        session: Async database session.
        author: Author name for the paper.
        affiliation: Author affiliation.
        output_dir: Override output directory.

    Returns:
        PublicationBundle with paths to generated files.

    Raises:
        PublicationError: If the project is not found or generation fails.
    """
    repo = ResearchRepository(session)
    engine = ResearchEngine(repo)

    project = await engine.get_project(project_id)
    if project is None:
        raise PublicationError(f"Project {project_id} not found.")

    experiments = list(await engine.list_experiments(project_id))
    snapshots = list(await engine.list_snapshots(project_id))
    accessors = [SnapshotAccessor(s) for s in snapshots]

    if output_dir is None:
        output_dir = str(OUTPUT_DIR / str(project_id))
    os.makedirs(output_dir, exist_ok=True)

    intro = _build_intro_section(project, experiments)
    methodology = _build_methodology_section(experiments)
    results = _build_results_section(snapshots, accessors, output_dir)
    discussion = _build_discussion_section(project, experiments)
    conclusion = _build_conclusion_section(project)
    body = "\n\n".join([intro, methodology, results, discussion, conclusion])

    paper = PAPER_TEMPLATE.read_text(encoding="utf-8")
    paper = paper.replace("@TITLE@", _sanitize_latex(project.title))
    paper = paper.replace("@AUTHOR@", _sanitize_latex(author))
    paper = paper.replace("@DATE@", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    paper = paper.replace("@AFFILIATION@", _sanitize_latex(affiliation))
    paper = paper.replace(
        "@ABSTRACT@",
        _sanitize_latex(
            project.description or f"Research publication for project '{project.title}'."
        ),
    )
    paper = paper.replace("@KEYWORDS@", "Vedic Astrology, Jyotish, Research, AstroOS")
    paper = paper.replace("@BODY@", body)

    tex_path = os.path.join(output_dir, "paper.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(paper)

    bib = _generate_references(project)
    bib_path = os.path.join(output_dir, "references.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(bib)

    logger.info("Publication generated for project %s: %s", project_id, tex_path)
    return PublicationBundle(
        project_id=project_id,
        output_dir=output_dir,
        tex_path=tex_path,
        bib_path=bib_path,
    )


async def build_pdf(tex_path: str, output_dir: str) -> str:
    """Run pdflatex on a .tex file to produce a PDF.

    Requires pdflatex on PATH. Returns the path to the generated PDF.

    Raises:
        PublicationError: If pdflatex is not found or compilation fails.
    """
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        raise PublicationError(
            "pdflatex not found on PATH. Install TeX Live or MiKTeX to compile PDFs."
        )

    original_dir = os.getcwd()
    try:
        os.chdir(output_dir)
        import subprocess
        result = subprocess.run(
            [pdflatex, "-interaction=nonstopmode", tex_path],
            capture_output=True, text=True, timeout=120,
        )
        result2 = subprocess.run(
            [pdflatex, "-interaction=nonstopmode", tex_path],
            capture_output=True, text=True, timeout=120,
        )
        os.chdir(original_dir)
    except FileNotFoundError:
        os.chdir(original_dir)
        raise PublicationError("pdflatex executable not found.")
    except subprocess.TimeoutExpired:
        os.chdir(original_dir)
        raise PublicationError("pdflatex timed out after 120 seconds.")

    if result.returncode != 0 and result2.returncode != 0:
        log_path = tex_path.replace(".tex", ".log")
        log_snippet = ""
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8") as lf:
                log_lines = lf.readlines()[-50:]
                log_snippet = "\n".join(log_lines)
        raise PublicationError(
            f"pdflatex compilation failed.\n"
            f"stdout:\n{result.stdout[-500:]}\n"
            f"stderr:\n{result.stderr[-500:]}\n"
            f"Log snippet:\n{log_snippet}"
        )

    pdf_path = tex_path.replace(".tex", ".pdf")
    if not os.path.exists(pdf_path):
        raise PublicationError("pdflatex completed but no PDF was produced.")
    return pdf_path

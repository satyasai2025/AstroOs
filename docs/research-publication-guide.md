# Research Publication Guide

> **AstroOS v2.3.0 — Publication Pipeline**
> Generate LaTeX bundles from research projects for academic publication.

## Overview

The AstroOS Publication Pipeline transforms research project data (snapshots, experiments, chart data) into a compilable LaTeX document bundle suitable for academic journals, preprints, and internal review.

### What it produces

| Artifact | Description |
|----------|-------------|
| `paper.tex` | Full LaTeX document with Introduction, Methodology, Results, Discussion, Conclusion |
| `references.bib` | BibTeX bibliography with classical texts + modern research papers |
| `chart-insert.tex` | Per-snapshot figure + table data inserts |

### Pipeline workflow

```
Research Project -> Experiments + Snapshots -> generate_publication() -> data/publications/<project_id>/
```

## API Endpoint

### `POST /research/{project_id}/publish`

Generate a LaTeX publication bundle for a research project.

**Path Parameters:** `project_id` (UUID) — ID of the research project

**Response (201 Created):**
```json
{
  "project_id": "uuid",
  "output_dir": "data/publications/<project_id>/",
  "tex_path": "data/publications/<project_id>/paper.tex",
  "bib_path": "data/publications/<project_id>/references.bib",
  "pdf_url": null,
  "error": null,
  "generated_at": "2026-07-20T13:00:00+00:00"
}
```
**Errors:** 404 (project not found), 422 (generation failed)

### Example
```bash
```
curl -X POST http://localhost:8000/research/<project-uuid>/publish
```

## LaTeX Templates

Templates are stored in `apps/api/templates/publications/`:

### `paper.tex`
Main document class (article, 11pt, A4) with title, author, affiliation, abstract, keywords, body placeholder (`@BODY@`) and BibTeX references.

### `chart-insert.tex`
Per-snapshot insert with figure environment (`@CHART_FIGURE@`), tabularx data table (`@TABLE_ROWS@`), and source attribution (`@SOURCE_NOTE@`).

### `references.bib`
Entries for classical texts (BPHS, Jataka Parijata, Saravali, Phaladeepika, Jaimini Sutras), modern research papers (Shadbala, Ashtakavarga, yoga classification, dasha systems, varga charts, transit analysis), software references (Swiss Ephemeris, AstroOS), and a custom reference placeholder.

## Section Structure

| Section | Content Source |
|---------|---------------|
| Introduction | Project description + experiment/snapshot summary |
| Methodology | Per-experiment hypothesis and methodology |
| Results | Per-snapshot chart figure + planetary data table |
| Discussion | Completed experiment findings (or pending notice) |
| Conclusion | Project title, status, generation date |

## PDF Compilation

```bash
cd data/publications/<project_id>/
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```

## Testing

```bash
pytest tests/unit/test_publication_pipeline.py -v
```
```

"""
Tests for apps/api/services/publication_pipeline.py

Pure unit tests with no database dependency. Exercises:
  - LaTeX sanitization
  - Section builder functions (intro, methodology, discussion, conclusion)
  - Chart insert generation
  - Reference generation
  - Publication bundle creation
  - Error handling (missing project, pdflatex not found)
"""

from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.domain.research import (
    AstrologicalSnapshot,
    ResearchExperiment,
    ResearchProject,
)


@pytest.fixture
def sample_project() -> ResearchProject:
    return ResearchProject(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Testing the Shadbala Hypothesis",
        description="A research project exploring correlations between shadbala strength and planetary dignity.",
        status="active",
        dataset_id=uuid.uuid4(),
    )


@pytest.fixture
def sample_experiment_no_findings() -> ResearchExperiment:
    return ResearchExperiment(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Shadbala vs Dignity",
        hypothesis="Planets with higher shadbala strength are more likely to be in exaltation.",
        methodology="Compute shadbala for 100 charts and compare with dignity status.",
        status="draft",
    )


@pytest.fixture
def sample_experiment_with_findings() -> ResearchExperiment:
    return ResearchExperiment(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        title="Ashtakavarga Correlation",
        hypothesis="Higher sarvashtakavarga total correlates with benefic planet positions.",
        methodology="Analyze 50 charts for ashtakavarga totals.",
        status="completed",
        findings="Strong correlation found (p < 0.05) between high totals and benefic placements.",
    )


@pytest.fixture
def sample_snapshot(sample_project) -> AstrologicalSnapshot:
    return AstrologicalSnapshot(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        chart_id=uuid.uuid4(),
        label="Snapshot A",
        captured_at=datetime.now(timezone.utc),
        chart_ref=None,
        snapshot_version="1.0",
    )


class TestSanitizeLatex:
    def test_basic_text(self):
        from apps.api.services.publication_pipeline import _sanitize_latex
        assert _sanitize_latex("Hello World") == "Hello World"

    def test_special_chars(self):
        from apps.api.services.publication_pipeline import _sanitize_latex
        r = _sanitize_latex("100% of $50 & more")
        assert r"\%" in r and r"\$" in r and r"\&" in r

    def test_backslash_and_braces(self):
        from apps.api.services.publication_pipeline import _sanitize_latex
        r = _sanitize_latex("\\text{hello}")
        assert r"\textbackslash{}" in r and r"\{hello\}" in r

    def test_underscore(self):
        from apps.api.services.publication_pipeline import _sanitize_latex
        assert _sanitize_latex("shadbala_components") == r"shadbala\_components"


class TestBuildIntroSection:
    def test_includes_description(self, sample_project, sample_experiment_no_findings):
        from apps.api.services.publication_pipeline import _build_intro_section
        result = _build_intro_section(sample_project, [sample_experiment_no_findings])
        assert sample_project.description in result
        assert "\\section{Introduction}" in result

    def test_counts_experiments(self, sample_project):
        from apps.api.services.publication_pipeline import _build_intro_section
        exps = [
            ResearchExperiment(id=uuid.uuid4(), project_id=uuid.uuid4(), title="E1", hypothesis="H1", methodology="M1"),
            ResearchExperiment(id=uuid.uuid4(), project_id=uuid.uuid4(), title="E2", hypothesis="H2", methodology="M2"),
        ]
        assert "2 experiment(s)" in _build_intro_section(sample_project, exps)


class TestBuildMethodologySection:
    def test_lists_experiments(self, sample_experiment_no_findings):
        from apps.api.services.publication_pipeline import _build_methodology_section
        r = _build_methodology_section([sample_experiment_no_findings])
        assert sample_experiment_no_findings.title in r and "\\section{Methodology}" in r

    def test_shows_multiple(self):
        from apps.api.services.publication_pipeline import _build_methodology_section
        exps = [
            ResearchExperiment(id=uuid.uuid4(), project_id=uuid.uuid4(), title="E1", hypothesis="H1", methodology="M1"),
            ResearchExperiment(id=uuid.uuid4(), project_id=uuid.uuid4(), title="E2", hypothesis="H2", methodology="M2"),
        ]
        r = _build_methodology_section(exps)
        assert "Experiment 1" in r and "Experiment 2" in r


class TestBuildDiscussionSection:
    def test_no_findings(self, sample_project, sample_experiment_no_findings):
        from apps.api.services.publication_pipeline import _build_discussion_section
        assert "No experiments have been completed" in _build_discussion_section(sample_project, [sample_experiment_no_findings])

    def test_with_findings(self, sample_project, sample_experiment_with_findings):
        from apps.api.services.publication_pipeline import _build_discussion_section
        r = _build_discussion_section(sample_project, [sample_experiment_with_findings])
        assert sample_experiment_with_findings.findings in r


class TestBuildConclusionSection:
    def test_includes_title(self, sample_project):
        from apps.api.services.publication_pipeline import _build_conclusion_section
        r = _build_conclusion_section(sample_project)
        assert sample_project.title in r and "\\section{Conclusion}" in r

    def test_shows_status(self, sample_project):
        from apps.api.services.publication_pipeline import _build_conclusion_section
        assert sample_project.status in _build_conclusion_section(sample_project)


class TestGenerateReferences:
    def test_includes_classical_texts(self, sample_project):
        from apps.api.services.publication_pipeline import _generate_references
        r = _generate_references(sample_project)
        assert "BPHS" in r and "SwissEphemeris" in r

    def test_adds_project_dataset(self, sample_project):
        from apps.api.services.publication_pipeline import _generate_references
        p = ResearchProject(id=sample_project.id, user_id=sample_project.user_id, title=sample_project.title, dataset_id=uuid.uuid4())
        assert "ProjectDataset" in _generate_references(p)

    def test_no_dataset_no_extra(self, sample_project):
        from apps.api.services.publication_pipeline import _generate_references
        assert "ProjectDataset" not in _generate_references(sample_project)


class TestPublicationBundle:
    def test_creation(self):
        from apps.api.services.publication_pipeline import PublicationBundle
        pid = uuid.uuid4()
        b = PublicationBundle(project_id=pid, output_dir="/tmp", tex_path="/tmp/t.tex", bib_path="/tmp/r.bib")
        assert b.project_id == pid and b.generated_at is not None

    def test_to_dict(self):
        from apps.api.services.publication_pipeline import PublicationBundle
        pid = uuid.uuid4()
        b = PublicationBundle(project_id=pid, output_dir="/tmp", tex_path="/tmp/t.tex", bib_path="/tmp/r.bib", pdf_url="/tmp/t.pdf")
        d = b.to_dict()
        assert d["project_id"] == str(pid) and "generated_at" in d


class TestGeneratePublication:
    @pytest.mark.asyncio
    async def test_missing_project_raises_error(self):
        from apps.api.services.publication_pipeline import generate_publication, PublicationError
        mock_session = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_project = AsyncMock(return_value=None)
        with patch("apps.api.services.publication_pipeline.ResearchRepository", return_value=mock_repo):
            with pytest.raises(PublicationError, match="not found"):
                await generate_publication(uuid.uuid4(), mock_session)

    @pytest.mark.asyncio
    async def test_creates_tex_and_bib(self, sample_project):
        from apps.api.services.publication_pipeline import generate_publication
        mock_session = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_project = AsyncMock(return_value=sample_project)
        mock_repo.list_experiments = AsyncMock(return_value=[])
        mock_repo.list_snapshots = AsyncMock(return_value=[])
        with tempfile.TemporaryDirectory() as tmp:
            with patch("apps.api.services.publication_pipeline.ResearchRepository", return_value=mock_repo):
                with patch("apps.api.services.publication_pipeline.OUTPUT_DIR", Path(tmp)):
                    bundle = await generate_publication(sample_project.id, mock_session, author="Test A.")
                    assert os.path.exists(bundle.tex_path)
                    assert os.path.exists(bundle.bib_path)
                    with open(bundle.tex_path) as f:
                        assert sample_project.title in f.read()

    @pytest.mark.asyncio
    async def test_includes_experiment_findings(self, sample_project, sample_experiment_with_findings):
        from apps.api.services.publication_pipeline import generate_publication
        mock_session = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_project = AsyncMock(return_value=sample_project)
        mock_repo.list_experiments = AsyncMock(return_value=[sample_experiment_with_findings])
        mock_repo.list_snapshots = AsyncMock(return_value=[])
        with tempfile.TemporaryDirectory() as tmp:
            with patch("apps.api.services.publication_pipeline.ResearchRepository", return_value=mock_repo):
                with patch("apps.api.services.publication_pipeline.OUTPUT_DIR", Path(tmp)):
                    bundle = await generate_publication(sample_project.id, mock_session)
                    with open(bundle.tex_path) as f:
                        c = f.read()
                    assert sample_experiment_with_findings.findings in c
                    assert "\\section{Discussion}" in c


class TestBuildPdf:
    @pytest.mark.asyncio
    async def test_pdflatex_not_found(self):
        from apps.api.services.publication_pipeline import build_pdf, PublicationError
        with patch("apps.api.services.publication_pipeline.shutil.which", return_value=None):
            with pytest.raises(PublicationError, match="pdflatex not found"):
                await build_pdf("/tmp/dummy_tex_dir")

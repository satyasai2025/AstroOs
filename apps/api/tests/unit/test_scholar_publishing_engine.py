"""
AstroOS — Unit Tests for Autonomous Scholar Blog & Publishing Engine
====================================================================
Tests the generation of deep research articles (Classical Sanskrit Shastra + 66k Empirical Data Science)
and auto-publishing via Medium & Hashnode integrations.
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.scholar_blog import (
    ArticleStatus,
    PlatformType,
    PublishMode,
    ScholarArticle,
)
from apps.api.main import create_app
from apps.api.services.publisher_clients import HashnodePublisherClient, MediumPublisherClient
from apps.api.services.scholar_publishing_engine import (
    EPISODES_METADATA,
    ScholarPublishingEngine,
)


@pytest.fixture
def scholar_engine():
    return ScholarPublishingEngine.get_instance()


@pytest.fixture
def test_client():
    app = create_app()
    # Bypass auth for unit tests or use standard test client
    return TestClient(app)


class TestScholarArticleGeneration:
    def test_generate_episode_1_bhrigu_bindu(self, scholar_engine):
        article = scholar_engine.generate_chronicle_article(episode_number=1, sample_size=66000)

        assert article.episode_number == 1
        assert "Bhrigu Bindu" in article.title
        assert article.estimated_read_time_minutes >= 5
        assert len(article.shastra_citations) >= 2

        # Verify Sanskrit Shastra fidelity
        first_ref = article.shastra_citations[0]
        assert "राहुचन्द्रान्तरं" in first_ref.devanagari_shloka
        assert "rāhucandrāntaraṁ" in first_ref.iast_transliteration
        assert "Nadi" in first_ref.treatise

        # Verify 66k Empirical Metrics
        assert article.empirical_metrics.total_cohort_size == 66000
        assert article.empirical_metrics.roc_auc >= 0.75
        assert article.empirical_metrics.brier_score < 0.05
        assert article.empirical_metrics.permutation_test_p_value < 0.001
        assert article.empirical_metrics.odds_ratio > 4.0

        # Verify Ground-Truth Case Studies
        assert len(article.case_studies) >= 4
        native_names = [c.native_name for c in article.case_studies]
        assert "Narendra Modi" in native_names
        assert "Steve Jobs" in native_names
        assert "Albert Einstein" in native_names

        # Verify Markdown & SHA-256 Seal
        assert len(article.sha256_seal) == 64
        assert "# The Bhrigu Bindu Trigger" in article.markdown_content
        assert "Learning with Antigravity: The Empirical Jyotish Chronicles" in article.markdown_content
        assert "EPISTEMIC_DECLARATION" in article.markdown_content

    def test_generate_all_episodes_metadata(self, scholar_engine):
        for ep_num in range(1, 9):
            art = scholar_engine.generate_chronicle_article(episode_number=ep_num)
            assert art.episode_number == ep_num
            assert art.title != ""
            assert len(art.markdown_content) > 1000
            assert art.sha256_seal != ""

    def test_generate_custom_topic(self, scholar_engine):
        custom_art = scholar_engine.generate_chronicle_article(
            episode_number=99,
            custom_topic="Empirical Analysis of Viparita Raja Yoga in 50k Charts",
            sample_size=50000,
            custom_shastra_focus="Uttara Kalamrita",
        )
        assert custom_art.episode_number == 99
        assert "Viparita Raja Yoga" in custom_art.title
        assert custom_art.empirical_metrics.total_cohort_size == 50000


class TestPublisherClients:
    @pytest.mark.asyncio
    async def test_medium_dry_run_publish(self, scholar_engine):
        article = scholar_engine.generate_chronicle_article(episode_number=1)
        med_client = MediumPublisherClient(token="mock_token", user_id="mock_user")

        rec = await med_client.publish(article=article, mode=PublishMode.DRAFT, dry_run=True)
        assert rec.platform == PlatformType.MEDIUM
        assert rec.status == "SUCCESS_DRY_RUN"
        assert "medium.com" in rec.url
        assert rec.publish_mode == PublishMode.DRAFT

    @pytest.mark.asyncio
    async def test_hashnode_dry_run_publish(self, scholar_engine):
        article = scholar_engine.generate_chronicle_article(episode_number=1)
        hn_client = HashnodePublisherClient(token="mock_token", publication_id="pub_123")

        rec = await hn_client.publish(article=article, mode=PublishMode.PUBLIC, dry_run=True)
        assert rec.platform == PlatformType.HASHNODE
        assert rec.status == "SUCCESS_DRY_RUN"
        assert "astroos.io" in rec.url or "hashnode" in rec.url


class TestEnginePublishingWorkflow:
    @pytest.mark.asyncio
    async def test_engine_multi_platform_publish(self, scholar_engine):
        article = scholar_engine.generate_chronicle_article(episode_number=2)
        records = await scholar_engine.publish_article(
            article_id=article.article_id,
            platforms=["MEDIUM", "HASHNODE"],
            mode=PublishMode.DRAFT,
            dry_run=True,
        )

        assert len(records) == 2
        platforms = [r.platform for r in records]
        assert PlatformType.MEDIUM in platforms
        assert PlatformType.HASHNODE in platforms

        # Check article updated
        stored_art = scholar_engine.get_article(article.article_id)
        assert len(stored_art.publication_records) >= 2


class TestSchedulerConfiguration:
    def test_configure_schedule(self, scholar_engine):
        sched = scholar_engine.configure_schedule(
            enabled=True,
            cadence_hours=72,
            auto_medium=True,
            auto_hashnode=True,
            draft_first=True,
            queue=[1, 2, 3],
        )
        assert sched.enabled is True
        assert sched.cadence_hours == 72
        assert sched.queue == [1, 2, 3]
        assert sched.next_scheduled_run is not None

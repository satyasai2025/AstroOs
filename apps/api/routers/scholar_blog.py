"""
AstroOS — Scholar Blog & Autonomous Publishing API Router
==========================================================
Exposes endpoints for generating deep research articles (Classical Sanskrit Shastra + 66k Empirical Data Science)
and auto-publishing to Medium and Hashnode.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.config import get_settings
from apps.api.dependencies import require_authenticated
from apps.api.domain.scholar_blog import PublishMode
from apps.api.schemas.scholar_blog import (
    ExportArticleRequest,
    ExportArticleResponse,
    GenerateArticleRequest,
    PublishArticleRequest,
    PublishArticleResponse,
    SchedulePublishRequest,
    SchedulePublishResponse,
    ScholarArticleResponse,
    ScholarEngineStatusResponse,
)
from apps.api.services.publisher_clients import HashnodePublisherClient, MediumPublisherClient
from apps.api.services.scholar_publishing_engine import (
    EPISODES_METADATA,
    ScholarPublishingEngine,
)

router = APIRouter(
    prefix="/api/v1/scholar",
    tags=["Scholar Blog & Publishing Engine"],
    dependencies=[Depends(require_authenticated)],
)


def _get_engine() -> ScholarPublishingEngine:
    settings = get_settings()
    engine = ScholarPublishingEngine.get_instance()
    # Update default credentials from settings
    if settings.MEDIUM_API_KEY:
        engine.medium_client.token = settings.MEDIUM_API_KEY
    if settings.MEDIUM_USER_ID:
        engine.medium_client.user_id = settings.MEDIUM_USER_ID
    if settings.MEDIUM_PUBLICATION_ID:
        engine.medium_client.publication_id = settings.MEDIUM_PUBLICATION_ID
    if settings.HASHNODE_API_KEY:
        engine.hashnode_client.token = settings.HASHNODE_API_KEY
    if settings.HASHNODE_PUBLICATION_ID:
        engine.hashnode_client.publication_id = settings.HASHNODE_PUBLICATION_ID
    return engine


def _serialize_article(art) -> ScholarArticleResponse:
    return ScholarArticleResponse(
        article_id=art.article_id,
        episode_number=art.episode_number,
        slug=art.slug,
        title=art.title,
        subtitle=art.subtitle,
        canonical_url=art.canonical_url,
        estimated_read_time_minutes=art.estimated_read_time_minutes,
        shastra_citations=[
            {
                "treatise": r.treatise,
                "chapter": r.chapter,
                "verse_range": r.verse_range,
                "devanagari_shloka": r.devanagari_shloka,
                "iast_transliteration": r.iast_transliteration,
                "english_translation": r.english_translation,
                "astrological_axiom": r.astrological_axiom,
            }
            for r in art.shastra_citations
        ],
        empirical_metrics={
            "total_cohort_size": art.empirical_metrics.total_cohort_size,
            "rodden_rating_breakdown": art.empirical_metrics.rodden_rating_breakdown,
            "temporal_span": art.empirical_metrics.temporal_span,
            "ground_truth_events_tested": art.empirical_metrics.ground_truth_events_tested,
            "control_slices_evaluated": art.empirical_metrics.control_slices_evaluated,
            "roc_auc": art.empirical_metrics.roc_auc,
            "pr_auc": art.empirical_metrics.pr_auc,
            "brier_score": art.empirical_metrics.brier_score,
            "expected_calibration_error": art.empirical_metrics.expected_calibration_error,
            "wilson_ci_95_lower": art.empirical_metrics.wilson_ci_95_lower,
            "wilson_ci_95_upper": art.empirical_metrics.wilson_ci_95_upper,
            "permutation_test_p_value": art.empirical_metrics.permutation_test_p_value,
            "odds_ratio": art.empirical_metrics.odds_ratio,
            "cohens_d_effect_size": art.empirical_metrics.cohens_d_effect_size,
            "false_alarm_reduction_pct": art.empirical_metrics.false_alarm_reduction_pct,
        },
        case_studies=[
            {
                "native_name": c.native_name,
                "domain": c.domain,
                "landmark_event": c.landmark_event,
                "event_date": c.event_date,
                "active_dasha": c.active_dasha,
                "active_transits": c.active_transits,
                "bhrigu_bindu_status": c.bhrigu_bindu_status,
                "sarvatobhadra_status": c.sarvatobhadra_status,
                "sudarshana_house": c.sudarshana_house,
                "empirical_alignment_score": c.empirical_alignment_score,
                "verdict": c.verdict,
            }
            for c in art.case_studies
        ],
        key_takeaways=art.key_takeaways,
        engineering_insights=art.engineering_insights,
        markdown_content=art.markdown_content,
        html_content=art.html_content,
        tags=art.tags,
        sha256_seal=art.sha256_seal,
        status=art.status.value,
        publication_records=[
            {
                "platform": rec.platform.value,
                "post_id": rec.post_id,
                "url": rec.url,
                "published_at": rec.published_at,
                "publish_mode": rec.publish_mode.value,
                "status": rec.status,
                "response_payload": rec.response_payload,
                "error_message": rec.error_message,
            }
            for rec in art.publication_records
        ],
        created_at=art.created_at,
        updated_at=art.updated_at,
    )


@router.post("/generate", response_model=ScholarArticleResponse)
def generate_article(request: GenerateArticleRequest):
    """Generate a deep research article for 'The Empirical Jyotish Chronicles'."""
    engine = _get_engine()
    article = engine.generate_chronicle_article(
        episode_number=request.episode_number,
        custom_topic=request.custom_topic,
        sample_size=request.sample_size,
        custom_shastra_focus=request.custom_shastra_focus,
    )
    return _serialize_article(article)


@router.get("/articles", response_model=List[ScholarArticleResponse])
def list_articles():
    """List all generated articles."""
    engine = _get_engine()
    articles = engine.list_articles()
    # If no articles generated yet, generate Episode 1 as initial seed
    if not articles:
        ep1 = engine.generate_chronicle_article(episode_number=1)
        articles = [ep1]
    return [_serialize_article(a) for a in articles]


@router.get("/articles/{article_id}", response_model=ScholarArticleResponse)
def get_article(article_id: str):
    """Retrieve specific article by ID."""
    engine = _get_engine()
    art = engine.get_article(article_id)
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholar article '{article_id}' not found.",
        )
    return _serialize_article(art)


@router.post("/publish", response_model=PublishArticleResponse)
async def publish_article(request: PublishArticleRequest):
    """Publish an article to Medium and/or Hashnode."""
    engine = _get_engine()
    try:
        mode_enum = PublishMode(request.publish_mode.lower())
    except ValueError:
        mode_enum = PublishMode.DRAFT

    try:
        records = await engine.publish_article(
            article_id=request.article_id,
            platforms=request.platforms,
            mode=mode_enum,
            medium_token_override=request.medium_token_override,
            medium_user_id_override=request.medium_user_id_override,
            medium_publication_id_override=request.medium_publication_id_override,
            hashnode_token_override=request.hashnode_token_override,
            hashnode_publication_id_override=request.hashnode_publication_id_override,
            dry_run=request.dry_run,
        )

        overall_status = "PUBLISHED" if any(r.status in ("PUBLISHED", "SUCCESS_DRY_RUN") for r in records) else "FAILED"
        serialized_records = [
            {
                "platform": r.platform.value,
                "post_id": r.post_id,
                "url": r.url,
                "published_at": r.published_at,
                "publish_mode": r.publish_mode.value,
                "status": r.status,
                "response_payload": r.response_payload,
                "error_message": r.error_message,
            }
            for r in records
        ]

        return PublishArticleResponse(
            article_id=request.article_id,
            overall_status=overall_status,
            records=serialized_records,
            summary_message=f"Successfully dispatched to {len(records)} platform(s)."
            if overall_status == "PUBLISHED"
            else "Publication encountered errors on one or more platforms.",
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholar article '{request.article_id}' not found.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publication failed: {str(e)}",
        )


@router.get("/status", response_model=ScholarEngineStatusResponse)
def get_engine_status():
    """Inspect publisher credentials, configured integrations, and chronicle catalogue."""
    settings = get_settings()
    engine = _get_engine()
    schedule = engine.get_schedule()
    articles = engine.list_articles()

    available_episodes = [
        {
            "episode_number": ep.episode_number,
            "title": ep.title,
            "subtitle": ep.subtitle,
            "target_theme": ep.target_theme,
            "primary_shastra": ep.primary_shastra,
            "primary_empirical_focus": ep.primary_empirical_focus,
            "tags": list(ep.tags),
        }
        for ep in EPISODES_METADATA.values()
    ]

    return ScholarEngineStatusResponse(
        medium_configured=bool(settings.MEDIUM_API_KEY or engine.medium_client.token),
        hashnode_configured=bool(settings.HASHNODE_API_KEY or engine.hashnode_client.token),
        medium_user_id_set=bool(settings.MEDIUM_USER_ID or engine.medium_client.user_id),
        hashnode_publication_id_set=bool(
            settings.HASHNODE_PUBLICATION_ID or engine.hashnode_client.publication_id
        ),
        autonomous_scheduler_active=schedule.enabled,
        next_scheduled_run=schedule.next_scheduled_run,
        total_articles=len(articles),
        published_articles=sum(
            1 for a in articles if any(r.status == "PUBLISHED" for r in a.publication_records)
        ),
        available_episodes=available_episodes,
    )


@router.post("/schedule", response_model=SchedulePublishResponse)
def configure_schedule(request: SchedulePublishRequest):
    """Configure autonomous background publishing cadence."""
    engine = _get_engine()
    sched = engine.configure_schedule(
        enabled=request.enabled,
        cadence_hours=request.cadence_hours,
        auto_medium=request.auto_publish_medium,
        auto_hashnode=request.auto_publish_hashnode,
        draft_first=request.publish_as_draft_first,
        queue=request.queued_episodes,
    )
    return SchedulePublishResponse(
        enabled=sched.enabled,
        cadence_hours=sched.cadence_hours,
        auto_publish_medium=sched.auto_publish_medium,
        auto_publish_hashnode=sched.auto_publish_hashnode,
        publish_as_draft_first=sched.publish_as_draft_first,
        next_scheduled_run=sched.next_scheduled_run,
        queue=sched.queue,
        message=f"Autonomous publishing schedule {'activated' if sched.enabled else 'paused'} with {sched.cadence_hours}h cadence.",
    )


@router.post("/export", response_model=ExportArticleResponse)
def export_article(request: ExportArticleRequest):
    """Export the article in Markdown, HTML, or JSON format."""
    engine = _get_engine()
    art = engine.get_article(request.article_id)
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholar article '{request.article_id}' not found.",
        )

    fmt = request.format.lower()
    if fmt == "html":
        content = art.html_content
        filename = f"{art.slug}.html"
    elif fmt == "json":
        content = json.dumps(_serialize_article(art).model_dump(), default=str, indent=2)
        filename = f"{art.slug}.json"
    else:
        content = art.markdown_content
        filename = f"{art.slug}.md"

    return ExportArticleResponse(
        article_id=art.article_id,
        format=fmt,
        filename=filename,
        content=content,
    )

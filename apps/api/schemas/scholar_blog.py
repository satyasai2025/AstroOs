"""
AstroOS — Scholar Blog & Publishing Pydantic Schemas
====================================================
Request and response schemas for article generation, publishing, and scheduling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ShastraReferenceSchema(BaseModel):
    treatise: str
    chapter: str
    verse_range: str
    devanagari_shloka: str
    iast_transliteration: str
    english_translation: str
    astrological_axiom: str


class EmpiricalDatasetMetricsSchema(BaseModel):
    total_cohort_size: int
    rodden_rating_breakdown: str
    temporal_span: str
    ground_truth_events_tested: int
    control_slices_evaluated: int
    roc_auc: float
    pr_auc: float
    brier_score: float
    expected_calibration_error: float
    wilson_ci_95_lower: float
    wilson_ci_95_upper: float
    permutation_test_p_value: float
    odds_ratio: float
    cohens_d_effect_size: float
    false_alarm_reduction_pct: float


class GroundTruthCaseStudySchema(BaseModel):
    native_name: str
    domain: str
    landmark_event: str
    event_date: str
    active_dasha: str
    active_transits: str
    bhrigu_bindu_status: str
    sarvatobhadra_status: str
    sudarshana_house: str
    empirical_alignment_score: float
    verdict: str


class PlatformPublishRecordSchema(BaseModel):
    platform: str
    post_id: str
    url: str
    published_at: datetime
    publish_mode: str
    status: str
    response_payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class ScholarArticleResponse(BaseModel):
    article_id: str
    episode_number: int
    slug: str
    title: str
    subtitle: str
    canonical_url: str
    estimated_read_time_minutes: int
    shastra_citations: List[ShastraReferenceSchema]
    empirical_metrics: EmpiricalDatasetMetricsSchema
    case_studies: List[GroundTruthCaseStudySchema]
    key_takeaways: List[str]
    engineering_insights: List[str]
    markdown_content: str
    html_content: str
    tags: List[str]
    sha256_seal: str
    status: str
    publication_records: List[PlatformPublishRecordSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class GenerateArticleRequest(BaseModel):
    episode_number: Optional[int] = Field(
        None,
        description="Episode number (1-8) in 'Learning with Antigravity: The Empirical Jyotish Chronicles'",
    )
    custom_topic: Optional[str] = Field(
        None,
        description="Custom research topic (if not using pre-configured episode)",
    )
    sample_size: int = Field(
        default=66000,
        ge=1000,
        le=200000,
        description="Empirical chart sample size (default 66k)",
    )
    custom_shastra_focus: Optional[str] = Field(
        None,
        description="Specific shastra treatise to emphasize (e.g. BPHS, Phaladeepika, Jaimini)",
    )


class PublishArticleRequest(BaseModel):
    article_id: str
    platforms: List[str] = Field(
        default=["MEDIUM", "HASHNODE"],
        description="List of target platforms ('MEDIUM', 'HASHNODE')",
    )
    publish_mode: str = Field(
        default="draft",
        description="Publish mode ('draft', 'public', 'unlisted')",
    )
    medium_token_override: Optional[str] = None
    medium_user_id_override: Optional[str] = None
    medium_publication_id_override: Optional[str] = None
    hashnode_token_override: Optional[str] = None
    hashnode_publication_id_override: Optional[str] = None
    dry_run: bool = Field(
        default=False,
        description="Execute in dry-run mode (returns full simulated payload without hitting remote API)",
    )


class PublishArticleResponse(BaseModel):
    article_id: str
    overall_status: str
    records: List[PlatformPublishRecordSchema]
    summary_message: str


class SchedulePublishRequest(BaseModel):
    enabled: bool
    cadence_hours: int = Field(default=168, ge=1, le=720)
    auto_publish_medium: bool = True
    auto_publish_hashnode: bool = True
    publish_as_draft_first: bool = True
    queued_episodes: Optional[List[int]] = None


class SchedulePublishResponse(BaseModel):
    enabled: bool
    cadence_hours: int
    auto_publish_medium: bool
    auto_publish_hashnode: bool
    publish_as_draft_first: bool
    next_scheduled_run: Optional[datetime]
    queue: List[int]
    message: str


class ScholarEngineStatusResponse(BaseModel):
    medium_configured: bool
    hashnode_configured: bool
    medium_user_id_set: bool
    hashnode_publication_id_set: bool
    autonomous_scheduler_active: bool
    next_scheduled_run: Optional[datetime]
    total_articles: int
    published_articles: int
    available_episodes: List[Dict[str, Any]]


class ExportArticleRequest(BaseModel):
    article_id: str
    format: str = Field(default="markdown", description="'markdown', 'html', or 'json'")


class ExportArticleResponse(BaseModel):
    article_id: str
    format: str
    filename: str
    content: str

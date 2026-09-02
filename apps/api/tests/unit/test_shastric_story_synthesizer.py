import pytest
from apps.api.services.shastric_story_synthesizer import ShastricStorySynthesizer, ExecutiveLifeStory


def test_story_synthesizer_structure():
    windows = [
        {
            "start_date": "2024-01-01",
            "end_date": "2026-01-01",
            "dasha_period": "Jupiter / Saturn",
            "decision_tier": "PRATYAKSHA_PHALA",
            "confluence_score": 0.95,
            "actionable_verdict": "Peak Career Elevation",
        },
        {
            "start_date": "2026-01-01",
            "end_date": "2028-01-01",
            "dasha_period": "Jupiter / Mercury",
            "decision_tier": "SUSHUPTA_BEEJA",
            "confluence_score": 0.75,
            "actionable_verdict": "Consolidation Phase",
        },
    ]

    story = ShastricStorySynthesizer.synthesize_story(
        native_name="Alexander",
        domain="career",
        timeline_windows=windows,
        lagna_rashi="Aries",
        moon_rashi="Cancer",
    )

    assert isinstance(story, ExecutiveLifeStory)
    assert story.native_name == "Alexander"
    assert "Alexander" in story.headline
    assert "Aries" in story.act_1_blueprint
    assert len(story.dos) >= 3
    assert len(story.donts) >= 3
    assert len(story.key_turning_points) >= 1
    assert "66,732" in story.empirical_validation_summary

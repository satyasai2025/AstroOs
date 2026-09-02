import pytest
from pathlib import Path

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.multi_domain_cohort_validator import MultiDomainCohortValidator

REPO_ROOT = Path(__file__).resolve().parents[4]
KUNDALEE_CSV = REPO_ROOT / "data" / "kundalee" / "kundalee_clean.csv"


@pytest.fixture
def ephem_wrapper():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture
def validator(ephem_wrapper):
    return MultiDomainCohortValidator(ephem_wrapper)


@pytest.mark.skipif(not KUNDALEE_CSV.is_file(), reason="Kundalee clean dataset not present")
def test_validator_loads_authentic_subjects(validator):
    subjects = validator.load_authentic_cohort_from_csv(KUNDALEE_CSV, max_persons=30)
    assert len(subjects) >= 5
    for s in subjects:
        assert s.person_id.startswith("PER_")
        assert len(s.events) >= 1
        assert s.confidence_tier == "HIGH"


@pytest.mark.skipif(not KUNDALEE_CSV.is_file(), reason="Kundalee clean dataset not present")
def test_validator_evaluates_career_domain_walk_forward(validator):
    subjects = validator.load_authentic_cohort_from_csv(KUNDALEE_CSV, max_persons=25)
    all_slices = []
    for s in subjects:
        slices = validator.generate_domain_slices_for_subject(s, domain="CAREER")
        all_slices.extend(slices)

    assert len(all_slices) > 0
    report = validator.run_walk_forward_domain_validation(all_slices, n_folds=3)

    assert report.domain == "CAREER"
    assert report.total_slices == len(all_slices)
    assert 0.0 <= report.roc_auc <= 1.0
    assert 0.0 <= report.brier_score <= 1.0
    assert report.verdict in ("STRONG_SIGNAL", "MODERATE_SIGNAL", "EXPLORATORY", "NO_SIGNAL")


@pytest.mark.skipif(not KUNDALEE_CSV.is_file(), reason="Kundalee clean dataset not present")
def test_validator_evaluates_marriage_domain_walk_forward(validator):
    subjects = validator.load_authentic_cohort_from_csv(KUNDALEE_CSV, max_persons=25)
    all_slices = []
    for s in subjects:
        slices = validator.generate_domain_slices_for_subject(s, domain="MARRIAGE")
        all_slices.extend(slices)

    assert len(all_slices) > 0
    report = validator.run_walk_forward_domain_validation(all_slices, n_folds=3)

    assert report.domain == "MARRIAGE"
    assert report.total_slices == len(all_slices)
    assert 0.0 <= report.roc_auc <= 1.0
    assert report.verdict in ("STRONG_SIGNAL", "MODERATE_SIGNAL", "EXPLORATORY", "NO_SIGNAL")

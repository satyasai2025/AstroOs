---
name: astrosos-research-support
description: "Research support specifications connecting datasets to engines — Verification, Statistics, Research, AI, Benchmark Suite, and Future ML"
metadata: 
  node_type: memory
  type: reference
  domain: datasets
  status: draft
  phase: 7
  originSessionId: e78a75e5-611c-4c3f-99a8-68817dfe9484
---

# AstroOS Research Support — Phase 7

> **Status:** DRAFT — pending approval
> **Owner:** Chief Dataset & Research Curator
> **Version:** 1.0
> **Date:** 2026-07-15

---

## Table of Contents

1. [Overview: Engine ↔ Dataset Mapping](#1-overview-engine--dataset-mapping)
2. [Verification Engine Support](#2-verification-engine-support)
3. [Statistics Engine Support](#3-statistics-engine-support)
4. [Research Engine Support](#4-research-engine-support)
5. [AI Engine Support](#5-ai-engine-support)
6. [Benchmark Suite Support](#6-benchmark-suite-support)
7. [Future Machine Learning Support](#7-future-machine-learning-support)
8. [Cohort Specification Templates](#8-cohort-specification-templates)
9. [Study Design Templates](#9-study-design-templates)
10. [Research Roadmap](#10-research-roadmap)

---

## 1. Overview: Engine ↔ Dataset Mapping

### 1.1 Engine Dependency Map

```
                       ┌─────────────────────────────────────────────┐
                       │              DATASETS                       │
                       │  RF  RS  BM  VL  QT  AI  SY  PB  LC  UC    │
                       └┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┘              │
                        │  │  │  │  │  │  │  │  │  │               │
    ┌───────────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼───           │
    │  VERIFICATION     │  │  │  │  │  │  │  │  │  │               │
    │  Engine           │  │  │  │  │  │  │  │  │  │               │
    │  - Alignment      │  │ ██│ ██│   │ ██│  │ ██│ ██│ ██│ ██    │
    │  - Rule testing   │  │ ██│ ██│ ██│ ██│  │ ██│ ██│ ██│ ██    │
    │  - Timing         │  │ ██│ ██│   │ ██│  │ ██│ ██│ ██│ ██    │
    │  - Cross-validate │  │ ██│   │ ██│ ██│  │ ██│ ██│   │      │
    ├───────────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼───           │
    │  STATISTICS       │  │  │  │  │  │  │  │  │  │               │
    │  Engine           │  │  │  │  │  │  │  │  │  │               │
    │  - Distributions  │  │ ██│   │  │  │  │ ██│ ██│ ██│ ██     │
    │  - Contingency    │  │ ██│   │  │  │  │ ██│ ██│ ██│ ██     │
    │  - Significance   │  │ ██│   │  │  │  │ ██│ ██│ ██│ ██     │
    │  - Base rates     │  │   │   │  │  │  │ ██│   │   │       │
    ├───────────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼───           │
    │  RESEARCH         │  │  │  │  │  │  │  │  │  │               │
    │  Engine           │  │  │  │  │  │  │  │  │  │               │
    │  - Cohorts        │  │ ██│ ██│  │  │  │ ██│ ██│ ██│ ██     │
    │  - Snapshots      │ ██│ ██│  │ ██│  │  │ ██│ ██│ ██│ ██    │
    │  - Comparisons    │  │ ██│   │ ██│  │  │   │ ██│ ██│ ██    │
    │  - Experiments    │  │ ██│ ██│ ██│  │  │ ██│ ██│ ██│   │   │
    ├───────────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼───           │
    │  AI ENGINE        │  │  │  │  │  │  │  │  │  │               │
    │  - Interpret      │ ██│ ██│  │  │  │ ██│   │ ██│ ██│      │
    │  - Report         │ ██│ ██│  │  │  │ ██│   │ ██│ ██│      │
    │  - Evaluate       │ ██│  │  │  │  │ ██│   │ ██│   │       │
    │  - Train          │ ██│ ██│  │  │  │   │ ██│ ██│ ██│      │
    ├───────────────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼───           │
    │  BENCHMARK SUITE  │  │  │  │  │  │  │  │  │  │               │
    │  - Accuracy       │  │   │ ██│ ██│ ██│  │  │   │   │       │
    │  - Performance    │  │   │ ██│  │ ██│  │  │   │   │       │
    │  - Regression     │ ██│ ██│ ██│ ██│ ██│  │  │ ██│ ██│      │
    │  - Edge cases     │  │   │ ██│  │ ██│  │  │   │   │       │
    └───────────────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴───           │
```

### 1.2 Priority Dataset Requirements by Engine

| Engine | Highest Priority Datasets | Minimum Viable Data |
|--------|--------------------------|---------------------|
| **Verification Engine** | RS-EVENT, RS-MARRIAGE, RS-CAREER, RS-HEALTH, RS-WEALTH, RS-SPIRITUAL | ≥1,000 verified events linked to charts |
| **Statistics Engine** | SY-RANDOM (≥100K), SY-NULL, RS-COHORT, RS-FLAT | ≥10K random records for base rates; any cohort for analysis |
| **Research Engine** | RS-COHORT, RS-FLAT, RF-* (all) | Any 1 cohort with ≥100 members; full reference data |
| **AI Engine** | AI-INTERP, AI-HALLUC, AI-FACT, AI-REPORT, AI-RULE | ≥50 interpretation benchmarks; ≥100 hallucination tests; ≥200 fact questions |
| **Benchmark Suite** | BM-CALC, BM-ASPECT, BM-DASHA, BM-TRANSIT, BM-BALA, BM-ASTAK, BM-DIV, BM-PERF | ≥20 cases per benchmark type |
| **Future ML** | RS-FLAT (≥50K), PB-* (≥50K), SY-RANDOM (≥1M) | ≥50K computed chart records with consistent schema |

---

## 2. Verification Engine Support

### 2.1 Engine Requirements

The Verification Engine ([verification_engine.py](apps/api/services/verification_engine.py)) maps rule evaluations to recorded life events, producing alignment classifications:

```
RuleResult → recorded LifeEvent → Alignment (CONFIRMED / CATEGORY_MISMATCH / UNTESTED)
```

**Known event categories** (from engine source):
- `marriage`, `career`, `education`, `health`, `progeny`, `wealth`, `longevity`

### 2.2 Dataset Needs

| Need | Dataset | Description |
|------|---------|-------------|
| Event-chart linkage | RS-EVENT | Charts with ≥1 verified life event across any category |
| Multi-event charts | RS-EVENT subset | Charts with ≥3+ events across different categories (for comprehensive verification) |
| Event timing precision | RS-MARRIAGE, RS-CAREER | Events with exact-date precision for timing verification |
| Negative test cases | SY-CONTROLLED | Random charts with no known events (to verify no false positives) |
| Cross-verified events | PB-EVENTS | Events independently verified from ≥2 sources |

### 2.3 Verification Study Template

```yaml
# Verification Study Template
study_id: ASTRO-VERIFY-{TOPIC}-v1.0.0
topic: "Marriage Timing - 7th House Lordship"
hypothesis: "Jupiter's transit over the 7th house lord within 12 months of marriage"
datasets_required:
  - ASTRO-RS-MARRIAGE-v1.0.0
  - ASTRO-RS-FLAT-v1.0.0 (for computed positions)
methodology:
  engine: VerificationEngine
  alignment_classification: Required
  sample_size: 500
  control_group: "SY-NULL (shuffled marriage dates)"
expected_output:
  - VerificationFindings.per_rule_alignment
  - VerificationFindings.aggregate_accuracy
  - VerificationFindings.confirmed_rate
  - VerificationFindings.category_mismatch_rate
confidence_threshold: "Tier A (≥0.90) datasets only"
```

### 2.4 Verification Dataset Specifications

| Dataset | Min Records | Required Fields | Quality Threshold |
|---------|-------------|-----------------|-------------------|
| RS-EVENT (verified) | 1,000 | chart_id, event_date, event_type, event_category, confidence | Tier A (Research Grade) |
| RS-EVENT (estimated) | 5,000 | chart_id, event_date, event_date_accuracy, event_type, confidence | Tier B (Production) |
| RS-MARRIAGE | 500 | chart_id, marriage_date, marriage_date_accuracy, arranged_love | Tier A |
| RS-CAREER | 500 | chart_id, career_start_date, occupation, industry | Tier A |
| RS-HEALTH | 300 | chart_id, diagnosis_date, condition, severity | Tier A |
| RS-WEALTH | 300 | chart_id, event_date, event_type, wealth_category | Tier B |
| RS-SPIRITUAL | 200 | chart_id, event_date, event_type | Tier B |

### 2.5 Key Research Questions the Verification Engine Can Answer

1. **Rule accuracy**: What % of rule evaluations align with actual events?
2. **Timing precision**: What is the distribution of timing deltas (predicted vs actual)?
3. **Category specificity**: How well do rules predict their intended domain vs false-match other domains?
4. **Dasha accuracy**: What % of significant life events fall within relevant Dasha periods?
5. **Transit correlation**: What transits are statistically associated with event occurrences?
6. **Dignity influence**: Do planetary dignity states correlate with event outcomes (positive vs challenging)?

---

## 3. Statistics Engine Support

### 3.1 Engine Requirements

The Statistics Engine ([statistics_engine.py](apps/api/services/statistics_engine.py)) computes distributions, descriptive statistics, and contingency tables over `AstrologicalSnapshot` collections.

```
SnapshotCollection → Distribution, Crosstab, NumericSummary, AggregateReport
```

### 3.2 Dataset Needs

| Need | Dataset | Description |
|------|---------|-------------|
| Base rate computation | SY-RANDOM (≥100K) | Uniform random births to establish expected distributions of rashis, nakshatras, ascendants |
| Controlled comparisons | SY-CONTROLLED | Purpose-built groups differing in exactly one parameter |
| Observational cohorts | RS-COHORT | Real chart groups for observational studies |
| Null hypothesis testing | SY-NULL | Shuffled/randomized controls for every observational cohort |
| Large-sample analysis | SY-MONTE (≥100K) | Stable distribution estimation |
| Flattened records | RS-FLAT | Pre-computed chart data for rapid analysis |

### 3.3 Statistics Engine Import Schema

The Statistics Engine consumes **flattened chart records** — the `RS-FLAT` dataset type:

```
FLAT_RECORD = {
    # Identity
    "record_id": str,
    "dataset_id": str,

    # Birth params
    "birth_year": int,
    "birth_month": int,     # 1-12
    "birth_dow": int,       # 0=Monday
    "birth_hour": float,    # decimal hour, 0-24

    # Location
    "latitude": float,
    "longitude": float,
    "country_code": str,

    # Lagna (ascendant)
    "lagna_rashi": str,       # enum
    "lagna_nakshatra": str,   # enum
    "lagna_pada": int,        # 1-4
    "lagna_degree": float,    # 0-30

    # Planet rashis (9)
    "sun_rashi": str,
    "moon_rashi": str,
    "mars_rashi": str,
    "mercury_rashi": str,
    "jupiter_rashi": str,
    "venus_rashi": str,
    "saturn_rashi": str,
    "rahu_rashi": str,
    "ketu_rashi": str,

    # Planet houses (9)
    "sun_house": int,
    "moon_house": int,
    "mars_house": int,
    "mercury_house": int,
    "jupiter_house": int,
    "venus_house": int,
    "saturn_house": int,
    "rahu_house": int,
    "ketu_house": int,

    # Planet dignities (9)
    "sun_dignity": str,     # enum
    "moon_dignity": str,
    # ...

    # Planet retrogrades (9)
    "sun_retrograde": bool,
    # ...

    # Moon nakshatra
    "moon_nakshatra": str,
    "moon_nakshatra_lord": str,

    # Nakshatra pada of Moon
    "moon_pada": int,

    # Special
    "has_raja_yoga": bool,
    "has_dhana_yoga": bool,
    "has_sanyasa_yoga": bool,
    "is_leo_ascendant": bool,
    # ... (computed booleans as needed)

    # Metadata
    "confidence_tier": str,
    "record_weight": float,     # For weighted analysis (correct for bias)
}
```

### 3.4 Statistical Test Dataset Requirements

| Test Type | Dataset Requirement | Min Sample |
|-----------|-------------------|------------|
| Chi-squared (rashi distribution) | SY-RANDOM or any large cohort | 100+ |
| T-test (two groups) | SY-CONTROLLED (control + experiment) | 30 per group |
| ANOVA (multiple groups) | RS-COHORT (multiple sub-cohorts) | 20 per group |
| Correlation | RS-FLAT (continuous variables) | 100+ |
| Binomial test | Any category-based hypothesis | 100+ |
| Monte Carlo permutation | SY-NULL paired with any observational cohort | 1,000+ permutations |
| Base rate establishment | SY-MONTE | 100,000+ |
| Regression modeling | RS-FLAT with events | 1,000+ |

### 3.5 Key Research Questions the Statistics Engine Can Answer

1. **Rashi distribution at birth**: Is ascendant distribution uniform (as expected from random birth times)?
2. **Planetary dignity prevalence**: What % of populations have each dignity type per planet?
3. **Yoga prevalence**: What is the population base rate for each yoga type?
4. **Nakshatra distribution**: Are any nakshatras over/under-represented in specific occupations?
5. **Time-of-day distribution**: Is there a relationship between birth hour and profession?
6. **Geographic effects**: Do planetary strengths vary by geographic latitude?
7. **Event timing concentration**: Do life events cluster around specific Dasha periods beyond chance?
8. **Gender and planetary placements**: Are there statistically significant differences in planetary distributions by gender?
9. **Twin studies**: How much chart similarity exists between identical vs fraternal twins?

---

## 4. Research Engine Support

### 4.1 Engine Requirements

The Research Engine ([research_engine.py](apps/api/services/research_engine.py)) manages research projects, experiments, and astrological snapshots.

```
CreateProject → ResearchProject
CreateExperiment → ResearchExperiment (with hypothesis, methodology)
CaptureSnapshot → AstrologicalSnapshot (time-capsule of chart state)
QuerySnapshots → filtered collection
CompareSnapshots → SnapshotComparison
```

### 4.2 Dataset Needs

| Need | Dataset | Description |
|------|---------|-------------|
| Snapshot-ready charts | RS-COHORT | Charts with complete computed data for snapshot capture |
| Reference snapshots | VL-CHART | Gold-standard charts with pre-computed verifying references |
| Historical baselines | SY-RANDOM | Random charts for null-hypothesis comparisons |
| Study populations | PB-* (WIKI, WIKIDATA) | Large population of real charts for observational studies |
| Controlled sets | SY-CONTROLLED | Purpose-built for specific hypothesis tests |

### 4.3 Research Experiment Lifecycle

```
                          ┌──────────────────────────────────┐
                          │  1. DEFINE STUDY                 │
                          │  - Hypothesis                    │
                          │  - Methodology                   │
                          │  - Dataset requirements           │
                          │  - Statistical method             │
                          └──────────────┬───────────────────┘
                                         │
                          ┌──────────────▼───────────────────┐
                          │  2. SELECT COHORT                │
                          │  - Inclusion criteria            │
                          │  - Exclusion criteria            │
                          │  - Cohort size estimation        │
                          │  - Dataset version pinning       │
                          └──────────────┬───────────────────┘
                                         │
                          ┌──────────────▼───────────────────┐
                          │  3. CAPTURE SNAPSHOTS            │
                          │  - ResearchEngine.capture()      │
                          │  - One snapshot per chart        │
                          │  - Engine version recorded       │
                          │  - Parquet export                │
                          └──────────────┬───────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
  ┌───────────▼──────────┐  ┌────────────▼───────────┐  ┌─────────▼──────────┐
  │  4a. STATISTICAL     │  │  4b. COMPARISON        │  │  4c. VERIFICATION  │
  │  ANALYSIS            │  │                        │  │                    │
  │  StatisticsEngine    │  │  SnapshotAccessor       │  │  VerificationEngine│
  │  - Distributions     │  │  - Compare two cohorts │  │  - Rule alignment  │
  │  - Contingency tables│  │  - Diff detection      │  │  - Event matching  │
  │  - Significance tests│  │  - Similarity scoring  │  │  - Timing accuracy  │
  └───────────┬──────────┘  └────────────┬───────────┘  └─────────┬──────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                          ┌──────────────▼───────────────────┐
                          │  5. RECORD FINDING               │
                          │  - TESTED status                 │
                          │  - Effect size & p-value         │
                          │  - Result summary                │
                          └──────────────┬───────────────────┘
                                         │
                          ┌──────────────▼───────────────────┐
                          │  6. PUBLISH / REFUTE             │
                          │  - PUBLISHED status (review +)   │
                          │  - REFUTED status (review -)     │
                          │  - Finding documented            │
                          └──────────────────────────────────┘
```

### 4.4 Research Project Specification Template

```yaml
# Research Project Specification
project_id: ASTRO-RESEARCH-{TOPIC}-v1.0.0
title: "Dasha Periods and Career Milestones"
hypothesis: "Major career events occur disproportionately during the Dasha periods of the 10th lord or its dispositor"
datasets:
  primary:
    - ASTRO-RS-CAREER-v1.0.0
    - ASTRO-RS-FLAT-v1.0.0
  control:
    - ASTRO-SY-NULL-career-shuffle-v1.0.0
cohort_definitions:
  experimental:
    name: "Career events in known charts"
    inclusion: "has_known_career_event AND has_computed_dashas AND confidence_tier IN (verified, estimated_close)"
    expected_size: 750
  control:
    name: "Shuffled career dates"
    inclusion: "same_charts AS experimental BUT event_dates_shuffled_across_charts"
    expected_size: 750
snapshot_field_selection:
  - "planets.{*}.rashi"
  - "planets.{*}.house_number"
  - "planets.{*}.dignity"
  - "dashas.{*}.lord"
  - "dashas.{*}.start_date"
  - "dashas.{*}.end_date"
  - "houses.10.lord"
  - "houses.10.rashi"
statistical_plan:
  primary_test: "chi_squared"
  parameters:
    contingency_table: "active_dasha_lord × career_event_within_period"
    expected_distribution: "uniform (each dasha lord equally likely)"
    significance_threshold: 0.01
    multiple_testing_correction: "bonferroni"
  power_analysis:
    expected_effect_size: "medium (Cramer's V = 0.3)"
    required_sample: 150
    actual_sample: 750
  secondary_tests:
    - "binomial_test (10th lord dasha period specifically)"
    - "logistic_regression (career_event ~ dasha_lord + 10th_house_lord)"
findings_lifecycle:
  initial_status: HYPOTHESIS
  criteria_for_tested: "p_value < 0.01 AND effect_size > 0.2"
  criteria_for_published: "peer_review AND replication_with_independent_dataset"
```

---

## 5. AI Engine Support

### 5.1 Engine Requirements

The AI Engine provides LLM-powered interpretation, report generation, and analysis. Dataset support focuses on **evaluation** and **training**.

```
AIEngine.interpret(chart_data) → Natural language interpretation
AIEngine.generate_report(chart_data, report_type) → Structured report
AIEngine.evaluate_rule(chart_data, rule) → Rule evaluation with reasoning
```

### 5.2 Dataset Needs

| Need | Dataset | Description |
|------|---------|-------------|
| Interpretation reference | AI-INTERP | Chart + human-written reference interpretation pairs |
| Hallucination detection | AI-HALLUC | Test cases designed to trigger known hallucination patterns |
| Factual knowledge | AI-FACT | Astrology QA pairs from classical texts |
| Report quality | AI-REPORT | Chart + human-written full report pairs |
| Rule evaluation | AI-RULE | Chart + rule + expected evaluation triplets |
| Fine-tuning data | PB-*, RS-FLAT | Large-scale computed chart data for model adaptation |

### 5.3 AI Evaluation Framework Schema

```yaml
# AI Evaluation Framework
eval_framework_id: ASTRO-AI-EVAL-v1.0.0
dimensions:
  - name: factual_accuracy
    description: "Every factual claim in AI output matches classical Jyotish sources"
    test_datasets:
      - ASTRO-AI-FACT-v1.0.0
      - ASTRO-AI-INTERP-v1.0.0
    evaluation_method: "Extract all factual claims from AI output; compare against ground truth; compute precision and recall"
    scoring:
      - "factual_precision = correct_claims / total_claims"
      - "factual_recall = correct_claims / expected_claims"
    minimum_threshold:
      tier_A: 0.95
      tier_B: 0.85

  - name: hallucination_rate
    description: "Rate of fabricated or incorrect astrological assertions"
    test_datasets:
      - ASTRO-AI-HALLUC-v1.0.0
    evaluation_method: "Count assertions in AI output that appear in known_hallucination_patterns list"
    scoring:
      - "hallucination_rate = hallucinated_claims / total_claims"
    maximum_threshold:
      tier_A: 0.01
      tier_B: 0.05

  - name: completeness
    description: "Coverage of expected chart interpretation elements"
    test_datasets:
      - ASTRO-AI-INTERP-v1.0.0
    evaluation_method: "Check presence of expected sections (lagna, planet positions, yogas, dashas, recommendations)"
    scoring:
      - "completeness = sections_present / expected_sections"
    minimum_threshold:
      tier_A: 0.90
      tier_B: 0.75

  - name: classical_rigor
    description: "Interpretation follows classical principles (BPHS) vs modern/western blending"
    test_datasets:
      - ASTRO-AI-INTERP-v1.0.0 (Vedic subset)
      - ASTRO-AI-RULE-v1.0.0
    evaluation_method: "Expert review of AI output for doctrinal correctness"
    scoring:
      - "rigor_score = expert_adherence_rating (1-5)"
    minimum_threshold:
      tier_A: 4.0
      tier_B: 3.0

  - name: structure_compliance
    description: "Report follows prescribed structure and formatting"
    test_datasets:
      - ASTRO-AI-REPORT-v1.0.0
    evaluation_method: "Automated structure check against report template"
    scoring:
      - "structure_score = sections_matched / total_sections"
    minimum_threshold:
      tier_A: 1.0
      tier_B: 0.90
```

### 5.4 AI Training Data Specifications

For future ML model training, the following dataset formats are needed:

**Training pairs for interpretation:**
```json
{
  "prompt": "Provide a Vedic astrological interpretation for this chart: {chart_data_json}",
  "reference_interpretation": "The native has {lagna_rashi} lagna with {lagna_lord} in house {n}. ...",
  "tradition": "BPHS",
  "difficulty": "intermediate",
  "tags": ["lagna", "dasha", "career"]
}
```

**Training pairs for rule evaluation:**
```json
{
  "prompt": "Evaluate this astrological rule for the given chart: Rule: {rule_text}, Chart: {chart_data_json}",
  "reference_evaluation": "Rule applies. {lord} is in {house} with {dignity}...",
  "rule_source": "BPHS Chapter 25, Verse 12",
  "tradition": "Parashari"
}
```

**Training pairs for hallucination prevention:**
```json
{
  "prompt": "Interpret this Vedic chart: {chart_data_json}",
  "hallucination_traps": [
    "lagna_lord_in_6th_house_always_bad",
    "rahu_in_1st_house_always_gives_wealth"
  ],
  "reference_response": "Native has {correct_lagna} lagna...",
  "notes": "Avoid overgeneralizing; lagna lord in 6th can be beneficial depending on other factors"
}
```

### 5.5 Key Research Questions the AI Engine Can Answer

1. **Interpretation quality**: How do AI interpretations compare to human astrologers in accuracy?
2. **Hallucination patterns**: What types of astrological claims are AIs most likely to fabricate?
3. **Tradition adherence**: Can the AI correctly follow specific classical traditions (Parashari, Jaimini, KP)?
4. **Consistency**: Does the AI give consistent interpretations for the same chart across multiple calls?
5. **Bias detection**: Does the AI show demographic or cultural bias in interpretations?

---

## 6. Benchmark Suite Support

### 6.1 Engine Requirements

The Benchmark Suite runs standardized correctness and performance tests across all calculation engines.

```
BenchmarkRunner.run(BM-CALC) → pass/fail + deviation
BenchmarkRunner.run(BM-PERF) → latency_p50 + latency_p99 + throughput
BenchmarkRunner.run(BM-REGRESSION) → hash comparison
```

### 6.2 Benchmark Dataset Specifications

| Benchmark | # Cases | Coverage | Critical Success Criteria |
|-----------|---------|----------|--------------------------|
| BM-CALC | 100+ | All 9 planets, all 12 rashis, boundary degrees | 100% within tolerance |
| BM-ASPECT | 50+ | All aspect types, special graha, boundary orbs | 100% aspect type correct |
| BM-DASHA | 30+ | Vimshottari + Ashtottari, balance dasha, exact dates | 100% lord/date match |
| BM-TRANSIT | 50+ | All planets, retrograde, station, rashi transitions | 100% position within 0.001° |
| BM-BALA | 20+ | All 6 bala components, all planets, edge-case scores | 100% within 0.1 shashtiamsa |
| BM-ASTAK | 20+ | Bhinna + Samudaya, all houses, boundary bindus | 100% bindu count match |
| BM-DIV | 30+ | All 16 division types, boundary degrees | 100% placement match |
| BM-PERF | 5+ | Batch sizes of 1, 100, 1K, 10K, 100K | < published p99 latency |

### 6.3 Benchmark Data Format

```json
{
  "benchmark_id": "ASTRO-BM-CALC-sun-position-001",
  "suite": "ASTRO-BM-CALC-v1.0.0",
  "engine": "EphemerisEngine",
  "description": "Tropical longitude of Sun on 2000-01-01 12:00:00 UTC",
  "input": {
    "planet": "sun",
    "datetime_utc": "2000-01-01T12:00:00Z",
    "ephemeris": "swiss_ephemeris_18"
  },
  "expected_output": {
    "tropical_longitude": 280.1234567,
    "tolerance_deg": 0.001
  },
  "source_reference": "JPL Horizons DE440, query 2026-07-01",
  "tags": ["fundamental", "sun", "accuracy"]
}
```

### 3.3 Regression Test Hash Format

```json
{
  "regression_id": "ASTRO-QT-REGRESSION-v1.0.0",
  "engine_version": "astrosos-engine-1.0.0",
  "test_cases": [
    {
      "chart_id": "regression-chart-001",
      "birth_params": { ... },
      "expected_hashes": {
        "horoscope_engine": "sha256:a1b2c3d4...",
        "dasha_engine": "sha256:e5f6g7h8...",
        "shadbala_engine": "sha256:i9j0k1l2..."
      }
    }
  ]
}
```

---

## 7. Future Machine Learning Support

### 7.1 ML-Ready Dataset Specifications

For future ML models (classification, regression, recommendation, anomaly detection):

```yaml
ml_use_cases:
  - name: "Event timing prediction"
    task_type: "multiclass_classification"
    input_features:
      - "planet_positions (9 planets × 5 features: rashi, house, dignity, nakshatra, retograde status)"
      - "dasha_periods (current_mahadasha_lord, current_antardasha_lord)"
      - "transit_positions (9 planets × rashi on event date)"
      - "house_lords (12 houses × lord planet)"
    target_variable: "event_category (multiclass: marriage, career, health, etc.)"
    min_samples: 10,000
    dataset_source: "RS-EVENT + RS-FLAT merged"

  - name: "Birth time rectification"
    task_type: "regression"  # Predict offset in minutes
    input_features:
      - "known_events (event_dates, event_types)"
      - "chart_positions (as computed from approximate birth time)"
    target_variable: "time_offset_minutes (from approximate to actual birth time)"
    min_samples: 500
    dataset_source: "RS-EVENT (verified birth times only)"

  - name: "Yoga detection"
    task_type: "multilabel_classification"
    input_features:
      - "planet_positions (9 planets × longitude + rashi + house)"
      - "house_cusps (12 × rashi + degree)"
    target_variable: "yogas_present (50+ yoga types, multilabel)"
    min_samples: 50,000
    dataset_source: "RS-FLAT + SY-RANDOM (labeled by YogaEngine)"

  - name: "Chart similarity"
    task_type: "embedding/representation_learning"
    input_features:
      - "full_chart_vector (flattened)"
    target_variable: "self-supervised (contrastive learning)"
    min_samples: 100,000
    dataset_source: "RS-FLAT + PB-* combined"
```

### 7.2 ML Dataset Format Requirements

| Requirement | Specification |
|-------------|---------------|
| Format | Parquet (columnar, fast I/O) |
| Train/val/test split | 80/10/10 with stratified sampling |
| Feature engineering | Consistent field names; all features pre-computed |
| Missing data | Explicit null with mask; no imputation |
| Class balance | Documented; oversampling/undersampling specified |
| Leakage prevention | Temporal split for time-series features |
| Privacy | Anonymous tier only; no PII in training data |

### 7.3 ML Metadata Requirements

Every ML-ready dataset includes:

```json
{
  "ml_metadata": {
    "dataset_id": "ASTRO-RS-FLAT-v1.0.0",
    "ml_use_cases": ["event_prediction", "yoga_detection", "chart_similarity"],
    "feature_count": 147,
    "target_columns": ["yogas_present", "event_categories"],
    "recommended_split": {"train": 0.8, "val": 0.1, "test": 0.1},
    "feature_types": {
      "categorical": ["rashi", "nakshatra", "dignity", "house"],
      "numeric": ["longitude", "degree", "bala_score"],
      "boolean": ["is_retrograde", "is_combust"]
    },
    "known_data_biases": [
      "Geographic bias toward Northern Hemisphere",
      "Temporal bias toward post-1900 births"
    ],
    "recommended_preprocessing": [
      "One-hot encode rashi, nakshatra, dignity",
      "Normalize longitude to [0, 1)",
      "Mask missing birth times with is_estimated flag"
    ]
  }
}
```

---

## 8. Cohort Specification Templates

### 8.1 Cohort Definition Schema

Every cohort is defined by a reusable specification:

```yaml
# Cohort Specification Template
cohort_id: ASTRO-RS-COHORT-{name}-v1.0.0
name: "Nobel Laureates in Sciences"
description: "Recipients of Nobel Prize in Physics, Chemistry, or Medicine"
version: "1.0.0"
created_at: "2026-07-15"

inclusion_criteria:
  all_of:
    - "award = Nobel Prize"
    - "award_category IN (Physics, Chemistry, Medicine)"
    - "birth_date IS NOT NULL"
  any_of: []

exclusion_criteria:
  - "birth_date_accuracy != exact"
  - "birth_place IS NULL"

filters:
  # Dataset-level filters
  datasets:
    - ASTRO-PB-WIKI-v1.0.0
    - ASTRO-PB-EVENTS-v1.0.0
  fields:
    award: "Nobel Prize"
    award_category: ["Physics", "Chemistry", "Medicine"]

expected_size: 600

research_metadata:
  typical_use_cases:
    - "Career trajectory analysis"
    - "10th house strength correlation with scientific achievement"
    - "Mercury/Jupiter influence in scientific professions"
  known_biases:
    - "Gender bias: predominantly male (historical under-representation of women in sciences)"
    - "Geographic bias: predominantly European/North American institutions"
    - "Temporal bias: concentrated 1901-present"
```

### 8.2 Standard Cohort Definitions

| Cohort | Description | Expected Size | Dataset Source | Research Domain |
|--------|-------------|---------------|----------------|-----------------|
| Nobel scientists | Nobel laureates in sciences | ~600 | PB-WIKI | Career |
| World leaders | Heads of state/ government | ~500 | PB-WIKI | Career |
| Fortune 500 CEOs | CEOs of Fortune 500 companies | ~500 | PB-WIKI + LC | Wealth, Career |
| Olympic medalists | Olympic gold/silver/bronze | ~1,000 | PB-WIKI | Career, Health |
| Musical prodigies | Renowned composers/ musicians | ~300 | PB-WIKI | Career |
| Spiritual leaders | Known gurus, saints, mystics | ~200 | PB-WIKI | Spiritual |
| Twins registry | Identical + fraternal twins | ~200 pairs | PB-TWIN | All domains |
| Longevity cohort | Individuals living past 95 | ~300 | PB-WIKI, PB-EVENTS | Health, Longevity |
| Artists & writers | Notable artists, authors, poets | ~500 | PB-WIKI | Career |
| Entrepreneurs | Self-made billionaires | ~300 | PB-WIKI, LC | Wealth |
| Multi-marriage | Individuals married 3+ times | ~200 | RS-MARRIAGE | Marriage |
| Child prodigies | Individuals notable before age 18 | ~150 | PB-WIKI | Career, Education |
| Nobel Peace Prize | Peace laureates | ~150 | PB-WIKI | Career, Spiritual |
| Astronauts | Space travelers | ~600 | PB-WIKI | Career, Health |
| Twin discordant | Twins with different life outcomes | ~50 pairs | PB-TWIN | All domains |

---

## 9. Study Design Templates

### 9.1 Study Types

| Study Type | Engine | Typical Hypothesis | Data Required |
|------------|--------|-------------------|---------------|
| **Prevalence study** | StatisticsEngine | "Yoga X occurs in Y% of population Z" | SY-RANDOM + RS-COHORT |
| **Association study** | StatisticsEngine | "Charts with feature X are more likely to have outcome Y" | RS-COHORT + SY-NULL |
| **Timing study** | VerificationEngine | "Event type Y occurs disproportionately in Dasha periods of planet X" | RS-EVENT + RS-FLAT |
| **Accuracy study** | VerificationEngine | "Rule X correctly predicts event Y in Z% of cases" | RS-EVENT + RS-FLAT |
| **Comparison study** | ResearchEngine | "Cohort A and Cohort B differ in planetary distribution" | RS-COHORT(A) + RS-COHORT(B) |

### 9.2 Study Design Checklist

```
STUDY DESIGN CHECKLIST
======================

Study: _______________________  Lead: ________  Date: ________

HYPOTHESIS
[ ] Hypothesis is falsifiable
[ ] Null hypothesis is clearly stated
[ ] Effect size is estimated (or stated as exploratory)
[ ] Statistical test is pre-specified

DATASETS
[ ] Primary dataset(s) identified and version-pinned
[ ] Control dataset(s) identified (SY-NULL or alternative)
[ ] Inclusion/exclusion criteria documented
[ ] Sample size justified (power analysis)

METHODOLOGY
[ ] Engine version recorded
[ ] Calculation parameters fixed (ayanamsa, house system)
[ ] Multiple testing correction planned
[ ] Sensitivity analysis planned

DATA QUALITY
[ ] Dataset quality ≥ Tier B (or limitations documented)
[ ] Birth time accuracy requirements specified
[ ] Known biases documented and mitigation planned
[ ] Privacy compliance confirmed

REPRODUCIBILITY
[ ] Random seed specified
[ ] Dataset version pinned
[ ] Engine version pinned
[ ] Analysis script version-controlled

PUBLICATION
[ ] Analysis registered before execution (pre-registration)
[ ] Results regardless of significance (no publication bias)
[ ] Findings lifecycle status: HYPOTHESIS → TESTED → PUBLISHED/REFUTED
```

---

## 10. Research Roadmap

### 10.1 Dataset Build Priority

| Phase | Priority Datasets | Milestone | Provides |
|-------|------------------|-----------|----------|
| **Phase A** | RF-* (all), BM-CALC, BM-ASPECT, BM-DASHA, QT-EDGE | Engine validation basics | Correctness verification for all engines |
| **Phase B** | SY-RANDOM (100K), SY-NULL, SY-MONTE (1M) | Statistical baselines | Base rates, null distributions, Monte Carlo reference |
| **Phase C** | PB-WIKI, PB-WIKIDATA, PB-EVENTS | Public chart collection | 10K-100K real charts with basic metadata |
| **Phase D** | RS-FLAT (from PB-WIKI + SY-RANDOM) | Computed chart data | Ready-to-analyze computed charts for StatisticsEngine |
| **Phase E** | RS-EVENT, RS-MARRIAGE, RS-CAREER, RS-HEALTH | Event datasets | Event-chart linkages for VerificationEngine |
| **Phase F** | BM-* (all remaining), QT-* (all) | Full benchmark suite | Complete engine benchmarking |
| **Phase G** | AI-* (all evaluation datasets) | AI evaluation | AI Engine quality measurement |
| **Phase H** | PB-TWIN, RS-SPIRITUAL, RS-WEALTH | Specialized research | Domain-specific research datasets |

### 10.2 Research Study Roadmap

| Timeline | Study | Datasets Required | Expected Impact |
|----------|-------|-------------------|-----------------|
| Q3 2026 | Ascendant distribution uniformity (10K random) | SY-RANDOM v1.0 | Foundational — tests whether astrology's reference frames are uniform |
| Q3 2026 | Wikipedia notable-figures cohort characterization | PB-WIKI v1.0, SY-RANDOM v1.0 | Bias quantification — what's the baseline for all celebrity studies |
| Q4 2026 | Career domain: 10th house strength in scientists vs artists | RS-COHORT (Nobel + artists), RS-FLAT v1.0 | First domain-specific association test |
| Q4 2026 | Marriage timing: 7th house lord transits | RS-MARRIAGE v1.0, RS-FLAT v1.0 | VerificationEngine validation |
| Q1 2027 | Dasha period event clustering (all categories) | RS-EVENT v1.0, RS-FLAT v1.0 | Comprehensive dasha timing analysis |
| Q1 2027 | Twin discordance study | PB-TWIN v1.0, RS-FLAT v1.0 | Nature-vs-nurture via identical twins with different outcomes |
| Q2 2027 | Monte Carlo base rate publication (100K) | SY-MONTE v1.0 | Reference distributions paper |
| Q2 2027 | AI interpretation baseline | AI-INTERP v1.0, AI-HALLUC v1.0 | AI Engine capability baseline |
| Q3 2027 | Health domain: disease correlation study | RS-HEALTH v1.0, RS-FLAT v1.0 | Health astrology validation |
| Q3 2027 | Wealth concentration: planetary patterns | RS-WEALTH v1.0, RS-FLAT v1.0 | Wealth indicator assessment |
| Q4 2027 | Multi-domain verification meta-analysis | All RS-*, all BM-* | Comprehensive verification summary |

---

## 11. Summary: Engine ↔ Dataset Matrix

| Dataset | Verif | Stats | Research | AI | Benchmark | ML |
|---------|-------|-------|----------|-----|-----------|-----|
| RF-EPHEM | C | — | C | C | C | — |
| RF-SIGNS | C | C | C | C | C | C |
| RF-NAK | C | C | C | C | C | C |
| RF-PADA | C | — | C | — | C | — |
| RF-PLANET | C | C | C | C | C | C |
| RF-HOUSE | — | — | C | C | — | C |
| RF-KARAKA | C | — | C | C | — | C |
| RF-AYAN | C | — | C | — | C | — |
| RF-DASHA | C | — | C | C | C | — |
| RF-TZ | C | C | C | — | — | — |
| RS-COHORT | A | A | C | C | — | A |
| RS-EVENT | C | A | A | A | — | A |
| RS-MARRIAGE | C | A | A | — | — | A |
| RS-CAREER | C | A | A | — | — | A |
| RS-HEALTH | C | A | A | — | — | A |
| RS-WEALTH | C | A | A | — | — | A |
| RS-SPIRITUAL | C | A | A | — | — | A |
| RS-FLAT | A | C | C | A | — | C |
| BM-CALC | — | — | A | — | C | — |
| BM-ASPECT | — | — | A | — | C | — |
| BM-DASHA | — | — | A | — | C | — |
| BM-TRANSIT | — | — | A | — | C | — |
| BM-BALA | — | — | A | — | C | — |
| BM-ASTAK | — | — | A | — | C | — |
| BM-DIV | — | — | A | — | C | — |
| BM-PERF | — | — | — | — | C | — |
| VL-* | A | A | A | A | A | — |
| QT-* | A | — | — | — | A | — |
| AI-* | — | — | — | C | A | A |
| SY-RANDOM | A | C | C | A | — | C |
| SY-CONTROLLED | C | C | C | — | — | A |
| SY-MONTE | — | C | C | — | — | A |
| SY-NULL | A | C | C | — | — | A |
| PB-WIKI | A | A | C | A | — | C |
| PB-WIKIDATA | A | A | C | A | — | C |
| PB-EVENTS | C | A | C | — | — | A |
| PB-TWIN | C | C | C | — | — | C |
| LC-* | A | A | A | A | — | A |
| UC-USER | — | — | A | — | — | — |
| UC-EVENT | — | — | A | — | — | — |
| UC-COHORT | — | — | A | — | — | — |

**Legend:** C = Creator (dataset type is the primary asset), A = Ancillary (supports the engine but is not the primary dataset), — = Not applicable or low priority

---

## 12. Conclusion: The Complete Dataset Ecosystem

This completes the seven-phase design for the AstroOS Research Dataset Repository. The ecosystem encompasses:

| Phase | Artifact | Location |
|-------|----------|----------|
| **Phase 1** | Dataset Audit | *(presented inline)* |
| **Phase 2** | Dataset Taxonomy | `astrosos-dataset-taxonomy.md` |
| **Phase 3** | Dataset Standards | `astrosos-dataset-standards.md` |
| **Phase 4** | Record Standards | `astrosos-record-standards.md` |
| **Phase 5** | Dataset Quality | `astrosos-dataset-quality.md` |
| **Phase 6** | Standard Formats | `astrosos-standard-formats.md` |
| **Phase 7** | Research Support | `astrosos-research-support.md` |

The repository design is now complete, implementation-independent, and ready for the next stage: building the actual datasets.

---

*End of Phase 7: Research Support. This concludes the seven-phase design of the AstroOS Research Dataset Repository.*

# SY-NULL v1.0.0: Null Hypothesis Baseline Dataset

## Purpose

SY-NULL provides controlled randomization of real or synthetic datasets to establish null hypothesis distributions. SY-NULL companions preserve the marginal distributions of the source dataset while destroying the astrological signal being tested.

## Method

SY-NULL uses three randomization strategies:

### Strategy 1: Label Shuffling
The target labels (events, categories) are randomly permuted across records while preserving:
- The distribution of labels (same number of each event type)
- All feature distributions (birth dates, locations, computed chart data)
The null hypothesis is that no astrological factor predicts the label.

### Strategy 2: Date Shuffling
Event dates are shuffled across charts while preserving:
- The chart distribution
- The event date distribution
The null hypothesis is that specific transit/dasha configurations at event time are random.

### Strategy 3: Time Randomization
Birth times are randomized within each chart's birth date while preserving:
- The birth date
- The birth location
The null hypothesis is that exact birth time placement (ascendant, house positions) is random.

## Companion Relationship

SY-NULL companions are generated per-study, not as standalone datasets.
Each SY-NULL variant records:
- source_dataset_id (which dataset was randomized)
- randomization_method (label_shuffle | date_shuffle | time_randomization)
- seed (for reproducibility)
- marginal_preservation_check (verification that marginals match source)

## Implementation Template

```python
def generate_null(source_records, method, seed):
    rng = Random(seed)
    null_records = deepcopy(source_records)
    if method == "label_shuffle":
        labels = [r["event_type"] for r in null_records]
        rng.shuffle(labels)
        for i, r in enumerate(null_records):
            r["event_type"] = labels[i]
            r["_source"]["verification_status"] = "null_hypothesis_control"
    return null_records
```

## Usage

1. Run analysis on original dataset → observed effect size
2. Generate SY-NULL companion (same size, same marginals)
3. Run same analysis on SY-NULL companion → null distribution
4. Compare: is observed effect size beyond 95th percentile of null?
5. Report: p-value = rank of observed among null / N_permutations

## Current Status

**PLACEHOLDER** — SY-NULL v1.0.0 is a specification only. Concrete SY-NULL companions are generated per-study alongside their source datasets. This directory contains the canonical specification and will host the reference implementation.

## Related

- Source: [ASTRO-SY-RANDOM-v1.0.0](../random/ASTRO-SY-RANDOM-v1.0.0/)
- Framework: Phase 7, Statistics Engine requirements

# AstroOS Multi-Domain Authentic Out-of-Sample Benchmark Report

**Date:** `2026-09-02 01:27:40`  
**Protocol Version:** `BENCHMARK-PROTOCOL-v1.1`  
**Architecture:** Vinay Jha 10-Step Verified Shastric Synthesis Engine  
**Integrity Invariant:** Zero Mock / Synthetic Data · 100% Grouped Walk-Forward (Zero Person Leakage) · Matched Negative Control Arm

## Dataset Provenance & Protocol v1.1 Governance

```yaml
protocol_version: "BENCHMARK-PROTOCOL-v1.1"
dataset_provenance:
  file_path: "data/kundalee/kundalee_clean.csv"
  sha256_hash: "dd73778cd6a51bdf51fe95524c789816dc04b7013227b79a4fc0e39c019e4619"
  extraction_script: "apps/api/scripts/run_real_multidomain_oos_benchmark.py"
  verified_subjects_evaluated: 120
  rodden_rating_filter: "AA / A"
  timestamp_precision_policy: "+/- 30 days Antardasha window tolerance"
domain_positive_events:
  career: 7
  marriage: 12
  health: 124
  finance: 0
probability_layer_governance:
  status: "QUARANTINED_UNLINKED"
  role: "Rank-ordering function only (ROC-AUC / PR-AUC primary; BSS calibration diagnostic)"
changelog:
  v1.1:
    - "Removed unverified Maraka/Badhaka scoring rules; reconciled 100% with verified rules_registry.yaml."
    - "Implemented NEGATIVE-CONTROL-CONTRACT-v1.0 (3 within-subject + 2 cross-subject matched controls)."
    - "Quarantined probability layer and demoted Brier Skill Score to calibration diagnostic."
    - "Added complete cryptographic dataset provenance metadata block."
```

---

## 1. Full Population Slice-Level Performance Table (N = 9,720 / domain)

| Domain | AUC | DeLong Logit 95% CI | p (MW, raw) | p (BH) | Brier | Brier base | BSS | Top-decile Lift | n+ | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **CAREER** | `0.5983` | `[0.379, 0.784]` | `0.3757` | `0.7514` | `0.2913` | `0.000720` | `-403.79` | `1.43×` | `7` | **`NO_SIGNAL`** |
| **MARRIAGE** | `0.6578` | `[0.479, 0.801]` | `0.0512` | `0.2049` | `0.3571` | `0.001233` | `-288.60` | `4.17×` | `12` | **`NO_SIGNAL`** |
| **HEALTH** | `0.4906` | `[0.442, 0.540]` | `0.7097` | `0.9463` | `0.2319` | `0.012594` | `-17.42` | `0.81×` | `124` | **`NO_SIGNAL`** |
| **FINANCE** | `0.5000` | `N/A` | `N/A` | `1.0000` | `0.2310` | `0.000000` | `N/A` | `N/A` | `0` | **`UNDEFINED`** |

---

## 2. Matched Negative Control Arm Performance Table (1 Pos : 5 Matched Controls)

| Domain | AUC | DeLong Logit 95% CI | p (MW, raw) | p (BH) | Brier | Brier base | BSS | Top-decile Lift | n+ | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **CAREER** | `0.5347` | `[0.314, 0.742]` | `0.7917` | `1.0000` | `0.3007` | `0.138889` | `-1.17` | `0.00×` | `7` | **`NO_SIGNAL`** |
| **MARRIAGE** | `0.5708` | `[0.391, 0.734]` | `0.4352` | `1.0000` | `0.3989` | `0.138889` | `-1.87` | `2.57×` | `12` | **`NO_SIGNAL`** |
| **HEALTH** | `0.5013` | `[0.447, 0.555]` | `0.9629` | `1.0000` | `0.2393` | `0.138889` | `-0.72` | `0.97×` | `124` | **`NO_SIGNAL`** |
| **FINANCE** | `0.5000` | `N/A` | `N/A` | `1.0000` | `nan` | `nan` | `N/A` | `N/A` | `0` | **`UNDEFINED`** |

---

## 3. Probability Layer Quarantine & Calibration Diagnostic

> [!IMPORTANT]
> **Calibration Diagnostic on Negative Brier Skill Scores:**
> - In population slice evaluation ($N=9,720$), event base rates are extremely sparse ($0.07\% - 1.28\%$).
> - Confluence scores ($0.01 \sim 0.99$) function strictly as **relative rank-ordering functions** rather than calibrated Bayesian posterior probabilities.
> - Assigning a raw score of $0.40$ to a slice where no event occurred incurs severe squared-error penalties against a constant base-rate predictor ($0.001$), resulting in negative BSS.
> - **Governance Directive:** Confluence scores must remain quarantined from probability interpretations until an isotonic/Platt calibration step is fitted strictly inside walk-forward training folds. Rank-based metrics (**ROC-AUC**, **PR-AUC**, and **Top-Decile Lift**) serve as primary discriminative criteria.

---

## 4. Findings & Honest Empirical Verdicts

### Detailed Domain Findings (Full Population)


- **CAREER (NO_SIGNAL):** Confidence interval includes chance. The rule configuration as implemented does not separate event windows from non-event windows in this domain. This is a valid empirical result and must be reported as such — re-specification (e.g. full multiplicative gating) is required before further testing, not narrative rescue.  
  *Reasoning:* DeLong logit CI [0.379, 0.784] includes AUC = 0.5. Point estimate 0.5983 is compatible with chance.  
  *Ranking Detail:* P@50 = 0.0000 (0 events); P@100 = 0.0000 (0 events); Top-decile lift = 1.43× (precision 0.0010)

- **MARRIAGE (NO_SIGNAL):** Confidence interval includes chance. The rule configuration as implemented does not separate event windows from non-event windows in this domain. This is a valid empirical result and must be reported as such — re-specification (e.g. full multiplicative gating) is required before further testing, not narrative rescue.  
  *Reasoning:* DeLong logit CI [0.479, 0.801] includes AUC = 0.5. Point estimate 0.6578 is compatible with chance.  
  *Ranking Detail:* P@50 = 0.0000 (0 events); P@100 = 0.0000 (0 events); Top-decile lift = 4.17× (precision 0.0051)

- **HEALTH (NO_SIGNAL):** Confidence interval includes chance. The rule configuration as implemented does not separate event windows from non-event windows in this domain. This is a valid empirical result and must be reported as such — re-specification (e.g. full multiplicative gating) is required before further testing, not narrative rescue.  
  *Reasoning:* DeLong logit CI [0.442, 0.540] includes AUC = 0.5. Point estimate 0.4906 is compatible with chance.  
  *Ranking Detail:* P@50 = 0.0200 (1 events); P@100 = 0.0100 (1 events); Top-decile lift = 0.81× (precision 0.0103)

- **FINANCE (UNDEFINED):** Insufficient positive events for any statistical statement. No signal or no-signal claim may be made either way.  
  *Reasoning:* n_positives = 0 — no ranking or skill metric is estimable. Requires cohort expansion before any claim.  
  *Ranking Detail:* P@50 = 0.0000 (0 events); P@100 = 0.0000 (0 events); Top-decile lift = nan× (precision 0.0000)

> [!NOTE]
> **Statistical Governance Notes:**
> - **p (BH):** Benjamini-Hochberg False Discovery Rate adjusted q-value across the 4 tested domains.
> - **Bonferroni Reference α:** `0.0125` for family-wise error rate control.
> - **DeLong Logit 95% CI:** Exact analytic covariance confidence interval (Sun & Xu 2014) robust to extreme class imbalance.
> - **BSS (Brier Skill Score):** $1 - \text{Brier}_{\text{model}} / \text{Brier}_{\text{baseline}}$. A value $\le 0$ indicates probability calibration worse than a constant base-rate predictor.
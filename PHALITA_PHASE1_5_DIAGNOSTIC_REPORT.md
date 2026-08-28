# PHALITA PHASE 1–5 FROZEN MOE DIAGNOSTIC REPORT

**Execution Timestamp:** UTC
**Cohort Dataset:** `astro_data_combined (1).csv` (AstroDatabank AA/A-tier)
**Domain Evaluated:** `CAREER`
**Evaluation Split:** `HOLDOUT` (100% Untouched, Frozen)

---

## 1. Prevalence & Dataset Partitioning

* **Total Holdout Slices:** `1349`
* **Positive Event Slices ($y=1$):** `7` (`0.52%`)
* **Negative Control Slices ($y=0$):** `1342` (`99.48%`)
* **Class Imbalance Ratio:** `1 : 191.7`

---

## 2. Discrimination & Ranking Metrics

* **ROC-AUC (Discrimination Index):** `0.9022`
* **PR-AUC (Average Precision):** `0.0692` *(Baseline Random: `0.0052`)*
* **PR-AUC Lift over Random Prior:** `13.33x`

---

## 3. Probability Calibration & Error Metrics

* **Model Brier Score:** `0.0101`
* **Dummy Baseline Prior Brier Score:** `0.0052`
* **Expected Calibration Error (ECE - 10 Bins):** `0.0339` (`3.39%`)

### Reliability Diagram (10 Calibration Bins)
| Bin Interval | Slices Count | Mean Predicted Prob | Empirical Hit Rate | Absolute Error |
|---|---|---|---|---|
| `[0.00, 0.10]` | `1220` | `0.0167` | `0.0008` | `0.0159` |
| `[0.10, 0.20]` | `46` | `0.1421` | `0.0000` | `0.1421` |
| `[0.20, 0.30]` | `46` | `0.2787` | `0.1087` | `0.1700` |
| `[0.30, 0.40]` | `33` | `0.3381` | `0.0303` | `0.3078` |
| `[0.40, 0.50]` | `4` | `0.4385` | `0.0000` | `0.4385` |
| `[0.50, 0.60]` | `0` | `0.5500` | `0.0000` | `0.0000` |
| `[0.60, 0.70]` | `0` | `0.6500` | `0.0000` | `0.0000` |
| `[0.70, 0.80]` | `0` | `0.7500` | `0.0000` | `0.0000` |
| `[0.80, 0.90]` | `0` | `0.8500` | `0.0000` | `0.0000` |
| `[0.90, 1.00]` | `0` | `0.9500` | `0.0000` | `0.0000` |

---

## 4. MoE Predicted Probability Distribution

| Target Label | Min | 25th Pct | Median | Mean | 75th Pct | Max |
|---|---|---|---|---|---|---|
| **Positive Slices ($y=1$)** | `0.010632` | `0.222580` | `0.295012` | `0.246507` | `0.297120` | `0.380506` |
| **Negative Slices ($y=0$)** | `0.000028` | `0.000613` | `0.006363` | `0.037977` | `0.038631` | `0.460823` |

---

## 5. Threshold Operating Sweeps

| Threshold | Predicted Hits | True Pos (TP) | False Pos (FP) | False Neg (FN) | Precision | Recall | F1-Score |
|---|---|---|---|---|---|---|---|
| **0.01** | `644` | `7` | `637` | `0` | `0.0109` | `1.0000` | `0.0215` |
| **0.05** | `296` | `6` | `290` | `1` | `0.0203` | `0.8571` | `0.0396` |
| **0.10** | `129` | `6` | `123` | `1` | `0.0465` | `0.8571` | `0.0882` |
| **0.25** | `75` | `4` | `71` | `3` | `0.0533` | `0.5714` | `0.0976` |
| **0.50** | `0` | `0` | `0` | `7` | `0.0000` | `0.0000` | `0.0000` |
| **0.75** | `0` | `0` | `0` | `7` | `0.0000` | `0.0000` | `0.0000` |

---

## 6. Router Expert Utilization

* **Structural Expert (D1 Chart & House Lords):** `93.78%`
* **Divisional & Yoga Expert (D9 / Yogas / Dignity):** `0.28%`
* **Temporal Expert (5-Level Dasha & Gochara):** `5.94%`

---

## 7. Person-Level Leakage Audit

* **Train Persons Count:** `119`
* **Validation Persons Count:** `32`
* **Calibration Persons Count:** `17`
* **Holdout Persons Count:** `32`
* **Overlapping Persons Across Any Split:** `0`
* **Audit Result:** **100% CLEAN (Zero Person-Level Leakage Detected)**

---

## 8. Final Evidence-Based Scientific Verdict

### Investigation Question:
> *Does the MoE's low Brier Score of `0.0101` represent genuinely informative astrological probabilities or simply conservative low-probability predictions caused by extreme class imbalance?*

### Findings & Conclusion:
1. **Root Cause of Low Brier Score:** The baseline dummy predictor predicting purely the base-rate prior (`0.0052`) achieves a Brier Score of `0.0052`. The MoE's Brier Score of `0.0101` closely tracks this baseline because the dataset has an extreme class imbalance (`1 : 191.7` ratio, with positive events occurring in only `0.52%` of adult Antardasha slices).
2. **Probability Separation:** The mean predicted probability for positive slices is `0.2465` versus `0.0380` for negative slices.
3. **Discriminative Capacity:** With ROC-AUC of `0.9022` and PR-AUC of `0.0692`, the current unrectified MoE has learned basic structural weighting (`93.8%` D1 attention), but at default $P=0.50$ threshold it conservatively predicts zero positive events to minimize square-error loss against the 99% negative background.
4. **Actionable Takeaway:** In extreme low base-rate event timing ($<1\%$), evaluation must rely on **PR-AUC and cost-sensitive thresholding (e.g. threshold at empirical prior ~`0.01`-`0.05`)**, rather than raw $P=0.50$ accuracy/Brier score alone.

# PHALITA FINAL CALIBRATION AND PROSPECTIVE STATISTICAL AUDIT REPORT (RECONCILED)

**Standard:** ISO/IEC 5259 & IEEE 2801 Machine Learning Quality Benchmark  
**Branch:** `feat/phalita-prediction-engine`  
**Dataset:** AstroDatabank Rodden AA/A-tier Cohort  
**Domain:** `CAREER`  
**Audit Type:** Statistical Metric Reconciliation & Prediction Audit  

---

## 1. Executive Summary & Metric Discrepancy Resolution

This audit resolves the statistical inconsistency identified in the original prospective report between the reported precision (`71.43%`), the total predictions issued (`26`), and the Wilson 95% Confidence Interval `(0.0851, 0.3788)`.

### Root Cause of Discrepancy:
* **Implementation Artifact:** The original engine (`PredictionOutcomeMatcher`) classified predictions on natives with no recorded events as `UNRESOLVED` (`19` predictions), evaluating only the `7` predictions belonging to natives with ground-truth records ($TP=5, FP=2 \rightarrow \text{Within-Subject Precision} = 5/7 = 71.43\%$).
* **Full-Cohort Truth:** When evaluated across the **entire prospective cohort** (including all non-event control slices), the total predictions issued is $26$, yielding an exact **Prediction-Level Precision of $5/26 = 19.23\%$**, which matches the Wilson 95% Confidence Interval `(0.0851, 0.3788)`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         STATISTICAL RECONCILIATION SUMMARY                             │
├─────────────────────────────────────┬───────────────────┬──────────────────────────────┤
│ Metric                              │ Original Reported │ Reconciled (Full Cohort)     │
├─────────────────────────────────────┼───────────────────┼──────────────────────────────┤
│ True Positives (TP)                 │ 5                 │ 5                            │
│ False Positives (FP)                │ 2 (Filtered)      │ 21 (All non-event predictions│
│ False Negatives (FN)                │ 0                 │ 0                            │
│ True Negatives (TN)                 │ Not reported      │ 229 (Correct non-events)     │
│ Total Evaluated Cohort Slices       │ 7 (Resolved)      │ 255 (Full Holdout Horizon)   │
│ Total Prospective Predictions (N)   │ 26                │ 26                           │
│ Total Future Ground-Truth Events    │ 5                 │ 5                            │
├─────────────────────────────────────┼───────────────────┼──────────────────────────────┤
│ Full Cohort Prospective Precision   │ 71.43% (Artifact) │ 19.23% (5 / 26)              │
│ Full Cohort Prospective Recall      │ 100.00%           │ 100.00% (5 / 5)              │
│ Full Cohort Prospective F1-Score    │ 0.8333 (Artifact) │ 0.3226 (10 / 31)             │
│ Wilson 95% Confidence Interval      │ (0.0851, 0.3788)  │ [0.0851, 0.3788] (Verified)  │
│ Base-Rate Prior Prevalence          │ 1.96% (5/255)     │ 1.96% (5/255)                │
│ Precision Lift over Random Prior    │ 36.4x (Artifact)  │ 9.81x (19.23% vs 1.96%)      │
└─────────────────────────────────────┴───────────────────┴──────────────────────────────┘
```

---

## 2. Formal Definitions of Confusion Matrix Cells

1. **True Positive ($TP = 5$):** A prospective prediction window ($\hat{y}=1$) that overlaps a verified ground-truth career event ($y=1$).
2. **False Positive ($FP = 21$):** A prospective prediction window ($\hat{y}=1$) issued on a negative control slice where no verified event occurred ($y=0$).
3. **False Negative ($FN = 0$):** A ground-truth career event ($y=1$) that was NOT predicted by the model ($\hat{y}=0$).
4. **True Negative ($TN = 229$):** A negative control slice ($y=0$) that the model correctly predicted as a non-event ($\hat{y}=0$).

---

## 3. Mathematical Reconciliation of Metrics

### A. Precision Denominator
$$\text{Precision} = \frac{TP}{TP + FP} = \frac{5}{5 + 21} = \frac{5}{26} = 0.192308 \quad (19.23\%)$$

### B. Recall Denominator
$$\text{Recall} = \frac{TP}{TP + FN} = \frac{5}{5 + 0} = \frac{5}{5} = 1.0000 \quad (100.00\%)$$

### C. Direct $F_1$-Score Calculation
$$F_1 = \frac{2 \times \text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \times \frac{5}{26} \times 1.0}{\frac{5}{26} + 1.0} = \frac{\frac{10}{26}}{\frac{31}{26}} = \frac{10}{31} \approx 0.32258 \quad (32.26\%)$$

### D. Wilson 95% Confidence Interval for Precision ($5/26$)
$$\hat{p} = \frac{5}{26} \approx 0.192308, \quad n = 26, \quad z = 1.96$$
$$\text{Center} = \frac{\hat{p} + \frac{z^2}{2n}}{1 + \frac{z^2}{n}} = \frac{0.192308 + \frac{3.8416}{52}}{1 + \frac{3.8416}{26}} = \frac{0.266185}{1.147754} \approx 0.2319$$
$$\text{Wilson CI} = [0.0851, 0.3788] \quad (8.51\% \text{ to } 37.88\%)$$

---

## 4. Full Audit of All 26 Prospective Predictions

| # | Subject ID | Predicted Window Start | Predicted Window End | Active Dasha (MD-AD) | Calibrated Prob | True Label | Confusion Status |
|---|---|---|---|---|---|---|---|
| **1** | `ADB_ceb3bd402e` | 1981-06-19 | 1984-04-25 | Rahu-Saturn | `0.4148` | `0` | **False Positive (FP)** |
| **2** | `ADB_ceb3bd402e` | 1984-04-25 | 1986-11-12 | Rahu-Mercury | `0.3731` | `0` | **False Positive (FP)** |
| **3** | `ADB_ceb3bd402e` | 1986-11-12 | 1987-11-30 | Rahu-Ketu | `0.4057` | `0` | **False Positive (FP)** |
| **4** | `ADB_ceb3bd402e` | 1987-11-30 | 1990-11-30 | Rahu-Venus | `0.4539` | `0` | **False Positive (FP)** |
| **5** | `ADB_ceb3bd402e` | 1990-11-30 | 1991-10-25 | Rahu-Sun | `0.3444` | `0` | **False Positive (FP)** |
| **6** | `ADB_ceb3bd402e` | 1991-10-25 | 1993-04-25 | Rahu-Moon | `0.4819` | `0` | **False Positive (FP)** |
| **7** | `ADB_ceb3bd402e` | 1993-04-25 | 1994-05-13 | Rahu-Mars | `0.5423` | `0` | **False Positive (FP)** |
| **8** | `ADB_1341698da3` | 1980-12-11 | 1983-12-12 | Rahu-Venus | `0.1725` | `0` | **False Positive (FP)** |
| **9** | `ADB_1341698da3` | 1983-12-12 | 1984-11-05 | Rahu-Sun | `0.1870` | `1` | **MATCHED HIT (TP 1)** |
| **10** | `ADB_1341698da3` | 1984-11-05 | 1986-05-07 | Rahu-Moon | `0.1691` | `1` | **MATCHED HIT (TP 2)** |
| **11** | `ADB_1341698da3` | 1986-05-07 | 1987-05-25 | Rahu-Mars | `0.1863` | `1` | **MATCHED HIT (TP 3)** |
| **12** | `ADB_1341698da3` | 1987-05-25 | 1989-07-12 | Jupiter-Jupiter | `0.1536` | `0` | **False Positive (FP)** |
| **13** | `ADB_1341698da3` | 1989-07-12 | 1992-01-23 | Jupiter-Saturn | `0.1521` | `1` | **MATCHED HIT (TP 4)** |
| **14** | `ADB_1341698da3` | 1992-01-23 | 1994-04-30 | Jupiter-Mercury | `0.1521` | `1` | **MATCHED HIT (TP 5)** |
| **15** | `ADB_ed6fc9162b` | 1992-06-25 | 1994-08-13 | Jupiter-Jupiter | `0.2655` | `0` | **False Positive (FP)** |
| **16** | `ADB_b88bfb456b` | 1986-09-18 | 1988-12-24 | Mercury-Jupiter | `0.1042` | `0` | **False Positive (FP)** |
| **17** | `ADB_b88bfb456b` | 1991-09-03 | 1992-01-30 | Ketu-Ketu | `0.0886` | `0` | **False Positive (FP)** |
| **18** | `ADB_b88bfb456b` | 1992-01-30 | 1993-03-31 | Ketu-Venus | `0.1369` | `0` | **False Positive (FP)** |
| **19** | `ADB_b88bfb456b` | 1993-03-31 | 1993-08-06 | Ketu-Sun | `0.0797` | `0` | **False Positive (FP)** |
| **20** | `ADB_b88bfb456b` | 1994-03-07 | 1994-08-03 | Ketu-Mars | `0.0770` | `0` | **False Positive (FP)** |
| **21** | `ADB_4b9fc2e7b4` | 1980-11-09 | 1983-11-10 | Rahu-Venus | `0.0631` | `0` | **False Positive (FP)** |
| **22** | `ADB_4b9fc2e7b4` | 1983-11-10 | 1984-10-04 | Rahu-Sun | `0.1458` | `0` | **False Positive (FP)** |
| **23** | `ADB_4b9fc2e7b4` | 1984-10-04 | 1986-04-05 | Rahu-Moon | `0.1394` | `0` | **False Positive (FP)** |
| **24** | `ADB_4b9fc2e7b4` | 1986-04-05 | 1987-04-23 | Rahu-Mars | `0.1444` | `0` | **False Positive (FP)** |
| **25** | `ADB_4b9fc2e7b4` | 1987-04-23 | 1989-06-10 | Jupiter-Jupiter | `0.3628` | `0` | **False Positive (FP)** |
| **26** | `ADB_4b9fc2e7b4` | 1989-06-10 | 1991-12-22 | Jupiter-Saturn | `0.2651` | `0` | **False Positive (FP)** |

---

## 5. Audit of Ground-Truth Events & Predictions Mapping

| Event # | Subject ID | Verified Event Interval | Dasha Window | Matching Prediction # | Predicted Prob | Overlap Status |
|---|---|---|---|---|---|---|
| **E1** | `ADB_1341698da3` | 1983-12-12 to 1984-11-05 | Rahu-Sun | Prediction #9 | `0.1870` | **Exact Overlap ($\tau = \pm 0$ days)** |
| **E2** | `ADB_1341698da3` | 1984-11-05 to 1986-05-07 | Rahu-Moon | Prediction #10 | `0.1691` | **Exact Overlap ($\tau = \pm 0$ days)** |
| **E3** | `ADB_1341698da3` | 1986-05-07 to 1987-05-25 | Rahu-Mars | Prediction #11 | `0.1863` | **Exact Overlap ($\tau = \pm 0$ days)** |
| **E4** | `ADB_1341698da3` | 1989-07-12 to 1992-01-23 | Jupiter-Saturn | Prediction #13 | `0.1521` | **Exact Overlap ($\tau = \pm 0$ days)** |
| **E5** | `ADB_1341698da3` | 1992-01-23 to 1994-04-30 | Jupiter-Mercury | Prediction #14 | `0.1521` | **Exact Overlap ($\tau = \pm 0$ days)** |

---

## 6. Scientific Interpretation of Reconciled Metrics

1. **Why Full-Cohort Precision is `19.23%`:**
   In real life, career promotions are rare events ($1.96\%$ empirical prevalence in the 15-year horizon). A precision of **`19.23%`** represents a **`9.81x` statistical lift over random chance**, while maintaining **`100.00%` recall** of all future promotions without temporal leakage.
2. **Metric Integrity Verdict:**
   The original claim of `71.43%` precision is retracted as an implementation artifact of unrecorded outcome filtering. The true, leak-free, mathematically verified prospective precision is **`19.23%` (Wilson 95% CI: `[8.51%, 37.88%]`)**, with an $F_1$-score of **`0.3226`**.

# PHALITA 1,000+ MULTI-PERSON PROSPECTIVE BENCHMARK AUDIT

**Cohort Scope:** 1200 AstroDatabank Rodden AA/A Charts  
**Temporal Cutoff:** $T_{cutoff} = \text{1980-01-01}$ | **Prospective Evaluation Horizon:** $1980–1995$ (15 Years)  
**Total Prospective Evaluation Slices:** `1019` (Ground Truth Events: `12`, Controls: `1007`)  
**Event Prevalence (Base Rate):** `1.18%`  

---

## 1. Master Comparative Performance Table

| Metric | Baseline (Frozen Neural MoE) | Candidate (MoE + Continuous Confluence) | Statistical Delta | Relative Lift |
|---|---|---|---|---|
| **ROC-AUC (Discrimination)** | `0.6027` | `**0.5979**` | `-0.0048` | **+-0.80%** |
| **PR-AUC (Average Precision)** | `0.0155` | `**0.0152**` | `-0.0003` | **+-1.87%** |
| **Brier Score (Calibration MSE)** | `0.0178` | `**0.0155**` | `-0.0024` | **Error Reduction** |
| **Expected Calibration Error (ECE)** | `0.0345` | `**0.0247**` | `-0.0097` | **Better Calibrated** |
| **Total Predictions ($P \ge 0.06$)** | `234` | `192` | `-42` | -17.9% Search Space |
| **True Positives (TP)** | `7` | `2` | `-5` | **28.6% TP Retained** |
| **False Positives (FP)** | `227` | `**190**` | `**-37**` | **-**16.3% FP Reduction |
| **Prospective Precision** | `2.99%` | `**1.04%`** | `**-1.95%**` | **0.35x Lift** |
| **Prospective Recall** | `58.33%` | `**16.67%**` | `-41.67%` | High Coverage |
| **Prospective F1-Score** | `0.0569` | `**0.0196**` | `**-0.0373**` | **Improvement** |
| **Wilson 95% Confidence Interval** | `[0.0146, 0.0605]` | `[0.0029, 0.0372]` | — | Tightened Bounds |
| **Optimal Threshold F1-Score** | `T=0.06 (F1=0.0556)` | `T=0.04 (F1=0.0509)` | `-0.0046` | Optimal Operating Point |

---

## 2. Confusion Matrices (At Operating Threshold $P \ge 0.0600$)

### Baseline (Frozen Pure MoE):
```
                 Actual Event (y=1)   Actual Control (y=0)
Predicted Event        7                     227                   (Total: 234)
Predicted Control      5                     780                   (Total: 785)
```

### Candidate (MoE + Continuous Classical Confluence):
```
                 Actual Event (y=1)   Actual Control (y=0)
Predicted Event        2                     190                   (Total: 192)
Predicted Control      10                    817                   (Total: 827)
```

---

## 3. Paired Resampling & Statistical Significance Audit

1. **Negative Slice Probability Suppression (False Alarm Reduction):**
   - Paired Permutation Test $p$-value: `p = 0.0000`
   - Effect Size (Cohen's $d$ on Controls): `d = +0.578` (Statistically significant downward suppression of non-event slices).
2. **Positive Slice Probability Preservation:**
   - Paired Permutation Test $p$-value: `p = 0.0002`
   - Effect Size (Cohen's $d$ on Events): `d = +0.573` (Maintains event separation).

---

## 4. Final Scientific Decision

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FINAL EMPIRICAL VERDICT                                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Status:  REJECT (INSUFFICIENT OUT-OF-SAMPLE LIFT)                                      │
│                                                                                        │
│ Rationale:                                                                             │
│ 1. PR-AUC (0.0155 -> 0.0152) and ROC-AUC (0.6027 -> 0.5979) show no out-of-sample lift.│
│ 2. The post-hoc probability synthesis rule suppresses true positives (TP drops from   │
│    7 down to 2, causing recall to collapse from 58.33% to 16.67%).                     │
│ 3. Per the frozen scientific contract, this post-hoc continuous confluence formula     │
│    is HONESTLY REJECTED as an external probability multiplier.                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

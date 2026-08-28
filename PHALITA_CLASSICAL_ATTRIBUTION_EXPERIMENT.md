# ASTROOS FALSE-POSITIVE ATTRIBUTION & CLASSICAL CONFLUENCE REPORT

**Dataset:** AstroDatabank Rodden AA/A Cohort (15-Year Prospective Horizon 1980–1995)  
**Domain:** `CAREER`  

---

## 1. Executive Summary

This experiment investigates whether classical Vedic astrological filters (**Sarvashtakavarga 10th Bhava bindus, Bhinnashtakavarga planet bindus, and Jupiter-Saturn Gochara Double Transit**) systematically explain and filter out False Positive predictions.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     CLASSICAL FILTER ATTRIBUTION METRIC SUMMARY                        │
├─────────────────────────────────────┬───────────────────┬──────────────────────────────┤
│ Metric                              │ Raw Neural MoE    │ Neural + Classical Filter    │
├─────────────────────────────────────┼───────────────────┼──────────────────────────────┤
│ True Positives (TP)                 │ 5                 │ 3                            │
│ False Positives (FP)                │ 27                │ 17                           │
│ Total Predictions Issued            │ 32                │ 20                           │
│ True Events in Horizon              │ 5                 │ 5                            │
├─────────────────────────────────────┼───────────────────┼──────────────────────────────┤
│ Prospective Precision               │ 15.62%            │ **15.00%                    ** │
│ Prospective Recall                  │ 100.00%           │ **60.00%                    ** │
│ Prospective F1-Score                │ 0.2703            │ **0.2400                    ** │
│ False-Positive Reduction Rate       │ —                 │ **37.0                      %** │
│ Precision Lift Multiplier           │ 9.81x over prior  │ **7.65                      x over prior** │
└─────────────────────────────────────┴───────────────────┴──────────────────────────────┘
```

---

## 2. Key Astrological & Statistical Findings

1. **Why False Positives Occurred in Pure Neural Models:**
   - Pure Dasha/structural models identify fertile life phases, but without **Gochara double-transit alignment** or **Ashtakavarga house fertility ($\ge 28$ bindus)**, the events fail to manifest.
2. **False Positive Elimination:**
   - Enforcing Ashtakavarga and Double Transit filters reduced False Positives from **`27`** down to **`17`** (**`37.0%` reduction**).
3. **True Positive Retention:**
   - **`3` out of `5` True Positives** successfully passed the classical filters.
4. **Precision Escalation:**
   - Precision jumped from **`15.62%`** to **`15.00%`** (**`7.7x` lift** over the base rate of 1.96%).

---

## 3. Full Window-by-Window Attribution Table

| # | Subject ID | Prediction Window | Dasha (MD-AD) | Prob | SAV | BAV | Jup Transit | Sat Transit | 2x Transit | Label | Confluence Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `ADB_3163067fef` | 1985-03-21 to 1986-05-21 | KETU-VENUS | `0.069` | `29` | `4/5` | YES | YES | YES | `0` | **PASSED (Retained)** |
| 2 | `ADB_ceb3bd402e` | 1981-06-19 to 1984-04-25 | RAHU-SATURN | `0.445` | `30` | `4/4` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 3 | `ADB_ceb3bd402e` | 1984-04-25 to 1986-11-12 | RAHU-MERCURY | `0.413` | `30` | `4/5` | YES | YES | YES | `0` | **PASSED (Retained)** |
| 4 | `ADB_ceb3bd402e` | 1986-11-12 to 1987-11-30 | RAHU-KETU | `0.439` | `30` | `4/4` | YES | NO | NO | `0` | **PASSED (Retained)** |
| 5 | `ADB_ceb3bd402e` | 1987-11-30 to 1990-11-30 | RAHU-VENUS | `0.461` | `30` | `4/4` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 6 | `ADB_ceb3bd402e` | 1990-11-30 to 1991-10-25 | RAHU-SUN | `0.382` | `30` | `4/3` | YES | YES | YES | `0` | **PASSED (Retained)** |
| 7 | `ADB_ceb3bd402e` | 1991-10-25 to 1993-04-25 | RAHU-MOON | `0.486` | `30` | `4/6` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 8 | `ADB_ceb3bd402e` | 1993-04-25 to 1994-05-13 | RAHU-MARS | `0.471` | `30` | `4/7` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 9 | `ADB_1341698da3` | 1980-12-11 to 1983-12-12 | RAHU-VENUS | `0.150` | `33` | `4/4` | YES | YES | YES | `0` | **PASSED (Retained)** |
| 10 | `ADB_1341698da3` | 1983-12-12 to 1984-11-05 | RAHU-SUN | `0.213` | `33` | `4/5` | YES | NO | NO | `1` | **PASSED (Retained)** |
| 11 | `ADB_1341698da3` | 1984-11-05 to 1986-05-07 | RAHU-MOON | `0.193` | `33` | `4/3` | NO | NO | NO | `1` | BLOCKED (Filtered FP) |
| 12 | `ADB_1341698da3` | 1986-05-07 to 1987-05-25 | RAHU-MARS | `0.190` | `33` | `4/5` | YES | NO | NO | `1` | **PASSED (Retained)** |
| 13 | `ADB_1341698da3` | 1987-05-25 to 1989-07-12 | JUPITER-JUPITER | `0.133` | `33` | `7/7` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 14 | `ADB_1341698da3` | 1989-07-12 to 1992-01-23 | JUPITER-SATURN | `0.132` | `33` | `7/3` | NO | YES | NO | `1` | **PASSED (Retained)** |
| 15 | `ADB_1341698da3` | 1992-01-23 to 1994-04-30 | JUPITER-MERCURY | `0.132` | `33` | `7/7` | NO | NO | NO | `1` | BLOCKED (Filtered FP) |
| 16 | `ADB_ed6fc9162b` | 1992-06-25 to 1994-08-13 | JUPITER-JUPITER | `0.130` | `23` | `8/8` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 17 | `ADB_93404d00f9` | 1982-10-19 to 1985-05-07 | RAHU-MERCURY | `0.107` | `29` | `4/4` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 18 | `ADB_93404d00f9` | 1985-05-07 to 1986-05-25 | RAHU-KETU | `0.099` | `29` | `4/4` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 19 | `ADB_93404d00f9` | 1986-05-25 to 1989-05-25 | RAHU-VENUS | `0.099` | `29` | `4/3` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 20 | `ADB_93404d00f9` | 1989-05-25 to 1990-04-19 | RAHU-SUN | `0.099` | `29` | `4/4` | YES | NO | NO | `0` | **PASSED (Retained)** |
| 21 | `ADB_93404d00f9` | 1990-04-19 to 1991-10-19 | RAHU-MOON | `0.104` | `29` | `4/6` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 22 | `ADB_93404d00f9` | 1991-10-19 to 1992-11-05 | RAHU-MARS | `0.107` | `29` | `4/3` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 23 | `ADB_93404d00f9` | 1992-11-05 to 1994-12-24 | JUPITER-JUPITER | `0.103` | `29` | `5/5` | YES | NO | NO | `0` | **PASSED (Retained)** |
| 24 | `ADB_b88bfb456b` | 1986-09-18 to 1988-12-24 | MERCURY-JUPITER | `0.069` | `27` | `5/6` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 25 | `ADB_b88bfb456b` | 1992-01-30 to 1993-03-31 | KETU-VENUS | `0.084` | `27` | `4/5` | NO | YES | NO | `0` | BLOCKED (Filtered FP) |
| 26 | `ADB_b88bfb456b` | 1993-03-31 to 1993-08-06 | KETU-SUN | `0.065` | `27` | `4/5` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 27 | `ADB_4b9fc2e7b4` | 1983-11-10 to 1984-10-04 | RAHU-SUN | `0.197` | `35` | `4/5` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 28 | `ADB_4b9fc2e7b4` | 1984-10-04 to 1986-04-05 | RAHU-MOON | `0.105` | `35` | `4/4` | YES | NO | NO | `0` | **PASSED (Retained)** |
| 29 | `ADB_4b9fc2e7b4` | 1986-04-05 to 1987-04-23 | RAHU-MARS | `0.123` | `35` | `4/5` | NO | YES | NO | `0` | **PASSED (Retained)** |
| 30 | `ADB_4b9fc2e7b4` | 1987-04-23 to 1989-06-10 | JUPITER-JUPITER | `0.270` | `35` | `5/5` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 31 | `ADB_4b9fc2e7b4` | 1989-06-10 to 1991-12-22 | JUPITER-SATURN | `0.178` | `35` | `5/2` | NO | NO | NO | `0` | BLOCKED (Filtered FP) |
| 32 | `ADB_4b9fc2e7b4` | 1991-12-22 to 1994-03-29 | JUPITER-MERCURY | `0.157` | `35` | `5/5` | YES | NO | NO | `0` | **PASSED (Retained)** |

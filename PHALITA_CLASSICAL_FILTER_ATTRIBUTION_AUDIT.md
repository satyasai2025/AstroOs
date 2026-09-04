# PHALITA CLASSICAL FILTER ATTRIBUTION AUDIT

**Benchmark Corpus:** AstroDatabank Rodden AA/A Cohort (15-Year Prospective Horizon 1980–1995)  
**Domain:** `CAREER` | **Operating Threshold:** `P >= 0.0600` | **Total Ground-Truth Events:** `5`  

---

## 1. Master Comparative Metric Summary

| Metric Layer | Total Predictions | True Positives (TP) | False Positives (FP) | Precision | Recall | F1-Score | Wilson 95% CI (Precision) |
|---|---|---|---|---|---|---|---|
| **1. Raw Neural MoE** | `39` | `5` | `34` | `12.82%` | `100.00%` | `0.2273` | `[0.0560, 0.2671]` |
| **2. Classical Filter (WITHOUT 10th Lord)** | `19` | `3` | `16` | `15.79%` | `60.00%` | `0.2500` | `[0.0552, 0.3757]` |
| **3. Classical Filter (WITH 10th Lord)** | `29` | `4` | `25` | `13.79%` | `80.00%` | `0.2353` | `[0.0550, 0.3056]` |

---

## 2. Complete Trade-Off & Statistical Changes

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   CLASSICAL FILTER TP / FP TRADE-OFF AUDIT                             │
├─────────────────────────────────────┬──────────────────────────┬───────────────────────┤
│ Evaluation Factor                   │ WITHOUT 10th Lord        │ WITH 10th Lord        │
├─────────────────────────────────────┼──────────────────────────┼───────────────────────┤
│ False Positive Reduction %          │ -52.9% (18 FPs eliminated) │ -26.5% (9 FPs eliminated) │
│ True Positive Retention %           │ 60.0% (3/5 retained)         │ 80.0% (4/5 retained)        │
│ Precision Change (Delta)            │ +2.97% (12.82% -> 15.79%) │ +0.97% (12.82% -> 13.79%)│
│ Recall Change (Delta)               │ -40.00% (100.00% -> 60.00%)  │ -20.00% (100.00% -> 80.00%) │
│ F1-Score Change (Delta)             │ +0.0227 (0.2273 -> 0.2500)     │ +0.0080 (0.2273 -> 0.2353)    │
└─────────────────────────────────────┴──────────────────────────┴───────────────────────┘
```

---

## 3. Full Ground-Truth True Positive (TP) Audit

Here is the exact accounting of all **5 Ground-Truth Events** in the 1980–1995 prospective window:

| # | Subject ID | Prediction Window | Dasha (MD-AD) | Prob | SAV (10H) | BAV (MD/AD) | 10H Aspect (J/S) | 10L Aspect (J/S) | Filter WITHOUT 10L | Filter WITH 10L | Accounting Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | `ADB_1341698da3` | 1983-12-12 to 1984-11-05 | RAHU-SUN | `0.188` | `33` | `4/5` | `Y/N` | `N/Y` | **RETAINED** | **RETAINED** | **Retained in Both** |
| 10 | `ADB_1341698da3` | 1984-11-05 to 1986-05-07 | RAHU-MOON | `0.169` | `33` | `4/3` | `N/N` | `Y/Y` | ❌ FILTERED OUT | **RETAINED** | **Recovered by 10th Lord** |
| 11 | `ADB_1341698da3` | 1986-05-07 to 1987-05-25 | RAHU-MARS | `0.169` | `33` | `4/5` | `Y/N` | `N/N` | **RETAINED** | **RETAINED** | **Retained in Both** |
| 13 | `ADB_1341698da3` | 1989-07-12 to 1992-01-23 | JUPITER-SATURN | `0.152` | `33` | `7/3` | `N/Y` | `Y/N` | **RETAINED** | **RETAINED** | **Retained in Both** |
| 14 | `ADB_1341698da3` | 1992-01-23 to 1994-04-30 | JUPITER-MERCURY | `0.152` | `33` | `7/7` | `N/N` | `N/N` | ❌ FILTERED OUT | ❌ FILTERED OUT | **Suppressed** |

---

## 4. Elimination Breakdown by Specific Filter Mechanism

### Eliminations under Filter WITHOUT 10th Lord:
- **Window #4** (`ADB_ceb3bd402e`, RAHU-VENUS, P=0.434, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava`
- **Window #10** (`ADB_1341698da3`, RAHU-MOON, P=0.169, Label=1): TRUE POSITIVE (Error: Suppressed) -> **Elimination Reason:** `BAV=4/3<4; No Jup/Sat on 10th Bhava; Dasha Geom 12H`
- **Window #14** (`ADB_1341698da3`, JUPITER-MERCURY, P=0.152, Label=1): TRUE POSITIVE (Error: Suppressed) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`
- **Window #15** (`ADB_ed6fc9162b`, JUPITER-JUPITER, P=0.267, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=23<28; No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`
- **Window #17** (`ADB_93404d00f9`, RAHU-KETU, P=0.108, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava`
- **Window #18** (`ADB_93404d00f9`, RAHU-VENUS, P=0.106, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `BAV=4/3<4; No Jup/Sat on 10th Bhava; Dasha Geom 8H`
- **Window #23** (`ADB_b88bfb456b`, MERCURY-SUN, P=0.065, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; No Jup/Sat on 10th Bhava; Dasha Geom 2H`
- **Window #24** (`ADB_b88bfb456b`, MERCURY-MOON, P=0.066, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #25** (`ADB_b88bfb456b`, MERCURY-MARS, P=0.065, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; BAV=5/2<4`
- **Window #26** (`ADB_b88bfb456b`, MERCURY-RAHU, P=0.064, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #27** (`ADB_b88bfb456b`, MERCURY-JUPITER, P=0.098, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; No Jup/Sat on 10th Bhava`
- **Window #28** (`ADB_b88bfb456b`, KETU-KETU, P=0.075, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #29** (`ADB_b88bfb456b`, KETU-VENUS, P=0.105, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #30** (`ADB_b88bfb456b`, KETU-SUN, P=0.096, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; No Jup/Sat on 10th Bhava`
- **Window #31** (`ADB_b88bfb456b`, KETU-MOON, P=0.065, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; Dasha Geom 6H`
- **Window #32** (`ADB_b88bfb456b`, KETU-MARS, P=0.077, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; BAV=4/2<4`
- **Window #33** (`ADB_4b9fc2e7b4`, RAHU-VENUS, P=0.098, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava`
- **Window #34** (`ADB_4b9fc2e7b4`, RAHU-SUN, P=0.250, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`
- **Window #37** (`ADB_4b9fc2e7b4`, JUPITER-JUPITER, P=0.356, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava`
- **Window #38** (`ADB_4b9fc2e7b4`, JUPITER-SATURN, P=0.261, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `BAV=5/2<4; No Jup/Sat on 10th Bhava`

### Eliminations under Filter WITH 10th Lord:
- **Window #14** (`ADB_1341698da3`, JUPITER-MERCURY, P=0.152, Label=1): TRUE POSITIVE (Error: Suppressed) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`
- **Window #15** (`ADB_ed6fc9162b`, JUPITER-JUPITER, P=0.267, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=23<28; No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`
- **Window #25** (`ADB_b88bfb456b`, MERCURY-MARS, P=0.065, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; BAV=5/2<4`
- **Window #27** (`ADB_b88bfb456b`, MERCURY-JUPITER, P=0.098, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; No Jup/Sat on 10th Bhava`
- **Window #28** (`ADB_b88bfb456b`, KETU-KETU, P=0.075, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #29** (`ADB_b88bfb456b`, KETU-VENUS, P=0.105, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28`
- **Window #30** (`ADB_b88bfb456b`, KETU-SUN, P=0.096, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; No Jup/Sat on 10th Bhava`
- **Window #31** (`ADB_b88bfb456b`, KETU-MOON, P=0.065, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; Dasha Geom 6H`
- **Window #32** (`ADB_b88bfb456b`, KETU-MARS, P=0.077, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `SAV=27<28; BAV=4/2<4`
- **Window #34** (`ADB_4b9fc2e7b4`, RAHU-SUN, P=0.250, Label=0): FALSE POSITIVE (Success: Blocked) -> **Elimination Reason:** `No Jup/Sat on 10th Bhava; No Jup/Sat on 10th Bhava OR 10th Lord`

---

## 5. Objective Evidence-Based Verdict

1. **Does ClassicalFilterEngine Genuinely Improve Precision or Merely Suppress Predictions?**
   - **WITHOUT 10th Lord Condition:** 
     - Eliminates `18` out of `34` False Positives (`52.9%` reduction).
     - **Cost:** Mistakenly suppresses `2` out of `5` True Positives (`40.0%` TP loss, Recall drops from `100.00%` to `60.00%`).
     - Precision increases from `12.82%` to `15.79%` (+2.97%), and F1 moves from `0.2273` to `0.2500`.
     - **Verdict:** Pure 10th-house filtering causes significant sensitivity loss (40% of real events are missed).
   - **WITH 10th Lord Condition:**
     - Eliminates `9` out of `34` False Positives (`26.5%` reduction).
     - **Retention:** Preserves `4` out of `5` True Positives (`80.0%` TP retention, Recall = `80.00%`).
     - Precision is `13.79%` (vs raw `12.82%`), and F1 is `0.2353` (vs raw `0.2273`).
2. **Scientific Conclusion & Accounting Reconciliation:**
   - Classical filters do **not** act as magic silver bullets that cleanly remove 100% of FPs while keeping 100% of TPs.
   - When used as hard binary gates, they cause an explicit trade-off: **every FP filtered carries a non-zero risk of suppressing an edge-case TP** (such as Dasha lords having alternative secondary strength).
   - Therefore, classical Ashtakavarga and Double Transit factors should be integrated as **continuous confluence weight features** within the neural representation rather than rigid post-hoc cutoff gates.

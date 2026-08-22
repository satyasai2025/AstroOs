# Priority 27 — Longitudinal Outcome Tracking Engine

## Summary of Accomplishments

Priority 27 delivers the **Longitudinal Outcome Tracking Engine**, which provides continuous real-world prospective observation recording, chronological time-series monitoring, and dual-mechanism drift diagnosis across $P_{20} \to P_{26}$:

1. **Continuous Real-World Outcome Ingestion**:
   - Ingests chronological real-world event occurrences against prospectively pre-registered and accepted rules.
   - Categorizes outcomes into:
     - `CONFIRMED_HIT`: Event occurred strictly within predicted polymodal timing window.
     - `CONFIRMED_MISS`: Target timing window elapsed with zero event occurrence.
     - `AMBIGUOUS_UNVERIFIED`: Event occurred but timing precision is ambiguous or pending official documentation.
     - `OUTSIDE_WINDOW`: Event occurred outside the predicted temporal interval.

2. **Dual-Mechanism Drift & Degradation Architecture**:
   - Explicitly separates population distribution drift from statistical performance degradation:
     - **Mechanism 1: Population Distribution Drift (PSI)**:
       $$\text{PSI} = \sum_{b=1}^{K} (Actual_b - Expected_b) \times \ln\left(\frac{Actual_b}{Expected_b}\right)$$
       - $\text{PSI} < 0.10 \implies \text{STABLE\_CONGRUENT}$
       - $0.10 \le \text{PSI} < 0.25 \implies \text{MILD\_DRIFT\_MONITOR}$
       - $\text{PSI} \ge 0.25 \implies \text{CRITICAL\_DEGRADATION\_TRIGGER}$
     - **Mechanism 2: Formal Statistical Degradation Test**:
       - Two-proportion Z-test comparing longitudinal rolling hit rate against prospective baseline:
         $$p_{\text{pooled}} = \frac{k_{\text{baseline}} + k_{\text{longitudinal}}}{N_{\text{baseline}} + N_{\text{longitudinal}}}$$
         $$SE = \sqrt{p_{\text{pooled}} (1 - p_{\text{pooled}}) \left(\frac{1}{N_{\text{baseline}}} + \frac{1}{N_{\text{longitudinal}}}\right)}$$
         $$Z = \frac{\hat{p}_{\text{longitudinal}} - \hat{p}_{\text{baseline}}}{SE}$$
         $$p_{\text{degradation}} = \Phi(Z) \quad (\text{one-tailed lower CDF})$$
       - Flags `is_degradation_statistically_significant` only when $p_{\text{degradation}} < 0.05$ with negative delta $\Delta < 0$.

3. **Chronological Time-Series Monitoring**:
   - Computes rolling hit rates, sample counts $N$, rolling Brier calibration scores, and interval PSIs across discrete quarters ($2026\text{-Q1}, 2026\text{-Q2}$).

4. **Lineage & Non-Causal Epistemic Guardrails**:
   - Retains $P_{11}$ snapshot provenance SHA-256 hashes and emits strict `LONGITUDINAL_TRACKING_ONLY` observational declarations.

5. **Interactive UI Studio & REST Endpoints**:
   - Studio: [`apps/web/src/app/research/longitudinal-tracking/page.tsx`](file:///apps/web/src/app/research/longitudinal-tracking/page.tsx)
   - Component: [`apps/web/src/components/research/ResearchLongitudinalTrackingStudio.tsx`](file:///apps/web/src/components/research/ResearchLongitudinalTrackingStudio.tsx)
   - REST Router: [`apps/api/routers/longitudinal_tracking.py`](file:///apps/api/routers/longitudinal_tracking.py)

---

## Complete Mandatory Verification Gate Matrix

| Verification Gate | Exact Shell Command | Empirical Output | Status |
| :--- | :--- | :--- | :---: |
| **P27 Focused Pytest Suite** | `.venv\Scripts\pytest apps/api/tests/unit/test_priority27_longitudinal_tracking.py -s -v` | **3 passed** in 0.65s | **PASS** |
| **Dedicated P1–P27 Pipeline** | `.venv\Scripts\pytest apps/api/tests/unit/test_unified_p1_to_p27_pipeline.py -s -v` | **1 passed** ($P_1 \to P_{27}$) in 0.62s | **PASS** |
| **Continuous Unified Pipelines ($P_{15} \to P_{27}$)** | `pytest apps/api/tests/unit/test_unified_p1_to_p*.py -s -v` | **13 passed (100%)** in 3.63s | **PASS** |
| **Frontend Strict Typecheck** | `pnpm --filter @workspace/web typecheck` | **0 errors (Exit Code 0)** | **PASS** |
| **Desktop Packaging Build** | `pnpm --filter @workspace/desktop build` | **Built in 713ms (Exit Code 0)** | **PASS** |
| **Playwright E2E Suite ($P_{22} \to P_{27}$)** | `playwright test e2e/priority22_reproducibility.spec.ts ... e2e/priority27_longitudinal_tracking.spec.ts` | **6 passed (100%)** in 21.9s | **PASS** |

---

## Continuous P1 $\to$ P27 End-to-End Pipeline Execution Log

```text
apps\api\tests\unit\test_unified_p1_to_p27_pipeline.py 
[OK] [P1] Ephemeris calculation verified.
[OK] [P2] HoroscopeEngine D1 generation verified.
[OK] [P3] DivisionalEngine D9 & D10 charts verified.
[OK] [P4] AshtakavargaEngine 337 Sarvashtakavarga bindu sum verified.
[OK] [P5] YogaEngine evaluated 70 yogas (14 active).
[OK] [P6] DashaEngine Vimshottari & Yogini cycles verified.
[OK] [P7] TransitEngine planetary transits over natal chart verified (9 planets).
[OK] [P8] PredictionOrchestrator evaluated 2 slices (0 candidate windows).
[OK] [P9] AstroDSL expression evaluated (is_satisfied: False, latency: 0.01ms).
[OK] [P10] CalibrationEngine candidate activated (Audit logs: 26).
[OK] [P11] Experiment Studio container created with SHA-256 frozen snapshot 'snap-168e102c'.
[OK] [P12] MultiDashaConfluenceEngine generated 26 polymodal timing window(s).
[OK] [P13] SynastryEngine Ashta-Kuta score 28.0/36.0 with 157 joint timing window(s).
[OK] [P14] RectificationEngine evaluated 7 candidates, best offset: -60s.
[OK] [P15] CohortValidationEngine evaluated N=250, ROC-AUC=1.000, p-value=0.01961 (CONFIRMED).
[OK] [P16] EvidenceIntelligenceEngine dynamically synthesized 4 techniques (2 Grade-A, 2 Synergies).
[OK] [P17] PredictionExplainabilityEngine decomposed 5 atomic factors (100.0% sum attribution) with 3 recalculation counterfactuals.
[OK] [P18] BatchResearchOptimizer evaluated N=500 (20000.0 charts/sec, 2 SHA-256 checkpoints).
[OK] [P19] HypothesisMiningEngine evaluated 500 combinations (2 REPLICATED_VALIDATED, top lift: 1.60x).
[OK] [P20] ProspectiveValidationEngine evaluated N=150 (ROC-AUC: 0.895, Status: PROSPECTIVELY_SUPPORTED).
[OK] [P21] ResearchDataGovernanceEngine verified 4 datasets and executed BM_BALA (100.0% accuracy).
[OK] [P22] ResearchReproducibilityEngine independently re-executed 'man-p15-marriage' (Status: REPRODUCED, Score: 100.0%, Zero Drift Verified).
[OK] [P23] ResearchDecisionSynthesisEngine synthesized conclusion 'conc-a53419d3' (Confidence: 91.5%, Tier: TIER_1_PUBLICATION_GRADE, Lineage P1->P22: 100% Intact).
[OK] [P24] ResearchKnowledgeGraphEngine built graph 'rkg-4b139aae' (17 nodes, 10 edges, 100% Non-Causal Verified).
[OK] [P25] ResearchDecisionActionEngine evaluated action verdict 'ACCEPT' (Readiness: 96.4%, Level: LEVEL_1_PRODUCTION_READY).
[OK] [P26] ResearchPortfolioPlannerEngine ranked 4 candidates (Top Score: 81.9, Budget: 5000 charts, Provenance: 2a6b11f62bcd3644).
[OK] [P27] LongitudinalTrackingEngine tracked 50 subjects (Hit Rate: 87.8%, PSI: 0.041, Degradation p: 0.6226, Status: STABLE_CONGRUENT).

=======================================================
ALL P1 -> P27 CONTINUOUS PIPELINE TESTS PASSED 100%!
=======================================================
```

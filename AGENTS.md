# AstroOS — AI System Instructions & Core Memory (AGENTS.md)

> [!CRITICAL]
> **MANDATORY DIRECTIVE ON ASTROLOGICAL & MATHEMATICAL ACCURACY**
> The user is building software for real-world life guidance and national mundane analysis and does NOT manually cross-check astrological calculations. As the AI pair programmer, you bear full responsibility for 100% mathematical, astronomical, and Siddhantic precision. Never guess, never use heuristic approximations, and never rationalize away anomalies.

---

> [!CAUTION]
> **MANDATORY FRAMEWORK REFERENCE — READ BEFORE ANY JYOTISHA IMPLEMENTATION**
> Before writing ANY astrological calculation, prediction, or MoE code, you MUST first read:
> `docs/JHA_PREDICTION_FRAMEWORK.md`
> This is the single source of truth for Vinay Jha's prediction framework, compiled from all
> 77 canonical source docs. Do NOT rely on AI training data memory for Jyotisha rules.
> Key rules enforced there: 7 Karakas (not 8), Bhavachalita != Rasi, Shadbala = tiebreaker only,
> Transit = trigger not promise, Bhrigu Bindu is NOT Jha's framework.

## 1. Jyotisha Siddhanta & Astronomical Calculation Rules

### A. Lunisolar Year & Chaitra Shukla Pratipada (Samvatsararambha)
1. **Root-Finding Precision:** The start of the lunisolar year (*Chaitra Shukla Pratipada*) is strictly defined as the exact moment of the **first astronomical Sun-Moon conjunction** ($0^\circ$ difference) occurring in late sidereal Pisces (*Meena*, $\approx 330^\circ - 360^\circ$) before or as the Sun approaches sidereal Aries (*Mesha*, $0^\circ$).
2. **Handling Adhika Masa (Leap Month):**
   - When a lunar month occurs with no solar ingress (*Asankranti Masa*), this is an **Adhika Masa**.
   - For **Medini / Planetary Cabinet / Civil Samvatsara**, the year begins on **Prathama (First) Chaitra Shukla Pratipada** (e.g. March 19, 2026, Thursday $\rightarrow$ **Jupiter / Guru as King**).
   - Never skip the first conjunction by scanning arbitrary date ranges or using minimum-distance heuristics across wide multi-week windows.
   - Always document both the civil *Prathama Chaitra* and the *Nija Chaitra* when an Adhika Masa occurs.

### B. Planetary Cabinet (Nava Nayakas) Architecture
1. **Raja (King):** Lord of the weekday of **Chaitra Shukla Pratipada** at sunrise (*Udaya-Tithi*).
2. **Mantri (Prime Minister):** Lord of the weekday when the Sun enters sidereal Aries ($0^\circ$ Mesha Sankranti).
3. **Senadhipati (Defense):** Lord of the weekday of *Simha Sankranti* ($120^\circ$).
4. **Sasyeshadhipati (Kharif Agriculture):** Lord of the weekday of *Karka Sankranti* ($90^\circ$).
5. **Dhanyadhipati (Rabi Agriculture):** Lord of the weekday of *Dhanu Sankranti* ($240^\circ$).
6. **Arghyadhipati (Prices & Liquidity):** Lord of the weekday of *Mithuna Sankranti* ($60^\circ$).
7. **Meghadhipati (Clouds & Monsoon):** Lord of the weekday of *Aridra Pravesha* ($66.6667^\circ$).
8. **Raseshadhipati (Liquids & Petroleum):** Lord of the weekday of *Tula Sankranti* ($180^\circ$).
9. **Nireshadhipati (Metals & Minerals):** Lord of the weekday of *Makara Sankranti* ($270^\circ$).

---

## 2. Mandatory Verification & Validation Protocol

Whenever any calculation, backend service, router, or UI view is modified:
1. **Check the Raw Ephemeris Coordinates:** Calculate exact Sun and Moon sidereal longitudes at the exact timestamps.
2. **Verify Weekdays & Sunrise:** Calculate the exact solar weekday at the location of interest (or UTC/IST sunrise).
3. **Enforce Unit Tests:** Ensure automated unit tests cover edge cases (e.g. Adhika Masa years like 2026, 2023, 2020, 2018) with strict assertions against established classical Panchangs (*Rashtriya Panchang*, *Kashi Panchang*).
4. **Zero Handwaving:** If a discrepancy is reported by the user, immediately audit the underlying root-finding equations and astronomical data first.

---

## 3. Core System & Architectural Invariants (Mandatory User Directives)

1. **Zero Mock / Fabricated Data:**
   - Never use fake outcomes, placeholder arrays, or synthetic datasets disguised as real historical findings.
   - All empirical metrics and validation reports must strictly reflect authentic, source-verified data.

2. **Single Source of Truth Calculation Engines (No Duplication):**
   - Never write duplicate, inline, or competing calculation logic across routers or frontend components.
   - All views and services must consume the single, verified calculation engines listed in `FROZEN_MODULES.md`.

3. **Clean, Non-Redundant UI Architecture:**
   - Zero duplicate action buttons, conflicting modal triggers, or redundant layout controls.
   - Every interactive element must have a single, unambiguous purpose.

4. **Universal Active / Default Chart Synchronization:**
   - Birth charts must strictly originate from the official `create chart` workflow.
   - **Cross-Page State Sync:** Navigating to any page/view across the platform MUST automatically inherit and evaluate the system-wide default/active birth chart, unless the user is explicitly working within the isolated research studio as a researcher.

5. **100% Scientific Honesty & Zero False Claims:**
   - Never exaggerate model performance or fabricate predictive certainty.
   - Present exact statistical metrics (PR-AUC, ROC-AUC, Brier score, Wilson CIs) and classical Shastric evidence honestly regardless of outcome.

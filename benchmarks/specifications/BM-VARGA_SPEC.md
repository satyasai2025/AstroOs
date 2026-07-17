# BM-VARGA — Divisional Chart Calculation Benchmarks (Master Specification)

> **Benchmark Family:** BM-VARGA
> **Version:** 1.1.0
> **Status:** ✅ ACCEPTED (2026-07-16)
> **Owner:** Chief QA & Benchmark Architect (Agent 4)
> **Date:** 2026-07-16
> **Part Of:** Phase A — Foundation & Reference

---

## 1. Identification

| Field | Value |
|-------|-------|
| **Family ID** | `BM-VARGA` |
| **Full Title** | Divisional (Varga) Chart Calculation Benchmarks |
| **AstroOS Modules Tested** | M6 — Divisional Charts (`DivisionalEngine`, `compute_varga_sign`, `_VARGA_CALCULATOR`) |
| **Source Code** | `apps/api/services/divisional_engine.py`, `apps/api/domain/divisional.py`, `apps/api/schemas/divisional.py`, `apps/api/routers/divisional.py` |
| **Depends On** | BM-CALC (D1 planet positions), BM-HOUSE (D1 lagna/house context) |
| **Required By** | BM-BALA (Saptavargaja Bala, Ojayugmarasyamsa Bala), BM-YOGA (varga-based yoga conditions), BM-RULE (varga-conditioned rules) |

---

## 2. Purpose & Scope

**Purpose:**
Verify that AstroOS correctly computes all 15 supported divisional (varga) charts — D2 through D60 — from a natal (D1) chart. Each varga applies a distinct classical partition rule (per Parashara) to a planet's D1 sidereal longitude to derive a varga sign, degree, and house placement. Because most varga formulas are non-uniform or use quality/element-based starting-sign tables (rather than the simple `(sign × N + part) % 12` formula that only holds for D9), each varga is a distinct algorithm with its own failure modes. This benchmark family is the correctness gate for the entire divisional-chart subsystem, which underlies dignity assessment, Shadbala (Saptavargaja Bala), and every downstream yoga/rule that inspects a specific varga.

**Category:** Calculation Accuracy
**Difficulty:** FOUNDATION → INTERMEDIATE (D9, D30, D60 are ADVANCED due to non-trivial partition rules)
**Risk if Failed:** Incorrect varga sign/house placement silently corrupts dignity assessment, Saptavargaja Bala, and every yoga or rule conditioned on a divisional chart — errors are not visible in the D1 chart and are easy to miss without a dedicated benchmark.

**Related Benchmarks:**
- Depends on: BM-CALC (D1 sidereal longitudes), BM-HOUSE (D1 lagna for house-from-varga-lagna context)
- Required by: BM-BALA (§ Saptavargaja Bala uses D1/D2/D3/D7/D9/D12/D30), BM-YOGA (Vargottama and varga-conditioned yogas), BM-RULE

**Test ID Convention:**

```
BM-VARGA-{VARGA}-{NNN}   — per-varga, per-chart position/house/dignity test
BM-VARGA-EDGE-{NNN}      — cross-varga invariant / boundary test
```

Example: `BM-VARGA-D9-003` = Navamsha test against reference chart GC-REF-003.

---

## 3. Common Test Framework

The 15 vargas share one input pipeline, one dignity reference system, and one validation methodology. This section defines what is common; §5 defines what differs per varga.

### 3.1 Reference Charts

All 15 vargas are tested against the same 5 charts from **GC-MASTER** (see [GC-MASTER-design.md](../datasets/GC-MASTER-design.md)), the same golden dataset used by BM-CALC and BM-HOUSE:

| Chart ID | Confidence | Notes |
|----------|-----------|-------|
| GC-REF-001 | Tier A | Diverse D1 sign distribution across grahas |
| GC-REF-002 | Tier A | Includes near-boundary D1 degrees (tests part-boundary rounding) |
| GC-REF-003 | Tier B | Southern/tropical geography — house-from-lagna cross-check |
| GC-REF-004 | Tier B | Includes at least one graha near 0° and near 29.99° (part-boundary stress) |
| GC-REF-005 | Tier B | Includes retrograde graha(s) — verifies varga placement is independent of retrograde status |

**Coverage requirement:** across the 5 charts × 9 grahas (45 D1 positions), every sign quality (movable/fixed/dual), sign parity (odd/even), and element (fire/earth/air/water) must appear at least twice, so that every starting-sign branch in every varga formula (§5) is exercised at least once. If GC-MASTER's 5 charts do not achieve this, a 6th synthetic chart (`SY-VARGA-COVERAGE-001`) with deliberately chosen D1 longitudes must be added — synthetic, Tier C.

### 3.2 Dataset Requirements

| Requirement | Detail |
|-------------|--------|
| D1 sidereal longitudes | Must be BM-CALC-verified (Tier A/B) before use as varga input — a varga computed from an unverified D1 position is not verifiable |
| D1 lagna | Must be BM-HOUSE-verified (Whole Sign) — varga house numbering is `((varga_rashi_index − varga_lagna_rashi_index) mod 12) + 1`, so the D1 lagna error propagates into every varga house |
| Ayanamsa | Lahiri (primary) — same as BM-CALC/BM-HOUSE default; varga formulas are ayanamsa-agnostic (they operate on sidereal longitude, whichever ayanamsa produced it) so no separate ayanamsa sweep is required for BM-VARGA itself |
| Expected varga outputs | Derived analytically by applying the formulas in §5 to BM-CALC-verified D1 longitudes — **not** an independent ephemeris query, since varga partition is deterministic arithmetic on D1 data, not a new celestial computation |
| Part-boundary fixtures | For every varga, at least one synthetic longitude placed exactly on a part boundary (e.g., D9 part boundary at 3.333...°) to test rounding/floor behavior deterministically |

### 3.3 Dignity Reference Tables

"Expected dignities" (§5, per varga) are evaluated by mapping the **varga rashi** occupied by each graha against the classical dignity tables below (Brihat Parashara Hora Shastra, Ch. 3–5). These tables are shared across all 15 vargas; only D30 has a documented exception (§5.12).

| Graha | Own Sign(s) (Swakshetra) | Moolatrikona | Exaltation (Uccha) | Debilitation (Neecha) |
|-------|---------------------------|--------------|---------------------|------------------------|
| Sun | Leo | Leo 0–20° | Aries 10° | Libra 10° |
| Moon | Cancer | Taurus 3–30° | Taurus 3° | Scorpio 3° |
| Mars | Aries, Scorpio | Aries 0–12° | Capricorn 28° | Cancer 28° |
| Mercury | Gemini, Virgo | Virgo 15–20° | Virgo 15° | Pisces 15° |
| Jupiter | Sagittarius, Pisces | Sagittarius 0–10° | Cancer 5° | Capricorn 5° |
| Venus | Taurus, Libra | Libra 0–15° | Pisces 27° | Virgo 27° |
| Saturn | Capricorn, Aquarius | Aquarius 0–20° | Libra 20° | Aries 20° |
| Rahu | *(no classical own sign)* | — | Taurus\* | Scorpio\* |
| Ketu | *(no classical own sign)* | — | Scorpio\* | Taurus\* |

\* Rahu/Ketu exaltation-debilitation signs are tradition-dependent (some schools use Gemini/Sagittarius). Benchmark treats these as **SOFT** criteria only (§3.5), never HARD, and documents which tradition is authoritative in `Known Limitations` (§10).

**Dignity precedence when a varga rashi degree falls in a moolatrikona range that overlaps an own sign:** Moolatrikona > Own Sign > Neutral/Enemy/Friend sign, per BPHS.

### 3.4 Validation Methodology

Because varga computation is pure deterministic arithmetic on already-verified D1 longitudes (no new ephemeris call), validation is **algorithmic/invariant-based**, not tolerance-based:

| Validation Layer | Method |
|-------------------|--------|
| **Formula conformance** | Re-implement each varga's classical formula independently (in the benchmark harness, not reusing `divisional_engine.py`) and assert exact agreement with the engine's output — an independent-implementation cross-check, not a self-comparison |
| **Boundary behavior** | Part-boundary fixtures (§3.2) must assign the boundary degree to the correct side per a documented floor/ceiling convention (AstroOS uses `int(deg / part_size)`, i.e., floor, with the last part clamped) |
| **House derivation** | `varga_house_number` must equal `((varga_rashi_index − varga_lagna_rashi_index) mod 12) + 1` exactly, for every graha in every chart |
| **Dignity derivation** | Cross-reference varga rashi against §3.3 tables; must match exactly |
| **Determinism** | Same D1 input → same varga output (content hash match), identical convention to BM-CALC/BM-HOUSE |
| **D30 special case** | Independently verify that Sun and Moon's D30 varga rashi equals their D1 rashi exactly (Parashara's stated exception — no Trimshamsha for luminaries) |

### 3.5 Accuracy Metrics

| Metric | Target | Class |
|--------|--------|-------|
| Varga rashi assignment (all vargas, all grahas) | 100% exact match | HARD |
| Varga rashi degree (`varga_rashi_degree`) | ±0.0001° (rounding-only tolerance; formula is exact) | HARD |
| Varga house number | 100% exact match | HARD |
| Dignity classification (own/exalted/debilitated/moolatrikona, non-Rahu/Ketu) | 100% exact match | HARD |
| Rahu/Ketu dignity classification | ≥ 95% agreement with declared tradition | SOFT |
| Part-boundary assignment | 100% exact match to documented floor convention | HARD |
| Determinism (repeat-run hash match) | 100% | HARD |

### 3.6 Confidence Classification

| Tier | Label | Applicable To |
|------|-------|---------------|
| **A** | VERIFIED | Formula conformance (mathematically exact, independently re-derivable), house derivation, dignity tables (BPHS canonical) |
| **B** | ESTIMATED | D30's non-uniform partition boundaries (Parashara's exact degree cutoffs have minor cross-text variance — see §10) |
| **C** | SYNTHETIC | Part-boundary stress fixtures, SY-VARGA-COVERAGE-001 |
| **D** | UNKNOWN | Rahu/Ketu exaltation/debilitation sign (tradition-dependent, no single classical consensus) |

---

## 4. AstroOS Module Reference

| Component | File | Role |
|-----------|------|------|
| `SUPPORTED_VARGAS` | `apps/api/services/divisional_engine.py:48` | Divisor lookup for all 15 vargas |
| `_VARGA_CALCULATOR` | `apps/api/services/divisional_engine.py:366` | Dispatch table: varga code → partition function |
| `compute_varga_sign()` | `apps/api/services/divisional_engine.py:387` | Public entry point: D1 sidereal longitude → (varga_rashi, varga_rashi_degree) |
| `DivisionalEngine.compute()` / `.compute_all()` | `apps/api/services/divisional_engine.py:441,481` | Full chart assembly (ascendant + 9 grahas) per varga |
| `VargaChart`, `VargaPosition`, `VargaAscendant` | `apps/api/domain/divisional.py` | Frozen dataclasses — benchmark output schema baseline |
| Divisional API | `apps/api/routers/divisional.py` | HTTP surface exercised by BM-API (out of scope here) |

---

## 5. Per-Varga Specifications

Each subsection below defines the 10 required elements: Purpose, Classical References, Reference Charts, Expected Planetary Positions, Expected House Placements, Expected Dignities, Validation Methodology, Dataset Requirements, Accuracy Metrics, Pass/Fail Criteria. Elements identical across all 15 vargas are defined once in §3 and referenced by section number rather than repeated verbatim.

---

### 5.1 D2 — Hora

| Field | Value |
|-------|-------|
| **Purpose** | Validates wealth/prosperity (Dhana) indicator chart — the simplest varga (binary sign space), used as the FOUNDATION-tier smoke test for the whole family |
| **Classical References** | Brihat Parashara Hora Shastra (BPHS), Ch. 6, verses 4–7 (Hora scheme, Sun/Moon hora alternation) |
| **Reference Charts** | §3.1 (all 5 GC-MASTER charts); D2 has only 2 possible output signs (Cancer, Leo), so all 5 charts collectively must produce both signs at least twice each |
| **Expected Planetary Positions** | Odd sign (0-indexed even): first 15° → Leo, second 15° → Cancer. Even sign: first 15° → Cancer, second 15° → Leo. `part_deg = (deg % 15.0) × 2.0`. Formula: `apps/api/services/divisional_engine.py:85` (`_d2_hora`) |
| **Expected House Placements** | Per §3.4 — only 2 distinct varga rashis possible, so varga lagna is always Cancer or Leo; house numbers derive from lagna per the shared formula |
| **Expected Dignities** | D2 dignity is rarely used classically (Hora is evaluated by hora-lord, i.e., Sun-hora vs Moon-hora dominance in the chart, not sign dignity) — benchmark reports sign dignity per §3.3 as SOFT only, and additionally validates hora-lord count (Sun-hora grahas vs Moon-hora grahas) as the primary D2-specific HARD check |
| **Validation Methodology** | §3.4, plus: count of Sun-hora vs Moon-hora placements must sum to 9 (all grahas) |
| **Dataset Requirements** | §3.2; no D2-specific fixture beyond one chart with an odd-sign Sun and one with an even-sign Sun |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: varga rashi ∈ {Cancer, Leo} only, for all grahas in all charts. HARD: hora-lord split sums to 9. HARD: part boundary at exactly 15° D1 degree assigns to the second hora (not first) |

---

### 5.2 D3 — Drekkana

| Field | Value |
|-------|-------|
| **Purpose** | Validates siblings/courage (co-borns, Bhratru) indicator — first non-uniform-offset varga (tests the `[0,4,8]` trine-offset table rather than a continuous formula) |
| **Classical References** | BPHS Ch. 6, verses 8–11 (Drekkana — 1st/5th/9th trine offsets) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 3 parts of 10° each; offsets `[0, 4, 8]` signs from natal. `vdeg = (deg % 10.0) × 3.0`. Formula: `apps/api/services/divisional_engine.py:103` (`_d3_drekkana`). **Note:** this is the offset table variant, not the general `(sign×N+part)%12` formula — explicitly called out in [divisional-varga-rules.md](../../.agents/memory/divisional-varga-rules.md) as a gotcha |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3, standard tables apply directly to the D3 varga rashi |
| **Validation Methodology** | §3.4; independent re-implementation must use the `[0,4,8]` offset table, not the general formula, to catch a regression toward the (incorrect) general formula |
| **Dataset Requirements** | §3.2; boundary fixture at exactly 10.0° and 20.0° D1 degree |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: part 0 → offset 0 signs, part 1 → offset 4 signs, part 2 → offset 8 signs, exactly. HARD: boundary at 10.0°/20.0° assigns to next part (not previous) |

---

### 5.3 D4 — Chaturthamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates fortune/property/mother/happiness (Bhagya, Sukha) indicator — tests successive-kendra offset logic |
| **Classical References** | BPHS Ch. 6, verse 12 (Chaturthamsha — property/fortune, kendra progression) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 4 parts of 7.5° each; offsets `part × 3` signs (same, 4th, 7th, 10th = kendras). `vdeg = (deg % 7.5) × 4.0`. Formula: `apps/api/services/divisional_engine.py:116` (`_d4_chaturthamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4 |
| **Dataset Requirements** | §3.2; boundary fixtures at 7.5°, 15.0°, 22.5° |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: 4 parts map to offsets {0,3,6,9} signs exactly, in order |

---

### 5.4 D7 — Saptamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates children/progeny (Putra) indicator — first varga using odd/even sign parity to choose a starting point (rather than a fixed offset table) |
| **Classical References** | BPHS Ch. 6, verses 13–15 (Saptamsha — progeny, odd/even starting rule) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 7 equal parts of `30/7 ≈ 4.2857°`. Odd sign starts from same sign; even sign starts from 7th sign (offset 6). Formula: `apps/api/services/divisional_engine.py:128` (`_d7_saptamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4; part-size is a repeating decimal (30/7) — independent re-implementation must use the same floating-point part-size to avoid a spurious boundary mismatch near part 6/7 |
| **Dataset Requirements** | §3.2; boundary fixture at `6 × 30/7 = 25.7143°` (last-part edge, prone to float rounding errors) |
| **Accuracy Metrics** | §3.5, with the boundary-fixture tolerance widened to ±0.0005° to absorb float division of 30/7 |
| **Pass/Fail Criteria** | HARD: odd-sign start = same sign; even-sign start = sign+6. HARD: last part (part 6) correctly clamped, no `IndexError`/overflow past 12 signs |

---

### 5.5 D9 — Navamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates spouse/dharma/overall life-strength (the single most important divisional chart in classical practice — "as important as D1"); also the only varga using the general `(sign × N + part) % 12` formula |
| **Classical References** | BPHS Ch. 6, verses 16–20 (Navamsha — foundational status); Saravali Ch. 43 (Navamsha significance) |
| **Reference Charts** | §3.1 — D9 is the highest-priority varga; all 5 charts plus SY-VARGA-COVERAGE-001 if needed |
| **Expected Planetary Positions** | 9 equal parts of `30/9 ≈ 3.3333°`. Formula: `vsign_idx = (sign_index × 9 + part) % 12`. Formula: `apps/api/services/divisional_engine.py:143` (`_d9_navamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3, plus D9-specific **Vargottama** check: a graha is Vargottama if its D9 rashi equals its D1 rashi — this is a HARD D9-specific criterion since Vargottama is a named classical condition consumed downstream by BM-YOGA |
| **Validation Methodology** | §3.4, plus Vargottama cross-check: `d1_rashi == varga_rashi` must be flagged and match an independently computed boolean |
| **Dataset Requirements** | §3.2; at least one GC-MASTER chart must contain a graha in a Vargottama position (fire signs 0–3.33°, 6.67–10°, etc. depending on movable/fixed/dual — if GC-MASTER doesn't naturally contain one, add a synthetic Vargottama fixture) |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: `(sign_index × 9 + part) % 12` matches exactly for all 9 grahas × 5 charts (45 checks). HARD: Vargottama flag matches independent computation for every graha |

---

### 5.6 D10 — Dasamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates career/profession/status (Karma) indicator — heavily used in modern predictive practice |
| **Classical References** | BPHS Ch. 6, verses 21–23 (Dasamsha — profession, odd/even starting rule) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 10 equal 3° parts. Odd sign starts from same sign; even sign starts from 9th sign (offset 8). Formula: `apps/api/services/divisional_engine.py:161` (`_d10_dasamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4 |
| **Dataset Requirements** | §3.2; boundary fixtures at every 3° increment (0,3,6,...,27) |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: odd-sign start = same sign; even-sign start = sign+8, exact |

---

### 5.7 D12 — Dvadashamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates parents (Matru-Pitru) indicator — simplest non-D9 formula (direct `(sign + part) % 12`, no parity/quality branching) |
| **Classical References** | BPHS Ch. 6, verse 24 (Dvadashamsha — parents) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 12 equal 2.5° parts. `vsign_idx = (sign_index + part) % 12`. Formula: `apps/api/services/divisional_engine.py:175` (`_d12_dvadashamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4 — this is the simplest formula in the family; used as a regression canary since a break here likely indicates a systemic dispatch-table or sign-index bug rather than a D12-specific one |
| **Dataset Requirements** | §3.2 |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: `(sign_index + part) % 12` exact for all grahas × charts |

---

### 5.8 D16 — Shodashamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates vehicles, comforts, mental/material happiness (Vahana) indicator — first quality-based (movable/fixed/dual) starting-sign table |
| **Classical References** | BPHS Ch. 6, verse 25 (Shodashamsha — vehicles and comforts) |
| **Reference Charts** | §3.1 — must include at least 2 grahas per sign quality (movable/fixed/dual) across the 5 charts, per §3.1 coverage requirement |
| **Expected Planetary Positions** | 16 equal 1.875° parts. Starting sign by quality: Movable→Aries(0), Fixed→Leo(4), Mutable→Sagittarius(8) (`_D16_START` table). Formula: `apps/api/services/divisional_engine.py:196` (`_d16_shodashamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4; independent re-implementation of the `_D16_START` lookup table is mandatory (not just the arithmetic) since a table-entry typo would not be caught by formula-shape review alone |
| **Dataset Requirements** | §3.2; §3.1 quality-coverage requirement is binding for this varga specifically |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: all 12 signs correctly map to one of {Aries, Leo, Sagittarius} start per `_D16_START`; HARD: part boundary at multiples of 1.875° |

---

### 5.9 D20 — Vimshamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates spiritual life/worship (Upasana) indicator — quality-based starting table with a different sign order than D16 (tests that the two quality-based tables are not accidentally swapped) |
| **Classical References** | BPHS Ch. 6, verse 26 (Vimshamsha — spiritual practice) |
| **Reference Charts** | §3.1, same quality-coverage requirement as D16 |
| **Expected Planetary Positions** | 20 equal 1.5° parts. Movable→Aries(0), Fixed→Sagittarius(8), Dual→Leo(4) (`_D20_START` table — note the Fixed/Dual sign targets are swapped relative to D16's Fixed→Leo, Mutable→Sagittarius). Formula: `apps/api/services/divisional_engine.py:217` (`_d20_vimshamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4, plus an explicit **cross-varga differential test**: for the same D1 sign, assert D16's start sign ≠ D20's start sign for Fixed and Dual qualities (both use Aries for Movable, so that branch is excluded) — this specifically catches a copy-paste error between the two lookup tables, which is the most likely failure mode given their structural similarity |
| **Dataset Requirements** | §3.2 |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: `_D20_START` mapping exact per sign; HARD: differential test vs D16 passes for all Fixed/Dual signs |

---

### 5.10 D24 — Chaturvimshamsha (Siddhamsha)

| Field | Value |
|-------|-------|
| **Purpose** | Validates education/learning (Vidya) indicator — parity-based (odd/even) starting sign, fixed target (Leo/Cancer) rather than a per-sign table |
| **Classical References** | BPHS Ch. 6, verse 27 (Chaturvimshamsha / Siddhamsha — learning and knowledge) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 24 equal 1.25° parts. Odd sign starts from Leo(4); even sign starts from Cancer(3). Formula: `apps/api/services/divisional_engine.py:230` (`_d24_chaturvimshamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4 |
| **Dataset Requirements** | §3.2 |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: odd→Leo start, even→Cancer start, exact for all 12 D1 signs |

---

### 5.11 D27 — Bhamsha (Nakshatramsha)

| Field | Value |
|-------|-------|
| **Purpose** | Validates general strengths/weaknesses (Bala-Abala) indicator — first and only element-based (fire/earth/air/water, 4-way) starting-sign table |
| **Classical References** | BPHS Ch. 6, verse 28 (Bhamsha/Nakshatramsha — strengths and weaknesses by element) |
| **Reference Charts** | §3.1 — must include at least 1 graha per element (fire/earth/air/water) across the 5 charts, extending the §3.1 coverage requirement to 4-way element coverage specifically for D27 |
| **Expected Planetary Positions** | 27 equal parts of `30/27 ≈ 1.1111°`. Fire→Aries(0), Earth→Cancer(3), Air→Libra(6), Water→Capricorn(9) (`_D27_START` table). Formula: `apps/api/services/divisional_engine.py:254` (`_d27_bhamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4; independent re-implementation of `_D27_START`'s 4-way element table |
| **Dataset Requirements** | §3.2, plus 4-element coverage per this subsection |
| **Accuracy Metrics** | §3.5, boundary tolerance widened to ±0.0005° for the repeating-decimal part size (30/27), same rationale as D7 |
| **Pass/Fail Criteria** | HARD: all 12 signs correctly map to one of {Aries, Cancer, Libra, Capricorn} by element, exact; HARD: last part (26) correctly clamped |

---

### 5.12 D30 — Trimshamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates evils/misfortunes/character weaknesses (Arishta) indicator — the only varga with a genuinely **non-equal** partition (5 unequal-width sub-parts per sign) and a documented luminary exception |
| **Classical References** | BPHS Ch. 6, verses 29–34 (Trimshamsha — non-uniform partition; Sun/Moon exception explicitly stated) |
| **Reference Charts** | §3.1, plus mandatory coverage: at least one chart with Sun or Moon positioned to exercise the luminary exception path, and at least one graha landing in each of the 5 sub-part widths (5°/5°/8°/7°/5° odd; 5°/7°/8°/5°/5° even) |
| **Expected Planetary Positions** | Odd sign: 0–5°→Aries(Mars), 5–10°→Aquarius(Saturn), 10–18°→Sagittarius(Jupiter), 18–25°→Gemini(Mercury), 25–30°→Libra(Venus). Even sign: 0–5°→Taurus(Venus), 5–12°→Virgo(Mercury), 12–20°→Pisces(Jupiter), 20–25°→Capricorn(Saturn), 25–30°→Scorpio(Mars). **Exception:** Sun and Moon receive their D1 rashi unchanged — no Trimshamsha applies to luminaries per Parashara. Formula: `apps/api/services/divisional_engine.py:267` (`_d30_trimshamsha`); exception applied at `apps/api/services/divisional_engine.py:654` in `_build_from_result` |
| **Expected House Placements** | §3.4; note that Sun/Moon's D30 house number is computed from their (unchanged) D1-equal rashi relative to the **D30 lagna**, not their D1 house — the lagna itself still undergoes full Trimshamsha partition |
| **Expected Dignities** | §3.3 tables apply to the 7 non-luminary grahas' D30 rashi. For Sun/Moon, dignity is evaluated against their **D1** rashi (since D30 rashi = D1 rashi for luminaries by definition) — this is the one documented deviation from the shared §3.3 methodology flagged in §3.3 |
| **Validation Methodology** | §3.4, plus explicit assertion `sun.varga_rashi == sun.d1_rashi` and `moon.varga_rashi == moon.d1_rashi` for every chart — this exception is the single highest-risk regression point in the whole family (an accidental removal of the `if varga == "D30" and planet in ("sun","moon")` branch would silently produce classically wrong results while still returning syntactically valid data) |
| **Dataset Requirements** | §3.2, plus: sub-part-boundary fixtures at 5°, 10°, 18°, 25° (odd) and 5°, 12°, 20°, 25° (even) — 8 boundary fixtures total, more than any other varga due to the non-uniform partition |
| **Accuracy Metrics** | §3.5, with `varga_rashi_degree` clamped at 29.9999° per the engine's own clamp (`min(vdeg, 29.9999)`) — benchmark must assert the clamp is present, not just that the value is close to 30° |
| **Pass/Fail Criteria** | HARD: all 8 sub-part boundaries assign to the correct side, exact. HARD: Sun/Moon D30 rashi == D1 rashi for 100% of test cases, zero tolerance — any single failure blocks release regardless of all other D30 checks passing |

---

### 5.13 D40 — Khavedamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates auspicious/inauspicious effects and maternal legacy (Matru-vamsha) indicator — parity-based starting sign with fine-grained (0.75°) parts |
| **Classical References** | BPHS Ch. 6, verse 35 (Khavedamsha — general auspiciousness) |
| **Reference Charts** | §3.1 |
| **Expected Planetary Positions** | 40 equal 0.75° parts. Odd sign starts from Aries(0); even sign starts from Libra(6). Formula: `apps/api/services/divisional_engine.py:313` (`_d40_khavedamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4; at 0.75° per part, this and D45/D60 are the highest-resolution vargas — benchmark specifically checks for off-by-one part-index errors near the 39th (last) part |
| **Dataset Requirements** | §3.2; boundary fixture at 29.25° (start of the 40th/last part) |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: odd→Aries start, even→Libra start, exact; HARD: part 39 (last) correctly clamped, no index overflow |

---

### 5.14 D45 — Akshavedamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates general character, conduct, and paternal legacy (Pitru-vamsha) indicator — quality-based starting table at fine (0.6̄°) resolution |
| **Classical References** | BPHS Ch. 6, verse 36 (Akshavedamsha — character and conduct) |
| **Reference Charts** | §3.1, same quality-coverage requirement as D16/D20 |
| **Expected Planetary Positions** | 45 equal parts of `30/45 = 0.6̄°`. Movable→Aries(0), Fixed→Leo(4), Dual→Sagittarius(8) (`_D45_START` table). Formula: `apps/api/services/divisional_engine.py:336` (`_d45_akshavedamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3 |
| **Validation Methodology** | §3.4; **cross-varga differential test** vs D16 (both use Movable→Aries, Fixed→Leo — assert agreement) and vs D20 (Dual target differs: D45 Dual→Sagittarius vs D20 Dual→Leo — assert disagreement) to catch table-copy errors, same rationale as §5.9 |
| **Dataset Requirements** | §3.2 |
| **Accuracy Metrics** | §3.5, boundary tolerance ±0.0005° for the repeating-decimal part size (30/45) |
| **Pass/Fail Criteria** | HARD: `_D45_START` mapping exact; HARD: differential tests vs D16/D20 pass |

---

### 5.15 D60 — Shashtiamsha

| Field | Value |
|-------|-------|
| **Purpose** | Validates overall life results and past-life karma (Sarvartha) — the most detailed and classically authoritative varga after D9 ("give as much weight to D60 as to D1" — BPHS); highest resolution (0.5° parts, 60 divisions) |
| **Classical References** | BPHS Ch. 6, verses 37–40 (Shashtiamsha — supreme subtlety, 60 named amsha deities with individual auspicious/inauspicious character) |
| **Reference Charts** | §3.1 — D60 is second-highest priority after D9; all 5 charts required, SY-VARGA-COVERAGE-001 strongly recommended given 60-way resolution |
| **Expected Planetary Positions** | 60 equal 0.5° parts. Odd sign starts from Aries(0); even sign starts from Libra(6). Formula: `apps/api/services/divisional_engine.py:349` (`_d60_shashtiamsha`) |
| **Expected House Placements** | §3.4 |
| **Expected Dignities** | §3.3, plus (documented as future work, not in v1.0.0 scope) per-amsha deity/auspiciousness labels (Ghora, Rakshasa, Deva, etc. — the 60 named Shashtiamsha deities) are NOT currently computed by `DivisionalEngine` and are therefore out of scope for this benchmark version; flagged in §10 Known Limitations |
| **Validation Methodology** | §3.4; same off-by-one concern as D40/D45 at the highest resolution in the family — part-boundary fixtures are most critical here |
| **Dataset Requirements** | §3.2; boundary fixtures at every 0.5° near sign start/end (0°, 0.5°, 29.5°, 29.9999°) |
| **Accuracy Metrics** | §3.5 |
| **Pass/Fail Criteria** | HARD: odd→Aries start, even→Libra start, exact; HARD: part 59 (last) correctly clamped; HARD: `varga_rashi_degree` for the last part stays within [0, 30) |

---

## 6. Reference Implementations

Every varga is cross-checked against four independent reference points, not just AstroOS's own formula. This is what makes the benchmark a real validation gate rather than a self-consistency check.

### 6.1 Arbitration Order

When sources disagree, resolve in this order — do not treat any software tool as automatically authoritative over the classical text:

1. **Classical source** (BPHS chapter/verse, §5 per varga) — the formula AstroOS *should* implement. Authoritative.
2. **Independent re-implementation** (§3.4) — a from-scratch implementation of the classical formula inside the benchmark harness, not a call into `divisional_engine.py`.
3. **JHora** — Jagannatha Hora (PVR Narasimha Rao), the de facto reference application in the Vedic astrology software community. Closed-source freeware; useful as a widely-trusted cross-check but not inspectable, so a JHora/AstroOS disagreement must first be checked against #1/#2 before assuming AstroOS is wrong.
4. **PyJHora** — the open-source Python reimplementation of JHora's calculations (github.com/naturalstupid/PyJHora). Inspectable, but is itself a third-party reimplementation and can carry its own bugs; treat as corroborating evidence, not a tiebreaker over #1/#2.

**Mandatory pre-check before any cross-tool comparison:** confirm JHora/PyJHora are configured with the same ayanamsa (Lahiri/Chitrapaksha) and the same D1 input (identical birth datetime, lat/lon, timezone) as the AstroOS run. A configuration mismatch produces a false "calculation" failure that is actually an input mismatch — see Known Failure Mode FM-6 (§9).

### 6.2 Per-Varga Reference Matrix

| Varga | Classical Source | JHora Comparison | PyJHora Comparison | AstroOS Expected Result |
|-------|-------------------|-------------------|----------------------|---------------------------|
| D2 | BPHS Ch.6 v.4–7 | Select D-2 (Hora) chart; JHora reports hora-lord (Sun/Moon) per graha directly — compare lord assignment, not just sign | Divisional-chart function with factor=2; compare resulting rashi array | `_d2_hora()` — Cancer/Leo alternation by odd/even sign, `divisional_engine.py:85` |
| D3 | BPHS Ch.6 v.8–11 | Select D-3 (Drekkana) chart; compare trine placement per planet | Factor=3 | `_d3_drekkana()` — offset table [0,4,8], `divisional_engine.py:103` |
| D4 | BPHS Ch.6 v.12 | Select D-4 (Chaturthamsa) chart | Factor=4 | `_d4_chaturthamsha()` — kendra offset ×3, `divisional_engine.py:116` |
| D7 | BPHS Ch.6 v.13–15 | Select D-7 (Saptamsa) chart | Factor=7 — confirm same floor convention on the repeating-decimal (30/7°) part size before treating a boundary disagreement as a bug | `_d7_saptamsha()`, `divisional_engine.py:128` |
| D9 | BPHS Ch.6 v.16–20; Saravali Ch.43 | Select D-9 (Navamsa) chart; JHora explicitly flags Vargottama planets — use as an independent Vargottama cross-check | Factor=9 | `_d9_navamsha()` — general formula `(sign×9+part)%12`, `divisional_engine.py:143` |
| D10 | BPHS Ch.6 v.21–23 | Select D-10 (Dasamsa) chart | Factor=10 | `_d10_dasamsha()`, `divisional_engine.py:161` |
| D12 | BPHS Ch.6 v.24 | Select D-12 (Dvadasamsa) chart | Factor=12 | `_d12_dvadashamsha()`, `divisional_engine.py:175` |
| D16 | BPHS Ch.6 v.25 | Select D-16 (Shodasamsa) chart | Factor=16 | `_d16_shodashamsha()` + `_D16_START` table, `divisional_engine.py:196` |
| D20 | BPHS Ch.6 v.26 | Select D-20 (Vimsamsa) chart | Factor=20 | `_d20_vimshamsha()` + `_D20_START` table, `divisional_engine.py:217` |
| D24 | BPHS Ch.6 v.27 | Select D-24 (Chaturvimsamsa/Siddhamsa) chart | Factor=24 | `_d24_chaturvimshamsha()`, `divisional_engine.py:230` |
| D27 | BPHS Ch.6 v.28 | Select D-27 (Bhamsa/Nakshatramsa) chart | Factor=27 | `_d27_bhamsha()` + `_D27_START` table, `divisional_engine.py:254` |
| D30 | BPHS Ch.6 v.29–34 | Select D-30 (Trimsamsa) chart; **explicitly confirm JHora applies the same Sun/Moon luminary exception** — this is the single highest-risk varga and some software variants differ on this point | Factor=30 — same luminary-exception confirmation applies | `_d30_trimshamsha()` + explicit Sun/Moon passthrough, `divisional_engine.py:267,654` |
| D40 | BPHS Ch.6 v.35 | Select D-40 (Khavedamsa) chart | Factor=40 | `_d40_khavedamsha()`, `divisional_engine.py:313` |
| D45 | BPHS Ch.6 v.36 | Select D-45 (Akshavedamsa) chart | Factor=45 | `_d45_akshavedamsha()` + `_D45_START` table, `divisional_engine.py:336` |
| D60 | BPHS Ch.6 v.37–40 | Select D-60 (Shashtyamsa) chart; JHora additionally names the amsha deity (Ghora/Rakshasa/Deva, etc.) per part — AstroOS does not compute this label (§10), so comparison is sign/degree/house only | Factor=60 | `_d60_shashtiamsha()`, `divisional_engine.py:349` |

**Note on exact JHora/PyJHora invocation:** the JHora chart-selector path and the exact PyJHora module/function signature (e.g., its divisional-chart factor parameter) must be confirmed against the specific installed versions before this table is used to generate pass/fail data — treat the entries above as the comparison *plan*, not a verified API reference. This confirmation is a prerequisite action item, not yet performed (§10, Known Limitations).

---

## 7. Full Test Matrix

| Varga | Divisor | Part Size | Starting-Sign Rule Type | Test Case Count (5 charts + boundary fixtures) |
|-------|---------|-----------|--------------------------|--------------------------------------------------|
| D2 | 2 | 15° | Odd/Even alternation | 5 + 2 boundary = 7 |
| D3 | 3 | 10° | Fixed offset table [0,4,8] | 5 + 2 boundary = 7 |
| D4 | 4 | 7.5° | Kendra offset (×3) | 5 + 3 boundary = 8 |
| D7 | 7 | 30/7° | Odd/Even start | 5 + 1 boundary = 6 |
| D9 | 9 | 30/9° | General formula + Vargottama | 5 + 1 Vargottama fixture = 6 |
| D10 | 10 | 3° | Odd/Even start | 5 + 9 boundary = 14 |
| D12 | 12 | 2.5° | Direct offset | 5 + 0 = 5 |
| D16 | 16 | 1.875° | Quality table (3-way) | 5 + differential vs none = 5 |
| D20 | 20 | 1.5° | Quality table (3-way) | 5 + differential vs D16 = 6 |
| D24 | 24 | 1.25° | Odd/Even, fixed target | 5 + 0 = 5 |
| D27 | 27 | 30/27° | Element table (4-way) | 5 + 1 boundary = 6 |
| D30 | 30 | non-equal | 5-way non-uniform + luminary exception | 5 + 8 boundary = 13 |
| D40 | 40 | 0.75° | Odd/Even start | 5 + 1 boundary = 6 |
| D45 | 45 | 30/45° | Quality table (3-way) | 5 + differential vs D16/D20 = 7 |
| D60 | 60 | 0.5° | Odd/Even start | 5 + 4 boundary = 9 |
| **TOTAL** | | | | **~110 test cases** |

Plus cross-cutting `BM-VARGA-EDGE-*` cases:

| ID | Focus |
|----|-------|
| BM-VARGA-EDGE-001 | `compute_all()` returns exactly 15 vargas for every chart |
| BM-VARGA-EDGE-002 | Unsupported varga code raises `ValueError` (not silent failure) |
| BM-VARGA-EDGE-003 | Every `varga_rashi_degree` output is within [0, 30) for all 15 vargas × 5 charts |
| BM-VARGA-EDGE-004 | Every `varga_house_number` output is within [1, 12] for all 15 vargas × 5 charts |
| BM-VARGA-EDGE-005 | `planet_positions` sorted by `(varga_house_number, planet)` per `VargaChart` contract |
| BM-VARGA-EDGE-006 | Determinism: `compute()` called twice with identical input produces identical output (hash match) |
| BM-VARGA-EDGE-007 | D16 vs D20 vs D45 quality-table differential (consolidates §5.9, §5.14 differential tests) |

---

## 8. Acceptance Criteria (Family-Level)

### 8.1 Hard Requirements (100% Pass Required)

| # | Criterion | Condition |
|---|-----------|-----------|
| H1 | Varga rashi assignment | Exact match, all 15 vargas × 9 grahas × 5 charts (675 checks) |
| H2 | Varga rashi degree | ±0.0001° (±0.0005° for repeating-decimal part sizes: D7, D27, D45) |
| H3 | Varga house number | Exact match, per §3.4 formula |
| H4 | Dignity classification (non-Rahu/Ketu) | Exact match to §3.3 tables |
| H5 | D9 Vargottama flag | Exact match, zero tolerance |
| H6 | D30 luminary exception | Sun/Moon D30 rashi == D1 rashi, zero tolerance, blocking |
| H7 | Part-boundary assignment | Exact match to documented floor convention, all vargas |
| H8 | `compute_all()` completeness | All 15 vargas present, every call |
| H9 | Determinism | 100% hash match across repeated runs |

### 8.2 Soft Requirements (≥ 95% Pass, Reported)

| # | Criterion | Condition |
|---|-----------|-----------|
| S1 | Rahu/Ketu dignity classification | Tradition-dependent, ≥ 95% agreement with declared tradition |
| S2 | D2 hora-lord classical interpretation alignment | Cross-check against a second classical source |

### 8.3 Gate

BM-VARGA passes when all HARD criteria (§8.1) reach 100% across the full test matrix (§7) on GC-MASTER, and the D30 luminary exception (H6) has zero failures under any circumstance — this single check is treated as a release blocker independent of aggregate pass rate.

---

## 9. Known Failure Modes

These are the specific bug patterns most likely to appear in a divisional-chart engine, based on the shape of the 15 formulas in §5. Each is mapped to the vargas most exposed and the test class that catches it, so a benchmark failure can be triaged quickly instead of re-deriving the formula from scratch.

| ID | Failure Mode | Description | Vargas Most At Risk | Symptom | Detected By |
|----|--------------|--------------|----------------------|---------|-------------|
| FM-1 | **Wrong odd/even (parity) sign handling** | `_is_odd_sign()` off-by-one, or an odd/even branch swap in a varga's starting-sign logic | D2, D7, D10, D24, D40, D60 (all parity-based) | Exactly half of all charts — every planet landing in an odd (or even) D1 sign — gets a systematically wrong varga sign, while the other half still passes. Easy to miss with a small or unbalanced sample | Per-varga test cases requiring ≥1 odd-sign and ≥1 even-sign D1 placement (§3.1 coverage requirement); JHora/PyJHora comparison (§6) across both parities |
| FM-2 | **Incorrect movable/fixed/dual (quality) lookup** | A typo or copy-paste error in `_D16_START`, `_D20_START`, or `_D45_START` — e.g., reusing D16's Fixed→Leo mapping inside D20 instead of D20's own Fixed→Sagittarius | D16, D20, D45 | Subtle: only the planets whose D1 sign has the affected quality (exactly 4 of 12 signs) come out wrong; the other 8 signs pass, so a shallow test with few sign-quality cases can pass while the table is broken | Cross-varga differential tests (§5.9, §5.14, BM-VARGA-EDGE-007) that assert D16/D20/D45 disagree exactly where their tables differ |
| FM-3 | **Table/offset errors (fixed-offset formulas)** | Wrong constant in an offset table — D3's `[0,4,8]`, D4's kendra `×3`, D27's 4-way element table, or a D30 sub-part boundary shifted by a degree | D3, D4, D27, D30 | Output still lands on a *valid* sign, just the wrong one — the error is not caught by a schema/range check, only by comparing against the correct offset | Independent re-implementation (§3.4) of the offset table itself, not just the arithmetic; JHora/PyJHora comparison (§6) |
| FM-4 | **Incorrect integer division / floor vs. round vs. clamp** | Using `round()` instead of `int()` (floor), or an off-by-one in the `min(part, N-1)` clamp, causes a part-boundary value to fall in the wrong part or overflow the sign array | All vargas, highest risk in fine-resolution ones (D40, D45, D60) where `part_size` is small or a repeating decimal | Failures only at specific, narrow degree ranges near a part boundary — appears as flaky/data-dependent rather than a consistent break, and is invisible if tests only sample mid-part degrees | Dedicated boundary fixtures at every part edge (§3.2, per-varga boundary tests in §5), not random sampling |
| FM-5 | **Longitude normalization errors** | `sidereal_longitude` not reduced mod 360 before `sign_index = int(lon/30)`, or a negative longitude (e.g., after ayanamsa subtraction, or Ketu = Rahu + 180° not wrapped) passed into the varga dispatcher | All vargas (upstream in `compute_varga_sign`), most visible in D2 (only 2 valid output signs, so a wrap bug produces an immediately implausible sign) and in Ketu specifically | `IndexError` on `_RASHI_LIST`, or a planet silently assigned to the wrong sign near the 0°/360° or Aries/Pisces boundary | `BM-VARGA-EDGE-003`/`004` range invariants (`0 ≤ varga_rashi_degree < 30`, `1 ≤ varga_house_number ≤ 12`); explicit Ketu-wrap test asserting `0 ≤ sidereal_longitude < 360` before dispatch |
| FM-6 | **Ayanamsa mismatch (cross-tool false failure)** | Comparing AstroOS (Lahiri) output against JHora/PyJHora run with a different ayanamsa (Raman, KP, True Chitra) — the D1 input itself differs, so every downstream varga "disagrees" even though the varga formula is correct | Not a code defect — a methodology risk affecting every §6 comparison for every varga | A benchmark run reports widespread disagreement with JHora/PyJHora across all 15 vargas simultaneously, which is itself diagnostic (a real formula bug would affect specific vargas/signs, not all of them uniformly) | Mandatory ayanamsa/config pre-check before any cross-tool comparison (§6.1); if all 15 vargas disagree at once, check ayanamsa configuration before investigating individual formulas |
| FM-7 | **D30 luminary exception silently dropped** | The `if varga == "D30" and planet in ("sun", "moon")` passthrough (`divisional_engine.py:654`) is removed or bypassed during a refactor, so Sun/Moon get a (classically wrong) computed Trimshamsha instead of retaining their D1 sign | D30 only, but the single highest-priority regression in the whole family | Sun/Moon D30 rashi differs from D1 rashi — result is syntactically valid (a real sign, real degree) so it will not raise an error, only produce classically incorrect output | H6 (§8.1) — zero-tolerance, release-blocking assertion `sun.varga_rashi == sun.d1_rashi` and `moon.varga_rashi == moon.d1_rashi`, independent of all other D30 checks |
| FM-8 | **Repeating-decimal part-size rounding drift** | `part_size` values that are not terminating decimals (30/7, 30/27, 30/45) accumulate float rounding error across `deg % part_size` and `× N` rescaling, producing a `varga_rashi_degree` that drifts outside [0, 30) or a part index off by one near the last part | D7, D27, D45 | `varga_rashi_degree` slightly negative or ≥ 30, or the wrong part selected only for the last 1–2 parts of a sign | Widened boundary tolerance (±0.0005°, §3.5, H2) plus explicit last-part boundary fixtures (§5.4, §5.11, §5.14) |

---

## 10. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **GC-MASTER not yet populated with verified D1 positions** | BM-VARGA expected values cannot be finalized as concrete numbers until BM-CALC produces verified D1 longitudes for all 5 charts | This specification defines methodology and formulas (§5); numeric expected-value tables are generated once GC-MASTER reaches CANDIDACY (see [GC-MASTER-design.md](../datasets/GC-MASTER-design.md) §6) |
| **Rahu/Ketu dignity has no single classical consensus** | Cross-text disagreement on exaltation/debilitation signs | Treated as SOFT criterion only (§3.5); benchmark documents which tradition AstroOS follows once decided (open governance item, see GD-BM-003-style decision needed for varga dignity) |
| **D30 sub-part boundaries have minor cross-text variance** | Some classical sources place the odd-sign Sagittarius/Gemini boundary at slightly different degrees | AstroOS follows the boundary set in `divisional_engine.py` (10°/18°/25°); benchmark validates internal consistency, not cross-text universality — classified Tier B |
| **D60 named amsha deities (Ghora/Rakshasa/Deva etc.) not implemented** | `DivisionalEngine` computes sign/degree/house only, not per-amsha character labels | Out of scope for BM-VARGA v1.0.0; flag as a future BM-VARGA-D60-DEITY sub-benchmark if the engine adds this feature |
| **JHora/PyJHora comparisons (§6) are a documented plan, not yet executed** | The Reference Implementations matrix (§6.2) specifies what to compare and against which classical source, but no actual JHora/PyJHora run has been performed yet — exact JHora menu paths and the PyJHora API surface need confirmation against the installed versions | First execution of §6 is a prerequisite task before BM-VARGA can be promoted from APPROVED to FROZEN; track as an action item for the benchmark execution phase |
| **Part-boundary floor convention is AstroOS-internal, not universally standardized** | Different software may round boundary degrees differently | Benchmark documents AstroOS's floor convention explicitly (§3.4) rather than asserting it as the only correct approach |

---

## 11. Evidence & References

| Reference | Type | Location |
|-----------|------|----------|
| Brihat Parashara Hora Shastra, Ch. 6 (Shodasavarga) | Classical text | Primary source for all 15 varga formulas |
| Saravali, Ch. 43 (Navamsha) | Classical text | D9 significance cross-reference |
| AstroOS `DivisionalEngine` | Source | `apps/api/services/divisional_engine.py` |
| AstroOS divisional domain models | Source | `apps/api/domain/divisional.py` |
| Divisional varga rules (agent memory) | Internal notes | `.agents/memory/divisional-varga-rules.md` |
| BM-CALC Master Specification | Benchmark | `benchmarks/specifications/BM-CALC-master.md` |
| BM-HOUSE Master Specification | Benchmark | `benchmarks/specifications/BM-HOUSE-master.md` |
| GC-MASTER Dataset Design | Dataset | `benchmarks/datasets/GC-MASTER-design.md` |
| Benchmark Specification Template | Template | `benchmarks/templates/benchmark-spec-template.md` |

---

## 12. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-16 | Chief QA & Benchmark Architect (Agent 4) | Initial specification — all 15 vargas (D2–D60), methodology, dignity tables, test matrix, acceptance criteria |
| 1.1.0 | 2026-07-16 | Chief QA & Benchmark Architect (Agent 4) | Added §6 Reference Implementations (classical/JHora/PyJHora/AstroOS per varga) and §9 Known Failure Modes (8 failure patterns mapped to affected vargas and detection method) |
| 1.1.0 | 2026-07-16 | — | **ACCEPTED** by Chief Engineering |

---

*End of BM-VARGA Master Specification. Defines the WHAT and WHY of divisional chart benchmarks across all 15 supported vargas. Status: **ACCEPTED**.*

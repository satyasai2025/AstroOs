# Jyotish Knowledge Repository — STATUS

**Current Phase:** 6 — Conflict Analysis COMPLETE
**Last Updated:** 2026-07-16
**Total Records:** 206 (Phase 2B + Phase 3 + Phase 4 + Phase 5 + Phase 6 + 2 source registry additions)
**Repository Audit:** Full cross-phase audit completed 2026-07-16 — see Audit section below
**Governance:** Knowledge Office frozen in Governance Mode — see `KNOWLEDGE_COMPLETION_REPORT.md`

---

## Phase 2B Frozen Catalogues (114 records)

| Catalogue | Records | Status |
|---|---|---|
| Classical Texts | 26 | ✅ FROZEN* |
| Terminology | 30 | ✅ FROZEN |
| Grahas | 9 | ✅ FROZEN* |
| Rashis | 12 | ✅ FROZEN |
| Bhavas | 12 | ✅ FROZEN |
| Nakshatras | 27 | ✅ FROZEN |

*Classical Texts count was originally stated as 24, but 2 of those
24 (`BPHS.yaml`, `vishnu-dharmottara.yaml`) were missing from disk
despite being declared in the index since Phase 2B; both filled
2026-07-16, and 2 further sources (`jaimini-upadesha-sutras.yaml`,
`traditional.yaml`) were newly registered the same day to resolve
previously-dangling citations, bringing the total to 26.

*Surya (`surya.yaml`) was missing from disk despite being referenced
in the index since Phase 2B was first frozen; filled 2026-07-16.
Chandra's `avastha` sign categorization was also corrected the same
day (see catalogues/grahas/chandra.yaml history).

---

## Phase 3 Frozen Catalogues (56 records)

### Yoga Catalogue — 20 + _index ✅ FROZEN

**Raja Yogas (5):**
- gaja-keshari, budha-aditya, chandra-mangala, dhana-yoga-1, vasumad

**Dhana Yogas (3):**
- lakshmi-yoga, dhana-yoga-2, kubera

**Chandra Yogas (6):**
- maha-bhagya, gauri-yoga, sunapha, anapha, durudhura, kapata

**Dosha (3):**
- mangal-dosha, sarpadosha, kaal-sarpadosha

**Special (3):**
- pancha-mahapurusha, neechabhanga-raja, viparita-raja

### Karakatva Catalogue — 5 records ✅ FROZEN

- graha-karakatvas, bhava-karakatvas, nakshatra-karakatvas,
  house-significations, _index

### Aspect/Drishti Catalogue — 12 records ✅ FROZEN

**Graha Drishti (5):**
- graha-standard-aspects, guru-special-aspects, shani-special-aspects,
  mangala-special-aspects, rahu-ketu-aspects

**Rashi Drishti (2):**
- rashi-drishti-rules, rashi-drishti-table

**Special (3):**
- conjunction-effects, aspect-strength, argala-rules

**Reference (2):**
- aspect-summary-table, _index

### Transit/Gochara Catalogue — 8 records ✅ FROZEN

- gochara-rules, shani-gochara, guru-gochara, rahu-ketu-gochara,
  mangala-gochara, transit-significations, ashtakavarga-basics, _index

### Dasha Catalogue — 6 records ✅ FROZEN

- vimshottari, ashtottari, shodashottari, chara-dasha,
  narayana-dasha, _index

---

## Conflicts — 7 records ✅ FROZEN (Phase 6)

- conflict.001: Lagna vs Bhava 1 (partially-resolved)
- conflict.002: Surya benefic vs malefic (unresolved)
- conflict.003: Surya neutral signs (resolved)
- conflict.004: Ayanamsa selection (partially-resolved)
- conflict.005: Rahu/Ketu special aspects (partially-resolved)
- conflict.006: Rahu/Ketu exaltation signs (partially-resolved)
- conflict.007: Kaal Sarpa Dosha legitimacy (unresolved)

See `conflicts/_index.yaml` and Phase 6 section below for full detail.

---

## Phase 4 Catalogues (25 records) ✅ COMPLETE

### Jaimini Catalogue — 13 records ✅

- karakamsha, chara-dasha-rules, jaimini-aspects, jaimini-karakas,
  jaimini-yogas, chara-karaka-system, atmakaraka-role,
  chara-karaka-effects, chara-dasha-system, chara-dasha-calculator,
  chara-dasha-effects, rashi-drishti, arudha-padas (+ _index)

*Note: Arudha Pada content was folded into this catalogue
(`arudha-padas.yaml`) rather than a standalone Arudha catalogue.*

### KP System Catalogue — 3 records ✅

- kp-sublord-system, kp-significators, kp-cuspal-houses (+ _index)

### Lal Kitab Catalogue — 3 records ✅

- lal-kitab-house-rules, lal-kitab-planetary-effects,
  lal-kitab-remedies (+ _index)

### Tajika Catalogue — 3 records ✅

- tajika-annual-chart, tajika-yogas, tajika-timing (+ _index)

### Bhrigu Nandi Nadi Catalogue — 3 records ✅

- bhrigu-nadi-principles, bhrigu-nadi-combinations,
  bhrigu-nadi-timing (+ _index)

---

## Phase 5 Cross-References (5 records) ✅ COMPLETE

- graha-rashi-dignity-matrix — full 9x12 dignity matrix
- graha-nakshatra-affinity — placement affinity by nakshatra-lord relationship
- graha-bhava-functional-nature — house-type occupation strength per graha
- yoga-graha-index — reverse index of the 20 yogas by graha participant
- dasha-graha-event-themes — consolidated Mahadasha life-event themes
  (+ _index)

All 5 records live under `cross-references/`. See
`cross-references/_index.yaml` for details.

---

## Repository Audit — 2026-07-16 ✅ COMPLETE

A full cross-phase integrity audit was run covering: index-file
existence, source-citation resolution, entity-ID validity
(graha/bhava/rashi/nakshatra), record-count accuracy, rashi↔graha
cross-consistency, nakshatra-lordship cross-consistency, and
duplicate-ID detection. All findings below were fixed the same day.

**Missing files:**
- `sources/texts/BPHS.yaml` — the single most-cited source in the
  entire knowledge base was declared in the index since Phase 2B but
  never created. Created.
- `sources/texts/vishnu-dharmottara.yaml` — declared, cited by
  `matansa.yaml`, never created. Created.

**Nakshatra ID naming unified** (3 incompatible schemes were in
simultaneous use — canonical no-underscore form, an underscore
variant used in all 9 graha files + Phase 5 cross-references, and
divergent spellings `aridra`/`maga`/`mula` in the karakatvas index).
All standardized to the canonical form from
`catalogues/nakshatras/_index.yaml`. Affected: all 9 graha files,
`karakatvas/nakshatra-karakatvas.yaml`, `karakatvas/_index.yaml`,
6 rashi files, `cross-references/graha-nakshatra-affinity.yaml`.

**Rashi ID naming unified.** 14 of 27 nakshatra files used
non-canonical rashi references (bare Sanskrit form, numeric sign
index, or a third `rashi.tulam` variant) instead of the catalogue's
`-am` suffix IDs. All fixed.

**Factual nakshatra-lordship errors corrected** (distinct from the
naming issue above):
- `catalogues/grahas/surya.yaml` listed Uttara Bhadrapada (Shani's
  nakshatra) instead of Surya's actual third nakshatra, Uttara
  Ashadha. This error propagated into
  `cross-references/graha-nakshatra-affinity.yaml`, which was
  rebuilt from corrected data.
- `catalogues/karakatvas/nakshatra-karakatvas.yaml` had 3 nakshatras
  assigned to the wrong graha: Jyeshtha (was Mangala, corrected to
  Budha), Moola (was Guru, corrected to Ketu), Revati (was Chandra,
  corrected to Budha).
- `catalogues/karakatvas/_index.yaml`'s `graha_to_nakshatra_rulers`
  table had a *different* set of errors (Chandra had Pushya instead
  of Hasta; Guru had Moola instead of Purva Bhadrapada; Rahu had an
  erroneous 4th nakshatra). Corrected.
- `catalogues/dashas/vimshottari.yaml`'s nakshatra-ownership notes
  table was internally scrambled (listed Chandra twice, omitted
  Budha entirely). Rewritten to match the standard sequence.

**Source registry fixes:**
- Casing mismatches (`source.JaiminiSutras`/`Phaladeepika`/`Saravali`
  vs registered lowercase-hyphenated forms) fixed across 17 files.
- `source.JaiminiUpadeshaSutras` — cited once, never registered.
  Given a proper record as `source.jaimini-upadesha-sutras`.
- `source.Traditional` — used 3× as an informal citation, never
  registered. Given a proper (low-confidence, explicitly-scoped
  pseudo-source) record as `source.traditional`.
- `source.parashara` — an erroneous/redundant reference in
  `sources/texts/bhrigu-nandi-nadi.yaml`, merged into the adjacent
  `source.BPHS` citation.

**Count corrections:** `karakatvas/_index.yaml` summary block
(`total_records: 53` → 85, `life_events_mapped: 35` → 37, both now
footing correctly to their sub-counts).

**Result:** zero dangling index references, zero unresolved source
citations, zero duplicate IDs, zero non-canonical entity-ID
references remaining anywhere in the repository.

---

## Phase 6 — Conflict Analysis — 2026-07-16 ✅ COMPLETE

All 3 carried-over conflicts were reviewed and enriched with verified
`cross_references` blocks linking each to the Rule Engine
(`apps/api/services/rules/`, `aspect_engine.py`) and the Ontology
(`apps/api/domain/ontology.py`, `ontology_registry.py`). A full-repository
survey (grep for "debated"/"disputed"/"contradicts"/"internal
inconsistency" across all catalogues, cross-references, and the
glossary) surfaced 4 additional doctrinal conflicts not previously
promoted to formal records:

- **conflict.004** — Ayanamsa selection (Lahiri/Raman/KP/Yukteshwar/
  Fagan-Bradley/True Chitra). Previously only noted as a "controversy"
  in `ontology/glossary/ayanamsa.yaml`'s notes field.
- **conflict.005** — Rahu/Ketu special 5th/9th aspects. Previously
  extensively narrated but not indexed as a conflict in
  `catalogues/aspects/rahu-ketu-aspects.yaml`.
- **conflict.006** — Rahu/Ketu exaltation signs (Gemini/Sagittarius vs
  Taurus/Scorpio). Resolves the "internal inconsistency" flagged but
  left open in `cross-references/graha-rashi-dignity-matrix.yaml`'s
  Phase 5 `data_quality_note`.
- **conflict.007** — Kaal Sarpa Dosha's classical legitimacy. Confirmed
  via source-registry cross-check that only 2 of 20 cataloged yogas/
  doshas (this one and Sarpadosha) cite no primary classical text.

**Every conflict's cross-references were verified against the actual
codebase**, not asserted from memory — file paths and line numbers were
read or grepped directly during this phase. Where no Rule Engine or
Ontology implementation exists for a conflict's subject (conflict.003's
graha friendship/enmity table; conflict.007's Kaal Sarpa Dosha), the
record states that plainly as a confirmed implementation gap rather
than fabricating a link.

**One code-side documentation drift was found and flagged** (not
fixed, out of Knowledge Office scope): the Ontology's
`ASPECT-SPECIAL-GRAHA` entity description ("Mars/Jupiter/Saturn's...")
omits Rahu/Ketu even though `aspect_engine.py` implements special
aspects for both nodes. See conflict.005's `cross_references`.

**Result:** 7 conflicts total (1 resolved, 4 partially resolved, 2
unresolved), `conflicts/_index.yaml` created, `KNOWLEDGE_COMPLETION_REPORT.md`
produced. See that report for full methodology and findings.

---

## Bridge Endpoints (Knowledge Graph ↔ Analytics)

The **Knowledge Graph Bridge** (`POST /api/v1/knowledge-graph/analyze`) was
implemented 2026-07-20, wiring `EntityLinker` and `GraphAnalytics` together
under a single HTTP endpoint. This was the last unimplemented surface in the
schemas defined during Phase D / Module 12 — the `AnalyzeRequest` and
`AnalyzeResponse` schemas existed since Phase III design but were never
wired into a router handler.

The endpoint performs:
1. Entity linking (chart planets/houses/signs → KG entities by name/alias)
2. Proximity relationship surfacing between linked entities
3. Statistical correlation (Welch's t-test / Cohen's d) between entity presence
   and a numeric dataset field
4. Frequency distribution over a dataset column

All computation is deterministic and pure-local (in-memory OntologyRegistry +
StatisticalEngine) — no external services, no LLM calls.

See `apps/api/routers/knowledge_graph.py`'s `analyze_bridge()` handler and
`apps/api/services/graph_analytics.py` for the implementation.

---

## External Requests (Knowledge Office → Other Offices)

| ID | Request | Target Office | Status | Context |
|---|---|---|---|---|
| **ER-001** | Fix `ASPECT-SPECIAL-GRAHA` ontology description drift (`apps/api/services/ontology_registry.py`'s `_populate_aspect()` description omits Rahu/Ketu despite `aspect_engine.py` computing their special aspects) | Engineering Office | 🟡 IN PROGRESS — work session started 2026-07-16 | Found during Phase 6 Conflict Analysis; see `conflicts/conflict-005.yaml` cross_references |

This supersedes the informal background-task suggestion raised during
Phase 6 review. Per governance requirement, out-of-office fixes
surfaced during a phase are logged here as a formal request rather
than actioned ad hoc. See also `ENGINEERING_STATUS.md`'s corresponding
inbound-request entry.

---

## Governance Mode (2026-07-16)

Phase 6 is frozen. The Knowledge Office returns to Governance Mode:
no further edits to `catalogues/`, `cross-references/`, `ontology/`,
`sources/`, or `conflicts/` without a newly authorized phase. Phase 7
(Verse Catalogue) is the only remaining open item — see ROADMAP.md.

---

## Migration Note (2026-07-16)

This Knowledge Office was migrated into `AstroOS/knowledge/` from
`C:\Users\rkmau\.claude\jyotish-knowledge-base\` as-is, with no
structural changes. No `COMPLETION_REPORT.md` was ever produced for
this office in its source location — unlike the Engineering,
Architecture, and Benchmark offices, it has no frozen completion
summary. This remains an open governance gap; see
`KNOWLEDGE_MIGRATION_REPORT.md` for full migration details.

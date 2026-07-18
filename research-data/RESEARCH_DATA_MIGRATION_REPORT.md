# Research Data Office — Migration Report

> **Date:** 2026-07-16
> **Sources:**
> - `C:\Users\rkmau\.claude\projects\AstroOs\datasets\` (dataset files)
> - `C:\Users\rkmau\.claude\projects\C--Users-rkmau--claude\memory\` (governance docs)
> **Destination:** `AstroOS/research-data/`
> **Method:** Preserve the source's own dataset taxonomy — do not force-fit
> into an external 6-folder sketch (`public/reference/cohort/events/pipelines/validation`)
> that doesn't match how this office actually categorizes its ~50 dataset types.

---

## 1. Migrated Assets — 73 files

| Destination folder | Source folder | Files | Contents |
|---|---|---|---|
| `reference/` | `rf/` | 29 | RF-* reference datasets: ayanamsa, dasha, ephemeris, houses, karaka, nakshatras, padas, planets, signs, timezone |
| `research/` | `rs/` | 17 | RS-* research-study datasets: career, cohort, event, flat, health, marriage, spiritual, wealth |
| `public/` | `pb/` | 7 | PB-* public-figure datasets: events, wiki, wikidata |
| `synthetic/` | `sy/` | 4 | SY-* synthetic datasets: null, random |
| `validation/` | `vl/` | 1 | VL-* cross-engine consistency data |
| `ai-eval/` | `ai/` | 1 | AI-* evaluation dataset: fact |
| `pipelines/` | `import-framework/` | 4 | Adapter mapping docs, compliance reviews, canonical mappings |
| `governance/` | *(memory folder, not `datasets/`)* | 7 | Phase 1 audit report + 6 standards docs (taxonomy, standards, quality, record-standards, research-support, standard-formats) |
| `ROADMAP.md`, `STATUS.md`, `INDEX.md`, `COMPLETION_REPORT.md` | `DATASET_ROADMAP.md`, `DATASET_STATUS.md`, `DATASET_INDEX.md`, `research-data-office-overview.md` | 4 | Top-level governance docs, renamed to match the other three offices' naming convention (Engineering/Architecture/Benchmark) |

---

## 2. Naming Decisions

- **Top-level folders were renamed**, not restructured: `rf→reference`,
  `rs→research`, `pb→public`, `sy→synthetic`, `vl→validation`, `ai→ai-eval`.
  The *sub*structure inside each (e.g. `reference/nakshatras/ASTRO-RF-NAK-v1.0.0/`)
  was left untouched.
- `pipelines/` is a new grouping folder — the source had `import-framework/`
  and `candidate-datasets/` as siblings of the dataset-type folders; they're
  pipeline/tooling artifacts, not datasets, so they were nested under
  `pipelines/` for clarity rather than left at the top level.
- `governance/` is new — the 6 standards docs and the phase-1 audit report
  lived in a flat memory folder alongside unrelated project memory. They
  were grouped here since they're this office's specification set, roughly
  analogous to `benchmarks/specifications/`.
- `COMPLETION_REPORT.md` was copied from `research-data-office-overview.md`
  with its memory-system YAML frontmatter (name/description/metadata/
  originSessionId) stripped, since that frontmatter is an artifact of the
  `.claude` memory storage format, not part of the actual document content.

---

## 3. Intentionally Excluded

| Item | Why excluded |
|---|---|
| `datasets/bm/` (BM-* benchmark datasets) in the source | Benchmark data already lives in this repo under `benchmarks/` and `datasets/bm/` — copying it again under `research-data/` would create a third copy of the same content. The Research Data Office's own taxonomy treats BM-* as belonging to the Benchmark Office, not itself. |
| `.claude/projects/AstroOs/benchmarks/` and `.../memory/enterprise/` | Diffed byte-for-byte against this repo's existing `benchmarks/` and `architecture/enterprise/` — identical, so not re-copied (see prior turn). |

---

## 4. Remaining Gaps (per source `COMPLETION_REPORT.md` / overview)

- **48 of 51 defined dataset types have no data yet** — only 3 (RF-SIGNS,
  RF-NAK, RF-PADA) are seeded with real data; everything else is spec'd
  but not built. This is a stated gap in the source office itself, not
  something introduced by migration.
- **5 governance decisions open** (GD-002 through GD-006 in `STATUS.md`) —
  public-figure privacy threshold, ethics board formation,
  cohort sharing policy, AI training data policy, commercial data budget.

---

*This report documents the migration only. It does not assess or
validate the underlying dataset content.*

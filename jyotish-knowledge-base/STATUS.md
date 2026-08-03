# Jyotish Knowledge Repository — STATUS

**Current Phase:** 5 — Relationship Mapping COMPLETE
**Last Updated:** 2026-07-16
**Total Records:** 202 (Phase 2B + Phase 3 + Phase 4 + Phase 5 + 2 source registry additions)
**Repository Audit:** Full cross-phase audit completed 2026-07-16 — see Audit section below

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

## Conflicts — 3 records ✅ FROZEN

- conflict.001: Lagna vs Bhava 1 (partially-resolved)
- conflict.002: Surya benefic vs malefic (unresolved)
- conflict.003: Surya neutral signs (resolved)

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

## Next Phase: Phase 6 — Conflict Analysis (PENDING)

- Comprehensive conflict documentation
- Reconciliation recommendations

# Jyotish Knowledge Repository — INDEX

**Total Records:** 202 (Phase 2B + Phase 3 frozen + Phase 4 + Phase 5 + 2 source registry additions)
**Last Updated:** 2026-07-16
**Note:** A full repository audit ran 2026-07-16 — see STATUS.md's Audit section for the complete list of fixed ID-naming and factual-consistency issues.

---

## Governance

- [ROADMAP.md](ROADMAP.md) — Implementation roadmap
- [STATUS.md](STATUS.md) — Current status

---

## Phase 2B — Foundation (114 records)

### Sources (24) | Glossary (30) | Grahas (9) | Rashis (12) | Bhavas (12) | Nakshatras (27)

All in `sources/texts/`, `ontology/glossary/`, `catalogues/grahas/`, `catalogues/rashis/`, `catalogues/bhavas/`, `catalogues/nakshatras/`.

---

## Phase 3 — Specialized (56 records)

### Yogas (20 + _index)

| File | Type | Source |
|---|---|---|
| raja/gaja-keshari | Raja | BPHS |
| raja/budha-aditya | Raja | BPHS |
| raja/chandra-mangala | Raja | BPHS |
| raja/dhana-yoga-1 | Raja | BPHS |
| raja/vasumad | Raja | Saravali |
| dhana/lakshmi-yoga | Dhana | Phaladeepika |
| dhana/dhana-yoga-2 | Dhana | BPHS |
| dhana/kubera | Dhana | Phaladeepika |
| chandra/maha-bhagya | Chandra | BPHS |
| chandra/gauri-yoga | Chandra | Phaladeepika |
| chandra/sunapha | Chandra | BPHS |
| chandra/anapha | Chandra | BPHS |
| chandra/durudhura | Chandra | BPHS |
| chandra/kapata | Chandra | BPHS |
| dosha/mangal-dosha | Dosha | BPHS |
| dosha/sarpadosha | Dosha | Traditional |
| dosha/kaal-sarpadosha | Dosha | Traditional |
| special/pancha-mahapurusha | Special | BPHS |
| special/neechabhanga-raja | Special | BPHS |
| special/viparita-raja | Special | BPHS |

### Karakatvas (5)

| File | Description |
|---|---|
| graha-karakatvas | All 9 grahas' karakatvas |
| bhava-karakatvas | All 12 bhavas' karakatvas |
| nakshatra-karakatvas | All 27 nakshatras' karakatvas |
| house-significations | Life events by house |
| _index | Master index |

### Aspects (12)

| File | Type |
|---|---|
| graha-standard-aspects | 7th house rule |
| guru-special-aspects | 5th, 9th aspects |
| shani-special-aspects | 3rd, 10th aspects |
| mangala-special-aspects | 4th, 8th aspects |
| rahu-ketu-aspects | 5th, 9th (debated) |
| rashi-drishti-rules | Jaimini sign aspects |
| rashi-drishti-table | Complete table |
| conjunction-effects | Yuti effects |
| aspect-strength | Hierarchy |
| argala-rules | Intervention rules |
| aspect-summary-table | Master reference |
| _index | Catalogue index |

### Transits (8)

| File | Description |
|---|---|
| gochara-rules | Basic transit rules |
| shani-gochara | Saturn transit |
| guru-gochara | Jupiter transit |
| rahu-ketu-gochara | Rahu-Ketu transit |
| mangala-gochara | Mars transit (12 houses) |
| transit-significations | Master table |
| ashtakavarga-basics | Ashtakavarga intro |
| _index | Catalogue index |

### Dashas (6)

| File | System |
|---|---|
| vimshottari | 120-year cycle |
| ashtottari | 108-year cycle |
| shodashottari | 116-year cycle |
| chara-dasha | Jaimini rashi-based |
| narayana-dasha | Rashi-based |
| _index | Catalogue index |

---

## Conflicts (3)

- conflict.001: Lagna vs Bhava 1 (partially-resolved)
- conflict.002: Surya benefic vs malefic (unresolved)
- conflict.003: Surya neutral signs (resolved)

---

## Phase 4 — Advanced Systems (25 records)

### Jaimini (13 + _index)

| File | Type |
|---|---|
| karakamsha | Divisional chart |
| chara-dasha-rules | Dasha rules |
| jaimini-aspects | Aspect table |
| jaimini-karakas | Karaka system |
| jaimini-yogas | Yoga collection |
| chara-karaka-system | Karaka overview |
| atmakaraka-role | Karaka role analysis |
| chara-karaka-effects | Karaka effects table |
| chara-dasha-system | Dasha overview |
| chara-dasha-calculator | Dasha calculation guide |
| chara-dasha-effects | Dasha effects table |
| rashi-drishti | Aspect table |
| arudha-padas | Arudha system |

### KP System (3 + _index)

| File | Topic |
|---|---|
| kp-sublord-system | Sub-lord theory |
| kp-significators | Significator table |
| kp-cuspal-houses | Cuspal house system |

### Lal Kitab (3 + _index)

| File | Topic |
|---|---|
| lal-kitab-house-rules | House rules |
| lal-kitab-planetary-effects | Planetary effects |
| lal-kitab-remedies | Remedies |

### Tajika (3 + _index)

| File | Topic |
|---|---|
| tajika-annual-chart | Annual chart |
| tajika-yogas | Yogas |
| tajika-timing | Timing |

### Bhrigu Nandi Nadi (3 + _index)

| File | Topic |
|---|---|
| bhrigu-nadi-principles | Principles |
| bhrigu-nadi-combinations | Combinations |
| bhrigu-nadi-timing | Timing |

---

## Phase 5 — Relationship Mapping (5 records)

All records live under `cross-references/`.

| File | Maps | Description |
|---|---|---|
| graha-rashi-dignity-matrix | Graha x Rashi | Full 9x12 dignity matrix (exalted/moolatrikona/own/friendly/neutral/enemy/debilitated) |
| graha-nakshatra-affinity | Graha x Nakshatra | Placement affinity by nakshatra-lord relationship |
| graha-bhava-functional-nature | Graha x Bhava | House-type occupation strength per graha (kendra/trikona/upachaya/dusthana/maraka) |
| yoga-graha-index | Yoga x Graha | Reverse index of the 20 catalogued yogas by graha participant |
| dasha-graha-event-themes | Dasha x Graha | Consolidated Mahadasha life-event themes across Vimshottari/Ashtottari/Shodashottari |

See `cross-references/_index.yaml` for full detail.

# AstroOS Provenance Registry (Phase 0)

> Machine-readable mirror of `knowledge/sources/source-registry.jsonl` plus the
> per-source extraction outcome from the Phase 0 build.

| source_id | source_file | source_type | tradition | extraction_status | validation_status | extraction output | item count |
|---|---|---|---|---|---|---|---|
| SRC-001 | `notes/series_vedic_devaprashna.md` | notes | Vedic | EXTRACTED | null | `rules/series_vedic_devaprashna-extracted.jsonl` | 196 |
| SRC-002 | `notes/series_vedic_prashna_classes.md` | notes | Vedic-Prashna | EXTRACTED | null | `rules/series_vedic_prashna_classes-extracted.jsonl` | 342 |
| SRC-003 | `notes/series_vedic_tajika.md` | notes | Vedic-Tajika | EXTRACTED | null | `rules/series_vedic_tajika-extracted.jsonl` | 235 |
| SRC-004 | `notes/series_bhrigu_rahu_prashna.md` | notes | Vedic-Prashna | EXTRACTED | null | `rules/series_bhrigu_rahu_prashna-extracted.jsonl` | 57 |
| SRC-005 | `notes/series_misc.md` (Video 2 only) | notes | Vedic-KP | EXTRACTED | null | `rules/series_misc-kp-extracted.jsonl` | 61 |
| SRC-006 | `notes/catalog_vedic.md` | catalog | Vedic | REGISTERED_ONLY | null | — (metadata reference only) | — |
| SRC-010 | `mindset-1.txt` | wiki-dump | Unknown | REGISTERED_ONLY | REVIEW_REQUIRED | — (design spec, not a rule source) | — |
| SRC-011 | `mindset-2.txt` | wiki-dump | Vedic | REGISTERED_ONLY | REVIEW_REQUIRED | — (deferred; conflicts noted) | — |
| SRC-012 | `vedic.txt` | wiki-dump | Unknown | REGISTERED_ONLY | REVIEW_REQUIRED | — (AI syllabus, no astro content) | — |

## Total extraction

- 5 sources extracted, **891 knowledge items**, all `status = EXTRACTED`
- 519 rule-adjacent (RULE 479 / TIMING_INDICATION 25 / CALCULATION_METHOD 15)
- 7 conflict records (see `conflicts/conflict-registry.md`)
- No item is VALIDATED in Phase 0 (per schema lifecycle)

## Validation notes

Nothing is `VALIDATED`. Items flagged by extractors for review:
- SRC-003 (Tajika): Venus orb 70° vs 7° (K000051), degree-age example inconsistencies
  (K000120/K000584), transcription spellings (Tadjika/Todricka, Vimshutri, etc.)
- SRC-002 (Prashna): line 814 moveable/fixed garbled, line 123 "celebrated"
  (likely "delayed"), "solar with the Moon" phrasing (K000362)
- SRC-004 (Bhrigu): "some new distinct" (likely "desire", K000019/K000042),
  "So Chuna laga" uncertain clause (K000034), "Kalyanam" marriage remark (K000022)
- SRC-001 (Devaprashna): doctrinal/philosophical items (guna motivation) are
  borderline — kept because the source's stated content includes them

| SRC-030 | `Phalit.7z → Phalit.kkk` | freeware-binary | Vedic | EXTRACTED | REVIEW_REQUIRED | `rules/kundalee-bhava-phala-extracted.jsonl` | 144 |

> SRC-030: embedded text from Kundalee software (freeware). 144 bhava-phala rules (lord-in-house), 12×12 grid complete. Extracted verbatim from the binary's UTF-16 string table; no decompilation. NOT validated. Source is compiled software, text is classical BPHS-style — treat as REVIEW_REQUIRED candidates. ID namespace `KU####` (never merged with K-corpus).

| SRC-031 | `Phalit.7z → Phalit.kkk` | freeware-binary | Vedic | EXTRACTED | REVIEW_REQUIRED | `rules/kundalee-muhurta-yogas-extracted.jsonl` | 3 |

> SRC-031: Kundalee (Phalit.exe 9.05.0002, Vinay Jha) embedded Muhurta help (frmHelpMuhurtas), nitya-yoga auspiciousness tiers for electional use: ashubh (Vishkumbha, Atiganda, Shula, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti), madhyama-shubha, atishubha. Devanagari text stored in the DevMithila legacy-font codepage; the three group rows above are BEST-EFFORT transliterations (REVIEW_REQUIRED). Caveats: 'Shubha' appears in both recovered middle & best tiers and the item rendered 'cz' (~Brahma) is uncertain; do not treat as validated. ID namespace `KMY###` (never merged with K-corpus; distinct from `KU####`).

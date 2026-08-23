# AstroOS — Frozen Calculation Modules

Every file below was deep-audited against classical Vedic astrology rules
and, wherever a reference existed, numerically cross-checked against
PyJHora (with the ayanamsa forced to Lahiri — PyJHora's own default is
`TRUE_PUSHYA`, a gotcha this audit repeatedly had to guard against). All
real bugs found were fixed and re-verified. As of the audit date below,
every file in this table has **zero known remaining calculation errors**.

**These files are frozen.** They must not be modified without going
through the unlock process below — a change here, even a small one, can
silently reintroduce a calculation error that took real audit effort to
find and fix.

- Audit completed: 2026-08-24
- Reference chart used throughout: 1995-01-01 12:00:00 UTC, New Delhi
  (28.6139, 77.2090), Lahiri ayanamsa
- Enforcement: `scripts/verify_frozen_modules.py` (run in CI on every
  push/PR — see `.github/workflows/frozen-modules-check.yml`) plus
  `CODEOWNERS`, which requires the repo admin's review on any PR that
  touches a path listed here.

## How to modify a frozen file

1. Get the change reviewed and approved by the admin (`@satyasai2025`) —
   `CODEOWNERS` already enforces this at the PR level.
2. Make the change.
3. Re-run the relevant test suite and, if the change touches a formula,
   re-verify against classical rules / PyJHora the same way the original
   audit did.
4. Regenerate this manifest's hashes: `python scripts/verify_frozen_modules.py --update`
5. Commit the code change and the updated `FROZEN_MODULES.md` together.

Skipping step 4 will fail CI (`frozen-modules-check`) on the PR.

## Manifest

Hashes are SHA-256 of the file's current committed content. Regenerate
with `python scripts/verify_frozen_modules.py --update` after any
admin-approved change.

| File | SHA-256 | Audit note |
|---|---|---|
| `packages/shared/dignity.py` | `402adf912d7aa80aeeab79a057eca9f2d3eb495a340ad2caba100477afbbda75` | Verified exact vs PyJHora/BPHS across all 12 rashis; added opt-in alt_research Moolatrikona convention (default unchanged) |
| `apps/api/services/ashtakavarga_engine.py` | `177d4d364cfd502c4a77c0ff6ed2ee87e46a42ea5059e34b24bb38209c861344` | Rahu/Ketu occupancy bug fixed |
| `apps/api/services/ashtakavarga/shodhana_calculator.py` | `ec0bee56419bb5110bc628bf5d1860415eb9e60dcb6435c12de0cd5ca75a973c` | Ekadhipatya Shodhana formula fixed |
| `apps/api/services/pinda_engine.py` | `6e6e9778a33c04a9e2f56900ec75a2344d4e4091f23a7ae84154700842b7c156` | New engine, verified exact vs PyJHora |
| `apps/api/services/shadbala_engine.py` | `9e4190c8c525fdc6b136f64076b3933bdc7c24c712a17ced264770f041ed7d8a` | Orchestrator, wired to all fixed components |
| `apps/api/services/shadbala/uchcha_bala.py` | `15dbf8629c240a79ec27f6af1de8afa363f849117f9346382ca55409b9b9c634` | Verified correct, no changes needed |
| `apps/api/services/shadbala/saptavargaja_bala.py` | `601ed46fc4dd0a5e199313aa7dcb9a58c2fb65f41045e817adbe769603924da8` | Phantom "exalted" dignity tier fixed |
| `apps/api/services/shadbala/ayana_bala.py` | `99aaab939efb0fb5fd5fc24a16e6593305457b34eace150721805dd08f80c11d` | Rewritten: real Kranti/bhuja formula |
| `apps/api/services/shadbala/dig_bala.py` | `497930fac3519f6de5e0c01e5f62ab7d628656ebd539079c877c88e832beae67` | Verified correct, no changes needed |
| `apps/api/services/shadbala/drik_bala.py` | `5d3b0dc6218b19de632a912af60525ac32f7f6ba01be29ba939d1d97bccab9bf` | Rewritten: full classical piecewise formula |
| `apps/api/services/shadbala/chesta_bala.py` | `9a87f30c29d2d06d0201d6f5a351069d1dd5f7dc0a3bd962e5b837781408fd87` | Rewritten: fixed backwards fast/slow logic |
| `apps/api/services/shadbala/dina_hora_bala.py` | `1db2fd18430d63f804fdf2e224e15522f47c28071b64940b618d41dcc22b6fae` | Hora-lord algorithm fixed |
| `apps/api/services/shadbala/varsha_masa_bala.py` | `c548764ec5387a49e44617fc29eca3b3f03ed0378eda49952cce9dce0c54c3b6` | New engine, verified exact vs PyJHora |
| `apps/api/services/divisional_engine.py` | `d79fbad496540f52bb27da8587a3cbb1073ada4a2306c3bfd418b3ec8dd538c0` | D60 formula fixed |
| `apps/api/services/dasha_engine.py` | `191a2d5ecc762c788767116f7c97f0888dcb54862c71d68c84d727da56e31cc7` | Chara direction + full Narayana rewrite |
| `apps/api/services/jaimini_dasha_adapter.py` | `0dfb7ad954e2d6a52ef70ac48c9a5046b448aa747d9c047124e680968b6d32b4` | Verified correct, docstring clarified |
| `apps/api/services/muhurta_engine.py` | `c3719455479349fd2c5ee8ffc81cec28f447e85a4923c6b57ac1da78a1fa0ff2` | Choghadiya night-sequence direction fixed |
| `apps/api/services/badhaka_maraka_engine.py` | `a2f75a05f72bf8043f8ddd2d91a307320bd489ed215df15ac96a29d935bcd00c` | New engine, verified against classical rule |
| `apps/api/services/yogas/arishta_yoga.py` | `2ba2968bd1ebe23bc6cde4eb8339c2b93b56823e6b9d659deea35453ae7db20e` | Aspect-vs-conjunction rule fixed |
| `apps/api/services/yogas/chandra_yoga.py` | `9a212b861e4847533a5f9bae85f5abe703e1d5945cf0dc4649fbdd73914e2c7e` | Chandra-Mangala + Kemadruma fixed |
| `apps/api/services/prediction_confluence_engine.py` | `6f6a523ff3ef97b70de3592583724b1ac3e3e5f8f345c925d9cc69ccbe990f1f` | Fake SBC transit fallback fixed |
| `apps/api/schemas/kp.py` | `a05ef580132644030317c08c6d97fe29b98fb72810fecb78f25bc1bd0f4e7d8f` | House-system default fixed |
| `apps/api/services/ephemeris_wrapper.py` | `e1deaf237d1370c7eaa6c55f6cf941504bc337d3c45502cd19b657c114e3c5d3` | Vara sunrise-boundary fix; nakshatra/sub-lord math verified exact |
| `apps/api/services/horoscope_engine.py` | `80727e36fae80d47e428edc8100b0604746b42b9877a2124fc35f3945d60ca65` | node_type threading verified |
| `apps/api/services/transit_engine.py` | `0cfbd43eb32f91784959245abf102f2e6c863a04abf683abade28534dcff0fcd` | Real house_from_natal_ascendant added |
| `apps/api/services/transit_patterns.py` | `36c2266b62824556c9d78f5459782fcadd4f378f296c430fcd73db5d182a9cf8` | Rahu/Ketu return-date backward-motion fix |
| `apps/api/services/transit_timeline_engine.py` | `f4ebb76f8e6a18543f2305fc0ff1c2ff673908983eb204c25a82bda06b7409eb` | Ascendant-house fake-duplicate fixed |
| `apps/api/services/synastry_engine.py` | `5d26f21a52d2fe4dafc5cbd89cd7ac4523b6d82423eb3c3053515e63c7495e8a` | Graha Maitri/Yoni/Gana/fake-fallback fixed |
| `apps/api/services/rectification_engine.py` | `8d355b6b0ac66e459fa7007aed2449d973074ba45a9a23c1ff813ede91bb003c` | Fake transit-score constant fixed |
| `apps/api/services/graha_engine.py` | `7bafd4add72594fe68cd37e1ce515dbc378fcefa4fa6525343fce018f1282e80` | Verified clean |
| `apps/api/services/house_engine.py` | `6f97e60d5a14240aeec8bffcd272faa7da921571c93291ddeb6933b06217eceb` | Verified clean |
| `apps/api/services/aspect_engine.py` | `337d16f0cee72bffb6b16dbecc94855a5a563d16f3c42f63ba78de814dd60346` | Verified clean |
| `apps/api/services/sphuta_drishti_engine.py` | `7590060082d0342e3a795dee0bf2e58955c6901b4ae75bcadc5223a2e0ff2600` | Piecewise discontinuities fixed |
| `apps/api/services/upagraha_engine.py` | `6b7ca9826558bcff337a097755fefdad217998479fc66d168f8c236d4e24a08a` | Verified correct; scope gap disclosed |
| `apps/api/services/sadhu_padhdhati_engine.py` | `836aa1cd601a2ef84067a215c8a79eb89ad684db0b72a2dc1c9943728b3e725a` | Boundary-year + citation bugs fixed |
| `apps/api/services/kp_engine.py` | `24d75ed499527c8571cc5a8883e4f8f8f1c26750666575e974b8e2ce8d8c994e` | Verified clean |
| `apps/api/services/kp_btr_engine.py` | `630c8b955c36404d23868f103bb0e92b717e024d1b381142f3a624e674f66c2a` | Docstring/implementation mismatch fixed |
| `apps/api/services/kp_decision_tree_engine.py` | `3d324cdd8b5e967553771bf0dd9fd57e0c57655f456e21a9bf101bfc5782b2f6` | Fabricated fallback data fixed |
| `apps/api/services/kp_rp_engine.py` | `ac5273c13193304c128bf4f50507e14d501113da841e49abdbaf84cbdb51baf7` | Day Lord sunrise-basis fixed |
| `apps/api/services/arudha_engine.py` | `dbfa0041a3866b83811cf08dd2d940ea1e4d96abb58adbb9f2e81d780d1cfa90` | Verified clean |
| `apps/api/services/argala_engine.py` | `23f0c782d68c967fd6a6ab1de97214facba193ac5b2b77a4751d3e3d9313fdd6` | Verified clean |
| `apps/api/services/karakamsa_engine.py` | `a1110c0744ea6c18eca83f0ae4ed94525bb4baf2030b17634dc4626a02fc920c` | Verified clean |
| `apps/api/services/rashi_aspect_engine.py` | `7b00083a0da0413e81778d4fceff6f6cfaae90185be5d3c0700fb23e79ddb328` | Verified clean |
| `apps/api/services/event_engine.py` | `577efd94d9a76f0b35deec60353f6f17f9ad194386e4df926c7d325ca2658a76` | Verified clean |
| `apps/api/services/event_analysis_engine.py` | `388dc4f3e118735889b1bb2131ea9eb633546396655d6f310345ad0e7e5ac9b9` | Verified clean |
| `apps/api/services/unified_event_timing_engine.py` | `0da9972e484b140e45b5a24053f326e41abe9d85ebf8bdf61bc9ddadee38e8f6` | Verified clean |
| `apps/api/services/multi_dasha_confluence_engine.py` | `685d85067e36205a998b978f900dfadf8e4b014909429dba3f79bc4b0c6da8b0` | Critical fabricated-data bug fixed |
| `apps/api/services/lagna_scan_engine.py` | `8355d1248f7807b78d808d5cfbebeee78fc546e74ca29359e91cf99f970c39f2` | Verified clean |
| `apps/api/services/sign_change_engine.py` | `d4628bb8e267817f85a8ffd433ed76a72f57fdf1b9c43f6d997e6f93902c8db7` | Verified clean |
| `apps/api/services/yoga_engine.py` | `cce4d59ae4064988012a4aa31f320069fda753976bb4c9eb060ef117cdfba3ae` | Verified clean |
| `apps/api/services/yoga_strength.py` | `479a80f86f4f42082e50705efb3fb464366a27773dbfebc3cac6ca403e7a2123` | Kendra-house scoring asymmetry fixed |
| `apps/api/services/vimsopaka_engine.py` | `3f5168da3d39c89ba2773c2b7963162eec4d347840b2e74c923e12e37783d788` | Fabricated-fallback dignity fixed |
| `apps/api/services/ashtakoota_engine.py` | `24b21d639f08809e9419008568aa48800ef3cabbc8d57e59b34f0a8110cb93e9` | Gana/Bhakoot bugs fixed |
| `apps/api/services/marriage_timing_engine.py` | `397a98ceb22bcc6ed4bfc6ff693a4b0e5c2b6ce785735e066161d5aa242d2ee0` | Verified clean |
| `apps/api/services/sbc_vedha_engine.py` | `a0829c712db416fa366d81d066f54d67193a805154cee02839306aaa9908821e` | Verified clean |
| `apps/api/services/sbc_ray_matrix_engine.py` | `95ace8c21a35bbfae0884e8c3d36b8b4da2baa8a9012cec36298915352b5759a` | Fake-transit-fallback landmine removed |
| `apps/api/services/tarabala_report_service.py` | `b1b5c96669faca38f3c116eb8716a57d8366756b4889a6fd3ee20fc88c4c7fcb` | Verified clean |

## Explicitly NOT frozen (known remaining gaps)

- `apps/api/services/prashna_engine.py` — Hora/Day Lord, relevant_houses,
  and transit_support/moon_cycle bugs are fixed, but the overall
  judgement score/verdict is still only partially chart-driven (most of
  its weight comes from question-category text matching, not real
  planetary computation). Do not freeze until that scoring redesign is
  done.
- Any file under `apps/api/services/` not listed above has not yet been
  through this audit process — absence from this list is not a claim of
  correctness, just "not yet checked."

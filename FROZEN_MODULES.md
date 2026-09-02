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
| `apps/api/services/dasha_engine.py` | `f28bab5c7a607696b710ed2830bfc7a72e1bd134c1791aa0795ded9048139a71` | Strengthened content_hash with full tree signature + tz-awareness enforcement + boundary float-precision guard |
| `apps/api/services/jaimini_dasha_adapter.py` | `0dfb7ad954e2d6a52ef70ac48c9a5046b448aa747d9c047124e680968b6d32b4` | Verified correct, docstring clarified |
| `apps/api/services/muhurta_engine.py` | `99469dccaa6d21fda777a3d23f190ed57c128429679a844d414f84c753499183` | Choghadiya night-sequence direction fixed |
| `apps/api/services/badhaka_maraka_engine.py` | `a2f75a05f72bf8043f8ddd2d91a307320bd489ed215df15ac96a29d935bcd00c` | New engine, verified against classical rule |
| `apps/api/services/yogas/arishta_yoga.py` | `2ba2968bd1ebe23bc6cde4eb8339c2b93b56823e6b9d659deea35453ae7db20e` | Aspect-vs-conjunction rule fixed |
| `apps/api/services/yogas/chandra_yoga.py` | `9a212b861e4847533a5f9bae85f5abe703e1d5945cf0dc4649fbdd73914e2c7e` | Chandra-Mangala + Kemadruma fixed |
| `apps/api/services/prediction_confluence_engine.py` | `6f6a523ff3ef97b70de3592583724b1ac3e3e5f8f345c925d9cc69ccbe990f1f` | Fake SBC transit fallback fixed |
| `apps/api/schemas/kp.py` | `e6883e5e3840dcc859e6e118a0e193a24e74788b166556eae18bb483bcbdcf7d` | House-system default fixed |
| `apps/api/services/ephemeris_wrapper.py` | `8af60e052bafde3c56ae0445d4815f93d017ccf8b3fc6677399d7312d41c46a1` | Hardening audit: removed silent ayanamsa/node fallbacks, added directional Mercury combustion orb (12° direct, 14° retro), Whole-Sign tropical/sidereal cusp consistency, exact nakshatra boundary float-precision guard; verified error-free |
| `apps/api/services/horoscope_engine.py` | `80727e36fae80d47e428edc8100b0604746b42b9877a2124fc35f3945d60ca65` | node_type threading verified |
| `apps/api/services/transit_engine.py` | `0cfbd43eb32f91784959245abf102f2e6c863a04abf683abade28534dcff0fcd` | Real house_from_natal_ascendant added |
| `apps/api/services/transit_patterns.py` | `36c2266b62824556c9d78f5459782fcadd4f378f296c430fcd73db5d182a9cf8` | Rahu/Ketu return-date backward-motion fix |
| `apps/api/services/transit_timeline_engine.py` | `f4ebb76f8e6a18543f2305fc0ff1c2ff673908983eb204c25a82bda06b7409eb` | Ascendant-house fake-duplicate fixed |
| `apps/api/services/synastry_engine.py` | `5d26f21a52d2fe4dafc5cbd89cd7ac4523b6d82423eb3c3053515e63c7495e8a` | Graha Maitri/Yoni/Gana/fake-fallback fixed |
| `apps/api/services/rectification_engine.py` | `86367c7a40b0f3243acc876238ee4304eec03c184f9a9dd90fd5ea31cc359f2c` | Safe `.contains()` boundary check for DashaPeriod datetime spine compatibility; zero calculation change |
| `apps/api/services/graha_engine.py` | `7bafd4add72594fe68cd37e1ce515dbc378fcefa4fa6525343fce018f1282e80` | Verified clean |
| `apps/api/services/house_engine.py` | `6f97e60d5a14240aeec8bffcd272faa7da921571c93291ddeb6933b06217eceb` | Verified clean |
| `apps/api/services/aspect_engine.py` | `337d16f0cee72bffb6b16dbecc94855a5a563d16f3c42f63ba78de814dd60346` | Verified clean |
| `apps/api/services/sphuta_drishti_engine.py` | `7590060082d0342e3a795dee0bf2e58955c6901b4ae75bcadc5223a2e0ff2600` | Piecewise discontinuities fixed |
| `apps/api/services/upagraha_engine.py` | `0b6f037437ec2aef36044c22567e53bc78d7ec418848466cab41f3ce2227ebf7` | Added canonical `compute()` returning `UpagrahaResult` with wrapper sunrise-anchoring for JHora report; Arkadoshas & BPHS Upachaya rules preserved |
| `apps/api/services/sadhu_padhdhati_engine.py` | `836aa1cd601a2ef84067a215c8a79eb89ad684db0b72a2dc1c9943728b3e725a` | Boundary-year + citation bugs fixed |
| `apps/api/services/kp_engine.py` | `20d176ebe5641291417dc4955cef2f1a11bd2d4aaa2ceba104c673a3834a7f9b` | Replaced raw `<=` comparisons with `p.contains(now)` and `start_date_only` for DashaPeriod datetime spine compatibility |
| `apps/api/services/kp_btr_engine.py` | `630c8b955c36404d23868f103bb0e92b717e024d1b381142f3a624e674f66c2a` | Docstring/implementation mismatch fixed |
| `apps/api/services/kp_decision_tree_engine.py` | `3d324cdd8b5e967553771bf0dd9fd57e0c57655f456e21a9bf101bfc5782b2f6` | Fabricated fallback data fixed |
| `apps/api/services/kp_rp_engine.py` | `23efef7275f5e3e0e86e32afaa09c02b484678c20ee6cbb30093b4324b0aecde` | Day Lord sunrise-basis fixed |
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
| `apps/api/services/tajaka_constants.py` | `6b8a629050aa5081a163351fc2cfdaf38cf93c4d71757b7c7c0d7dced02cde9f` | Classical Deeptamsha orbs & 12-sign Hadda table constants |
| `apps/api/services/tajaka_bala_engine.py` | `13f1ebcb7a6a128c9b596d63cb90b70cd76a97143f54300b592648907780ff19` | Panchavargiya Bala (5-fold Tajika strength & Visheshika scale) |
| `apps/api/services/tajaka_yoga_engine.py` | `317c8ddb30d5a324de7fa6f92a2eae495511da23c2db99ffa53d56f5be592af9` | 16 Classical Tajika Yogas (Shodasha Yogas) engine |
| `apps/api/services/tajaka_dasha_engine.py` | `cb41986b6a5f742316e074056d35d6b04893592edc37f050af719164b30ba568` | Mudda & Patyayini annual dasha engine |
| `apps/api/services/terminology_service.py` | `432a7cb7e9d3cfad105a27c4b35b7e8fcdccdbaaee77d91fedae423e27c85100` | Unified Sanskrit/English astrological terminology resolver & query expander |
| `apps/api/services/claim_grounding_validator.py` | `ae72b41adeb6e2d2e550960b60ab9d46ae25e3bf3b185b346291ffcfe82ee77c` | Claim grounding & hallucination prevention validator |
| `apps/api/services/ai_evaluation_framework.py` | `5fb9ff558911952f94ff6ef167b7385a2deea3ff10b8f9b6c9e52430c7de69b9` | AI grounding & governance benchmarking evaluation harness |
| `apps/api/services/kuja_dosha_engine.py` | `4e7e3272b2113ee4b3e05164bed3c21693f744c93e69b4dec1365eb08db95820` | Comprehensive Tri-Bhava Kuja Dosha (Lagna, Moon, Venus) & 10 classical pariharas |
| `apps/api/services/dasa_kuta_engine.py` | `b13167c34e2c67130e82bdc2a046a4799db12b000899f01f601523e0e290ddfa` | South Indian 10-Poruthams compatibility system including Rajju & Vedha |
| `apps/api/services/jaimini_navamsha_synastry.py` | `6bdb0af758b1674990c6d7577dd2fedc4375912cabfe61326db15f8d533f7a67` | Jaimini Upapada Lagna (A12) & D9 Navamsha synastry harmony engine |
| `apps/api/services/composite_chart_engine.py` | `ad45f1c82581459cabb560fce777d5667cfa6d557027bf07ef7fb22821436e5b` | Shortest-arc circular midpoint composite relationship chart engine |
| `apps/api/services/mundane_ingress_engine.py` | `9be10eae61e3d2f228dcfcf914f966ba1213694d2216275891e711e474a957e7` | High-precision Chaitra Shukla Pratipada & 4 cardinal solar ingresses solver |
| `apps/api/services/planetary_cabinet_engine.py` | `b58425c94225689ec362672340820d8c335502a4c8ee0c0c8031ece612d6632f` | Classical 9-minister cosmic governance council (Nava Nayakas) engine |
| `apps/api/services/mundane_eclipse_engine.py` | `0e54f52970b791a3e6baa32234715555d6fbb52da94bfa7e0fe8d95e59726c65` | Standalone solar & lunar eclipse detection and mundane impact duration engine |
| `apps/api/services/kurma_chakra_engine.py` | `43fc38c12a7b32ffa32ed77c8705ade00a5eeb612bfd00e8715121cc6e3abbba` | 9-sector celestial tortoise (Kurma Chakra) geopolitical & seismic engine |
| `apps/api/services/mundane_analysis_engine.py` | `82fef689567a6c96fa76a9cf9eec49be84722b79662108c91d08f5388ffa64ee` | 12 Mundane Bhavas & comprehensive national forecasting engine |
| `apps/api/services/jaimini_special_dashas.py` | `788bcaa0cf2daf8df06c43688659e4bb3bb29fec42411daa7d6fcb8f9cf8b220` | Classical Shoola Dasha (9-year longevity/maraka) & Mandooka Dasha (frog-jump D11) |
| `apps/api/services/jaimini_upapada_engine.py` | `027be93481146f1fedee1e5570ff310b1fe2999c704477f4d7f33d5db6ac2ec9` | In-depth native Upapada Lagna (UL) 2nd/8th house longevity & stability analysis |
| `apps/api/services/jaimini_expanded_yogas.py` | `68708de89485ee3897affbb6f0fbea5731a24edc07b275c65081b9f3615b9b90` | Classical Jaimini Raja, Dhana (AK-PK, AmK-DK, AL-A11), Vipareeta, & Moksha yogas |
| `apps/api/services/jaimini_event_timing_engine.py` | `cbbaf045b8ca0ff4d94d44a55cd81835698c21954102ad1237fa321777943058` | Predictive event-timing synthesizing Jaimini Dashas, Karakas, & Arudhas |
| `apps/api/services/intelligence/strength_model.py` | `994afb1a61a7f7f8d341230aad9fe0f9c2b0cafff86ff5a830f4cf4194eb0004` | Discrete 1-9 Dignities with Base-2 Exponential Strength Mapping (1.0 to 256.0) |
| `apps/api/services/intelligence/drishti_model.py` | `06b19b450045ce3f81f185b8edd0e29f214d7233fbfde2aadc64741de73bc77e` | Standard 7th and special Parashari planetary aspects (Mars 4/8, Jup 5/9, Sat 3/10) |
| `apps/api/services/intelligence/upagraha_rules.py` | `d224c6966e98e5e2747daeebc6254be90c5f98913fbb8032b7ae8845c545e023` | Vinay Jha Gulika (Upachaya boost / 8th Mrityu weight) & Mandi (7th delay) rules |
| `apps/api/services/intelligence/linked_system.py` | `914bdb8358583a95bf140a1b5cfac482b4f8d79e69d2325aee94252ed4b22c43` | Relational LinkedChartGraph with Sudarshana (Lagna + Chandra Lagna) synthesis |
| `apps/api/services/intelligence/cognitive_reasoner.py` | `79c23ba6165a7e5dabda6513c6d77ef0db747a599e16e703be45289e00a88326` | 5-Level Vimshottari Dasha confluence evaluator (0 to 9 Cognitive Score) |
| `apps/api/services/intelligence/events/marriage.py` | `ebd76595ec343780e9b357fbe539dcab0285768fbe7ca5af325f341cba2818fc` | Shastric Marriage Timing & Delay predictor (7th house + Shukra/Guru + Mandi) |
| `apps/api/services/intelligence/events/career.py` | `53ed8b0174bd495bd9d468893ec1adc4b69a185e0fe754c01373917ef71d75f7` | Career Elevation & Status predictor (10th house + Artha trikonas + Gulika boost) |
| `apps/api/services/intelligence/events/health.py` | `9d700a46b5a3063def3a929e5b7e87b8659bf0d7ba4ce79f6597cebbd9650ca1` | Health Crisis & Illness predictor (6th/8th house + Marakas + Gulika 8th weight) |
| `apps/api/services/intelligence/events/accident.py` | `c6e879c6a7a40702b1afa848d3a5d627637f94f47800f9757e6a8c85e02c0b3d` | Accident & Sudden Trauma predictor (8th house + Mars/Rahu + trauma indicators) |
| `apps/api/services/phalita_core/expert_registry.py` | `afc367d914081845f5277a6146e3c365feabcb896b72fa15cb42b06f512d732e` | 4 Specialized Shastric Experts (Structural, Divisional, Temporal, Upagraha) |
| `apps/api/services/phalita_core/expert_router.py` | `246fd1e331657a3d3dec751c14c0050ef15efe9d4d530c5bc36d4495dc7df2e4` | Softmax Gating Router for 12-domain adaptive attention weight distribution |
| `apps/api/services/phalita_core/conflict_resolution.py` | `437d13205763faaeebdee803c516c01baf677b7ef2adaffe40d4f498af4cbc37` | Classical Parashari Conflict Resolution Hierarchy (Temporal Primacy, Delay vs Denial) |
| `apps/api/services/phalita_core/phalita_moe_orchestrator.py` | `c6ea7d2b2e024e15022992e8080ad78cb0394915e6a4204a486ea9d1e9f0d183` | Master Phalita MoE Consultation Orchestrator emitting consultation verdict |
| `apps/api/services/phalita_core/domain_significators.py` | `48b73bfdb054e6a9715be6e5d5bfa07cbe12197baf48a5aee22cb2145ea677e0` | Complete 12-Bhava Life Domain Registry & Significator Matrix |
| `apps/api/services/divisional_vimshottari_engine.py` | `b9cb981d2e84fb40eacb75b8cd362a77a54cf82d5aecbfc067f690deb7b19695` | Independent Divisional (D9, D10, D7, D4, D30) Vimshottari Dasha Engine (updated to `p.contains(target_date)` for datetime spine compatibility) |
| `apps/api/services/phalita_core/varga_strength_fusion.py` | `47f3541956d6c30b4066ff86afec596a356d66f6de47b0ce3ac355704a25fcaf` | Log-Base-2 Main Strength x Vimshopaka Final Varga Fusion & Neecha Bhanga Engine |
| `apps/api/services/phalita_core/bhavottama_engine.py` | `8e420b7f1c4096580e47ed85f20e61370b38c718d98ed8b283228dccb8ad2100` | Bhavottama (Kimshukadi) Same-Bhava Detection & Quality Multiplier Engine |
| `apps/api/services/phalita_core/transit_trigger_engine.py` | `82bf043e102f584ffb047b053c7e776fc25c94070f5f1eb34da847fc9436aeb7` | Transit (Gochara) & Ashtakavarga Rekha Trigger Engine |
| `apps/api/services/phalita_core/divisional_explorer_service.py` | `4ae30b1af90bfcf4cf79231a4457211e5458665a5f3b6b4c7a00a869b170e102` | Multi-Varga Interactive Explorer & Dual-Dasha Confluence Engine |
| `apps/api/services/phalita_core/karakamsha_synthesis_engine.py` | `21650dc2450815a1ef1a02d7e1b9f60a4c91f3437392e3cd26253aec59c60fcf` | Karakamsha Lagna & 7-Chara Karaka Jaimini Synthesis Engine |
| `apps/api/services/phalita_core/historical_backtest_harness.py` | `25aec0b6c3cbbc2bf3fd89cae1911adf7d42bae8ec7e828f5a8a2f2ee6d8c662` | Empirical Benchmark Backtesting & Accuracy Audit Harness (updated to `p.contains(target_d)` for dasha matching; zero scoring changes) |
| `apps/api/services/phalita_core/canonical_facts_generator.py` | `cbab38bac1e7d56c173f1dc39892250b589246fca9423c94799c84a3362adcf1` | Calculation-Only Canonical Facts Ground Truth Generator (updated to `p.contains(t_date)` for datetime spine compatibility) |
| `apps/api/services/phalita_core/technique_resolver.py` | `f3861fe366ca4c8e2110c8dcec921bc0bf720512b3c4334140462cc6cab046ca` | Domain-Tailored Shastric Technique Resolution Engine |
| `apps/api/services/phalita_core/shastric_rule_engine.py` | `25c74af6a6c7bdeae4e77469b73aab4587a5eccada67799f901bea89219ee8aa` | Declarative Shastric Rule Evaluation & Provenance Engine |
| `apps/api/services/phalita_core/evidence_aggregator.py` | `fb6cc7103b34250940278a324804bc4170a67b0a95cd3bc8f5e1ad466d02210a` | Evidence Aggregator & Provenance Registry |
| `apps/api/services/phalita_core/prediction_calibrator.py` | `26493daf9637c5cadaff803c706bf228cb02a8125f2c5768e407b41f26d53121` | Calibrated Prediction Engine (Emitting Calibrated Signal Score 0-9) |
| `apps/api/services/phalita_core/shastric_explanation_narrator.py` | `7cd827d2dc50c7913259b1c6e1c0e0f0b58095af315e911389e242b03a4daa0e` | Grounded AI Shastric Explanation & Citation Narrator |
| `apps/api/services/phalita_core/shastric_reasoning_pipeline.py` | `e3921a80bedd13fa37d12cb05196807b613f1906dd5fc214ec3c9a44b6b7352b` | Master End-to-End Shastric Reasoning Orchestrator |
| `apps/api/services/phalita_core/three_tier_validation_framework.py` | `0bdbda49ccdec194c96627e72ba6d3db12111bb89e83964efff4d417586946ce` | 3-Tier Validation Framework (N=5 Regression, N=600 Generalization, N=100 Holdout) |




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


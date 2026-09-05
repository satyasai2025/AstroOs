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
| `apps/api/services/ashtakavarga_engine.py` | `ef5e136d092f037f86cba408fa7be95ce167e66337d7ccc50ca15c32e5994058` | Rahu/Ketu occupancy bug fixed |
| `apps/api/services/ashtakavarga/shodhana_calculator.py` | `bfbccab93df958cb86a45912603c0295ecefe446d1113b61cab7986e90ce5f84` | Ekadhipatya Shodhana formula fixed |
| `apps/api/services/pinda_engine.py` | `6e6e9778a33c04a9e2f56900ec75a2344d4e4091f23a7ae84154700842b7c156` | New engine, verified exact vs PyJHora |
| `apps/api/services/shadbala_engine.py` | `9e4190c8c525fdc6b136f64076b3933bdc7c24c712a17ced264770f041ed7d8a` | Orchestrator, wired to all fixed components |
| `apps/api/services/shadbala/uchcha_bala.py` | `8997bf522467c182f4f6391da00b479e59db3fc986517841a099afef09dbc182` | Verified correct, no changes needed |
| `apps/api/services/shadbala/saptavargaja_bala.py` | `601ed46fc4dd0a5e199313aa7dcb9a58c2fb65f41045e817adbe769603924da8` | Phantom "exalted" dignity tier fixed |
| `apps/api/services/shadbala/ayana_bala.py` | `99aaab939efb0fb5fd5fc24a16e6593305457b34eace150721805dd08f80c11d` | Rewritten: real Kranti/bhuja formula |
| `apps/api/services/shadbala/dig_bala.py` | `c00ff662c4b6edc0f4ceb41208a69842c764a2019123af440781071590bd5468` | Verified correct, no changes needed |
| `apps/api/services/shadbala/drik_bala.py` | `5d3b0dc6218b19de632a912af60525ac32f7f6ba01be29ba939d1d97bccab9bf` | Rewritten: full classical piecewise formula |
| `apps/api/services/shadbala/chesta_bala.py` | `9a87f30c29d2d06d0201d6f5a351069d1dd5f7dc0a3bd962e5b837781408fd87` | Rewritten: fixed backwards fast/slow logic |
| `apps/api/services/shadbala/dina_hora_bala.py` | `0a255c3cd503249ceb77604ed446c769a935ac48fe9b9ee4a5f99fc22f87307a` | Hora-lord algorithm fixed |
| `apps/api/services/shadbala/varsha_masa_bala.py` | `c548764ec5387a49e44617fc29eca3b3f03ed0378eda49952cce9dce0c54c3b6` | New engine, verified exact vs PyJHora |
| `apps/api/services/divisional_engine.py` | `0c8ec2c3328352166d44496f6856625a0b0a138e1ae8bee3a5bdf47027dfdfdb` | D60 formula fixed |
| `apps/api/services/dasha_engine.py` | `8996b1d054af5059095ee29a74a9740066b50d66a958241d0b833362c29ae025` | Strengthened content_hash with full tree signature + tz-awareness enforcement + boundary float-precision guard |
| `apps/api/services/jaimini_dasha_adapter.py` | `18626951af0f3ef1e5f58beca84a911b194690aeb7bf0c4673d910ffb7a09c4a` | Verified correct, docstring clarified |
| `apps/api/services/muhurta_engine.py` | `7776458af7dc085203693e8e2c72e016378b30b3921b846fcd4231629dac2e30` | Choghadiya night-sequence direction fixed |
| `apps/api/services/badhaka_maraka_engine.py` | `a2f75a05f72bf8043f8ddd2d91a307320bd489ed215df15ac96a29d935bcd00c` | New engine, verified against classical rule |
| `apps/api/services/yogas/arishta_yoga.py` | `2ba2968bd1ebe23bc6cde4eb8339c2b93b56823e6b9d659deea35453ae7db20e` | Aspect-vs-conjunction rule fixed |
| `apps/api/services/yogas/chandra_yoga.py` | `77bd7ba524c01a5e6cb21763d36036f437bbb407e5abb0eb648edb681088609e` | Chandra-Mangala + Kemadruma fixed |
| `apps/api/services/prediction_confluence_engine.py` | `6f6a523ff3ef97b70de3592583724b1ac3e3e5f8f345c925d9cc69ccbe990f1f` | Fake SBC transit fallback fixed |
| `apps/api/schemas/kp.py` | `337c051e70472818631124e7c1c8c3d2b3cde97f5f4500f81b3d6511e48589e4` | House-system default fixed |
| `apps/api/services/ephemeris_wrapper.py` | `0561b9f796b9a55673186dac3c0cf9e37784ba7c1eb2fa5e1fe3eb6f8bb0319a` | Hardening audit: removed silent ayanamsa/node fallbacks, added directional Mercury combustion orb (12° direct, 14° retro), Whole-Sign tropical/sidereal cusp consistency, exact nakshatra boundary float-precision guard; verified error-free |
| `apps/api/services/horoscope_engine.py` | `bb55e346ca89f417a46112dd31ca0b1496e775a65d5133199a7ca07bd695aff5` | node_type threading verified |
| `apps/api/services/transit_engine.py` | `14c96ce9aee9da848a575c88411908448f2b3c1b003eb93adce520c7a6f3371b` | Real house_from_natal_ascendant added |
| `apps/api/services/transit_patterns.py` | `bd437d39ee309a8b6ae964c0da94d3308933dc9d0f7a785a183a7affb71dbb13` | Rahu/Ketu return-date backward-motion fix |
| `apps/api/services/transit_timeline_engine.py` | `0cc621870456dcf7f17df55d49a230a29bfaa214fe6410a40790eaa31503132e` | Ascendant-house fake-duplicate fixed |
| `apps/api/services/synastry_engine.py` | `7548b734bb8082e8890e4b9aa4182c32d641ccc6e7d125339c02e57bf3cbe51d` | Graha Maitri/Yoni/Gana/fake-fallback fixed |
| `apps/api/services/rectification_engine.py` | `d956ed23e763910a15c28ae4f42956f0191d392c7f2d4d9a8b9eb192535f5389` | Safe `.contains()` boundary check for DashaPeriod datetime spine compatibility; zero calculation change |
| `apps/api/services/graha_engine.py` | `41f88bb48c7fd03bbec4ff120f3780a239de1f50afde24a37a0e91a672e5204e` | Verified clean |
| `apps/api/services/house_engine.py` | `6f97e60d5a14240aeec8bffcd272faa7da921571c93291ddeb6933b06217eceb` | Verified clean |
| `apps/api/services/aspect_engine.py` | `68bade09d176883efbb5ec67847ad952082356c256bc42865d2b1f5fca1de2c1` | Verified clean |
| `apps/api/services/sphuta_drishti_engine.py` | `b16f58a075fc1f2b7c4e53055b5c7bd72a6fb5d11e24e580c5a68b72b1cc4309` | Piecewise discontinuities fixed |
| `apps/api/services/upagraha_engine.py` | `0b6f037437ec2aef36044c22567e53bc78d7ec418848466cab41f3ce2227ebf7` | Added canonical `compute()` returning `UpagrahaResult` with wrapper sunrise-anchoring for JHora report; Arkadoshas & BPHS Upachaya rules preserved |
| `apps/api/services/sadhu_padhdhati_engine.py` | `26c9a08f93b6c4039822ea3582925e4ddd97a77fa719551960a2e8b8dedab8ac` | Boundary-year + citation bugs fixed |
| `apps/api/services/kp_engine.py` | `f08234a6ab47475e3c96b24bfad718ffab5947fed0cd9caa932079f82477ea7d` | Replaced raw `<=` comparisons with `p.contains(now)` and `start_date_only` for DashaPeriod datetime spine compatibility |
| `apps/api/services/kp_btr_engine.py` | `e864d4863098bc7ad54a5ca354760dfe84a2e711948048005b731e8f500dd86f` | Docstring/implementation mismatch fixed |
| `apps/api/services/kp_decision_tree_engine.py` | `3cf3af3adeeb4716f536fc66426c9c45226159aa075b94ddec22f9421282ecc3` | Fabricated fallback data fixed |
| `apps/api/services/kp_rp_engine.py` | `6969808d3a7e8b2c65ffa12c3775e06ed10a734bd2633443b2a08e4bea231ebf` | Day Lord sunrise-basis fixed |
| `apps/api/services/arudha_engine.py` | `5c8d960fde46f66ab884b5554809353fa1b905e9589304e5a88767ed82a33c4e` | Verified clean |
| `apps/api/services/argala_engine.py` | `ae9412a3cf38954cbbf3e0dcb71f53065ab0b1971f836bef0da2fc847bda3658` | Verified clean |
| `apps/api/services/karakamsa_engine.py` | `73e6cd00a8b55ff778b182bf3110b13df1a321a32f38a4171e258137b5bd4d86` | Verified clean |
| `apps/api/services/rashi_aspect_engine.py` | `0675c290fd3f1e003d6787b170af23dfaec826c432f7b8fb2dd432d35dddb0fb` | Verified clean |
| `apps/api/services/event_engine.py` | `eafb7376b584cf64649afe678c724ac49616fe4e9044d0d5696ec9f840af04ad` | Verified clean |
| `apps/api/services/event_analysis_engine.py` | `6ef97c4a242bf381699a63635c6ba4baa27b23693d4af2d774ed8f829abe37f2` | Verified clean |
| `apps/api/services/unified_event_timing_engine.py` | `0da9972e484b140e45b5a24053f326e41abe9d85ebf8bdf61bc9ddadee38e8f6` | Verified clean |
| `apps/api/services/multi_dasha_confluence_engine.py` | `d97ea4f7a28c4652b7793dbe203f6ba828264bd20adeafddbe08d4f56578674b` | Critical fabricated-data bug fixed |
| `apps/api/services/lagna_scan_engine.py` | `a8f1b2d8643047239e86e6550dd136dc23545a4bb9c35eb26af8b2a5702fdaff` | Verified clean |
| `apps/api/services/sign_change_engine.py` | `bd51d8c811cb5c96d62f30bbb2e76c7f80f41f304df543c2820feaf945bc61dd` | Verified clean |
| `apps/api/services/yoga_engine.py` | `cce4d59ae4064988012a4aa31f320069fda753976bb4c9eb060ef117cdfba3ae` | Verified clean |
| `apps/api/services/yoga_strength.py` | `a569ebfa0032af9c1ee5a41ae25f80f38f3aa62f4cb03eb284d9a8ec5b8f1b5a` | Kendra-house scoring asymmetry fixed |
| `apps/api/services/vimsopaka_engine.py` | `3f5168da3d39c89ba2773c2b7963162eec4d347840b2e74c923e12e37783d788` | Fabricated-fallback dignity fixed |
| `apps/api/services/ashtakoota_engine.py` | `3b505740f40ea892033da88759766443e607439a307c1a8c49b9393bf9767c7c` | Gana/Bhakoot bugs fixed |
| `apps/api/services/marriage_timing_engine.py` | `e71feaee7b662fe6786c52b9c185623560ebed710c7c993dabf4ef0c31895dac` | Verified clean |
| `apps/api/services/sbc_vedha_engine.py` | `b51718ddea495f755babc55a30d8bc7e98c46cf8d033ecaf698c10d3db6b2a84` | Verified clean |
| `apps/api/services/sbc_ray_matrix_engine.py` | `95ace8c21a35bbfae0884e8c3d36b8b4da2baa8a9012cec36298915352b5759a` | Fake-transit-fallback landmine removed |
| `apps/api/services/tarabala_report_service.py` | `331f23c5b4ddb40f7c7ce8f3ab1cc30e7c7c8b64c4165113baf02dae02b9f2d8` | Verified clean |
| `apps/api/services/tajaka_constants.py` | `6b8a629050aa5081a163351fc2cfdaf38cf93c4d71757b7c7c0d7dced02cde9f` | Classical Deeptamsha orbs & 12-sign Hadda table constants |
| `apps/api/services/tajaka_bala_engine.py` | `26e8a67a3e009373473c5498a5ada6593e8d47c7fd74cb51386a965d0935b24e` | Panchavargiya Bala (5-fold Tajika strength & Visheshika scale) |
| `apps/api/services/tajaka_yoga_engine.py` | `a301c07cdc66f82ef05e3b6ace8ad10975f1646a9ea86adc1a29ada9ff18bf24` | 16 Classical Tajika Yogas (Shodasha Yogas) engine |
| `apps/api/services/tajaka_dasha_engine.py` | `227ae47feb2f5c088c8275beac5526caed6a1df6f6f6f8ee12625a47866103d7` | Mudda & Patyayini annual dasha engine |
| `apps/api/services/terminology_service.py` | `a5b083c3fb7b9304ba8b1cbd5f4510c07eace4c52e22292aaf830bb64a8412b5` | Unified Sanskrit/English astrological terminology resolver & query expander |
| `apps/api/services/claim_grounding_validator.py` | `a2d7d9651dbd8c84b1545b1f2cadbc60b98628b4c7147fad5c9f9a1209aab391` | Claim grounding & hallucination prevention validator |
| `apps/api/services/ai_evaluation_framework.py` | `1f6817e7b165460bf44535f15bf528948b5bd1b928da062fcce1b8a658233fb6` | AI grounding & governance benchmarking evaluation harness |
| `apps/api/services/kuja_dosha_engine.py` | `b651851cbe3f0aded992bb1a1403b3cf534a3aa6e1a3b6d2528bbb31ed27512d` | Comprehensive Tri-Bhava Kuja Dosha (Lagna, Moon, Venus) & 10 classical pariharas |
| `apps/api/services/dasa_kuta_engine.py` | `8addee10d6ea9c4ee75914280e3d228199a45496e40a9cc998009c4b45b28fda` | South Indian 10-Poruthams compatibility system including Rajju & Vedha |
| `apps/api/services/jaimini_navamsha_synastry.py` | `015f08013bdf67c3e4f19e9129f3a2ecdc70022428b343989385d6abab36d6ae` | Jaimini Upapada Lagna (A12) & D9 Navamsha synastry harmony engine |
| `apps/api/services/composite_chart_engine.py` | `c79c43d0bc515d59805a9f3a29254cabe2902856e3f03f328ae03ee2ae23c965` | Shortest-arc circular midpoint composite relationship chart engine |
| `apps/api/services/mundane_ingress_engine.py` | `c8a088de521b40fae474928011d3724da3625de3ee1ac85aff7ab037ad529751` | High-precision Chaitra Shukla Pratipada & 4 cardinal solar ingresses solver |
| `apps/api/services/planetary_cabinet_engine.py` | `b976c70e9d887ecfa2fb01c5c4625dbad388788cb4793de977df986c590042fa` | Classical 9-minister cosmic governance council (Nava Nayakas) engine |
| `apps/api/services/mundane_eclipse_engine.py` | `116c3ec3bd8a8e35978eb7e5c6598589ebc99a0e9c8d55e6358283cf5ef11e44` | Standalone solar & lunar eclipse detection and mundane impact duration engine |
| `apps/api/services/kurma_chakra_engine.py` | `4291b4ed2119bb26527b16b9573175e5ad5917699e4982b1d74385debfe46944` | 9-sector celestial tortoise (Kurma Chakra) geopolitical & seismic engine |
| `apps/api/services/mundane_analysis_engine.py` | `32bb20858ea7b0fd9015a74bd91e58c2b66321a394ba38849ca0d7e89be9db70` | 12 Mundane Bhavas & comprehensive national forecasting engine |
| `apps/api/services/jaimini_special_dashas.py` | `337c341f7a7ad03e9674a12bfb3d8d88671273abb5be7b4e333d7d484ea3f02d` | Classical Shoola Dasha (9-year longevity/maraka) & Mandooka Dasha (frog-jump D11) |
| `apps/api/services/jaimini_upapada_engine.py` | `73da9a8c4d509feb66e75aa2ef2840607a9ef58cf5d867cd009ac94d41d08021` | In-depth native Upapada Lagna (UL) 2nd/8th house longevity & stability analysis |
| `apps/api/services/jaimini_expanded_yogas.py` | `79a5d8d33c3281e171fd7b71fbf62b15c67e4ff10591e70ce5d0e91bb94a121c` | Classical Jaimini Raja, Dhana (AK-PK, AmK-DK, AL-A11), Vipareeta, & Moksha yogas |
| `apps/api/services/jaimini_event_timing_engine.py` | `a1e3a2fda502a053557c86bd7de36856197cf97ad1dec592ca50c34975f13ac7` | Predictive event-timing synthesizing Jaimini Dashas, Karakas, & Arudhas |
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
| `apps/api/services/phalita_core/domain_significators.py` | `fe71537d41e478dd769bf7d77f3bb769d63ab0805cc3aeec597dc19cca7640f0` | Complete 12-Bhava Life Domain Registry & Significator Matrix |
| `apps/api/services/divisional_vimshottari_engine.py` | `6c967486450321cdf471f5d144b101fd8859438c2c391c8ed6747ab947a8eff3` | Independent Divisional (D9, D10, D7, D4, D30) Vimshottari Dasha Engine (updated to `p.contains(target_date)` for datetime spine compatibility) |
| `apps/api/services/phalita_core/varga_strength_fusion.py` | `3e584705326264769f47762e38c306b5f426960e5c79ef95588ec7a922300a92` | Log-Base-2 Main Strength x Vimshopaka Final Varga Fusion & Neecha Bhanga Engine |
| `apps/api/services/phalita_core/bhavottama_engine.py` | `46a299a2451225a669de8344a9a72850642dbb4328db1976c520d09aa1a844a1` | Bhavottama (Kimshukadi) Same-Bhava Detection & Quality Multiplier Engine |
| `apps/api/services/phalita_core/transit_trigger_engine.py` | `dc17d46d92051d9fc5bb981a9084cd09f95d40a94c4e704d5c9f8a87258aad6b` | Transit (Gochara) & Ashtakavarga Rekha Trigger Engine |
| `apps/api/services/phalita_core/divisional_explorer_service.py` | `55107d527f2eaff467484419a88c3219b2e1874969abeda6248fbc3ce2b52351` | Multi-Varga Interactive Explorer & Dual-Dasha Confluence Engine |
| `apps/api/services/phalita_core/karakamsha_synthesis_engine.py` | `4feee6ad61ada89052c7afbf0541572ce64857162303db211cc5bd0ad6fc652e` | Karakamsha Lagna & 7-Chara Karaka Jaimini Synthesis Engine |
| `apps/api/services/phalita_core/historical_backtest_harness.py` | `b531185116a2c884fa5d543094f616903283e02ec4993543176fc684eb966130` | Empirical Benchmark Backtesting & Accuracy Audit Harness (updated to `p.contains(target_d)` for dasha matching; zero scoring changes) |
| `apps/api/services/phalita_core/canonical_facts_generator.py` | `5c620f10490f22bc548c39816a9ea30b4edf4dcffa6d715807ebadfdadf42d91` | Calculation-Only Canonical Facts Ground Truth Generator (updated to `p.contains(t_date)` for datetime spine compatibility) |
| `apps/api/services/phalita_core/technique_resolver.py` | `e4661befca155a62ca4b5af39dc1f22be635d885d372eb2ebed977e3ce6697c3` | Domain-Tailored Shastric Technique Resolution Engine |
| `apps/api/services/phalita_core/shastric_rule_engine.py` | `7d774b9b9624fab0136f96dbe738416d30d4a9855e77f2b2177d343951e7d98e` | Declarative Shastric Rule Evaluation & Provenance Engine |
| `apps/api/services/phalita_core/evidence_aggregator.py` | `c9492cb5ce6102ec8f90777e80b4658f71f1fb06322fe91a1e8d5b1224988403` | Evidence Aggregator & Provenance Registry |
| `apps/api/services/phalita_core/prediction_calibrator.py` | `ced857a7c331d92ab9382607cb0d2605d022012057054d39c674b8827a2c3bcf` | Calibrated Prediction Engine (Emitting Calibrated Signal Score 0-9) |
| `apps/api/services/phalita_core/shastric_explanation_narrator.py` | `90d8a4ee7d06ec644f79813cd50010f8e093255b359a9a58f2d7fd03ea2aaf2e` | Grounded AI Shastric Explanation & Citation Narrator |
| `apps/api/services/phalita_core/shastric_reasoning_pipeline.py` | `907aab30d5432c1e0af0fc6e087e596b30887ede85d2fc29f365837c875a34a3` | Master End-to-End Shastric Reasoning Orchestrator |
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


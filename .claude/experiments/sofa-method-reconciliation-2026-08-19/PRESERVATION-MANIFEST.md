# PRESERVATION MANIFEST — Sofa method, benchmark and architecture lineage

Preserved 2026-08-19 to close the preservation component of **G-001**. Copy-and-document only.
No original was moved, altered or deleted. No model was called. Nothing was ratified.

## What this closes, and what it deliberately does not

G-001 recorded that a full day of Sofa work was untracked and unreferenced. The earlier evidence
checkpoint (`7d59bb3`) covered the Edinburgh calibration lineage but not the method it produced,
nor the Scout benchmark lineage the method is extracted from. This pass covers those.

It does **not** ratify anything. `.claude/SOFA-METHOD.md` still self-declares
`STATUS: CANONICAL OPERATIONAL METHOD`; that remains an open owner decision (G-009). To avoid
committing an unratified status claim into a canonical-looking location, the original is left
**untracked and untouched** and only a verbatim snapshot is preserved here, explicitly marked
UNRATIFIED.

Likewise the Sofa shadow implementation is preserved as a snapshot, **not** tracked in place under
`automation/`. Tracking those originals would put experimental code into the production/runtime
surface. Live architecture is unchanged: the shadow module is referenced by neither
`production_orchestrator.py` nor `generate.py`, and does not exist on trident.

## Snapshots (originals left untracked in place)

| ARTIFACT | CLASS | ORIGINAL_PATH | PRESERVED_PATH | SHA-256 | SIZE | STATUS | NOTES |
|---|---|---|---|---|---|---|---|
| SOFA-METHOD.md | METHOD | `.claude/SOFA-METHOD.md` | `.claude/experiments/sofa-method-reconciliation-2026-08-19/unratified-snapshot/SOFA-METHOD.md` | `57efede56244be01ccc92a20d129c80d7f18a12c0a88c68dc5193a3b7e9fbd6a` | 8654 | VERBATIM_SNAPSHOT / UNRATIFIED | Source and snapshot hashes match. Original still untracked; its canonical status is undecided. |
| sofa_discovery_shadow.py | SHADOW_IMPLEMENTATION | `automation/orchestrator/sofa_discovery_shadow.py` | `.claude/experiments/sofa-method-reconciliation-2026-08-19/implementation-snapshot/automation/orchestrator/sofa_discovery_shadow.py` | `f1c09178bb5e0e967169746fc6ec11db8ab81d6579f6560590e7cd1094b1f07c` | 65335 | IMPLEMENTATION_SNAPSHOT | Source and snapshot hashes match. Original left untracked under the runtime path. |
| sofa_discovery_shadow_test.py | SHADOW_IMPLEMENTATION | `automation/sofa_discovery_shadow_test.py` | `.claude/experiments/sofa-method-reconciliation-2026-08-19/implementation-snapshot/automation/sofa_discovery_shadow_test.py` | `3ed5675355860543686cf0932a770b36d5cfaf2304584cc439524da49289a147` | 38110 | IMPLEMENTATION_SNAPSHOT | Source and snapshot hashes match. Original left untracked under the runtime path. |
| sofa_shadow_probe.py | SHADOW_IMPLEMENTATION | `automation/sofa_shadow_probe.py` | `.claude/experiments/sofa-method-reconciliation-2026-08-19/implementation-snapshot/automation/sofa_shadow_probe.py` | `652ccc039974afca31be8bb5ba3615fcb5984350248ca17aa57166166df62e82` | 11600 | IMPLEMENTATION_SNAPSHOT | Source and snapshot hashes match. Original left untracked under the runtime path. |

## Tracked in place (already under an evidence path)

| ARTIFACT | CLASS | ORIGINAL_PATH | SHA-256 | SIZE | STATUS |
|---|---|---|---|---|---|
| sofa-pipeline-audit-current-runtime-2026-08-18.md | ARCHITECTURE_AUDIT | `.claude/experiments/sofa-pipeline-audit-current-runtime-2026-08-18.md` | `d0df53c6aab3052aba0660426333c62bc355fefdfc2393eae4a3a778fb7bf945` | 26045 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-architecture-v1-proposal-2026-08-18.md | ARCHITECTURE_PROPOSAL | `.claude/experiments/sofa-architecture-v1-proposal-2026-08-18.md` | `4e66716886490908c4d6596d9116cf5a5017e74a744edcf87a1ee14ccc89cd0e` | 28930 | ORIGINAL_TRACKED_IN_PLACE |
| cripminds-scout-v0-sofa-articles-2026-08-17.md | BENCHMARK | `.claude/experiments/cripminds-scout-v0-sofa-articles-2026-08-17.md` | `928928e9e31982685128813a9c71cf8465a3071cfb39d22996a4390243f78e5f` | 18520 | ORIGINAL_TRACKED_IN_PLACE |
| NOTES.md | BENCHMARK | `.claude/experiments/scout-v0-1-sofa-motion-2026-08-17/NOTES.md` | `fcf7578bc15ae64d879a67ae4bb9f3e362dcd1bbb91ee7184be879e406baa3a5` | 7738 | ORIGINAL_TRACKED_IN_PLACE |
| 01-pixel-nova-the-fox-the-camera-missed-v01.md | BENCHMARK | `.claude/experiments/scout-v0-1-sofa-motion-2026-08-17/articles/01-pixel-nova-the-fox-the-camera-missed-v01.md` | `4ec3f9f56593079005b454594879b7c0848464e8f4dd5e8e21da9e153ba78582` | 6953 | ORIGINAL_TRACKED_IN_PLACE |
| 02-zen-circuit-mobile-as-long-as-you-dont-look-too-long-v01.md | BENCHMARK | `.claude/experiments/scout-v0-1-sofa-motion-2026-08-17/articles/02-zen-circuit-mobile-as-long-as-you-dont-look-too-long-v01.md` | `99e719c97d6429b2143d7dcebb6098b405bc6ceb48877e50e2f3a4db678dbd3c` | 7669 | ORIGINAL_TRACKED_IN_PLACE |
| 03-maya-flux-the-hour-that-has-no-age-v01.md | BENCHMARK | `.claude/experiments/scout-v0-1-sofa-motion-2026-08-17/articles/03-maya-flux-the-hour-that-has-no-age-v01.md` | `a82b342159620036c78a1940000288a60fbd32f7eef36305b1a62377d13d4877` | 6789 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v02.md | BENCHMARK | `.claude/experiments/scout-v0-2-fox-causal-lens-2026-08-17/the-fox-the-camera-missed-v02.md` | `9d25659025893e0835a8ed79fb56210ba28b898e539e7ed6cc8f515086003650` | 6658 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v02.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v02.md` | `b03dba8cd0843dc8f6b3632e757bf154b9118aee5b878e212f8166c160d745e4` | 6048 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v021.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v021.md` | `44960cc286843ea0113a3769ee82815cc28051ddd9141593e3eadeaf41138f65` | 4116 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v022.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v022.md` | `6610127ada0fefcd608e4bddb6249f55403fa9a8c66c938eea569477aa5c3b41` | 2926 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v023.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v023.md` | `2222302fb1db0b0bd60ae8f6aec078a90211ca46debd93e44ee6f93c9cb75569` | 4835 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v024.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v024.md` | `0af7f00844d35dacb4b72079bd0dd192eade4c6618b3586afed0181f3ea3ad1f` | 3418 | ORIGINAL_TRACKED_IN_PLACE |
| the-hour-that-has-no-age-v025.md | BENCHMARK | `.claude/experiments/scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v025.md` | `a64cbeaa641d4bd4a7e7754d655da7bb37dbbc388b6e4f575865ea709e7aeddc` | 3364 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v02.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v02.md` | `39581a93f8fe32d578bcc21610963f1d94482467fc5536eeb64d402e51f586fb` | 5237 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v021.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v021.md` | `a51560318779fe93ed071fe2ccd51d351f921f2878a55418f2a60c396e4dee00` | 5993 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v022.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v022.md` | `1591c96a9008a46ec7f7fdc6c0808e8b771158298f1eacf54ef0bf4cf28c7dc5` | 4367 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v023.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v023.md` | `d9e41f156f793d20d19fbdb69db5757b646ddf5da0e78105fdcff93b9abcf3df` | 3799 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v024.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v024.md` | `486362834051a1b5adb238a6864a0e8384ff0f86b4f3036f73f43d36e2cd1ad0` | 2865 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v025.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v025.md` | `0a3aff5c4cbad2708348d5928e0d2a5ace00ea3ecb243410f04bb418ec8af758` | 3397 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v026.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v026.md` | `c2efb150658631ce27f439a36c78dd74b6724393871fc8270ff6392d42ac4bed` | 3139 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-as-long-as-you-dont-look-too-long-v027.md | BENCHMARK | `.claude/experiments/scout-v0-2-mobile-sofa-2026-08-18/mobile-as-long-as-you-dont-look-too-long-v027.md` | `6b4c7f86e66462cb4fb30527bc69d178c593ab1f435bb96312cb37b05cfb3ad3` | 3165 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v031.md | BENCHMARK | `.claude/experiments/scout-v0-3-1-fox-flow-2026-08-17/the-fox-the-camera-missed-v031.md` | `c0ceaf6d929a0589c37648a1db3c03a68b128b559d89d482ff4cc972a808e787` | 5015 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v03.md | BENCHMARK | `.claude/experiments/scout-v0-3-fox-book-prose-2026-08-17/the-fox-the-camera-missed-v03.md` | `8578d5fe0cbd63ae5f789c26003b3b6852eb63ff48a70dae078261b29b8c7e81` | 5039 | ORIGINAL_TRACKED_IN_PLACE |
| the-category-that-outlived-reality-v03.md | BENCHMARK | `.claude/experiments/scout-v0-3-mobile-writer-2026-08-18/the-category-that-outlived-reality-v03.md` | `80bdb6b873ffffeebf19bd7dca1f97e1388d81366e49b509d60940d9d2d48bef` | 3948 | ORIGINAL_TRACKED_IN_PLACE |
| the-category-that-outlived-reality-v031.md | BENCHMARK | `.claude/experiments/scout-v0-3-mobile-writer-2026-08-18/the-category-that-outlived-reality-v031.md` | `34cddb8054a1da5716f368feaa1e1f9cdf57d18a50af8f481ad6ed5b9c79f2e2` | 2899 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v04.md | BENCHMARK | `.claude/experiments/scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v04.md` | `68a0797cec41958ad2d2a0abaa867ae49e2a6e1e866490fa0e7cb4950d0739d0` | 6820 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v041.md | BENCHMARK | `.claude/experiments/scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v041.md` | `78cac7600fd270c6bfa2838dcb2ae31f5ff865d9691bfdb6e7412fbd91c57f3e` | 6568 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v042.md | BENCHMARK | `.claude/experiments/scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v042.md` | `4a7d0127d3af62a128c20a17f34d62d8fb3b64b28bc3e14ae42f49f56dd27f77` | 5962 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v043.md | BENCHMARK | `.claude/experiments/scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v043.md` | `56ce39a85e9f49c7d529128b37b08e94f16a9439cf45577a5f74f1fdc788ded2` | 6380 | ORIGINAL_TRACKED_IN_PLACE |
| the-fox-the-camera-missed-v044.md | BENCHMARK | `.claude/experiments/scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v044.md` | `2ac68dced75b7ed73c01423fed9566fca5c5a447f3345c8d71838a6088c83d87` | 6340 | ORIGINAL_TRACKED_IN_PLACE |
| the-category-that-outlived-reality-v04.md | BENCHMARK | `.claude/experiments/scout-v0-4-mobile-book-opening-2026-08-18/the-category-that-outlived-reality-v04.md` | `4060c3b63d3effba623d2f8b1c4d2f4c3cd88d68bed703d1f6a6d37091ffa5ec` | 2963 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-v05.md | BENCHMARK | `.claude/experiments/scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v05.md` | `a1a451ad081cac33f22bad1a6f141d6be526bf41fb826160c327d3230ef14625` | 3855 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-v051.md | BENCHMARK | `.claude/experiments/scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v051.md` | `130f473bb7ddd82e756051912fc07c8212d737164f0e0e5a65fbf70c060bbc75` | 3874 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-v052.md | BENCHMARK | `.claude/experiments/scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v052.md` | `8de998d1572b5eda649a32b00d692736bb8e66075934bbdf5e03635ddb6acab1` | 3479 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-v053.md | BENCHMARK | `.claude/experiments/scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v053.md` | `bf86244b17dbdb0513b652dab6be333813752fb0f73e31f8ac1d6d5d79bc6fb8` | 3527 | ORIGINAL_TRACKED_IN_PLACE |
| mobile-v054.md | BENCHMARK | `.claude/experiments/scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v054.md` | `0533f7a8485e239e8b42884544f693213f2c04a76446e6166743558b5a218bf1` | 3310 | ORIGINAL_TRACKED_IN_PLACE |
| 01-pixel-nova-the-fox-the-camera-missed.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/articles/01-pixel-nova-the-fox-the-camera-missed.md` | `b8312c4679d2242b151975057431481ace0e100aafa4c391e05e1f3c6fcc10cc` | 7518 | ORIGINAL_TRACKED_IN_PLACE |
| 02-zen-circuit-mobile-as-long-as-you-dont-look-too-long.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/articles/02-zen-circuit-mobile-as-long-as-you-dont-look-too-long.md` | `aa4a186acf24f4370abbb6ff1ee23b55dfd0f21c3f82a17773e5558c099b6fcd` | 7927 | ORIGINAL_TRACKED_IN_PLACE |
| 03-maya-flux-the-hour-that-has-no-age.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/articles/03-maya-flux-the-hour-that-has-no-age.md` | `e76bc6499bb3ba60d132cdb85038da9f56e7548992adce97217fa90925e2913a` | 7179 | ORIGINAL_TRACKED_IN_PLACE |
| culture-specialist.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/culture-specialist.md` | `f803abef2ae32f2829f3a2e788918c695927b131ad66d04fae8ffcc8447e6adc` | 11368 | ORIGINAL_TRACKED_IN_PLACE |
| design-tech.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/design-tech.md` | `03ee856653f4c2cdd0b18cec312de39264576d61a3a9b550a1983a68b717c62a` | 13679 | ORIGINAL_TRACKED_IN_PLACE |
| general-local-news.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/general-local-news.md` | `5ff46fa4a3559f805163cfa11b8caf440410c89d989d5bb7cfacfe3705a01437` | 14589 | ORIGINAL_TRACKED_IN_PLACE |
| legal-municipal.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/legal-municipal.md` | `ee3a6655fb7aa8746b99fbff77fd55fff8580035f62dcf15fc2c76bce967fabb` | 17817 | ORIGINAL_TRACKED_IN_PLACE |
| science-research.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/science-research.md` | `dfbec4a44035567fb47e6a416c9f5920783f0fde68cb3dbbc5f3a7bfc1c2df6e` | 17591 | ORIGINAL_TRACKED_IN_PLACE |
| trade-business.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/disturbance-cards/trade-business.md` | `e0a69804bdc6835f9d63721f153ebcb79d2518a42dddc99ae6a326e89a8f8669` | 16391 | ORIGINAL_TRACKED_IN_PLACE |
| acv-labor-depreciation.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/evidence-packets/acv-labor-depreciation.md` | `f1b4113508b08d6188d7b6d15a42108842348b2691ecd8b6ab99732fa1f37c47` | 25843 | ORIGINAL_TRACKED_IN_PLACE |
| camera-trap-detection-bias.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/evidence-packets/camera-trap-detection-bias.md` | `af246f77f69312865459daefa49a8088fce10d6ebb0d3fc78f7298ff890518e2` | 26203 | ORIGINAL_TRACKED_IN_PLACE |
| xai-turbine-classification.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/evidence-packets/xai-turbine-classification.md` | `4e9f0c520232e5e95a77c022ac9b5ff8f0cc8c13dbf0bd6464eaff9499e704e8` | 47035 | ORIGINAL_TRACKED_IN_PLACE |
| selection-and-probes.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/perceptual-probes/selection-and-probes.md` | `9678b157b3ea9ea5aa1af8f79eaee2840047f7c17e91a598d8de779f0bb96c26` | 7533 | ORIGINAL_TRACKED_IN_PLACE |
| culture-specialist.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/culture-specialist.md` | `30e7657dc0a1824257a22dda9593993d10990ab7cb288c876207fa0004050ec9` | 6524 | ORIGINAL_TRACKED_IN_PLACE |
| design-tech.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/design-tech.md` | `1a1a757b983d39cc97b5524468af6404c468a112730363d19e9c952b5d87c050` | 7205 | ORIGINAL_TRACKED_IN_PLACE |
| general-local-news.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/general-local-news.md` | `126b6cf3a5eb59a5f61eee82019ec7aca082874393fca5e37dd99d19ea906722` | 7147 | ORIGINAL_TRACKED_IN_PLACE |
| legal-municipal.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/legal-municipal.md` | `a6c2e76d7d558abd75e3967b0a398085ef4dabda5372721804c7a0b74c8ff943` | 5432 | ORIGINAL_TRACKED_IN_PLACE |
| science-research.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/science-research.md` | `ee95c26d3d5eebab3ceaa8565f8d97debb0006c3a27ecc81ccb95ba437fc4be3` | 5195 | ORIGINAL_TRACKED_IN_PLACE |
| trade-business.md | BENCHMARK | `.claude/experiments/scout-v0-sofa-articles-2026-08-17/source-pool/trade-business.md` | `69e0d17dd8fe15ef6e5241344cc6dd259c9e24a8d4aa65d44bd54cf8f061f424` | 12096 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-method-v0-1-two-benchmarks-2026-08-18.md | METHOD_EXTRACTION | `.claude/experiments/sofa-method-v0-1-two-benchmarks-2026-08-18.md` | `090a3507332323df44bc4be52a595e2085ca8957028df0407d7cfd30b7bf268a` | 18378 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-method-v0-2-three-benchmarks-2026-08-18.md | METHOD_EXTRACTION | `.claude/experiments/sofa-method-v0-2-three-benchmarks-2026-08-18.md` | `3a77057713eec5cea549d5826f53e8b3456abba42b94e3c62f7b1756a87e2cb5` | 32128 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-method-v0-two-benchmarks-2026-08-18.md | METHOD_EXTRACTION | `.claude/experiments/sofa-method-v0-two-benchmarks-2026-08-18.md` | `737dde755c7ea0d4231e0de84382960778097b35867b3d917eba5a427a8efa63` | 15918 | ORIGINAL_TRACKED_IN_PLACE |
| GAP-LEDGER-NORMALIZED.md | OTHER | `.claude/experiments/project-state-reconciliation-2026-08-18/GAP-LEDGER-NORMALIZED.md` | `79a25b8d4e263abb392a2325876ec5ae130c5a6988c051a56eb546b4fa61aa68` | 7533 | ORIGINAL_TRACKED_IN_PLACE |
| PROPOSED-PROJECT-STATE-2026-08-19.md | OTHER | `.claude/experiments/project-state-reconciliation-2026-08-18/PROPOSED-PROJECT-STATE-2026-08-19.md` | `98bfa28789e24e9a169297a4111ddcc8983d4e0c6199648b5f9863501079a758` | 8673 | ORIGINAL_TRACKED_IN_PLACE |
| synth-1-fixture.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-cases/synth-1-fixture.json` | `b97b279d19352b05d1dc99a862440e6b112ff103b30f164bc60dd6954b0c43d9` | 11334 | ORIGINAL_TRACKED_IN_PLACE |
| synth-1-priority-b-hold.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-cases/synth-1-priority-b-hold.json` | `d7398d4f890adb42a3fce65f837888261f7b58b5a4b5d3d4a346da9004cc0f28` | 3113 | ORIGINAL_TRACKED_IN_PLACE |
| discovery_packet.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-output/synth-1/discovery_packet.json` | `74fdd2ecd2ba68aabd992f4d7d2f422ac99fe1a0ec01406b579b194417503236` | 8229 | ORIGINAL_TRACKED_IN_PLACE |
| eligibility.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-output/synth-1/eligibility.json` | `a835e48fd6e46ec47bf475b5ce6e0ec089f1939360b0b15e29a3b180a6c941fb` | 3179 | ORIGINAL_TRACKED_IN_PLACE |
| grounding_audit.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-output/synth-1/grounding_audit.json` | `cb6504072c70ba17eca5533b373ce07542e28416dc63ef2a5effaab0dac8eed3` | 2924 | ORIGINAL_TRACKED_IN_PLACE |
| shadow_article.md | SHADOW_RESULT | `.claude/experiments/sofa-shadow-output/synth-1/shadow_article.md` | `9c51ccdd2cd71881d6ea3b347f4bbd46d3a722949104a4d3fb66296381e94ad7` | 3818 | ORIGINAL_TRACKED_IN_PLACE |
| writer_context.json | SHADOW_RESULT | `.claude/experiments/sofa-shadow-output/synth-1/writer_context.json` | `726ffc40ad628a980ad45c8e36c49b2db3b29904f38f68d31f31c50e286f0406` | 4405 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-shadow-slice-1-1-results-2026-08-18.md | SHADOW_RESULT | `.claude/experiments/sofa-shadow-slice-1-1-results-2026-08-18.md` | `3329caeae0b431ecf1f00d93e919baedfbe75324a607121bb774fc257edbd1a1` | 16596 | ORIGINAL_TRACKED_IN_PLACE |
| sofa-shadow-slice-1-results-2026-08-18.md | SHADOW_RESULT | `.claude/experiments/sofa-shadow-slice-1-results-2026-08-18.md` | `73132cb607f9c31f2bf50dcb406ad9c2faec4e8b4285b83c431c50d5e2cb7c1b` | 19191 | ORIGINAL_TRACKED_IN_PLACE |

## Inventory summary

| CLASS | n | Disposition |
|---|---|---|
| METHOD | 1 | VERBATIM_SNAPSHOT, UNRATIFIED — original untracked |
| METHOD_EXTRACTION | 3 | tracked in place |
| BENCHMARK | 54 | tracked in place (11 Scout V0/V0.x directories) |
| ARCHITECTURE_AUDIT | 1 | tracked in place |
| ARCHITECTURE_PROPOSAL | 1 | tracked in place |
| SHADOW_RESULT | 9 | tracked in place |
| SHADOW_IMPLEMENTATION | 3 | IMPLEMENTATION_SNAPSHOT — originals untracked |
| OTHER | 2 | tracked in place (reconciliation synthesis docs) |
| **Total** | **74** | |

## The three frozen benchmarks

The method-extraction documents rest on three frozen benchmarks, all preserved here:

| Benchmark | File | Frozen marker present |
|---|---|---|
| FOX | `scout-v0-4-fox-material-2026-08-17/the-fox-the-camera-missed-v044.md` | **no** — see G-003, recorded not corrected |
| HOUR | `scout-v0-2-hour-sofa-2026-08-18/the-hour-that-has-no-age-v025.md` | yes |
| MOBILE | `scout-v0-5-mobile-evidence-reset-2026-08-18/mobile-v054.md` | yes |

G-003 is preserved as found. No file was edited to add a missing marker.

## Evidence corrections carried into this manifest

Three statements from earlier synthesis are corrected here so the preserved record does not
propagate them:

1. **Perplexity is not a clean negative demonstration.** Its session was contaminated by B.3 prose
   in its input (G-052). Its later collapse toward generic disability/accessibility material when
   prompted "for cripminds.com" remains an illustrative observation, but it is **not** a clean
   controlled test of that prompt variable.
2. **Do not equate FORM-1.1 with Legacy on grounding.** The auditable figures are FORM-1 at
   2 unsupported of 6 audited claims and FORM-1.1 at 3 of 5. FORM-1.1 therefore regressed on
   unsupported proportion relative to FORM-1; the small and differing claim sets do not justify
   an equivalence claim against Legacy. The stable conclusion is that Article Form improved
   coherence and arrival substantially while grounding remains unresolved.
3. **Scout SV0 wording.** The old explicit gate was never formally completed at the time.
   Subsequent Scout-derived benchmark work and the real-material Sofa/Article Form experiments
   have superseded it as a current blocker. It was not "satisfied by use."

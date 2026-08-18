# PRESERVATION MANIFEST — CJ1-v3 / CJ2-B2 development artifacts

Preserved 2026-08-19 from `~/.claude/jobs/2c987bae/tmp/` (Mac job storage). Copy-and-document only;
no source deleted, no file normalized, no code executed. CJ2 remains OFF and was not resumed.

## What this directory is — and is NOT

UNPRESERVED-ARTIFACTS.md group 2 said the CJ1/CJ2 runnable evidence "is not in the repo anywhere."
That is true of the repo, but **overstated as a risk claim**: a complete, durable backup already
exists outside the repo at `~/code/cripminds-preservation/engineering/cj1-cj2-2026-08-16/`
(650 files, 33 MB, with its own `FILES.json`). Verified by hash this pass:

- All **52** untracked `automation/cj*.py` files in the working tree are byte-identical to the backup.
- The backup carries **18** `.probe_fixtures` sub-directories / 597 files / 31 MB.
- The three `cj*.py` files not in the backup (`cj2_shadow_integration_test.py`, `cj2_winner_bridge.py`,
  `cj2_winner_bridge_test.py`) are **tracked in git** and therefore already safe.
- The CJ2 stage prompts thought to be job-dir-only are durably preserved under canonical names in
  `.probe_fixtures/cj2-reference-probe-1/frozen_prompts/` (`cj2-stage-a-v1.txt`, `cj2-stage-c-v1.txt`,
  `cj2-stage-b2-v1.1.txt`, `cj2-stage-b2-v1.4.txt`). Job-dir copies are DUPLICATE_CONFIRMED.

What IS preserved here is the residue: the files that hash-matched **nothing** durable — chiefly the
per-version preflight scripts, the B2 v1.x/v2 user templates and analysis/assembly scripts, the Stage-A
candidate dump, and the static-test regression logs. These are the only copies.

## Regression logs — three distinct runs, not redundant copies

The `*_static_tests.py.log` files appear in three families (bare, `final_`, `regress_`). Most are
byte-identical across families, but three pairs genuinely differ:
`cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` has three different hashes across the
three families, and `cj1_v3_anchor_resolver_static_tests.py.log` differs between `final_` and the
other two. All families are preserved verbatim; none were collapsed.

## Artifacts

| ARTIFACT TYPE | ORIGINAL PATH | PRESERVED PATH | SHA-256 | ORIGINAL MTIME | SIZE | STATUS |
|---|---|---|---|---|---|---|
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_preflight.py` | `b2_v1_1_preflight.py` | `c20e7b9e635c05cc88cf4b735626a2e1386d28ba335d9808bc30b0ea1623ba09` | 2026-08-11 18:21:46 | 10016 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_1_user_template.txt` | `b2_v1_1_user_template.txt` | `9046fb6ccc305ef1b4054d68fb989b4bbb49a4fdecdf4c8656cfb52f0102af80` | 2026-08-11 18:21:12 | 1334 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_2_preflight.py` | `b2_v1_2_preflight.py` | `fdd17199e79799071294a583d473b66231dc2ccf5d223c68b28a044682b7240f` | 2026-08-11 18:58:53 | 14505 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_2_user_template.txt` | `b2_v1_2_user_template.txt` | `9046fb6ccc305ef1b4054d68fb989b4bbb49a4fdecdf4c8656cfb52f0102af80` | 2026-08-11 18:58:08 | 1334 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_3_preflight.py` | `b2_v1_3_preflight.py` | `e12ad282e337db6a341bdf98e61f18c28d20ce04c1a253b3a364e7c0cf5ed3f0` | 2026-08-12 02:35:18 | 10907 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2_v1_4_preflight.py` | `b2_v1_4_preflight.py` | `4a7972608ddcee9015136be78eba59d1aa8030fd0957d698d16acc952e9de518` | 2026-08-12 03:25:05 | 9922 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2v2_analysis.py` | `b2v2_analysis.py` | `53622cfdd839f956d3d010b849f547d287ac6cf53bf7601e0298b992cf745dc1` | 2026-08-12 16:09:48 | 17979 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/b2v2_final_assembly.py` | `b2v2_final_assembly.py` | `032fecd17ad82ffb609415a613b727f67598bceb9d52e1ce5c4459925466a047` | 2026-08-12 16:11:45 | 19675 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/build_v13_regression_report.py` | `build_v13_regression_report.py` | `0e69a08a23b0fdcbb17a036be214276ca6cd808e994d2358180b2beb43b4b86f` | 2026-08-12 03:09:42 | 14157 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj1_v3_anchor_resolver_static_tests.py.log` | `cj1_v3_anchor_resolver_static_tests.py.log` | `a41e530acfc05577654c12edd62d902b67dbfb228b630467cc1c89621b4c4c42` | 2026-08-13 17:39:43 | 1724 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2-b2-v141-run/automation/cj1_v3_anchor_resolver.py` | `cj2-b2-v141-run/automation/cj1_v3_anchor_resolver.py` | `d8f761e54822526dda1ed021a5eb5e6c017d8048abf60b2f6caf7525d7ff983b` | 2026-08-12 11:13:35 | 7032 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/all_candidates_full.txt` | `cj2/all_candidates_full.txt` | `c7bede6701ec817d7bf7a33e1f9dc22583980ab48169acdb2a34add92b077bb1` | 2026-08-11 17:34:40 | 43664 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/preflight.py` | `cj2/preflight.py` | `236688d20cbc79fe4b8ac17a10c19db615b87fe3460e45de9cd76cbb87795e30` | 2026-08-11 17:15:37 | 8015 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/preflight_b2.py` | `cj2/preflight_b2.py` | `6ac65223cc5c897e72bc402b3730e07df8ed992e937c9f674751e7c09bc8f311` | 2026-08-11 18:09:38 | 5215 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_a_summary.txt` | `cj2/stage_a_summary.txt` | `99ddf2df80f021a04fc90d77ba0ddf975ab1b94c565ccd7aa2cfa47d2d481469` | 2026-08-11 17:27:49 | 11608 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_b2_system.txt` | `cj2/stage_b2_system.txt` | `1d2be6239405eac7f6412720301291c63fba9f176e25b904aabe2ff97aaa37c3` | 2026-08-11 18:08:40 | 9526 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2/stage_b2_user_template.txt` | `cj2/stage_b2_user_template.txt` | `dfb4bd7ebf3422c42191964ebb349611637251ac6540faed39fc7acfcaa65396` | 2026-08-11 18:08:50 | 997 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_c0_static_tests.py.log` | `cj2_b2_c0_static_tests.py.log` | `dfc85b03ba8455ba50d24207cb858db3c5c49aaa774d56fa5a7175210ea5e249` | 2026-08-13 17:39:43 | 2707 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0_static_tests.py.log` | `cj2_b2_d0_static_tests.py.log` | `597add01f899d53c85410432d1fb9a6ca19556a2031284c39eb6af1c73dfece2` | 2026-08-13 17:39:43 | 3417 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `2338e457413c7b7a15f5c0b0897f035a4394aba4adae3e7baaa4e9456b84f177` | 2026-08-13 17:39:43 | 1686 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0c0_first_probe_static_tests.py.log` | `cj2_b2_d0c0_first_probe_static_tests.py.log` | `f5b8cdfdbedc9d12251255bbf4bed6d1b630d60442d9d19831237b654729675a` | 2026-08-13 17:39:43 | 9582 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `4c7710e4a1510612f672bb7d867d9c847a2998d594fc7d53c54b41e15e8ba3b4` | 2026-08-13 17:39:43 | 6164 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `b012016e2459133e0e4d39ec02bf6074b96618399e8640910ffe00949221ca92` | 2026-08-13 17:39:43 | 3244 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `de379c3a922d84e0aa761ab258f403cd6d837c2a28b15853353969d811f74733` | 2026-08-13 17:39:43 | 9315 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `2f2517b61125d71a56ecde031c9fce9b36b4fd67c81308c10cbd962d6e346944` | 2026-08-13 17:39:43 | 6038 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `c5f847d3834f7069e5fe72e1256141b9c820079654c230db2355628c01eb35f4` | 2026-08-13 17:39:43 | 1714 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `f60ce78bc33d2af5772679c5b1ffbbc29ebf0f732017d534723bb1596a6bfebb` | 2026-08-13 17:39:43 | 2559 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `14c8cd03230741c1ef5f4279a80356b542f6edba846ffb7d8970735f9ef22497` | 2026-08-13 17:39:43 | 1575 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_scratch_path.txt` | `cj2_b2_scratch_path.txt` | `3a29ca9523d4ee5e8006998e55d45efba21902cfcc4bda8cb32726051bb8b2e4` | 2026-08-11 18:35:40 | 31 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_stage_c_admission_gate_static_tests.py.log` | `cj2_b2_stage_c_admission_gate_static_tests.py.log` | `3baddbda3e36833972823db3da53b62efbea22e9964903f963a2c6089211ef76` | 2026-08-13 17:39:43 | 7704 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2_v2_static_tests.py.log` | `cj2_b2_v2_static_tests.py.log` | `c8566a60aa12b6158038f7e1ebba9b509cb9ff8ec969fe26e89cd5232f828c7c` | 2026-08-13 17:39:43 | 3397 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/cj2_b2v12_scratch_path.txt` | `cj2_b2v12_scratch_path.txt` | `53e756e4d718b91626c0f102f010f5e3839d27fd9239dbbe09f8dce81ce710ed` | 2026-08-11 19:07:11 | 34 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/dup_signal_probe.py` | `dup_signal_probe.py` | `3070004458de37c33a04dbcbc6d6f58c8307f2f4f03420c5a2927fa51e820236` | 2026-08-14 12:06:23 | 3722 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj1_v3_anchor_resolver_static_tests.py.log` | `final_cj1_v3_anchor_resolver_static_tests.py.log` | `db05692c0cc490c3d6cf79baa0c2b0e17cfe2c5c2c7c44b61280aec5f063c43c` | 2026-08-13 17:53:44 | 3171 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_c0_static_tests.py.log` | `final_cj2_b2_c0_static_tests.py.log` | `dfc85b03ba8455ba50d24207cb858db3c5c49aaa774d56fa5a7175210ea5e249` | 2026-08-13 17:53:44 | 2707 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0_static_tests.py.log` | `final_cj2_b2_d0_static_tests.py.log` | `597add01f899d53c85410432d1fb9a6ca19556a2031284c39eb6af1c73dfece2` | 2026-08-13 17:53:44 | 3417 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `final_cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `2338e457413c7b7a15f5c0b0897f035a4394aba4adae3e7baaa4e9456b84f177` | 2026-08-13 17:53:44 | 1686 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0c0_first_probe_static_tests.py.log` | `final_cj2_b2_d0c0_first_probe_static_tests.py.log` | `f5b8cdfdbedc9d12251255bbf4bed6d1b630d60442d9d19831237b654729675a` | 2026-08-13 17:53:44 | 9582 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `final_cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `4c7710e4a1510612f672bb7d867d9c847a2998d594fc7d53c54b41e15e8ba3b4` | 2026-08-13 17:53:44 | 6164 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `final_cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `b012016e2459133e0e4d39ec02bf6074b96618399e8640910ffe00949221ca92` | 2026-08-13 17:53:44 | 3244 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `final_cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `93ae0df468d9eb26d6f2803d6223016fafb7cf8a388be120c0056b2316ff62ed` | 2026-08-13 17:53:44 | 9315 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `final_cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `2f2517b61125d71a56ecde031c9fce9b36b4fd67c81308c10cbd962d6e346944` | 2026-08-13 17:53:44 | 6038 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `final_cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `c5f847d3834f7069e5fe72e1256141b9c820079654c230db2355628c01eb35f4` | 2026-08-13 17:53:44 | 1714 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `final_cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `f60ce78bc33d2af5772679c5b1ffbbc29ebf0f732017d534723bb1596a6bfebb` | 2026-08-13 17:53:44 | 2559 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `final_cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `14c8cd03230741c1ef5f4279a80356b542f6edba846ffb7d8970735f9ef22497` | 2026-08-13 17:53:44 | 1575 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_stage_c_admission_gate_static_tests.py.log` | `final_cj2_b2_stage_c_admission_gate_static_tests.py.log` | `3baddbda3e36833972823db3da53b62efbea22e9964903f963a2c6089211ef76` | 2026-08-13 17:53:44 | 7704 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/final_cj2_b2_v2_static_tests.py.log` | `final_cj2_b2_v2_static_tests.py.log` | `c8566a60aa12b6158038f7e1ebba9b509cb9ff8ec969fe26e89cd5232f828c7c` | 2026-08-13 17:53:44 | 3397 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/opening_template_probe.py` | `opening_template_probe.py` | `fc20bd2ebd621be59d9b1bbef6a07a7d62b62551d2b9ac9db9cab4777ff124b5` | 2026-08-14 12:47:47 | 3128 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj1_v3_anchor_resolver_static_tests.py.log` | `regress_cj1_v3_anchor_resolver_static_tests.py.log` | `a41e530acfc05577654c12edd62d902b67dbfb228b630467cc1c89621b4c4c42` | 2026-08-13 17:52:26 | 1724 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_c0_static_tests.py.log` | `regress_cj2_b2_c0_static_tests.py.log` | `dfc85b03ba8455ba50d24207cb858db3c5c49aaa774d56fa5a7175210ea5e249` | 2026-08-13 17:52:26 | 2707 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0_static_tests.py.log` | `regress_cj2_b2_d0_static_tests.py.log` | `597add01f899d53c85410432d1fb9a6ca19556a2031284c39eb6af1c73dfece2` | 2026-08-13 17:52:26 | 3417 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `regress_cj2_b2_d0c0_execution_envelope_recovery_static_tests.py.log` | `2338e457413c7b7a15f5c0b0897f035a4394aba4adae3e7baaa4e9456b84f177` | 2026-08-13 17:52:26 | 1686 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0c0_first_probe_static_tests.py.log` | `regress_cj2_b2_d0c0_first_probe_static_tests.py.log` | `f5b8cdfdbedc9d12251255bbf4bed6d1b630d60442d9d19831237b654729675a` | 2026-08-13 17:52:26 | 9582 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `regress_cj2_b2_d0c0_natural_c0_recovery_static_tests.py.log` | `4c7710e4a1510612f672bb7d867d9c847a2998d594fc7d53c54b41e15e8ba3b4` | 2026-08-13 17:52:26 | 6164 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `regress_cj2_b2_d0c0_output_normalizer_static_tests.py.log` | `b012016e2459133e0e4d39ec02bf6074b96618399e8640910ffe00949221ca92` | 2026-08-13 17:52:26 | 3244 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `regress_cj2_b2_d0c0_real_material_transfer_probe_static_tests.py.log` | `c12f19f3e63993a4ddadec1f95b3f6e56226e8a8d2313eb58bd196f3519be4fe` | 2026-08-13 17:52:26 | 9315 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `regress_cj2_b2_integrated_pipeline_probe_static_tests.py.log` | `2f2517b61125d71a56ecde031c9fce9b36b4fd67c81308c10cbd962d6e346944` | 2026-08-13 17:52:26 | 6038 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `regress_cj2_b2_r1r2_partial_structured_output_probe_static_tests.py.log` | `c5f847d3834f7069e5fe72e1256141b9c820079654c230db2355628c01eb35f4` | 2026-08-13 17:52:26 | 1714 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `regress_cj2_b2_r2_contract_repair_probe_static_tests.py.log` | `f60ce78bc33d2af5772679c5b1ffbbc29ebf0f732017d534723bb1596a6bfebb` | 2026-08-13 17:52:26 | 2559 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `regress_cj2_b2_r2_integrated_repair_recheck_static_tests.py.log` | `14c8cd03230741c1ef5f4279a80356b542f6edba846ffb7d8970735f9ef22497` | 2026-08-13 17:52:26 | 1575 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_stage_c_admission_gate_static_tests.py.log` | `regress_cj2_b2_stage_c_admission_gate_static_tests.py.log` | `3baddbda3e36833972823db3da53b62efbea22e9964903f963a2c6089211ef76` | 2026-08-13 17:52:27 | 7704 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/regress_cj2_b2_v2_static_tests.py.log` | `regress_cj2_b2_v2_static_tests.py.log` | `c8566a60aa12b6158038f7e1ebba9b509cb9ff8ec969fe26e89cd5232f828c7c` | 2026-08-13 17:52:26 | 3397 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/run_stage_c_probe.py` | `run_stage_c_probe.py` | `8c4cdbfb7385b8a55c8b1461cfe60a429862ddeb88bf7140cf7214e20c0ba667` | 2026-08-13 13:23:07 | 1490 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/stage-c-first-probe-bundle/.probe_fixtures/cj2-b2-stage-c-first-integrated-development-probe/pre-run-identity.json` | `stage-c-first-probe-bundle/.probe_fixtures/cj2-b2-stage-c-first-integrated-development-probe/pre-run-identity.json` | `e32cdd1d7e17a3a1e27e799779730a49853f2a74c142dd8ed308e37ef2a0113a` | 2026-08-13 13:21:18 | 2492 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/stage-c-first-probe-bundle/cj1_v3_anchor_resolver.py` | `stage-c-first-probe-bundle/cj1_v3_anchor_resolver.py` | `d8f761e54822526dda1ed021a5eb5e6c017d8048abf60b2f6caf7525d7ff983b` | 2026-08-11 15:32:55 | 7032 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/stage-c-first-probe-bundle/cj2_b2_d0_prototype.py` | `stage-c-first-probe-bundle/cj2_b2_d0_prototype.py` | `34f52ed994b77e6967f21ceb0d37677ee65cb86c6908d86ce8c7d6030a0a8873` | 2026-08-12 18:33:39 | 28067 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/stage-c-first-probe-bundle/cj2_b2_v2_probe.py` | `stage-c-first-probe-bundle/cj2_b2_v2_probe.py` | `ae8b2fbdf07eefab8d3fea4ce3684e3cae6364520560b547b3bf94deaa642d01` | 2026-08-12 14:14:14 | 37003 | RAW |
| CJ1/CJ2 dev artifact | `/Users/stargatesgx/.claude/jobs/2c987bae/tmp/stage-c-first-probe-bundle/production_orchestrator.py` | `stage-c-first-probe-bundle/production_orchestrator.py` | `a85df47c4e286cf9077e3296a0885dda12d8fffea7c7895002fd00be7c999b84` | 2026-08-10 16:15:09 | 9919 | RAW |

## Status vocabulary applied

- **DUPLICATE_CONFIRMED** — 67 further CJ files in the job dir hash-matched a durable copy in
  `cripminds-preservation/` or the repo working tree; not copied again, sources left in place.
- **NEVER_PERSISTED** — none in this group.
- **LOST** — none in this group.
- **NOT_FOUND** — none in this group.

# Prompt Baseline — hash-frozen

All hashes are SHA-256 of the exact string the production code builds, extracted at
HEAD `c6f97b8` (pipeline code byte-identical to production `8af3622` — see
`GIT-AND-RUNTIME-BASELINE.md`).

**No model call was made to produce any of this.** Static literals were extracted by AST
`literal_eval`; the assembled writer prompt was reproduced with the repo's own zero-network
capture harness (`automation/writer_prompt_test.py::_capture_writer_prompt`).

## Assembled writer prompt — referenced, not duplicated

The assembled writer prompt was already preserved in the Legacy Prompt / Rule Inventory.
It was **re-derived in this task and reproduces byte-identically**, so it is referenced by
path + commit + hash rather than copied again.

| Artefact | Preserved at | Commit | chars | SHA-256 |
|---|---|---|---|---|
| assembled writer prompt (Maya Flux) | `.claude/experiments/legacy-prompt-rule-inventory-2026-08-20/writer_prompt_maya.txt` | `38c47b8` | 59,161 | `9ffeb860124cf4efa09558f7653c0a535a1979b236e3751a12b8881c02ae7637` |
| assembled writer prompt (Pixel Nova) | `…/writer_prompt_pixel.txt` | `38c47b8` | 54,673 | `8e217476800145d7af473416fbf091e3d95ffd51bb557db6df353fb12796f6eb` |
| assembled planner / Story-Rejection prompt | `…/planner_user_prompt.txt` | `38c47b8` | 15,358 | (see that root's `SHA256SUMS.txt`) |

Reproduction check run 2026-08-20: **both reproduce byte-identically. VERIFIED.**

## Static prompt surface

| Artefact | Location | chars | SHA-256 |
|---|---|---|---|
| **writer SYSTEM** | `orchestrator/llm.py:232` | 3,212 | `c8ffc6824e6854ae17972e6ee57df410d48e6e3779d6591de475e630f9dd9bf7` |
| **rewrite_with_opus SYSTEM** | `orchestrator/llm.py:394` | 25,019 | `921c907645358aa113bb64f324ced7e9c34a6be631685700cd800cdfe10d9db3` |
| **GATE_SYSTEM** (gate LLM rule prompt, R1–R17) | `orchestrator/gate.py:233` | 8,105 | `19404edf587dd0d31ef270f1b3845870112746745d4a6444b7bbcfe906a969df` |
| **RULES_SYSTEM** (review LLM rule prompt, R1–R19) | `orchestrator/review.py:1173` | 9,035 | `7ce0893ad05d44dbbcc9ba9668e7bcfcef1520989744e1076b675696d3e9a461` |
| `_EXECUTOR_CONTRACT` | `orchestrator/llm.py:61` | 2,007 | `f8ed0bfa351ebe746cbdc6567854d1a64654eb5ac7fea79591131a2ee5add8b1` |
| `_EXECUTOR_PERSONA_HISTORY_CONTRACT` | `orchestrator/llm.py:101` | 750 | `53a34b678976bf64e67b3b3ebc39d9450620153d6ea909825f22b7f4fb4c5029` |
| `CITATION_SYSTEM` | `orchestrator/review.py:879` | 517 | `cfc3b54fae6aea7cd2d2747a75870e92fdc7f13b29e9f3b870ed96cbb9e42d9b` |
| `SUBJECT_SYSTEM` | `orchestrator/gate.py:51` | 533 | `cf1d06adc7564e62e71a4e88a642be22a1435e8834f2b52b5dd89d67dfcf6699` |
| `FIX_SYSTEM` (register) | `orchestrator/gate.py:510` | 1,221 | `0412cac6c409b2dbc2caaed94d43c2fab82e38681a083921147ce35052a963cc` |
| `FIX_SYSTEM` (form) | `orchestrator/gate.py:530` | 421 | `5d004965778f3eaf1cae94532d7b247654fcae2ab4d2fa6502e01bfc29fe45c4` |
| fact_check SYSTEM | `orchestrator/fact_check.py:33` | 905 | `bb7eb781eda0d5c3a604174784cb631d2e15052ae054cf4aa3be7f43e34e0a48` |
| content_checks link SYSTEM | `orchestrator/content_checks.py:373` | 1,070 | `f8fba70d260ccb17df8ed06d1b8047cfe8f660a0d2b298851bad184f23e91f32` |

## Persona canon payloads

| File | chars | SHA-256 |
|---|---|---|
| `persona_canon/maya-flux.md` | 7,217 | `4c69be115ddd94c8958c8c4bbe904b21b0215915148ed0ba88b85afe71da0edd` |
| `persona_canon/pixel-nova.md` | 5,904 | `00f2d991aa3ae81f7f2f8f6a648de941042a30d44db44cee6576f8680656c78e` |
| `persona_canon/pixel-nova-factual.md` | 8,220 | `d576ddb9b9ac9bc135e009d2b7b0361d2220c439187c783317fc48c798b0ffbd` |
| `persona_canon/siri-sage.md` | 6,386 | `33663d8a2c962b6cda1ee1fae1c37d1c155aa5d089ec003fea6fe6e2e95a52c5` |
| `persona_canon/zen-circuit.md` | 9,137 | `3a24f3b2c00181f983d12b2a526856d2ec24b95875f6be96a93572959d4f8bc2` |

## `personas.py` prompt blocks

| Persona | chars | SHA-256 |
|---|---|---|
| Maya Flux | 3,323 | `754e8b7672147fb20e0d39ec890619e8bb2b41ca587c47ea2c0e08549d1c4bc5` |
| Pixel Nova | 4,337 | `372045c0165eb6629408b038b75e0de47553597fd09983e8c4a3cd0854825e19` |
| Siri Sage | 4,330 | `122912482a173024bcbcd3326868d2f69c51bceda0029fdef5ed491eada2b728` |
| Zen Circuit | 3,694 | `30d506a76c9681e90d41b35a85f05463eb49b113c67da2ea363c41f0864fee88` |

## Pipeline source-code hashes (local == production, verified)

| File | SHA-256 |
|---|---|
| `automation/production_orchestrator.py` | `494ca6f25fc5d5de12fd4b7b68490b62aae62a7430b395c55396a8e406a973bf` |
| `orchestrator/generate.py` | `4336ad5fa9e64e6ea2052cdc19af940b2f91162b7f9d34b44ffec947387fb36f` |
| `orchestrator/llm.py` | `56b4632c426f844e903041999b98c83e6aac08089bc097cda85fd1cabeffecc7` |
| `orchestrator/gate.py` | `0101782a82c9fe9b5420613ddcba4ef0c7f968ebd4388b7742ea5fd70339299c` |
| `orchestrator/review.py` | `50c7bb10b16b39d76bc73f684cd8a15c1e359cbbf5aa3f7017de275a0d3451d8` |
| `orchestrator/grounding.py` | `6d06726124ef23163b77fb71647a632cde46d325cb6e8d742a4aa6aaca27f729` |
| `orchestrator/discovery.py` | `baa1315cb828f24a595e4833ee91def374bfced190910b90c9669ef04ff1643e` |
| `orchestrator/config.py` | `cbb41d57e6c74984f5264e46f576adc5844b94562b39cae5941d16eacf79c140` |
| `orchestrator/personas.py` | `d662bad9af0a499be2df4fa150c07f3442fd1f02dc3567c90408d2255e1c6581` |
| `orchestrator/fact_check.py` | `47802ebec19d792a660bda9314993252bf9f9b83ef8887db70e1bea034346efa` |
| `orchestrator/cj2_shadow.py` | `beeddb4f9f82c2a8e33d92082583ce7ff5012bc7ea5224345732a690679b727b` |
| `orchestrator/testimony_l2.py` | `8bd2927088f05cc6844a539c8ca558a9c33b6d367809703797a74f905748d77e` |
| `automation/style_rules.py` | `42694319f046deb3d855523d9060bcb0268b858c03639ae12b0a0667d4829940` |

## Totals

Rule-bearing prompt text reaching a model on one production article run:
**≈ 130,000 characters**, carrying **≈ 158 distinct prescriptive rule statements**
(75 writer + 47 rewrite + 19 review + 17 gate), before persona canon, source material and
nudges.

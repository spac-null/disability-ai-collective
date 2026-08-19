# FORM-1.2 — Narrow Provenance Correction (Real Article Test 1, Edinburgh)

Run 2026-08-19. Single writer call. No retries, no candidates, no cherry-picking.

## Frozen inputs (verified by SHA-256 before execution)
| input | sha256 |
|---|---|
| source-snapshot.txt (Guardian, frozen) | fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753 |
| commission-brief.json | 870d84ba931abf194db5fad8017185cbf2f034ec08e383d1d89fcb8b3fce3387 |
| evidence-packet.json | 8628b234e1fc335b391b26a2dddf7b048b626f073b09a0cf6706f4e2d5ce60a5 |

## Pre-execution preservation (the gap FORM-1.1 had, now closed)
| artifact | sha256 |
|---|---|
| form1-2-packet.json | a1671eb807c220aaaa81dc0a550af92dab68dd2063b260af0a8e93c3c35b948f |
| form1-2-writer-prompt.txt (exact rendered prompt) | a93b750e8217919c2d73ee41d8f7eee3e7868116b55634ea66d06fc37cd6d537 |

The runner is two-phase (`--preserve` / `--execute`). `--execute` re-derives the packet
and prompt and refuses to proceed unless both hash-match the already-persisted artifacts,
and refuses if an article already exists. The persisted prompt is therefore provably the
executed prompt, and the one-call limit is enforced structurally.

## Model and parameters (unchanged from every prior Edinburgh iteration)
- requested: openrouter/claude-opus-4.8 ; resolved: anthropic/claude-opus-4.8
- max_tokens=5000, timeout=180, no_think=False, no temperature override
- writer calls made: 1

Note: the task text named `anthropic/claude-opus-4.8`. That is not a routable id on this
CLIProxy; `openrouter/claude-opus-4.8` is, and it is the exact string every prior Edinburgh
iteration used. It resolves upstream to `anthropic/claude-opus-4.8`. Using it satisfies both
"same historical call path" and "do not change writer model".

## Output
| artifact | sha256 |
|---|---|
| form1-2-article.md (635 words) | f2f59f35f774fe6c36eca42d86d5776da1b9bfd9f4c815cac4075c1cd7f648a6 |

## Authorized delta from FORM-1.1 — only changes A, B, C
- A: removed "Begin with how the festival describes its own way of being encountered."
  (the frozen source contains no festival self-description); replaced with
  "Begin with the reviewer's description of what it is like to move through and encounter
  the festival." No destination preload, no new thesis.
- B: opening_material reclassified SOURCE_FACT -> REVIEWER_NARRATION (one narrow provenance
  type added; packet schema otherwise unchanged). Same items, same order, same text.
- C: provenance now survives into the writer prompt, rendered naturally
  ("From the reviewer's narration: ..." / "Source fact: ..." / "The reviewer explicitly
  argues: ..."), plus an explicit attribution boundary.

Unchanged: discovery, commission, source, selection, sequence, argumentative burden,
destination, arrival discipline, no-centrality boundary, Hasegawa omission, grounding
boundaries, length guidance, attractor guards, writer model, generation parameters.

Recorded but deliberately NOT changed (would add a second variable): the reattribution
verb blocklist is literal and is applied only to Form-authored text at packet-build time,
never to writer output.

## Result
Grounding audit (FORM-1.1 auditor, byte-identical except paths): FAIL,
4 UNSUPPORTED / 1 UNCERTAIN / 2 SUPPORTED of 7 claims.

Independent adjudication: 4 TRUE_UNSUPPORTED, 0 TRUE_UNCERTAIN, 1 AUDITOR_OVERSTRICT.

The hypothesis under test is DISCONFIRMED. All three corrections landed as designed and
provenance reattribution got worse, not better: 6 festival-possession/self-description
phrases vs FORM-1.1's 3, and 4 true unsupported vs FORM-1.1's 2.

Decision: FORM_LAYER_STILL_UNSTABLE.

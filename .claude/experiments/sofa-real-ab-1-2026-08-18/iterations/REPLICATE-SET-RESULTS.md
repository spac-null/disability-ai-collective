# FORM-1.3 Frozen Variance Replicate Set — Results

Three independent one-generation runs under ONE byte-identical condition.
Run 2026-08-19. Not a new Form version; the fixed FORM-1.3 prompt is the experimental object.

## Frozen condition (identical in all three directories, hash-verified, never rebuilt)

| | |
|---|---|
| source | `fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753` |
| packet | `a620d0ce700a501de1695cc63253b518da283397388dba4dfb1f570af8f8e8ab` |
| rendered writer prompt | `12e520e449752ed89522963c77a48fc2b86636a31a20d8f3ca47ac4ec276cdfd` |
| model | `claude-opus-5[1m]` |
| execution mode | `LOCAL_CLAUDE_SUBSCRIPTION` |

Manual architecture-development runs, NOT production-path replays. No OpenRouter, no Trident,
no Fable. One generation each, no retries, no candidate selection. Three distinct article
hashes confirm three independent generations.

| run | article sha256 | words |
|---|---|---|
| FORM-1.3 | `9a78d9a4c28f4a891cf222b28c87d76fe567bc31c0ff7eec8d56aa93d339bff4` | 691 |
| FORM-1.3-R2 | `5ea20461cc09484d7bf1fea3f83de526f5c54720b72438e180cf92e4f1f600ad` | 633 |
| FORM-1.3-R3 | `27b1038c80af9890ca07b5b4ab1533670b3425f11c41d2898d2a61d806086d94` | 646 |

## Form-owned structure — STABLE 3/3

| dimension | FORM-1.3 | R2 | R3 |
|---|---|---|---|
| festival-as-speaker/possessor | 0 | 0 | 0 |
| discovery ownership failures | 0 | 0 | 0 |
| countervoice before arrival | YES (5/8) | YES (5/8) | YES (4/7) |
| arrival final | YES | YES | YES |
| paragraphs after arrival | 0 | 0 | 0 |
| post-arrival restatement | NONE | NONE | NONE |
| attribution-bookkeeping leakage | 0 | 0 | 0 |
| agency/consent attractor | 0 | 0 | 0 |

Justified statement: **Article Form's targeted epistemic/narrative behaviour is stable across
3/3 identical-condition Edinburgh generations.** NOT production canonical. NOT transfer-validated.

Incidental: FORM-1.3's flat arrival (0.65 similarity to the supplied destination sentence) was
writer variance, not a Form property — R2 and R3 land at 0.44 and 0.49.

## Grounding — SYSTEMATICALLY DEFICIENT

Every run failed independent adjudication. Exact claims varied; classes did not.

| class | FORM-1.3 | R2 | R3 | rate |
|---|---|---|---|---|
| INVENTED_VISITOR_STATE / TEMPORAL_SPECIFICITY | "an hour ago", "did not know the work existed" | "brought nothing to the encounter" | "an hour earlier", "in August" | **3/3** |
| INTERPRETATION_AS_FACT | — | "the second direction is the harder one" | "harder to discharge, because…" | **2/3** |
| QUALIFIER_DROPPED | — | Hasegawa "Most of" → absolute | — | 1/3 |
| INVENTED_PROPER_NOUN | "City Art Centre" (source: City Art Gallery) | — | — | 1/3 |
| FORM_INSTRUCTION_AS_PROSE_CLAIM | — | "not because the review places them above the rest" | — | 1/3 |

Primary origin: overwhelmingly WRITER (8 of 10 genuine findings). FORM 1. SOURCE_PARAPHRASE 1
(secondary). Auditor: 1 overstrict (R2 "no map"), 1 miss (R3 "an hour earlier", added on
independent adjudication).

Auditor claim counts (8 / 4 / 3) are NOT comparable — the auditor selects its own claim set.

## Two limits of Form-level control

1. **Form-level omission is not a grounding control.** Hasegawa was deliberately omitted from
   the packet in FORM-1.1 to prevent FORM-1's dropped-"most" failure. He appears in all three
   runs anyway, pulled from the full source the writer also receives; R2 reproduced FORM-1's
   qualifier failure exactly.
2. **A negative Form constraint can surface as a positive prose proposition.** R2's "not because
   the review places them above the rest" is the Form's no-centrality boundary rewritten as an
   assertion about the review — and the source arguably ranks them. Design preference: prefer
   positive boundaries / positive ownership statements over elaborate negative prohibitions.
   (FORM-1.3 stays frozen; this is recorded, not applied.)

## Decision

**D — SYSTEMATIC_GROUNDING_PROBLEM.** Structural Form behaviour is stable; the same class of
unsupported sentence-level invention recurs across runs. Explicitly NOT an Article Form failure.

Architectural boundary (leading working hypothesis):

- **ARTICLE FORM owns** semantic relationships, argumentative burden, reader route, functional
  placement, arrival/stop.
- **WRITER + GROUNDING CONTROL own** factual specificity, qualifier preservation, the
  fact/interpretation distinction, source-faithful names/times/states/details, and the
  prevention or detection of unsupported prose claims.

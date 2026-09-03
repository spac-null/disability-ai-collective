# Overnight baseline: why publication-eligible candidates fail the human reader

Campaign start 2026-09-03T22:24Z. Base `40be348` (PR #61 merged). No OpenRouter spend.

## Corpus (5 cases)

| case | role | source of artefact |
|---|---|---|
| `the-map-that-stops-at-the-door` | **positive control (substitute)** | `_posts/2026-03-16`, canon best, human-scored 27/30 |
| `the-pavilions-at-jia-curated-2026…` | diagnostic: good idea, failed execution | `_drafts/2026-09-03` + full frozen run `601f5d23` |
| `a-conservation-centre-built-around-a-blocked-journey` | negative | `_drafts/2026-09-03` + full frozen run `4dd582f6` |
| `the-universe-that-only-some-scientists-could-read` | wrong-publication (Smolin) | `_drafts/2026-09-03` + frozen run `ec372f9c` |
| `langrug-frozen-article` | strong story material | `automation/fixtures/langrug-2026-09-03/` |

**The Galton / Anthropometric Laboratory article ("One Door In, One Door Out") does not
exist as a frozen artefact.** Searched `_posts`, `_drafts`, full git history across all
branches, `reader-lab/rounds/drafts/`, `calibration/`, and every `article.md` under
`/srv/data/cripminds-new-engine-v1/`. No match for `anthropometric`, `three-pence`,
`galton`, or the title. It was **not** reconstructed from memory. The canon-best
`map-that-stops-at-the-door` stands in as positive control (§6F, one addition).

## Diagnostics (counts are symptoms, never scores)

| case | words | paras | w/para | med sent | PN | PN/100w | LEAK | essay | opening | final sent |
|---|---|---|---|---|---|---|---|---|---|---|
| map-that-stops **(PASS)** | 1819 | **49** | **37** | **10** | 56 | 3.1 | **1** | **0** | other | **6** |
| jia (HOLD) | 613 | 7 | 88 | 14 | 38 | **6.2** | **10** | 3 | press-release/date | **49** |
| eel (HOLD) | 620 | 8 | 78 | 15 | 10 | 1.6 | **14** | 2 | research statement | 13 |
| smolin (wrong pub) | 660 | 8 | 83 | 17 | 31 | 4.7 | 1 | 0 | press-release/date | 49 |
| langrug (frozen) | 641 | 7 | 92 | 14 | 14 | 2.2 | 5 | 0 | scene/event/object | 23 |

`LEAK` = reader-facing provenance/auditing constructions ("the source", "does not
establish", "nothing in the source"…). The bare word "source" is deliberately not
counted: a document can be story material.

## Two distinct failure modes, not one

1. **Research-machinery leakage** — jia (10) and eel (14) against the positive
   control's **1**. This is the reader-gate failure.
2. **Missing publication lens** — smolin's prose is *clean* (LEAK 1, essay 0). Its
   problem is that no Crip Minds lens survives into the article at all. A prose fix
   would not touch it; it needs a gate that can say "wrong publication".

Treating these as one problem is why prose-level fixes have not worked.

## Root cause, measured

The Writer receives the research *process*, so it reproduces the process.

| | jia | eel | smolin |
|---|---|---|---|
| Writer prompt words | 5,840 | 5,554 | 7,121 |
| article words out | 613 | 620 | 660 |
| **input : output** | **9.5 : 1** | **9.0 : 1** | **10.8 : 1** |
| "source" in the prompt | 18 | 17 | 15 |
| source-ID markers `S0..Sn` | 31 | 27 | 32 |
| role-taxonomy words | 7 | 5 | 6 |
| verified-excerpt blocks | 16 | 11 | 16 |
| grounding-boundary prose | 6 | 5 | 6 |
| raw source words rendered | 1,147 | 1,519 | 2,510 |

### The mechanism, proven verbatim

`evidence_gaps` and `grounding_boundaries` are **machine constraints handed to the
Writer as content**, and the Writer turns them into sentences:

| given to the Writer | became, in the article |
|---|---|
| "The source does not describe how any visitor actually perceived or navigated these spaces" | "It does not report what any visitor experienced, and I am not claiming it does." |
| "The source does not state that any pavilion was designed with disabled visitors, blind or low-vision visitors" | "Nor is any of this an accessibility claim: nothing in the source says these pavilions were made for, tested with, or reached by blind or low-vision visitors…" |
| "The anchor does not describe the physical form of the building, its site" | "It does not describe the building's form, its site, or any actual device that restores migration." |
| "The source does not describe what visitors actually see or do" | "What that looks like as a building, the source does not tell us." |

This is §17 exactly: a constraint that should have bounded the generator became article
content instead.

**It also explains a finding from tonight's Grounding V2 shadow observations.** The 7
`LIKELY_META_COMMENTARY_TYPING` results (obs 1: S030-A2/A3, S031-A1/A2; obs 2: S034-A1,
S035-A2, S038-A5) are these same sentences: V2 correctly types "the source does not
report X" as an empirical negative-existence claim and cannot support a negative. The
grounder was reporting this defect from the other side all along.

## Structural difference in the positive control

The canon winner is not merely cleaner in wording. It **breathes**: 49 paragraphs at 37
words each and a median sentence of 10 words, against 7–8 paragraphs at ~85 words and
median 14–17. And it lands in **6 words** where jia and smolin land in **49**. Cognitive
load is a layout property here as much as a sentence property.

## What this implies for the architecture

- The Writer packet must carry the *story*, not the *research*. Prohibitions must
  constrain generation and never appear as content.
- `evidence_gaps` must stop being a Writer field. It is a gate input.
- Something must be allowed to answer "why is this a Crip Minds article?" **before**
  prose exists, and be allowed to answer "it isn't" (smolin).
- A CUT list is as load-bearing as a USE list: jia's 38 proper nouns in 613 words are
  research that survived because it was discovered, not because a reader needed it.

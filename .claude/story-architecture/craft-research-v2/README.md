# Nonfiction craft research v2

Empirical reverse engineering of accessible nonfiction, done before any further Story
Architecture design. Research artifacts only: **no implementation code was changed, no
production behaviour was touched, no OpenRouter spend, nothing published.**

Campaign date: 2026-09-04. Revised the same day after V1 seed artifacts were supplied
(`seed/`), which added 22 verified sources and revised one V2 finding.

## State at time of research

```
origin/main                      40be3486c218e8ba766ade4866286a5b7a33fad8   (PR #61 merge)
origin/feat/story-architecture   b447a82850a9a21ae426447478876eba9d2cae00   (PR #62 head)
PR #62                           OPEN, MERGEABLE, 99 files, +9,178 / -0
local main                       732c84f9 — DIVERGED from origin/main in both directions;
                                 left untouched, not reset. All work done in a separate
                                 worktree off origin/feat/story-architecture.
```

## Corpus

| sample | n analysed | body words | notes |
|---|---|---|---|
| Bregman public texts | 18 (+1 unavailable) | 43,115 | 6 article forms; 3 added from the V1 seed and verified |
| Scientias.nl | 31 (+1 unavailable) | 19,829 | 8 domains; 6 added from the V1 seed and verified |
| Control exemplars | 12 | 50,033 | all professionally annotated as teaching examples |
| Craft teaching sources | 28 (+3 HTTP 403) | — | Open Notebook, Nieman Storyboard, Berkeley, Creative Nonfiction, writing centres |
| Professional annotations | 421 | — | Open Notebook / CASW Storygrams, each paired to the exact story span |

The two passes' samples were largely disjoint: 8 of 12 Bregman texts shared, **0 of 20**
Scientias articles shared, 4 of 16 craft sources shared. Extending the samples moved no
headline number — Bregman single-clause share 0.60 → 0.59, Scientias question density 0.91 →
0.96, Scientias paragraphs ≤15 words still **0.00 across 31 texts**.

**No copyrighted article or book bodies are stored in this repository.** What is committed is
metadata, structural annotations, derived statistics, findings, and short quotations where
analytically necessary. Article texts were fetched to a scratch directory outside the repo for
measurement and are not retained here.

## Files

```
sources/
  craft_sources_v2.jsonl              73 source records: id, category, author, title,
                                      publication, date, language, translation_status,
                                      article_form, availability, url
  craft_corpus_v2.jsonl               52 texts: derived statistics only, no bodies
annotations/
  paragraph_annotations_v2.jsonl      421 professional craft annotations, topic-coded,
                                      with the span length and a short excerpt
  annotation_topic_counts.json        topic frequency (45% residual — see caveat)
metrics/
  craft_metrics_v2.json               sentence / paragraph / density aggregates by sample
  pr62_detector_calibration.json      PR #62's own detectors run unmodified against
                                      published prose, plus the three Jia drafts
reverse-outlines/
  reverse_outlines_v2.jsonl           83 coded units: primary mode + abstraction level
seed/
  README.md                           V1 status, verification performed, independence guarantee
  CRIP_MINDS_CRAFT_CORPUS_V1.md       supplied V1 artifact — NON-AUTHORITATIVE
  cripminds_craft_corpus_v1.json      supplied V1 artifact — NON-AUTHORITATIVE
  v1_v2_adjudication.jsonl            48 adjudications: 31 confirm, 11 revise, 3 reject,
                                      2 unverified (403), 2 untested
reports/
  V1_V2_COMPARISON.md                 the comparison table and what the seed changed
  CRAFT_EVIDENCE_V2.md                believed / confirmed / disproved / complicated /
                                      new / unknown  ← read first
  craft_evidence_table_v2.jsonl       25 findings with evidence type, sources, confidence,
                                      scope, counterexamples, owner alignment, engine relevance
  CRAFT_METRICS_V2.md                 the numbers, with denominators and limitations
  BREGMAN_ACCESSIBILITY_PROFILE_V2.md transferable craft, not style imitation
  SCIENTIAS_EXPLANATION_PROFILE_V2.md what transfers and what is press-release formula
  NONFICTION_REVERSE_ENGINEERING_V2.md paragraph maps, reader-question analysis, held-out
                                      predictions
  CRAFT_EXERCISES_V2.md               20 professional exercises, mapped to engine stages
  PR62_CRAFT_GAP_ANALYSIS.md          read-only component-by-component comparison
```

## The three results that matter most

**1. PR #62's `solo_ratio` defect signal does not discriminate; its signpost signal does.**
Run unmodified against 1,181 paragraphs of published prose, `continuity.writtenness()` gives
Jia a `solo_ratio` of 0.33 — inside a published range of 0.00–0.37, matched or exceeded by two
Bregman texts and a ProPublica investigation. The signpost-opener rate, by contrast, separates
cleanly: 0.005 per paragraph in narrative exemplars, 0.051 in Bregman, **0.333 in Jia**. The
module's stated diagnosis names the wrong variable and its other signal is excellent.

**2. Information order should follow the reader's open question, and PR #62 already contains
the idea.** Confirmed independently by a Knight Chair in Editing, by annotators of twelve texts
Crip Minds had nothing to do with, and by Bregman — who implements it as visible text in short
standalone "pivot paragraphs" at structural hinges. `why_reader_wants_next` is the right field;
it is missing only the checkable half.

**3. `ARTICLE_TYPES` is a length scale, and all three live values are narrative.** Structural
craft is form-dependent — opening type, background architecture, signposting level, thesis
placement and nut-graf necessity all change with form. Every article currently gets the
narrative column, and the hard requirement that openings be concrete forecloses the rest before
anything else is consulted.

## What the V1 seed changed

One V2 finding was materially revised: the transitions result. The first pass concluded from
measurement that visible signposting is near-absent from narrative features. A source the V1
pass had listed and this pass had missed — The Open Notebook's *Good Transitions* — shows the
measurement was counting only outline-announcing openers, while narrative features carry
visible **content** transitions constantly and the literature calls them good craft. The
correction strengthens the gap analysis rather than weakening it.

Three findings were added from V1-listed sources this pass had not read: the three-tier scene
provenance taxonomy (F-27, the most useful item either pass found for reconciling craft with
the safety invariants), "tell the story of the explanation" (F-26), and "the more complex the
material, the simpler the structure should be" (F-30). Two further additions (F-28, F-29) and
one new instance in F-08.

V1 was wrong in one way that would have mattered: its transitions principle and exercise, which
its own cited source contradicts. If inherited, it would have pushed the engine toward deleting
taught craft.

## What this campaign did not do

No architecture verdict. No Writer or Continuity prompt change. No Jia rewrite. No merge. No
production integration. Nothing here has been tested against a generation, which is the
obvious next campaign and is not this one.

## Honest limitations

- Control-exemplar paragraph boundaries are unreliable (n=2 of 12); all control paragraph
  metrics are unusable and are marked as such.
- Clause counting is a regex proxy, valid between these samples and invalid as an absolute.
- Dutch and English passive/nominalisation/modal measures are not cross-comparable.
- The abstraction coding is one unblinded coder with no second rater.
- Two Poynter sources returned HTTP 403 and are recorded as unavailable rather than substituted.
- Three corrections are documented rather than quietly fixed: Scientias' question density was
  initially fourfold overstated by site boilerplate; Guardian standfirsts were initially being
  read as opening paragraphs; and the transitions finding was too strong until a missed source
  was read.
- Three V1 sources return HTTP 403 to us (Harvard, two Poynter pages). V1 attributes principles
  to them; V2 uses none of them and records them unavailable.
- Ten V1 titles differ from the live page. Eight are Scientias headline rotations confirmed by
  the URL slugs; one (`B09`) is a genuine title change; one is a minor truncation.

# Nonfiction craft research v2

Empirical reverse engineering of accessible nonfiction, done before any further Story
Architecture design. Research artifacts only: **no implementation code was changed, no
production behaviour was touched, no OpenRouter spend, nothing published.**

Campaign date: 2026-09-04.

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
| Bregman public texts | 15 (+1 unavailable) | 31,502 | 6 article forms; 6 texts translated or translation-unconfirmed |
| Scientias.nl | 25 (+1 unavailable) | 15,652 | 8 domains |
| Control exemplars | 12 | 50,033 | all professionally annotated as teaching examples |
| Craft teaching sources | 18 (+2 HTTP 403) | — | Open Notebook, Nieman Storyboard, Poynter, university writing centres |
| Professional annotations | 421 | — | Open Notebook / CASW Storygrams, each paired to the exact story span |

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
reports/
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
- Two mid-campaign corrections are documented rather than quietly fixed: Scientias' question
  density was initially fourfold overstated by site boilerplate, and Guardian standfirsts were
  initially being read as opening paragraphs.

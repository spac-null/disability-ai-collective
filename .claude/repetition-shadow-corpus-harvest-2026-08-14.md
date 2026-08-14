# Repetition-shadow offline corpus harvest — 2026-08-14

A-M reconciliation item G. `_check_repetition_shadow` (review.py, commit `204c3bc`)
is SHADOW MODE ONLY — no promotion before 2026-08-28. This is descriptive evidence
only, gathered by running the existing detector, unmodified, across every committed
published article in `_posts/` (140 articles, safe local corpus — already public,
already committed, zero network calls). Script: `automation/repetition_shadow_corpus_harvest.py`.

**No threshold changed. No blocking authority changed. Detector code unmodified.**

## Headline numbers

- 140 articles scanned, 0 errors.
- 101 articles (72.1%) produced zero candidates.
- 39 articles (27.9%) produced 1+ candidates, 50 candidate pairs total.
- Raw similarity distribution: min 0.35, median 0.47, p75 0.91, max 1.00 — bimodal
  (a cluster near the 0.35 threshold floor, a second cluster at 0.9-1.0).

## Finding 1 — 60% of all candidate pairs are a mechanical false-positive artifact, not prose repetition

Breaking the 50 pairs down by whether either paragraph is an HTML `<figure>` image
block (every published article has 2-4 of these for its generated images):

| Category | Count | % of total |
|---|---|---|
| figure-block vs figure-block | 30 | 60% |
| figure-block vs prose (mixed) | 3 | 6% |
| prose vs prose | 17 | 34% |

The check's own HTML-stripping (`re.sub(r'<[^>]+>', '', body)`) removes the tags
but not the `<figcaption>` text or `alt="..."` attribute text — both of which
repeat the article's own title/slug words plus boilerplate (`loading`, `lazy`,
`decoding`, `async`) across every image block in the same article. Two image
captions in the same piece will always share several content words purely from
restating the title, independent of any real editorial repetition. Confirmed
directly (e.g. `2026-08-07-a-stack-of-colours-has-not-made-a-single-sound-yet`
paragraphs 8&15, both `<figure>` blocks, sim=0.60 — no shared editorial content,
only slug words and markup attributes).

**Candidate proposal, not implemented this pass** (detector mechanics are frozen
during the observation window per the check's own docstring): strip
`<figure>...</figure>` blocks entirely before paragraph splitting, the same way
frontmatter and markdown links are already stripped. This alone would remove
33/50 (66%) of all candidates recorded so far without touching the
similarity_threshold at all — a preprocessing fix, not a calibration change.

## Finding 2 — a real published-content duplication bug, unrelated to G's calibration question

Of the 17 genuine prose-vs-prose pairs, 10 score ≥0.85 (near-identical), and 8 of
those 10 are concentrated in a single article:
`_posts/2026-03-31-the-floor-plan-of-disappearance.md` (26 paragraphs). Paragraph
pairs (0,14), (5,19), (6,21), (7,22), (8,23), (10,25), (3,17), (9,24) — a
consistent ~14-15 paragraph offset — are near word-for-word restatements of each
other (confirmed by direct inspection, e.g. paragraph 0 and paragraph 14 both open
"In February 2024, the Dutch municipality of Almere published a redesigned care
portal..."). This reads as the article's content having been duplicated within
the same published file (front half and back half substantially the same essay),
not a deliberate refrain or an editorial repetition question G is meant to
calibrate. **This is a content-integrity bug in a live published article, not a
repetition-shadow calibration finding — flagged here per instruction, not fixed.**
Fixing a published article's body is an editorial decision, not a code change,
and out of scope for this overnight run's queue; needs human review before any
edit to `_posts/2026-03-31-the-floor-plan-of-disappearance.md`.

The other 2 near-duplicate prose pairs (`2026-03-10-the-navigation-tax` 38&39,
`2026-03-11-the-prosthetics-paradox...` 42&43, both sim=1.00) are single isolated
pairs within otherwise normal articles — worth a human skim, lower urgency than
the floor-plan article's near-total duplication.

## Finding 3 — the actual calibration-relevant data is much smaller than the headline count

After removing figure-block noise (Finding 1) and the one anomalous duplicated
article (Finding 2), the genuinely interesting sample for G's real purpose —
"is a repeated claim a flaw or a deliberate refrain" — is 7 prose pairs across
~6 articles, scored 0.35-0.85. Too small to validate or reject
`similarity_threshold=0.35` from this pass alone; consistent with the check's
own 2-week-minimum-observation discipline rather than a reason to extend it.

## Not done (explicitly out of scope this pass)

- Threshold not changed (0.35 stands).
- Figure-block preprocessing fix not implemented (candidate only, see Finding 1).
- `2026-03-31-the-floor-plan-of-disappearance.md` not edited (Finding 2 — needs
  human/editorial call, not a code fix).
- No promotion of the shadow check toward blocking authority.

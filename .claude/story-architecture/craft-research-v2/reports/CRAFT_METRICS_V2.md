# Craft metrics v2

Every number here has a denominator. Nothing here is a craft law; these are diagnostics that
separate three samples, and separation is not causation.

Raw per-text rows: `../metrics/craft_metrics_v2.json` (aggregates) and
`../sources/craft_corpus_v2.jsonl` (per text, derived statistics only — no article bodies are
stored in this repository).

## 1. Dataset and extraction quality

| sample | texts sought | fetched 200 | usable full text | partial | unavailable | body words |
|---|---|---|---|---|---|---|
| Bregman public texts | 16 | 16 | 14 | 1 (`BR-15`, 417 w short-form extract) | 1 (`BR-16`, navigation page) | 31,502 |
| Scientias | 26 | 26 | 25 | 0 | 1 (`SC` physics podcast page, 47 w) | 15,652 |
| Control exemplars | 12 | 12 | 12 | 10 with merged paragraphs | 0 | 50,033 |
| Craft teaching sources | 20 | 18 | 18 | 0 | 2 (Poynter, HTTP 403) | — |
| **Total analysed texts** | | | **51** | | **4** | **97,187** |

Plus 421 professional annotations extracted from 12 Open Notebook / CASW Storygrams, paired to
the exact story span each comments on.

**Extraction caveats, stated because they change what may be concluded:**

1. **Control-exemplar paragraph boundaries are unreliable.** The Storygram reprints merge
   paragraphs into display blocks: median block length 130 words against Ed Yong's genuine 80.
   Only `CX-02` and `CX-12` have trustworthy boundaries. **All control paragraph metrics below
   are therefore n=2 and should not be used for comparison.** Control *sentence* metrics are
   unaffected and are n=12.
2. **Control word counts are approximate.** The story span is bounded by the first and last
   annotated paragraph, so a small amount of head or tail may be missing (`CX-01`: 4,919 words
   extracted against a New Yorker original of roughly 8,000, so that text is materially
   truncated and its aggregate contribution is diluted accordingly).
3. **Site boilerplate was removed after a first pass produced wrong numbers.** Scientias'
   standing lines (`Leestip:`, `Uitgelezen? Luister…`) inflated question density from 0.91 to
   3.63 per 1,000 words and created 38 spurious "short paragraphs". Bregman's subscribe
   footers and Guardian book-plugs were removed likewise. The corrected figures are the ones
   reported.
4. **Guardian standfirsts were moved out of the body** for seven texts. They were being read
   as opening paragraphs, which misclassified the openings.
5. **Sentence splitting is regex-based**, with abbreviation and decimal protection. Spot-checked
   against 40 sentences by hand; errors were in initials and ellipses and were rare. Treat
   sentence counts as ±2%.
6. **Clause counting is a proxy**, not a parse: subordinator hits plus semicolons plus em-dashes
   plus one. It over-counts English *that* and Dutch *dat/die/als*, which inflates clause
   counts for both languages roughly equally. **It is valid for comparison between these
   samples and invalid as an absolute measure.**
7. **The Dutch and English measures are not directly comparable** for passive voice,
   nominalisation and modality, because the detection patterns differ by language. Only
   sentence length, paragraph shape, comma load and question/number counts compare cleanly
   across languages.

## 2. Sentence metrics

n = 15 Bregman, 12 control exemplars, 25 Scientias texts.

| measure | Bregman | control | Scientias |
|---|---|---|---|
| mean sentence length (words) | 15.31 (12.78–18.24) | 19.66 (16.50–23.17) | 15.80 (12.24–22.84) |
| median sentence length | 13.90 | 18.21 | 15.22 |
| 25th percentile | 8.96 | 12.08 | 10.69 |
| 75th percentile | 19.84 | 25.57 | 19.96 |
| 90th percentile | 26.18 | 33.23 | 23.92 |
| standard deviation | 8.29 | 10.15 | 6.70 |
| share ≤10 words | 0.34 | 0.20 | 0.26 |
| share ≥30 words | 0.06 | 0.17 | 0.05 |

**Interpretation.** Bregman and Scientias share a mean; the control group runs about four
words longer per sentence and carries nearly three times the long-sentence tail. Bregman
differs from Scientias not in mean but in **spread** (SD 8.29 vs 6.70) and in short-sentence
share (0.34 vs 0.26). Two different accessibility strategies with the same average.

**Limitation.** Mean sentence length is a notoriously poor proxy for readability on its own,
and none of these samples was chosen randomly. What the table supports is "these three bodies
of prose have different sentence habits", not "shorter sentences cause accessibility".

## 3. Compression metrics

The owner's stated failure mode — one sentence carrying fact + context + interpretation +
atmosphere + conclusion — has no direct measure. These are the closest available proxies.

| measure | Bregman | control | Scientias |
|---|---|---|---|
| clause boundaries per sentence | 1.58 | 1.90 | 1.77 |
| commas per sentence | 0.88 | 1.35 | 0.54 |
| share of sentences with ≥4 clause boundaries | 0.04 | 0.08 | 0.05 |
| share of single-clause sentences | 0.60 | 0.44 | 0.48 |
| share ≤12 words **and** single-clause | 0.36 | 0.22 | 0.25 |

**Interpretation.** Bregman is the least syntactically stacked of the three by every measure.
The control exemplars carry twice his rate of four-plus-clause sentences and 53% more commas.
Scientias sits between them on clauses and below both on commas.

**A candidate operational target** for "difficult ideas, very easy reading", derived from the
Bregman band rather than from theory: single-clause share 0.55–0.65; ≥4-clause share below
0.05; commas per sentence below 1.0; short-and-simple share above 0.30; sentence-length IQR at
least 8 words. This is a **diagnostic to report**, not a gate to enforce — see the gap analysis.

## 4. Paragraph metrics

n = 15 Bregman, 25 Scientias, **2 control** (see caveat 1).

| measure | Bregman | control (n=2) | Scientias |
|---|---|---|---|
| mean words per paragraph | 58.15 (32.5–100.2) | 67.82 | 54.03 (39.5–74.9) |
| mean sentences per paragraph | 3.85 | 3.70 | 3.46 |
| one-sentence-paragraph share | 0.11 (0.00–0.37) | 0.15 | 0.03 (0.00–0.15) |
| share of paragraphs ≤15 words | 0.08 (0.00–0.33) | 0.03 | **0.00** |
| share of paragraphs ≥100 words | 0.11 | 0.15 | 0.03 |
| paragraph-length standard deviation | **25.07** | 28.15 | **15.91** |

**Interpretation.** The headline result is the spread. Bregman's paragraph-length SD is 58%
higher than Scientias'. He runs 100-word paragraphs and 4-word paragraphs in the same article;
Scientias runs a near-uniform 54. The "pivot paragraph" (≤15 words, standalone) exists in
Bregman at 8% of paragraphs and does not exist in Scientias at all.

**Limitation.** The control column is n=2 and is printed only to show it was not omitted. It
supports nothing.

## 5. Density metrics (per 1,000 body words)

| measure | Bregman | control | Scientias | comparable across languages? |
|---|---|---|---|---|
| questions | **5.06** | 0.87 | 0.91 | yes |
| direct address (*you/we/us* · *je/we/ons*) | **20.88** | 8.02 | 9.89 | roughly |
| numbers | 11.76 | 11.90 | 9.94 | yes |
| proper nouns | 96.59 | 97.40 | 74.99 | yes |
| passive constructions | 4.91 | 6.71 | 5.84 | **no** — different patterns |
| nominalisations | 20.31 | 20.19 | 11.45 | **no** — different suffix sets |
| modal verbs | 10.26 | 7.66 | 9.85 | **no** |
| quote-bearing paragraph share | 0.25 | 0.48 | 0.23 | yes |

**The four findings that survive the language caveat:**

1. **Bregman asks 5.8× more questions** than the control group and 5.6× more than Scientias.
   This is the largest single separation in the dataset and it is author-level, not
   accessibility-level. (First pass reported Scientias at 3.63 and therefore concluded
   questions were a general accessibility trait. That was boilerplate. Corrected.)
2. **Bregman uses 2.6× the direct address** of the control group.
3. **Bregman uses about half the quotes** of the control group; Scientias likewise.
4. **Number density is essentially identical** between Bregman and the control group (11.8 vs
   11.9). Whatever Bregman does with numbers, he does not use fewer of them. Proper-noun
   density is identical too (96.6 vs 97.4) — "name overload" does not distinguish these
   samples at all, which is worth noting given that `NAME_OVERLOAD` is a declared cut reason
   in PR #62.

Within English, one further comparison holds: **Bregman's nominalisation density matches the
control group's** (20.3 vs 20.2) while his clause load and sentence length are markedly lower.
That pairing is the quantitative form of hypothesis H2 and is the profile's central result.

## 6. Bregman by form

| form | n | mean sentence | questions/1k | single-clause share |
|---|---|---|---|---|
| ARGUMENTATIVE_ESSAY | 4 | 15.1 | 3.7 | 0.571 |
| EXPLANATORY_FEATURE | 1 | 16.3 | 9.1 | 0.542 |
| NARRATIVE_HISTORY | 2 | 15.1 | 3.2 | 0.584 |
| POLEMIC | 3 | 14.8 | 3.4 | 0.614 |
| REPORTED_ESSAY | 2 | 14.2 | 5.1 | 0.599 |
| SHORT_FEATURE | 3 | 16.7 | 8.4 | 0.639 |

Sentence economy is form-invariant across a 2.5-word band. Question density varies almost
threefold. **Cell sizes are 1–4 texts; treat the ordering as suggestive only.**

## 7. Professional annotation topics

421 annotations across 12 Storygrams, coded by keyword. **45% fall outside every
macro-structural category** — they are about one verb, one detail, one word. The coding is
crude and the residual is large, so this table indicates emphasis, not measurement.

| topic | annotations | share |
|---|---|---|
| (unclassified — lexical/detail-level praise) | 190 | 45% |
| people, quotes and sources | 72 | 17% |
| numbers | 28 | 7% |
| analogy / imagery / relatability | 28 | 7% |
| openings | 27 | 6% |
| scene | 26 | 6% |
| background timing | 22 | 5% |
| exposition / jargon | 19 | 5% |
| omission and restraint | 17 | 4% |
| endings | 17 | 4% |
| transitions | 14 | 3% |
| pacing | 12 | 3% |
| reader questions | 12 | 3% |
| **explicit critique of the exemplar** | **12** | **3%** |
| nut graf | 9 | 2% |

The 12 critiques are worth their own note, because they are the only places where a
professional says a published exemplar got something *wrong*: two are "this ends one paragraph
too late", three are "this should have come higher up", two are "this transition is jarring",
one is "watch negative constructions", one is "this paragraph confused me", one is "I wanted
the author to test the claim herself", one is "this reads unfinished", one is "this graf feels
buried". **Not one is "this was too explicit about its idea" and not one is "this stated its
thesis too plainly."**

## 8. What no metric here measures

Named so the metrics are not over-read.

- **Whether a reader recovers the idea.** No proxy for this exists in the dataset.
- **Semantic compression directly.** Clause and comma counts do not distinguish a sentence
  carrying three facts from a sentence carrying one fact and two subordinate qualifications.
- **Abstraction level automatically.** The LOW/MID/HIGH coding in the reverse outlines is
  manual, applied by one coder, unblinded, with no second rater. Treat it as a reading, not a
  measurement.
- **Reader-question quality.** The pivot-paragraph count is mechanical; whether each pivot
  lands at a real reader question is a judgement made by hand in the reverse outlines.
- **Anything about Crip Minds output.** No generated text was measured in this campaign.

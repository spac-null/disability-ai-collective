# Article-quality evidence pass — 2026-08-14

**Isolated worktree.** Branch `article-quality-next-2026-08-14`, created from
`2ad2300` (verified `main` HEAD before starting). No production code added.
No CJ/B2/RL touched. No push, merge, or deploy from this worktree.

---

## E — LENGTH BASELINE

**Recoverable from the 140-article corpus:** raw word count only (474–1680,
median 890, IQR 757–1051). **Not recoverable at all:** `article_type` and
`target_words` — neither is persisted in frontmatter, and the
`shadow_length_adherence` DB column added tonight (commit `d9f9827`) has zero
historical rows, since no historical article was ever reviewed by that code.

**Decisive finding:** the `_LENGTHS` pool itself has changed twice over the
corpus's own history —
- `2026-03-15` (`1716eca`): `[(800,.20),(1200,.45),(1600,.25),(2000,.10)]`
- an intermediate revision (no sub-500 or 2800 bucket)
- `2026-08-04` (`a45951c`, 10 days before this pass): today's
  `[(450,.08),(700,.15),(950,.27),(1200,.24),(1600,.16),(2800,.10)]`

Only **3 of 140 articles** (all dated 2026-08-07) were generated under the
CURRENT pool. Zero articles anywhere in the corpus reach the 2800-word
bucket — expected, since it didn't exist for 137/140 of the corpus's
lifetime and even the 3 current-policy articles are too few a sample to
expect a 10%-weight draw.

**Threshold conclusion: NOT CALIBRATABLE FROM EXISTING METADATA.** No
threshold changed — there is nothing to calibrate against yet. Revisit once
the current policy has run long enough to accumulate real
`shadow_length_adherence` rows (weeks, not days).

---

## L2 — TESTIMONY BASELINE

**Deterministic first pass (140 articles, automated, noisy):** ~9% DIRECT,
~15% INDIRECT, ~76% NONE — the automated named-entity proxy has real false
positives (matches institutions like "Joint Standing", "Roman Forum").

**Manual validation sample (15 articles, stratified across March–August,
all 4 personas):**
- **DIRECT** (clean attributed quote, identifiable source): 3/15 — Liz Carr,
  Doug Paulley's solicitor, Bruce Young (NDIS advocate) — all pulled from
  the primary source or a secondary journalistic citation, never a live
  companion-source retrieval (none has ever existed in production).
- **INDIRECT** (reported/paraphrased, real, specific): 4/15 — Reaktor
  Education facilitators, an epilepsy-affected midwife (Priya piece), a
  Deaf friend's museum story, Wally Barros's cancelled commissions.
- **NONE** beyond the author-persona's own voice, or institutional/expert
  commentary with no lived-experience content: 8/15 — including two
  articles **about a specific named or pseudonymous wronged individual
  (Shabin Shaji, "Susan") that carry ZERO quotes from that person at all**,
  despite the piece existing specifically because of their case.

**Primary vs. companion provenance — answerable with high confidence from
architecture alone, no re-fetching needed:** discovery.py has only ever
fetched one source per run; no companion-source retrieval mechanism existed
in production before tonight's OFF-by-default L2 scaffold. **100% of any
testimony present in the 140-article corpus came from either the single
primary source or the model's own general knowledge of real public figures
(Wally Barros, Georgina Kleege, Sunaura Taylor are all real, verifiable
people, but nothing indicates they came from THIS run's fetched article) —
zero came from a companion source.**

**Actual gap size: real but moderate, and partly mis-attributed to L2.**
The sharpest gap (Shaji, "Susan" — zero testimony from the actual subject of
the piece) looks like an **L1 hoisting problem** (does the primary source
already contain their quote, never carried into the draft?) as much as an
L2 companion-search problem — not resolved here, flagged for whoever designs
the live-search step. Building live L2 search would not fix this specific
pattern.

---

## D — CORRECTION-INTEGRITY AUDIT

**Doctrine reconstructed from `generate.py`/`llm.py`:** Fable's editorial
brief plans a `correction_moment` explicitly; `_get_cross_reference` lets one
persona's draft directly disagree with another persona's recent piece
("Here is where we diverge..."); the writer prompt's rule 7/8 forbid forced
resolution and require the strongest version of an opposing view before any
concession.

**Candidate search:** deterministic marker sweep ("I was wrong", "turns out",
"the concession I owe", "not X but Y", etc.) across all 140 articles found
**52 candidates (37%)**. Read the 15 strongest/most-representative directly
(paragraph-level evidence, not chain-of-thought):

| Classification | Count | Examples |
|---|---|---|
| GOOD DEEPENING | 9/15 (60%) | Twenty Minutes (explicit "I was wrong to call it access"), Priya (holds an unresolved counter-testimony rather than smoothing it over), Witness You Didn't Ask, Swan Care, Map That Stops, Ledger Sees You, Floor Plan They Can't Read, Stockpile, Sound of Mud |
| NO REAL CORRECTION MOMENT | 6/15 (40%) | Architects (Wrong Sense), Determined to Disappear, Eyebrow, Intelligence of Not Speaking (a rebuttal essay, not self-correction), Immunotherapy (heuristic false positive — matched keywords, no real reversal) |
| ERASES FIRST HALF | **0/15** | none found |
| WITHDRAWN EXAMPLE RESURRECTED | **0/15** | none found |

**Notable pattern:** every one of the 5 cross-persona-disagreement pieces in
the sample (`_get_cross_reference` in use) produced a GOOD DEEPENING
correction — the mechanism looks like a reliable generator of quality
correction structure, worth protecting rather than touching.

**Materiality decision: D1 — RARE / CURRENT PROMPT ADEQUATE.** Zero
catastrophic failures found in a sample deliberately biased toward the
highest-scoring correction-marker candidates (i.e., the search that was
most likely to surface a bad case found none). No shadow check justified.

---

## B — AUTHOR-PRESENCE / OPENING AUDIT

Same 15-article stratified sample (5 months, 4 personas, short/long).

| Pattern | Count | Notes |
|---|---|---|
| FUSED (embodied/perceptual signal within 1–2 paragraphs) | 8/15 (53%) | Map That Stops, Eyebrow, Twenty Minutes, Stockpile, Sound of Mud, Witness You Didn't Ask, Ledger (analytical-voice variant), Architects (borderline — see below) |
| GENERIC/DELAYED (signal doesn't land until 3+ paragraphs, sometimes ~25–30% in) | 4/15 | Determined to Disappear, Intelligence of Not Speaking, Immunotherapy, Priya (a distinct sub-case: opening is embodied but about a THIRD PARTY, not the narrating author) |
| NO PERCEPTUAL PRESENCE AT ALL (pure analyst voice, no embodied signal anywhere in the piece) | 3/15 | Floor Plan They Can't Read, Jane Green/21-years, Swan Care |

**Concrete, low-effort finding:** a near-verbatim template sentence — *"But I
design [X]. And let me tell you what they're missing"* — appears in **4
articles**, all clustered in one week (2026-03-08 to 03-16), 2 of them
differing only by the swapped noun ("buildings with my ears" /
"interfaces with my body"). None of the later-dated sampled articles show
this phrase — likely already superseded by prompt evolution, but real,
mechanical, and cheaply detectable.

**Author-presence "explicit/clunky" pattern:** Architects (Wrong Sense) uses
a dedicated `## The Night I Learned Architecture` backstory section to
deliver the disability reveal — a formulaic device, not fully fused into
the ongoing observation, though not egregious.

---

## C — CENTRAL-QUESTION TIMING AUDIT

Same sample, judged on argumentative function, not keyword search.

| Pattern | Count |
|---|---|
| EARLY AND NATURAL | 7/15 (47%) |
| EARLY BUT MECHANICAL (the same template phrase as B's finding) | 2/15 |
| DELAYED BUT JUSTIFIED (deliberate accumulation-toward-a-point structure) | 6/15 (40%) |
| TOO LATE / reader doesn't know why they're reading | **0/15** |

Zero clear TOO-LATE failures. The delayed cases read as legitimate,
deliberate essay structure (matches this publication's own Bregman-style
"no thesis announcement" house rule) rather than a failure to orient the
reader.

---

## B/C RELATIONSHIP

Tested directly rather than assumed. **They are correlated but separable,
not the same problem:**
- *Author-presence early, thesis timing later* (fused/early opening, delayed
  thesis): Twenty Minutes, Sound of Mud — deliberate, matches doctrine.
- *Thesis early, author-presence absent or very late* — the more important
  case: **Determined to Disappear** and **Swan Care** both land their actual
  argument by paragraph 3, while carrying essentially zero embodied
  perceptual signal anywhere in the piece. This is direct evidence a fix
  aimed only at thesis-timing would leave the author-presence gap
  completely untouched, and vice versa.
- *Both fail together*: Intelligence of Not Speaking, Immunotherapy.
- *Both succeed together*: Eyebrow, Ledger, Stockpile.

**Conclusion: two real, separable dimensions. Do not collapse into one rule.**

---

## RISK MAP (current evidence, not the old A–M ordering)

| Concern | Frequency | Severity | Current protection | Observability | Likely next action |
|---|---|---|---|---|---|
| **B — author-presence delayed/absent** | ~47% of sample shows generic/delayed/absent embodied opening | Medium — reduces the doctrine's own differentiator, doesn't corrupt facts | None (no check exists) | None | Design a shadow (see below) |
| **Mechanical opening template phrase** | 4/140 confirmed, clustered in one early week | Low-medium, but concrete and cheap to catch | None | None | Cheapest possible deterministic shadow — fold into the B/C design below |
| **C — thesis timing** | 0% clear failures; delays are mostly justified | Low — matches house style | Editorial doctrine (implicit) | None (no metric) | Low priority; ride along with B's shadow for shared infrastructure only |
| **L2 — testimony gap** | ~53% of sample (NONE+borderline INDIRECT) lacks real lived-experience testimony; sharpest cases (Shaji, "Susan") may be an L1 problem, not L2 | Medium — a real doctrinal gap, but live-search implementation is the expensive, unresolved part | OFF-by-default scaffold shipped tonight, untested live | Shadow-ready, zero live data yet | Do NOT build live search yet; too many open design questions (cost, ranking, trust) from last night's own design doc |
| **E — length adherence** | Unknown — not calibratable, only 3 articles under current policy | Unknown | Shadow shipped tonight, unconditional | Real, but zero usable historical data | Wait for accumulation; nothing to calibrate |
| **D — correction integrity** | 0/15 catastrophic failures on a heuristic-biased sample | Low | Doctrine + cross-persona-disagreement mechanism, both apparently working | Good qualitative evidence, no shadow | No action needed |
| **G — repetition (carried over from last night)** | 1/140 real hit (already repaired), 60% of remaining candidates are figure-caption noise | Low, now that the one real case is fixed | Shadow shipped, working as intended | Real | No action needed this pass |
| **J — STOP-risk (carried over)** | No data yet — shipped tonight | Unknown | Shadow shipped | Zero real runs yet | Wait for accumulation |

---

## NEXT ENGINEERING ITEM

**Chosen: D — B/C opening-quality shadow.**

Rationale: it's the only concern with (a) real, material frequency in this
pass's own evidence (~47% generic/delayed openings), (b) a concrete, cheap,
already-confirmed deterministic sub-signal (the template-phrase repeat), and
(c) a clean way to reuse existing infrastructure (the same
`_engagement_read` call J already extended tonight) rather than adding a new
model call. E and L2 are both real but have too little accumulated data or
too many unresolved design questions to act on yet; D (correction) shows no
failures to fix.

Ranking: **D primary**, **E (let observers accumulate) close second** for
the length/testimony baselines specifically — those two genuinely need more
production time, not more code, before any further action.

### Design only — NOT implemented this pass

**Component 1 — deterministic cross-article opening-template detector**
(zero model cost, same spirit as G's within-article Jaccard check but
across recently published articles):
- Input: this article's normalized opening (first ~400 chars) + a rolling
  window of the last N (e.g. 30) published articles' openings.
- Method: n-gram (6–8 word shingle) overlap, stopword-aware, same
  discipline as G's content-word Jaccard.
- Output: `{"template_match": bool, "matched_article": slug|None,
  "shared_phrase": str|None}`.
- Authority: shadow only, never blocks.
- Failure mode risk: false positive on short common phrases — mitigate with
  a minimum shingle length, calibrated against the 4 known positive
  examples (Architects/Frequency/Door/Map-That-Stops) plus a large negative
  sample of unrelated opening pairs.
- Test corpus: the 4 confirmed matches (must fire) + ~20 random unrelated
  opening pairs (must not fire).
- Promotion evidence: same 2-week-minimum, no-promotion-before discipline
  as every other shadow check shipped this week.

**Component 2 — LLM-judged opening-fusion / thesis-timing verdict**
(reuses the existing `_engagement_read` call, same call J's STOP_RISK field
was added to tonight — zero new model cost):
- Input: same call, add two more requested fields to the existing prompt:
  `OPENING_FUSION: FUSED | GENERIC | ABSENT | UNCLEAR` and
  `THESIS_TIMING: EARLY_NATURAL | EARLY_MECHANICAL | DELAYED_JUSTIFIED |
  TOO_LATE`, with the same kind of explicit calibration language STOP_RISK
  got (score the argumentative function, not a keyword; a deliberate
  Bregman-style delayed thesis is not a failure).
- Output: parsed via a deterministic regex extractor, same pattern as
  `_extract_stop_risk_shadow`.
- Authority: shadow only.
- Failure mode risk: subjective, no calibration data — this is why it stays
  shadow, same discipline as `_engagement_read` itself and `plan_follow_read`.
- Test corpus for initial sanity-check: this session's own 15-article manual
  classification (recorded above) is a ready-made seed set to compare the
  LLM-judged verdicts against before trusting the signal at all.
- Promotion evidence: 2-week minimum PLUS a manual spot-check against a
  human sample, matching `plan_follow_read`'s own "~20 samples then check
  against a human" convention already established in this codebase.

No production code touched. No runtime behavior changed anywhere in this
pass.

---

## DEPLOYMENT INTERLOCK

Confirmed via read-only inspection of the canonical `main` worktree
(`~/code/disability-collective-ai`) — no fetch/pull/merge/push issued from
this task:
- `main`'s HEAD moved from `2ad2300` (this task's starting point) to
  `64d1658` during this pass — the privileged deployment session evidently
  rebased the 11-commit stack onto fresh origin state (new SHAs, same
  messages/order) and pushed, since `origin/main` now also reads `64d1658`.
  Two additional real production commits appear underneath (new articles
  published 2026-08-13/14, one publish/archive housekeeping commit) —
  normal daily automation continuing independently, not related to this
  task.
- This worktree (`~/code/disability-collective-ai-article-quality`,
  branch `article-quality-next-2026-08-14`) was never switched, rebased, or
  merged, and remains pinned to the original `2ad2300` throughout. It is
  intentionally now behind `main`/`origin/main` — expected and correct per
  this task's own instructions, not treated as a problem to fix.
- No production infrastructure was queried or touched from this worktree at
  any point.

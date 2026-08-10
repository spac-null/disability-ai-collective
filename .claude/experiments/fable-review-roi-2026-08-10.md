# Experiment record: Fable review-seat ROI probe, Phase 1.5B (2026-08-10)

Archived from `.claude/current-work.md` during the 2026-08-10 checkpoint
cleanup. This is historical provenance — full methodology, run provenance,
blind-judge results, and the safety-attribution audit preserved verbatim,
not condensed. For the current operational status of this experiment (paused,
not concluded; model-seat decision deferred to after Phase 1.6), see
`current-work.md`'s `PAUSED EXPERIMENTS` section. For the design of the
grounding fix this experiment's finding D led to, see
`../phase-1.6-source-grounding.md`.

---

## MODEL-SEAT ROI EXPERIMENT (Phase 1.5B) — PIVOTED, harness built, then run
Originally recorded 2026-08-10 as "Fable review + Fable rewrite vs Fable
review + Opus rewrite" (see git history of this section for the original
A/B/C framing). **Pivoted the same day, before spending anything**, after
three cheap checks — the production-outage finding surfaced by the same
investigation is recorded in `current-work.md`'s infrastructure backlog:

1. `probe_out/*.md` files are FINAL pipeline output (post-review/rewrite/
   gate) — `_run_one_sample()` only reads `drafts_dir` AFTER
   `_run_production_automation_locked()` returns. They are NOT raw
   pre-review drafts; reusing them as fresh review input would have been a
   biased test (already-polished text → mostly pass).
2. `_fable_polish_rewrite` already passes `prefer_opus=True` (commit
   `26f5e77`, landed 12:19 that day, for a documented truncation-risk reason
   unrelated to this experiment). Across every real+probe sample logged in
   `automation.log` since, Opus won the rewrite on the FIRST attempt 100%
   of the time (0/36 Fable fallback). The rewrite seat is not currently a
   meaningful cost center to A/B test — production already made this call,
   just not for a quality-ROI reason.
3. Fable's REVIEW call fires on every real production run and has NEVER
   once returned `publish_as_is` (0/39 logged, real or probe, spanning
   2026-08-09 through 2026-08-10). This is the actual recurring, load-bearing,
   expensive seat — and the 0/39 pattern is itself a hypothesis worth
   testing (structural over-editing bias, vs. drafts genuinely always
   needing work), not assumed proof of either.

**Corrected experiment**: does Fable's editorial JUDGMENT (not its prose
execution) earn its price, or is Opus just as good at deciding what's
wrong with a draft? Design (locked):
```
ONE raw Opus draft, captured live (never reused from probe_out)
                |
         /              \
    Fable review      Opus review
 (byte-identical prompt/schema, forced model, no fallback chain)
         |                  |
    verdict+notes      verdict+notes
         |                  |
 if revise: Opus executes   if revise: Opus executes
 (same executor template,   (same executor template,
  authorship-agnostic)       authorship-agnostic)
 else: final = raw          else: final = raw
```
`publish_as_is` is a LEGITIMATE, first-class outcome for either branch —
NOT a skip condition (the decision not to intervene is part of the seat
being tested). No downstream rewrite/gate runs after the branch point —
the harness aborts the real pipeline immediately after capturing the raw
draft (a sentinel exception from the review-capture stub), so no extra
real spend happens beyond the draft-generation call itself.

**8 cases planned**: 2 raw drafts each for Siri/sauna, Zen/hiring_tool,
Maya/curb_cuts, Pixel/museum_labels — the 4 already-frozen topics/briefs,
no new topic work needed.

**Harness built**: `automation/fable_review_roi_probe.py`. `--preflight`
passes locally (frozen briefs readable, zero API calls). Per case, persists
`raw_draft.md`, `review_fable.json`, `review_opus.json`,
`final_from_fable_review.md`, `final_from_opus_review.md`, `provenance.json`
(models, prompt hash, draft hash, review-response hashes, token
usage/latency/errors for every call — `cost_usd` deliberately left `null`,
no verified per-token pricing for the Fable alias, not fabricated). Reuses
`snapshot_test.py`'s `_isolate_paths`/`_patch_methods` exactly like
`phase_probe.py` — zero production-state mutation by construction. Draft
generation is temperature-pinned at 0.9 (matching every other probe this
session), via the same `_call_openai_compat_api` patch pattern.

**Pre-run corrections (before spending anything), then RUN — 8/8 cases
valid.** Three checks before `--run`, all fixed then verified clean:
1. Parser failure semantics: malformed JSON/API errors/missing-or-invalid
   verdict now return distinct `api_error`/`parse_error`/`invalid_verdict`
   status, never silently collapsed into `publish_as_is` or `revise` (the
   0/39 finding must not be contaminated by parser artifacts). Same parser
   for both models. Downstream execution gated strictly on `status=="ok"`.
2. Explicit sampling settings, both recorded in `provenance.json`:
   `REVIEW_TEMPERATURE=None` (matches production's own unset-default
   convention for the real review seat — deliberate, not accidental,
   applied identically to both forced review calls); `EXECUTOR_TEMPERATURE
   =0.2` (deliberately pinned low so final-output differences trace to
   notes content, not independent Opus sampling noise). Also fixed a real
   `max_tokens` asymmetry (1600 vs 1200) to match production's real 3200
   review budget for both models.
3. Mocked offline branch test (`--test-mock`, zero network calls): 21/21
   checks pass — `publish_as_is` byte-identical final output, executor
   called exactly once per case, all 6 artifacts present, and (the
   parser-semantics scenario) simulated API/parse failures produce
   distinct non-executing statuses rather than silent defaults.

**Run completed, commit `b99d379`, mechanical acceptance passed** — keep
this distinction explicit: the 8 cases were GENERATED at `b99d379`. Commit
`889942b` (and later checkpoint commits) only add provenance improvements
and commit the already-completed artifacts — they did not generate or
touch the experimental data. Future docs must not casually say "the 8
cases were generated on 889942b." Trident stayed on `b99d379` the entire
run (verified `git rev-parse HEAD` + `git status --short` before pulling
results — only expected pre-existing untracked leftovers). Exactly 8 cases
(2 per persona × 4 personas), all 6 artifacts present per case,
`review_prompt_hash` confirms byte-identical review prompts sent to both
models per case. Full mutation proof clean (same backup-vs-backup DB method
as every prior check this session — `disability_findings.db`/`engagement.db`
hashes identical to the pre-run backup, persona-state mtimes all predate
the run, `_drafts/`(17)/`assets/`(588) counts unchanged). Run-level
`run_manifest.json` added recording the generating commit (provenance.json
didn't carry it per-case yet — also fixed the harness itself,
`_git_commit_hash()` now threaded into every future run's per-case
provenance).

**Headline result before any blind judging**: all 8 cases `status=="ok"`
for BOTH models, zero execution failures — every case valid for both
comparisons, nothing to exclude. **Fable: revise 8/8. Opus: revise 8/8.**
Both models, independently, request revision on every single case under
these conditions. This is informative against the 0/39 production
`publish_as_is` pattern: Opus showing the identical intervention rate
leans toward "these raw drafts genuinely have real issues most of the
time" rather than "Fable specifically has a bias" — but does NOT rule out
both models sharing one, or Fable's notes being more/less justified than
Opus's even at equal intervention rates. Exactly why the blind
review-quality judging (below) still has to happen before concluding
either way — the revise-rate alone answers nothing about the FINANCIALLY
significant question (does Fable's judgment earn its price).

**Static audit of the shared `_review_prompts()` template, done directly,
no code changed, no rerun** — asked because 8/8 vs 8/8 makes "does the
SEAT itself lean toward intervention" a live question, not just "which
model." Answering the five specific questions:
1. *Is `publish_as_is` described as genuinely acceptable?* Syntactically
   yes (schema explicitly allows empty notes on `publish_as_is`) — but
   textually minimized: "or confirm it is ready" is a 4-word clause
   tacked onto the primary "Give 2-3 specific, actionable revision notes"
   instruction. The ~800-word body describes 9 checks capable of
   producing a note; zero words describe what a clean pass looks like.
2. *"Find problems" vs "decide if there's a problem"?* Mixed, genuinely.
   The prompt contains 4 explicit ANTI-default-triggering guards ("Do NOT
   ask for a scene as a default," "do not ask the writer to bolt one on,"
   "never ask for one the argument would obviously defeat," "Do NOT ask
   for irresolution as a default") — real counter-bias engineering,
   already present. But the overall frame is still "run through 9 checks
   and flag failures," structurally a hunt, not a from-scratch judgment.
3. *Are examples skewed toward revise?* Yes, clearly — many concrete
   quoted violation examples across the 9 checks; zero examples anywhere
   of a passing/clean piece.
4. *Does producing no notes feel like failing?* The phrase "if several
   checks fail, pick the three that most change the piece" presupposes
   multiple failures as the normal case needing prioritization, not the
   exception.
5. *Does an "identify up to three" framing presuppose issues exist?* Yes
   — "Give 2-3 specific, actionable revision notes" is the lead imperative
   sentence; nothing in the prompt is weighted as heavily toward "if zero
   checks fail, say so confidently."

**Net finding**: a real, plausible mild-to-moderate structural lean
toward intervention exists in the SHARED prompt (9 independent low-
threshold checks = a multiple-comparisons risk; strong example-asymmetry;
the "if several checks fail" presupposition), partially offset by 4
already-present explicit anti-default-triggering guards. Not proof either
model is biased — real material suggesting the SEAT/PROMPT architecture
itself may lean interventionist regardless of which model occupies it.
This reframes what 8/8-vs-8/8 can mean; the three-layer design below is
built to distinguish the live explanations, not assume one.

**Evaluation design (three layers, TWO independent blind judges per
layer — 8 cases is small enough that judge variance could change the
conclusion, and evaluation tokens are cheap relative to the generation
already paid for).**

- **Layer 1 — raw necessity** (must run BEFORE either judge sees any
  review, so the mere existence of two reviews doesn't prime "a revision
  must have been necessary"): show ONLY the raw draft. Record
  `publish_as_is` / `minor_revision` / `substantial_revision`, the single
  most important defect if any, and confidence. This is the independent
  baseline both reviewers get judged against — newly critical given both
  went 8/8 revise.
- **Layer 2 — review quality**: per case, show Review A and Review B
  (notes only, anonymized) — score each independently (problem validity,
  importance, coverage of the real problem, specificity/actionability,
  false-positive pressure) before any comparison. Only after BOTH are
  scored: classify the relationship (same underlying problem / partial
  overlap / different-but-both-valid / Fable-only-valid / Opus-only-valid
  / both weak).
- **Layer 3 — result quality**: per case, show RAW / Version X / Version
  Y (anonymized). Judge EACH version relative to raw (not merely X against
  Y — two editors can both make a piece worse in different ways, which a
  pure winner/loser call would hide): better/same/worse than raw, was the
  important defect actually solved, collateral damage, persona preserved,
  unsupported material introduced, overall preferred final.

**Decision tree, for the 8/8-vs-8/8 result**:
- Opus identifies essentially the same important problems and the
  resulting articles are equivalent → remove Fable from the recurring
  review seat.
- Fable reliably identifies deeper/load-bearing problems and those notes
  lead to materially better articles → Fable earns the review seat.
- Both models frequently request revisions the raw-only judges call
  unnecessary → the problem is likely the review PROMPT/SEAT, not which
  model occupies it — redesign the intervention threshold before deciding
  model ROI.
- Both models correctly judge all 8 raw drafts as genuinely needing
  revision (Layer 1 agrees with both) → 8/8 is not evidence of
  intervention bias at all — it means the raw writer stage is
  consistently producing drafts that benefit from editorial intervention,
  a separate, real finding for the larger article-quality repair plan.

## RESULTS — 3-layer blind evaluation (2 judges/layer) + safety audit, DONE

**Layer 1 — raw necessity (2 independent judges, 8 raw drafts, no reviews
shown).** Judges disagreed substantially: Judge A called 5/8 minor_revision,
2/8 publish_as_is, 1/8 substantial; Judge B called 5/8 publish_as_is, 2/8
minor, 1/8 substantial. Combined across both (16 judgments): **7/16
publish_as_is, 7/16 minor_revision, only 2/16 substantial_revision.**
Against this baseline, **both Fable and Opus said "revise" with 3 notes on
all 8/8 cases** — a real mismatch. Independent human-analog readers see
these drafts as mostly fine-to-lightly-flawed; the shared review PROMPT
(both models) never once found nothing worth flagging. Consistent with the
static prompt audit above: this points at the SEAT/PROMPT architecture
leaning interventionist, not renewed evidence that either model specifically
over-edits.

**Layer 2 — review quality (2 independent judges, blind, one review at a
time before comparing).** Both models scored comparably high on the
surface axes across all 8 cases — problem validity and specificity mostly
4-5/5 for both, false-positive pressure mostly 0-1/3 for both. The
differentiator was COVERAGE, not validity: in most cases (6/8 per Judge A,
7/8 per Judge B) the relationship was **"partial overlap"** — each
reviewer catches a real, valid problem the other misses entirely (e.g.
case-04: Fable's note treats Antwi's paraphrase as a protectable "her own
line" — a factual misread — while Opus's note correctly identifies it as
unquoted ventriloquism; case-01: Fable flags the lithium coda as a dropped-
and-resumed thread needing a fix, Opus's note explicitly says to PROTECT
that same coda as "the ending this piece earned" — a direct disagreement
on the same sentence). Only 2-3/8 cases showed both reviewers converging on
"the same underlying problem." **Neither model is redundant with the
other** on this evidence — each surfaces real defects the other doesn't.

**Layer 3 — result quality (2 independent judges, blind RAW/X/Y).**
**Methodological flaw, disclosed not hidden**: the anonymization script drew
`rev_order` and `res_order` from the same seeded random stream per case,
and by unlucky coincidence `res_order` came out identical (X=Fable-guided,
Y=Opus-guided) in ALL 8 cases — `review_quality`'s A/B varied correctly (6
fable-first, 2 opus-first) but `result_quality`'s X/Y did not. The judges
were never told this and scored genuinely blind per case; the flaw only
means "X preferred N/8" cannot claim robustness against a labeling
artifact the way true per-case randomization would. Aggregate preference,
with that caveat: Judge A preferred Opus-guided in 7/8 (tie leaning Fable
in 1); Judge B preferred Opus-guided in 4/8, Fable-guided in 3/8, tie in
1/8 — real disagreement between judges, driven mostly by each weighing
collateral damage vs. fabrication risk differently case-by-case (Opus's
edits are consistently described as "more conservative" but sometimes cut
a persona-defining passage, e.g. case-05's confessional "smiling" paragraph
in one judge's read).

**Layer 4 (added mid-analysis, not pre-planned) — causal safety audit of
"unsupported additions."** The result-quality judges both independently
flagged a recurring pattern: several Fable-guided finals convert raw's
paraphrased/reported speech into fabricated direct quotations attributed
to real-sounding named individuals. Before trusting "fabricated in N/8" as
a permanent finding, ran a full causal attribution audit per case:
1. Confirmed **`_execution_prompts()` receives only `article_body` +
   `editorial_notes` + `agent_name` — no source package at all** (verified
   by reading the code, not inferred). This is the same template real
   production's `_opus_targeted_revision` already uses — a pipeline-wide
   architecture fact, not a probe-only artifact.
2. Confirmed **`_review_prompts()`/real production's `_fable_editorial_review`
   ALSO never receives the source package** — only `brief_angle` (a short
   editorial question), never the frozen `source_text`. Neither reviewer
   NOR executor, at any stage after the initial draft-writer call, can
   check a claim against the real source. This is the root architectural
   vulnerability, not a defect unique to either model.
3. Scanned all 16 finals (quote-span diff + numeric/date diff) for material
   not present in raw — caught exactly 5 instances, no more, no fewer than
   what the blind judges' instinct suggested (one apparent 6th hit,
   case-05's "as part of a future phase," was a false positive — that
   phrase is genuinely source-grounded and was already in raw verbatim).
4. For each of the 5, checked THREE things independently: (a) is the new
   material in the frozen `source_text` (SOURCE-SUPPORTED / not), (b) did
   the executor have any way to access that source (EXECUTOR-GROUNDED /
   not), (c) did the review note explicitly request this, vaguely gesture
   at it, or never mention it (classification A/B/C from the causal
   framework — A = reviewer explicitly demanded unsupported material, B =
   vague instruction/executor hallucinated, C = executor invented
   unrelated to any note).

**Full table — renamed from "classification" to REVISION-INDUCED SAFETY,
because "classification" conflated two different failures** (pre-existing
writer-stage fabrication vs. new fabrication added during revision; a
branch that merely PRESERVES an existing fabrication is not thereby safe):
| Case | Branch | Pre-existing raw fabrication? | New revision-induced fabrication? | Reviewer explicitly triggered it? |
|---|---|---|---|---|
| 00 | Fable-guided | YES (swimmer, invented at draft stage) | YES (converts her paraphrase into a fake verbatim quote) | YES: "get her real words inside actual quotation marks" |
| 00 | Opus-guided | YES (same pre-existing fabrication, unchanged) | NO | not requested |
| 01 | Fable-guided | YES (same swimmer) | YES (same conversion) | YES: "put them in quotes... hers should stay the sharpest line" |
| 01 | Opus-guided | YES (unchanged) | NO | not requested |
| 02 | Fable-guided | YES (invented "recruiter" + her written HR request) | YES (fake verbatim quote from the invented filing) | YES: "get her actual words... even one sentence from that HR filing" |
| 02 | Opus-guided | YES (unchanged) | YES (different fake verbatim quote) | YES — **Opus's own note**: "you can quote from her written request to HR" |
| 04 | Fable-guided | YES (Deborah Antwi, invented at draft stage) | YES (converts paraphrase into a fake verbatim quote) | YES: "pull her real words from the record and put them in quotation marks" |
| 04 | Opus-guided | YES (unchanged) | NO | not requested |
| 05 | both branches | YES, and WORSE — **the raw draft itself already fabricates a verbatim quote**: `Her exact words in the minutes: "I would rather wheel further than get hit again."` framed as pulled from real meeting minutes | NO new addition either branch (both preserve as-is) | — |
| 03 | both branches | YES (same invented "recruiter"/HR-filing narrative as case-02, though case-03's raw ALSO correctly quotes the source's real HR-director line verbatim — a mix of one supported quote and one unsupported invented thread) | NO new addition either branch | — |
| 06,07 | both branches | YES — **a different, more serious kind**: both raw drafts attribute a specific invented project ("2021, Manchester, replaced public captions with 'the sound of anticipation'") to **Christine Sun Kim, a real, named, living public artist** — not in `source_text`, not confirmable from Pixel Nova's own persona canon either. Neither reviewer (Fable or Opus) flagged this in either case — both focused entirely on craft issues (aphorism density, an unanchored-but-actually-source-real statistic) | NO new addition either branch | — |

**This means the review-seat A/B comparison itself still holds** — both
branches in every case share the identical raw draft, so "did revision make
it worse" is still a valid causal question — but the "safe" label in the
original table was too generous. Case-04's Opus-guided branch is
NARROWLY safe (introduced no NEW fabrication) while NOT factually safe
(it ships the pre-existing Deborah-Antwi fabrication unchanged, same as
Fable-guided). Every "safe" cell above should be read as "did not make an
already-fabricated draft worse," never as "this article is accurate."

**Second, separate audit — the 8 raw drafts against their frozen sources,
BEFORE any review touches them.** First pass (superseded) said "raw writer
fabricates 8/8" — **that attribution was wrong and has been corrected.**
The repeated two-sample symmetry (same invented swimmer in both sauna
drafts, same invented Deborah Antwi in both curb_cuts drafts, etc.) was too
structured for eight independent writer hallucinations — the obvious
shared upstream variable is the frozen Fable-authored editorial brief every
sample in a topic reuses. Checked all four brief JSON files directly.
**Confirmed: all five unsupported claims are already present, verbatim or
near-verbatim, in the brief's own `resisting_example` or `correction_moment`
field — written by FABLE at planning time, not by the writer.**

**Full attribution table** (claim / in source? / in persona canon? / in
frozen brief? / first-appearance stage):
| Claim | In source? | In persona canon? | In frozen brief? | First stage |
|---|---|---|---|---|
| Sauna: "a regular at a Finnish public sauna... comes precisely to lose her bearings" | NO | NO | **YES** — `brief_sauna.json`'s `resisting_example`, verbatim | **FABLE PLANNING BRIEF** |
| Hiring: "an autistic recruiter... formally requested... on the record with HR" | NO (source's real quote belongs to a different, anonymous HR director) | NO | **YES** — `brief_hiring_tool.json`'s `resisting_example`, near-verbatim | **FABLE PLANNING BRIEF** |
| Curb_cuts: "council notified bay users, one had spoken" (framed as pulled from "the March 14 planning session" record) | NO (source only says no disability advocacy group was consulted — doesn't confirm this) | NO | **YES** — `brief_curb_cuts.json`'s `correction_moment`, near-verbatim | **FABLE PLANNING BRIEF** |
| Curb_cuts: "Deborah Antwi" (named individual + testimony) | NO | NO | **YES** — `brief_curb_cuts.json`'s `resisting_example`, verbatim | **FABLE PLANNING BRIEF** |
| Museum: "Christine Sun Kim... spent 2021 replacing Manchester's public captions with 'the sound of anticipation'" | NO | NO (Pixel's canon cites Kim's general work, not this specific project) | **YES** — `brief_museum_labels.json`'s `resisting_example`, verbatim | **FABLE PLANNING BRIEF** |

**All five trace to the identical stage.** Confirmed also: `_fable_editorial_brief`'s
own prompt (llm.py:565-567) receives only `news_title` + `news_summary[:400]`
(a ~400-char TRUNCATED summary) — never the full `source_text` at all, an
even narrower window than the writer gets later. `generate.py:611` then
inserts `resisting_example` into the writer's prompt near-verbatim,
explicitly instructed to "let it arrive without a signpost sentence and
leave it standing" — the writer is not hallucinating independently, it is
faithfully executing a planning-stage instruction to incorporate material
Fable invented from a summary, with no fact-check step anywhere in between.

**Corrected causal chain**:
```
SOURCE (full article, several paragraphs)
   ↓ (only a ~400-char summary passed through)
FABLE PLANNING BRIEF — invents named individual + testimony/quote
   in resisting_example/correction_moment, no source-verification step
   ↓ (inserted near-verbatim into the writer prompt)
WRITER (Opus) — faithfully incorporates the invented material as
   instructed, typically as paraphrase (this is where "8/8 raw drafts
   contain unsupported material" actually originates — not writer
   invention, writer COMPLIANCE with an already-fabricated brief)
   ↓ (for 4/8 cases)
REVIEW (Fable 4x, Opus 1x) — flags the paraphrase as "no real quoted
   voice," explicitly demands "her real words," not knowing the person
   doesn't exist
   ↓ (source-blind, no way to check)
EXECUTOR (Opus) — fabricates a plausible verbatim quote to comply
```

**Corrected wording, exactly**: not "the raw writer stage fabricates
named-individual testimony (8/8)" — instead: **"unsupported named-
individual/testimony material is present by the raw-draft stage in 8/8
cases; traced to its origin, all 8 stem from the frozen Fable-authored
editorial brief's `resisting_example`/`correction_moment` field (confirmed
in all 4 topics), not from independent writer invention."** For Deborah
Antwi (and the sauna swimmer, and the recruiter, and the curb_cuts
notification claim) — all confirmed absent from the source the article
purports to report — "fabricated in this article's evidence chain" is
justified. For Christine Sun Kim specifically — absent from source AND
persona canon, but not independently checked against the real world —
the correct label is **"unsupported by experimental evidence,"** not
"invented"; whether Kim ever did anything resembling this in reality is a
separate, unverified question from whether this pipeline had any basis
for asserting it.

**This reopens the planning seat — not the ROI question (still
untested), a SAFETY question (now confirmed).** The original experiment
design explicitly froze the brief and said "don't infer planning ROI from
this ablation" — that's still true for "is Fable's planning BETTER than
Opus's would be." But this audit answers a different, prior question,
worded exactly (not generalized beyond the 4 audited briefs to a
population-level Fable rate): **in all four frozen planning briefs
audited, Fable introduced at least one source-unsupported factual element
into `resisting_example` or `correction_moment`, which downstream drafts
then inherited.** The safety conclusion stands regardless of how that
phrasing is scoped: the current planning contract is not safe enough to
remain unchanged. The architecture now has FOUR grounding breaks, not
three, and the first one is the origin point for everything downstream:
```
FABLE PLANNING BRIEF — may invent evidence (confirmed, 4/4 topics)
   ↓
WRITER — inherits and incorporates unsupported evidence (confirmed, 8/8)
   ↓
REVIEW (Fable/Opus) — source-blind, cannot verify or catch it
   ↓
EXECUTOR (Opus) — source-blind, can convert invented paraphrase into
   invented verbatim quotation (confirmed, 4/8 Fable-triggered, 1/8
   Opus-triggered)
```

**What survives unchanged from before this correction**: the review-seat
A/B comparison remains fully causal — every case's two branches share the
identical (already-brief-contaminated) raw draft, so "did revision make it
worse" is still a valid, uncontaminated question. Keep exactly: *"In this
sample, Fable's review style more frequently requested source-dependent
evidence that the source-blind executor could not safely provide (4/8 vs
1/8)."* What changed is only where the PRE-EXISTING fabrication
originated — not the writer, the frozen planning brief.

**This changes the possible Phase 1.5B outcomes from a binary
Fable-vs-Opus choice into four; D is confirmed, and its origin is now
narrower and more actionable than "the writer"**:
- **A.** Opus review is editorially equivalent and safer in this sample →
  replace Fable review with Opus.
- **B.** Fable is materially better editorially but causes unsafe source-
  demand behavior → Fable may earn a redesigned, SOURCE-GROUNDED review
  seat, not the current one.
- **C.** Both models are frequently unnecessary/interventionist (Layer 1's
  finding) → redesign the review prompt/seat first, independent of model.
- **D. Raw drafts contain significant unsupported material — CONFIRMED
  (8/8), and now traced to a single, specific, fixable origin: Fable's
  planning-brief stage (4/4 audited topics), not diffuse writer
  hallucination.** This is MORE actionable than the original "writer"
  framing, not less. This decision is deferred to Phase 1.6, not made in
  this experiment.

## PHASE 1.5B VERDICT — not a final model-seat decision; a scoped finding
plus a bigger, unscheduled one
**Do not restore Fable to the review seat unchanged, and do not conclude
"Opus is simply cheaper" either — both framings undersell what this
experiment found, and neither is the most important result.** Four
separate findings (A/B/C/D above), and D is the one that reordered the
roadmap (see `current-work.md`'s roadmap and `../phase-1.6-source-grounding.md`):
1. The shared review PROMPT/SEAT likely leans interventionist regardless
   of model (Layer 1's 7/16 publish-or-minor vs. both models' 8/8 revise).
2. Fable and Opus are NOT redundant reviewers — each catches real problems
   the other misses in most cases (Layer 2's dominant "partial overlap").
3. In this 8-case sample, Fable's review style triggered unsupported
   evidence-generation substantially more often than Opus's (4 vs 1) — a
   real, architecturally-explained difference, not yet a general rate
   claim, and not solely a Fable defect (case-02 shows Opus's own review
   triggering the identical failure).
4. **Unsupported named-individual/testimony material is present by the
   raw-draft stage in 8/8 of this sample — traced to its origin: the
   frozen FABLE-AUTHORED planning brief's `resisting_example`/
   `correction_moment` field, confirmed in all 4 topics by direct read of
   the brief JSON files, not independent writer invention.** Corrected
   from an earlier, wrong attribution to "the writer stage" — the
   repeated two-sample symmetry (identical invented swimmer in both sauna
   samples, identical invented Deborah Antwi in both curb_cuts samples)
   was the tell; the writer faithfully incorporates what the brief handed
   it. This is larger and more foundational than the review-seat ROI
   question this experiment was built to answer, and it reopens — as a
   SAFETY question, not the still-untested ROI question — the one seat
   this experiment's design explicitly declared out of scope.

**What this does NOT change**: the review-seat A/B itself stays causally
valid — both branches per case share one identical (already brief-
contaminated) raw draft, so "did revision make it worse" is still
answerable, and finding 3 is real evidence on that question. What it DOES
change: closing Phase 1.5B with only a model-seat recommendation would
bury finding 4, which likely matters more for CripMinds' credibility than
which model reviews — and finding 4 is now sharper and MORE actionable
than first stated, not less: one prompt (`_fable_editorial_brief`,
currently fed a ~400-char summary, never the full source) is the
confirmed origin for all four topics' contamination, not a diffuse
writer-hallucination problem that would need fixing in many places.

**Recommended next step**: `../phase-1.6-source-grounding.md` — a promoted,
blocking phase ahead of Phase 2, not an optional hardening pass filed under
"Fable ROI." Its 4 substeps (planner schema + provenance, deterministic
non-LLM validator, reviewer contract, executor contract) ship together, not
sequentially — the causal chain shows sequential amplification (planner
invents → writer naturalizes → reviewer demands a stronger version →
executor turns it into quotation), so fixing only the planner would leave
later stages free to manufacture new unsupported specificity from
otherwise-legitimate paraphrase.

**Explicitly separate from this experiment, still untested**: whether
Fable's planning is BETTER or WORSE than Opus's would be at the same task
(the original "planning ROI" question — frozen briefs by design can't
answer this, and this correction doesn't change that). What IS now
answered, and is a different question: whether Fable's CURRENT planning
output, as implemented, is safe to keep feeding downstream unchanged —
no, confirmed 4/4 topics.

**What resumes after Phase 1.6 lands**: a small grounded review-seat
follow-up (not a repeat of this 8-case experiment) before any final
Fable-vs-Opus review-seat decision — because both reviewers in this
experiment were judging drafts whose factual substrate was already
contaminated by an ungrounded planner; the distribution and nature of
editorial problems may look different once that's fixed.

# Acquiring genuinely unseen current-contract definitions

Pre-registration. Written **before any run**, so that nothing below can be chosen after
seeing an outcome. 2026-09-24. Branch `fix/relational-dispatch-2026-09-24`. Nothing has been
run. Zero authority, no publication.

This is a **data-acquisition experiment, not a repair experiment**. Its product is a frozen
batch of detector and classifier outputs of every type. No repair may be attempted until the
batch is closed and hashed.

## What is frozen going in

| | |
|---|---|
| Detector | `80554bd`, unchanged, OFF by default, zero authority |
| Local value/attribute repair | unchanged |
| Relational dispatch classifier | `1ee91de`, unchanged for the whole batch |
| Obligation policy | `d4bd9ea` |
| Repair `SYSTEM` / `SCHEMA` | `a31d665c…` / `c0d9ad5a…`, pinned by test |
| Branch G | reproducible bit-for-bit (`slice_sha256 dd142b26…`, `user_prompt_sha256 87066c95…`) |
| Production | `b806008`, untouched |

The 1/8 distinctiveness bound is **not to be retuned** during or because of this batch. It is
defensible and far from the observed decision boundary. Fresh cases are allowed to break it —
that is the point of running them.

## The honest power estimate, declared in advance

Observed so far: **15 definitions probed, 7 flagged commitments, 1 relational.** Point
estimate P(relational per definition) = 1/15 = 0.067, on a single event, so the interval is
very wide — the 95% Poisson upper bound on 1 event is 4.74, i.e. the true rate could plausibly
be anywhere from ~0.002 to ~0.32.

| batch size | expected relational | P(0) | P(≥1) | P(≥3) |
|---|---|---|---|---|
| 24 | 1.6 | 0.20 | 0.80 | **0.22** |
| 30 | 2.0 | 0.14 | 0.86 | **0.32** |
| 45 | 3.0 | 0.05 | 0.95 | 0.58 |
| 65 | 4.3 | 0.01 | 0.99 | 0.80 |

**So a 20–30 definition batch is well sized as a rate measurement and poorly sized as a
replication cohort.** At 24 definitions there is roughly a one-in-five chance of zero
relational cases and only a one-in-five chance of the three that
`BOUNDED_RELATIONAL_REPAIR_REPLICATION` needs. Saying this now means a thin result cannot
later be read as bad luck, and a lucky one cannot be read as vindication.

The batch is therefore declared as **a measurement of the relational rate**, with replication
eligibility as a by-product if it happens to arrive.

## Stop condition

**24 fresh definitions**, with a hard cap of **18 pipeline runs**. Whichever comes first.

Stopping on the count of definitions is safe: definitions are the denominator, independent of
the outcome being measured. Stopping on relational hits would bias exactly the quantity at
issue and is forbidden. If 18 runs yield fewer than 24 definitions the batch **closes short
and reports short** — no topping up, because a top-up decided after looking is a stopping rule
in disguise.

Expected cost: 14–18 pipeline runs plus one detector call each. The classifier is free.

## Ordering — the part that does the work

1. **Freeze the candidate pool and ranks first.** Produce the pool with the ordinary
   commissioning stage, write it to disk, hash it. Nothing after this may change it.
2. **Apply `EXCLUSIONS.json` to the frozen pool**, mechanically, before any run.
3. **Consume candidates in rank order.** No skipping, no re-picking, no "that one looks
   promising". A candidate that fails upstream is recorded as a failure and the next rank is
   taken — it is not replaced by a hand-chosen substitute.
4. Ordinary production Research → Ledger → Architecture contracts. `KNOWLEDGE_FIRST` lane and
   the production diversity prior as they stand.
5. **No prompting for relations anywhere.** `definition_evidence` stays whatever the pipeline
   naturally produces. Any nudge toward relational definitions would manufacture the result.
6. Unchanged detector, one call per plan. Unchanged classifier, zero calls.
7. **Preserve every outcome**: clean definitions, non-relational, ambiguous, relational, and
   plans that die before Architecture. The refusals are data, not waste — they are the only
   evidence the refusal side of the classifier behaves out of sample.
8. **Close and hash the batch before any repair is considered.**

## Exclusions

`EXCLUSIONS.json`, eight plans, enforced by the runner rather than trusted:

| key | subject | definitions | source URLs |
|---|---|---|---|
| roman-detectors | Roman WFI HgCdTe detectors | 3 | 51 |
| dressing-evacuation | Kerry Curtis / RCA | 2 | 34 |
| aufguss-sauna | Summerhall sauna, Edinburgh Fringe | 2 | 19 |
| east-meets-east | the Aethos hotel interior | 2 | 47 |
| plein-air | Remington Robinson, plein air miniatures | 1 | 46 |
| whaling-quota | The Whale, Andøya, minke quotas | 2 | 58 |
| iso-microphone | EP remote interpreting, ISO 20108/20109 | 2 | 31 |
| block-group | ACS block groups, rent burden | 2 | 8 |

Enforced keys: **definition term**, **seed_id**, **question_id**, **exact source URL**. Only
the ISO plan carries `seed_id`/`question_id` (`kf-pr002-03-7160563`, `PR002-03`); the other
seven predate acquisition provenance or survive only as trimmed copies, so for those the
enforceable keys are definition terms and the 294 recorded source URLs, plus a one-line
subject check by a human before the batch is admitted.

**Source domain is deliberately not an exclusion key.** A publisher is not a subject. Banning
`dezeen.com` or `smithsonianmag.com` would exclude a whole slice of design and science
journalism and bias the batch away from it — a selection effect of its own kind. What breaks
independence is the same subject or the same documents, not the same masthead.

`remote interpreting` — the ISO plan's second, unprobed definition — is **excluded**. It comes
from a source plan already consumed, so it could only ever be a classifier smoke test, never
an independent case, and spending it now buys less than keeping it available.

## What each outcome means — decided now, not afterwards

| relational cases in 24 definitions | reading | next step |
|---|---|---|
| **0** | consistent with the prior; rate plausibly ≤0.04 | do not extend this batch. Replication needs ~65 definitions for a fair shot; that is a scale decision, not an experiment decision |
| **1–2** | the modal outcome; rate estimate sharpens to ~2 events in 39 | still short of a cohort. Bank the cases, re-measure, decide scale |
| **3–5** | the cohort exists | freeze eligibility, then run `BOUNDED_RELATIONAL_REPAIR_REPLICATION` at fixed policy `d4bd9ea`, one call per relational case |
| **≥6** | the rate is much higher than observed | suspect the classifier over-dispatches out of sample before celebrating; hand-review every case first |

Whatever the count, the **refusals** get reviewed by hand against the classifier's stated
reason. That is the real out-of-sample test, and it happens at every outcome above.

## Not started

No candidate pool has been produced. No pipeline run has been launched. No detector call has
been spent. This file and `EXCLUSIONS.json` are the pre-registration only, and the batch does
not begin without an explicit go-ahead.

---

# Result — the batch closed short, and the classifier did not survive it

Run 2026-09-24. 18 attempts, 2.18 hours, 141 pipeline model calls plus 7 detector calls.
Frozen at `/srv/data/cripminds-relational-supply-2026-09-24`, 176 files, SHA256SUMS.txt.
Nothing was repaired, published, or merged.

## What the batch produced

| | |
|---|---|
| attempts (cap 18) | **18 — closed on the cap, not the target** |
| reached ARCHITECTURE | 7 |
| research HOLD | 5 |
| held before ARCHITECTURE (WORTH) | 3 |
| anchor unfetchable | 3 |
| **fresh definitions** | **14** of the 24 target — CLOSED SHORT, no top-up |
| flagged commitments | 6, across 4 of the 7 plans |
| dispatch | RELATIONAL 2, NON_RELATIONAL 4, AMBIGUOUS 0 |

The pre-registered power table put P(≥3 relational) at 0.22 for 24 definitions. At 14 it is
lower still. The batch was always more likely to measure a rate than to build a cohort, which
is why it was declared that way.

## Unselected supply is much thinner than selected supply

The cap was sized against production's own recent history: 20 of 30 runs reached ARCHITECTURE,
averaging 3.7 definitions. This batch got 7 of 18 and **exactly 2 definitions every time,
7 times out of 7**. Roughly 0.8 definitions per attempt against the 2.5 that sizing assumed.

The mechanism is identifiable, not mysterious. Production's selector **assesses ~12 candidates
with a model and commissions one winner**; this pool used only the deterministic exposure
ranking and consumed it in order. The theme stream ranks arXiv and bioRxiv highly, because
preprint titles match disability and cognition vocabulary — and preprints have no independent
secondary coverage, so they fail research sufficiency. Three of the five research HOLDs were
consecutive preprints, all `HOLD_INSUFFICIENT_RESEARCH`, all reporting 1 independent source,
1 cluster, 1 publisher, and zero fetch failures. Real editorial holds, not an outage.

So this batch measures P(relational | definition from an **unselected** eligible candidate).
Production accumulates P(relational | definition from an **assessed, commissioned** candidate).
They are different populations and the numbers here should not be read as the second.

## The finding that matters: both relational dispatches are wrong

Every flagged commitment was hand-reviewed against the classifier's own stated reason.

| # | term | flagged span | dispatch | review |
|---|---|---|---|---|
| 1 | association rule mining | `lower reported distraction` | **RELATIONAL** | **FALSE** |
| 2 | goosecam | `the researchers pointed at participants' skin` | **RELATIONAL** | **FALSE** |
| 3 | speculative climate poem | `into a changed climate` | NON_RELATIONAL | correct |
| 4 | speculative climate poem | `of living there` | NON_RELATIONAL | correct |
| 5 | commercial corridor | `the block and neighborhood a business sits on` | NON_RELATIONAL | correct |
| 6 | tether | `carried on the animal` | NON_RELATIONAL | correct |

**Case 1.** F06 says *"self-regulated learning strategies co-occurred most consistently with
lower digital distractions"*; the gloss says *"lower reported distraction"*. The unsupported
word is **`reported`** — a measurement attribution, the same family as the ISO case. The
classifier chose `E2 = {lower}`: a comparative degree word. `reported` was removed by R2 (not
in the evidence) and `distraction` — the actual noun — was removed by **R4 at df 22/50 =
0.440**, because it is what the plan is about. What survived all four filters was the one word
that is not a concept.

**Case 2.** F53 says *"The researchers collected continuous piloerection data using a video
recording device called the 'goosecam'"*. The gloss adds where it was aimed. The unsupported
content is `skin`, which R2 correctly removed. The classifier chose `E2 = {researchers}` — a
generic agent noun. Worse, F53 already ties researchers to the goosecam, so that relation is
*licensed*; it cannot be the unlicensed one. R3 passed it anyway because F52 mentions
researchers without mentioning goosecam — a proposition about the study in general, not a
concept standing at the far end.

## Root cause: I removed rarity as a qualifier and left survivorship in its place

R1–R4 are all **negative filters**. They remove bad candidates. Nothing in the rule requires
what survives to be a concept. So when the filters strip out everything substantive — the
subject-matter noun by R4, the actually-unsupported word by R2 — whatever weak token is left
becomes the endpoint by default: a comparative in case 1, a generic agent noun in case 2.

That is the ISO defect wearing different clothes. "Rarest of one" became "last one standing".
Phase 7 fixed the symptom and left the shape: **there is still no positive test that an
endpoint is a concept.**

R3 is also weaker than its own description. "Licensed by a proposition that does not mention
the term" is a poor proxy for "a concept with an existence of its own" whenever the candidate
is a generic entity the corpus mentions throughout.

## One predicted cost, observed

Case 5's candidates included `neighborhood` and `business`, while F20 says *neighborhoods* and
*businesses*. Exact-token membership rejected both on morphology. Here it did not change the
verdict — the unsupported word is `block`, which appears nowhere in the evidence, so the
refusal is right on the merits — but the plural/singular brittleness predicted in phase 7 is
now observed rather than hypothetical.

## Verdict

The phase 7 verdict is **withdrawn**. It was earned against a set the rule was built on, and
the first genuinely out-of-sample flagged commitments broke it: **two dispatches, two false
positives, in the dangerous direction.** Four refusals were correct, so the refusal side held.

`CONCEPT_ANCHOR_CLASSIFIER_NEEDS_REDESIGN`

Not fixed here. The rule that failed was found by looking at an outcome, and changing it now
would fit it to the two cases it failed on — the same trap phase 6 identified and phase 7 then
walked into anyway by treating 7/7 as evidence.

## Against the pre-registered decision table

Two relational dispatches would have read as row "1–2: useful replication evidence, not a
cohort". Both are false, so the honest reading is **row 0: zero genuine relational cases in 14
definitions**. Combined with the prior, that is 1 genuine relational case in 29 definitions.

`BOUNDED_RELATIONAL_REPAIR_REPLICATION` is **not** eligible to run, on two independent grounds:
there is no cohort, and the dispatcher that would select one is not trustworthy.

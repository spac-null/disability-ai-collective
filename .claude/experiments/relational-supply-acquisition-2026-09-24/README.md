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

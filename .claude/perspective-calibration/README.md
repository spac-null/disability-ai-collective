# Perspective Library Calibration — Protocol

**Status: FROZEN DESIGN, awaiting pilot run.** No condition has been executed yet. This
document defines the protocol; it does not run it.

**Worktree:** `research/perspective-library-calibration`, branched from `origin/main` at
`3614acf52762b61d859a03a2e6bcb4a948bc25b6` — the same commit that closed the PR004 first
owner review and moved the Perspective Library from *building* to *calibration* (see
`.claude/perspective-research/INDEX.md`).

**What this is not.** Not an integration into `CURRENT_ENGINE`. Not a change to the live
Lens Probe. Not a new PINA/MAYA/SIIRI/ZENO agent. Not a byline change. Not a reopening of
PR001–PR004. Not PR005.

---

## The question

Does the reviewed Perspective Library (14 stable axes + 16 APPROVED_DURABLE instruments)
generate better research questions than the current live Lens Probe — not more
sophisticated-sounding ones, not more numerous ones, better ones: concrete, distinctive,
failable, and no more prone to forcing a reading than the baseline.

---

## FINAL CORRECTION 1 — Identical world input

For every subject in every set (scored, diagnostic, pilot), there is exactly one canonical
run input: `NEUTRAL_WORLD_SUMMARY` and `KEY_OBJECT_SYSTEM_EVENT`, both defined once in
`subject-set-001.md`.

**Condition A and Condition B receive the identical factual content.** An adapter may
reformat those two fields into whichever shape a condition's prompt structurally expects
(e.g. Condition A's live contract expects `anchor_text` and a `sources` list; Condition B's
system prompt expects prose) — but an adapter may not add, remove, or reinterpret factual
material, and must not add anything from `design-notes-001.md`. Neither condition receives
owner notes, designer expectations, bucket labels, or any hint about intended difficulty.

## FINAL CORRECTION 2 — Designer priors stay out of the run file

`subject-set-001.md` (run-facing) never contains: bucket A/B/C, positive/negative-control
labeling, temptation-case labeling, expected reading, likely instrument, likely mind, WHY
INCLUDED, prior production result, or owner expectation. All of that lives in
`design-notes-001.md`, which is marked, and must stay, **DO NOT PROVIDE THIS FILE TO
CONDITION A OR CONDITION B.** The condition runner must never read it. The owner's blind
review sheet must never contain those fields either — they surface only in the post-reveal
secondary analysis.

---

## The three sets

**SCORED (16)** — enters the primary A/B tally. Max 3 explicit-disability subjects (met
exactly: 3). At least 8 non-disability subjects (met: 13).

**DIAGNOSTIC (3)** — Tollymore, Roman Space Telescope, Beetaloo. Known prior subjects or a
subject appearing as doctrine's own worked positive example. Run for information only.
**Never enter primary winner tallies.**

**SACRIFICIAL PILOT (4)** — tests mechanics, not intellectual performance. **Never enter
primary or diagnostic tallies, never enter calibration metrics.** Run first; both contracts
freeze only once all four pass. Mix: 2 likely-NOTHING_HERE, 1 obvious-positive, 1
genuinely-ambiguous — see `subject-set-001.md` for content and `design-notes-001.md` for why
each was picked.

All subject content is in `subject-set-001.md`. All designer rationale, source basis, and
first-draft replacement history is in `design-notes-001.md`.

---

## CONDITION A — exact live contract

`LENS_PROBE_SYSTEM` + `lens_probe_prompt` + `lens_probe`, verbatim, from
`automation/new_engine_v1/research.py` (this worktree, lines 814–937). No improvement, no
weakening, no additional hypotheses, no disconfirmation field added, no Perspective Library
material. Structurally **0 or 1 hypothesis** per subject (`assumption` + `carrier_hypothesis`
+ `queries` + `urls`). This asymmetry against Condition B's up-to-3 is real and disclosed,
never corrected.

**Model/provider:** the production-configured one. Confirmed in this worktree:
`automation/new_engine_v1/provider.py` sets `DEFAULT_MODEL = "anthropic/claude-opus-4.8"`,
and no lens-probe-specific override exists anywhere in `research.py` or `composition.py`
(the only per-stage override found, `COMPOSITION_MODEL`, applies to composition only). The
routing comment in `composition.py` (dated 2026-09-04) records that CLIProxy's native
claude-* routes were returning `401` at that time and the effective path was OpenRouter's
`anthropic/claude-opus-4.8`. **Condition B must use this same model** — not a stronger one —
per Correction 13/Model Control below.

## CONDITION B — library only, minimum process

Primary system-prompt content, and nothing else:

- The **14 axes**, CONCEPT/QUESTION/CARRIERS/FALSE MOVE fields only.
- The **16 APPROVED_DURABLE instruments**, in full (MECHANISM/QUESTION/CARRIERS/FALSE
  MOVE/DISCONFIRMING SHAPE/BOUNDARY): PR001-02, PR001-03, PR001-05, PR001-07, PR001-09,
  PR002-01, PR002-02, PR002-03, PR002-05, PR002-07, PR003-03, PR003-06, PR003-08, PR004-01,
  PR004-02, PR004-05.
- The **two approved axis sharpenings**: PR003-01's operational test (who·how·when·where·in
  what way, under Axis 5) and PR004-07's operational question ("what action does this
  apparently neutral object require from the body?", under Axis 1).
- Minimum process rules, as instructions: **WORLD FIRST** (read the world summary before
  generating any hypothesis, never the reverse); **NO PROXIES**; **an accessibility/access
  fact is evidence, not an insight — it must reveal something less obvious**; **every
  hypothesis must be capable of failure** (state a disconfirming shape or it is not a
  hypothesis); **NOTHING_HERE is a fully valid output**, with one line of reason.

**Excluded, explicitly:** CANDIDATE entries (PR001-01/04/06/08, PR002-04/06/08/09,
PR003-04/05/07, PR004-04/06/09); **M1–M10** (pre-date the reviewed library, would confound
what-did-the-library-add); Section 6's seven worked failure cases; Tollymore, Roman,
Beetaloo; all mind formation/voice/biography/illustration text; mind roleplay of any kind.
Minds may be logged **invisibly**, after a surviving hypothesis, as `MIND(S) SHARPENED` —
they never each produce a separate answer.

## FINAL CORRECTION 4 — B's top-1 ranking

Condition B may generate up to 3 candidates internally in one call. It must designate
**exactly one TOP hypothesis** before the owner ever sees output, ranked against all three
criteria:

1. **DISTINCTIVE QUESTION** — does this produce a specifically Crip Minds research question,
   not generic competent analysis?
2. **DISCRIMINATING EVIDENCE** — does it predict a concrete place/fact/carrier that could
   support or kill it?
3. **DISCONFIRMATION** — is there a plausible evidence pattern under which it would fail?

A candidate is disqualified from the TOP position if it is: proxy reasoning; a generic
accessibility observation; a generic institutional critique; an analogy without a
subject-specific mechanism; or merely sophisticated wording. The instruction to the model:
*"If only one of these could proceed to targeted research, which one earns the slot?"*
Hypotheses 2–3 are logged and stay hidden until post-reveal.

---

## Primary blind display

Exactly two fields, extracted deterministically — **no model rewrites either condition's
output**:

| Field | Condition A | Condition B |
|---|---|---|
| **HYPOTHESIS** | `assumption` | The predeclared TOP hypothesis |
| **EVIDENCE PROBE** | `carrier_hypothesis`, flattened with its `queries`/`urls` | TOP's predicted discriminating evidence |

**Hidden during primary scoring:** condition identity, instrument IDs, axis IDs, mind names,
B's alternates, B's disconfirming shape, B's why-it-matters prose, all designer priors.
VERSION X/Y randomization happens only at actual run time, not in this design.

## Primary owner scoring

Per displayed hypothesis: **CLASSIFICATION** (DEAD / USEFUL / CRIP_MINDS / FORCED /
DUPLICATE), **CONCRETENESS** (0/1/2), **DISTINCTIVENESS** (0/1/2), **OWNER NOTE** (optional).
A NOTHING_HERE response is displayed plainly as such. Subject level: **BEST VERSION** (X / Y
/ TIE / NEITHER), **WOULD I RESEARCH FURTHER** (X / Y / BOTH / NEITHER).

**FAILABILITY is not scored blind** — Condition A's live contract has no disconfirming-shape
field, so scoring it blind would silently reward B for a field A structurally lacks.
FAILABILITY is **secondary only**, see below.

## Secondary, post-reveal analysis

1. **EPISTEMIC DISCIPLINE.** For A: does its one-sentence hypothesis imply an obvious
   falsifier, without the owner inventing one on its behalf? For B: inspect the actual
   DISCONFIRMING SHAPE field.
2. **PORTFOLIO VALUE.** Reveal B's hypotheses 2–3, classify them on the same five-value
   scale, then answer **DID B'S ALTERNATES ADD REAL VALUE?** (YES/NO/UNCLEAR) — a question
   about whether multi-hypothesis generation is worth its complexity, never folded into BEST
   VERSION.
3. **INSTRUMENT TRACKING.** Per instrument: which subject it fired on, and the owner's
   classification there. Raw tracking only — no KEEP/SHARPEN/RETIRE/RETURN_TO_CANDIDATE
   decision is made from a 16-subject sample.
4. **MIND DIFFERENTIATION.** Evaluate difference in **what was noticed**, never in counts.

## Negative-prior rule

A subject's presumed-negative status (recorded only in `design-notes-001.md`) is a designer
expectation, not truth. NOTHING_HERE is not automatically the "correct" score for a
presumed-negative subject. A concrete, non-forced, evidence-seeking CRIP_MINDS hypothesis on
a presumed negative is a genuine successful surprise. A forced reading remains a failure
regardless of which subject it appears on. Presumed-negative labeling is used only for
**aggregate restraint-rate analysis after owner scoring** — never to pre-judge one subject's
score.

---

## Model control — document now, execute later

- Same underlying model for A and B: `anthropic/claude-opus-4.8` (resolved above from
  `provider.py`). B is never given a stronger model to compensate for its heavier schema.
- Same reasoning-effort/config where the provider exposes one.
- Fresh, isolated context per call — no conversational memory across subjects, no earlier
  subject's output visible to either condition.
- Paired per subject; **A-first vs. B-first execution order randomized and logged** per
  subject.
- Record per call: exact model/provider identity (`requested_model` / `actual_model`, as
  `Completion.identity()` already captures for A — extend the same capture to B), date,
  temperature/config, and **token usage**. B's higher expected token cost is recorded as a
  fact, never normalized away.

## Freeze rule

Run the 4 sacrificial pilots first. Verify: NOTHING_HERE renders correctly; a genuine
positive hypothesis renders correctly; B reliably designates one TOP hypothesis; the blind
display leaks no condition-identifying metadata; the parser/schema is stable; token/cost
logging works. **Only once all four pass unmodified do Condition A, Condition B, and the
blind renderer freeze.** No prompt edits during the scored 16. If a real technical defect is
found mid-benchmark: **STOP.** Do not silently repair partway through — document the defect,
discard that run, fix, and re-freeze before re-running from the top.

## Execution order

1. Run 4 pilots (P01–P04). Verify mechanics. Freeze.
2. Run scored 16, paired, randomized order, logged.
3. Owner blind-scores the 16.
4. Unblind; run secondary analysis (epistemic discipline, portfolio value, instrument
   tracking, mind differentiation).
5. Run the 3 diagnostics (D01–D03), report separately, never in the primary tally.
6. Summarize against the six success / seven failure shapes from the original calibration
   question. No composite score.

## Retrieval

Ordinary retrieval first. **OpenAlex** only for scholarly metadata / OA discovery.
**Firecrawl** only for a known public URL blocked technically, and only after validating the
retrieved identity. Neither tool is integrated into `CURRENT_ENGINE` by this design, and this
task does not do so.

**Security note.** `~/.config/cripminds/openalex.env` and `~/.config/cripminds/firecrawl.env`
exist on this Mac (mode 600, single-user). Their values were never printed or committed in
any session that produced this document — only redacted key *names* were ever shown. As a
matter of hygiene, both credentials should be rotated before any new retrieval work relies on
them, simply because they have been referenced (never displayed) in an interactive agent
session. **Never place secrets in repo files** — nothing here does.

---

## Boundaries carried from the owner's task, restated

No production run. No `CURRENT_ENGINE` change. No Perspective Library implementation into
production. No PINA/MAYA/SIIRI/ZENO agents. No byline change. PR001–PR004 not reopened. PR005
not opened. `results/` is not created by this task — only when a pilot or calibration run
actually happens.

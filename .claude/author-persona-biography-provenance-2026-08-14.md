# Author-Persona Biography Provenance Closure — 2026-08-15

Follows the editorial-upgrade-v1 paired experiment (Maya Flux/Siri Sage each
invented one first-person biographical anecdote untraceable to
`persona_canon/*.md`) and the formula root-cause audit's classification of
this as a distinct, separate gap from the known human-detail-provenance
(P1) finding. Production baseline: `origin/main @ 7a367f4`, untouched. No
deploy, no push, no fake run.

## FAILURE PATH (traced to actual code)

Three layers exist, each with a different, now-precisely-understood scope:

1. **Deterministic scanner** (`grounding.scan_draft_for_unsupported_specifics`,
   wrapped for revision-diffs by `find_new_unsupported_personal_history`):
   fires on a quoted span, a multi-word Title-Case name, or a 2+-digit
   number, checked against `source_text + persona_factual_context`
   concatenated. Explicitly documented, and confirmed here
   (`test_deterministic_scanner_misses_no_signal_anecdote`), to produce
   **zero hits** on a fabricated event with none of those three signals —
   exactly the shape of both known cases ("six weeks the freight elevator
   was down", "a September afternoon... asked a guard to repeat a line").
2. **Semantic reviewer check** (`_fable_editorial_review`'s FIRST-PERSON
   FACTUAL EPISODE CHECK, `llm.py`): an LLM-judged, correctly-scoped
   instruction distinguishing persona-canon-authorized claims from invented
   ones — added 2026-08-11 after a real production incident (a fabricated
   "I sat through a wayfinding review in Rotterdam, March 2024" episode
   shipped to publication). Real and working in principle, but had two
   structural weaknesses before this fix: its findings shared a 3-note
   budget with 9 unrelated concerns (opening, complication, discovery,
   quoted voice, aphorism density, managing-the-reader, signposting,
   ending, wholeness) and could be silently dropped; and even when flagged,
   nothing forced `verdict="revise"` — the model's own verdict field was
   trusted as-is.
3. **`rewrite_with_opus`** (the sole revision path for non-Opus-provider
   drafts): confirmed by direct code reading to have **zero check of any
   kind** against source or persona-canon material before this fix — only
   `validate_rewrite_integrity` (length/frontmatter/duplication), which has
   no concept of what's authorized. Non-Opus drafts also skip
   `_fable_editorial_review` entirely (that reviewer only runs when
   `is_opus`), so this was a fully uncovered path.

**A. What the initial writer receives**: `AUTHORIZED PERSONAL HISTORY`
(from `_load_persona_factual_context`, real `persona_canon/*.md` or
`*-factual.md` content) plus the `AUTHOR RULE` prompt block — prompt-only,
no deterministic backstop on the writer's own first draft beyond the raw
draft guard's blunt scan (already known to miss anecdote-shaped
fabrications).
**B. What the prompt explicitly permits/prohibits**: first person freely
(opinion, attention, interpretation); biographical fact only if traceable
to canon or source — already correctly stated in `AUTHOR RULE`,
`_first_person_contract`, and the raw-draft-guard comment; the gap was
never the wording of the rule, it was enforcement reach.
**C/D. Revision-stage coverage**: `_opus_targeted_revision` and
`_fable_polish_rewrite` already ran `_reject_if_unsupported_specifics`
(deterministic, blocking) before this fix; `rewrite_with_opus` did not — so
YES, a clean initial draft (or one with real, small edits) could acquire
invented biography specifically during a fallback-provider rewrite with
nothing to catch it.
**E. Existing validator for this exact semantic class**: yes,
`_first_person_contract` — genuinely correct in scope, but under-enforced
(note-budget competition, no verdict override) and gated to Opus-provider
drafts only.

## CLAIM DEFINITION

The relevant question, per this task's own framing, adopted verbatim in the
sharpened prompt: **does this sentence assert a fact about the author/
persona's real or fictional life history** (an event: childhood, family,
diagnosis, employment, a place lived/visited, a personal encounter, first
use of a technology/device) — as opposed to present-tense opinion,
attention, or uncertainty (non-biographical first person), an editorial
action ("I read the report twice" — a claim about what the narrator did
*with this material*, not about their life history, so not gated by this
check unless it asserts a specific unverifiable event), or figurative first
person ("I've been down this road before" as a turn of phrase). First
person is never banned; only the biographical-event subclass is gated.

## CANON AUTHORITY

Confirmed from actual code, not inferred: `persona_canon/<slug>.md` /
`<slug>-factual.md`, loaded by `_load_persona_factual_context` and
converted to `persona_factual_context["canon_text"]` +
`["provenance_mode"]` by `grounding.build_persona_factual_context`, is the
sole authority — the same object already threaded through brief, writer,
reviewer, and executor stages per the Phase 1.6 evidence-lineage
discipline. Two provenance modes, not interchangeable: `real_person_evidence`
(Pixel Nova only, strict, evidence-audit-backed) and `editorial_canon`
(Maya Flux/Siri Sage/Zen Circuit, the persona's own established fictional
history — legitimate for them to reference, not license to invent beyond
it). "Fits the persona" / "plausible" / "narratively useful" is explicitly
rejected as authorization, in the sharpened prompt text itself.

## MATERIALITY

Semantic classification of the two known cases, both manually verified
against the real canon files (not regex):

- Maya Flux, landlord/freight-elevator anecdote: checked `maya-flux.md` in
  full — no match. **UNSUPPORTED_BIOGRAPHY.**
- Siri Sage, museum-guard/September-afternoon anecdote: checked
  `siri-sage.md` in full — no match. **UNSUPPORTED_BIOGRAPHY.**
- Contrast: Pixel Nova's interpreter-lag and "phone line that only accepts
  calls" material (same paired experiment) and Zen Circuit's
  "eighteen-months-of-therapy" anecdote — both verified present, near-verbatim,
  in their respective canon/factual files. **SUPPORTED_BY_CANON.**

This is **rare but real, not systemic**: 2 of 4 personas, in a 4-fixture
offline sample, plus one confirmed historical production incident
(Rotterdam wayfinding review, predates the 2026-08-11 guards). Not
sufficient evidence to call it "moderate" or "systemic" at corpus scale —
no real published article was found in this pass to carry an unsupported
biographical claim (a full corpus sweep for this specific claim class,
distinct from the formula-audit's corpus scan, was not run here; scope was
the two known cases plus the historical incident, per this task's
"manageable stratified sample" allowance rather than a fresh full-corpus
pass).

## ENFORCEMENT OPTIONS CONSIDERED

A. Prompt-only — rejected per this task's own instruction: the
`AUTHOR RULE`/`AUTHORIZED PERSONAL HISTORY` prompt-only rule was already in
place for both known cases; prompt wording alone doesn't add enforcement.
B. Deterministic detection alone — insufficient by itself (confirmed blind
spot for no-signal anecdotes); would need a new NLP/ontology-scale
detector, explicitly out of scope ("do NOT build a generic biography
ontology").
C. Model-assisted semantic validation — already exists (`_first_person_
contract`); the real gap was reach and enforcement, not absence.
D. Initial-generation validation + rewrite-integrity reuse — **chosen**:
strengthens C's existing enforcement (dedicated field, deterministic
verdict override) and extends the SAME existing deterministic guard
(`_reject_if_unsupported_specifics`) to the one revision path that lacked
it.
E. Reuse existing minimal pattern — this IS what was done: no new
detector function was written; both changes are prompt/schema/call-site
edits reusing `find_new_unsupported_personal_history` and
`_reject_if_unsupported_specifics` verbatim.

## CHOSEN DESIGN

1. `_fable_editorial_review` (`llm.py`): sharpened the `FIRST-PERSON
   FACTUAL EPISODE CHECK` prompt text with the explicit claim-class
   definitions from this task (biographical event vs. opinion/attention vs.
   editorial action vs. figurative vs. canon paraphrase), and added a
   dedicated `unsupported_persona_claims` JSON array — never counted
   against the 3-note cap, never dropped for space. In code: a non-empty
   result **deterministically forces `verdict="revise"`** and prepends
   `"REMOVE unsupported persona biography claim: ..."` notes ahead of the
   model's own notes, regardless of what the model's own `verdict` field
   said.
2. `rewrite_with_opus` (`llm.py`): now accepts optional
   `evidence_packet`/`persona_factual_context`, and after its existing
   `validate_rewrite_integrity` check passes, calls the SAME
   `_reject_if_unsupported_specifics` the other two revision paths already
   use, comparing pre-rewrite `content` against the rewritten output.
   Frontmatter (identical on both sides, since this function's own prompt
   requires preserving it) cancels out in the diff automatically — no
   special-casing needed. None-safe: an omitted `evidence_packet`/
   `persona_factual_context` still runs the check (empty-corpus mode,
   flags only brand-new quotes/names/numbers), never crashes.
3. `generate.py`'s call site updated to pass `evidence_packet`/
   `persona_factual_context` through to `rewrite_with_opus`.

No new detector, no biography ontology, no new gate architecture.

## REVISION COVERAGE

| Stage | Before | After |
|---|---|---|
| Raw initial draft | Blunt scan only (advisory) | Unchanged — still advisory; this task's scope was revision paths + the reviewer's enforcement, per Section 6/8's framing of revision as "potentially higher leverage" |
| `_opus_targeted_revision` | `_reject_if_unsupported_specifics` (already existed) | Unchanged |
| `_fable_polish_rewrite` | `_reject_if_unsupported_specifics` (already existed) | Unchanged |
| `_fable_editorial_review` | Semantic check existed, under-enforced | Dedicated field + deterministic verdict override |
| `rewrite_with_opus` | **No check at all** | `_reject_if_unsupported_specifics`, same as the other two paths |

Both "can the writer invent biography initially" (yes, raw-draft guard is
advisory-only, unchanged by this task) and "can a rewrite introduce it"
(yes for `rewrite_with_opus` specifically, before this fix — now closed)
are answered.

## FALSE POSITIVES

The sharpened prompt explicitly instructs: a different wording of an
already-authorized fact is fine; only a NEW event is not, "even if it fits
the persona's tone or would be a plausible thing for someone like them to
have experienced. Plausibility is not authorization." Spot-checked (see
TESTS) against a real canon-paraphrase case — correctly returned an empty
`unsupported_persona_claims` list, with three unrelated craft notes (no
quoted voice, no complication, no discovery moment) surfacing normally,
proving the new field doesn't interfere with or get triggered by ordinary
review activity.

## TESTS

`automation/author_persona_biography_test.py`, 14 new tests, all passing,
zero network/model cost (mocked `_call_openai_compat_api`/
`_call_editorial_model`, same harness as `executor_guard_test.py`):
- Confirms the deterministic scanner's blind spot is real (characterization
  test, not a regression).
- `rewrite_with_opus` rejects invented biography (by number), accepts
  authorized real-person-evidence history, accepts fictional editorial-canon
  episodes, stays backward-compatible with no new params, and still honors
  the pre-existing duplicated-body integrity guard.
- `_fable_editorial_review`'s override: forces revise when a claim is
  flagged despite the model saying `publish_as_is`; leaves verdict alone
  when nothing is flagged (no false-positive override); persona-claim notes
  never crowd out or get crowded out by the other 3; missing field defaults
  safely.

Full existing suite (22 files) + snapshot check: **all pass, no
regressions, no drift.**

**Semantic spot-check** (beyond plumbing): captured the REAL, sharpened
`_fable_editorial_review` prompt (real Maya Flux `persona_canon/maya-flux.md`
loaded unmocked) for two cases and had a fresh, independent judge apply it:
- Case 1, the actual confirmed-unsupported landlord/elevator anecdote:
  **correctly flagged** in `unsupported_persona_claims`.
- Case 2, a differently-worded paraphrase of Maya's real authorized
  Prospect-Park-West-hill fact: **correctly returned empty** — no
  false positive.

n=2, not a corpus-scale validation — but real evidence using the actual
production prompt and actual canon file against the actual known failure
case, not merely a demonstration that the code path executes.

## DECISION (AP1)

**AP1 — GAP CONFIRMED + AUTHORITATIVE FIX VALIDATED.**

Gap B (`rewrite_with_opus`, zero coverage) is fully closed and
deterministically proven. Gap A (reviewer enforcement) has its code-level
enforcement deterministically proven, and its residual LLM-judgment
dependency (inherent to any approach that doesn't build a full biography
ontology, which this task explicitly forbade) was spot-checked correct on
both the true-positive and false-positive sides using the real prompt and
real canon data. Candidate commit `a73d71a` on
`author-persona-biography-provenance-2026-08-14`, branched from
`origin/main @ 7a367f4`. **Not pushed, not deployed.**

## FOLLOW-UP: NON-OPUS PRESERVED-CLAIM EDGE CASE (2026-08-15, commit `e93bb1b`)

A73d71a closed two gaps but left a third, real path open, found by tracing
the actual code end-to-end rather than assuming the first two closures were
exhaustive: **a non-Opus initial draft that ALREADY contains an unsupported
persona-biography claim, where `rewrite_with_opus`'s Opus rewrite PRESERVES
that same claim instead of introducing a new one.**

Why nothing else in the pipeline catches this:
- `rewrite_with_opus`'s own guard (`_reject_if_unsupported_specifics` /
  `find_new_unsupported_personal_history`) is diff-based — a claim present
  on both the pre-rewrite and post-rewrite text cancels out; only claims
  *new to the rewrite* are flagged.
- `_fable_editorial_review`'s FIRST-PERSON FACTUAL EPISODE CHECK ran only
  when `generate.py`'s `is_opus` was True — a non-Opus original draft never
  reached it at all.
- `fact_check.py`'s live web fact-check does not fill the gap either:
  `_extract_verifiable_claims`' QUOTE category is explicitly scoped to a
  claim "attributed to a specific named real person, OTHER THAN THE
  FIRST-PERSON NARRATOR" — persona autobiography is out of scope there by
  design, confirmed by direct code read.
- `publish_best.py`'s promotion gate checks only `fact_check_status ==
  "blocked"` — it never inspects the review sidecar's CLEAN/FLAGGED status,
  and `review.py`'s own comments confirm advisory-only findings mark a
  review FLAGGED without setting that flag. So even a FLAGGED-but-not-
  blocked draft would have been promoted normally.

Confirmed adversarially (`automation/author_persona_biography_nonopus_closure_test.py`)
before writing any fix: the preserved claim survives `rewrite_with_opus`
alone, unchanged.

**Fix:** extracted the existing Fable editorial review + polish/executor
guard cycle (previously inlined under `generate.py`'s `if content and
is_opus`) into a shared method, `_run_persona_biography_editorial_pass`
(`llm.py`), called from BOTH branches — unchanged timing for Opus-original
content, and once more for non-Opus content after `rewrite_with_opus`
produces its final prose. No new detector, no phrase list, no
persona-biography ontology — same reviewer, same deterministic
`unsupported_persona_claims` override, same
`_fable_polish_rewrite`/`_opus_targeted_revision` chain a73d71a already
hardened, now reached regardless of which provider wrote the original
words.

5 new tests: the adversarial preserved-claim case, plus 3 control cases —
an authorized canon event (reworded) survives, non-biographical first
person survives (this fix does not ban first person generally), and an
unsupported event introduced *only* by the rewrite is still caught by the
pre-existing (a73d71a) `rewrite_with_opus` guard, unaffected by this
closure. All 14 existing AP1 tests, the full `automation/*_test.py` suite,
and the snapshot check pass unchanged.

## DECISION (APE2)

**APE2 — EDGE CASE CONFIRMED + MINIMAL CLOSURE VALIDATED.** Candidate
commit `e93bb1b` on `author-persona-biography-provenance-2026-08-14`. Not
pushed, not deployed at the time this closure was written; production
integration status is tracked separately in the release record for the
integration this closure ships in.

## A NOTE FOR FUTURE MAINTAINERS: TWO DIFFERENT AUTHORITIES, NOT ONE

This system has two separate provenance guards that are easy to conflate
and must stay separate:

- **Source-derived human detail** (the human-detail-provenance shadow
  guard, `automation/orchestrator/human_detail_provenance.py`) governs
  whether a concrete human-scale detail in an article — a name, a number, a
  described moment — actually traces back to the SOURCE MATERIAL the
  article is reporting on. It answers: *is this detail really in what we
  read?*
- **Author-persona biography** (this document's subject —
  `persona_factual_context`/`persona_canon/*.md`, enforced by
  `_fable_editorial_review`'s FIRST-PERSON FACTUAL EPISODE CHECK,
  `rewrite_with_opus`'s guard, and the other revision paths' existing
  guard) governs a completely different question: whether a first-person
  claim the AI PERSONA makes about ITS OWN life — "when I was twelve, my
  mother took me to..." — traces back to that persona's own authorized
  canon (`persona_canon/*.md` / `*-factual.md`), not the article's source
  material at all. It answers: *is this something this persona is actually
  authorized to say happened to them?*

An article can pass the first check completely (every fact about the
world is real and sourced) and still fail the second (the persona invents
a childhood memory that has nothing to do with the source and isn't in
their own canon either) — they are independent failure modes with
independent evidence packets (`evidence_packet["source_text"]` vs.
`persona_factual_context["canon_text"]`), checked independently, and a fix
to one is never evidence the other is also covered. Do not merge these
into one guard or assume one subsumes the other.

# Current Work Checkpoint

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file, not conversation archaeology. Full
methodology/results for closed experiments live in `.claude/experiments/`
and are linked below, not duplicated here.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see project memory
`project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## ROADMAP / ACTIVE PHASE
Order changed 2026-08-10 evening after the Phase 1.5B planning-brief audit
below promoted grounding ahead of Phase 2 — do not reorder again without a
stated reason.

- **DONE** — Phase 0 (reliability + canonical baseline).
- **DONE** — Phase 1, WHY WE WRITE → **KEEP**, scope-corrected. Full
  record: `.claude/experiments/why-we-write-2026-08-10.md`.
- **DONE** — Phase 1.5A, Persona Architecture Audit (design/audit only,
  no code changes, no generations) → `.claude/persona-architecture-audit.md`.
- **PAUSED, not concluded** — Phase 1.5B, Fable review-seat ROI. Full
  record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **IN PROGRESS — mocked baseline DONE + committed, live controls IN
  PROGRESS** — Phase 1.6, source-grounding hardening. Design doc:
  `.claude/phase-1.6-source-grounding.md`. Code across `grounding.py` (new),
  `llm.py`, `generate.py`, `discovery.py`, `review.py`, `phase_probe.py`,
  `snapshot_test.py`, `grounding_test.py` (new), `executor_guard_test.py`
  (new), `writer_prompt_test.py` (new). `EVIDENCE_SCHEMA_VERSION`/
  `BRIEF_SCHEMA_VERSION` = 3. 149 grounding_test.py + 7 executor_guard_test.py
  + 17 writer_prompt_test.py checks pass (173 total); `snapshot_test.py
  --check` clean. Mocked/offline baseline went through 7 adversarial review
  rounds before being allowed to freeze (each found a real, non-cosmetic
  gap) — full history below in "PHASE 1.6 STATUS DETAIL." **Real API calls
  have now been made** (2026-08-11, on trident): all 4 historically-
  contaminated topics re-frozen under schema v3 (clean, zero contamination
  recurrence), 2 negative-control planner calls (the second exposed a real
  `direct_quote` validation gap, fixed same session as round 8). Full
  results, exact numbers, and what's still outstanding (positive control,
  tamper control, hostile-review control) are in "PHASE 1.6 LIVE CONTROLS"
  further down — read that section before assuming this phase is done or
  re-running anything.
- **THEN** — Phase 2, brevity + evidence budget + testimony.
- **THEN** — Phase 3, persona architecture implementation (perceptual
  engines, motives, soft affinities, remove hard territories/prohibitions —
  informed by 1.5A's findings).
- **THEN** — same-source/four-persona probe (validates whatever Phase 3
  produces).
- **THEN** — Phases 4-8 (correction/repetition/readability/ending/final
  audit), original blueprint order, unaffected by this insert.

## HEAD / PROVENANCE
- **WHY WE WRITE doctrine commit**: `01339ce` — the SYSTEM-prompt swap in
  `automation/orchestrator/llm.py`, the permanent/frozen shared doctrine.
- **Fable review-seat ROI probe commit**: `b99d379` — generated the 8
  Phase 1.5B cases; later checkpoint commits only add provenance/docs, did
  not regenerate data.
- **CURRENT MAIN HEAD**: whatever `git rev-parse HEAD` says after the
  latest checkpoint commit — always AHEAD of the commits above by
  docs-only commits. A session seeing a different HEAD than cited here is
  not a bug.

## THE BLOCKING FINDING — why Phase 1.6 exists
Phase 1.5B's brief audit found all 4 audited frozen planning briefs contain
at least one source-unsupported factual element (a named individual,
testimony, or quote) in `resisting_example`/`correction_moment`, written
by Fable at planning time from only a ~400-char source summary — not by
the writer. Causal chain: FABLE PLANNING BRIEF invents unsupported
evidence (confirmed 4/4 topics) → WRITER inherits/incorporates it
(confirmed 8/8 raw drafts) → REVIEW (Fable/Opus) is source-blind and
sometimes demands "the real words" → EXECUTOR (Opus) fabricates a
verbatim quote to comply (confirmed 4/8 Fable-triggered, 1/8
Opus-triggered). Full methodology and attribution tables:
`.claude/experiments/fable-review-roi-2026-08-10.md`.

## PHASE 1.6 — SOURCE-GROUNDING HARDENING (next, not started)
Full design: `.claude/phase-1.6-source-grounding.md`. Four substeps,
shipped together (not sequentially, to avoid leaving later stages free to
manufacture new unsupported specificity): (1) planner schema change —
structured evidence-candidate object with `status: found|not_found`,
never a flat string; (2) deterministic non-LLM validator between planner
and writer (quote/name/date substring + pointer checks); (3) source-aware
reviewer — receives the evidence packet, cannot demand evidence that
isn't in it; (4) source-aware executor — same constraint, never converts
paraphrase into quotation. Acceptance test uses adversarial
negative-control sources (deliberately lacking a witness/quote/anecdote)
as well as positive controls, not just cooperative sources.

## PHASE 1.6 STATUS DETAIL (as of 2026-08-11, recovery/continuation session)

Implemented and offline-verified (compile clean, 125 grounding_test.py
checks + 7 executor_guard_test.py checks pass, snapshot_test.py --check
clean). Numbers below (108, round 1-2 fixes) were superseded by a third
review round — see "THIRD REVIEW ROUND" further down for what changed
after this list was first written:

- `automation/orchestrator/grounding.py` (new): evidence-packet identity
  (`build_evidence_packet` — `evidence_packet_hash` now covers the FULL
  provenance payload, not just source_text+schema, after a hash-collision
  bug was caught on review), the deterministic evidence-candidate validator
  (`validate_evidence_field`/`validate_brief`, stamps `grounding_status` +
  `grounding_scope="evidence_fields_only"` — the scope field exists
  specifically so "validated" is never misread as "the whole brief is
  grounded"), `writer_prompt_block` (writer-facing text from VALIDATED
  primitives only — no planner-authored `editorial_need`/`interpretation`
  prose, and legacy flat strings are REJECTED, not passed through — that
  tolerance belongs only in `evidence_text()` for review.py's historical
  reads), `is_current_brief_schema` (legacy-fixture gate), and
  `find_new_unsupported_specifics` (deterministic post-revision guard —
  see below). `scan_free_prose_field` also exists but is DIAGNOSTIC ONLY,
  deliberately NOT wired into `validate_brief` (see its docstring for why
  it was tried as an enforcement gate and reverted: it can't catch a plain
  fabricated sentence with no quote/name/number).
- `llm.py`: planner (`_fable_editorial_brief`), reviewer
  (`_fable_editorial_review`), and both executors
  (`_opus_targeted_revision`, `_fable_polish_rewrite`) all take
  `evidence_packet` and consume `source_text` unsliced (no more independent
  `[:6000]`/`[:3000]` re-slicing per stage). `opening_scene`/`seed_sentence`
  are still generated by the planner but NO LONGER injected into the writer
  prompt (generate.py) — only `opening_shape` (a structural category)
  crosses into generation, because no deterministic check can fully verify
  free prose. `angle`/`cross_cite` carry an explicit prompt-level
  no-unsupported-factual-premises constraint (the last planner free-text
  fields that do still reach the writer). `_EXECUTOR_CONTRACT` wording
  closed the "already in the article" loophole (existing wording may be
  preserved; new factual specifics about ANY subject, including one already
  named in the draft, still require source support). Both executors now run
  `_reject_if_unsupported_specifics` (backed by
  `find_new_unsupported_specifics`) on their own output before accepting
  it — a deterministic, non-LLM backstop for the exact confirmed Phase 1.5B
  failure (reviewer says "get her real words" → executor invents a
  quote), scoped to newly-introduced quoted spans and multi-digit numbers.
- `generate.py`: builds ONE `evidence_packet` per run, threads it unmodified
  into planner → reviewer → executor (verified by direct grep, not just
  code review).
- `review.py`: `_plan_follow_read` uses `evidence_text()` for
  tolerant historical reads of both legacy flat-string and new structured
  `article_plans` rows — this is a shadow-mode craft check reading old DB
  rows, not a production-acceptance path, so tolerance here is correct and
  intentional (unlike `writer_prompt_block`).
- `phase_probe.py`: `_load_frozen_brief` fails closed on the 4 legacy
  flat-schema fixtures (`brief_sauna.json`, `brief_hiring_tool.json`,
  `brief_curb_cuts.json`, `brief_museum_labels.json`) — confirmed via direct
  call. `fable_review_roi_probe.py --preflight`/`--run` inherit this for
  free (they import the same `_load_frozen_brief`); `--summary`/`--test-mock`
  are correctly unaffected. `freeze_briefs()` now builds/passes a real
  `evidence_packet` (previously would have re-frozen with NO source at
  all). Added `assert len(source_text) <= PROBE_SOURCE_MAX_CHARS` so a
  future oversized fixture fails loudly instead of silently giving the
  probe planner more evidence than production's real cap allows.
- `snapshot_test.py`: `_make_editorial_brief_fake`'s mock had silently
  drifted behind `_call_openai_compat_api`'s real signature (missing
  `check_truncation`/`temperature` kwargs) — every call raised TypeError on
  argument binding BEFORE the fake body ran, meaning `generate_calls.json`
  had recorded `brief=None, calls=[]` for both fixtures since before this
  session, giving zero real coverage. Fixed; fixture now exercises the real
  prompt construction and schema-v2 validation end to end.

This round went through two adversarial review passes before recording the
snapshot (both caught real gaps, not style nits) — worth reading in full if
picking this back up cold, since the fixes compound: (1) `editorial_need`/
`interpretation` were being handed to the writer as trusted prose despite
being explicitly non-evidence by schema design — closed by dropping them
from `writer_prompt_block` entirely; (2) a first attempt to grounding-check
`opening_scene`/`seed_sentence` via pattern-matching
(`scan_free_prose_field`) was itself later judged unsafe to use as an
enforcement boundary (it has real false negatives) and was demoted to
diagnostic-only — the actual fix is structural (stop injecting the text);
(3) `evidence_packet_hash` had a hash-collision bug; (4) `grounding_status`
lacked a scope disclaimer; (5) the executor contract was prompt-only with
no deterministic backstop.

THIRD REVIEW ROUND (same session, after the above): found the mocked
baseline STILL had real holes even after rounds 1-2 closed the
editorial_need/interpretation and opening_scene/seed_sentence laundering
paths. Fixed before recording the final snapshot:

1. **Quote-attribution grounding** (the most important of these): the
   post-revision guard (`find_new_unsupported_specifics`) originally only
   checked that a NEW quote's TEXT appeared somewhere in source_text --
   which allowed a genuinely-real quote to be REASSIGNED to a fabricated
   speaker (source: `Jane Doe said "X"` → revision: `Deborah Antwi said
   "X"`) and pass, because the words existed even though the attribution
   didn't. Fixed: for any new quote whose text checks out, `_nearest_name`
   finds the closest named-entity candidate attributing it in the revision,
   and that name must appear within a window around the SAME quote's
   location in source_text, or the revision is rejected
   (`new_quote_misattributed`). Numbers were left as an explicitly
   documented TOKEN-level check only (not semantic) -- `"400 residents
   affected"` → `"400 people injured"` still passes, and the docstring says
   so rather than overclaiming.
2. `is_current_brief_schema` only checked `brief_schema_version == 2`,
   which a hand-edited/stale JSON could satisfy without ever having gone
   through `validate_brief`. Now also requires `grounding_scope`,
   `evidence_schema_version`, `grounding_status` in
   `validate_brief`'s own defined value set, and `source_hash`/
   `evidence_packet_hash` present as keys. `phase_probe.py`'s
   `_load_frozen_brief` additionally rebuilds the evidence packet from the
   topic's CURRENT `source_text` and asserts the frozen brief's hashes
   match it -- catching a fixture whose source_text changed since the
   brief was frozen (the Pixel-validation mixed-brief lesson, generalized).
3. The angle/cross_cite constraint and the no-source fallback both
   originally said a specific person/quote/date/number was allowed if it
   "appears in the summary/disability angle" -- re-blessing the exact
   short-summary authority whose ungrounded use caused the original
   contamination. Fixed: only the SUPPLIED SOURCE SNAPSHOT authorizes
   specificity; with no source snapshot at all, angle/cross_cite must stay
   abstract regardless of what the summary says.
4. Added `automation/executor_guard_test.py` (new, 7 checks): mocked
   integration tests proving `_opus_targeted_revision`/
   `_fable_polish_rewrite` actually CALL and ACT ON
   `find_new_unsupported_specifics`'s verdict -- not just that the pure
   detector function works in isolation. Includes the exact Phase 1.5B
   failure shape (primary rewrite fabricates a quote → rejected → Opus
   fallback ALSO fabricates a quote → rejected → untouched original
   returned).
5. Added `grounding.build_evidence_lineage` (called from `generate.py`,
   stamped onto the persisted `article_plans` row as
   `fable_brief["evidence_lineage"]`): records which stages
   (planner/writer/reviewer/executor) actually consumed this run's
   `evidence_packet`, with `None` for a stage that didn't run (e.g. no
   reviewer call on a non-Opus draft). Acceptance check for a future audit:
   `len(set(v for v in lineage.values() if v is not None)) == 1`.

FOURTH REVIEW ROUND (same session, after the above): found the writer path
still had a live analog of every hole the planner path had already closed.

1. The writer's OPENING instruction still said to draw from "the source/
   summary material above" -- summary/disability_angle were only fixed as
   non-authoritative for the PLANNER (angle/cross_cite), not for the writer
   itself, which could independently treat summary text as factual. Fixed:
   OPENING now says factual specifics come only from the supplied source
   snapshot / validated evidence blocks, explicitly not the summary.
2. **angle/cross_cite were still injected verbatim into the writer prompt**
   -- the last planner-authored free-prose channel after opening_scene/
   seed_sentence/editorial_need/interpretation were already removed. A
   grammatically valid question ("Why did the council ignore earlier
   complaints?") can assert an unsupported event with no name/quote/number
   to catch it -- structurally the same class of problem, just not yet
   fixed for this field. Fixed the same way: literal angle/cross_cite text
   no longer reaches the writer prompt at all (replaced with generic,
   code-authored structural instructions -- "write from a live unresolved
   question," "let a genuine competing position stand on its merits");
   angle/cross_cite remain on the persisted brief and as REVIEWER context
   (`_fable_editorial_review`'s brief_angle param) -- safe to keep there
   since the reviewer only judges/notes, and any notes it writes still pass
   through the executor's deterministic guard.
3. The quote-misattribution guard (added round 3) had three real weaknesses:
   only checked the FIRST occurrence of a quote in source_text
   (`source_text.find`), didn't recognize curly single quotes ('...'), and
   treated the nearest Title-Case phrase as an "attribution" with no
   requirement that an actual attribution verb (said/told/wrote/etc.) be
   nearby -- so an unrelated capitalized phrase near a quote could produce
   a false misattribution flag, or a correct attribution near a LATER
   occurrence of a repeated quote could be missed. Fixed: checks ALL
   occurrences (any one corroborating is enough), added curly-single-quote
   support, and requires `_ATTRIBUTION_VERBS_RE` near the candidate name
   before treating it as an attribution claim at all (`_nearest_name` ->
   `_nearest_attributed_name`). Still explicitly documented as heuristic,
   not full NER/coreference resolution.
4. `evidence_lineage` originally just copied one packet hash into all 4
   slots based on booleans -- proving the orchestrator DECLARED the same
   packet per stage, not that each stage's ACTUAL prompt consumed it.
   `build_evidence_lineage`'s signature changed to take 4 explicit
   caller-supplied hashes instead of computing them itself. generate.py now
   derives "planner" from `fable_brief.get("source_hash")` (read back what
   validate_brief ITSELF stamped from the packet it actually received --
   real cross-check) and "writer" only when `source_text` is confirmed to
   literally appear inside the actual constructed writer prompt string
   (real containment check) -- "reviewer"/"executor" remain declared from
   shared object identity, honestly documented as weaker than the other two
   rather than presented as uniformly strong.
5. **The single biggest test-coverage gap**: `snapshot_test.py` never
   covered the actual WRITER prompt built inside
   `_run_production_automation_locked` -- only `_fable_editorial_brief`'s
   own prompt construction. The most safety-critical text in the whole
   pipeline (what Opus/Fable actually see) had zero regression coverage,
   meaning the mocked baseline could go green while this boundary silently
   regressed. Added `automation/writer_prompt_test.py` (new, 11 checks):
   runs the real pipeline up to the writer's LLM call with a deliberately
   canary-laden mock brief (fabricated angle/opening_scene/seed_sentence/
   editorial_need/interpretation text), captures the actual prompt sent via
   a `BaseException`-based sentinel (a plain `Exception` sentinel gets
   silently swallowed by generate.py's own `except Exception` around that
   call site -- found the hard way, first attempt reported "pipeline
   completed" despite having captured the prompt), and asserts every
   canary is ABSENT while real validated evidence and the SOURCE MATERIAL
   block are PRESENT.
6. `is_current_brief_schema` proves an artifact's shape/identity is
   trustworthy, not that it's a USEFUL positive fixture -- a brief with
   `grounding_status="rejected"` is safe (bad evidence stripped) but empty.
   `_load_frozen_brief` now takes `require_grounding_status` (default
   `{"validated", "validated_with_rejections"}`) so an ordinary probe run
   requires a meaningfully grounded fixture; an adversarial negative-control
   probe can pass a broader/different set explicitly.

FIFTH REVIEW ROUND (same session; explicitly scoped to 3 targeted fixes, no
further general architecture review): confirmed round 4's writer-boundary
work was correct, then found two real regressions in the round-3/4 fixes
themselves plus one unaudited source-origin gap:

1. **evidence_lineage had regressed from packet identity to source
   identity**: the round-4 rewrite (making planner/writer independently
   re-derived) accidentally used only `source_hash` for the comparison,
   which is exactly the collapse Phase 1.6 built `evidence_packet_hash` to
   prevent (two packets can share source_text but differ in truncation/
   schema/provenance). Fixed: `evidence_lineage_entry(source_hash,
   packet_hash, verification)` now keeps BOTH identities per stage plus the
   verification strength, so source-equality and packet-identity-equality
   are separately checkable
   (`len({e["source_hash"] for e in lineage.values() if e}) <= 1` and the
   same for `packet_hash`) rather than one silently standing in for the
   other. Added a regression test proving a stage with the SAME source_hash
   but a DIFFERENT packet_hash is caught by the packet check even though
   source-equality alone would have missed it.
2. **The ordinary-probe positive-fixture gate accepted empty evidence**:
   `grounding_status in {"validated", "validated_with_rejections"}`
   legitimately includes the case where the source existed and BOTH
   `resisting_example`/`correction_moment` correctly came back `not_found`
   -- a valid brief, but not a useful POSITIVE fixture for a probe meant to
   exercise a real witness/quote through writer/reviewer/executor. Fixed:
   `_load_frozen_brief` now also requires `require_found_fields` (default:
   at least one of the two evidence fields must have
   `evidence_candidate.status == "found"`), with an explicit
   `require_found_fields=()` opt-out for negative-control probes that
   deliberately want `not_found` on both.
3. **Fallback-to-summary source text was indistinguishable from a real
   fetch** -- confirmed by direct inspection of `discovery.py`'s
   `fetch_source_article`/`get_source_text` (both return a plain
   `str | None` on every path, whether the return value came from a real
   HTML fetch+extraction or from `fallback_text` -- the ~400-char RSS
   summary -- being substituted after a failed/blocked fetch). This meant
   `generate.py`'s `source_text = self.get_source_text(url,
   fallback_text=news_seed.get("summary"))` could silently hand
   `build_evidence_packet` the SAME short, unvetted summary already shown
   separately as plain "Summary:" context, certifying it as if it were a
   genuinely fetched ~3000-char article -- reopening the exact short-
   summary-as-authority problem the rest of Phase 1.6 exists to close.
   Fixed: added `self._last_fetch_origin` (set on every return path inside
   `fetch_source_article`) and `get_source_origin(url)` (cached per-url
   alongside the text in `get_source_text`), returning
   `"fetched_article"` / `"fallback_summary"` / `"none"`. Both of
   generate.py's call sites (news_seed and discovery branches) now check
   `get_source_origin(url) == "fallback_summary"` and set `source_text =
   None` in that case -- downgrading to "no source available" rather than
   granting fallback text the same authority as a real fetch. Verified
   end-to-end (not just unit-tested) with a new `writer_prompt_test.py`
   scenario: under a mocked `fallback_summary` origin, the evidence_packet
   passed to the planner has `source_text=None`, and the captured writer
   prompt contains neither a SOURCE MATERIAL block nor the fetched-article-
   only content -- 4 new checks, all passing.

SIXTH REVIEW ROUND (same session; explicitly scoped to 3 tiny corrections
on round 5's own work, no new architecture areas): confirmed round 5's
fixes were directionally correct, then found round 5 itself had introduced
one real regression and left two loose ends.

1. `require_found_fields` (round 5) was semantically "at least ONE of
   these fields must be found," but the name reads like "all of these are
   required." Renamed to `require_any_found_fields` throughout
   `phase_probe.py` (parameter, constant `_ORDINARY_PROBE_ANY_OF_FOUND_FIELDS`,
   docstrings, error message) -- no behavior change, naming only.
2. **`source_origin` was detected (round 5) but never actually persisted**
   -- `get_source_origin()` correctly drove the `source_text = None`
   downgrade, but nothing carried the ORIGIN itself into evidence
   provenance. That meant "a fetch failed and fell back to summary" and
   "there was genuinely no source at all" became indistinguishable again
   one layer down, inside the packet -- exactly the distinction this whole
   fix exists to preserve. Fixed: `build_evidence_packet` now takes
   `source_origin` (one of `fetched_article`/`fixture`/`fallback_summary`/
   `none`), stores it on the returned packet, and includes it in
   `evidence_packet_hash` (two otherwise-empty packets with different
   origins must not hash the same). `generate.py`'s three source branches
   (news_seed, discovery, fallback-topic-list) each now capture
   `_source_origin` and pass it through -- verified end-to-end with a new
   `writer_prompt_test.py` assertion that a `fallback_summary` run's
   evidence_packet has `source_text=None` AND `source_origin==
   "fallback_summary"` (not silently "none").
3. Round 4's `evidence_lineage_entry` used a single `verification` label
   per stage, which let the writer's real source-text containment check
   appear to also authenticate `packet_hash` -- it doesn't; containment
   proves the raw text is present, not that the packet's other metadata
   (truncation flag, schema version, origin) was independently confirmed.
   Split into separate `source_verification`/`packet_verification` fields
   per lineage entry. planner is the only stage that legitimately claims
   `validator_stamped` for both (validate_brief stamps both hashes from one
   packet in one pass); writer claims `present_in_actual_prompt` for
   source_verification but `declared_shared_packet` for packet_verification;
   reviewer/executor remain `declared_shared_packet` for both.

SEVENTH REVIEW ROUND (same session; explicitly scoped to 4 implementation-
cleanup items on round 6's own work, no new architecture areas): confirmed
round 6's rename/source_origin/split-verification fixes were directionally
correct, then found round 6 had detected `source_origin` but never actually
persisted it, missed a schema-version bump the change itself required, and
left a probe/cache inconsistency.

1. `source_origin` was flowing into the evidence PACKET (round 6) but never
   onto the persisted BRIEF -- `validate_brief` stamped `source_hash`/
   `evidence_packet_hash`/`evidence_schema_version`/`source_truncated` but
   not `source_origin`. Fixed: also stamps `source_origin`,
   `source_length_chars`, `source_original_length_chars` from the packet.
   `is_current_brief_schema` now also requires `source_origin` present as a
   key (same "key presence, not truthiness" pattern as source_hash).
2. `source_origin` becoming part of the packet's canonical identity/hash
   (round 6) is exactly the kind of packaging change
   `EVIDENCE_SCHEMA_VERSION` exists to distinguish -- it had been left at 2.
   Bumped `EVIDENCE_SCHEMA_VERSION`/`BRIEF_SCHEMA_VERSION` to 3 together
   (a brief's schema version should reflect the full contract, including
   the packet shape available at validation time). Zero migration cost --
   the only pre-existing frozen fixtures are the 4 legacy ones already
   being rejected/regenerated regardless.
3. `phase_probe.py`'s `freeze_briefs()`/`_load_frozen_brief()` packet
   construction didn't pass `source_origin` at all (defaulting to `None`)
   even though production packets now carry meaningful origin provenance --
   both now pass `source_origin="fixture"` explicitly, kept consistent
   between freeze and load so the hash-identity comparison still matches.
4. `get_source_text`'s cache init (`if not hasattr(self,
   "_source_text_cache"): self._source_text_cache = {};
   self._source_origin_cache = {}`) would skip creating
   `_source_origin_cache` entirely for any instance that already had
   `_source_text_cache` set from before this Phase 1.6 addition --
   `AttributeError` waiting to happen. Split into two independent
   `hasattr` checks.

## PHASE 1.6 LIVE CONTROLS (real API calls, 2026-08-11, on trident)

All 4 real planner freezes done; 2 negative-control planner calls done; one
real code fix (round 8) landed as a direct result. Not yet done: positive
control through the FULL pipeline (writer/reviewer/executor preserving
evidence unchanged), tamper control, hostile-review control.

**Re-freeze of the 4 historically-contaminated topics under schema v3**
(`phase_probe.py --freeze-briefs --topic <x> --force`, one at a time,
inspected individually before proceeding to the next):

| Topic | Grounding | Validator rescue | Historical fabrication recurrence | Role fidelity |
|---|---|---|---|---|
| sauna | PASS | none | none | weak/plausible |
| hiring_tool | PASS | none | none | plausible |
| curb_cuts | PASS | none | none (worst historical case: "Deborah Antwi" + fabricated "March 14" record both explicitly absent) | plausible/strong |
| museum_labels | PASS | none | none (Christine Sun Kim/Manchester/2021/"sound of anticipation" chain explicitly absent) | plausible |

Every `source_excerpt`/`named_person`/`direct_quote`/`dates_numbers` on all
4 briefs verified programmatically (not eyeballed) as a real verbatim
substring of its own fixture. All 4 `grounding_violations == []` (clean
planner successes, not validator rescues). Strong behavioral signal on
hiring_tool/curb_cuts specifically: both sources contain unnamed human
roles (an anonymous HR director, an anonymous transport lead), and the
planner left `named_person=""` in both cases rather than manufacturing a
named character — direct evidence the new architecture changed planner
behavior, not just that the validator cleans up afterward.

**Negative control, run 1** (isolated, `/tmp/adversarial_negative_control_result.json`
on trident, never touched the 4 production fixtures): a synthetic barren
source that happened to include an explicit sentence about the ABSENCE of
consultation/testimony. `resisting_example` → `not_found` (best case).
`correction_moment` → `found`, using that real "no consultation record"
sentence as a legitimate correction fact. Reclassified on review: this is
NOT a not_found-discipline failure — the source itself supplied a real,
usable "absence is the finding" fact, and using it is defensible editorial
behavior. Real residual finding from this run: the planner's own
UN-validated free prose (angle, interpretation) overreached beyond what the
source actually supports (angle asserted "...a schedule nobody in a chair
signed off on" — the source only says no consultation record exists, not
that no one signed off; interpretation converted "no consultation record"
into "no consultation"). Neither phrase entered a validated evidence field
or the writer prompt, so this is not a grounding-safety defect — recorded
as a live-confirmed observation that free planner prose remains
epistemically loose even when the evidence fields are disciplined. Not
acted on in code (no semantic prose validator was built or should be).

**Negative control, run 2** (isolated, `/tmp/adversarial_negative_control_result_v2.json`):
a genuinely barren 3-sentence maintenance notice (repaint, temporary
closure, resume when dry) with NO meta-statement about absence of anything.
Result: **0/2 fields returned not_found.** Both `resisting_example` and
`correction_moment` came back `found`, each using a real, verbatim,
non-fabricated sentence stretched into an editorial role it does not
actually perform (an ordinary repaint-cause sentence became a "resisting
example"; an ordinary completion-schedule sentence became a "correction
moment"). No fabrication — every excerpt is genuinely verbatim, no invented
names/dates/numbers. But `correction_moment.direct_quote` was set to
`"Work will resume when the surface is dry."` — identical to its own
`source_excerpt` — despite nobody in the source being quoted as saying it.
**This is the live bug that produced the round-8 code fix below.**

**Round 8 code fix** (the one narrow correction made in response to a live
finding, not speculative hardening): `direct_quote` previously only
required verbatim presence in `source_excerpt` — which any ordinary
narrative sentence trivially satisfies. Added
`_direct_quote_in_quotation_marks()` (`grounding.py`) requiring
`direct_quote` to sit immediately inside an actual quote-character pair in
the excerpt (position-based check, not a broad regex scan — deliberately
includes straight single quotes here, since real production sources use
British-style single-quote attribution, e.g. Dezeen's `'The project is
shaped around ambiguity,' studio founder Niko told Dezeen.`, and excluding
that punctuation style would have broken all 4 real freezes above). New
reason_code `direct_quote_not_in_quotation_marks`. Re-validating the exact
captured raw planner output from negative-control run 2 through the fixed
validator now correctly downgrades `correction_moment` to
`grounding_status="validated_with_rejections"` with that reason recorded —
confirmed before landing the fix, not assumed. Added a matching planner
prompt clarification (`llm.py`): `direct_quote` must be text the source
actually presents as quoted speech/writing, not merely a reproducible
sentence; and status should be `not_found` rather than stretching an
ordinary source fact into a correction/resisting role it doesn't actually
perform. **Claim precision, corrected on review**: the deterministic check
proves quotation-MARK SYNTAX and verbatim provenance only — it does NOT
prove speaker attribution or that the quoted text is genuinely someone's
testimony (`The artwork is titled "No Exit."` would pass the mechanical
check just as validly as real reported speech). `grounding.py`'s docstring
and rejection message were written to say exactly that, not more — the
planner prompt (a judgment instruction to the model, not a claim about what
the deterministic layer proves) still asks Fable to reserve direct_quote
for actual speech/writing. 6 new regression tests added (the exact live
case, a British-single-quote non-regression check, a possessive-apostrophe
false-positive check) — 149 grounding_test.py checks total. Did NOT build a
semantic validator for correction_moment/resisting_example role-fidelity
(explicitly rejected as "NLP theater" -- role fidelity remains a
planner-prompt/editorial-judgment concern, not a deterministic-validator
concern).

**Round 9 code fix (validator provenance)**: the round-8 fix changed
validate_evidence_field's RULES (what counts as a valid direct_quote)
without changing EVIDENCE_SCHEMA_VERSION/BRIEF_SCHEMA_VERSION (correctly --
the packet/brief STRUCTURE didn't change). That left a real gap: the 4
schema-v3 frozen briefs (all generated before the direct_quote fix existed)
still report `brief_schema_version=3`/`evidence_schema_version=3` and
matching hashes, so nothing in their provenance could distinguish "passed
the old rules" from "passed the current rules." Added
`GROUNDING_VALIDATOR_VERSION = 2` (bumped from an implicit 1), stamped as
`grounding_validator_version` in `validate_brief()`, and required by
`is_current_brief_schema()` alongside the existing checks — a brief
validated by an older validator version is now correctly rejected even
when every schema/hash field still matches. 3 new regression tests (stamp
presence, stale-version rejection, missing-key rejection) — 152
grounding_test.py checks total.

**Offline revalidation of the 4 already-frozen briefs (no new planner/API
calls)**: each was re-run through `validate_brief()` against its EXISTING
planner output and its current fixture packet, checking three separate
things per topic (not just "did it pass"): (1) `correction_moment`/
`resisting_example`'s `editorial_need`/`evidence_candidate`/
`interpretation`, plus `angle`/`register`/`opening_shape`/`opening_scene`/
`seed_sentence`/`cross_cite`/`persona`, are all byte-identical before and
after — validator v2 must CERTIFY the existing planner result, not rewrite
it; (2) the specific real quote already confirmed during the original
freeze audit survives the new quotation-mark rule verbatim (sauna: "The
project is shaped around ambiguity"; hiring_tool: "We're not replacing
human judgment, we're focusing it"; curb_cuts: "This was a genuinely
difficult trade-off between two forms of sustainable, accessible
transport"; museum_labels: "the beginning of a relationship, not the end
of an explanation"); (3) `source_hash`/`evidence_packet_hash` unchanged,
`grounding_violations` still empty, `grounding_validator_version` now
stamped 2, `is_current_brief_schema()` true. **4/4 topics passed all three
checks** — only re-saved to disk because every check passed; the script
was written to refuse to write any topic that diverged.

**Test-harness rigor correction (found on review, applied AFTER the commit
above landed, as a re-verification not a redo)**: the first revalidation
script compared field snapshots via a shallow `dict(old_brief)` copy and
Python `==` on live nested-dict references -- correct only if
`validate_brief()` never mutates a nested `correction_moment`/
`resisting_example` dict in place. Direct inspection of
`validate_evidence_field` confirms it doesn't (every code path either
returns the SAME object unchanged or a brand-new `_empty_candidate()`,
never an in-place `field[key] = ...` write) -- but the test itself
shouldn't rely on that as an unverified assumption. Re-ran the exact same
4-topic comparison against the pristine pre-migration backups using
`copy.deepcopy()` on the input and canonical (`sort_keys=True`) JSON
serialization for the before/after comparison, immune to in-place mutation
regardless of what `validate_brief` does internally, now or later. **All
4 topics reconfirmed clean** under the mutation-proof method -- identical
result to the original run, so the already-committed migration (`df50809`)
did not need to be redone, only re-verified with a trustworthy method.
Terminology,
precise: the ORIGINAL frozen briefs (produced before this fix existed)
never contained a `grounding_validator_version` field at all -- calling
them "validator v1" would imply a version number that was never actually
stored. They're accurately described as pre-versioning / effectively
validated under the original (single) rule set, not literally "v1". The
REVALIDATED briefs now on disk carry `brief_schema_version=3`,
`grounding_validator_version=2`, identical planner output, identical
hashes — a legitimate deterministic fixture migration, not regeneration.

**Experimental interpretation, stated plainly**: source grounding is
necessary but not sufficient for something to be a CripMinds contribution.
Negative-control run 2 demonstrated this cleanly — the system was fully
factually grounded (every excerpt verbatim, zero fabrication) while still
trying too hard to manufacture editorial significance out of a source that
had none to give. Grounding safety and editorial worth are different axes;
Phase 1.6 only ever claimed to guarantee the first.

**Editorial doctrine note (NOT a Phase 1.6 code change, not yet in the
production prompt)**: the live negative controls surfaced a question bigger
than grounding safety — CripMinds' premise should not become "every source
must yield a disability insight if pushed hard enough" (that would make the
disability lens a stylistic overlay on arbitrary news, the opposite of the
project's actual purpose — see `project_cripminds_true_purpose.md`). The
proposed higher-order commissioning question, to live in the editorial
constitution (not a giant prompt rule) once Phase 1.6 is fully landed:
**"What does this disabled way of perceiving make knowable about the
subject that the dominant framing misses?"** — not "what's the disability
angle," not "how are disabled people affected." If Fable cannot answer that
concretely from the material, the article probably shouldn't be
commissioned. Ties directly to the "terugeisen" (reclaiming) framing:
CripMinds recovers knowledge treated as peripheral, rather than translating
disabled experience outward for a non-disabled audience. Deliberately not
implemented now — this is a scope note for after Phase 1.6, not something
to fold into this phase's prompt surgery.

STILL OUTSTANDING before this phase can be called fully done:

- Positive control through the FULL live pipeline (not just the planner
  stage) — a source with an unmistakable named witness + exact quotation,
  confirming writer/reviewer/executor preserve it unchanged end-to-end. The
  4 freezes above already prove the PLANNER extracts real evidence
  correctly; the full-pipeline chain (writer receives it, reviewer doesn't
  demand more, executor doesn't mutate attribution) hasn't been exercised
  live yet.
- Tamper control: take a valid found candidate and alter excerpt/name/
  quote/number — confirm deterministic rejection and that unsafe material
  never reaches the writer.
- Hostile-review control: a reviewer instruction that explicitly asks for a
  quote the source doesn't contain — confirm the executor refuses, and if
  the model nevertheless invents one, confirm the post-revision guard
  (`find_new_unsupported_specifics`) actually rejects it in a REAL run (only
  mocked so far, in `executor_guard_test.py`).
- A small real production confirmation run, only after the above are green.
- `_EXECUTOR_CONTRACT`/`find_new_unsupported_specifics` (including the new
  attribution check) have not been exercised against a REAL model response
  yet — only unit-tested with synthetic before/after text and mocked LLM
  output (`executor_guard_test.py`).
- The attribution-grounding check (`_nearest_attributed_name`) is a
  nearest-candidate heuristic, not general entity resolution -- a name
  spelled differently from the source, or a quote attributed to an unnamed
  reference ("a resident said..."), isn't checked either way. Worth
  watching real-run false-positive/negative rates once real API calls
  resume.
- **Product-level flag, not just a safety fix**: round 4 item 2 removed
  literal angle/cross_cite injection from the writer prompt entirely,
  replacing Fable's story-specific investigative question with a generic
  code-authored "write from an unresolved question" instruction. This is
  architecturally consistent with removing opening_scene/seed_sentence
  (same laundering-path logic), but it does change what "BRIEF A QUESTION,
  NOT A VERDICT" (the centerpiece of Phase 1 WHY WE WRITE) actually hands
  the writer -- previously a specific, planner-crafted question; now a
  generic reminder plus the validated evidence blocks. Implemented per
  explicit reviewer instruction this session, but flagging here because it
  touches the exact mechanism Phase 1's own experiment validated and the
  FROZEN DECISIONS section is protective of. Worth a deliberate quality
  check (does article-quality/specificity suffer without the planner's own
  question reaching the writer?) once real generations resume, not just an
  assumption that removing the injection was strictly an improvement.
- `writer_prompt_test.py`'s mocked writer-prompt capture only exercises ONE
  topic/persona/register combination (Maya Flux/wry, the sauna-adjacent
  fixture) -- it proves the boundary CAN be captured and asserted on, not
  that every persona/register/article-type combination is equally clean.

## PHASE 1.6 CONTINUATION — PERSONA FACTUAL CONTEXT, SECOND CORRECTION (2026-08-11, third session)

The prior session (documented above) added `persona_factual_context` and
`scan_draft_for_unsupported_specifics` to catch the live Rotterdam/March-
2024 fabrication, but got interrupted before landing and, on inspection
this session, had one real architectural bug: `generate.py` built
`persona_factual_context` from `agent_info['prompt_block'] + _canon` --
i.e. the ENTIRE persona voice/engine brief and canon file, the exact
anti-pattern the mechanism exists to prevent (canon mixes personality,
perceptual engine, voice rules, interpretation and hypothesis with any
real biography; "it's already in canon" is not evidence a first-person
claim is real). Confirmed compiling and all tests passing before this
correction (172+ checks across `grounding_test.py`/`executor_guard_test.py`/
`writer_prompt_test.py`) -- the interrupted work was functionally intact,
just conceptually wrong.

**The fix — two separately-sourced layers, not one file split into two
readings:**

1. `LLMMixin._load_persona_factual_context(agent_name)` (`llm.py`): reads
   a NEW file, `persona_canon/<slug>-factual.md` (separate from
   `<slug>.md`, the existing canon file `_load_persona_canon` reads), and
   returns ONLY the text under `## AUTHORIZED FACTUAL CONTEXT` -- a later
   `## PENDING VERIFICATION` heading, if present, is structurally excluded
   from what's returned (same heading-scoped extraction pattern
   `_extract_persona_wound` already used for `## THE WOUND`). Returns `''`
   for any persona without this file -- fail-closed: an empty
   `persona_factual_context` makes the reviewer/writer prompts both treat
   "no basis to accept any first-person experience claim" as the default,
   not a silent fallback to canon.
2. `generate.py` now calls `self._load_persona_factual_context(agent_name)`
   instead of concatenating `prompt_block` + `_canon`.

**Pixel Nova specifically** (the only persona with real-world grounding;
Maya Flux/Siri Sage/Zen Circuit are fully fictional and untouched this
session -- they now get an empty, fail-closed `persona_factual_context`
until/unless someone builds a `-factual.md` for them, which is correct,
not a regression):

- `persona_canon/pixel-nova-factual.md` (new): `## AUTHORIZED FACTUAL
  CONTEXT` built ONLY from material with direct-quotation or
  strongly-supported backing in the 2026-08-11 evidence audit of the
  supplied `jascha-dna` archive (`~/code/trident/deaf-persona-evidence-
  audit.md` -- one of the two evidence audits referenced this session;
  the second was not locally available to this session, so this file
  reflects the one audit actually inspected, cross-checked against
  Jascha's own corrections in-thread). Covers: NGT as mother tongue,
  Rietveld interpreter experience and translation-lag ("other time zone",
  laughing late at a joke), *De Gebarentaaltolk en Ik*'s actual
  translation/back-translation/synchronization structure, *Retrieve My
  Time*'s blinking/time mechanic, Deaf Village/temporary-belonging
  material, sequential-vs-simultaneous presentation, video/GIF as a
  representation medium, and a real telephone-only-service access
  problem. **Correction (see the fourth-session section below): this
  bullet originally also claimed the notary/legal-deed anecdote as
  AUTHORIZED, "re-verified against `03-WORKS.md`." That citation was
  fabricated by this session, not found -- a direct `grep -i notary`
  against the actual evidence audit returns nothing; the anecdote's only
  real source in this repo is the retired fictional canon. Moved to
  PENDING VERIFICATION.** `## PENDING VERIFICATION` (hearing parents, a
  Deaf brother, detailed schooling history, vibration memory, Gallaudet,
  generalized face-reading claims, museum-guide work, other named
  Deaf-led spaces beyond L'Altro Spazio, and now the notary anecdote) is
  excluded from the extraction by construction, not by convention.
- `persona_canon/pixel-nova.md` rebuilt from a fictional-character
  biography (female Pixel, born Amsterdam 1987, Jordaan→Bijlmer, a
  typesetter father, Rietveld/KABK, Brooklyn 2011, an invented museum/
  Rothko wound) into a compact editorial/personality architecture: CORE
  PERSON, FORMATIVE TENSION (not one cinematic wound -- delay/translation/
  sequence as a recurring structural condition), PERCEPTUAL ENGINE
  (THING → TRANSMISSION/MEDIATION → WHAT CHANGED? → HIDDEN MECHANISM),
  MOTIVE (terughalen / terugeisen), CONTRIBUTION, TEXTURE, AFFINITIES
  (explicitly soft, not owned), CORE RULE ("Deafness supplies Pixel's
  instrument, not Pixel's subject list" -- accessibility/wayfinding/
  interpreters/policy are not Pixel's beat), RISK. No heading named
  `## THE WOUND` remains, so `_extract_persona_wound` now correctly
  returns `''` for Pixel -- already handled gracefully by existing
  conditional code, not a new failure mode.
- `personas.py`'s Pixel `prompt_block` (the writer-facing generation-time
  brief, separate from and previously containing the SAME class of
  problem as the canon file: a "YOUR LIFE" paragraph with the fire-alarm
  origin, the museum/Rothko wound, and invented habit details) rewritten
  to match: kept the intellectual-formation references (Flusser, Stokoe,
  Neurath, Christine Sun Kim, Lentz/Valli, Deaf West -- interpretive/
  engine material, not biographical claims), replaced the obsession
  list's hard-ownership framing ("information architecture that reveals
  or conceals power," "wayfinding systems and who they fail") with the
  mediation/timing engine and an explicit "NOT your beat" line, and
  replaced "YOUR LIFE" with only the interpreter-lag material the new
  factual file actually authorizes plus an explicit prohibition on
  inventing new episodes.

**Verification, not just claimed:**
- All pre-existing suites still pass unchanged after the rewrite:
  `grounding_test.py` (all checks), `executor_guard_test.py` (7/7),
  `writer_prompt_test.py` (all checks).
- Reclassified the exact captured downstream scenario through
  `scan_draft_for_unsupported_specifics` using the NEW factual corpus
  (source_text + `pixel-nova-factual.md`'s AUTHORIZED section only):
  Rossi's real quote -- PASS (unflagged); "12 signs" -- PASS (unflagged);
  the fabricated "In March 2024 I sat through a wayfinding review for a
  Rotterdam civic building" episode -- FLAGGED on both the date and the
  entity signal. (The notary anecdote's classification at this point in
  the session was wrong -- see the fourth-session correction below.)

**Explicitly not done this session, corrected in the fourth-session pass
below**: Maya/Siri/Zen's empty `persona_factual_context` was originally
logged here as "a correct default, not a TODO" -- that turned out to be
wrong (see below); Siri's `personas.py` ownership sentence was logged as
"not fixed this session, per scope" -- also since fixed.

**Still true, not revisited**: the second evidence audit the user
referenced was not locally available to this session --
`pixel-nova-factual.md`'s AUTHORIZED section reflects only the one audit
actually inspected plus the user's own in-thread corrections; and
`scan_draft_for_unsupported_specifics` remains advisory-only (handed to
the reviewer as candidates, not auto-stripped or fail-closed at
publication).

## PHASE 1.6 CONTINUATION — FOURTH-SESSION CORRECTIONS (2026-08-11, same day)

The third-session work above was directionally correct but had three
real defects and two provenance-wording problems, all caught by the
user's own re-audit of the actual evidence document (not by this
session's own testing, which only checked internal consistency, not
whether the cited sources actually existed).

1. **Fabricated source citation for the notary anecdote (the most
   serious).** The third session wrote "re-verified against `03-WORKS.md`"
   for the notary/legal-deed anecdote without actually re-checking it --
   `grep -i notary` against the real evidence audit
   (`~/code/trident/deaf-persona-evidence-audit.md`) returns ZERO matches.
   The anecdote's only real source anywhere in this repo is the OLD,
   retired, fully fictional `pixel-nova.md` canon's "FROM THE INTERVIEWS"
   section -- i.e. this session almost laundered exactly the kind of
   claim the whole two-layer split exists to catch, immediately after
   building the mechanism to catch it. Moved from `## AUTHORIZED FACTUAL
   CONTEXT` to `## PENDING VERIFICATION` in `pixel-nova-factual.md`, with
   an explicit note not to re-add it on "sounds consistent with Pixel's
   themes" reasoning -- it needs an actual primary-source passage (a
   specific line in `03-WORKS.md` or the interview transcript) first.
2. **Empty `persona_factual_context` was globally fail-closed, which
   broke Maya Flux/Siri Sage/Zen Circuit.** The reviewer's first-person
   contract treats an empty context as "no basis to accept ANY
   first-person experience claim" -- correct for Pixel (whose context is
   now strictly real-evidence-only) but wrong for the three fully
   fictional personas, who have editorially authorized wounds/histories
   (Maya's wedding-steps wound, Siri's roommate/pool routine, Zen's
   dinner-party wound) that were never invented DURING article
   generation -- they were authored once, deliberately, as the
   character. Fixed with a `provenance_mode` field
   (`grounding.PERSONA_PROVENANCE_HUMAN_EVIDENCE` /
   `_EDITORIAL_CANON`): `LLMMixin._load_persona_factual_context()` now
   returns `(text, provenance_mode)`; Pixel gets her strict
   `-factual.md` (`human_evidence`); any persona WITHOUT a `-factual.md`
   falls back to `_load_persona_canon()` in full (`editorial_canon`) --
   restoring pre-regression reviewer behavior for the three fictional
   personas. `_fable_editorial_review`'s first-person contract now
   phrases its instruction differently per mode (human-evidence-verified
   vs. this-persona's-own-authorized-canon) instead of one blanket
   "you have no life" message. Verified directly (not just by re-running
   the test suite, which doesn't exercise this path): loaded all 4
   personas' factual context standalone and confirmed Pixel gets
   `human_evidence`/her real biography, and Siri/Maya/Zen get
   `editorial_canon`/their full canon with their established wound text
   intact (Siri's "I need someone who can see my face right now",
   Maya's "three steps" wedding line both present).
3. **Territory-metadata investigation, not a blind edit.** Traced every
   consumer of `personas.py`'s `categories`/`perspective` fields (an
   Explore-agent pass across all of `automation/`) before touching
   anything, per explicit instruction. Finding: neither field drives
   topic→persona ROUTING anywhere -- they're pure article-metadata/SEO-
   keyword-fallback/frontmatter text, plus one soft, LLM-advisory use in
   `llm.py`'s `_fable_editorial_brief` (persona `perspective` text shown
   to Fable as descriptive context for its own holistic "most alive
   voice" judgment, explicitly instructed to weigh "not just topic
   match"). The REAL hard routing lives in two places that don't
   reference `personas.py` at all: `discovery.py`'s `_THEME_TO_PERSONA`
   dict (the dominant news-seed path) and a domain-keyword if/elif chain
   in `generate.py` (~line 203). **Both were deliberately left untouched
   this session** -- `_THEME_TO_PERSONA` currently sends `space_cosmos`,
   `technology`, `science_nature`, `philosophy`, and `behavioral_science`
   to Zen Circuit, not Pixel Nova, meaning Pixel structurally will not
   get astronomy/AI/science/philosophy news-seed stories by default today
   regardless of how her prompt reads -- this is real topic gravity, just
   implemented by a different mechanism than the one asked about, and
   redistributing it is a 4-persona-wide decision (this repo's own FROZEN
   DECISIONS already calls persona-territory rearchitecture Phase 3, not
   started) -- NOT a "clean up Pixel's stale labels" fix. Flagging here
   as a live, confirmed, unresolved constraint on the new engine's actual
   reach, not a TODO quietly deferred. What WAS changed, confirmed safe
   by the trace above: Pixel's `categories`/`perspective` in
   `personas.py` updated to match the new engine (was purely cosmetic --
   article frontmatter `category:` tag and the one soft Fable-advisory
   signal -- confirmed zero effect on routing before touching); and
   Siri Sage's `personas.py` VOICE ANCHOR text, which explicitly said
   spatial legibility/wayfinding/information architecture "belong to
   Pixel Nova," rewritten to drop the ownership claim while keeping
   Siri's own acoustic-instrument differentiation -- this one direct
   textual contradiction of Pixel's new CORE RULE, closed as instructed.
4. **"Formed by Flusser/Stokoe/Christine Sun Kim" is itself a
   biographical claim** -- "formed by X" asserts Pixel/Jascha actually
   studied or was intellectually shaped by these thinkers, which the
   evidence doesn't establish. Relabeled in `personas.py`'s prompt_block
   as a "CONCEPTUAL REFERENCE LIBRARY -- tools available to you when
   genuinely relevant, not a claim that you personally studied, met, or
   were formed by them unless your factual context says otherwise."
5. **False provenance claim in code comments.**
   `_load_persona_factual_context`'s docstring said
   `pixel-nova-factual.md` was "curated by a human, not generated" --
   false; this session generated it from the evidence audit, Jascha has
   not reviewed/approved it line-by-line. Corrected the docstring and
   added an explicit provenance note at the top of
   `pixel-nova-factual.md` itself: "drafted by Claude from the evidence
   audit cited below, not authored or line-by-line approved by Jascha
   yet... a curated draft artifact subject to his review, not a
   human-verified source in its own right."

**Verification after all five fixes:** `grounding_test.py`,
`executor_guard_test.py`, `writer_prompt_test.py` all still pass
unchanged. `snapshot_test.py --check` correctly detected drift in
`_fable_editorial_brief`'s recorded prompt (Pixel's `perspective` string
changed, which is embedded in the planner prompt's persona list) --
confirmed the diff was exactly that one line across both fixtures (2
insertions/2 deletions total, `git diff --stat`), then re-recorded with
`--record`. Reclassification re-run against the corrected
`pixel-nova-factual.md`: Rossi/12-signs still pass, Rotterdam/2024 still
flagged; the notary anecdote produces no deterministic-scanner signal
either way (no quote/name/number pattern in that sentence for
`scan_draft_for_unsupported_specifics` to catch, PENDING VERIFICATION or
not -- consistent with that scanner's documented limitations) -- its
actual enforcement point is the reviewer's judgment-based first-person
contract, which now correctly has no AUTHORIZED text to point to for it.

## PHASE 1.6 CONTINUATION — FIFTH-SESSION CORRECTIONS: THE WRITER BOUNDARY BUG (2026-08-11, same day)

The fourth-session pass fixed the reviewer/scanner side correctly but
missed the single most important consumer: the writer itself. Found by
the user re-reading the actual generate.py diff, not by this session's
own tests -- writer_prompt_test.py existed and ran clean the whole time,
because it never asserted on this specific text.

**The bug, confirmed by direct trace before touching anything (per
instruction):** `persona_factual_context` (built from
`_load_persona_factual_context`) was passed to the reviewer
(`_fable_editorial_review`) and the raw-draft scanner
(`scan_draft_for_unsupported_specifics`, post-writer) -- but NEVER
inserted into the writer's own prompt. The writer prompt's "PERSONA
FACTUAL CONTEXT BOUNDARY" instruction still said "your CANON above is
the complete set of events, testimony, and documented facts you are
authorized to claim as your own lived history" -- referring to `_canon`
(the full `_canon_block`, unrelated to the new split), not
`persona_factual_context` at all. Confirmed by grep: every read of
`persona_factual_context` in `generate.py` was at the raw-draft-guard
call site (post-writer) and the reviewer call site -- zero reads before
or during `prompt` construction. Result: reviewer/scanner correctly saw
Pixel's real, curated biography; the writer that actually generates the
first-person prose was told its factual authority was the ENTIRE
editorial canon (engine, motive, texture, reference library,
interpretations) -- almost exactly the mistake the whole two-layer split
exists to prevent, just relocated one stage earlier.

**Fix:** Replaced the boundary instruction with an explicit
`--- AUTHORIZED PERSONAL HISTORY ---` / `--- END AUTHORIZED PERSONAL
HISTORY ---` block built from `_persona_factual_text` itself (the same
variable already computed for `persona_factual_context`, just never
written into `prompt`). New instruction text: canon governs voice/
engine/worldview and does NOT authorize autobiographical facts; the
AUTHORIZED PERSONAL HISTORY block (phrased differently for
`real_person_evidence` vs `editorial_canon` -- see rename below) is the
ONLY persona material authorizing a first-person claim; the source
material may additionally authorize article-specific facts;
interpretation/argument/metaphor/present-tense perception remain always
free to invent. For Pixel this block is ONLY her `-factual.md`'s
AUTHORIZED section (PENDING VERIFICATION structurally cannot reach it,
same extraction mechanism as before); for the three fictional personas
it's their own canon under `editorial_canon`, per the fourth-session
fix -- the conceptual separation is now visible to the writer for every
persona, not just enforced downstream of it.

**New regression, not just a unit test of the loader** (per explicit
instruction): added `test_pixel_persona_factual_boundary()` to
`writer_prompt_test.py`, capturing the REAL Pixel Nova writer prompt
(persona_canon/pixel-nova*.md read from disk, unpatched -- only
`_capture_writer_prompt` gained a `persona_name`/`register_name`
parameter, defaulting to the existing Maya Flux/wry fixture so every
prior assertion is unchanged). Proves: authorized interpreter/time-zone
material present ("another time zone", "Gerrit Rietveld Academie");
`AUTHORIZED PERSONAL HISTORY` heading present; real story source evidence
still present (Priya Nathan/Dana Ruiz); `PENDING VERIFICATION` heading
absent; "notary" absent (case-insensitive) anywhere in the prompt; the
old "CANON above is the complete set of" sentence gone; and the editorial
canon (perceptual engine/motive/reference library) is still present and
distinct from the factual block, not replaced by it. All 8 new checks
pass; all prior `writer_prompt_test.py` checks unaffected (unchanged
Maya Flux default path).

**Persona-factual provenance now persists, mirroring evidence_lineage but
kept SEPARATE from it (deliberately -- see
`grounding.build_persona_factual_lineage`'s docstring):** added
`grounding.persona_factual_lineage_entry()`/`build_persona_factual_lineage()`
(new, 5 unit tests) and wired both a writer entry (real containment check:
`_persona_factual_text in prompt`, computed right where the confirmed
containment bug above would have been caught immediately had this existed
sooner) and a reviewer entry (`declared_shared_context`, same-object
reasoning as evidence_lineage's reviewer/executor entries) into
`fable_brief["persona_factual_lineage"]`, persisted alongside
`fable_brief["evidence_lineage"]` via the same `_persist_article_plan`
call -- no new persistence pathway needed. No "planner" slot (persona
factual context is loaded once per run, not produced by a planner call).
**Executor slot is always `None`, explicitly, not a bug**: the executor
stages (`_opus_targeted_revision`/`_fable_polish_rewrite`) do not
currently receive `persona_factual_context` at all -- a real, separate
gap (an executor revision could reintroduce or preserve an unauthorized
first-person claim that `find_new_unsupported_specifics` wouldn't catch,
since that guard only checks against `evidence_packet`'s `source_text`)
that this session did NOT fix, per the instruction to close only the two
named gaps. Flagging it here rather than silently wiring it in.

**Renamed `PERSONA_PROVENANCE_HUMAN_EVIDENCE`/`"human_evidence"` to
`PERSONA_PROVENANCE_REAL_PERSON_EVIDENCE`/`"real_person_evidence"`**
throughout (`grounding.py`, `llm.py`, `generate.py`, comments): the old
name reads as "human-reviewed evidence," which overstates
`pixel-nova-factual.md`'s actual status (model-drafted, not yet
line-by-line approved by Jascha -- correctly stated in prose since the
fourth-session pass, but the machine-readable constant itself still
implied more than the prose claimed). Historical entries above (fourth-
session section) still say `human_evidence` -- left as-is; they're
accurate logs of what the code said AT THAT TIME, not something to
retroactively edit.

**Explicitly documented, not silently assumed equal:** `real_person_evidence`
and `editorial_canon` are different provenance CLASSES, not two labels for
equally-strong verification -- `real_person_evidence` is a strict,
evidence-audit-curated factual corpus; `editorial_canon` is an authorized
fictional world where the deterministic scanner will have more false
negatives (canon prose contains names/references/interpretation a
strict factual file wouldn't), and its actual safety property rests on
reviewer semantic judgment, not substring matching. Both the writer-
boundary instruction text and this doc now say so explicitly rather than
treating both modes as "verified" without qualification.

**Verification:** full suite re-run after all of the above --
`grounding_test.py` (new persona_factual_lineage tests included),
`executor_guard_test.py`, `writer_prompt_test.py` (new Pixel boundary
test included), `snapshot_test.py --check` -- all pass, zero drift (this
correction touches writer-prompt construction downstream of
`_fable_editorial_brief`'s own prompt, which is the only thing
snapshot_test.py's fixtures cover, so no re-recording was needed this
time).

## FROZEN DECISIONS (do not reopen by drift)
- WHY WE WRITE (commit `01339ce`) is the shared publication doctrine.
  KEEP, scope-corrected: entitled to claim "improved or preserved the four
  personas under the then-current planning architecture," NOT "works
  under the final intended CripMinds pipeline" (that architecture is now
  known to include the contamination above). Do not rerun the 12+12
  doctrine experiment — after Phase 1.6, a small smoke confirmation
  suffices (see phase-1.6 doc's closing section).
- Historical persona territories are hypotheses, not canon — target
  architecture (perceptual engine / motive / affinity / risk / texture)
  is Phase 3 work, not started. Audit: `.claude/persona-architecture-audit.md`.
- Phase 1.5A persona audit is done; implementation waits for Phase 3.
- Phase 1.5B final model-seat decision waits until after Phase 1.6
  grounding — both reviewers in that experiment judged drafts whose
  factual substrate was already contaminated by an ungrounded planner.
- Production `temperature` stays unset/`None`; only probes pin it (0.9).
- Repetition judge (Phase 5) and ending judge (Phase 7): shadow-only
  first, backtested, never auto-block/auto-rewrite until real
  false-positive data justifies it.
- `engagement.db`/`disability_findings.db` living inside the repo checkout
  remains a known, mitigated risk (safe sync wrapper + daily backups);
  moving them out is deferred infrastructure hardening.
- CJ-2 remains future competitive persona reframing ("what does each
  persona's engine expose, which reframe is strongest" — not topic
  ownership), not scheduled.
- `_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
  Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
  correction-discipline rules: do not touch until their own dedicated
  experiment.

## PAUSED EXPERIMENTS — what resumes after grounding
- **Fable review-seat ROI (Phase 1.5B)**: full 3-layer blind evaluation +
  causal safety audit done, model-seat decision deferred. Resumes as a
  small grounded review-seat follow-up once Phase 1.6 lands, not a repeat
  of the 8-case experiment. Record: `.claude/experiments/fable-review-roi-2026-08-10.md`.
- **WHY WE WRITE**: KEEP decision stands; resumes only as the small smoke
  confirmation described above. Record: `.claude/experiments/why-we-write-2026-08-10.md`.

## OPEN INFRASTRUCTURE ISSUES (not blocking Phase 1.6)
- CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
  can poison routing for ALL requests, not just its own — a `systemctl
  --user restart cliproxyapi` fixed it same-day. Still needs: remove/
  refresh the dead account, or file upstream that per-account refresh
  failures shouldn't affect other accounts.
- Real production article shipped degraded on 2026-08-10 09:03:24: Fable
  review returned `revise` but all four rewrite fallback attempts failed
  (403s/500/monthly key limits), so the article shipped unrevised and
  without images. Open question, not yet answered: was this stamped
  `pipeline_degraded` correctly, given `generate.py`'s Step 3b
  image-generation failure doesn't appear to be tracked by
  `_degraded_stages` at all — possibly undercounting the real failure
  surface. Not investigated further; check against the published
  article's frontmatter when reliability work has capacity.
- `--retry-failed` exists as general `phase_probe` infrastructure but was
  deliberately not used to patch `baseline-attempt-1` — a contiguous clean
  run was required instead, to avoid mixing external-condition windows in
  data meant to detect subtle writing differences.
- Rest of cripminds' backlog (judge-panel generation, persona evolution,
  shadow-check promotion, CJ-2, Stage B/D-E) stays in
  `.claude/audience-engagement-tasklist.md`, untouched.

## HISTORICAL RECORDS (full detail, not condensed)
- `.claude/experiments/why-we-write-2026-08-10.md` — Phase 1 WHY WE WRITE
  3-topic + Pixel Nova 4th-persona validation, full 4-persona decision.
- `.claude/experiments/fable-review-roi-2026-08-10.md` — Phase 1.5B
  harness, 8-case run, 3-layer blind evaluation, safety audit that found
  the Phase 1.6 blocking finding.
- `.claude/persona-architecture-audit.md` — Phase 1.5A six-category
  persona matrix and territory-ownership bugs.
- `.claude/2026-08-10-engagement-db-incident.md` — Phase 0's
  `engagement.db` incident, fully recovered/closed.
- `.claude/audience-engagement-tasklist.md` — rest of the backlog, untouched by this roadmap.

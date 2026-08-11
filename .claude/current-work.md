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
- **DONE — mocked/offline baseline, 7 review rounds closed, committed**
  — Phase 1.6, source-grounding hardening. Design doc:
  `.claude/phase-1.6-source-grounding.md`. Code implemented across
  `grounding.py` (new), `llm.py`, `generate.py`, `discovery.py`, `review.py`,
  `phase_probe.py`, `snapshot_test.py`, `grounding_test.py` (new),
  `executor_guard_test.py` (new), `writer_prompt_test.py` (new).
  `EVIDENCE_SCHEMA_VERSION`/`BRIEF_SCHEMA_VERSION` are now 3 (bumped from 2
  in round 7 once `source_origin` became part of the packet/brief
  contract). 143 grounding_test.py checks + 7 executor_guard_test.py checks
  + 17 writer_prompt_test.py checks pass (167 total); `snapshot_test.py
  --check` clean throughout (generate_calls.json re-recorded 3 times as
  hashing/schema changed; deterministic.json/llm_calls.json unaffected --
  note snapshot_test.py only ever covers `_fable_editorial_brief`'s own
  prompt, NOT the writer prompt built in `_run_production_automation_locked`;
  `writer_prompt_test.py` is what actually covers that boundary, added in
  round 4 after this exact gap was flagged). NO real API calls made yet —
  `phase_probe.py --freeze-briefs` (would replace the 4 legacy-contaminated
  fixtures with schema-v3 ones) and the adversarial negative/positive-control
  probes are still outstanding, and cost real tokens. See "PHASE 1.6 STATUS
  DETAIL" below before resuming — seven adversarial review passes each
  found real, non-cosmetic gaps before the mocked baseline was allowed to
  freeze; read the full list before assuming this is done.
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

STILL OUTSTANDING before this phase can be called done (none touched yet
— no real API calls have been made this session):

- `phase_probe.py --freeze-briefs --force` for all 4 topics, to replace the
  legacy-contaminated fixtures with real schema-v2 ones (costs real
  tokens). The legacy-schema gate currently makes `--run`/`--preflight`
  fail until this happens.
- Adversarial negative-control probe (source deliberately lacking a
  witness/quote/anecdote → planner must say `not_found`, reviewer must not
  demand nonexistent evidence, executor must introduce nothing) and
  positive-control probe (source genuinely contains a named witness + quote
  → validator accepts it, writer/reviewer/executor preserve it without
  mutation) — per the design doc's acceptance test and the strict test
  order's steps 5-6.
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

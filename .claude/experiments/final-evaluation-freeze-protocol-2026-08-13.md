# CRIPMINDS B2/CJ2 FINAL EXPERIMENTAL FREEZE + HELD-OUT EVALUATION PROTOCOL

**Status: PREREGISTRATION / GOVERNANCE ONLY. Written 2026-08-13. Zero model
calls made in the writing of this document. No held-out content read. No
D0/C0/R1/R2/repair-v1/admission-gate/Stage-C code touched. No RL-2026-002
partial answers inspected. No RL-2026-003 ingestion/publication.**

This document exists to answer one question honestly, before any more human
evidence or held-out results arrive and could bias the answer: **what has to
be true before this project stops tuning B2 semantics and moves to a frozen
held-out evaluation, and what happens if that evaluation goes badly?**
Everything below is a rule to be followed later, not a report of something
already done. Where evidence doesn't yet exist to fully settle a question
(Shape C in particular), that is stated explicitly rather than guessed.

Cross-reference, not a duplicate: full narrative history of every pass this
protocol depends on lives in `cj2-competitive-reframing-design-2026-08-11.md`
(sections `## B2 ZERO-SAFE BOTTLENECK ATTRIBUTION AUDIT`, `## B2
HUMAN-CALIBRATED SUPPORT-BOUNDARY AUDIT`, `## B2 SUPPORT-BOUNDARY TARGETED
CALIBRATION ROUND DESIGN`, `## B2 SHAPE-E TARGETED HUMAN-CALIBRATION ROUND
DESIGN`, `## B2 ANCHOR RESOLVER V2 STATUS-PROPAGATION COMPATIBILITY PASS`).
This document does not restate that history — only the boundaries and rules
derived from it.

---

## 0. CURRENT MATURITY (as recovered from disk, zero model calls)

**Structurally complete, apparatus side:**
- D0/C0 proposition-coverage architecture (Option B, segment-based).
- R1/R2 factuality architecture, including `R1_R2_SEMANTIC_CONFLICT`
  handling and `compute_effective_v2`.
- R2 narrow validator-guided repair (repair-v1).
- Deterministic B2→Stage-C admission gate.
- Resolver v2 (`terminal_punct_recovered`) + the just-completed status-
  propagation compatibility pass — Decision A, apparatus ready.
- Reader Lab v0 infrastructure: publication, completion-detection, research
  export, calibration orchestrator (`analyze-human-round-v1`/`v2`),
  candidate ingestion, policy-driven autonomy — all deployed and live.

**Semantic calibration remaining (the actual open question this protocol
governs):**
- **Shape A** (wholly unanchored property/fact): has strong development
  must-stay-strict anchors already (see `## 2` below) — not blocking.
- **Shape B** (adjacent-fact synthesis): one supported calibration
  hypothesis exists (H14 vs. De Hooch), RL-2026-002 is actively testing it
  — **in progress, do not inspect partial answers**.
- **Shape C** (modality/hedge hardening, H01/H07): **no human-calibration
  evidence exists at all** — see `## 5` for the reasoned answer on whether
  this blocks freeze.
- **Shape E** (single-fact/partial-anchor mechanism elaboration): RL-2026-003
  is designed, hashed, frozen locally — **not ingested, not published**.
- **Shape F** (D0 structural span-resolution failure, H06/H15): not a Reader
  Lab question at all — H06 is a permanent must-fail apparatus regression
  case, H15 was fixed at the resolver layer (terminal-punct recovery), not
  a semantic B2 question. Out of scope for this protocol's semantic-freeze
  gate.

No B2/CJ-1/CJ-2 semantic revision has occurred since the audit that
produced the Shape-B hypothesis. B2's currently-live semantic contract is
unchanged from before RL-2026-001 was even published.

---

## 1. HELD-OUT MATERIAL: DOES IT EXIST? (metadata only, no content read)

**Finding: no held-out corpus currently exists anywhere in this repository.**

Checked exhaustively, without reading any candidate/source text:
- Every `"dataset_purpose"` key found anywhere in the repo (probe fixtures,
  Reader Lab drafts, calibration candidates/research-context, handoff
  artifacts — see file list below) has the value `"development"`. Zero
  occurrences of `"held_out_evaluation"` or `"blind_calibration"` as an
  actual stored value anywhere.
- Every mention of `held_out_evaluation` in code
  (`calibrationWorkflow.js`, `candidateIngestion.js`,
  `prepare-next-round-v1.md`) is a **fail-closed guard** — code that
  refuses to admit such material into `calibration_candidates` — not a
  reference to an actual stored dataset. The guard has never fired because
  no candidate has ever carried that purpose value.
- Every mention of "cross-publisher" material in `current-work.md` /
  the experiment doc is either (a) a negative confirmation ("no
  cross-publisher/held-out material [used/collected]"), or (b) a reference
  to the **preregistered, design-only** "cross-publisher sampling
  protocol" (`.claude/current-work.md` line ~1592) — explicitly "NOT
  EXECUTED... no new source collection."
- One historical reclassification is on record and matters for the
  leakage rule below: at one point 18 "fresh-batch-1" candidates were
  provisionally treated as held-out, then were **explicitly, permanently
  reclassified to development/regression material** once they were used to
  diagnose a v1.2 overcorrection failure (`current-work.md` line 1591:
  "both the 12-candidate dev set AND the 18 fresh-batch candidates are now
  explicitly development/regression material, no longer held-out"). This
  is the project's own precedent for the burn rule in `## 9`.

Files consulted for this finding (metadata/keys only, no candidate text
read): every `dataset_purpose` key across
`automation/.probe_fixtures/**/*.json`, `calibration/candidates/*.json`,
`calibration/research-context/*.json`, `reader-lab/rounds/drafts/*.json`,
`.claude/reader-lab-handoff/*.json`.

**Consequence: a real held-out corpus does not need to be protected from
this pass because it does not exist yet.** It must be **freshly collected**
after semantic freeze, via the already-designed cross-publisher sampling
protocol, from sources not already spent as development or Reader Lab
material. This is stated explicitly in `## 8` (held-out contract) — the
held-out set is a future collection event, not a current asset.

If a reader of this document later locates or creates a candidate corpus
before it's tagged `dataset_purpose`, the correct action is to tag it
immediately and re-run this metadata check before any inspection —
never to read it "just to see what it is."

---

## 2. DEVELOPMENT / EVALUATION / READER-LAB BOUNDARIES

Three non-overlapping pools, stated so future leakage is structurally
harder, not just procedurally discouraged.

### DEVELOPMENT MATERIAL (safe to read, tune against, regression-test)
- **B2/Stage-C development corpora already spent:** the 14-item
  `cj2-b2-stage-c-first-integrated-development-probe` corpus (H01, H02,
  H03, H04, H06, H07, H09, H10, H11, H12, H13, H15, H16, H18); the 9-item
  `cj2-b2-r2-integrated-repair-recheck` set; the 18-item
  `cj2-b2-v2-r2-recovery` set (includes the original reference-probe Cave
  DNA / AI-Cheating-Exam / De Hooch candidates); the `cj2-reference-probe-1`
  corpus (`01_cave_dna`, `07_ai_cheating_exam`).
- **CJ-1-track development/regression material** (a separate leakage
  boundary from the B2/Stage-C corpora above — different track, same
  discipline): the 12-candidate CJ-1 dev set; the 18-candidate
  `cj2-fresh-batch-1` set (explicitly reclassified from held-out to
  development, `## 1` above) — both are permanently spent, never eligible
  to be treated as held-out again.
- **Reserved anti-overcorrection / must-stay-strict cases** (Shape A,
  explicitly NOT to be spent on Reader Lab, kept as a standing regression
  check): H03/c7, H03/c9, H09/c10, H10/c1 — clean, wholly-unanchored
  claims used to verify a future revision doesn't accidentally loosen
  Shape A while fixing Shape B/C/E.
- **RL-2026-003's draft candidates**, once RL-2026-003 is eventually
  ingested/published/completed, become development/calibration material
  (see the Reader Lab leakage rule, `## 13`) — until then they are frozen
  Reader Lab material, not yet spent, not development.
- **No Shape-C candidate pool exists yet.** H01/H07 are known to contain
  Shape-C instances (development corpus, already read/tagged by the
  bottleneck-attribution audit), but no round-shaped candidate extraction
  has been done — this is the central fact behind the `## 5` answer.

### HELD-OUT / BLIND MATERIAL (identity/count only — see `## 1`)
- **Does not exist yet.** Zero files, zero rows, zero `dataset_purpose`
  values anywhere in the repo currently carry a held-out/blind marker.
  Nothing to protect from reading because nothing is there. Future
  collection must happen only after semantic freeze (`## 8`).

### READER LAB MATERIAL
- **RL-2026-001**: COMPLETE, analyzed. 5 items (H08, H17, H14, H05, De
  Hooch/Z control). Both reviewers 5/5. Now spent — informs calibration,
  cannot become held-out again (`## 13`).
- **RL-2026-002**: ACTIVE. 5 items (2 `ADJACENT_FACT_SYNTHESIS`: H04/c10,
  H12/c6; 2 `UNANCHORED_PROPERTY` contrast: H11/c6, `01_cave_dna/S`/c8; 1
  control: H16/c4). **Partial answers not inspected by this pass, per
  standing instruction — this protocol does not know and does not ask how
  many of RL-2026-002's 5 have been answered.**
- **RL-2026-003**: designed, hashed, frozen locally only. 5 items (3
  Shape E: AI-Cheating-Exam/c13, H13/c11, H02/c17; 1 Shape-A contrast:
  H03/c14 — fresh, not one of the 4 reserved anti-overcorrection cases
  above; 1 control: H18/c2). **Not ingested. Not published.** Ingestion
  readiness was previously confirmed by code inspection
  (`reconcileStuckCalibrationRuns` would not auto-resume it) but was
  deliberately not relied upon — still sitting fully inert.

---

## 3. THE SEMANTIC FREEZE POINT

**Definition of SEMANTIC CHANGE** (anything in this list requires the
consolidated-revision discipline in `## 14`, is forbidden after freeze
except under `## 9`'s narrow held-out-burn exception):
- D0 prompt or its semantic contract (what counts as a claim, a
  non-propositional item, a segment boundary rule).
- C0 prompt or its semantic contract (what counts as adequate coverage).
- R1 prompt or role logic (`empirical_dependency`, `world_truth_question`,
  `concrete_restatement`).
- R2 support/declaration logic (`causality_hardening`, `mechanism_invention`,
  `modality_hardening`, the SUPPORT test itself, `R1_R2_SEMANTIC_CONFLICT`
  resolution).
- repair-v1's semantic behavior (what it is allowed to repair toward, not
  its retry/transport mechanics).
- B2's terminal-state mapping (`compute_effective_v2`, `EFFECTIVE_VERDICT_*`
  thresholds).
- Stage C's semantic prompt, hard gates, or scoring/comparator logic.
- Candidate-selection semantics, if and only if the selection criterion
  itself could affect which candidates ever reach evaluation (e.g.
  changing what counts as `eligible_for_reader_lab`, or which skip reasons
  exist) — cosmetic candidate bookkeeping is not included.

**Distinguished from EXECUTION-APPARATUS FIXES** (allowed at any time,
including after freeze, under the narrow condition stated below):
- Transport/auth (API client, provider outage handling, retries).
- Deterministic parser bugs (schema-shape handling, JSON extraction).
- Provenance/resolver bugs (exactly the class the last pass fixed —
  `resolve_anchor`, `is_resolved_anchor`, span-offset computation).
- Logging, hashing, provenance recording.

**Are apparatus fixes allowed after freeze?** Yes, under an extremely
narrow condition: the fix must be provably behavior-preserving on every
already-recorded development/Reader-Lab result (the same "48 files, 1,123
spans, exactly 1 intentional change" discipline the resolver-v2 pass
already demonstrated), and it must not touch any of the semantic surfaces
listed above. If a fix cannot be shown to be behavior-preserving on
existing results, it is treated as a semantic change and triggers `## 9`'s
held-out-burn rule, even if the code being touched is nominally
"apparatus."

**The freeze gate itself** (each stage is a precondition for the next, not
just a sequence):

```
Human calibration sufficient (## 12 stop rule satisfied)
   -> AT MOST ONE consolidated, evidence-targeted B2 semantic revision (## 14)
   -> development regression probe #1 (## 7, all criteria met)
   -> development regression probe #2 (## 7, all criteria met, no prompt edits between #1 and #2)
   -> at least one Stage-C exit criterion met (## 6)
   -> SEMANTIC FREEZE (a named, hashed snapshot of every prompt/module/config)
   -> fresh held-out corpus collected (## 1, ## 8)
   -> held-out evaluation executed
   -> production-candidate review (## 10)
```
No stage may be skipped. No stage may be reordered without a stated reason
recorded in `current-work.md`, following this document's own convention.

---

## 4. "DONE TUNING B2" — STRUCTURAL CHECKLIST (no arbitrary percentage)

All of the following must be true before the consolidated revision in
`## 14` is even drafted:

- [ ] **Every material blocker family** driving current development
  failures (Shape A/B/C/E, per the zero-safe bottleneck audit) has one of:
  (a) human calibration evidence (Shape B has this now; Shape E pending
  RL-2026-003), (b) an explicit, recorded decision to preserve strictness
  absent evidence (candidate outcome for Shape C, per `## 5`), or (c) a
  documented unresolved status that itself blocks freeze.
- [ ] Any semantic revision drafted is **targeted** to the specific
  evidenced failure class(es) — no incidental changes bundled in.
- [ ] The 4 reserved must-stay-strict cases (H03/c7, H03/c9, H09/c10,
  H10/c1) remain correctly blocked after the revision — checked directly,
  not assumed.
- [ ] No **new** recurring factuality failure class appears in either
  development regression probe that wasn't already known before the
  revision.
- [ ] R1/R2 validators and repair remain fail-closed (a validator error or
  ambiguous state still resolves to "not resolved," never silently to
  "safe").
- [ ] C0's coverage-protection role is intact — no revision may route
  around C0 or weaken what counts as adequate coverage as a side effect of
  fixing something else.
- [ ] The revision's own preregistration (written before results are seen,
  per `## 14`) states what would count as the revision failing its
  objective.

Every box must be checkable against a specific artifact (a test result, a
hash, a preregistration file) — "it looks fine" is not a checked box.

---

## 5. SHAPE C DECISION — REQUIRED BEFORE FREEZE, OPTIONAL, OR UNDECIDED?

**Using only existing development evidence** (the zero-safe bottleneck
attribution audit, `current-work.md` lines ~708-738; no model calls, no
held-out content, no new round designed this pass):

- Shape C (modality/hedge hardening) was found in exactly 2 of the 8
  unsafe items in the 10-item eligible corpus: **H01 (2/2 of its
  unsupported claims) and H07 (2/3)** — 4 claims total out of 42
  unsupported claims audited across those 8 items. That is a real,
  independently-recurring pattern (two distinct items, not a single
  outlier), but it is the **smallest** of the three semantic families
  identified in that audit — smaller than Shape A (12/42) and much
  smaller than Shape E (22/42, the audit's own explicit next-priority
  recommendation).
- There is one piece of **historical**, not current-B2, evidence bearing
  on the risk of loosening modality-hardening strictness: an earlier B2
  iteration (`cj2-stage-b2-v1.2`, `current-work.md` lines 1997-2024)
  tightened a modality-hardening judgment and, as a direct side effect,
  flipped an unrelated clean candidate (`05_dutch_painting_soldier`/P)
  from `boundary_ambiguous` to `unsafe` — logged at the time as
  DEVELOPMENT ACCEPTANCE FAILS (overcorrection). That result concerned an
  older prompt version and is evidence about the *direction of risk*
  (tightening/loosening modality logic has caused unrelated overcorrection
  before), not about today's frozen v2 apparatus specifically — it is
  supporting context, not proof about the current system.
- No Reader Lab round has ever tested Shape C. No candidate pool for it
  has been extracted. There is zero independent-human evidence on which
  direction (if any) Shape C should move.

**Decision: OPTIONAL / CAN REMAIN STRICT before freeze.**

**Rationale:** Shape C is real but a minority contributor to the current
zero-safe bottleneck, and the project's own standing default — preserve
strictness absent calibration evidence, exactly the treatment already
given to Shape A — applies here with no evidence pushing against it. The
one relevant historical data point argues for caution around loosening
modality logic, not for loosening it. Requiring Shape-C calibration before
freeze would mean an unbounded number of Reader Lab rounds chasing every
observed pattern regardless of size, which `## 12`'s stop rule exists
specifically to prevent. This is a recommendation, not a foreclosure: if a
future audit finds Shape C's share of the *held-out* zero-safe bottleneck
is large, `## 9`'s failure-handling rule (case D, new semantic failure
class) governs what happens next — and that would burn the held-out set,
which is exactly why remaining strict now, when the cost of being wrong is
only continued strictness rather than a burned evaluation set, is the
lower-risk default.

Backlog, not scheduled: a Shape-C-specific Reader Lab round is recorded as
a possible future third round in the RL-2026-003 design doc — this
decision does not cancel that possibility, it only says it is not a
precondition for freeze.

---

## 6. STAGE C EXIT CRITERION

Stage C has never been semantically exercised on a naturally admitted real
candidate (every development probe to date has been B2-blocked, 0/14
across the completed Stage-C probe). Minimum evidence required before
semantic freeze:

- At least one naturally-occurring real development candidate reaches
  `EFFECTIVE_VERDICT_SAFE` **without any candidate-selection intervention**
  (not hand-picked to be safe, not a synthetic/placeholder input — a real
  D0→C0→R1→R2→repair pipeline run that happens to clear).
- The admission gate routes it to Stage C automatically, via the same
  deterministic gate every other candidate goes through.
- Stage C receives it **exactly once** (no accidental double-invocation,
  checked directly against logs/call counts).
- Stage C's output is mechanically valid (schema-conformant, no parser
  failure).
- Stage C's hard gates and comparator logic execute and produce a result
  (not a crash, not a silent no-op).
- No B2-blocked candidate reaches Stage C during the same run (a negative
  check, not just a positive one).

**Is one real admission sufficient, or are two qualitatively different
admissions needed?**

**Two qualitatively different admissions are required.** Rationale: a
single natural admission only proves Stage C's plumbing works for one
shape of input — it cannot distinguish "Stage C works" from "Stage C
happened to work on the one candidate that reached it." "Qualitatively
different" means differing on at least one axis Stage C's own hard
gates/comparator are sensitive to (e.g., different `resisting_detail`
shape, different claim-count/structure, or arising from a different
semantic family than the first). This is not a large-sample statistical
target — it is the minimum needed to exercise more than one code path
through Stage C's gates, consistent with this protocol's general rule
against inventing sample sizes without evidence (`## 7`, `## 4`). If
natural admissions remain scarce even after the consolidated revision,
that scarcity is itself evidence to record, not a reason to synthesize an
admission artificially — see `## 9`, case F, for what happens if this
extends into held-out evaluation.

---

## 7. DEVELOPMENT STABILITY REQUIREMENT — "TWO STABLE PROBES," FORMALIZED

A development probe counts as **stable** iff ALL of the following hold,
checked directly against its own recorded results (not asserted):

- **No configuration failure**: no auth/transport/schema-shape error that
  invalidates any call in the run.
- **No new structural failure class**: every D0/C0 structural failure
  observed already matches a previously-documented failure shape (Shape
  A/B/C/E/F as currently understood, or the specific class the
  consolidated revision targeted) — a genuinely novel failure shape
  breaks stability and must be triaged before the second probe counts.
- **No unexpected validator failure class**: R1/R2 validator errors, if
  any, are all already-known shapes.
- **No unsafe admission**: nothing reaches `EFFECTIVE_VERDICT_SAFE` that
  an independent read of its source would call unsupported (this is a
  human-in-the-loop spot check, not automatable away).
- **Anti-overcorrection set preserved**: all 4 reserved must-stay-strict
  cases (`## 2`) still resolve `unsupported`/blocked, checked explicitly.
- **Natural safe candidates handled consistently**: if any candidate
  reaches Stage C in this probe, its handling matches `## 6`'s exit
  criterion behavior (not a one-off fluke that the second probe
  contradicts).
- **No post-result prompt edits between probe #1 and probe #2** — the
  exact prompt/module/config hashes used for #1 must be identical to
  those used for #2 (hash-verified, not assumed). If any hash differs,
  the "two stable probes" counter resets to zero; that would itself be an
  undeclared semantic change and is forbidden by `## 14`.

Both probes must be run with the same discipline as every prior probe in
this project: a written preregistration before execution, hash-recorded
inputs, no selective rerun of individual items after seeing results.

---

## 8. HELD-OUT EVALUATION CONTRACT

**INPUT**: a frozen held-out corpus, collected fresh (`## 1`) via the
already-designed cross-publisher sampling protocol, after semantic freeze
— never material already spent as development or Reader Lab content
(`## 13`).

**FROZEN SYSTEM**: exact prompt text, module source, and config for every
component (D0, C0, R1, R2, repair-v1, admission gate, Stage C, the
resolver), each recorded by hash at the moment of freeze — the same
apparatus-record discipline already used for the resolver-v2 compatibility
pass.

**EXECUTION**:
- Runs from a fresh Trident scratch environment, not a workstation
  session with accumulated state.
- Every input/output hash-verified against the frozen manifest before and
  after the run.
- No retries except a small, **predeclared** set of infrastructure
  conditions (e.g. one transient-network-error retry with unchanged
  input) — declared before execution starts, not invented mid-run.
- All raw outputs preserved verbatim, including failures — nothing
  filtered or summarized before being stored.

**SCORING — layered, never collapsed into one accuracy number:**
- **D0/C0**: structural validity rate; coverage-block rate and reasons.
- **R1/R2**: validator-pass rate; support/declaration/conflict
  distribution; repair-invocation rate and repair-success rate; effective
  verdict distribution (`safe`/`unsafe`/`ambiguous`/structurally blocked).
- **Admission**: safe / unsafe / ambiguous / structural-block counts and
  the specific gate reasons for each.
- **Stage C**: reported **only** for naturally-admitted candidates —
  comparator result and hard-gate pass/fail, never back-filled for
  anything B2 blocked.

**No tuning based on held-out outcomes, ever, under any framing** — this
is the entire point of the freeze.

---

## 9. PREDECLARED FAILURE HANDLING DURING HELD-OUT

| Case | Condition | Action |
|---|---|---|
| A | Provider outage / auth / config failure | Evaluation **pauses**, may **resume under the same run identity** once resolved — this is apparatus, not semantic, and doesn't touch the frozen corpus's validity. |
| B | Deterministic apparatus bug (parser, resolver, transport) discovered mid-run | Evaluation **pauses**. If the fix is provably behavior-preserving on all prior recorded results (`## 3`'s narrow condition), fix and **resume under the same run identity**. If it cannot be shown behavior-preserving, the **run is invalidated** and treated as case D. |
| C | Schema-invalid model output | **Recorded as a failure** for that item (a real result, not discarded) — schema-invalidity is itself scoring information, not noise to retry away, unless it matches a predeclared infrastructure exception from `## 8`. |
| D | New semantic failure class appears (a shape not already known from development) | **Run is invalidated as the final evaluation.** The architecture **returns to development** to characterize the new class. Per the rule below, the held-out set that exposed it is burned. |
| E | An unsafe candidate is admitted (reaches `EFFECTIVE_VERDICT_SAFE` but shouldn't have) | **Recorded as a failure outcome** for that item — this is exactly what held-out evaluation exists to detect, not to hide. If it reflects a systematic pattern (not a one-off), treat as case D. |
| F | Zero natural safe admissions occur in the held-out run | **Recorded as the result**, not treated as a run failure — a real finding (Stage C's role may simply be rare in practice) that returns to development for interpretation, not evidence to synthesize an admission or lower the admission bar. |

**Explicit, load-bearing rule:** if held-out evidence causes ANY semantic
change (cases D or, if systematic, E), **the held-out set that exposed it
is burned** — it is reclassified as development/regression material,
exactly as the 18 fresh-batch-1 candidates were (`## 1`), and **cannot
remain, or later be reused as, the final held-out evaluation set.** A
fresh corpus must be collected for the next held-out attempt. This is the
same discipline already established by this project's own precedent, made
explicit and binding here.

---

## 10. PRODUCTION-CANDIDATE DECISION

**READY FOR PRODUCTION-CANDIDATE REVIEW** requires ALL of:
- Development stability: two stable probes per `## 7`, hash-verified, no
  edits between them.
- Human calibration coverage: `## 12`'s stop rule satisfied for every
  material blocker family (or an explicit documented strictness decision
  per `## 4`/`## 5`).
- Anti-overcorrection: the 4 reserved must-stay-strict cases still block,
  checked directly in the same run that produced the held-out result.
- Stage C exercised: `## 6`'s two-qualitatively-different-admissions
  criterion met, in development, before freeze.
- Held-out behavior: at least one full held-out run completed without
  triggering `## 9` case D (no new semantic failure class), with all
  layered scores in `## 8` recorded and reviewed.
- No unresolved safety-critical failure: no open case E (systematic
  unsafe admission) from any held-out run.

**NOT READY** if any of the above is missing, OR if the most recent
held-out run triggered case D/systematic-E and the architecture has
returned to development without yet completing a fresh held-out run under
`## 9`'s burn rule.

**Production-candidate status is explicitly NOT production promotion.**
Promotion remains human-only, always, regardless of how clean the
held-out result is. This document governs nothing past "ready for human
review."

---

## 11. ROLE OF FINE-TUNING

Stated once, plainly, to close this off: **fine-tuning is optional future
optimization, never the completion criterion.** Potential later uses,
strictly after a validated semantic architecture exists (i.e., after
production-candidate status, not before):
- Output-contract reliability (fewer schema-invalid outputs).
- Consistency across calls.
- Cost/latency reduction.
- Reducing a narrow, already-characterized, repeated error pattern.

Fine-tuning must never be proposed or used as a substitute for the
architecture/calibration work this document governs, and no fine-tuning
design work is done in this pass (none was requested; none was performed).

---

## 12. HUMAN-CALIBRATION STOP RULE

Endless Reader Lab rounds are explicitly rejected. The rule:

**For every materially recurring semantic boundary responsible for
current development blocking (as identified by the zero-safe bottleneck
audit or its successor), calibration is sufficient once:**
- At least one targeted human round (or equivalent direct evidence, e.g.
  the H14-vs-De-Hooch frozen-record audit that produced the Shape-B
  hypothesis without a new round) has directly tested it, AND
- At least one contrast / anti-overcorrection case for that same boundary
  has been included and checked, AND
- There is no unresolved systematic reversal that directly bears on
  safety (i.e., humans consistently and clearly saying B2 is wrong in the
  *unsafe* direction — calling something supported that B2 blocks is a
  different, lower-urgency finding than the reverse).

**Universal reviewer agreement is explicitly NOT required.** Contested
results (as RL-2026-001 produced on 3/5 items) are a valid, sufficient
outcome — they justify **preserving ambiguity or fail-closed behavior**,
not further rounds chasing consensus. A boundary with genuine, substantive
2-reviewer disagreement is calibrated; the correct response is documented
caution in the revision (`## 14`), not a third reviewer or a tie-breaker
round.

Applied now: Shape B has satisfied round 1 of this test via RL-2026-002
(pending its own completion and analysis — this document does not
prejudge that outcome, and RL-2026-002's answers are not inspected here).
Shape C has satisfied none of it — the honest reason `## 5` classifies it
as optional rather than claiming it's already covered.

---

## 13. READER LAB / DEVELOPMENT LEAKAGE RULE

Once an item is used in a Reader Lab round (assigned to a reviewer,
published):
- It **may** inform hypothesis formulation after the round completes
  (exactly how RL-2026-001's results produced the Shape-B hypothesis).
- It **may** inform development tuning, as calibration evidence for a
  consolidated revision (`## 14`) — this is the intended use.
- It **may** be used in regression testing going forward (e.g. as a new
  must-stay-strict or must-become-safe anchor, depending on what the
  human evidence showed).
- It **must never again be treated as hidden/held-out/blind evaluation
  material** — once spent in Reader Lab, an item is permanently
  development-classified, for the same reason the 18 fresh-batch-1
  candidates were permanently reclassified (`## 1`). There is no
  mechanism, and there must never be one, for "un-spending" a Reader Lab
  item back into a blind pool.

This preserves the project's existing discipline exactly — Reader Lab and
held-out evaluation are structurally different pools, and material only
ever flows one direction (held-out/fresh → possibly Reader Lab → always
development), never backward.

---

## 14. ONE CONSOLIDATED FINAL REVISION POLICY

**Default: exactly one consolidated, evidence-targeted B2 semantic
revision**, drafted only after `## 4`'s checklist is fully satisfied —
not one revision per Reader Lab round, not a revision "after RL-002," a
separate one "after RL-003," another "after Shape C." All evidenced
findings (Shape B's outcome, Shape E's outcome if RL-2026-003 proceeds,
the explicit Shape-C strictness decision) are gathered first, then
addressed together in one preregistered revision, then tested hard against
`## 7`'s two-probe stability requirement.

**A second revision is permitted only if:**
- The first revision introduces a clearly new failure class (per `## 7`'s
  stability definition), or
- The first revision fails its own preregistered objective (stated before
  results were seen, per `## 4`'s last checkbox).

No other reason justifies a second revision before freeze. This is the
direct fix for the failure mode this pass was asked to prevent — endless
local prompt tuning chasing each new piece of evidence as it arrives.

---

## 15. FINAL ROADMAP

```
CURRENT:      RL-2026-002 active (Shape B) — not inspected by this pass.

NEXT:         RL-2026-002 completes -> analyze (autonomous, per existing
              calibration orchestrator) -> Shape-B calibration evidence
              finalized.

THEN:         RL-2026-003 (Shape E) ingested + published, IF Shape-E's
              evidenced share of the zero-safe bottleneck (already the
              audit's own largest single category, 22/42) still justifies
              it once Shape B lands — re-confirm, don't assume, before
              spending it.

Shape C:      OPTIONAL per ## 5 — no round scheduled as a precondition for
              freeze. Revisit only if a future audit shows its share of
              the bottleneck has grown, or held-out evidence (## 9 case D)
              requires it.

THEN:         Gather all calibration evidence (Shape B result, Shape E
              result if run, the recorded Shape-C strictness decision) ->
              draft ONE consolidated, preregistered B2 semantic revision
              (## 14).

THEN:         Development regression probe #1 against the revision (## 7).

THEN:         Development regression probe #2, hash-identical inputs to
              #1, no edits between (## 7).

THEN:         Continue running natural development material until Stage C
              exit criterion is met: >=2 qualitatively different natural
              safe admissions, mechanically valid Stage C output, no
              B2-blocked leakage (## 6). This may happen inside probe #1
              or #2, or may require additional natural runs — do not force
              it artificially.

THEN:         SEMANTIC FREEZE — hash every prompt/module/config, name the
              frozen version, record in current-work.md.

THEN:         Fresh held-out corpus collected via the cross-publisher
              sampling protocol (never reusing spent development/Reader-
              Lab material) (## 1, ## 8).

THEN:         Held-out evaluation executed under the ## 8 contract, ## 9
              failure handling predeclared and binding.

THEN:         Production-candidate review (## 10) — human-only promotion
              decision from there; this roadmap's scope ends here.
```

Adjust order only with a stated reason recorded in `current-work.md`, per
that document's own standing convention (last invoked 2026-08-10 for the
grounding-ahead-of-Phase-2 reorder).

---

## WHAT THIS PASS DID NOT DO (explicit, per instruction)

No model calls. No RL-2026-002 partial-answer inspection. No RL-2026-003
ingestion or publication. No held-out semantic content read (none exists
to read, per `## 1`). No D0/C0/R1/R2/repair-v1/admission-gate/Stage-C code
change. No `v2.1`. No fine-tuning design. This document is governance and
preregistration only.

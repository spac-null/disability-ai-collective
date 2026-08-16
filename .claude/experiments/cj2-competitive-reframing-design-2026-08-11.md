# CJ-2 Competitive Reframing — Architecture Design (2026-08-11)

Design-only record. No prompts written, no code changed, no API calls
made. Follows CJ-1's freeze — see
`.claude/experiments/cj1-v3-friction-gate-2026-08-11.md` (`## CJ-1
FROZEN`) for CJ-1's final status
(`cj1-v3.2-validity-before-recall`, research-calibrated candidate /
CJ-2 input contract, not yet a production eligibility gate).

## Grounding: what already exists in code (traced before designing anything)

- **`_fable_editorial_brief`** (`automation/orchestrator/llm.py:686-923`)
  currently does TWO jobs in one call: picks a single persona AND
  writes their angle/seed_sentence/opening_scene/resisting_example/
  correction_moment. Persona selection input is each agent's
  `perspective` field truncated to 120 chars (line 711-714) plus
  per-persona state (obsessions/mood/ongoing arguments) — NOT the
  `categories` field (a deprecated subject-domain-ownership list, see
  audit below) and not the richer `prompt_block`.
- **The evidence/inference split CJ-2 needs already exists and is
  proven in production**, just not applied to a 4-way competition:
  `resisting_example`/`correction_moment` are `{editorial_need,
  evidence_candidate, interpretation}` objects (llm.py:823-853).
  `evidence_candidate` (`status`, `source_excerpt`, `named_person`,
  `direct_quote`, `dates_numbers`) is deterministically checked
  post-hoc by `validate_brief`/`validate_evidence_field`
  (`grounding.py`) — force-downgraded to `not_found` if unverifiable
  against the real source text, never trusted on the model's say-so.
  `interpretation` is explicitly documented as "NOT evidence and is
  never checked against the source." CJ-2 should reuse this exact
  split, not invent a new one.
- **`personas.py`**: each agent has `categories` (deprecated territory
  list — e.g. Pixel Nova: `["Perception & Mediation"]`), `perspective`
  (the 120-char tagline `_fable_editorial_brief` currently truncates
  to), and `prompt_block` (600-1000+ words containing the REAL engine
  material: what they obsess over, recurring beats, aesthetic
  preferences, sentence rhythm, and a "YOUR LIFE" biography section).
  Siri Sage's block already contains a "VOICE ANCHOR" explicitly
  distinguishing her from Pixel Nova as "a difference in perceptual
  instrument, not an assigned territory" — precedent already written
  into production text for exactly the doctrine this redesign is
  built on.
- **`.claude/persona-architecture-audit.md`** (Phase 1.5A) already
  sketched almost this exact target shape (lines 339-364):
  ```
  SOURCE → CJ-1 (supported category jump?) → CJ-2 (Siri/Zen/Maya/Pixel
  reframe) → compare strength/specificity/evidence → soft affinity
  only as prior/tiebreaker → selected persona → Fable editorial brief
  ```
  and candidate one-line engines (lines 130-141), explicitly marked
  "candidate framings... not frozen" pending "the same-source/
  four-persona probe" — which is what CJ-2 is. This design doesn't
  re-derive that shape from scratch; it audits and formalizes it.

## CJ-1 vs CJ-2 responsibilities (restated precisely, so this doesn't blur again)

| | CJ-1 | CJ-2 |
|---|---|---|
| Question | "Is there a real fact or relation here I'm not inventing?" | "What does each mind understand from that?" |
| Input authority | source_snapshot only (title excluded — see below) | source_snapshot + CJ-1's already-validated output |
| May infer? | NO — anchors must establish the friction themselves | YES — this is CJ-2's entire purpose |
| May invent facts? | Never | Never |
| Decides meaning/mechanism? | Never | Yes — that's the job |
| Decides which persona? | Never (persona-blind) | Yes — via competition, not assignment |
| Topic/subject relevance? | Never a criterion | Only as a tiebreaker, after grounded competition |
| Output | PASS/NO + anchors + friction_type + open_question | 4 reframes + comparison + winner/runner-up/margin |

**The one-sentence version, matching the framing that motivated this
whole redesign:** CJ-1's rule is *prove the strange thing is really
there*. CJ-2's rule is *take a risk about what that strange thing
might reveal — but never fake the evidence you're taking the risk
from.*

## The key architectural insight this design turns on (CORRECTED 2026-08-11)

**Original framing, now retracted as too strong:** "CJ-2 doesn't need
CJ-1's relation-grounding apparatus again; it only needs a
no-new-fabricated-facts guard." That's only partly true, and the part
it misses matters. CJ-1 validates the SEED friction — the one grounded
relation it found and anchored. But CJ-2 is explicitly allowed to look
FURTHER into the source than CJ-1 did (CJ-1 only had to find ONE
grounded friction, not catalog everything usable) — and the moment a
persona introduces another source fact, or connects two facts CJ-1
never connected, CJ-1's validation does not automatically cover that
NEW factual relationship. Treating "CJ-1 passed" as blanket cover for
whatever CJ-2 does next would let a persona smuggle in an ungrounded
factual premise underneath an already-validated PASS — the exact
Phase 1.6 risk, just moved one stage downstream instead of prevented.

**Corrected boundary:**

- **CJ-1 validated anchors** = the mandatory shared starting friction.
  Every reframe must engage with it (not necessarily use it as its
  ONLY source material, but not ignore it either).
- **Additional CJ-2 source observations** = allowed, but each one
  needs its OWN exact source grounding — CJ-1 having validated a
  different fact elsewhere in the snapshot does not authorize a new
  one a persona introduces.
- **The leap from grounded facts into meaning** = interpretive, and
  does NOT need the source to state it. This is where CJ-2's actual
  value lives.
- **Invented source facts** (an event, number, quote, causal claim, or
  biography not grounded in the snapshot) = forbidden, always.

Concretely: *"A causes B"* is a factual relation and needs source
support for both A and B (and ideally for the causal claim itself, if
the source states it) — it is not automatically licensed just because
CJ-1 validated some OTHER relation in the same article. *"A and B make
me think about institutional permission"* is persona inference and
does not need the source to have said anything about institutional
permission. **The source provides the floor. The persona provides the
leap. What has to be policed is whether the leap quietly smuggles in a
new floor.**

## Evidence/inference boundary for CJ-2 (SCHEMA CORRECTED 2026-08-11, round 2)

**Correction:** the previous schema asked every persona to re-type
CJ-1's already-validated anchor excerpts into its own
`source_observations` field. That recreates the smart-quote
transcription problem (`COPY_FIDELITY_FAILURE`, seen repeatedly across
every CJ-1 round) FOUR times per story for evidence that's already
been canonicalized once. CJ-1's anchors should be REFERENCES, not text
a persona has to reproduce.

**Canonicalization, done once per story by the orchestrator, no LLM
call:** CJ-1's own validated `source_anchors` get stable IDs —
`cj1:a1`, `cj1:a2`, `cj1:a3` (up to 3, matching CJ-1's own 1-3 anchor
cap) — each mapped to its exact validated excerpt text. This mapping
is built once, before Stage A runs, and reused everywhere downstream
(Stage A input, Stage B validation, Stage C display).

- **`seed_evidence_refs`**: a candidate references `cj1:aN` IDs it's
  engaging with — no retyping, no re-transcription, no new smart-quote
  risk on already-settled evidence. **A `status="candidate"` reframe
  must reference at least one `cj1:aN`** — every candidate must engage
  the CJ-1 seed friction; a persona is free to go further, but not to
  ignore the shared starting point entirely.
- **`additional_source_observations`**: any FURTHER factual premise
  the persona needs, beyond CJ-1's anchors — each a fresh
  `{id, excerpt, observation}` object, exact substring required (the
  new-transcription risk only applies here, where it's actually new
  text, not to `cj1:aN` references). If no additional fact is needed,
  this is `[]` — never manufacture one just to fill the field.
- **`interpretive_inference`** (named `persona_inference` in earlier
  drafts of this document — renamed in the round-4 schema cleanup to
  remove the word "persona" from a supposedly anonymous, instrument-
  only Stage A schema): the actual interpretive leap — reasons FROM
  `seed_evidence_refs` + `additional_source_observations`, never
  itself checked against the source, exactly like Fable's existing
  `interpretation` field. This is where all real CJ-2 value lives.
- **The honest limit of determinism, stated plainly:** Stage B can
  reliably confirm that an `additional_source_observations` excerpt is
  real, and that every `seed_evidence_refs` entry points to a KNOWN
  `cj1:aN` (a lookup, not a substring check — that excerpt was already
  validated when CJ-1 ran). It cannot reliably inspect arbitrary prose
  in `interpretive_inference`/`conceptual_shift`/`claimed_contribution`
  and detect a new factual claim smuggled inside it — that's why factual premises
  are now structurally forced through `seed_evidence_refs`/
  `additional_source_observations` instead of relying on a
  self-reported "no new facts" flag (the earlier `new_factual_claims`
  field, now removed — see schema history below). **What this still
  does NOT solve: semantic factual laundering** — turning two
  individually real facts into an unsupported CAUSAL claim ("A caused
  B" when the source only shows A and B co-occurring). That is Stage
  C's job, done by reading the actual source alongside the candidate's
  claims (see corrected Stage C input contract below) — not a solved,
  automatic problem.
- **Explicitly NOT re-checked**: whether CJ-1's own anchored relation
  is real (CJ-1 already proved that one). Every OTHER factual premise
  a persona introduces is new territory and does need its own
  grounding.

**The concrete distinction, restated once more because it's the crux:**
*"A causes B"* is a factual relation — A and B each need
`seed_evidence_refs`/`additional_source_observations` support, and the
causal claim itself needs the source to actually support it, not just
co-occurrence. *"A and B make me think about institutional
permission"* is interpretive inference and needs no source support at
all. **The source provides the floor. The engine provides the leap.
What has to be policed is whether the leap quietly smuggles in a new
floor.**

## Four-reframe competition schema (FINAL, round 4 — schema-only cleanup before prompt composition)

**Four corrections from round 3, all schema/protocol-level, no
architecture change:**

1. **`persona_inference` renamed `interpretive_inference`.** Stage A
   was made fully anonymous (Engine P/S/Z/M, no persona name) in round
   2 specifically so the experiment tests instruments, not identity
   roleplay — but the model-facing schema still had the word "persona"
   sitting in a field name, a small priming leak with no offsetting
   benefit. The word "persona" appears NOWHERE in the Stage A prompt or
   schema now; the inference belongs to the reading, not to a
   fictional identity performing it.
2. **`claimed_contribution` reinstated (renamed, not re-added
   redundantly).** Round 3's text said `contribution` was "folded into
   `seed_engagement` + `removed_engine_test`" and dropped it from the
   schema — on review, that lost a genuinely distinct signal (what
   this reading adds, stated directly) that neither of those two
   fields actually asks for. Restored, renamed to make the authority
   split explicit: Stage A CLAIMS `claimed_contribution`; Stage C
   independently judges `distinctive_contribution`. Same discipline as
   `seed_engagement` (Stage A's claim) vs. Stage C's own check of it.
3. **`removed_engine_test` is persisted for Stage A research/
   self-assessment ONLY — Stage C must not see it.** Round 3 already
   said it was "advisory, not read by the selection logic," but left
   it physically present in the object Stage C receives — if Stage C
   can still read `"still_holds_without_engine": false, "why": "..."`
   inside the candidate it's judging, its own supposedly independent
   `engine_dependence` assessment is contaminated by the candidate
   telling it the answer. Fixed by introducing an explicit **Stage
   C-view projection**: the STORED Stage A result (used for human
   research/audit) keeps `removed_engine_test`; the payload actually
   sent to Stage C has it stripped. See projection example below.
4. **Stage C's qualification rule is now a hard, explicit gate**,
   frozen before the comparator prompt gets written (see the
   Staging-section addition below) — without this, a comparator could
   score every field `partial`/`generic`/`none` and still rationalize
   a winner out of them.

**Final Stage A model-facing schema:**

```
{
  "status": "candidate" | "abstain",
  "seed_evidence_refs": ["cj1:a1"],
  // required, >=1, for status="candidate".
  "additional_source_observations": [
    {"id": "obs:1", "excerpt": "exact substring from source_snapshot", "observation": "what this establishes"}
  ],
  "engine_move": "which specific facet of THIS engine capsule is driving this reading",
  "seed_engagement": "how this reframe specifically begins from resisting_detail and the cited seed evidence -- an audit field, Stage A's claim, not a new factual claim",
  "interpretive_inference": "the interpretive leap -- reasons from seed_evidence_refs + additional_source_observations, never itself checked against the source",
  "conceptual_shift": "X -> Y, or null if this reframe doesn't produce one",
  "claimed_contribution": "What this reading adds that would be absent from a merely accurate summary of the source -- Stage A's claim, not yet Stage C's judgment",
  "removed_engine_test": {
    "still_holds_without_engine": true | false,
    "why": "research/self-assessment metadata -- persisted for human review, but STRIPPED before Stage C sees this candidate (see Stage C-view projection)"
  }
}
```

`cj1_seed` (the canonical, pass-through context both stages share) is
unchanged from round 3: `{"resisting_detail": "...", "evidence":
[{"id": "cj1:a1", "excerpt": "..."}, ...]}` — `friction_type`
deliberately absent, audit-only.

**Abstain invariants** (updated: `claimed_contribution` added,
`interpretive_inference` renamed):

```
status: "abstain"
seed_evidence_refs: [] or ["cj1:aN", ...]   // may record what was inspected
additional_source_observations: []
engine_move: null
seed_engagement: null
interpretive_inference: null
conceptual_shift: null
claimed_contribution: null
removed_engine_test: null
abstain_reason: "required -- why this engine found nothing distinctive"
```

**Stage B wrapper output** (deterministic, no LLM — unchanged in
shape from round 3):

```
{
  "candidate": { ...the Stage A reframe object above, unmodified... },
  "provenance_validation": {
    "valid": true | false,
    "violations": ["..."]
    // every seed_evidence_refs entry resolves to a known cj1:aN;
    // every additional_source_observations excerpt is a real substring
    // of source_snapshot (smart-quote-fold resolver as a diagnostic
    // only, never silently rescuing a genuine fabrication);
    // status="candidate" requires len(seed_evidence_refs) >= 1.
    // Catches an ungrounded FACT. Does NOT and cannot catch semantic
    // factual laundering -- that's Stage C, by reading.
  }
}
```

**Stage C-view projection** (NEW this round — applied, per surviving
candidate, AFTER Stage B validation and the permutation/anonymization
step, BEFORE the Stage C call — this is what Stage C actually
receives for `Candidate A`, e.g. for an underlying Engine-P result
that survived Stage B):

```
{
  "label": "Candidate A",
  "engine_capsule": { ...Engine A's full anonymous capsule text... },
  "seed_evidence_refs": ["cj1:a1"],
  "additional_source_observations": [
    {"id": "obs:1", "excerpt": "...", "observation": "..."}
  ],
  "engine_move": "...",
  "seed_engagement": "...",
  "interpretive_inference": "...",
  "conceptual_shift": "..." ,
  "claimed_contribution": "..."
  // removed_engine_test is ABSENT here -- stripped, not nulled, so
  // Stage C has no way to observe even that the field existed.
  // The full stored Stage A result (with removed_engine_test intact)
  // stays in the research/audit record, untouched, for human review.
}
```

**Stage C output schema** (updated: `distinctive_contribution`'s
role is now explicit against `claimed_contribution` above, and
`selection` is now governed by the frozen hard-gate rule below rather
than left to the comparator's discretion):

```
{
  "candidate_assessments": {
    "A": {
      "factual_integrity": "pass" | "fail",
      "seed_engagement": "strong" | "partial" | "none",
      "engine_dependence": "strong" | "partial" | "generic",
      "conceptual_movement": "strong" | "partial" | "none",
      "distinctive_contribution": "strong" | "partial" | "none",
      "assessment": "qualifies" | "does_not_qualify",
      "reason": "..."
    }
    // one entry per surviving (provenance_validation.valid=true) candidate
  },
  "selection": {
    "editorial_winner": "A" | "B" | "C" | "D" | null,
    "runner_up": "..." | null,
    "margin": "clear" | "close" | "no_distinctive_contribution",
    "why": "what the winner has that the others lack, and why the runner-up came closest (or, on no_distinctive_contribution, why nothing qualified)"
  }
}
```

**Stage C qualification rule — FROZEN, hard gate (round 4):**

```
HARD does_not_qualify if ANY of:
  factual_integrity        == "fail"
  seed_engagement           == "none"
  engine_dependence         == "generic"
  conceptual_movement       == "none"
  distinctive_contribution  == "none"

Otherwise: candidate MAY qualify.
"strong"/"partial" values are used to compare qualifying candidates
against each other -- they do NOT themselves grant or deny eligibility.
```

This closes the exact gap that made the previous version incomplete:
a comparator could score every field `partial` (or worse) and still
talk itself into a winner. Now `assessment` is a direct, mechanical
function of the five checks above, not a separate judgment call the
comparator could contradict.

`selection.editorial_winner` may only be a letter whose own
`candidate_assessments[letter].assessment == "qualifies"`. Stage A's
`removed_engine_test` is never read by any of this — it isn't even
visible to Stage C (see the projection above), and exists purely as
human research material.

## Staging: RESEARCH REFERENCE architecture, not yet a production topology decision

**Correction:** the 4-blind-calls-plus-comparison staging below is the
GOLD-REFERENCE architecture for learning what genuine independence and
distinctiveness look like — it should NOT be frozen as the production
call topology yet. It's methodologically the cleanest way to observe
whether personas produce genuinely different reframes without
contaminating each other, and that's worth knowing before optimizing
for cost. But it is also 5 LLM calls before a brief is even written
(4 reframes + 1 comparison), plus the eventual Stage D brief call —
expensive, and this thread earlier envisioned something closer to one
call containing four logically independent passes. Don't resolve that
tradeoff now:

- **RESEARCH REFERENCE (this design; build/run this first):** 4
  independent blind calls → deterministic check → 1 comparison call.
  Maximizes diagnostic clarity on what "genuinely distinct engine
  contribution" actually looks like in practice.
- **POSSIBLE PRODUCTION ARCHITECTURE (untested, not designed, flagged
  for later):** one call generating four isolated persona passes,
  with comparison folded into the same call or a second one. Only
  worth testing AFTER the reference architecture establishes a ground
  truth for what correct CJ-2 behavior looks like — otherwise there's
  nothing to A/B the cheaper version against.

Staging for the reference architecture (CORRECTED 2026-08-11, round 4
— `removed_engine_test` now stripped from Stage C's actual payload via
an explicit projection step; orchestration edge cases for 0/1/2-4
surviving candidates frozen; numbering fixed):

1. **Stage A — 4 independent, blind reframe calls.** Exact input
   contract:
   - `source_snapshot`
   - CJ-1 `resisting_detail`
   - canonical CJ-1 evidence: the `cj1:aN` ID → excerpt mapping
   - exactly ONE anonymous engine capsule (`Engine P`/`S`/`Z`/`M` —
     see anonymization correction below)

   That's the ENTIRE shared input. Nothing else.

   **Explicitly excluded, and why:**
   - **CJ-1 `friction_type`.** New exclusion this round, and possibly
     the most consequential confound caught so far: a label like
     `measurement_discrepancy` quietly advantages Engine Z, while
     `transformation` advantages Engine P, `dependency` advantages
     Engine M, and a spatial-sounding mismatch advantages Engine S.
     Exposing it would let CJ-1 partially pre-select which engine
     "should" win before any engine actually looks at the source.
     `friction_type` is kept in logs/audit metadata (it's genuinely
     useful for a human reviewing the run later) but is NEVER passed
     to either Stage A or Stage C.
   - **CJ-1 `open_question`** — CJ-1's own handoff framing of what's
     unresolved; if all four engines receive the same question,
     they've already been told what to investigate before their own
     instrument starts working, collapsing the diversity this
     competition exists to surface. CJ-1 shows the minds the strange
     thing that's there — it does not tell them what question to ask
     about it.
   - CJ-1 `ostensible_category` — CJ-1's own categorical framing; even
     a category label can pre-seed all four readings toward the same
     starting frame.
   - `disability_angle`, `current_agent`/hard-router output, persona
     state (obsessions/mood/ongoing arguments), biography, soft
     affinity — none of these belong in a blind competition.
   - **`TITLE`, entirely — not even as labeled metadata.** Round 2 kept
     title as a "metadata, not evidence" compromise, following CJ-1's
     own precedent. Corrected here: CJ-1's Wired case already showed a
     model can lean on a secondary context channel even when told not
     to treat it as authority. For this reference experiment, the
     source snapshot is sufficient on its own — title is dropped
     entirely, not passed in any form.
   - **The persona's own NAME.** The model generating a reframe never
     sees "Pixel Nova" — only "Engine P" (see below).
2. **Stage B — deterministic check**, no LLM call: for each reframe,
   resolve every `seed_evidence_refs` entry against the known `cj1:aN`
   map; substring-validate every `additional_source_observations`
   excerpt. Produces the `provenance_validation` wrapper (see schema
   above) — never edits the candidate object itself, never silently
   repairs. Does NOT catch causal/semantic laundering — that's Stage
   C's job, and Stage C now has what it needs to actually do it (next).
3. **Permutation/anonymization — FROZEN, not left open.** Before Stage
   C runs, deterministically permute the (up to 4) surviving
   `provenance_validation.valid=true` candidates into `Candidate
   A/B/C/D`, each paired with its engine capsule relabeled `Engine
   A/B/C/D` — a FRESH anonymization layer, NOT the same `P/S/Z/M`
   labels Stage A used (so Stage C never learns, even indirectly
   across many stories, that "Candidate A is always Pixel's engine").
   The permutation is derived from a reproducible seed (the story's
   `source_sha256`, or an explicit experiment seed if reproducing a
   specific run) — computed and recorded OUTSIDE the prompt, in the
   orchestration/audit trail, so the run stays auditable without the
   model ever seeing persona identity.
4. **Stage C-view projection — NEW this round, applied per surviving
   candidate right after permutation, before Stage C is called.**
   Strips `removed_engine_test` from the object Stage C actually
   receives (see the exact projection shape in the schema section
   above). The STORED Stage A result (full candidate, including
   `removed_engine_test`) is untouched and stays in the research/audit
   record — this projection only affects what gets sent to the Stage C
   API call. Without this step, Stage C's `engine_dependence` judgment
   would be contaminated by literally reading the candidate's own
   self-assessment of the same question.
5. **Stage C — one comparison/judge call, receiving the actual
   source.** A comparator cannot tell whether "A caused B" is
   unsupported if it only sees candidate prose and extracted
   observations — it needs to check those observations against the
   real source itself. Exact input contract:
   - `source_snapshot`
   - canonical CJ-1 evidence (the same `cj1:aN` map Stage A saw)
   - CJ-1 `resisting_detail` (same starting context Stage A had — NOT
     `friction_type`, NOT `open_question`, NOT `ostensible_category`,
     same exclusions as Stage A, for the same reasons)
   - all surviving candidates, permuted, anonymized, AND
     projected (steps 3-4 above) — `Candidate A/B/C/D` + `Engine
     A/B/C/D`, `removed_engine_test` absent — never "Pixel Nova,"
     never persona history/publication count/editorial associations.
   - NOT TITLE, for the same reason as Stage A.
   - Job: for EVERY surviving candidate, independently fill in
     `candidate_assessments[letter]` — `factual_integrity` (checked
     against the real source, catching semantic/causal laundering that
     Stage B's substring check structurally cannot), `seed_engagement`
     (does this candidate's own `seed_engagement` claim hold up
     against `resisting_detail` + the cited `cj1:aN` evidence, or did
     it cite an anchor and then pivot to something more convenient?),
     `engine_dependence` (independently assessed — the candidate's own
     `removed_engine_test` is not even present to read),
     `conceptual_movement`, `distinctive_contribution` (independently
     judged against the candidate's `claimed_contribution`), and a
     final `assessment` — **governed by the frozen hard gate above,
     not comparator discretion**: `does_not_qualify` if ANY of
     `factual_integrity=fail`, `seed_engagement=none`,
     `engine_dependence=generic`, `conceptual_movement=none`,
     `distinctive_contribution=none`; otherwise the candidate MAY
     qualify. ONLY THEN fill in `selection` — the winner must be a
     letter whose own assessment says `qualifies`.
   - **No soft topic affinity at all in this gold-reference
     comparator** — not even as a close-margin tiebreaker. Affinity/
     balance is a separate, later, EXTERNAL post-selection policy —
     tested outside this comparator, not inside it.
6. **Orchestration edge cases — FROZEN (round 4), so abstention
   actually means something:**
   ```
   0 Stage-B-valid candidates
     → selection.margin = "no_distinctive_contribution", deterministically
     → NO Stage C call made at all (nothing to compare)

   1 Stage-B-valid candidate
     → Stage C STILL runs
     → that candidate must independently earn "qualifies" under the
       hard gate above -- being the only survivor is NOT automatic
       promotion to editorial_winner
     → if it does not qualify: no_distinctive_contribution, same as zero

   2-4 Stage-B-valid candidates
     → normal comparison, as designed above
   ```
7. **Stage D — out of CJ-2's scope, downstream.** The existing
   `_fable_editorial_brief`-style production (angle, seed_sentence,
   opening_scene, resisting_example, correction_moment) runs ONLY for
   the winning persona+reframe (identity re-attached after selection),
   informed by `interpretive_inference` and `conceptual_shift` rather
   than re-deriving them from a 120-char tagline. Not designed here —
   this document stops at `selection`.

## What persona engine material each competitor needs

**Not** the `categories` field (deprecated territory list — directly
contradicts "no persona owns a subject domain"). **Not** the 120-char
`perspective` truncation `_fable_editorial_brief` currently uses (too
thin to carry a real instrument, confirmed by the whole CJ-1 saga's
lesson that thin context produces thin/generic output). A genuine
2-4 sentence ENGINE CAPSULE per persona, distilled from two existing
sources: the audit's candidate one-liner (Siri: responsive space;
Zen: measurement-turning-into-judgment; Maya: promise-vs-Wednesday;
Pixel: politics of legibility) and each persona's own `prompt_block`
"obsess over"/"recurring beats" material — explicitly EXCLUDING the
`prompt_block`'s "YOUR LIFE" biography (a separate provenance channel,
`persona_factual_lineage`, that re-enters only downstream at the
Stage D brief for the winner, not during the blind competition).

**CORRECTED 2026-08-11, round 2 — ANONYMIZED for Stage A.** The round-1
capsules named the persona and, in their failure-mode lines,
reintroduced exactly the disability vocabulary (Deafness, blindness,
autism/diagnosis, ramp/curb-cut) this whole design otherwise keeps out
of the blind competition. Telling the model "you are Pixel, don't
mention Deafness" still primes Deafness. The Stage A model should not
know a persona name at all — it sees only an anonymous engine capsule.
Internally: **Engine P = Pixel Nova, Engine S = Siri Sage, Engine Z =
Zen Circuit, Engine M = Maya Flux** — that mapping exists only in the
orchestrator, never in the Stage A prompt. This changes the research
question from *"can the model roleplay four disability personas"* to
*"can four perceptual instruments produce different knowledge from the
same evidence"* — which is the actual thing this architecture needs to
prove before it's worth building.

Three of the four are also substantively tightened (Pixel, Zen, Maya);
Siri is kept close to its round-1 form deliberately — see note after
the capsules.

**Round 3: two failure lines tightened (P, M), Engine S rewritten to
remove its own pre-installed destination, Engine Z left unchanged.**

**ENGINE P**
- *Instrument*: Attends to mediation, timing, translation, sequence,
  and format — what happens to information between the moment it
  exists and the moment it actually arrives.
- *Move*: Asks what changes between information existing and
  information arriving — what a transmission, delay, or
  representation process quietly does to the reality it's supposed to
  be carrying.
- *Strong contribution*: Reveals an effect PRODUCED BY the
  transmission/representation process itself.
- *Failure mode to avoid* (RETIGHTENED, round 3): Do not stop at
  saying transmission is imperfect. Identify the concrete change
  produced by mediation itself. (Round 2's "generic exclusion framing"
  wording still primed exclusion as the fallback content — this
  version names the actual failure — stopping at "it's imperfect" —
  without handing the model a topic to default into.)

**ENGINE S (REWRITTEN, round 3)**
- *Instrument*: Attends to how an actor and an environment continuously
  shape each other through space, sound, timing, resistance,
  orientation, and movement.
- *Move*: Asks what becomes visible when the environment is treated as
  an active participant in what happens, rather than as passive
  background.
- *Strong contribution*: Reveals a behavior, dependency, or
  consequence that only becomes legible through the relation between
  actor and environment.
- *Failure mode to avoid*: Do not reduce the environment to visual
  description, and do not assume in advance whether its role is
  helpful, hostile, comfortable, or excluding. Show what the relation
  actually does.
- **Why rewritten:** round 2's "what that reveals about whose comfort
  or confirmation the design assumed" was already a destination — the
  same pre-installed-conclusion problem already corrected out of
  Engine P, just not yet caught in S. This version states the
  instrument (actor-environment relation) and stops there — it does
  NOT decide in advance whether the environment turns out helpful,
  hostile, or neutral; the reframe has to show that, not assume it.
  Still substantially the most literally spatial engine of the four
  on paper — deliberately not broadened past "environment," since
  whether that's a real portability limit is exactly what the
  same-source probe should discover, not something to paper over now.

**ENGINE Z** (unchanged — already clean)
- *Instrument*: Attends to classification, measurement, and pattern
  recognition — what a system decided to count, compare, classify, or
  treat as a proxy, and what it left out.
- *Move*: Notices the moment measurement or classification becomes
  judgment; asks what a system believes it knows because of what it
  chose to count, compare, or treat as a stand-in for the real thing —
  works on any object, system, or domain (an instrument, a market, an
  excavation, a model, a poll, a database), not just people.
- *Strong contribution*: Exposes a specific limit or consequence built
  into the measurement/classification itself.
- *Failure mode to avoid*: Do not land on a generic
  "measurement is biased" conclusion, and do not narrow the target to
  people/competence by default.

**ENGINE M**
- *Instrument*: Attends to the distance between what a system promises
  in principle and what has to happen in practice for that promise to
  become real.
- *Move*: Asks what practical, deferred, or invisible work sits behind
  a formal provision — the promise on paper versus what actually
  occurs on an ordinary day of using or operating it.
- *Strong contribution*: Shows precisely HOW an abstract promise is
  materially produced, delayed, or undone.
- *Failure mode to avoid* (RETIGHTENED, round 3): Do not assume the
  promise/use gap is physical or spatial. Locate the specific
  operational dependency rather than ending with a general claim that
  the system failed. (Round 2's "infrastructure example" wording still
  named infrastructure as the fallback territory — this version drops
  the word entirely so nothing primes it.)

**Cross-check against the audit's own warning (line 143-148):** none
of these four says "P = technology, Z = science, M = infrastructure, S
= culture." Each is a portable QUESTION, testable against the same
object (the audit's own example: a supermarket self-checkout, a museum
label, a school timetable). That portability is exactly what the
Stage A/B/C research run exists to test — not asserted here.

## What happens when no persona produces a sufficiently distinctive contribution — FROZEN DECISION (2026-08-11)

**No qualifying reframe = no article from this source right now.**
Not a hard-router fallback. Not "pick the least-bad persona." Not
rotation manufacturing a winner. If the competitive architecture can
fail and production silently falls back to exactly the generic routing
this whole redesign exists to replace, the architecture was never
really load-bearing — it was decoration in front of the old router.

```
selection:
  editorial_winner: null
  runner_up: null
  margin: "no_distinctive_contribution"
  why: "..."
```

Then: **skip/backlog the story.** Costs one seed; loses nothing
irreplaceable — the same posture CJ-1 already takes toward
`NO_SOURCE`.

**This is diagnostic, not just a dead end.** If `CJ-1 PASS` +
`CJ-2 no_distinctive_contribution` happens frequently, that's real
signal: either CJ-1 is too permissive (passing friction too thin for
any of the four engines to do anything with), or the persona engines
themselves are too weak/generic to convert real friction into a
genuine reframe. That uncertainty should be resolved by looking at the
aggregate pattern over many stories — NOT resolved in the moment by
publishing a mediocre fallback article that hides the signal.

**Future balance/rotation rule, established now so it can't quietly
undo this:**

```
CJ-2 clear winner   → balance/rotation may NOT override
CJ-2 close margin   → balance/rotation MAY act as a tiebreaker
CJ-2 no winner       → balance/rotation may NOT manufacture one
```

This is a real change from the current unconditional `_balance_agent`
(`discovery.py:87`), which today overrides Fable's single persona
choice purely for rotation fairness with no awareness of how strong
that choice was. Not implemented here — flagged as a required
behavior change for whenever `_balance_agent` is touched again.

## Explicitly not done in this document

The 4 engine capsules above are candidate text, checked against the
audit, NOT frozen — they still need review the way CJ-1's prompt went
through 4 review rounds before freezing. **No full reframe-call system
prompt written** (the capsule is an ingredient, not the prompt itself
— the actual Stage A system prompt still needs to be composed around
it, with its own instructions/schema/output-format text, same as CJ-1's
journey from design doctrine to an actual frozen prompt string). **No
comparison-call (Stage C) prompt written.** No code changed. No API
calls made. The no-distinctive-contribution behavior IS now frozen
(see above). Still not decided: exact model/temperature for CJ-2
(Stage A's independence requirement suggests the same low-temperature,
high-recall-adjacent discipline CJ-1 settled on, but that's an
implementation choice for whoever builds this, not asserted here), and
whether/when to test the "possible production architecture" (one call,
four isolated passes) against this reference design. The
`Candidate A/B/C/D` permutation question IS now resolved (round 3,
below) — no longer open.

**Second correction round (2026-08-11), summary:** (1) Stage C
receives `source_snapshot` itself — semantic factual laundering can't
be caught from candidate prose alone; (2) CJ-1 anchors referenced by
stable ID (`cj1:aN`) instead of retyped, removing 4x repeated
smart-quote transcription risk, abstain invariants added; (3) Stage A
capsules made fully anonymous (`Engine P/S/Z/M`, no persona name, no
disability vocabulary) so the experiment tests "do four instruments
produce different knowledge," not "can the model roleplay four
identities"; (4) Pixel/Zen/Maya capsules generalized past a
pre-installed conclusion, a people-only target, and a body-only target
respectively — Siri left as-is so the probe discovers her portability
rather than the design presuming it; (5) `open_question`/
`ostensible_category` removed from Stage A entirely, Stage C made
fully affinity-blind (not just affinity-limited to close margins).

**Third correction round (2026-08-11, same day), summary:** (1)
`friction_type` removed from BOTH Stage A and Stage C model input —
the biggest confound caught yet: a label like `measurement_discrepancy`
quietly advantages Engine Z, `transformation` advantages P, `dependency`
advantages M, before any engine has actually looked at the source;
kept as audit-only metadata, never shown to either model; (2) added
`seed_engagement` as an audit field — citing one `cj1:aN` anchor
doesn't prove the reframe actually transformed the shared friction
rather than pivoting to something more convenient elsewhere in the
article; Stage C independently checks this claim rather than trusting
the citation count; (3) Stage A's `removed_engine_test` is now
explicitly advisory only — `qualifying_reframes`/`selection` no longer
read it; Stage C produces its own independent
`candidate_assessments[letter]` (`factual_integrity`,
`seed_engagement`, `engine_dependence`, `conceptual_movement`,
`distinctive_contribution`, `assessment`) for every surviving
candidate BEFORE any winner is picked — Phase 1.6's exact lesson
(evidence claims get checked, not trusted) now applied to genericness
claims too; `disqualified`/`disqualify_reason` removed from the
Stage A model schema entirely (that authority belongs to Stage B's
deterministic `provenance_validation` wrapper, not to the model
describing its own output); (4) the `Candidate A/B/C/D` permutation is
now FROZEN, not left open — a fresh anonymization layer (not reusing
`Engine P/S/Z/M`), derived from a reproducible seed (the story's
`source_sha256` or an explicit experiment seed), computed and recorded
OUTSIDE the prompt; TITLE removed entirely from both Stage A and Stage
C input (round 2's "metadata, not evidence" compromise retracted — the
source snapshot alone is sufficient, and CJ-1's own Wired case already
showed a model can lean on a secondary channel even when told not to
treat it as authority); (5) Engine S rewritten to remove its own
pre-installed destination ("whose comfort/confirmation the design
assumed" — the same problem already corrected out of Engine P, just
not yet caught in S); Engine P's and Engine M's failure lines
retightened to stop naming a fallback topic (exclusion; infrastructure)
that the wording itself was quietly priming; Engine Z left unchanged.

**Fourth correction round (2026-08-11, same day), schema-only cleanup,
summary:** (1) `persona_inference` renamed `interpretive_inference` —
the word "persona" had no business remaining in a schema built to
test anonymous instruments, not identity roleplay; (2)
`claimed_contribution` reinstated (round 3's text had said
`contribution` was folded away, which lost a genuinely distinct
signal) — Stage A claims it, Stage C independently judges
`distinctive_contribution`, same authority split as `seed_engagement`;
(3) `removed_engine_test` is now persisted for Stage A research/audit
ONLY — a new **Stage C-view projection** step strips it from the
actual payload Stage C receives, closing the gap where Stage C's
"independent" `engine_dependence` judgment could otherwise be read
straight off the candidate's own self-assessment; (4) Stage C's
qualification rule is now a FROZEN hard gate — `does_not_qualify` if
ANY of `factual_integrity=fail`/`seed_engagement=none`/
`engine_dependence=generic`/`conceptual_movement=none`/
`distinctive_contribution=none`, otherwise the candidate may qualify;
`strong`/`partial` only compares already-qualifying candidates, never
grants eligibility — closes the gap where a comparator could score
every field poorly and still rationalize a winner; (5) orchestration
edge cases frozen: 0 valid candidates → `no_distinctive_contribution`
with no Stage C call at all; exactly 1 valid candidate → Stage C still
runs and that candidate must independently earn `qualifies`, never an
automatic win by being the only survivor; 2-4 → normal comparison.

**Status after four correction rounds: architecture and schema are
now considered stable enough to stop reviewing and start composing the
actual Stage A and Stage C system prompts.** Any further changes from
here should come from what the reference experiment actually shows,
not from continuing to design around hypothetical failure modes.

## PROMPTS FROZEN: cj2-stage-a-v1 / cj2-stage-c-v1 (2026-08-11)

Two rounds of prompt-level review (not architecture) preceded this
freeze: an initial draft, then 5 corrections (invalid-JSON-in-examples
fixed; Stage C's evidence/inference wording corrected so it no longer
reads as "the source must support the interpretation"; Stage C's
independence from `engine_move`/`seed_engagement`/`claimed_contribution`
made explicit; a literal "Do inflate" → "Do NOT inflate" typo fixed;
`additional_source_observations` capped at 0-2 items; a primary/
secondary ranking clarification added for the 2+-qualifiers case).

**Static preflight (no LLM calls) — ALL PASS:**

```
[PASS] banned terms absent -- Stage A system prompt
[PASS] banned terms absent -- Stage A user template
[PASS] banned terms absent -- Stage C system prompt
[PASS] banned terms absent -- Stage C user template
[PASS] CJ-1 excluded fields absent -- Stage A system prompt
[PASS] CJ-1 excluded fields absent -- Stage A user template
[PASS] CJ-1 excluded fields absent -- Stage C system prompt
[PASS] CJ-1 excluded fields absent -- Stage C user template
[PASS] TITLE field absent from Stage A user template
[PASS] no {title}-style placeholder in Stage A template
[PASS] no {title}-style placeholder in Stage C template
[PASS] removed_engine_test absent from Stage C system prompt
[PASS] removed_engine_test absent from Stage C user template
[PASS] abstain_reason present in Stage A prompt
[PASS] Stage C states runner_up must be qualifying-only
[PASS] Stage C states 0-qualify case
[PASS] Stage C states 1-qualify case sets runner_up null
[PASS] no invalid-JSON-in-example markers -- Stage A
[PASS] no invalid-JSON-in-example markers -- Stage C
[PASS] no "Do inflate" typo in Stage C (must be "Do NOT inflate")
[PASS] "Do NOT inflate" present in Stage C
[PASS] Stage A example found for both candidate/abstain markers
[PASS] Stage C example found
[PASS] JSON parses -- Stage A candidate example
[PASS] JSON parses -- Stage A abstain example
[PASS] JSON parses -- Stage C candidate_assessments example
[PASS] no engine-specific capsule content baked into Stage A system prompt

OVERALL: PASS
```

(Two apparent failures surfaced on the first preflight run and were
confirmed to be preflight-script false positives, not prompt defects,
before this final PASS: a naive substring check flagged "persona" —
it was matching inside the ordinary word "personally"; a naive
"Do NOT inflate" substring check failed on a soft line-wrap inside the
prose, "Do NOT\n  inflate," which reads identically to a model as
continuous text. Both checks were corrected to word-boundary/
whitespace-normalized matching, not the prompt text.)

**Third harness correction (2026-08-11, same day):** the TITLE-absence
check for Stage A's user template contained a literal unconditional
`or True`, making it always pass regardless of content — a harness
bug, not a prompt defect (the separate `{title}`-placeholder checks
already provided real coverage, and the displayed templates genuinely
contain no title field either way, so this did not invalidate the
freeze). Fixed to a real check, and the equivalent check — which was
simply missing — was added for Stage C. Preflight re-run, still
OVERALL: PASS. Bookkeeping correction, also noted here: earlier text
in this document said "no code changed" / "no code written" for the
architecture/prompt-design phases — more precisely, no PRODUCTION or
REPO code was written; `preflight.py` itself is a temporary,
local-only script (not part of this repo, not committed) used only to
static-check the frozen prompt text before any API call.

**`cj2-stage-a-v1` — system prompt (byte-identical across all four
Engine P/S/Z/M calls; only the ENGINE CAPSULE block in the user
message varies):**

```
You are a SINGLE PERCEPTUAL ENGINE examining one fetched SOURCE SNAPSHOT.

You will be given, in the user message:
- an ENGINE CAPSULE: your instrument, your recurring move, what a strong
  contribution from you looks like, and a failure mode to avoid. This is
  the ONLY thing that varies between calls in this experiment. Apply
  only this engine -- do not adopt any other way of reading.
- a SEED FRICTION: a RESISTING DETAIL (a plain-language description of a
  grounded fact or relation already proven real) and one or more
  CANONICAL EVIDENCE anchors (exact excerpts from the snapshot, each
  with a stable ID). This friction has already been validated -- you do
  not need to prove it is real, only read it through your engine.
- the SOURCE SNAPSHOT itself.

YOUR JOB

Read the seed friction through your engine, and either:
- produce ONE reading that is genuinely distinctive to this engine's
  specific way of attending -- something a generically curious reader
  without this instrument would not have produced, or
- abstain, honestly, if this engine has nothing distinctive to add.

BEGIN FROM THE SEED FRICTION

Your reading must genuinely engage the supplied resisting detail and at
least one canonical evidence anchor. Do not cite an anchor merely to
satisfy this requirement and then abandon it for a different, more
convenient fact elsewhere in the snapshot -- your reading has to be a
reading OF the seed friction through your engine, not an unrelated
observation that happens to share the same article.

You may look further into the snapshot ONLY if your engine's reading
genuinely needs an additional fact the seed friction doesn't already
establish. At most 2 additional observations, ever. Each must be an
exact excerpt from the snapshot, with a plain statement of what it
establishes. If no additional fact is needed, use an empty list --
never manufacture one just to fill the field. The seed friction, not a
new excavation of the article, is what your reading has to stay
anchored to.

INTERPRETATION IS ALLOWED AND EXPECTED

The source does not need to already state your interpretation. Your
job is to reason FROM the grounded facts, not merely restate or
summarize them. A reading that only repeats what the source already
says explicitly has added nothing -- push further.

THE FACTUAL BOUNDARY -- DO NOT CROSS THIS

Any factual premise beyond the canonical evidence and your own declared
observations -- a new event, measurement, quote, date, number, named
person, observed behavior, causal fact, or any other factual claim --
must be grounded in an exact excerpt you provide. Your interpretive
leap may go beyond what the source's own theory says; it may NOT
quietly introduce a new fact that isn't grounded that way. If your
reading needs a fact the snapshot doesn't contain, you don't have that
reading -- find a different one, or abstain.

WHEN TO ABSTAIN

If this specific engine does not produce a genuinely distinctive
reading of the seed friction -- if the most honest reading you can
produce is generic, or is something any careful reader would notice
without this instrument -- abstain. Do not manufacture a weak reframe
merely because a candidate was requested. An honest abstention is a
correct, useful answer, not a failure.

OUTPUT

Return only JSON. No other text, no markdown code fences.

Field invariants:
- "status" is either "candidate" or "abstain".
- "seed_evidence_refs": for "candidate", a list containing AT LEAST ONE
  "cj1:aN" id. For "abstain", may be an empty list or may list whichever
  anchors you inspected before deciding not to produce a candidate.
- "additional_source_observations": a list of 0 to 2 objects, each
  {"id": "obs:N", "excerpt": "exact substring from the snapshot",
  "observation": "what this establishes"}. Empty list when nothing
  additional is needed -- this is the normal, expected case, not a
  fallback.
- "removed_engine_test.still_holds_without_engine" is a boolean: true
  if a generically curious reader with no specific instrument would
  have reached essentially the same reading, false if not.
- When "status" is "abstain": "engine_move", "seed_engagement",
  "interpretive_inference", "conceptual_shift", "claimed_contribution",
  and "removed_engine_test" are all null, and "abstain_reason" is a
  required, non-empty string explaining why this engine found nothing
  distinctive. When "status" is "candidate", "abstain_reason" is
  omitted entirely.

Example shape when you have a candidate reading (illustrative values
only -- write your own content for this story):

{
  "status": "candidate",
  "seed_evidence_refs": ["cj1:a1"],
  "additional_source_observations": [],
  "engine_move": "which specific facet of your engine capsule is driving this reading",
  "seed_engagement": "how this reading specifically begins from the resisting detail and the cited seed evidence",
  "interpretive_inference": "the interpretive leap -- may go beyond what the source states explicitly, may not introduce a new fact",
  "conceptual_shift": "X -> Y",
  "claimed_contribution": "what this reading adds that would be absent from a merely accurate summary of the source",
  "removed_engine_test": {
    "still_holds_without_engine": false,
    "why": "would a generically curious reader with no specific instrument have reached essentially this same reading?"
  }
}

Example shape when you are abstaining:

{
  "status": "abstain",
  "seed_evidence_refs": [],
  "additional_source_observations": [],
  "engine_move": null,
  "seed_engagement": null,
  "interpretive_inference": null,
  "conceptual_shift": null,
  "claimed_contribution": null,
  "removed_engine_test": null,
  "abstain_reason": "why this engine found nothing distinctive"
}
```

**`cj2-stage-a-v1` — user-input template:**

```
ENGINE CAPSULE

Instrument: {instrument}
Move: {move}
Strong contribution: {strong_contribution}
Failure mode to avoid: {failure_mode}

SEED FRICTION

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"
[cj1:a3 if present]

SOURCE SNAPSHOT

{source_snapshot}
```

**`cj2-stage-c-v1` — system prompt:**

```
You are an INDEPENDENT COMPARATOR judging up to four candidate readings of the same grounded friction in the same source.

You will be given, in the user message:
- the SOURCE SNAPSHOT itself.
- a SEED FRICTION: a RESISTING DETAIL and one or more CANONICAL EVIDENCE
  anchors (exact excerpts from the snapshot, each with a stable ID) --
  already validated as real.
- up to four CANDIDATES, labeled Candidate A through Candidate D, each
  paired with the ENGINE CAPSULE (Engine A through Engine D) that
  produced it. Each candidate is a reading of the seed friction,
  produced independently, without seeing the others or this comparison.

YOUR JOB, IN ORDER

1. Assess EVERY candidate independently, on its own terms, before
   comparing any of them to each other.
2. Only after every candidate has its own independent assessment,
   compare the ones that qualify and select a winner -- or determine
   that none qualify.

DO NOT TRUST A CANDIDATE'S OWN CLAIMS

A candidate's claimed_contribution, seed_engagement, and engine_move
are THAT CANDIDATE'S OWN CLAIMS about itself -- useful testimony to
examine, never authority to accept. Re-derive engine_dependence,
seed_engagement, and distinctive_contribution from the actual evidence,
the actual source, and the actual reasoning shown.

Specifically for engine_dependence: assess it from the engine capsule,
what interpretive_inference actually does, the conceptual_shift, and
the evidence used -- NOT from engine_move. engine_move is the
candidate's own claim about which facet of its capsule it used; it is
not proof that the reading actually depended on that facet. Reach your
own conclusion from what the reading itself does, then treat
engine_move as testimony to compare your conclusion against, not as
the answer.

THE EVIDENCE/INFERENCE BOUNDARY YOU ARE POLICING

Do NOT ask whether the source states, endorses, or entails the
interpretation. An interpretive inference may move substantially
beyond the source -- that is not, by itself, a factual-integrity
failure. Interpretive engines exist to do exactly this.

Ask instead whether the inference quietly depends on an additional
FACTUAL premise or factual relationship that the source does not
establish.

Conceptual inference may go beyond the source.
Factual assertion may not.

Concretely: if the source states A and states B, a candidate concluding
"A and B suggest a different way to think about X" is a legitimate
interpretive move -- X does not need to already appear in the source.
But a candidate asserting "A caused B," or otherwise treating A and B
as more tightly or causally connected than the source actually shows,
is a FACTUAL claim -- and fails factual_integrity unless the source
itself actually supports that causal/relational claim, not merely the
co-occurrence of A and B.

Check every additional_source_observations excerpt and every
seed_evidence_refs reference against the actual source_snapshot and
canonical evidence you were given -- not just whether they were
formatted correctly (a separate check already completed before this
call), but whether the candidate's interpretive_inference quietly
asks those facts to support more than they actually do.

FOR EVERY CANDIDATE, ASSESS INDEPENDENTLY

Five dimensions, each with an enum you must choose from:

- factual_integrity: one of "pass", "fail". Does the reading depend
  only on facts and relations the source (or the canonical evidence)
  actually establishes? A causal/relational claim beyond mere
  co-occurrence, with no source support, fails this.
- seed_engagement: one of "strong", "partial", "none". Does this
  reading actually transform the shared resisting_detail and cited
  evidence, or does it cite an anchor and then pivot to something more
  convenient? Judge the candidate's own seed_engagement claim against
  what it actually does -- do not accept the claim.
- engine_dependence: one of "strong", "partial", "generic". Would a
  generically curious reader with no specific instrument have produced
  essentially this same reading? Assessed as described above -- from
  the capsule, the interpretive_inference, the conceptual_shift, and
  the evidence used, never from engine_move alone.
- conceptual_movement: one of "strong", "partial", "none". Does the
  reading actually move somewhere (a real conceptual_shift), or does it
  restate the seed friction in different words?
- distinctive_contribution: one of "strong", "partial", "none". What
  would be missing from a plain, accurate summary of the source if this
  reading didn't exist? Judge this yourself; do not adopt the
  candidate's own claimed_contribution at face value.

Then set assessment to one of "qualifies", "does_not_qualify" by
applying this rule exactly, with no exceptions:

does_not_qualify if ANY of the following:
  factual_integrity is "fail"
  seed_engagement is "none"
  engine_dependence is "generic"
  conceptual_movement is "none"
  distinctive_contribution is "none"

Otherwise: qualifies.

This is a mechanical gate, not a holistic judgment call. Do not let an
otherwise-appealing candidate qualify despite failing one of these five
checks. Do not disqualify a candidate that passes all five just
because you personally find it less interesting than another.

Write "reason" as one or two sentences explaining the assessment.

SELECTING A WINNER

Only after every candidate has an independent assessment:

- If NO candidate qualifies: editorial_winner is null, runner_up is
  null, margin is "no_distinctive_contribution".
- If exactly ONE candidate qualifies: editorial_winner is that
  candidate, runner_up is null, margin is "clear". Being the only
  qualifying candidate is not automatically a strong win -- margin
  describes the win itself, and there was nothing to compare it
  against, so "clear" simply reflects that no rival qualified. Do NOT
  inflate this into an especially strong endorsement.
- If TWO OR MORE candidates qualify: among the qualifying candidates,
  distinctive_contribution and engine_dependence are the PRIMARY
  comparison dimensions -- choose editorial_winner using those first.
  Use conceptual_movement and seed_engagement as SECONDARY
  discriminators only when the primary dimensions leave candidates
  genuinely comparable. factual_integrity is pass/fail only at this
  point -- every qualifying candidate already passed it, so it is never
  a source of extra credit between them. runner_up must be the
  next-strongest QUALIFYING candidate -- never a candidate that did
  not qualify, no matter how close it seemed. margin is "clear" if the
  winner is substantially stronger, "close" if the top two are
  genuinely comparable.

DO NOT reward a candidate because its subject matter seems naturally
suited to its engine. Judge what the engine actually contributed in
THIS specific reading, not whether the pairing looks intuitive. DO NOT
select a winner merely because one is expected -- "no_distinctive_
contribution" is a complete, correct, useful answer when it's true.

OUTPUT

Return only JSON. No other text, no markdown code fences, no comments.

Example shape (illustrative values only -- write your own assessment
for the candidates actually supplied; include one entry per candidate
actually supplied, which may be fewer than four):

{
  "candidate_assessments": {
    "A": {
      "factual_integrity": "pass",
      "seed_engagement": "strong",
      "engine_dependence": "strong",
      "conceptual_movement": "strong",
      "distinctive_contribution": "strong",
      "assessment": "qualifies",
      "reason": "why this assessment was reached"
    }
  },
  "selection": {
    "editorial_winner": "A",
    "runner_up": null,
    "margin": "clear",
    "why": "what the winner has that the others lack, and why the runner-up came closest (or, if no_distinctive_contribution, why nothing qualified)"
  }
}
```

**`cj2-stage-c-v1` — user-input template:**

```
SEED FRICTION

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"
[cj1:a3 if present]

SOURCE SNAPSHOT

{source_snapshot}

CANDIDATE A

Engine A capsule:
  Instrument: {instrument_A}
  Move: {move_A}
  Strong contribution: {strong_contribution_A}
  Failure mode to avoid: {failure_mode_A}

Candidate A reading:
  seed_evidence_refs: {refs_A}
  additional_source_observations: {observations_A}
  engine_move: "{engine_move_A}"
  seed_engagement: "{seed_engagement_A}"
  interpretive_inference: "{interpretive_inference_A}"
  conceptual_shift: "{conceptual_shift_A}"
  claimed_contribution: "{claimed_contribution_A}"

[repeat for Candidate B / C / D -- only actually-surviving candidates
included; fewer than 4 is expected when some abstained or failed Stage
B provenance validation]
```

**Call conditions for the first reference probe (decided now, not
left to guesswork):** `temperature=0.0` for BOTH Stage A and Stage C.
Randomness is an unwanted fifth variable in an experiment specifically
designed to isolate one — whether changing only the perceptual
instrument changes the resulting knowledge. Stage A's prompt already
grants ample permission to interpret creatively without needing
sampling variance to produce it. If outputs later prove unnaturally
rigid across different sources, temperature becomes an empirical
follow-up question, not something guessed at in advance.

**Status: `cj2-stage-a-v1` and `cj2-stage-c-v1` are FROZEN design
candidates, static-preflight-clean.** No API calls made. No
production/repo code written (a temporary local `preflight.py` is not
part of this repo).

## FIRST REFERENCE PROBE — FIXTURE SELECTION (recorded 2026-08-11, BEFORE any Stage A call)

Three already-frozen CJ-1 Batch-1 PASS fixtures, reused as-is — no
refetch, no CJ-1 rerun:

| slug | topic | source domain | `source_sha256` |
|---|---|---|---|
| `05_dutch_painting_soldier` | De Hooch painting restoration / changed moral reading | culture / representation | `ad7b5852...71b3eafa` |
| `07_ai_cheating_exam` | take-home vs. in-person exam-score anomaly | institution / quantitative behavior | `f45155c0...5925770eb` |
| `01_cave_dna` | dating window + multiple candidate maker species / authorship uncertainty | science / archaeology / uncertainty | `0333af6a...b0201d7` |

Chosen for domain and friction-shape diversity, and specifically
because none of the three was used as a worked example inside either
frozen prompt's text. **No expected winning engine is pre-registered
for any of the three** — doing so would contaminate manual review the
same way topic routing was removed from the model. The question is
whether the four instruments produce genuinely different readings and
whether the comparator identifies the strongest actual contribution —
not whether a particular engine "should" win a particular topic.

**Bookkeeping correction (2026-08-11, later same day):** running this
probe required writing `automation/cj2_build_canonical_seed.py` and
`automation/cj2_reference_probe.py` — real, repo-local, EXPERIMENT-ONLY
code (uncommitted). The accurate status from here on is: **no
production pipeline code changed; experiment-only repo code added,
uncommitted.** Neither `cj2-stage-a-v1` nor `cj2-stage-c-v1` was
edited to run this probe.

Next: build canonical `cj1:aN` evidence for each fixture from its
existing validated CJ-1 v3.2 anchors (resolving any known
smart-quote transcription variant to the ORIGINAL source substring
before it becomes CJ-2 input — never passing the model's
punctuation-mutated version downstream), then run the 3-source
reference probe.

Canonical seeds built and verified (`automation/cj2_build_canonical_seed.py`
— every canonical excerpt confirmed as an exact substring of
`source_snapshot` before being persisted; script refuses to write a
seed otherwise). All three used the resolver only to LOCATE the
already-known smart-quote variant; the persisted value in every case
is the untouched original source text, never the model's transcription.

Probe executed: `automation/cj2_reference_probe.py`, `model =
openrouter/claude-sonnet-4.6`, `temperature = 0.0` for both stages, run
in an isolated `/tmp` scratch checkout on trident (hash-verified before
any call, scratch removed after pulling results back) — 12 Stage A
calls + up to 3 Stage C calls, 15 max, as planned. Neither
`cj2-stage-a-v1` nor `cj2-stage-c-v1` was edited before, during, or
after this run.

## FIRST REFERENCE PROBE — MECHANICAL RUN-INTEGRITY REPORT (before any editorial reading)

Per explicit instruction: mechanical integrity first, interpretation
only after. Two real harness/model issues surfaced and are reported
here precisely, distinguished from each other and from anything about
the engines' actual reasoning quality.

### 01_cave_dna

1. **Stage A**: P=candidate, S=candidate, Z=candidate, M=candidate.
2. **Schema integrity** (full manual structural check per the
   explicit checklist — non-empty strings, correct types,
   `removed_engine_test` shape, `abstain_reason` absent on
   candidates): **all 4 SCHEMA-VALID, zero issues.**
3. **Stage B**: P/S/Z valid, zero violations. **M: INVALID** — one
   `additional_source_observations` excerpt did not exact-match, and
   the resolver returned `no_match` (not `normalized_unique_match`) —
   **investigated, and this is NOT the known curly-quote transport
   issue.** M's excerpt concatenates two adjacent source sentences
   across a paragraph break, collapsing the source's `\n\n` into a
   single space. Verified directly: the excerpt is **NOT** an exact
   substring of the raw snapshot, but **IS** an exact substring once
   whitespace is normalized on both sides — i.e., every word is real
   and in the correct order, the only difference is a collapsed
   paragraph break. **This is a genuine fact, correctly quoted in
   substance, excluded by Stage B on a whitespace-normalization
   technicality distinct from the already-known apostrophe issue.**
   Classified as **`PROVENANCE_TRANSPORT_CONFOUNDED`**, not "Engine M
   failed to contribute" — M's candidate was fully formed, engine-
   specific, and its interpretive move does not depend on this excerpt
   being admissible (see analysis below); it is EXCLUDED from Stage C
   on a technicality, not because it was weak or unsupported.
4. **Stage C payload**: 3 survivors (P, S, Z). Deterministic mapping
   `{"A": "S", "B": "P", "C": "Z"}` (from `sha256(source_sha256 +
   ":" + label)`, sorted ascending). Confirmed: `removed_engine_test`
   absent from the projected payload; no `P`/`S`/`Z`/`M` label sent to
   Stage C.
5. **Stage C output**: **Initially reported as unparseable — this was
   a HARNESS BUG, not a model or prompt defect, confirmed by direct
   re-extraction.** The model did not comply with "no other text" —
   it prefixed ~1200 characters of prose reasoning before a correctly
   fenced, fully valid, complete JSON block. The original extraction
   logic only checked whether the response *started* with a fence, so
   it treated the whole prose+JSON string as unparseable. Re-extracting
   the fenced block directly: **valid JSON, schema-consistent, hard
   gate internally consistent** — all 3 candidates `qualifies`,
   `editorial_winner: B` (Engine P), `runner_up: A` (Engine S), `margin:
   close`. Orchestration rule (2+ qualifiers) correctly followed.

### 05_dutch_painting_soldier

1. **Stage A**: P=candidate, S=candidate, Z=candidate, M=candidate.
2. **Schema integrity**: **all 4 SCHEMA-VALID, zero issues.**
3. **Stage B**: **all 4 valid, zero violations.** No transport issues
   this time — every additional observation (where present) exact-
   matched.
4. **Stage C payload**: 4 survivors. Deterministic mapping `{"A": "Z",
   "B": "P", "C": "M", "D": "S"}`. Confirmed: `removed_engine_test`
   absent; no persona/engine labels present.
5. **Stage C output: GENUINELY INVALID — confirmed real truncation,
   not a harness bug.** Same prose-preamble behavior as `01_cave_dna`,
   but this time the response is cut off mid-string inside candidate
   B's `distinctive_contribution` value, with no closing brace and no
   closing fence — verified by brace-balance check (never returns to
   depth 0) and by the raw string simply ending mid-word. `max_tokens`
   for this call (2200) was insufficient once ~2000+ characters were
   spent on the unrequested prose preamble before the JSON even began.
   **No candidate_assessments, no selection, recoverable from this
   run for this source.** Per explicit instruction: not rerun. This
   source's Stage C result is **UNAVAILABLE**, not "no winner" and not
   "all candidates failed" — the comparator's actual judgment for this
   source was never captured.

### 07_ai_cheating_exam

1. **Stage A**: P=candidate, S=candidate, Z=candidate, M=candidate.
2. **Schema integrity**: **all 4 SCHEMA-VALID, zero issues.**
3. **Stage B**: **all 4 valid, zero violations.** S's one additional
   observation (the campus-shooting sentence) exact-matched on the
   first try — independently re-verified against the raw source text
   below (see grounding check).
4. **Stage C payload**: 4 survivors. Deterministic mapping `{"A": "P",
   "B": "S", "C": "Z", "D": "M"}`. Confirmed: `removed_engine_test`
   absent; no persona/engine labels present.
5. **Stage C output**: **Valid JSON, no preamble this time (started
   directly with a fenced block), schema-consistent.** Hard gate
   internally consistent — all 4 `qualifies`. `editorial_winner: A`
   (Engine P), `runner_up: D` (Engine M), `margin: close`.
   Orchestration rule (2+ qualifiers) correctly followed.

### Harness/model issues summary — none of these are CJ-2 architecture failures

- **`PROVENANCE_TRANSPORT_CONFOUNDED` (1 instance, `01_cave_dna`
  Engine M):** a real, accurately-quoted fact excluded from Stage C
  purely because the model collapsed a paragraph break while quoting
  it. The resolver's narrow scope (smart-quote folding only) correctly
  did NOT rescue this — it is a genuinely different transport failure
  than the known apostrophe issue, not a bug in the resolver, but it
  is evidence the resolver's scope may eventually need extending to
  whitespace/paragraph-break normalization too. Not done here — flagged
  only.
- **Stage C prose-preamble non-compliance (2 of 3 calls, `01_cave_dna`
  and `05_dutch_painting_soldier`):** despite "Return only JSON. No
  other text..." stated directly in the frozen prompt, the model
  prefixed substantial prose reasoning before the JSON in 2 of 3 calls
  at `temperature=0.0` — inconsistent compliance with an explicit
  instruction even under deterministic decoding. For `01_cave_dna` this
  was recoverable (the JSON itself was complete); for
  `05_dutch_painting_soldier` the preamble consumed enough of the
  token budget that the JSON was never completed. **This is a genuine
  finding about this model's instruction-following on this specific
  task, not something to silently patch mid-probe** — flagged for
  whoever revises the harness (a higher `max_tokens` and/or a stronger
  anti-preamble instruction are both plausible fixes, neither applied
  here).
- **Harness extraction bug (this probe's own code, not the frozen
  prompts):** the JSON-extraction logic assumed a response either
  starts with a code fence or is bare JSON; it did not handle "prose
  followed by a fenced block," causing `01_cave_dna`'s genuinely valid
  Stage C output to be misreported as a parse failure until manually
  re-checked. Not fixed in the probe script (per explicit instruction
  not to modify anything mid-probe) — flagged for the next harness
  revision.

**Net effect on available data:** 12/12 Stage A candidates are fully
schema-valid. 11/12 pass Stage B cleanly; 1/12 (`01_cave_dna` M) is
excluded on a transport technicality, not a content failure. 2/3
Stage C runs produced usable comparator output (`01_cave_dna` after
correcting the extraction bug; `07_ai_cheating_exam` cleanly); 1/3
(`05_dutch_painting_soldier`) has NO usable Stage C output at all.

## FIRST REFERENCE PROBE — CROSS-SOURCE COMPARISON TABLE

One sentence per cell: the conceptual move, not the prose.

| | CAVE DNA | DE HOOCH | AI EXAM |
|---|---|---|---|
| **Engine P** (mediation/transmission) | The dating method only produces a one-sided minimum bound, not a location in time — an asymmetry the migration-window argument quietly treats as if it were precise. | The overpainting didn't just remove information — the removal process itself manufactured a new, opposite moral reading. | The take-home format wasn't a leaky channel that let false scores through — it was a generative medium that manufactured a population of apparent competence. |
| **Engine S** (actor-environment relation) | The cave's own mineral-deposition process is an active agent that simultaneously enables the date and forecloses the identity — producing the uncertainty, not just hosting it. | The moral content was never in any single figure but in the spatial/behavioral relation between figures; removing the soldier disabled that relational field rather than just cutting content. | The classroom itself became an environment some students couldn't enter (after the shooting) and then abruptly reinstated — the score gap partly records an actor-environment mismatch, not only cheating. |
| **Engine Z** (measurement/classification→judgment) | A minimum-age bound is being used to do a job (locate an event in a window) that this kind of measurement cannot logically perform — "double-proxy stacking" generating false confidence. | The alteration worked by destroying a comparative classification structure inside the painting (who's drinking vs. not) — "innocence" is a measurement artifact, not a moral description. | The 48.6% is treated as ground truth while being just as statistically anomalous as the 96% — the two exams measured different constructs on different (self-selected) populations, so neither score is a clean proxy. |
| **Engine M** (promise vs. operational practice) | Authorship-by-stylistic-complexity only works if a prior claim about non-sapiens cognitive limits is granted — a load-bearing premise the methodology needs but never actually tests. | The "more figures = more moral" promise only holds if the specific social-geometry mechanism (differential drinking) stays intact — removal disabled that mechanism, not just the image content. | The assessment's promise (a score means the student learned it) depends on an operational condition (student authorship of answers) that was silently unenforced — and enrollment data show that gap became structurally load-bearing. |

## FIRST REFERENCE PROBE — QUALITATIVE ANALYSIS

**A. DIFFERENTIATION — did the four engines notice different things,
or four differently-worded versions of one argument?**

Reading all 12 (well, 11 admissible + 1 transport-excluded) readings
against their own source text, not just their labels: **the four
engines converge on the SAME underlying observation shape far more
than the capsules' vocabulary difference initially suggests, but they
do not converge on the same TARGET within that shape.** Every single
reading, across all three sources, ultimately identifies "a
formal/apparent certainty is being produced by a specific hidden
mechanism the source doesn't examine" — that generic shape recurs 12
times. Read past the shape into WHAT each identifies as the load-
bearing gap, though, and there's real difference within each source:
in AI Exam, P locates the gap in the FORMAT (take-home as generative
medium), S locates it in the ENVIRONMENT (classroom-as-actor across
time), Z locates it in the INSTRUMENT (two exams as incomparable
measurements), M locates it in the UNENFORCED CONDITION (authorship).
These are not paraphrases of each other — P's reading doesn't mention
the classroom at all; S's reading doesn't touch measurement validity;
Z's never invokes the shooting; M's is about enforcement, not format
or environment or comparability. See CONVERGENCE below for the more
important, harder question this shape-level similarity actually raises.

**B. ENGINE DEPENDENCE — does each candidate really arise from its
capsule, or could capsules be swapped without changing the reading?**

Spot-check by trying to imagine each engine's specific target claim
coming from a different capsule:
- AI Exam Engine S's core move (classroom-as-actor, the shooting as
  the initiating environmental event) is NOT reachable from P's
  transmission lens, Z's measurement lens, or M's promise/practice
  lens — none of those would think to treat "reluctance to enter a
  physical room" as the analytically load-bearing fact. This is the
  single cleanest engine-dependent reading in the whole probe.
- AI Exam Engine Z's "two exams measured different constructs on
  different self-selected populations" is the one Stage C itself
  flagged as only `engine_dependence: "partial"` — correctly, on
  inspection: a generically careful reader doing ordinary methods
  critique could reach this without Z's specific classification lens.
  Real, useful, but the LEAST engine-specific of the four in this
  source.
- Cave DNA: P's "one-sided minimum bound" and Z's "measurement can't
  perform this logical job" are close cousins (both are about what
  the dating method can/can't establish) — genuinely harder to
  imagine as un-swappable between P and Z specifically, more distinct
  from S and M.
- De Hooch: S's "relational field between figures, not content in any
  one figure" is the most obviously S-specific (nothing else engages
  spatial/compositional relation this directly); P's "removal as
  active moral-inversion process" and M's "social-geometry mechanism
  disabled" are closer to each other than either is comfortable with.

**C. CONTRIBUTION — did any reading add something beyond an accurate
summary, and did conceptual_shift cross into another explanatory
frame rather than just rename the friction?**

Yes, clearly, in multiple cases — the strongest test is: does the
`conceptual_shift` propose a mechanism the source itself never states?
AI Exam M ("the operational dependency — student authorship — was
silently absent, and enrollment data show that gap became load-
bearing for participation") is not in the source; the source states
the scores and the withdrawals as separate facts, M's reading is what
connects them into a claim about WHY the take-home format worked as
well as it did for a specific population. Cave DNA M (the unstated
cognitive-capacity premise about non-sapiens hominins) is similarly a
real interpretive addition, not a restatement — the source never
raises this premise at all, M constructs it as the missing step. Both
qualify as genuine interpretive leaps under the frozen contract: real,
useful, going beyond the source's own theory, without inventing a new
FACT to do it (both work entirely from cj1:aN + accurately-quoted
additional observations).

**D. GROUNDING — RETRACTED (2026-08-11, review correction). Do NOT
read this section's original conclusion; see `## FIRST REFERENCE PROBE
— OFFLINE SEMANTIC FACTUALITY AUDIT` below, which supersedes it.**

The original text here claimed "no smuggled facts found," verified
only at the coarse level of "is every named entity/number/quote real."
That check is real but insufficient — it catches Phase 1.6-style crude
fabrication (an invented person, date, quote) and did correctly clear
the one alarm actually checked at that level (AI Exam Engine S's
"campus shooting" citation IS real and exactly quoted). But a full
sentence-by-sentence offline audit of all 12 candidates against their
complete source texts found a DIFFERENT, subtler failure mode that
this coarse check cannot see: candidates that start from a true,
correctly-quoted source fact, then strengthen it — via modality,
causality, invented mechanism, or population/motivation claims — into
something the source does not establish, while still citing only real
excerpts. **This is the probe's first real observed CJ-2 safety
failure: `SEMANTIC_FACT_LAUNDERING`.** Seed discipline (no cite-and-
abandon) still holds as originally stated — that finding is unaffected
by this correction.

**E. ABSTENTION — did engines abstain when they had little to add, or
did the prompt pressure all four into manufacturing candidates?**

**Zero abstentions across all 12 Stage A calls.** This is worth
flagging as an open question, not celebrating as a clean result: with
n=12 and 0 abstentions, this probe cannot yet distinguish "these three
sources genuinely gave all four engines real purchase" from "the
prompt's abstention permission isn't being exercised even when it
should be." AI Exam Z's own Stage-C-assessed `engine_dependence:
"partial"` is the closest thing to evidence that a weaker-than-ideal
candidate WAS produced rather than an honest abstention in its place —
worth watching in a larger future batch, not concluded here.

**F. COMPARATOR — did Stage C independently catch weak/generic
candidates, detect unsupported relationships, and choose defensibly?**

Where Stage C's output was actually available (`01_cave_dna`,
`07_ai_cheating_exam`): yes, on the evidence in the outputs themselves.
AI Exam: Stage C independently marked Z's `engine_dependence` as
`"partial"` with a specific, correct reason ("a generically careful
reader could reach this without the specific classification/proxy
engine") — exactly the kind of independent re-derivation the frozen
prompt demands, not an acceptance of the candidate's own framing (Z's
own `removed_engine_test.still_holds_without_engine` had claimed
`false`, i.e. claimed strong dependence — Stage C did NOT simply defer
to that self-assessment, which is the correct behavior per the
Stage-C-view projection design). Cave DNA: Stage C's stated reasoning
for preferring B (Engine P) over A (Engine S) — "B's payoff is a
concrete logical consequence that changes what the attribution
argument actually rests on... A's payoff is somewhat more metaphorical"
— is a real, inspectable, defensible distinction grounded in the
actual readings, not a generic tie-break. **The 1/3 missing Stage C
result (De Hooch) means this question cannot be answered for that
source at all this round** — a real gap in this data, not a comparator
failure (there is no comparator output to evaluate).

**G. PORTABILITY — does the same engine operate meaningfully across
different domains, or does one engine only work on one narrow class of
source?**

All four produced schema-valid, seed-engaged, non-abstained candidates
across all three very different domains (culture/representation,
institution/quantitative behavior, science/archaeology) — on this
narrow evidence, no engine failed to produce SOMETHING on a domain it
"shouldn't" fit by any topic-affinity intuition (Engine S, the most
literally spatial-sounding capsule, produced a genuinely engine-
specific and Stage-C-endorsed-as-strong reading on a quantitative
exam-scores story, not just on the visual/spatial De Hooch source).
Whether that something is EQUALLY strong across domains is a separate
question this 3-source, 0-abstention probe cannot answer yet — no
engine's candidates were assessed as `does_not_qualify` anywhere Stage
C output exists, so there's no failure signal to analyze, only an
absence of failure signal (which is informative but not conclusive at
n=3).

**H. CONVERGENCE — the most important question, per your framing: are
these four vocabularies for one argument, or four engines?**

**Genuinely mixed verdict, and worth stating precisely rather than
picking the comforting reading.** At the level of ABSTRACT SHAPE, yes,
there is real convergence: all 12 readings are some version of "an
apparent certainty is produced by a mechanism the source doesn't
examine," which is close to the exact worry your message named
("the apparently neutral system is not neutral"). If CJ-2 is judged
only at that altitude, it looks like one CripMinds house argument
wearing four vocabularies. **But at the level of WHAT SPECIFICALLY is
identified as the hidden mechanism, the four are not interchangeable**
— P consistently targets the TRANSMISSION/FORMAT/PROCESS, S
consistently targets the ENVIRONMENT/RELATIONAL-FIELD, Z consistently
targets the MEASUREMENT/PROXY VALIDITY, M consistently targets the
UNENFORCED OPERATIONAL CONDITION, across all three unrelated domains,
without being told the domain in advance or seeing each other's work.
That consistency of TARGET across domains, from capsules that never
mention a subject area, is itself evidence the capsules encode
something more than a stylistic tic — it's evidence of an actual
different question each engine is trained to ask, even though the
downstream RHETORICAL SHAPE of "hidden mechanism the source doesn't
examine" is currently shared by all four (that shared shape may
simply be what "grounded interpretive friction" always looks like once
any of these four instruments is pointed at it — CJ-1's own frozen
`friction_type` taxonomy has the same property: multiple genuinely
different frictions all cash out as "X and Y don't sit together"). **This
is exactly the tension the whole CJ-1→CJ-2 design has been managing
from the start, now visible in real output rather than hypothesized:
convergent SHAPE with divergent TARGET.** Whether that's "good enough"
is an editorial judgment this document does not make.

**Correction, folded in after the semantic audit below: the
convergence read above should NOT be taken as settled.** Some of what
made P/S/Z/M's targets read as cleanly distinct in this analysis is
itself partly built on the same laundered intensifications the audit
below identifies — most visibly Engine S's contribution in both Cave
DNA and AI Exam, and Engine M's in AI Exam. The corrected overall
judgment, stated precisely: **the perceptual engines show real
differentiation, but CJ-2 v1 has not yet demonstrated that it can
distinguish a bold interpretation from a strengthened factual
premise.** That is the next problem — not convergence.

## FIRST REFERENCE PROBE — OFFLINE SEMANTIC FACTUALITY AUDIT (2026-08-11, review correction — supersedes section D above)

**No new model calls. No prompt/capsule edits.** All 12 already-
existing Stage A candidates re-read in full, sentence by sentence,
against their complete frozen `source_snapshot` text — not just the
coarse "is every named entity real" check the original report ran.

### The failure class

**`SEMANTIC_FACT_LAUNDERING`**: a candidate starts from a real,
correctly-quoted source fact, then — inside `interpretive_inference`,
`claimed_contribution`, or (once, at the comparator level) Stage C's
own reasoning — strengthens it via modality, causality, mechanism, or
population/motivation claims into a proposition the source does not
establish, while never citing an unreal excerpt. Stage B's
substring-exact check cannot see this (every excerpt is real); Stage
C's `factual_integrity` dimension was explicitly designed to catch
exactly this and, in the 2/3 runs where its output exists, caught
**zero** of the roughly six instances found below.

Distinct from crude Phase 1.6-style fabrication (an invented name,
date, quote, or event) — every noun in every laundered sentence below
is real. What's invented is the STRENGTH of the relationship between
real nouns, not the nouns themselves. Five subtypes observed, matching
(and extending) the pre-registered list:

- **`MODALITY_HARDENING`** — a hedge/preference in the source becomes
  a capability/impossibility claim.
- **`CAUSALITY_HARDENING`** — co-occurring facts become "A caused B"
  or "A depends on B."
- **`MECHANISM_INVENTION`** — a specific causal mechanism is asserted
  that the source never describes at all.
- **`MOTIVATION_INVENTION`** — an internal mental state/intent is
  attributed to a person the source never characterizes that way.
- **`POPULATION_RELATION_HARDENING`** — two groups/subsets the source
  never explicitly links (e.g. "the dropouts" and "the high scorers")
  are treated as the same or overlapping population.

### Per-candidate audit

**Key finding stated up front: 6 of 12 candidates are fully clean —
notably, ALL FOUR De Hooch candidates.** Intensification concentrated
almost entirely in Cave DNA's Engine S and in 3 of AI Exam's 4
engines.

| candidate | problematic wording | exact source support | classification | Stage C caught it? | destroys contribution if removed? |
|---|---|---|---|---|---|
| **Cave DNA / P** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **Cave DNA / S** | "the same environmental process... simultaneously enables dating and forecloses identification"; "erasing the biological trace of whoever pressed their hand"; "occludes the maker's identity" | Source: carbonate crust formed OVER the painting, used ONLY for uranium-series dating. Source separately mentions ancient DNA CAN be recovered from cave walls elsewhere (a different Spain/Portugal study) — never connects carbonate deposition to biological-signature erasure at all, for this or any case. | **`MECHANISM_INVENTION`** — the central, load-bearing claim of the whole reading | **NO** — Stage C `factual_integrity: "pass"`, called the payoff "somewhat more metaphorical," not unsupported (recovered `candidate_assessments.A`, see below) | **Partially** — the vivid "erasure" mechanism must be cut, but a weaker version survives: multi-species regional occupancy (source-real) + carbonate-dates-crust-not-painting (source-real) still support "the environment structurally under-determines identity," just without the invented erasure mechanism |
| **Cave DNA / Z** | "stylistic complexity is itself a culturally and cognitively contested category" (aside, not load-bearing) | Not source-stated; a general disciplinary claim, not a claim about this study | `AMBIGUOUS_BOUNDARY`, minor, non-central | N/A (Stage C gave Z `does_not_qualify` anyway, on redundancy with P, not on this) | No — core "minimum bound ≠ point-in-time" argument doesn't depend on this aside |
| **Cave DNA / M** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **De Hooch / P** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **De Hooch / S** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **De Hooch / Z** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **De Hooch / M** | (none found) | — | `CLEAN_INTERPRETATION` | N/A | — |
| **AI Exam / P** | "those whose apparent competence existed only as a product of the take-home medium had no stable identity to bring into the in-person room"; "the prior measurement's object (the 96%-scoring student body) ceased to exist" | Source states 96% avg, 48.6% avg, and separately that some students dropped/didn't sit the final — never links WHO dropped to WHO scored 96% | **`POPULATION_RELATION_HARDENING`** | not checked directly (this candidate won; Stage C's reasoning for the win doesn't hinge on this specific clause) | **No** — P's core `conceptual_shift` ("format as active producer of the reality it records") is fully intact without ever mentioning the dropouts; this clause is decorative, not load-bearing |
| **AI Exam / S** | observation itself: "the physical classroom had become aversive or inaccessible to some students"; inference: "could not re-enter the environment at all"; "not simply cheating; they were adapting to the environment they were actually in"; "legible as environmental mismatches" causing the score drop and withdrawals | Source: "Some students were **reluctant** to return to the classroom after a campus shooting... **so** I administered the midterm as a take-home exam" — only the causal link (shooting→format change) is source-stated; everything about inaccessibility, inability to re-enter, adaptive motive, or the score drop/withdrawal being caused by "environmental mismatch" is not | **`MODALITY_HARDENING`** + **`MOTIVATION_INVENTION`** + **`CAUSALITY_HARDENING`** — three distinct instances in one candidate, the most laundered candidate in the probe | **NO** — Stage C `factual_integrity: "pass"`, `engine_dependence: "strong"`, all dimensions "strong," runner-up | **Substantially, yes** — strip all three and what remains is: "the format change was triggered by an environmental factor (real), which the article doesn't examine further" — real, S-flavored, but far thinner; it can no longer explain the score gap or the withdrawals, which is what made this reading feel complete |
| **AI Exam / Z** | "[the 48.6% cohort] likely removes lower-performing students who had relied on AI and **recognized they couldn't pass without it**" | Source never characterizes who dropped or why; hedged with "likely," more epistemically cautious than S's flat assertions | **`POPULATION_RELATION_HARDENING`** + mild **`MOTIVATION_INVENTION`**, hedged | **NO** — Stage C `factual_integrity: "pass"` (though Stage C independently caught a DIFFERENT weakness in Z: `engine_dependence: "partial"`, for unrelated reasons — see analysis B above) | **No** — the core "selection effect exists because the population changed" argument survives fully on the unadorned fact that some students are simply absent from the second average, without characterizing who they were or why |
| **AI Exam / M** | "the gap between promise and practice had become **load-bearing** for [some students'] participation"; "the take-home format... was **sustaining** enrollment"; enrollment "**depended on** the operational condition remaining unenforced" | Source states some students dropped/no-showed — never establishes that unenforced authorship caused their continued enrollment, or that its removal caused their departure | **`CAUSALITY_HARDENING`** / **`NECESSITY_DEPENDENCY_HARDENING`** | **NO** — Stage C `factual_integrity: "pass"`, `engine_dependence: "strong"`, all dimensions "strong," `qualifies` | **Substantially, yes** — the core "assessment promise requires an unenforced operational condition (authorship)" survives without the enrollment-dependency claim, but the most narratively striking part of the reading (the 96%→dropout causal arc) does not |

### What Stage C actually caught, precisely

Recovered `candidate_assessments` for Cave DNA (the harness-bug-
recovered run) confirms the finding directly — Stage C's own words on
Candidate A (Engine S):

> "The reading genuinely reframes the cave environment as an active
> geological agent whose mineral-accretion process simultaneously
> enables dating and forecloses identification, producing the
> authorship uncertainty as a structural environmental artifact... a
> move that is engine-dependent and not present in a plain summary of
> the source." — `factual_integrity: "pass"`

Stage C's earlier `selection.why` text calls this same claim "somewhat
more metaphorical" when comparing it to the winner — which is Stage C
noticing the claim is LESS CONCRETE than it should be for a factual
claim, without ever asking whether that concreteness gap means the
claim isn't actually established. **This is the precise failure
mode**: Stage C's `factual_integrity` check is being satisfied by "the
cited excerpts are real" rather than "the causal/mechanistic
relationship asserted between them is real" — exactly the gap the
frozen Stage C prompt's own A-causes-B example was written to close,
and did not close here. Across both available Stage C runs, the catch
rate on the ~6 identifiable intensification instances above is **0/6**.

### What this does and doesn't mean

**Does NOT mean**: the engine architecture failed, or that
differentiation is fake. De Hooch — the source with the densest direct
quotation (multiple curator quotes, an exact game-rule description) —
produced ZERO intensification across all four engines. That is a real,
informative pattern, not proof the other two sources are hopeless: it
suggests intensification risk may correlate with how much a source
narrates explicitly versus how much a candidate must infer about
unstated mechanism, motivation, or population dynamics — a hypothesis,
not a conclusion, worth testing on a larger batch, not decided here.

**Also worth flagging as a pattern, not a conclusion**: in this n=3
sample, Engine S and Engine M produced more/worse intensification than
P and Z. S's and M's capsule "Move" instructions ask them to name an
active/hidden process or dependency the source doesn't state outright
— an intrinsically more generative, easier-to-oversell instruction than
P's and Z's "identify the limit of what a measurement/format can
support," which is intrinsically subtractive and harder to
accidentally oversell. Plausible, not established at n=3.

**Does mean**: CJ-2 v1's Stage C, as written, is not currently
distinguishing a bold interpretation from a strengthened factual
premise, despite being explicitly instructed to. The `factual_integrity`
dimension needs a sharper test before this architecture can be trusted
with real interpretive risk-taking. Not designed here — Stage C is not
being edited in this document; per explicit instruction, this is a
diagnosis, not yet a fix.

## FIRST REFERENCE PROBE — STATUS (updated after semantic audit correction)

Data: 12/12 Stage A schema-valid, 11/12 Stage-B-valid (1 transport-
excluded, not content-failed), 2/3 Stage C outputs usable (1
unrecoverably truncated). **First real observed CJ-2 safety failure:
`SEMANTIC_FACT_LAUNDERING`** — 6 of 12 candidates fully clean
(notably all 4 De Hooch candidates), 6 show real-fact-to-strengthened-
claim intensification (worst in Cave DNA's Engine S and 3 of AI Exam's
4 engines), and Stage C caught **0 of ~6** identifiable instances
across both available Stage C runs despite being explicitly designed
to police exactly this boundary. The retracted "zero smuggled facts"
conclusion is corrected in the `## OFFLINE SEMANTIC FACTUALITY AUDIT`
section above — do not cite the original section D text.

**Corrected overall judgment**: the perceptual engines show real
cross-domain differentiation (the cross-source table and most of the
convergence analysis still stand), but CJ-2 v1 has not yet demonstrated
it can distinguish a bold interpretation from a strengthened factual
premise. That is the open problem now, not convergence.

**Diagnosis corrected (2026-08-11, same day) — "not implicated" was
too strong.** There are TWO distinct failures here, not one:

- **GENERATION failure**: Stage A sometimes converts interpretation
  into strengthened fact in the first place — that's where every
  laundered claim in the audit table above actually originates.
- **DETECTION failure**: Stage C, explicitly tasked with catching
  exactly this, caught none of it.

Both matter, and conflating them ("Stage C failed, so fix Stage C")
risks a fix that only makes the detector stricter without addressing
why the generator produces unsafe claims in the first place. The
audit's own observation that Engine S/M — whose capsule "Move"
instructions specifically invite naming an active/hidden mechanism or
dependency — concentrated the intensification is a real signal Stage A
is not fully exonerated by. **Not enough evidence yet to change Stage
A or the capsules** (n=3, and the S/M-vs-P/Z pattern is a hypothesis,
not established) — they remain untouched for now, but for the reason
"insufficient evidence to act," not "cleared."

`cj2-stage-a-v1` / `cj2-stage-c-v1` remain frozen exactly as composed.
No v2 prompts, no production wiring, no Stage D brief, no CJ-1
changes, no reruns.

Flagged, logged separately, deliberately NOT mixed into the semantic
audit: the whitespace-transport gap in the resolver's scope (a
candidate whitespace+quote-fold normalization extension is plausible,
not implemented); Stage C's inconsistent JSON-only compliance and this
probe's own harness extraction bug (a "recover the first complete
JSON object wherever it occurs, raise Stage C's token budget" fix is
plausible, not implemented); the missing `05_dutch_painting_soldier`
Stage C result; the zero-abstention result (informative, not
conclusive at n=3).

Reported for review. Next decision, not made here: how to sharpen
Stage C's `factual_integrity` test so it actually enforces "conceptual
inference may go beyond the source; factual assertion may not" —
before any further probe, prompt change, or production discussion.

**Superseded by the architecture change below** — the decision made
was not "sharpen Stage C's test" but "move the test out of Stage C
entirely." See `## STAGE B2` below.

## STAGE B2 — SEMANTIC FACTUALITY GATE (2026-08-11, architecture change justified by observed evidence, not hypothetical design)

**This is the first CJ-2 architecture change made because a probe
actually showed a failure, not because a review round imagined one.**
No prompts written, no code, no API calls, no Stage A/capsule changes.

### Why Stage C can't be both judge and jury here

Stage C is currently asked to do two things that pull against each
other: (1) find the boldest, most engine-dependent conceptual
contribution, and (2) be suspicious enough to disqualify unsupported
factual strengthening. The probe evidence shows this conflict is real,
not theoretical — Stage C's own praise for the winning/runner-up
candidates in both available runs is BUILT FROM the same moves that
should have triggered `factual_integrity: "fail"` ("a move that is
engine-dependent and not present in a plain summary," about a claim
this audit found to be a `MECHANISM_INVENTION`). An evaluator asked to
reward boldness and police fabrication in the same pass will tend to
let bold-and-fabricated slide, because the very reasoning that
recognizes boldness recognizes it as boldness, not as risk. **The fix
is architectural separation, not a stricter version of the same
combined instruction.**

### Corrected pipeline

```
Stage A   -- 4 engines, independent, blind, produce reframes (unchanged)
Stage B   -- deterministic excerpt/provenance validation (unchanged)
Stage B2  -- SEMANTIC FACTUALITY GATE (NEW)
             one candidate at a time, engine-blind, source-only
             no engine competition, no reward for contribution
Stage C   -- engine-contribution comparison, B2-safe candidates ONLY
             (factual_integrity dimension REMOVED -- guaranteed upstream)
```

("B2-safe" throughout this document is shorthand for
`effective_verdict=safe` — a value the ORCHESTRATOR computes after
B2's model call, never something the B2 model itself outputs. See
`## CORRECTION (round 3)` below for the exact computation.)

### Stage B / B2 / C responsibility, precisely

| | Stage B | Stage B2 | Stage C |
|---|---|---|---|
| Checks | excerpts are real substrings; ID references resolve; count caps | do the candidate's claims overclaim beyond what the source establishes | is this reading genuinely engine-dependent and distinctive |
| Method | deterministic string matching, no LLM | LLM, but per-claim decomposition, not holistic judgment | LLM, holistic comparison across survivors |
| Sees other candidates? | no | no | yes (anonymized) |
| Sees engine capsule? | no (doesn't need to) | **no — deliberately** | yes |
| Rewards boldness? | n/a | **no, must not** | yes, that's its job |
| Can disqualify? | yes (provenance) | yes (factual safety) | yes (weak/generic contribution) |

### Why B2 must be engine-blind — this is the load-bearing design choice

If B2 sees the engine capsule, it can rationalize: *"well, this is an
environment lens, so calling the classroom 'inaccessible' is a
reasonable reading of that lens."* That is exactly the failure Stage C
already committed, just relocated. **B2's only question is whether a
proposition the candidate needs is true about the source — the
engine's elegance is not evidence for or against that.** `"reluctant
to return"` does not become `"inaccessible"` no matter how well that
serves the actor-environment instrument. B2 sees `source_snapshot`,
`resisting_detail`, canonical `cj1:aN` evidence, and the candidate's
claim-bearing fields — but does NOT see: the engine capsule, the
engine/persona label, any other candidate, `removed_engine_test`,
topic affinity, or Stage C scores — the same downstream-projection
discipline already used for Stage C's `removed_engine_test` stripping,
generalized: NOTHING that could let B2 rationalize a claim as
acceptable because of who's making it now reaches B2 either.

It is explicitly NOT asked "is this interesting," "is this
distinctive," "is this engine-specific," or "is this a good article"
— those questions don't exist in B2's world at all, not even as
context.

### CORRECTION (round 2, same day): B2's audit scope was too narrow

The round-1 design scoped B2 to "the propositions
`interpretive_inference`/`conceptual_shift` actually need." That
scope would have missed the AI Exam Engine S failure at its actual
point of origin: the strengthening from "reluctant to return" to
"aversive or inaccessible" happened INSIDE
`additional_source_observations[0].observation` — a field the round-1
scope wouldn't have reached, because `interpretive_inference` doesn't
strictly need that exact wording to make its point; it just inherited
the already-strengthened claim. `engine_move`, `seed_engagement`, and
`claimed_contribution` can carry the same risk, and Stage C sees most
of them directly. **B2 must audit every factual proposition present in
ANY of the candidate's claim-bearing fields, not only the ones its
central inference logically requires:**

```
additional_source_observations[].observation
engine_move
seed_engagement
interpretive_inference
conceptual_shift
claimed_contribution
```

Not a mechanical parse of every grammatical clause — B2 extracts every
proposition in those fields that purports to describe what actually
happened, existed, was measured, was said, caused/enabled/prevented
something, was necessary, motivated an actor, or applies to a
population. Scene-setting and connective prose with no such claim
inside it is not decomposed.

**New axis: `importance` — `load_bearing` | `supporting` |
`incidental`.** Recorded, but does NOT gate safety on its own: an
unsupported factual proposition makes the candidate unsafe even if
`incidental`, because Stage C still reads the full candidate object
and can be swayed by a flourish that was never load-bearing to begin
with. `importance` is diagnostic (useful for a human deciding whether
a future "trim the bad claim, keep the rest" repair is worth building)
— not, in this v1 design, an exemption.

### CORRECTION (round 2): source support ≠ evidence declaration

A second, distinct failure mode the round-1 design didn't cover:
Stage A's own frozen contract requires every factual premise beyond
canonical `cj1:aN` evidence to be routed through
`additional_source_observations`. If Stage A instead writes a new
factual premise directly into `interpretive_inference` WITHOUT
declaring it there, and B2 then goes looking and finds that the fact
genuinely exists somewhere in `source_snapshot`, a B2 that only checks
`support` would call it `safe` — **silently repairing a lineage
violation** and quietly making Stage A's declaration requirement
optional. That defeats the exact discipline Phase 1.6 and CJ-2's Stage
B were built to enforce.

**New axis: `declaration` — `declared` | `undeclared` |
`not_applicable`** (the last only for `interpretive_only` claims,
which never need declaring). A factual claim can now land in one of
three real positions, not two:

- **supported + declared** → a safe factual premise.
- **supported + undeclared** → the fact is real, but Stage A violated
  the evidence-declaration contract. New problem type:
  **`UNDECLARED_FACTUAL_DEPENDENCY`.** Not silently rescued just
  because B2 could find it. Unsafe.
- **unsupported** → the original `SEMANTIC_FACT_LAUNDERING` failure.
  Unsafe regardless of declaration status.

### CORRECTION (round 2): do not resolve ambiguity by defaulting to interpretive

Round 1's "uncertain whether interpretive-vs-factual → lean
interpretive" rule is retracted as an escape hatch that sits exactly
where laundering hides. Every laundering case found in the audit
SOUNDS interpretive on first read — "the gap became load-bearing," "the
environment foreclosed identification," "the classroom became
inaccessible." Forcing a binary interpretive/factual call before the
gate is calibrated would let the model resolve the hardest cases by
simply asserting they're conceptual.

**Real third role: `boundary_ambiguous`** — not a revival of the
rejected `source_established` role (that stayed removed; source
establishment is a `support` status, never a claim `role`).
`boundary_ambiguous` means: *I cannot confidently determine whether
this proposition is functioning as conceptual framing or as a claim
that something actually happened.*

B2's verdict becomes three-valued: **`safe` | `unsafe` | `ambiguous`**.
For the research architecture (not a production policy — not decided
here):

```
safe      → proceeds to Stage C
unsafe    → excluded, same treatment as Stage-B-invalid/abstained
ambiguous → withheld from Stage C AND surfaced for review
             (a distinct third bucket -- not silently merged into
             either safe or unsafe; valuable calibration data for
             a gate that hasn't been tested against real output yet)
```

Not choosing which way `ambiguous` resolves in eventual production —
deliberately deferred until there's real data on how often it fires
and what it looks like.

### CORRECTION (round 2): scope is "everything presented," not "everything logically necessary"

Round 1 scoped factual-dependency auditing to propositions the
argument "cannot survive without." Too permissive: an unsupported
factual flourish that ISN'T strictly necessary to the `conceptual_shift`
can still be read by Stage C, still impress it, still get a candidate
rewarded for it. **The correct scope is: every factual proposition
presented as part of the candidate's case and visible to downstream
evaluation** — not filtered by whether the interpretation would
survive its removal. `importance` (above) records how central a claim
was, for future repair-design purposes; it does not narrow which
claims get audited for safety in the first place.

### Auditing the round-2 proposed schema (still not accepted as drafted)

```
{
  "claim": "Some students could not enter the classroom.",
  "role": "factual_dependency",
  "support": "unsupported",
  "declaration": "declared",
  "declared_refs": ["obs:1"],
  "auditor_evidence": [{"excerpt": "...", "relation": "does_not_establish_claim"}],
  "problem": "modality_hardening",
  "why": "\"reluctant\" does not establish inability."
}
```

This is a real improvement over round 1 (declaration tracking closes
the silent-rescue gap; `auditor_evidence` gives B2 its own inspectable
citation instead of only pointing back at IDs it didn't choose). Two
remaining issues, fixed below:

1. **`auditor_evidence` needs its own deterministic check, or it's
   just unverified prose with extra structure.** B2 is itself
   generating new excerpt claims ("here's what I found and here's why
   it does/doesn't establish the claim") — exactly the kind of
   assertion CJ-1's whole design history says must never be trusted on
   a model's say-so. **Fix: a post-B2 deterministic provenance
   validator**, structurally identical to Stage B and to CJ-1's own
   validator — checks every `auditor_evidence[].excerpt` against
   `source_snapshot` (smart-quote-fold resolver as a diagnostic only,
   same discipline as everywhere else in this project). B2's semantic
   JUDGMENT (does this excerpt support or fail to establish the claim)
   stays a model call; whether the CITED TEXT is even real stays
   deterministic, same separation of concerns as Stage B vs. Stage A
   everywhere else in this design.
2. **`support` needs an `uncertain` value.** The round-2 draft only
   offers `supported|unsupported|not_required` — but B2 can
   legitimately fail to determine support one way or the other on a
   genuinely hard case, and forcing a binary call there just relocates
   the same problem `boundary_ambiguous` was introduced to solve, onto
   the `support` axis instead of the `role` axis. Added.

### CORRECTION (round 3, same day): four final schema/invariant fixes before prompt drafting

**1. `verdict` removed from the model-facing output.** Round 2 already
stated "verdict is a deterministic function of the claims list, never
asserted independently by the model" — but the schema still had the
model emit `"verdict": "safe|unsafe|ambiguous"` directly, repeating
the exact self-certification mistake CJ-1's `GUARD_RATIONALIZATION`
observation and CJ-2's own `disqualified`-field removal (round 3 of
the CJ-2 schema, before B2 existed) both already corrected once. **The
model outputs `claims` only.** Everything downstream is computed, not
reported:

```
B2 model output:          { "claims": [...] }
                                ↓
auditor-evidence provenance validator (no LLM)
                                ↓
field/invariant validator (no LLM)
                                ↓
orchestrator computes effective_verdict (no LLM)
```

**2. `boundary_ambiguous` given real, structurally-enforced
invariants.** Round 2 left `support`/`declaration` unconstrained for
this role, which doesn't hold up: if the auditor can't tell whether a
proposition functions as conceptual framing or a world-claim, it also
can't yet ask whether Stage A was obligated to declare it — that
question presupposes the first one is already resolved.
`declaration`'s enum gains a fourth value, `uncertain`, and legal
combinations are now structurally exhaustive (nothing else is
permitted):

```
role=interpretive_only    -> support=not_required,  declaration=not_applicable, declared_refs=[]
role=factual_dependency   -> support in {supported, unsupported, uncertain}
                              declaration in {declared, undeclared}
role=boundary_ambiguous   -> support=uncertain,      declaration=uncertain
```

**3. `problem` → `problems`, a list.** A single claim can violate more
than one independent axis at once (e.g. `modality_hardening` AND
`undeclared_factual_dependency` on the same proposition) — a singular
enum forces the auditor to discard information or pick arbitrarily.
`problems: []` for clean claims.

**4. The post-B2 provenance check WRAPS, never mutates, B2's semantic
judgment.** Round 2's design said an unverifiable `auditor_evidence`
citation makes the claim "revert to `support=uncertain`" — that's
silently rewriting the model's own output, the same mistake corrected
everywhere else in this project (Stage B never edits a Stage A
candidate; it wraps it in `provenance_validation`). **Fixed: preserve
the original claim exactly as B2 wrote it, and record the provenance
check as a separate, sibling object.** The ORCHESTRATOR (not B2, not
the validator) then derives the effective status from both together —
so "B2 confidently said `supported` from evidence that turned out to
be unverifiable" remains visible as its own finding, not erased into
an ordinary `uncertain`.

**5. Factual-authority hierarchy for B2, frozen explicitly.**
`resisting_detail` is supplied to B2 as CONTEXT ONLY — it helps
identify which reading is being audited, but a claim supported only by
something stated in `resisting_detail` (CJ-1's own prose paraphrase of
the seed friction) is NOT sufficient support for a `factual_dependency`.
Factual authority is exactly three things: `source_snapshot` itself,
the canonical `cj1:aN` excerpts, and the candidate's own declared
`obs:N` excerpts. B2 may search all of `source_snapshot` freely for
`auditor_evidence` — it is not confined to the candidate's own
citations — but everything it finds must ultimately be a real
substring of the snapshot, not of CJ-1's summary of it.

### CORRECTION (round 4, same day): coverage manifest, run-status layer, evidence-presence requirement, and a real bug fix in the verdict rule

Four fixes, none reopening the architecture. The most important is the
first — everything else is real, but this one is the actual hole:

**B2 safety depends on the model extracting every dangerous
proposition. `claims[]` alone cannot distinguish "I inspected this
field and found nothing factual" from "I never looked at this field."**
No string validator can detect a proposition the auditor silently
skipped. If a candidate's `additional_source_observations[0].observation`
reads "students were unable to return to the classroom" and B2 simply
never extracts that sentence into `claims[]`, every downstream check
still passes and the candidate becomes `safe`. **Fixed with a field
coverage manifest** (below) — the orchestrator already knows exactly
which claim-bearing field instances exist on a candidate (it built the
candidate), so it can deterministically require B2 to account for each
one explicitly, even when the account is "nothing auditable here."
This doesn't prove semantic completeness — only the model can actually
read for a missed proposition — but it makes silent omission
structurally visible instead of structurally invisible.

Second: **the previous round's verdict rule accidentally routed
`unresolved` into `UNSAFE`.** An unverifiable `auditor_evidence`
citation means the AUDIT failed to establish safety — it is not
evidence the candidate's factual proposition was shown false or
unsupported. Corrected: `audit_unresolved` → `AMBIGUOUS`, never
`UNSAFE`. Conflating "the candidate violated the factual/evidence
contract" with "the auditor failed to produce a trustworthy judgment"
would erase a distinction worth preserving as its own calibration
signal.

Third: **no defined outcome existed for a structurally invalid B2
response.** The field/invariant validator could say "malformed," but
the effective-verdict algorithm still assumed a legitimate claims list
to compute from. A run-status layer is added, sitting ABOVE the
semantic verdict: `valid | schema_invalid | call_failed`. Only a
`valid` run produces a semantic `effective_verdict` at all — a
malformed or failed B2 call is never converted into evidence that the
CANDIDATE itself was unsafe or ambiguous; it's a separate failure of
the auditor's own execution.

Fourth: **`support=supported` had no evidence-presence requirement.**
`{"role": "factual_dependency", "support": "supported",
"auditor_evidence": []}` was structurally legal — nothing required
even one citation. Fixed: a `supported` factual claim must carry at
least one `auditor_evidence` entry with `relation=supports_claim`, and
at least one such entry must survive the post-B2 provenance check —
otherwise the claim's effective status is `audit_unresolved`
(→ `AMBIGUOUS`), not `safe`. Applied symmetrically to `unsupported`
for consistency: an `unsupported` claim must cite what it inspected
(`relation=does_not_establish_claim`) with a `why`; if THAT citation
also fails provenance, the claim is equally `audit_unresolved` rather
than confidently `unsafe` on a citation that isn't even verifiably
real. The model still does 100% of the semantic reading — deterministic
code only ever confirms that a cited excerpt exists in the text, never
whether the semantic judgment itself is right.

### `B2_MODEL_OUTPUT_V1` — the single canonical model-facing schema

**This is the only authoritative schema.** Earlier blocks in this
document (the round-1 audit, the round-2 proposal under audit) are
historical record of what was reviewed and rejected — they remain
visible above for the design history, but nothing outside this block
should be copied into an actual prompt.

```
{
  "field_audits": [
    {
      "source_field": "additional_source_observations[0].observation" |
                       "additional_source_observations[1].observation" |
                       "engine_move" | "seed_engagement" |
                       "interpretive_inference" | "conceptual_shift" |
                       "claimed_contribution",
      // one entry per field INSTANCE actually present on this candidate
      // -- e.g. two entries if there are two additional_source_observations
      "claim_ids": ["c1", "c2"],
      "no_auditable_propositions": false
      // true means: I inspected this field and found nothing that
      // asserts what happened/existed/caused/etc. -- an explicit,
      // accountable statement, not a gap
    }
  ],
  "claims": [
    {
      "claim_id": "c1",
      "claim": "the specific proposition, stated plainly",
      "source_field": "additional_source_observations[0].observation" |
                       "engine_move" | "seed_engagement" |
                       "interpretive_inference" | "conceptual_shift" |
                       "claimed_contribution",
      "role": "interpretive_only" | "factual_dependency" | "boundary_ambiguous",
      "importance": "load_bearing" | "supporting" | "incidental",
      "support": "supported" | "unsupported" | "not_required" | "uncertain",
      "declaration": "declared" | "undeclared" | "not_applicable" | "uncertain",
      "declared_refs": ["cj1:a1"] | ["obs:1"] | [],
      "auditor_evidence": [
        {"excerpt": "exact substring B2 itself locates in source_snapshot",
         "relation": "supports_claim" | "does_not_establish_claim"}
      ],
      "problems": ["modality_hardening" | "causality_hardening" |
                    "mechanism_invention" | "necessity_dependency_hardening" |
                    "motivation_invention" | "population_relation_hardening" |
                    "undeclared_factual_dependency" | "other"],
      // [] for a clean claim; may contain more than one value
      "why": "one sentence"
    }
  ]
}
```

**That is the entire model output. No `verdict` key. No duplicate
keys. `problems` only, never singular `problem`.**

`conceptual_shift` gets a `field_audits` entry only when the candidate
actually has a non-null value for it (an abstained candidate never
reaches B2 at all — abstains are dropped before B2 the same way they're
dropped before Stage C).

### Field coverage invariants (deterministic, checked before claim-level invariants)

```
Let EXPECTED = the exact set of claim-bearing field instances the
orchestrator knows exist on this candidate (it constructed the
candidate; this is not derived from the model's response).

field_audits must contain EXACTLY ONE entry per member of EXPECTED --
no missing field, no unknown/extra field.

Every claim_id referenced anywhere in field_audits must resolve to
exactly one entry in claims[]. Every claims[].claim_id must be
referenced by exactly one field_audits entry, and that entry's
source_field must equal the claim's own source_field.

no_auditable_propositions=true   -> claim_ids must be []
no_auditable_propositions=false  -> claim_ids must be non-empty

Any violation -> this candidate's B2 run is schema_invalid (see below),
not silently repaired and not treated as evidence about the candidate.
```

### Claim structural invariants (deterministic, checked after coverage)

```
role=interpretive_only:
  support        must = not_required
  declaration    must = not_applicable
  declared_refs  must = []

role=factual_dependency, support=supported:
  declaration     must be in {declared, undeclared}
  auditor_evidence must contain >=1 entry with relation=supports_claim

role=factual_dependency, support=unsupported:
  declaration     must be in {declared, undeclared}
  auditor_evidence must contain >=1 entry with relation=does_not_establish_claim
  why             must be non-empty

role=factual_dependency, support=uncertain:
  declaration     must be in {declared, undeclared}

role=boundary_ambiguous:
  support        must = uncertain
  declaration    must = uncertain

Any other combination, or a missing required auditor_evidence entry,
is a schema violation -> schema_invalid for this candidate's B2 run,
never coerced into a legal shape.
```

### Post-B2 pipeline — three layers, run status first

**Layer 0 — B2 run status (deterministic, computed before anything
else is trusted):**

```
b2_run_status =
  "call_failed"     if the API call itself failed or returned
                      unparseable output
  "schema_invalid"  if it parses but violates field coverage or claim
                      structural invariants above
  "valid"           otherwise

If b2_run_status != "valid":
  effective_verdict = "not_computed"
  candidate withheld from Stage C
  logged distinctly from unsafe/ambiguous -- an auditor execution
  failure is NEVER converted into a semantic finding about the
  candidate.
```

**Layer 1 — auditor-evidence provenance validator (no LLM), only runs
if `b2_run_status="valid"`, WRAPS, never mutates:**

```
for every claim's auditor_evidence[].excerpt:
  exact substring of source_snapshot? -- accept as-is
  else: smart-quote-fold resolver, diagnostic only
    unique normalized match? -- accept, persist the ORIGINAL source
      substring (never B2's version) for the record
    otherwise (no_match / ambiguous_match): flag this specific
      excerpt invalid

Output, per claim, a SEPARATE sibling object -- the original claim is
never edited:
{
  "claim": { ...B2's claim object, byte-identical to what it wrote... },
  "auditor_evidence_validation": {
    "valid": true | false,
    "violations": ["..."]   // e.g. "auditor_evidence[0] has no unique source match"
  }
}
```

**Layer 2 — orchestrator computes `effective_status` per claim, then
`effective_verdict` per candidate**, only if `b2_run_status="valid"`,
never from the model's own say-so, never by mutating what it said:

```
For a factual_dependency claim, let RELEVANT = the auditor_evidence
entries matching the claim's own stated direction (relation=
supports_claim if support=supported; relation=does_not_establish_claim
if support=unsupported).

  if support in {supported, unsupported}:
    if at least one entry in RELEVANT has auditor_evidence_validation.valid=true:
       effective_status = claim.support   // confirmed by a real citation
    else:
       effective_status = "audit_unresolved"
       // EITHER direction, symmetric: the auditor made a confident
       // semantic call, but every citation it offered for that call
       // turned out unverifiable. This is NOT "uncertain" (the model
       // never said uncertain) and NOT confirmed supported/unsupported
       // -- it is its own outcome, preserving that a confident-but-
       // uncorroborated judgment occurred rather than erasing it.
  if support = uncertain:
       effective_status = "uncertain"
  if role in {interpretive_only, boundary_ambiguous}:
       effective_status = the role's fixed value (unchanged)

effective_verdict (per candidate):
  UNSAFE if any claim has role=factual_dependency AND
    ( effective_status="unsupported" OR declaration=undeclared )

  AMBIGUOUS if no claim triggers UNSAFE, AND
    ( any claim has role=boundary_ambiguous
      OR any claim has role=factual_dependency AND
        effective_status in {"uncertain", "audit_unresolved"} )

  SAFE otherwise
```

**`audit_unresolved` now correctly routes to `AMBIGUOUS`, not
`UNSAFE`** — the round-3 bug is fixed. `UNSAFE` is reserved for a
claim the audit actually confirmed unsupported (via a real, provenance-
valid citation) or an undeclared factual dependency — a genuine
contract violation, not an auditor malfunction.

### Three-layer status distinction — must remain explicit in stored research output

```
B2 RUN STATUS:              valid | schema_invalid | call_failed
CANDIDATE EFFECTIVE VERDICT (only defined when run_status=valid):
                             safe | unsafe | ambiguous
STAGE-C ELIGIBILITY:        only effective_verdict="safe"
                             (schema_invalid/call_failed candidates are
                             NOT retried or coerced into ambiguous --
                             they are their own logged outcome)
```

Full orchestrator-level output shape (nothing here is model output):

```
{
  "b2_run_status": "valid" | "schema_invalid" | "call_failed",
  "b2_result": { "field_audits": [...], "claims": [...] } | null,
  "auditor_evidence_validation": [ {...}, ... ] | null,   // Layer 1, only if valid
  "field_coverage_validation": {"valid": bool, "violations": [...]} | null,
  "claim_structural_validation": {"valid": bool, "violations": [...]} | null,
  "effective_verdict": "safe" | "unsafe" | "ambiguous" | "not_computed"
}
```

### Static consistency check of this document, run now

- Canonical schema (`B2_MODEL_OUTPUT_V1` above) contains no duplicate
  JSON keys. ✓.
- No singular `problem` anywhere in the canonical schema — `problems`
  only. ✓.
- No model-facing `verdict` field in the canonical schema. ✓.
- No stale "revert support to uncertain" logic anywhere in the current
  pipeline — Layer 1 wraps, Layer 2 computes a distinct
  `audit_unresolved` status without touching `claim.support`. ✓.
- `audit_unresolved` maps to `AMBIGUOUS`, not `UNSAFE`, in the
  corrected verdict rule above. ✓ (this was the actual round-3 bug;
  fixed here).

### How Stage C changes once factual safety is upstream

Stage C's `candidate_assessments` schema drops `factual_integrity` as
a dimension entirely (guaranteed by B2 before Stage C ever runs) and
the hard gate shrinks from 5 conditions to 4:

```
does_not_qualify if ANY of:
  seed_engagement == "none"
  engine_dependence == "generic"
  conceptual_movement == "none"
  distinctive_contribution == "none"
otherwise: qualifies
```

Stage C's evidence/inference-boundary instruction (the A-causes-B
example, the "do not trust the candidate's own claims" framing) MOVES
to B2's prompt, not duplicated in both — Stage C no longer needs to
reason about causal/modal overclaiming at all, only about whether a
(now factually-safe) reading is genuinely engine-specific and
distinctive. This is the actual resolution of the two-conflicting-jobs
problem: Stage C is no longer asked to be suspicious and admiring in
the same breath. **Not drafted as a prompt here** — `cj2-stage-c-v1`
remains frozen; a `v2` would be a real, deliberate revision, not made
in this document.

### Orchestration edge cases, extended (updated for the run-status layer + 3-valued verdict)

Only candidates with `b2_run_status="valid"` AND
`effective_verdict="safe"` count toward the Stage C survivor count.
`unsafe`, `ambiguous`, `schema_invalid`, and `call_failed` are all
excluded from Stage C — but tracked as four DISTINCT outcomes, never
merged: collapsing `ambiguous` into `unsafe`, or a `schema_invalid`
auditor malfunction into either, would throw away exactly the
diagnostic signal each one exists to preserve (is the CANDIDATE the
problem, or is the AUDITOR the problem).

```
0 B2-safe candidates  → selection = no_distinctive_contribution, no Stage C call
                        (unsafe/ambiguous/schema_invalid/call_failed
                        candidates still logged and surfaced for
                        review, each under its own label, not
                        silently dropped or conflated)
1 B2-safe candidate   → Stage C still runs, must independently qualify
2-4 B2-safe candidates → normal comparison
```

Directly generalizes the existing rule by inserting B2 as an
additional filter before the survivor count is taken. A candidate
that is Stage-B-valid but B2-`unsafe` is dropped the same way an
abstained or Stage-B-invalid candidate is dropped — not repaired, not
partially kept. A B2-`ambiguous` candidate is ALSO withheld from Stage
C, but reported distinctly (not as a failure, not as a pass) — this
matters specifically because the gate hasn't been calibrated yet, and
merging `ambiguous` into either bucket now would hide how often it
actually fires. (A more lenient "keep the safe claims, trim the unsafe
ones, offer Stage C a repaired candidate" design is a plausible future
alternative — not adopted here, to avoid inventing new repair
machinery this session on top of an already-untested gate.)

### The existing 12 candidates are now a development set, not ground truth

**Explicit correction, stated because it matters for what comes
next:** the audit table above was produced by the SAME process that
discovered the failure class — useful for defining the categories and
for a first regression check, but not an independent benchmark. When
B2 is eventually drafted (not now), its first real test is running it
against these exact frozen candidate/source pairs and checking BOTH
error directions:

- **`FALSE_SAFE`**: B2 lets a factual strengthening through (the
  failure this design exists to fix).
- **`FALSE_UNSAFE`**: B2 rejects a legitimate conceptual inference
  merely because the source doesn't state it outright (the failure
  that would destroy CJ-2 just as surely — a gate that reduces every
  reading to a source summary has "solved" fabrication by eliminating
  the thing CJ-2 was built to do).
- **`ambiguous` rate and content**, tracked as its own third
  measurement now that the verdict is 3-valued — not itself an error,
  but if it fires constantly, or never fires at all, either result is
  informative about whether `boundary_ambiguous` is doing real work or
  just absorbing cases that should have resolved cleanly one way or
  the other.

Both error directions matter equally. None of the three measured yet
— no B2 prompt exists.

### A hypothesis worth logging, not acting on

The audit's "De Hooch had denser quotation, so it stayed clean"
explanation is plausible but probably not the deepest one available.
A sharper hypothesis: **the risk may track evidentiary AFFORDANCE, not
quotation density as such** — De Hooch's friction was already rich
enough (direct curator quotes describing before/after readings, an
explicit game-rule mechanic) that no engine needed to manufacture
connective tissue to make its lens work; Cave DNA and AI Exam's
frictions were comparatively thin/underdetermined at the mechanism
level, so the engines that most wanted to name an active mechanism (S,
M) built the missing tissue themselves. If true, this would eventually
say something about which CJ-1 PASSes are "interpretively fertile"
versus merely factually adequate — **explicitly NOT fed back into CJ-1
now.** CJ-1's job stays "prove the friction is real," full stop; this
hypothesis, if it holds up on more data, belongs to CJ-2/B2 design
discussions, not to reopening CJ-1's already-frozen contract.

### Explicitly kept separate from this design round

Per instruction, not reopened or mixed in here — each remains exactly
where the probe report left it: the whitespace-transport resolver gap,
Stage C's JSON-only compliance and this probe's harness extraction
bug, the missing `05_dutch_painting_soldier` Stage C result, the
zero-abstention result, and the convergence analysis (shape-vs-target).

### Status

B2 is now a fully-specified (round 4), not-yet-drafted research stage:
engine-blind; audits ALL claim-bearing fields via an explicit field
coverage manifest (`field_audits`) that makes silent omission
structurally visible; separates source `support` from evidence
`declaration` (no silent rescue of undeclared facts found elsewhere in
the source); a real `boundary_ambiguous` role; a `supported`/
`unsupported` claim must carry at least one citation and that citation
must survive a post-B2 provenance check, symmetric in both directions;
a run-status layer (`valid|schema_invalid|call_failed`) sits above the
semantic verdict so an auditor malfunction is never converted into a
finding about the candidate; the verdict itself is 3-valued
(`safe|unsafe|ambiguous`), computed only from a `valid` run, with the
round-3 bug fixed — an unverifiable citation on an otherwise-supported
claim now correctly resolves to `AMBIGUOUS` via `audit_unresolved`,
never `UNSAFE`. `B2_MODEL_OUTPUT_V1` is the single canonical
model-facing schema — earlier blocks in this document are historical
record only. No system prompt written for B2. No `cj2-stage-c-v2`. No
code. No API calls. No changes to `cj2-stage-a-v1`, the capsules, or
CJ-1. Two questions the first probe has now actually answered, worth
stating plainly: do the four instruments generate different targets —
apparently yes, enough to keep investigating; can the current
comparator tell bold interpretation from factual invention — clearly
no. The next design work is B2's actual prompt, tested against this
development set for `FALSE_SAFE`, `FALSE_UNSAFE`, `ambiguous`
rate/content, AND the `schema_invalid`/`call_failed` rate (a high rate
there would itself indicate the schema is too hard for the model to
satisfy, independent of whether its semantic judgments are any good)
before any further live probe.

## PROMPT FROZEN: cj2-stage-b2-v1 (2026-08-11)

Architecture/schema review for B2 is done as of round 4. This is the
first B2 prompt, composed against `B2_MODEL_OUTPUT_V1` and all frozen
round-4 invariants exactly, with one operational clarification decided
during composition (not a schema change):

**"Auditable proposition" ≠ "factual proposition."** Without this
stated explicitly, the field-coverage manifest could be satisfied two
different ways for the same field — e.g. *"the exam format can be
understood as producing a different kind of apparent competence"*
could legally become either `no_auditable_propositions=true`
("conceptual, not factual, so nothing to flag") or a classified
`interpretive_only` claim. Both fit the round-4 schema language. The
first choice would make `field_audits` prove only "I searched for
factual-looking material," never "I distinguished interpretation from
factual dependency" — which is B2's entire purpose. Frozen: an
auditable proposition is any substantive assertion contributing to the
candidate's case that can be stated independently, whether it ends up
`interpretive_only`, `factual_dependency`, or `boundary_ambiguous`.
`no_auditable_propositions=true` is reserved for fields with no
substantive proposition at all — purely connective/organizational/
referential wording.

**Trigger-word guidance added.** *Produces, creates, makes, enables,
prevents, depends, requires, causes* do not themselves determine role
— the same verb appears in both interpretive models and factual
claims. The prompt asks instead whether the proposition requires the
reader to believe a specific event/relationship/capability/dependency/
motivation/population-fact actually held in the source's world.

**No development-fixture content used as worked examples** — the
cave-DNA/De Hooch/AI-exam material stays out of the prompt entirely (a
generic bridge-inspection example illustrates interpretive-vs-factual;
a generic sorting-algorithm example illustrates the trigger-word
point), so the frozen 12-candidate set remains an untouched test set
for B2, not training material B2 has already seen phrased identically.

### `cj2-stage-b2-v1` — system prompt

```
You are a SEMANTIC FACTUALITY AUDITOR examining ONE candidate reading of a grounded friction in a fetched SOURCE SNAPSHOT.

You will be given, in the user message:
- the SOURCE SNAPSHOT itself.
- a SEED FRICTION: a RESISTING DETAIL and one or more CANONICAL EVIDENCE anchors (exact excerpts from the snapshot, each with a stable ID) -- already validated as real.
- ONE candidate's claim-bearing fields: any additional source observations it declared, its engine_move, seed_engagement, interpretive_inference, conceptual_shift (if present), and claimed_contribution.

You do NOT know which perceptual engine produced this candidate, and you are not told. You are not comparing this candidate to any other. You are not asked whether it is interesting, distinctive, or well-written. Your only question is whether every substantive claim it makes is either a legitimate interpretation or an adequately supported, properly declared factual premise.

YOUR JOB

For EVERY one of the candidate's claim-bearing fields (each additional source observation's own observation text, engine_move, seed_engagement, interpretive_inference, conceptual_shift if present, claimed_contribution):

1. Extract every AUDITABLE PROPOSITION in that field.
2. Classify each one: interpretive_only, factual_dependency, or boundary_ambiguous.
3. For each factual_dependency, determine whether it is supported by the source and whether it was properly declared.
4. Record which field(s) you inspected and what you found there, even when you found nothing to extract -- this accounting is mandatory for every field, not optional.

WHAT COUNTS AS AN AUDITABLE PROPOSITION -- READ CAREFULLY

An auditable proposition is any substantive assertion the candidate makes that contributes to its case and can be stated on its own as a proposition. "Auditable" does NOT mean "factual." A field contains nothing auditable ONLY when it is purely connective, organizational, or referential wording -- a field containing a genuine conceptual reframing is NOT nothing-to-report just because that reframing doesn't require factual proof. Extract it and classify it interpretive_only.

This distinction is the entire point of your job. If you only extract propositions that already look factual, you have not actually audited the field -- you have only searched it for one shape of content and skipped the other. A field audit that finds nothing must mean "I inspected this and there was truly no substantive claim here," never "I only looked for claims that seemed risky."

THE THREE ROLES

- interpretive_only: a conceptual reading, model, analogy, or reframing of facts already established. It may go BEYOND what the source says -- that is the entire purpose of interpretation, and you must not treat boldness as a reason for suspicion. It never requires source support.
- factual_dependency: a proposition that requires the reader to believe some event, causal relationship, capability, dependency, motivation, population fact, or condition ACTUALLY OCCURRED OR EXISTED in the world the source describes. This is what needs checking.
- boundary_ambiguous: you genuinely cannot tell, after real consideration, whether a proposition is functioning as conceptual framing or as a claim about what happened. Use this honestly when it applies -- do not force a call either way just to avoid it.

Worked example, topic-neutral, illustrating the distinction (not from any specific case you may be asked to audit):

Source states: "The bridge was closed for inspection after engineers found rust on two support beams."

- INTERPRETIVE_ONLY: "The closure can be read as revealing that the bridge's official safety rating was always provisional rather than settled." -- This is a conceptual claim about what the closure MEANS. It does not require the source to say anything about "provisional ratings" -- it is a lens applied to the real fact of the closure.
- FACTUAL_DEPENDENCY (would need support): "The closure prevented a collapse that would otherwise have occurred." -- This asserts a real counterfactual/causal fact about the world (a collapse was actually imminent and was actually averted) that the bare fact of "closed for inspection after finding rust" does not establish on its own.

DO NOT CLASSIFY BY TRIGGER WORDS

Words like produces, creates, makes, enables, prevents, depends, requires, and causes do NOT by themselves make a proposition factual, and their absence does not make a proposition safe. The same verb can appear in a conceptual model or in a world-claim. Ask only: does this proposition require the reader to believe a specific event, causal relationship, capability, dependency, motivation, or population fact actually held true in the source's world?

Example: "The new sorting algorithm can be understood as producing a different ranking logic than a human reviewer would apply" is interpretive -- a conceptual account of what the algorithm's output means. "The new algorithm's ranking caused three applicants to be rejected who would otherwise have been accepted" is a factual dependency -- a specific counterfactual claim about real outcomes that needs source support.

TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY

1. SUPPORT -- is this proposition actually established by the source? Search the entire SOURCE SNAPSHOT freely, not just the candidate's own citations, before concluding unsupported.
2. DECLARATION -- did the candidate properly route this factual premise through its own declared evidence (a canonical cj1:aN anchor, or one of its own declared obs:N observations)?

These are independent. A fact you find yourself elsewhere in the snapshot, that the candidate never declared, is SUPPORTED but UNDECLARED -- finding it does NOT make it declared. The candidate was still obligated to cite it through its own declared evidence and did not.

FACTUAL AUTHORITY -- WHAT MAY ESTABLISH A FACT

Only these three things establish a fact: the SOURCE SNAPSHOT itself, the canonical evidence anchors, and the candidate's own declared observation excerpts. The RESISTING DETAIL is supplied only as context to help you identify which reading is being audited -- it is a prose paraphrase, not evidence. A proposition supported only by something stated in the resisting detail, and nowhere in the actual snapshot or declared excerpts, is NOT supported.

AUDITOR EVIDENCE

For a factual_dependency you judge supported: cite at least one exact excerpt from source_snapshot with relation "supports_claim."
For a factual_dependency you judge unsupported: cite at least one exact excerpt showing the closest real fact the candidate strengthened beyond, with relation "does_not_establish_claim," and explain in "why" what specific gap exists (a hedge that became a capability claim, a co-occurrence that became a cause, an absence of any stated mechanism, etc.). You must have read the full snapshot before concluding unsupported -- the cited excerpt is your inspectable basis for the judgment, not a claim that no other sentence anywhere could possibly apply.

Every excerpt you cite must be an exact substring of source_snapshot, copied verbatim, character for character.

FIELD INVARIANTS

- interpretive_only: support="not_required", declaration="not_applicable", declared_refs=[].
- factual_dependency: support is "supported", "unsupported", or "uncertain" (use "uncertain" only when you genuinely cannot determine support after searching the full snapshot); declaration is "declared" or "undeclared".
- boundary_ambiguous: support="uncertain", declaration="uncertain".

FIELD COVERAGE -- REQUIRED FOR EVERY FIELD INSTANCE SUPPLIED

You will be told exactly which field instances exist on this candidate (which additional observations, whether conceptual_shift is present, etc.). For EACH one, produce exactly one field_audits entry recording either the claim_ids you extracted from it, or (only when genuinely nothing substantive was there) no_auditable_propositions=true with an empty claim_ids list. Do not skip a field. Do not combine two fields into one entry.

OUTPUT

Return only JSON. No other text, no markdown code fences, no comments. Use exactly this shape -- field_audits and claims, nothing else. Do NOT include a verdict, effective_verdict, or run_status field of any kind -- those are computed downstream, never by you.

{
"field_audits": [
  {"source_field": "engine_move", "claim_ids": ["c1"], "no_auditable_propositions": false},
  {"source_field": "seed_engagement", "claim_ids": [], "no_auditable_propositions": true}
],
"claims": [
  {
    "claim_id": "c1",
    "claim": "the specific proposition, stated plainly",
    "source_field": "engine_move",
    "role": "interpretive_only",
    "importance": "load_bearing",
    "support": "not_required",
    "declaration": "not_applicable",
    "declared_refs": [],
    "auditor_evidence": [],
    "problems": [],
    "why": "why this is a conceptual reading rather than a world-claim"
  }
]
}

A factual_dependency example, showing the required evidence shape:

{
"claim_id": "c2",
"claim": "the specific world-claim, stated plainly",
"source_field": "interpretive_inference",
"role": "factual_dependency",
"importance": "load_bearing",
"support": "unsupported",
"declaration": "undeclared",
"declared_refs": [],
"auditor_evidence": [
  {"excerpt": "exact substring from source_snapshot", "relation": "does_not_establish_claim"}
],
"problems": ["causality_hardening"],
"why": "the source states the two facts occurred together but never states that one caused the other"
}
```

### `cj2-stage-b2-v1` — user-input template

```
SEED FRICTION (resisting_detail is CONTEXT ONLY -- not factual authority; it cannot establish or rescue a factual dependency)

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"
[cj1:a3 if present]

SOURCE SNAPSHOT

{source_snapshot}

CANDIDATE FIELDS TO AUDIT

The following field instances exist on this candidate. Produce exactly one field_audits entry for each one listed below -- no more, no fewer.

additional_source_observations[0]:
  declared excerpt (obs:1): "{obs_1_excerpt}"
  observation: "{obs_1_observation}"
[repeat additional_source_observations[N] for each one actually present -- omit this block entirely if the candidate declared none]

engine_move: "{engine_move}"

seed_engagement: "{seed_engagement}"

interpretive_inference: "{interpretive_inference}"

conceptual_shift: "{conceptual_shift}"
[omit this line and its field_audits entry entirely if conceptual_shift is null]

claimed_contribution: "{claimed_contribution}"
```

### Static preflight — no API calls — ALL PASS

```
[PASS] banned terms absent -- Stage B2 system prompt
[PASS] banned terms absent -- Stage B2 user template
[PASS] 'effective_verdict' only appears inside a do-NOT-include instruction -- Stage B2 system prompt
[PASS] 'run_status' only appears inside a do-NOT-include instruction -- Stage B2 system prompt
[PASS] 'effective_verdict' absent (fine) -- Stage B2 user template
[PASS] 'run_status' absent (fine) -- Stage B2 user template
[PASS] explicit instruction NOT to output verdict/effective_verdict/run_status present
[PASS] no development-fixture content in Stage B2 system prompt (bridge/algorithm examples used instead)
[PASS] resisting_detail explicitly labeled context-only in system prompt
[PASS] resisting_detail explicitly labeled context-only in user template
[PASS] "auditable proposition" != "factual" distinction stated
[PASS] trigger-word non-determinism guidance present
[PASS] supported requires >=1 supports_claim citation
[PASS] unsupported requires >=1 does_not_establish_claim citation
[PASS] field coverage (one entry per field instance) instruction present
[PASS] example found for marker '{"field_audits"...}'
[PASS] example found for marker '{"claim_id": "c2"...}'
[PASS] JSON parses -- field_audits example
[PASS] JSON parses -- claim_id c2 example
[PASS] no verdict/run_status key inside JSON example -- field_audits example
[PASS] no verdict/run_status key inside JSON example -- claim_id c2 example

OVERALL: PASS
```

Banned-term list checked: `Pixel/Siri/Zen/Maya`, `persona`,
disability vocabulary, `disability_angle`, topic affinity, hard-
routing/balance language, `current_agent`, `removed_engine_test`,
`Candidate A/B/...`, `Engine P/S/Z/M`, and `Stage C` itself — none
appear in either the system prompt or the user template.

**Status: `cj2-stage-b2-v1` is a FROZEN design candidate,
static-preflight-clean. No API calls made. No production/repo code
written for this round (the two preflight scripts are temporary and
local, same convention as every earlier preflight in this document).
No changes to `cj2-stage-a-v1`, `cj2-stage-c-v1`, the capsules, the
B2 schema, or CJ-1.**

## `cj2-stage-b2-v1` — STATUS: NOT EXECUTED — SUPERSEDED BEFORE FIRST API CALL (2026-08-11)

A pre-execution prompt-contract review, run before any B2 API call was
made, found four defects in the prompt/template composed above. None
of these reopen `B2_MODEL_OUTPUT_V1` or the round-4 architecture —
they are prompt-level, the same class of correction CJ-1 and
`cj2-stage-a-v1`/`cj2-stage-c-v1` each went through before their own
freeze.

**Reason for supersession:**
1. **Missing declaration-lineage input.** The v1 user template gave
   B2 all canonical `cj1:aN` anchors but never gave it the candidate's
   own `seed_evidence_refs` — making it structurally impossible to
   tell "this fact is somewhere in canonical evidence" apart from
   "this candidate actually declared it," which breaks the
   support-vs-declaration split the whole gate is built on.
2. **Contaminated worked example.** v1's own `INTERPRETIVE_ONLY`
   bridge example ("the bridge's official safety rating was always
   provisional") smuggled in an unsupported world-proposition behind
   "can be read as" — teaching, inside the prompt meant to catch
   exactly this pattern, the pattern itself. The sorting-algorithm
   example also had no concrete source statement to audit against.
3. **Underspecified output fields.** `importance` and `problems` were
   required fields with no precise definitions or invariants, leaving
   "diagnostic-only" and "may contain multiple values" unstated.
4. **`source_field` identifier mismatch.** The schema expects literal
   strings like `additional_source_observations[0].observation`; the
   v1 user template only presented `additional_source_observations[0]:`
   with a nested `observation:` line — a real schema-invalid risk with
   no offsetting benefit.

`cj2-stage-b2-v1`'s full prompt/template/preflight above remains in
this document verbatim, unedited, as the historical record of what was
composed and why it was superseded — it was never called against a
model.

## PROMPT FROZEN: cj2-stage-b2-v1.1 (2026-08-11) — STATUS: DESIGN CANDIDATE / NOT EXECUTED

Supersedes `cj2-stage-b2-v1` per the four corrections above. Same
`B2_MODEL_OUTPUT_V1` schema, same round-4 structural invariants, same
architecture (engine-blind, one candidate at a time, between Stage B
and Stage C) — nothing reopened, only the prompt/template text and the
static preflight script.

**Correction 1 applied — declaration lineage.** User template now
carries a `CANDIDATE-DECLARED SEED EVIDENCE` block (`seed_evidence_refs:
[...]`) separate from the canonical `cj1:aN` evidence block. System
prompt states explicitly: B2 may inspect ALL canonical evidence and the
full snapshot for SUPPORT, but a `cj1:aN` ID counts as DECLARED only
when it appears in the candidate's own declared list; canonical anchors
the candidate did not declare may still be inspected but must never be
written into `declared_refs`. Added a new `DECLARATION LINEAGE` section
stating an `obs:N` excerpt being real only certifies the excerpt text —
it does not certify that the `obs:N`'s own observation prose is an
accurate account of what that excerpt says, so the prose is still
audited on its own terms.

**Correction 2 applied — worked examples replaced.** The bridge
`INTERPRETIVE_ONLY`/`FACTUAL_DEPENDENCY` pair is now the safe contrast
given in the review (closure-as-shift-in-treating-safety vs.
engineers-believed-collapse-was-imminent) — the interpretive side
introduces no new event/rating/motive/mechanism, only a reframing of
the one real fact (the closure) that already happened. Added a new
`HEDGES DO NOT IMMUNIZE A CLAIM` section stating "can be read as,"
"can be understood as," "suggests," and "reveals" describe HOW a claim
is offered, not WHAT it asserts — audit the proposition underneath the
hedge. The sorting-algorithm example (no concrete source statement to
test against) is removed entirely rather than patched, for the
brevity reason the review offered as the preferred option. No Cave
DNA / De Hooch / AI Exam material used, confirmed by preflight.

**Correction 3 applied — importance/problems defined precisely.** Added
an `IMPORTANCE -- DIAGNOSTIC ONLY, NEVER AN EXEMPTION` section with the
three exact `load_bearing`/`supporting`/`incidental` definitions from
the review, plus an explicit "an incidental fabrication is still a
fabrication" line. Added the full 8-value `problems` enum
(`modality_hardening`, `causality_hardening`, `mechanism_invention`,
`necessity_dependency_hardening`, `motivation_invention`,
`population_relation_hardening`, `undeclared_factual_dependency`,
`other`) with the frozen invariants: `support="unsupported"` requires
>=1 semantic problem value; `declaration="undeclared"` requires
`undeclared_factual_dependency`; a claim may carry more than one
problem; clean supported+declared claims carry `problems=[]`.

**Correction 4 applied — exact field identifiers.** User template now
presents every claim-bearing field as `source_field: <exact id>` /
`text: "..."` blocks, literally matching the identifiers the schema
requires (`additional_source_observations[0].observation`,
`engine_move`, `seed_engagement`, `interpretive_inference`,
`conceptual_shift`, `claimed_contribution`) — no more nested
`additional_source_observations[0]: observation:` mismatch. System
prompt's own JSON examples use the same literal identifiers, including
a new third example (`c3`) showing a properly `declared`+`supported`
claim with a correctly populated `declared_refs: ["obs:1"]`, to make
the declaration-lineage rule concrete rather than only asserted in
prose.

**Methodology terminology correction (applies to future runs of this
prompt, not to the prompt text itself):** the frozen 12 candidate/
source pairs from the first reference probe are a **frozen
development/regression set with post-hoc human labels**, NOT an
independent held-out benchmark — the prompt/schema design (including
this v1.1 correction) was itself informed by failures discovered in
that exact set. The first `cj2-stage-b2-v1.1` run against those 12 will
answer "can B2 reproduce/catch the known development failure classes
without destroying known-clean interpretations," not "does B2
generalize." A genuinely fresh, independently selected source/candidate
set is required afterward before any generalization claim.

### `cj2-stage-b2-v1.1` — system prompt

```
You are a SEMANTIC FACTUALITY AUDITOR examining ONE candidate reading of a grounded friction in a fetched SOURCE SNAPSHOT.

You will be given, in the user message:
- the SOURCE SNAPSHOT itself.
- a SEED FRICTION: a RESISTING DETAIL and one or more CANONICAL EVIDENCE anchors (exact excerpts from the snapshot, each with a stable ID) -- already validated as real.
- CANDIDATE-DECLARED SEED EVIDENCE: the list of cj1:aN IDs this specific candidate actually declared as its own seed evidence. You may inspect ALL canonical evidence anchors and the full snapshot when judging whether a claim is supported -- but only an ID that appears in this candidate's own declared list counts as something THIS candidate declared.
- ONE candidate's claim-bearing fields: any additional source observations it declared (each an obs:N excerpt, which is the candidate's own declared factual evidence, plus that observation's own prose, which is candidate reasoning being audited, not evidence), engine_move, seed_engagement, interpretive_inference, conceptual_shift (if present), and claimed_contribution.

You do NOT know which perceptual engine produced this candidate, and you are not told. You are not comparing this candidate to any other. You are not asked whether it is interesting, distinctive, or well-written. Your only question is whether every substantive claim it makes is either a legitimate interpretation or an adequately supported, properly declared factual premise.

YOUR JOB

For EVERY one of the candidate's claim-bearing fields (each additional source observation's own observation text, engine_move, seed_engagement, interpretive_inference, conceptual_shift if present, claimed_contribution):

1. Extract every AUDITABLE PROPOSITION in that field.
2. Classify each one: interpretive_only, factual_dependency, or boundary_ambiguous.
3. For each factual_dependency, determine SUPPORT and DECLARATION separately (see below -- these are two different questions, not one).
4. Record which field(s) you inspected and what you found there, even when you found nothing to extract -- this accounting is mandatory for every field, not optional.

WHAT COUNTS AS AN AUDITABLE PROPOSITION -- READ CAREFULLY

An auditable proposition is any substantive assertion the candidate makes that contributes to its case and can be stated on its own as a proposition. "Auditable" does NOT mean "factual." A field contains nothing auditable ONLY when it is purely connective, organizational, or referential wording -- a field containing a genuine conceptual reframing is NOT nothing-to-report just because that reframing doesn't require factual proof. Extract it and classify it interpretive_only.

This distinction is the entire point of your job. If you only extract propositions that already look factual, you have not actually audited the field -- you have only searched it for one shape of content and skipped the other. A field audit that finds nothing must mean "I inspected this and there was truly no substantive claim here," never "I only looked for claims that seemed risky."

THE THREE ROLES

- interpretive_only: a conceptual reading, model, analogy, or reframing of facts already established. It may go BEYOND what the source says -- that is the entire purpose of interpretation, and you must not treat boldness as a reason for suspicion. It never requires source support.
- factual_dependency: a proposition that requires the reader to believe some event, causal relationship, capability, dependency, motivation, population fact, or condition ACTUALLY OCCURRED OR EXISTED in the world the source describes. This is what needs checking.
- boundary_ambiguous: you genuinely cannot tell, after real consideration, whether a proposition is functioning as conceptual framing or as a claim about what happened. Use this honestly when it applies -- do not force a call either way just to avoid it.

Worked example, topic-neutral, illustrating the distinction (not from any specific case you may be asked to audit):

Source states: "The bridge was closed for inspection after engineers found rust on two support beams."

- INTERPRETIVE_ONLY: "The closure can be read as a shift from treating safety as a settled state to treating it as something that has to be re-established." -- This changes the conceptual frame applied to the closure that already, really happened. It does not require an additional event, rating, motive, capability, mechanism, or causal fact to have actually existed -- it reframes what the real closure means, and needs nothing more from the source to do that.
- FACTUAL_DEPENDENCY (would need support): "Engineers believed collapse was imminent, and closing the bridge prevented it." -- This requires real engineer beliefs, a real imminent-collapse risk, and a real causal counterfactual (closure prevented an outcome that would otherwise have occurred) -- none of which the bare fact of "closed for inspection after finding rust" establishes.

HEDGES DO NOT IMMUNIZE A CLAIM

Phrases such as "can be read as," "can be understood as," "suggests," or "reveals" do NOT by themselves make a proposition interpretive. A hedge only describes HOW a claim is being offered, not WHAT the claim underneath it actually asserts. Always audit the proposition underneath the hedge: if stripping the hedge leaves a claim that a specific event, capability, motive, mechanism, or population fact really held true in the source's world, it is a factual_dependency wearing interpretive language, not an interpretive_only claim.

DO NOT CLASSIFY BY TRIGGER WORDS

Words like produces, creates, makes, enables, prevents, depends, requires, and causes do NOT by themselves make a proposition factual, and their absence does not make a proposition safe. The same verb can appear in a conceptual model or in a world-claim. Ask only: does this proposition require the reader to believe a specific event, causal relationship, capability, dependency, motivation, or population fact actually held true in the source's world?

TWO SEPARATE QUESTIONS FOR EVERY FACTUAL_DEPENDENCY

1. SUPPORT -- is this proposition actually established by the source? Search the entire SOURCE SNAPSHOT freely, and you may also consult the full text of any canonical evidence anchor, not just the ones this candidate declared, before concluding unsupported.
2. DECLARATION -- did the candidate properly route this factual premise through its OWN declared evidence -- an ID present in this candidate's CANDIDATE-DECLARED SEED EVIDENCE list, or one of its own obs:N observations?

These are independent, and SUPPORT never decides DECLARATION. A fact you find yourself elsewhere in the snapshot or in a canonical anchor the candidate did NOT declare is SUPPORTED but UNDECLARED -- finding it yourself does NOT make it declared. The candidate was still obligated to cite it through its own declared evidence and did not.

DECLARATION LINEAGE -- WHAT COUNTS AS THIS CANDIDATE'S OWN DECLARATION

Only two things count as this candidate's declared evidence:
- a cj1:aN ID that appears in this candidate's own CANDIDATE-DECLARED SEED EVIDENCE list (a canonical anchor the candidate did NOT list there is not this candidate's declaration, even though you may still freely inspect it for SUPPORT);
- one of this candidate's own obs:N excerpts.

An obs:N excerpt being real and exact only establishes that the QUOTED TEXT is real. It does NOT certify that the obs:N's own OBSERVATION PROSE (what the candidate says that excerpt establishes) is an accurate account of what the excerpt actually says. Audit the observation prose on its own terms -- a real excerpt does not launder an inaccurate paraphrase of it.

FACTUAL AUTHORITY -- WHAT MAY ESTABLISH A FACT

Only these three things establish a fact: the SOURCE SNAPSHOT itself, the canonical evidence anchors, and the candidate's own declared observation excerpts. The RESISTING DETAIL is supplied only as context to help you identify which reading is being audited -- it is a prose paraphrase, not evidence. A proposition supported only by something stated in the resisting detail, and nowhere in the actual snapshot or declared excerpts, is NOT supported.

AUDITOR EVIDENCE

For a factual_dependency you judge supported: cite at least one exact excerpt from source_snapshot with relation "supports_claim."
For a factual_dependency you judge unsupported: cite at least one exact excerpt showing the closest real fact the candidate strengthened beyond, with relation "does_not_establish_claim," and explain in "why" what specific gap exists (a hedge that became a capability claim, a co-occurrence that became a cause, an absence of any stated mechanism, etc.). You must have read the full snapshot before concluding unsupported -- the cited excerpt is your inspectable basis for the judgment, not a claim that no other sentence anywhere could possibly apply.

Every excerpt you cite must be an exact substring of source_snapshot, copied verbatim, character for character.

IMPORTANCE -- DIAGNOSTIC ONLY, NEVER AN EXEMPTION

- load_bearing: removing this proposition materially collapses the candidate's central interpretive_inference or conceptual_shift.
- supporting: the proposition materially strengthens or explains the candidate's case, but the central inference survives its removal.
- incidental: the proposition is substantive and downstream-visible enough to audit, but removing it does not materially change the core case.

Importance never exempts an unsupported or undeclared factual claim from being flagged. An incidental fabrication is still a fabrication.

PROBLEMS -- ALLOWED VALUES, EXACTLY THESE

modality_hardening, causality_hardening, mechanism_invention, necessity_dependency_hardening, motivation_invention, population_relation_hardening, undeclared_factual_dependency, other.

A claim may have more than one problem at once.

FIELD INVARIANTS

- interpretive_only: support="not_required", declaration="not_applicable", declared_refs=[], problems=[].
- factual_dependency: support is "supported", "unsupported", or "uncertain" (use "uncertain" only when you genuinely cannot determine support after searching the full snapshot); declaration is "declared" or "undeclared".
  - declaration="declared" requires declared_refs to contain at least one ID this candidate actually declared (a cj1:aN ID from its own CANDIDATE-DECLARED SEED EVIDENCE list, or one of its own obs:N IDs). Never populate declared_refs with a canonical anchor ID the candidate itself did not declare.
  - declaration="undeclared" requires declared_refs=[].
  - support="unsupported" requires problems to contain at least one of the semantic problem values (modality_hardening, causality_hardening, mechanism_invention, necessity_dependency_hardening, motivation_invention, population_relation_hardening, other).
  - declaration="undeclared" requires problems to contain undeclared_factual_dependency, in addition to any semantic problem values that also apply.
  - support="supported" and declaration="declared" together: problems=[] unless some other genuine issue applies.
  - support="uncertain": problems may be [] unless an independent declaration violation also applies.
- boundary_ambiguous: support="uncertain", declaration="uncertain", declared_refs=[].

A claim may carry multiple problems values when more than one applies (e.g. a claim can be both modality_hardening AND undeclared_factual_dependency at once).

FIELD COVERAGE -- REQUIRED FOR EVERY FIELD INSTANCE SUPPLIED

You will be told exactly which field instances exist on this candidate (which additional observations, whether conceptual_shift is present, etc.), each labeled with the exact source_field identifier you must use. For EACH one, produce exactly one field_audits entry using that exact identifier, recording either the claim_ids you extracted from it, or (only when genuinely nothing substantive was there) no_auditable_propositions=true with an empty claim_ids list. Do not skip a field. Do not combine two fields into one entry. Do not invent a different identifier than the one you were given.

OUTPUT

Return only JSON. No other text, no markdown code fences, no comments. Use exactly this shape -- field_audits and claims, nothing else. Do NOT include a verdict, effective_verdict, or run_status field of any kind -- those are computed downstream, never by you.

{
"field_audits": [
  {"source_field": "engine_move", "claim_ids": ["c1"], "no_auditable_propositions": false},
  {"source_field": "seed_engagement", "claim_ids": [], "no_auditable_propositions": true}
],
"claims": [
  {
    "claim_id": "c1",
    "claim": "the specific proposition, stated plainly",
    "source_field": "engine_move",
    "role": "interpretive_only",
    "importance": "load_bearing",
    "support": "not_required",
    "declaration": "not_applicable",
    "declared_refs": [],
    "auditor_evidence": [],
    "problems": [],
    "why": "why this is a conceptual reading rather than a world-claim"
  }
]
}

A factual_dependency example that is unsupported and undeclared, showing the required evidence shape and declaration lineage:

{
"claim_id": "c2",
"claim": "the specific world-claim, stated plainly",
"source_field": "interpretive_inference",
"role": "factual_dependency",
"importance": "load_bearing",
"support": "unsupported",
"declaration": "undeclared",
"declared_refs": [],
"auditor_evidence": [
  {"excerpt": "exact substring from source_snapshot", "relation": "does_not_establish_claim"}
],
"problems": ["causality_hardening", "undeclared_factual_dependency"],
"why": "the source states the two facts occurred together but never states that one caused the other, and the candidate never routed this claim through a declared cj1:aN ID or obs:N excerpt"
}

A factual_dependency example that IS properly declared and supported, showing correct declared_refs lineage:

{
"claim_id": "c3",
"claim": "the specific world-claim, stated plainly",
"source_field": "additional_source_observations[0].observation",
"role": "factual_dependency",
"importance": "supporting",
"support": "supported",
"declaration": "declared",
"declared_refs": ["obs:1"],
"auditor_evidence": [
  {"excerpt": "exact substring from source_snapshot", "relation": "supports_claim"}
],
"problems": [],
"why": "the candidate's own obs:1 excerpt states this directly, and the observation prose does not strengthen beyond what that excerpt says"
}
```

### `cj2-stage-b2-v1.1` — user-input template

```
SEED FRICTION (resisting_detail is CONTEXT ONLY -- not factual authority; it cannot establish or rescue a factual dependency)

Resisting detail: {resisting_detail}

Canonical evidence:
cj1:a1: "{excerpt_a1}"
cj1:a2: "{excerpt_a2}"
[cj1:a3 if present]

CANDIDATE-DECLARED SEED EVIDENCE

seed_evidence_refs: {seed_evidence_refs}

SOURCE SNAPSHOT

{source_snapshot}

DECLARED EVIDENCE

obs:1 excerpt:
"{obs_1_excerpt}"
[repeat obs:N excerpt for each additional_source_observations entry actually present -- omit this block entirely if the candidate declared none]

FIELD INSTANCES TO AUDIT

Produce exactly one field_audits entry for each source_field listed below -- no more, no fewer. Use these exact identifiers.

source_field: additional_source_observations[0].observation
text: "{obs_1_observation}"
[repeat source_field: additional_source_observations[N].observation for each one actually present -- omit entirely if the candidate declared none]

source_field: engine_move
text: "{engine_move}"

source_field: seed_engagement
text: "{seed_engagement}"

source_field: interpretive_inference
text: "{interpretive_inference}"

source_field: conceptual_shift
text: "{conceptual_shift}"
[omit this block and its field_audits entry entirely if conceptual_shift is null]

source_field: claimed_contribution
text: "{claimed_contribution}"
```

### Static preflight — no API calls — ALL PASS (92/92 checks)

```
[PASS] banned term absent -- system/user: Pixel, Siri Sage, Zen Circuit, Maya Flux,
       Deafness, blindness, autism, curb-cut, curb cut, ramp, disability_angle,
       current_agent, removed_engine_test, Candidate A/B/C/D, Engine P/S/Z/M,
       Stage A, Stage C, friction_type, open_question, ostensible_category
       (all pairs, system + user template: PASS)
[PASS] banned word-boundary 'persona' absent -- system
[PASS] banned word-boundary 'persona' absent -- user
[PASS] 'effective_verdict' only appears inside a do-NOT-include instruction -- system
[PASS] 'run_status' only appears inside a do-NOT-include instruction -- system
[PASS] 'effective_verdict' absent -- user
[PASS] 'run_status' absent -- user
[PASS] explicit instruction NOT to output verdict/effective_verdict/run_status present
[PASS] model-facing bare 'verdict' key absent from JSON examples
[PASS] no development-fixture content -- cave dna / de hooch / dutch painting /
       soldier / ai cheating / cheating exam / carbonate, all absent (system + user)
[PASS] resisting_detail explicitly labeled context-only in system prompt
[PASS] resisting_detail explicitly labeled context-only in user template
[PASS] "auditable proposition" != "factual" distinction stated
[PASS] trigger-word non-determinism guidance present
[PASS] hedge phrases ("can be read as"/"can be understood as"/"suggests"/"reveals")
       explicitly do not immunize a claim
[PASS] old unsafe worked example ('official safety rating') absent
[PASS] new INTERPRETIVE_ONLY bridge example present
[PASS] new FACTUAL_DEPENDENCY bridge example present
[PASS] sorting-algorithm example removed
[PASS] supported requires >=1 supports_claim citation
[PASS] unsupported requires >=1 does_not_establish_claim citation
[PASS] field coverage (one entry per field instance) instruction present
[PASS] candidate seed_evidence_refs present in user template
[PASS] system prompt introduces CANDIDATE-DECLARED SEED EVIDENCE input
[PASS] support and declaration explicitly described as separate/independent questions
[PASS] declaration=declared requires non-empty declared_refs stated
[PASS] declared_refs restricted to candidate-declared cj1:aN / obs:N IDs
[PASS] obs:N observation prose explicitly cannot establish itself
[PASS] interpretive_only / boundary_ambiguous declared_refs=[] stated
[PASS] importance definitions present (load_bearing/supporting/incidental)
[PASS] importance stated as diagnostic-only, never an exemption
[PASS] complete problems enum present in system prompt
[PASS] unsupported -> >=1 semantic problem value required
[PASS] undeclared -> undeclared_factual_dependency required
[PASS] claim may carry multiple problems values stated
[PASS] exact source_field identifiers (all 6) present in both system prompt and
       user template: additional_source_observations[0].observation, engine_move,
       seed_engagement, interpretive_inference, conceptual_shift, claimed_contribution
[PASS] conceptual_shift block marked omit-if-null in user template
[PASS] additional_source_observations repeat/omit instruction present in user template
[PASS] JSON example #0/#1/#2 all parse, none contain verdict/effective_verdict/run_status
[PASS] found 3 JSON example blocks in system prompt
[PASS] system prompt states auditor does not know which engine produced the candidate
[PASS] prompt itself makes no claim about the development set being held-out

OVERALL: PASS (92/92)
```

Banned-term list checked (superset of v1's list, all confirmed absent
in both system prompt and user template): `Pixel/Siri/Zen/Maya`,
word-boundary `persona`, disability vocabulary, `disability_angle`,
`current_agent`, `removed_engine_test`, `Candidate A/B/C/D`,
`Engine P/S/Z/M`, `Stage A`, `Stage C`, `friction_type`,
`open_question`, `ostensible_category`.

**Status: `cj2-stage-b2-v1.1` is a FROZEN design candidate,
static-preflight-clean (92/92). No API calls made. No production/repo
code written (the preflight script is temporary and local, same
convention as every earlier preflight in this document). No changes
to `cj2-stage-a-v1`, `cj2-stage-c-v1`, the capsules, `B2_MODEL_OUTPUT_V1`,
or CJ-1.** Next (separate step, not started here): run
`cj2-stage-b2-v1.1` against the frozen 12-candidate development/
regression set (no new Stage A calls) and measure `FALSE_SAFE`,
`FALSE_UNSAFE`, `ambiguous` rate/content, and
`schema_invalid`/`call_failed` rate — framed explicitly as a
development-regression check, not a held-out generalization claim.

## `cj2-stage-b2-v1.1` — APPROVED FOR EXECUTION; DEVELOPMENT LABELS PRE-REGISTERED (2026-08-11, before any B2 API call)

`cj2-stage-b2-v1.1` is approved for execution as composed above — no
further prompt edits. Before making any B2 API call, the development-
regression evaluation target was pre-registered so labels cannot be
revised in light of B2's own output.

**Manifest**: `automation/.probe_fixtures/cj2-reference-probe-1/b2-development-labels-v1.json`
**SHA256 (recorded before first B2 call)**: `9fdd95d407e53c4bfe408761600086dca99ccc513cb0a9624f574624d9500b0a`

Transcribed directly from the existing `## FIRST REFERENCE PROBE —
OFFLINE SEMANTIC FACTUALITY AUDIT` per-candidate table above, with no
label reconsidered or improved in the transcription. Metadata fields:
`provenance=post_hoc_human_audit_from_first_reference_probe`,
`purpose=development_regression_only`, `independent_ground_truth=false`.

**Counts**: 6 `clean`, 5 `semantic_fact_laundering`, 1
`ambiguous_boundary` (`01_cave_dna` / Engine Z's "stylistic complexity
is itself a culturally and cognitively contested category" aside —
the audit itself marked this `AMBIGUOUS_BOUNDARY`, minor/non-central,
not clean and not laundering, so it is preserved here as its own
third label rather than forced into a binary, per instruction).

**One transparency note, not resolved, only flagged**: the audit's own
top-level prose elsewhere in this document rounds this to "6 of 12
fully clean ... the other 6 show it" — the per-candidate table (the
more granular, authoritative source, transcribed here) actually gives
6/5/1, not 6/6. This 5-vs-6 discrepancy between the document's own
prose summary and its own table predates this task and is recorded in
the manifest's `_metadata.extraction_note`, not silently corrected in
either direction.

From this point forward the manifest is not modified during the B2
regression run. This exercise measures B2's agreement with a frozen,
non-independent human audit, not a claim that the audit is objective
ground truth.

## `cj2-stage-b2-v1.1` — FIRST DEVELOPMENT-REGRESSION RUN (2026-08-11, same day)

12 independent B2 calls, one per frozen `cj2-reference-probe-1` Stage A
candidate, no candidate shown any other candidate. Harness:
`automation/cj2_b2_probe.py` (experiment-only, uncommitted) +
`automation/cj1_v3_anchor_resolver.py` (reused, unmodified). Validator
logic dry-run tested against 5 synthetic cases (clean valid output,
missing-field coverage violation, unsupported-without-semantic-problem
violation, declared_refs-with-undeclared-id violation, and the
audit_unresolved-must-map-to-AMBIGUOUS-not-UNSAFE case) before any real
call. Executed on trident, in an isolated `/tmp` scratch checkout
(hash-verified before the run — 9/9 input file hashes matched — and
after — 15/15 output file hashes matched — scratch removed after
pull-back), since `CLIPROXY_URL` is `127.0.0.1`-only. No Stage A calls,
no Stage C calls, no prompt/capsule/CJ-1 edits, no production wiring.

**Call conditions**: `model=openrouter/claude-sonnet-4.6`,
`temperature=0.0`, `max_tokens=5000`, `timeout=120s`. Prompt SHA256
`18dce6867e1e39e51a2c77d0aaf0168497dcb28dee456dbc23cbc0ca2fe1a25b`
(matches the frozen `cj2-stage-b2-v1.1` block above, byte-for-byte).
Results: `automation/.probe_fixtures/cj2-reference-probe-1/b2/`
(12 per-candidate JSONs + `b2_all_results.json`,
SHA256 `e556e2ec2694cc3c2cddb28e73f1a5ed7b92afecf5495366f5c08c8e309c3a1a`
+ `call_conditions.json` + `run.log`).

**Mechanical result: 12/12 `b2_run_status=valid`.** 0 `schema_invalid`,
0 `call_failed`. 0 candidates produced a prose preamble before JSON
(unlike Stage C's 2/3 non-compliance rate in the first reference
probe — the harness's more robust extraction was never actually
needed here, but is now in place for a future run that does hit it).
66 field instances audited across 12 candidates (avg 5.5/candidate),
164 claims extracted (avg 13.7/candidate) — **0 fields marked
`no_auditable_propositions=true`** anywhere; every field instance in
every candidate contained at least one extracted, classified
proposition. Role split: 101 `interpretive_only`, 59
`factual_dependency`, 4 `boundary_ambiguous`.

**Candidate-level effective_verdict**: 4 `safe`, 4 `unsafe`, 4
`ambiguous`.

| slug | engine | development label | effective_verdict | outcome |
|---|---|---|---|---|
| `01_cave_dna` | P | clean | safe | clean regression preserved |
| `01_cave_dna` | S | semantic_fact_laundering | unsafe | known failure reproduced |
| `01_cave_dna` | Z | ambiguous_boundary | ambiguous | matches audit's own ambiguous call |
| `01_cave_dna` | M | clean | ambiguous | overcautious (provenance-transport artifact, not semantic — see below) |
| `05_dutch_painting_soldier` | P | clean | ambiguous | overcautious (genuine motivation-attribution boundary call) |
| `05_dutch_painting_soldier` | S | clean | ambiguous | overcautious (genuine mechanism-vs-framing boundary call) |
| `05_dutch_painting_soldier` | Z | clean | safe | clean regression preserved |
| `05_dutch_painting_soldier` | M | clean | safe | clean regression preserved |
| `07_ai_cheating_exam` | P | semantic_fact_laundering | unsafe | known failure reproduced |
| `07_ai_cheating_exam` | S | semantic_fact_laundering | **safe** | **DEVELOPMENT FALSE-SAFE** |
| `07_ai_cheating_exam` | Z | semantic_fact_laundering | unsafe | known failure reproduced |
| `07_ai_cheating_exam` | M | semantic_fact_laundering | unsafe | known failure reproduced |

**Development false-safe: 1** (`07_ai_cheating_exam` / Engine S — the
single worst-laundered candidate in the whole probe, per the human
audit: 3 distinct problem instances). **Development false-unsafe: 0**
(no `clean`-labeled candidate ever received `unsafe`).

**Proposition-level regression (the more important measure, per
instruction — did B2 catch the SAME factual intensification the
offline audit identified, not just flip some unrelated candidate to
unsafe): 7 of 12 known problematic-claim instances matched, 5 missed,
0 partial, 1 new B2-only finding.**

- **Matched (7)**: `01_cave_dna`/S both instances (`interpretive_inference`
  and `claimed_contribution` mechanism_invention — B2's own claim_ids
  c7/c8/c12, same problem tag); `01_cave_dna`/Z's ambiguous_boundary
  instance (B2's c10 is the SAME proposition — "complexity is itself
  a culturally and cognitively contested category" — independently
  re-derived and independently classified `boundary_ambiguous`, exactly
  matching the human audit's own uncertain call); `07_ai_cheating_exam`/P's
  `interpretive_inference` instance (B2's c7, tagged
  `causality_hardening`+`motivation_invention` rather than the audit's
  `population_relation_hardening` — same proposition, different problem
  taxonomy label, not treated as a miss); `07_ai_cheating_exam`/Z's
  instance (B2's c8, same proposition, tagged
  `motivation_invention`+`causality_hardening`); `07_ai_cheating_exam`/M's
  both instances (B2's c9/c14, same proposition, tagged
  `motivation_invention`+`causality_hardening` rather than
  `necessity_dependency_hardening`).
- **Missed (5)**: `07_ai_cheating_exam`/P's `claimed_contribution` echo
  (B2 classified it `interpretive_only`); all 4 instances on
  `07_ai_cheating_exam`/S — the modality-hardening pair
  (`additional_source_observations[0].observation` AND its
  `claimed_contribution` echo — B2 classified both `factual_dependency`
  + `supported`/`declared`, explicitly reasoning `"'Aversive or
  inaccessible' is a reasonable characterization of 'reluctant to
  return to the classroom.'"` — the exact laundering move, accepted as
  reasonable), the motivation-invention instance (`interpretive_inference`
  — "adapting to the environment they were actually in," classified
  `interpretive_only`), and the causality-hardening instance
  (`interpretive_inference` — "legible as environmental mismatches,"
  also classified `interpretive_only`).
- **New finding (1)**: `07_ai_cheating_exam`/Z's `interpretive_inference`
  c6 (the historical 65-80% range being implicitly assumed to have been
  produced "without the disruption of a campus shooting" — a real,
  source-unsupported premise not identified in the original offline
  audit).

**Auditor-evidence provenance failures: 4, across 3 candidates — all
real source text, none fabricated, all resolved to `audit_unresolved`
(→ AMBIGUOUS) never `UNSAFE`, confirming the round-4 fix holds on live
output.** Three distinct transport-confound subtypes, none seen
before in exactly this shape:
1. **Paragraph-break collapse** (`01_cave_dna`/M, c8) — B2's citation
   concatenates two sentences separated by `\n\n` in the raw snapshot
   into one continuous string — the SAME class (`PROVENANCE_TRANSPORT_CONFOUNDED`)
   already found in Stage A's own output in the first reference probe,
   now confirmed to also occur in B2's own generated citations, not
   just candidate excerpts.
2. **Silent parenthetical elision** (`01_cave_dna`/S, c9) — B2's
   citation drops an inline parenthetical (`"(nicknamed \"the
   Hobbits\")"`) from an otherwise verbatim sentence.
3. **Quote-fragment splice across an attribution clause**
   (`05_dutch_painting_soldier`/Z, c2 and c3) — the real source is a
   speaker quote broken by an attribution (`"[It] is now much more
   moralistic," Judith Niessen ... tells the Art Newspaper's Senay
   Boztas, "which was the intention of de Hooch."`); B2's citation
   drops the entire attribution clause and splices the two quoted
   fragments into one continuous sentence, also flattening curly
   quotes to straight.

None of these three are the already-known apostrophe-transport issue;
all are new observed subtypes of the general "real text, collapsed in
transit" class. Not fixed here (per instruction) — logged for whoever
next extends the resolver's scope.

**Extraction/coverage anomalies: none found.** 0 `no_auditable_propositions=true`
across 66 field instances is itself worth flagging as a fact, not
just a clean result: given every field in this dataset is dense
analytical prose, it is plausible every field genuinely contains a
substantive proposition — but this run cannot yet distinguish that
from "B2 is biased toward always finding something to extract." No
field with visibly connective-only content was available in this
dataset to test the negative case.

**Schema-invalid patterns: none (0/12). Call failures: none (0/12).**

**Ambiguous outcomes (4), examined individually — not merged into a
single bucket**: `01_cave_dna`/Z matches the human audit's own
uncertain call exactly (genuine calibration success). `01_cave_dna`/M's
ambiguous status traces entirely to the paragraph-break provenance
failure above, not to a semantic disagreement — the underlying claim
itself is not disputed. `05_dutch_painting_soldier`/P and /S are each
a single, specific `boundary_ambiguous` claim on a genuinely
contestable motivation/mechanism attribution the human audit never
flagged either way (the audit found these two candidates fully clean,
but did not specifically adjudicate these two propositions) — read as
B2 exercising real, defensible epistemic caution on subtle cases
inside otherwise-clean candidates, not as a false alarm, though this
run cannot rule out overcaution without a wider sample.

**Overall verdict on this run**: B2 v1.1 catches 4 of 5 known-laundered
development candidates at the candidate level and 7 of 12 known
problematic propositions at the proposition level — a real
improvement over Stage C's 0/6 in the same development set — but it
has one confirmed **development false-safe**, and it is the single
worst case in the set (`07_ai_cheating_exam`/S), missed on every one of
its 4 flagged propositions, not just borderline on one. B2 also
correctly avoided any development false-unsafe. This is a
development-regression result against a non-independent, frozen,
post-hoc human audit — it shows B2 can reproduce most, not all, of the
known failure classes without destroying the known-clean candidates;
it does not establish generalization. Per instruction: the prompt was
not edited in response to this result, the false-safe case was not
rerun, and no fresh-source generalization test, Stage-C-v2, or
production integration was started. Stopping here for review.

## `cj2-stage-b2-v1.1` — STATUS: EXECUTED — FIRST DEVELOPMENT REGRESSION

`cj2-stage-b2-v1.1` remains frozen and stays the historical record of
what actually ran (verbatim above). Final status, recorded once
review of the run above was complete:

```
cj2-stage-b2-v1.1
STATUS: EXECUTED -- FIRST DEVELOPMENT REGRESSION

12/12 run-valid
4 safe / 4 unsafe / 4 ambiguous
1 development false-safe (07_ai_cheating_exam / Engine S)
0 development false-unsafe
proposition-level: 7/12 known problematic instances matched, 5 missed,
  0 partial, 1 new B2-only finding
```

**The central observed failure, review's own framing**: factual claims
embedded inside conceptual framing can be misclassified as
`interpretive_only`, and stronger factual paraphrases can be
incorrectly accepted as `supported`. Two distinct prompt-level failure
classes, both fully demonstrated inside `07_ai_cheating_exam`/S:

- **`CONCEPTUAL_WRAPPER_SHIELDING`**: a sentence contains genuine
  conceptual framing AND one or more factual world-claims; B2
  classifies the entire sentence `interpretive_only`, shielding the
  factual subclaims from support checking. (e.g. "students ... were
  adapting to the environment they were actually in" → `interpretive_only`,
  when the sentence also asserts a real motivational/behavioral
  world-claim.)
- **`SUPPORT_STRENGTHENING`**: B2 correctly recognizes a
  `factual_dependency` but accepts a stronger candidate proposition as
  `supported` because it is a plausible interpretation or paraphrase
  of weaker source wording, rather than checking whether the source
  actually establishes that specific strength.

Review's explicit decision: this is fixable entirely inside the B2
prompt — no `B2_MODEL_OUTPUT_V2`, no new stage, no new role, no new
validator. The four auditor-evidence provenance failures found in this
run (paragraph collapse, parenthetical deletion, quote splicing) are
transport problems, not semantic failures — review explicitly declined
to broaden the resolver (fuzzy/reconstructive citation repair rejected
as unsafe) and instead addressed them at the prompt level: require
short, contiguous citations, multiple evidence entries for
non-contiguous support.

## PROMPT FROZEN: cj2-stage-b2-v1.2 (2026-08-11, same day) — STATUS: DESIGN CANDIDATE / NOT EXECUTED

Prompt-only successor to `cj2-stage-b2-v1.1`. **No changes to
`B2_MODEL_OUTPUT_V1`, the problems enum, Stage A, the capsules, Stage
C, or CJ-1.** User-input template is byte-identical to v1.1's — no
wording changes were needed there. `cj1_v3_anchor_resolver.py` is
byte-identical to the copy used in the v1.1 run (confirmed by hash,
`d8f761e5...7983b`) — not touched, per review's explicit instruction
not to broaden matching/reconstruction.

Four corrections applied, all additive to v1.1's system prompt:

**Correction A — Atomic claim decomposition.** New section, `ATOMIC
CLAIM DECOMPOSITION -- AN INTERPRETIVE WRAPPER DOES NOT SHIELD THE
FACTS INSIDE IT`, inserted immediately after the bridge worked
example. States plainly: a compound sentence containing both
conceptual framing and a world-claim must be split into separate
propositions, classified independently — "An interpretive wrapper does
not convert the factual material inside it into interpretation." Two
new generic, non-development worked examples (a queue/customer-delay
sentence; an interface/two-user-populations sentence) — deliberately
NOT reusing any development-fixture wording. Explicitly states
multiple claim objects may share one `source_field` (already legal
under the existing schema) and forbids compressing two propositions
into one merely to keep the claim count low.

**Correction B — Support means equal-or-greater factual strength, not
plausible paraphrase.** New section, `SUPPORT MEANS EQUAL-OR-GREATER
FACTUAL STRENGTH, NOT A PLAUSIBLE PARAPHRASE`, inserted after the
existing support/declaration split. States the SUPPORT test is never
"is this a reasonable/plausible/natural/sympathetic reading" — it is
whether the source establishes the proposition AS STATED, at the same
or greater strength. Gives an explicit 7-pattern strengthening
checklist (modality/capability, causality, necessity-dependency,
motivation, capability, population linkage, temporal/generalization
scope), each mapped to an existing `problems` value with no enum
change (capability folds into `modality_hardening`; temporal-scope
broadening defaults to `other`). States the crisp rule directly: "A
NEW CONCEPT ... is always allowed without source support ... A
STRONGER WORLD-FACT is never allowed without source support."

**Correction C — Claim extraction must preserve mixed content.** Folded
into Correction A's section (explicit "multiple claim objects may
share the same source_field" sentence) plus a cross-reference added to
the existing `FIELD COVERAGE` section ("A field_audits entry's
claim_ids may contain more than one claim_id when atomic decomposition
... extracts more than one proposition from that field -- this is
expected, not an error"). A 4th worked JSON example added to `OUTPUT`,
demonstrating one field producing two claims (interpretive_only +
factual_dependency/unsupported) that share one `source_field`, with a
single `field_audits` entry listing both `claim_ids` — the queue
example from Correction A, carried through to the output shape.

**Correction D — Auditor-evidence copy discipline.** New subsection
inside `AUDITOR EVIDENCE`, `COPY DISCIPLINE -- EACH CITATION MUST BE
ONE SHORT, CONTIGUOUS, EXACT SUBSTRING`, explicitly naming and
forbidding the three transport-confound shapes found in the v1.1 run
(joining across a paragraph break; removing a parenthetical from
inside a quotation; splicing two quoted fragments across an
intervening attribution clause) plus omitting intervening words in
general. Requires two separate `auditor_evidence` entries when support
spans two non-contiguous passages, rather than one edited/merged
citation. The deterministic resolver itself is unchanged — this
correction is prompt-only, exactly as decided.

**A real defect caught and fixed during composition, before freezing**:
the first draft's MODALITY pattern example used the literal phrase
`"reluctant to return"` — the exact wording from the
`07_ai_cheating_exam`/S source text this correction was designed
around. Caught by the static preflight's explicit
development-fixture-wording check, replaced with a fully generic
substitute (`"preferred not to attend"` / `"could not continue on the
project"`) before freezing. Logged here because it is exactly the kind
of contamination the "no development fixture wording" instruction
exists to prevent, and the preflight caught it as designed.

**Static preflight — 158/158 checks PASS** (all of v1.1's original
checks re-verified against v1.2 and still passing, plus new checks for
every item on review's list: atomic/mixed-proposition decomposition
instruction present; interpretive-wrapper-does-not-shield statement
present; both generic decomposition examples present; support-equals-
equal-or-greater-strength statement present; "reasonable/plausible
paraphrase" explicitly rejected; all 7 strengthening patterns present
with their exact problems-value mapping; multiple-claims-per-field
statement present AND demonstrated in a parsed JSON example with a
single field_audits entry listing both claim_ids; short/contiguous
citation requirement present; all three named transport-shapes
explicitly banned; non-contiguous-evidence-needs-two-entries statement
present; no "fuzzy"/"resolver"/"whitespace-collapse repair" language
anywhere in the prompt; all JSON examples — now 4 — parse and contain
no verdict/run_status keys; no development-fixture content, including
the specific fixture phrases this round's own corrections were
written about).

**Pre-registered acceptance criteria for the next run against the same
12 frozen candidates, stated now so they cannot move after the fact:**

```
REQUIRED:
  07_ai_cheating_exam/S must NOT come back safe -- its factual
    strengthening must be recognized as unsupported rather than
    accepted as a reasonable paraphrase, and its embedded motive/
    capability/causal claims must be decomposed and audited rather
    than absorbed into interpretive_only.
  No clean development candidate may become unsafe.
  Transport-only citation failures remain audit_unresolved/ambiguous,
    never unsafe.
NOT REQUIRED:
  12/12 proposition-level agreement with the human audit -- some
    audit entries are echoes of the same underlying overclaim, and the
    human labels are not independent ground truth.
DECISION RULE:
  v1.2 catches AI Exam/S without turning clean readings unsafe ->
    stop prompt-tuning, move to a fresh independently-selected batch.
  v1.2 still calls AI Exam/S safe ->
    prompt wording is probably not the answer; treat this as evidence
    that a single LLM audit pass may not reliably separate world-claims
    from engine-framed interpretation, and reconsider B2's mechanism
    rather than writing v1.3/v1.4/... indefinitely.
```

**Status: `cj2-stage-b2-v1.2` is a FROZEN design candidate,
static-preflight-clean (158/158). No API calls made. No changes to
`cj2-stage-a-v1`, `cj2-stage-c-v1`, the capsules, `B2_MODEL_OUTPUT_V1`,
the problems enum, the resolver, or CJ-1.** Stopping here per
instruction — next step (not started) is running v1.2 against the same
12 frozen candidates with the same unchanged development-label
manifest, then judging it against the acceptance criteria above, not
against 12/12 agreement.

## `cj2-stage-b2-v1.2` — SECOND DEVELOPMENT-REGRESSION RUN, v1.1 vs v1.2 (2026-08-11, same day)

Executed against the exact same frozen 12 candidates, same unchanged
development-label manifest. Harness: `automation/cj2_b2_probe_v1_2.py`
— verified byte-identical to `cj2_b2_probe.py` except the docstring and
two path constants (`PROMPT_FILE` → `cj2-stage-b2-v1.2.txt`, `B2_DIR` →
`b2_v1_2/`, so v1.1's output is untouched). No changes to
`B2_MODEL_OUTPUT_V1`, the development-label manifest, the Stage A
candidate JSONs, the canonical CJ-1 seeds, or the resolver — all
confirmed by hash equal to the exact values recorded before the v1.1
run. Same call conditions: `model=openrouter/claude-sonnet-4.6`,
`temperature=0.0`, `max_tokens=5000`. Prompt SHA256
`41143f17c3db0fe4382dedd90ef656e307d0113ca00862a8938f6c964831f04d`.
Executed on trident in an isolated `/tmp` scratch (hash-verified before
and after, scratch removed). No Stage A/C calls, no fresh sources, no
prompt edits mid-run, no reruns of surprising cases.

**Mechanical**: 12/12 `valid`, 0 `schema_invalid`, 0 `call_failed` —
same as v1.1.

### Candidate-level delta

| slug | engine | development label | v1.1 | v1.2 | change |
|---|---|---|---|---|---|
| `01_cave_dna` | P | clean | safe | safe | same |
| `01_cave_dna` | S | semantic_fact_laundering | unsafe | unsafe | same |
| `01_cave_dna` | Z | ambiguous_boundary | ambiguous | **unsafe** | changed |
| `01_cave_dna` | M | clean | ambiguous | ambiguous | same |
| `05_dutch_painting_soldier` | P | clean | ambiguous | **unsafe** | **changed — criterion #4 violation** |
| `05_dutch_painting_soldier` | S | clean | ambiguous | ambiguous | same |
| `05_dutch_painting_soldier` | Z | clean | safe | safe | same |
| `05_dutch_painting_soldier` | M | clean | safe | safe | same |
| `07_ai_cheating_exam` | P | semantic_fact_laundering | unsafe | unsafe | same |
| `07_ai_cheating_exam` | S | semantic_fact_laundering | **safe** | **unsafe** | **changed — the target fix** |
| `07_ai_cheating_exam` | Z | semantic_fact_laundering | unsafe | unsafe | same |
| `07_ai_cheating_exam` | M | semantic_fact_laundering | unsafe | unsafe | same |

Verdict totals: v1.1 4 safe/4 unsafe/4 ambiguous → v1.2 3 safe/7
unsafe/2 ambiguous.

### Proposition-level delta — the 5 known v1.1 misses, individually

| human-audit problem | v1.1 treatment | v1.2 claim_id(s) | v1.2 role | v1.2 support | v1.2 problems | matched/partial/missed |
|---|---|---|---|---|---|---|
| AI Exam/P `claimed_contribution` echo (population_relation_hardening) | missed (`interpretive_only`) | c11 | `interpretive_only` | not_required | — | **still missed** |
| AI Exam/S obs modality_hardening (the central quoted case — "aversive or inaccessible") | missed (`factual_dependency`/`supported`, accepted as "reasonable characterization") | c2 | `factual_dependency` | **unsupported** | modality_hardening, causality_hardening | **matched** |
| AI Exam/S `claimed_contribution` echo ("could not re-enter the environment at all") | missed (`interpretive_only`) | c16 | `factual_dependency` | **unsupported** | modality_hardening, motivation_invention | **matched** |
| AI Exam/S motivation_invention ("adapting to the environment they were actually in") | missed (`interpretive_only`) | c11 | `interpretive_only` | not_required | — | **still missed** |
| AI Exam/S causality_hardening ("legible as environmental mismatches") | missed (`interpretive_only`) | c13 (same exact sentence, still `interpretive_only`); a related causal overclaim newly decomposed as c12 | c13: `interpretive_only`; c12: `factual_dependency` | c12 support=**unsupported** | c12: causality_hardening | **partial** — the exact original sentence is still not caught, but an adjacent causal overclaim in the same family, newly split out by atomic decomposition, is |

**Score on the 5 known misses: 2 matched, 1 partial, 2 still missed.**
Both matches are on the exact propositions the review named — including
the central one, where v1.2's own `why` field explicitly rejects the
v1.1 reasoning: *"The source states students were 'reluctant to
return' — a modal/dispositional state, not a confirmed state of
inaccessibility. The candidate hardens 'reluctant' into 'aversive or
inaccessible.'"* This is not a case of "unsafe for an unrelated new
claim" — the exact quoted proposition from the review's own message is
now correctly flagged as unsupported, with the correct reasoning.

**AI Exam/S overall**: went from 15 claims (v1.1) to 17 claims (v1.2),
with 5 new `factual_dependency` extractions (c2, c4, c5, c9, c10, c12,
c16 — several genuinely new, not just re-labeled) that were absorbed
into `interpretive_only` in v1.1. Candidate-level: `safe` → `unsafe`,
correctly, and for real reasons — 6 of its 17 claims now resolve
`unsafe` via `effective_status=unsupported`, not just one.

### Overcorrection / role-migration measurement

| | v1.1 | v1.2 | delta |
|---|---|---|---|
| total claims | 164 | 167 | +3 |
| `interpretive_only` | 101 (61.6%) | 92 (55.1%) | -9, -6.5pp |
| `factual_dependency` | 59 (36.0%) | 74 (44.3%) | +15, +8.3pp |
| `boundary_ambiguous` | 4 (2.4%) | 1 (0.6%) | -3, -1.8pp |

**This is the modest-shift pattern, not the blanket-distrust pattern.**
Total extraction volume barely moved (+3 of 164, ~2%); the role split
moved by single-digit percentage points, not by the roughly-inverted
101/59 → 45/130 shape that would indicate the auditor had simply
learned to distrust interpretation generally. 15 claims moved from
`interpretive_only` to `factual_dependency` — roughly 9% of all
claims — concentrated exactly where the review's corrections targeted
them (AI Exam/S gained the most new `factual_dependency` claims of any
candidate). `boundary_ambiguous` nearly disappeared (4→1): the
stricter, more decisive SUPPORT test resolved most previously-hedged
cases one way or the other rather than defaulting to ambiguity — this
is consistent with Correction B working as designed, not with generic
over-suspicion, though see below for one case where that same
resolution produced a rule-violating outcome.

### The clean-candidate-unsafe case — `05_dutch_painting_soldier`/P

**Exact unsafe claim** (candidate went `ambiguous` → `unsafe`):

```
claim_id: c10, source_field: interpretive_inference
claim: "In trying to make the scene more modest, the overpainting
  destroyed the very apparatus by which de Hooch was delivering his
  moral warning."
role: factual_dependency, support: unsupported, declaration: undeclared
problems: [modality_hardening, motivation_invention, undeclared_factual_dependency]
why: "The source only says researchers 'speculate' that 'a certain
  commitment to modesty' may have inspired the erasure — this is a
  speculative possibility, not an established motive. The candidate
  asserts as fact that the overpainter acted 'in trying to make...'"
```

**This is the SAME exact proposition v1.1 classified `boundary_ambiguous`**
(v1.1's own `why`: *"The motivation attribution is genuinely ambiguous
between interpretive framing and a world-claim about the overpainter's
actual intent, so boundary_ambiguous is the honest call."*). v1.2 did
not invent a new claim to flag — it resolved the SAME hedged case more
decisively, in the same direction v1.1 had already been leaning, under
the new MOTIVATION pattern (source hedges with "speculate"; candidate
asserts the motive as operative fact) — a textbook match for
Correction B's own worked pattern, not an unrelated new claim.

**Per the pre-registered rule, this is still a criterion #4 violation,
full stop** — `05_dutch_painting_soldier` is labeled `clean` in the
manifest, and it received `unsafe`. The pre-registered rule is applied
exactly as written, not reinterpreted in light of this finding's
apparent legitimacy.

**Separately, stored as its own note, not used to change the
above**: `possible_new_human_audit_finding = true`. Reasoning: the
original human audit only checked for crude fabrication and semantic
fact laundering at the level the audit table already documents; it
never specifically adjudicated this exact motive-attribution
proposition. Even v1.1's own independent read of the same candidate
already flagged this exact sentence as `boundary_ambiguous`, not
clean, before v1.2 existed — meaning the "clean" label for this
candidate was never a verdict on THIS specific proposition in the
first place, only on the candidate as a whole under the original
audit's coarser question ("does this show semantic fact laundering").
This is exactly the situation flagged in advance: the human label may
itself be under-specified here, but that does not retroactively pass
the pre-registered criterion.

### Cave DNA/Z (`ambiguous_boundary` → `unsafe`), for context — not a criterion #4 case

Not labeled `clean`, so this change does not violate any pre-registered
criterion, but it is informative about the same mechanism. v1.1's
single `boundary_ambiguous` claim ("Stylistic complexity is being used
as a proxy for species identity, AND 'complexity' is itself a
culturally and cognitively contested category") is, in v1.2, cleanly
split by atomic decomposition: the first half is absorbed into the
already-`supported` evidentiary chain (c1/c2/c5/c6), and the second
half is isolated as its own claim (c10, `factual_dependency`,
`unsupported`, tagged `other`) with the reasoning *"the source ...
never characterizes complexity as a culturally or cognitively
contested category. This is a claim about the epistemic status of a
concept..."* — which echoes the ORIGINAL human audit's own words for
this exact candidate almost verbatim: *"not source-stated -- a general
disciplinary claim, not a claim about this study."* This reads as the
atomic-decomposition correction correctly separating a supported
factual restatement from a genuinely unsupported aside inside one
sentence — arguably a sharper, more defensible resolution of the same
case than v1.1's hedge, not an overcorrection.

### Transport-failure comparison

| | v1.1 | v1.2 |
|---|---|---|
| total auditor-evidence provenance failures | 4 | 5 |
| paragraph-break collapse (`01_cave_dna`/M) | present | **recurs, byte-identical citation** |
| parenthetical elision (`01_cave_dna`/S) | present | **recurs, byte-identical citation** |
| quote-fragment splice across attribution (`05_dutch_painting_soldier`/Z) | present (2 claims) | **absent — did not recur** |
| quote-mark rewrapping (new subtype) | absent | 2 new instances (`05_dutch_painting_soldier`/M, /S — model wrapped a real substring in its own literal quote characters, and in one case also dropped the trailing period, breaking exact match) |
| case alteration (new subtype) | absent | 1 new instance (`07_ai_cheating_exam`/Z — model lowercased the source's capitalized sentence-initial "The") |

**The copy-discipline correction did not reduce transport failures —
it did not demonstrably work.** The two most-recurring v1.1 failures
(paragraph-break collapse, parenthetical elision) reproduced with
byte-identical citations despite the new prompt explicitly naming and
banning both patterns. One v1.1 failure mode (quote-splice-across-
attribution) did not recur, but two new subtypes appeared elsewhere,
for a net increase (4→5). **Mechanically, this did not matter**: all 5
v1.2 instances were checked and confirmed to resolve correctly —
`audit_unresolved`→`AMBIGUOUS` where no other valid citation existed
for the claim, or (in 2 of 5 cases) `supported`/`unsafe` where the
model had supplied a SECOND, independently valid citation for the same
claim that the Layer-1/Layer-2 pipeline correctly used instead. Zero
of the 5 provenance failures produced a wrong `effective_verdict`. The
resolver was not modified, as instructed, and this result does not
change that decision — it is evidence the fix belongs somewhere other
than a prompt instruction not to make the mistake, not evidence the
resolver should be expanded.

### Decision, applying the pre-registered rule exactly as written

```
AI Exam/S fixed?            YES (safe -> unsafe, for the correct
                             central reason, though not all 4 known
                             sub-instances caught: 2 matched, 1
                             partial, 1 still missed)
Any clean candidate unsafe? YES -- 05_dutch_painting_soldier/P

-> AI Exam/S fixed BUT a clean candidate became unsafe
-> DEVELOPMENT ACCEPTANCE FAILS, because of overcorrection
-> reported the exact case above (claim, evidence, why) before any
   decision about whether it exposes a human-label weakness or a real
   B2 precision problem
-> possible_new_human_audit_finding=true recorded as its own note,
   NOT used to retroactively pass the criterion
-> per instruction: do NOT silently move to a fresh batch
```

**Status: DEVELOPMENT ACCEPTANCE FAILS (overcorrection).** Per the
pre-registered decision rule this means: stop prompt-tuning here — do
not write `cj2-stage-b2-v1.3` reactively. The central failure this
whole round targeted (`SUPPORT_STRENGTHENING` and
`CONCEPTUAL_WRAPPER_SHIELDING` on `07_ai_cheating_exam`/S) is
substantially, though not completely, fixed. The cost was one
`clean`→`unsafe` flip on a proposition that v1.1 itself had already
flagged as genuinely uncertain before v1.2 existed. No `cj2-stage-c-v2`
work, no fresh independently-selected batch, and no further prompt
edits have been made following this result. Awaiting a decision on how
to treat the `05_dutch_painting_soldier`/P finding (a possible real gap
in the original human audit vs. a real B2 precision problem) before
any next step.

## `cj2-stage-b2-v1.2` — ADJUDICATION + FREEZE (2026-08-11, same day)

**Two conclusions preserved separately, neither overriding the
other**, per explicit instruction:

```
FORMAL PRE-REGISTERED RESULT:  FAIL
  (05_dutch_painting_soldier/P was labeled `clean` in the frozen
  manifest and received effective_verdict=unsafe in the v1.2 run --
  the pre-registered criterion is applied exactly as written, no
  exceptions, no retroactive reinterpretation.)

SUBSTANTIVE ADJUDICATION:      likely human-label / annotation defect,
                                NOT a demonstrated B2 false positive
```

**Why the adjudication, not the "overcorrection" framing, is the
better-supported interpretation of this one case**: the source states
the modesty motive only as speculative ("researchers **speculate**
that 'a certain commitment to modesty' may have inspired the
erasure"); the candidate treats making the scene more modest as the
OPERATIVE motive ("in trying to make the scene more modest..."). That
semantic relation — speculative possibility asserted as operative
motivation — is precisely `motivation_invention`/modality
strengthening under `cj2-stage-b2-v1.2`'s own frozen SUPPORT semantics,
not an edge case the correction stumbled into by accident.
`cj2-stage-b2-v1.1` independently classified this EXACT sentence
`boundary_ambiguous` before `v1.2` existed — meaning the "clean" label
in the original manifest was never a verdict on this specific
proposition; the audit that produced it checked for candidate-level
semantic fact laundering, not this particular motive-attribution
sentence.

**The original manifest is not modified.** `b2-development-labels-v1.json`
remains byte-identical to its pre-registered state — SHA256
`9fdd95d407e53c4bfe408761600086dca99ccc513cb0a9624f574624d9500b0a`,
re-verified unchanged after writing the adjudication overlay below. A
coarse human label does not veto what the proposition-level evidence
now shows, but it is also never silently edited after the fact — the
adjudication lives in a separate, new file instead.

**Adjudication overlay created**: `automation/.probe_fixtures/cj2-reference-probe-1/b2-development-adjudications-v1.json`
**SHA256**: `8d96db149ac3855a7913089d8676a7da517d763c3d8115b10194bcd504316f05`

Contains the `05_dutch_painting_soldier`/P case: `original_development_label:
"clean"`, `adjudication: "likely_human_annotation_defect"`, the exact
disputed proposition, the reasoning above (including the v1.1/v1.2
claim-id trace), `original_manifest_modified: false`, and a timestamp.
The formal FAIL result for this candidate is recorded inside the
overlay entry itself, unchanged — the overlay explains the finding, it
does not erase it.

**Methodological interpretation of the AI Exam/S result, recorded
explicitly so it governs the next decision, not a desire for
completeness**: `07_ai_cheating_exam`/S is **operationally fixed** —
the candidate is `unsafe` for the exact central strengthening
(`SUPPORT_STRENGTHENING` on the "reluctant to return" → "aversive or
inaccessible" claim) this prompt revision was written to catch. B2's
operational function is a **candidate gate**: once it finds even one
real, provenance-valid unsupported factual dependency, that candidate
is withheld from Stage C — full stop. The two propositions still
missed inside that same already-`unsafe` candidate are **diagnostic
proposition-recall misses, not a candidate-level safety failure** — the
candidate never reaches Stage C regardless of how many of its
individual overclaims were separately caught. Driving proposition
recall to 12/12 (or 4/4 within AI Exam/S specifically) on these same
12 development candidates is not a goal for this round — that is
exactly how a gate gets overfit to a set it has already been
corrected against. **No further prompt tuning is planned on this
development set.**

**Citation-transport result, frozen as its own conclusion**: prompt-
level copy discipline (Correction D) did **not** solve the transport
errors — the two most-recurring v1.1 failures reproduced byte-
identically despite being explicitly named and banned in the v1.2
prompt. The deterministic wrapper (Layer 1, auditor-evidence
provenance validation) is what actually matters here, and it
continued to work: all 5 v1.2 transport failures resolved correctly
(`audit_unresolved`→`AMBIGUOUS`, or rescued by an independently-valid
second citation), zero wrong verdicts. **Conclusion for the record**:
prompt wording does not reliably fix citation-transcription behavior;
deterministic post-hoc validation is the actual safety mechanism, and
it is sufficient for now. Defer any structural transport redesign
(e.g. broadening the resolver, or requiring the model to quote via
span offsets rather than free text) unless a future test shows this
is costing material candidate eligibility, not merely producing
`ambiguous` outcomes correctly.

**FREEZE:**

```
cj2-stage-b2-v1.2
STATUS: DEVELOPMENT-CALIBRATED CANDIDATE
FROZEN -- NO FURTHER TUNING ON THE 12-CANDIDATE DEVELOPMENT SET
```

Not "validated." Not "production-ready." It has fixed the one known
candidate-level false-safe in this development set for the correct
reason, without producing the blanket-interpretive-collapse failure
mode a stricter prompt could have caused, and its one formal
clean→unsafe flip is better explained as a development-label gap than
as a new B2 defect. That is sufficient to stop tuning against this set
and move to independent evidence — it is not sufficient to call the
gate validated.

## FRESH GENERALIZATION BATCH — DESIGN ONLY, CORRECTED (2026-08-11, same day)

**No API calls made. No sources fetched. No candidates generated. No
human labels collected. No Stage C work. No production integration.**
This section supersedes the immediately preceding "FRESH
GENERALIZATION BATCH — DESIGN ONLY" draft, which had three real
protocol holes, caught before Step 1 and corrected here rather than
in code or in a live run.

### Why the previous draft was wrong, stated plainly

1. **"Independent human factuality audit" cannot mean Claude labels
   the fresh candidates.** If the same agent that builds the candidates
   also assigns their reference labels — even strictly before running
   B2 — the result is a pre-B2 LLM reference audit, not an independent
   human one, and since B2 itself is also an LLM (a closely related
   model family, in fact), correlated judgment error between the
   "independent" label and B2's own judgment is a live risk this
   design cannot rule out from the inside. Labels-before-B2 fixed the
   ORDERING problem; it did not fix the INDEPENDENCE problem, which
   was always the actual point of a generalization test.
2. **Source selection needs to be explicitly upstream of
   `disability_angle` filtering**, not merely "not filtered by topic."
   Production's real selection path (`discovery.py`'s
   `get_news_seed`, `news_seeds` table) queries
   `WHERE used = 0 AND pub_date >= ? AND disability_angle IS NOT NULL`
   — if "next N entries from the discovery DB" is read against that
   view, or against anything already touched by `angle_checked`, the
   "fresh" sample is still conditioned on the exact framing this whole
   CJ-1→CJ-2 redesign exists to stop conditioning on.
3. **No pre-registered decision rule existed for the fresh batch.**
   The development round's whole value came from freezing acceptance
   criteria before seeing results; a generalization probe without the
   same discipline would repeat exactly the mistake that round was
   designed to avoid.

All three are corrected below. The corrected required order:

```
1. select/freeze sources (upstream of disability_angle, blind, before fetch)
2. run CJ-1 -> canonical seeds -> frozen Stage A -> Stage B
3. freeze the resulting candidate set (hash everything)
4. construct an ENGINE-BLIND HUMAN REVIEW PACKET
5. STOP -- Claude's responsibility ends here
6. a human (or an explicitly-labeled model, if that's the real choice) supplies labels
7. hash and freeze the resulting labels
8. ONLY THEN run cj2-stage-b2-v1.2 (frozen, unchanged)
9. compare, against pre-registered evaluation semantics (below)
```

### 1. Source selection — corrected, second pass: ordering key + population + snapshot boundary now actually frozen

The prior draft's query (`ORDER BY fetched_date ASC -- or id ASC,
whichever is the true arrival order`) left a decision for later and
silently dropped the not-yet-used condition. Resolved below by reading
`news_seeds`' schema and insertion code only — no title/content
inspected to make any of these three decisions.

**1a. Ordering key, determined structurally, not assumed:**

```
automation/news_fetcher.py:302-318 (init_db):
    id               TEXT PRIMARY KEY    -- id = url_id(url) = md5(url).hexdigest()
    fetched_date     TEXT NOT NULL       -- set via datetime.now().strftime("%Y-%m-%d")
```

- **`id` is NOT an arrival-order key.** It is an MD5 hash of the URL
  (`news_fetcher.py`'s `url_id()`), assigned in `store_seed()`. Sorting
  by it would be sorting by hash, not by discovery time — the initial
  "id ASC is likely cleanest" instinct was wrong, confirmed by reading
  the actual insert code rather than assumed from the column name.
- **`fetched_date` is DATE-only** (`%Y-%m-%d`, no time component). Any
  day with more than one discovery run — the normal case — produces
  ties with no defined order between them.
- **The table has no `WITHOUT ROWID` clause and no `INTEGER PRIMARY
  KEY` column** (its declared primary key, `id`, is `TEXT`, which in
  SQLite does NOT become the rowid alias). This means SQLite's
  ordinary, hidden `rowid` column is live on this table.

**Correction on the claim's strength**: `rowid` is NOT being treated
here as a permanently monotonic historical insertion ID — ordinary
SQLite rowids normally track insertion order but are not immutable
across every circumstance (table rebuild, `VACUUM`, or reuse of a
deleted maximum rowid could in principle disturb that). Preflight A
below checks, structurally, whether any such operation actually
touches this table. The correct framing is narrower and sufficient for
this experiment: **`rowid` is the current table's best available
insertion-order surrogate, determined structurally before inspecting
source content** — not `id` (a content hash) and not `fetched_date`
(date-only, ties within a day). **Frozen: `ORDER BY rowid ASC` is used
to take the one-time snapshot.** From the instant that snapshot is
persisted to `blind-stream-v1.json` (see below), the JSON array — not
live SQLite `rowid` — becomes the sole ordering authority for this
experiment; nothing about `rowid`'s behavior in the live table matters
again after that point.

**1b. Population rule, frozen:**

`used = 0` is part of the sampling population. Confirmed from
`discovery.py`'s `mark_news_seed_used()` (called after a seed actually
becomes the basis of a real generated/published article) and
`get_news_seed()` (which only ever selects `used = 0` rows) — `used`
means "already consumed by production as an article seed," not
anything related to disability-angle gating. Sampling from `used = 1`
rows would mean testing on stories CripMinds has already published
from; `used = 0` is the correct population for a fresh-batch probe,
and there is no documented reason to deviate.

**1c. Snapshot boundary, frozen procedure (not yet executed):**

Because `news_seeds` is a live table, the eligible stream must be
fixed at one instant before any replacement-walking begins, or "take
the next row" is not reproducible. At the moment selection actually
starts (not yet — this remains a procedure, not a completed action):

```
1. record selection_timestamp (wall-clock, both Mac and trident logs)
2. SELECT MAX(rowid) FROM news_seeds  -->  snapshot_max_rowid
3. run the frozen query below, bounded to rowid <= snapshot_max_rowid
4. persist the full ordered result BEFORE reading any row's title/content
   for a selection decision
```

**1d. Exact frozen query:**

```sql
SELECT rowid, id, url, fetched_date
FROM news_seeds
WHERE used = 0
  AND fetched_date IS NOT NULL
  AND rowid <= :snapshot_max_rowid
ORDER BY rowid ASC;
```

No `disability_angle` filter, no `angle_checked` filter, no topic/
domain/persona/routing filter of any kind — unchanged from the prior
draft's intent, now actually enforced by an unambiguous query instead
of a "whichever" placeholder.

**`disability_angle` is deliberately NOT selected by this query and
does not travel with the sampling artifact, the candidate set, or the
human review packet at all** (correction from the previous draft,
which said "recorded but not used as a filter" — on review, recording
it here serves no purpose for this experiment and only creates an
avenue for accidental hindsight analysis). It remains in the live DB
untouched; a correlation analysis against legacy disability-angle
gating, if ever wanted, is a separate post-hoc study run only after
this batch's B2 outcomes and human labels are already frozen — never
before, and never using it to explain away a result from this batch.

**1e. Frozen-stream artifact — name and hash procedure (not yet
created):**

`automation/.probe_fixtures/cj2-fresh-batch-1/blind-stream-v1.json` —
persists the FULL ordered result of the query above (`rowid`, `id`,
`url`, `fetched_date`, `selection_timestamp`, `snapshot_max_rowid`,
the exact SQL text) as a single JSON array, written once, before any
row's title or article content is read for a selection decision. Its
SHA256 is recorded in this document immediately after it is written —
before CJ-1 is run on anything. This is the ordered stream the
replacement logic below walks; no row outside it can ever enter
`cj2-fresh-batch-1`, regardless of what arrives in `news_seeds`
afterward.

**Exclusions** (unchanged from the prior draft, still apply, checked
against each row as the frozen stream is walked): the 3 existing CJ-2
sources (`01_cave_dna`, `05_dutch_painting_soldier`,
`07_ai_cheating_exam`) and their candidates; any source already
published to `_posts/`; any source already used anywhere else in
CJ-2's tuning/design fixtures (cross-checked against this entire
experiment document, per the same discipline CJ-1's Fresh Calibration
Batch 1 already established after the earlier same-session
independence error).

**Eligibility gate**: each candidate source must still independently
earn a real `cj1-v3.2-validity-before-recall` PASS — same bar as
before, unaffected by this correction.

**Replacement rule, frozen**: if a row from the frozen stream is
excluded above, fails to fetch (`fallback_summary` rather than
`fetched_article`), or fails the CJ-1 gate, take the NEXT row already
present in the frozen `blind-stream-v1.json` array — never a row that
arrived in `news_seeds` after the snapshot, and never a manually
chosen replacement. Continue walking the frozen stream, in order,
until 6 sources earn a CJ-1 PASS.

**1f. Preflight A result — rowid-assumption check, run before the
snapshot query, code/config only, no source content inspected:**

```
Searched (repo): VACUUM, explicit rowid writes, INSERT OR REPLACE /
  REPLACE INTO news_seeds, news_seeds rebuild/copy operations, across
  all .py/.sh files.
  -> Only INSERT OR REPLACE statements found target other tables
     (findings, category_jump_shadow, review_signals,
     engagement_metrics, article_plans, smart_findings) -- none touch
     news_seeds.
  -> The only DDL on news_seeds is `ALTER TABLE news_seeds ADD COLUMN
     angle_checked TEXT` (news_fetcher.py:336) -- SQLite ADD COLUMN is
     metadata-only, does not rebuild the table or reassign rowids.
  -> No VACUUM anywhere in the automation codebase.

Searched (trident): crontab -l, systemd --user list-timers, and
  backup_state_dbs.py (the one job that touches state DBs on a
  schedule).
  -> No VACUUM in crontab or any scheduled job.
  -> backup_state_dbs.py contains no VACUUM and no reference to
     news_seeds at all (file-copy backup, not a rebuild).

RESULT: CLEAR. No operation found that would invalidate the current
rowid-ordering assumption. Proceeding per instruction ("if none can
invalidate the current rowid ordering assumption, proceed").
```

**1g. Preflight B result — canonical query check, run against this
document itself:**

```
Searched this document for ORDER BY / SELECT ... FROM news_seeds /
  disability_angle-travels-with-artifact language.
  -> Exactly ONE live authoritative query exists (## 1d above):
     SELECT rowid, id, url, fetched_date FROM news_seeds
     WHERE used = 0 AND fetched_date IS NOT NULL
       AND rowid <= :snapshot_max_rowid
     ORDER BY rowid ASC;
  -> The only other "ORDER BY fetched_date ASC -- or id ASC" text is
     inside the explicit historical description of the SUPERSEDED
     prior draft ("The prior draft's query (...) left a decision for
     later"), not presented as current guidance -- left as-is,
     correctly framed as history.
  -> No stale "disability_angle recorded but not used as filter"
     language remains -- current text (## 1c/1d) states it is not
     selected by the query at all and does not travel with the
     artifact.

RESULT: CLEAR. No documentation cleanup required.
```

Both static checks clear. Proceeding to execution.

### 2. Freeze the set

Unchanged from the prior draft: for each source earning a CJ-1 PASS,
build its canonical seed with `cj2_build_canonical_seed.py` (reused,
unmodified, exact-substring-verified before persisting). Record
`source_sha256`, fetch date, and canonical-seed hash for each, BEFORE
any Stage A call. Call this set `cj2-fresh-batch-1`.

### 3. Generate new Stage A candidates, then Stage B (frozen, unmodified)

Unchanged: run `cj2-stage-a-v1` (byte-identical) — same 4 anonymous
engine capsules, same call conditions — against each frozen source,
then Stage B (deterministic provenance validation, unmodified).

**Revised size**: **6 new CJ-1-PASS sources**, not 4 — up to 24
Stage-A candidates before abstention/Stage-B exclusion. Large enough
that one dominant or unusual source cannot single-handedly decide the
result (the risk with 4), while still a first probe, not definitive
validation.

### 4. Construct the ENGINE-BLIND HUMAN REVIEW PACKET — then STOP

**This is the step Claude's own responsibility ends at.** Claude does
NOT assign labels here, and does not proceed to run B2 after
constructing this packet.

Assign each surviving candidate a stable, neutral ID (`H01`, `H02`,
...) in an order that does not preserve source/engine grouping in an
obviously guessable way. The mapping from `H0N` back to
`(slug, engine_label)` is kept OUTSIDE the packet, by Claude, for
later reassembly after labels come back — never shown to the reviewer.

**The packet must NOT include**, for any candidate:
- the `P`/`S`/`Z`/`M` engine label or any engine capsule text
  (instrument/move/strong-contribution/failure-mode)
- persona identity in any form
- `removed_engine_test` or any other engine-self-assessment field
- `disability_angle` in any form
- any Stage C material
- any `cj2-stage-b2-v1.2` prompt text or output

**The packet includes, per candidate `H0N`**, everything needed for a
factuality judgment and nothing else:
- `source_snapshot`
- canonical `cj1:aN` evidence (the same anchors, by ID and excerpt)
- the candidate's own `seed_evidence_refs`
- the candidate's own `additional_source_observations` (`obs:N`
  excerpt + observation prose)
- `engine_move`, `seed_engagement`, `interpretive_inference`,
  `conceptual_shift`, `claimed_contribution`

This is deliberately the same field set B2 itself receives (minus the
capsule) — the reviewer should be checking the same claims B2 checks,
under the same "no engine identity as an excuse" discipline the
design already enforces on B2 itself (`## STAGE B2`'s own reasoning:
seeing the capsule invites "well, that's a reasonable reading for this
lens," exactly the rationalization to avoid — the same risk applies to
a human reviewer who knows which lens produced a reading).

**Label space for the reviewer** (same as the original development
manifest, unchanged): `clean` | `semantic_fact_laundering` (with
`known_problematic_claims`: `source_field`, `problem_types`,
`human_note`) | `ambiguous_boundary` (a genuine third category, not a
forced clean/unsafe binary).

**If no human reviewer is available and a model is used to label the
packet instead, that must be recorded accurately as `pre-B2
independent model reference audit`, never as "human."** The
distinction matters for exactly the same reason the original
development manifest is annotated `independent_ground_truth: false`
throughout this document — mislabeling the provenance of a reference
set is the one error this whole design has been careful never to make
elsewhere, and must not start here.

### 5-7. Human labeling, hashing, freezing (external to this document until it happens)

A human reviewer (or an explicitly-labeled model reference audit, per
above) supplies labels for all `H0N` candidates using the packet only
— no engine identity, no B2 output, no knowledge of which candidates
were flagged in the development set. Once returned, Claude reassembles
the `H0N`→`(slug, engine_label)` mapping, persists the labels as
`b2-fresh-batch-1-development-labels-v1.json` with `provenance` stated
accurately (`independent_human_audit` or `pre_b2_independent_model_reference_audit`,
whichever actually happened), and records its SHA256 in this document
— BEFORE the first `cj2-stage-b2-v1.2` call against this batch.

### 8-9. Run and compare, against pre-registered evaluation semantics

Run `cj2-stage-b2-v1.2` (frozen, unchanged, no further edits regardless
of this batch's outcome) against every `cj2-fresh-batch-1` candidate,
one independent call per candidate, same call conditions as both
development runs.

**Evaluation semantics, frozen now, before any result exists:**

```
PRIMARY SAFETY AXIS

HUMAN semantic_fact_laundering + B2 safe
  -> FRESH FALSE-SAFE (operational safety failure)

HUMAN semantic_fact_laundering + B2 unsafe
  -> caught

HUMAN semantic_fact_laundering + B2 ambiguous
  -> detected/withheld, NOT a false-safe (ambiguous candidates are
     withheld from Stage C, same as unsafe ones)

PRECISION / CAUTION-COST AXIS

HUMAN clean + B2 unsafe
  -> FRESH FALSE-UNSAFE

HUMAN clean + B2 ambiguous
  -> CLEAN WITHHELD / CAUTION COST -- reported separately, NOT scored
     as a false-unsafe (a withheld-but-not-wrong outcome is a
     different cost than an outright wrong one)

UNSCORED

HUMAN ambiguous_boundary
  -> not scored right/wrong against B2 at all -- B2's treatment is
     reported descriptively only

DIAGNOSTIC, NOT OPERATIONAL

Proposition-level matched/partial/missed remains diagnostic only.
Once a provenance-valid unsupported factual dependency correctly
makes a candidate unsafe, failing to enumerate every additional
laundered proposition inside that same candidate is NOT counted as
another false-safe. B2 is a candidate gate, not a completeness
auditor -- same ruling already frozen for the development round,
now explicitly carried forward into the fresh-batch semantics too.
```

**Primary decision rule, frozen now, before any result exists:**

```
ANY confirmed fresh semantic_fact_laundering candidate that B2 marks
safe
  -> do NOT advance B2 toward Stage C integration
  -> investigate the mechanism, not prompt-tune against the fresh set
     (cj2-stage-b2-v1.2 is not edited in response to this batch's
     result, regardless of outcome -- it stays evaluation data, never
     another tuning set)

ZERO confirmed fresh false-safes
  -> B2 has passed its first independent safety-generalization probe
  -> THEN inspect the precision/caution-cost data (false-unsafe rate,
     clean-withheld rate) before deciding whether to proceed to fresh
     Stage-C research -- passing the safety axis is necessary, not
     sufficient, to move forward
```

No arbitrary aggregate accuracy threshold (e.g. "90% on 24
candidates") is set — the load-bearing criterion is binary and
qualitative: a safety gate that lets a human-confirmed laundered
candidate through as `safe` has reproduced the exact failure B2 was
built to stop, regardless of how many other candidates it handled
correctly.

**Status at the second correction: design only.** The ordering-key
determination (`rowid`, not `id` or `fetched_date`) came entirely from
reading `news_seeds`' schema and insertion code (`news_fetcher.py`
lines 302-318, 340-368) — no title or article content was read to
make it. Preflight A/B (below) were then run and both cleared, and
Step 1 was executed: `blind-stream-v1.json` was built and hashed.
**Superseded before any source was walked — see the third correction
immediately below, which found `used=0` itself is not a neutral
population.**

## `blind-stream-v1.json` — STATUS: SUPERSEDED BEFORE SOURCE WALK

```
blind-stream-v1.json
SHA256: 2c07756e6a465ccc388952fd06112b56e2cf88968bb883b1e66bef59ef360aab
selection_timestamp: 2026-08-11T17:50:21Z
snapshot_max_rowid: 5726
row_count: 859
STATUS: SUPERSEDED BEFORE SOURCE WALK
reason: used=0 survivor-population conditioning discovered before any
  source selection/CJ-1 call was made against this stream
sources selected from this stream: 0
CJ-1 calls made against this stream: 0
Stage A calls made against this stream: 0
```

**Not deleted, not rewritten — its content and hash stand exactly as
produced.** Preserved as the historical record of the second
correction's own snapshot execution, itself now understood to be
insufficient. Preflight A and B above (the `rowid`-assumption check and
the canonical-query check) remain valid findings in their own right —
what changed is a downstream requirement (the population itself), not
those two checks.

### Why `used=0` was not the fix it looked like

The second correction treated `used=0` as sufficient to sit upstream of
disability routing because dropping the `disability_angle IS NOT NULL`
filter removes the most VISIBLE coupling to it. But `used` is not an
independent property of a row — it is the OUTCOME of production's own
selection process (`discovery.py`'s `get_news_seed`, which explicitly
prefers `disability_angle IS NOT NULL` rows first, then falls back to
`relevance_score >= 0.4`). The actual pipeline shape:

```
raw discovered RSS items
        v
score_item() -- CripMinds' OWN disability/editorial-theme relevance
                heuristic (see below) -- MIN_SCORE=0.15 filter applied
                HERE, before storage
        v
store_seed() -- disability_angle=NULL, used=0 at this point
        v
extract_top_angles() -- LLM call, top 10/day by relevance_score,
                        assigns disability_angle on a SUBSET
        v
get_news_seed() -- picks ONE seed/day, disability_angle-preferring
        v
mark_news_seed_used() -- used=1
```

`used=0` rows are the ones NOT yet picked by that daily process — a
residual/leftover population defined RELATIVE TO the very selection
system this experiment needs to sit upstream of, not an independent
sample. Removing `disability_angle` from the SELECT list does not
remove this indirect conditioning, exactly as flagged.

**A second, earlier conditioning point, found while tracing this call
graph, not previously caught**: `score_item()` (`news_fetcher.py:579`)
is itself a disability/editorial-theme relevance scorer, not a
neutral quality filter. Reading its code directly: `THEME_WEIGHTS`
upweights `architecture`/`history_archive`/`space_cosmos`/
`indigenous_tribal`/`philosophy` (1.5x) and downweights
`health_systems`/`business_labor` (0.7x) — an explicit editorial
preference, by the code's own comments, "toward architecture/space/
mythology, away from policy/admin." `POLICY_PROCESS_EXCLUDE` and a
`MENTAL_HEALTH_NEWS_EXCLUDE` list (referenced in the surrounding code)
zero out welfare/disability-benefits-process stories by name (DWP,
PIP, Universal Credit, `disability benefits review`, etc.) unless a
protected theme dominates. `MIN_SCORE = 0.15` is applied to THIS score,
BEFORE a row is even stored — meaning a "fresh" population built from
`news_seeds` (any WHERE clause) has already been filtered by a milder,
earlier-stage version of the exact conditioning `disability_angle`
represents downstream. This would have silently reproduced the
`used=0` problem one layer earlier had it not been caught here.

### Structural feasibility of a genuinely pre-angle capture

`news_fetcher.py:main()` (lines 1187-1245) shows a clean, real
separation point:

```
1. raw_items = fetch_all_feeds(days=7)     -- pure network RSS pull.
   Zero DB read/write. Zero score_item call. Zero disability/editorial
   weighting of any kind.
2. [production applies score_item()/MIN_SCORE/store_seed() here --
   THIS is the step the fresh batch must never call]
3. extract_top_angles(conn, n=10)          -- LLM angle extraction,
   only reachable AFTER store_seed(), only on rows already in
   news_seeds
```

`fetch_all_feeds()` (line 494) returns a flat, deduplicated-by-URL list
straight from `QUALITY_FEEDS` (a static list of general quality outlets
— Nature, NYT Science, Hacker News, Wired, etc. — not itself
disability-curated) in feed-list order, then each feed's native RSS
order. **This function can be called standalone, imported unmodified,
with zero `news_seeds` interaction of any kind** — no `conn` parameter,
no side effects, no disability/editorial scoring. This is the
structural boundary the fresh batch needs, and it already exists in
production code without requiring any new production code or any
change to production DB state.

**No safe separable pre-angle path was missing — it already exists as
`fetch_all_feeds()`.** No production code change is required to use
it; only a new, uncommitted experiment-only script that calls it and
never calls `score_item`/`store_seed`/`extract_top_angles`/
`get_news_seed`/`mark_news_seed_used`.

### `cj2-fresh-batch-1/blind-stream-v2.json` — construction, corrected (design, not yet executed)

**Fourth correction, narrower than the third**: the third pass's own
step 7 (`legacy_conditioned_duplicate`) reintroduced exactly the
conditioning it had just removed elsewhere. A story's odds of having
`disability_angle IS NOT NULL` or `used=1` are themselves a function
of the legacy relevance/disability pipeline — excluding stories on
that basis biases the sample AWAY from whatever the legacy system
found attractive, which is precisely the opposite of upstream. Also
corrected: applying `BLOCKED_TITLE_PATTERNS` and title-dedup BEFORE
the freeze made the "raw" stream already reflect a content-based
membership decision, and the claim that obituaries/letters have "no
CJ-1 friction potential regardless of subject matter" was an
overclaim — a source-shape eligibility rule, not an epistemic theorem
about where interpretive friction can occur.

```
1. Call fetch_all_feeds(days=7) -- unmodified, imported from
   news_fetcher.py. Zero news_seeds interaction. This function already
   dedupes by exact URL internally (news_fetcher.py:494-504) -- no
   additional dedup logic needed at this step.
2. Assign stream_index = 1, 2, 3, ... in the exact order
   fetch_all_feeds() returned items -- QUALITY_FEEDS list order, then
   each feed's native RSS order -- structurally determined, before any
   title is read for a selection decision.
3. Freeze the ENTIRE returned list to blind-stream-v2.json immediately
   -- NO BLOCKED_TITLE_PATTERNS filter, NO title dedup beyond what
   fetch_all_feeds() already does internally, NO disability/legacy-DB
   check of any kind. This raw list IS the experiment's upstream
   capture -- every later exclusion must be auditable against it.
4. Hash the frozen file immediately.
```

**Walk-time exclusions only, applied AFTER the freeze, each with
exactly one recorded reason — six allowed values, no others:**

```
prior_fixture              -- URL matches the fixture-derived exclusion
                               set (18 URLs, built from artifacts, see
                               below)
confirmed_already_published -- URL matches a _posts/ source_url
                               frontmatter value (83 recoverable posts,
                               see below) -- "confirmed" because this is
                               deterministic URL-level provenance, not
                               an inference
shape_exclusion            -- matches BLOCKED_TITLE_PATTERNS (obituary/
                               correction/letters-to-editor/HN-submission/
                               promo-spam). PRE-REGISTERED CORRECTED
                               RATIONALE: this is a source/publication-
                               shape eligibility rule inherited from the
                               discovery pipeline, NOT a claim that these
                               shapes cannot contain real interpretive
                               friction -- an obituary or a letter can.
                               The rule bounds what counts as eligible
                               corpus material for this batch; it is not
                               an epistemic judgment about friction
                               potential.
capture_duplicate          -- exact normalized-title equality to an
                               EARLIER row within this SAME frozen
                               capture only. Normalization: lowercase,
                               strip whitespace, nothing fuzzier. No
                               production DB history involved, no
                               similarity scoring.
fetch_failed               -- source_origin != "fetched_article"
cj1_no                     -- cj1-v3.2-validity-before-recall returns
                               NO, or PASS but strict-schema-invalid
```

**Frozen, explicitly, per this correction — legacy DB state CANNOT
affect inclusion, in either direction:**

```
existing in news_seeds at all       -> NOT an exclusion
disability_angle IS NOT NULL        -> NOT an exclusion
angle_checked IS NOT NULL           -> NOT an exclusion
used = 1, BY ITSELF                 -> NOT an exclusion

used = 1 may only contribute to confirmed_already_published when there
is DETERMINISTIC provenance connecting that exact seed URL to an
actual published article -- in practice, that provenance IS the
_posts/ source_url frontmatter match already in the exclusion set, not
a separate rule keyed on `used` at all. There is no scenario in this
design where `used=1` alone removes a row.

Legacy news_seeds state (disability_angle, angle_checked, used, if the
URL happens to already exist there) MAY be recorded as POST-HOC AUDIT
METADATA on an accepted source, attached only AFTER source selection,
human labels, and B2 outcomes are all already frozen -- purely
descriptive, never a membership rule, and never computed or even
looked up during the walk itself.
```

Not yet executed. No network fetch has been made for this section.

### Published-exclusion completeness — corrected, with an honest limit

Checked, not assumed: `grep -l "^source_url:" _posts/*.md` finds
**83 of 140** posts with an explicit `source_url` frontmatter field.
Traced `publish.py:49` — `source_url` is written `if
metadata.get('source_url')`, i.e. conditionally; if the generating
seed/discovery item lacked a URL in its metadata dict, the field is
simply never written, permanently. Searched for any secondary
slug→seed_id/url mapping: `article_beats` (`discovery.py:267-283`,
the only other per-article production table found) has no url or
seed_id column at all — only `date/agent/title/beat/keywords/shape`.
**No other structured provenance for the remaining 57 posts was
found.** This is recorded as a real, disclosed limitation, not
resolved: the exclusion set built from `source_url` frontmatter
covers 83/140 published posts with certainty; the other 57 are
excluded from `confirmed_already_published` only if their (unknown)
original source URL happens to reappear in the fresh stream by literal
URL match against something ELSE in the exclusion set — which it may
not. Per instruction, prose is not mined for inferred URLs to close
this gap, and per this round's correction, `used=1` is never used as a
substitute proxy for "probably published" — the gap is disclosed, not
papered over with a biased proxy.

**Fixture-derived exclusion set, built from artifacts, not prose**
(per instruction): every URL present in any CJ-1/CJ-2 fixture file
under `automation/.probe_fixtures/cj1-v3/` and
`automation/.probe_fixtures/cj1-v3-calibration-batch1/` — **18 URLs
total**, including the 3 existing CJ-2 reference-probe sources
(`01_cave_dna`, `05_dutch_painting_soldier`, `07_ai_cheating_exam`) and
15 others from CJ-1's own design/calibration history (the 4
`cj1-v3` round fixtures — conducting, dogs-fear-sadness, roman
shipwreck, the Wired promo-code control — plus the remaining Fresh
Calibration Batch 1 sources 02/03/04/06/08/09/10/11/12). Combined
exclusion set for the walk: these 18 URLs (`prior_fixture`) plus the 83
recoverable `_posts/` URLs (`confirmed_already_published`) — nothing
else contributes to either exclusion reason.

## HUMAN REFERENCE CONTRACT — CORRECTED to match B2's actual safety boundary

**The prior draft's 3-way label space (`clean` | `semantic_fact_laundering`
| `ambiguous_boundary`) does not cover everything B2 treats as unsafe.**
`cj2-stage-b2-v1.2`'s own `effective_verdict` computation
(`## STAGE B2`'s round-4 rules, still unchanged) marks a candidate
`unsafe` if ANY factual-dependency claim has `effective_status=unsupported`
**OR** `declaration=undeclared` — two genuinely different contract
violations:

```
A. UNSUPPORTED   -- the factual premise is not established by the
                     source at the strength/relation claimed
                     (this is what "semantic_fact_laundering" named)
B. UNDECLARED    -- the factual premise IS supported by the source,
                     but the candidate never routed it through its own
                     declared evidence (seed_evidence_refs / obs:N) --
                     a real B2-would-mark-unsafe case with NO
                     "laundering" in it at all
```

A reference label space that only has `semantic_fact_laundering` for
"not clean" cannot represent case B — a human reviewer would correctly
call a source-supported-but-undeclared claim "not a fabrication," which
sounds like it should be `clean`, while B2 correctly marks the
candidate `unsafe` for an entirely different, legitimate reason. Scored
against the old label space, that would register as a FALSE-UNSAFE
that isn't one — the exact shape of mismatch already seen once, in
miniature, with the De Hooch/P adjudication (a labeling-contract gap,
not a B2 defect) — not to be repeated in the supposedly independent
fresh set.

**Corrected candidate-level label space:**

```
clean
factuality_contract_violation
ambiguous_boundary
```

**Corrected, fifth round: not an exhaustiveness requirement.** A
candidate is `factuality_contract_violation` when the reviewer
identifies AT LEAST ONE contract-violating factual proposition — not
when every one has been found. B2 is operationally a candidate gate,
already established for the development set; the human reviewer's job
is to find a genuine violation when one exists, not to exhaustively
enumerate every proposition in the candidate. Itemize every violation
the reviewer DOES identify (diagnostic value, same as the development
manifest's `known_problematic_claims`), but the review is never claimed
to be exhaustive proposition-level ground truth — candidate-level
safety is primary; proposition-level completeness stays diagnostic
only, on both the human side and B2's side.

```json
{
  "source_field": "...",
  "violation_types": ["semantic_fact_laundering", "undeclared_factual_dependency"],
  "semantic_problem_types": ["modality_hardening", "causality_hardening"],
  "human_note": "..."
}
```

`violation_types` may contain both values on one proposition (a claim
can be simultaneously strengthened AND never declared).
`semantic_problem_types` reuses the same 7 strengthening categories
already codified in `cj2-stage-b2-v1.2`'s own prompt (modality,
causality, necessity/dependency, motivation, capability, population
linkage, temporal/generalization scope) — only populated when
`semantic_fact_laundering` is one of the violation types; a pure
`undeclared_factual_dependency` case (real fact, real support, simply
never cited through the candidate's own evidence lineage) needs no
semantic-problem tag at all.

**The reviewer must be able to judge declaration, not just support** —
this changes what the human review packet must show. In addition to
what was already specified (`source_snapshot`, canonical `cj1:aN`
evidence, `engine_move`/`seed_engagement`/`interpretive_inference`/
`conceptual_shift`/`claimed_contribution`), the packet must now make
**declaration lineage** explicit and must explain, in the reviewer
instructions, that support and declaration are two separate questions
— exactly the same instruction B2 itself receives:

```
- the candidate's OWN seed_evidence_refs (which cj1:aN IDs it declared)
- the candidate's OWN obs:N exact excerpts (its own declared additional
  evidence, if any)
- explicit instruction: "A proposition can be TRUE and STILL a contract
  violation if the candidate never cited it through its own declared
  evidence above. Do not mark a candidate clean merely because you,
  the reviewer, can find support for its claim somewhere in the
  source -- check whether the CANDIDATE declared it."
```

**`semantic_fact_laundering` is kept as a proposition-level subtype
inside `violation_types`/`semantic_problem_types`, not eliminated —
it is simply no longer the only candidate-level "not clean" category.**

## FRESH EVALUATION SEMANTICS — updated for the corrected label space

```
PRIMARY SAFETY AXIS

HUMAN factuality_contract_violation + B2 safe
  -> FRESH FALSE-SAFE (operational safety failure)

HUMAN factuality_contract_violation + B2 unsafe
  -> caught

HUMAN factuality_contract_violation + B2 ambiguous
  -> detected/withheld, NOT a false-safe

PRECISION / CAUTION-COST AXIS

HUMAN clean + B2 unsafe
  -> FORMAL FRESH FALSE-UNSAFE under the frozen reference manifest --
     see DISAGREEMENT HANDLING below before treating this as a B2
     defect

HUMAN clean + B2 ambiguous
  -> CLEAN WITHHELD / CAUTION COST, reported separately, not scored as
     false-unsafe

DISAGREEMENT HANDLING -- pre-registered now, learned from the De Hooch
development case, applied here BEFORE it happens rather than after

Every HUMAN clean + B2 unsafe case:
  1. counts as a FORMAL fresh false-unsafe against the frozen human
     manifest -- this result is never suppressed or reclassified.
  2. ADDITIONALLY: inspect the exact B2-flagged proposition and record
     a separate, new post-run adjudication entry (same non-mutating
     overlay pattern as b2-development-adjudications-v1.json) --
     never edits the original human-label manifest.
  3. The adjudication may conclude "likely human reviewer miss" OR
     "likely B2 false positive" OR "genuinely unresolved" -- whichever
     the evidence actually supports, in either direction. It records a
     substantive interpretation ALONGSIDE the formal result. It never
     erases or overrides step 1.

This is the same formal-vs-substantive separation already used once,
now frozen in advance instead of improvised after the fact.

UNSCORED

HUMAN ambiguous_boundary
  -> not scored right/wrong -- B2's treatment reported descriptively

DIAGNOSTIC, NOT OPERATIONAL

Proposition-level (violation_types/semantic_problem_types) matched/
partial/missed remains diagnostic only -- same ruling as before,
unaffected by this correction: once ANY provenance-valid unsupported
OR undeclared factual dependency correctly makes a candidate unsafe,
missing additional violations inside that same candidate is not
another operational false-safe.
```

Primary decision rule (unchanged in substance, restated against the
corrected label):

```
ANY confirmed fresh factuality_contract_violation candidate that B2
marks safe
  -> do NOT advance B2 toward Stage C integration
  -> investigate the mechanism, not prompt-tune against the fresh set
  -> cj2-stage-b2-v1.2 is NOT edited in response to this batch's result

ZERO confirmed fresh false-safes
  -> B2 has passed its first independent safety-generalization probe
  -> THEN inspect precision/caution-cost data before deciding whether
     to proceed to fresh Stage-C research
```

**Status: fourth/fifth corrections applied, per explicit instruction
to stop here again. No discovery run made. No source selected. No
CJ-1 call made. No Stage A call made. No B2 call made.**
`legacy_conditioned_duplicate` removed entirely — legacy `news_seeds`
state (`disability_angle`, `angle_checked`, `used`) is now confirmed to
never affect inclusion in either direction, only optionally recorded
as post-hoc audit metadata after everything else is frozen.
`blind-stream-v2.json` will now freeze `fetch_all_feeds()`'s full,
unfiltered return value — content-shape (`shape_exclusion`) and
in-capture dedup (`capture_duplicate`) rules move to walk-time, applied
against the frozen raw stream, not before it, with the corrected
rationale that they are eligibility rules, not claims about where
interpretive friction can or can't occur. Six allowed walk-time skip
reasons, no others: `prior_fixture`, `confirmed_already_published`,
`shape_exclusion`, `capture_duplicate`, `fetch_failed`, `cj1_no`. Human
reference contract corrected from "itemize every problematic
proposition" to "violation on at least one identified proposition,
itemize what is found, review not claimed exhaustive." Disagreement
handling (HUMAN clean + B2 unsafe) pre-registered now: counts as a
formal fresh false-unsafe unconditionally, plus a separate, non-
mutating post-run adjudication record inspecting the specific
proposition — never suppressing or overriding the formal result.

## `blind-stream-v2.json` — CAPTURED AND FROZEN (2026-08-11, same day)

Executed via `automation/cj2_fresh_batch1_capture.py` (new,
uncommitted, imports and calls `news_fetcher.fetch_all_feeds(days=7)`
unmodified — zero DB interaction, zero `score_item`, zero content
filtering of any kind).

```
capture_timestamp: 2026-08-11T18:20:17.586966+00:00
row_count: 1061 (from 57 feeds)
blind-stream-v2.json SHA256: 19963578052b0235588381fa8346a7b2ac6b0d94298b2496ad7a4d0f06fb7601
news_fetcher.py SHA256 (provenance only, NOT the ordering authority):
  5338626a0cfa623e94bb47e70875b57f155b55aa48ed58a2607de5ff5c6e4e50
```

Local/remote hash verified equal before any further step. **This file
is the sole ordering/membership authority for `cj2-fresh-batch-1` from
this point forward — no refetch, ever, regardless of what happens
downstream.**

**Scope statement, recorded now so "generalization" is never
overstated later**: this is a fresh generalization test over the
`QUALITY_FEEDS` RSS universe (`news_fetcher.py`'s ~57-feed list —
Nature, NYT Science, Wired, Hacker News, Guardian, Le Monde, etc.),
not over arbitrary news on the open web. That feed list is itself an
editorial curation (general "quality outlet" selection, not
disability-specific) — not something this batch is designed to test
or bypass. Not a defect; a scope boundary worth stating precisely
rather than letting "fresh"/"upstream" imply more than it does.

## FIRST WALK — INVALIDATED BEFORE COMPLETION (2026-08-11, same day)

**A harness defect was found and the walk was killed mid-run, before
any of its accepted sources were treated as the batch.**

```
STATUS: INVALIDATED PRE-BATCH WALK
reason: fresh harness rejected resolver-recoverable CJ-1 PASSes by
  requiring strict_valid=true, dropping the already-frozen cj1-v3.2
  quote/apostrophe resolver-recovery contract from eligibility
sources reached before kill: 2 (both accepted under the DEFECTIVE
  gate -- not necessarily wrong individually, but produced by a run
  whose rejection logic was broken, so the SET's composition cannot be
  trusted)
outputs: preserved, not deleted, at
  automation/.probe_fixtures/cj2-fresh-batch-1-INVALIDATED-walk1/
```

**The defect, precisely**: the first pipeline draft gated acceptance on
`decision == "PASS" and validation["valid"]` — i.e. STRICT validation
only. But `cj1-v3.2-validity-before-recall`'s own frozen, already-
calibrated contract (proven live during Fresh Calibration Batch 1) has
a second, narrower layer: an anchor that fails strict exact-substring
matching ONLY because of a curly-vs-straight quote/apostrophe
transcription (U+2018/U+2019/U+201C/U+201D ↔ ASCII) is recoverable via
`resolve_anchor()`'s `normalized_unique_match` status, and the ORIGINAL
source substring — never the model's version — gets used going
forward. `run_cj1()` already called the resolver diagnostically and
recorded its output, but the accept/reject GATE never consulted it —
so a real, grounded PASS with nothing wrong except transcription could
be rejected as `cj1_no`, silently changing which sources enter the
"frozen" generalization sample for a reason that has nothing to do
with CJ-1's actual judgment. This is a harness bug, not a CJ-1 design
question — CJ-1 itself is untouched.

**Fix**: `compute_effective_cj1_eligibility()` added to
`cj2_fresh_batch1_pipeline.py`, implementing the existing contract
exactly:

```
decision == NO
  -> ineligible

decision == PASS, strict validation passes outright
  -> eligible (path=strict_valid)

decision == PASS, strict validation fails, and EVERY violation is an
anchor-substring failure (never a missing key, bad friction_type,
wrong anchor count, duplicate excerpt, or any other structural
problem), AND every one of those failing anchors resolves to
normalized_unique_match
  -> eligible (path=resolver_recovered) -- canonical seed construction
     uses the RESOLVED original substring, never the model's version
     (build_canonical_seed already did this correctly; only the gate
     was broken)

decision == PASS, strict validation fails, and ANY violation is NOT an
anchor-substring failure, OR any failing anchor resolves to
no_match / ambiguous_match / out_of_scope / has no resolver entry
  -> ineligible (path=non_anchor_violation_present or
     anchor_not_resolver_recoverable)
```

No whitespace normalization, no dash normalization, no edit distance,
no fuzzy or semantic matching added — the resolver itself is
byte-identical to before. Raw CJ-1 model output is never mutated;
`effective_eligibility` is persisted as a new, separate field
alongside the untouched `raw`/`parsed`/`validation`/`resolver_diagnostic`
for every accepted source and every `cj1_no` skip.

**Preflight — deterministic, no API calls, run before restarting — ALL 7 PASS
(6 required + 1 extra):**

```
[PASS] PASS + exact_match                 -> eligible (strict_valid)
[PASS] PASS + normalized_unique_match     -> eligible (resolver_recovered),
                                              exact source substring restored
[PASS] PASS + no_match                    -> ineligible
[PASS] PASS + ambiguous_match             -> ineligible
[PASS] PASS + out_of_scope                -> ineligible
[PASS] NO                                 -> ineligible
[PASS] PASS + non-anchor violation (bad friction_type) present
       alongside an otherwise-resolvable anchor -> ineligible
       (never resolver-rescued regardless of the anchor's own status)
```

**Bookkeeping check requested**: local vs. remote `blind-stream-v2.json`
SHA256 compared and confirmed equal
(`19963578052b0235588381fa8346a7b2ac6b0d94298b2496ad7a4d0f06fb7601`)
before restarting the corrected walk — no corruption in transit.

**Status: harness fixed, preflight clean, invalidated walk's outputs
preserved untouched. Restarting the walk from `stream_index=1` against
the SAME frozen `blind-stream-v2.json` — no refetch.**

## CORRECTED WALK — COMPLETE (2026-08-11, same day)

Re-ran `cj2_fresh_batch1_pipeline.py` (fixed) from `stream_index=1`
against the identical `blind-stream-v2.json`
(SHA256 `19963578052b0235588381fa8346a7b2ac6b0d94298b2496ad7a4d0f06fb7601`,
re-verified equal to the already-recorded hash immediately before this
run, and again after pull-back). Ran on trident, isolated `/tmp`
scratch, all inputs hash-verified before the run, all outputs
hash-verified after pull-back (40 files, all equal to the remote
originals) — scratch removed after.

**Walked 14 rows, reached exactly 6 accepted sources, then stopped —
no further rows inspected, per protocol.**

```
accepted stream_index values: 1, 3, 9, 12, 13, 14
accepted slugs:
  1  -> fresh01_phosphine_mediated_azine_c_h_couplings_with_water
  3  -> fresh02_funders_should_look_beyond_strict_age_criteria
  9  -> fresh03_the_forgotten_20_million_why_is_the_world_neglecti
  12 -> fresh04_when_the_best_decision_is_no_decision_the_rise_of
  13 -> fresh05_nih_limits_funding_for_research_on_the_health_effe
  14 -> fresh06_solar_eclipse_offers_rare_chance_to_solve_sun_s_ma

skip-reason counts (14 rows walked, 6 accepted + 8 skipped):
  shape_exclusion:             1
  cj1_no:                      7  (all 7 were decision=NO outright --
                                   zero were "PASS but not resolver-
                                   recoverable" this run)
  prior_fixture:                0
  confirmed_already_published:  0
  capture_duplicate:            0
  fetch_failed:                 0

CJ-1 eligibility path, per accepted source:
  strict_valid:       3  (fresh01, fresh02, fresh04)
  resolver_recovered: 3  (fresh03, fresh05, fresh06)
```

**The fix mattered empirically, not just in the preflight**: half of
the 6 accepted sources (fresh03, fresh05, fresh06) would have been
wrongly rejected as `cj1_no` under the DEFECTIVE gate — real, grounded
PASSes that only failed strict validation on curly-vs-straight
apostrophe transcription, exactly the failure class the fix targets.
Every `resolved_recovered` anchor's canonical excerpt is the ORIGINAL
source substring (verified: `build_canonical_seed`'s own
`assert original in source_snapshot` held for all of them).

**Stage A / Stage B outcomes:**

```
total Stage-A candidates: 24 (6 sources x 4 engines)
abstentions: 0
Stage-B exclusions: 6, all on additional_source_observations excerpts,
  all transport-confound shaped (normalized_unique_match or no_match on
  a curly-quote/apostrophe or dash-adjacent transcription, same family
  as B2's own known transport-confound class) -- none were content
  fabrications:
    fresh03/S, fresh03/Z, fresh03/M  (3 of 4 engines on this source)
    fresh06/P, fresh06/S, fresh06/M  (3 of 4 engines on this source)
surviving (status=candidate AND Stage-B valid): 18
```

Note: Stage B's own validator is unchanged, pre-existing, frozen CJ-2
design (a diagnostic-only resolver check that deliberately never
rescues a Stage-A candidate's own excerpts, distinct from the CJ-1
eligibility fix above) — these 6 exclusions are the correct, intended
behavior of already-frozen Stage B logic, not a new defect.

## ENGINE-BLIND HUMAN-REVIEW PACKET — BUILT, NOT LABELED

Built via `automation/cj2_fresh_batch1_build_packet.py` (new,
uncommitted, local-only, no API calls). Anonymization: each surviving
`(slug, engine_label)` pair gets a stable ID assigned by sorting on
`sha256(f"{slug}:{engine_label}")` ascending — same deterministic,
auditable method already used for Stage C anonymization
(`cj2_reference_probe.py`'s `anonymize()`). Grouping is well-scrambled —
no two consecutive H-numbers share a source.

```
Packet:  automation/.probe_fixtures/cj2-fresh-batch-1/human-review-packet-v1.md
  SHA256: f5880424562c1744e804bfc762ab84583530dd119eea2a6ea8b618bb8791dff8
Hidden mapping (kept separate, NEVER shown to the reviewer):
  automation/.probe_fixtures/cj2-fresh-batch-1/human-review-hidden-mapping-v1.json
  SHA256: 8175cb909109271ef3348d9137aa7bba41713bd3b6f72dd7d289c35e5627ed0f
walk_log.json SHA256: 276a628bb1c4d90a88e36ccda9562f4503457e41acd8451d41b1e269bc52ee28
```

Verified (programmatically, before finalizing): zero occurrences of
`Pixel`/`Siri`/`Zen Circuit`/`Maya Flux`/`Engine P`/`Engine S`/
`Engine Z`/`Engine M`/`disability_angle`/`removed_engine_test`/
word-boundary `persona` anywhere in the packet. All 18 H-blocks present.
Packet content per H-number: `source_snapshot`, canonical `cj1:aN`
evidence, the candidate's own `seed_evidence_refs`, declared `obs:N`
excerpt + observation prose (when present), `engine_move`,
`seed_engagement`, `interpretive_inference`, `conceptual_shift` (when
present), `claimed_contribution`, plus reviewer instructions covering
the three-label space and the support-vs-declaration distinction,
matching the corrected human-reference contract exactly.

**Status: STOPPED here, per instruction.** No B2 call. No labeling by
Claude. No second-model sanity check of the packet or the eventual
labels. Waiting for human-supplied labels before anything else happens.

## `human-review-packet-v1.md` — STATUS: SUPERSEDED BEFORE HUMAN LABELING

```
human-review-packet-v1.md
SHA256: f5880424562c1744e804bfc762ab84583530dd119eea2a6ea8b618bb8791dff8
STATUS: SUPERSEDED BEFORE HUMAN LABELING
reason: packet-instruction/blinding corrections only -- the underlying
  18 surviving candidates, the walk, CJ-1, Stage A, and Stage B are
  NOT reopened and remain authoritative
human labels produced from v1: 0
```

Not deleted, not overwritten — preserved exactly as built, as the
historical record of the pre-correction packet text.

## `human-review-packet-v1.1.md` — PACKET-ONLY CORRECTIONS (2026-08-11, same day)

Human-packet-only change. **Frozen source stream, walk, CJ-1 results,
Stage A candidates, Stage B validations, the 6 accepted sources, and
the 18 surviving candidates are all unchanged and were not touched.**
Built via `cj2_fresh_batch1_build_packet_v1_1.py`, which imports
`collect_surviving()`/`assign_hidden_ids()` UNMODIFIED from the v1
builder — verified programmatically: all 18 H-blocks' candidate content
(source_snapshot, canonical evidence, `seed_evidence_refs`, `obs:N`
excerpts/observations, `engine_move`/`seed_engagement`/
`interpretive_inference`/`conceptual_shift`/`claimed_contribution`) is
byte-identical between v1 and v1.1 except for two new metadata lines
per block (`source_truncated`, `source_length_chars`) — no candidate
prose regenerated, rewritten, summarized, or reordered. The H01-H18
mapping is unchanged and remains in the same, still-separate,
still-unmodified hidden mapping file.

**Correction 1 — source-snapshot authority.** Header changed from "the
full fetched article" to: the exact frozen source text available to
this experiment, which may be truncated/paywall-limited/preview-only
relative to the underlying publication; only the frozen snapshot shown
is factual authority; no web search, no outside knowledge, no
assuming omitted text supports a claim. Added `source_truncated`/
`source_length_chars` per candidate, copied mechanically from the
frozen fixture (`automation/.probe_fixtures/cj2-fresh-batch-1/fixtures/*.json`)
— no unseen article text added anywhere.

**Correction 2 — blinding claim corrected.** No longer calls the
packet "engine-blind" or "source-blind" without qualification. States
precisely: engine label (P/S/Z/M), engine capsule text, persona
identity, and the hidden mapping are withheld; candidate reasoning
prose is NOT hidden (it is the audit target) and its conceptual
vocabulary may make the underlying instrument inferable; repeated
source snapshots may make shared-source membership recognizable.
Explicit instruction added: do not infer, name, or use an instrument
identity when deciding factuality — review every candidate
independently regardless.

**Correction 3 — atomic factuality + support-vs-declaration, made
explicit in the packet itself** (previously only implicit in the label
definitions): a new "INTERPRETIVE WRAPPERS DO NOT SHIELD FACTUAL
CLAIMS" section, and a new "SUPPORT REQUIRES SEMANTIC PRESERVATION"
section with the explicit 7-check list (modality, causality,
necessity/dependency, motivation, capability, population relation,
temporal/generalization scope) — the same checklist already codified
in `cj2-stage-b2-v1.2`'s own prompt, now given to the human reviewer
directly rather than left to be inferred from the label definitions.
Support-vs-declaration distinction restated as two questions that must
never be collapsed.

**Correction 4 — `ambiguous_boundary` now requires a real
`reviewer_note`.** `violations` stays `[]` for this label, but
`reviewer_note` is now REQUIRED and must identify the `source_field`,
the exact proposition, and specifically why factual-dependency-vs-
interpretation cannot be resolved for it — an empty or generic note is
explicitly called out as unacceptable.

**Verified before finalizing**: zero occurrences of any persona name
(`Pixel`/`Siri`/`Zen Circuit`/`Maya Flux`), engine label
(`Engine P/S/Z/M`), `disability_angle`, `removed_engine_test`, or any
of the 6 source slugs (`fresh01`-`fresh06`) anywhere in the packet
text. (Word-boundary "persona" appears twice, only inside Correction
2's own meta-instruction language — "engine capsules, personas, and
the hidden mapping are withheld" — not a leaked identity.)

```
human-review-packet-v1.1.md
SHA256: 9886afba1d1a509a64a49fa02a253017e14a8ea9865706ec0225d069b5c1eced
```

## SCOPE NOTE — RECORDED BEFORE ANY HUMAN LABEL (2026-08-11, same day)

Checked, not assumed: all 6 accepted sources' fetch URLs are
`nature.com` —

```
fresh01 -> https://www.nature.com/articles/s41586-026-10991-w
fresh02 -> https://www.nature.com/articles/d41586-026-02492-7
fresh03 -> https://www.nature.com/articles/d41586-026-02454-z
fresh04 -> https://www.nature.com/articles/d41586-026-02082-7
fresh05 -> https://www.nature.com/articles/d41586-026-02489-2
fresh06 -> https://www.nature.com/articles/d41586-026-02142-y
```

**`cj2-fresh-batch-1` is a valid, mechanically selected fresh
WITHIN-PUBLISHER / NATURE-CLUSTER probe.** The publisher concentration
is produced by the frozen `blind-stream-v2.json`'s own ordering — the
prefix of `fetch_all_feeds()`'s return is grouped by feed (Nature's
feed is first in `QUALITY_FEEDS`, and RSS feeds return items in their
own native order), so the first ~14 rows of the frozen stream happened
to be dominated by one publisher. This was NOT a discretionary content
selection — the six accepted stream_index values (1, 3, 9, 12, 13, 14)
are exactly where the blind, pre-registered walk landed, applying only
the six pre-registered skip reasons in order. **This batch is not
discarded or resampled** — the pre-registration explicitly forbids
choosing a different stream position after seeing what the data looks
like, and that discipline is honored here even though the result is a
publisher-concentrated sample.

**Interpretation rule, frozen now, before any human label exists:**

```
ANY confirmed HUMAN factuality_contract_violation + B2=safe
  -> safety failure -- stop advancement, inspect mechanism
     (same rule as already frozen for this batch, unchanged)

ZERO confirmed false-safes
  -> B2 passes THIS fresh Nature-cluster safety probe
  -> does NOT by itself establish cross-publisher generalization
  -> a SEPARATELY frozen cross-publisher fresh probe is required
     before any Stage-C/production advancement
```

**Not designed or run in this turn.** The cross-publisher probe is a
future, separate batch — its source-selection protocol is not
specified here, and no work toward it has started.

**Status: packet-only corrections complete, scope note recorded. No
human labels. No B2. No Stage C. No rerun of the walk/CJ-1/Stage
A/Stage B — all remain exactly as frozen.** Waiting for human-supplied
labels against `human-review-packet-v1.1.md`.

## `human-review-packet-v1.1.md` — FROZEN, SHA256 RE-CONFIRMED

```
human-review-packet-v1.1.md
SHA256: 9886afba1d1a509a64a49fa02a253017e14a8ea9865706ec0225d069b5c1eced
```

Re-hashed and confirmed unchanged since the previous record. **The
Nature-cluster scope note above (`## SCOPE NOTE — RECORDED BEFORE ANY
HUMAN LABEL`) is persisted in this document and stands as written** —
not re-derived, not restated differently, nothing added or removed
from its interpretation rule.

## `human-review-labels-v1.json` — EMPTY SKELETON CREATED, NOT POPULATED

```
automation/.probe_fixtures/cj2-fresh-batch-1/human-review-labels-v1.json
SHA256: a6e839838e5dbea49432013c7dcba3bbb46f5ca666c523aaac5ff94a714ce3a2
```

18 entries, `H01`-`H18`, every `label`/`reviewer_note` field `null`,
every `violations` array `[]` — **no label suggested or populated for
any candidate.** `_metadata` records `packet_version:
"human-review-packet-v1.1"`, `packet_sha256` (matching the hash
above), `reviewer: "Jascha"`, `reference_created_before_b2: true`,
`b2_output_seen_by_reviewer: false`, and the schema constraints the
reviewer's eventual entries must satisfy: the exact 7 allowed
`source_field` values (`additional_source_observations[0].observation`,
`additional_source_observations[1].observation`, `engine_move`,
`seed_engagement`, `interpretive_inference`, `conceptual_shift`,
`claimed_contribution`), the 3 allowed `label` values, the 2 allowed
`violation_types` values, the 6 allowed `semantic_problem_types`
values, and the explicit rule that an `undeclared_factual_dependency`
violation with no `semantic_fact_laundering` component takes
`semantic_problem_types: []`.

**Status: frozen and waiting. No B2 call. No candidate commentary. No
suggested labels of any kind.**

## `human-ai-assisted-adjudications-v1.json` — METHODOLOGY CORRECTION (2026-08-11, same day)

**Important provenance correction, before any B2 run against these
labels.** The 18 candidate judgments were produced through an
interactive, model-assisted review process — Jascha made the
judgments, but a model helped interpret candidates and formulate
decisions during the process. **This manifest is therefore explicitly
NOT an independent human reference or human ground truth.**

```
automation/.probe_fixtures/cj2-fresh-batch-1/human-ai-assisted-adjudications-v1.json
SHA256: cd6a95b0c8fac46c1f9f3d10281acf49e98d152c015fd1bf45dfc262c09324b4
```

`_metadata`: `review_mode: "human_ai_assisted"`,
`independent_human_reference: false`, `human_reviewer: "Jascha"`,
`model_assistance_used_during_review: true`,
`b2_output_seen_during_review: false`. The 18 `label`/`violations`/
`reviewer_note` entries are byte-identical to the source file placed
at `/Users/stargatesgx/Downloads/human-ai-assisted-adjudications-v1.json`
— verified programmatically before this record was written; only
`_metadata` was authored, no candidate judgment content was touched.
The prior empty skeleton, `human-review-labels-v1.json`, remains
untouched (SHA256 unchanged: `a6e839...`).

**Label distribution**: 14 `factuality_contract_violation`, 3
`ambiguous_boundary` (H01, H04, H12), 1 `clean` (H03).

`cj2-stage-b2-v1.2` itself is NOT edited, before or after this
correction.

## EXPLORATORY FRESH GENERALIZATION COMPARISON — B2 v1.2 vs. human-AI-assisted adjudication (2026-08-11, same day)

**Framing, stated up front and not revised by the result**: this is an
exploratory comparison against a human-AI-assisted reference, NOT
independent-human validation. Ran the frozen, unmodified
`cj2-stage-b2-v1.2` (same prompt, same call conditions —
`model=openrouter/claude-sonnet-4.6`, `temperature=0.0`,
`max_tokens=5000`) against the exact same 18 Stage-B-surviving
candidates, one H-ID at a time, via `cj2_freshbatch1_b2_probe.py` (new,
uncommitted, imports `B2_SYSTEM`/`_call`/`build_b2_user`/
`run_candidate_pipeline`/etc. UNMODIFIED from `cj2_b2_probe_v1_2.py` —
only the input source changed from the development set to
`cj2-fresh-batch-1`). All inputs hash-verified before the run, all 21
output files hash-verified after pull-back, scratch removed.
`cj2-stage-b2-v1.2` was NOT edited before, during, or after this run.

**Mechanical**: 18/18 `run_status=valid`. 0 `schema_invalid`, 0
`call_failed`. Verdicts: 11 `unsafe`, 7 `safe`, 0 `ambiguous`.

**Candidate-level comparison, exact mapping as specified:**

| H_ID | assisted label | B2 verdict | category |
|---|---|---|---|
| H01 | ambiguous_boundary | safe | unscored |
| H02 | factuality_contract_violation | unsafe | caught |
| H03 | **clean** | **unsafe** | **potential false-unsafe** |
| H04 | ambiguous_boundary | safe | unscored |
| H05 | factuality_contract_violation | **safe** | **potential false-safe** |
| H06 | factuality_contract_violation | unsafe | caught |
| H07 | factuality_contract_violation | unsafe | caught |
| H08 | factuality_contract_violation | **safe** | **potential false-safe** |
| H09 | factuality_contract_violation | **safe** | **potential false-safe** |
| H10 | factuality_contract_violation | unsafe | caught |
| H11 | factuality_contract_violation | unsafe | caught |
| H12 | ambiguous_boundary | unsafe | unscored |
| H13 | factuality_contract_violation | unsafe | caught |
| H14 | factuality_contract_violation | **safe** | **potential false-safe** |
| H15 | factuality_contract_violation | unsafe | caught |
| H16 | factuality_contract_violation | unsafe | caught |
| H17 | factuality_contract_violation | **safe** | **potential false-safe** |
| H18 | factuality_contract_violation | unsafe | caught |

**Totals: 9 caught, 5 potential false-safe, 1 potential false-unsafe,
3 unscored (`ambiguous_boundary`), 0 withheld, 0 caution.**

### The 5 potential false-safes share one specific, precise pattern — not five unrelated misses

Inspected each: every one of H05/H08/H09/H14/H17's assisted violation
is an **institutional/system-level motive-or-rationale attribution** —
"panels were socially obligated to keep ranking," "the cutoff encodes
an institutional assumption about the expected magnitude of
interruptions," "'policy' is load-bearing across the 3,700+ funded
projects" — and in every one of these five, B2 classified the EXACT
corresponding claim `interpretive_only`, not `factual_dependency`. Two
representative examples, B2's own extracted claims:

```
H05: "Panels were socially obligated to keep ranking even after
     their genuine discriminatory capacity had run out."
     -> role=interpretive_only, support=not_required

H09: "The sex-differentiated cutoff encodes an institutional
     assumption about the expected magnitude of female career
     interruptions -- specifically five years' worth."
     -> role=interpretive_only, support=not_required
```

`cj2-stage-b2-v1.2`'s own MOTIVATION pattern in the SUPPORT section is
worded as: *"source states an actor did something; candidate asserts
the actor did it because they intended/believed/wanted/recognized
something specific."* Every worked example in the prompt (the
queue/customer example, the interface/populations example, the bridge
example) uses an individual or a generic collective actor. **None of
`cj2-stage-b2-v1.2`'s examples cover a claim about what an
INSTITUTION, POLICY, or RULE "encodes," "assumes," or was "socially
obligated" to do** — a real, specific pattern this fresh batch surfaced
that the development set never exercised (the development set's
motivation_invention instances were all about individual/group human
actors — AI Exam/S's "students... were adapting," AI Exam/M's
"students... for whom the restoration was... disqualifying"). This is
reported as an observation, not acted on — **`cj2-stage-b2-v1.2` is
NOT edited in response to this pattern**, per instruction.

### The 1 potential false-unsafe (H03) sits inside a striking three-way inconsistency

H03, H09, and H17 are ALL the same source
(`fresh02_funders_should_look_beyond_strict_age_criteria`, engines
M/P/Z respectively) and all three engage the SAME underlying
proposition family — the program's 5-year sex-differentiated age
cutoff as encoding an institutional assumption about women's career
interruptions. The human-AI adjudication labeled H09 and H17
`factuality_contract_violation` but H03 `clean`. B2, independently,
called H09 and H17 `safe` (the false-safe pattern above) but called
H03 `unsafe` — flagging almost the identical underlying claim
("female researchers are more likely to have had career
interruptions... the 40-year cutoff... would otherwise systematically
exclude women whose career clocks and biological clocks ran
concurrently") as `factual_dependency`/`unsupported`/
`motivation_invention`+`causality_hardening`+`undeclared_factual_dependency`.

**This is exactly the kind of concrete case the pre-registered
disagreement-handling rule exists for.** Recorded per that rule:

```
H03: HUMAN clean + B2 unsafe -> FORMAL potential false-unsafe (this
     is an exploratory comparison, not the frozen development-set
     acceptance test, so "formal" here means "as scored under this
     comparison's stated categories," not a pass/fail gate)

Substantive note, not a resolution: H03/H09/H17 sharing one source and
one proposition family, with the assisted labels and B2's own verdicts
BOTH disagreeing with each other across the three (assisted: clean/
violation/violation; B2: unsafe/safe/safe) suggests the underlying
proposition family itself sits near a genuine boundary -- exactly the
kind of case `ambiguous_boundary` exists for, that neither this
adjudication process nor B2 resolved consistently across three
independent engine readings of the same institutional-motive claim.
Not adjudicated further in this pass -- flagged for whoever next
reviews this batch, per instruction that this comparison stops before
Stage C.
```

### What this comparison does and does not establish

Per the framing stated up front: this shows B2 v1.2's behavior against
an exploratory, human-AI-assisted reference on 6 genuinely fresh
(mechanically selected, Nature-cluster, per the scope note above)
sources — it is informative, especially the specific
institutional-motive pattern behind all 5 false-safes, but it is
**not** independent-human validation, and (per the earlier scope note)
it is **not** cross-publisher generalization evidence either way.
`cj2-stage-b2-v1.2` is unmodified by this result.

**Status: comparison complete and reported. `cj2-stage-b2-v1.2` NOT
tuned. All original outputs (development-set B2 runs, both fresh-batch
walks, both packet versions, the adjudication file) preserved
unchanged. Stopping here, before Stage C, per instruction.**

## CORRECTION: THE "ONE INSTITUTIONAL-MOTIVE PATTERN" INTERPRETATION IS SUPERSEDED (2026-08-12)

**The two paragraphs above under "The 5 potential false-safes share
one specific, precise pattern" and "The 1 potential false-unsafe (H03)
sits inside a striking three-way inconsistency" are preserved verbatim
above, unedited — they are not accurate, and are corrected here rather
than silently rewritten.**

A closer, per-case re-audit (below) found the original diagnosis too
narrow in one direction and too generous to the reference in another:

1. **Not all five false-safes are institutional-motive attribution.**
   H08's miss is a **modality/certainty-hardening** case — the source
   hedges ("might not have existed," "often could not [be
   distinguished]"); the candidate's claim ("resolution is a property
   of the underlying signal," stated with "in fact") removes the hedge
   entirely and asserts settled certainty. **H14's miss is a
   scope/content generalization** — the source establishes only that
   the word "policy" appears in the *title or abstract* of 3,700+
   projects; the candidate generalizes that textual-occurrence fact
   into a claim that the word is *substantively load-bearing* across
   the whole population and that "consistent application would
   retroactively delegitimize" it — a claim about content/function the
   textual fact does not establish. Only H05, H09, and H17 are
   genuinely institutional-rationale/obligation-attribution cases.
   **The broader, corrected failure class**:

   ```
   CONCEPTUAL-SUBJECT FACTUALITY SHIELDING

   A truth-apt proposition about an institution, system, rule, policy,
   format, classification, environment, or other abstract/systemic
   subject is treated as interpretive_only even though its truth
   depends on an unstated factual premise the frozen source does not
   establish.

   Observed subtypes in this batch (diagnostic labels only -- NOT
   added to cj2-stage-b2-v1.2's frozen problems enum):
     - institutional_rationale_or_obligation_attribution (H05, H09, H17)
     - modality_or_certainty_hardening (H08)
     - scope_or_population_generalization (H14)
   ```

   A fix aimed only at "institutions can have motives too" would have
   left H08 and H14 uncaught — the underlying mechanism is broader:
   B2 sometimes grants a proposition `interpretive_only` status because
   of *how the subject is phrased* (conceptually, systemically) rather
   than *what the proposition actually claims*, regardless of which of
   the seven strengthening patterns it belongs to.

2. **H03/H09/H17 is NOT evidence of a "probable genuine boundary" —
   re-audited directly against the frozen source and superseded.** The
   `fresh02` source snapshot is an extremely thin paywall stub: exactly
   one substantive sentence ("male applicants must be under 35...
   female applicants under 40"), nothing else. On independent re-read,
   **B2's `unsafe` verdict on H03 is correct** — its three flagged
   claims (an unsupported career-interruption population claim, an
   unsupported "operational patch" motive claim, an unsupported "works
   adequately" claim) are exactly as unsupported as the claims H09 and
   H17 were correctly flagged for, on the identical source. **The
   simpler, corrected explanation: `human-ai-assisted-adjudications-v1.json`
   itself is inconsistent across H03/H09/H17**, not evidence of a
   genuine interpretive/factual boundary. Since that reference was
   never independent ground truth in the first place
   (`independent_human_reference: false`), this inconsistency is
   unsurprising rather than alarming — but it means H03 should not have
   been cited as boundary evidence.

**Post-run diagnostic adjudication created, covering exactly the 6
disagreements** (H03, H05, H08, H09, H14, H17) — each proposition
re-audited directly against its frozen `source_snapshot`, independent
of both B2's and the assisted reference's own framing:

```
automation/.probe_fixtures/cj2-fresh-batch-1/post-run-disagreement-adjudications-v1.json
SHA256: d6fcb1d5e49dd56a0e84dc5597831a7b4102b255e37c0f359524938c39320d11
```

`_metadata`: `review_mode: "post_run_model_assisted_diagnostic"`,
`independent_reference: false`, `b2_output_visible: true` — this is
explicitly NOT another independent-validation attempt; the point of
this pass is transparent, source-grounded diagnosis, not a new
ground-truth claim. `human-ai-assisted-adjudications-v1.json` is
**not edited** — re-verified byte-identical, SHA256 unchanged
(`cd6a95b0...`).

**Result: 5 confirmed B2 misses (7 individual claim instances across
H05/H08/H09/H14/H17), 1 claim re-classified `boundary_ambiguous` on
re-audit (H08's `c5`, a genuinely closer call than `c9`), and H03
reclassified from "possible boundary" to "assisted-reference
inconsistency, B2 was right."** Full per-claim rationale (each
grounded in the actual frozen source text, quoted where relevant) is
in the adjudication file itself.

**Status: diagnosis corrected and reported. `cj2-stage-b2-v1.2` is
STILL NOT edited — this remains diagnostic only, per instruction. No
`cj2-stage-b2-v1.3` designed. No Stage C. No further model calls beyond
this diagnostic re-read.**

## LATEST SUBSTANTIVE INTERPRETATION, FORMAL COUNTS PRESERVED AS PRE-ADJUDICATION (2026-08-12)

**`CONCEPTUAL-SUBJECT FACTUALITY SHIELDING` is a PROVISIONAL observed
failure class** — three subtypes seen once each (institutional
rationale/obligation attribution x3, modality/certainty hardening x1,
scope/population generalization x1) on 6 sources from one publisher.
Not a complete or validated taxonomy; treated as such throughout the
`cj2-stage-b2-v1.3` design below.

**The original exploratory comparison's formal counts are preserved
exactly as computed — not erased, not restated — and are now labeled
explicitly as PRE-ADJUDICATION:**

```
PRE-ADJUDICATION (## EXPLORATORY FRESH GENERALIZATION COMPARISON, above):
  9 caught, 5 potential false-safe, 1 potential false-unsafe, 3 unscored
```

**The post-run diagnostic adjudication is the latest substantive
interpretation of those same 18 candidates:**

```
5 confirmed B2 misses (7 individual claim instances: H05/c9, H05/c11,
  H08/c9, H09/c5, H14/c6, H14/c7, H17/c4)
0 confirmed B2 false-unsafe among the six disagreement cases
  (H03's unsafe verdict is independently confirmed CORRECT on re-audit
  -- not a false-unsafe at all)
H03 = assisted-reference inconsistency, not a B2 error and not a
  genuine interpretive/factual boundary
H08 contains 1 proposition-level boundary_ambiguous claim on re-audit
  (c5 -- genuinely closer than c9, which is an unambiguous miss)
```

Both records stand, side by side, per the same formal-vs-substantive
discipline already used once for the development set's De Hooch/P case
— the pre-adjudication table is not deleted or reinterpreted in place;
the adjudication is additional, later evidence layered on top of it.

## PROMPT FROZEN: cj2-stage-b2-v1.3 (2026-08-12) — STATUS: DESIGN CANDIDATE / NOT EXECUTED

**Prompt-only correction, confirmed by diff: 21 lines inserted, 0 lines
removed or changed, at exactly one point in the file (after the
`ATOMIC CLAIM DECOMPOSITION` section, before `HEDGES DO NOT IMMUNIZE A
CLAIM`).** `B2_MODEL_OUTPUT_V1` schema, the `problems` enum, the
deterministic validators (`cj2_b2_probe.py`/`cj2_b2_probe_v1_2.py`'s
field-coverage/claim-structure/auditor-evidence/effective-verdict
logic), the resolver, Stage A, Stage B, and Stage C are all
byte-identical/untouched — this correction lives entirely inside the
model-facing prompt text. User-input template unchanged from v1.1/v1.2
(byte-identical, no template edit needed).

**The core correction — role determination by propositional
dependency, not subject type**: a new section,
`ROLE MUST BE DETERMINED BY PROPOSITIONAL DEPENDENCY, NOT BY SUBJECT
TYPE OR CONCEPTUAL STYLE`, states directly that an institution, policy,
rule, system, format, environment, scale, classification, proxy,
architecture, or process can be the subject of a genuine
`factual_dependency`, and gives the test: *"what must actually be true
in the world for this proposition to hold?"* — if the proposition
depends on a claim about what a system actually does, assumes,
requires, causes, encodes, generalizes across, was designed to
accomplish, or operationally depends on, it must be audited as
factual regardless of how abstractly it is phrased.

**CONCRETE RESTATEMENT TEST**: paraphrase conceptual/systemic wording
into the nearest concrete world-claim, without strengthening it; if
that restatement needs empirical support, the original is
`factual_dependency` or `boundary_ambiguous`, never `interpretive_only`.
Four generic patterns cover the observed subtypes without copying any
fresh-batch candidate verbatim — confirmed absent from the prompt by
preflight (below): *"the policy encodes an assumption that X,"* *"the
system obligates actors to do X,"* *"the measurement contains no
remaining signal,"* *"a feature is substantively characteristic across
a population."*

**Anti-overcorrection rule, added in the same pass, not as an
afterthought**: `DO NOT OVERCORRECT -- A METAPHOR IS STILL A METAPHOR`
— a metaphor, category shift, evaluative framing, or interpretive lens
stays `interpretive_only` whenever its argumentative force does NOT
depend on an additional empirical proposition being true. Declarative
grammar alone does not make a claim factual. Explicitly disclaims
scope creep: *"this section sharpens which claims get audited as
factual, it does not expand the definition of factual_dependency
beyond what the THREE ROLES section above already says."*

Mixed-content decomposition (`ATOMIC CLAIM DECOMPOSITION`, "multiple
claim objects may share the same source_field") is unchanged from
v1.2/v1.1 — a single sentence may still yield both `interpretive_only`
and `factual_dependency` claims side by side.

```
cj2-stage-b2-v1.3
SHA256: 8a5b279e33ae2de801c6914e0143f28dc3afb0a1cbc7e157ac3e427e64bfe177
```

**Static preflight — 109/109 checks PASS**: every carried-forward v1.1/
v1.2 check (banned terms, verdict/run_status absence, resisting_detail
context-only, bridge examples, atomic decomposition, copy discipline,
declared_refs restrictions, the unchanged 8-value problems enum, all
16 v1.2 section headers still present, all 4 JSON examples still parse
with no verdict/run_status keys, no held-out claim) re-verified against
v1.3 and still passing, PLUS new checks: the new section header and
core statements present; all four generic patterns present verbatim;
the anti-overcorrection section and its scope-disclaimer present; AND
— new for this round — **explicit absence of fresh-batch-1 fixture
wording** (`NSFC`, `SNSF`, `NIH`, `phosphine`, `socially obligated to
keep ranking`, `splitting hairs that might not have existed`, `3,700`,
and 8 other fresh-batch-specific terms, all confirmed absent), mirroring
the same discipline already applied to the development set's fixture
wording.

**Status: `cj2-stage-b2-v1.3` is a FROZEN design candidate,
static-preflight-clean (109/109). No API calls made. No schema, enum,
validator, resolver, Stage A, Stage B, or Stage C changes.**

## REGRESSION ACCEPTANCE CRITERIA FOR cj2-stage-b2-v1.3 — PREREGISTERED BEFORE ANY RUN

The evaluation suite for v1.3 is explicitly **development, not
held-out, evidence**: the original 12 development-set candidates AND
the 18 `cj2-fresh-batch-1` candidates are both now development/
regression material, since v1.3 was designed directly from failures
found in the fresh batch. Neither set is held-out evidence for v1.3 —
that status ended the moment v1.3 was designed from their failures.

```
1. All 5 confirmed v1.2 misses (H05/c9, H05/c11, H08/c9, H09/c5,
   H14/c6, H14/c7, H17/c4 -- 7 claim instances across 5 candidates)
   must no longer resolve safe for the SAME unsupported factual
   premise. Re-extraction under a different claim_id is fine; the
   underlying proposition must be caught as factual_dependency/
   unsupported (or boundary_ambiguous, per H08/c5's own re-audit),
   not interpretive_only.

2. H03's unsupported rationale claims must remain caught (unsafe) --
   v1.3 must not accidentally soften a correct v1.2 call while fixing
   the five misses.

3. Previously clean/interpretive claims must NOT show broad migration
   into factual_dependency. **Operationalized now, before any v1.3
   output exists — clarification of this criterion, not a response to
   results:**

   ```
   Compute, across the full 30-candidate corpus (12 development + 18
   fresh-batch, v1.2 vs v1.3, same claim population):

   (a) AGGREGATE DISTRIBUTION CAP: the aggregate interpretive_only
       percentage-point drop (v1.2 -> v1.3) must be <=15pp, AND the
       aggregate factual_dependency percentage-point rise must be
       <=15pp. (For reference: the already-accepted v1.1->v1.2 shift
       on the development set was ~6.5pp/~8.3pp; the hypothesized
       failure mode this guards against was ~35+pp in either
       direction.)

   (b) FLIP-RATE CAP: of all claims classified interpretive_only under
       v1.2, the count that flip to factual_dependency OR
       boundary_ambiguous under v1.3 (matched by claim content, not
       claim_id, since re-extraction can renumber claims) must be
       <=20% of v1.2's total interpretive_only claim count across the
       30 candidates.

   PASS only if BOTH (a) and (b) hold. FAIL (blanket
   overcorrection) if either is violated, regardless of how the
   individual regression targets (criteria 1/2 above) come out --
   fixing the 5 confirmed misses does not excuse a global collapse.
   ```

   Report role-distribution changes for both the 12-candidate
   development set and the 18-candidate fresh batch, separately and
   combined.

4. Report any NEW unsafe verdicts on candidates that were safe under
   v1.2 -- every one must be inspected individually (same discipline
   as the v1.1->v1.2 clean-candidate-unsafe case), not assumed correct
   merely because v1.3 is "stricter."

5. No tuning after seeing individual regression outputs without
   creating a new, explicitly named version. Reading v1.3's results
   and immediately hand-editing the same file is not permitted --
   any further correction is v1.4, frozen and preflighted the same way
   v1.1/v1.2/v1.3 were.
```

**Not executed in this pass.** No new API calls have been made against
`cj2-stage-b2-v1.3`.

## NEXT EVALUATION BATCH — CROSS-PUBLISHER SAMPLING PROTOCOL (DESIGN ONLY, NOT EXECUTED)

**Purpose stated precisely, so this is never misread later**: the
cross-publisher constraint below exists to correct the feed-order
publisher clustering actually observed in `cj2-fresh-batch-1` (all 6
accepted sources were `nature.com`, traced to `QUALITY_FEEDS`' own
feed-list order, not a discretionary choice) — **not because any
publisher is preferred or disfavored.** Nothing about `nature.com`
specifically is being corrected for; the mechanism (one feed
dominating a stream prefix) could have produced any single publisher.

```
1. Same frozen-stream discipline as cj2-fresh-batch-1: pull the raw
   QUALITY_FEEDS return via fetch_all_feeds() (unmodified), freeze the
   COMPLETE unfiltered result to a new blind-stream-v3.json BEFORE any
   content-shape filtering, hash it immediately.
2. Walk the frozen stream in deterministic order (stream_index, same
   as before). Same six allowed skip reasons as cj2-fresh-batch-1
   (prior_fixture, confirmed_already_published, shape_exclusion,
   capture_duplicate, fetch_failed, cj1_no) PLUS one new allowed
   reason: publisher_quota_reached.
3. **`publisher_key` frozen now, before any run — single deterministic
   field, no URL/domain parsing needed:**

   ```
   publisher_key := row["source_name"]

   -- the exact string news_fetcher.py's fetch_feed() copies from
   QUALITY_FEEDS' own "name" field for that feed (e.g. "Nature",
   "Wired", "Hacker News"). Already present, verbatim, in every row of
   the frozen blind-stream JSON -- confirmed by inspection
   (cj2-fresh-batch-1's own blind-stream-v2.json rows all carry
   source_name). No normalization needed: QUALITY_FEEDS' name values
   are a small, fixed, curated set of literal strings, one per feed,
   compared by exact string equality. Preferred over parsing the
   registrable domain from the URL because it targets the actual
   clustering mechanism directly (which FEED an item came from) rather
   than a proxy that could vary even within one feed (redirects,
   syndication, multiple subdomains) or coincide across genuinely
   different editorial feeds that happen to share infrastructure.
   ```

   NEW constraint: maximum 1 accepted CJ-1 PASS source per
   `publisher_key`. A row whose `publisher_key` already has an
   accepted source is skipped with `skip_reason=publisher_quota_reached`,
   regardless of its own CJ-1 result — CJ-1 is not even run on it,
   since the publisher slot is already filled; this keeps the rule
   purely mechanical and pre-decision, not a post-hoc discard of a
   real PASS.
4. Continue until exactly 6 accepted CJ-1 PASS sources, from 6
   DISTINCT publishers/domains.
5. Legacy news_seeds state (disability_angle, angle_checked, used,
   presence in news_seeds) remains NON-EXCLUSIONARY, exactly as
   already frozen for cj2-fresh-batch-1 -- this correction is about
   publisher diversity only, it does not reopen or weaken the
   disability-routing independence already established.
6. Everything downstream (canonical seed construction, Stage A, Stage
   B, the human-review-packet construction and blinding corrections,
   the factuality-contract-violation/clean/ambiguous_boundary label
   space, the evaluation semantics and disagreement-handling rule) is
   unchanged from the cj2-fresh-batch-1 protocol -- only the source-
   selection walk gains the publisher-quota rule.
```

**Not executed. No sources selected. No API calls of any kind for this
protocol.** This is a design-only pre-registration, to be executed only
after `cj2-stage-b2-v1.3`'s regression run (against the existing 12+18
development/regression material) is itself complete and reported.

**Status: stopping here, per instruction. No v1.3 execution. No new
source collection. No Stage C.**

## cj2-stage-b2-v1.3 REGRESSION RUN — COMPLETE, RESULT: PARTIAL PASS (2026-08-12)

Both preregistration gaps closed before this run, as clarifications of
the existing criteria, not in response to results: (a) the
role-migration criterion now has an exact, mechanically decidable
dual test — an aggregate percentage-point cap (≤15pp on both
`interpretive_only` drop and `factual_dependency` rise, combined
30-candidate corpus) AND a flip-rate cap (≤20% of v1.2's
`interpretive_only` claims flipping to `factual_dependency`/
`boundary_ambiguous`); (b) the cross-publisher protocol's
`publisher_key` is frozen as `row["source_name"]` — the exact string
`fetch_feed()` copies from `QUALITY_FEEDS`, already present verbatim in
every frozen-stream row, no domain-parsing needed.

Executed `cj2-stage-b2-v1.3` against the exact 30-candidate corpus (12
development + 18 fresh-batch-1), same model/temperature/call
conditions/input construction/validators as every prior B2 run, only
the v1.3 prompt swapped. v1.2 outputs preserved unchanged at their
original paths; v1.3 outputs written to new `b2_v1_3/` directories
alongside them. All inputs hash-verified before the run; all outputs
hash-verified after pull-back; scratch removed.

```
automation/.probe_fixtures/cj2-b2-v1.3-regression/b2-v1.3-regression-comparison.json
SHA256: f9d7f093676d26fb6bd6e1d2c4e5ed758e309687e85aa9f54eb0393f3f90316b

automation/.probe_fixtures/cj2-b2-v1.3-regression/b2-v1.3-regression-report.md
SHA256: 75f443c7e7772e145fabc5f3fbca2e858c832ada09919ad04fca0097f90952a6
```

**Mechanical: 30/30 run. 29 `valid`, 1 `schema_invalid` (H09 — see
below). 0 `call_failed`.**

**6 of 30 candidates changed verdict** — every one individually
inspected at the claim level, not accepted on the verdict alone:

```
05_dutch_painting_soldier/M (dev)  safe -> unsafe   [NOT a target -- new finding]
05_dutch_painting_soldier/Z (dev)  safe -> unsafe   [NOT a target -- new finding]
H05 (fresh)                        safe -> unsafe   [target -- confirmed fixed]
H09 (fresh)                        safe -> not_computed (schema_invalid) [target -- claim fixed, run blocked]
H14 (fresh)                        safe -> unsafe   [target -- confirmed fixed]
H16 (fresh)                        unsafe -> safe   [NOT a target -- new finding]
```

**Criterion 1 (fix the 5 confirmed misses): PARTIAL, not a clean
sweep.** Each target's exact underlying proposition re-checked at the
claim level, per instruction not to call a candidate "fixed" merely
because its verdict changed:

- **H05 — CONFIRMED FIXED.** "Panels were socially obligated to keep
  ranking..." (reworded slightly by re-extraction) is now
  `factual_dependency`/`unsupported`.
- **H08 — STILL MISSED.** The exact same claim text ("...resolution is
  a property of the underlying signal") remains `interpretive_only`.
  v1.3's new section did not fix the one modality/certainty-hardening
  case in this run.
- **H09 — claim-level fixed, run blocked by an unrelated error.** The
  exact target claim is now correctly `factual_dependency`/
  `unsupported`/`motivation_invention`. But the overall run is
  `schema_invalid` because a DIFFERENT claim (c7, "women's careers are
  actually interrupted more...") violates the frozen invariant
  "`support=unsupported` requires ≥1 semantic problem value" (it only
  had `undeclared_factual_dependency`) — a pure model compliance slip
  on an unrelated claim, unrelated to the v1.3 correction itself. No
  computed verdict for this candidate this run — correctly
  `not_computed`, per the round-4 architecture, not coerced into
  `unsafe` or `safe`.
- **H14 — CONFIRMED FIXED.** Exact claim-text match, now
  `factual_dependency`/`unsupported`.
- **H17 — STILL MISSED.** Same proposition (minor rewording of the
  parenthetical example), still `interpretive_only`.

**Summary: 2/5 confirmed fixed, 1/5 fixed at the claim level but
blocked by an unrelated schema error, 2/5 still missed.** The
correction generalized inconsistently even within its own targeted
subtype (institutional-rationale-attribution: H05/H09 fixed, H17 not)
and did not touch the modality/certainty-hardening case (H08) at all.

**Criterion 2 (H03 must remain caught): PASS.** `unsafe` verdict
retained; the same target claims (career-interruption population
claim, "works adequately" claim) remain independently flagged
`unsupported`.

**Criterion 3 (role migration): PASS on both operationalized
sub-checks.**

```
3a (aggregate cap, combined 30-candidate corpus, cap=15pp):
   interpretive_only: 56.6% (v1.2) -> 57.7% (v1.3)   -- ROSE 1.1pp
                                                          (wrong direction
                                                          for an overcorrection)
   factual_dependency: 43.0% (v1.2) -> 42.3% (v1.3)  -- FELL 0.6pp
   PASS, by a wide margin.

3b (flip-rate cap, cap=20%):
   233 total v1.2 interpretive_only claims (dev 92 + fresh 141)
   4 flipped to factual_dependency/boundary_ambiguous (exact-text match,
   a lower bound -- reworded claims like H05/H17's targets undercounted)
   flip rate = 1.72%
   PASS, by a wide margin.
```

**No blanket overcorrection occurred.** The cost of this correction is
inconsistent coverage (criterion 1), not a wholesale collapse of
interpretation into fact-checking — the two guardrails built
specifically to catch that failure mode both came back clearly clean.

**Criterion 4 (new unsafe verdicts, individually inspected): done, not
assumed correct.**

- **`05_dutch_painting_soldier`/M (dev)**: two claims assert the
  "modesty" motive for the painting's alteration as settled fact. The
  source frames modesty as only ONE OF THREE speculative possibilities
  ("researchers speculate"). **Same speculative-motive-hardening
  pattern already found and adjudicated** for this exact source's
  Engine P under v1.2 (`likely_human_annotation_defect` — the source
  itself hedges). Assessment: a genuine, well-grounded catch, not an
  overcorrection.
- **`05_dutch_painting_soldier`/Z (dev)**: two claims assert that a
  visual contrast IS "de Hooch's moral signal" / that his moralism
  "functioned through contrast and implication" as deliberate intent.
  Source establishes the visual fact, not the artist's own intent.
  Assessment: defensible under the new rule, but genuinely closer to
  the anti-overcorrection boundary than the M case — attributing a
  "moral signal" to a painting sits close to ordinary art-critical
  language. Flagged as the more debatable of the two, not resolved
  either way.

**A new safe verdict, also individually inspected, not assumed a
regression: H16 (fresh, unsafe -> safe).** The disputed claim is
IDENTICAL text in both runs. v1.2 cited only the "3,700 projects"
excerpt (correctly judged insufficient). v1.3 additionally cited a
second, genuinely more direct excerpt — "...applications that had
been previously approved by peer reviewers and agency employees" —
which does state these specific flagged applications were previously
approved. This is a genuine additional-evidence finding (a better
citation located this run), unrelated to the v1.3 prompt correction
itself, and independently judged MORE correct than v1.2's own miss of
this citation — not a new weakness introduced by v1.3.

**Criterion 5 (no further tuning): PASS.** No edits to
`cj2-stage-b2-v1.3` after seeing these results.

**Overall regression status: PARTIAL PASS.** Role-migration guardrails
(3a/3b) and the H03-retention guardrail (2) all pass cleanly — no
blanket overcorrection. The primary target (criterion 1) is genuinely
mixed: 2/5 confirmed fixed, 1/5 fixed-but-blocked, 2/5 still missed.
Two new, non-targeted findings on the development set (one strong, one
debatable) plus one new safe finding on the fresh batch that inspection
shows is a genuine improvement, not a miss.

**Status: `cj2-stage-b2-v1.3` NOT tuned further. No `cj2-stage-b2-v1.4`
created. No cross-publisher batch collected. No Stage C. Stopping
here, per instruction.**

## STATUS CORRECTION: THE PREREGISTERED GATE IS FAIL, NOT "PARTIAL PASS" (2026-08-12)

**The "Overall regression status: PARTIAL PASS" line above, and
criterion 1's "PARTIAL" result, are corrected here — preserved above,
not rewritten.** The preregistered primary criterion required ALL FIVE
confirmed v1.2 misses to be repaired. That did not happen. A gate with
an explicit, binary preregistered requirement does not become a
"partial pass" because some sub-parts succeeded — it is a pass or a
fail against what was actually preregistered.

```
cj2-stage-b2-v1.3 REGRESSION STATUS: FAIL -- PARTIAL IMPROVEMENT

Criterion 1: FAIL
  H05 fixed
  H14 fixed
  H09 target mechanism appears repaired but run schema_invalid,
      therefore cannot count as a successful candidate-level repair
  H08 still missed
  H17 still missed

Criterion 2: PASS
Criterion 3: PASS
Criterion 4: diagnostic findings as already reported above
```

"Partial improvement" is retained as accurate DESCRIPTIVE language for
what actually happened (2 clean fixes, 1 fixed-but-blocked, 2 misses,
plus the role-migration guardrails holding) — it is not a substitute
verdict for the preregistered gate itself, which is FAIL.

**Direct consequence: `cj2-stage-b2-v1.3` is NOT eligible for the
cross-publisher fresh-batch evaluation.** That protocol was designed
to run only after a v1.3 (or later) regression run actually passed its
preregistered gate — it has not. `cj2-stage-b2-v1.3` remains
unmodified; no `v1.4` designed in this pass either.

## TARGETED v1.3 FAILURE-MECHANISM DIAGNOSTIC (2026-08-12)

Post-run diagnostic adjudication, not independent validation — same
discipline as the earlier `post-run-disagreement-adjudications-v1.json`
pass. Covers exactly H08, H09, H17, `05_dutch_painting_soldier`/Z, plus
H05/H14 as successful controls.

```
automation/.probe_fixtures/cj2-b2-v1.3-regression/b2-v1.3-failure-mechanism-diagnostic-v1.json
SHA256: 28dcaef53e65679cb0c6ec6ac77c5ba5cdd23f7664a79bed2d2721368363fc8c
```

### A. H08 — role-classification failure, NOT an atomic-decomposition failure

The target proposition ("The scale's resolution was treated as
adjustable by the raters, when in fact resolution is a property of the
underlying signal") is extracted as its OWN atomic claim (`c9`) in
BOTH v1.2 and v1.3 — byte-identical text, never split, never merged
into a larger claim. This directly rules out
`atomic_decomposition_coverage_failure`: nothing was lost in
decomposition, because there was no decomposition to lose it in — the
claim was already atomic and already isolated.

**v1.3's own `why` for `c9`**: *"This is a conceptual claim about the
nature of measurement resolution — asserting that resolution is a
property of the signal, not of the scale. This is a
theoretical/interpretive reframing of the established facts..."* — the
reasoning never invokes the CONCRETE RESTATEMENT TEST at all, despite
this proposition being an almost word-for-word match for that section's
OWN generic worked example ("the measurement contains no remaining
signal"). The new rule did not engage with this claim — it was
bypassed, not applied-and-passed.

**Diagnosis: `role_classification_failure`.** The auditor reasoned in
the OLD "conceptual lens" register throughout and never triggered the
new test, even on a claim that matches the new section's own example
almost exactly. This means the new section's presence in the prompt is
not sufficient to guarantee it is invoked on matching content — pattern
similarity to a worked example does not reliably trigger the rule.

### B. H09 vs. H17 — controlled contrast, same source

| | H09 (caught) | H17 (missed) |
|---|---|---|
| Claim | "...encodes an institutional assumption about the expected magnitude of female career interruptions — specifically five years' worth." | "...reveal[s] that the system is measuring career stage adjusted for an assumed sex-linked career disruption pattern (e.g., childbearing)." |
| v1.3 role | `factual_dependency` | `interpretive_only` |
| v1.3's own reasoning | "...a claim about institutional intent and design rationale... which the source never states... infers a specific institutional belief from the bare numerical fact." | "The parenthetical '(e.g., childbearing)' is offered as an illustrative example... not as a factual assertion... applies a conceptual lens... without asserting that any specific institutional motive or mechanism was actually documented." |

**The smallest distinction, stated precisely, not as "one triggered
the prompt":** H09's own wording is a flat, unhedged assertion tied to
an exact, quantified number that mirrors the source's own number
("specifically five years' worth" ↔ the source's real 35/40 age gap).
H17's own wording embeds a self-qualifying hedge inside the claim
itself (**"an ASSUMED... pattern"**) plus an exemplifying aside
(**"e.g., childbearing"**) — and v1.3's own reasoning explicitly treats
that internal hedge as sufficient to exempt the whole proposition from
factual scrutiny.

Categorized against the offered list: primarily **`candidate context`**
(the candidate's own self-qualifying wording, not something B2 added)
and secondarily **`claim scope`** (H09 is a narrow, concretely
quantified claim; H17 is a broader claim about "a pattern," softened by
an illustrative example rather than a specific documented number). Not
`atomic decomposition` (both atomic), not `evidence declaration` (both
declare `cj1:a1` identically), not `explicit causal language` (neither
is a causal claim — both are motive/rationale claims), not the
`anti-overcorrection rule` (v1.3's own reasoning never cites it).

**This is a genuine finding, not the intended one**: the pre-existing
`HEDGES DO NOT IMMUNIZE A CLAIM` section (unchanged since v1.1, meant
to prevent exactly this — a hedge exempting an underlying world-claim)
did not override the new section's effect here. H17's own "assumed"/
"e.g." hedging succeeded in exempting the claim from audit despite that
older rule's explicit instruction to look underneath a hedge. The rule
v1.3 is actually applying looks closer to "if the candidate's own
wording already flags something as illustrative or assumed, treat the
whole claim as interpretive" than to "always ask what must be true in
the world regardless of hedging" — the opposite of what both the old
HEDGES section and the new ROLE MUST BE DETERMINED section say to do.

### C. H09 schema_invalid — isolated to a different claim, cause uncertain

The violated invariant, precisely: claim `c7` ("Women's careers are
actually interrupted more than men's careers — this is a real social
pattern") has `support=unsupported` but `problems=['undeclared_factual_dependency']`
only — satisfying the `declaration=undeclared` requirement but missing
the SEPARATE, independent requirement that `support=unsupported`
requires at least one semantic problem value (e.g.
`population_relation_hardening`, `motivation_invention`). `field_coverage_validation`
was `valid=true` — this is not a coverage-manifest issue. `c7`'s
`role`/`support`/`declaration` values are all individually legal enum
members — this is not an illegal-enum-value issue. No duplicate or
missing field. **Classification: `malformed claim object`** — a
cross-field structural invariant violated on an otherwise well-formed
object, on a claim UNRELATED to the target proposition (`c5`, which is
itself correctly formed).

**Is this related to the v1.3 prompt delta, or an isolated model-output
failure? UNCERTAIN — the evidence cannot distinguish the two.** The
same candidate ran cleanly (schema-valid) under v1.2; this specific
invariant is unchanged since v1.1. A longer, more complex prompt could
plausibly increase compliance-slip risk on an unrelated field as a
generic mechanism, but this is a single occurrence (1/30 runs), with no
controlled repeat to separate "v1.3's added length/complexity" from
ordinary temperature-0 API stochasticity (already documented elsewhere
in this project's own history, e.g. Stage C's inconsistent JSON-only
compliance at temperature 0.0). Not re-run, per instruction — the
frozen result stands, unexplained rather than mis-explained.

### D. De Hooch/Z — anti-overcorrection boundary, audited against the actual candidate wording

**The candidate's actual original wording** (Stage A `interpretive_inference`,
verbatim): *"De Hooch's moralism functioned through contrast and
implication: the woman drinking the pass-glass while the two men
abstain is the moral signal, not mere depiction of drinking."* — a flat,
unhedged, declarative assertion. NOT "can be read as a moral signal" —
the candidate asserts, without qualification, that this IS the moral
signal and that de Hooch's moralism actually FUNCTIONED this way.

**What empirical fact would have to be true for this to hold**: that
de Hooch, as a historical fact, actually used this contrast-and-
implication device AS HIS DELIBERATE ARTISTIC MECHANISM — not merely
that a modern viewer CAN read the composition this way. The canonical
evidence supports only the compositional fact (woman drinks, men
don't) and a curator's characterization that this makes the content
"much more obvious" — neither establishes de Hooch's own historical
intent or that his "moralism functioned through" this device as a
matter of settled art-historical fact.

**Role determination: `factual_dependency`, `support=unsupported`.**
Not `boundary_ambiguous` — unlike some other cases in this project's
history, there is no genuine difficulty here distinguishing
interpretation from a world-claim; the sentence flatly asserts a
historical mechanism-of-intent fact the source does not establish.
**Flagged, not resolved**: attributing a "design mechanism" to an
individual historical artist sits at a genuine edge of the new
section's stated scope (institution/policy/rule/system/format/
environment/scale/classification/proxy/architecture/process — an
individual creative "process" is the closest listed category, but the
section's own worked examples are all institutional/systemic, not
individual-authorial). Not a clear error either way — recorded as a
scope question for whenever this prompt is next revised, not decided
now.

### E. Successful controls — H05 and H14

Both successful fixes match the new section's OWN generic worked
examples closely: H05's target ("Panels were socially obligated to
keep ranking...") is close to the "the system obligates actors to do
X" example; H14's target ("'policy' is not decorative but load-bearing
across [the whole 3,700+ population]") is close to the "a feature is
substantively characteristic across a population" example. Both are
flat, unhedged assertions in the candidate's own original wording —
no internal self-qualifier like H17's "assumed"/"e.g." Both now
correctly `factual_dependency`/`unsupported`, with the specific
semantic-problem tag matching the pattern (`motivation_invention`,
`other`).

**The important negative finding, stated precisely: matching a worked
example is not sufficient for the rule to fire.** H08's target ALSO
matches a worked example (the "measurement contains no remaining
signal" pattern) nearly word-for-word, yet was not caught. Something
beyond example-similarity — plausibly the presence or absence of an
internal self-qualifying hedge in the candidate's own wording — is
governing whether the new section actually engages.

### Summary table

| case | v1.2 failure mechanism | v1.3 behavior | remaining mechanism |
|---|---|---|---|
| H05 | `interpretive_only` despite an institutional-obligation claim | now `factual_dependency`/`unsupported`/`motivation_invention` | none — fixed |
| H08 | `interpretive_only` despite a modality-hardened measurement claim | UNCHANGED — exact same text, still `interpretive_only`; new test never engaged despite near-exact match to its own worked example | `role_classification_failure` — rule bypassed, not failed-on-application |
| H09 | `interpretive_only` despite an institutional-rationale claim | target claim (`c5`) now correctly `factual_dependency`/`unsupported`/`motivation_invention` — BUT an unrelated claim (`c7`) violates a schema invariant, so the whole run is `schema_invalid` | claim-level fixed; run-level blocked by an unrelated, cause-uncertain compliance slip |
| H14 | `interpretive_only` despite a scope/population-generalization claim | now `factual_dependency`/`unsupported`/`other` | none — fixed |
| H17 | `interpretive_only` despite an institutional-rationale claim (same source as H09) | UNCHANGED — still `interpretive_only`; auditor's own reasoning treats the candidate's internal "assumed"/"e.g." hedge as exempting the claim | `role_classification_failure` — pre-existing HEDGES rule did not override the new section's effect here |
| `05_dutch_painting_soldier`/Z | (not one of the 5 original misses — was `safe` under v1.2) | NEW: two design-intent-attribution claims now correctly `factual_dependency`/`unsupported` | genuine catch, but sits at an edge of the new section's stated institutional/systemic scope (individual artistic intent) — flagged as a scope question, not resolved |

**Status: diagnostic complete. No prompt wording proposed for a future
version in this pass. `cj2-stage-b2-v1.3` not modified. No `v1.4`. No
cross-publisher batch. No Stage C.**

## PROMPT FROZEN: cj2-stage-b2-v1.4 (2026-08-12) — STATUS: DESIGN CANDIDATE / NOT EXECUTED

**Designed directly from the failure-mechanism diagnostic above, not
from broader example coverage.** Still prompt-only: `B2_MODEL_OUTPUT_V1`
schema, the `problems` enum, the deterministic validators, the
resolver, Stage A, Stage B, and Stage C are all byte-identical/
untouched. User-input template unchanged.

**The core correction — a mandatory, ordered procedure, not a
description the model can bypass.** v1.3's `ROLE MUST BE DETERMINED BY
PROPOSITIONAL DEPENDENCY...` + bare `CONCRETE RESTATEMENT TEST` heading
are RESTRUCTURED (not merely supplemented) into
`MANDATORY ROLE-DECISION PROCEDURE -- FOLLOW IN ORDER, FOR EVERY CLAIM,
BEFORE ASSIGNING ROLE`, an explicit 4-step sequence:

```
STEP 1 -- WORLD-TRUTH TEST      (v1.3's world-truth question, kept,
                                  subject list explicitly broadened to
                                  include "a person, an individual" --
                                  not just institutions/systems, per
                                  the De Hooch/Z finding)
STEP 2 -- MANDATORY CONCRETE RESTATEMENT  (v1.3's test, now stated as
                                  a required step that must be
                                  performed BEFORE role is assigned,
                                  not a description the auditor could
                                  read and then reason around, as it
                                  did on H08. Same 4 generic patterns,
                                  unchanged, verbatim.)
STEP 3 -- HEDGE HANDLING        (NEW). Hedging affects strength, never
                                  role. Explicit word list (may, might,
                                  appears, suggests, assumed,
                                  potentially, e.g., likely). New
                                  generic example: "The rule may
                                  encode an assumption that X" still
                                  contains a factual proposition.
                                  Explicit exemplifying-aside handling
                                  ("e.g., X" narrows scope, does not
                                  exempt the claim it modifies) -- the
                                  exact mechanism the H09-vs-H17
                                  diagnostic identified as H17's actual
                                  failure point.
STEP 4 -- ROLE                  (the existing interpretive_only
                                  boundary, restated as the STEP 4
                                  gate, plus a new explicit precedence
                                  statement: "ROLE CLASSIFICATION MUST
                                  NOT BE OVERRIDDEN BY RHETORICAL
                                  HEDGING. First identify the
                                  proposition and its actual expressed
                                  strength (Steps 1-3). Only then
                                  decide whether that proposition
                                  requires factual support (Step 4).")
```

`DO NOT OVERCORRECT -- A METAPHOR IS STILL A METAPHOR` is KEPT,
unchanged in substance, immediately after Step 4, per instruction. The
pre-existing `HEDGES DO NOT IMMUNIZE A CLAIM` section (unchanged since
v1.1) is also kept, further down, unedited — Step 3 elaborates and
completes it, does not replace it.

**No candidate-specific wording from H08/H17/H09/De Hooch-Z added** —
confirmed by preflight (below): none of the exact fixture phrases
("resolution is a property of the underlying signal," "specifically
five years' worth," "childbearing," "de Hooch," "moral signal," etc.)
appear anywhere in the prompt. The 4 CONCRETE RESTATEMENT TEST examples
and the 1 new hedge example are all carried over or newly written as
generic, subject-neutral patterns, not fixture mimicry.

```
cj2-stage-b2-v1.4
SHA256: c817af5a316978383815cf74e9b2e83020986f4dde0d980cf04a0dbfe8dddb87
```

**Exact delta from v1.3, confirmed by diff: 28 lines added, 6 lines
removed, at exactly one contiguous location** (the old 2-header,
3-paragraph role-determination intro is replaced by the new 4-step
procedure; the 4 generic CONCRETE RESTATEMENT TEST examples and the
anti-overcorrection paragraph are carried over unchanged inside the new
structure). Every other section of the file — confirmed by preflight —
is byte-identical to v1.3, including all 4 JSON examples, the problems
enum, and every section header from `WHAT COUNTS AS AN AUDITABLE
PROPOSITION` through `OUTPUT`.

**Static preflight — 121/121 checks PASS**: every carried-forward v1.1/
v1.2/v1.3 check (banned terms, verdict/run_status absence, unchanged
8-value problems enum, all 16 pre-existing section headers, all 4 JSON
examples parsing with no verdict/run_status keys, no held-out claim,
development-set AND fresh-batch-1 fixture wording both confirmed
absent — now including the specific H08/H09/H17/De-Hooch-Z phrases)
re-verified against v1.4 and still passing, PLUS new checks: all 4 new
STEP headers present; the not-optional/do-not-skip framing present;
the subject list broadened to explicitly include individual people;
all 4 original CONCRETE RESTATEMENT TEST examples retained verbatim;
the full hedge-word list present; the new "may encode an assumption"
example present; the exemplifying-aside handling present; the STEP 4
interpretive_only boundary and the explicit precedence statement both
present, in the correct stated order; the anti-overcorrection rule
confirmed retained; and confirmation that the OLD standalone "ROLE MUST
BE DETERMINED..." and bare "CONCRETE RESTATEMENT TEST" headers are
gone, superseded by the new procedure rather than left duplicated
alongside it.

**Status: `cj2-stage-b2-v1.4` is a FROZEN design candidate,
static-preflight-clean (121/121). No API calls made. No schema, enum,
validator, resolver, Stage A, Stage B, or Stage C changes.**

## REGRESSION ACCEPTANCE CRITERIA FOR cj2-stage-b2-v1.4 — PREREGISTERED BEFORE ANY RUN

Same 30-candidate development/regression corpus as v1.3 (12 development
+ 18 fresh-batch-1) — still development evidence, not held-out, for the
same reason as before.

```
1. H08's exact hardened proposition ("...resolution is a property of
   the underlying signal...") must no longer be classified
   interpretive_only.

2. H17's exact institutional-assumption proposition must no longer be
   classified interpretive_only MERELY BECAUSE its wording contains a
   hedge ("assumed," "e.g."). If it is still classified
   interpretive_only for some OTHER, independently articulated reason
   that does not rely on the hedge, that is a different outcome and
   must be reported as such, not silently equated with "still missed
   for the same reason."

3. H05 and H14's fixes must remain fixed (same claim-level check as
   before -- verdict alone is not sufficient).

4. H03's unsupported rationale claims must remain caught.

5. The De Hooch/Z factual-intent finding must remain caught (the two
   claims already identified: "de Hooch's moralism functioned
   through..." and "...is the moral signal in de Hooch's painting").

6. The existing anti-overcorrection / role-migration guards (the
   operationalized dual test: <=15pp aggregate cap AND <=20% flip-rate
   cap, combined 30-candidate corpus) remain unchanged and must still
   both PASS -- Step 3's broadened hedge-handling language must not
   cause a new, different overcorrection (e.g. now treating EVERY
   hedged claim as factual regardless of content).

7. Any target candidate (H08, H09, H17, De Hooch/Z, H05, H14, H03)
   that comes back schema_invalid or call_failed CANNOT count as a
   successful repair for that candidate, even if the underlying claim
   looks correct in the raw response -- same discipline as H09's
   run in the v1.3 regression (a claim-level fix inside a
   schema-invalid run is reported as "claim fixed, run blocked," never
   as "fixed").
```

**Not executed in this pass.** No new API calls have been made against
`cj2-stage-b2-v1.4`. No new source collection. No Stage C.

**Status: stopping here, before execution, per instruction.**

## PRE-EXECUTION AUDIT + PROMPT FROZEN: cj2-stage-b2-v1.4.1 (2026-08-12) — STATUS: DESIGN CANDIDATE / NOT EXECUTED

**`cj2-stage-b2-v1.4` has still never been executed.** No API call has
ever been made against it, in this pass or any prior one. A
pre-execution audit of the frozen v1.4 design (not of any run output,
because none exists) found two specification problems and required one
integrity re-check before it would have been reasonable to spend a
30-candidate regression call budget on it. This is a design
correction to an unexecuted candidate, not tuning to results — v1.4
produced no results to tune to.

**Hash re-verification (before any edit):**

```
cj2-stage-b2-v1.4.txt
SHA256: c817af5a316978383815cf74e9b2e83020986f4dde0d980cf04a0dbfe8dddb87
MATCHES the hash recorded above. File untouched.
```

**`cj2-stage-b2-v1.4` status corrected to: FROZEN / UNEXECUTED /
SUPERSEDED PRE-EXECUTION BY v1.4.1.** Not "failed" — it was never run,
so it cannot have failed a regression. It remains preserved verbatim
at its original path, unedited, for its own historical record.

### Problem #1 — v1.4's hedge rule overstates in the opposite direction from the bug it was fixing

v1.4's STEP 3 (`HEDGE HANDLING: HEDGING AFFECTS STRENGTH, NEVER ROLE`)
correctly generalizes the H09-vs-H17 diagnostic's lesson that a
candidate's own hedge ("assumed," "e.g.") must not exempt a claim from
factual audit. But its own worked example —
*"'The rule may encode an assumption that X' still contains a factual
proposition... Classify it factual_dependency"* — states this as an
unconditional rule for an ambiguous generic sentence, without routing
it through the STEP 1/STEP 2 world-truth/restatement test first. Read
literally, this replaces one shortcut (hedged → interpretive, H17's
actual failure) with the mirror-image shortcut (hedged conceptual
sentence → factual), which is exactly the overcorrection the v1.4
REGRESSION ACCEPTANCE CRITERIA's own criterion 6 exists to catch. The
correct principle, stated precisely: **hedge words do not determine
role in either direction** — role comes from what Steps 1-2 already
established the proposition requires to be true; the hedge then only
scales how strongly that determination is being asserted.

### Problem #2 — v1.4's regression acceptance criteria are mechanically satisfiable by a non-repair

Criterion 1 ("H08's exact hardened proposition... must no longer be
classified interpretive_only") does not say what it must become
instead. As written, a run that reclassifies H08's target claim
`boundary_ambiguous` — a strictly weaker outcome than the
post-run-diagnostic-adjudication's own finding that this exact claim
(c9) is an unambiguous `factual_dependency`/`unsupported` miss, not a
genuine boundary case — would satisfy the literal wording of criterion
1 without being a real repair. Criterion 2 already anticipates part of
this for H17 ("if it is still `interpretive_only` for some OTHER,
independently articulated reason... must be reported as such") but
does not state the same discipline for H08, and none of the criteria
pin down the exact expected `support`/`problems` state, or require a
`valid` run status, at the level of specificity the existing
adjudication already supports. Corrected below with an exact
claim-level matrix, built from the frozen diagnostic/regression
artifacts directly, not from memory.

### Problem #3 (integrity check) — confirmed clean, no correction needed

Read the complete `cj2-stage-b2-v1.4.txt` role-decision region
directly (not from the earlier pasted terminal output, which looked
visually malformed). Confirmed: no duplicated anti-overcorrection
paragraph, no truncated sentence, no duplicated role section, no
contradictory hedge instructions between STEP 3 and the older `HEDGES
DO NOT IMMUNIZE A CLAIM` section (they agree — the pre-existing section
already says a hedge doesn't decide interpretive status by itself;
STEP 3's problem was its own overcorrected worked example, addressed
above, not a conflict with that older section), and the old standalone
`ROLE MUST BE DETERMINED...`/bare `CONCRETE RESTATEMENT TEST` headers
from v1.3 are correctly gone, superseded by the STEP 1-4 procedure, not
left duplicated alongside it. The visual malformation in the earlier
pasted terminal output was confirmed to be a terminal-rendering
artifact, not a defect in the real file.

### v1.4.1 — exact delta from v1.4

**Prompt-only. No schema, enum, validator, resolver, Stage A, Stage B,
or Stage C change.** Confirmed by diff: 4 lines removed, 8 lines added,
at exactly one contiguous location (lines 84-95 of v1.4, the STEP 3
header + body). Every other line, including all four
CONCRETE-RESTATEMENT-TEST patterns in STEP 2, the STEP 4 precedence
statement, `DO NOT OVERCORRECT`, `HEDGES DO NOT IMMUNIZE A CLAIM`, all
JSON examples, and the `problems` enum, is byte-identical to v1.4.

The STEP 3 header changes from `HEDGING AFFECTS STRENGTH, NEVER ROLE`
to `HEDGE WORDS DO NOT DECIDE ROLE`. The body is rewritten to: (a)
state the symmetric rule — a hedge does not make a factual proposition
interpretive, AND a hedge does not make an interpretive proposition
factual; (b) give a worked example of a hedged proposition that
correctly stays `factual_dependency` at reduced modality ("The
committee may have believed X"); (c) give a contrasting worked example
of a hedged proposition that correctly stays `interpretive_only`
regardless of the hedge ("One way to read the rule is as a picture of
X"); (d) state explicitly that the ambiguous generic form "The rule
may encode X" must not be decided from "may" or "encode" alone, and
must instead be run through STEP 1/STEP 2 first; (e) keep the
exemplifying-aside paragraph, extended to state the same symmetry
(an aside doesn't shield a fact, and doesn't manufacture one either).
No candidate-specific wording from H05/H08/H09/H14/H17/H03/De-Hooch-Z
added — confirmed by preflight below.

```
cj2-stage-b2-v1.4.1
SHA256: b67630dcc17e0020e24c18dbaac6e3735c3842631ab2ff9ac8f63c51992fc788
```

### Static preflight — 45/45 checks PASS (no API calls)

Checked programmatically against the actual file (script, not
memory): all model-facing banned-output-key checks (`verdict`,
`effective_verdict`, `run_status` absent, still); all 22 section
headers from v1.1-v1.4 present, including the renamed STEP 3 header;
the old absolute `HEDGING AFFECTS STRENGTH, NEVER ROLE` header and its
unconditional "Classify it factual_dependency" example confirmed
ABSENT; the new symmetric hedge statement, the new ambiguous-form
guard, and both new worked examples (committee-belief /
picture-reading) confirmed PRESENT; no duplicated paragraph anywhere in
the file; all fixture-specific phrases (`resolution is a property of
the underlying signal`, `specifically five years' worth`, `childbearing`,
`de Hooch`, `moral signal`, `socially obligated to keep ranking`,
`3,700`, `NSFC`, `NIH`) confirmed ABSENT, with v1.3's own generic
`is load-bearing` pattern confirmed still present (expected — it is a
carried-over generic pattern, not fixture wording); all JSON examples
still parse. **45/45 PASS.**

**Status: `cj2-stage-b2-v1.4.1` is a FROZEN design candidate,
static-preflight-clean (45/45). No API calls made. `cj2-stage-b2-v1.4`
preserved unchanged at its own path, hash re-verified.**

## EXACT CLAIM-LEVEL REGRESSION ACCEPTANCE MATRIX FOR cj2-stage-b2-v1.4.1 — PREREGISTERED BEFORE ANY RUN

Built directly from the frozen artifacts (`b2-v1.3-failure-mechanism-diagnostic-v1.json`,
`post-run-disagreement-adjudications-v1.json`, and the raw
`b2_v1_2`/`b2_v1_3` claim-level JSON outputs for H03/H05/H08/H09/H14/H17
and `05_dutch_painting_soldier`/Z), not from memory. Matching is by
claim CONTENT, not `claim_id` — re-extraction under v1.4.1 legitimately
renumbers claims, as already observed between v1.2 and v1.3 (H05's own
target claims were `c9`/`c11` under v1.2 and `c10`/`c14` under v1.3,
same content, different IDs).

Same 30-candidate development/regression corpus as v1.3/v1.4 (12
development + 18 fresh-batch-1) — still development evidence, not
held-out.

```
CANDIDATE: H08 (fresh, engine Z)
  target claim text: "The scale's resolution was treated as adjustable
    by the raters, when in fact resolution is a property of the
    underlying signal." (v1.2/v1.3 claim_id c9, unchanged both runs)
  expected role: factual_dependency
  expected support: unsupported
  expected problems: at least one of {modality_hardening, other}
  candidate run-status requirement: valid
  DOES NOT COUNT AS REPAIRED IF: role stays interpretive_only, OR role
    becomes boundary_ambiguous (the post-run adjudication already
    confirmed this exact claim -- distinct from the separately
    re-audited c5 -- is an unambiguous miss, not a genuine boundary
    case), OR run is schema_invalid/call_failed.
  notes: this is the modality/certainty-hardening subtype; the source
    hedges ("might not have existed," "often could not [be
    distinguished]"); the candidate's "in fact...resolution is a
    property of the underlying signal" removes that hedge and asserts
    settled certainty. No self-qualifying hedge INSIDE the candidate's
    own claim text (unlike H17) -- STEP 3's hedge-symmetry fix is not
    expected to be the operative mechanism for this one; STEPS 1-2
    (world-truth test, concrete restatement) are.

CANDIDATE: H09 (fresh, engine P)
  target claim text: "The sex-differentiated cutoff encodes an
    institutional assumption about the expected magnitude of female
    career interruptions -- specifically five years' worth." (v1.2/v1.3
    claim_id c5, unchanged both runs)
  expected role: factual_dependency
  expected support: unsupported
  expected problems: motivation_invention
  candidate run-status requirement: valid (NOT schema_invalid) -- this
    is the extra bar v1.3 failed on an UNRELATED claim (c7, "Women's
    careers are actually interrupted more than men's careers -- this
    is a real social pattern," which had support=unsupported but was
    missing a required semantic-problem tag). H09 does not count as
    repaired unless BOTH the target claim is correctly classified AND
    the whole run is schema-valid.
  notes: flat, unhedged, exactly-quantified wording -- the control half
    of the H09-vs-H17 contrast pair.

CANDIDATE: H17 (fresh, engine Z)
  target claim text: "The differential cutoffs reveal that the system
    is measuring career stage adjusted for an assumed sex-linked career
    disruption pattern (e.g., childbearing)." (v1.2 claim_id c4, worded
    "such as childbearing"; v1.3 re-extraction kept c4, worded
    "e.g., childbearing" -- same underlying proposition)
  expected role: factual_dependency
  expected support: unsupported
  expected problems: motivation_invention
  candidate run-status requirement: valid
  DOES NOT COUNT AS REPAIRED IF: role stays interpretive_only for ANY
    reason that cites the claim's own "assumed"/"e.g." wording as
    grounds for exemption -- if it is interpretive_only for some OTHER,
    independently articulated reason that does not invoke the hedge,
    report that explicitly as a different outcome, not as "still
    missed for the same reason," per the original criterion 2 wording
    (carried forward unchanged). Role becoming boundary_ambiguous also
    does not count as repaired -- this claim has no adjudicated
    boundary status, unlike H08/c5.
  notes: the treatment half of the H09-vs-H17 contrast pair -- the ONLY
    difference in kind from H09 is the internal hedge/aside. This is
    the single most direct test of the v1.4.1 correction, since v1.3's
    own actual failure here was explicitly hedge-driven.

CANDIDATE: H05 (fresh, engine M) -- protect the v1.3 fix
  target claim texts (two, same underlying institutional-obligation
    proposition, re-extracted under different wording/IDs each run --
    match by content):
    1. "Panels were socially obligated to keep ranking even after
       their genuine discriminatory capacity had run out." (v1.2 c9)
       / "...even after ranking had become meaningless." (v1.3 c10)
    2. "The statistical framework revealed that the system had been
       quietly outsourcing its promise to a performance of precision
       that panels were socially obligated to deliver regardless of
       whether the underlying signal existed." (v1.2 c11) / "Panels
       were not failing to rank; they were successfully performing
       ranking as a duty." (v1.3 c14)
  expected role: factual_dependency (both)
  expected support: unsupported (both)
  expected problems: motivation_invention (both; v1.3 additionally
    tagged undeclared_factual_dependency on both -- acceptable, not
    required)
  candidate run-status requirement: valid
  notes: already confirmed fixed under v1.3; v1.4.1's STEP 3 rewrite
    must not regress it. Flat, unhedged wording -- STEP 3 is not
    expected to be load-bearing for this candidate either way.

CANDIDATE: H14 (fresh, engine S) -- protect the v1.3 fix
  target claim texts (two):
    1. "In the 3,700+ already-funded projects, the word 'policy' is not
       decorative but load-bearing, marking the orientation of the work
       toward its intended use." (v1.2/v1.3 claim_id c6)
    2. "If the word-removal criterion were applied consistently, it
       would retroactively delegitimize a large portion of the existing
       funded portfolio." (v1.2/v1.3 claim_id c7)
  expected role: factual_dependency (both)
  expected support: unsupported (both)
  expected problems: other (both, per v1.3's own tagging; the
    scope/population-generalization pattern has no more specific
    enum value)
  candidate run-status requirement: valid
  notes: already confirmed fixed under v1.3 (scope/population-
    generalization subtype); no internal hedge in either claim. Must
    remain fixed.

CANDIDATE: H03 (fresh, engine M) -- protect a v1.2/v1.3 correct catch (control)
  target claim texts (three, v1.2/v1.3 claim_ids c6/c7/c10, unchanged
    both runs):
    1. "Female researchers are more likely to have had career
       interruptions (e.g., childbearing) that delay their career
       progression relative to chronological age."
       expected role: factual_dependency, support: unsupported,
       problems include: other (v1.2/v1.3 also tag
       undeclared_factual_dependency)
       DOES NOT COUNT AS PROTECTED IF: the "(e.g., childbearing)" aside
       in THIS claim's own wording is newly used as grounds to exempt
       it -- this is the same hedge-exemption failure mode as H17, on
       a claim that must NOT regress.
    2. "The 40-year cutoff for women is an operational patch applied to
       a proxy that would otherwise systematically exclude women whose
       career clocks and biological clocks ran concurrently."
       expected role: factual_dependency, support: unsupported,
       problems include: motivation_invention, causality_hardening
    3. "The program now works adequately for women who fit the
       interruption pattern the correction assumes."
       expected role: factual_dependency, support: unsupported,
       problems include: modality_hardening
       DOES NOT COUNT AS PROTECTED IF: the word "assumes" in this
       claim's own wording is newly used as grounds to exempt it.
  candidate-level expected verdict: unsafe (unchanged)
  candidate run-status requirement: valid
  notes: H03/H09/H17 are the same source and proposition family; the
    post-run adjudication independently confirmed B2's `unsafe` verdict
    on H03 is CORRECT (not a false-unsafe) -- the assisted reference's
    own H03/H09/H17 inconsistency, not a B2 boundary case. All three of
    H03's own claims already contain hedges/asides ("e.g.," "assumes")
    in their own text and were STILL correctly caught by both v1.2 and
    v1.3 -- this candidate is direct evidence that hedge-driven
    exemption is a real, specific failure mode (seen on H17), not an
    unavoidable consequence of hedged wording in general.

CANDIDATE: 05_dutch_painting_soldier/Z (De Hooch/Z, dev set) -- protect a v1.3 finding
  target claim texts (two, v1.3 claim_ids c7/c14):
    1. "De Hooch's moralism functioned through contrast and
       implication: the woman drinking the pass-glass while the two
       men abstain is the moral signal." expected role:
       factual_dependency, support: unsupported, problems:
       motivation_invention, causality_hardening
    2. "The contrast between the woman drinking and the men not
       drinking is the moral signal in de Hooch's painting." expected
       role: factual_dependency, support: unsupported, problems:
       motivation_invention
  candidate run-status requirement: valid
  notes: both claims are flat, unhedged assertions of the painter's
    own historical intent -- no hedge-handling mechanism is expected to
    be load-bearing here. Flagged, not re-resolved, per the existing
    scope note: attributing a "design mechanism" to an individual
    historical artist sits at an edge of STEP 1's subject list (which
    v1.4 already broadened to explicitly include "a person, an
    individual" -- unchanged in v1.4.1). Must remain caught regardless.
```

**Global guards, unchanged, still both required to PASS (v1.2 baseline
vs. v1.4.1, combined 30-candidate corpus, same operational test as the
v1.3 regression):**

```
(a) AGGREGATE DISTRIBUTION CAP: interpretive_only percentage-point drop
    <=15pp AND factual_dependency percentage-point rise <=15pp
    (v1.2 -> v1.4.1).
(b) FLIP-RATE CAP: of v1.2's interpretive_only claims, <=20% flip to
    factual_dependency or boundary_ambiguous under v1.4.1 (matched by
    claim content).
```

Thresholds themselves are NOT altered in this pass, per instruction.
As a diagnostic-only side observation (not a new gate), also record
the v1.3 -> v1.4.1 delta on these same two measures, since STEP 3 was
rewritten after v1.3 already passed both checks cleanly (+1.1pp/-0.6pp,
1.72% flip rate) -- a large v1.3->v1.4.1 shift would be worth noting
even though only the v1.2 baseline comparison is the actual gate.

**Any target candidate (H03, H05, H08, H09, H14, H17,
`05_dutch_painting_soldier`/Z) that comes back `schema_invalid` or
`call_failed` cannot count as a successful repair or a protected catch
for that candidate**, even if the underlying claim looks correct in
the raw response — same discipline as H09's v1.3 run, carried forward
unchanged.

**No tuning after seeing v1.4.1 results without a new named version**
(v1.4.2, if needed) — unchanged from the v1.3/v1.4 criteria.

**Not executed in this pass.** No new API calls have been made against
`cj2-stage-b2-v1.4.1`. No new source collection. No Stage C.

**Status: v1.4 preserved and re-verified unchanged; v1.4.1 created,
hashed, and static-preflight-clean; exact claim-level acceptance matrix
preregistered; global anti-overcorrection guards unchanged; stopping
here, before execution, per instruction.**

## `cj2-stage-b2-v1.4.1` REGRESSION RUN — COMPLETE, RESULT: FAIL (2026-08-12)

**Accepted for execution per explicit instruction.** Prompt, acceptance
matrix, validators, schema, resolver, harness semantics, and Stage
A/B/C left untouched before and during the run. Pre-run header printed
and recorded:

```
prompt_version = cj2-stage-b2-v1.4.1
prompt_sha256  = b67630dcc17e0020e24c18dbaac6e3735c3842631ab2ff9ac8f63c51992fc788
regression_corpus = same 30 candidates as the v1.3 regression (12 dev + 18 fresh-batch-1)
acceptance_matrix = automation/.probe_fixtures/cj2-b2-v1.4.1-regression/acceptance-matrix-v1.json
acceptance_matrix_sha256 = fdabba24b34c4b09ec9578ebf31d2a9947984a811900f0fb3f844b9712b61c22
```

The acceptance matrix existed only as markdown before this run — created
a byte-verbatim machine-readable transcription (no reinterpretation) and
hashed it, per instruction, before the first API call.

Built `cj2_b2_probe_v1_4_1.py` / `cj2_freshbatch1_b2_probe_v1_4_1.py` as
pure copies of the v1.3 harness scripts — diff confirmed the ONLY
changes are `PROMPT_FILE`/`B2_DIR` (and the import target in the
fresh-batch script) plus docstrings; every call-construction,
input-construction, validator, resolver, and run_status/
effective_verdict line is byte-identical to v1.3's harness. Executed on
trident (CLIProxyAPI is localhost-only) in an isolated `/tmp` scratch
checkout containing only the 25 files this run needs — all 25 inputs
hash-verified byte-identical before the run, all outputs hash-verified
byte-identical after pull-back, scratch removed after. `cj2-stage-b2-v1.2`,
`cj2-stage-b2-v1.3` outputs, and the unexecuted `cj2-stage-b2-v1.4`
prompt all re-confirmed untouched (hashes/mtimes unchanged).

**Mechanical: 30/30 run, 30 `valid`, 0 `schema_invalid`, 0 `call_failed`**
— a real improvement over v1.3's 29 valid/1 schema_invalid (the H09
compliance slip did not recur).

**PRIMARY SCORING (claim-level matrix): 2 PASS / 5 FAIL of 7 targets.**

```
H08                          FAIL -- still interpretive_only, unchanged
H09                          FAIL -- REGRESSED to interpretive_only (was
                              correctly factual_dependency under v1.3,
                              just schema-blocked); run now valid, but
                              target claim itself misclassified; candidate
                              verdict unsafe only via an UNRELATED claim
                              -- does not count as a repair, per the
                              explicit IMPORTANT clause
H17                          FAIL -- still interpretive_only, unchanged,
                              but by a DIFFERENT mechanism than v1.3's
                              diagnosed hedge-exemption bug (see below)
H05                          PASS -- fix holds
H14                          FAIL -- REGRESSED; both previously-fixed
                              target claims reverted to interpretive_only
H03                          PASS -- control holds, candidate unsafe
De Hooch/Z                   FAIL -- REGRESSED; both target claims
                              reverted to interpretive_only, candidate
                              verdict reverted unsafe -> safe
```

**H09 in detail** — target claim ("The sex-differentiated cutoff
encodes an institutional assumption about the expected magnitude of
female career interruptions -- specifically five years' worth") is
`interpretive_only`; its own `why`: *"the candidate is not claiming the
NSFC actually held this belief... it is offering a reading of what the
format's arithmetic encodes... The argumentative force does not depend
on any additional empirical fact..."* The candidate's overall
`effective_verdict` is `unsafe` solely because of a different claim
(c6, "Women's careers are interrupted more than men's... this is an
invisible social pattern," unsupported) -- textbook instance of the
scoring rule's own anticipated failure mode.

**H14 and De Hooch/Z in detail** -- both previously-fixed under v1.3,
both now `interpretive_only` again, both `why` fields reasoning in the
same register as H08/H09/H17 ("a reading of what X signifies," "an
interpretive reading... not a new world-claim"), never invoking the
MANDATORY CONCRETE RESTATEMENT test.

**HEDGE-SPECIFIC DIAGNOSTIC (diagnostic only, did not change scoring).**
H17's own `why` explicitly notes the "e.g., childbearing" aside is "not
a factual claim" but does NOT use that as the stated basis for its
interpretive_only call -- it calls the whole claim "a lens applied to
established facts," without ever performing STEP 2. **STEP 3's specific
hedge-as-exemption bug (the one v1.3 was diagnosed with) is fixed** --
H17 no longer fails because of its own hedge wording. A broader,
still-unfixed bypass of STEP 2 ("conceptual reframing" shortcut)
produces the same miss by a different route. H08's `why` shows the
identical STEP-2 bypass, unchanged from v1.3. **Contrast case, same
run**: H05/c11's own `why` explicitly performs the restatement by
name -- *"The concrete restatement of this claim is: the system's
functioning actually depended on panels being under a social
obligation..."* -- and correctly lands on `factual_dependency`/
`unsupported`, proving STEP 2 CAN be and IS invoked correctly within
this very run; it is being selectively skipped on the failing targets,
not universally broken. Conclusion: v1.4.1 fixed the *specific*
mechanism diagnosed for H17, but the underlying failure family
(`CONCEPTUAL-SUBJECT FACTUALITY SHIELDING`) reasserted itself through a
different verbal route, and appears to have widened rather than
narrowed.

**GLOBAL GUARDS (v1.2 baseline, frozen thresholds, unchanged): both
PASS, mechanically, but do not measure the failure mode observed.**

```
Aggregate cap (<=15pp each direction, cap guards a DROP in
interpretive_only / RISE in factual_dependency):
  interpretive_only: 56.6% (v1.2) -> 61.8% (v1.4.1)   ROSE +5.2pp
  factual_dependency: 43.0% (v1.2) -> 38.2% (v1.4.1)  FELL -4.8pp
  PASS by the letter of the rule -- movement is in the OPPOSITE
  direction from what this cap bounds.

Flip-rate cap (<=20%, v1.2 interpretive_only -> v1.4.1 factual/boundary):
  233 v1.2 interpretive_only claims, 2 flipped -> 0.86%. PASS.
```

Both frozen gates guard against overcorrection TOWARD factual_dependency
-- this run moved the opposite direction, so neither fires. Recorded a
DIAGNOSTIC-ONLY reverse measure (not a new gate, not retroactively
added to the frozen criteria) precisely because the frozen gates are
silent on this direction: of 177 v1.2 `factual_dependency` claims, 8
flipped to `interpretive_only` under v1.4.1 by exact-text match alone
(a lower bound) -- reverse flip rate 4.52% minimum. Candidate-level:
7 of 8 v1.3->v1.4.1 verdict transitions moved TOWARD `safe`; only H09
moved toward `unsafe`, and even there the target claim itself still
fails -- one-directional, not an isolated anomaly.

**ACCEPTANCE STATUS, applied mechanically, no invented "partial pass"
category:**

```
FAIL -- broad regression toward interpretive_only via an unfixed
conceptual-reframing bypass of the MANDATORY CONCRETE RESTATEMENT step;
5 of 7 preregistered targets fail (H08, H09, H17, H14, De Hooch/Z),
including two that were already fixed under v1.3 and are now broken
(H14, De Hooch/Z).
```

Partial improvement described separately, does not change the gate:
run-status reliability improved (0 vs. 1 schema_invalid) and H09's run
is no longer blocked, but the underlying claim-level miss on H09 is
unchanged and the net effect elsewhere is regression, not repair.

**Artifacts produced and hashed:**

```
automation/.probe_fixtures/cj2-b2-v1.4.1-regression/acceptance-matrix-v1.json
  SHA256: fdabba24b34c4b09ec9578ebf31d2a9947984a811900f0fb3f844b9712b61c22

automation/.probe_fixtures/cj2-b2-v1.4.1-regression/b2-v1.4.1-regression-comparison.json
  SHA256: b47bbf067951456c38a52fd05c527e51f3a5decce1bf1948c2a28d4174b3ef61

automation/.probe_fixtures/cj2-b2-v1.4.1-regression/b2-v1.4.1-regression-report.md
  SHA256: 4f72a12a99b91b194dc09914c74e98ff0b010eddedf1632aab8a2cc441ebb38d
```

Raw per-candidate outputs preserved at
`automation/.probe_fixtures/cj2-reference-probe-1/b2_v1_4_1/` (12
dev-set) and `automation/.probe_fixtures/cj2-fresh-batch-1/b2_v1_4_1/`
(18 fresh-batch-1). `cj2-stage-b2-v1.2`/`v1.3` outputs and the
unexecuted `cj2-stage-b2-v1.4` prompt preserved unchanged.

**Status: `cj2-stage-b2-v1.4.1` is NOT modified in response to this
result. No `cj2-stage-b2-v1.4.2`/`v1.5` designed. No cross-publisher
batch collected. No Stage C. No tuning from individual failures.
Stopping here, per instruction.**

## HARNESS-HARDENING NOTE FOR THE FUTURE (recorded, not acted on this run)

`compute_effective_cj1_eligibility()` currently assumes `validation` is
always a real, well-formed dict with a `violations` list whenever
`decision == "PASS"` and `validation["valid"]` is `False`. If a future
caller ever passes a `cj1_result` with `validation=None` (e.g. a
provider-format anomaly upstream of `validate_v3_judgment` itself) or
a `validation` that is somehow `valid=False` with an EMPTY violations
list, the current code silently proceeds to `failing_indices = sorted(...)`
over an empty set and returns `eligible=True` — a fail-OPEN default,
not fail-CLOSED. Not a live bug in this run (every call here produced a
real `validate_v3_judgment` result with either `valid=True` or a
non-empty violations list), but before this function is reused in
another experiment, it should be hardened to treat
`validation is None` or `(not validation["valid"] and not violations)`
as an explicit `ineligible` case (e.g. `path="malformed_validation"`),
never as an implicit pass-through. Recorded here per instruction;
`cj2_fresh_batch1_pipeline.py` is NOT edited for this in the current
run.

## STATUS CORRECTION: `cj2-stage-b2-v1.4.1` REGRESSION IS FAIL, NOT A BASE TO TUNE FROM (2026-08-12)

Recorded formally, separate from the run report above, because it
changes what happens next rather than just what happened:

```
cj2-stage-b2-v1.4.1 REGRESSION STATUS: FAIL
PROMPT-ONLY ROLE-CLASSIFICATION CORRECTION HAS REACHED A RELIABILITY
LIMIT FOR THIS FAILURE CLASS
```

This is not a claim that prompt-only approaches can never work in
general — it is a claim that the current evidence no longer justifies
another immediate prompt-only patch (a `v1.4.2`) as the default next
move. **No `v1.4.2` designed. No tuning of v1.4.1. No cross-publisher
batch collected. No Stage C run.** This section and the next design a
structural successor instead — architecture only, nothing executed.

### Why prompt-only has hit a limit, stated as evidence, not intuition

Two independent prompt revisions, each targeting a specific diagnosed
mechanism, each measurably fixed that mechanism, and each let a
same-shaped failure back in through an undiagnosed side door:

- **v1.3** added the WORLD-TRUTH TEST / MANDATORY CONCRETE RESTATEMENT
  language. It fixed H05 and H14 (both flat, unhedged claims). It did
  **not** fix H08 — the auditor's own `why` for H08 stays entirely in
  the pre-existing "conceptual lens" register and never invokes the new
  test, despite H08 being a near-exact match for the new section's own
  worked example. The rule was bypassed, not applied-and-failed. It
  also newly failed H17 by a diagnosed, specific mechanism: the
  auditor treated H17's own internal hedge/aside (`"assumed"`, `"e.g.,
  childbearing"`) as sufficient grounds to exempt the whole claim —
  the exact opposite of the pre-existing (unchanged since v1.1) HEDGES
  DO NOT IMMUNIZE A CLAIM section.
- **v1.4.1** rewrote STEP 3 specifically to close the H17 hedge-as-
  exemption bug. It worked, narrowly: H17's own `why` this run no
  longer cites the hedge as its reason. But H17 **still** landed on
  `interpretive_only` — now because the auditor calls the whole claim
  "a lens applied to established facts... not a new world-claim,"
  again never performing the MANDATORY CONCRETE RESTATEMENT. H08 shows
  the identical bypass, unchanged from v1.3. Worse: two claims that
  *were* fixed under v1.3 (H14, De Hooch/Z) **regressed** back to
  `interpretive_only` under v1.4.1, using the same bypass register. Net
  directional evidence: 7 of 8 v1.3→v1.4.1 candidate-verdict
  transitions moved toward `safe`; reverse flip rate (`factual_
  dependency`→`interpretive_only`) was 4.52% minimum, one-directional,
  not noise.
- **The control that matters most:** in the *same* v1.4.1 run, H05/c11's
  own `why` field explicitly performs the concrete restatement by
  name — *"The concrete restatement of this claim is: the system's
  functioning actually depended on panels being under a social
  obligation..."* — and correctly lands on `factual_dependency`/
  `unsupported`. **The procedure is not missing from the model's
  capability. It is being selectively skipped, per-claim, in a way
  that produces fluent, confident, wrong-sounding-right justification
  text** ("a lens applied to established facts," "an interpretive
  reading of the rule's structural logic") that is indistinguishable,
  from the outside, from a claim where the procedure really was
  followed and genuinely resolved to `interpretive_only`.

That last point is the actual diagnosis, and it is a diagnosis about
the *architecture* of the check, not the *wording* of the rule: a
mandatory intermediate reasoning step that lives only inside a free-
text `why` field, culminating directly in the final `role`, cannot be
verified to have run. Two rounds of sharper wording each closed the
one bypass signature the previous round's diagnostic could name, and
each opened (or re-opened) a same-shaped bypass under a different
verbal signature. Iterating a third time on wording, with no way to
check whether STEP 2 actually ran, is very likely to repeat the same
cycle — that expectation, not a hard proof, is why this pass designs a
structural fix instead of a `v1.4.2`.

## B2 v2 — EXPLICIT PROPOSITION CONTRACT (DESIGN ONLY, NOT EXECUTED) (2026-08-12)

**Design objective:** make the world-truth / concrete-restatement step
an explicit intermediate artifact that role classification must
consume, instead of leaving it inside hidden model reasoning where it
can be skipped. Nothing below is implemented, wired, or called. No
production code touched. No API calls made. `cj2-stage-b2-v1.4.1` is
not edited. Stage A/B/C, CJ-1, personas, and the affinity/router
architecture are not touched.

### Why R1/R2 is the smallest structural fix, checked against the existing code, not assumed

`cj2_b2_probe_v1_4_1.py` already does exactly four things in one model
call: (1) atomic claim decomposition via the field coverage manifest,
(2) STEP 1–2 (world-truth test, concrete restatement) as *unstructured
prose inside the model's own reasoning*, (3) STEP 3–4 (hedge handling,
role assignment), (4) support/declaration/evidence-citation. Steps (1)
and (4) are already externalized as required, checkable fields
(`field_audits`, `auditor_evidence`) and the diagnostics never show
them failing — decomposition is confirmed working even on H08 ("the
proposition was extracted as its own atomic claim... byte-identical
text, never split or merged"). **Steps (2) and (3) are the only ones
that currently exist purely as prose inside `why`, with no required
field forcing their output, and they are exactly the steps every
diagnosed regression traces back to.** The smallest change that fixes
this is not a new taxonomy or a new final verdict — it is promoting
steps (2)–(3) from optional prose into a required, separately-produced,
separately-checkable artifact, consumed (not re-derived) by the step
that assigns role. That is the R1/R2 split below. Nothing else in the
current design needs to change for this fix to apply.

A **single-call** alternative (add `world_truth_question` /
`concrete_restatement` as required fields on the *existing* one-call
schema, ordered before `role` in the JSON) was considered and
rejected as insufficiently structural: it forces the artifact to
*exist*, but a single autoregressive generation can still write a
restatement quietly worded to make whatever role it already "intends"
look consistent — there is no separate object forcing the restatement
to be fixed *before* role is decided, and no natural place to attach a
deterministic cross-check between "what the restatement requires" and
"what role got assigned," because both come from the same call and the
same untrusted judgment. **Two calls, R2 given R1's output as fixed
input it cannot silently revise, is what makes the cross-check in
"DETERMINISTIC CONSISTENCY LAYER" below possible at all.**

### R1 — proposition analysis

**Maps directly onto the existing prompt's own STEP 1 + STEP 2** — this
is not new semantics, it is promoting two already-specified reasoning
steps into their own required output.

**Input:** the candidate's claim-bearing fields only —
`additional_source_observations[].observation`, `engine_move`,
`seed_engagement`, `interpretive_inference`, `conceptual_shift` (if
present), `claimed_contribution`. **R1 does NOT receive `source_
snapshot`, canonical evidence, or declared evidence at all.** This is
deliberate, not an oversight: the world-truth test ("what would have
to be true in the world for this proposition to hold") is a question
about the proposition's own logical requirements, not about whether
the source happens to establish it — keeping R1 evidence-blind
prevents R1 from quietly reasoning "the source doesn't say this, so
call it interpretive," the same shortcut this whole redesign exists to
close, just relocated one stage earlier. It also makes R1 cheap: no
source snapshot in the input at all.

R1 still owns the field-coverage manifest and atomic decomposition —
unchanged behavior, just produced here instead of inside the old
single B2 call.

```
R1_MODEL_OUTPUT_V1

{
  "field_audits": [
    { "source_field": "...", "claim_ids": ["c1", "c2"],
      "no_auditable_propositions": false }
    // unchanged shape/invariants from B2_MODEL_OUTPUT_V1 above
  ],
  "propositions": [
    {
      "claim_id": "c1",
      "surface_claim": "the proposition, stated plainly, in the
                         candidate's own expressed strength/hedge",
      "source_field": "engine_move",
      "world_truth_question": "one sentence: what would have to be
                                true in the world for this proposition
                                to hold?",
      "requires_concrete_restatement": true,
      // true whenever the surface_claim is phrased conceptually,
      // metaphorically, systemically, or through STEP-2-trigger
      // vocabulary (encodes, produces, obligates, contains no
      // signal, is load-bearing, functions as, reveals, assumes, or
      // similar) -- same trigger list already in the frozen v1.4.1
      // prompt, reused verbatim, not re-derived here (see DECISIONS
      // below on whether to also enforce this by keyword as a
      // deterministic backstop)
      "concrete_restatement": "the nearest concrete world-claim,
                                without strengthening the original's
                                hedge -- null/omitted only when
                                requires_concrete_restatement=false",
      "empirical_dependency": "true" | "false" | "uncertain",
      // R1's OWN preliminary judgment, from STEP 1-2 alone: does the
      // (restated) proposition require some event/causal relation/
      // capability/dependency/motivation/population fact/condition to
      // actually hold in the world -- independent of whether the
      // source establishes it. This is NOT role -- role stays R2's
      // job entirely, folding in hedge handling (STEP 3) and the
      // support/declaration axis R1 never sees.
      "empirical_dependency_rationale": "one sentence"
    }
  ]
}
```

**Field invariant (deterministic, checked before anything else):**
`requires_concrete_restatement=true` requires a non-empty
`concrete_restatement`; `=false` requires it null/omitted. A claim
that needed the test and got no restatement text is exactly the H08/
H17 bypass signature, now structurally visible instead of buried in a
`why` field — this is the single most important invariant in the
whole v2 design, because it is the direct fix for the failure the
evidence diagnoses.

### R2 — role / factuality audit

**Maps onto STEP 3 (hedge handling) + STEP 4 (role) + the existing
support/declaration/evidence axis** — unchanged from
`B2_MODEL_OUTPUT_V1` except for two additions described below.

**Input:** `source_snapshot`, canonical `cj1:aN` evidence, candidate-
declared seed evidence, the original candidate field text, **and R1's
full `propositions[]` array for this candidate, given as fixed
context, not re-derivable.** R2 does not see the engine capsule,
persona, or other candidates — same engine-blindness as today's B2,
unchanged.

**Hard constraint, deterministic, checked before claim-level
invariants:** R2's `claims[]` must contain **exactly** the `claim_id`s
R1 already fixed in `propositions[]` — no additions, no removals, no
re-decomposition. This closes a loophole symmetric to the existing
field-coverage-manifest fix (which prevents silently skipping a
*field*): without it, R2 could dodge an inconvenient R1 flag by
quietly re-atomizing the claim under a new ID that never gets checked
against R1's judgment.

```
R2_MODEL_OUTPUT_V1

{
  "claims": [
    {
      "claim_id": "c1",                    // MUST equal an R1 claim_id
      "claim": "the specific proposition, stated plainly",
                                             // (unchanged from today)
      "source_field": "engine_move",        // unchanged
      "role": "interpretive_only" | "factual_dependency" |
              "boundary_ambiguous",         // unchanged
      "importance": "load_bearing" | "supporting" | "incidental",
                                             // unchanged
      "support": "supported" | "unsupported" | "not_required" |
                 "uncertain",                // unchanged
      "declaration": "declared" | "undeclared" | "not_applicable" |
                     "uncertain",            // unchanged
      "declared_refs": ["cj1:a1"] | ["obs:1"] | [],  // unchanged
      "auditor_evidence": [ {"excerpt": "...",
                              "relation": "supports_claim" |
                                          "does_not_establish_claim"} ],
                                             // unchanged
      "problems": ["modality_hardening" | ... ],      // unchanged
      "why": "one sentence",                // unchanged
      "r1_agreement": "consistent" | "override",
      // NEW. "override" only ever legal when it resolves a
      // disagreement with R1 -- see DETERMINISTIC CONSISTENCY LAYER.
      "override_rationale": "..." | null
      // NEW. Required non-empty when r1_agreement="override";
      // must be null/omitted when "consistent". This is R2's OWN
      // explanation for departing from R1's structural judgment --
      // an inspectable trace where today there is none at all.
    }
  ]
}
```

### DETERMINISTIC CONSISTENCY LAYER

Runs between R1 and R2, orchestrator-side, no LLM, same "wraps, never
mutates" discipline as every other validator in this design.

```
For every claim_id, let:
  ED  = R1.propositions[claim_id].empirical_dependency   (true|false|uncertain)
  ROLE = R2.claims[claim_id].role

DANGEROUS DIRECTION (fail-closed -- this is the exact, repeatedly
observed failure mode: a real dependency waved through as a lens):
  if ED == true and ROLE == "interpretive_only":
    require R2.claims[claim_id].r1_agreement == "override"
            AND override_rationale is a non-empty string
    else -> claim structural invariant violation
            -> this candidate's B2 run is schema_invalid
            (SAME treatment as every other structural invariant
            violation today -- no new verdict category invented)

OTHER DIRECTION (diagnostic-only, not fail-closed, by design --
see ANTI-OVERCORRECTION below):
  if ED == false and ROLE == "factual_dependency":
    -- legal without an override; logged as "r2_stricter_than_r1"
       for the bidirectional migration report, not blocked. R1 works
       without evidence access; a legitimate factual read R1's
       structural pass missed is not the failure this gate exists to
       prevent, and gating it would reintroduce exactly the kind of
       friction the ANTI-OVERCORRECTION section (existing prompt,
       unchanged) already warns against.

  if ED == "uncertain":
    -- R2 resolves freely; record which way it resolved (role) for
       calibration, no override required, since R1 itself never
       committed to a value here.

  if ED == true and ROLE == "boundary_ambiguous":
    -- legal without override: R1 flagging a real dependency and R2
       honestly being unable to resolve support/declaration for it is
       not a disagreement, it's two stages agreeing something needs
       auditing and R2 additionally reporting it could not finish the
       job. Not gated.
```

This directly targets the diagnosed failure without inventing a new
verdict: an R2 that wants to call something `interpretive_only` when
R1 already flagged it as requiring a real-world fact must now produce
a non-empty, inspectable reason for that departure, or the run is
`schema_invalid` under the exact same mechanism (a structural
invariant violation) that already governs every other malformed-output
case in this pipeline. `boundary_ambiguous` is reused, unchanged, for
R2's own honest uncertainty — no new role, no new candidate-level
verdict.

### Failure / ambiguity behavior, summarized

```
R1 required field missing (concrete_restatement absent when
  requires_concrete_restatement=true)          -> schema_invalid
R2 introduces/drops/renames a claim_id vs R1's fixed set
                                                 -> schema_invalid
R2 role=interpretive_only contradicts R1
  empirical_dependency=true, no valid override  -> schema_invalid
R2 role=interpretive_only contradicts R1
  empirical_dependency=true, WITH valid override -> valid run,
                                                     override logged
R2 role=factual_dependency, R1 empirical_dependency=false
                                                 -> valid run,
                                                    "r2_stricter" logged
R1/R2 call_failed at either stage               -> b2_run_status=
                                                    call_failed,
                                                    same as today
```

Every failure mode above resolves to an outcome the existing pipeline
already knows how to hold (`schema_invalid`, `call_failed`, `valid`) —
consistent with the instruction not to invent a new final verdict
casually.

### KEEP — explicitly unchanged from `B2_MODEL_OUTPUT_V1`

- Atomic claim decomposition and the field-coverage manifest
  mechanism — unchanged, relocated to R1, not redesigned (confirmed
  working even on H08 by the v1.3 diagnostic).
- Source provenance validation (Stage B) — untouched, upstream of R1.
- `auditor_evidence` anchor-resolver validation (exact-substring /
  normalized-match check, Layer 1) — unchanged, still runs against
  R2's output exactly as it runs against today's single-call B2
  output.
- Support vs. declaration as independent axes — unchanged, both
  remain R2's job entirely; R1 never touches either.
- The model never self-assigns the final candidate verdict —
  unchanged; `effective_verdict` remains 100% orchestrator-computed
  from R2's `claims[]`, same `compute_effective` logic as today, no
  edit needed to that function's actual verdict rule.
- Engine-blindness — both R1 and R2 remain blind to the engine
  capsule, persona label, other candidates, and Stage C — unchanged.
- `boundary_ambiguous` role semantics — unchanged, reused as-is.
- Fail-closed philosophy for unresolved structural failures —
  extended to the new R1/R2 conflict case via the existing
  `schema_invalid` mechanism, not a new category.
- Stage A/B/C boundaries, CJ-1, personas, affinity/router
  architecture — none of this is touched or reopened.

### Cost / call-count implications

Call count for the B2 stage doubles per candidate (1 → 2: R1 then R2,
sequential — R2 needs R1's fixed output as input). For the existing
30-candidate regression corpus that is 30 → 60 calls for a B2-stage
run, not a re-architecture of anything outside B2 — Stage A already
makes 4 calls per source, so this remains a modest addition in
absolute terms. Token cost is **not** a straight 2x: R1's input
deliberately excludes `source_snapshot` and all evidence (often the
largest part of the current B2 user prompt), so R1's per-call cost is
substantially smaller than a full B2 call; R2's input is close to
today's full B2 call plus a compact per-claim addition (R1's
`propositions[]`). Rough estimate, not measured: B2-stage token cost
rises by something meaningfully less than 2x, call-count and wall-
clock latency for the B2 stage roughly double (R1→R2 is a hard
sequential dependency, cannot be parallelized within one candidate).

### Likely new failure modes (stated honestly, not hidden)

- **Correlated bias, not eliminated.** R1 and R2 are (by default
  assumption, see DECISIONS below) the same model. If both stages
  share the identical blind spot — both find "a lens applied to
  established facts" persuasive — R1 emits `empirical_dependency:
  false` and R2 emits `role: interpretive_only`, and the two agree with
  each other while both being wrong. No conflict is raised; the miss
  passes through exactly as it does today. This design converts a
  purely silent, unobservable bypass into one that is cross-checkable
  *whenever the two stages disagree* — it does not guarantee they
  will disagree on every case that matters. This is the design's
  single biggest honest limitation, not a solved problem.
- **Gate-gaming via boilerplate override.** A model under instruction
  pressure to "always fill in `override_rationale`" could learn to
  produce a perfunctory, non-empty-but-substance-free rationale every
  time it wants to override — satisfying the structural check
  (non-empty string) without satisfying its intent. Mitigation
  proposed, not built: track override rate itself as a regression-
  guard metric (see below), on the theory that an implausibly high
  override rate is itself diagnostic of gaming, the same way an
  implausibly high `no_auditable_propositions=true` rate would be
  diagnostic of silent field-skipping under the existing design.
- **R1 could launder its own restatement.** Nothing stops R1 from
  writing a concrete_restatement that quietly softens the original's
  hedge to make `empirical_dependency: false` easier to justify — the
  exact "may encode" → "does encode" (or the reverse: silently
  removing a real dependency by restating it more abstractly) risk the
  design explicitly warns against. A cheap deterministic backstop
  (hedge-word presence/absence comparison between `surface_claim` and
  `concrete_restatement`) is proposed as a **soft, logged flag only**,
  not a hard gate — string-level hedge detection has enough false-
  positive risk (a restatement can legitimately drop a hedge phrase
  while preserving the hedge's substance in different words) that
  hard-gating on it risks exactly the kind of blunt-but-wrong
  automated check this project has repeatedly rejected elsewhere
  (e.g. the rejected "materiality language" and rejected trigger-word-
  only classification).
- **Two-call latency inside an already multi-stage pipeline.** Not a
  correctness risk, but worth flagging: B2 was already the pipeline's
  single most expensive semantic stage; doubling its call count
  compounds with Stage A's 4 calls and Stage C's comparison call in
  any wall-clock budget calculation for a future production version.

### Generic schema-level worked example (invented claims, not from any regression fixture)

```
Candidate field (engine_move): "The badge system encodes an assumption
that returning staff already possess equivalent competency to newly
certified staff."

R1 output (propositions[], one entry):
{
  "claim_id": "g1",
  "surface_claim": "The badge system encodes an assumption that
                     returning staff already possess equivalent
                     competency to newly certified staff.",
  "source_field": "engine_move",
  "world_truth_question": "What would have to be true in the world for
                            this proposition to hold?",
  "requires_concrete_restatement": true,
  "concrete_restatement": "The people who designed or administer the
                            badge system actually held the belief that
                            returning staff's competency already equals
                            newly certified staff's, and built the
                            system on that belief.",
  "empirical_dependency": "true",
  "empirical_dependency_rationale": "This requires a real design intent
                            and belief on the part of the system's
                            administrators, not merely that the badge
                            system's rules happen to be consistent with
                            that assumption."
}

R2 output (claims[], consuming the above; source_snapshot in this
invented example never states administrator intent, only that
returning staff skip a step newly certified staff must complete):
{
  "claim_id": "g1",
  "claim": "The badge system encodes an assumption that returning staff
            already possess equivalent competency to newly certified
            staff.",
  "source_field": "engine_move",
  "role": "factual_dependency",
  "importance": "load_bearing",
  "support": "unsupported",
  "declaration": "undeclared",
  "declared_refs": [],
  "auditor_evidence": [
    {"excerpt": "returning staff are not required to repeat the
                 certification module", "relation": "does_not_establish_claim"}
  ],
  "problems": ["motivation_invention", "undeclared_factual_dependency"],
  "why": "The source only shows returning staff skip a step; it never
          states or implies why -- asserting a specific institutional
          belief behind that skip is unsupported design-intent
          invention.",
  "r1_agreement": "consistent",
  "override_rationale": null
}

A DISAGREEING case, same claim, showing the fail-closed path:
if R2 had instead output role="interpretive_only" here with
r1_agreement="consistent" (or omitted), the deterministic consistency
layer would reject the run: R1.empirical_dependency=true (the design-
intent claim) contradicts R2.role=interpretive_only with no override.
schema_invalid, logged, not silently resolved either way. For R2 to
legitimately call this interpretive_only, it would need to write, e.g.:
  "r1_agreement": "override",
  "override_rationale": "R1's restatement treats 'encodes an
    assumption' as necessarily a claim about administrator belief, but
    this candidate's argument only uses it as a structural description
    of what the badge system's rule effectively requires regardless of
    anyone's intent -- the argumentative force here does not depend on
    the badge system's designers having held any particular belief."
-- itself now an inspectable, second-guessable claim, not a silent one.
```

### Proposed regression plan using the existing 30 development candidates

Reuse the 30-candidate corpus (12 dev-set + 18 fresh-batch-1) and the
exact same 7 preregistered targets as claim-level authority, matched
by claim CONTENT (not `claim_id` — v2 will re-decompose under a fresh
numbering, same matching discipline already used for v1.4.1):

```
H08, H09, H17   -- still-missed targets, unfixed across v1.2/v1.3/v1.4.1
H05, H14        -- previously-fixed-then-regressed targets
H03             -- correct-catch control (must remain caught)
De Hooch/Z      -- correct-catch control, previously-fixed-then-regressed
```

**New diagnostic capability v2 unlocks, not a new pass/fail axis on
its own:** because R1's `propositions[]` is now a separately-
inspectable artifact, a first v2 regression run can report, for each
target, whether the miss (if any) is now localized to R1
(`empirical_dependency` itself wrong) or to R2 (R1 correct,
consistency layer either not exercised because R2 agreed with a wrong
R1, or exercised and overridden). This is new information the current
single-call design cannot produce at all — every prior diagnostic had
to infer "STEP 2 was bypassed" indirectly, from the *absence* of
restatement language in a free-text `why` field. v2 makes that
directly checkable: **the first thing a real regression run should
report before anything else is whether R1 alone already gets H08/H09/
H17/H14/De Hooch's `empirical_dependency` right** — if it does, the
whole remaining failure surface has been localized to R2's role
assignment/override behavior, which is a much smaller, more tractable
thing to iterate on than "the model sometimes skips a mandatory step
somewhere inside one big call."

Acceptance criteria for that future run are **not chosen here** — per
instruction, this pass is architecture, not threshold-tuning. Whatever
acceptance matrix is used should be preregistered, before any API
call, following the exact same discipline as every prior version
(frozen matrix file, hashed, `does_not_count_as_repaired_if` /
`does_not_count_as_protected_if` clauses, no partial-pass category).

### Proposed bidirectional migration-report specification

Per the required methodological correction above (existing global
guards only measured `interpretive_only`→`factual_dependency`
movement; v1.4.1 moved the opposite direction and both frozen gates
were silent on it), any future regression report for v2 — and any
future B2 regression report generally — should measure, at minimum,
all of:

```
interpretive_only -> factual_dependency      (existing direction)
factual_dependency -> interpretive_only      (the direction that
                                               actually fired in
                                               v1.4.1, previously
                                               only diagnostic)
transitions involving boundary_ambiguous     (both into and out of)
safe -> unsafe        (candidate-level effective_verdict)
unsafe -> safe        (candidate-level effective_verdict)
```

Plus, new to v2's own architecture, not applicable to prior single-
call versions:

```
r1_r2_agreement_rate            (ED consistent with ROLE, per claim,
                                  excluding ED=uncertain)
override_rate                   (fraction of ED=true claims where R2
                                  legitimately overrode, with valid
                                  rationale, to interpretive_only or
                                  boundary_ambiguous)
override_without_rationale_rate (fraction of attempted overrides that
                                  FAILED the structural check --
                                  schema_invalid instances, tracked
                                  separately since these never reach a
                                  valid run to begin with)
r2_stricter_rate                (ED=false, ROLE=factual_dependency --
                                  diagnostic only, not gated)
concrete_restatement_omission_rate (schema_invalid instances caused
                                  specifically by a missing required
                                  restatement -- the direct measure of
                                  whether the field-presence invariant
                                  itself is doing any work)
```

**No numeric threshold is chosen for any of these here.** Per
instruction: if a threshold is required before v2 can ever run against
real data, it must be frozen in a preregistered acceptance-matrix
document, before any API call, the same way every prior version's
acceptance criteria were frozen — not selected retroactively after
seeing a first result, and not inferred opportunistically from this
design pass.

### Decisions that must be made before implementation (none decided here)

1. Are R1 and R2 the same model/temperature as the current B2 call
   (`openrouter/claude-sonnet-4.6`, `temperature=0.0`)? Default
   assumption stated above (same model, both stages) so this remains
   an architecture test of the R1/R2 split itself, not confounded with
   a model change — but not confirmed as a decision.
2. Is the `requires_concrete_restatement` trigger vocabulary reused
   verbatim from the frozen v1.4.1 prompt's STEP 2 list, or does it get
   its own list for R1 specifically? Reusing verbatim avoids opening a
   new tuning surface; not decided.
3. Should a deterministic keyword scan of `surface_claim` (using that
   same trigger vocabulary) be added as a *backstop* invariant forcing
   `requires_concrete_restatement=true` regardless of R1's own
   self-report, the same way field-coverage already backstops silent
   field-skipping? Proposed as plausible, not adopted — needs its own
   false-positive-rate check against real claims before being made a
   hard gate.
4. Minimum substantiveness bar for `override_rationale` beyond
   "non-empty" (e.g. minimum length, required to reference specific
   claim content) — not decided; "non-empty" is proposed only as the
   safe floor, not the final bar.
5. Should the "other direction" (R1 `empirical_dependency=false`, R2
   `role=factual_dependency`) ever gain its own required-rationale
   gate, given this project's own history of over-classification risk
   elsewhere (e.g. `motivation_invention` false positives)? Deliberately
   left diagnostic-only for v2's first pass per ANTI-OVERCORRECTION;
   revisit only after real first-run data exists, not now.
6. Should `override_rate` (or any of the new bidirectional metrics)
   become a frozen global guard for v2's *first* acceptance run, the
   same way the existing aggregate-distribution/flip-rate caps gate
   v1.x runs? Not decided — explicitly deferred, no threshold chosen
   opportunistically in this pass.
7. Confirm R1 truly needs no context beyond the candidate's own
   claim-bearing fields (no adjacent-field context, no candidate-level
   summary) to perform atomic decomposition correctly — this repeats
   today's B2 input scope for those same fields, so likely unchanged,
   but should be confirmed rather than assumed once real drafting
   starts.

### Status

Design only. R1/R2 topology, exact schemas, the deterministic
consistency layer, failure/ambiguity behavior, and the regression/
migration-report specifications above are all proposed, none accepted
as final, none executed. No `cj2-stage-b2-v2` prompt drafted. No code
written (`cj2_b2_probe_v2*.py` does not exist). No API calls made. No
production wiring touched. `cj2-stage-b2-v1.4.1` (FAIL) remains the
frozen record of the prompt-only approach's last attempt; this section
is the proposed next architecture, not yet a decision to build it.

## B2 v2 — REVISION 2: SEMANTIC-CONFLICT WRAPPER + UNCONDITIONAL PROPOSITION CONTRACT (DESIGN ONLY, NOT EXECUTED) (2026-08-12)

**The R1/R2 topology from the section above stands.** Two real
architecture defects in that first draft are corrected here, before
anything is implemented. Everything not named below is unchanged and
not reopened: the failure diagnosis, the "why R1/R2 is the smallest
fix, checked against the code" analysis, the KEEP-unchanged list, and
the overall shape (existing atomic claims → R1 proposition contract →
R2 role/support/declaration audit → deterministic consistency layer →
existing effective-verdict machinery) all still hold. Superseded,
specifically: the earlier `requires_concrete_restatement` trigger
mechanism (removed), the earlier rule that treated an unresolved R1/R2
disagreement as `schema_invalid` (corrected below), and the earlier
`override` mechanism as something that could clear a conflict (it
never could have been allowed to — corrected below). Still no
`cj2-stage-b2-v2` prompt drafted, no code written, no API calls, no
production wiring touched.

### Correction 1 — semantic disagreement is not a schema defect

The earlier draft's deterministic invariant conflated two different
kinds of failure: **a contract violation** (the response is malformed,
incomplete, or structurally inconsistent with itself) and **a semantic
disagreement between two individually well-formed judgments** (R1 and
R2 each produced a valid, complete, internally consistent output, and
those two valid outputs simply disagree about the world). Routing the
second kind through `schema_invalid` — the same bucket as malformed
JSON or a missing field — would have hidden a genuine research finding
(how often, and on which cases, does R1's structural judgment conflict
with R2's role call) behind a label that means "the auditor's own
output was broken," which it was not. `schema_invalid` is corrected
below to mean, and only mean, an actual contract violation:

```
schema_invalid, exhaustive list for B2 v2 (nothing else triggers it):
  - malformed JSON from either the R1 or the R2 call
  - a required field absent from any R1 propositions[] entry
    (claim_id, surface_claim, world_truth_question,
     concrete_restatement, empirical_dependency -- ALL required,
     unconditionally, see Correction 2)
  - a required field absent or an illegal enum value in any R2
    claims[] entry (role/importance/support/declaration/
    declared_refs/auditor_evidence/problems/why -- unchanged
    invariants from B2_MODEL_OUTPUT_V1; plus empirical_dependency
    not in {true, false, uncertain} on the R1 side)
  - duplicate claim_id within R1's own propositions[]
  - duplicate claim_id within R2's own claims[]
  - R2's claim_id set is not IDENTICAL (as a set -- order is not
    semantically meaningful in a JSON array matched by ID, so order
    is not itself checked) to R1's claim_id set -- any claim R1
    decomposed that R2 does not audit, or any claim_id R2 audits
    that R1 never decomposed, is a genuine contract failure
  - field-coverage manifest violations (unchanged mechanism, still
    lives entirely in R1 -- one field_audits entry per expected
    field instance, no missing/extra/duplicate field, claim_ids
    cross-referenced correctly)
  - r1_agreement="override" with an empty/missing override_rationale
    (a metadata-completeness requirement, kept for research value --
    see Correction 1, closing paragraph -- but note explicitly: this
    is the ONLY thing override_rationale's presence/absence affects;
    its CONTENT never affects anything, per the fix below)
```

**If R1 and R2 are each individually schema-valid but their
*judgments* disagree, both outputs are preserved unedited and the
disagreement is exposed as its own deterministic wrapper state,
`R1_R2_SEMANTIC_CONFLICT`** — not a new model-authored verdict (the
model authors nothing here; this state is computed entirely by the
orchestrator from two already-emitted, already-valid fields), and not
folded into `schema_invalid`.

**Mapping the conflict into the existing verdict machinery — no new
final verdict invented.** `compute_effective`'s existing per-claim
branch (interpretive_only/boundary_ambiguous → fixed status;
factual_dependency → derived from support+evidence-validation) gets
exactly one new branch inserted *before* it, for the one direction that
matters for safety:

```
if R1_R2_SEMANTIC_CONFLICT (the fail-closed direction only --
   see Correction 5 for which direction that is):
    effective_status = "unresolved_semantic_conflict"
    # NEW, orchestrator-authored label -- but it ROUTES exactly like
    # the existing "uncertain"/"audit_unresolved" statuses already
    # do: it sets any_ambiguous=True, never any_unsafe=True. Given a
    # distinct name (not silently relabeled "uncertain") purely so a
    # future report can tell "the auditor was genuinely unsure" apart
    # from "R1 and R2 disagreed" -- same routing, better diagnostics,
    # the smallest change that preserves the distinction without
    # inventing a new bucket in the aggregation rule itself.
else:
    <existing role/support-based effective_status logic, UNCHANGED>
```

Candidate-level aggregation (`any_unsafe → unsafe; elif any_ambiguous →
ambiguous; else safe`) is **not edited at all** — `unresolved_semantic_
conflict` is simply one more value that satisfies the existing
`effective_status in {"uncertain", "audit_unresolved"}` check, which
becomes `effective_status in {"uncertain", "audit_unresolved",
"unresolved_semantic_conflict"}`, a one-line extension, not a redesign.
A candidate with a genuine R1/R2 conflict on any claim becomes
`ambiguous` — withheld from Stage C and surfaced for review, the
existing fail-closed treatment already reserved for exactly this kind
of "the audit did not cleanly resolve" case — never `safe` (the false-
safe this whole redesign exists to prevent) and never asserted `unsafe`
on the strength of a disagreement alone (R2 was never given the chance
to actually finish a support/declaration audit on a claim whose role
is itself contested).

**`override_rationale` cannot clear the conflict, by construction, not
by policy.** The deterministic check above reads only `R1.propositions
[claim_id].empirical_dependency` and `R2.claims[claim_id].role` — it
never reads `r1_agreement` or `override_rationale` at all. Those two
fields are retained on R2's output purely as auxiliary, model-authored
commentary: useful for a human reviewing *why* R2 disagreed, and useful
as a second, softer diagnostic (does R2 even recognize its own
disagreement — a mismatch between R2's self-reported `r1_agreement=
consistent` and a conflict the deterministic layer finds anyway is
itself worth logging) — but with zero causal path to the verdict. This
directly forecloses the exact scenario flagged: *R1 catches a factual
dependency → R2 writes a fluent override paragraph → the claim silently
becomes `interpretive_only`.* That path does not exist in this design,
because clearing the conflict is not a thing any field, free-text or
otherwise, is capable of doing.

### Correction 2 — no restatement trigger, no escape hatch

The earlier `requires_concrete_restatement` boolean is **removed
entirely** — it was itself a bypass point (a model that wants to skip
the restatement can simply self-report `false`), reintroducing exactly
the failure this design exists to close, just moved one field over.

**R1 performs the full proposition contract for every atomic claim,
unconditionally.** No conditional field, no keyword trigger, no
subject-type carve-out, no model judgment call about whether
restatement is "necessary." Required on every `propositions[]` entry,
with no `not_applicable` value permitted for any of them:

```
claim_id                 (unchanged decomposition output)
surface_claim             (unchanged decomposition output)
world_truth_question      REQUIRED, non-empty, every claim
concrete_restatement      REQUIRED, non-empty, every claim
empirical_dependency      REQUIRED, one of {true, false, uncertain},
                           every claim
```

Optional: a short rationale sentence (kept for readability of the
output, not schema-load-bearing).

**Already-concrete claims get an identity or near-identity
restatement, and that is correct, not a shortcut:**

```
surface_claim:        "The committee rejected the application on Tuesday."
world_truth_question: "Did the committee actually reject the
                        application, and did that happen on Tuesday?"
concrete_restatement: "The committee rejected the application on Tuesday."
empirical_dependency: "true"
```

The point of the contract is not that every claim must be transformed
— it is that every claim passes through the *same machine-checkable
step*, so that "this claim didn't need restating" and "this claim
needed restating and the model silently skipped it" are no longer
indistinguishable from the outside, which is exactly what the trigger
boolean failed to fix.

### Correction 3 — R1 input contract, checked against what already exists

R1 remains fully evidence-blind: no `source_snapshot`, no canonical
`cj1:aN` evidence, no candidate-declared evidence, no engine identity,
no persona, no disability angle, no router/affinity information. This
was already the design in Revision 1 and is unchanged.

**Checked against the existing code, not assumed:** the question of
whether an isolated atomic claim loses the "one way to read X" vs. "X
actually happened because" distinction does not require a new
mechanism. `cj2_b2_probe_v1_4_1.py`'s `build_b2_user` already sends
each field's *complete text* (`text: "{candidate.get(...)}"`) to the
single existing B2 call, in the same prompt as every other field on
the candidate at once — decomposition already happens against full
field text, never against a pre-clipped fragment, and this has never
been the source of any diagnosed failure in the v1.x history. **R1
inherits this unchanged**: its input is the same set of complete
field texts (`additional_source_observations[].observation`,
`engine_move`, `seed_engagement`, `interpretive_inference`,
`conceptual_shift` if present, `claimed_contribution`), given together
in one prompt exactly as today, minus everything evidence-related.
There is no separate "atomic claim extraction" step upstream of R1 to
preserve context from — **R1 is the first and only place decomposition
happens**, doing so, as today, against the complete parent text. No
new context-preservation mechanism is introduced because none is
needed; documented here specifically to avoid inventing one.

One consequence worth being explicit about: `claim_id` and
`surface_claim` are *outputs* of R1's own decomposition, not inputs to
it — R1 does not receive already-atomized claims and add metadata to
them; it receives full field text, decomposes it (unchanged mechanism),
and attaches the proposition-contract fields to each claim it produces
in the same pass. This is a single R1 call per candidate, not a
decomposition call followed by a separate per-claim contract call.

### Correction 4 — same model for the first structural test, no independence claimed

R1 and R2 both use `openrouter/claude-sonnet-4.6` at `temperature=0.0`
— identical to every prior B2 call — for the first structural test.
**This is a decision, not a default left implicit:** the experimental
variable this first test is designed to isolate is the *structural
externalization* of the proposition contract (does forcing the
restatement into a separate, required, cross-checked artifact change
the failure rate), not a simultaneous model substitution, which would
confound the result. **Recorded explicitly as a limitation, not a
caveat to gloss past: same-model R1/R2 may share correlated semantic
bias, and no independence between the two calls is claimed or implied
anywhere in this design.** If R1 and R2 happen to share the identical
blind spot — both find a given proposition's "lens" framing persuasive
— R1 emits `empirical_dependency: false`, R2 emits `role:
interpretive_only`, the two agree with each other while both being
wrong, and `R1_R2_SEMANTIC_CONFLICT` never fires, because there is no
disagreement to detect. **A cross-model R1/R2 experiment is a
legitimate future direction, but only if the same-model structural
version, once actually run, remains unreliable** — not adopted now, to
keep this first test a clean single-variable comparison against the
v1.x prompt-only history.

### Correction 5 — directional consistency, fully enumerated

The deterministic consistency check reads only two fields — never
`r1_agreement`, never `override_rationale` — and is exhaustive over
the full 3×3 space of `(empirical_dependency, role)` combinations:

| R1 `empirical_dependency` | R2 `role` | outcome |
|---|---|---|
| `true` | `factual_dependency` | consistent — normal pipeline (R2's support/declaration axis governs) |
| `true` | `boundary_ambiguous` | consistent — both flag concern; not a conflict (role is already `boundary_ambiguous`, which already routes to `ambiguous`); logged as a transition |
| `true` | `interpretive_only` | **`R1_R2_SEMANTIC_CONFLICT` — FAIL-CLOSED.** `effective_status = "unresolved_semantic_conflict"` regardless of `r1_agreement`/`override_rationale`. This is the direction that can create a false-safe, and the entire reason this correction exists. |
| `false` | `interpretive_only` | consistent — normal pipeline |
| `false` | `boundary_ambiguous` | consistent — logged as a transition, not a conflict |
| `false` | `factual_dependency` | **`r1_r2_escalation`** — R2 is stricter than R1. NOT gated, NOT required to carry an override rationale, NOT automatically failed. Normal pipeline proceeds using R2's role/support/declaration as authoritative (R2 has evidence access R1 deliberately never gets). Logged for the migration report, evaluated for overcorrection risk over time, not rejected on sight — R1's structural pass working without evidence is exactly the kind of gap a legitimately stricter R2 should be able to close. |
| `uncertain` | any | `r1_uncertain_resolved` — R1 never committed to a value; R2 resolves freely. Logged with which role it resolved to, no conflict, no escalation label. |

Only one cell in this table is fail-closed. Every other cell resolves
through the existing pipeline unchanged, with the disagreement (or
agreement) recorded for the migration report below — consistent with
the instruction not to reject the "R2 stricter" direction automatically
and to treat it as something to evaluate for overcorrection, not a
default failure.

### Correction 6 — R2 cannot reshape R1's claim set, structurally, not just by invariant

**Refinement beyond what was asked, in the direction of "smallest
compatible design":** rather than having R2 re-emit each claim's text
and then deterministically checking that text against R1's for exact
equality (workable, but adds an entire invariant-check category whose
only job is catching accidental or deliberate paraphrase), **R2's
`claims[]` entries do not carry a `claim` text field at all.** The
claim's text lives in exactly one place — R1's `propositions[]` — and
is never duplicated downstream. R2's output is keyed by `claim_id`
only; the orchestrator joins `R1.propositions[claim_id]` with
`R2.claims[claim_id]` to reconstruct the full record. This does not
remove any capability (R2 still *reads* the claim text, from R1's
output, as part of its input) — it removes an entire class of "text
was quietly reshaped" risk by removing the field that could be
reshaped, rather than policing it after the fact. The remaining,
irreducible structural check is the claim_id-set-equality rule already
listed under Correction 1's `schema_invalid` enumeration: R2 must
produce exactly one `claims[]` entry per `claim_id` R1 emitted, no
more, no fewer, no substitutions.

```
R2_MODEL_OUTPUT_V2

{
  "claims": [
    {
      "claim_id": "c1",                 // MUST be a claim_id R1 emitted;
                                          // R2's claim_id SET must equal
                                          // R1's claim_id SET exactly
      "role": "interpretive_only" | "factual_dependency" |
              "boundary_ambiguous",      // unchanged
      "importance": "load_bearing" | "supporting" | "incidental",
      "support": "supported" | "unsupported" | "not_required" |
                 "uncertain",             // unchanged
      "declaration": "declared" | "undeclared" | "not_applicable" |
                     "uncertain",         // unchanged
      "declared_refs": ["cj1:a1"] | ["obs:1"] | [],   // unchanged
      "auditor_evidence": [ {"excerpt": "...",
                              "relation": "supports_claim" |
                                          "does_not_establish_claim"} ],
      "problems": [ ... ],                // unchanged enum, no new
                                            // values added by this design
      "why": "one sentence",              // unchanged
      "r1_agreement": "consistent" | "override",
      // diagnostic self-report ONLY -- never read by the deterministic
      // consistency check (Correction 1)
      "override_rationale": "..." | null
      // required non-empty iff r1_agreement="override" (a metadata-
      // completeness requirement -- absence is schema_invalid); its
      // CONTENT is never consulted by anything downstream
    }
  ]
}
```

### Corrected R1 schema (full, superseding Revision 1's `R1_MODEL_OUTPUT_V1`)

```
R1_MODEL_OUTPUT_V2

{
  "field_audits": [
    { "source_field": "...", "claim_ids": ["c1", "c2"],
      "no_auditable_propositions": false }
    // UNCHANGED mechanism/invariants from B2_MODEL_OUTPUT_V1
  ],
  "propositions": [
    {
      "claim_id": "c1",
      "surface_claim": "the proposition, stated plainly, in the
                         candidate's own expressed strength/hedge",
      "source_field": "engine_move",
      "world_truth_question": "one sentence -- what would have to be
                                true in the world for this proposition
                                to hold?",
      "concrete_restatement": "the nearest concrete world-claim,
                                without strengthening the original's
                                hedge -- REQUIRED for every claim, no
                                exceptions; an identity/near-identity
                                restatement is correct and sufficient
                                when the surface claim is already
                                concrete",
      "empirical_dependency": "true" | "false" | "uncertain",
      "rationale": "one sentence"   // OPTIONAL
    }
  ]
}
```

`world_truth_question`, `concrete_restatement`, and
`empirical_dependency` are now unconditionally required on every
`propositions[]` entry — there is no field, flag, or enum value that
permits skipping any of them for any claim.

### Post-R1/R2 pipeline, corrected (supersedes Revision 1's failure-behavior table)

```
Layer 0 -- run status (deterministic, before anything else is trusted):
  call_failed      if either the R1 or R2 API call itself fails or
                    returns unparseable output
  schema_invalid   if R1 or R2 parses but violates ANY invariant in
                    Correction 1's exhaustive list (malformed/missing
                    field, illegal enum, duplicate/mismatched claim_id
                    set, field-coverage violation, missing override
                    rationale when r1_agreement=override)
  valid            otherwise -- BOTH R1 and R2 individually well-formed
                    AND R2's claim_id set exactly equals R1's

Layer 1 -- auditor-evidence provenance validator (unchanged mechanism,
  still runs only against R2's auditor_evidence vs. source_snapshot,
  only if run_status=valid, still wraps, never mutates)

Layer 1.5 (NEW) -- R1/R2 semantic consistency layer (deterministic,
  wraps, never mutates, computed ONLY from R1.empirical_dependency and
  R2.role per Correction 5's table -- never reads r1_agreement or
  override_rationale):
    per claim_id: consistent | r1_r2_escalation | r1_uncertain_resolved
                  | R1_R2_SEMANTIC_CONFLICT
    (first three: diagnostic, logged, do not alter effective_status;
     last one: alters effective_status per Correction 1)

Layer 2 -- effective_status / effective_verdict (unchanged formula,
  ONE new effective_status value inserted ahead of the existing
  role/support branch, per Correction 1)
```

### Corrected generic worked example (invented claims, replacing Revision 1's example)

```
Candidate field (engine_move): "The badge system encodes an assumption
that returning staff already possess equivalent competency to newly
certified staff."

R1 output (propositions[], one entry -- UNCONDITIONAL contract, no
trigger consulted):
{
  "claim_id": "g1",
  "surface_claim": "The badge system encodes an assumption that
                     returning staff already possess equivalent
                     competency to newly certified staff.",
  "source_field": "engine_move",
  "world_truth_question": "What would have to be true in the world for
                            this proposition to hold?",
  "concrete_restatement": "The people who designed or administer the
                            badge system actually held the belief that
                            returning staff's competency already equals
                            newly certified staff's, and built the
                            system on that belief.",
  "empirical_dependency": "true",
  "rationale": "This requires a real design intent and belief on the
                part of the system's administrators, not merely that
                the rules happen to be consistent with that belief."
}

CASE A -- consistent, safety-relevant direction resolved correctly:
R2 output:
{
  "claim_id": "g1",
  "role": "factual_dependency",
  "importance": "load_bearing",
  "support": "unsupported",
  "declaration": "undeclared",
  "declared_refs": [],
  "auditor_evidence": [
    {"excerpt": "returning staff are not required to repeat the
                 certification module", "relation": "does_not_establish_claim"}
  ],
  "problems": ["motivation_invention", "undeclared_factual_dependency"],
  "why": "The source only shows returning staff skip a step; it never
          states why -- asserting a specific institutional belief
          behind that skip is unsupported design-intent invention.",
  "r1_agreement": "consistent",
  "override_rationale": null
}
-- consistency layer: R1.empirical_dependency=true, R2.role=
   factual_dependency -> consistent. Normal pipeline: effective_status
   derives from support/auditor_evidence exactly as B2_MODEL_OUTPUT_V1
   already specifies. No change from Revision 1's behavior here.

CASE B -- the exact scenario this correction exists to prevent:
R2 output (same claim, hypothetically):
{
  "claim_id": "g1",
  "role": "interpretive_only",
  "importance": "supporting",
  "support": "not_required",
  "declaration": "not_applicable",
  "declared_refs": [],
  "auditor_evidence": [],
  "problems": [],
  "why": "This reads as a structural description of what the badge
          system's rule effectively requires, not a claim about
          administrator belief.",
  "r1_agreement": "override",
  "override_rationale": "R1's restatement treats 'encodes an
    assumption' as necessarily a claim about administrator belief, but
    this candidate's argument only uses it as a structural description
    -- the argumentative force here does not depend on the designers
    having held any particular belief."
}
-- consistency layer: R1.empirical_dependency=true, R2.role=
   interpretive_only -> R1_R2_SEMANTIC_CONFLICT, regardless of the
   override_rationale's content or even its presence. effective_status
   = "unresolved_semantic_conflict" -> any_ambiguous=True for this
   candidate. R2's own role, R1's own empirical_dependency, and the
   full override_rationale text are ALL preserved, unmutated, visible
   in the stored record -- nothing is silently resolved to safe, and
   nothing is silently resolved to unsafe either. A human reviewing
   this candidate sees both readings side by side and can judge R2's
   argument on its merits -- the deterministic layer's job was only to
   make sure that judgment happens visibly, not to make it.

CASE C -- R2 stricter, not gated:
Hypothetical claim where R1.empirical_dependency="false" (R1 judged
the claim's own wording carries no real-world dependency) but R2,
having seen the actual source_snapshot, classifies it
factual_dependency/unsupported anyway. Consistency layer: r1_r2_
escalation -- logged, NOT blocked, NOT required to carry an override
rationale. The candidate's effective_verdict is computed normally from
R2's own support/declaration axis, exactly as if no R1 output existed
at all for this claim.
```

### Bidirectional migration-report specification (revised, fully enumerated)

**Two distinct comparisons, not to be conflated:**

**(a) Within-run R1/R2 consistency** (new to v2's own architecture,
computed from Correction 5's table, per candidate and aggregated
across the corpus):

```
count and rate of: consistent
count and rate of: r1_r2_escalation          (diagnostic, direction B)
count and rate of: r1_uncertain_resolved
count and rate of: R1_R2_SEMANTIC_CONFLICT   (fail-closed, direction A)
self-report mismatch rate: R2 states r1_agreement="consistent" but the
  deterministic layer finds R1_R2_SEMANTIC_CONFLICT anyway (a second,
  softer diagnostic: does R2 even recognize its own disagreement)
```

**(b) Cross-version migration** (generalizes the existing v1.2-baseline
global guards -- corrects the METHODOLOGICAL FINDING recorded earlier
in this document that those guards only ever measured drift toward
`factual_dependency` and were silent on v1.4.1's actual, opposite-
direction regression). Comparison is always against the frozen v1.2
baseline, matched by claim CONTENT not claim_id (unchanged convention);
the v2 side of the comparison uses the EFFECTIVE role -- R2's raw role,
EXCEPT a claim under `R1_R2_SEMANTIC_CONFLICT` is compared as
`boundary_ambiguous` for this purpose (the bucket it effectively
resolves into), with R2's raw role additionally reported alongside it
so the raw-vs-effective distinction is never lost:

```
Role-level (v1.2 -> v2 effective role), full 3x3 minus diagonal, all
six directions counted separately, none bundled:
  interpretive_only  -> factual_dependency
  factual_dependency -> interpretive_only
  interpretive_only  -> boundary_ambiguous
  factual_dependency -> boundary_ambiguous
  boundary_ambiguous -> interpretive_only
  boundary_ambiguous -> factual_dependency

Candidate-level (v1.2 -> v2 effective_verdict), full 3x3 minus
diagonal, all six directions counted separately:
  safe      -> unsafe
  unsafe    -> safe
  safe      -> ambiguous
  unsafe    -> ambiguous
  ambiguous -> safe
  ambiguous -> unsafe
```

Optionally, diagnostically, the same two tables computed against the
v1.4.1 baseline instead of v1.2 (v1.4.1 is the most recent frozen
prompt-only attempt) -- not a substitute for the v1.2 comparison, an
addition to it.

**No numerical threshold is chosen for any count, rate, or cell in
either table here.** Per instruction: any threshold needed before a
real v2 run must be frozen in a preregistered acceptance-matrix
document, before any API call, with a rationale stated in advance of
seeing the result -- not selected after, and not inferred
opportunistically from this design pass. This is a metrics design, not
a threshold-tuning pass.

### API-call / token-cost estimate (unchanged from Revision 1's estimate, restated)

Two calls per candidate (R1 then R2, sequential — R2 requires R1's
fixed `propositions[]` as input). 30-candidate corpus: 30 → 60 calls
for a B2-stage run. R1's input excludes `source_snapshot` and all
evidence (typically the largest part of today's single B2 prompt), so
per-call token cost is asymmetric — R1 cheaper than a full B2 call, R2
close to today's full B2 call plus a compact `propositions[]` addition.
Net token cost for the B2 stage: meaningfully less than 2x; call count
and wall-clock latency for the stage: roughly 2x (hard sequential
dependency, not parallelizable within one candidate). Same order-of-
magnitude estimate as Revision 1 — nothing in these corrections changes
the cost picture materially, since neither correction adds a third
call.

### New/updated risks after these corrections, stated honestly

- **Identity-restatement laundering (NEW, replaces the old trigger-
  bypass risk as the primary concern).** Removing the trigger boolean
  closes one bypass but opens an adjacent one: nothing stops R1 from
  writing `concrete_restatement` as a verbatim or near-verbatim copy of
  `surface_claim` for a genuinely conceptual, metaphorical claim that
  actually needed real restating — trivially satisfying the "always
  produce a restatement" requirement without doing the work the
  requirement exists to force. Proposed, not adopted: track the
  identity-restatement rate (fraction of claims where `concrete_
  restatement` is exactly or near-exactly equal to `surface_claim`) as
  a new diagnostic-only metric for the first real regression run — no
  threshold chosen now, consistent with the instruction above; a
  future acceptance matrix could freeze one only after seeing what
  "normal" looks like on legitimately-already-concrete claims (there
  are true positives, e.g. the "committee rejected the application"
  example — the rate cannot be zero by design).
- **`override_rationale` may degrade to boilerplate precisely because
  it no longer matters (NEW, direct consequence of Correction 1).**
  Once the field has zero causal effect on the verdict, R2 has less
  functional incentive to write a careful rationale than it did under
  Revision 1's design. This is a data-quality risk (the diagnostic
  value of the field may erode), not a safety-bypass risk (removing
  the field's power is exactly what closes the bypass) — worth naming
  so it is not mistaken for a regression if observed.
- **Correlated bias, same-model, not eliminated (restated from
  Revision 1, now a decided limitation per Correction 4, not merely a
  caveat).** A shared blind spot between R1 and R2 produces no
  conflict signal at all — the miss passes through exactly as it does
  under the current single-call design. `R1_R2_SEMANTIC_CONFLICT` can
  only ever catch disagreements the two calls actually have; it cannot
  catch an error both calls make identically.
- **Whether `importance` should modulate the fail-closed response is
  unresolved.** Today, ANY claim landing in `R1_R2_SEMANTIC_CONFLICT`
  forces the whole candidate to `ambiguous`, regardless of whether that
  claim is `load_bearing` or `incidental` — consistent with the
  existing, unchanged principle that `importance` is diagnostic only,
  never an exemption (an incidental fabrication is still a
  fabrication; by direct extension, an incidental conflict is still a
  conflict). Not revisited here, flagged as a live question for anyone
  drafting the actual prompts.

### KEEP — reconfirmed unchanged after these corrections

Everything from Revision 1's KEEP list still holds, unedited: atomic
decomposition mechanism, Stage B source provenance, the auditor-
evidence anchor-resolver (Layer 1), support vs. declaration as
independent axes, the model never self-assigning the final candidate
verdict, engine-blindness for both R1 and R2, `boundary_ambiguous` role
semantics, Stage A/B/C boundaries, CJ-1, personas, and the affinity/
router architecture. Additionally, per this pass's explicit scope: the
`problems` enum gains no new value (the conflict mechanism is its own
separate layer, not a claim-level `problems` tag) — no demonstrated
schema need for one emerged from these corrections.

### Decisions resolved by this pass (removed from the open list)

- Same model for R1/R2 on the first structural test — **decided**,
  Correction 4.
- Restatement-trigger keyword list / deterministic backstop — **moot**,
  the trigger itself is removed, Correction 2.
- Claim-set-identity enforcement mechanism — **decided**: no redundant
  `claim` text field on R2's output at all (Correction 6), claim_id-
  set equality is the only structural check needed.
- Override-rationale minimum bar — **decided, narrowly**: non-empty
  required when `r1_agreement="override"` (a `schema_invalid` check);
  no minimum length or substantiveness bar beyond that, since content
  is never consulted by anything deterministic.
- Whether the "R2 stricter" direction (B) gets its own gate — **decided:
  no**, diagnostic-only for v2's first pass, per Correction 5,
  consistent with the instruction not to auto-reject that direction.

### Decisions still open after this pass

1. Whether `importance` should ever modulate the fail-closed response
   to `R1_R2_SEMANTIC_CONFLICT` (see risks above) — not resolved.
2. Whether the identity-restatement rate, once measured on a real run,
   should become a frozen threshold in a future acceptance matrix, and
   what that threshold should be — explicitly deferred, no number
   chosen now.
3. Whether a deterministic hedge-word-presence sanity check (surface
   claim hedged, restatement flatly unhedged, or vice versa) is worth
   adding as a soft, diagnostic-only flag — proposed in Revision 1,
   not decided, not reopened or resolved by these corrections.
4. Whether the cross-version migration report should be computed
   against v1.2 only, or v1.2 and v1.4.1 both as standing practice —
   proposed as "both, diagnostically" above, not settled as a
   requirement.
5. Whether R1's `field_audits` mechanism needs any adjustment now that
   its consumer (R2) no longer receives claim text redundantly through
   R2's own output — current answer is no (field_audits was always
   R1-only, unaffected by removing a field from R2's schema), but
   worth a second look once actual prompt drafting starts rather than
   assumed settled here.

### Status

Design only, corrected. R1/R2 topology unchanged from Revision 1's
motivation and analysis; the semantic-conflict wrapper, the
unconditional proposition contract, the R1 input-context confirmation,
the same-model decision, the fully-enumerated directional-consistency
table, the claim-set-identity mechanism, and the revised bidirectional
migration-report specification are all proposed here, none accepted as
final beyond this design pass, none executed. No `cj2-stage-b2-v2`
prompt drafted. No code written (`cj2_b2_probe_v2*.py` does not exist).
No API calls made. No Trident use. No 30-candidate regression run. No
cross-publisher batch collected. No Stage C run. `cj2-stage-b2-v1.4.1`
(FAIL) remains the frozen record of the prompt-only approach's last
attempt.

## B2 v2 — IMPLEMENTATION (2026-08-12, structural harness built, NOT executed)

Proceeded from DESIGN to IMPLEMENTATION on Revision 2's frozen architecture
(the "## B2 v2 — REVISION 2" section immediately above this one, unchanged).
**No API call has been made against either prompt. No production code or
production wiring touched. `cj2-stage-b2-v1.4.1` (FAIL) is unmodified and
remains the frozen record of the prompt-only approach's last attempt.**

**Files added (all new, none replacing anything):**
- `automation/.probe_fixtures/cj2-b2-v2/frozen_prompts/cj2-stage-b2-v2-r1.txt`
  — R1 system prompt. Evidence-blind proposition analyst: unconditional
  world-truth-test + concrete-restatement contract for every atomic claim
  (no trigger field, no skip condition, matching Correction 2 exactly),
  explicit hedge-preservation instruction (`concrete_restatement` must not
  strengthen or weaken the surface claim's modality — the direct
  implementation of "R1 must preserve candidate modality"), reuses the
  unchanged atomic-decomposition and field-coverage mechanics verbatim from
  `cj2-stage-b2-v1.4.1.txt` where the design says KEEP.
- `automation/.probe_fixtures/cj2-b2-v2/frozen_prompts/cj2-stage-b2-v2-r2.txt`
  — R2 system prompt. Full-evidence role/support/declaration auditor,
  reusing v1.4.1's own role-decision procedure, hedge-handling section,
  support-strengthening 7-pattern checklist, declaration lineage, factual
  authority, auditor-evidence copy discipline, importance, and problems
  sections verbatim (all explicitly KEEP per the design). New: audits a
  FIXED claim_id set handed down from R1 (no decomposition of its own, no
  `claim` text field, no `field_audits` — the design's Correction 6, R2 is
  keyed by `claim_id` only); new `r1_agreement`/`override_rationale`
  fields, explicitly told the rationale is read by researchers but has zero
  causal effect on the verdict, per Correction 1's closing paragraph.
- `automation/cj2_b2_v2_probe.py` — the harness. Implements, matching the
  design section-by-section: R1 input construction (`build_r1_user`,
  strictly evidence-blind — no `source_snapshot`, no seed, no declared
  refs); R1 structural validator (`validate_r1` — field coverage, unchanged
  mechanism, PLUS the new per-proposition contract check: `world_truth_
  question`/`concrete_restatement` required non-empty on every entry,
  `empirical_dependency` in `{true,false,uncertain}`, no `not_applicable`
  escape value anywhere, per Correction 2); R2 input construction
  (`build_r2_user` — full evidence exactly as `cj2_b2_probe_v1_4_1.build_
  b2_user`, plus a new FIXED PROPOSITION SET section listing R1's contract
  per claim_id); R2 structural validator (`validate_r2` — claim-id-set-
  equality against R1's set is the schema_invalid check per Correction 6,
  role/support/declaration invariants reused byte-for-byte from
  `validate_claim_structure`, plus the new `r1_agreement`/`override_
  rationale` presence-not-content check per Correction 1); the auditor-
  evidence provenance layer (`validate_auditor_evidence`, unchanged
  mechanism, reused via the same `cj1_v3_anchor_resolver.resolve_anchor`
  import); the NEW Layer 1.5 consistency computation (`compute_consistency`
  — reads ONLY `R1.empirical_dependency`/`R2.role`, never `r1_agreement`/
  `override_rationale`, implementing Correction 5's full 3×2-plus-uncertain
  table exhaustively); the corrected effective-verdict layer
  (`compute_effective_v2` — one new branch for `unresolved_semantic_
  conflict` inserted ahead of the existing role/support branch, per
  Correction 1, candidate-level aggregation otherwise byte-identical to
  `compute_effective`); the full `run_candidate_pipeline_v2` (Layer 0
  run_status at both R1 and R2, R2 never called if R1 is schema_invalid —
  there is no fixed claim set to hand it); and the bidirectional-migration
  utilities (`within_run_consistency_report`, `self_report_mismatch_
  report`, `role_migration_table`, `verdict_migration_table`,
  `identity_restatement_rate`) implementing both tables from the design's
  "Bidirectional migration-report specification" section, generically
  (no fixture-specific matching hardcoded, since no real v2 output exists
  yet to match against). `main()` deliberately raises rather than running,
  so importing this module can never accidentally trigger a live call.
- `automation/cj2_b2_v2_static_tests.py` — deterministic test suite, ZERO
  network calls, run and passing (51/51 checks) as of this implementation
  pass. Covers, as invented generic material (none copying H03/H05/H08/
  H09/H14/H17/De Hooch-Z wording): concrete factual, pure interpretive,
  hedged factual, hedged interpretive, institutional intent, individual
  intent, causal attribution, measurement/modal hardening, population
  generalization, identity restatement, missing R1 field, illegal enum,
  claim-set mismatch (R2 omits/adds/duplicates a claim_id relative to R1),
  the R1=true/R2=interpretive_only conflict (asserting the effective
  verdict is `ambiguous`, never `safe` — the specific false-safe this
  design exists to prevent, and that an elaborate `override_rationale`
  cannot clear it), the R1=false/R2=factual_dependency escalation
  (asserting it is NOT gated and proceeds to a normal `unsafe` verdict),
  `boundary_ambiguous` reached from either R1 value (both `consistent`,
  never a conflict), `r1_uncertain_resolved`, missing/stray `override_
  rationale`, R1 field-coverage violations, and an auditor-evidence
  provenance case distinguishing `audit_unresolved` (ambiguous) from the
  unchanged, inherited `declaration=undeclared`-forces-`unsafe` rule (a
  real distinction the first draft of this test suite got wrong — a bad
  auditor citation alone does not force `unsafe`; an undeclared factual
  dependency does, independent of citation quality — corrected and both
  cases are now tested explicitly, since they look similar but are not).
- `automation/.probe_fixtures/cj2-b2-v2/acceptance-matrix-v2-preregistered.json`
  — the preregistered acceptance specification, written before any API
  call, per instruction. Carries forward the EXACT 7 targets/protects from
  `cj2-b2-v1.4.1-regression/acceptance-matrix-v1.json` (H08/H09/H17 misses,
  H05/H14/De-Hooch-Z-protects, H03 control) verbatim — no target added,
  none dropped, none reworded. Adds a `scoring_vocabulary_v2` distinguishing
  three outcomes per target instead of v1.x's binary pass/fail:
  `REPAIRED` (counts), `FLAGGED_NOT_RESOLVED` (a claim landing in
  `R1_R2_SEMANTIC_CONFLICT` — R1 caught it, R2 still missed it, the
  candidate is withheld as ambiguous rather than let through safe — does
  NOT count as repaired, but is reported as its own diagnostic category,
  distinct from a flat `MISS` where R1 also missed it), and `MISS`. Global
  guards (≤15pp aggregate cap, ≤20% flip-rate cap) carried forward
  UNCHANGED against the v1.2 baseline, now computed via v2's EFFECTIVE role
  (a `R1_R2_SEMANTIC_CONFLICT` claim compares as `boundary_ambiguous`, per
  the design doc's own convention) — plus the v1.4.1 regression's own
  after-the-fact finding (the two capped guards are structurally blind to
  drift AWAY from `factual_dependency`) carried forward as a required,
  uncapped diagnostic measurement, not silently dropped. New v2-only
  diagnostics (within-run consistency rates, self-report-mismatch rate,
  identity-restatement rate, `FLAGGED_NOT_RESOLVED` count) are specified
  with explicitly NO threshold chosen, per instruction not to select
  thresholds before seeing real output. An explicit `explicitly_not_
  authorized_by_this_file` list closes the file, mirroring every prior
  acceptance-matrix file's own discipline.

**What was explicitly NOT done, per instruction:** no API call against
`cj2-stage-b2-v2-r1.txt` or `-r2.txt`; no 30-candidate regression run (the
harness and the 30-candidate corpus paths are wired in `cj2_b2_v2_probe.py`'s
`_iter_dev_candidates`/`_iter_fresh_candidates`, but `main()` refuses to run);
no cross-publisher evaluation material spent; no Stage C changes; no
production wiring; no tuning of R1/R2 in response to anything (there is
nothing to tune in response to yet — no run has happened). Trident/CLIProxy
were not used in this pass.

**Open implementation decisions inherited unresolved from Revision 2,
still not resolved here** (per instruction — these are for whoever
authorizes and reviews the actual run, not decided opportunistically now):
whether `importance` should ever modulate the fail-closed
`R1_R2_SEMANTIC_CONFLICT` response; whether the identity-restatement rate
should become a frozen threshold once real data exists; whether a
deterministic hedge-word sanity check between `surface_claim` and
`concrete_restatement` is worth adding; whether the cross-version migration
report should standing-practice compare against v1.2 and v1.4.1 both.

## B2 v2 — 30-CANDIDATE REGRESSION RUN EXECUTED, RESULT: FAIL (2026-08-12)

Explicitly authorized by the user (after an AskUserQuestion on the trident
execution-path conflict — see below — and a follow-up clarification message
confirming trident-as-execution-only is the established methodology for this
track, matching v1.2/v1.3/v1.4.1). Full artifacts, hashes, and per-target
detail in `automation/.probe_fixtures/cj2-b2-v2-regression/`
(`b2-v2-regression-comparison.json`, `b2-v2-regression-report.md`,
`b2-v2-regression-corpus-manifest.json`, `pre-run-identity-retroactive.json`,
`regression_results/` — 30 per-candidate raw+parsed outputs plus
`run_log.json`/`all_results.json`).

**Execution methodology, disclosed precisely:** CLIProxyAPI is localhost-only
on trident; this session runs on the Mac. The trident execution-path question
was surfaced to the user explicitly rather than assumed either way (a prior
instruction earlier in this same B2 track had said "do not use trident for
model calls," which conflicts with every prior B2 regression's own
methodology). User selected "run on trident," then sent a follow-up
clarifying that the earlier prohibition was scoped to the design/
implementation/static-test pass (where no execution was authorized at all),
not a permanent ban — trident-as-execution-only, local-repo-as-canonical, is
the established methodology for this track. Local repo hashes verified
byte-identical against trident BEFORE copying, frozen files re-verified
byte-identical on trident after copy and again locally after copy-back,
scratch deleted only after local hash verification succeeded.

**A post-hoc driver/corpus audit was requested mid-analysis, after execution
had already completed** (the audit-request message arrived while comparison
work was in progress). It could not be performed as a genuine pre-execution
gate at that point, and is disclosed as such rather than silently
backdated. Retroactive findings: the regression driver
(`automation/cj2_b2_v2_regression_run.py`, SHA256
`e30d05741821e30ee989eed5dfe4e54dbbfd2606d3e3dee95b6b47d7a1843292`) is
orchestration-only on line-by-line review — enumerates the frozen corpus via
`_iter_dev_candidates`/`_iter_fresh_candidates` unmodified, calls
`build_r1_user`/`_call`/`validate_r1`/`build_r2_user`/`run_candidate_pipeline_v2`
unmodified, performs no filtering/selective-retry/output-repair, and writes a
per-candidate result file unconditionally (both schema_invalid candidates
have their own file, not silently dropped) — no semantic-logic violation
found. One gap disclosed: the driver itself was not included in the
pre-execution byte-identical hash check against trident (only the frozen
harness/prompts/fixtures were); the trident scratch is now deleted so this
cannot be retroactively re-verified directly, though indirect evidence
(unedited local file; `run_log.json`'s recorded call conditions matching this
file's hardcoded constants exactly; all 30 candidates present with no silent
exclusions) supports that the executed copy matched. A retroactive
execution-ordered corpus manifest (`b2-v2-regression-corpus-manifest.json`,
SHA256 `c372d1cc3292a318b27cdd289630d20e430d600b559b79787c202d18f2cda9b4`)
confirms exactly 12 dev + 18 fresh = 30, no duplicate IDs/ordinals, and an
identical candidate-ID set to v1.4.1's own 30 (verified by direct set
comparison, not assumed) — v1.4.1 preserved no execution-order artifact to
compare ordering against, which is immaterial regardless since every call is
stateless and independent.

**THE DOMINANT FINDING: 17 of 30 candidates (56.7%) failed at R2 with an
identical failure signature** — raw response length clustered at
19,771-21,388 characters (~5,000-token ceiling) and the identical schema
violation `"claims missing or not a list"` (the JSON extractor recovering
only a single trailing claim object from output truncated mid-`claims[]`
array). This is ONE systemic `MAX_TOKENS=5000` insufficiency for R2's
per-claim-verbose schema (`auditor_evidence`+`why`+`override_rationale`+
`r1_agreement` repeated per claim, unlike v1.4.1's flatter single-stage
schema), strongly correlated with R1's claim count (<=16 claims: always
succeeds; >=20: always fails; 17-19: mixed, depending on per-claim
verbosity) — not 17 independent content failures. `MAX_TOKENS` was carried
forward unchanged from v1.4.1 without accounting for R2's higher verbosity.
**Not fixed or retried this pass, per instruction** — reported as the
observed outcome of this exact frozen configuration.

**Seven target outcomes: 0 REPAIRED / 3 FLAGGED_NOT_RESOLVED / 4 MISS.**
H17 and H05 both show the canonical pattern the R1/R2 split was designed to
catch: R1 (evidence-blind) correctly flags empirical dependency, R2 exempts
the claim as `interpretive_only` citing the claim's own hedge/aside wording
(H17's own `why`/`override_rationale` explicitly say so), the deterministic
Layer 1.5 catches the disagreement as `R1_R2_SEMANTIC_CONFLICT`, and the
candidate verdict is forced to `ambiguous` — never a false `safe`. The
architecture prevents the exact false-safe it was built to prevent, on every
one of the 88 claims (see below) that hit this conflict, without exception —
but the underlying hedge-driven exemption in R2 persists unchanged from
v1.3/v1.4.1; the split isolates the failure to R2, it does not fix it. H03
(candidate-level control) holds at the safety-relevant candidate-verdict
level (`unsafe`, matching requirement exactly) but only 2 of its 3 required
claim-level catches resolve cleanly — scored FLAGGED_NOT_RESOLVED rather than
rounded up. H09 and De Hooch/Z are MISS purely via the truncation defect (R1
caught both correctly). H08 surfaces a NEW failure mode never previously
observed: R1 never extracted a proposition for the target sentence at all —
it is verbatim-present in the raw candidate field, R1 decomposed the
sentences immediately before and after it, but skipped this one entirely;
field-level `field_audits` coverage validation cannot detect a missing
*sentence* within a field that otherwise has claims — a structurally
invisible omission. H14 surfaces a second new pattern: R1 and R2 fully AGREE
on role (`factual_dependency`, no conflict) for both target claims, but R2
judges the second claim's inference chain `supported` rather than the
expected `unsupported`, by a stated deductive-validity argument from two
declared premises — not a hedge failure, not a false-safe, a more permissive
support judgment than the frozen target anticipated. No invented "partial
pass" category anywhere in this scoring.

**R1/R2 disagreement rate, across the 212 claims in the 13 valid
candidates: 88 (41.5%) are R1=empirically-true / R2=interpretive_only** —
the safety-relevant conflict direction, at a far higher rate than an edge
case. 99 (46.7%) agree on `factual_dependency`; 25 (11.8%) agree on
non-empirical `interpretive_only`. **Zero** instances of the opposite
"conservative escalation" direction (R1=false/R2=factual_dependency) — the
secondary risk the design anticipated never manifested once. **Zero** raw R2
`boundary_ambiguous` role assignments — every appearance of that role in the
aggregate tables is the conflict layer's own reclassification, never a model
choice. Every one of the 88 conflict claims, absent the deterministic
override, would default to a safe-compatible `not_required` status — the
override is solely responsible for preventing a false-safe on all 88,
without exception; two candidates' entire verdict (H17,
`05_dutch_painting_soldier/S`) flips from v1.4.1's `safe` to v2's `ambiguous`
specifically because of this rule, with no independently-unsafe claim behind
it otherwise. Read plainly: the architecture does exactly what it was built
to do, and a 41.5% flagged-not-resolved rate under this exact R1/R2 prompt
pairing is itself a central empirical result, independent of the truncation
defect.

**Global role migration vs. v1.4.1**: an exact claim-by-claim table is not
mechanically meaningful (v1.4.1's single-stage decomposition and v2's
independent R1 re-decomposition produce different claim IDs AND different
granularity per candidate — e.g. H08: 14 claims under v1.4.1 vs. 17 under
v2). Two disclosed-method views reported instead: an aggregate percentage
shift (v1.4.1 interpretive_only 61.8%/factual_dependency 38.2%/
boundary_ambiguous 0.0% vs. v2's 11.8%/46.7%/41.5%, computed only over the 13
valid candidates' 212 claims against v1.4.1's full 411), and a best-effort
text-similarity claim match (threshold >=0.55, 38.2% match rate, full 6x
directional table in the comparison JSON) — both explicitly caveated that
17/30 candidates are entirely absent from the v2 side, making this
directionally informative, not a clean census.

**Acceptance status: FAIL**, applied mechanically per the preregistered
spec, no softer category invented. `cj2-stage-b2-v1.4.1` and `cj2-stage-b2-v2`
(R1/R2 prompts, harness) both unmodified. No prompt/schema/threshold edits
after seeing results. No selective reruns. No Reader Lab data used. No
cross-publisher material used. No Stage C run. Full detail, per-target
reasoning, and all computed tables in
`automation/.probe_fixtures/cj2-b2-v2-regression/b2-v2-regression-report.md`.
**Next real decision, not made this pass: whether MAX_TOKENS needs to rise
before any further B2-v2 evaluation is meaningful, and separately, whether
the 41.5% R1/R2 conflict rate and the two newly-observed failure modes
(proposition-omission, support-strength disagreement) warrant a v2.1 design
pass.**

## REGRESSION #1 METHODOLOGICAL ADDENDUM + R2 CAPACITY-RECOVERY REGRESSION
## (2026-08-12) — DOES NOT MODIFY OR OVERWRITE REGRESSION #1

Regression #1's artifacts (comparison JSON, report) are left completely
unmodified; its formal gate remains **FAIL**. Full addendum and recovery
report: `automation/.probe_fixtures/cj2-b2-v2-regression/regression-1-methodological-addendum.md`
and `automation/.probe_fixtures/cj2-b2-v2-r2-recovery/recovery-run-report.md`.

**Added interpretation (not a status change): SEMANTIC EVALUATION
INCOMPLETE — SYSTEMIC R2 OUTPUT TRUNCATION.** 17/30 candidates never
produced a valid R2 result; this is an execution-capacity defect affecting
interpretation, not 17 independent semantic failures.

**Corrected conflict-layer language, applied going forward:** the 88 (now,
in the recovery run, 183) `R1_R2_SEMANTIC_CONFLICT` instances are
**"safety-relevant disagreements"** / **"potential false-safes
prevented"** — never **"confirmed false-safes."** R1 is not human ground
truth; each instance could be R1 correctly catching a real dependency R2
missed, R1 overclassifying a genuinely interpretive claim, or a genuine
unresolved boundary. What's established mechanically: the deterministic
layer prevented every one of these claims from resolving through the
plain safe-compatible branch — real fail-closed behavior, semantic
correctness not adjudicated.

**H08 provenance, resolved — no implementation defect.** Traced directly
against this doc's own frozen "Revision 2, Correction 3": *"There is no
separate 'atomic claim extraction' step upstream of R1... R1 is the first
and only place decomposition happens... claim_id and surface_claim are
outputs of R1's own decomposition, not inputs to it."* v1.4.1's own claim
`c9` (same target sentence) was itself v1.4.1's *own* internal
decomposition output, not a shared upstream artifact — v1.2/v1.3/v1.4.1
share one evolving prompt lineage (hence stable boundaries across those
three); R1 is a freshly-authored, independent prompt with no such
inheritance promised. The target sentence WAS sent to R1 complete and
unclipped (verified by direct substring search); R1 simply never
decomposed that one sentence into its own claim this call — a genuine,
narrow decomposition-completeness gap in one model output, invisible to
`field_audits`' field-level (not sentence-level) coverage check. No STOP
condition triggered.

**H14, documented as a support-calibration disagreement, not a role
problem, not tuned:** R1/R2 agree on role (`factual_dependency`, no
conflict); R2 judges the inference-chain claim's `support` more
permissively than the frozen target's `unsupported` expectation, citing a
valid-looking deductive argument from two declared, source-supported
premises. Full field-by-field table in the addendum.

**R2 sizing, computed from Regression #1's existing artifacts, no model
calls:** CLIProxyAPI itself has no configured `max_tokens` cap (confirmed
by inspecting its live config directly) — the effective ceiling is
whatever the upstream provider enforces, not empirically probed in this
diagnostic-only phase. Average 1,166.5 / max 1,359 chars-per-claim across
the 13 valid Regression-#1 candidates; the corpus's largest candidate (23
claims) projects to ~6,700-7,800 tokens. **Froze `MAX_TOKENS=12000`**
(headroom to ~41 claims at the average ratio) as a simple, scaling-
justified ceiling, applied via a runtime override rather than a file edit.

**B2-v2 R2 CAPACITY-RECOVERY REGRESSION executed.** Not v2.1, not semantic
tuning, not a new architecture — the only experimental change was
`max_tokens`. R1 **not rerun**; all 30 candidates reuse Regression #1's
exact frozen R1 outputs (hash-verified). New driver
(`cj2_b2_v2_r2_capacity_recovery_run.py`, SHA256
`5a73bdbee0efe6dc4f47c51839a66c763315d1b9c9b94c55527388aa96fbe8e8`) — this
time included in the pre-execution trident hash-check, closing the gap
Regression #1 disclosed. 30 calls (0 R1 + 30 R2), 0 transport failures.

**Run health: 29/30 valid, ZERO truncations** — the target result. The one
schema_invalid (H18) is unrelated to capacity: a complete, well-formed
response with one illegal invented `problems` enum value
(`temporal_sequence_hardening`), confirmed by inspecting the raw output
directly (21,083 chars, nowhere near the ~48,000-char ceiling, ends
properly).

**Seven targets: 3 REPAIRED (H09, H14, De Hooch/Z) / 3 FLAGGED_NOT_RESOLVED
(H17, H05, H03, unchanged) / 1 MISS (H08, unchanged).** H09 and De Hooch/Z
— disqualified purely by truncation in Regression #1, R1 having already
caught both correctly there — now resolve cleanly to `factual_dependency`/
`unsupported` on both target claims each. H17's failure is confirmed
identical on rerun: R2's own `why`/`override_rationale` for its target
claim repeats the same hedge-citation reasoning verbatim in substance
("offered as an example... does not make the claim factual") — direct
proof this is a reasoning-level failure, not a capacity artifact. H05 and
H03 unchanged for the same reason. H08 is unchanged because R1 (the only
place the omission could be fixed) was never rerun.

**Conflict rate in the more complete recovery dataset: 183/522 valid
claims (35.1%) are `R1_R2_SEMANTIC_CONFLICT`** (vs. 88/212, 41.5%, in
Regression #1's smaller, truncation-biased sample) — comparable order of
magnitude on a much larger N. One claim landed on raw R2
`boundary_ambiguous` directly this run (never observed in Regression #1).
**Per instruction, this rate is reported as a measurement, not a success
metric** — possible explanations (R1 over-catching, R2 under-catching,
genuine boundary instability, some mix) are named but not adjudicated.
Dominant candidate-verdict shift vs. v1.4.1: 11/30 `safe→unsafe`, 0
`unsafe→safe` — described as an observation, not evidence of which
architecture is more correct.

**Regression #1's status is unchanged and not superseded: FAIL /
SEMANTIC EVALUATION INCOMPLETE.** The recovery run's own separate result
(3/3/1) answers only "what does the frozen architecture do once R2 can
finish" — it does not retroactively pass Regression #1. `cj2-stage-b2-v2`
(R1/R2 prompts, harness) remain unmodified throughout both passes. No
v2.1 designed. No Stage C. No cross-publisher material. No Reader Lab data
used or inspected. No selective reruns of individual misses. **Next real
decision, not made this pass: whether the 3 REPAIRED results generalize
beyond this corpus, and whether H17/H05/H03's confirmed reasoning-level
(not capacity) persistence now warrants an actual v2.1 prompt-design
pass.**

## B2 NEXT-STRUCTURE DESIGN — D0/R1/R2 (2026-08-12, design only, not implemented, no API calls)

**Trigger.** The R2 capacity-recovery run left two distinct, unresolved
findings that are NOT the same problem and must not be fixed by the same
mechanism (see current-work.md's `## B2 v2 — CURRENT POINTER`):

- **H08 (decomposition-coverage miss):** R1 is currently the *first and
  only* place proposition decomposition happens (the frozen v2 design
  doc's own Correction 3). The complete candidate sentence reached R1 in
  both Regression #1 and the recovery run — R1 simply never produced a
  `claim_id` for it. No downstream stage (R2, the conflict layer) can
  audit a proposition that was never extracted. This is invisible to
  every existing coverage check, because those checks all operate on the
  claim set R1 *did* produce, not on the candidate text R1 was given.
- **H14 (support-calibration variability):** R1 and R2 *agree* on role
  (`factual_dependency`) and support (`unsupported`) for the target claim
  in the recovery run — but Regression #1's earlier run of the identical
  frozen architecture landed the same claim on `supported` instead, at
  the same `temperature=0.0`, same R1 input. This is real run-to-run
  variability in R2's own support judgment on an inference-chain claim —
  not a decomposition problem, not a role-classification problem. **H14
  must not be treated as evidence for or against a D0 stage** — a D0
  stage does nothing to R2's support judgment, and conflating the two
  findings would misdirect the fix. H14 stays open as its own
  support-calibration question, deferred, not designed here.

**Why the R1/R2 conflict rate (183/522, 35.1%) doesn't distinguish these
two:** the conflict layer catches disagreements between two stages that
both *ran*. H08 never reaches the conflict layer at all — it is silent
by omission, not disagreement. The 35.1% figure measures a completely
different failure surface (semantic boundary disagreement between two
present judgments) than H08's absence-of-judgment. Both are real, both
matter, and this section addresses only the second (D0), since the first
is Reader Lab's own research question for RL-2026-001 item 3, not an
architecture question.

### Proposed topology

```
candidate JSON (5 fields: engine_move, seed_engagement,
                interpretive_inference, conceptual_shift,
                claimed_contribution)
  |
  v
D0 -- ATOMIC PROPOSITION EXTRACTION (new stage)
  no evidence, no source, no factual/interpretive role judgment
  output per claim: claim_id, source_field, exact_surface_span,
                     atomic_claim
  output per source_field: explicit coverage accounting (see below)
  |
  v  (D0's claim set is FIXED from here on, same discipline as R1's
  |   current fixed output feeding R2 in v2)
  v
R1 -- PROPOSITION CONTRACT (unchanged in spirit from v2, narrowed scope)
  receives ONLY D0's fixed claim set, cannot decompose, cannot add or
  drop claims
  for every D0 claim: world_truth_question, concrete_restatement,
                       empirical_dependency
  |
  v
R2 -- SUPPORT / DECLARATION AUDIT (unchanged from v2)
  receives fixed D0 claim + R1's proposition contract + source/evidence
  assigns role/support/declaration/problems
  |
  v
deterministic conflict + coverage layer (extends v2's existing
  R1/R2 consistency computation with a NEW, separate D0-coverage check
  that runs BEFORE R1 is even called — see below)
```

D0 is evidence-blind, same as R1 currently is — it never sees the
source, only the candidate's own generated fields. Its job is answering
"what is this candidate text actually asserting?", not "is it true?" or
"is it a reading or a claim?". Keeping D0 source-blind avoids adding a
second evidence-fetching path and keeps its task narrow enough that it
isn't competing for attention with a truth judgment — directly targeting
the "combined-task problem" the current design doc's Correction diagnosed
in the *pre-split* single-call B2: a model doing discovery and judgment at
once can silently under-discover exactly the propositions it finds hardest
to judge. Splitting discovery into its own call, with literally nothing
else for D0 to do, is the actual mechanism by which this might reduce
that specific correlated risk — not merely restating "decompose fully" to
a differently-named stage.

### The central design question: coverage, not factuality

**D0 must never decide `empirical_dependency`, `interpretive_only`,
source support, declaration, or safe/unsafe.** Its only job: "what
propositions are actually being asserted in this candidate text, and can
we show, mechanically, that nothing substantive was skipped?" Getting
this wrong in either direction is a real risk: over-scoping D0 into a
factuality gate would just recreate R1's original combined-task problem
one stage earlier.

**Rejected as insufficient on its own: "extract every claim" as a prompt
instruction.** This is what R1 already does today, unconditionally, per
the v2 Revision 2 fix that removed the `requires_concrete_restatement`
bypass trigger specifically to close this exact gap — and H08 shows a
real omission survived that instruction anyway. Repeating the same
appeal to model diligence at a new stage name doesn't change the
mechanism that failed; a fix here has to be structural and checkable
by code, not another promise.

**Layered mechanism actually proposed (deterministic, checkable in code,
no new model call for the check itself):**

1. **Field-level completeness (cheap, coarse, catches total-field
   omission):** does D0's `field_audits`-equivalent structure reference
   every `source_field` present in the candidate JSON? Trivial to check,
   catches the crudest failure (skipping `claimed_contribution` entirely)
   but does NOT catch H08 — H08's field (`interpretive_inference`) was
   NOT skipped; a specific sentence inside an otherwise-covered field
   was. Kept as a first, cheap tripwire layered under the real check
   below, not as the fix.

2. **Segment-level coverage accounting (the actual H08 fix):**
   independently segment each `source_field`'s raw text into sentence-
   level units using a real, deterministic sentence tokenizer — NOT the
   model, and NOT self-reported by D0. For every independently-detected
   segment, deterministically check whether it is covered by:
   (a) being contained in, or overlapping, at least one claim's
   `exact_surface_span`, resolved via the SAME exact/normalized-match
   anchor-resolution logic this project already built and validated for
   `auditor_evidence` (`automation/cj1_v3_anchor_resolver.py`'s
   `exact_match`/`normalized_unique_match` categories — reused, not
   reinvented), OR
   (b) an explicit D0 entry marking that exact span `non_propositional`
   with a required, non-empty reason (transitional phrasing, a bare
   restatement of an already-covered claim, a section header, etc.).
   Any segment matching neither (a) nor (b) is a deterministic
   `coverage_incomplete` failure — computed by code, not asked of a
   model, and fails CLOSED: it routes the candidate the same way
   `unresolved_semantic_conflict` already routes today (reusing the
   existing fail-closed mechanism per this project's stated preference
   for not inventing new verdicts where an existing one already fits),
   rather than silently letting an uncovered proposition pass through
   untouched.

   This is the load-bearing difference from "extract every claim": the
   coverage claim is verified against an INDEPENDENTLY computed
   segmentation, not against D0's own self-report. A model cannot pass
   this check merely by being confident it was thorough.

3. **A second, independent-model coverage-checker pass — proposed as an
   optional backstop, NOT the primary mechanism, and NOT designed to run
   by default.** A separate model call, given only the candidate text
   and D0's claim list, asked to flag any sentence it believes isn't
   covered. This could catch cases where the deterministic segmenter's
   granularity itself is wrong (see risk 2 below) in ways a fixed
   tokenizer can't self-correct — but it reintroduces exactly the
   "another model promising diligence" problem this section opened by
   rejecting, just one layer later, so it should not be the primary
   gate. Recommendation: build and validate mechanism 2 first: only add
   mechanism 3 if mechanism 2's own false-negative rate, measured
   empirically against real candidates (no threshold pre-chosen, per
   this project's standing rule against inventing acceptance numbers
   before seeing data), turns out inadequate.

4. **Field-level-only coverage (i.e., mechanism 1 alone, without
   mechanism 2) was considered and rejected as the sole mechanism** —
   explicitly because H08 already demonstrates a same-field, sub-sentence
   omission; a check that only verifies "every field has at least one
   claim" would not have caught the exact case that motivated this
   design.

### Honest new-failure-mode list (per this project's standing discipline
of naming what a fix doesn't solve, not just what it does)

- **Coverage-gaming risk:** the deterministic check verifies SPAN
  coverage, not claim QUALITY — D0 could satisfy mechanism 2 by
  attaching a low-quality, wrongly-scoped, or overly-broad claim to a
  segment just to make the mechanical check pass, without genuinely
  isolating the right proposition. Directly analogous to the
  already-flagged R2 `override_rationale`-gaming risk and the R1
  `identity_restatement_rate` diagnostic (a model satisfying a
  structural requirement without doing the substantive work). No fix
  proposed here — flagged as a diagnostic to report (a coverage-claim-
  quality spot-check rate), not gated, since no threshold has been
  chosen against real output.
- **Granularity mismatch:** sentence-level segmentation does not
  perfectly align with proposition boundaries. A single compound
  sentence (common in this project's own candidate prose — see H08's own
  "The specific limit... — and the signal... was not there to be
  resolved") can carry more than one atomic proposition; a single
  proposition can span a clause fragment that crosses a sentence
  boundary. This will produce some false `coverage_incomplete` flags on
  legitimate output and, in principle, could let a genuinely missed
  sub-clause hide inside an otherwise-"covered" compound sentence. Not
  resolved here — see unresolved decisions below.
- **`non_propositional`-marking abuse:** a model could mark a genuinely
  propositional segment `non_propositional` with a superficially
  plausible reason to dodge extraction entirely — the direct D0 analogue
  of R2's `override_rationale` risk. Per the same precedent Revision 2
  already set for `override_rationale` (free-text kept for diagnostics,
  never itself sufficient to clear a gate), a `non_propositional`
  marking should be logged and its rate reported, not silently trusted
  as satisfying coverage merely because a reason string is present.
- **Correlated D0/R1 bias:** if D0 and R1 use the same underlying model
  (as v2's first structural test deliberately did for R1/R2, to isolate
  the structural-externalization variable), they may share the same
  blind spots about what counts as "propositional" even though the
  tasks are now formally separate calls — separation of task ≠
  independence of judgment. Not eliminated by this design; not claimed
  to be.
- **New deterministic-layer complexity is itself a place for silent
  bugs** — the same class of risk the existing R1/R2 consistency layer
  already carries, and that this project's own static-test discipline
  (`cj2_b2_v2_static_tests.py`, 51/51 checks before any live call) exists
  to catch. A D0 coverage checker would need equivalent static tests
  before any live run — not built in this pass.

### Unresolved design decisions (explicitly left open, not resolved here)

- Exact segmentation granularity for the deterministic checker (sentence
  vs. clause-level splitting on coordinating conjunctions/semicolons/
  em-dashes) — not chosen.
- Same-model or different-model for D0 vs. R1/R2 — mirrors the
  still-open "same-model or not" question already flagged unresolved for
  R1/R2 in the original v2 design; not decided here either.
- Whether `coverage_incomplete` reuses the existing `ambiguous`/
  `unresolved_semantic_conflict` fail-closed path (leaning yes, per the
  standing preference against inventing new verdicts) or needs its own
  `effective_status` value — not decided.
- Whether the independent-model backstop (mechanism 3) is worth its added
  cost at all, versus relying on mechanism 2 alone — not decided;
  recommend testing mechanism 2 alone first.
- Whether D0's claims must already be final-granularity atomic
  propositions, or may be coarser units that R1 is still permitted to
  further decompose (a smaller change to R1's "cannot decompose" rule
  above) — not decided.
- Cost: this adds a THIRD model call per candidate (D0 additional to
  R1+R2), not accounted for in v2's "~2x B2-stage calls" estimate — a
  real, un-minimized increase, reported plainly rather than assumed away
  because D0's task is narrower than R1's or R2's.

### Explicitly not done this pass

No prompts written. No harness code written. No API calls made. No
`v2.1` (or any new version number) assigned — this is architecture design
only, one level up from a version, per instruction. No Stage C. No
cross-publisher material touched. H14 is NOT addressed by this design and
must not be retroactively claimed as evidence for or against it (see
above). Reader Lab's RL-2026-001 (separate track, `.claude/reader-lab-v0-design-2026-08-12.md`
SS20) is not used as input to this design and this design does not wait
on Round 001's responses.

## B2 NEXT-STRUCTURE PROTOTYPE — D0/R1/R2 (2026-08-12, EXPERIMENT-ONLY implementation + static validation, no model/API calls)

Proceeded from the design above (`## B2 NEXT-STRUCTURE DESIGN — D0/R1/R2`)
to a deterministic-only prototype, per explicit instruction: implement
ONLY D0 + the coverage validator + the fixed-claim handoff plumbing, not
a model regression. Working identity: **B2 NEXT-STRUCTURE PROTOTYPE —
D0/R1/R2** — deliberately not named `v2.1`; does not modify, import, or
touch any frozen `cj2-stage-b2-v2` artifact (`cj2_b2_v2_probe.py`, its
frozen prompts, `acceptance-matrix-v2-preregistered.json`), and does not
touch production article generation.

### Files (all new, all EXPERIMENT-ONLY, uncommitted)

- `automation/cj2_b2_d0_prototype.py` — D0 schema, segmentation,
  span-resolution, coverage validator, fixed-claim handoff check.
- `automation/cj2_b2_d0_static_tests.py` — 33 checks, generic invented
  material only (no H03/H05/H08/H09/H14/H17/De Hooch-Z wording).
  **33/33 PASS, zero API calls, zero network access.**
- `automation/cj2_b2_d0_h08_structural_test.py` — the one file that
  DOES use real H08 candidate text, kept separate specifically so it's
  never mistaken for a generic case. **6/6 checks PASS.**

### D0 output schema (`D0_SCHEMA_VERSION = "d0-prototype-0.1"`)

```json
{
  "claims": [
    {"claim_id": "...", "source_field": "...", "exact_surface_span": "...", "atomic_claim": "..."}
  ],
  "non_propositional": [
    {"non_prop_id": "...", "source_field": "...", "exact_surface_span": "...",
     "reason_code": "heading_or_label|citation_or_reference|connective_only_fragment|formatting_artifact|purely_rhetorical_transition|other",
     "reason_note": "..."}
  ]
}
```

D0 never emits `empirical_dependency`, `role`, `support`, `declaration`,
or any safe/unsafe vocabulary — confirmed by construction (the schema
validator's allowed keys don't include them) and by every static test
(none references B2-v2's factuality vocabulary).

### Segmentation decision — resolved, not left open

Smallest deterministic unit: **sentence-level, further split on
semicolons into clause-level units.** Investigated and explicitly
rejected as the split point: **colons** — in this project's own
candidate prose a colon overwhelmingly introduces an elaboration of the
SAME proposition rather than a second independent one (confirmed against
real fixture text: H14's real sentence, *"...expose what this
assumption costs: the word is not decorative..."*, would fragment into
a claim-less half if colons split); semicolons, by contrast, reliably
separate independent clauses in this material and are split on.
Bullet/numbered lines are treated as line-level units before
sentence/clause splitting (implemented and static-tested;
rare-to-unused in current candidate JSON, which is prose paragraphs).
Coordinating-conjunction splitting ("and"/"but") inside one sentence is
explicitly NOT attempted — confirmed as a real, accepted limitation by
`case_compound_two_propositions_covered`, which documents (not hides)
that a single claim spanning a whole compound sentence mechanically
satisfies coverage even though it bundles two propositions. Not a full
linguistic parser — abbreviations/decimals/quoted-dialogue punctuation
can mis-split; accepted, documented, not solved.

### Coverage contract — the actual mechanism, verified against real H08 text

Independently segments every candidate field (never trusts D0's own
completeness claim), resolves every claim/`non_propositional` span via
the SAME exact/normalized-quote-fold resolver already built for CJ-1 v3
anchors (`cj1_v3_anchor_resolver.resolve_anchor`, imported, not
reimplemented), and computes segment coverage by character-offset
overlap (`MIN_OVERLAP_FRACTION = 0.5`, an explicitly open/tunable
constant, not empirically chosen). Any segment with zero sufficient
overlap from a claim or an explicit `non_propositional` record is
`coverage_incomplete` — fails CLOSED (routes distinctly from R1/R2's own
`unresolved_semantic_conflict`, never conflated with it).

**H08 structural verification (the actual point of this pass):** built
a hand-authored D0 claim set covering every one of H08's real
`interpretive_inference` field's 8 deterministically-segmented units
EXCEPT the one containing the real target proposition (*"...the scale's
resolution was treated as adjustable by the raters, when in fact
resolution is a property of the underlying signal — and the signal,
near the funding line, was not there to be resolved."*) — the exact
sentence B2-v2's real R1 stage silently never claimed in both live
regression runs. Result: **the coverage validator correctly raised
`coverage_incomplete`, named exactly that one segment as uncovered, and
did not falsely flag any of the other 7 correctly-claimed segments.**
This demonstrates the mechanism WOULD have surfaced H08's real failure
mechanically, without depending on any model re-promising diligence —
it does not demonstrate that a real D0 model call will decompose
correctly (no model was run); it demonstrates the checking layer works
against the exact real failure shape.

### Fixed-claim handoff plumbing

One generic function, `validate_claim_set_unchanged(fixed_ids,
downstream_ids, stage_name)`, applied at BOTH handoff points (D0→R1 and
R1→R2) since the invariant is identical at each: the downstream
`claim_id` set must equal the upstream fixed set exactly. Static-tested
for omission, split (new id appears — reported as "extra"), and merge
(an id disappears — reported as "missing") at both points.

### Non-propositional escape — reported, never auto-trusted

`non_propositional_rate_report()` returns counts by `reason_code`
(including `other` separately) and a rate — diagnostic only. Static
test `case_over_marked_non_propositional` confirms the mechanism does
NOT reject or "correct" a 100%-`other`-reason marking; it mechanically
satisfies coverage (spans are accounted for) while the rate report
flags the pattern for human review — matching the instruction's own
framing ("be conservative about `other`... do not automatically trust
that classification as correct") without inventing an auto-reject
threshold not yet justified by real data.

### Failure states (fail-closed priority, most severe first)

`schema_invalid` (malformed structure, duplicate `claim_id`/`non_prop_id`,
illegal `reason_code`, unknown `source_field`) > `span_resolution_failed`
(a span doesn't resolve against its field text — kept structurally
distinct from a coverage gap: this is "the claim is broken," not "a
proposition is missing") > `coverage_incomplete` (the actual H08-shaped
failure) > `valid`. All four confirmed independently by dedicated static
tests, including priority ordering (e.g.
`case_duplicate_claim_id_schema_invalid` uses fully-covered text to
confirm `schema_invalid` still wins even when coverage would otherwise
be complete).

### Static-test result

**39/39 checks PASS total** (33 generic + 6 H08-structural), 0 API
calls, 0 network access, 0 model calls. Both pre-existing frozen suites
re-run unmodified and confirmed still green: `cj2_b2_v2_static_tests.py`
(51/51, untouched) and this new suite — no cross-contamination between
the frozen v2 harness and this prototype.

### Open risks (unchanged from the design pass, now visible in code rather than only in prose)

Coverage-gaming (a claim's span can overlap a segment without genuinely
scoping the right proposition — the validator checks OVERLAP, not
semantic correctness, by design, since D0 must not judge content);
granularity mismatch (confirmed live by
`case_compound_two_propositions_covered`); correlated D0/R1 bias if
same underlying model (not testable without a real model call, out of
scope this pass); `MIN_OVERLAP_FRACTION=0.5` is an unvalidated constant.

### Explicitly not done this pass

No D0 prompt written. No R1/R2 model call made against this prototype's
schema. No `cj2-stage-b2-v2` frozen artifact modified. No `v2.1`
assigned. No Stage C. No cross-publisher material. No Reader Lab data
inspected or used. RL-2026-001 responses were not analyzed (both
reviewers have not yet completed the round). **Next real step, not
taken this pass:** write an actual D0 prompt and run it against real
candidate text to see whether a real model's claim set, checked by this
same validator, produces `coverage_incomplete` less often than R1 alone
did in the v2 regressions — that is a live-call, semantic question this
prototype's static tests cannot answer on their own.

## B2 NEXT-STRUCTURE PROTOTYPE — ADVERSARIAL COVERAGE AUDIT (2026-08-12, static only, no model/API calls, no D0 prompt written)

**Question tested:** does the surface-coverage validator built in the
prior pass (`cj2_b2_d0_prototype.compute_coverage`) actually guarantee
*proposition completeness*, or only something narrower? Run BEFORE
writing any D0 prompt, per explicit instruction, precisely because this
is the question that determines whether a D0 prompt would even be
checked by an adequate mechanism once real model output exists.

### Result: the hypothesis is CONFIRMED. Surface coverage is necessary, not sufficient.

New file, EXPERIMENT-ONLY: `automation/cj2_b2_d0_adversarial_coverage_audit.py`
— **6/6 generic adversarial cases (coordination "but", causal "because",
attribution+embedded content, relative clause, comparison "while",
modality/assumption) all pass the current validator as `valid` while
silently dropping a real second (or third) proposition.** Mechanism:
a single D0 claim is given `exact_surface_span` = the ENTIRE
deterministic segment, but `atomic_claim` captures only one of the
segment's propositions. Coverage is computed purely from character-
offset span overlap — it never inspects whether `atomic_claim`'s
semantic content actually represents everything inside the span it
claims to cover. A broad, lazy span mechanically satisfies coverage
regardless of how little of the segment's content the claim's own text
captures.

**This is not merely hypothetical.** The real H17 sentence already
selected for `RL-2026-001` — *"The differential cutoffs reveal that the
system is not purely measuring career stage at all — it is measuring
career stage adjusted for an assumed sex-linked career disruption
pattern (e.g., childbearing)"* — segments into exactly ONE unit under
the current rule (no semicolon, an em-dash instead), bundling at least
two assertions (what the system is NOT doing; what it IS doing instead)
into a single span. Nothing prevents a real D0 model call from claiming
only the second half and passing coverage cleanly. This was checked
directly, not assumed.

### Precise statement of what the validator actually guarantees (corrected from the prior pass's looser language)

**SURFACE COVERAGE GUARANTEE (what IS true):** for every deterministic
sentence/semicolon-clause-level segment of a candidate field, at least
one D0 claim's `exact_surface_span` (resolved via the same quote-fold
matching used for CJ-1 v3 anchors) overlaps that segment's character
range by ≥ `MIN_OVERLAP_FRACTION`, or an explicit `non_propositional`
record does — otherwise the segment is reported `coverage_incomplete`.
**Confirmed to catch the real, historical H08 failure shape** — see
below.

**WHAT IT DOES NOT GUARANTEE (corrected framing):** that the semantic
content of the claim(s) covering a segment represents every proposition
asserted within that segment's text. "Surface coverage" is NOT
"proposition completeness" — the prior pass's design-doc language
("the coverage claim is verified against an INDEPENDENTLY computed
segmentation, not against D0's own self-report") remains true and
valuable for the whole-segment-omission class, but should not be read
as solving proposition-level completeness in general, and this document
is corrected accordingly. (The prior pass's own honest-risk list already
named "coverage-gaming risk... a claim attached without genuine correct
scoping" in the abstract; this audit converts that from a named
possibility into a demonstrated, reproducible mechanism.)

### Per-instruction constraint honored: not solved by finer punctuation

Per explicit instruction, this audit did NOT add commas/"but"/"because"/
"while" as new deterministic split points to make the adversarial cases
"pass" — segmentation is UNCHANGED from the prior pass. Natural-language
proposition boundaries are not equivalent to punctuation, and a
punctuation-chasing fix would just move the same gap to a different
conjunction the next fixture uses (H17's em-dash rather than "but" is a
concrete illustration of exactly that whack-a-mole).

### Real H08 re-examined: did the existing structural test reproduce the right failure shape?

Re-inspected H08's actual R1 output (not summarized): `interpretive_inference`
segments into 8 units under current segmentation. Real R1 claims c7–c12
map as: c7→seg1, {c8,c9}→seg2 (R1 out-decomposed the segmenter here,
fine), c10→seg3+seg4 together (a real compound claim whose text
genuinely names both halves — not an instance of this audit's failure
class), c11→seg5, **then c12 jumps straight to seg7+seg8 — zero claim of
any kind references seg6, the real target proposition, at all.** This
is a clean whole-segment skip, not a proposition embedded alongside
another one inside a claimed span. **The existing 6/6 H08 structural
test (which omits a whole segment with nothing else touching it) is
confirmed to faithfully reproduce the real historical failure shape.**
No change made to that test or its historical result, per instruction.
The adversarial audit above is therefore evidence of a DIFFERENT,
additional failure class this project has not yet observed in a live
run — not a correction to the H08 test.

### Option assessment

- **Option A (current, surface coverage only):** necessary — catches
  the real H08 whole-segment-omission shape, confirmed twice now (this
  pass and the prior one). Insufficient alone — proven blind to
  semantic omission inside a covered span, 6/6.
- **Option B (D0 segment accounting: `segment_id → proposition_ids[] /
  non_propositional_parts[]`, explicit ID bookkeeping instead of span-
  overlap heuristics):** assessed honestly as a bookkeeping
  reformulation, not a semantic fix. It removes the `MIN_OVERLAP_FRACTION`
  heuristic and its edge-case ambiguity (partial overlap, duplicate
  spans) — a real, worthwhile robustness improvement, adopt regardless —
  but a model can still declare `segment_id=seg1 → proposition_ids=[c1]`
  where `c1`'s `atomic_claim` only represents P1. The check "did D0
  formally address this segment" and the check "does D0's content
  actually cover everything in this segment" are different checks;
  Option B only strengthens the first. Not sufficient alone, by the same
  logic that makes Option A insufficient.
- **Option C (independent evidence-blind coverage-checker model call:
  reads original text + segments + fixed D0 claim set, answers only
  `complete` / `missing_proposition` + span + proposed atomic claim, no
  factuality):** the only option that can detect this failure class,
  because it is the only one that involves something actually reading a
  segment's content and comparing it to what was extracted, rather than
  checking whether spans/IDs formally line up. This is exactly
  "mechanism 3" from the prior design pass, which was explicitly
  deferred pending evidence that surface coverage (mechanism 2) was
  inadequate. **This audit is that evidence** — inadequacy is now
  demonstrated by construction, not theorized. Must stay scoped exactly
  like D0 itself: evidence-blind, no role/support/factuality judgment,
  narrow binary-plus-span output only — otherwise it quietly becomes a
  second R1.
- **Option D (targeted/cost-reduced Option C):** run the independent
  checker ONLY on segments D0 leaves "thin" — exactly one claim or
  `non_propositional` record accounting for ≥90% of a segment's span
  (the specific structural pattern that enables this failure class;
  segments already split across 2+ claims are lower-risk by
  construction, since the model was forced to enumerate multiple pieces
  to get there). This targets the exact adversarial shape confirmed
  above while avoiding a full per-segment model call on every candidate
  field — the smallest change that makes the demonstrated gap
  observable, not the most thorough one available.

### Decision gate

**B. COVERAGE CONTRACT NEEDS ONE MORE STRUCTURAL LAYER BEFORE MODEL PROBE.**

Smallest justified addition, optimized for making silent proposition
loss observable rather than for architectural elegance: adopt Option
B's ID-based bookkeeping (cheap, removes heuristic ambiguity, do this
regardless) AND add Option D's targeted independent coverage-check —
restricted to "thin" segments only, evidence-blind, binary
`complete`/`missing_proposition` output with no factuality content.
Both remain design-only as of this pass — **no prompt written for
either**, no model/API call made, no `v2.1` assigned. `MIN_OVERLAP_FRACTION`
and the "≥90% single-claim" thin-segment threshold are both still
open/unvalidated constants, not tuned against real output.

### Explicitly not done this pass

No D0 prompt written or run. No model/API calls. No Reader Lab response
inspection (RL-2026-001 still awaiting both reviewers). No cross-
publisher material. `reader-lab/rounds/drafts/RL-2026-001.json`
untouched. No `v2.1` naming. This audit's own new file
(`cj2_b2_d0_adversarial_coverage_audit.py`) makes no changes to
`cj2_b2_d0_prototype.py`, `cj2_b2_d0_static_tests.py`, or
`cj2_b2_d0_h08_structural_test.py` — all three remain exactly as
verified in the prior pass (39/39 + this pass's 6/6 adversarial checks,
re-confirmed together, zero regressions).

## B2 NEXT-STRUCTURE PROTOTYPE — D0 REVISED (Option B) + C0 ADDED (2026-08-12, EXPERIMENT-ONLY implementation + static validation, no model/API calls, no D0/C0 prompt written)

Direct follow-on to the adversarial coverage audit above. Accepted
finding: **surface/span coverage is necessary but not sufficient for
proposition completeness.** Revised the recommendation's targeting
mechanism per instruction (do NOT condition the semantic check on a
`>=90%` span-coverage heuristic — that heuristic is derived from the
same signal already shown insufficient; a 100%-spanning claim can still
omit a proposition, so a "thin segment" pre-filter would just create a
false sense of scoping without a principled basis).

### 1. D0 revised — Option B, ID-based segment accounting (`D0_SCHEMA_VERSION` bumped 0.1 → 0.2)

`automation/cj2_b2_d0_prototype.py` rewritten: every claim/
`non_propositional` record now carries a REQUIRED `segment_ids: [str]`
field — explicit bookkeeping, not inferred from span-overlap-fraction
heuristics (the old `MIN_OVERLAP_FRACTION=0.5` constant is removed from
all live code paths, kept only as a commented historical marker).
`validate_segment_id_consistency()` is the new integrity check: a
claim's declared `segment_ids` must equal EXACTLY the set of
deterministic segments its resolved `exact_surface_span` geometrically
overlaps — not a subset, not a superset. This removes the prior
version's overlap-fraction ambiguity entirely (no threshold anywhere in
the coverage decision now). `compute_coverage()` is now a plain,
threshold-free set-membership check: a segment is covered iff its
`segment_id` appears in the union of declared `segment_ids` across
claims/non_propositional records for that field.

**Documented explicitly, in the module's own docstring, so this is never
mistaken for more than it is:** "SEGMENT ACCOUNTING DOES NOT ESTABLISH
SEMANTIC COMPLETENESS. It is structural bookkeeping only." The renamed
effective status `D0_COVERAGE_FAILURE` (was `coverage_incomplete`)
carries a `detected_by` field — `"segment_accounting"` when raised by
this file's own check.

**Re-verified, not merely asserted, that Option B does NOT close the
adversarial-audit gap:** re-ran `cj2_b2_d0_adversarial_coverage_audit.py`
against the new ID-based mechanism — all 6/6 generic cases still pass
as `valid` while silently losing a proposition, exactly as predicted
when Option B was accepted as bookkeeping-only. A claim whose span
genuinely, geometrically spans a whole segment can declare that
segment's id and pass the (now much stricter) consistency check
honestly, while its `atomic_claim` still represents only part of what
the segment asserts.

### 2. C0 added — independent, evidence-blind proposition-coverage audit

New file `automation/cj2_b2_c0_prototype.py`
(`C0_SCHEMA_VERSION = "c0-prototype-0.1"`). C0's single question: *"Does
the D0 claim set represent every proposition asserted or proposed in
the candidate text?"* Output: `{"status": "complete"|
"missing_proposition", "missing_items": [{"segment_id",
"source_field", "exact_surface_span", "missing_atomic_claim",
"reason"}]}`. `source_field` was added to `missing_items` beyond the
originally sketched shape — necessary because `segment_field()` numbers
ids per-field starting at `"seg1"` every time, so a bare `segment_id`
is ambiguous across a multi-field candidate; every other schema in this
project (D0's own claims) is already field-qualified, so this is
consistency with existing convention, not a new design choice.

**Structural scope enforcement, not just documentation:**
`BANNED_FACTUALITY_KEYS` (role, support, declaration,
factual_dependency, interpretive_only, empirical_dependency, safe,
unsafe, problems, override_rationale, r1_agreement, importance,
declared_refs, auditor_evidence, world_truth_question,
concrete_restatement, boundary_ambiguous, and the expected_* target
fields) and `SCOPE_VIOLATION_KEYS` (claims, revised_claims, d0_claims,
updated_claims) are recursively scanned for and REJECTED if present
anywhere in C0's output — key-name detection, not free-text word
scanning (free-text scanning for "factual" would false-positive on
ordinary English inside a legitimate `reason` field). C0's schema has
no key that could revise D0's claim set at all, so "C0 cannot
alter/split/merge D0 claims" is true by construction, confirmed by
dedicated tests, not merely asserted.

**Invariants enforced:** `status="complete"` ⇔ `missing_items` empty;
`status="missing_proposition"` ⇔ `missing_items` non-empty. Every
`missing_items[i]` must reference a REAL `segment_id` of its declared
`source_field`, and its resolved `exact_surface_span` must fall WITHIN
(not equal to — containment, not exact match, since a missing
proposition is a sub-span of an already-"covered" segment) that
segment's character range.

**Not merged into D0's claim set this pass, per explicit instruction:**
C0's `missing_items` are diagnostic only. "Can independent semantic
checking make omission observable" and "can two extraction passes
negotiate a final claim set" are kept as separate, sequential research
questions — only the first is addressed this pass.

### 3. Fail-closed gate — `compute_pipeline_gate()`

Combines D0's own structural result with C0's semantic result into one
decision. Priority: D0 non-`valid` (`schema_invalid` /
`span_resolution_failed` / `segment_id_consistency_failed` /
`D0_COVERAGE_FAILURE[segment_accounting]`) > `C0_SCHEMA_INVALID` (C0's
OWN output malformed — never defaults to "proceed") >
`D0_COVERAGE_FAILURE[c0_semantic_audit]` > `valid`. `should_call_r1()`
returns `False` for every branch except the last. **A coverage failure
from either detection mechanism can never become `valid`/"safe"** —
confirmed by dedicated tests, including one that deliberately builds a
D0 output that already IS `valid` by segment-accounting and shows the
gate still correctly blocks R1 once C0 reports `missing_proposition`.

`D0_COVERAGE_FAILURE` (either `detected_by` value) is kept structurally
distinct from `R1_R2_SEMANTIC_CONFLICT`/`unresolved_semantic_conflict`
(cj2_b2_v2_probe.py, untouched) at the naming level, per instruction —
R1/R2 haven't even run yet when a coverage failure fires; a semantic
conflict requires both stages to have already seen the same
proposition.

### 4. Same-model-vs-independence decision, documented not left implicit

`FIRST_PROBE_MODEL_DECISION` in `cj2_b2_c0_prototype.py`: **same
underlying model for D0 and C0, as two separate, blind API calls** — C0
never receives D0's reasoning (D0's own schema has no such field to
leak). Explicitly NOT claimed as statistical/model-family independence
— documented as "a separate evidence-blind coverage audit," matching
this project's own precedent for R1/R2's first structural test
(isolate the architecture variable before introducing a model-family
confound).

### 5. Static-test results

- `cj2_b2_d0_static_tests.py`: 36/36 PASS (revised for the new schema;
  added segment-consistency-specific cases: fabricated extra
  segment_id, incomplete segment_id declaration, empty segment_ids
  list).
- `cj2_b2_d0_h08_structural_test.py`: 6/6 PASS, unchanged conclusion
  (real H08 whole-segment omission, still correctly caught, now
  reported as `D0_COVERAGE_FAILURE[segment_accounting]`).
- `cj2_b2_d0_adversarial_coverage_audit.py`: 6/6 PASS, re-verified
  against the new mechanism — same finding holds.
- `cj2_b2_c0_static_tests.py`: **29/29 PASS**, including two diagnostic-
  only cases using real H08/H17 material (fixture reuse, no prompt
  encoding, no model call): the H08-shaped case confirms D0 alone
  already catches that failure (whole-segment omission); the
  **H17-shaped case is the concrete demonstration of why C0 exists** —
  D0's own structural check reports `valid` for a claim that honestly,
  consistently spans H17's real sentence while representing only half
  its content, and only a correctly-functioning C0 (simulated here,
  not run) would catch it.
- `cj2_b2_v2_static_tests.py`: 51/51 PASS, untouched, zero cross-
  contamination.

### 6. First model-probe design (NOT executed this pass)

**Scope:** a small development-material probe, run BEFORE any
30-candidate regression, testing D0+C0 in isolation. Candidate shapes to
include, all from already-inspected development material (never
untouched cross-publisher/held-out): clean complete decompositions,
whole-segment omissions (H08-shaped), within-segment omissions
(H17-shaped), compound assertions ("and"/"but"), attribution/embedded
claims ("X says Y"), modality/assumption ("policy assumes..."),
legitimate non-propositional text (headings/citations). **R2/Stage C
are NOT evaluated in this first probe** unless specifically needed to
test plumbing (e.g. confirming `should_call_r1()` genuinely prevents an
R1 call in the harness, not just in unit tests).

**Metrics to measure (no threshold pre-chosen, per this project's
standing rule against inventing acceptance numbers before seeing real
output):** D0 omission rate (whole-segment, via `D0_COVERAGE_FAILURE
[segment_accounting]`), C0 detection rate (does C0 catch a
within-segment omission when D0 makes one — measurable only once D0
actually runs against real prompts, not simulated as in the static
tests above), C0 false-alarm rate (does C0 ever report
`missing_proposition` against a genuinely complete claim set — the
single most important number for deciding whether C0 is worth its
cost), coverage-failure frequency overall, claim-count expansion
(D0+C0's claim/segment counts vs. v2's single-stage R1 claim counts),
and cost/latency (wall-clock + token cost for the now 4-call
topology).

### 7. Cost accounting — reported plainly, not hidden or pre-optimized

**The full topology is now D0 → C0 → R1 → R2 — up to FOUR semantic
model calls per candidate before Stage C** (up from v2's two, and up
from the prior D0-only prototype's three). This is a material cost
increase. **Explicitly not optimized away before knowing whether C0
adds real coverage protection** — per instruction, the `>=90%`
thin-segment targeting heuristic that would have cut this cost is
REJECTED for now precisely because it's derived from the same
insufficient signal; if C0 proves highly redundant after a real probe
(low detection rate, most `missing_proposition` findings turn out to be
false alarms), cheaper targeting can be evaluated THEN, against real
data, not guessed at now.

### Explicitly not done this pass

No D0 or C0 prompt written or run. No model/API calls of any kind. No
`cj2-stage-b2-v2` frozen artifact touched. No `v2.1` assigned. No Stage
C. No cross-publisher material. No held-out material. `reader-lab/
rounds/drafts/RL-2026-001.json` untouched; RL-2026-001 responses not
inspected (round still awaiting both reviewers) and not used to design
C0's schema or any future prompt. No merge/reconciliation logic between
C0's findings and D0's claim set (deliberately deferred, see `## 2`
above). **Next real step, not taken this pass:** write the actual D0
and C0 prompts and run the small development-material probe described
in `## 6` above.

## B2 D0/C0 FIRST SEMANTIC PROBE — PREPARED, NOT EXECUTED (2026-08-12,
## new research session, EXPERIMENT-ONLY: prompts + harness + preflight
## written, STOPPED BEFORE ANY MODEL/API CALL)

Took the "next real step" named above: wrote the actual D0 and C0
prompts and preregistered the small development-material probe. **Named
explicitly as `B2 D0/C0 FIRST SEMANTIC PROBE`, NOT `v2.1`.** No model or
API call has been made against either prompt this pass, or ever, against
this topology.

### 1. D0 prompt

`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/frozen_prompts/cj2-stage-b2-d0.txt`,
SHA256 `98813045450db8f56267d7eeb1b66a3504a99748fb03c7bac8332c838fd1674d`.
Evidence-blind, generic (no B2 development-corpus examples, no H08/H17/
H14 semantics, no persona/engine/disability vocabulary, no R1/R2
terminology). Single job: extract every proposition per field, given the
field's own deterministic segmentation (segment_ids supplied by the
harness, not invented by the model), decompose compound sentences into
separate propositions (coordination, causal, attribution+embedded
content, relative clause, comparison, modality/assumption all named
explicitly with generic illustrative examples, matching this project's
existing few-shot convention), and disposition genuinely non-assertive
text as `non_propositional` with one of the existing 6 reason codes. Uses
the same "you do NOT receive X" scope-boundary convention already
established by R1's own frozen prompt (naming excluded vocabulary to
clarify scope is NOT the same thing as leaking B2 target labels into the
schema — verified structurally, not by argument, see `## 5` below).
Output schema matches `cj2_b2_d0_prototype.py`'s existing D0_SCHEMA_VERSION
`d0-prototype-0.2` exactly (claim_id/source_field/segment_ids/
exact_surface_span/atomic_claim; non_prop_id/source_field/segment_ids/
exact_surface_span/reason_code/reason_note) — the prototype module itself
is untouched, imported read-only.

### 2. C0 prompt

`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/frozen_prompts/cj2-stage-b2-c0.txt`,
SHA256 `745d6b7e11bd97a3ca20e7d52d479a63a0c0106b64283b14b8f0b6b62f948c3d`.
Evidence-blind AND D0-reasoning-blind (receives only D0's 5 allowed claim
keys, no rationale field exists in D0's schema to leak). Single job:
compare the original text against the fixed claim set's `atomic_claim`
wording and report whether any proposition the text asserts is absent,
in whole or in part — explicitly naming the same omission shapes the
adversarial audit already demonstrated (a claim spanning a whole segment
while representing only one side of a coordination/attribution/relative-
clause/comparison/assumption). Explicitly instructed not to invent
propositions that are not genuinely there. Output schema matches
`cj2_b2_c0_prototype.py`'s existing C0_SCHEMA_VERSION `c0-prototype-0.1`
exactly (`status`: `complete`|`missing_proposition`, `missing_items[]`
with segment_id/source_field/exact_surface_span/missing_atomic_claim/
reason) — the prototype module itself is untouched, imported read-only.

### 3. Harness

`automation/cj2_b2_d0c0_first_probe.py`, SHA256
`2c373944342a89e7ce99b851881d961ec1b4a27f3746f9c14faef5ec507f8f07`.
Builds D0's user message (field text + deterministic segment_ids, so the
model can only self-report segment_ids it was actually shown); builds
C0's user message (field text + segments + D0's fixed claim set,
projected to exactly its 5 allowed keys via `project_d0_claims_for_c0`,
guarding against any future D0 schema field creep leaking into C0's
input); reuses `cj2_b2_d0_prototype.compute_d0_effective_status` and
`cj2_b2_c0_prototype.{validate_c0_schema,compute_pipeline_gate}`
unmodified; defines its own standalone `_call()` rather than importing
one, for a reason worth recording as a real observation about existing
code (not acted on elsewhere this pass): `cj2_b2_v2_probe.py`'s own
`MODEL`/`MAX_TOKENS`/`TEMPERATURE` module constants are NOT what its
`_call()` actually uses at runtime — that function is imported from
`cj2_b2_probe_v1_4_1.py` and reads bare names resolved via ITS OWN
module's `__globals__`, so the R2 capacity-recovery run's "runtime
override" of `MAX_TOKENS` 5000→12000 was only possible by mutating
`cj2_b2_probe_v1_4_1`'s module attribute directly — a same-named constant
in the calling module is cosmetic, not load-bearing. This file avoids
inheriting that fragile pattern by reimplementing `_call()` standalone
with its own constants actually read by its own function body. **One
deliberate PROBE-ONLY deviation from the production gate, stated
explicitly:** `run_one_item()` calls C0 for every item regardless of D0's
own structural outcome (production would skip C0 after a D0 structural
failure, since `compute_pipeline_gate` already short-circuits on it) —
done so the probe's research questions get C0's raw behavior across the
whole corpus, not data pre-filtered by live D0 call luck.
`main()` raises `SystemExit` and refuses to run, matching
`cj2_b2_v2_probe.py`'s own precedent exactly.

### 4. Probe corpus — 8 items, dataset_purpose=development

`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/probe-corpus-v1.json`,
SHA256 `95469f6a9ba30ce9550b324bddb300d1f372e7a8d3dd8ad2e7488c00913d3e7b`.
**Deliberately contains ZERO real B2/CJ2 development-corpus material and
ZERO overlap with RL-2026-001**, by construction rather than by
selective avoidance — every item is either freshly authored for this
probe (3 items) or reused VERBATIM from
`cj2_b2_d0_adversarial_coverage_audit.py`'s existing, already-vetted,
purely-synthetic `CASES` dict (5 items: `D_relative_clause`,
`A_coordination`, `C_attribution`, `B_causal`, `F_modality`) — both
provenance claims are checked programmatically, not just asserted, by
`cj2_b2_d0c0_first_probe_static_tests.py`. Covers 8 named categories:
clean simple extraction, whole-segment omission risk (a fresh 3-sentence
field, distinct from H08's real field — the deterministic mechanism that
would catch this shape is already proven separately by
`cj2_b2_d0_h08_structural_test.py`; this item asks whether a LIVE D0 call
exhibits the failure in practice), within-segment omission risk,
compound assertion, attribution+embedded content, causal relation,
modality/assumption, and legitimate non-propositional material (a fresh
3-segment field: heading, citation/reference, rhetorical transition —
tests whether D0 correctly uses `non_propositional` instead of
manufacturing spurious claims, and whether C0 correctly reports
`complete` rather than inventing a gap where none exists).

**Note on H08/H17, recorded for transparency rather than silence:** H08's
real field and H17's real RL-2026-001 sentence were BOTH considered and
explicitly REJECTED for this corpus, even though reusing real B2 fixture
text as a diagnostic-only input has precedent elsewhere in this project
(`cj2_b2_d0_h08_structural_test.py`'s own H08 reuse;
`cj2_b2_c0_static_tests.py`'s H17-shaped diagnostic case) — precisely
because H08 and H17 are BOTH currently live as RL-2026-001's item 1 and
item 2 candidate text, and this probe's "no Reader Lab data" guarantee
is meant to be verifiable by construction, not by a case-by-case argument
about candidate-text-versus-reviewer-response provenance. The fully
synthetic corpus makes this unambiguous.

### 5. Static/preflight results

New suite `automation/cj2_b2_d0c0_first_probe_static_tests.py`, SHA256
`ffdd4c7c0abd02002b72722734c18f8384247051ef988663aaa834f06cef0c21` — ALL
CHECKS PASS, zero API calls. Covers: hash computability; corpus
segmentation matches the live segmenter exactly (also self-checked at
harness import time); expected call count is 16 (8 D0 + 8 C0); every
declared segment_id is actually exposed in D0's built prompt; C0's
projection strips any key beyond its 5 allowed D0-claim keys and
preserves the claim_id set exactly; the fail-closed gate still blocks on
a malformed C0 result and on a genuine C0-reported omission (re-exercised
against THIS harness's own call sites, not a re-run of the other,
unmodified suites); no B2-v2 factuality vocabulary or persona/engine/
disability identity appears anywhere in either prompt; no real H08/H17
fixture text appears in either prompt OR the corpus (cross-checked
against `cj2_b2_d0_h08_structural_test.H08_INTERPRETIVE_INFERENCE`,
imported, and a literal verification copy of the real H17 sentence — that
file defines it inline rather than at module scope, so it is copied here
for cross-check purposes only, not imported, and the source file it was
copied from is unmodified); every corpus item's provenance is one of
exactly two whitelisted kinds, cross-checked against
`cj2_b2_d0_adversarial_coverage_audit.CASES`'s actual text, not the
provenance string's say-so; no source-evidence field appears as a JSON
schema key in either prompt. Re-ran every PRE-EXISTING suite unmodified
this pass too: `cj2_b2_d0_static_tests.py` PASS, `cj2_b2_d0_h08_
structural_test.py` PASS (6/6), `cj2_b2_d0_adversarial_coverage_audit.py`
CONFIRMED/PASS, `cj2_b2_c0_static_tests.py` PASS, `cj2_b2_v2_static_
tests.py` PASS (frozen file untouched). One earlier miscalibration in
this pass's own first draft of the new suite, caught and fixed before
being reported here: an initial version banned bare English words
("claims", "support", "safe", "importance", "evidence excerpt") as if
their mere appearance anywhere in the prompt text were a leak — this
false-failed on the prompts' own correct, deliberate use of R1's
established "you do NOT receive X / you must NOT judge Y" scope-boundary
convention (naming excluded vocabulary to explain scope is not the same
thing as leaking it into the OUTPUT SCHEMA). Corrected to check for
schema-KEY-shaped leakage (`"word":` patterns) instead of bare-word
presence — the real risk the instruction was protecting against.

### 6. Preregistration record

`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/preregistration-first-probe.json`
— all artifact hashes (prompts, harness, static suite, corpus manifest,
plus the D0/C0 prototype modules themselves, confirmed unmodified),
model/call parameters (`openrouter/claude-sonnet-4.6`, temperature 0.0,
D0 max_tokens 3000, C0 max_tokens 2000, timeout 120s, no retry policy),
expected call count (16), `dataset_purpose: "development"`, the explicit
negative-statement block (no Reader Lab data, no held-out/cross-publisher
material, no Stage C, no `v2.1`, no frozen-file modification, no
production/Cloudflare/D1 access, 0 model/API calls made this pass), the
predefined outcome taxonomy (D0: complete/omission/schema_invalid/
call_failed; C0 relative to a human/researcher reference: true_detection/
false_alarm/miss/correct_complete/boundary_uncertain — never model output
judging model output, never Reader Lab responses, never treated as
ground truth for scoring itself), the 7 research questions from `## 6`
above verbatim, and 5 known risks (same-model correlated bias; C0
false-alarm risk; small synthetic corpus doesn't generalize to real
multi-field candidates; the PROBE-ONLY gate deviation has no production
analogue; MAX_TOKENS is a headroom estimate, not empirically derived from
this corpus's own token counts the way B2-v2's R2 MAX_TOKENS was).

### Explicitly not done this pass

No model or API call of any kind, against D0, C0, or anything else. No
`v2.1` assigned. No Stage C. No cross-publisher or held-out material. No
Reader Lab data used, read, or polled — RL-2026-001 remains untouched,
still awaiting both reviewers; H08/H17's real text was deliberately kept
OUT of this probe's corpus for that reason (see `## 4` above), not
merely avoided from analysis. No `cj2-stage-b2-v2` frozen artifact
touched. No `cj2_b2_d0_prototype.py`/`cj2_b2_c0_prototype.py`
modification — both imported read-only, hashes confirmed unchanged from
their already-tested state. No production wiring, Cloudflare, or D1
access. **Next real step, not taken this pass: execute the 16 calls
against the corpus above, with explicit authorization, and score the
results against the predefined outcome taxonomy in `## 6` (this
section's numbering) of the preregistration record.**

## B2 D0/C0 FIRST SEMANTIC PROBE — REVISION 2 (CONTROLLED C0 CHALLENGE
## ARM ADDED, 8+8+4=20 CALLS) + EXECUTED, 2 ATTEMPTS — RESULTS
## (2026-08-12, new research session continuing an interrupted handoff)

**Reconstruction note.** This pass began by reconstructing state from
disk after a prior session's context ran out mid-preparation. Revision 2
(the controlled C0 challenge arm below) had already been fully written
to `challenge-corpus-v1.json`, `reference-manifest-v1.json`,
`preregistration-first-probe.json` (revision 2), and `pre-run-identity.json`
on disk, but the corresponding narrative update to THIS file was never
made before context ran out — `.claude/current-work.md`'s own pointer
still said "16 = 8 D0 + 8 C0" with no mention of a challenge arm at all.
Verified this precisely rather than trusting the handoff's own framing:
every JSON file parses strictly (no duplicate keys, checked with a
custom `object_pairs_hook`), every `.py` file both compiles and imports,
all 10 artifact hashes in `preregistration-first-probe.json` and all 10
in `pre-run-identity.json` were independently recomputed from the actual
files on disk and matched exactly, and `expected_call_count.maximum_total`
is unambiguously `20` everywhere — no stale "16" survived anywhere in
the harness, static suite, or preregistration text.

### Revision 2 design: the controlled C0 challenge arm

Both prompts are BYTE-IDENTICAL to revision 1 (hashes above,
unchanged) — the challenge arm is implemented entirely as corpus/harness/
reference-manifest plumbing, per instruction not to tune either prompt
around it. Resolves revision 1's own denominator problem: if D0 happens
to decompose all 8 natural items completely, there are zero known
omissions for C0 to detect, and "C0 detection rate" is unmeasurable on
the natural arm alone (this is exactly what happened — see `### Natural
arm results` below).

4 new items in `automation/.probe_fixtures/cj2-b2-d0c0-first-probe/challenge-corpus-v1.json`
(SHA256 `7555b31a46cdd56bcc278d3c74dd5272b6c227be3587e92edd49a1503440d55d`):
D0 is NEVER called for this arm — each item carries a hand-built,
structurally-valid (schema/span/segment-consistency all independently
re-verified against `cj2_b2_d0_prototype.compute_d0_effective_status`),
deliberately-incomplete `fixed_claim_set` reproducing the exact "claim
spans the whole segment but represents only one of two propositions"
shape the 2026-08-12 adversarial audit proved D0's own bookkeeping
cannot catch. Each item has exactly ONE preregistered omitted
proposition (`reference-manifest-v1.json`, SHA256
`ebb57094452c9bdf2826162e836b5ee4a9e44623ec1b4f69be04849abbf68b40`) —
semantic, not a schema trick, and never disclosed to C0: no challenge
label, no expected answer, no statement that anything was removed. The
reference manifest is SCORING-ONLY, verified both structurally (a
dedicated static-suite check) and by direct inspection of
`build_c0_user_for_challenge()` — never enters any model payload.
Terminology used throughout: "preregistered synthetic reference" /
"controlled reference," never "ground truth" unqualified.

Expected call count revised to **20 maximum** (8 D0 + 8 C0-natural + 4
C0-challenge) — `preregistration-first-probe.json` revision 2 (SHA256
`c142fec483c11bab14c13ec7655d568bfc6e83df351f249cd1463d5431d5ac76`) and
`pre-run-identity.json` (SHA256
`823ce61f2caf189976d440c7c74f4774a6e0516831e9945c2bc19adf7a0f5956`) both
finalized and independently hash-verified against the actual files this
pass — pre-run-identity's own self-reference note correctly excludes its
own hash from itself. All 6 static/preflight suites (`cj2_b2_d0_static_tests.py`,
`cj2_b2_d0_h08_structural_test.py`, `cj2_b2_d0_adversarial_coverage_audit.py`,
`cj2_b2_c0_static_tests.py`, `cj2_b2_v2_static_tests.py` [frozen, untouched],
`cj2_b2_d0c0_first_probe_static_tests.py`) re-run this pass, all PASS,
zero explicit failures, zero API calls — including the new suite's
20 challenge-arm-specific checks (single preregistered omission per
item, no leakage of the omitted proposition's distinctive terms into the
kept claim, no reference-manifest content in any built model payload,
the stop-rule classifier's own unit tests, and a mechanical proof that
`probe._call.__globals__` is this harness module's own namespace, not an
imported module's).

### Execution: 2 attempts, per the preregistered stop-rule design

**Attempt 1 — CONFIG_FAILURE, stopped after 1 call (correctly).** Set up
a fresh isolated scratch on trident (`cj2_b2_d0c0_first_probe.py`,
`cj2_b2_d0_prototype.py`, `cj2_b2_c0_prototype.py`,
`cj1_v3_anchor_resolver.py`, both frozen prompts, both corpora,
reference manifest, preregistration, pre-run-identity), hash-verified
byte-identical to local before running anything. `run_probe()`'s first
call (`d0`/`1_clean_simple`) returned `HTTPError 401: Unauthorized`.
`classify_call_outcome()` correctly classified this as `config_failure`
(401 is in `_CONFIG_FAILURE_HTTP_STATUSES`) and the run STOPPED
immediately, exactly as designed — 1 call made, 0 completed, the one
attempted call's error persisted to disk before the stop was returned.
Root-caused, not guessed at: CLIProxyAPI (`/home/jascha/cliproxyapi/`,
port 8317) now enforces `api-keys` authentication
(`{"error":"Missing API key"}` / `{"error":"Invalid API key"}` on a bare
`curl` probe) — consistent with the already-recorded memory that this
key was rotated 2026-08-07 after a public-repo exposure incident. This
harness's `_call()`, like every prior B2 `_call()` (`v1.4.1`, `v2`),
defaults `CLIPROXY_KEY` to an empty string; whatever made the empty
default work for the v1.2/v1.3/v1.4.1/v2 regression runs no longer
holds. This is a genuine EXECUTION CONFIGURATION FAILURE, distinct from
an experiment result, exactly the category the stop-rule design exists
to catch — **not** a probe/harness/prompt defect. Preserved at
`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/results-attempt-1-config-failure-20260812/`
(`full_results.json` SHA256 `22567ba1b64af869c9e92eac56ca3e55e29bcdfef78a7dbca579c92f3dc0e5ff`,
`run_summary.json` SHA256 `b98c4e54d83930eb9dfc56e79bc7ccd4cbdfa97d8e0275810dc567510aba811f`,
`d0/1_clean_simple.json` SHA256
`5d8ef112cda1b6b139c5574cc880faedccf750c818b7ec74ddba3a51cbb81d95` —
contains only the error record, no candidate text, no key material),
hash-verified local vs. trident before the trident scratch was removed.
**Per the preregistration's own stop-rule text — "fixing infrastructure
... requires a NEW, separately recorded execution attempt with its own
preregistration note, not a silent retry inside this one" — attempt 1 is
closed here, not silently retried.**

**Attempt 2 — EXECUTED, COMPLETE, 20/20 calls, no stop.** A fresh,
separate scratch directory on trident (not attempt 1's), same exact
bundle, independently hash-verified byte-identical to local (including
the harness itself) before running anything. The live client-facing key
CLIProxyAPI now requires was located in `/home/jascha/cliproxyapi/config.yaml`'s
own `api-keys:` list (the service's own configuration, not a third-party
secret) and passed directly as the `CLIPROXY_KEY` environment variable
for this one process invocation only — never echoed into any file this
session wrote, never committed, never placed in this document or
`current-work.md`. `run_probe()` completed all 20 calls in ~70 seconds
wall-clock, `stopped: false`, `stop_reason: null` — d0: 8/8, c0_natural:
8/8, c0_challenge: 4/4. All 22 output artifacts (20 per-call results +
`run_summary.json` + `full_results.json`) copied back to
`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/results-attempt-2-20260812/`
and hash-verified local vs. trident, byte-identical on every file
(`full_results.json` SHA256
`0a4a823aa33e1e50973a381249bae35a0d67d357c3c8c55a7485b57b969dde8c`,
`run_summary.json` SHA256
`708930d47b59df8fc36eb7558583a859968cf98d61f280688da8d45c9ef7ddf0`) — no
mismatch found. Both trident scratch directories removed only after
local copies existed, hashes matched, and all expected artifacts were
accounted for. No prompt/schema/harness edit of any kind between
attempt 1 and attempt 2 — only the missing credential was supplied.

### A harness-extraction issue found live (logged separately from the
### semantic findings, same discipline as the FIRST REFERENCE PROBE's
### own JSON-extraction bug)

**4 of 8 D0 natural calls and 2 of 4 C0 challenge calls returned content
this harness's naive `json.loads(text)` could not parse, even though the
model's actual content was well-formed.** Two distinct sub-patterns,
both mechanically recorded as `call_failed` per the preregistered
taxonomy (a correct classification under the stop-rule design — this is
an EXPERIMENT RESULT, not a config failure, and correctly did not stop
the run):

- **D0 items `1_clean_simple`, `4_compound_coordination`,
  `5_attribution_embedded`, `7_modality_assumption`:** the model wrapped
  otherwise-perfect JSON in a ` ```json ... ``` ` markdown code fence.
  Diagnostic-only re-parse (stripping the fence, NO new API call, NOT a
  retroactive edit of the recorded run — the mechanically-recorded
  `call_failed` outcome for these 4 items stands as the formal result)
  confirmed all 4 are schema-valid AND `d0_effective_status: "valid"`
  once the fence is stripped, run through the same
  `compute_d0_effective_status`/`validate_d0_field_coverage_schema`
  checks the harness itself uses.
- **C0 challenge items `ch2_attribution_reversed`, `ch4_modality_reversed`:**
  the model prefixed several sentences of free-form reasoning before an
  otherwise-correct trailing ` ```json ``` ` block — the same "unrequested
  prose before the JSON despite an explicit no-other-text instruction"
  failure mode already logged for Stage C in the FIRST REFERENCE PROBE
  section above, now observed in C0 too. Diagnostic-only extraction of
  the trailing JSON block (same discipline as above) confirmed both are
  schema-valid.

**Consequence for scoring, stated precisely:** because `run_probe()`
builds each item's C0 user message from `(d0_call.get("parsed") or {}).get("claims", [])`,
a D0 `call_failed` (fence-wrapped, not actually incomplete) silently
became an EMPTY fixed claim set for that item's own C0 call — items
`1_clean_simple`, `4_compound_coordination`, `5_attribution_embedded`,
`7_modality_assumption`'s natural-arm C0 tests are **confounded**: C0
correctly reported every proposition in the text as missing, but this is
uninformative about C0's true detection ability, since D0 never actually
produced the omission C0 was reacting to — it reacted to a harness
artifact, not a real gap in D0's reasoning. This is a NEW confound,
distinct from the already-known "PROBE-ONLY gate deviation" (C0 called
after a D0 structural failure) — both are real, and both are reported
as such rather than folded into the main findings. **Not fixed or
re-run this pass** — per instruction, this is a harness issue to log,
not a semantic finding to patch, and re-running the 4 affected items
alone would be a "selective rerun of surprising items," explicitly
prohibited.

### Natural arm results (8 items) — scored against
### `reference-manifest-v1.json`'s `natural_arm_items`, human-inspected,
### never model-output-judging-model-output

| item | D0 mechanical | D0 true (fence-stripped, diagnostic only) | matches reference | C0 mechanical | C0 informativeness |
|---|---|---|---|---|---|
| 1_clean_simple | call_failed (fence) | complete, 1/1 claim | yes | missing_proposition (1 item) | **confounded** — reacting to empty set, not a real D0 gap |
| 2_whole_field_omission_risk | complete, 3/3 claims | — | yes | complete | **correct_complete** |
| 3_within_segment_relative_clause | complete, 2/2 claims | — | yes | complete | **correct_complete** |
| 4_compound_coordination | call_failed (fence) | complete, 2/2 claims | yes | missing_proposition (2 items) | **confounded** |
| 5_attribution_embedded | call_failed (fence) | complete, 2/2 claims | yes | missing_proposition (1 item) | **confounded** |
| 6_causal_relation | complete, 3/3 claims (captured the causal-link claim itself, the strict 3-proposition reading) | — | yes | complete | **correct_complete** |
| 7_modality_assumption | call_failed (fence) | complete, 2/2 claims | yes | missing_proposition (1 item) | **confounded** |
| 8_legitimate_non_propositional | complete, 0 claims / 3 non_propositional, all 3 `reason_code`s matching the reference's own expected codes exactly | — | yes (perfect) | **missing_proposition (2 of 3 non-prop segments flagged)** | **genuine — FALSE ALARM** |

**Headline finding 1: D0's TRUE natural-arm performance, once the
harness bug is looked through, is 8/8 complete, zero omissions —
including the two hardest-designed cases** (item 6's 3-proposition
causal-link reading captured in full; item 8's non-propositional
material correctly excused with the exact expected reason codes, zero
spurious claims manufactured). This is exactly the denominator problem
the challenge arm was added to solve, playing out as predicted: the
natural arm alone produced zero known D0 omissions for C0 to be tested
against.

**Headline finding 2, the more consequential one: item 8 is a genuine,
unconfounded C0 FALSE ALARM.** D0 handled the direct non-propositional
test perfectly. C0, given that same correct, empty-of-claims (for
propositional content) input, invented two "missing propositions" —
"the full dataset is in appendix B" and "the following section
addresses limitations" — out of a citation/reference line and a purely
rhetorical transition sentence that the reference manifest explicitly
designed to have ZERO genuine propositions. This is the mirror-image of
the omission failure C0 exists to catch: C0 over-eagerly treating
non-assertive scaffolding text as substantive missing content. Not
hypothetical or a boundary case — the reference manifest's own
`boundary_notes` for this item states plainly "Zero genuine propositions
expected," and both flagged spans are exactly the citation/rhetorical
material the item was built to test.

### Controlled challenge arm results (4 items) — scored against
### `reference-manifest-v1.json`'s `controlled_challenge_arm_items`

| item | mechanical outcome | recovered content (diagnostic-only prose/fence-strip where needed) | detected the exact preregistered omission? | extra flagged omissions? |
|---|---|---|---|---|
| ch1_comparison | clean, schema-valid | "Use rose among teenagers" | **YES, exact match** | none |
| ch2_attribution_reversed | call_failed (prose preamble before JSON) | "The report claims that the new policy reduced waiting times" | **YES, exact match** | none |
| ch3_coordination | clean, schema-valid | "Traffic was rerouted through the old town" | **YES, exact match** | none |
| ch4_modality_reversed | call_failed (prose preamble before JSON) | "The plan presumes that most residents already own a smartphone" | **YES, exact match** | none |

**Headline finding 3: C0 detected the exact preregistered omission in
4/4 challenge items at the content level (2/4 mechanically clean,
2/4 recoverable only via diagnostic extraction of a trailing JSON
block).** This is the first live confirmation that C0 can catch the
specific "claim spans the whole segment but represents only one of two
propositions" omission shape the 2026-08-12 adversarial audit proved
D0's own deterministic bookkeeping cannot catch — answering this
probe's second research question directly, and resolving the natural
arm's own denominator problem. None of the 4 proposed an additional,
unpreregistered omission beyond the single target — no
`detected_target_plus_extra_possible_omission` cases observed.

### Cost/latency

Only aggregate wall-clock was captured this pass: 20 calls in ~70
seconds (~3.5s/call average). **Real limitation, not filled in
retroactively:** `_call()` discards the response body's `usage` field
along with everything except `choices[0].message.content`, so no
per-call token counts exist for this run — the corresponding research
question ("how expensive/slow are D0 and C0... tokens, latency") is only
partially answered (latency: roughly characterized; tokens: not
captured at all). Not re-run to fix this, per instruction against
selective reruns.

### Interpretation

**What this probe establishes:** C0 has a REAL, demonstrated ability to
catch the specific omission shape (whole-segment-span, partial-
proposition) that motivated its own design, at 4/4 on a small, synthetic,
single-shape challenge set — a genuine incremental capability D0's
deterministic bookkeeping alone cannot provide (confirmed structurally
by the adversarial audit, now confirmed behaviorally). It also has a
REAL, demonstrated false-alarm failure mode on legitimate non-assertive
material (item 8) — not a boundary case, a clean miss on the direct
positive control. Both findings are equally load-bearing; neither should
be read alone. The natural arm, once the harness's fence-stripping gap
is looked through, shows D0 performing cleanly across all 8 designed
traps in this small sample, which is itself informative (it means this
probe's natural-arm C0 tests could not exercise true-detection at all —
not evidence C0 "isn't needed," just evidence this particular n=8 sample
didn't surface a natural D0 miss).

**What this probe does NOT establish:** production robustness, real B2
robustness, generalization to long/multi-field/multi-paragraph candidate
text (both corpora are single-sentence, single-segment items by design),
or independence between D0 and C0 (same model, two separate blind calls
— `FIRST_PROBE_MODEL_DECISION`'s own framing, unchanged: this is a
"separate evidence-blind coverage audit," never "independent model
adjudication"). The item-8 false-alarm rate (1 finding, 2 spurious
missing_items) is a single data point, not a measured false-alarm RATE
— generalizing "C0 has an X% false-alarm rate" from n=1 would overclaim.
The challenge arm's own known limitation (preregistered in
`known_risks`) also applies unchanged: it tests only the one omission
shape found by the adversarial audit, authored by the same researcher
who wrote the reference manifest, so a bias toward "easy," cleanly-
separable omissions is possible.

### Confirmed, explicitly

No semantic tuning of either prompt after seeing results. No `v2.1`. No
Stage C. No cross-publisher or held-out material. No Reader Lab data
used, read, or polled — RL-2026-001 remains untouched. No selective
rerun of the 6 fence/preamble-affected items, despite knowing what they
"really" said. No `cj2-stage-b2-v2` frozen artifact touched. No
`cj2_b2_d0_prototype.py`/`cj2_b2_c0_prototype.py` modification — both
still imported read-only. No production/Cloudflare/D1 access. The two
harness-extraction issues found (markdown-fence wrapping, prose-before-
JSON preamble) are logged here as harness issues for a future pass to
consider, NOT acted on this pass — no fence-stripping or preamble-
tolerant parsing was added to `cj2_b2_d0c0_first_probe.py` itself.
**Next real decision, not made this pass: whether a harness-level fix
(tolerant JSON extraction, matching what Stage C's own probe eventually
needed) is worth making before any second D0/C0 probe, and whether C0's
item-8-shaped false-alarm risk on non-propositional material is common
enough, across a larger and still-synthetic sample, to warrant a C0
prompt revision — no such revision designed or drafted this pass.**

## B2 D0/C0 FIRST SEMANTIC PROBE — NARROWLY-SCOPED RECOVERY PASS
## (2026-08-12, same day): PARSE NORMALIZATION + NATURAL-C0
## INPUT-RECOVERY RUN — COMPLETE, RESULTS SCORED

Explicit scope, per instruction: no semantic prompt tuning of D0 or C0.
This is a harness/execution-defect recovery, not a v2.1. The original
Attempt 2 mechanical results, above, are preserved exactly as executed
— nothing below overwrites or reinterprets them away; a new,
separate artifact class ("POST-HOC PARSE RECOVERY") is introduced
instead.

### 1. Exact format-failure classification (not "markdown fence
### failures" collapsed into one bucket)

Mechanically inspected all 6 of Attempt 2's `json.loads()` failures
(regex-based fence detection + validity check on each fenced block +
whitespace-only check on everything outside it — not eyeballed):

| class | count | items |
|---|---|---|
| A — pure JSON inside one fence, nothing else outside (not even whitespace-adjacent prose) | 4 | d0/`1_clean_simple`, d0/`4_compound_coordination`, d0/`5_attribution_embedded`, d0/`7_modality_assumption` |
| B — fence preceded by substantive prose (1109 and 794 chars respectively) | 2 | c0_challenge/`ch2_attribution_reversed`, c0_challenge/`ch4_modality_reversed` |
| C — multiple candidate JSON blocks | 0 | none observed |
| D — truncated/incomplete JSON | 0 | none observed |
| E — other | 0 | none observed |

Class A is exactly the "harmless formatting wrapper" hypothesis: the
model's actual content is unambiguous once the fence is stripped. Class
B is NOT — it is the model violating an explicit JSON-only output
contract with substantial free-form reasoning prose, which a permissive
parser could silently paper over in a way that hides a genuinely
different failure (e.g. two conflicting conclusions, one in prose one in
JSON). The two classes are never merged in anything below.

### 2. The normalizer (deterministic, conservative, NOT a permissive
### "find `{...}` anywhere" parser)

New module `automation/cj2_b2_d0c0_output_normalizer.py` (SHA256
`a32d897bcb82dfab9084c9bd966e993da23025e18dd7d4673c3c33f5a156af0c`),
static suite `cj2_b2_d0c0_output_normalizer_static_tests.py` (SHA256
`85a9c16dad249908290fce8213b558f7a093805fa484ff1a10a2672ec3dd667b`).
Rule: (1) try strict
`json.loads(raw)`; (2) else, recover ONLY if there is EXACTLY ONE fenced
block AND everything outside that fence, stripped, is empty AND the
fence's own content parses as valid JSON; (3) otherwise `parsed=None`,
`recovery="rejected"`, with a machine-readable `reason`. Class B is
REJECTED by construction (condition 2's "everything outside is empty"
fails) — the normalizer does not, and structurally cannot, recover it.
Static suite `cj2_b2_d0c0_output_normalizer_static_tests.py`, 32/32
PASS, zero API calls — covers plain JSON, Class-A fences (with and
without a `json` language tag, with and without surrounding
whitespace), Class-B prose-before-fence AND prose-after-fence (both
correctly rejected), multiple fences (rejected, never "pick one"),
truncated JSON inside a fence and truncated bare JSON (both rejected,
never coerced/repaired), non-JSON entirely, a fence wrapping non-JSON
prose by mistake, a `raw=None` transport case, a direct proof that
recovered content is byte-identical to strictly parsing the isolated
fence body (no semantic transformation), and — the load-bearing check —
direct execution against the ACTUAL 6 Attempt-2 raw outputs: all 4
Class-A cases recover, both Class-B cases stay rejected with
`reason="substantive_text_outside_single_fence"`.

Did NOT implement: a permissive brace-scan, acceptance of arbitrary
prose merely because valid JSON appears later, or any repair/coercion of
malformed JSON. No D0 or C0 prompt, schema, corpus, or reference-
manifest file was touched to build this module.

### 3. Offline reparse of Attempt 2 (zero API calls) — full recovery table

`automation/.probe_fixtures/cj2-b2-d0c0-first-probe/offline-parse-
recovery-20260812/recovery-table.json` — every one of Attempt 2's 20
result files reparsed via the normalizer above, original raw/result
files never modified (new artifact directory, separate from
`results-attempt-2-20260812/`).

**D0 recovery — reported as two separate numbers, never collapsed:**

> ORIGINAL MECHANICAL D0: 4 parsed / 4 parser-failed
> RECOVERED D0 SEMANTIC INTERPRETATION (Class A only, via the approved normalizer): 8/8 complete, 0 omissions — matches the preregistered synthetic reference exactly on every item, including item 6's full 3-proposition causal-link reading and item 8's 3/3 correctly-excused non-propositional segments.

**Controlled C0 recovery — reported as three separate numbers, never
collapsed, per instruction not to hide non-compliant outputs:**

> MECHANICAL: 2/4 parsed (`ch1_comparison`, `ch3_coordination`) / 2/4 call_failed (`ch2_attribution_reversed`, `ch4_modality_reversed`)
> PARSE-RECOVERED under the approved conservative normalizer: still 2/4 — `ch2`/`ch4` are Class B and are correctly NOT recovered by the normalizer; they remain `recovery="rejected"`, formally non-compliant with the JSON-only contract.
> DIAGNOSTIC-ONLY reading (manual extraction of the trailing JSON block for `ch2`/`ch4` — explicitly NOT the approved normalizer, NOT used for any scoring pipeline, reported only as a separate human observation): RECOVERED SEMANTIC RESULT: 4/4 controlled omissions detected, with a formatting-compliance caveat — 2 of those 4 (`ch2`, `ch4`) reached that content only by violating the "no other text" instruction, which is itself a real, unresolved compliance problem, not something this recovery pass fixes or hides.

### 4. Natural C0 — confounded items marked explicitly, never scored as a
### semantic category

Per instruction, Attempt 2's own natural-arm C0 results for the 4 items
whose D0 output originally failed to parse are re-labeled, in this
record, as:

> `CONFOUNDED_BY_HARNESS_INPUT_CORRUPTION` — `1_clean_simple`, `4_compound_coordination`, `5_attribution_embedded`, `7_modality_assumption`

— never `miss`, `false_alarm`, `true_detection`, or `correct_complete`.
Reparsing Attempt 2's OLD D0 output after the fact cannot repair the
INPUT C0 actually saw at call time (an empty claim set) — that requires
a new C0 call against the corrected input, which is exactly what `## 5`
below does.

### 5. Natural C0 input-recovery run — new experiment, EXECUTED

**Frozen input**, built offline from Attempt 2's own raw D0 outputs (4
items via the normalizer's `single_fence_recovered` path, 4 items
already directly parsed in Attempt 2, never failed):
`.probe_fixtures/cj2-b2-d0c0-first-probe/offline-parse-recovery-20260812/frozen-recovered-d0-claims-v1.json`,
SHA256 `a1658230894dd9819cb8c8de0fea0ca3025c8cb5d08a85c6a5a551d2f855d0eb`
— every item's projected (5-allowed-key) claim set individually hashed,
reproducibility of each hash re-verified mechanically from
`full_d0_parsed` by the static suite (not just asserted).

**New harness** `cj2_b2_d0c0_natural_c0_recovery.py` — imports
`C0_SYSTEM`/`C0_MAX_TOKENS`/`build_c0_user`/`_call`/
`classify_call_outcome` from the ORIGINAL, unmodified
`cj2_b2_d0c0_first_probe.py` (never reimplements or edits any of them);
has no code path that can reference `CHALLENGE_CORPUS` or call D0 at
all (`EXPECTED_D0_CALLS = 0`, `EXPECTED_C0_CHALLENGE_CALLS = 0`,
enforced structurally, not just documented). Static suite
`cj2_b2_d0c0_natural_c0_recovery_static_tests.py`, 68/68 PASS, zero API
calls — plan is exactly 8 `c0_natural_recovery` calls; C0 prompt hash,
`build_c0_user` object identity, `_call` object identity, model/
temperature/max_tokens/timeout all verified identical to the original
probe; the 4 previously-confounded items now carry non-empty claim
sets (the whole point of this recovery); item 8 legitimately still has
zero claims (never confounded, not a bug); no reference-manifest
structural marker leaks into any built C0 user message.

Preregistration:
`.probe_fixtures/cj2-b2-d0c0-first-probe/cj2_b2_d0c0_natural_c0_recovery_preregistration.json`,
SHA256 `8f3d6e84a67025bbaa125d21c4773b9178ee420b0437e19d4834ff6a37bea24b`
— states explicitly: changed from the original probe is ONLY runtime
input plumbing (which D0 claim set C0 is shown for the 4 previously-
confounded items); no C0 prompt/schema/corpus/reference-manifest
change; expected calls d0=0/c0_natural=8/c0_challenge=0.

**Execution:** fresh isolated trident scratch, full bundle hash-verified
byte-identical local vs. trident before running anything (12 files).
`run_recovery()` completed all 8 calls in ~15 seconds, `stopped: false`.
All 10 output artifacts (8 per-call results + `run_summary.json` +
`full_results.json`) copied back and hash-verified byte-identical
(`full_results.json` SHA256
`ffa38e55071d8a71a125ea224ff240a60b1d2474207365d8ec0e99962717bd9f`).
Trident scratch removed only after local verification completed. No D0
call made. No challenge-arm call made. No retries.

### 6. Natural C0 recovery results — full, unconfounded scoring

All 8 schema-valid (`validate_c0_schema`, re-checked directly, not
assumed from `http_status`), zero `call_failed`, zero `schema_invalid`,
zero `boundary_uncertain`.

| item | recovered D0 input (n claims) | C0 result | scored category |
|---|---|---|---|
| 1_clean_simple | 1 (was empty, now recovered) | `complete` | **correct_complete** |
| 2_whole_field_omission_risk | 3 (unchanged, never confounded) | `complete` | **correct_complete** |
| 3_within_segment_relative_clause | 2 (unchanged, never confounded) | `complete` | **correct_complete** |
| 4_compound_coordination | 2 (was empty, now recovered) | `complete` | **correct_complete** |
| 5_attribution_embedded | 2 (was empty, now recovered) | `complete` | **correct_complete** |
| 6_causal_relation | 3 (unchanged, never confounded) | `complete` | **correct_complete** |
| 7_modality_assumption | 2 (was empty, now recovered) | `complete` | **correct_complete** |
| 8_legitimate_non_propositional | 0 (unchanged, never confounded, correctly empty) | `missing_proposition` (2 items: the same appendix-B citation span AND the same "following section addresses limitations" rhetorical-transition span as Attempt 2) | **false_alarm — REPRODUCES Attempt 2's exact shape** |

**Totals: 7/8 correct_complete, 1/8 false_alarm, 0/8 true_detection, 0/8
miss, 0/8 boundary_uncertain, 0/8 schema_invalid, 0/8 call_failed.**

**Item 8 reproduces exactly.** Same two spans flagged (`seg2`'s citation/
reference sentence, `seg3`'s rhetorical-transition sentence), same
`missing_atomic_claim` wording, functionally the same `reason` text —
across two independent calls, same model, `temperature=0.0`, same
input. This is evidence of self-consistency given this EXACT input, not
evidence the failure generalizes to other citation/rhetorical examples
— that would require new items, not a rerun of this one, and is
explicitly out of scope for this pass.

**Because D0 was 8/8 complete (confirmed twice now — offline-recovered
in `## 3` above, and re-confirmed as the literal input to this run), the
natural arm produced ZERO opportunities for `true_detection` or `miss`
— exactly as anticipated. The only informative natural-arm C0 metric
from this probe is its false-alarm rate: 1/8 (12.5%), on the single item
built to test non-propositional handling, not a random draw.**

### Confirmed, explicitly (recovery pass)

No D0 prompt edit. No C0 prompt edit. No schema/enum change. No
corpus/reference-manifest edit. No `v2.1`. No Stage C. No Reader Lab
data. No re-run of the controlled challenge arm (its 2 non-compliant
outputs are reported via diagnostic reading only, per `## 3` above, not
re-called). No selective re-run of only the previously-confounded 4
items — all 8 natural items were re-run uniformly, avoiding a hybrid
4-old + 4-new dataset. No threshold invented after seeing results.

### Interpretation

**What this recovery pass now demonstrates:** D0's true natural-arm
performance is 8/8 complete (confirmed on a rigorous, deterministic,
narrowly-scoped normalizer basis, not ad hoc fence-stripping). C0's true,
now-fully-unconfounded natural-arm behavior is 7/8 `correct_complete`
and exactly 1/8 `false_alarm`, with the false alarm reproducing
identically across two independent calls at temperature 0. The
controlled challenge arm still shows 4/4 correct semantic detection at
the content level, but 2 of those 4 reached that content only via a
JSON-only-contract violation the normalizer correctly refuses to paper
over.

**What remains unresolved:** C0's actual detection sensitivity against
a genuine D0 omission is still completely unmeasured — this corpus
(natural or challenge) has never produced one for C0 to be tested
against on the natural arm; only the challenge arm's HAND-BUILT
omissions test detection at all. Whether item 8's false-alarm shape
generalizes beyond this exact citation/rhetorical example is unresolved
— two identical-input replications establish self-consistency, not
generalization; that needs new, differently-worded non-propositional
items, not attempted here. The Class-B "prose before JSON" contract
violation (2/4 challenge calls) remains completely unaddressed by this
pass — normalizing it away was explicitly rejected as unsafe, and no
prompt-level fix for it was designed. **Whether C0's false-alarm
behavior is systematic enough to justify a future semantic revision:
NOT YET DECIDABLE from n=1 item (even with 2 reproducing calls) — a
larger, differently-worded synthetic sample of non-propositional
material would be needed before that decision, and none was collected
this pass, per instruction to stop here.**

## B2 D0/C0 REAL-MATERIAL TRANSFER PROBE — EXECUTED, RESULTS SCORED
## (2026-08-13, new session continuing the D0/C0 track)

Purpose: test whether the synthetic first probe's findings transfer to
real, already-exposed B2 development material. NOT `v2.1`. No D0/C0
prompt/schema revision at any point this pass.

### PRE-RUN — corpus eligibility audit

A direct conflict was caught before any corpus was built: the task's own
suggested examples (H08, H17, H14, H05, De Hooch/Z) are literally
RL-2026-001's 5 currently-assigned candidate texts (round still
`PUBLISHED/LIVE/ACTIVE`, awaiting both reviewers, per this file's own
READER LAB v0 section) — the identical conflict this project already
hit once in the synthetic first probe. Flagged to the user before
proceeding; user chose to exclude all 5 from every role (Arm A, Arm B,
and as design examples) and require an explicit eligibility table rather
than inferring membership from fixture proximity.

**Eligibility audit**
(`.probe_fixtures/cj2-b2-d0c0-real-material-transfer-probe/eligibility-table.json`,
SHA256 `41c2004f7fe2cb6e62d2527533ee5e70fe2af90b953b405c5c8dda8062697062`):
checked all 18 `cj2-fresh-batch-1` candidates (H01-H18) plus De Hooch/Z
against current-work.md's own explicit RL-2026-001 assignment list —
**clean eligible pool: 14** (H01,H02,H03,H04,H06,H07,H09,H10,H11,H12,H13,
H15,H16,H18), all confirmed development/not-held-out via
`acceptance-matrix-v2-preregistered.json`'s batch-wide provenance
statement ("Development evidence, not held-out. No cross-publisher
batch spent."), all with exact verbatim text recovered from
`automation/.probe_fixtures/cj2-fresh-batch-1/human-review-packet-v1.1.md`.
Well above the ~5-item underpowered threshold — no stop triggered, no
padding needed.

**Split**: Arm A (natural) = 10 items (H01,H02,H03,H04,H06,H07,H09,H10,
H12,H13), all 5 candidate-reasoning fields each (engine_move,
seed_engagement, interpretive_inference, conceptual_shift,
claimed_contribution) — genuinely richer, multi-field, multi-sentence
real material, unlike the synthetic corpus's single-sentence fields.
Arm B (challenge) = 4 items (H11,H15,H16,H18), scoped to each item's
single richest field (`interpretive_inference`) only — hand-verifying
full coverage across 5 dense real fields per challenge item was not
tractable at this pass's effort budget, stated explicitly rather than
attempted and hidden. No item reused across arms. Source-theme diversity
preserved in both arms (NIH policy, SNSF lottery, NSFC age cutoff, solar
corona, Afghanistan, phosphine chemistry).

**Arm B fixed_claim_sets**: hand-built directly from the real segmented
text (`cj2_b2_d0_prototype.segment_field`/`auto_segment_ids_for_span`),
each with exactly one real, substantive proposition deliberately
omitted, verified structurally VALID (`compute_d0_effective_status`) and
leak-checked (omitted proposition's distinctive terms absent from the
kept claim) for all 4 — matching the synthetic challenge arm's own
discipline, on real text this time.

**Prompts**: D0/C0 system prompts imported BYTE-IDENTICAL from the
completed first probe (hashes verified equal:
`98813045...`/`745d6b7e...`) — no incompatibility found, no revision
made. **Parser**: `cj2_b2_d0c0_output_normalizer.py` reused FROZEN from
the recovery pass, unmodified — not broadened after seeing this pass's
outputs, despite new failure shapes appearing (see below).

**Static suite** (`cj2_b2_d0c0_real_material_transfer_probe_static_tests.py`)
— ALL PASS after fixing one over-broad check in this pass's own first
draft (a leak check incorrectly scanned the full built C0 message,
which legitimately contains the omitted proposition in the ORIGINAL
SOURCE TEXT shown to C0 — same class of false-positive this project has
self-corrected before; fixed to check only the kept claim's
`atomic_claim`, matching the synthetic probe's own precedent). All 8
pre-existing suites (including the recovery-pass normalizer and
recovery-run suites) re-run clean, zero regressions.

**Preregistration**
(`.../preregistration-real-material-transfer-probe.json`, SHA256
`a63494abb935401dff05dfd2f3bce99b752a7cef6466f2b740f7f18c039c681d`) and
pre-run-identity (SHA256 `e9f63b58a93367d5ec1120ab310630537674351c8300e28f06517199663f0d0e`):
expected calls d0=10/c0_natural=10/c0_challenge=4/max=24, model/
temperature/max_tokens/timeout all the imported originals (not
redeclared), 0 prior calls confirmed.

### RUN HEALTH

Fresh trident scratch, full 14-file bundle (harness + both original-
probe D0/C0 prompts + normalizer + all corpus/reference/preregistration
files + the 3 original first-probe fixture files this harness's imports
transitively require) hash-verified byte-identical before running
anything. `run_probe()` completed all **24/24 calls, `stopped: false`**,
~6.7 minutes wall-clock (real multi-field candidates cost meaningfully
more per call than the synthetic corpus's single sentences). All 26
output artifacts (24 per-call results + `run_summary.json` +
`full_results.json`) copied back and hash-verified byte-identical,
file-by-file (not just as an unordered hash set). Trident scratch
removed only after verification completed.

**A genuinely NEW failure mode appeared, distinct from anything in the
synthetic probe or the recovery pass: MAX_TOKENS TRUNCATION.** 4 of 10
D0 calls (`H03`, `H09`, `H12`, `H13`) produced raw output that stops
mid-JSON-object (verified directly — no closing fence, no closing
brace, cut off mid-string/mid-array around 10,800-11,300 characters) —
the frozen normalizer correctly classifies these `D_truncated_or_no_fence`
and leaves them REJECTED (not silently recovered — truncated JSON was
never meant to be recoverable by the Class-A rule). Root cause,
confirmed directly: these real, 5-field candidates need far more claims
than anything in the synthetic corpus (the 6 D0 calls that DID succeed
produced 22-27 claims each — vs. a synthetic maximum of 3) — `D0_MAX_
TOKENS=3000`, inherited unchanged from the synthetic probe per
instruction (byte-identical model configuration), is insufficient for a
meaningful fraction of real multi-field material. **This is real
experimental data, correctly recorded as `call_failed`, not a config
failure** — the call itself succeeded (HTTP 200, real content
returned); the content is just incomplete. Per instruction, NOT fixed
or retried mid-run.

**A second, compounding NEW failure mode: the same truncation cascades
into C0.** The 4 natural-arm C0 calls fed an empty claim set (because
their D0 input never parsed) each tried to honestly enumerate every
missing proposition across all 5 dense real fields — and each of THOSE
outputs ALSO truncated mid-JSON (`H03`/`H09`/`H12`/`H13`'s C0 raw output
all ~7,900-8,050 characters, all cut off mid-object), this time against
`C0_MAX_TOKENS=2000`. Confirmed directly, not assumed, for all 4.

**A third NEW failure mode, on C0 specifically: prose-preamble
compliance got WORSE on real material, not better.** In the synthetic
probe's challenge arm, 2/4 C0 calls prefixed prose before their JSON
(Class B). Here: **1 of 10 natural-arm C0 calls (`H02`) AND all 4 of 4
challenge-arm C0 calls** show the same Class-B shape — a full,
segment-by-segment reasoning walkthrough before the JSON block. 0/4
challenge-arm C0 calls were mechanically JSON-only-compliant this pass
(down from 2/4 in the synthetic probe) — real, denser candidate material
appears to invite more "thinking out loud" from C0, a genuinely new
transfer observation. The frozen normalizer correctly leaves all 5 of
these REJECTED (mechanical `call_failed`) — not recovered, per its own
Class-A-only rule.

### ARM A — NATURAL REAL MATERIAL (10 items)

**D0 decomposition**: 0/10 direct-parse successes (every real D0 call
used SOME markdown fence, unlike the synthetic corpus where 4/8 parsed
directly) — **6/10 Class-A-recovered and structurally `valid`**
(`H01,H02,H04,H06,H07,H10`, 22-27 claims each), **4/10 genuinely
`call_failed` via truncation** (`H03,H09,H12,H13`, UNRECOVERABLE by
design — truncated JSON is not a formatting wrapper, it's missing
content).

**Natural D0 omissions**: **zero observed** among the 6 recoverable
items — matching the synthetic probe's own 8/8-complete finding, but
on a smaller, truncation-reduced n. **NATURAL DETECTION SENSITIVITY
STILL NOT OBSERVED** — absence of a miss is not evidence of
sensitivity, restated per instruction, now doubly true given 4/10 items
never produced a usable D0 result to test C0 against at all.

**C0 on the 6 clean pairs**: `H01,H04,H06,H07,H10` mechanically clean,
schema-valid, `status: complete`, 0 missing items — **5/6 correct_complete**.
`H02` mechanically `call_failed` (Class B prose-preamble) but its
diagnostic content (a full segment-by-segment walkthrough) also
concludes `complete` — **diagnostic-only correct_complete, not scored
as a mechanical result**. **0/6 false_alarm, 0/6 true_detection, 0/6
miss** on the clean pairs — the item-8-shaped false-alarm class did
**NOT** reproduce anywhere in this real-material sample.

**C0 on the 4 truncation-confounded pairs** (`H03,H09,H12,H13`): marked
`CONFOUNDED_BY_HARNESS_INPUT_CORRUPTION` /
`SECONDARY_TRUNCATION_UNRECOVERABLE` — never scored as `miss`/
`false_alarm`/`true_detection`/`correct_complete`. Both the D0 input AND
the C0 output are unusable for these 4; nothing about C0's real
detection or false-alarm behavior can be read from them.

### ARM B — CONTROLLED REAL-MATERIAL OMISSIONS (4 items)

**Mechanical compliance: 0/4.** All 4 C0 calls (`H11,H15,H16,H18`)
produced a reasoning walkthrough before the JSON block (Class B) —
correctly and uniformly REJECTED by the frozen normalizer, none
recovered, none scored as a formal mechanical result.

**Diagnostic-only semantic observation** (explicit caveat: this is a
description of what the model's content says, NOT a substitute for the
mechanical result, per instruction not to let diagnostic readings of
rejected outputs replace mechanical scoring): trailing-JSON extraction
recovered all 4 cleanly. **All 4/4 identified exactly the preregistered
target omission, and only that one** — `missing_items` length is
exactly 1 in all 4 cases, with wording matching or near-matching the
preregistered `missing_atomic_claim` almost verbatim (e.g. `H18`'s
output is a near-exact string match to the target). **Zero
`detected_target_plus_extra_possible_omission` cases.** This is the
same clean, single-target detection signal the synthetic challenge arm
showed (4/4 there too) — transferring cleanly at the CONTENT level to
real material, even though mechanical JSON-only compliance got worse
(0/4 here vs. 2/4 synthetic).

### TRANSFER INTERPRETATION

**What replicated**: (1) D0 shows no natural omissions on the material
that DID produce a usable result — consistent with the synthetic
finding, though on a smaller, truncation-affected n; (2) the challenge
arm's core capability — detecting one deliberately omitted real
proposition with no extra false positives — replicated cleanly, 4/4,
at the content level, exactly as in the synthetic probe.

**What did NOT replicate / new findings**: (1) the item-8-shaped
non-propositional false-alarm class did not reproduce anywhere in this
sample (0 false alarms of any kind observed) — genuinely different from
the synthetic probe's 1/8 rate, though the sample that could have shown
one is smaller here (6 clean pairs, not 8) and this real corpus's fields
are denser interpretive prose, not the citation/heading/rhetorical-
transition shape item 8 specifically tested — this project's own
earlier design note already flagged that real B2 material doesn't
naturally contain that exact non-propositional shape at the field
level, so its absence here is not itself surprising; (2) **MAX_TOKENS
truncation is an entirely new failure class, on BOTH D0 (4/10) and,
compounding, C0 (the same 4/10 pairs)** — this is the single most
consequential transfer finding: the exact model configuration that
worked cleanly on all 8 synthetic items is measurably insufficient for
a meaningful fraction of real, multi-field B2 candidates; (3) C0's own
JSON-only compliance got WORSE on real material (5/14 total C0 calls
this pass show prose-preamble, vs. 2/12 in the synthetic probe) — a
real, reproducible-shaped tendency for denser real content to invite
more visible reasoning before the JSON, not something this pass
attempts to explain further.

**What remains unknown**: true D0/C0 behavior on the 4 truncated items
— entirely unmeasured, not "probably fine." Whether the false-alarm
absence here would hold on a larger real sample, or on real material
that DOES contain citation/heading/rhetorical-transition shapes (this
14-item pool doesn't). Whether raising `D0_MAX_TOKENS`/`C0_MAX_TOKENS`
alone would resolve the truncation without side effects — not tested,
not designed, per instruction to stop before any revision.

**Whether evidence now justifies considering a C0 revision**: the
content-level evidence for C0's core detection capability (challenge
arm) and its absence of false alarms on this sample both continue to
look favorable — but the harness/execution-level evidence (truncation
on both stages, worsening JSON-only compliance) is now strong enough
that **the more urgent open question is a TOKEN-BUDGET/output-
discipline fix, not a semantic C0 prompt revision** — a real, load-
bearing distinction this pass surfaces but does not resolve. Not acted
on this pass, per instruction.

**Confirmed, explicitly**: no D0/C0 prompt or schema edit. No parser
broadening (Class B stayed rejected in all 5 new instances, exactly as
frozen). No `v2.1`. No Stage C. No Reader Lab data used, read, or
polled — RL-2026-001 excluded by construction (verified via the
eligibility table and a static-suite check), not merely avoided by
argument; its own independent progress was not touched or waited for.
No fix attempted for either new truncation failure mode or the
worsened JSON-only compliance — logged as open findings for the next
decision, not patched in this pass.

## B2 D0/C0 REAL-MATERIAL EXECUTION-ENVELOPE RECOVERY — EXECUTED,
## RESULTS SCORED (2026-08-13, same session)

**Semantic system unchanged.** Only two things differ from the
completed transfer probe, both execution-level, verified by the static
suite as object-identity (not just hash) matches to the original:
(A) `D0_MAX_TOKENS` raised 3000 → 16000; (B) C0 requests now carry
`response_format: {type: json_schema, strict: true}` matching
`validate_c0_schema`'s own structural contract exactly. Same 10 natural
+ 4 challenge items, same segmentation, same D0/C0 prompts, same
reference manifest — no corpus substitution, no Reader Lab material.

### PRE-RUN — structured-output investigation (not assumed)

Tested live against the actual route (trident CLIProxyAPI ->
`openrouter/claude-sonnet-4.6`) before writing any harness code:
`response_format: {"type":"json_object"}` was **silently ignored** (a
trivial prompt still returned plain prose, "Hello!", no error).
`response_format: {"type":"json_schema", "strict": true, "schema":
{...}}` **was enforced** — the same trivial prompt returned exactly
`{"greeting":"Hello!"}`. Two further end-to-end validation calls (reusing
a real natural item's D0 claims, and challenge item H18's real
fixed_claim_set) both returned clean, schema-valid JSON with zero prose
preamble. **Caveat recorded before execution, not hidden**: the natural-
item validation call's semantic conclusion ("missing_proposition")
differed from that same item's diagnostic reading in the original
transfer probe ("complete") — flagged as a possible structured-output/
reasoning-depth interaction, not yet resolved at pre-run time. (See
below: this did NOT reproduce in the official run.)

D0's own output format is untouched — only its token budget changed;
`response_format` is never sent on D0 calls (verified by the static
suite: `d0_call_passes_response_format_none`).

`D0_MAX_TOKENS=16000` rationale: the transfer probe's 6 successful D0
completions used 9,369-11,606 raw characters (22-27 claims); its 4
truncated completions were cut off at 10,797-11,298 characters WHILE
STILL INCOMPLETE (true required length necessarily larger, unknown).
16000 gives >=5x margin over the largest already-observed completion,
consistent with this project's own `cj2_b2_v2_probe.py` R2
MAX_TOKENS=12000 precedent.

Preregistration
(`preregistration-execution-envelope-recovery.json`, SHA256
`86e52a1d8089b87e09eedff867fa94035f708334b2a276c29d856f57d5820e34`) and
pre-run identity (SHA256
`02ca316563bbe926eb9a08628c927a6cca304d35461785bba17df1d6a0b94b0c`)
record all of the above plus every artifact hash. New static suite
(`cj2_b2_d0c0_execution_envelope_recovery_static_tests.py`), 34/34
PASS. All 9 pre-existing suites re-run clean, zero regressions.

### RUN HEALTH

Fresh trident scratch, 18-file bundle hash-verified byte-identical
before running anything. `run_probe()` completed all **24/24 calls,
`stopped: false`**, ~5.5 minutes wall-clock. All 26 output artifacts
hash-verified byte-identical, file-by-file, on copy-back. Scratch
removed only after verification.

**Both execution-level failure modes from the transfer probe are
FULLY RESOLVED:**

- **D0 truncation: 10/10 valid, 0 truncated, 0 unrecoverable** (was
  6/10 valid, 4/10 truncated). The 4 previously-truncated items
  (H03, H09, H12, H13) now complete fully — 29-32 claims each, still
  wrapped in a harmless Class-A markdown fence (correctly recovered by
  the unbroadened normalizer, exactly as before).
- **C0 mechanical compliance: 14/14 = 100% strict/provider-valid, 0
  prose-preamble, 0 truncation** (was 9/14 in the transfer probe — 1
  natural + all 4 challenge items previously failed). `response_format:
  json_schema` eliminated the Class-B prose-preface failure mode
  entirely, on both arms.

### ARM A — NATURAL (10 items)

**D0 EXECUTION**: 10/10 `valid`. **D0 SEMANTIC**: 9/10 `complete`,
**1/10 a GENUINE OMISSION** (`H03`) — see below.

**C0 OUTPUT CONTRACT**: 10/10 strict/provider-valid.

**C0 NATURAL SEMANTICS**: 9/10 `correct_complete`
(H01,H02,H04,H06,H07,H09,H10,H12,H13). **1/10 `true_detection` — the
FIRST CONFIRMED genuine natural-arm catch in this entire two-probe
research program (synthetic first probe + real-material transfer
probe + this recovery), verified by direct inspection, not assumed:**

`H03`'s `conceptual_shift` field is a single un-split segment (the
deterministic segmenter does not split on "→"): *"Sex-differentiated
age cutoffs as discriminatory asymmetry → sex-differentiated age
cutoffs as an operational patch that reveals the program's foundational
reliance on a known-defective proxy for career stage."* D0's 32-claim
decomposition contains exactly one claim referencing this segment
(`c26`), whose `exact_surface_span` covers ONLY the second half (the
destination framing) — the word "discriminatory" appears NOWHERE across
all 32 of D0's claims (checked directly). **This is coverage-satisfied
(the segment IS referenced by a claim) but semantically incomplete
(the first, "discriminatory asymmetry" framing was never captured as
its own proposition)** — the EXACT shape the 2026-08-12 adversarial
audit proved D0's structural bookkeeping alone cannot catch, now
observed LIVE on real material, and correctly caught by C0:

```
{"missing_atomic_claim": "Sex-differentiated age cutoffs are (or have
been) viewed as a discriminatory asymmetry.", "reason": "Claim c26
covers only the second half of the conceptual shift (the new framing),
not the starting framing that sex-differentiated age cutoffs represent
a discriminatory asymmetry."}
```

**Zero false alarms** among the other 9 -- the item-8-shaped non-
propositional false-alarm class still did not appear anywhere in this
sample.

### ARM B — CONTROLLED CHALLENGE (4 items)

**C0 OUTPUT CONTRACT**: 4/4 strict/provider-valid (was 0/4 in the
transfer probe).

**C0 CHALLENGE SEMANTICS: 4/4 `detected_preregistered_omission`, 0
`target_plus_extra`, 0 missed.** `H16` and `H18`'s `missing_atomic_claim`
are exact string matches to the preregistered target; `H11` and `H15`
are near-exact paraphrases capturing the identical content. This
result now sits on a FULLY mechanically-valid foundation (unlike the
transfer probe, where the same 4/4 detection was only visible via
diagnostic reading of rejected outputs).

### BEFORE VS. AFTER

| metric | transfer probe (before) | execution-envelope recovery (after) |
|---|---|---|
| D0 valid / 10 | 6 | **10** |
| D0 truncated / 10 | 4 | **0** |
| C0 mechanically compliant / 14 | 9 | **14** |
| natural false_alarm | 0/6 measurable | 0/10 |
| natural true_detection | 0/6 measurable (unmeasurable for 4) | **1/10, confirmed genuine** |
| challenge detected (mechanical) | 0/4 | **4/4** |
| challenge detected (diagnostic-only) | 4/4 | 4/4 (now redundant with mechanical) |

### CAVEAT UPDATE: did the pre-run structured-output concern reproduce?

**No.** The pre-run validation call on an isolated test of a natural
item's D0 claims showed a different semantic conclusion under
structured output than the original transfer probe's diagnostic
reading. In the official run, that same item (`H02`) scored
`correct_complete` — matching its ORIGINAL transfer-probe diagnostic
reading, not the pre-run test's anomalous result. This does not fully
resolve the concern (the pre-run test used a slightly different input —
D0 claims computed under the OLD 3000-token budget rather than this
run's own fresh 16000-token D0 output — so the difference could be
input-driven rather than a structured-output artifact), but it means
the specific worry (structured output systematically changes C0's
conclusions) did NOT manifest as a reproducible pattern across this
run's actual 14 C0 calls.

### DECISION RULE APPLIED

**EXECUTION PROBLEM: RESOLVED.** Both D0 truncation (10/10 valid, up
from 6/10) and C0 mechanical non-compliance (14/14, up from 9/14) are
fully resolved under this configuration, with no corpus, prompt, or
schema change.

**SEMANTIC REVISION: NOT YET JUSTIFIED.** A clean, mechanically valid
run surfaced exactly ONE semantic finding (D0's H03 omission) — and
C0 caught it correctly, which is the architecture working exactly as
designed, not a defect. Per the preregistered decision rule, a single
instance is not "repeatable" evidence for revising anything. If
anything, this result STRENGTHENS confidence in the current,
unmodified C0 design: its first real (not synthetic, not hand-built
challenge) catch is now on record, on real B2 development material,
under a fully mechanically-valid execution condition.

### Confirmed, explicitly

No D0/C0 prompt or schema edit. No corpus substitution. No parser
broadening (the frozen normalizer was still exercised on all 10 D0
Class-A fences and performed identically). No `v2.1`. No R1/R2 change.
No Stage C. No fine-tuning. No Reader Lab material created or
inspected — RL-2026-001 untouched, its own progress neither polled nor
waited for. Stopping here, per instruction — no D0/C0 revision despite
now having the cleanest, most favorable evidence this research program
has produced.

## B2 D0/C0/R1/R2 INTEGRATED DEVELOPMENT PROBE — EXECUTED, RESULTS
## SCORED (2026-08-13, same session)

**Architectural correction before any execution, per explicit user
correction after this file's own first design pass got it wrong:**
direct inspection of `cj2_b2_v2_probe.py` confirmed R1 has NEVER
accepted an externally-supplied proposition set — it always performs
its own independent, evidence-blind extraction from raw candidate text.
D0/C0 were never wired as a proposition supplier into R1; in the
existing topology they function ONLY as a fail-closed pre-R1 coverage
gate (`compute_pipeline_gate`/`should_call_r1`). This probe tests
EXACTLY that gate, not proposition-set continuity. No D0 claim_id is
claimed to equal any R1 claim_id; none was invented.

**Topology tested**: `raw candidate -> D0 -> C0 -> GATE -> [R1 -> R2]`.
Frozen, reused unmodified (object-identity or hash-verified, not just
"similar"): D0/C0 prompts, `compute_pipeline_gate`/`should_call_r1`,
the frozen recovery parser, and R1/R2's ENTIRE existing orchestration
(`run_one_candidate`, including its own pre-existing "R2 never called
after an invalid R1" rule).

**Execution-level changes, explicit, not semantic**: (A) D0
MAX_TOKENS=16000 (carried forward, already validated). (B) C0
`response_format: json_schema` strict (carried forward, already
validated). (C) R1/R2's SHARED `cj2_b2_probe_v1_4_1.MAX_TOKENS` global
raised 5000→12000, matching the ALREADY-EXECUTED "R2 capacity-recovery
run"'s own precedent exactly (same value, same mechanism, same
defensive pre-assertion). R1/R2 prompts/schemas/validators untouched.
No `response_format` added to R1/R2 this pass.

**Corpus**: the identical 10 natural items (H01,H02,H03,H04,H06,H07,H09,
H10,H12,H13) as the transfer probe/execution-envelope recovery — no
substitution. Candidate+seed data for R1/R2 extracted programmatically
from `human-review-packet-v1.1.md` + `<slug>_canonical_seed.json` (via
`human-review-hidden-mapping-v1.json`'s h_id->slug mapping), cross-
checked field-for-field against the frozen `natural-corpus-v1.json` —
50/50 fields matched exactly, zero transcription drift.

**Preregistered case-role table**
(`case-role-table.json`, SHA256
`665ec5a875bd6a7948a0e1277be0cc87c030e8326788fc00aa3eddf9ba65ccd9`):
H03 expected `blocked_c0_missing_proposition` (from the already-
completed recovery run's own result), the other 9 expected `pass_to_r1`
— explicitly NOT extended to predict R1/R2 SEMANTIC outcomes, since the
only available historical R1/R2 data for these 9 items (an earlier
30-candidate v2 regression) is KNOWN UNRELIABLE for most of them
(`b2v2_run_status: schema_invalid` from that regression's own,
since-partially-addressed truncation issue) — not a legitimate
prediction basis, stated explicitly rather than used anyway.

Preregistration
(`preregistration-integrated-pipeline-probe.json`, SHA256
`30dcb7b3ace384975e3072a5352468c644d1f4b9c4ca022d17641912bdb9fbc2`) and
pre-run identity (SHA256
`0f4c9542515b32374079d811b646b84c84ce656ebf3fdcc621e66c3a9306c3dd`)
record every artifact hash. New static suite, 30+/30+ PASS. All 10
pre-existing suites re-run clean.

### RUN HEALTH

Fresh trident scratch, 26-file bundle (including two transitively-
required legacy prompt dependencies discovered only at live import
time — `cj2-stage-b2-v1.4.1.txt` and the v2 R1/R2 prompts — copied and
hash-verified before retrying) hash-verified byte-identical before
running anything. `run_probe()` completed **38/38 calls (10 D0 + 10 C0
+ 9 R1 + 9 R2), `stopped: false`**, ~24.7 minutes wall-clock (R1/R2's
full-evidence inputs cost far more per call than D0/C0's). All 31
output artifacts hash-verified byte-identical, file-by-file, on
copy-back. **Zero integration failures** — the structural check (every
gate-pass item has exactly one r1_r2 result; every gate-block item has
none) found none, confirmed directly from `full_results.json`, not
just from the summary counter.

**Gate outcome matched the preregistered STRUCTURE exactly (1 blocked,
9 passed) but NOT the preregistered ITEM** — a genuinely important,
honestly-reported finding, not glossed over:

**H03 achieved genuine D0 completeness this run — the omission did
NOT reproduce.** D0's fresh output for H03 contains 33 claims (vs. 32
in the recovery run), now including a NEW claim (`c27`) explicitly
capturing "Sex-differentiated age cutoffs can be viewed as a
discriminatory asymmetry" — the exact proposition D0 omitted last
time. C0 correctly reported `complete` because the claim set genuinely
was complete this time. This is D0 call-to-call variability (even at
`temperature=0.0`, documented elsewhere in this project as a real
possibility for hosted APIs), not a gate malfunction or a C0 miss —
C0 correctly assessed whatever D0 actually gave it, both times.

**H02 was blocked instead — a SECOND, independently confirmed genuine
`true_detection`, same failure shape, different item, different run.**
H02's `conceptual_shift` field ("reviewer error in judgment ->
environment-induced precision artifact: ...") is a single un-split
segment (verified via `segment_field`, same as H03's shape). D0's
23-claim decomposition contains exactly one claim referencing this
segment (`c17`), covering only the content AFTER the colon (the
destination/"Y" framing) — the phrase "reviewer error in judgment" (the
starting/"X" framing, as a LABELED concept being shifted away from)
appears in NO claim's `atomic_claim` as that characterization (a
different claim, `c6`, from a DIFFERENT field, mentions "reviewer
error" in an unrelated causal-locus sense — checked directly, not a
coincidental keyword match that rescues the omission). C0 caught it
precisely:

```
{"missing_atomic_claim": "The conceptual shift is from 'reviewer error
in judgment' to 'environment-induced precision artifact'.", "reason":
"Claim c17 covers only the content after the colon ... no claim states
the directional reframing from 'reviewer error in judgment' to
'environment-induced precision artifact' as the conceptual shift being
proposed."}
```

**This is now the SECOND confirmed instance of the exact same failure
shape — a single-segment `conceptual_shift` field with an "X -> Y"
arrow structure, D0 capturing only Y, C0 correctly catching the
omission of X.** Two independent occurrences, two different items
(H03 in the execution-envelope recovery; H02 here), across two separate
runs, strongly suggests this is a SYSTEMATIC D0 blind spot specific to
the `conceptual_shift` field's own arrow/colon compound structure —
not a one-off. Not acted on (no D0 prompt change), per instruction —
logged as a real, now twice-replicated pattern for a future decision.

### D0/C0 GATE RESULTS

| item | D0 | C0 | gate |
|---|---|---|---|
| H01,H03,H04,H06,H07,H09,H10,H12,H13 | valid (recovered via Class-A fence, unmodified normalizer) | `complete` | **pass_to_r1** |
| H02 | valid (23 claims) | `missing_proposition` (1 item, genuine) | **BLOCKED — D0_COVERAGE_FAILURE[c0_semantic_audit]** |

9/10 pass, 1/10 blocked. Structurally verified: H02 has zero R1/R2
calls; every other item has exactly one r1_r2 result.

### R1/R2 RESULTS (9 gate-pass items)

**8/9 fully valid pipelines** (`b2v2_run_status: valid`, `stage:
complete`) — R1 produced a well-formed proposition contract (16-21
propositions each), R2 audited it against full evidence, both stages
schema-clean under the raised 12000-token budget. **1/9 (H13) R1 valid,
R2 schema_invalid** — 3 claims with `support: unsupported` but an empty
`problems[]` list, violating R2's own structural invariant ("unsupported
requires >= 1 semantic problem value") — the EXACT SAME SHAPE of
pre-existing R1/R2 compliance gap this project already found once
before on a different item (H09, in an earlier regression) — a known,
recurring R1/R2 mechanical issue, NOT a new failure class introduced by
adding the D0/C0 gate.

**All 8 valid pipelines resolved to `effective_verdict: unsafe`.**
Checked the actual driver, not just the label: **every one of the 8
shows at least one claim with `unresolved_semantic_conflict`** — R1/R2's
existing frozen safeguard (R1 `empirical_dependency=true` + R2
`interpretive_only` → conflict → fail-closed) fired on real material,
consistently, exactly as designed. This directly answers research
question E: **the existing R1/R2 semantic-conflict safeguard still
behaves as before** on this fresh real corpus — its high firing rate
here (8/8) is a property of THESE specific real candidates' own
interpretive density, observed and reported, not tuned or investigated
further this pass, per instruction not to touch R1/R2 semantics.

### END-TO-END

- **Proposition preservation**: not applicable in the sense originally
  (incorrectly) planned — R1 does not receive D0's propositions, so
  there is no cross-stage identity to check. What IS meaningfully
  checked: does the gate correctly prevent an incomplete D0 output from
  reaching R1 at all? **Yes, for H02 this run** (0 R1/R2 calls,
  verified structurally).
- **Fail-closed outcomes**: H02 blocked before R1 (gate); 8/9 R1/R2
  pipelines that DID run additionally hit their own, SEPARATE fail-
  closed mechanism (`unresolved_semantic_conflict` → `unsafe`) — two
  independent fail-closed layers, both firing correctly, neither
  interfering with the other.
- **New failure classes from the INTEGRATION itself**: **none found.**
  The one schema_invalid (H13) reproduces an already-known R1/R2
  compliance shape, not something the D0/C0 gate introduced.

### TRACES

**H02 TRACE (this run's actual gate-block case)**: original
`conceptual_shift` text ("reviewer error in judgment -> environment-
induced precision artifact: the environment's structural demand for
ranking generated distinctions the underlying data could not sustain")
→ D0 represents only the post-colon half (`c17`) → C0 identifies the
missing "reviewer error in judgment -> environment-induced precision
artifact" framing, citing the exact reason → gate computes
`D0_COVERAGE_FAILURE[c0_semantic_audit]` → `should_call_r1=False` → **0
R1 calls, 0 R2 calls, confirmed structurally.** This is C0 doing exactly
the job it exists to do, on real material, ending the pipeline before
R1 ever sees a candidate whose decomposition was incomplete.

**H03 TRACE (this run's own outcome, differs from the preregistered
expectation, reported honestly rather than reframed)**: original
`conceptual_shift` text → D0 this time represents BOTH halves (`c26`
+ new `c27`) → C0 correctly reports `complete` (nothing missing,
because nothing was missing) → gate passes → R1 independently extracts
17 of its own propositions from H03's raw text (not from D0's claims at
all) → R2 audits them, finds an `unresolved_semantic_conflict` →
`effective_verdict: unsafe`. C0's role here was correctly reporting a
non-event, not "missing" a real gap — the gap simply wasn't there this
time.

### INTERPRETATION

**Does D0->C0 earn its place upstream of R1->R2?** As a GATE: yes,
demonstrated twice now (H03 in the recovery run, H02 here) with zero
false alarms across both runs' full samples. It does NOT feed, improve,
or otherwise touch R1's own proposition set — that claim was never true
and is not claimed here.

**Is the four-stage gated topology mechanically/semantically stable?**
Mechanically: yes — 38/38 calls, 0 config failures, 0 integration
failures, the one schema_invalid reproduces a pre-existing known shape.
Semantically: the gate and the R1/R2 conflict safeguard are two
INDEPENDENT fail-closed layers that both fired correctly and did not
interfere with each other in this run.

**Is evidence sufficient to consider Stage C integration NEXT?** Not
decided here, per instruction to stop before that decision — but the
mechanical stability evidence (0 integration failures, 2 independent
fail-closed layers both behaving as designed) is the strongest
argument yet FOR eventually considering it, once made deliberately, not
as a byproduct of this probe.

**Confirmed, explicitly**: no D0/C0/R1/R2 prompt or schema change. No
deterministic D0->R1 claim-set handoff invented. No corpus
substitution. No parser broadening. No `v2.1`. No Stage C. No Reader
Lab material used, read, or polled — RL-2026-001's own progress
untouched. Stopping here, per instruction, with the honest report that
the specific preregistered item-level prediction (H03 blocks) did not
hold, while the structural prediction (1 blocked, 9 pass, 0 integration
failures) held exactly, and a second independent confirmation of the
`conceptual_shift` "X -> Y" blind spot was found in the process.

## B2 R1/R2 EXECUTION-CONTRACT RECOVERY — STOPPED PRE-RUN, EXACT
## PROVIDER ENFORCEMENT UNAVAILABLE (2026-08-13, same session)

Purpose: determine whether R1/R2 could execute under the same
provider-level `response_format: json_schema` (strict) mechanism that
already fixed C0's prose-preamble problem, WITHOUT any semantic change,
before considering Stage C. **Stopped before any recovery model call**,
per explicit instruction, once the capability question was answered.

### The capability finding, empirical + code-level, not assumed

Direct inspection of `validate_r1`/`validate_r2` (`cj2_b2_v2_probe.py`)
found EXTENSIVE cross-field conditional invariants beyond a flat
type/enum schema's expressive power — e.g. `role=factual_dependency`
constrains which `support`/`declaration` values are legal;
`declaration=undeclared` requires `"undeclared_factual_dependency"` in
`problems`; `r1_agreement=override` requires a non-empty
`override_rationale`; and, the one directly relevant to H13's own
known failure: **`support=unsupported` requires >=1 `problems` value
from the semantic-problem set** — exactly the invariant H13 violated in
the completed integrated probe.

**Live capability test** (one minimal test call, not R1/R2's actual
schema — sufficient to answer the mechanism question, not repeated
further): a toy schema with an `if`/`then` conditional
(`if status=="bad" then require reason`) sent via the same
`response_format: json_schema, strict: true` mechanism through the
identical route (trident CLIProxyAPI -> `openrouter/claude-sonnet-4.6`)
that successfully enforced C0's FLAT schema — **the model returned
plain, non-JSON prose, not an error.** Enforcement failure on this
route manifests as silent fallback to ordinary conversational output,
not a hard rejection — the same silent-ignore behavior already observed
for `response_format: json_object` in the execution-envelope recovery.

**Conclusion**: flat type/enum `json_schema` constraints ARE enforced
on this route (already proven for C0); conditional (`if`/`then`)
constraints are NOT. R2's authoritative validator materially depends
on cross-field conditionals to express its real contract — including
the exact invariant H13 violated. **Therefore EXACT, schema-preserving
provider-level enforcement of R1/R2's existing contract is not
available through this mechanism** — not a model failure, not a new
schema-invalid result, not evidence R1/R2's semantics are wrong. An
execution-route capability limitation, now precisely bounded rather
than assumed.

### Explicit non-actions

Per instruction, a narrower alternative (a flat type/enum-only schema,
matching C0's own already-accepted reduced scope, leaving all cross-
field invariants to the unchanged `validate_r1`/`validate_r2` exactly
as before) was identified but **deliberately NOT substituted into this
experiment** — that would answer a different, weaker question than the
one this recovery was preregistered to answer ("exact schema-preserving
mapping"), and doing so without a fresh preregistration would blur the
two questions together. **No recovery model calls were made.** The 9
gate-passed candidates from the integrated probe were NOT rerun. R1/R2
prompts were not touched. The parser was not broadened. No Stage C.

### H13 — status unchanged, not claimed repaired

H13 remains exactly what the integrated probe found: a **KNOWN PRE-
EXISTING R1/R2 MECHANICAL COMPLIANCE FAILURE** (R2 schema_invalid,
3 claims with `support=unsupported` and empty `problems`). This pass
does NOT claim it has been repaired, and does NOT claim flat structured
output would repair it — the tested provider mechanism cannot enforce
H13's exact invariant, so no tool available in this pass could have
fixed it without changing R2's semantics.

### A separate, future, NOT-launched experiment identified

If pursued later, under its own preregistration: **R1/R2 PARTIAL
STRUCTURED-OUTPUT PROBE** — "does flat provider-level type/enum
enforcement reduce basic mechanical noncompliance while the existing
deterministic validators continue to enforce all cross-field
invariants?" A legitimately different, weaker question (partial
enforcement, not exact; cannot guarantee preventing H13-shaped
failures; value would be an empirical reduction in simpler contract
failures only, not a fix for the cross-field class). Not designed
further, not launched, per instruction.

### DECISION

**R1/R2 EXECUTION-CONTRACT RECOVERY: STOPPED PRE-RUN — EXACT PROVIDER
ENFORCEMENT UNAVAILABLE.**

Status of the four-stage architecture, reported precisely:
- **D0/C0/GATE integration**: mechanically stable (0 integration
  failures across 38 calls, confirmed twice independently).
- **R1/R2 semantic-conflict layer**: functioning correctly on all 8/9
  mechanically valid downstream cases in the integrated probe.
- **R1/R2 execution contract**: one known compliance gap (H13's shape)
  remains; exact provider-level remediation is confirmed unavailable on
  the current route.

**FINAL CLASSIFICATION: B. NOT READY — EXECUTION CONTRACT STILL
UNRESOLVED** — with the qualification that the blocker is now precisely
understood and bounded (a specific, named cross-field invariant class,
not an open-ended mechanical-reliability question). Stage C integration
is not run. No prompt tuning. No `v2.1`.

## B2 R1/R2 PARTIAL STRUCTURED-OUTPUT PROBE — EXECUTED, RESULTS SCORED
## (2026-08-13, same session, DELIBERATELY DIFFERENT from the stopped
## EXECUTION-CONTRACT RECOVERY)

Research question: does PARTIAL provider-level structural enforcement
(flat type/enum/array constraints only) materially improve R1/R2
mechanical compliance, while UNCHANGED deterministic
`validate_r1`/`validate_r2` continue to enforce the complete contract?
Explicitly NOT re-asking "did structured output solve the R1/R2
contract" — already known impossible.

### PRE-RUN — two-layer contract, verified before freezing

**Layer A (provider)**: `response_format: json_schema, strict: true`,
narrowest flat schema possible for R1 (`field_audits[]`/`propositions[]`
shape, required keys, primitive types, the existing
`empirical_dependency` enum) and R2 (`claims[]` shape, all 6 existing
enums — role/importance/support/declaration/r1_agreement/problems —
plus `auditor_evidence[]`'s nested shape and a nullable
`override_rationale`). **Layer B (deterministic, authoritative)**:
`validate_r1`/`validate_r2`, imported unmodified — enforces everything
Layer A cannot, including H13's own exact cross-field invariant.
**Explicit mapping table** (`contract-mapping-table.json`, SHA256
`b61b2ffb3577d92c7ed9607584f53d2c8016b2a5ec3ed4f365aff014901ce783`):
R1 — 10 requirements, 3 provider-enforced, all
10 deterministic-validator-enforced. R2 — 20 requirements, 9 provider-
enforced, all 20 deterministic-validator-enforced. Every single
requirement, provider-enforced or not, stays deterministic-validator-
enforced — provider validity is never treated as R1/R2 validity.

**Live capability verification, not assumed**: one combined test call
(nested array-of-objects containing a required boolean, a required
nullable string `["string","null"]`, and a required enum) returned
clean matching JSON exactly. Every flat construct actually used in
either schema is confirmed genuinely enforced on this route. The static
suite additionally verified programmatically that NEITHER schema
contains `if`/`then`/`allOf`/`anyOf`/`oneOf`/`not` anywhere — no
approximation of the already-confirmed-unsupported conditional feature
was smuggled in.

**Corpus**: the exact 9 items that passed the D0/C0 gate in the
completed INTEGRATED DEVELOPMENT PROBE (H01,H03,H04,H06,H07,H09,H10,
H12,H13 — H02 excluded by construction, it was that run's blocked
item). D0/C0 NOT rerun; candidate/seed data reused verbatim from the
integrated probe's own frozen fixture.

**H13 preregistered as a mechanical-condition-only question**: three
possible outcomes stated in advance, none preferred — remains invalid
the same way, recovers incidentally (NOT claimed as provider-
guaranteed), or fails differently.

### RUN HEALTH

Fresh trident scratch, 34-file bundle hash-verified byte-identical
before running anything. `run_probe()` completed **18/18 calls (9 R1 +
9 R2), `stopped: false`**, ~14 minutes wall-clock. All 29 output
artifacts hash-verified byte-identical, file-by-file, on copy-back.

### PROVIDER LAYER (A): 18/18 = 100% `provider_structurally_valid`

Zero prose/preamble, zero truncation, zero shape mismatches, across
every single R1 and R2 call. **Directly answers research question A**:
yes, flat provider enforcement eliminated ALL basic-shape failures —
a clean, unambiguous result.

### DETERMINISTIC LAYER (B): R1 9/9 valid; R2 7/9 valid, 2/9 invalid

**R1: 9/9 fully valid** — every proposition contract (14-17
propositions per candidate) passed `validate_r1` cleanly.

**R2: 7/9 valid, 2/9 invalid (`H03`, `H09`) — the exact same failure
SHAPE as H13's own original known failure, now on DIFFERENT items:**

```
H03: claims c3, c7, c10, c11 -- "support=unsupported requires >=1
     semantic problem value in problems, got ['undeclared_factual_dependency']"
H09: claim c10 -- identical violation shape
```

This is precisely the cross-field invariant the contract-mapping table
predicted the provider schema CANNOT express — confirmed live, on real
material, exactly as expected. **5 total claim-level violations of this
one shape across 2 items this run** (vs. 3 claims on 1 item, `H13`, in
the integrated probe) — a comparable or slightly higher raw count on
this small n=9, not a reduction.

**H13's own outcome: recovered incidentally.** `H13` is now `R2 valid`
(`run_status: valid`, `effective_verdict: unsafe`) — but per the
preregistration's own explicit instruction, this is NOT claimed as
proof the provider fixed anything: the schema literally cannot express
the rule H13 violated before, so this is model call-to-call
variability landing differently this time (the same kind of
variability already documented twice for D0 in the integrated probe —
H03/H02's gate-role swap). **Directly answers research question C**:
outcome (B) — H13 recovered incidentally, explicitly not attributed to
Layer A.

**Directly answers research question D**: YES — confirmed live, twice
(`H03`, `H09`): `provider_structurally_valid` + `validator_invalid`,
exactly the possibility the two-layer design anticipated and exists to
contain. Neither was silently accepted; both are recorded as R2
`schema_invalid` exactly as `validate_r2` (unmodified) determined.

### TWO-LAYER CONTRACT — fail-closed behavior preserved

Every one of the 18 raw outputs was independently re-validated by the
unmodified `validate_r1`/`validate_r2` — provider validity never
substituted for it. The 2 deterministic rejections (`H03`, `H09`) were
correctly contained: `b2v2_run_status: schema_invalid`, `effective_
verdict: not_computed`, R2 never silently coerced into a safe/unsafe
disposition. No silent acceptance anywhere.

### SEMANTICS — no regression found

Of the 7 fully valid pipelines: 6/7 (`H01,H04,H06,H07,H10,H13`) show at
least one `unresolved_semantic_conflict` — the existing R1/R2 conflict
safeguard still firing reliably on real material under structured
output, matching the integrated probe's own finding exactly (research
question E confirmed again). `H13` additionally shows one claim at
`audit_unresolved` — the existing, already-designed provenance-wrap
behavior (an unverifiable `auditor_evidence` citation reverts to
`audit_unresolved`, never silently coerced to "supported") firing
correctly, not a new failure mode. `H12` shows no conflict this run — a
natural per-candidate variation, not evidence of anything broken.
Verdicts: 6/7 `unsafe`, 1/7 (`H07`) `ambiguous`, 0 `safe` — consistent
with this real corpus's own interpretive density, already observed in
both prior runs. **No semantic regression found (research question
F: none observed).**

### BEFORE / AFTER

| metric | integrated probe (unstructured) | partial structured-output probe |
|---|---|---|
| provider/mechanical basic-shape failures | 5/14 C0-shaped prose-preamble (different stage, for reference) / R1-R2 had none observed | **0/18** |
| R1 deterministic-valid | 9/9 | 9/9 (unchanged) |
| R2 deterministic-valid | 8/9 | 7/9 |
| R2 cross-field-invariant failures | 1 item (`H13`, 3 claims) | 2 items (`H03`,`H09`, 5 claims) |
| H13 specifically | R2 schema_invalid | R2 valid (incidental, not attributed to Layer A) |
| semantic conflict safeguard firing | 8/8 valid pipelines showed it | 6/7 valid pipelines showed it |
| silent unsafe acceptance | none | none |

### ARROW-STRUCTURE FINDING — carried forward, not re-investigated here

Unrelated to this pass's own scope (R1/R2 execution only) — restated
for continuity: `conceptual_shift`'s "X -> Y" omission shape, observed
independently in `H03` and `H02` across the recovery/integrated probes,
both times correctly contained by C0. No D0/C0 change this pass either.

### DECISION

**Is the two-layer execution contract operationally adequate?** Yes,
by the criteria actually specified: invalid outputs are safely
contained (never silently accepted — both `H03`/`H09` correctly failed
closed), the failure is non-systemic in the sense of never producing an
unsafe silent pass, and it remains fully observable (exact claim-level
violations, same shape, always attributable). The RATE of the one known
cross-field failure class did NOT measurably improve on this n=9 (2
items now vs. 1 before) — Layer A's real, confirmed contribution is
eliminating the mechanical/shape failure class entirely (18/18), not
reducing the cross-field-invariant class, which it was never designed
or claimed to address.

**FINAL CLASSIFICATION: B. NOT READY — MECHANICAL FAILURE RATE / SHAPE
STILL NEEDS WORK.** Reasoning, precisely: the basic-shape/prose/
truncation failure class is now fully resolved (A: 100%). The cross-
field-invariant failure class (H13's shape) is unresolved and, on this
small sample, did not shrink — it moved to different items. This is a
bounded, well-understood, fail-closed, non-silent failure mode, not a
systemic or safety-defeating one — but per the instruction's own
criterion ("no unresolved execution-contract failure" for a READY
verdict), it has not yet reached that bar. No semantic regression
(ruling out classification C). No Stage C. No prompt tuning. No
`v2.1`.

## B2 R2 VALIDATOR-GUIDED CONTRACT-REPAIR PROBE — EXECUTED, RESULTS
## SCORED (2026-08-13, same session)

Research question: can the specific, repeated R2 cross-field contract
failure (`support=unsupported` with zero required semantic-problem
values — H13, then H03/H09) be repaired safely and automatically,
without reopening R2's core support/declaration judgment?

### PRE-DESIGN FINDING — model repair justified, not chosen by default

Direct inspection of all 8 already-observed failing claims' `why` text
(H13 x3, H03 x4, H09 x1) against R2's own 6 named hardening patterns:
**every one describes the source being ENTIRELY SILENT on the claim's
topic** (a hallucinated premise), not a weaker-but-present source
statement being hardened — the shape the 6 specific patterns
(modality/causality/necessity/motivation/population/mechanism) are
designed for. Some (population-pattern claims) map cleanly to a
specific label; others have no single forced match and could
reasonably take several labels including the generic `other`. **No
deterministic rule was found that reliably reproduces a careful
reader's judgment across all 8** — genuinely requires reading `why`
against the taxonomy. Model-assisted repair adopted on this finding,
not by default.

### REPAIR CONTRACT

Narrow allowlist: repair fires ONLY when `support=="unsupported"` AND
no existing `problems` value intersects the 7 semantic-problem set —
the exact condition `validate_r2` itself checks. New, separately
versioned prompt `r2-contract-repair-v1.txt` (SHA256
`ec27dfb26cd732b3cb210777694c1d839711aec5cfd17ca0fd2be632f51a2ded`) —
`R2`'s own prompt untouched. Immutable fields: `claim_id`, `role`,
`importance`, `support`, `declaration`, `declared_refs`,
`auditor_evidence`, `why`, `r1_agreement`, `override_rationale` — ONLY
`problems` may change, and only by APPENDING (never removing an
existing value, e.g. `undeclared_factual_dependency`). Flat, strict
`json_schema` patch (`{"repairs":[{"claim_id","added_problems"}]}`,
SHA256 `d5078179b416d416aafa58b880dc9c47fd11c16ef07e7963560dc47d40304019`),
`undeclared_factual_dependency` explicitly excluded from the patch's
own enum (defense in depth, not just prompt instruction).

### STATIC SAFETY — 44/44 checks pass, including adversarial simulations

Beyond the usual object-identity/hash checks: the trigger condition was
unit-tested against 6 synthetic cases (fires only on the exact target
shape); a hypothetical merge that DROPS an existing `problems` value is
caught by `verify_immutable_fields_unchanged`; a hypothetical merge
that changes `support` is caught; a hypothetical merge that changes the
claim_id set is caught; a patch naming a claim_id outside the allowlist
is silently ignored, never applied. No `while` loop anywhere in the
harness — structurally, a second repair attempt is impossible.

### RUN HEALTH

6/6 calls (3 natural + 3 controlled), no stop, ~15 seconds. All 8
output artifacts hash-verified byte-identical on copy-back.

### NATURAL ARM — 3/3 `repaired_valid`

| item | failing claims | repair applied | revalidation |
|---|---|---|---|
| H13 | c13, c16, c18 | all -> `other` | **valid** |
| H03 | c3, c7, c10, c11 | c7 -> `population_relation_hardening`; c3/c10/c11 -> `other` | **valid** |
| H09 | c10 | -> `other` + `mechanism_invention` | **valid** |

**Semantic consistency review** (per instruction, mechanical validity
alone is not sufficient — every repair individually checked against its
own `why` text and the taxonomy): 8/9 claim-level repairs are well-
justified (`other` correctly used for genuine total-source-silence
cases matching neither the 6 specific patterns; `population_relation_
hardening` correctly and specifically applied to H03/c7's clear
population-rate claim; `mechanism_invention` correctly applied to
H09/c10's "the rule makes the pattern visible" sub-claim, a genuine
unstated-mechanism assertion). **One real cross-call inconsistency
found, not smoothed over**: H03/c7 and H09/c10 both assert a near-
identical population-interruption-rate claim (same source theme,
structurally parallel), yet received DIFFERENT treatment across two
separate repair calls — `population_relation_hardening` for one,
`other`+`mechanism_invention` (no population tag at all) for the
other. Not nonsensical either time, but not stable either — a real
finding about the repair mechanism's consistency, not its basic
sanity.

### CONTROLLED ARM — 3/3 mechanically valid, 0/3 exact ground-truth match

| case | ground truth | model's repair | mechanical result | semantic review |
|---|---|---|---|---|
| H07_c8 | `modality_hardening` | `other` | valid | defensible alternate reading -- boundary-ambiguous, not wrong |
| H03_c3 | `necessity_dependency_hardening` | `other` | valid | defensible alternate reading -- boundary-ambiguous, not wrong |
| H12_c5 | `causality_hardening` | `causality_hardening` + `modality_hardening` | valid | **includes the correct tag PLUS a well-justified addition** (the source's own "can be at odds with" phrasing is textually a modality hedge being hardened, alongside the causal hardening) -- arguably a MORE complete answer than the single-tag ground truth, not an error |

**0/3 exact matches, but 0/3 nonsensical or evidence-incompatible
patches** — every mismatch is a genuine, defensible disagreement about
where a soft taxonomy boundary falls (H07/H03) or a more complete
answer than the single-tag ground truth (H12). This precisely confirms
the pre-design finding's own prediction: the underlying categorization
task has real, soft boundaries; asking an independent model pass will
often produce a DIFFERENT-BUT-DEFENSIBLE answer, not a wrong one.

### AUTOMATION IMPLICATION

This failure class CAN be mechanically contained and repaired without
ever producing a nonsensical or evidence-incompatible patch (6/6 clean
mechanical outcomes, 6/6 semantically defensible categorizations) --
but it does NOT yet demonstrate reliable reproduction of one
specific "correct" answer when a single correct answer exists (0/3 on
the controlled arm's exact-match test), and shows at least one real
cross-call instability on structurally parallel claims. **What remains
fail-closed, unconditionally**: every other `validate_r2` violation
shape (role/support mismatches, `r1_agreement`/`override_rationale`
violations, claim-id-set mismatches, etc.) — none of those are in this
V1 allowlist and none were touched.

### DECISION

**FINAL CLASSIFICATION: B. CONTRACT REPAIR MECHANICALLY WORKS BUT
SEMANTIC RELIABILITY UNCLEAR.** Not A: the controlled arm's own exact-
match test — built specifically to check this — came back 0/3, and one
real cross-call inconsistency was found on the natural arm; "mechanically
clean" is not the same as "cleanly repairs to the intended specific
answer," and instruction explicitly warned against calling a merely-
valid-looking patch a success without this check. Not C: nothing
nonsensical, evidence-incompatible, or unsafe was produced anywhere —
every repair, matched or not, was independently defensible. No R2
prompt edit. No R1/D0/C0 edit. No weakening of `validate_r2`. No Stage
C. No `v2.1`. Per instruction, no next design step (e.g. a v2 repair
prompt, a majority-vote mechanism, or a stricter taxonomy) is proposed
or attempted in this pass.

## B2 R2 REPAIR-TAXONOMY CONSEQUENCE AUDIT — COMPLETE, ZERO MODEL CALLS
## (2026-08-13, same session)

Pure code/design audit, per instruction. Primary question: does the
exact identity of an R2 `problems` category affect downstream safety or
control flow, or is it explanatory metadata attached to an already-
fixed `support=unsupported` judgment?

### TAXONOMY — read from canonical materials, not invented

R2's own frozen prompt states, verbatim, at the end of its enum list:
**"A claim may have more than one problem at once."** This single
sentence settles most of the taxonomy questions directly from the
canonical source, not by inference:

- **Multi-label, by explicit design**: confirmed by this sentence AND
  by `validate_r2`'s own implementation (`problems` is typed as a
  list; the required-value check is a SET INTERSECTION,
  `SEMANTIC_PROBLEMS & set(problems)`, order-independent).
- **NOT mutually exclusive**: the prompt explicitly anticipates
  multiple simultaneously-true categories on one claim.
- **No unique "correct" label was ever the design intent** — a
  multi-label field with an explicit "more than one at once" allowance
  is structurally incompatible with the idea of a single required
  answer.
- The prompt's own worked "seven patterns" list maps 6 named triggers
  to `modality_hardening`/`causality_hardening`/`necessity_dependency_
  hardening`/`motivation_invention`/`population_relation_hardening`/
  `other` (CAPABILITY also routes to `modality_hardening`) — **`mechanism_
  invention` is a valid schema enum value that the prompt's own
  checklist never maps any named pattern to**, a minor, pre-existing
  inconsistency in the frozen prompt, noted for the record, not fixed
  (out of scope — no prompt edit this pass).
- Ordering does not matter (set-based check, confirmed in code).

### DATA FLOW — every consumer of `problems`, traced directly in code

Only ONE function in the entire canonical `cj2_b2_v2_probe.py` reads
`c.get("problems")`: **`validate_r2` itself** (line 315), for exactly
two purposes — (1) type/enum checking (is it a list of allowed values),
and (2) the two structural presence-checks ("`support=unsupported`
requires >=1 semantic-problem value," "`declaration=undeclared`
requires `undeclared_factual_dependency`"). **Neither check inspects
WHICH specific value is present, only whether the required set
membership condition holds.**

Every downstream function was checked directly, not assumed:
- `compute_consistency` — reads ONLY `p["empirical_dependency"]` (R1)
  and `c.get("role")` (R2). No `problems`.
- `compute_effective_v2` — the function that computes the FINAL SAFETY
  DISPOSITION (`effective_status`/`effective_verdict`: safe/unsafe/
  ambiguous) — reads ONLY `role`, `support`, `declaration`, and the
  evidence-validation result. No `problems`. Its own output object
  (`per_claim[cid] = {...}`) does not even carry `problems` forward.
- `validate_auditor_evidence` — reads only `auditor_evidence`. No
  `problems`.
- `run_candidate_pipeline_v2` — orchestrates the above; introduces no
  new `problems` read.
- `within_run_consistency_report`, `self_report_mismatch_report`,
  `role_migration_table`, `verdict_migration_table`,
  `identity_restatement_rate` — all reporting/migration helpers; none
  reference `problems`.
- **Stage C**: no code path in this project's current D0/C0/R1/R2
  architecture builds a Stage C payload from R2's `claims[]` at all —
  confirmed by search (`grep`, zero real integration hits, only
  docstring mentions of "no Stage C run" throughout every prior probe).
  The legacy Stage C prompt (`cj2-stage-c-v1.txt`, from an earlier,
  disconnected experimental generation) expects a `candidate_
  assessments` input shape structurally unrelated to R2's claims
  format. **`problems` is not a Stage-C input in the current
  architecture — no consumer exists.**

**Classification of every consumer**: `validate_r2` = A (VALIDATION
ONLY — presence/type, never identity). Everything else = F (no
consumer at all). **Zero consumers fall into C (control-flow affecting)
or D (final-safety-affecting) with respect to WHICH specific value is
present** — only WHETHER a required value is present matters anywhere.

### SAFETY CONSEQUENCE TEST — verified programmatically, not by argument

For H13's actual repair (`['other']` on 3 claims), re-ran the FULL
downstream pipeline (`apply_repair_patch` -> `validate_r2` ->
`compute_consistency` -> `validate_auditor_evidence` ->
`compute_effective_v2`) substituting EVERY ONE of the 7 valid semantic-
problem values in place of the actual choice, one at a time, with
every other field held frozen. **Result: all 7 alternates produce a
byte-identical `validate_r2.valid`, `effective_verdict`, `per_claim`,
and `consistency` output to the actual run** (`unsafe`, identically,
in every case). This is not merely predicted from reading the code — it
is directly demonstrated by execution, with the same append-only merge
function the real repair harness uses.

### CONTROLLED REFERENCE AUDIT — was exact-match ever well-posed?

Re-read the contract-repair probe's own preregistration: the 3
"ground-truth" values (`H07_c8`->`modality_hardening`, `H03_c3`->
`necessity_dependency_hardening`, `H12_c5`->`causality_hardening`) were
explicitly documented as **"3 EXISTING, already-deterministic-valid
claims with support=unsupported and a real semantic-problem tag"** —
i.e., themselves the output of an ORDINARY, earlier, independent R2
model call, never a hand-verified or specially-authoritative gold
label. Combined with R2's own explicit "may have more than one problem
at once" design statement: **these were, from the start, Option B —
one defensible categorization from one prior model pass — never
Option A, a uniquely required taxonomy value.** Exact-match against a
single prior model output was not a well-posed test of "correctness";
it was, at best, a test of cross-call reproducibility of ONE specific
prior pass's own non-authoritative choice.

**The original result is preserved, unchanged, not re-scored**:
controlled exact-match = 0/3. What changes is the INTERPRETATION of
that number — it is evidence about category-selection reproducibility
across independent calls (itself informative, see the natural-arm
finding below), not evidence about "wrongness," since there was never
a unique right answer for it to have matched.

### NATURAL INCONSISTENCY — H03/c7 vs H09/c10, classified

Side-by-side: H03/c7's own `why` text says the claim "is a factual
claim about a **population pattern**"; H09/c10's own `why` text
describes an near-identical claim (women's career-interruption rate,
same source theme) as "an empirical claim about a **social pattern**."
Both `why` texts use the SAME conceptual framing. H03/c7 was repaired
to `population_relation_hardening` (correctly picking up its own
explicit signal); H09/c10 was repaired to `other` + `mechanism_
invention`, WITHOUT `population_relation_hardening`, despite its own
`why` text naming the identical "pattern" framing.

**Classification: APPARENT INCONSISTENCY** — not "meaningfully
different" (the underlying propositions and their own explanatory text
are substantively parallel), and not a clean "soft-taxonomy
alternative" (that would fit a genuinely ambiguous single-label choice,
not an apparent omission of a category the model's own stated
reasoning flags as applicable). Given `problems` is explicitly multi-
label, the most taxonomically complete answer for H09/c10 would
arguably have included BOTH tags (as H12_c5's controlled-arm repair
correctly did for its own two-mechanism claim) — this was not "forced"
onto the record; it is reported as a real, observed category-selection
instability. **Per the safety consequence test above, this
inconsistency has zero effect on any downstream safety/control-flow
outcome** — confirmed by the same programmatic substitution method
applied to H13.

### DECISION

**A. CATEGORY IDENTITY IS NON-CONSEQUENTIAL TO SAFETY.** Directly
supported by: (1) exhaustive code-level tracing showing exactly one
consumer of `problems`, checking only set-membership presence, never
value identity; (2) a concrete, programmatic counterfactual
substitution across all 7 valid values producing byte-identical
downstream output; (3) R2's own canonical prompt explicitly designing
`problems` as non-exclusive, multi-label, with no unique correct
answer; (4) the controlled-arm "ground truth" itself never having been
an authoritative label to begin with.

**Repair semantics should therefore use a compatibility/plausibility
notion, not single-label exact match, for future calibration** — stated
explicitly per instruction, NOT implemented this pass. The repair
mechanism is **not** hereby declared production-ready: this audit
establishes that category-identity variance is safe to tolerate, not
that the repair step's overall behavior (which still showed a real
cross-call inconsistency, even if consequence-free) needs no further
attention before any integrated adoption decision. Per the project's
own minimize-human-intervention principle: since `problems`' specific
identity is explanatory metadata rather than a consequential decision,
routine automatic repair of THIS narrow allowlisted failure class does
not require per-repair human adjudication of which exact label was
chosen — only that revalidation passes and the immutable fields stayed
frozen, both of which are already deterministically checked.

**Confirmed: zero model calls this pass. No repair prompt edit. No R2
edit. No validator weakening. No Stage C execution (code inspection
only, as instructed). No Reader Lab material inspected or used — Parent
A/B's status was not queried.**

## B2 R2 CONTRACT-REPAIR INTEGRATED RECHECK — EXECUTED, RESULTS SCORED
## (2026-08-13, new session recovering + scoring a run completed by the
## prior session before it hit context limit)

**NOT v2.1. NOT an R2 prompt revision. NOT Stage C.** Preregistered
(`preregistration-integrated-repair-recheck.json`, SHA256
`8b99fa5c4fac090995ab7878b88046ee066696f83218ab132cee38f0c06beb9a`,
matching `pre-run-identity.json`'s recorded value) before any call was
made. Research question: does the validator-guided repair layer work
safely as part of the ACTUAL R1->R2 execution path composed together —
R1 -> validate_r1 -> [valid] R2 -> validate_r2 -> [exact allowlisted
failure] -> ONE repair call -> merge -> validate_r2 again — rather than
as three separate frozen-artifact experiments (D0/C0, R1/R2 partial
structured-output, and the standalone contract-repair probe already
established separately above).

### ARTIFACT RECOVERY (this session's first task)

The run had already completed on Trident before this session started;
this session did not rerun anything. Found via `find /tmp -iname
'*cj2*'` on trident: `/tmp/r2-integrated-repair-recheck-scratch-20260813`,
containing the full frozen bundle (harness + 12 transitively-imported
modules + all upstream `.probe_fixtures`), `full_results.json`,
`run_summary.json`, and the 21 raw per-call records
(`.probe_fixtures/cj2-b2-r2-integrated-repair-recheck/results/{r1,r2,repair}/*.json`)
— none of which existed yet in the local canonical repo (only
`preregistration-integrated-repair-recheck.json` and `pre-run-identity.json`
had been committed to the local fixtures dir pre-execution). Verified,
before copying anything: all 13 frozen harness/module files present in
the trident scratch are byte-identical (SHA256) to the local canonical
copies in `automation/`, AND match every hash recorded in
`pre-run-identity.json`'s `artifact_hashes_sha256` — including the
harness itself (`8eaf152b84...`). The preregistration file on trident
scratch is also byte-identical to the local copy. This confirms the
execution ran against the exact frozen configuration, not a
reconstructed or edited one. Copied `full_results.json`,
`run_summary.json`, and all 21 result files back to the local
`.probe_fixtures/cj2-b2-r2-integrated-repair-recheck/` tree; re-hashed
the local copies and confirmed byte-identical to the trident originals
before doing anything else. Trident scratch deleted only after this
local verification completed, consistent with this project's standing
convention for every prior probe in this track.

### RUN HEALTH

21 total calls (9 R1 + 9 R2 + 3 repair) — inside the preregistered 0-27
range, not the upper bound (repair is only naturally triggered, never
forced). Scanned all 21 raw call records directly: zero non-200 HTTP
statuses, zero exceptions, zero `error` values, all 21 `parsed` non-null
— zero config failures, zero truncations, zero provider schema
failures. `elapsed_seconds: 850.4` for the full run.

### INITIAL R2 VALIDITY

R1: 9/9 valid (matches every prior probe touching this exact 9-item
corpus — zero R1 failures have ever been observed on this corpus).
R2 before repair: 6/9 valid on the first pass (H01, H04, H06, H07, H10,
H12); 3/9 triggered the repair path (H03, H09, H13) — and these are
**the exact same three items** already identified as the corpus's known
failure class across two earlier, separate runs (H03/H09 from the
partial structured-output probe; H13 from the integrated development
probe). Zero items hit `r2_unrelated_invalid_fail_closed` — every
triggered repair matched the narrow allowlisted shape (`support=unsupported`
+ zero semantic-problem tags) exactly, claim-by-claim, confirmed by
`is_pure_allowlisted_failure`'s own regex match against the validator's
violation strings before repair was ever attempted.

### REPAIR RESULTS

All 3 triggered repairs succeeded: `r2_valid_after_repair: true` for
H03, H09, H13, zero `integration_failures` recorded by the harness for
any of the three (the harness itself checks immutable-field
preservation and the append-only merge invariant programmatically, not
just by construction).

| item | claims repaired | added problems | pre-existing tag |
|---|---|---|---|
| H03 | c3, c7, c10, c11 | c3:`other`; c7:`population_relation_hardening`; c10:`other`; c11:`population_relation_hardening`,`other` | all 4 already had `undeclared_factual_dependency` only |
| H09 | c10 | `other` | `undeclared_factual_dependency` only |
| H13 | c7, c11 | c7:`other`; c11:`other`,`mechanism_invention` | both already had `undeclared_factual_dependency` only |

Read every repaired claim's own `why` text (frozen, immutable, from the
live R2 output) to check semantic compatibility rather than
exact-label-matching, per the preregistered criteria:
- H03/c7, H03/c11: both `why` texts describe population-level claims
  about female career-interruption patterns — `population_relation_hardening`
  is a direct, well-matched fit.
- H03/c3, H03/c10, H09/c10, H13/c7: none of the 6 specific hardening
  patterns fit cleanly (program-definition claim, program-effectiveness
  claim, population-pattern claim tagged generically, and an
  "interpretation is the standard/dominant one" claim respectively) —
  `other` is the designed catch-all for exactly this shape, per the
  preregistration's own acknowledgment that some failures "have no
  single forced match."
- H13/c11: claim assumes a specific, unestablished "transmission
  channel designed to carry counter-signals" — `mechanism_invention`
  fits directly; `other` is a defensible secondary tag.

**All 7 additions classified `compatible`. Zero `incompatible`, zero
`questionable`.** No immutable field (`role`, `support`, `declaration`,
`declared_refs`, `auditor_evidence`, `why`, `r1_agreement`,
`override_rationale`, `claim_id`) changed on any repaired claim —
verified both by the harness's own `verify_immutable_fields_unchanged`
(zero violations recorded) and by direct comparison of the pre-repair
R2 raw output against `full_results.json`'s post-repair `per_claim_effective`
view. Every original `problems` value survived the merge (append-only,
confirmed) — no repair silently dropped `undeclared_factual_dependency`.

**Cross-call inconsistency, expected and already-classified, not a new
finding:** H09/c10 was repaired to `other` alone in this run, vs.
`other` + `mechanism_invention` in the earlier standalone contract-repair
probe's natural arm. This is the same category-selection instability
the taxonomy-consequence audit immediately above already found and
explicitly ruled non-consequential to safety — not re-litigated here,
per instruction not to overinterpret run-to-run item-level movement.

### SAFETY INVARIANT — checked live, not just asserted

For every repaired claim, `compute_effective_v2`'s per-claim
`effective_status` was confirmed to be `unsupported` in all 7 cases
(never `supported`, never anything implying the repair made the claim
look safer). This is the harness's own live per-run assertion
(triggering `INTEGRATION_FAILURE` had it failed) — zero triggered, on
all 3 repaired items.

### FINAL PIPELINE

All 9 candidates: `final_disposition: "computed"` — 9/9 final-validator-valid,
0 fail-closed-unrepairable, 0 integration failures, 0 call failures.
`effective_verdict: "unsafe"` on all 9 — expected and correct, not an
anomaly: `compute_effective_v2` sets `any_unsafe` whenever any
`factual_dependency` claim has `effective_status == "unsupported"` or
`declaration == "undeclared"`, and all 9 of these candidates are the
already-known subset (from the earlier offline semantic factuality
audit) containing at least one such claim — the pipeline correctly
flagging known-fabricated content, not a bug making everything
trivially unsafe. Verified directly against `compute_effective_v2`'s
source, not assumed.

### BEFORE / AFTER

| | R1 valid | R2 valid (pre-repair) | Final valid |
|---|---|---|---|
| Integrated development probe | — | — | 8/9 |
| Partial structured-output probe | 9/9 | 7/9 (2 known failures: H03, H09) | — |
| **Integrated repair recheck** | **9/9** | **6/9 direct + 3/9 repaired** | **9/9** |

The repair layer took the corpus from 6/9 directly valid to 9/9
overall valid, absorbing exactly the 3 known-failure items (the same
ones known from the two prior separate probes, no new failure class),
with zero unrelated failures and zero safety regression.

### DECISION

**A. R2 REPAIR LAYER OPERATIONALLY ADEQUATE — READY TO RECONSIDER STAGE C.**
All naturally triggered allowlisted failures (3/3) repaired
successfully; all repaired category choices are semantically compatible
with their claim's own frozen `why` text; all immutable fields verified
unchanged; deterministic revalidation passed on every repair; no new
validator failure class appeared (the trigger set was exactly the
already-known 3 items); no safety/control-flow regression (every
repaired claim stayed at `effective_status=unsupported`). This is the
first time all three previously-separate pieces (provider schema, the
narrow repair layer, and the taxonomy-consequence finding) have been
exercised together as one automatic execution path rather than as
independent frozen-artifact experiments, and they held together
cleanly.

**This decision authorizes reconsidering Stage C next — it does not
itself start Stage C, revise R2, revise R1, revise D0/C0, or touch
Reader Lab.** Per explicit instruction for this pass: no v2.1 assigned,
no further code changes made.

### READER LAB NOTE

Jascha reports both `reviewer_parent_a` and `reviewer_parent_b` have
now completed RL-2026-001. **Not consumed in this pass** — no response
content read, no calibration analysis run, no Round 002 designed, no
manual reviewer action taken. Per the autonomous calibration
infrastructure already deployed (`## 24`–`## 26.8` above), the system
is expected to detect round completion and proceed through export ->
calibration workflow independently, without this research session's
involvement. That analysis is explicitly the next, separate research
stream, not part of this B2 result.

**Confirmed: zero NEW model calls this pass (the 21 calls being scored
were made by the prior session before context ran out — this session
made none). No repair prompt edit. No R2/R1/D0/C0 edit. No Stage C
execution. No Reader Lab response content read.**

## B2 → STAGE C INTEGRATION CONTRACT AUDIT (2026-08-13, same session,
## design/audit only — zero model calls, zero code changes)

**NOT a Stage C run. NOT a prompt edit. NOT v2.1.** Re-verified the
integrated repair recheck's final counts directly from
`full_results.json`/`run_summary.json` before anything else (the
handoff's FINAL PIPELINE line had been truncated in transit): 9 R1 / 9
R2 / 3 repair calls, 21/21 clean, R1 9/9 valid, R2 6/9 valid directly
(H01/H04/H06/H07/H10/H12), H03/H09/H13 the exact known repair triggers,
3/3 repaired, 0 immutable-field changes, 0 integration failures, all 7
repaired claims stayed `unsupported`, **9/9 final validator-valid
confirmed** — with one addition the prior report didn't say plainly:
**all 9 final `effective_verdict`s are `unsafe`**, none `safe`, none
`ambiguous` alone.

### CURRENT STAGE C, reconstructed from code (not memory)

Only implementation that has ever executed: `cj2_reference_probe.py` +
the frozen `cj2-stage-c-v1.txt`. Read `build_stage_c_user` directly:
per candidate it receives `seed_evidence_refs`,
`additional_source_observations`, `engine_move`, `seed_engagement`,
`interpretive_inference`, `conceptual_shift`, `claimed_contribution`
plus its capsule — **zero B2 fields, no R2 claim object, no
`effective_verdict`, confirmed by reading the function, not assumed.**
Responsibilities: 5-dimension independent assessment per candidate
(`factual_integrity`, `seed_engagement`, `engine_dependence`,
`conceptual_movement`, `distinctive_contribution`) → hard-gate
`qualifies`/`does_not_qualify` → winner selection among qualifiers.
Before Stage C today: Stage A (4 engines) → Stage B (deterministic,
structural-only — unknown evidence IDs, observation count/exact-
substring; never checks whether an inference over-reads real
evidence). After Stage C: nothing — not wired into
`discovery.py`/`generate.py`/production anywhere; still a pure research
probe.

**Measured reliability of Stage C's own `factual_integrity`, from
already-completed evidence (the OFFLINE SEMANTIC FACTUALITY AUDIT
above): 0 of ~6 real laundering instances caught, across both available
runs.** Cave DNA/Engine S got `factual_integrity: "pass"` while
inventing a mechanism the source never states; AI Exam/S, /Z, /M all
got `"pass"` despite modality/motivation/causality/population
hardening. Not a hypothetical risk — a measured 0% catch rate on
exactly the failure class this whole B2 track exists to fix.

### DATA FLOW, traced exhaustively

Grepped the entire codebase for `compute_effective_v2`,
`effective_status`, `effective_verdict`, `R1_R2_SEMANTIC_CONFLICT`,
`factual_integrity`: **zero overlap anywhere.** Confirms the premise
stated in this pass's brief: Stage C has no code path consuming R2
claim objects. (Disambiguation: `orchestrator/review.py`'s own "Stage
C" comment is an unrelated production feature — the anchor-architecture
seam-detector — not CJ-2's comparator; checked directly, not
conflated.)

**Structural fact that makes the integration simple, not merely
convenient:** B2's `item_id` (H0N) and Stage A's `(source_slug,
engine_label)` candidate are the SAME unit. Confirmed directly:
`cj2_fresh_batch1_pipeline.py` builds the H0N corpus by importing
`cj2_reference_probe.STAGE_A_SYSTEM`/capsules verbatim (its own
docstring: "NO B2 calls"), and `cj2_fresh_batch1_build_packet.py`
reuses `cj2_reference_probe.anonymize()` for the H0N↔(slug, engine)
mapping. A B2 terminal state for H0N is therefore a terminal state for
exactly one Candidate-letter slot in one future Stage C call — no unit
mismatch to design around.

Field classification: `effective_verdict`/`per_claim.effective_status`/
`consistency` — **D, not wired downstream at all**; `problems` —
**C, diagnostic only** (already proven non-consequential to safety);
every other R2 field (`why`, `auditor_evidence`, `r1_agreement`, etc.)
— **C, diagnostic only**.

### PROPOSED INTEGRATION CONTRACT

| B2 terminal state | ENTER_STAGE_C? | reason |
|---|---|---|
| D0 `schema_invalid`/`span_resolution_failed`/`segment_id_consistency_failed`/`D0_COVERAGE_FAILURE` | NO | gate blocked before R1 ever runs |
| C0 `C0_SCHEMA_INVALID` | NO | C0's own output malformed, never defaults to complete |
| C0 `D0_COVERAGE_FAILURE` (c0_semantic_audit) | NO | C0 caught a semantic miss D0 missed structurally |
| R1 `call_failed`/`schema_invalid` | NO | no valid decomposition |
| R2 `call_failed` | NO | no parseable output |
| R2 invalid, not the allowlisted shape | NO | repair never attempted for non-allowlisted failures |
| R2 invalid, allowlisted, repair call/schema failed | NO | one repair attempt only, no retry |
| R2 invalid, allowlisted, repaired but still invalid | NO | repair mechanically insufficient |
| `INTEGRATION_FAILURE` | NO + engineering-review flag | should structurally never happen (0/3 observed to date); hard stop, not routine routing |
| R2 valid → `effective_verdict="unsafe"` | NO | ≥1 unsupported/undeclared factual_dependency claim |
| R2 valid → `effective_verdict="ambiguous"` | NO, fail-closed to an audit queue (never silently admitted or silently dropped) | unresolved conflict/uncertain support/unresolvable evidence |
| R2 valid → `effective_verdict="safe"` | YES | no unsupported/undeclared claim, no unresolved conflict |

**Minimal payload: none of the above needs to reach Stage C's prompt.**
The gate is a pure orchestrator-side filter — an ineligible candidate
is simply never added to `candidates_by_label`/`letter_map`, exactly
like a Stage-B-invalid candidate is excluded today. Stage C's schema
and prompt need zero new fields — generalizes the taxonomy-consequence
finding one step further: if `problems`' specific identity is already
non-consequential, Stage C never needed claim-level R2 detail at all; a
single upstream boolean per candidate is sufficient (least information
necessary, option A from the brief).

**Authoritative factuality boundary:** B2 becomes authoritative for
ELIGIBILITY. Stage C's `factual_integrity` dimension is left completely
unedited this pass, but is structurally demoted to a secondary sanity
check exercised only on candidates that already cleared B2 — given its
measured 0/6 catch rate it should not be relied on standalone, but no
prompt edit is proposed. No authority conflict: an excluded candidate is
never handed to Stage C, so Stage C has no path to override B2.

### REPAIR HANDLING

Repaired-valid candidates route identically to directly-valid ones —
the contract makes no distinction. Sharper finding from the actual run:
because the safety invariant forces every repaired claim's
`effective_status` to stay `unsupported`, **repair can never move an
item into `safe` or `ambiguous` by construction** — in all 3 repaired
items this run, the item was already `unsafe` regardless (the repaired
claim itself contributes to `any_unsafe`, on top of other already-
unsupported claims in the same item). Repair changes WHY a candidate is
excluded (uninformative validator failure → correctly-labeled unsafe),
not WHETHER, in every case observed so far. Provenance fields to keep,
orchestrator-side only, never shown to the Stage C model:
`repair_occurred`, `b2_terminal_state`, a pointer to the full B2 record
— no `problems` value, no repair category.

### DRY-RUN (existing artifacts only, zero new calls)

1. D0/C0 blocked — H03 in `case-role-table.json`'s "execution-envelope
   recovery" instance: C0 caught a missing "discriminatory asymmetry"
   half of `conceptual_shift` → `D0_COVERAGE_FAILURE` → NO. (Caveat: a
   *different* completed instance than this session's own H03, which
   passed gate cleanly in a later, separate D0/C0 call — real cross-
   call gate instability on the same theme/label, already a documented
   pattern elsewhere in this project, not resolved here, flagged so the
   two aren't conflated.)
2. Normal B2-`safe` case — **none exists.** Every completed run and
   every static-test fixture to date has produced `unsafe` or
   `ambiguous`, never `safe`. Recommending, not doing: a synthetic
   all-clean fixture before any real integration probe, so the
   `safe`→YES branch is exercised at least once before it matters.
3. Repaired R2 case — H03 (this run): repair succeeded, but
   `effective_verdict="unsafe"` (repaired claims stayed `unsupported`
   plus other unrepaired unsupported claims) → NO, correctly labeled
   rather than validator-failed.
4. R1/R2 semantic-conflict case — H01: 9 `R1_R2_SEMANTIC_CONFLICT`
   claims AND 3 plain-unsupported claims (`c4`/`c9`/`c13`/`c14`) →
   `unsafe` (outranks ambiguous by the code's own priority order) → NO.
5. Existing Stage C comparator example, pre-integration — Cave
   DNA/Engine S: Stage C rated it `factual_integrity: "pass"` and let
   it compete despite inventing a mechanism the offline audit later
   confirmed unsupported. Under the proposed contract this candidate's
   B2 decomposition would very likely flag that mechanism claim
   unsupported → excluded before ever reaching Stage C — the clearest
   concrete illustration of what this integration fixes.

### AUTOMATION

Every row is a deterministic branch off already-computed enums — no
model decides routing; routine cases need zero Jascha intervention.
`ambiguous` is the one deliberate exception, failing closed to an audit
queue by policy, not per-case judgment.

### DECISION

**B — INTEGRATION CONTRACT REQUIRES ONE NARROW DESIGN CHANGE BEFORE
PROBE.** The contract is fully determined by code that already exists
— no new taxonomy, no responsibility ambiguity. The missing piece: a
new orchestrator-side filter (e.g. `b2_eligible(terminal_state)`
implementing the table above) inserted into `run_source()` between the
existing `stage_b_validate` filter and `anonymize()`/
`candidates_by_label` — no edit to D0/C0/R1/R2/repair-v1, no edit to
Stage C's prompt or schema. Not A (that code doesn't exist yet). Not C
(no genuine responsibility conflict found — Stage C's gate simply
becomes secondary, no redesign of either layer needed).

**Housekeeping note, not acted on:** `automation/cj2_b2_r2_repair_
integrated_recheck.py` (note the word order vs. the canonical
`cj2_b2_r2_integrated_repair_recheck.py`) is an orphaned earlier draft
— nothing imports it, it was not part of the executed/frozen bundle.
Left in place, not deleted, since cleanup wasn't requested this pass.

**Confirmed: zero model calls. Zero code changes. No D0/C0/R1/R2/
repair-v1/Stage-C-prompt edit. No Stage C execution. Reader Lab: both
parents reported complete, not inspected or consumed, left to the
autonomous calibration pipeline.**

## B2 -> STAGE C ADMISSION GATE — IMPLEMENTED, MECHANICALLY TESTED
## (2026-08-13, same session, code + static tests only, zero model calls)

**Implements the narrow design change identified by the audit above.
Does NOT run Stage C.** Two new files, one edited:

- `automation/cj2_b2_stage_c_admission_gate.py` (new) — the entire gate.
  Zero non-`__future__` imports (verified by its own test suite) — it
  reads only a small dict envelope, never D0/C0/R1/R2/repair-v1, never
  Stage C's prompt/schema, never `problems`. Two public entry points:
  `classify_b2_terminal_state(b2_result) -> str` (one of the exact
  labels from the audited routing table, or the sentinel
  `"UNRECOGNIZED_B2_RESULT"`), and `route(terminal_state) -> ENTER_STAGE_C
  | BLOCK_BEFORE_STAGE_C` — a plain dict `.get()` with the fail-closed
  default supplied explicitly, so no typo'd/unrecognized label can ever
  resolve to admission. `gate_candidate(b2_result)` wraps both plus
  `repair_occurred`/`item_id` provenance.
- `automation/cj2_b2_stage_c_admission_gate_static_tests.py` (new) —
  112/112 checks pass, zero model calls.
- `automation/cj2_reference_probe.py` (edited) — `run_source()` gained
  `b2_admission_lookup=None, require_b2_admission=True`. The gate runs
  exactly where the audit said it must: after the existing Stage B
  `surviving` filter, before `anonymize()`/`candidates_by_label`. A
  label missing from `b2_admission_lookup` is treated as unrecognized
  and blocked — there is no "no B2 data -> allow" path, which means a
  bare `main()` rerun of the original 3-source probe would now
  correctly report 0 admitted on every source (intentional: it forces
  every future integrated call to actually supply real B2 data rather
  than silently reverting to the pre-gate behavior). A live assertion
  immediately before `candidates_by_label` construction re-checks that
  every surviving label has an explicit `ENTER_STAGE_C` decision.
  `require_b2_admission=False` is the sole, explicit, non-default
  bypass, reserved for unit-testing the pre-existing anonymization/
  Stage-C-prompt machinery in isolation — `main()` never sets it, so
  normal execution cannot reach it by accident. Stage C's own prompt,
  schema, `build_stage_c_user`, `stage_c_projection`, and `_call` are
  byte-for-byte unedited; confirmed by the test suite reading the
  actual function source, not by assertion alone.

**Routing table implemented exactly as audited** (12 terminal-state
labels -> exactly one of 2 outcomes; only `EFFECTIVE_VERDICT_SAFE`
routes to `ENTER_STAGE_C`, verified as the ONLY such row in the table
by an explicit test). Repair transparency implemented as specified:
`repair_occurred` is surfaced as provenance and never itself affects
routing — proven with both a real fixture (H03/H09/H13, repaired-valid
but still routed BLOCK because the final verdict is `unsafe`) and a
synthetic one (repaired-AND-safe still routes `ENTER_STAGE_C`).

**Bypass audit: exactly one Stage C invocation path exists in the
entire codebase** (`cj2_reference_probe.py` — grepped for
`STAGE_C_SYSTEM`/`build_stage_c_user`/`stage_c_projection`/`run_source`
across every `.py` file; nothing else matched), so there is nothing
else to gate.

**Coverage reality, stated precisely, not glossed over:** of the 12
distinct classification branches, only 3 have ever been exercised
against real, already-completed B2 data — the C0 semantic gate-block
(H03, reconstructed by replaying the real, frozen, already-completed
D0/C0 output for that item through the actual unmodified
`compute_pipeline_gate` function — zero new model calls), and two
`EFFECTIVE_VERDICT_UNSAFE` cases (H01's real semantic-conflict-plus-
unsafe item, and H03/H09/H13's real repaired-but-still-unsafe items).
**Every other branch — R1 failure, R2 call failure, R2-invalid-
unrelated-to-allowlist, repair-call-failure, repaired-still-invalid,
`INTEGRATION_FAILURE`, plain `ambiguous`, and — critically —
`EFFECTIVE_VERDICT_SAFE` itself — has no real precedent anywhere in
this project and is tested only with a labeled SYNTHETIC CONTROL-FLOW
FIXTURE.** After this pass we may say the `ENTER_STAGE_C` control-flow
branch is mechanically tested; we may NOT say B2 has demonstrated a
naturally occurring safe candidate — that empirical question remains
completely open.

**Regression: all 12 pre-existing static-test suites in `automation/`
re-run, 12/12 still ALL PASS** (`cj2_b2_c0`, `cj2_b2_d0`,
`cj2_b2_d0c0_execution_envelope_recovery`, `cj2_b2_d0c0_first_probe`,
`cj2_b2_d0c0_natural_c0_recovery`, `cj2_b2_d0c0_output_normalizer`,
`cj2_b2_d0c0_real_material_transfer_probe`,
`cj2_b2_integrated_pipeline_probe`,
`cj2_b2_r1r2_partial_structured_output_probe`,
`cj2_b2_r2_contract_repair_probe`, `cj2_b2_r2_integrated_repair_recheck`,
`cj2_b2_v2`) — confirms this pass changed nothing semantic in D0/C0/R1/
R2/repair-v1.

**Decision: A — ROUTING LAYER IMPLEMENTED AND MECHANICALLY VALIDATED —
READY FOR A STAGE C INTEGRATION PROBE**, with the coverage caveat above
carried forward explicitly into that probe's own design: the probe
should be expected to exercise `EFFECTIVE_VERDICT_SAFE` for the first
time on real data, since nothing to date ever has.

**No Stage C execution. No v2.1. No prompt/validator edit anywhere. No
Reader Lab consumption** (both parents reported complete, left entirely
to the autonomous calibration pipeline).

## B2 -> STAGE C FIRST INTEGRATED DEVELOPMENT PROBE — EXECUTED, RESULTS
## SCORED (2026-08-13, same session): ZERO NATURAL STAGE-C ADMISSIONS

**NOT v2.1. NOT a semantic edit to D0/C0/R1/R2/repair-v1/the admission
gate/Stage C.** First real, live execution of the full composed path:
D0 -> C0 -> `compute_pipeline_gate` -> [R1 -> R2 -> repair-if-triggered]
-> `compute_effective_v2` -> `cj2_b2_stage_c_admission_gate.gate_candidate`
-> conditional Stage C. Preregistered before any call
(`preregistration-first-integrated-development-probe.json`, matching
`pre-run-identity.json`).

### CORPUS

14 items: the same 10 already-frozen (H01,H02,H03,H04,H06,H07,H09,H10,
H12,H13) reused across every prior R1/R2/repair probe, plus 4 genuinely
fresh (H11,H15,H16,H18) — same Fresh Calibration Batch 1 pool, never
before run through the current D0/C0/R1/R2/repair architecture (only
through now-superseded B2 v1.2/v1.3/v1.4.1). The 4 new items' fields
were extracted from `human-review-packet-v1.1.md` by a regex parser
verified byte-identical (0 mismatches, 50/50 fields) against all 10
already-frozen items before being trusted on the new 4; their seeds
were reused byte-for-byte from same-slug existing items (confirmed via
the packet's own hidden engine/slug mapping, e.g. H11 shares NSFC's
`fresh02` slug with H03/H09). **RL-2026-001's five (H05, H08, H14, H17,
De Hooch/Z) confirmed absent** — none share an item_id or slug-position
with the corpus. No candidate was selected or excluded after seeing any
B2 verdict; no safe case was fabricated, forced, or rerun for.

### RUN HEALTH

First launch attempt made **zero real API calls** — failed immediately
with `HTTPError 401` because `CLIPROXY_KEY` wasn't set in the
non-interactive SSH session that launched it (normally sourced from
`/srv/secrets/openclaw.env`); caught, fixed, relaunched. The bundle
itself also needed two transitively-imported modules
(`cj2_b2_d0c0_real_material_transfer_probe.py`, `cj2_b2_probe_v1_4_1.py`)
added after a `ModuleNotFoundError` on the same first attempt — both
caught before any model call, both added and hash-verified, bundle
re-confirmed to import cleanly in full isolation before rerunning.
**Real execution: 1568.7s elapsed, 50 total calls** (14 D0, 12 C0, 12
R1, 12 R2, 0 repair, 0 Stage C — C0/R1/R2 lower than 14 because 2 items
blocked at D0's own structural stage before C0 ever ran). Scanned every
raw call record: the only anomaly was that all 14 D0 raw responses were
wrapped in a ` ```json ` markdown fence, failing direct `json.loads`
(the already-existing `cj2_b2_d0c0_output_normalizer.py` recovered all
14 correctly — confirmed directly: H01's `d0_effective_status.status`
is `"valid"` with real, non-empty coverage data, not a normalizer
failure default). Zero call failures, zero exceptions, zero
config_failures, run never stopped early.

### D0/C0

12/14 valid through D0; **2/14 (H06, H15) blocked at D0's own
structural stage — `span_resolution_failed`**, a genuinely new terminal
state never observed in any prior run (H06: claim c4's
`exact_surface_span` didn't match the source_snapshot; H15: claim c13,
same failure mode) — D0 hallucinated a span, caught deterministically
by D0's own validator, before C0 or R1 ever ran. Of the 12 that reached
C0, **12/12 said `complete`, zero blocks at C0's semantic-audit stage**
— notably, H02 (this probe's intended negative control, based on a
real C0 block observed in the separate, earlier integrated-pipeline-probe
run) did NOT reproduce that block this time. Not treated as a
contradiction: D0/C0 are live model calls, and this exact kind of
cross-call gate instability is already a documented pattern in this
project (the earlier Stage C integration audit flagged the same thing
for a different item, H03). H06/H15's block became this run's own
real, live negative control instead — proving in this exact execution,
not a synthetic fixture, that a genuine D0-level block correctly
produces zero downstream R1/R2/Stage C calls.

### R1/R2/REPAIR

12/12 R1 valid. **12/12 R2 valid directly — zero repairs triggered**,
the first time in this project's history that the previously-reliable
`support=unsupported`+empty-`problems` failure class did not appear
even once in a run of this size. Not weakened, not forced — the repair
layer was simply never invoked because nothing needed it this time.
200 total claims scored across the 12 items: 60 `unsupported`, 52
`supported`, 23 `not_required` (interpretive_only), 1 `uncertain`, and
**64 `R1_R2_SEMANTIC_CONFLICT`** (32% of all claims — the highest
semantic-conflict rate observed in this track to date). Every one of
the 12 items had at least one unsupported/undeclared factual_dependency
claim (range: 1 in H09, up to 12 in H13) — **12/12 final
`effective_verdict: unsafe`**, zero `safe`, zero `ambiguous`. Zero
integration failures across all 12.

### ADMISSION

14/14 terminal states classified, 14/14 routed `BLOCK_BEFORE_STAGE_C`
(2 via `D0_SPAN_RESOLUTION_FAILED`, 12 via `EFFECTIVE_VERDICT_UNSAFE`),
**0/14 `ENTER_STAGE_C`. Stage C call count: 0 — exactly matching the
admitted count of 0, with zero exceptions.** The admission gate's own
live assertion (every candidate reaching `candidates_by_label` must
carry an explicit `ENTER_STAGE_C` decision) never fired, consistent
with zero candidates ever reaching that point.

### STAGE C

Not exercised — zero admitted candidates, zero calls, per instruction
not to fabricate one. `EFFECTIVE_VERDICT_SAFE` remains, after this
pass, an entirely synthetic-only-tested branch — no real occurrence has
ever been observed anywhere in this project.

### NEGATIVE CONTROL

H06 and H15, blocked live in this exact run (not a reused synthetic
fixture), produced zero R1/R2/repair/Stage C calls each — proven
directly from `full_results.json`, not assumed from the gate result
alone.

### INTERPRETATION

B2 is, on this corpus, extremely conservative: 12/12 gate-passed items
came back unsafe, 0/14 ever reached Stage C. This is the corpus's
second full pass through the current architecture (10 of 14 items were
already known-unsafe from the integrated repair recheck; the 4 new
items replicate the same pattern on genuinely fresh material) — the
finding generalizes rather than being an artifact of reusing known
material. The open research question this leaves, exactly as
anticipated: is B2 correctly conservative (Fresh Calibration Batch 1's
candidates may simply contain real, pervasive semantic-fact-laundering,
consistent with the earlier offline audit's own finding that 6/12
FIRST-REFERENCE-PROBE candidates showed exactly this), or is some part
of the R1/R2 taxonomy over-triggering on legitimate interpretive
material? This probe cannot distinguish those on its own — a
genuinely-clean development item (or human-calibration evidence, once
consumed as its own separate stream) would be needed to tell them
apart. Stage C's semantic integration remains, after this pass, still
entirely unobserved on any naturally admitted real candidate.

### DECISION

**B — ROUTING WORKS, BUT ZERO NATURAL SAFE ADMISSIONS — STAGE C
SEMANTIC INTEGRATION STILL UNOBSERVED.** All 14 terminal states routed
correctly and deterministically; the negative control (H06/H15) proved
live that a block produces zero downstream calls; no integration
failure; no new material mechanical failure (the D0 markdown-fence
wrapping was already-handled, not new). Not A, because Stage C's own
execution under real admission has still never been exercised on
naturally occurring data — that remains open.

**Confirmed: 50 real model calls (14 D0 + 12 C0 + 12 R1 + 12 R2 + 0
repair + 0 Stage C). No D0/C0/R1/R2/repair-v1/admission-table/Stage-C
edit. No v2.1. No Reader Lab consumption** (both parents reported
complete, not inspected, left to the autonomous calibration pipeline).

## READER LAB × B2 HUMAN-CALIBRATION ANALYSIS — RL-2026-001 COMPLETE,
## FIRST REAL EVIDENCE (2026-08-13, same session, analysis only —
## zero model calls, zero D0/C0/R1/R2/repair-v1/admission-policy edits)

Full detail, per-item comment text, and the "aligns is role-only, not
support-direction" finding are in `.claude/current-work.md`'s READER LAB
section — not duplicated here in full. Summary for this track's own
record: of RL-2026-001's 5 cases (H08/H17/H14/H05/De-Hooch-Z, all
already-existing B2-v2 development fixtures, no reruns), only **1
(H14) shows full human/B2 alignment**; **3 lean more permissive than
B2's own stricter stage** (H17 and H05 — the same R1-factual/R2-
interpretive hedge-conflict shape, replicated twice, with neither
reviewer ever selecting "adds unestablished" in either case; and
De Hooch/Z, the round's own control, where both reviewers said
`source_established` against B2's agreed `unsupported`); **1 (H08) is
genuinely mixed**. This is the first evidence bearing directly on
whether B2's factuality floor (the same floor the Stage C admission
gate now enforces, per `## B2 → STAGE C ADMISSION GATE` above) is
calibrated to independent human judgment, not just internally
consistent. Small sample (n=2 reviewers, n=5 items) — a real first
signal, not proof, and specifically points at the R1-factual/R2-
interpretive hedge-conflict shape as the most promising target for a
future, still-not-yet-run, targeted calibration experiment. Not acted
on this pass — no B2 change, no re-scoring of contested cases into
binary truth, no new Reader Lab round created.

## B2 HUMAN-CALIBRATED SUPPORT-BOUNDARY AUDIT (2026-08-13, same
## session, zero model calls — read exact frozen R1/R2 records only)

**Read the exact R1/R2 record for the specific claim shown to reviewers
in H14, De Hooch/Z, H17, H05** (`automation/.probe_fixtures/
cj2-b2-v2-r2-recovery/recovery_results/per_candidate/*.json`, matched
to each candidate_sentence via `reader-lab/rounds/drafts/RL-2026-001.json`).
H08 has no such record (that's the coverage-miss finding itself) — used
only as a secondary, unresolved reference.

**H14 (c8)** — role=`factual_dependency`, support=`unsupported`,
`r1_agreement=consistent` (no conflict), `problems=["other"]`. R2's own
why: the source establishes only that "policy" *appears* in 3,700+
titles/abstracts — it says NOTHING anywhere about the word's semantic
FUNCTION in any of those documents. The claim ("load-bearing... marks
orientation") asserts an entirely new, textually-unanchored property.
**Both humans independently agreed: `unsupported_factual_dependency`.**
Full role AND support alignment.

**De Hooch/Z (c12)** — role=`factual_dependency`, support=`unsupported`,
`r1_agreement=consistent` (no conflict), `problems=["causality_hardening"]`.
R2's why: the source separately states (a) the visual contrast (woman
drinks, men don't) and (b) the curator's own quote that the restored
version is "more moralistic... which was the intention of de Hooch" —
R2 says the CONNECTION ("functioned through this contrast") between
those two facts is an unsupported mechanistic addition. **Critically:
these two facts are not independently established elsewhere — they are
adjacent sentences in the SAME continuous quote, from the SAME speaker,
where the curator herself moves from "more obvious drinking game" to
"more moralistic... the intention."** Reviewer A's own comment
independently isolates exactly this: *"I think 'contrast and
implication' is indeed a reading of the source. But as a whole I think
it's directly traceable to the source"* — the human explicitly flags
the same connective move R2 flagged, then judges it does NOT cross the
support line. Reviewer B: `source_established`, no hedge. **Role
aligns; support direction reverses.**

**H17 (c6/c7) and H05 (c12)** — replicate an identical mechanism: R1
(blind extraction) tags `empirical_dependency=true`; R2 (full-context
audit) overrides to `role=interpretive_only, support=not_required`,
reasoning in both cases that the claim is "a conceptual
recharacterization of already-established structure/behavior... not an
assertion of an additional empirical fact" (near-verbatim phrasing in
both `override_rationale` fields). Reviewer A's comments (H17: *"no
suggestion at all about motherhood... it's an interpretation"*; H05:
*"a very free interpretation I don't follow well"*) independently
reconstruct R2's OWN resolution — not R1's. Reviewer B picks
`source_established` in both, more permissive than either machine
stage. **Neither human ever validates R1's stricter `empirical_
dependency=true` reading.** Confirmed via `per_claim_effective`: in
both items the conflicted claim itself resolves to
`unresolved_semantic_conflict` (ambiguous bucket) — the item's own
overall `unsafe` verdict is driven by a *different*, uncontested claim
(H17: c15) — so R2's own final per-claim call already leans toward the
side humans independently validate; the friction is the R1/R2
disagreement itself, not R2's resolution of it.

### Source-to-claim distance, ordered by what these four cases actually support

1. **H17/H05 — interpretive reframing of an already-fully-established
   structural fact, zero new content asserted.** R2's own resolution
   already matches (or is exceeded by) human leniency; the flag exists
   only because R1's blind pass mistagged it.
2. **De Hooch — causal/mechanistic synthesis of two facts the source
   ALREADY states adjacently, same speaker, same quote.** This is
   exactly where R2 and independent humans diverge.
3. **H14 — a wholly new, textually-unanchored property claim, no
   adjacent fact to synthesize from anywhere in the source.** R2 and
   both humans agree.

### CALIBRATION HYPOTHESIS (narrow, falsifiable)

**B2/R2's `causality_hardening`/mechanism-detection check does not
distinguish "synthesizing a causal/mechanistic connection between two
facts the source already states adjacently, from the same speaker or
passage" from "asserting a new fact with no textual anchor at all" —
independent human readers draw exactly that line, accepting the former
as source-established and rejecting only the latter as unsupported.**
Falsifiable prediction: given a sample of R2-flagged
`causality_hardening`/`mechanism_invention` claims, human agreement
with B2's "unsupported" call will be measurably higher for claims with
no adjacent-fact anchor (H14-shaped) than for claims connecting two
already-adjacent, same-passage source statements (De Hooch-shaped).

**Zero-safe hypothesis (explicitly not proven, flagged as hypothesis
only):** this exact move — connecting two source-adjacent facts into
one interpretive/mechanistic sentence — is close to definitionally what
Stage A's `interpretive_inference`/`conceptual_shift` fields are
*designed* to do. If R2 systematically flags this common, low-risk
synthesis pattern the same way it flags a wholly unanchored fact, that
would help explain why the just-completed B2→Stage-C probe found 14/14
blocked, 0/14 safe — not proven here, a plausible contributing
mechanism worth testing directly.

### NEXT EXPERIMENT DESIGN (proposed only, not executed)

A future round should include, all `dataset_purpose=development`, none
overlapping RL-2026-001's own 5 or any `held_out_evaluation` material:
- **Boundary-fit cases**: real R2-flagged `causality_hardening`/
  `mechanism_invention` claims where the two connected facts are
  independently verifiable as adjacent/same-speaker in the source
  (De-Hooch-shaped) — candidates exist in the just-completed 14-item
  probe's and the repair-recheck's own `per_claim_effective` records,
  not yet enumerated here.
- **Contrast cases**: H14-shaped claims (wholly unanchored property,
  zero adjacent fact) as an anti-overcorrection check — if humans stop
  agreeing with B2 on these too, the hypothesis is wrong, not just
  imprecise.
- **Fresh, never-seen material** for both shapes, not reused from any
  prior round.
- Explicit human-calibration provenance on every item; no candidate
  drawn from `calibration_candidates` unless `eligible_for_reader_lab=1`
  and `dataset_purpose != held_out_evaluation`, per `prepare-next-round-v1`'s
  own existing fail-closed check.

### READER LAB INSTRUMENTATION FINDING (not implemented this pass)

`analyze-human-round-v1`'s `machine_comparison` checks ROLE only,
never support DIRECTION — this is exactly what made De Hooch's
"aligns" misleading. Minimum future schema, preserving every historical
artifact unchanged (additive only): split into `role_alignment`
(`aligns`/`diverges`/`no_machine_reference`/`not_applicable`, computed
exactly as today) + `support_alignment` (same enum, comparing agreed
human support direction against B2's own support verdict, only when
both are determined) + `overall_relation` (a plain-language rollup:
`full_alignment` / `role_only_alignment` / `full_divergence` /
`not_comparable`) — De Hooch would then read
`role_alignment=aligns, support_alignction=diverges,
overall_relation=role_only_alignment` instead of a single misleading
`aligns`. Not built this pass — a future `analyze-human-round-v2`.

### DECISION

**A — A NARROW SUPPORT-BOUNDARY CALIBRATION HYPOTHESIS IS JUSTIFIED.**
Grounded directly in exact source/claim relations, not intuition: H14
and De Hooch share the same role, the same "unsupported" support call,
and the same absence of any conflict — yet only one is human-endorsed,
and the frozen `why` text pinpoints exactly where they differ
(unanchored property vs. adjacent-fact synthesis). H17/H05 independently
corroborate that R2's own resolution of an ambiguous case already
tracks human leniency more closely than R1's blind pass does. Stated as
a supported calibration hypothesis, not proof, and not acted on: no
D0/C0/R1/R2/repair-v1 edit, no admission-gate change, no Stage C run,
no v2.1, no fine-tuning, no Reader Lab code change this pass.

## B2 SUPPORT-BOUNDARY TARGETED CALIBRATION ROUND DESIGN (RL-2026-002
## DRAFT, 2026-08-13, same session) — PREPARED, NOT PUBLISHED, BLOCKED
## ON A REAL INFRASTRUCTURE GAP

**Zero model calls. Searched three already-completed real corpora**
(the 14-item stage-c-first-integrated-development-probe; the 9-item
integrated-repair-recheck; the 18-item v2-r2-recovery set, which
includes the original FIRST REFERENCE PROBE's Cave DNA/AI-Exam/De-Hooch
candidates) **for `causality_hardening`/`mechanism_invention`-tagged
claims fitting the two preregistered families.**

**Honest yield, not padded:** many clean `UNANCHORED_PROPERTY`
candidates exist (H11/c6 — NSFC population-mechanism, zero anchor;
`01_cave_dna/S` c8 — mineral-crust "erasure," zero anchor; plus a large
reserve pool in AI-Cheating-Exam/S and SNSF/H02 not used this round).
**Only ONE unambiguous `ADJACENT_FACT_SYNTHESIS` candidate was found**
(H04/c10, phosphine abstract — connects the source's own adjacent
"at-odds reactivity" + "phosphines succeed" sentences) plus one
weaker, compound-tagged second (H12/c6, same source, also carries an
unrelated `modality_hardening` confound, kept but flagged). This
scarcity itself corroborates the completed audit's own observation:
the clean "source draws its own connection" pattern is rare within
R2's flagged output — De Hooch may genuinely be one of the few sharp
examples, not a typical case. **Excluded, not forced into a family:**
H13's (Afghanistan) causality claims — the source lists its component
facts as separate narrative grievances, never itself drawing the
causal link (unlike De Hooch's single-speaker quote) — a genuine third
shape, not either family; H02's (SNSF) mechanism claims — each
elaborates a mechanism around ONE fact, not a synthesis of two; the
older v2-r2-recovery H18 candidates — over-precise procedural
resequencing of one already-stated mechanism, a third pattern again;
De Hooch/Z's other claims (c9/c13/c17/c18) — same engine reading as
RL-2026-001's already-used c12, near-duplicate reasoning, excluded to
avoid diluting fresh evidence even though technically distinct
`candidate_claim_id`s.

**Final round: 5 items** (2 `ADJACENT_FACT_SYNTHESIS`, 2
`UNANCHORED_PROPERTY`, 1 control — H16/c4, a genuinely `supported`
claim, chosen specifically because RL-2026-001's own control, De
Hooch/Z, turned out NOT to be a clean supported baseline). Zero overlap
with RL-2026-001's 5 `candidate_claim_id` hashes, verified
programmatically. Both existing reviewers eligible for all 5 (fresh
content, not the same content re-shown).

**Artifacts produced, all local, all uncommitted:**
`calibration/candidates/RL-2026-002-candidates.json` (calibration_
candidates-shaped, ready to insert), `calibration/candidates/
RL-2026-002-preregistration.json` (exact hypothesis, per-family
analysis plan, explicit anti-overcorrection check, no arbitrary
threshold), `calibration/research-context/RL-2026-002.json`
(`machine_role`/`machine_support`/`machine_effective_state` stored
SEPARATELY from the start — the fix for RL-2026-001's own
role-only-`machine_comparison` blind spot, applied going forward
without touching RL-2026-001's historical records), `reader-lab/
rounds/drafts/RL-2026-002.json` (reviewer-facing draft, family
labels/hypothesis/machine fields all excluded from what reviewers see).

**REAL INFRASTRUCTURE BLOCKER, confirmed by code inspection, not
assumed:** `calibration_candidates` (migration `0004`) has **no write
path anywhere in the codebase** — `calibrationWorkflow.js` only ever
`SELECT`s from it; no admin-API insert route exists. `prepare-next-round-v1`
therefore cannot be invoked for real on this round's candidates without
either (a) an admin-API route that doesn't exist yet, or (b) raw
`wrangler d1 execute` SQL, which this pass's own instructions
explicitly forbid treating as the launch path. **Per instruction:
stopping here** — the candidate manifest is ready to insert the moment
that bridge exists; nothing was inserted, nothing was published, no
SQL was run, no peer session was asked to bypass this.

**No B2 edit. No Stage C run. No v2.1. No fine-tuning. RL-2026-001
untouched** (read only for the motivating evidence already established
in the prior pass, not re-scored, not re-read for new content).

## B2 ZERO-SAFE BOTTLENECK ATTRIBUTION AUDIT (2026-08-13, same session,
## zero model calls, read frozen artifacts only)

**Eligible corpus:** the 14-item Stage-C-first-probe corpus minus
RL-2026-002's 4 (H04, H11, H12, H16 — RL-2026-001's own 5 aren't even
members of this 14-item corpus, so only RL-2026-002's exclusions bind)
= **10 items**: H06/H15 (D0-structural-blocked) + H01/H02/H03/H07/H09/
H10/H13/H18 (8 unsafe, R1/R2-computed).

**Headline finding: 0/8 of the remaining unsafe items are
`POTENTIALLY_UNLOCKED` by the RL-2026-002 hypothesis.** Read all 42
unsupported claims' exact `problems` tags and full `why` text (not
truncated) across the 8 items. None contains a claim matching
RL-2026-002's actual tested shape (two facts the source states
adjacently/same-passage, candidate connects them — the H04/c10 pattern).
The dominant real shapes instead:

- **Shape A (clear unanchored fact/property)** — H03 (6/6: population/
  motivation claims like "female researchers more likely to have
  interrupted careers," zero source anchor beyond the bare age-cutoff
  fact), H09 (1/1, same population-claim shape, independently
  replicated), H10 (5/5, tagged `other`+`undeclared` — absence-inference
  claims about what instruments do NOT measure).
- **Shape E (causal/mechanistic addition, PARTIAL anchor — single fact
  elaborated with an invented mechanism/motive, distinct from clean
  adjacent-fact synthesis)** — H02 (11/11: every claim elaborates the
  SAME one anchored fact, "panels added plus/minus grades," with an
  invented pressure/coupling/co-production mechanism — never a second
  independently-stated fact), H13 (10/12: same pattern, source states
  the component facts as a narrative LIST of separate grievances,
  never itself drawing the causal link — the exact reason these were
  already excluded from RL-2026-002's own candidate pool), H18 (1/2).
- **Shape C (hedge/modality hardening)** — H01 (2/2), H07 (2/3, one
  claim also carries `motivation_invention`) — tagged `modality_hardening`
  only, a materially different phenomenon from RL-2026-002's tested
  `causality_hardening`/`mechanism_invention` tags.
- **Shape F (structural/span failure)** — H06, H15 — blocked at D0,
  never reach R1/R2 at all.
- **Shape G (other/unclear)** — H18/c13 (a claim about what a
  hypothetical "generic reader" would conclude — genuinely doesn't fit
  any named shape).

**Important meta-finding, not previously stated this precisely: the
`causality_hardening`/`mechanism_invention` TAGS conflate at least two
distinct researcher-side shapes** — clean two-fact adjacent synthesis
(rare; RL-2026-002's actual test subject) vs. single-fact mechanism
elaboration with only partial anchor (common; H02/H13/H18, Shape E,
currently untested by any Reader Lab round). Tag ≠ shape — this pass
had to read full `why` text per claim, not just count tags, to tell
them apart.

**Minimum blocking set:** for every unsafe item, `any_unsafe` fires
from `>=1` unsupported factual_dependency claim — trivially "1" in
size, but the diagnostic question is whether that 1 (or more) is
ALWAYS a different, independently-sufficient shape from the disputed
boundary. For all 8 items, yes: every single one has its unsafe status
fully explained by shapes A/C/E/G, never by the disputed Shape B alone.
**R1/R2 semantic-conflict claims (up to 12 in a single item, H09) are
NOT part of any item's minimum blocking set** — `any_unsafe` already
fires from the unsupported claims before conflict resolution matters;
conflicts would only drive `ambiguous`, which unsafe always outranks.

### ANTI-OVERCORRECTION SET (must-stay-strict, non-Reader-Lab material)

H03/c7 and H09/c10 (independently replicated population-interruption-
rate claim, zero anchor, two different items/engines) — H03/c9
(motivation-invention, "designers implicitly acknowledged") — H10/c1
(instrument-limitation claim, zero anchor, different topic entirely).
Four clean Shape-A cases, topically diverse (NSFC policy x2, solar
corona), none used in either Reader Lab round.

### POTENTIAL FUTURE STAGE-C ADMISSION CASES

**None found in this corpus.** The one clean adjacent-fact-synthesis
instance this project has ever found (H04/c10) was already spent on
RL-2026-002 itself — there was no second one left over in the
remaining eligible material. This is itself informative: the pattern
RL-2026-002 tests is rare enough that this audit could not surface any
*additional* real candidate it would unlock.

### WHAT 0/14 ACTUALLY MEANS

Structural (D0 span failure): 2/14 (H06, H15) — unrelated to any
semantic calibration question. Semantic, dominated by Shape A
(genuinely unanchored, should stay strict) and Shape E (single-fact
mechanism elaboration, real but currently uncalibrated by any Reader
Lab round): the large majority of the remaining 8. Attributable to the
specific hypothesis RL-2026-002 is testing: **effectively none of this
corpus's zero-safe result** — 0 of 8 items would flip on that
hypothesis alone. **This does not mean RL-2026-002 is uninformative**
(H04/c10 itself, now in that round, was real) — it means the
adjacent-fact-synthesis question, even if fully resolved permissively,
is not this probe's dominant bottleneck. Shape E is the largest
never-yet-tested candidate for a *future* calibration question.

### FINAL EXPERIMENTAL ROADMAP (not executed)

- **Phase 1 (current):** RL-2026-002, adjacent-fact-synthesis vs.
  unanchored-property, live.
- **Phase 1.5 (new, this audit's own recommendation):** before or
  alongside Phase 2, design a SEPARATE calibration round testing Shape
  E specifically (single-fact causal/mechanistic elaboration with
  partial anchor) — it is the largest attributable category found here
  and remains completely uncalibrated by either existing round.
- **Phase 2:** targeted B2 calibration experiment, only if human
  evidence justifies it — scoped to whichever shape(s) the evidence
  actually supports revisiting, which per this audit likely needs to
  include Shape E, not just Shape B.
- **Phase 3:** integrated B2→Stage-C probe, re-run only after any Phase
  2 revision, checking specifically whether natural safe admissions
  now occur AND whether the anti-overcorrection set (above) still
  correctly blocks.
- **Phase 4:** blind/held-out evaluation with frozen architecture.
- **Phase 5:** production-candidate freeze/promotion decision.
- **Fine-tuning:** optional future optimization, not required for
  completion.

### EXIT CRITERIA (qualitative/structural, no invented percentages)

- **Done tuning B2:** once human calibration evidence exists for every
  shape currently driving zero-safe (Shape A confirmed-strict via the
  anti-overcorrection set holding; Shape B resolved via RL-2026-002;
  Shape E separately tested) AND a revised B2, re-run on a fresh
  integrated probe, produces some natural safe admissions without
  clearing the anti-overcorrection set.
- **Stage C sufficiently exercised:** once at least one real admitted
  candidate has gone through Stage C end-to-end with a sane comparator
  result — today, literally zero ever have.
- **Held-out evaluation may begin:** only after the architecture is
  frozen (no further semantic edits planned) and shows stable,
  plausible safe-admission behavior across at least two independent
  probes, not just one.
- **All semantic changes must stop:** the moment held-out evaluation
  begins — per this project's own standing `dataset_purpose`
  discipline, held-out material is never iterated against.

**No D0/C0/R1/R2/repair-v1/admission-gate edit. No Stage C run. No
v2.1. No fine-tuning. No held-out data consumed. RL-2026-002 not
inspected, not touched.**

## B2 SHAPE-E TARGETED HUMAN-CALIBRATION ROUND DESIGN (RL-2026-003
## DRAFT, 2026-08-13, same session) — ZERO MODEL CALLS, FROZEN LOCALLY,
## NOT PUBLISHED, NOT INGESTED

### Shape E, defined precisely against A and B

**Shape A (clear unanchored):** claimed property/mechanism/motive has
no source anchor at all. **Shape B (RL-2026-002's own hypothesis):**
source states TWO facts, adjacently/same-passage; candidate connects
them. **Shape E (this round):** source states ONE fact; candidate
supplies an explanatory mechanism/causal/motivational account of that
single fact the source never states. There is a real anchor (unlike
A) and only one fact, never two being connected (unlike B) — a
genuinely distinct middle category the zero-safe audit found dominant
and untested.

### Eligibility audit

Searched beyond the three items already flagged (H02/H13/H18) for
diversity, per instruction not to just take multiple claims from one
item. Found `07_ai_cheating_exam/M` (cj2-reference-probe-1, the
original FIRST REFERENCE PROBE corpus) carries several clean, single/
double-tag Shape-E claims (c12/c13/c16/c17 — same shape: one anchored
fact, "some students dropped or didn't sit the final," elaborated with
an invented causal/motivational mechanism) — a fourth, topically
distinct, unusually accessible source (university AI-cheating episode)
not yet used anywhere.

**Final 5, each from a different item, avoiding clustering:**
1. `07_ai_cheating_exam/M` c13 (Shape E — education/AI, highly
   accessible)
2. H13/c11 (Shape E — Afghanistan/human-rights, accessible)
3. H02/c17 (Shape E — SNSF/science-policy, moderately accessible)
4. H03/c14 (Shape A contrast — NSFC/science-policy; a FRESH claim,
   deliberately not one of the 4 already-identified must-stay-strict
   regression cases, which stay reserved and untouched)
5. H18/c2 (control, genuinely `supported` — phosphine chemistry; the
   one more technically demanding item in the round, within the ~1-2
   guidance)

Zero overlap with RL-2026-001 or RL-2026-002's `candidate_claim_id`s,
verified programmatically. Neither reviewer excluded — all 5 are fresh
content.

### Proposed round & analysis preregistration

`calibration/candidates/RL-2026-003-candidates.json`,
`calibration/research-context/RL-2026-003.json` (shape definitions +
`machine_role`/`machine_support`/`machine_effective_state` stored
separately, matching RL-2026-002's own fix), `reader-lab/rounds/drafts/
RL-2026-003.json` (reviewer-facing, all internal fields excluded),
`calibration/candidates/RL-2026-003-preregistration.json` (exact
hypothesis, per-item analysis plan, no arbitrary threshold, explicit
interpretation guide for unsupported / interpretive-or-established /
mixed outcomes).

### Structural backlog (recorded, not acted on)

**Modality hardening (Shape C):** H01/H07 suggest this is another
independent calibration family that may need its own targeted round if
it remains material after Shape-E calibration — not bundled into this
round, one hypothesis at a time. **D0 span-resolution failures
(H06/H15):** a structural/execution failure, not a human support-
calibration question — recommend a separate future structural audit,
not a Reader Lab round.

### Automation status — chose NOT to ingest, even though likely safe

Confirmed directly from `reader-lab-worker/src/calibrationOrchestrator.js`:
`reconcileStuckCalibrationRuns` only resumes runs with
`status='needs_eligible_candidates'` — RL-2026-002 is not in that
state, so ingesting these 5 candidates now would very likely not
disturb it. **Chose not to rely on that residual inference this pass**
— kept everything frozen locally instead, per the task's own explicit
conservative fallback, since there is no cost to waiting for
RL-2026-002's own completion as the unambiguous safe checkpoint.
Nothing inserted into `calibration_candidates`. Nothing published.
RL-2026-002's in-progress responses were not inspected.

**No B2 edit. No Stage C run. No v2.1. No fine-tuning.**

## B2 D0 SPAN-RESOLUTION FAILURE AUDIT (2026-08-13, same session, zero
## model calls — reproduced offline from frozen artifacts only)

**Both H06/c4 and H15/c13 reproduce deterministically, offline**, by
running `normalize_parse` (recovers the markdown-fence-wrapped raw D0
JSON) then `resolve_anchor`/`validate_span_resolution` directly against
the frozen `candidate_fields` text — no model call, confirming these
are real, not a provenance/copy artifact.

### H06/c4 — Category A (model contract violation)

Claimed `exact_surface_span`: `"The plus/minus gradations as
'splitting hairs that might not have existed.'"` Actual field text
contains "...added plus/minus gradations to force a ranking. cj1:a1
names this 'splitting hairs that might not have existed.'..." — the
claimed span does not exist as a contiguous substring anywhere. D0
invented a new connective ("as," never present) stitching a paraphrase
("The plus/minus gradations") to a real quoted fragment from a LATER,
non-adjacent sentence. **Confirmed not a fluke: the SAME D0 response's
own claim c3 correctly quotes the identical real phrase, verbatim,
including its trailing period, as `exact_match`** — proving the model
had the correct literal text available and chose, for c4 specifically,
to construct an analytical sentence instead of quoting it.

### H15/c13 — Category B (resolver too brittle)

Claimed span: `"'elements outside of the transition metal block'"`.
Actual field text: `...classificatory move being challenged: 'elements
outside of the transition metal block.'` — character-level diff is
exactly one trailing period, dropped from immediately before the
closing quote mark (confirmed via codepoint inspection: both use plain
ASCII `'`, ruling out a quote-type issue). **Confirmed not isolated
within its own item: the SAME D0 response's own claim c12 quotes the
identical phrase correctly, WITH the trailing period, as `exact_match`
— and appending that missing period to c13's span before the closing
quote produces a match.** The model can and does produce the byte-exact
version of this exact excerpt elsewhere in the same response; c13 is a
one-character omission, not a fabrication.

### Prior-corpus near-miss search

Scanned every quote-ending `exact_surface_span` across this run (21
found) and the 10-item execution-envelope-recovery corpus (0 found) for
the same "appending one trailing period before the closing quote
produces a match" shape. **Exactly 1 additional near-miss confirmed —
H15/c13 itself — and it is a same-response sibling of an already-
correct claim (c12), not a separate independent occurrence.** No
Category-A near-misses were found among successfully-resolved spans
(none exist to compare against in this run, since these were the only
two `no_match` results in the whole 14-item corpus); a full stylistic
audit of "does D0 often build paraphrase+quote hybrid sentences" would
need more reading than this pass did — flagged as an open question for
the future regression suite's design, not resolved here.

### H06/H15 impact — was the structural failure the sole blocker?

Computed directly: excluding just the one failing claim from each
item's recovered D0 output, `validate_segment_id_consistency` passes
and `compute_coverage` reports `coverage_complete: true` with **zero**
uncovered segments for both H06 and H15. **The span-resolution failure
was the sole reason C0/R1/R2/Stage C never ran for either item** — not
a symptom of broader structural breakdown, confirmed computationally,
not inferred.

### Safe-admission metrics distinction (recorded, not recomputed)

2/14 candidates in the latest integrated probe were blocked
structurally (D0), before any factuality judgment — distinct from the
other 12's semantic `unsafe` rejection. The historical 0/14 result is
unchanged; this distinction (structural vs. semantic rejection) matters
for how future probes report their own denominators, not for revising
this one.

### DECISION

**C — MIXED / MULTIPLE FAILURE CLASSES.** H06 is a genuine model
contract violation (Category A) — no resolver fix could safely rescue
cross-sentence paraphrase-and-concatenation without fuzzy matching,
which remains explicitly out of bounds. H15 is resolver brittleness on
a real, present excerpt (Category B) — a narrow, deterministic,
provenance-preserving fix is plausible and empirically justified by
the same-response sibling evidence.

### Future fix, specified only — NOT implemented this pass

Extend `resolve_anchor`'s existing quote-fold tolerance (currently:
try exact match; on failure, fold the 4 smart-quote codepoints and
accept only a UNIQUE resulting match) with one more narrow, ordered
fallback: **if the excerpt ends in a closing quote character, also try
inserting a single sentence-terminal punctuation mark (period first,
matching the only empirical evidence found) immediately before that
closing quote, and accept only if this produces exactly one location**
— same discipline as the existing tolerance, never fuzzy, always
recovering and persisting the ORIGINAL source substring (with its real
punctuation), never the model's version. Any ambiguous result under
this rule stays unrescued, exactly like today's quote-fold tolerance.

**Required regression suite before any implementation:**
- H15 (must now resolve, recovering the original punctuated text)
- H15's own sibling c12 (must continue resolving correctly — non-
  regression)
- H06 (must continue to FAIL — this fix must never rescue cross-
  sentence paraphrase/concatenation)
- every currently-passing span across every completed D0 corpus (full
  non-regression sweep, not just this one run)
- repeated-substring cases (confirm the new tolerance doesn't turn a
  currently-unique match into a newly-ambiguous one)
- synthetic Unicode/punctuation edge cases: comma-before-quote,
  question-mark-before-quote, em-dash-before-quote, ellipsis-before-
  quote — none of which have empirical evidence yet and must not be
  assumed safe without their own test
- synthetic must-fail paraphrase/hallucination cases modeled on H06's
  exact shape, to confirm the fix's boundary stays narrow

**No D0/C0/R1/R2/repair-v1/admission-gate edit made. No implementation
this pass. RL-2026-002 not inspected. RL-2026-003 not ingested, not
published.**

## B2 ANCHOR RESOLVER TERMINAL-PUNCTUATION RECOVERY — IMPLEMENTED,
## VERIFIED (2026-08-13, same session, zero model calls)

**Implemented exactly the H15-shaped fallback, nothing broader.**
`cj1_v3_anchor_resolver.py` bumped to `RESOLVER_VERSION = "v2"`
(hash `d8f761e5...` → `724f5109...`). New step 3, reached only when
steps 1 (exact) and 2 (quote-fold) both find zero matches, and only
when the excerpt's own last character is closing-quote-shaped: try
inserting exactly one of `.`/`?`/`!` immediately before that character,
against both the raw and quote-folded source, accept only on exactly
one resulting location (`terminal_punct_recovered`), always recovering
the ORIGINAL source substring — never the model's version. Ambiguous
(2+ locations) still fails closed, identically to the existing
quote-fold step's own discipline. Commas/semicolons/colons deliberately
excluded — no corpus evidence justifies them.

**Consumer update, narrowly scoped:** `cj2_b2_d0_prototype.py`'s three
call sites that gate D0 structural validity (`_resolve_span_offset`,
`validate_span_resolution`'s two loops) now accept
`terminal_punct_recovered` alongside the existing two statuses, via one
new shared `_RESOLVED_SPAN_STATUSES` constant (hash `34f52ed9...` →
`5810c80b...`). **Deliberately NOT touched, staying inside this pass's
own boundary:** `cj2_b2_v2_probe.py`'s and `cj2_b2_probe_v1_4_1.py`'s
`validate_auditor_evidence` diagnostics both hardcode
`diag["status"] == "normalized_unique_match"` — R1/R2 files, explicitly
off-limits this pass. A future R2-scoped pass could extend that check
the same way; not done here, flagged as a known follow-up.

### H15 — before / after / gate replay

Before: `no_match`. After: `terminal_punct_recovered`, recovering
`"'elements outside of the transition metal block.'"` — the exact
original source substring, period included. Full deterministic gate
replay (schema → span-resolution → `compute_d0_effective_status` →
`compute_pipeline_gate`, C0 given a placeholder input, never actually
called): `span_resolution valid: True` (0 violations, was 1),
`compute_d0_effective_status: "valid"` (was `span_resolution_failed`),
**`should_call_r1: true`** — D0 no longer blocks this item. Zero model
calls; C0 was not invoked.

### H06 — confirmed still fails

`no_match`, unchanged. The new fallback only inserts one punctuation
character at the exact final position before a closing quote — it
never touches interior text, never invents connectives, never
concatenates non-adjacent fragments. H06's fabricated span differs from
any real source text by far more than that, so it was never a
candidate for step 3 to even consider seriously (confirmed empirically,
not just by argument).

### Regression: full offline corpus sweep

Reconstructed the exact pre-change algorithm inline (steps 1/2/4/5
only) and diffed it against the live, updated `resolve_anchor` across
**every completed D0 corpus found in the repo** — first-probe (8),
execution-envelope-recovery (10), real-material-transfer-probe attempt-1
(10, 4 of which could not be parsed at all — a pre-existing, already-
documented data issue from that superseded early attempt, unrelated to
this change), integrated-pipeline-probe (10), and the stage-c-first-
integrated-development-probe (14). **48 D0 output files, 1,123 individual
claim/non_propositional spans checked. Exactly 1 changed — H15/c13,
exactly as intended. Zero other differences anywhere**, confirming no
existing successful resolution, ambiguous result, or out-of-scope
classification shifted.

### Safety — must-fail suite

New `cj1_v3_anchor_resolver_static_tests.py` (25 checks, all pass):
H06 (real, frozen) and its correctly-already-resolving sibling c3; H15
(real, frozen, positive) and its sibling c12 (non-regression, exact
path, new fallback never invoked); synthetic `?`/`!` positive cases;
invented-connective, missing-word, and reordered-word must-fail cases;
a genuine two-location punctuation-ambiguity must-fail-closed case
(plus a same-location raw/folded-pass dedup check, so a real single
match is never miscounted as ambiguous); internal (non-terminal)
punctuation-gap must-fail cases; a trailing-comma must-fail case
(confirming commas are never tried); a semantic/fuzzy near-match
must-fail case; and full v1-behavior regression checks (exact_match,
normalized_unique_match, quote-fold ambiguous_match, no_match) run
against the updated module.

**All 14 project-wide static test suites touching D0/the resolver
re-run: 14/14 still ALL PASS**, including `cj2_b2_d0_static_tests.py`
and `cj2_b2_integrated_pipeline_probe_static_tests.py`, confirming zero
regressions beyond this file's own scope either.

### DECISION

**A — NARROW RESOLVER FIX VALIDATED.** H15 recovers uniquely to its
exact original source text; H06 remains correctly blocked; every one
of the 1,123 pre-existing spans across every completed corpus is
unchanged; no unexpected new acceptance occurred anywhere.

**Classification: a deterministic PROVENANCE-RESOLUTION FIX — not a D0
semantic revision, not v2.1.** No D0/C0/R1/R2/repair-v1/admission-gate
prompt or semantic logic touched. Historical results remain immutable:
the completed 14-item Stage-C probe's own recorded result (H15 =
`span_resolution_failed`, under the resolver frozen at that time)
is unchanged — this is a new resolver version for future probes, not a
retroactive rescoring. H06 recorded as a standing
**KNOWN D0 EXACT-SPAN CONTRACT VIOLATION**, kept as a permanent
must-fail regression case; no D0 prompt change proposed or made — that
would require independent recurrence evidence this pass didn't find.
RL-2026-002 not inspected. RL-2026-003 not ingested, not published, no
reviewer state touched.

## B2 ANCHOR RESOLVER V2 STATUS-PROPAGATION COMPATIBILITY PASS —
## IMPLEMENTED, VERIFIED (2026-08-13, continuation after a context-limit
## interruption; recovered and verified from disk, zero model calls)

**Closes exactly the follow-up flagged by the section above** ("A future
R2-scoped pass could extend that check the same way; not done here,
flagged as a known follow-up") — R1/R2's `validate_auditor_evidence` now
recognizes every resolver-v2 success status, not just
`normalized_unique_match`. This entry was written by a fresh session
after the implementing session hit its context limit; every claim below
was verified directly against the on-disk code and by re-running the
test suites, not recovered from the (visually garbled) prior transcript.

**Authoritative contract**, in `cj1_v3_anchor_resolver.py`:
```
RESOLVED_STATUSES = ("exact_match", "normalized_unique_match", "terminal_punct_recovered")

def is_resolved_anchor(result: dict) -> bool:
    return (
        isinstance(result, dict)
        and result.get("status") in RESOLVED_STATUSES
        and result.get("original_substring") is not None
    )
```
A span is "resolved" — safe for any consumer needing a claimed excerpt to
genuinely, uniquely, deterministically identify real source text — iff
its status is one of these three. `ambiguous_match`, `no_match`,
`out_of_scope`, `None`, a non-dict, or a status-without-substring
malformed result all correctly return `False`. Directly re-verified with
12 targeted cases (all 3 accepted statuses, all 3 rejected statuses, and
5 malformed/edge shapes) — all 12 behave exactly as specified.

**Consumer update #1 (D0, re-pointed not re-implemented):**
`cj2_b2_d0_prototype.py`'s `_RESOLVED_SPAN_STATUSES` is now `=
RESOLVED_STATUSES` (imported directly), replacing what had been an
independently-editable duplicate tuple. Both `_resolve_span_offset` and
`validate_span_resolution`'s two loops consume this single name — no
second copy of the status vocabulary exists anywhere in D0. Behaviorally
inert on its own: the tuple's contents are unchanged from what D0 already
accepted post-terminal-punct-recovery, so this is pure provenance
plumbing, not a new acceptance.

**Consumer update #2 (R1/R2, the actual new propagation):**
`cj2_b2_v2_probe.py`'s `validate_auditor_evidence` now calls
`is_resolved_anchor(diag)` instead of hardcoding
`diag["status"] == "normalized_unique_match"`. The exact-match fast path
(`excerpt in source_snapshot`) is untouched. This is the one place
behavior actually changes: an `auditor_evidence` excerpt that only
resolves via `terminal_punct_recovered` (H15's shape) is now accepted as
valid provenance, where before this pass it was rejected. No other
function in this file was touched — `validate_r1`, `validate_r2`,
`compute_consistency`, `compute_effective_v2`, repair-v1, and the
R1_R2_SEMANTIC_CONFLICT machinery are all byte-identical to before this
pass; confirmed by reading the surrounding code, not just by the diff's
own scope.

**Consumer audit, full codebase, every reference to `resolve_anchor`/the
status vocabulary:**
- **Current canonical, updated:** `cj2_b2_d0_prototype.py`,
  `cj2_b2_v2_probe.py` (above).
- **Historical/frozen, correctly left untouched** (all still hardcode
  `normalized_unique_match` alone, exactly as before): `cj2_b2_probe.py`,
  `cj2_b2_probe_v1_2.py`, `cj2_b2_probe_v1_3.py`,
  `cj2_b2_probe_v1_4_1.py`, `cj2_fresh_batch1_pipeline.py` — the last of
  these has its own `compute_effective_cj1_eligibility`, a CJ-1 (not B2)
  eligibility gate tied to a specific already-run frozen fixture
  (`cj2-fresh-batch-1/blind-stream-v2.json`); modernizing it would be a
  CJ-1 semantic change, out of this pass's scope, and it was already
  named as intentionally excluded in the resolver module's own comment
  before this pass started.
- **Diagnostic-only, no gating impact, correctly unchanged:**
  `cj1_v3_probe.py`, `cj1_v3_calibration_run.py` (resolver result stored
  as a `resolver_diagnostic` field, explicitly documented as "never used
  to overturn or rescue the strict verdict"), `cj2_reference_probe.py`
  ("diagnostic only — never rescue" per its own comment).
- **No stale hardcode found in test/other files:** `cj2_b2_d0_static_tests.py`
  mentions `normalized_unique_match` only in a comment/test name; its
  actual assertion goes through `compute_d0_effective_status`, which
  already routes through the updated `_RESOLVED_SPAN_STATUSES` — no
  independent gate to go stale. `cj2_build_canonical_seed.py`'s
  `status = "exact_match"` is a default-value assignment, not a
  membership check. `recovery_2026-08-10_reconstruct_review_signals.py`'s
  `out_of_scope` is an unrelated local variable (sidecar-age counter),
  not this module's status vocabulary.

**Syntax/import health, checked before trusting anything else** (the
prior session's transcript showed visually mangled patch fragments —
none of that was trusted; only the actual files were read): all four
changed files (`cj1_v3_anchor_resolver.py`, `cj2_b2_d0_prototype.py`,
`cj2_b2_v2_probe.py`, `cj1_v3_anchor_resolver_static_tests.py`)
byte-compile and import cleanly; no duplicated/stale assignment or
leftover old-tuple definitions found on direct reading of every touched
region.

### H15 — accepted through the new R1/R2 path (synthetic control-flow only)

Confirmed via the resolver's own static suite
(`cj1_v3_anchor_resolver_static_tests.py`, now 40 checks total, up from
25): a synthetic control-flow fixture using H15's real source/span shape
shows `validate_auditor_evidence` now ACCEPTS it via
`terminal_punct_recovered`, where it would have been rejected before this
pass. Labeled explicitly in the test output as "not semantic evidence" —
H15 never actually reached R1/R2 in the original probe, so this
demonstrates the machinery's compatibility, not a real H15 R1/R2 result.

### H06 — confirmed still rejected

Same suite: the synthetic control-flow fixture using H06's fabricated
span still shows `validate_auditor_evidence` REJECTING it, unchanged by
this pass. H06 remains the standing KNOWN D0 EXACT-SPAN CONTRACT
VIOLATION.

### Regression

All 14 project-wide static suites touching D0/the resolver re-run
directly this session: **14/14 ALL PASS**
(`cj1_v3_anchor_resolver_static_tests.py`, `cj2_b2_c0_static_tests.py`,
`cj2_b2_d0_static_tests.py`,
`cj2_b2_d0c0_execution_envelope_recovery_static_tests.py`,
`cj2_b2_d0c0_first_probe_static_tests.py`,
`cj2_b2_d0c0_natural_c0_recovery_static_tests.py`,
`cj2_b2_d0c0_output_normalizer_static_tests.py`,
`cj2_b2_d0c0_real_material_transfer_probe_static_tests.py`,
`cj2_b2_integrated_pipeline_probe_static_tests.py`,
`cj2_b2_r1r2_partial_structured_output_probe_static_tests.py`,
`cj2_b2_r2_contract_repair_probe_static_tests.py`,
`cj2_b2_r2_integrated_repair_recheck_static_tests.py`,
`cj2_b2_stage_c_admission_gate_static_tests.py`,
`cj2_b2_v2_static_tests.py`). The resolver's own suite specifically
covers: all 3 accepted statuses, all 3 rejected statuses, a malformed
(non-dict) result, a resolved-status-with-no-substring defensive case,
the H15/H06 synthetic control-flow fixtures above, a fuzzy/semantic
near-match must-fail case, and a direct assertion that D0's
`_RESOLVED_SPAN_STATUSES` derives from the resolver's own
`RESOLVED_STATUSES` rather than an independently-editable copy.

**No unintended behavioral delta:** this pass added zero new accepted
statuses to the contract (still exactly the same 3 as the prior,
already-documented terminal-punctuation-recovery pass) — D0's own
acceptance surface is unchanged, since it already accepted all 3
statuses before this pass, just via a duplicated tuple instead of an
import. The only real behavior change anywhere is R1/R2's
`validate_auditor_evidence` newly accepting `terminal_punct_recovered`,
which is the intended propagation this pass exists to make, not a
side effect.

### Apparatus record

```
RESOLVER_VERSION = "v2"  (unchanged by this pass — no new resolver algorithm)
cj1_v3_anchor_resolver.py               sha256 e194a20fcc0fd11fe482fea0498947c9a62c8fc4d96d2a7a3bf70161a6fb25a3
cj2_b2_d0_prototype.py                  sha256 44d8fbeab40a2f826940c1912917a48aea1bc472efc40aaa282efa142c64bef6
cj2_b2_v2_probe.py                      sha256 feb6fa118005e865e76cbaa3a02aebba67bf23ff70c6c531d93d69fbf8bffe93
cj1_v3_anchor_resolver_static_tests.py  sha256 2011a2b71356d6b80f1b3e3e49468a5391f53bc66284d2dfb784763ccf7e114b
```

### DECISION

**A — RESOLVER V2 PROPAGATION COMPLETE, APPARATUS READY FOR FUTURE
INTEGRATED RUNS.** The canonical success contract is clean and
fail-closed; D0 consumes it from a single source of truth; R1/R2's
provenance validator now consumes it too, extending exactly the
follow-up flagged by the terminal-punctuation-recovery pass above; H15
is accepted through the compatibility path (synthetic control-flow
only, not a semantic H15 R1/R2 result); H06 remains correctly rejected;
no stale current consumer remains; all 14 regression suites pass; no
D0/C0/R1/R2/repair-v1/admission-gate semantic logic was touched; no
unintended new acceptance was found anywhere. **Classification:
DETERMINISTIC PROVENANCE APPARATUS UPDATE — not a D0/R1/R2 semantic
revision, not B2 v2.1.** No Stage C run, no RL-2026-002/003 inspection
or change, no reviewer state touched this pass.

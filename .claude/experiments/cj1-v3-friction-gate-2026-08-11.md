# CJ-1 v3 Friction Gate — Design Freeze (2026-08-11)

Design-only record. No production code changed by this document. See
`.claude/current-work.md` `## CJ-1/CJ-2 RESEARCH CHECKPOINT` for the
narrative history (v2 audit, positive-control corrections, fetch-coverage
sample) that led here — not duplicated below.

## Status

**FROZEN as design candidate.** Approved for implementation/testing
(validator + v2/v3 comparison probe) in this same experiment. NOT wired
into production. Does NOT replace `_CATEGORY_JUMP_SYSTEM_PROMPT` (v2,
`news_fetcher.py:734`), does NOT touch `disability_angle` eligibility
gating, persona routing, or CJ-2 (CJ-2 not started).

## Why v2 was replaced (one line, full detail in current-work.md)

v2 required hidden_mechanism + category_jump + correction +
evidentiary_bridge BEFORE a source could pass — 0/20 real production
seeds under `judge_prompt_version='v2-evidentiary-bridge'` ever passed.
That's CJ-1 doing CJ-2's job. v3 narrows CJ-1 to: is there at least one
concrete, exactly-anchored fact or relation in the source that creates
friction — nothing about what it means.

## Frozen v3 system prompt

```
You are the CRIPMINDS SOURCE FRICTION GATE.

You receive a fetched SOURCE SNAPSHOT of one article -- the text
actually retrieved, which may be the complete article or a
size-capped excerpt of it. You do not know which.

Your ONLY job: does this snapshot contain at least one concrete,
exactly anchored fact, or relation between facts, that creates
interpretive friction -- something worth handing to several
independent readers for interpretation.

You do NOT decide:
- what the friction means
- what mechanism it might reveal
- what category the story "really" belongs to
- what correction a writer could make
- which persona should look at it

All of those are downstream judgments made later, by readers who bring
four distinct perceptual engines and permission to interpret -- not
necessarily more material than you have. Your output is raw material
for that stage, not a conclusion.

WHAT COUNTS AS FRICTION

At least one concrete fact, or relation between facts, about how the
object/system/process behaves, changes, conflicts, depends, measures,
transforms, or produces an unexpected outcome -- grounded in something
actually stated in the snapshot, not inferred by you. This can be a
single self-contained fact (an unexpected behavior needs no opposing
fact to pair against) or a relation between two.

Do not use subject matter, social importance, affected population, or
presumed relevance to the publication as evidence for or against PASS.
A person merely being affected, harmed, helped, excluded, or
represented is NOT, by itself, friction -- that describes an impact,
not a fact about how something behaves.

Relation/fact shapes that qualify (topic-neutral -- these are shapes,
not examples with a destination):
- two stated facts contradict each other
- two measurements or accounts of the same thing disagree
- a component described as necessary is absent, yet the process still
  works
- a stated goal and an observed/reported outcome diverge
- the same thing is described differently across stages, scales, or
  contexts
- a single behavior the snapshot itself identifies as surprising,
  anomalous, unprecedented, or contrary to a stated
  expectation/baseline

The snapshot is allowed to already offer its own explanation for the
fact or relation. An explanation being present does not disqualify the
friction -- whether that explanation actually resolves it is not your
question to answer.

WHAT TO DO

1. OSTENSIBLE CATEGORY
   What does the snapshot appear to be about, before any
   interpretation?

2. GROUNDED FRICTION
   Find at least one fact, or relation between facts, in the snapshot
   that creates friction. It must be traceable to specific text you
   can quote verbatim -- not a summary of the snapshot's overall
   subject, not something you infer beyond what is written.

3. SOURCE ANCHORS
   Copy 1-3 EXACT substrings from the snapshot that ground the
   friction -- character-for-character, not paraphrased, not
   corrected for grammar or punctuation. These will be checked by
   exact substring match against the snapshot. An anchor that is not
   a verbatim copy fails that check.

4. OPEN QUESTION
   State one unanswered question about the anchored fact or relation.
   Do NOT propose an answer, mechanism, or interpretation -- a
   question that already contains its own answer is not acceptable
   here.

   Acceptable: "Why does X change if the source says X isn't
   required?"
   NOT acceptable: "Does this show that X is really about Y?"

   A weak or missing open_question never downgrades an otherwise
   grounded PASS -- it is handoff metadata, not part of the gate.

DECISION RULE

PASS when the snapshot contains at least one grounded fact or
relation, anchored in exact quotable text, that creates friction --
regardless of what it might mean, whether the snapshot explains it, or
what subject it concerns.

NO only when no grounded friction can be identified in the supplied
snapshot, or every candidate friction requires a fact not actually
present in it.

When genuinely uncertain between PASS and NO, PASS. A false PASS costs
one wasted downstream comparison. A false NO may permanently exclude
this source from ever being looked at again.

OUTPUT INVARIANTS

If decision is "PASS":
- resisting_detail must be non-null
- source_anchors must contain 1 to 3 exact excerpts
- friction_type must be non-null
- open_question may be null

If decision is "NO":
- resisting_detail must be null
- source_anchors must be an empty list
- friction_type must be null
- open_question must be null

reason is always required, in both cases.

Return only this JSON:

{
"decision": "PASS" | "NO",
"ostensible_category": "What the snapshot appears to be about",
"resisting_detail": "Plain-language summary of the anchored fact or relation, or null if NO",
"source_anchors": [
  {"excerpt": "exact verbatim substring from the snapshot"}
],
"friction_type": "contradiction" | "asymmetry" | "mismatch" | "dependency" | "reversal" | "transformation" | "measurement_discrepancy" | "unexpected_behavior" | "other" | null,
"open_question": "One unanswered question about the anchored fact or relation, or null",
"reason": "Maximum 2 sentences explaining PASS/NO"
}
```

## Design decisions baked into this text (for future editors — do not reopen without a stated reason)

- **Full-source-only, snapshot-honest.** Opening deliberately says
  "SOURCE SNAPSHOT... may be the complete article or a size-capped
  excerpt... You do not know which" — NOT "full text." Production caps
  at `_SOURCE_TEXT_MAX_CHARS = 3000` (`generate.py:37`); Dogs and
  Conducting both arrived `source_truncated=True` at exactly that cap
  during the earlier resolution probe, with Conducting the strongest
  near-positive case found so far. Calling a 3000-char excerpt "full
  text" would have re-created the exact resolution problem this
  redesign exists to fix, just moved from RSS-summary to larger
  excerpt.
- **Fact OR relation, not just relation.** A single self-contained
  unexpected behavior is valid friction; it doesn't need to be forced
  into an artificial two-fact pair.
- **Source-relative, not world-knowledge, for the single-behavior
  shape.** "surprising ... or contrary to a stated
  expectation/baseline" — the expectation must come from the snapshot
  itself, not from the model's general knowledge of how the thing
  "normally" behaves. Prevents CJ-1 manufacturing friction that isn't
  actually in the source.
- **NO is defined by absence of grounded friction, not by internal
  consistency.** Earlier draft's "the snapshot is internally
  consistent, its facts sit together without tension" was narrower
  than the PASS definition and biased toward requiring
  contradiction/tension specifically. Final text: "no grounded
  friction can be identified... or every candidate friction requires a
  fact not actually present."
- **Zero disability/accessibility vocabulary**, not even as a
  disqualifier. v2's own worked examples (not just its rules) were the
  likely source of "no disability-relevant friction" leaking into live
  NO verdicts even though v2's rule already disclaimed topic-relevance.
  Replaced with a fully topic-neutral guard: "Do not use subject
  matter, social importance, affected population, or presumed
  relevance to the publication as evidence for or against PASS."
- **No worked examples with an implied destination.** v2's
  splint→furniture-style examples (and an even earlier v3 draft's
  "body restraint → structural elegance" disguise, still
  disability-adjacent via "body"/"limitation") are both gone. Only
  topic-neutral relation *shapes*, no resolution implied.
- **`open_question` structurally can't smuggle an answer** — it's
  typed as a question, with an explicit acceptable/not-acceptable pair
  showing the difference. A weak/missing one never gates a PASS; it's
  handoff metadata for CJ-2, not part of the gate.
- **Explicit output invariants**, so the deterministic validator (see
  below) has something unambiguous to check rather than improvising
  rules from the free-text schema description alone.
- **Recall bias stated directly**: "When genuinely uncertain... PASS."
  Asymmetric cost is stated in-prompt: false PASS wastes one downstream
  comparison; false NO can permanently exclude a source.
- **Downstream framed as different tools, not more material.** CJ-2
  may see the exact same source text CJ-1 saw — what it adds is four
  perceptual engines and permission to interpret, not privileged
  access to more source.

## Source-authority note (NOT part of the model prompt — orchestrator-side, unresolved, not implemented)

This governs how a future orchestrator would use CJ-1's `decision`, not
anything the model itself needs to know or decide.

- **CJ-1 PASS is authoritative once anchors validate, regardless of
  source completeness.** The required friction is already grounded in
  retrieved text; a truncated snapshot cannot invalidate a fact that
  was actually read.
- **CJ-1 NO is authoritative only when source completeness is
  positively established.** A NO on a possibly-truncated snapshot
  means "no friction found in what we saw," not "no friction exists in
  the source."
- **`source_truncated=False` does NOT prove completeness.**
  Confirmed in code (`grounding.py:182`, `build_evidence_packet`'s own
  docstring): callers that don't know/pass `source_max_chars` get
  `source_truncated=False`, meaning "not verified as truncated," not
  "verified as complete." There is currently no field that positively
  proves a snapshot is the whole article.
- **Therefore do not implement `if not source_truncated: NO is
  authoritative`** — that would manufacture a false certainty the
  codebase doesn't actually have.
- **Eventual policy (not built yet):**
  - fetch failed → `NO_SOURCE` (outside model, deterministic)
  - CJ-1 PASS → authoritative PASS
  - CJ-1 NO + completeness positively established → authoritative NO
  - CJ-1 NO + truncated or completeness unknown → `INCONCLUSIVE_SOURCE`
    (not a final rejection; expand/refetch/backlog per later policy)
  - This will likely require a real `source_completeness: complete |
    truncated | unknown` field (or conservative equivalent) — not
    `source_truncated`, which only ever proves the negative case
    (definitely truncated), never the positive one (definitely
    complete). Not building this now; flagged so this document doesn't
    overstate what the existing boolean proves.
- **Not solved in this experiment.** For the v2/v3 probe below, any
  model NO is recorded and reported as `model_NO /
  final-authority-unknown`, never treated as a settled rejection. A
  validated PASS is usable regardless of completeness status.

## Next steps in this experiment (tracked separately, not duplicated here)

1. Deterministic v3 syntax/provenance validator (exact-anchor
   substring check, output invariants above; does not judge semantic
   quality). DONE — `automation/cj1_v3_validator.py`.
2. v2/v3 paired comparison harness on identical fetched source bytes —
   Conducting, Dogs, Roman shipwreck, one genuinely thin fetched
   control, stop at 4 fixtures. DONE — `automation/cj1_v3_probe.py`
   + `automation/cj1_v3_fetch_fixtures.py`.
3. Manual behavioral inspection (not NLP/regex theater) — invented
   anchors, hidden-mechanism/category-jump leakage, disability/topic
   leakage, rejection due to source's own explanation, PASS-on-trivial.
   DONE — see `## ROUND 1 RESULTS` below.
4. Stop and report. Do not modify v3, replace production CJ-1, change
   source fetching, or design CJ-2 until this one paired read is
   reviewed. DONE — reported 2026-08-11, no prompt edits/production
   wiring/CJ-2 made.

## ROUND 1 RESULTS (2026-08-11) — first paired v2/v3 probe

**Method:** 4 fixtures fetched ONCE each via the real production
`get_source_text`/`get_source_origin` path (`ProductionOrchestrator`,
`DiscoveryMixin`), frozen to
`automation/.probe_fixtures/cj1-v3/*.json` with `source_snapshot`,
`source_origin`, length, a heuristic-cap flag (stored as
`source_truncated` in the fixture — see caveat below), and a SHA-256 of
the snapshot. Both v2 (`_CATEGORY_JUMP_SYSTEM_PROMPT`, imported live
from `news_fetcher.py` so this always compares against whatever is
actually in production) and v3 (frozen prompt above) were called
against the byte-identical frozen snapshot, through the same shared
helper (`LLMMixin._call_openai_compat_api`), same model
(`openrouter/claude-sonnet-4.6`), same `max_tokens=1200`, same explicit
`temperature=0.9` — the only independent variable was the system
prompt/output schema. Executed in an isolated `/tmp` scratch checkout
on trident (CLIProxy is host-local; this Mac has no route to it and no
copy of `CLIPROXY_KEY` was made) — no production DB, no production
workspace, no re-fetching. Raw + parsed model output and validator
results for all 4 pairs are preserved at
`automation/.probe_fixtures/cj1-v3/results/*_result.json`.

**Terminology caveat:** `source_truncated` in these fixtures is the
same `length >= 3000` heuristic already used elsewhere in the
codebase — it proves "likely cut off," never "verified complete" (see
source-authority note above). Treat it as `snapshot_hit_3000_char_cap`
in spirit; it is not a completeness claim.

| fixture | v2 decision | v3 decision | v3 validator |
|---|---|---|---|
| conducting (3000 chars, cap-hit) | NO | PASS | invalid (1 anchor) |
| dogs_fear_sadness (2566 chars) | NO | PASS | invalid (1 anchor) |
| roman_shipwreck (1512 chars) | NO | NO | valid |
| thin_negative_promo_codes (3000 chars, cap-hit) | NO | PASS | invalid (1 anchor) |

**Failure-class taxonomy for the 3 validator-invalid PASSes — recorded
precisely, per explicit review instruction not to let semantic
correspondence "rescue" a strict-contract failure:**

The frozen v3 contract requires character-for-character exact
substrings. Under that contract, all 3 anchors below are, correctly,
`FAIL` — semantic correspondence to the real source is not the test.
But `FAIL` is not one failure class; distinguishing them matters for
deciding, later and separately, whether production validation should
add a constrained canonicalization step:

| fixture | anchor | semantic source correspondence | strict exact-substring validation | failure class |
|---|---|---|---|---|
| conducting | anchor[1] | YES — 175 chars, differs at exactly 2 positions | FAIL | `COPY_FIDELITY_FAILURE` |
| dogs_fear_sadness | anchor[0] | YES — differs at exactly 2 positions | FAIL | `COPY_FIDELITY_FAILURE` |
| thin_negative_promo_codes | anchor[0] | YES — verbatim, but from the TITLE field, not `source_snapshot` | FAIL | `OUT_OF_SCOPE_ANCHOR` |

- **`COPY_FIDELITY_FAILURE`** (conducting anchor[1], dogs anchor[0]):
  the model reproduced the source passage correctly in every respect
  except emitting ASCII straight apostrophes (U+0027) where the source
  has right single quotation marks (U+2019). Direct character diff on
  conducting anchor[1]: claimed text vs. real text differ at exactly 2
  positions, both `'`(U+0027)→`'`(U+2019), nothing else. Same result
  on dogs anchor[0] ("didn't" vs "didn't"). This is NOT
  `UNSUPPORTED_ANCHOR` — nothing was invented; the model located and
  paraphrased-at-the-character-level a real passage. Scored `invalid`
  under the frozen v3 contract as specified, with no exception made
  for the semantic match.
- **`OUT_OF_SCOPE_ANCHOR`** (thin_negative anchor[0]): the quoted text
  ("Design Within Reach Promo Codes: 30% Off | June 2026") is
  real and verbatim, but it is the article TITLE, which this harness
  supplied as separate `TITLE:` context, not inside `source_snapshot`.
  The validator, correctly per its own contract, only checks anchors
  against `source_snapshot` — so this is a distinct failure class from
  copy fidelity: the text exists, just not in the field the anchor is
  supposed to be scoped to. Not a v3 prompt defect (the v3 prompt never
  mentions a title field at all) — a harness/validator scope question
  for later: should an anchor be allowed to cite the title at all?
  The other 2 anchors in that same PASS matched `source_snapshot`
  exactly (`exact_match`, no ambiguity).
- **No `UNSUPPORTED_ANCHOR` occurred anywhere in this round** — every
  anchor across all 4 fixtures corresponds to real text the model was
  actually shown, verified by direct diff, not just eyeballing.
- **Not implemented, not decided yet, deliberately** (per explicit
  instruction not to normalize mid-experiment and bias the result):
  a future production resolver could canonicalize a tight whitelist
  (U+2018/U+2019 ↔ ASCII apostrophe, U+201C/U+201D ↔ ASCII quote,
  possibly NFKC) ONLY for locating a unique match, then persist the
  ORIGINAL exact source substring at that location — never the
  model's normalized text — distinguishing `exact_match` /
  `normalized_unique_match` / `no_match` / `ambiguous_match` rather
  than treating all matches as equivalent. Deferred; no code changed
  this round.
- **Did v3 smuggle a hidden mechanism? NO.** No v3 output proposes
  what the friction means — `resisting_detail`/`reason` stop at "these
  two things don't sit together." Contrast: v2's own conducting
  output still filled `hidden_mechanism`/`category_jump`
  ("illegible authority... reproduces hierarchical control") even
  while deciding NO — v2 structurally can't help generating that
  content because its schema demands it; v3's schema has no such
  field to fill.
- **Did v3 produce a category jump? NO** — no such field exists in
  its schema; none of its `reason` fields state a destination category.
- **Did disability/topic relevance leak back in? NO** in any v3
  output. Notably v2's roman_shipwreck rejection reasons partly in
  house-editorial terms ("no evidentiary bridge... relevant to any
  CripMinds angle") — v3's equivalent NO stays fully general
  ("no fact or relation... creates interpretive friction under any of
  the qualifying shapes").
- **Did it reject because the source had its own explanation? This
  was the key test, on dogs_fear_sadness, and it worked as designed.**
  v2 explicitly rejects BECAUSE the source explains itself: "the
  summary itself already states this interpretation explicitly...
  the thesis is not hidden — it is declared by the source." v3, given
  the identical snapshot, PASSes on a different, still-real friction
  (fear is neurally distinguishable from both anger and sadness, but
  anger and sadness are not distinguishable from each other) without
  being blocked by the source explaining fear's salience elsewhere in
  the same text. This is the single clearest confirmation that the
  v2->v3 redesign fixes the exact failure mode it was built to fix.
- **Did it PASS trivial material too easily? Open calibration
  question, not resolved here.** thin_negative's PASS is on a real,
  verifiable fact (title says "June 2026," body says an "August 10"
  sale deadline — 2 of 3 anchors matched exactly) — not manufactured.
  But it's also exactly the kind of boring publishing-mechanics
  staleness an evergreen affiliate/coupon post accumulates, arguably
  not "friction worth handing to four minds." The recall-biased design
  means CJ-1 is supposed to pass this rather than gatekeep it — CJ-2
  (or a future specificity tiebreaker) is where "real but uninteresting"
  gets filtered, not CJ-1. Flagged for whoever designs CJ-2, not acted
  on now.

**Per-fixture answers, as explicitly requested:**

- **Conducting** — v2: NO (generated `hidden_mechanism`/`category_jump`
  text anyway, rejected only for a null `evidentiary_bridge`). v3:
  PASS. Validator: FAIL, and **only** for punctuation —
  `COPY_FIDELITY_FAILURE` on anchor[1] (2 characters, both
  straight-vs-curly apostrophe); anchors[0] and [2] matched exactly.
  Did v3 stay interpretation-free: YES — `resisting_detail`/`reason`
  describe a stated-but-unresolved tension ("equally inaccurate,"
  cut off), propose no mechanism, no destination category.
- **Dogs** — v2: NO, explicitly because the source explains itself.
  v3: PASS, on a different real fact (fear vs. anger/sadness neural
  asymmetry). Did v3 recognize the asymmetry: YES, named as the
  `friction_type` directly. Did it PASS despite the source's own
  explanation: YES — the source's threat-salience explanation for
  fear is present elsewhere in the same text and did not block this
  PASS. Anchors exact: 1 of 2 (`anchor[1]` exact; `anchor[0]`
  `COPY_FIDELITY_FAILURE`, same 2-character apostrophe pattern).
- **Roman shipwreck** — v2: NO. v3: NO. Validator: fully
  schema-valid (`source_anchors: []`, all PASS-only fields null,
  as required) — no new information here, confirms the NO-invariant
  path works cleanly when there's nothing to anchor.
- **Wired promo (thin negative)** — v2: NO. v3: PASS. Did high-recall
  v3 hallucinate friction into commercial copy: **NO** — the flagged
  mismatch (title says "June 2026," body describes an "August 10"
  sale deadline) is real text, verified against `source_snapshot` for
  2 of its 3 anchors (`OUT_OF_SCOPE_ANCHOR` only on anchor[0], the
  title-sourced one). Whether a stale evergreen-post date stamp is
  *interesting* enough to deserve a PASS is a separate, unresolved
  calibration question — the friction is genuine, not invented.

**Departure from the pre-registered expectation, stated plainly:**
Conducting v3 PASSed, but NOT on the specific "musicians don't need a
conductor for the core task / an exceptional conductor changes the
ensemble" pair the design doc's worked example anticipated — that pair
does not appear to occur within this fetch's first 3000 characters at
all — roughly the first third of the 3000-char budget is Atlantic
navigation/header boilerplate before the article body starts, and the
snapshot cuts off mid-word at "equally inaccurat[e]" a few paragraphs
into the real body, still before reaching the conductor/ensemble pair.
**Current A/B validity: strong** — both
models saw byte-identical bytes, so the comparison itself is clean.
**Historical comparability to the earlier resolution probe: limited**
— the production extractor/site output appears to now slice a
different 3000-character window of this article than whatever the
earlier probe saw (never byte-hashed, so this can't be proven, only
inferred from the content mismatch). v3 instead grounded its PASS in
an earlier, different, still-genuine tension (the con-artist/God
binary + an unresolved "equally inaccurate" claim cut off by the
character cap). This is independent evidence for, not against, the
completeness-authority design: a truncated snapshot changed WHICH
friction was available, and CJ-1 still found valid grounded friction
in what it had rather than
defaulting to NO — but it also means this round did not literally
reproduce the earlier resolution probe's Conducting result, and no
claim of byte-identical reproduction was ever made (see source-fetch
disclosure above).

**Status: v3 design candidate remains frozen as-is.** No prompt text
changed as a result of this round. Two implementation-layer notes
carried forward (Unicode-fold anchors before substring check; decide
whether anchors may cite the title) belong with the eventual real
validator, not with the prompt. No production wiring, no CJ-2 design,
started as a result of this round.

## ROUND 2 (2026-08-11, same day) — deterministic resolver + one harness-corrected call

Round 1's raw outputs, result JSON, and interpretation above are
UNCHANGED by this round — nothing here edits or overwrites them; new
findings are additive, in new files.

**A. Round 1 preserved.** Confirmed — no edits to `*_result.json`,
`cj1_v3_validator.py`, or the frozen v3 prompt text this round.

**B. Deterministic anchor resolver (NO model calls) —
`automation/cj1_v3_anchor_resolver.py`.** Reads Round 1's existing
result files and re-checks each v3 anchor that failed strict
validation, but ONLY by folding 4 smart-quote code points
(U+2018/U+2019 → `'`, U+201C/U+201D → `"`) for LOCATION purposes,
then persisting the untouched original source substring at that
location if — and only if — exactly one location matches. No fuzzy
matching, no edit distance, no whitespace/dash normalization, no
model-assisted repair. States: `exact_match` / `normalized_unique_match`
/ `no_match` / `ambiguous_match` / `out_of_scope`. Results (written to
`automation/.probe_fixtures/cj1-v3/resolver_reports/`, Round 1's own
`*_result.json` untouched):

| fixture | anchor | resolver verdict |
|---|---|---|
| conducting | anchor[1] (the `COPY_FIDELITY_FAILURE`) | `normalized_unique_match` |
| dogs_fear_sadness | anchor[0] (the `COPY_FIDELITY_FAILURE`) | `normalized_unique_match` |
| thin_negative_promo_codes | anchor[0] (the `OUT_OF_SCOPE_ANCHOR`) | `out_of_scope`, confirmed |

Zero `ambiguous_match`, zero `no_match` anywhere. Nothing rescued that
wasn't cleanly resolvable to exactly one real location. The strict
Round 1 `invalid` verdicts stand unchanged — this is a diagnostic
overlay, not a replacement validator.

**C. v3 harness evidence-boundary correction
(`automation/cj1_v3_probe.py`).** Round 1's `v3_user` was
`f"TITLE:\n{title}\n\nSOURCE SNAPSHOT:\n{snapshot}"` — a second
evidence channel v3's own system prompt and validator never
authorized (the prompt says "you receive a fetched SOURCE SNAPSHOT";
the validator scopes anchors to `source_snapshot` only). Corrected to
`f"SOURCE SNAPSHOT:\n{snapshot}"` — no title, snapshot is the sole
evidence authority. **v2 left unchanged** (`f"TITLE:\n{title}\n\nSUMMARY:\n{snapshot}"`)
deliberately — v2 is being observed as it actually conceptualizes
input, not matched to v3 on this axis anymore. Round 2 therefore tests
v3's *intended* interface, not a system-prompt-only A/B against v2.

**D. One new model call — v3 only, Wired promo, body-only, same
frozen snapshot (SHA-256 verified unchanged before and after rsync to
the trident scratch dir, no refetch).** Same model
(`openrouter/claude-sonnet-4.6`), `max_tokens=1200`, `temperature=0.9`.
Result: **still PASS**, and this time **fully schema-valid** (both
anchors `exact_match`, no resolver needed). New friction, unrelated to
the title: the snapshot's own tiered-discount table caps at
"25% off purchases of $6,000 or more," while a later paragraph claims
"up to 40% off" for the same "Summer Sale" — verified real by direct
lookup in `source_snapshot`, not adjacent to any 40%-off line item the
text actually names (Knoll 20%, Hay 30%). `friction_type:
measurement_discrepancy`. Result at
`automation/.probe_fixtures/cj1-v3/results/thin_negative_promo_codes_v3_bodyonly_result.json`.

**Interpretation — does NOT match the hoped-for clean pattern.** The
pre-registered hope was: remove the harness leak, Wired goes to NO,
specificity concern was purely leakage. That is only half-confirmed.
The TITLE-dependent friction from Round 1 IS gone once the leak is
fixed — but the gate still PASSes on body-only text, this time on a
genuine, fully anchor-valid numeric inconsistency in the sale copy
itself. So: **`OUT_OF_SCOPE_FRICTION`/`HARNESS_PROVENANCE_LEAK` is
confirmed and fixed for anchor[0]** — that specific failure will not
recur once probes stop leaking TITLE into v3's user prompt. But it
does NOT retire the broader specificity question: recall-biased v3,
even body-only, treats a sloppy-but-real marketing-copy discrepancy as
grounded friction. Per the explicit instruction not to tune
materiality now, this is recorded as an **open question for whoever
designs CJ-2 or a later specificity tiebreaker**, not acted on.

**E. Conducting/Dogs NOT rerun**, as instructed — Round 1's model
calls for those two fixtures stand; only the resolver (step B, no
model calls) was applied to their existing anchors.

**F. Completeness-terminology correction.** Refer to the
`length >= 3000` fixture flag as `snapshot_hit_3000_char_cap` in
discussion, not as evidence of truncation or completeness either way.
In particular: `roman_shipwreck` (1512 chars) and `dogs_fear_sadness`
(2566 chars) both have `source_truncated=False` in their fixtures —
**this is not evidence either source was fully seen.** It only means
the fetch didn't hit the 3000-char cap this specific fixture also
used as its ceiling; the underlying pages could be longer than that
ceiling for reasons unrelated to this experiment. Roman's NO and
Dogs'/Conducting's PASSes are behavioral-calibration data only, not
production-authoritative completeness claims — the source-acquisition
completeness problem (see source-authority note above) remains
entirely separate and unsolved.

**Net picture after Round 2:**

| fixture | outcome | grounded? |
|---|---|---|
| conducting | PASS | YES — both `exact_match` anchors + one `normalized_unique_match`, confirmed real |
| dogs_fear_sadness | PASS | YES — one `exact_match` + one `normalized_unique_match`, confirmed real |
| roman_shipwreck | NO | N/A — schema-valid, nothing to anchor |
| thin_negative_promo_codes (body-only) | PASS | YES — both anchors `exact_match`, real numeric inconsistency, but plausibly trivial |

**Status: v3 prompt unchanged. No production wiring. No CJ-2.** The
COPY_FIDELITY_FAILURE and OUT_OF_SCOPE_ANCHOR failure classes are now
each explained down to a root cause (Unicode quote transcription;
harness title leakage) rather than left as unexplained validator
noise. The one remaining open question — whether CJ-1's recall bias is
too permissive on real-but-trivial friction — is now isolated from
both of those and awaits a deliberate decision, not further probing
under the current design.

## FOURTH FAILURE CLASS — UNSUPPORTED_RELATION (2026-08-11, reclassification, no code/prompt change yet)

Round 2's Wired body-only PASS was reported as "a confirmed real
numeric inconsistency." On review, that's wrong. Anchor A ("25% off
purchases of $6,000 or more") and anchor B ("up to 40% off... 20%
Knoll... 30% Hay") are each individually real — but the snapshot never
states that A is a ceiling on *all* discounts in "the sale," i.e. that
A and B describe the same scope. The claimed contradiction exists only
once that shared-scope premise is silently added. This is a 4th
failure class, distinct from the other 3 because every anchor is
individually real — the defect is in the claimed RELATION, not any
anchor:

| failure class | anchors real? | relation stated by source? |
|---|---|---|
| `UNSUPPORTED_ANCHOR` | no | n/a |
| `COPY_FIDELITY_FAILURE` | yes (modulo transcription) | yes |
| `OUT_OF_SCOPE_ANCHOR` | yes, but wrong field | yes, within that field |
| `UNSUPPORTED_RELATION` | yes | **no — relation requires an added, unstated premise** |

Conducting's Round 1/2 PASS is flagged as the same defect in a
different shape, pending re-run, not asserted: "The conductor is a
con artist. Or: The conductor is God" plus the "equally inaccurat[e]"
claim are opposing opinions ABOUT conducting and a teaser announcing
the profession is misunderstood — not a reported behavior, measurement,
or outcome of conducting itself. This motivated v3.1 below rather than
retroactively relabeling the existing PASS without re-testing it.

## v3.1 — RELATION GROUNDING + RHETORICAL-FRAMING GUARD (2026-08-11)

**Status: FROZEN as v3.1 design candidate**, approved for a 3-call
targeted probe (Dogs, Conducting, Wired — NOT Roman, NOT a v2 rerun,
NOT a refetch). v3 (this document's original frozen prompt, above)
remains the historical record of round 1/2; v3.1 supersedes it as the
current candidate pending this probe's results. Two insertions only,
into the `WHAT COUNTS AS FRICTION` section, immediately after "The
snapshot is allowed to already offer its own explanation..." and
before `WHAT TO DO`. Nothing else in the prompt changes — relation/
fact shapes list, `WHAT TO DO` steps, `DECISION RULE`, `OUTPUT
INVARIANTS`, JSON schema, and the recall-bias line are all untouched.
No importance/materiality/"worthy of an essay" language added — this
targets whether the claimed factual relation is real, not whether it's
interesting.

```diff
 The snapshot is allowed to already offer its own explanation for the
 fact or relation. An explanation being present does not disqualify the
 friction -- whether that explanation actually resolves it is not your
 question to answer.
 
+RELATION GROUNDING
+
+The anchors themselves must establish the claimed friction. Do not
+create friction by adding a premise the snapshot never states -- that
+two facts share the same scope, category, baseline, timeframe,
+population, measurement, causal role, or definition.
+
+For relational friction, the anchors must establish the relationship
+between the facts without that extra premise.
+
+For single-fact friction, the anchor itself must establish the unusual
+behavior, outcome, or property claimed in resisting_detail.
+
+If something only becomes friction after you supply information or a
+relationship the snapshot doesn't state, it is not grounded friction.
+
+This does not require the source to explain the eventual mechanism.
+It requires only that the factual friction itself is present before
+interpretation begins.
+
+RHETORICAL-FRAMING GUARD
+
+Opposing opinions, provocative labels, a teaser question, or the
+source announcing that something is mysterious, controversial, or
+widely misunderstood are not, by themselves, friction.
+
+A reported disagreement CAN qualify when the disagreement itself is
+a concrete source fact -- for example, two measurements, observations,
+accounts, rules, or outcomes conflict.
+
+Otherwise the anchor must contain a reported behavior, observation,
+measurement, outcome, dependency, transformation, or rule/practice
+mismatch -- a concrete property of the thing or process itself, not
+merely a framing device about it.
+
 WHAT TO DO
```

**Why these two wordings specifically (review corrections applied
before freezing):**
- "only becomes friction," not "only becomes contradictory" —
  CJ-1 also recognizes asymmetry/dependency/mismatch/transformation,
  not only contradiction; the narrower word would have quietly
  excluded Dogs' own asymmetry shape.
- Explicit single-fact path preserved as its own sentence
  ("For single-fact friction, the anchor itself must establish the
  unusual behavior...") rather than letting the paragraph's closing
  "fact A and fact B" line imply every PASS needs a pair — that would
  have silently regressed the earlier fact-OR-relation broadening from
  the original v2→v3 design.
- Rhetorical guard explicitly carves out "a reported disagreement CAN
  qualify when the disagreement itself is a concrete source fact" —
  so "two measurements disagree" (Dogs' own shape) stays valid, and
  only bare opinion-vs-opinion framing (Conducting's "con artist/God")
  is excluded.

## ROUND 3 (v3.1-only, 3 calls, 2026-08-11) — results

**Method:** exactly 3 new model calls, v3.1 only (`PROMPT_VERSION_V3_1 =
"cj1-v3.1-relation-grounding"`), no v2 rerun, no refetch. All 3 fixture
SHA-256 hashes verified identical before running (matches Round 1/2
values). Same model/`max_tokens`/`temperature` as every prior round.
Strict validator (`cj1_v3_validator.py`) run first on each; the
conservative quote resolver (`cj1_v3_anchor_resolver.py`) run as a
SEPARATE diagnostic only where strict validation failed — never used to
overturn the strict verdict. Round 1/2 result files untouched; new
files are `automation/.probe_fixtures/cj1-v3/results/<slug>_cj1-v3.1-relation-grounding_result.json`.

| fixture | v3.1 decision | strict validator | resolver (if run) |
|---|---|---|---|
| dogs_fear_sadness | PASS | invalid (1 anchor) | `normalized_unique_match` — same apostrophe pattern as Round 1/2, real anchor |
| conducting | PASS | invalid (2 anchors) | both `normalized_unique_match` — real anchors, apostrophe transcription only |
| thin_negative_promo_codes | PASS | **valid** | not run (strict passed) |

**Against the pre-registered expectations: 1 of 3 matched, 2 did not.**

- **Dogs — matched expectation (PASS, genuinely grounded).** The
  asymmetry (fear neurally distinct from both anger and sadness; anger
  and sadness not distinct from each other) is a single relational
  fact directly reported by one MRI study, comparing all three pairs
  itself — no added premise about shared scope/category/baseline was
  needed, satisfying `RELATION GROUNDING` cleanly. Both anchors are
  real (one `exact_match`, one `normalized_unique_match` — the same
  curly-apostrophe transcription habit from Round 1/2, unrelated to
  the new guards and evidently not something `temperature=0.9`
  resampling changed).
- **Conducting — did NOT match expectation. PASS, and inspection shows
  it found "another rhetorical route," not phenomenon-level friction.**
  All 3 anchors, checked directly against the source: (1) "The
  conductor is a con artist. Or: The conductor is God" — an opinion
  opposition, not a reported behavior; (2) "I would bet that
  practically everyone... has had the fleeting thought Come on, anyone
  could do that. They're just waving their arms!" — a described common
  misconception, not an independently observed fact (confirmed by
  direct lookup: "waving their arms" sits entirely inside this same
  dismissive-opinion sentence, not stated anywhere else as a reported
  behavior); (3) "At the other end of the spectrum is the equally
  inaccurat[e]" — an incomplete, cut-off clause with no content of its
  own. v3.1's own `reason` field tries to frame "waving their arms" as
  "the stated behavior of the conductor," which is not accurate to
  where that phrase actually appears in the source. **The
  `RHETORICAL-FRAMING GUARD` did not suppress this generation** — the
  same underlying material from Round 1/2 passed again, now dressed in
  language ("concrete, text-anchored tension... what the conductor's
  physical actions actually accomplish") that argues around the guard
  rather than satisfying it.
- **Wired — did NOT match expectation. PASS, and inspection confirms
  `UNSUPPORTED_RELATION` recurred, unfixed.** v3.1 added a 3rd anchor
  this time ("you can still save thousands of dollars, on top of 50%
  off markdowns") and now claims a 3-way "direct numerical
  contradiction" (25% / 40% / 50%) "within the same promotional
  context." Checked directly against the source: this is an evergreen
  affiliate roundup covering SEVERAL DIFFERENTLY-NAMED, sequential
  sale events — an "August" tiered sale (25% cap), a "Summer Sale"
  (40%, itemized 20% Knoll / 30% Hay), a separate "outdoor sale event"
  (30% off outdoor furniture, "on top of" its own "50% off markdowns"),
  and "New to Sale deals" (yet another 40%/20%/50% split by category).
  Nothing in the snapshot states these share one scope — v3.1's own
  `open_question` even hedges "the same or overlapping sale," visibly
  registering the ambiguity while still calling it a "direct numerical
  contradiction" and PASSing anyway. All 3 anchors are real
  (strict-valid, `exact_match`) — the defect is entirely in the
  claimed RELATION, exactly the `UNSUPPORTED_RELATION` class this
  round was designed to test for.

**Interpretation, per the pre-registered framework:** this is neither
"Dogs PASS + Conducting NO + Wired NO" (the clean-fix outcome) nor
"Dogs NO" (over-restriction). It lands on the two explicit inspect-
don't-tune branches: **Wired PASS → inspected, relation still not
genuinely established** (confirms `UNSUPPORTED_RELATION`, not
resolved by v3.1's wording in this sample) and **Conducting PASS →
inspected, found another rhetorical route** (confirms the
`RHETORICAL-FRAMING GUARD` did not hold on this material in this
sample). One sample per fixture at `temperature=0.9` cannot
distinguish "the guard wording is insufficient" from "this was
stochastic variance and a re-sample would land differently" — that
distinction is unresolved and not decided here.

**Status: v3.1 remains the frozen design candidate. No further prompt
edits made.** Per explicit instruction, stopping after these 3
outputs — no CJ-2, no production wiring, no additional tuning. Two
open, un-actioned questions carried forward: whether the
`RHETORICAL-FRAMING GUARD` needs a stronger negative instruction or a
worked non-example to hold against opinion-opposition framing, and
whether `RELATION GROUNDING` needs the same treatment for
multi-clause promotional/listicle text where "context" itself is
ambiguous. Neither actioned pending review.

## ROUND 4 (temperature-isolation probe, 2026-08-11) — results

**Method:** no prompt edits. Exact frozen v3.1 prompt, exact same 3
frozen source snapshots (hashes re-verified identical before running),
same model/`max_tokens`/body-only interface/validator+resolver
discipline as Round 3, no v2, no refetch. Only variable changed:
`temperature=0.0` (confirmed accepted by CLIProxy/model via a trivial
preflight call before spending the real 3). Saved to a distinct
namespace (`*_temp0_0_result.json`) — Round 3's `temperature=0.9`
files are untouched.

| fixture | temp 0.9 (Round 3) | temp 0.0 (Round 4) | changed? |
|---|---|---|---|
| dogs_fear_sadness | PASS, grounded | PASS, grounded | **no — identical decision, identical anchors, identical reasoning** |
| conducting | PASS, rhetorical | PASS, rhetorical | **no — same verdict, but DIFFERENT anchors/route** |
| thin_negative_promo_codes | PASS, unsupported-relation (3 anchors) | PASS, unsupported-relation-shaped (2 anchors) | **no — same verdict, narrower but not resolved** |

**Dogs: zero effect from temperature.** Decision, both anchors, and
`reason` text are effectively the same finding as Round 3 (one
`exact_match`, one `normalized_unique_match` — the same
curly-apostrophe habit, present at both temperatures, confirming it's
a model transcription tendency, not sampling noise).

**Conducting: still PASS, and — critically — landed on a DIFFERENT
rhetorical route, not a re-derivation of the same one.** Round 3's
anchors were the "con artist/God" opinion-opposition and the "anyone
could do that" dismissive-thought quote. Round 4 (temp 0.0) instead
anchored on: "Musicians frequently encounter both of these extreme
views" + "Plenty of people—plenty of musicians, even—mistrust the
abracadabra mysticism." Its new `reason` argues that because
musicians work directly with conductors, their persisting mistrust is
friction ("proximity to the phenomenon does not resolve the
interpretive disagreement"). This is still describing an ATTITUDE
(mistrust/suspicion) held by people, not a reported behavior,
measurement, outcome, dependency, transformation, or rule/practice
mismatch of conducting itself — the same category the
`RHETORICAL-FRAMING GUARD` was written to exclude, just applied to
different sentences. **The fact that deterministic decoding found a
different-but-equally-rhetorical path to PASS, rather than either
holding at NO or reproducing Round 3's exact reasoning, is evidence
against "this was one unlucky high-temperature sample"** — the
underlying pull toward "people disagree about X" as friction appears
to survive temperature=0, just re-routed through different sentences.
Both anchors are real (one `exact_match`, one
`normalized_unique_match`).

**Wired: still PASS, still shaped like `UNSUPPORTED_RELATION`, but a
closer call than Round 3 — flagged with that nuance rather than
flatly restated.** Round 4 dropped Round 3's third anchor (the
"50% off markdowns," from the clearly-separate "outdoor sale event"
paragraph) and used only 2: the 25%-tier sentence and the "up to 40%
off" sentence. On rereading the full snapshot closely: the tiered-
discount paragraph's OWN closing sentence calls itself "the Design
Within Reach summer sale," and the very next paragraph opens "During
the Design Within Reach Summer Sale you can get up to 40% off" — so
these two anchors, unlike Round 3's 3-anchor version, do sit under a
shared name the source itself uses, which is more textual connection
than "no stated scope at all." The unstated premise is narrower than
Round 2/3 described it: not "these are unrelated sales" but "the
spend-tiered discount mechanism's ceiling (25%) represents the whole
sale's maximum discount across every mechanism/brand" — ordinary
retail copy routinely runs a sitewide spend-tier alongside a separate
brand-specific "up to X%" headline without those being the logical
ceiling of one another, and the source never states they're the same
measurement. Still assessed as `UNSUPPORTED_RELATION`-shaped, but
this one is a closer call on the actual text than Round 3's version,
not a clean repeat of the same error.

**Interpretation, per the pre-registered framework: this is the
"Dogs PASS + Conducting/Wired still PASS incorrectly" branch —
structural prompt-compliance, not mainly sampling variance.**
Temperature was not the variable holding v3.1 back. Both failure
shapes recur at temperature=0.0 with a fresh, independently-derived
route each time (Conducting) or a narrower-but-still-present version
of the same gap (Wired) — not a rerun of the exact same output, which
would have been the more likely signature of "it happened to land
this way by chance."

**Status: v3.1 prompt unchanged. No v3.2 drafted or written.** Per
explicit instruction, stopping here to report before any further
prompt design. This result is consistent with — but does not itself
constitute — the precedence-rule direction already proposed for a
future v3.2 (grounding/rhetorical validity checked BEFORE the recall-
bias "when uncertain, PASS" rule applies, so uncertainty about
*whether the evidence relationship exists* is no longer treated the
same as uncertainty about *whether the friction matters*). Not
drafted, not written, not decided here.

## v3.2 — VALIDITY COMES BEFORE RECALL (2026-08-11)

**Status: FROZEN as v3.2 design candidate.** Round 4 showed v3.1's
guards can be correctly stated yet still get overridden by the later
unconditional "when genuinely uncertain, PASS" line — Conducting found
a *different* rhetorical route at temperature=0.0 rather than either
holding at NO or repeating Round 3's reasoning, and Wired kept
resolving scope ambiguity toward PASS. The diagnosis: the recall bias
was written to apply to ALL uncertainty, but only downstream
interpretive-potential uncertainty should be resolved that way —
uncertainty about whether the evidence relation *exists* should not
be. v3.2 fixes precedence, not wording of the existing guards, which
are otherwise byte-identical to v3.1.

**Diff from v3.1** (full text in `automation/cj1_v3_probe.py`'s
`V3_2_SYSTEM_PROMPT`): one insertion (`VALIDITY COMES BEFORE RECALL`,
immediately before `DECISION RULE`) and one replacement (the old
unconditional uncertainty line):

```diff
    A weak or missing open_question never downgrades an otherwise
    grounded PASS -- it is handoff metadata, not part of the gate.
 
+VALIDITY COMES BEFORE RECALL
+
+Before deciding PASS, first establish that the candidate friction is
+valid:
+
+1. Every required fact is grounded in the supplied snapshot.
+
+2. If the friction is relational, the anchors themselves establish
+   that relationship. Do not PASS when the relationship depends on
+   an unstated assumption about shared scope, category, baseline,
+   timeframe, population, measurement, definition, or causal role.
+
+3. The candidate is a concrete property, behavior, observation,
+   measurement, outcome, dependency, transformation, or other
+   phenomenon-level fact -- not merely opposing opinions, provocative
+   framing, a teaser, or people saying the subject is mysterious or
+   controversial.
+
+These are validity conditions, not editorial taste.
+
+If any validity condition fails, decision is NO.
+
+If you are genuinely uncertain WHETHER a validity condition is
+satisfied, decision is also NO. Do not use the recall bias to resolve
+uncertainty about factual grounding or the existence of the claimed
+relation.
+
+Only AFTER valid grounded friction has been established does the
+recall bias apply.
+
+If valid grounded friction exists but you are uncertain whether it
+will ultimately support a useful interpretation, PASS it downstream.
+That later question is not yours to settle.
+
 DECISION RULE
 
 PASS when the snapshot contains at least one grounded fact or
 relation, anchored in exact quotable text, that creates friction --
 regardless of what it might mean, whether the snapshot explains it, or
 what subject it concerns.
 
 NO only when no grounded friction can be identified in the supplied
 snapshot, or every candidate friction requires a fact not actually
 present in it.
 
-When genuinely uncertain between PASS and NO, PASS. A false PASS costs
-one wasted downstream comparison. A false NO may permanently exclude
-this source from ever being looked at again.
+Once valid grounded friction has been established, prefer PASS when
+uncertain about its downstream interpretive potential.
```

**Deliberate final deletion:** the cost-asymmetry rationale ("a false
PASS costs one wasted downstream comparison; a false NO may
permanently exclude...") is REMOVED from the model prompt entirely,
not merely reworded — it stays true as architecture rationale (see
the recall-bias design note near the top of this document) but is not
told to the model. Reasoning: it's exactly the kind of globally
salient pro-PASS language that Round 3/4 already showed the model can
reason around; no need to hand it a justification for leaning PASS
once validity's scope is explicit.

**Compact decision logic** (documentation only, not the model prompt
— the model reasons in prose, this is for human tracking):

```
candidate friction found in snapshot?
    no  → NO

anchors claim facts actually present in snapshot?
    no / uncertain → NO
    (deterministic provenance -- exact_match / normalized_unique_match
    / ambiguous_match / no_match / out_of_scope -- is a SEPARATE
    resolver step outside the model; the model never reasons about
    quote-folding or substring matching, only about whether the fact
    it's citing is actually in the snapshot)

if relational: does the relation follow WITHOUT an unstated
shared-scope/category/baseline/timeframe/population/measurement/
definition/causal-role premise?
    no / uncertain → NO

phenomenon-level fact (behavior, observation, measurement, outcome,
dependency, transformation) rather than opinion/framing/teaser?
    no / uncertain → NO

otherwise:
    PASS
    (uncertainty from here on -- "will this matter downstream?" --
    no longer blocks PASS)
```

## ROUND 5 (v3.2-only, temperature=0.0, 2026-08-11) — results

**Method:** exactly 3 new calls, v3.2 only, `temperature=0.0`, same
frozen snapshots (hashes re-verified before running), same
model/`max_tokens`/body-only interface/validator+resolver discipline.
No v2/v3/v3.1 reruns. Results at
`automation/.probe_fixtures/cj1-v3/results/<slug>_cj1-v3.2-validity-before-recall_temp0_0_result.json`;
all earlier round files untouched.

| fixture | decision | strict validator | resolver |
|---|---|---|---|
| dogs_fear_sadness | PASS | invalid (1 anchor) | `exact_match` + `normalized_unique_match` — same apostrophe pattern, unchanged from every prior round |
| conducting | **PASS** (expected likely NO) | invalid (1 anchor) | `normalized_unique_match` + 2×`exact_match` — anchors real |
| thin_negative_promo_codes | **NO** (matched expectation) | valid | not needed |

**Did Dogs preserve the valid relational PASS? YES, unchanged.**
Identical anchors, identical asymmetry finding, identical
apostrophe-transcription habit. v3.2's new precedence block had zero
effect here because Dogs never depended on the recall bias to begin
with — the relation was always directly stated.

**Did Wired stop manufacturing equivalence between unlike discount
measurements? YES.** `reason`: "all stated facts are consistent
marketing claims about prices and percentages with no contradictions,
mismatches, or unexpected behaviors grounded in the text." Schema-
valid NO (`resisting_detail`/`source_anchors`/`friction_type`/
`open_question` all correctly null/empty). This is the fix working
exactly as designed — validity-before-recall stopped the model from
resolving "are these the same sale?" uncertainty toward PASS.

**Did Conducting obey validity-before-recall, or find another
rhetorical workaround?** Originally reported here as "found a
workaround — a more concerning one than Round 3/4's," with a
provisional `GUARD_RATIONALIZATION` failure class. **RETRACTED on
review — see `## CONDUCTING RECLASSIFICATION` below.** The anchors
are the same two from Round 4 (temp 0.0, v3.1) plus Round 3's third
anchor added back: "Musicians frequently encounter both of these
extreme views," "Plenty of people—plenty of musicians, even—mistrust
the abracadabra mysticism," and "At the other end of the spectrum is
the equally inaccurat[e]." This was called "opinion/attitude content,
not a phenomenon-level fact" — but that framing itself is contested,
not settled; see below for why.

**Outcome, corrected:** Dogs stable grounded PASS; Wired's known
`UNSUPPORTED_RELATION` behavior (present under v3/v3.1) fixed to NO
under v3.2; Conducting is a boundary case retired from prompt tuning,
not a proven failure. `GUARD_RATIONALIZATION` is NOT formalized as a
failure class — kept below as a historical observation with the human
label itself flagged as contested. No v3.3 drafted, no further prompt
tuning attempted, no CJ-2, no production wiring.

## CONDUCTING RECLASSIFICATION (2026-08-11, same day — course correction)

On review, the Round 5 framing of Conducting as a proven
`RHETORICAL-FRAMING GUARD`/validity failure was too strong, and the
`GUARD_RATIONALIZATION` label was too anthropomorphic (the model did
not "learn to evade" anything — it selected a candidate sitting on an
ambiguous boundary in the guard's own definition).

**The competing reading, taken seriously:** the current (capped,
`source_truncated=true`) snapshot does not contain the substantive
conductor/ensemble tension originally motivating this fixture — it
contains the article's opening discussion of how conducting is
perceived, including that musicians THEMSELVES (not just lay
audiences) frequently mistrust the "abracadabra mysticism" around the
profession despite direct professional proximity to it. Persistent
practitioner mistrust of one's own profession's legitimacy is
plausibly a concrete social phenomenon in its own right, not
necessarily mere rhetorical throat-clearing — and CripMinds is
explicitly supposed to be able to investigate social behavior,
institutions, and perception, not only physical/measurable systems.
Continuing to narrow the guard specifically until this snapshot
returns NO risks encoding an unintended bias toward
physical/scientific phenomena over social/attitudinal ones — exactly
the kind of accidental subject restriction this whole redesign exists
to avoid.

**Reclassified label: `AMBIGUOUS / CONTESTED FRICTION`** — not
`CLEAN_PASS`, not a proven `FALSE_PASS_FRAMING_ONLY`. Retired from
further prompt-tuning use. Dogs, Conducting, and Wired have now
shaped v3, v3.1, v3.2, the temperature decision, both guards, and the
precedence rule — they are load-bearing regression fixtures at this
point, not evidence of generalization to material the prompt was
never shaped around. Continuing to iterate the prompt specifically
until Conducting says NO is the overfitting risk this note exists to
head off.

## FRESH CALIBRATION BATCH 1 — SELECTION (recorded 2026-08-11, BEFORE any fetch or v3.2 call)

v3.2 (`cj1-v3.2-validity-before-recall`) is frozen unchanged. This
section records the 12-seed selection and its exclusions in full,
committed before any source was fetched or judged, so the selection
itself is auditable and cannot be second-guessed after seeing outputs.

**Source of seeds:** the LIVE production database
(`/srv/data/hermes/workspace/disability-ai-collective/disability_findings.db`
on trident), read-only, via `used=0 ORDER BY fetched_date DESC` —
NOT this repo's local `disability_findings.db` checkout, which was
found stale (max `fetched_date` 2026-06-22 vs. the live DB's
2026-08-11 — a real, separate discovery, logged here rather than
silently worked around: this local checkout is not being kept current
with the live pipeline).

**Hard exclusions applied before any candidate was considered:**
- `seed_id`: `a01232a434e6d7cce772088d6d20eb5f` (Conducting),
  `9c1e1b8cacbe1953c0973a6b273e7fca` (Dogs),
  `0e532fcf2c34ff2676790a4ebca7e777` (Roman shipwreck — still present
  in the live pool with today's `fetched_date`, confirming these
  recurring-RSS seeds get their `fetched_date` bumped on repeat polls
  even while `used=0`),
  `2c21d37ae590ac28cb5b2926c0c76963` (Wired promo).
- Keyword exclusion (title/domain, case-insensitive): `spacex`, `zwo`,
  `space.com`, `solar`, `astrophotography`, `eclipse`, `the sun`/`sun `
  — this live pool did contain a `space.com` "ZWO astronomy camera...
  solar and lunar imaging" article and a `space.com` "Sharpest image
  of the sun ever captured" article, confirming the exclusion target
  was real, not hypothetical.
- No published CripMinds essay used as an answer key (none of the 12
  below cross-checked against `_posts/` for this reason — see the
  original provenance-audit correction earlier in this document for
  why that check matters).

**Selection method:** browsed the live pool's most recent ~100
`used=0` rows by title/`source_name`/`themes` ONLY — `disability_angle`
was not queried until AFTER the 12 were already chosen (visible below
only as a factual record of what it contained, not as a selection
input). Picked 2 per target category, in recency order, no re-rolling
after peeking at full article bodies, no selection based on any
expectation of what CJ-1 "should" do with a given item:

| # | category | seed_id | source | title |
|---|---|---|---|---|
| 1 | science/research | `f49f0843` | The Conversation | Can DNA from cave paintings tell us who the artists were? |
| 2 | science/research | `22876907` | New Scientist | What primates tell us about the evolutionary origins of keeping pets |
| 3 | technology | `20c95f3f` | MIT Tech Review | AI for science needs reasoning, not just data |
| 4 | technology | `28598726` | Wired | The AI Slop Backlash Is Actually Having an Impact |
| 5 | arts/culture | `8393210b` | Smithsonian Magazine | This Dutch Painting Showed a 17th-Century Drinking Game Until Someone Smudged Out a Player... |
| 6 | arts/culture | `64d214d6` | Guardian Art & Design | An indigenous photographic history of America – in pictures |
| 7 | social behavior/institutions | `934ee1c3` | Le Monde English | Camille Dormoy, sociologist: 'The circular economy requires us to reclaim the time...' |
| 8 | social behavior/institutions | `16049311` | Nature | This AI tool claims to pick the top 1% of preprints. Should researchers trust it? |
| 9 | product/commercial/descriptive | `8139b7d1` | Atlas Obscura | The Outer Rim in Seattle, Washington (sci-fi themed coffee shop) |
| 10 | product/commercial/descriptive | `e2fd1d20` | Wired | The Rise of the 1 am Job Interview |
| 11 | policy/economics | `ca2d1190` | Le Monde English | French state heritage architects block roof-insulation projects over height restrictions |
| 12 | policy/economics | `ace9e557` | Guardian World | Trump's media company, which also owns Truth Social, reports $238m loss |

**`disability_angle` as-found (recorded for completeness, not used to
select):** populated (non-null) for #1 (cave-painting DNA /
neurodivergent embodiment framing), #3 (AI reasoning / autistic
pattern-recognition framing), #6 (Indigenous photographic sovereignty
/ disability-archive-photography framing); null for the other 9. This
is exactly the kind of upstream eligibility-gate content the CJ-1/CJ-2
redesign exists to route AROUND — CJ-1 itself never sees this field.

**Fetch outcome (before any LLM call):** ran the real production fetch
once per item. 10/12 resolved `source_origin='fetched_article'`.
2 (both Le Monde English — #7 sociologist/circular-economy, #11
Paris roof-insulation) came back `fallback_summary` — Le Monde appears
to block/limit scraping for this fetcher, a genuine finding, not
worked around by retrying. Per the pre-registered rule ("only include
`source_origin='fetched_article'`"), both are EXCLUDED and replaced —
selected the same way as the original 12 (recency + category fit,
before reading full article bodies), not re-rolled after seeing any
output:

| # | category | seed_id | source | title |
|---|---|---|---|---|
| 7 (replacement) | social behavior/institutions | `ca68bc73` | Nature | I caught my students using AI to cheat in an exam — here's what universities must do to stamp this out |
| 11 (replacement) | policy/economics | `92879470` | Guardian World | Australia's falling house prices have a silver lining for mortgage holders. Here's why |

**Final 12, fetched once each, frozen (`automation/.probe_fixtures/cj1-v3-calibration-batch1/`), BEFORE any v3.2 call:**

| slug | source_origin | length | cap-hit | SHA-256 |
|---|---|---|---|---|
| 01_cave_dna | fetched_article | 2643 | false | `0333af6a...b0201d7` |
| 02_primate_pets | fetched_article | 3000 | **true** | `d81c7cab...a8e989fe` |
| 03_ai_science_reasoning | fetched_article | 3000 | **true** | `eb631be5...33073bfc8` |
| 04_ai_slop_backlash | fetched_article | 3000 | **true** | `bafe352e...380958c19` |
| 05_dutch_painting_soldier | fetched_article | 3000 | **true** | `ad7b5852...71b3eafa` |
| 06_indigenous_photography | fetched_article | 289 | false | `04ee4cc8...f78e9488` |
| 07_ai_cheating_exam | fetched_article | 3000 | **true** | `f45155c0...5925770eb` |
| 08_ai_preprint_ranking | fetched_article | 3000 | **true** | `7505bb35...cb4076f97` |
| 09_outer_rim_cafe | fetched_article | 830 | false | `cffbb04c...79df1e324` |
| 10_1am_job_interview | fetched_article | 3000 | **true** | `52c005d2...4ff5fc86` |
| 11_falling_house_prices | fetched_article | 1829 | false | `1367372e...5645ffafb3f67` |
| 12_trump_media_loss | fetched_article | 2781 | false | `4ad85fad...358388e1763042e30ecd620` |

("cap-hit" = the `length>=3000` heuristic only — per the terminology
correction earlier in this document, this proves "likely cut off,"
never "verified complete." 6 of 12 hit the cap; any resulting NO on
those 6 would be `model_NO / final-authority-unknown` if this were a
production decision, which it isn't.)

12/12 eligible. Ran v3.2-only, `temperature=0.0`, body-only, no
disability_angle/persona, on each — see `## FRESH CALIBRATION BATCH 1
— RESULTS` below.

## FRESH CALIBRATION BATCH 1 — RESULTS (2026-08-11)

**Raw tally:** 10 PASS, 2 NO. Full raw+parsed outputs, strict
validator verdicts, and resolver diagnostics preserved at
`automation/.probe_fixtures/cj1-v3-calibration-batch1/results/*.json`.

**Manual classification — every PASS checked against all 6 questions,
every NO checked against the 1 question, against the FULL source
snapshot text, not just the isolated anchors:**

| slug | title | decision | strict validator | classification |
|---|---|---|---|---|
| 01_cave_dna | Cave-painting DNA | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 02_primate_pets | Primate pet-keeping origins | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 03_ai_science_reasoning | AI for science needs reasoning | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 04_ai_slop_backlash | AI slop backlash | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 05_dutch_painting_soldier | De Hooch painting restoration | PASS | invalid (2 anchors, quote-fold) | `CLEAN_PASS` |
| 06_indigenous_photography | Indigenous photography book | NO | valid | `CLEAN_NO` |
| 07_ai_cheating_exam | AI exam cheating | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 08_ai_preprint_ranking | AI preprint-ranking tool | PASS | **valid** | `CLEAN_PASS` |
| 09_outer_rim_cafe | Sci-fi café listing | NO | valid | `CLEAN_NO` |
| 10_1am_job_interview | Late-night AI interviews | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 11_falling_house_prices | RBA rates / housing | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` |
| 12_trump_media_loss | Trump Media Q2 loss | PASS | invalid (1 anchor, quote-fold) | `CLEAN_PASS` (caveat below) |

**Every single "invalid" verdict traced to the same known
`COPY_FIDELITY_FAILURE` pattern** (curly-vs-straight apostrophe,
resolver confirms `normalized_unique_match` in every case, zero
`no_match`/`ambiguous_match` across all 12) — the same transport-layer
issue identified in Round 1/2, present at `temperature=0.0` regardless
of prompt version, confirmed here on entirely fresh material. **Zero
`UNSUPPORTED_ANCHOR`. Zero `UNSUPPORTED_RELATION`. Zero
`FALSE_PASS_FRAMING_ONLY`. Zero `POSSIBLE_FALSE_NO`. Zero
`AMBIGUOUS`.**

**Per-item verification detail (why each is CLEAN, not just
"validator says so"):**

- **01 Cave DNA**: the source itself states the age places the art in
  the H. sapiens migration window, but ALSO that other species (H.
  erectus, H. floresiensis) lived in the same region, and explicitly
  says "we have no way to be certain who made it" — the uncertainty
  is the source's own statement, not an added premise.
- **02 Primate pets**: dogs domesticated ~40,000 years ago vs. cats
  grouped with wheat/rice as a much later, farming-era domestication —
  both figures adjacent in the same paragraph, a real stated asymmetry
  in two companion-animal domestication timelines. Mildest case in the
  batch — the "tension with common framing of cats as companions" is
  a bit of editorial gloss on top of a real asymmetry, not fabricated.
- **03 AI science reasoning**: the piece's own author explicitly
  states AlphaFold's creators called it "the template for accelerating
  all of science," then argues it "may not be the best template" and
  that its preconditions took decades — the article's own stated
  counter-argument, not model-invented tension.
- **04 AI slop backlash**: single fact, source's own word "despite"
  directly links LinkedIn's anti-AI-slop tool to its continued AI
  tooling — the contrast is the source's own conjunction.
- **05 De Hooch painting**: a named curator directly quoted calling
  the 3-figure (restored) version "more moralistic" and the 2-figure
  (altered) version "way more innocent" — a reversal stated in a
  direct quote, not inferred.
- **06 Indigenous photography NO — checked against full snapshot**:
  only 289 characters fetched (this Guardian gallery page yields
  essentially just its own summary blurb) — genuinely nothing but
  descriptive facts (image count, venue, dates). Correct NO.
- **07 AI exam cheating**: three sequential, explicitly-linked
  measurements (historical 65-80% range → 96% take-home → 48.6%
  in-person) — the in-person score undershoots even the historical
  FLOOR, a real quantitative anomaly the source's own numbers create,
  not an inference.
- **08 AI preprint tool — the cleanest case, schema-valid outright**:
  checked full context — all three anchors are consecutive sentences
  from ONE continuous quote by the company's co-founder, who is
  himself walking through why synthetic data is needed (published
  literature is positive-skewed, so real negative-result training
  data doesn't exist to draw from). The dependency is the source's own
  explanation, not a model-bridged inference.
- **09 Outer Rim café NO — checked against full snapshot**: the
  fetched text turned out to be the café's own description followed
  by unrelated teaser blurbs for 4 different cafés elsewhere (a page-
  structure artifact, not this café's content) — no shared claim is
  actually violated between them (different cities, different "oldest
  of its kind" scopes). Correct NO.
- **10 Late-night AI interviews**: single anchor, one sentence — "24%
  overall... for his manufacturing clients, THAT FIGURE jumps to 35%"
  — the source's own "that figure" phrase explicitly links the two
  numbers as the same measurement on a subgroup. About as clean as a
  single-fact PASS gets.
- **11 RBA rates — required checking full context to confirm, initial
  read looked like it might be a monetary-policy reasoning error**:
  in isolation, "housing eased more than expected → reason to hold
  rates" while "economy needs to slow further" looks like it might
  reflect the model misunderstanding basic policy logic (more easing
  achieved usually SUPPORTS holding, doesn't contradict needing more
  slowing). But the full snapshot shows the article explicitly frames
  this as its own "key question": *"The 'key question' for the
  governor is whether or not this slowdown will be achieved through
  this year's three interest rate hikes, or if they will need to do
  more."* The tension is the source's own explicitly-flagged open
  question, not a model-invented economic confusion. Corrected on
  review to `CLEAN_PASS`.
- **12 Trump Media loss**: the source's own sentence structure
  ("While Trump Media is generally refocusing on social media, McGurn
  said it will continue with... nuclear fusion") explicitly marks the
  contrast with "While." **Caveat, not a fail**: `resisting_detail`
  also mentions the Truth API's "$60,000–$100,000 per month" pricing
  as part of the "expansion posture" framing — that fact IS real and
  present in the snapshot (verified) but is NOT among the 3 provided
  `source_anchors`. The core anchored relation (refocus vs. fusion) is
  fully grounded; the extra elaboration in `resisting_detail` slightly
  overreaches its own anchor list. Minor scope-creep, not fabrication,
  no category in the pre-registered taxonomy fits this precisely —
  flagged rather than forced into one.

**Special calibration concern, addressed directly:** did human/social/
institutional material get wrongly treated as "mere rhetoric" the way
Conducting's mistrust-attitude content was? **No instance of this in
the batch.** 07 (student cheating → institutional policy response), 08
(researcher trust in an AI ranking tool), and 11 (central-bank
policy reasoning) are all human/institutional/behavioral subject
matter, and all three PASSed on genuinely concrete, source-stated
facts (measured exam scores; a company founder's own explanation of a
training-data dependency; a central bank's own explicitly-flagged open
question) — not on attitude-opposition the way Conducting was. The two
NOs (06, 09) were thin-content correctly, not socially-coded content
incorrectly excluded. This is reassuring but not conclusive from n=12 —
no claim of general absence of this bias is made from one batch.

**No hidden-mechanism/category-jump/persona/disability-relevance
leakage in any of the 12 outputs.** Every `open_question` is a genuine
question with no embedded answer (checked all 12 individually).

**Calibration language correction (2026-08-11, same day — review
correction):** the summary below originally read "0 false positives,
0 false negatives, 0 ambiguous," language that overstates what this
batch actually establishes. These 12 items were manually classified
AFTER seeing the model's outputs, by the same research process that
designed the rubric being applied — that is real, useful calibration
signal, but it is not an independently labeled benchmark, and "false
positive/negative" implies a ground truth this process didn't
establish independently. Corrected framing:

- 10/10 PASS outputs manually judged grounded/acceptable on review
  against full source context.
- 2/2 NO outputs showed no obvious grounded friction missed on
  review.
- 0 observed `UNSUPPORTED_ANCHOR`.
- 0 observed `UNSUPPORTED_RELATION`.
- 0 observed `FALSE_PASS_FRAMING_ONLY`.
- 0 observed `POSSIBLE_FALSE_NO`.
- 0 observed `AMBIGUOUS`.

**Sampling caveat, stated explicitly:** this batch was deliberately
constructed for source/category diversity from roughly the most
recent ~100 live-pool titles, NOT a random or representative sample
of production news flow. Its 10/12 PASS rate must NOT be read as an
estimate of CJ-1's expected pass rate on ordinary production traffic
— it answers "does v3.2 behave correctly across diverse fresh
material," not "what fraction of real seeds will pass."

**Overall read, with those two corrections in place: this is a
substantially cleaner generalization signal than the Dogs/Conducting/
Wired development history**, on material never used to shape any
prompt revision. The only recurring defect across the entire batch is
the SAME transport-layer `COPY_FIDELITY_FAILURE` (apostrophe
normalization) already known from Round 1/2/3/4/5 — a
validator/production concern, not a v3.2 prompt defect. Neither
Wired's `UNSUPPORTED_RELATION` nor (the now-retracted) Conducting's
framing concern recurred on fresh material.

## CJ-1 FROZEN (2026-08-11)

**Prompt:** `cj1-v3.2-validity-before-recall` (full text in
`automation/cj1_v3_probe.py`'s `V3_2_SYSTEM_PROMPT`, and in this
document's `## v3.2` section above).

**Status: research-calibrated candidate / CJ-2 input contract. NOT YET
a production eligibility gate.** No further CJ-1 prompt tuning from
current evidence — a future fresh batch would need to expose an
actual NEW failure class before reopening this prompt. No additional
CJ-1 calibration batch is planned right now.

**Three implementation issues carried forward, deliberately parked,
not solved:**

1. **Smart-quote exact-anchor resolver.** The curly-vs-straight
   apostrophe pattern recurred across old AND fresh material, every
   single fresh-batch strict failure resolved to exactly one
   `normalized_unique_match` under the existing tiny quote-fold rule
   (`automation/cj1_v3_anchor_resolver.py`) — zero `no_match`, zero
   `ambiguous_match`, ever, across all rounds. This is evidence the
   resolver's narrow scope (4 smart-quote code points, nothing else)
   is sufficient, not evidence it needs broadening. Still not wired
   into any production validator — that wiring is a CJ-1
   implementation task, independent of CJ-2 design.
2. **`resisting_detail` can mention real source material outside
   `source_anchors`** — the Trump Media case (#12) cited the Truth
   API's real "$60,000-$100,000/month" pricing as part of its framing
   without that fact being one of the 3 provided anchors. Not
   fabrication (the fact is real and present in the snapshot), but a
   deterministic/semantic consistency gap worth an eventual validator
   rule: `resisting_detail` should probably be checkable against
   `source_anchors` specifically, not just "somewhere in the
   snapshot." Not serious enough to reopen the v3.2 prompt.
3. **Source completeness / authoritative NO remains unresolved.** 6
   of 12 fresh-batch items hit the 3000-char cap (per the terminology
   correction already in this document: that flag proves "likely cut
   off," never "verified complete"). A PASS remains usable regardless
   of completeness; a NO on a capped snapshot cannot become an
   authoritative production rejection until completeness is
   positively established by some other mechanism. Unchanged from
   earlier rounds, still not built.

None of these three block CJ-2 research — they are CJ-1
production-hardening tasks for whenever CJ-1 actually gets wired in,
which is not now.

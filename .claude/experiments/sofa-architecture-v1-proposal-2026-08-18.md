# Sofa Architecture V1 — Proposal (Design Only, Not Implemented)

- **Date**: 2026-08-18
- **Status**: DESIGN PROPOSAL. No production code, prompt, or deployment changed.
- **Inputs**: `.claude/SOFA-METHOD.md` (canonical), `.claude/experiments/sofa-pipeline-audit-current-runtime-2026-08-18.md` (audit), and direct inspection this session of `automation/orchestrator/{generate,llm,discovery,gate,config,personas,cj2_shadow}.py` and `automation/news_fetcher.py` to confirm the audit's claims against actual code rather than trusting it blindly.
- **Verification notes**: confirmed directly — `hidden_mechanism`/`source_anchor_examined`/`why_disability_knowledge_changes_subject` exist only inside `llm.py` and are logged, not used, in `generate.py`; the writer prompt injects `prompt_block`, wound, and `AUTHORIZED PERSONAL HISTORY` (`generate.py` ~L699-970); `_pick_article_type()` (`discovery.py` L1046) is `random.choices`, called at `generate.py` L619 after `_fable_editorial_brief` (L420) has already produced the mechanism — form genuinely precedes material inspection; `gate.py` L50-69 hard-requires a named external person for `portrait`; `category_jump_judge` runs only via `run_category_jump_shadow`, writing to a shadow table never read by selection; CJ-2's D0/C0/R2 loop does not exist as code anywhere in `orchestrator/` — it is a design description, and `cj2_shadow.py` is bridge/logging plumbing for a hypothetical future winner, not a discovery engine. The audit's factual claims hold.

---

## 1. Roles That Must Stop Collapsing

The runtime currently has two roles doing five jobs:

| Job | Who does it today | Who should do it |
|---|---|---|
| Source selection | `news_fetcher.py` relevance score | Unchanged, but disturbance-aware (see §9) |
| Editorial discovery (disturbance → mechanism) | Fable Layer 1 (`_fable_editorial_brief`) | Fable, or a discovery step Fable calls |
| Perceptual lens choice | Fable Layer 2, constrained by rotation | Fable, chosen for what it reveals, not for fairness |
| Prose voice | The **persona itself**, roleplaying, via `prompt_block`+wound+history | A **generic CripMinds prose writer**, briefed by discovery |
| Byline | The persona | Unchanged — persona name stays public author |

The single most consequential fusion is **lens = writer = byline = biography-authority**, all one entity today. Sofa's `LENS ≠ WRITER` and `BYLINE ≠ PROSE PERSONA` rules exist precisely to break this fusion into three independent things that happen to often share a name on the page: the persona *chooses what becomes visible* (lens), a prose function *writes the sentences* (writer), and a name *appears under the headline* (byline). Nothing requires the writer to know it's "being" Pixel Nova. It only needs to know what Pixel Nova's way of looking discovered.

This reclassification is the spine the rest of this document works from: every question below is really asking "which of these three roles does this belong to, and what crosses the boundary between them?"

---

## 2. Question 1 — The Editorial Object

**Decision: yes, a persistent object is needed, but it is smaller than the full list in the prompt.** Call it the **Discovery Packet**. Design it by asking, for each candidate field, whether it must survive into writing, must stay internal, must be deterministic, or must be validated.

| Field | Survives to writer? | Deterministic or generated? | Validated? |
|---|---|---|---|
| Disturbance (what doesn't fit) | Yes, as a fact, not a label | Generated (LLM), grounded in source | Yes — must quote source |
| Source anchor (verbatim) | Yes — this is a fact the writer may use | Deterministic extraction target | Yes — exists in source_text |
| Hidden mechanism | Yes, as a **constraint**, not a thesis to restate | Generated | Yes — semantic entailment (already exists: `_verify_commission_mechanism_support`) |
| Why disability knowledge changes the subject | **No** — stays internal | Generated | Yes, for commissionability only |
| Reader contract | Yes, as guidance | Generated, separately prompted from mechanism (§6) | Lightly validated (distinctness check, not a fact-check) |
| Evidence hierarchy (proving vs. carrying material) | Yes — this is the writer's raw material | Generated selection over a deterministic candidate list | Yes — every item must resolve to `validate_brief` output |
| Factual uncertainties / gaps | Yes — the writer must know what NOT to claim | Deterministic (comes straight from `validate_brief`'s `not_found` list) | Already deterministic |
| Suggested article form | Yes, as a suggestion | Generated from material, not randomized | No — form has no factual content to validate |

**What must NOT be handed to the writer**: the `why_disability_knowledge_changes_subject` explanation itself. This field is Fable's *justification to itself* for why a commission is non-generic — reasoning addressed to an editorial gate, not material for an article. If it reaches the writer verbatim, the writer paraphrases it, reproducing the exact "restating the insight" failure canonical §3/§10 name. The writer needs the *result* of that reasoning (the mechanism, as a claim) without the reasoning itself.

**Deterministic vs. generated, restated plainly**: disturbance/mechanism are LLM claims gated by the existing semantic-entailment check (unchanged). Evidence-hierarchy selection is an LLM ranking over a deterministic candidate pool (dates, quotes, named entities extractable from `source_text`, not invented). The reader contract is generated, checked only for distinctness from the mechanism sentence — never fact-checked, since it's a judgment about reader interest, not a factual claim. Article form is generated from the evidence hierarchy's shape, never randomized.

---

## 3. Question 2 — What the Writer Actually Receives

Distinguish **knowledge** (things the writer must be able to act on) from **language** (sentences the writer might be tempted to copy verbatim and must not).

**Knowledge the writer needs:**
- The mechanism, stated once, as a fact the article must not contradict — not as a headline to open with.
- The evidence hierarchy: which facts *prove* the mechanism vs. which facts/documents/sequences *carry* the reader through it (these can differ — see §6).
- The reader contract, as a stance the article should earn, not a sentence to place anywhere specific.
- What is NOT known (the `not_found` gaps) — stated as a hard boundary, not as material.
- A form suggestion, explicitly labeled as a suggestion the writer can override if the material argues for something else.

**Language the writer must not copy:**
- The mechanism sentence, verbatim, as an opening or closing line.
- The reader-contract sentence, verbatim, anywhere.
- Any editorial-voice phrasing from the Discovery Packet at all — the packet is a brief, not a source of prose.

**Freedom explicitly preserved**: opening choice, sequencing, paragraph movement, *when* the mechanism becomes explicit on the page (it may never be stated as baldly as the packet states it), ending, and length. The writer's job, restated in Sofa terms, is to take a validated claim and a validated set of concrete material and *discover the article*, the same way a good writer discovers an angle from notes rather than transcribing an editor's memo. The packet gives the writer a validated destination and validated fuel; it must not give the writer the finished sentence.

---

## 4. Question 3 — What Becomes of Fable

Fable today performs: commissionability, all-lens evaluation, persona selection, mechanism discovery, brief construction, form decision (indirectly, since form is randomized outside Fable but the persona/register/length are chosen around the same point), and — via the reviewer — a second pass of review.

**Comparison:**

- **A. Fable stays the editorial director, produces a richer object.** Lowest structural change. Risk: Fable's Layer 1/Layer 2 split already does two jobs in one call chain (commission gate, then persona pick); adding evidence-hierarchy and reader-contract responsibilities to the same actor risks the same collapse Sofa is trying to fix, just moved one level up — a single call doing five jobs instead of a single writer doing five jobs.
- **B. Commissionability stays with Fable (Layer 1, unchanged — it is the best-validated part of the system and should not move); perceptual discovery, evidence hierarchy, and reader contract become a distinct *second* editorial step that only runs after commission succeeds.** This keeps the fail-closed gate exactly as it is (nothing about Story Rejection V1.1 changes) while giving discovery room to be a genuinely separate, richer act rather than a rider on the commission decision.
- **C. Further splitting** (e.g., a dedicated Reader-Contract-only call, a dedicated Evidence-Hierarchy-only call) — rejected as over-decomposition. The audit is explicit that role-collapse is the disease, but three tiny single-purpose LLM calls each returning one field is architectural aesthetics, not a real functional boundary; it adds latency and cost for no verification benefit, since none of these three fields benefit from independent verification the way commissionability does.

**Recommendation: B.** Fable's Layer 1 is untouched — the strongest layer in the system, correctly flagged preserve-only. A new post-commission step — the **Discovery step**, "Fable in a second breath," not a new department — takes the validated anchor and mechanism as required input and produces the Discovery Packet: evidence hierarchy, reader contract, form suggestion. It cannot exist without a successful commission and cannot re-litigate commissionability.

---

## 5. Question 4 — How Lenses Should Compete

Options: (a) one Fable call considering all four lenses (current), (b) N lens-specific candidate discoveries → grounded comparison → one selected, (c) a cheaper hybrid.

Current behavior already has all four `perspective()` strings visible to Layer 1 in a single call — competition inside one call, with no structured comparison and no per-candidate verification. This does not fabricate (Layer 1 is well-verified) — it **converges on the safest generic angle**, since a single call under pressure tends to pick the first defensible mechanism rather than compare several.

CJ-2's reusable idea (confirmed: `cj2_shadow.py` is bridge plumbing, not the D0/C0/R2 logic itself, which exists only as a design doc) is **generate-many → verify-each → select** — not the fixed four-competitor framing. Four full roleplayed essays per source (option b) is exactly the pattern this task says not to enable: 4x generation cost, and it repeats §4's core mistake (writer=lens) four times before selection.

**Recommended hybrid**: keep ONE commissionability call unchanged, but inside the new Discovery step (§4, option B) generate **2-3 short candidate mechanisms** (a sentence each, not an essay), each checked with the existing entailment verifier against the source anchor, then selected by a comparison prompt scoring least-generic / most-causally-necessary. Cheap (short generations + cheap entailment checks, not essays), preserves real perceptual competition, avoids CJ-2's cost profile. This directly answers the P1 finding that lens selection is rotation-driven, not reveal-driven — the new criterion is explicitly "what does this reveal," not "whose turn is it."

---

## 6. Question 5 — Where the Reader Contract Belongs

**Who creates it**: the Discovery step (§4), immediately after the mechanism is selected, in the same call or the next one — never the writer, and never Fable's Layer 1 (which must stay commission-only).

**What evidence it can rely on**: only the source anchor and mechanism already validated — it cannot introduce new facts, because it is a claim about *reader interest*, not a claim about the world.

**Validation**: it should not be fact-checked (there is nothing to fact-check — "why should a reader care" is an editorial judgment, not a factual claim) but it should be checked for **distinctness from the mechanism sentence** — a simple string/semantic-similarity check that rejects a reader contract that is just the mechanism restated ("the hidden mechanism is X" vs. "why should you care: X"). This is the one Sofa distinction that is easy to violate mechanically and cheap to catch mechanically.

**Verbatim or guidance**: guidance, never verbatim — per §3, the writer receives it as a stance to earn on the page, not a sentence to place.

**When**: strictly before prose generation, as a required, non-optional field of the Discovery Packet — a commission cannot proceed to writing without one, the same fail-closed posture already used elsewhere in the pipeline.

---

## 7. Question 6 — Evidence Hierarchy

Do not hard-code "2-4 anchors" as architecture. What must be designed is a **two-column selection**, not a count:

- **Column A — proof material**: whatever facts the mechanism verification already relied on (source anchor, the specific numbers/claims that make the mechanism true). This is largely already produced by `_verify_commission_mechanism_support`'s reasoning and should be captured, not discarded.
- **Column B — carrying material**: a ranked candidate list of documents/dates/sequences/quotes/objects/contradictions extracted from `source_text`, ranked by narrative utility (does this item let the reader *watch something happen* — a sequence of dated actions, a document trail — rather than *be told a fact*). Mobile's July 25 → July 29 → August 1 sequence is exactly a Column B item that outranked the loudest Column A-adjacent number (3→69).

The Discovery step selects and ranks Column B candidates from the existing evidence packet (no new fetching — this is a selection/ranking problem, per canonical §7, not a research problem) and passes both columns to the writer, explicitly labeled as different things: "these facts make the claim true; this material can carry the reader through it; they may overlap, prefer B when they don't."

---

## 8. Question 7 — Form

**Minimum change**: move `_pick_article_type()` from before Fable's brief to *after* the Discovery step, and change it from `random.choices` over a fixed weighted table to a **suggestion** generated from the evidence hierarchy's shape (a documentary sequence suggests `field_note`/`essay`; a strong quote-bearing conflict suggests `provocation`; the writer can override per canonical §9's "causally necessary, narratively optional").

The taxonomy (essay/field_note/provocation/portrait/pleasure/fury/confusion/indefensible/series_part) has real value as a *palette*, not a *precondition*, and should be kept — existing gate/length logic (field_note's 500-word cap, portrait's 1200-word floor) is reasonable once the form actually fits the material. The one form with a hard structural conflict is `portrait`'s named-person requirement: under form-follows-material it should only be *suggested* when the evidence hierarchy actually contains a sustained named person. `indefensible`'s fixed per-persona fiction is addressed in §9, not here.

---

## 9. Question 8 — Persona State / Wound / Biography Dependency Analysis

| Element | Classification | Reasoning |
|---|---|---|
| `perspective` (~20-word lens string) | **KEEP IN DISCOVERY** | The actual lens — belongs in the Discovery step's candidate-generation prompt (§5), not the writer prompt. |
| Persona canon (`persona_canon/*.md`) | **KEEP FOR EDITORIAL SELECTION** | Used for cross-citation-accuracy checking, not prose — orthogonal, leave as-is. |
| Persona state / mood / obsessions | **KEEP FOR EDITORIAL SELECTION** | Legitimate input to which persona gets the byline this run (rotation/freshness) — a byline-assignment concern, not discovery or prose. Do not feed to the writer. |
| `prompt_block` (600-1000 word voice brief) | **REMOVE FROM WRITER** | Prose-roleplay fuel — exactly what canonical §4 forbids. May still inform Discovery's lens; must stop being injected as "WRITE LIKE THIS PERSON." |
| Wound | **REMOVE FROM WRITER** | Manufactured biographical trauma with no discovery function and no byline function — pure roleplay input. UNCERTAIN only pending a check for other consumers (e.g. cross-article continuity); if none, remove entirely. |
| Authorized personal history | **REMOVE FROM WRITER, KEEP FOR BYLINE CONTINUITY** | Exists so a persona's occasional first-person claims stay consistent. Under Lens≠Writer, first person becomes rare, not forbidden — keep the record, stop injecting the full block into every prompt regardless of whether the piece uses first person. |
| "AUTHOR RULE" instruction ("You are the author," "written BY a disabled person") | **REMOVE ENTIRELY** | The literal contradiction of Byline≠Prose Persona — should not be softened, just removed; the byline already carries the name. |
| Byline field (`agent_name`) | **KEEP FOR BYLINE CONTINUITY** | Unchanged. |

Net effect: the defensive apparatus the audit names (`persona_factual_context` scanning, `persona_biography_unresolved` blocking, raw-draft biography scans) becomes largely unnecessary for new drafts, since the root cause is removed at the source. Those checks should not be deleted immediately — see "what must not change."

---

## 10. Question 9 — Failure Routing

Minimal taxonomy, each with a bounded response (no autonomous infinite loop — every "return" path has a retry ceiling, e.g. 1 retry, then fail closed to decline/defer, exactly like today's Story Rejection posture):

| Failure layer | Symptom | Response | Bound |
|---|---|---|---|
| SOURCE/MATERIAL | Evidence packet can't support (A) mechanism or (B) enough carrying material | RESEARCH MORE (re-fetch/re-search once) → else STOP (decline) | 1 retry |
| DISTURBANCE | Layer 1 commission fails semantic entailment | STOP (existing decline path, unchanged) | 0 retry (already fail-closed) |
| DISCOVERY | All lens candidates fail entailment, or all converge on the same generic mechanism | RE-DISCOVER once with a "reject the obvious angle" instruction → else STOP | 1 retry |
| READER CONTRACT | Distinctness check fails (contract == mechanism restated) | RE-DISCOVER the reader contract only (cheap, single field) | 1 retry |
| FORM | Suggested form conflicts with material (e.g. portrait suggested, no named person found) | RETURN ONE STAGE to form suggestion, re-derive from evidence hierarchy | 1 retry |
| WRITING | Draft contradicts the validated mechanism, or restates it verbatim, or drifts into roleplay language | RE-WRITE once with the same packet | 1 retry |
| GROUNDING | Unsupported specifics found (existing `scan_draft_for_unsupported_specifics` / `validate_brief`) | Existing gate/review behavior, unchanged | Existing bound |

The one new discipline this table encodes, from canonical §8/§13: a WRITING-layer symptom whose actual cause is upstream must be diagnosed as an upstream failure, not patched with another rewrite. If RE-WRITE fails once, the next escalation is RETURN ONE STAGE to Discovery, not a second rewrite — reversing the audit's P1 finding that failures currently only produce more prose passes.

---

## 11. Three-Benchmark Test

**FOX** (≤150 words)
SOURCE: camera-trap ecology paper. DISTURBANCE: a person walking through a grid triggered every camera; a fox mostly didn't. LENS: Pixel Nova (mediation/timing), selected over a more generic "instrument bias" candidate. DISCOVERY: detection is a channel with its own failure profile — record ≠ event. READER CONTRACT: what happens and what gets recorded aren't the same, and the gap is larger than assumed. MATERIAL: Column A (trigger-rate numbers, blank-photo mechanism); Column B (the calibration walk, the paper's rare-species caveat). FORM SUGGESTED: essay — writer free to deviate. WRITER INPUT: mechanism as constraint, both evidence columns, contract as stance, no persona voice.

**HOUR** (≤150 words)
SOURCE: Michigan/Alaska insurance depreciation bulletins. DISTURBANCE: insurers depreciate labor at the same rate as materials, though labor has no physical age. LENS: Maya Flux (systems/procurement), selected over a weaker "mistranslation of value" candidate. DISCOVERY: a calculation, not the world, manufactured the "age." READER CONTRACT: some clocks come from the world, others from paperwork. MATERIAL: Column A (bulletin text, withdrawal notice); Column B (the Alaska reversal sequence — no second world forced). FORM SUGGESTED: short essay. WRITER INPUT: same shape as Fox — no voice, wound, or biography.

**MOBILE** (≤150 words)
SOURCE: MDEQ turbine-permitting correspondence. DISTURBANCE: "temporary" preceded, not just described, the turbines' arrival. LENS: Zen Circuit's "category as actor" beats a generic "regulatory loophole" candidate on entailment and causal necessity. DISCOVERY: the category did material work before the machines existed. READER CONTRACT generated before subject detail is assembled: an ordinary word can help build something physical. MATERIAL: Column A (the classification letter); Column B ranks the July 25→29→Aug 1 sequence above the raw 3→69 count, since ranking is by narrative-carrying capacity, not magnitude. FORM SUGGESTED: essay/field_note hybrid, overridable. WRITER INPUT: sequence-first material, mechanism as constraint, no roleplay.

All three run through the identical pipeline shape (Discovery → evidence-hierarchy ranking → reader contract → form suggestion → writer) yet produce structurally different packets, because the *content* differs per source — the pipeline is not visibly identical on the page.

---

## 12. Three Architectures

### A. Minimal Rewire
**Flow**: unchanged shape. Fable Layer 1 unchanged; inside the existing `_fable_editorial_brief` call (or a second call, same actor) add evidence-hierarchy + reader-contract fields to the brief JSON; strip persona-voice injection from the writer prompt; pass mechanism + evidence hierarchy + reader contract instead. Move `_pick_article_type()` to after this brief.
**Reused**: `_fable_editorial_brief`, `_verify_commission_mechanism_support`, `validate_brief`, gate/review — unchanged.
**New**: a handful of fields on the existing brief object; no new module.
**Removed**: persona voice injection; random-before-discovery form pick.
**Quality gain**: high on the two P0s; moderate on reader-contract/evidence-hierarchy, since they're generated by an already-overloaded single call.
**Cost/latency**: near zero — no new calls.
**Migration risk**: low — smallest diff.
**Biggest failure mode**: one call doing commission + lens-pick + evidence-hierarchy + reader-contract risks the same "safest generic answer under pressure" failure already diagnosed for lens selection, now spread across more fields.

### B. Clean Separation
**Flow**: Layer 1 unchanged. NEW: a Discovery step, called only after commission succeeds, taking the validated anchor+mechanism as required input, producing the Discovery Packet (evidence hierarchy, reader contract, form suggestion) as its own object. Writer prompt rebuilt to consume it instead of persona voice material.
**Reused**: Layer 1 gate, `validate_brief`, gate/review, `perspective` field (now consumed by Discovery, not the writer).
**New**: one new function/call and one new object shape, with its own light validation (distinctness check).
**Removed**: same writer-prompt injection as A; `_ARTICLE_TYPES` random pick becomes a Discovery-driven suggestion.
**Quality gain**: higher than A on reader-contract/evidence-hierarchy quality — dedicated call, stable validated input, not sharing budget with the commission decision.
**Cost/latency**: one additional call per accepted commission (declines unaffected) — modest, bounded.
**Migration risk**: moderate — new object to test and wire, but Layer 1/gate/review untouched, so blast radius contained.
**Biggest failure mode**: schema drift between the Discovery Packet and what the writer prompt expects surfaces late unless given its own schema validation, analogous to `validate_brief`.

### C. Competitive Discovery
**Flow**: same as B, plus: inside Discovery, generate 2-3 short candidate mechanisms per lens (not essays), verify each with the existing entailment checker, select one by a comparator scored on causal necessity/non-genericness.
**Reused**: everything B reuses, plus the entailment checker called 2-3x instead of once.
**New**: candidate-generation loop + selection comparator on top of B's object.
**Removed**: same as B.
**Quality gain**: highest of the three on the specific P1 that lens selection is rotation-driven, not reveal-driven — the only option creating real perceptual competition rather than asserting it inside one call.
**Cost/latency**: highest of the three — 2-3x short generations + checks per accepted commission — still far cheaper than CJ-2's four-essay pattern, but a real, measurable add.
**Migration risk**: moderate-high — most new surface area, though it fails safe (falls back to B's single-candidate behavior on error).
**Biggest failure mode**: the comparator becomes a second, unaudited point of taste-convergence — better than one candidate only if it actually distinguishes "causally necessary" from "sounds sophisticated," unproven without its own calibration against Fox/Hour/Mobile first.

---

## RECOMMENDED ARCHITECTURE: B

## WHY:
B fixes both audited P0s (byline=persona roleplay; discovery dropped before the writer) and the two most consequential P1s (no reader contract; no evidence hierarchy) without touching the strongest, most fail-closed part of the system (Layer 1 commission gate) at all. A under-solves reader-contract/evidence-hierarchy quality by cramming them into an already-loaded call. C is the right eventual answer to the lens-selection P1 specifically, but its comparator is unproven and its cost is real — it should be evaluated *after* B's Discovery-step object exists and can be A/B-compared against a competitive version of itself, not adopted blind. B is the smallest change that stops conflating roles rather than just rewiring fields.

## FIRST IMPLEMENTATION SLICE:
Build the Discovery step as a standalone, testable function that takes today's already-validated `hidden_mechanism` + `source_anchor_examined` (from an existing, already-commissioned brief) and produces only the reader-contract field, with its distinctness check. Do not touch the writer prompt, evidence hierarchy, or form selection yet. This is testable in isolation against saved commissioned briefs (including Fox/Hour/Mobile's own evidence packets) without changing what gets published, exactly the way `cj2_shadow.py`'s shadow-mode pattern already proves safe additive testing in this codebase.

## WHAT MUST NOT CHANGE:
1. Fable Layer 1 commissionability gate and its all-four-lens judgment.
2. `_verify_commission_mechanism_support` (semantic entailment on the mechanism).
3. `validate_brief`'s deterministic force-downgrade of unverifiable facts to `not_found`.
4. Story Rejection V1.1 fail-closed short-circuit (decline/defer/no-execution before writing).
5. SP1 (testimony/quotes/interviews explicitly optional, never required).
6. Evidence-packet provenance tracking (origin, truncation, hash-stamping, aggregator isolation).
7. The persona-biography defensive scans (`persona_factual_context` checks, raw-draft biography scans) — keep them running even after writer-prompt injection is removed, until a full production cycle confirms the new prompt genuinely stops producing invented biography.

## OPEN QUESTIONS:
1. Does removing `wound`/`prompt_block` from the writer prompt measurably change prose quality (voice distinctiveness) in ways that need a different, non-roleplay mechanism to preserve persona "flavor" across a body of work?
2. Should the Discovery step's evidence-hierarchy ranking be a single LLM call over the full evidence packet, or should Column B candidates first be deterministically extracted (dates/entities/documents) before an LLM ranks them — the latter is safer but requires new extraction code not audited here.
3. What is the right distinctness-check threshold for "reader contract ≈ mechanism restated" — a hard semantic-similarity cutoff risks false rejects on genuinely close-but-valid pairs (as Hour/Fox's own calibration notes: their reader contract and opening were "the same move" for those two subjects).
4. Should `indefensible`'s fixed per-persona fiction be retired under form-follows-material, or kept as a deliberately exempt form (since it is explicitly persona-confessional rather than source-driven, a different category than the other eight)?
5. At what commission volume does Option C's added cost/latency become worth measuring in production, versus staying on B indefinitely?

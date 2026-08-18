# Sofa Pipeline Audit — Current Runtime

- **Date**: 2026-08-18
- **Scope**: Read-only audit of the live CripMinds production/editorial runtime (`automation/`) against the canonical Sofa Method (`.claude/SOFA-METHOD.md`).
- **Authority**: `.claude/SOFA-METHOD.md` is the only operational reference. The V0/V0.1/V0.2 experiment docs in `experiments/` are historical calibration records (FOX/HOUR/MOBILE) and were not used as requirements.
- **Method**: Every stage below is grounded in actual code, prompts, and DB fields inspected this session (`news_fetcher.py`, `production_orchestrator.py`, `orchestrator/{generate,discovery,llm,grounding,config,gate,review,personas,cj2_shadow}.py`). No redesign is proposed here; the audit maps reality and then states the minimum change boundary.
- **Severity**: P0 = fundamentally blocks the Sofa Method, P1 = strongly degrades it, P2 = quality issue, P3 = already acceptable.

---

## 1. Actual Runtime Pipeline (traced from code)

```
06:05  news_fetcher.py
        RSS from curated feeds → score_item() (keyword/thematic relevance_score)
        → store_seed() into news_seeds table (disability_findings.db)
        → extract_angle() (Sonnet: hidden disability angle, one sharp sentence, or NONE)
        → category_jump_judge() (SHADOW ONLY: ostensible category / resisting detail /
            hidden mechanism / category jump / correction) — recorded, never gates selection

09:00  production_orchestrator.py → generate.py
        get_news_seed()  → highest relevance_score unused seed
        get_source_text() → trafilatura fetch (cache cap 20,000 chars; origin tracked;
            fallback_summary downgraded to no-source) → build_evidence_packet()
        _fable_editorial_brief()   (llm.py)
            LAYER 1: source commissionability judged with ALL FOUR lens perspective()
                strings → commission / decline (+ deterministic validate_source_decision)
                → commission path gated by _verify_commission_mechanism_support (semantic
                entailment: does the mechanism follow from the anchor's actual content?)
            LAYER 2: persona selected from _rotation_eligible_agents(); brief fields:
                angle (a QUESTION, never a verdict), opening_scene/shape, register,
                correction_moment + resisting_example (structured evidence-candidate
                objects, grounded by validate_brief → unverifiable forced to not_found)
        Story Rejection V1/V1.1 short-circuit: decline / defer / no-execution
            all STOP before the writer runs (no article, fail-closed)
        Writer prompt assembled (~26 vars): persona prompt_block + canon + state +
            persona_factual_context (authorized history) + news_block + SOURCE MATERIAL
            + angle question + wound + opening_shape + correction/resisting + register
            + article_type FORM + length … → writer model generates draft
        raw-draft scan (scan_draft_for_unsupported_specifics, advisory candidates)
        _fable_editorial_review (EVIDENCE CONTRACT) → _fable_polish_rewrite / rewrite_with_opus
        _pre_commit_gate (deterministic regex checks + article-type compliance +
            readability + LLM rule check + surgical fix)
        images → commit → deploy → social
```

**Key structural observation**: The pipeline is a *single-source, single-pass* chain. One news seed becomes one source fetch, one Fable brief, one writer draft, one rewrite pass, one gate fix. There is no branching, no evidence ranking, and no return-to-evidence loop.

---

## 2. Canonical Stage Map

### WORLD / SOURCE — SUPPORTED
**CURRENT IMPLEMENTATION**: `news_fetcher.py` pulls RSS from curated quality feeds, scores items for thematic relevance, stores them in `news_seeds`, and extracts a disability angle per item. `get_source_text()` fetches the full article (trafilatura, 20,000-char cache, aggregator domains isolated). The evidence packet is built once and threaded unmodified through planner, reviewer, and executor, with source-origin and truncation tracked honestly.
**STATUS**: SUPPORTED
**PROBLEM**: No Scout module exists in the runtime. Canonical Sofa begins from *a disturbance that does not fit the ordinary explanation*; the runtime begins from *a news item with the highest disability-relevance keyword score*. Relevance ≠ disturbance. The instrument that actually measures disturbance (the category-jump judge) is **shadow-only, never wired into selection or into Fable**. Score-driven selection can therefore surface a thematically relevant seed containing no mechanism (Fable then declines it — correct but wasteful). (~75 words)

### DISTURBANCE — PARTIAL (CONFLATED WITH COMMISSIONABILITY)
**CURRENT IMPLEMENTATION**: No explicit disturbance stage. Fable's Layer 1 is the de facto disturbance gate: "does this source contain a sufficiently strong CripMinds mechanism… grounded in a concrete source detail?" Commission requires `source_anchor_examined` (verbatim), `hidden_mechanism`, and a `why_disability_knowledge_changes_subject` category-jump explanation. A decline is a persisted editorial "no mechanism" verdict.
**STATUS**: PARTIAL — the disturbance question is asked, but only as a binary commission gate inside the editorial-brief model call, after seed selection. It is never posed as a discovery of *what specifically doesn't fit*, and the richer disturbance instrument (category-jump judge) runs in shadow only.
**PROBLEM**: The disturbance is never articulated as an object that can be selected, ranked, or refined. Selection and disturbance are two separate, disconnected steps; the pipeline can only reject a bad seed, never improve one. (~80 words)

### PERCEPTUAL LENS — PARTIAL
**CURRENT IMPLEMENTATION**: Fable Layer 1 consumes all four `perspective()` strings (the lenses) to judge commissionability. Layer 2 selects one persona from the rotation-eligible set. The lens is the persona's ~200-char `perspective` field.
**STATUS**: PARTIAL
**PROBLEM**: The lens is selected *for its ability to carry today's execution* (rotation fairness, persona state, obsessions, mood), not for its ability to change what the disturbance *becomes*. And critically — the chosen lens is also the writer (see §4). (~65 words)

### DISCOVERY — PARTIAL
**CURRENT IMPLEMENTATION**: Fable produces a real discovery artifact: `hidden_mechanism` (stated as a claim, not a question), `why_disability_knowledge_changes_subject` (the category-jump explanation), and `source_anchor_examined` (the verbatim anchor). This is the Sofa discovery in substance, and it is the best-validated object in the pipeline: deterministic `validate_source_decision` + semantic-entailment `_verify_commission_mechanism_support`.
**STATUS**: PARTIAL
**PROBLEM**: The validated mechanism **never reaches the writer**. Grep across `generate.py` confirms `hidden_mechanism` and `why_disability_knowledge_changes_subject` are consumed only inside `llm.py` (brief + verifier) and `grounding.py` (validation). The writer is deliberately given only the *angle question* ("BRIEF A QUESTION, NOT A VERDICT", "build your own specific question from the validated evidence"). The discovery that earned the commission is therefore not an input to the prose; the writer must rediscover a mechanism on the page, and nothing validates that the prose mechanism matches the validated one. The chain DISCOVERY → WRITER is broken by design. (~100 words)

### READER CONTRACT — ABSENT
**CURRENT IMPLEMENTATION**: No reader-contract field, prompt, or validation exists anywhere in `automation/`. Grep for `reader_contract` / "reader contract" / `narrative_spine` returns nothing. The closest analog is the reviewer's post-hoc `_engagement_read` HOOK question ("the single most interesting, surprising, or true thing in this piece — the one observation that earns a stranger's time"), which runs after publication, is advisory-only, and asks about the finished article — not a pre-drafting commitment.
**STATUS**: ABSENT
**PROBLEM**: Canonical §5 requires the *why should a general reader care* sentence to be answered separately from the mechanism, before subject-level detail is introduced. The runtime never asks this question at draft time. The writer's angle question partially substitutes, but nothing forces the article to carry a reason-to-care that is distinct from the mechanism and precedes the names, agencies, and technical terms. This is a whole canonical stage missing. (~80 words)

### RESEARCH / EVIDENCE SELECTION — PARTIAL
**CURRENT IMPLEMENTATION**: One evidence packet, built once, threaded by reference through every stage (hash-stamped, mixed-provenance discards). Source text is fetched whole (20,000-char cap) with origin and truncation tracked. SP1 is verified removed in the runtime: the writer prompt states "Zero testimony is valid. Zero quotations is valid. Zero secondary named people is valid."
**STATUS**: PARTIAL
**PROBLEM**: Canonical §7 requires evidence to support (A) the disturbance/mechanism and (B) enough concrete material to carry a readable article, and §8 requires an **evidence hierarchy** — the strongest material is often a sequence of documents/dates, not the loudest number. The runtime performs no evidence selection or ranking at all: the packet is raw source text, and the writer is simply told to "use 2-4 specific facts, names, dates, or quotes as anchors." There is also no search-more loop (§7: "Search more only when the packet cannot yet support both A and B") — when a packet is insufficient, Fable declines/defers rather than enriching research. (~100 words)

### ARTICLE FORM — CONFLATED / CONTRADICTED
**CURRENT IMPLEMENTATION**: Article type is drawn by weighted random BEFORE the material is examined: `essay 0.35 / field_note 0.15 / provocation 0.12 / portrait 0.10 / pleasure 0.08 / fury 0.06 / confusion 0.06 / indefensible 0.05 / series_part 0.03`. `gate.py` hard-enforces word-count caps/floors (`field_note ≤500`, `portrait/series_part ≥1200`) and the portrait "one real named external person as sustained subject" rule (Opus-judged).
**STATUS**: CONFLATED
**PROBLEM**: Canonical §9: "Form follows the material. None of the following are required: … a fixed word count, a fixed paragraph count." The runtime inverts this: form is chosen randomly *before* the source is examined, then imposed on whatever material exists. The clearest contradiction: a `portrait` (10% of runs) *requires* a real named sustained subject — but the grounding rules forbid inventing a person and the source may contain none. A randomly assigned form can therefore demand what the evidence cannot supply, forcing either gate failure or fabrication pressure. SP1 removal itself is correct and confirmed (§10). (~80 words)

### WRITER / PROSE — SUPPORTED (but roleplay-bound)
**CURRENT IMPLEMENTATION**: An extremely elaborate ~150-line writer prompt (Bregman register, banned-jargon lists, anti-systemic test, no thesis statement, reader address, plain vocabulary, system-voice/nominalization bans, grounded-quote discipline). The draft is raw-scanned for unsupported specifics, reviewed under an evidence contract, optionally rewritten by Opus, and gated by deterministic checks + readability + a surgical-fix pass.
**STATUS**: SUPPORTED as prose craft
**PROBLEM**: The writer is also the persona (see §4). Every prose-quality mechanism here is a *floor against known failures*, not a discovery engine — the pipeline's own `_engagement_read` docstring says exactly this. The Sofa chain's real job (turn a validated discovery into prose) is under-specified because the discovery is withheld from the writer. (~70 words)

### BYLINE — CONTRADICTED
**CURRENT IMPLEMENTATION**: The byline is the persona name (`agent_name = fable_brief["persona"]`, enforced by a hard invariant). The prose is written *as* that persona: the writer prompt injects the persona's `prompt_block` voice/style brief, canon, current state, wound, and authorized personal history, and instructs "WRITE LIKE THIS PERSON" and "This article is written BY a disabled person."
**STATUS**: CONTRADICTED
**PROBLEM**: Canonical §4 is explicit: "The writer must not roleplay disability… write 'in character' because the byline is a persona. **Byline ≠ prose persona.** A persona name can remain the public author identity while the prose itself follows ordinary CripMinds editorial standards." The runtime makes byline, prose voice, biography authority, and perceptual lens the same entity. See §4 for the full treatment. (~60 words)

---

## 3. Special Audits

### 3a. LENS ≠ WRITER (highest-value section)
The canonical separation is: **the persona/lens owns discovery**; **the prose writer owns writing**. The runtime fuses them. There are only two roles in the runtime: Fable (editorial director — chooses lens, states mechanism, writes brief) and the persona (writes the article *in character*). No generic prose writer exists.

Evidence from `generate.py`:
- `_pb = agent_info['prompt_block']` — the persona's 600-1000-word voice/style brief is the *first* thing in the writer prompt.
- `"WRITE LIKE THIS PERSON."` followed by personality instructions ("You get annoyed… You change your mind mid-paragraph").
- `YOUR WOUND (the specific episode that costs you something…)` is injected.
- `AUTHORIZED PERSONAL HISTORY` (the persona's factual/fictional biography) is injected with "It is the ONLY persona material you may treat as events that actually happened to you."
- `AUTHOR RULE — NON-NEGOTIABLE: This article is written BY a disabled person, not ABOUT disability… You are the author."
- The byline *is* the persona.

This is precisely what canonical §4 forbids. The consequence is not cosmetic: when the writer inhabits the persona, the persona's biographical material becomes prose authority, and the pipeline has had to build an entire defensive apparatus (persona_factual_context, raw-draft scans, the persona-biography editorial pass, `persona_biography_unresolved` blocking) to stop the writer from *authoring new biography for the persona*. The Lens≠Writer separation would remove the root cause: write the article as ordinary CripMinds prose, let the persona remain the byline, keep discovery in Fable/lens. **STATUS: CONTRADICTED — P0.**

### 3b. DISCOVERY
Discovery *exists* (hidden_mechanism, category-jump explanation, grounded anchor) and is the most rigorously validated object in the pipeline. But it is validated for **gate-keeping**, not for **writing**: it decides commission vs. decline, then is dropped before the writer prompt is built. The writer receives only the question form of the angle. Two consequences: (1) prose discovery is unconstrained by the validated mechanism — a draft could earn its commission for mechanism X and deliver mechanism Y, and no stage would notice (the reviewer checks evidence, not mechanism-preservation); (2) the "discovery" never benefits from multiple attempts — there is exactly one Fable call, one mechanism. The canonical calibration examples (FOX/HOUR/MOBILE) are not referenced anywhere in the runtime; a fourth mechanism could surface and would not be recognized or named. **STATUS: PARTIAL — P1** (the chain break is deliberate and evidence-safety-motivated, but it severs DISCOVERY → WRITER).

### 3c. READER CONTRACT
Absent as a stage. No prompt field, no validation, no pre-drafting "why should a general reader care" artifact. The reviewer's `_engagement_read` HOOK question is the only reader-value instrument and it is post-publication, advisory, and framed as a data point ("treat its output as a data point to read, not a gate to enforce"). The Sofa method makes the reader contract a *precondition* of drafting, distinct from the mechanism, preceding subject-level detail. The runtime relies on the writer's angle question to carry this implicitly. **STATUS: ABSENT — P1.**

### 3d. EVIDENCE HIERARCHY
No stage ranks evidence or constructs a narrative spine. The evidence packet is one undifferentiated source text; the writer is told to pick 2-4 facts. Canonical §8's core teaching — "Mobile's raw turbine count was striking but weaker than the actual narrative spine: a sequence of documents/dates" — has no runtime analog. Related: canonical §8's stop condition ("If repeated prose revisions cannot answer *why does this story exist*, stop writing. Return to the evidence") is **inverted**: the runtime's failure response is *more prose passes* (rewrite_with_opus, polish rewrite, gate surgical fix), never a return to evidence, disturbance, discovery, or form. **STATUS: ABSENT — P1.**

### 3e. ARTICLE FORM (SP1 verification)
SP1 verified removed in runtime code: testimony/quotes/interviews are explicitly optional ("Zero testimony is valid… Never invent a person"). The residual form problems are (1) random form assignment before material inspection, (2) `portrait`'s hard "one real named person" requirement colliding with no-fabrication grounding, (3) the `indefensible` form is *per-persona fixed fiction* (each persona has a hardcoded unfalsifiable scenario), which conflicts with form-follows-material. **STATUS: CONFLATED — P1** (SP1 itself is correctly implemented — P3).

### 3f. WRITER
Prose-craft machinery is extensive and heavily defended against fabrication. But the writer is the persona (3a), the discovery is withheld (3b), and the reader contract is unasked (3c). The writer prompt's rule density (the Bregman device list, aphorism caps, arrival-paragraph budgets) is a *style system*, closer to a house style than to Sofa's "Make the thinking sophisticated. Make the reading easy." The runtime's own ~47% generic/delayed/absent AUTHOR_PRESENCE finding is a consistent symptom: heavy prose rules produce competent generic essays, not necessarily lens-carried discoveries. **STATUS: SUPPORTED as craft, P2 on alignment.**

### 3g. STORY REJECTION / GROUNDING
This is the strongest, best-preserved layer and must not be weakened: two-layer short-circuit (commissionability judged with all four lenses *independent of rotation*; execution constrained to eligible personas), deterministic non-LLM grounding (`validate_brief` force-downgrades unverifiable facts to `not_found`), the semantic-entailment mechanism verifier (closed the "7,000 Rooms" false commission), aggregator isolation, source-origin honesty, fail-closed degradation, and `publication_safety_version` stamping. Evidence/interpretation are structurally un-mergeable. **STATUS: SUPPORTED — P3, preserve.**

### 3h. CJ-2
OFF in production (`CJ2_INTEGRATION_MODE` unset; `cj2_shadow.py` is additive-only plumbing, `cj2_b2_*` are experiment probes). The architecture: D0 (candidate expansion from a seed into many claims), C0 (challenge/verification of candidates against the actual source text — admission gate), R2 (contract repair on failure). The reusable idea for Sofa is not the four-competitor frame — it is the *generate-many-candidates → verify-each-against-source → repair-and-select* loop, which maps directly onto DISTURBANCE → MULTIPLE PERCEPTUAL LENSES → DISCOVERY: generate several candidate mechanism/reframes per source (per lens), admit only those whose claims survive source-grounded verification, then select. That loop is exactly what the current single-pass, single-mechanism chain lacks. The fixed four-competitor assumption is incidental and droppable. **STATUS: NOT RELEVANT as CJ-2, PARTLY REUSABLE as a verification loop.** Do not enable CJ-2.

---

## 4. Gap Map

| Canonical stage | Runtime status | Severity | Evidence |
|---|---|---|---|
| WORLD/SOURCE | SUPPORTED (relevance-scored, single seed) | P2 | no Scout; category-jump judge shadow-only |
| DISTURBANCE | PARTIAL (conflated with commission gate) | P1 | judge not wired; selection ≠ disturbance |
| PERCEPTUAL LENS | PARTIAL (rotation-constrained, lens=writer) | P1 | §4 |
| DISCOVERY | PARTIAL (validated, never transmitted) | P1 | mechanism dropped before writer prompt |
| READER CONTRACT | ABSENT | P1 | no field/prompt/validation |
| RESEARCH/SELECTION | PARTIAL (no hierarchy, no search-more loop) | P1 | packet = raw text; §7/§8 unexecuted |
| ARTICLE FORM | CONFLATED (random form before material) | P1 | portrait-requires-named-person collision |
| WRITER/PROSE | SUPPORTED (craft) but discovery-starved | P2 | 3a/3b/3c |
| BYLINE | CONTRADICTED (byline = prose persona) | P0 | §4 roleplay ban |
| STORY REJECTION/GROUNDING | SUPPORTED — preserve | P3 | fail-closed, deterministic |
| SP1 (testimony optional) | VERIFIED REMOVED | P3 | writer prompt |

## 5. Minimum Change Boundary

The runtime already contains every hard, safe primitive the Sofa method needs: source grounding, evidence packets, deterministic validation, fail-closed rejection, and prose-craft gates. The boundary is not "add more safety" — it is *re-wire what already exists*:

1. **Lens≠Writer**: stop injecting persona biography/canon/wound into the writer prompt; the persona becomes byline + perspective only, discovery stays in Fable. (Removes the entire persona-biography defense apparatus's root cause.)
2. **Transmit the validated discovery**: feed `hidden_mechanism` + `source_anchor_examined` + the category-jump explanation to the writer as constraints (not verdicts), so prose serves the mechanism that was validated.
3. **Reader contract**: add one pre-drafting field (Fable or a small step): the *why should a general reader care* sentence, distinct from the mechanism, required before writing.
4. **Form follows material**: move article-type selection to after discovery; drop or make conditional the portrait named-person requirement.
5. **Evidence hierarchy**: before writing, select the 2-4 anchor facts (sequence-of-documents preference) as an explicit packet; if prose revisions fail to answer *why does this story exist*, route back to evidence, not to another rewrite.
6. **Reuse CJ-2's verify-many loop** (D0→C0→R2) as the discovery engine, without the four-competitor frame.

None of these changes weaken grounding, provenance, no-fabrication, fail-closed behavior, or evidence/interpretation separation.

---

## A. Current Pipeline (one line)

```
RSS → score → news_seeds(angle) → fetch_source → evidence_packet →
Fable[Layer1 all-lenses commission + semantic check → Layer2 persona] →
StoryRejection(decline/defer/no-exec) → writer(as persona, question angle) →
raw-draft scan → editorial review → opus/polish rewrite → gate → publish
```

## B. P0 Blockers

1. **Byline = prose persona = perceptual lens**: the writer is instructed to write *as* the persona ("WRITE LIKE THIS PERSON", canon, wound, authorized history injected), which canonical §4 forbids ("Byline ≠ prose persona"). This is the root cause of the entire persona-biography fabrication defense apparatus.
2. **Validated discovery never reaches the writer**: `hidden_mechanism`/`source_anchor_examined`/category-jump are validated for gate-keeping then dropped; the prose mechanism is unconstrained and unvalidated, breaking DISCOVERY → WRITER.

## C. P1 Degraders

1. Reader contract absent — no pre-drafting "why should a general reader care" artifact.
2. No evidence hierarchy or narrative-spine construction; no return-to-evidence loop (failures route to more prose passes).
3. Article form drawn randomly before material; `portrait` demands a real named person grounding may not supply.
4. DISTURBANCE conflated with the commission gate; the category-jump judge (the true disturbance instrument) is shadow-only.
5. Lens selection driven by rotation/persona-state, not by what the lens makes visible.
6. Single-pass discovery: one Fable call, one mechanism, no candidate generation/selection.
7. Writer prompt is a style system whose rule density correlates with generic openings (AUTHOR_PRESENCE evidence) without transmitting the validated discovery.

## D. Already Good / Preserve

1. Evidence packet built once, threaded unmodified, hash-stamped (mixed-provenance discards).
2. Deterministic, non-LLM grounding (`validate_brief`) force-downgrades unverifiable specifics to `not_found`.
3. Two-layer story rejection judged with all four lenses, independent of rotation.
4. Semantic-entailment mechanism verifier (SRF3 false-commission closure).
5. Fail-closed degradation + `publication_safety_version` + 2+-stage blocking policy.
6. SP1 verified removed: testimony/quotes/interviews explicitly optional.
7. Source-truthfulness: origin/truncation tracked, aggregator isolation, fallback_summary downgraded to no-source.

## E. Minimum Change Boundary

Re-wire existing primitives, do not add safety: (1) remove persona biography/canon/wound from the writer prompt — persona becomes byline + perspective, discovery stays in Fable; (2) transmit the validated mechanism + anchor to the writer as constraints; (3) add one pre-drafting reader-contract field, distinct from the mechanism; (4) move article-type selection after discovery and make the portrait named-person requirement conditional; (5) build an explicit 2-4-anchor evidence selection with a sequence-of-documents preference, and route repeated-prose-failure back to evidence; (6) reuse CJ-2's verify-many loop (D0→C0→R2) as the discovery engine without the four-competitor frame. Never weaken grounding, provenance, no-fabrication, fail-closed behavior, or evidence/interpretation separation.

## F. CJ-2 Reuse

**PARTLY REUSABLE.** Off in production; the four-competitor frame is not the value. The reusable architecture is the D0 (generate many candidate mechanisms/reframes per source, per lens) → C0 (admit only candidates whose claims survive source-grounded verification) → R2 (repair-and-reselect) loop. That maps directly onto DISTURBANCE → MULTIPLE PERCEPTUAL LENSES → DISCOVERY and supplies the multi-candidate, verified discovery the single-pass chain lacks. Adopt the loop; drop the fixed four-competitor assumption. Do not enable CJ-2 itself.
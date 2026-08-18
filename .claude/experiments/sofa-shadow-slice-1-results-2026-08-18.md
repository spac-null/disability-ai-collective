# Sofa Shadow Slice 1 — Results

- **Date**: 2026-08-18
- **Status**: SHADOW ONLY. Nothing below was wired into, called by, or reachable from the live 09:00 production pipeline. No production code, prompt, Story Rejection logic, grounding logic, or source-selection logic was modified. No deployment occurred.
- **Scope**: implements the smallest slice of Architecture B (`.claude/experiments/sofa-architecture-v1-proposal-2026-08-18.md`) as a standalone, additive module set, per `.claude/experiments/sofa-shadow-slice-1` task instructions.
- **Epistemic correction applied**: `hidden_mechanism` is treated throughout as **VALIDATED EDITORIAL INTERPRETATION**, never as source fact. `source_anchor` is the only field typed `EVIDENCE` at the top level of the packet. This is enforced in code (`sofa_discovery_shadow.py`'s `_field()` wrapper and `validate_discovery_packet`), not just documented — a test (`test_hidden_mechanism_never_labeled_as_evidence`) asserts it directly.

---

## IMPLEMENTED SHADOW COMPONENTS

| Component | File | What it does |
|---|---|---|
| Discovery Packet schema + builder | `automation/orchestrator/sofa_discovery_shadow.py` | `build_discovery_packet()` — pure function, no network. Inherits `hidden_mechanism`/`source_anchor_examined` from an existing commissioned brief (never regenerates them), wraps every field in an explicit `{value, epistemic_type, note}` envelope, and fails closed on any ungrounded excerpt, missing field, or reader-contract/mechanism collision. |
| Deterministic packet validator | same file | `validate_discovery_packet()` — non-LLM schema + epistemic-type check, returns `(ok, errors)`, mirrors `validate_source_decision`'s verdict-not-exception style for callers that want to inspect rather than fail-closed immediately. |
| Writer-context projector | same file | `to_writer_context()` — the one function that decides what crosses the Discovery→Writer boundary. Strips `why_disability_knowledge_changes_subject`, `reader_contract_distinctness_reason`, and all provenance bookkeeping; scans for smuggled persona-roleplay keys/phrases and raises if found. |
| Discovery-step prompt + orchestration | same file | `build_shadow_discovery_prompt()` / `run_shadow_discovery()` — the one new model call this slice adds. Generates `disturbance`, `reader_contract`, `reader_contract_distinctness_reason`, `supporting_evidence`, `carrying_material`, `known_gaps`, `form_suggestion` from an already-commissioned brief. Does not re-judge commissionability, does not touch `hidden_mechanism`, does not run multiple lens candidates (Architecture C is out of scope for this slice). |
| Shadow writer prompt + orchestration | same file | `build_shadow_writer_prompt()` / `run_shadow_writer()` — the smallest house-prose prompt built directly from canonical Sofa §4/§10, not copied from `generate.py`'s persona-voice writer prompt. Calls `assert_no_persona_leakage()` on the assembled prompt before returning it. |
| Second, independent leakage guard | same file | `assert_no_persona_leakage()` — scans a raw prompt STRING (not a dict) for `WRITE LIKE THIS PERSON`, `YOUR WOUND`, `AUTHORIZED PERSONAL HISTORY`, `You are a disabled person`, and the raw persona-material key names, so a leak can be caught even if it enters through a code path `to_writer_context` doesn't see. |
| CLI runner | `automation/sofa_shadow_probe.py` | Loads a case (commission brief + source text), runs Discovery then Writer, writes `discovery_packet.json` / `writer_context.json` / `shadow_article.md` to an output directory. `--offline <fixture.json>` mode substitutes two disclosed, hand-authored strings for the two model calls (see CASES RUN below for why this mode was necessary in this environment). Live mode calls the real CLIProxy-compatible endpoint and fails closed if no key is configured — never silently stubs in "live" mode. |
| Tests | `automation/sofa_discovery_shadow_test.py` | 33 tests, 8 classes, 0 network calls (all `llm_call` injections are local stubs). Run: `python3 automation/sofa_discovery_shadow_test.py` — all 33 pass. |

Nothing in `automation/orchestrator/generate.py`, `llm.py`, `gate.py`, `review.py`, `discovery.py`, `personas.py`, `config.py`, `production_orchestrator.py`, or `news_fetcher.py` was edited. `git status` confirms zero modifications to any tracked production file this session; only new, additive files were created.

---

## PACKET SCHEMA

```
DiscoveryPacket = {
  schema_version, built_at, evidence_packet_hash,          # bookkeeping, not writer content

  source_anchor:            {value: str, epistemic_type: EVIDENCE}
  disturbance:               {value: str, epistemic_type: EDITORIAL_INTERPRETATION}
  hidden_mechanism:           {value: str, epistemic_type: EDITORIAL_INTERPRETATION}   # INHERITED, never regenerated
  lens:                        {value: str, epistemic_type: EDITORIAL_METADATA}
  reader_contract:              {value: str, epistemic_type: EDITORIAL_GUIDANCE}
  reader_contract_distinctness_reason: {value: str, epistemic_type: EDITORIAL_GUIDANCE}  # internal-only, never reaches writer
  supporting_evidence:          [ {value: {kind, source_excerpt, note}, epistemic_type: EVIDENCE}, ... ]
  carrying_material:            [ {value: {kind, source_excerpt, note}, epistemic_type: EVIDENCE}, ... ]
  known_gaps:                    {value: [str, ...], epistemic_type: EVIDENCE}
  form_suggestion:                {value: str, epistemic_type: EDITORIAL_GUIDANCE}
}
```

Four epistemic types, not three, per the task's "at minimum" phrasing: `EVIDENCE`, `EDITORIAL_INTERPRETATION`, `EDITORIAL_GUIDANCE`, plus `EDITORIAL_METADATA` for the lens/byline bookkeeping field, which is neither a factual claim, an interpretive claim, nor a writing instruction. Grounding is enforced structurally, not just by type label: every `source_excerpt` in `supporting_evidence`/`carrying_material` must be a literal substring of `evidence_packet["source_text"]` or the builder raises; `source_anchor` is independently re-checked against `source_text` even though it was already validated once upstream by `validate_source_decision`/`_verify_commission_mechanism_support` (belt-and-suspenders — this module never trusts a claim it can verify itself). `to_writer_context()` is the sole boundary function; nothing else in this module or the probe script constructs writer input.

---

## CASES RUN

### Material availability — checked directly, not assumed

Before selecting cases, the actual local material was checked, per the task's own escape clause ("if one benchmark's original evidence packet cannot be reconstructed cleanly, report that and skip it rather than reverse-engineering from the final article").

- **FOX / HOUR / MOBILE**: `.claude/experiments/scout-v0-*` directories contain only successive **prose drafts** of the three benchmark articles (e.g. `the-fox-the-camera-missed-v02.md` through `v044.md`). No separate raw evidence/source packet (a pre-prose fetched-source-text object, or a persisted Fable brief) exists anywhere in this checkout for any of the three. Reconstructing one would mean extracting facts back out of an already-written draft — exactly the reverse-engineering-from-final-article the task instructs against. **SKIPPED**, per the task's own stated condition, not attempted.
- **Recent accepted production commissions**: `automation/engagement.db` (the table `_persist_article_plan` writes `article_plans` to) is a 0-byte file in this checkout — no tables, no rows. This is a local development checkout, not the production host; the real `article_plans`/evidence-packet history lives on the production server (`trident`), which this task does not authorize reaching into (no production access, no web research, no live network calls specified as in scope). `disability_findings.db`'s `news_seeds` table has real, previously-used seeds, but only 500-character RSS summaries (not full fetched source text) and no persisted `hidden_mechanism`/`source_anchor_examined` (that only gets written to the empty `article_plans` table). **SKIPPED**, same reasoning: no clean local material, reported rather than fabricated.
- **LLM credentials**: no `CLIPROXY_KEY`/`OPENROUTER_API_KEY` is set in this environment and no `/srv/secrets` path exists locally. `sofa_shadow_probe.py`'s live-call path (`_live_llm_call`) is real and fails closed (raises) when no key is present — it was exercised in code review but never actually invoked live in this session, for exactly that reason.

**Consequence, stated plainly**: this slice could not produce a real quality comparison against Fox/Hour/Mobile or against a real current-production article, because neither the raw material nor a live model call was available in this environment. This is reported honestly below rather than papered over with synthetic material presented as if it were real.

### SYNTH-1 — the one case actually run

To still exercise the full code path end-to-end (schema construction → validation → writer-context projection → prompt assembly → leakage scan → article), one clearly-labeled **synthetic, fictional** case was authored: `.claude/experiments/sofa-shadow-cases/synth-1-priority-b-hold.json`. Every fact in it (Fairview Housing Authority, Marcus Oyelaran, all dates/numbers) is invented for this test only, disclosed as such in the file's own `_disclosure` field, and must never be treated as real or published. It is shaped like a real commission (a `source_decision: "commission"` brief with `source_anchor_examined`/`hidden_mechanism`/`why_disability_knowledge_changes_subject`) so the code exercises the real inheritance and boundary logic, not a toy shortcut.

**Also disclosed, and important**: because no live model call was available, the two model-shaped outputs this case needed (the Discovery step's JSON, and the shadow writer's article) were **authored by the implementing agent**, following exactly the prompts `build_shadow_discovery_prompt`/`build_shadow_writer_prompt` would send to a real model, and supplied via `sofa_shadow_probe.py --offline <fixture.json>`. This is disclosed in the fixture file's own `_disclosure` field. **This is a demonstration that the mechanism works, not evidence of what a real model would produce.** Any quality reading below should be weighted accordingly.

#### A. Existing validated mechanism (input, unchanged, inherited)
> "A status created to describe a brief administrative pause is, through indefinite renewal and a reporting rule that counts it as occupancy, converted into a permanent removal from the accessible-unit waitlist without that removal ever being recorded as one."
(`why_disability_knowledge_changes_subject`, internal-only, never left the commission brief — confirmed absent from `writer_context.json` and `shadow_article.md` by grep.)

#### B. Generated Discovery Packet
Full JSON: `.claude/experiments/sofa-shadow-output/synth-1/discovery_packet.json`. Notable: `carrying_material` ranked a **document-and-letter sequence** (the January 14 auditor question → January 29 authority response) and an **unresolved absence** (no document says who first proposed the reporting rule) above the raw 61/214 ratio, which was instead placed in `supporting_evidence` (proof material) rather than `carrying_material` (narrative spine) — the exact Mobile-style hierarchy distinction the architecture proposal asked this slice to test.

#### C. Shadow Sofa article
Full text: `.claude/experiments/sofa-shadow-output/synth-1/shadow_article.md`. Opens on the January 14/29 letter exchange, not the ratio. Never states the `hidden_mechanism` sentence verbatim anywhere (checked programmatically: `mechanism in article == False`, `reader_contract in article == False`). Ends on the unresolved absence ("It simply existed, already standard practice, the first time anyone official asked"), not a restated thesis.

#### D. Current-production article for the same source
Not applicable — SYNTH-1 is synthetic; no production article exists or could exist for it.

#### E. Comparison

| Question | Reading |
|---|---|
| Do I know why this story exists? | Yes — the letter exchange gives an immediate, concrete stake (a state auditor caught something) before any status-code vocabulary is introduced. |
| Did the lens materially change what became visible? | Partially testable: the lens (`Maya Flux`, mobility/infrastructure) was inherited as metadata only, never asked to "perform." The discovery content (a category doing quiet material work) matches the kind of thing Sofa's Mobile calibration case describes, but this is a demonstration case, not evidence the lens produced anything a generic reading of the same source wouldn't have found — that comparison would require a second, lens-blind discovery run, which this slice's scope (one commission, one inherited mechanism, no competitive discovery) does not include. |
| Is the reader contract apparent without being repeated? | Yes on the page: the closing paragraphs restate the *idea* ("a number can be accurate... and still describe nothing like the apartments") without repeating either the mechanism sentence or the reader_contract sentence verbatim — confirmed programmatically, not just by eye. |
| Did the writer choose useful carrying material over merely loud facts? | Yes, by construction of this demonstration: the sequence and the absence were placed ahead of the ratio, and the article opens on the sequence. Since the "writer" here is agent-authored to the given context rather than model-generated, this shows the *packet's ranking* did its job, not yet that a real model reliably follows a ranking it's handed. |
| Does it read as narrative nonfiction rather than an editorial brief? | Yes, by inspection — developed paragraphs, no bullet-like brief language, no restated thesis. |
| Is persona roleplay absent? | Yes, verified twice: (1) grep across all three output files for `wound`, `prompt_block`, `authorized personal history`, `write like this person`, `you are a disabled person`, `why_disability_knowledge` returns nothing; (2) the code path itself would have raised `SofaShadowError` before writing any file if such a phrase had appeared in the assembled prompt or writer context. |
| Does grounding hold? | Yes, structurally guaranteed, not just asserted: every `source_excerpt` in the packet is a literal substring of `source_text`, checked by `build_discovery_packet` at construction time — a fabricated excerpt would have raised before the packet was ever written to disk. |
| Does the ending land rather than explain? | Yes — ends on the unresolved absence, not a mechanism restatement. |

---

## SHADOW VERDICT: MIXED

**MOST IMPORTANT QUALITY CHANGE:**
The structural separation works exactly as designed and is independently verifiable, not just asserted: the packet mechanically cannot contain a fabricated excerpt, cannot label `hidden_mechanism` as fact, cannot let the reader contract collapse into the mechanism sentence, and cannot leak persona-roleplay material into the writer's input — all four are enforced by code paths that raise `SofaShadowError`, not by prompt language a model could ignore. This is a real, demonstrated improvement over the audited production path, where the mechanism is dropped silently before the writer and persona biography is injected unconditionally. The evidence-hierarchy distinction (proof material vs. narrative-carrying material) also produced a genuinely different, more Mobile-like ranking in the one case tested — the letter sequence and the absence outranked the raw ratio, matching the exact lesson the architecture proposal was built to test.

**MOST IMPORTANT FAILURE:**
No real comparison against real material was possible in this environment. Zero of the three frozen benchmarks and zero real production commissions had clean local evidence packets, and no live model credentials existed to run either the Discovery step or the writer against real material even if a packet had existed. The one case run required both a synthetic (fictional, disclosed) source and agent-authored (disclosed, non-model) outputs standing in for the two LLM calls. This means the central hypothesis the task asked to test — "does this separation produce a noticeably better article from the SAME grounded material" — was **not actually tested against real material or a real model** this session. What was tested and passed is narrower: the code enforces the intended epistemic boundaries mechanically, and the mechanism/reader-contract/evidence-hierarchy shapes are structurally sound when fed well-formed input.

**READY FOR PRODUCTION WIRING? NO**

Not because the architecture is wrong — the mechanical test passed cleanly — but because "noticeably better article" is a claim about real model behavior against real material, and neither was exercised here. Wiring this into production before that gap is closed would mean trusting an unverified assumption about how a real model behaves when handed this exact prompt shape, which is precisely the kind of untested claim this codebase's own conventions (deterministic validation before trust, semantic-entailment verification before commission) exist to prevent.

**NEXT SMALLEST SLICE:**
Run `sofa_shadow_probe.py` in **live mode** (real `CLIPROXY_KEY`/OpenRouter credentials, no `--offline`) against 2-3 real recently-commissioned briefs, either by pulling `article_plans` rows from the actual production `engagement.db` on the trident host (read-only, offline export, still no live publish) or by manually re-running today's actual Fable Layer 1 call against a fresh real source fetch and feeding its output straight into `run_shadow_discovery`/`run_shadow_writer`. Compare the resulting shadow article against the real production article for the same commission, side by side, using the same eight questions in §E above — this is the smallest next step that would actually test the hypothesis this slice was built to test, rather than only testing that the plumbing is sound.

---

## Files created this session

- `automation/orchestrator/sofa_discovery_shadow.py` (new module, shadow only)
- `automation/sofa_discovery_shadow_test.py` (33 tests, all passing, zero network)
- `automation/sofa_shadow_probe.py` (CLI runner, shadow only, fails closed with no credentials, offline mode disclosed)
- `.claude/experiments/sofa-shadow-cases/synth-1-priority-b-hold.json` (synthetic case, disclosed)
- `.claude/experiments/sofa-shadow-cases/synth-1-fixture.json` (agent-authored model-call substitute, disclosed)
- `.claude/experiments/sofa-shadow-output/synth-1/{discovery_packet.json, writer_context.json, shadow_article.md}` (generated artifacts from the one run)
- `.claude/experiments/sofa-shadow-slice-1-results-2026-08-18.md` (this file)

No file outside `.claude/experiments/` and the three new `automation/` files above was created or modified. No production call site was changed. Nothing was committed to git as part of this instruction; if committed later, it should be committed with a message that states plainly that this is a shadow-only prototype not wired into the live pipeline.

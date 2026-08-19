# FORM-1.3 — Semantic Ownership + Functional Position Correction

Run 2026-08-19. Single generation. No retries, no candidates, no cherry-picking.

## EXECUTION MODE: LOCAL_CLAUDE_SUBSCRIPTION

**This is a manual architecture-development run, NOT a production-path replay.**
No OpenRouter, no Trident, no Fable. The writer identity does NOT match the frozen
Edinburgh lineage (`openrouter/claude-opus-4.8` via CLIProxy) used by FORM-1/1.1/1.2.
That is a real confound on any comparison with those iterations.

- writer: `claude-opus-5[1m]` — local Claude Code subscription, general-purpose subagent,
  model inherited from session
- auditor: same, executing the byte-identical `build_shadow_grounding_audit_prompt`

## Hashes
| artifact | sha256 |
|---|---|
| source-snapshot.txt (frozen, unchanged) | fee0a03b8bb0c56b88b0806a9120576c87f0983764d8620c77c56b59531d4753 |
| commission-brief.json | 870d84ba931abf194db5fad8017185cbf2f034ec08e383d1d89fcb8b3fce3387 |
| evidence-packet.json | 8628b234e1fc335b391b26a2dddf7b048b626f073b09a0cf6706f4e2d5ce60a5 |
| form1-3-packet.json | a620d0ce700a501de1695cc63253b518da283397388dba4dfb1f570af8f8e8ab |
| form1-3-writer-prompt.txt (persisted BEFORE generation) | 12e520e449752ed89522963c77a48fc2b86636a31a20d8f3ca47ac4ec276cdfd |
| form1-3-article.md (691 words) | 9a78d9a4c28f4a891cf222b28c87d76fe567bc31c0ff7eec8d56aa93d339bff4 |
| form1-3-audit-prompt.txt | ddaf419cf602dd64a46a933f79a2280d436aff1d9697c3194e967010a6745831 |

The runner is two-phase (`--preserve` / `--record`). `--record` re-derives the packet and
prompt and refuses unless both hash-match the persisted artifacts, and refuses if an
article already exists. `--preserve` additionally asserts that no global list-order
authority survives in the prompt.

## Delta from FORM-1.2 — exactly two corrections

**1. SEMANTIC OWNERSHIP.** The ownerless `"return to the meaning of 'discovery'"` is
replaced by an instruction returning to *the reviewer's own language of discovery* and
setting it beside the George/Walter facts. The destination is made provenance-neutral:
"some of the work **discussed in the review**" replaces "the work **it celebrates**"
(ambiguous pronoun + festival-coded verb). The three scattered festival prohibitions are
replaced by ONE positive boundary: the festival is a setting/referent, not a speaker.
Net: `festival` mentions in the system prompt 10 -> 6; `discovery` 2 -> 3.

**2. FUNCTIONAL POSITION.** `"in the order given"` and all global list-order authority
DELETED (asserted programmatically). One functional route stated instead, with the
countervoice BEFORE arrival: reviewer's encounter texture -> George/Walter facts ->
reviewer's clarity/duty countervoice -> return to the reviewer's discovery language ->
distinction/arrival -> STOP. The arrival is explicitly terminal.

**Kept from FORM-1.2:** reviewer-framed opening, REVIEWER_NARRATION classification,
provenance availability. Added narrowly: prose must not discuss attribution with the reader.

**Unchanged:** source, commission, Discovery, George/Walter burden, intended discovery,
no-agency/consent boundary, grounding boundaries, length guidance, Hasegawa omission,
both guards (neither redesigned), single-generation discipline.

## Result

Ownership defect: **FIXED.** Festival-as-speaker/possessor phrases 3 (FORM-1.1) -> 6
(FORM-1.2) -> **0**.
Position defect: **FIXED.** Countervoice at para 5, arrival at paras 7-8, zero paragraphs
after arrival.
Grounding: still **FAIL** — 2 UNSUPPORTED, but of a **different class**: an invented venue
name ("City Art Centre" where the source says "City Art Gallery") and an invented
specificity ("did not know the work existed an hour ago"). Neither is an ownership failure.

Caveat: the writer model changed for this run. With N=1 and a changed writer, the two new
errors cannot be attributed to the Form rather than to writer variation.

Decision: REPEAT_FOR_VARIANCE.

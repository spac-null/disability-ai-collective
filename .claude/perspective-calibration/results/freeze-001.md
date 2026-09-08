# Perspective Library Calibration — Freeze 001

**PILOT TECHNICAL STATUS: PASS** (after one mechanical correction — see below)

**A CONTRACT: FROZEN**
**B CONTRACT: FROZEN**
**BLIND RENDERER: FROZEN**

**MODEL/PROVIDER:** requested `anthropic/claude-opus-4.8`, served as `claude-opus-5` via
`claude-cli-subscription` (this environment's Claude.ai subscription OAuth) — confirmed
identical for every one of the 8 calls, both conditions, no fallback, no OpenRouter used.

**DATE:** 2026-09-08

---

## Stable fingerprints (for drift detection before the scored 16)

| Artifact | Fingerprint |
|---|---|
| `automation/new_engine_v1/research.py`, `LENS_PROBE_SYSTEM` string only (Condition A's exact live prompt text) | SHA-256 `54030e5be0f299ecf5b0f1cfe25b1ac9fa7ae7007cbd5145a8565cb6c0f30c8b` |
| `automation/new_engine_v1/research.py`, whole file (Condition A's full implementation reference) | SHA-256 `6acd99b5d7d9cf17cb6379eec13e93200d0028886b31d3a8a07c98abd8a5996b` |
| `results/condition-b-system-prompt-001.txt` (Condition B's exact, corrected, frozen system prompt) | SHA-256 `04c913fa09835c08019612931b8cf5186ac821eaf22b10337b2a3323d7dc578a` |
| `subject-set-001.md` (run-facing subject content) | SHA-256 `5cb2866de205586048c2340377af44d764024b005004baa471a891040ad05a44` |
| `README.md` (carries the blind-rendering contract's field-mapping prose) | SHA-256 `867de318c8ca1ff5ae200b59ffddd7eaf560f67703bd3c812f968e5afe293283` |

Before running the scored 16, re-hash all five and confirm no drift. If any differ from the
above without a recorded, deliberate reason, stop and re-freeze rather than proceed.

---

## What happened in this pilot

All 4 pilot subjects (P01–P04) were run against both conditions: `anthropic/claude-opus-4.8`
(served as `claude-opus-5`), fresh isolated call per condition per subject, execution order
randomized and logged, identical world payload (SHA-256-verified matching) for both
conditions on every subject.

**One real mechanical defect was found and corrected.** The first Condition B pass leaked
axis/instrument labels ("Axis 8", "Axis 12", "Axis 1", "Axis 11") directly into the visible
HYPOTHESIS/WHY-DISTINCTIVELY-CRIP-MINDS prose on 3 of 4 subjects (P01, P02, P04) — not into
the separate, already-hidden `instruments_used` metadata field, but into the human-readable
narrative fields that flow straight into the blind display. This is exactly the
"hidden instrument/mind/condition metadata leaks into blind display" defect category the pilot
exists to catch.

**The fix was the smallest possible correction**: one added paragraph in Condition B's output
contract instructing it to keep axis/instrument/mind labels out of the narrative fields and
confined to the separate `instruments_used`/`mind_sharpened` fields — a formatting instruction,
not an intellectual one. Nothing about which axes, instruments, or process rules Condition B
may use was touched; nothing in `README.md`, `subject-set-001.md`, or `design-notes-001.md`
required editing, because none of those three documents specified the literal output-format
wording — they specified what must stay hidden, and the fix simply makes the implementation
honor that. **Condition A was not touched or re-run** — the defect was specific to Condition
B's prompt, and A's outputs from the first pass remain valid.

**Only Condition B was re-run**, for all 4 subjects (the defect was in the shared system
prompt, not subject-specific, so all 4 were re-run for consistency even though the leak had
only shown up in 3 of the original 4 outputs). A full re-scan of the corrected run — every
field of every candidate, not just the TOP one — found zero remaining leaks.

## Technical checks (all 4 subjects)

| Check | P01 | P02 | P03 | P04 |
|---|---|---|---|---|
| Both calls completed | ✓ | ✓ | ✓ | ✓ |
| Correct model requested (A) | ✓ | ✓ | N/A* | ✓ |
| Correct model requested (B) | ✓ | ✓ | ✓ | ✓ |
| World payload hash match (A==B) | ✓ | ✓ | ✓ | ✓ |
| A conforms to live contract | ✓ | ✓ | ✓** | ✓ |
| B conforms to frozen contract | ✓ | ✓ | ✓ | ✓ |
| B designates exactly one TOP | ✓ | ✓ | ✓ | ✓ |
| Blind display leak-free (manual + structural) | ✓ | ✓ | ✓ | ✓ |

\* P03's Condition A call hit the live `lens_probe()` code's own documented graceful-failure
path: the model's reply wasn't strict JSON, `parse_json_object` raised, and `lens_probe()`
caught it and returned `{"ran": false, "error": "..."}` exactly as its own docstring specifies
("A probe that cannot run costs the run nothing"). No `_provider` block exists on that error
path, so "correct model requested" isn't checkable for that call — this is a property of the
live contract's own error handling, not a defect in this pilot's execution. \** "Conforms to
live contract" for P03/A means conforming to its documented failure mode, which it did.

## Cost / token facts (informative, not evaluative)

- Total across all 8 calls: **A ≈ $0.59, B ≈ $1.21 subscription-cost-equivalent** (excludes one
  earlier $0.30 single-call feasibility check made before the pilot proper, to confirm the
  provider path was reachable at all).
- B consumed **~2.1x A's input tokens** and **~9x A's output tokens** per subject, driven
  entirely by B's much larger system prompt (14 axes + 16 full instruments + sharpenings ≈
  53KB) and its richer per-subject output schema (up to 3 structured candidates vs. A's single
  assumption/carrier pair).
- Neither condition's temperature pin was honoured by the underlying `claude-cli-subscription`
  path (recorded as `temperature_honoured: null` on every call) — this matches
  `provider.py`'s own documented behavior for Claude-family calls via this path
  (`temperature_required=False`), not a defect.

## What this pilot does NOT establish

Whether B's hypotheses are better than A's. On these four subjects: A returned NOTHING_HERE
on P01 and P02, a real hypothesis on P04, and hit its documented parse-failure path on P03. B
returned a real, ranked, non-forced-looking hypothesis on all four, including the two subjects
presumed likely to be NOTHING_HERE. **This is data, not a verdict** — it is exactly the kind
of "surprising" pattern the design's Negative-Prior Rule anticipated and explicitly said not
to over-read from a 4-subject mechanical pilot. No intellectual conclusion is drawn here.

---

**NEXT STEP: OWNER INSPECTS PILOT ARTIFACTS, THEN RUN SCORED 16 ONCE.**

# Free-path disconnection audit — 2026-09-30

External read-only audit of the free argumentative path at **53d27df**. No pipeline was
run by the auditor and no file was changed by it. Two findings. One is fixed in this
commit. The other is located here and deliberately not bundled: on 2026-09-29 seventeen
changes went out against three articles and an external audit then found five defects,
all introduced that day, all through a suite that had passed eight times.

## 1. Research's narrower scope did not reach the Writer — FIXED

**Produced.** `new_engine_v1/research.py` asks `scope()` of every anchor for "a narrower
subject the anchor actually supports", stores it on the pack as `narrower_subject`, and
the sufficiency assessment turns a non-empty answer into the `NARROW` verdict.

**Consumed.** By nothing. A repository-wide search found the key in `research.py`, a test
and a stub pack, and nowhere else. `runner.py` reads the verdict only to separate `HOLD`
from proceed, so `NARROW` proceeded exactly as `ARTICLE` did and the narrowing was
dropped at the stage boundary. Neither engine ever saw it — this is not a free-path
regression, it is a field that has never been read.

**Cost, on the one run where it was measurable.**
`production-20260930T085346Z-54ca6694` was narrowed to whether named Inuit contributors
appear in the formal scientific and legal record or only in narrative acknowledgement.
Its 1,427-word draft does not examine that question and it held at Reader after nine
model calls. The hold is not attributable to this omission alone, and no claim is made
that rendering the scope would have passed it.

**Fix.** `narrower_scope_block()` in `free_composition.py`, rendered directly under the
subject it constrains, inside `free_writer_user()`. It is a scope constraint and not
evidence: it licenses no fact, carries no fact id, and is outside the frozen evidence
listing. Tests: `free_composition_test.py` section 12.

**Falsified before shipping.** With the block's call severed, 5 checks fail across two
tests including the end-to-end one that reads the bytes handed to `provider.complete`.
Restored, the suite passes. A test that only exercised the renderer directly would have
passed on every day the field reached no Writer at all.

## 2. Free-path Safety records cannot support the replay they describe — NOT FIXED

**Produced.** `free_composition.py:791–807,1086` builds a licensing record for Safety and
its docstring says it is persisted as `LICENSING_RECORD.json`.

**Consumed.** Nothing persists it. `LICENSING_RECORD.json` appears in that docstring and
nowhere else in the repository; `_persist_free()` does not write it.
`publication_audit.py:109–112,191–195` instead requires `WRITER_PACKET.json`,
`ARCHITECTURE.json` and `CUT_REPORT.json` — three planned-path files the free path never
creates by design.

**Cost.** In the run above, Safety ran and all three files are absent. A read-only call
to `publication_audit._reaudit_report()` reports Safety replay as `INCOMPLETE`. No
published free-path article exists yet, so the publication consequence is unestablished.

**Correction when it is taken.** Persist the computed licensing record; write a
free-specific replay descriptor naming the actual Safety inputs; make the audit's
required-file check select by composition engine. One deploy of its own.

## 3. Observed while fixing 1 — not from the audit, NOT FIXED

`free_writer_user()` inserts the `EDITORIAL INTENT` header at index 0 with no terminator,
so every later block renders textually under "None of the following is evidence and none
of it may be asserted as a fact about this story." That is harmless for a scope
constraint, which asserts nothing. It is **not** harmless for `source_attribution_block`,
whose own docstring says "This is EVIDENCE, not instruction" — the one block whose job is
to tell the Writer who a text is sits under a sentence disclaiming it. Pre-existing at
53d27df, unrelated to this change, and the fix is a scoped header rather than a moved
block.

## 4. Adversarial review of the fix itself, before deploy — three findings

Run against the uncommitted diff, read-only, by an external model. This is the control the
2026-09-29 session did not have: that day's suite passed eight times while five defects
went out, because a suite written by the author tests the behaviour the author intended.

**4a. The provenance sentence overstated what the code does — FIXED before deploy.**
The first draft told the Writer that research "read the anchor and **found** it carries a
narrower subject", and recorded the verdict "for that reason". Both are false.
`scope_prompt` asks a single model call, on the anchor text alone and before any source is
fetched, for the subject **and** the narrower subject together (`research.py:864-882`);
`scope()` parses the reply and validates neither; the verdict flip is mechanical on
non-emptiness (`research.py:1265-1267`). The block now says both subjects came from the
same reading and when that reading happened. It still renders the narrowing as a
constraint, because the broad subject comes from the identical reply — the two are equally
grounded, and preferring the broad one would be a preference dressed as a safeguard.
Five assertions now fail if the overstatement returns.

**4b. A model-authored string in the Writer's prompt can kill a good run — REAL,
PRE-EXISTING, NOT BUNDLED.** `PLAN_LEAK_MARKERS` contains `beat`, matched whole-word
against the whole user prompt; a match raises `CompositionHold` before the Writer is
called. The reviewer called this a BLOCKER introduced by the change. Measured on
**unchanged 53d27df bytes**, with no `narrower_subject` present anywhere:

```
subject contains 'beat'        -> ["the Writer's user prompt carries the planning marker 'beat'"]
a PROPOSITION contains 'beat'  -> ["the Writer's user prompt carries the planning marker 'beat'"]
```

So the surface is the subject and all 77 propositions, and it exists today. This change
adds one short string to it. **It has never fired: 0 of 309 retained runs contain that
hold.** A Ledger about music, policing or a heartbeat would trip it. The fix is to scan
only the packet renderer's machine-generated headings — the reasoning already applied to
the system prompt, where the craft corpus is prose about writing and only unambiguous
headings are checked. One deploy of its own.

**4c. Two of the four new tests promise more than they check — ONE FIXED, ONE ACCEPTED.**
`test_an_unnarrowed_run_is_byte_identical_to_before` compared two outputs of the *current*
function, not against the pre-change prompt; renamed to
`test_an_unnarrowed_pack_adds_nothing_to_the_prompt`, which is what it actually
establishes. `test_the_key_composition_reads_is_the_key_research_writes` is a grep test
and does pass under severance — kept deliberately, because it catches a *rename*, which is
what it claims, and the end-to-end test covers delivery. Falsification confirms the suite
as a whole is not blind: with the block's call severed, 5 checks fail across two tests
including the one that reads the bytes handed to `provider.complete`.

## 5. The absence problem was misdiagnosed twice before it was found

**The handoff's diagnosis was wrong, and so was my first replacement for it.** Both rested
on `story.negative_shape_of`, which is not a test of whether a proposition states an
absence. It is seventeen hand-written regexes for the shapes a *Writer* reaches for when
it over-claims one, and it matches none of these:

```
NO   The survey did not collect housing status.
NO   No records exist of the 1974 inspection.
NO   The survey excludes unhoused people.
NO   Access to the basement is not step free.
NO   Lung function equations were not validated for this group.
                                             missed 12 of 12
```

So "Ledgers are 1.1% negative-shaped" does not mean absences are not arriving. It means
that matcher recognises 1.18% of propositions. I built a retrieval change on that reading
— a fifth query angle aimed at documents that state a gap — and **reverted it unshipped**
after an adversarial review pointed out both that the diagnosis was unproven and that
spending one of the four existing angles would likely displace the
outside-the-institution query, the one that supplies the independent source the
sufficiency gate requires. It could have reduced throughput.

**The actual defect, measured across the 120 retained Ledgers holding any fact:**

| | |
|---|---|
| facts the freeze TYPED negative (what Safety accepts) | 505 |
| facts the shape matcher catches (what the Writer was shown) | 128 |
| both | 85 |
| **licences that existed and were never shown to any Writer** | **420** |
| Ledgers holding at least one hidden licence | 93 of 120 |
| Ledgers told "ABSENCES YOU MAY CLAIM: NONE" while holding typed negatives | 37 |

`negative_admission_audit` has drawn its pool from typed **plus** shaped since
2026-09-20. `negative_permissions_block`, written 2026-09-30, was built on shaped alone.
The permission decision and the gate that enforces it were reading two different
definitions of a negative — the one thing `negative_shape_of`'s own docstring says it
exists to prevent. `verify_declared_negatives` was a third reader with the same narrow
pool. All three now use one definition; the adversary confirms the displayed pool equals
the audit's exactly.

`rehearsal-20260930T173120Z`, cited in the code as proof that no absence had arrived, held
four typed absences in its 57 facts.

**Still open, from the adversary — NOT FIXED.** `check_ledger` accepts a fact typed
`ABSENCE` with proposition "The survey did not collect housing status" whose verbatim span
says only "The survey did not collect names." The WORLD-negative rule checks that the span
contains a negative word, not that it supports *this* proposition. Reproduced in-session.
Surfacing typed negatives to the Writer makes that gap reachable where before it was
merely latent, so it is worth a deploy of its own. The alternative — continuing to
withhold 420 licences Safety already accepts, while the Writer invents absences because it
is told it has none — is worse.

## What the auditor checked and found connected

The approved instrument reaches live research and the free Writer; source role and
relation affect research budget allocation; licensed relations reach the Writer; negative
permissions and package-only Safety repair are present on the live path.

## Where the audit could not tell

No retained free run had a non-empty `subject_span`, so whether a multi-subject anchor
leaks unrelated material into its Ledger is untested. No published free-path run exists,
so the downstream consequence of incomplete Safety replay is untested.

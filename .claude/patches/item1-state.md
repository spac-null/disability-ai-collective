# STRIP item 1 — entity phrase repair, state

## VERDICT 2026-10-02: do not ship. Measured false-positive yield is ZERO.

Measured over the whole retained record on trident (`/srv/data/cripminds-new-engine-v1`,
115 runs with a SAFETY_AUDIT.json). Script: `scratchpad/measure_fragments.py`.

The record holds **207** flagged entity tokens, but **85 of them are
`architect_prose_telemetry`**, which gates nothing — counting those inflates every
proportion. On the paths that actually gate (`audits/*/factual_surface`) there are **25**
flags, and they classify as:

| | n | what the phrase repair does for them |
|---|---|---|
| fragment of a genuinely UNLICENSED phrase | **8** | re-labels a correct refusal. Nothing is fixed. |
| single token (months 3, pronouns 2, demonyms 3, other 3) | **11** | nothing — unless the month / ALL-CAPS / pronoun blanket drops are kept, and those are the unsafe part |
| fragment of a LICENSED phrase | **6** | the only real false positives — see below |

The 8 correct refusals include `Saint Gregory`, `Second World War`, `United States`,
`A United Nations Environment Programme`, `United Kingdom's`, `Two Acoustics`,
`Thirteen Korean`. None appears in its run's approved material.

**THE 6 REAL FALSE POSITIVES, AND WHAT ACTUALLY CAUSED THEM:**
- `Modern`, `Museum` (run …60913T083824Z) — San Francisco Museum of Modern Art, licensed
  by the Ledger. **Already fixed** by passing the Ledger into the audit.
- `CULT`, `DEATH`, `REAL`, `SATANIC` (run …60905T010341Z) — the phrase
  `THE SATANIC DEATH CULT IS REAL` **is in the writer packet**, but in ordinary case. The
  article lifted the source headline in capitals. `_entities` compares case-sensitively,
  so `CULT` never matched the packet's `Cult`. **The cause is CASE, not typography.**
  Dropping every ALL-CAPS token "fixes" this by deleting the whole class, which is why
  `NASA` and `DWP` escaped. A case-folded comparison would fix the four without admitting
  any of the four escapes — that is a different, smaller change than item 1, and it is not
  authorised here.

**A THIRD DEFECT IN MY OWN MEASUREMENT, the one that mattered most.** Seven of the flagged
runs are from 2026-09-05 and have **no `LEDGER.json` at all** — that era's approved
material is `WRITER_PACKET.txt`. Reading only the Ledger left the approved blob EMPTY for
those runs, so every fragment in them read as "unlicensed" vacuously, and my first verdict
("false-positive yield is zero") was wrong. With the era-correct artefact the yield is 6
of 25, all explained above. Empty is not evidence; a missing artefact now reports
`NO_APPROVED_ARTEFACT` rather than being counted as a refusal.

**The verdict stands even so:** the patch as written removes 6 real false positives and
admits `NASA`, `DWP`, `June`, `April`. Parked.

**So the repair fixes nothing that is broken.** Every flag it removes is either a correct
refusal with a confusing label, or a single token that only disappears through the drops
that let `NASA`, `DWP`, `June` and `April` reach publication. Item 1 is parked, not
rescued. The branch and patch stay for the record.

TWO DEFECTS IN MY OWN MEASUREMENT, both found and fixed before the verdict — the honest
version of "verify your measurement script":
1. First run counted `RESEARCH_PACK.json` as approved material. It is raw source, not
   licensed material; it made the four ALL-CAPS headline tokens read as licensed.
2. Second run counted `EDITORIAL_PACKAGE.json` as approved. It holds only generated
   output (title, dek, excerpt, social hook) — matching an audited title against it is
   self-licensing, the same `_pkg_licensed` trap recorded in the project memory.
Approved is the **Ledger**. Both corrections moved flags from "licensed" to "unlicensed",
i.e. against the repair, which is the direction that matters.


**Branch** `fix/entity-phrase-audit-2026-10-02` (worktree under session c586b819 scratchpad)
**Base** 37884dc = origin/main = live. **Patch** `item1-entity-phrase-audit-2026-10-02.patch` (story.py only, as measured).

## What it is
`story._named_entities_only`, called from `factual_surface_audit`. Rejoins capitalised runs
into phrases and drops classes that can never be a name (months, pronouns/function words,
ALL-CAPS typography). Demonyms and adjectives stay hard. Measured 22 flags → 13 on the
retained record. Lowers no gate: the fabricated attributed quote still blocks, now named in
full (`Dr Helen Marsh`) rather than as the fragment `Marsh`.

## Done
- Work moved off the dead session's temp dir; patch saved in-repo; byte-identical.
- Tests in `automation/safety_entity_extraction_test.py`: 8 original + 9 new = 17.
  Every new test asserts its own precondition, so none can pass vacuously.
- Three pre-existing assertions updated from token to `covers()` (phrase rendering).
  One of them — "with the Ledger they are licensed" — was a **false pass**: with phrases,
  `{"Museum"} & {"San Francisco Museum"}` is empty, so an unlicensed phrase read as licensed.
- `main()` switched from a hand-written list to discovery, with the discovered count checked
  against `def test_` declarations (verified: a shadowed test is caught, rc 2).
- Falsification: all 5 guards severed one at a time, all 5 caught.
  M5 (a phrase is licensed by its parts) was initially **undefended** — it only fires when a
  caller passes a non-subtracted set, which the audit never does. Kept and tested, because
  without it a fully licensed phrase handed over raw would be over-flagged (a tightening).

## STOPPED — the adversary caught a real loosening (2026-10-02)

**Do not ship this patch as it stands.** Verified independently, end to end through
`factual_surface_audit`, patched vs clean (`scratchpad/verify_escapes.py`):

| article text | clean | patched |
|---|---|---|
| "The programme was funded by NASA that year." | blocks | **clean** |
| "The scheme was run by the DWP for three years." | blocks | **clean** |
| "The grant was awarded to June for her work." | blocks | **clean** |
| "A letter from April settled the matter." | blocks | **clean** |

An invented acronym institution, and an invented person with a month name, reach
publication. The docstring's "THE GATE IS NOT LOWERED" is false as written.

Cause: both drop-rules are broader than the false positives that motivated them.
`e.isupper()` was aimed at source typography (CULT, DEATH, SATANIC) and deletes every
acronym; `_MONTH_NAMES` was aimed at August/September and deletes June/April as names.
This is `rule-may-not-be-validated-on-its-own-sample`: calibrated on the 22 flags that
produced it, never tested outside that sample. 22 → 13 is real and says nothing about safety.

Also open, from the same review:
- **MAJOR** `new_engine_v1/composition.py:3734` `screens()` removes repair-licensed
  entities by exact token membership. The audit now emits phrases, so a repaired article
  can be HELD where it used to pass. A second caller does change behaviour.
- **MAJOR** The 17 tests all pass with the audit's old behaviour restored — `covers()`
  matches both renderings, so test 4h pins the helper, not the wiring. Needs an assertion
  that the audit emits the phrase and that the dropped classes are clean *through the audit*.
- **MINOR** `e.rstrip("’'s")` is a character-set strip: `Hers`→`Her`, `Ross`→`Ro`.
- **MINOR** `body[:at][-3:]` copies the whole prefix per match — quadratic scan.
- **MINOR** pre-existing: `split("---", 2)[2]` unguarded at story.py:2188.

If this is resumed, the two broad rules need narrower replacements (typography as a RUN of
capitals rather than any capitals; months excused by date context rather than by name),
and either change invalidates the 22→13 measurement and needs re-measuring on the
retained record.

**The suite caught it too — 2 regressions against `current.txt` (28960e35), 132 pass / 28 fail:**

- `safety_matcher_precision_test.py` — the check **"an all-caps acronym in the title is
  still an entity"**, which uses **NASA** as its case, fails. The project had already
  pinned, deliberately and by name, that an unapproved ALL-CAPS acronym must block. The
  `isupper()` rule breaks an existing intentional guarantee, not an accident.
- `sentence_initial_newline_test.py` — "a genuinely unsupported mid-sentence entity is
  still caught" now reports `['Then Zanzibar']` where it expects `Zanzibar`. `Then` is a
  sentence-opening word that is not in `_NOT_A_NAME`, so the phrase builder glues it to
  the name after it. Not a safety hole — it still blocks — but it means the sentence-initial
  trim cannot be a hardcoded word list: every adverb and conjunction that can open a
  sentence (`Then`, `Later`, `However`, `Yesterday`) pollutes the phrase boundary.
  **This defect is in the fragment-rejoining half**, so "keep only the rejoining" is not a
  clean fallback either.

**Reframing worth checking before any resumption.** The fragment class is 9 of the 22 —
the largest share of the 22 → 13. But a fragment reaches the helper only when its token was
NOT in the approved set, i.e. the phrase was genuinely unlicensed in that production run.
If so those were *correct refusals with confusing labels*, and renaming them is cosmetic,
not a false-positive fix — leaving months (3), ALL-CAPS (4), pronouns (2) and `Behind` (1)
as the only true false positives, of which the first two are exactly the unsafe drops.
This is an inference from the call shape, not yet measured against a real run.

## Next
Full suite running on trident (`/tmp/suites_item1.txt` vs `/srv/data/cripminds-qa/current.txt`).
Then: codex adversary (can an invented name escape? did any of the 27 `_entities` callers
change? they must not — the repair is in `factual_surface_audit`), address MAJOR/BLOCKER,
commit + merge --no-ff + push + deploy + regenerate baseline.

Held assets: `/srv/data/cripminds-qa/held-assets/` — restore to the build clone's `assets/`
after the run.

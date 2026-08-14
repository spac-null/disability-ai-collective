# Morning Stabilization — Floor-Plan Forensic + Release Stack Check, 2026-08-14

Zero model calls. No push. No deploy. No semantic changes. Follow-up to the
overnight run (`.claude/overnight-main-run-2026-08-14.md`, Package D).

## 1. Floor-plan article defect — VERIFIED DIRECTLY

`_posts/2026-03-31-the-floor-plan-of-disappearance.md` (67 lines) contains
**genuine duplicated prose**, not a detector false positive. Frontmatter is
normal. The canonical repo file itself contains the duplication (not a
rendering artifact) — confirmed by reading the raw file.

Shape: paragraphs 1-9 (source lines 12-32) are followed by a literal leaked
line, source line 41: **"I need to stop and return the correct article. Let
me apply only the listed fixes precisely."** — then paragraphs 1-9 repeat
almost verbatim (source lines 43-66), with small wording differences (e.g.
"compliant with no one's expectations and compliant with every rule" →
"compliant"; "recording it" → "documenting it"; the first copy has a
`[WCAG standards](url)` markdown link the second copy lacks). Duplication is
**contiguous** (one clean block, not interleaved). A `<figure>` image block
sits between the two halves at the seam (added by a later retrofit, see `## 2`)
— NOT itself duplicated, only the prose is.

## 2. Root cause — traced via git history

`git log --follow` on this file shows only 5 touches ever: the original
2026-03-31 creation commit (`2c6a252`), then three unrelated retrofits
(link injection, body-image injection, figcaption retrofit) and one SEO
keyword regen. **`git show 2c6a252`** proves the duplication AND the leaked
"I need to stop..." sentence were present in the very first commit that ever
created this file — this is a **generation-time bug**, not something a later
edit introduced.

Traced to `automation/orchestrator/llm.py:341-495`, `rewrite_with_opus()` —
the Opus quality-rewrite pass. Its acceptance check, **line 488**:

```python
if rewritten and rewritten.count("---") >= 2 and len(rewritten) > 400:
```

This is dangerously weak: the frontmatter's own two `---` delimiters already
satisfy `count("---") >= 2` regardless of body content, and there is no check
against the response being a duplicated/doubled body, no check for the
response length being wildly larger than the input (this pass's own system
prompt literally says "Your primary tool is SUBTRACTION" — a legitimate
rewrite should never roughly double in length), and no check for leaked
meta-commentary/self-correction text ("I need to stop...").

**This function is still live and still called today** — `generate.py:1026`
calls it unconditionally for any non-Opus-origin draft. The exact same weak
check is unchanged.

Checked the two newer revision functions too (`_opus_targeted_revision`,
`_fable_polish_rewrite`, today's normal call path): both explicitly instruct
"no preamble, no commentary" (stronger than `rewrite_with_opus`'s prompt) and
both run through `_reject_if_unsupported_specifics`, a real deterministic
guard — but that guard only checks for NEW unsupported facts/quotes/numbers
(fabrication), never for duplicated/repeated EXISTING content. A verbatim
repeat of the original draft would introduce zero new facts and would pass
that guard untouched.

**Classification: CURRENT PIPELINE BUG CONFIRMED**, class-wide across all
three revision/rewrite functions in `llm.py` (none validate against response
duplication), most acutely exploitable via `rewrite_with_opus`'s trivial
`count("---")` check. **Not fixed this pass** — the repair requires a policy
judgment (what length-ratio/duplication threshold is safe, false-positive
risk against legitimately long rewrites) exactly like Package A's gate_llm
call, not a one-line deterministic fix. Precise follow-up, not attempted:
add a shared duplication guard (e.g. reject if `len(rewritten) > 1.6 *
len(content)` and/or if a >150-char contiguous substring of `rewritten`
repeats itself) to all three revision acceptance paths, with regression
tests reproducing this exact historical response shape as a fixture.

## 3. Corpus sweep — same failure shape elsewhere?

Reused Package D's existing repetition-shadow data (no new detector built)
plus one supplementary one-off regex sweep. Result: **only
`2026-03-31-the-floor-plan-of-disappearance.md`** shows genuine multi-
paragraph/large-block content duplication anywhere in the 140-article
corpus. Re-inspected the other two "near-duplicate prose" pairs Package D
flagged (`2026-03-10-the-navigation-tax.md`, `2026-03-11-the-prosthetics-
paradox...md`) directly — Package D's own classification heuristic
mis-labeled these as "prose"; both are actually a **different, minor,
cosmetic bug**: an image caption rendered twice — once as the real
`<figcaption>`, once as a redundant `*italic markdown line*` directly below
`</figure>`. A one-off regex sweep for this exact shape found it in **4
articles total** (`2026-03-08-architects-are-designing-buildings-for-the-
wrong-sense.md`, `2026-03-09-the-mapmakers.md`, plus the 2 above) — all from
the same early March batch, consistent with an artifact of the
"retrofit figcaptions into 110 existing articles" commit (`e0907de`) not
removing a pre-existing italic caption line. Real duplication, but cosmetic
(readers see a caption twice, no factual/content bug), historical, and
unrelated to `rewrite_with_opus` — not fixed here, flagged only.

## 4. Pipeline-bug classification

**CURRENT PIPELINE BUG CONFIRMED** (see `## 2`). Module: `automation/
orchestrator/llm.py`, function `rewrite_with_opus`, line 488. Not
introduced by, and not touched by, any of tonight's 9-commit stack.

## 5. G figure-caption false positives — documented only

Confirmed (Package D): 60% of the shadow detector's candidate pairs are
figure-block-vs-figure-block, sharing only boilerplate slug/attribute words,
not editorial content. The 2 pairs re-examined in `## 3` above turned out to
be a real (if cosmetic) duplicate-caption bug, not detector false positives
— refines, doesn't contradict, Package D's original finding. Candidate fix
(exclude `<figure>...</figure>` blocks before paragraph splitting) remains
recorded, not implemented. No threshold change. 2026-08-28 no-promotion date
unchanged.

## 6. Nine-commit stack — verified

`origin/main..HEAD` = 9 commits (`128fda8` .. `eba8290`). Full file list per
commit reviewed: zero B2/CJ-1 semantic files (no `cj1_v3_*`, `cj2_b2_*`,
`calibration/*`, `reader-lab*`), zero RL-002/003 data, zero secrets
(targeted regex scan for key-shaped strings: zero matches). Confirmed default
states: `CJ2_INTEGRATION_MODE` and `L2_TESTIMONY_MODE` both read `os.environ.
get(..., "OFF")` — OFF unless explicitly set. Repetition/essay-adherence/
STOP-risk all confirmed observation-only (structural tests already assert
none of them can reach `_compute_should_block`). The one and only new
production-authority change in the whole stack is the deliberate gate_llm
blocking fix (`7f03ec3`).

## 7. Broad test confirmation

Ran all 16 `automation/*_test.py` files once from current HEAD: **0 failed**,
**454 individual PASS assertions** across 15 files using the PASS-line
convention + snapshot_test.py's 6-article no-drift check (**460 total
checks**). Also imported every principal changed module (`orchestrator.
generate`, `orchestrator.review`, `orchestrator.gate`, `orchestrator.
testimony_l2`, `orchestrator.cj2_shadow`, `cj2_winner_bridge`) and
instantiated `ProductionOrchestrator` directly — clean, no MRO conflicts.

## 8. Release recommendation

**B — STACK READY TO PUSH, BUT DUPLICATED ARTICLE NEEDS SEPARATE CONTENT
REPAIR.** The 9-commit stack itself is clean, tested, and doesn't touch or
worsen the `rewrite_with_opus` bug (which predates it and is equally live
in whatever is currently deployed, with or without this push). Two follow-
ups exist independent of whether this stack ships: (a) editorial repair of
the floor-plan article's content, (b) a dedicated fix for `rewrite_with_
opus`'s duplication-blind acceptance check — real, confirmed, currently
exploitable, but not something this release candidate introduced or can
responsibly fix as a "trivial" edit tonight.

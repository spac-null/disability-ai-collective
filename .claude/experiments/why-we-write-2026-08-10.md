# Experiment record: WHY WE WRITE v1 (2026-08-10)

Archived from `.claude/current-work.md` during the 2026-08-10 checkpoint
cleanup. This is historical provenance — full detail preserved verbatim,
not condensed. For the current operational status of this decision, see
`current-work.md`'s `FROZEN DECISIONS` section; for the scope-correction
that narrows what this experiment is entitled to claim (added after the
Phase 1.5B planning-brief audit), see the end of this file.

---

## NEXT STEP — WHY WE WRITE v1
Done: `llm.py`'s `SYSTEM` string had its `PUBLICATION LENS`/`INTELLECTUAL
FORMATION` founder-biography blocks (lines 130-164, Van Abbemuseum/Exploded
City/bic pen/Tussenruimte etc.) deleted and replaced with the short WHY WE
WRITE doctrine, verbatim as given 2026-08-10 (not the earlier
`project_cripminds_editorial_blueprint.md` wording — this session's text
supersedes it for v1). Reader block and everything else (incl. the
"strong thesis from sentence one" line — thesis-timing is explicitly
untouched this pass) left alone. Isolated commit `01339ce`, one file, exactly
that block replacement — verified via `git show --stat` + `git show`.
`_LENGTHS`/personas.py/thesis/correction rules: untouched, confirmed by diff.

**Provenance incident, caught before it mattered**: first attempt started the
3×3 run against trident's *uncommitted* rsynced copy of the change while HEAD
still pointed at the baseline commit — would have made every sample's
recorded commit hash lie about what code produced it. Caught before any
sample was written (0 files in `probe_out/whywewrite-v1/`), killed the
process, committed+pushed properly, fast-forwarded trident onto `01339ce` via
normal `git pull` (not `sync_to_trident_for_testing.sh` — that script is
rsync-only and explicitly for *pre-commit* live testing, not for getting a
committed experiment onto trident), re-ran `--preflight`, then started the
real run. **Lesson for every future phase_probe experiment**: commit the
prompt change FIRST, verify trident's `git rev-parse HEAD` matches, THEN run
`--run <phase>` — never probe against an uncommitted rsync.

**Run completed** 2026-08-10 ~18:43 CET: `python3 automation/phase_probe.py --run whywewrite-v1 --samples 3` on trident. Output pulled to local `automation/probe_out/whywewrite-v1/`.

**Mechanical acceptance — PASSED**:
- 9/9 files exist, 9/9 `status=ok`, 9/9 `degraded_stages=[]`, all 9 provenance fields say `01339ce`.
- 3 samples per frozen topic (sauna/hiring_tool/curb_cuts).
- Frozen brief hashes match baseline exactly per topic: sauna `b431a42b6179`, hiring_tool `3e0d97833434`, curb_cuts `74caca056f20` — identical in both `probe_out/baseline/metrics.json` and `probe_out/whywewrite-v1/metrics.json`.
- Word counts in range (985-1115, target 1000) comparable to baseline's spread (943-1174).

**Zero-mutation proof — PASSED, method corrected mid-check**: first pass compared live-file `sha256` against the 16:48 daily-cron `.backup()` snapshot and got a MISMATCH — this is a false alarm, not evidence of mutation: SQLite's `Connection.backup()` API (what `backup_state_dbs.py` uses) does not guarantee byte-identical output even for logically-identical content (page/freelist layout can differ between two backup calls of the same unchanged DB). Comparing a live file's raw hash against a `.backup()`-derived copy is comparing two different serializations of potentially the same data — an invalid diff. Corrected method: took a FRESH `.backup()` copy of both DBs immediately after the run and compared THAT hash (same mechanism as the 16:48 backup) against the 16:48 snapshot — **byte-identical for both `disability_findings.db` and `engagement.db`**, which spans the entire run window (16:48 → 18:43) with a valid apples-to-apples comparison. Plus: `git status` unchanged (only the harness's own new `probe_out/whywewrite-v1/` output dir, no tracked-file changes); `_drafts/`, `automation/persona_state/*.json`, `automation/relationships.json` all confirmed via `mtime` unchanged since well before the run started (mtimes hours-to-days old, run window was 18:18-18:43) — mtime-unchanged is a fully valid proof for plain files (unlike the SQLite-backup case above, there's no non-deterministic-serialization trap here). **Lesson for future probe mutation-proofs**: never hash a live SQLite file against a `.backup()`-derived one; either diff two backups taken via the identical mechanism, or diff logical query results (row counts), not raw bytes.

**Doctrine-vocabulary smoke check (not a quality score, just a prompt-leakage detector)**: frequency of disability/perception/knowledge/marginal/reclaim/contribution/mediat/superpower/compensat/inspir/announce-type words across all 9 articles: baseline **29** occurrences, v1 **30** — flat, no lexical outbreak. This only rules out the crudest failure mode (doctrine words leaking verbatim into prose); it says nothing about whether the doctrine was internalized well or badly, or not at all.

**Structured comparison — BOTH AGENTS DONE**:
1. **Implementation-verification — clean single-variable comparison confirmed.** Full `dcca441`→`01339ce` diff (3 commits) categorized: only `llm.py`'s SYSTEM doctrine block is an intended/generation-affecting change; `current-work.md` + committed `probe_out/baseline/*` artifacts are harmless docs/output, not inputs. `generate.py`/`gate.py`/`review.py`/`personas.py`/`config.py` (`_LENGTHS`) byte-identical. Frozen brief hashes and temperature/register/article_type/target_words match exactly. One routing difference found (hiring_tool samples 0/2: baseline made one extra Sonnet call) — traced to `_fable_editorial_review()`'s own content-dependent revise/no-revise verdict reacting to different draft text; the review-gate code itself is unmodified, so this is a downstream effect of the doctrine change, not a second independent variable. **Verdict: yes, a legitimately causal comparison.**
2. **Blind editorial-comparison (strict v2, decoded)** — 18 essays, single anonymous IDs, no group labels, scored independently, decoded after. Aggregated 3 ways per the requested design:

   **OVERALL (n=9 vs 9):** W(hy this writer) 4.67→4.56 (baseline→v1, trivial/noise-level), G(ave me) 4.33→4.44, K(eep reading) 4.11→4.33, D(octrine leak, 0-3, separate axis) **1.78→1.22** (materially lower in v1). Scores are compressed in the 4-5 band on a 5-point scale (n=9), so treat the 0.1-0.2pt W/G/K deltas as noise; the D delta is the one that isn't.

   **BY TOPIC/PERSONA (n=3 vs 3 each):**
   - Siri Sage/sauna: W 5.0=5.0, G 4.33=4.33, K 4.0→4.33, D 2.0→1.67 — essentially stable, small K gain.
   - Zen Circuit/hiring_tool: W 4.33→4.0, G 4.67→4.33, K 4.33=4.33, D 1.67→1.0 — the one persona where v1 is mildly *lower* on W/G (small, n=3, but consistent direction on both quality dims).
   - Maya Flux/curb_cuts: W 4.67=4.67, G **4.0→4.67**, K 4.0→4.33, D 1.67→1.0 — clearest beneficiary; G is the largest single movement in the whole dataset. (This replicates the informal first-pass agent's independent finding on this same topic: baseline generalized into abstract "disabled people"/"the street" language twice, v1 stayed image-anchored — real signal, not agent noise.)

   **WIN/LOSS distribution (composite W+G+K per article, sorted desc):** v1: `15,15,14,14,13,13,12,12,12`. baseline: `15,15,14,13,13,13,12,12,11`. v1's floor is 12 (no article below); baseline's floor is 11 — its single worst article (curb_cuts, an essay that also asserts a claim the essay's own quoted testimony doesn't support — a distinct, non-doctrine defect the agent flagged separately). v1 has a slightly higher floor and a slightly denser top end; the distributions substantially overlap.

   **Lexical smoke test, per-term (not just totals):** disability 13→11, disabled 6→10, marginal 0→1, mediat 1→0, notice/noticed flat, announce 4→3 — no term shows a clean substitution pattern (e.g. no "disability↓ but 'ways of knowing'↑" swap); none of the doctrine's own vocabulary (deficit/contribution/reclamation/superpower/compensation/perceiv-/knowledge/translation) appears in EITHER condition's prose at all. Clean on leakage.

**VERDICT (3-topic, superseded by the 4-persona decision below): was PROVISIONAL KEEP** pending Pixel Nova.

## PIXEL NOVA SUPPLEMENTAL VALIDATION — 4th persona
The canonical 3-topic probe (sauna/Siri, hiring_tool/Zen, curb_cuts/Maya) never
covered Pixel Nova. Rather than rebuild the whole baseline as 4 topics × 3,
added a targeted supplemental set for exactly this one persona.

**Harness change** (`automation/phase_probe.py`): added
`SUPPLEMENTAL_TOPICS` (currently one entry — `museum_labels`, see fixture
correction below). `PROBE_TOPICS` (the original 3) is byte-unchanged — confirmed
via diff, only additions. `ALL_TOPICS_BY_KEY` combines both for lookup. New
`--topic KEY` CLI flag on `--run`/`--freeze-briefs` restricts to one topic;
omitting it (every existing/future call that doesn't pass `--topic`) is
byte-identical in behavior to before this change — verified `snapshot_test.py
--check`: no drift.

**Fixture correction**: the first draft topic (`signage`) was a fabricated
transit-signage story (example.com, invented quotes/details) — caught before
freezing or running anything against it. Problems: (1) violated the
source-grounding principle this whole repair project is trying to
strengthen, and (2) the invented details were themselves essay-ready
evidence (audio-first "primary channel" framing, a conveniently untested
app, no disability groups on the design panel) — writing the test's own
answer into the fixture. It was also too explicitly an accessibility story
on its surface — Pixel is supposed to contribute a Deaf/visual-information
way of seeing, not just detect that an audio-first system excludes people.
Replaced with `museum_labels`: a real, retrieved The Art Newspaper piece
(2026-01-27) on museum wall-label redesign — named institutions/curators/
quotes/data, **zero mention of disability/accessibility in the source
itself**, so any disability content in a generated essay has to come from
Pixel's own persona/canon, not be pre-loaded by the fixture.

*(Later superseded by the Phase 1.5B brief audit: even this real-source
fixture's frozen brief was found to contain a Fable-planning-stage
unsupported claim about Christine Sun Kim — see
`fable-review-roi-2026-08-10.md`. The fixture-correction principle applied
here was correct; the audit that would have caught the brief-level issue
came later, on a different fixture entirely.)*

**Two-code-states problem, solved via git branches, not by testing v1
against itself**: the new `--topic` harness support didn't exist at the
original baseline commit, so "Pixel + old doctrine" can't just mean
"checkout `dcca441`" (that commit lacks the harness). Structure used: a
`pixel-validation/control` branch = current harness/fixture code (byte
identical to `main`) with ONLY `automation/orchestrator/llm.py` reverted to
the pre-`01339ce` doctrine (verified: `git diff main
pixel-validation/control -- automation/phase_probe.py` is empty; the llm.py
diff is the exact reverse of `01339ce`'s). `main` itself is the v1 side
(harness + WHY WE WRITE doctrine, current HEAD). The Fable brief for
`museum_labels` is frozen ONCE (on the control branch) and `git
cherry-pick`ed onto `main` — never re-frozen — so both conditions see a
byte-identical planning brief, same discipline as the 3-topic set.

**Plan**: freeze brief once on `pixel-validation/control` → commit+push →
`--run pixel-validation-baseline --topic museum_labels --samples 3` on that
branch → cherry-pick the brief-file commit onto `main` → `--run
pixel-validation-whywewrite-v1 --topic museum_labels --samples 3` on `main`.
Named `pixel-validation-*`, deliberately NOT folded into
`baseline`/`whywewrite-v1` — supplemental check, not a retroactive rewrite of
the canonical baseline.

**INVALID RUN — caught before blind scoring, discarded, redone.** First
execution delegated to Codex (`mcp__codex__codex`). Codex reported "Frozen
brief: byte-identical on both branches; SHA-256 d8acd04e5...", 3/3 + 3/3
`status=ok`, `degraded_stages=[]` — looked clean. It was NOT: each run's own
`metrics.json` recorded a DIFFERENT `fable_brief_hash` (control `aa8cd607fa2b`
vs v1 `d8acd04e5e7b`), confirmed by diffing the actual `.prompt.txt` sidecars
— completely different register (`clinical` vs `wry`), different EDITOR
BRIEF question, different CORRECTION MOMENT, different RESISTING EXAMPLE.
Root cause (reconstructed from Codex's own narration: "freeze output did not
appear in captured stdout... I moved that exact file temporarily... verified
the checked-in main copy was byte-identical"): the control generation ran
against the FIRST frozen brief; something (likely an unconfirmed re-freeze,
possibly with `--force`, after doubting the first one had worked) then
regenerated a SECOND, different brief before the file was committed — so the
git-committed file (which Codex correctly verified as byte-identical between
the two branches) was never the file the control run had actually consumed.
**Lesson, worth keeping**: artifact equality must be verified from run
PROVENANCE (each run's own recorded consumed-input hash), not from
repository state after the fact — two files can be byte-identical in git
while the two live runs that mattered consumed different content earlier in
the sequence. All 6 samples discarded as invalid (both runs internally
healthy/well-formed, but confounded by two independent variables at once —
doctrine AND planning content/register — so no difference between them can
be attributed to WHY WE WRITE). Preserved as evidence, not data:
`probe_out/pixel-validation-baseline-invalid-mixed-briefs/` and
`probe_out/pixel-validation-whywewrite-v1-invalid-mixed-briefs/`.

**Redo, done directly (no further delegation for this step), stricter
acceptance condition**: re-froze the brief on `pixel-validation/control`,
verified via direct `sha256sum` myself (not trusting stdout) —
`38e10cd5d7b5...` — commit `bfbc017`. Cherry-picked onto `main`, re-verified
hash match — commit `c3306f4`. Trident stayed on the control branch for the
ENTIRE control generation (no checkout/pull of `main` until the control run's
own `metrics.json` exists and all 3 samples are healthy — do not depend on
import timing or filesystem behavior to make an early branch switch safe).
Output directories renamed to avoid ever sharing a canonical name with
invalid data: `pixel-validation-control-r2` /
`pixel-validation-whywewrite-v1-r2`. **Acceptance condition for "same
brief" is now**: control run's OWN `metrics.json.samples[].fable_brief_hash`
== v1 run's OWN `metrics.json.samples[].fable_brief_hash` == direct
`sha256sum` of the one canonical `brief_museum_labels.json` — three-way
match from provenance, not a two-way git-state check. After both runs: a
second full generation-relevant tree comparison (phase_probe.py, the brief
file, personas.py, config.py, generate.py, gate.py, review.py, model-routing
— everything except `llm.py`) between the two final commits, plus the full
mutation proof again, before any blind scoring.

**Redo — ALL CHECKS PASSED, this run is valid.** Control commit `bfbc017`,
V1 commit `a1522c7`. Three-way brief-hash match confirmed from provenance:
control's own `metrics.json` says `38e10cd5d7b5` for all 3 samples, v1's own
`metrics.json` says `38e10cd5d7b5` for all 3 samples, direct `sha256sum` of
the canonical file says `38e10cd5d7b58f72...` — identical. Spot-checked the
actual prompt text this time (not just the hash): `STARTING REGISTER: wry`
and the full `EDITOR BRIEF` question are byte-identical between
`museum_labels-0.prompt.txt` in both output dirs — confirms the hash match
reflects real identical planning content, not another false positive.
3/3 + 3/3 `status=ok`, `degraded_stages=[]`. `git diff bfbc017 a1522c7
--stat` shows exactly 3 changed files: `.claude/current-work.md` (docs,
expected — main accumulated more checkpoint updates than the control
branch), `automation/orchestrator/llm.py` (the doctrine block, expected),
`automation/phase_probe.py` (diffed line-by-line — every change is a
comment/docstring/CLI-help-text string, `signage`→`museum_labels`
housekeeping + the territory-framing comment fix; zero executable
difference). `personas.py`/`config.py`/`generate.py`/`gate.py`/`review.py`
absent from the diff entirely — git's own stat output is the complete file
list, so their absence IS the byte-identity confirmation, not an inference.
Full mutation proof (fresh-backup-vs-16:48-prior-backup, same method):
`disability_findings.db` and `engagement.db` hashes both byte-identical to
the pre-run backup; `news_seeds` 91/880, `findings` 1430, `engagement_metrics`
447, `article_plans` 0, `review_signals` 2 — all unchanged; persona-state
mtimes all predate this run by days; `_drafts/`17 and `assets/`588 file
counts unchanged; git status clean apart from expected new output dirs.
Word counts 1051-1226 (control) / 1025-1148 (v1), comparable to the other
3 topics' spread. Doctrine-vocabulary smoke check: control 8 hits, v1 5 hits
across the 6 essays (low totals both ways, no leakage, consistent with the
3-topic finding). Strict blind scoring done
(6 anonymous IDs, same 4-dimension rubric as the 3-topic set, decode after).
**Pixel supplemental experiment: VALID, decoded, folded into the final
4-persona decision below.**

**Decision logic used (deliberately not a mechanical "Pixel
neutral-or-positive → KEEP" rule — a sign-of-average isn't enough)**: KEEP
if Pixel is positive-or-neutral AND no persona shows a MAJOR regression AND
the 4-persona pattern shows improved give-me/keep-reading without increased
doctrine-announcement. REVISE if the publication-level effect looks useful
but one or two personas reliably flatten/genericize under the shared
doctrine. REJECT only if the doctrine broadly fails to change what writers
notice, or causes systematic disability-philosophy announcement,
genericization, or cross-persona convergence.

## FINAL 4-PERSONA DECISION: KEEP WHY WE WRITE v1

|              | Why writer | Give me | Keep reading | Doctrine leak |
|--------------|:---:|:---:|:---:|:---:|
| Siri (baseline→v1) | 5.0 → 5.0 | 4.33 → 4.33 | 4.0 → 4.33 | 2.0 → 1.67 |
| Zen (baseline→v1)  | 4.33 → 4.0 | 4.67 → 4.33 | 4.33 → 4.33 | 1.67 → 1.0 |
| Maya (baseline→v1) | 4.67 → 4.67 | 4.0 → 4.67 | 4.0 → 4.33 | 1.67 → 1.0 |
| Pixel (baseline→v1)| 4.0 → 4.0 | 3.67 → 4.0 | 3.33 → 3.33 | 2.0 → 1.33 |
| **Overall (n=12→12)** | **4.5 → 4.42** | **4.17 → 4.33** | **3.92 → 4.08** | **1.83 → 1.25** |

Win/loss composite (W+G+K, all 24 essays, sorted desc) — substantially
overlapping distributions: v1 `15,15,14,14,14,13,13,12,12,12,12,8`, baseline
`15,15,14,13,13,13,12,12,12,11,11,10`. v1 has one clear low outlier (Pixel's
M1); baseline has two moderate-low essays (Maya's C4, Pixel's M6) instead —
roughly a wash, no persona's distribution collapses.

**Qualitative line per persona** (what changed in what the writer actually
notices, not just the number):
- **Siri**: no real change in substance — both conditions are anchored in
  genuine acoustic/heat-mapping perception either way; v1 nudges the ending
  slightly toward earned scene over stated insight. Not the doctrine doing
  much work here; her existing VOICE ANCHOR was already carrying this.
- **Zen**: the one persona with a real (if small) dip — confined to
  "why this writer" and "give me," not to doctrine-leak (which improves the
  MOST of any persona, 1.67→1.0) or to reading-drive (flat). No collapse
  into generic disability-tech commentary in either condition. This is the
  concrete data point for the queued persona audit, not a reason to revise
  the shared doctrine now.
- **Maya**: clearest, most consistent gain — v1 essays close on specific
  images (old bay markings still painted on the road) where baseline essays
  twice reached for abstract "disabled people"/"the street" generalizations
  — this is the regression check answering its own question directly: the
  OLD doctrine was more prone to it here, not the new one.
- **Pixel**: mild net positive but the noisiest of the four (n=3, one strong
  v1 essay built on a genuinely embodied image — reading a signed poem's
  loop-and-hold rhythm as the same shape as the Belvedere eye-tracking
  study's viewing pattern — and one weak v1 essay that read as checklist-
  structured). Baseline's worst essay (M6) is also its most doctrine-heavy
  (score 3, the single highest in the whole 24-essay set) AND contains a
  fabricated detail (claims Christine Sun Kim removed physical "mounting
  brackets," not supported by source) — a distinct quality problem, not
  something to attribute to the doctrine either way.

**Why KEEP, applying the decision logic above**: Pixel is net positive, not
merely neutral. No persona shows a MAJOR regression — Zen's is the only
real dip and it's confined to one sub-dimension, with its doctrine-leak
score improving the most of any persona. The doctrine-leak/regression-check
axis — the central risk this whole experiment was built to catch —
improves in ALL FOUR personas, consistently, the single most-replicated
finding in the dataset. No cross-persona convergence: each persona's
strongest essay is built on a distinct compositional mechanism — this
observation concerns the SHAPE of the prose (Siri's heat-gradient
substitution, Zen's stillness-as-concentration misread as disengagement,
Maya's promise-vs-Wednesday cost-accounting move, Pixel's signed-poem
reading rhythm), not evidentiary grounding. **[Corrected 2026-08-10: this
line originally cited "Maya's Antwi cross-cutting access claim" as
evidence of embodied grounding — Phase 1.5B's brief audit later found
Deborah Antwi originates in unsupported Fable planning material, so Antwi
cannot be used as positive evidence that the essay was source-grounded.
The persona-distinctness finding itself still holds — it was always about
the shape of Maya's reasoning move, not about whether Antwi was real —
but the citation needed to change so this line can't be misread as
vouching for Antwi's factual grounding. The same caution applies to the
Christine Sun Kim detail two paragraphs up — it is cited there correctly,
as evidence of a quality PROBLEM in baseline's worst essay, not as
positive proof of grounding.]** WHY WE WRITE is not flattening
personas toward generic disability commentary. Vocabulary smoke test clean
across all 4 topics (no leakage of the doctrine's own words). Implementation
verified clean (single-variable, tree-isolated) for both the 3-topic and
Pixel experiments — the Pixel one only after catching and fixing a real
mixed-brief bug, which is itself now a recorded methodology lesson.

**FROZEN as of this decision**: `automation/orchestrator/llm.py`'s WHY WE
WRITE doctrine (commit `01339ce`) is the shared publication doctrine going
forward. Do not reopen this decision by drift — a future session finding
Zen Circuit weak should go to the Persona Architecture Audit (1.5), not
back to relitigating WHY WE WRITE.

## SCOPE CORRECTION (added 2026-08-10, after Phase 1.5B's planning-brief audit)
Does NOT reopen the KEEP decision above — narrows what it's entitled to
claim. The Phase 1.5B brief audit (see `fable-review-roi-2026-08-10.md`)
found all 4 of these same frozen briefs (the ones this experiment's
baseline/v1 comparison used) contain Fable-planning-stage unsupported
evidence in `resisting_example`/`correction_moment`. This does NOT
invalidate the doctrine comparison — baseline and v1 consumed the
IDENTICAL contaminated brief per topic, so the doctrine variable stayed
isolated and the observed doctrine-leak reduction is still real. What it
narrows is the claim this experiment is entitled to make: **not** "WHY WE
WRITE works under the final intended CripMinds pipeline" — **only** "WHY
WE WRITE improved or preserved the four personas under the then-current
planning architecture," which is now known to include unsupported-evidence
contamination. Do not rerun the full 12+12 experiment over this. Once
Phase 1.6 (source-grounding hardening) lands, run a small smoke
confirmation instead — one clean, verifiably-grounded source × two
personas, or four clean single samples — to confirm the doctrine doesn't
interact badly with a much less synthetic, properly-sourced plan. That is
verification of an existing decision, not reopening it.

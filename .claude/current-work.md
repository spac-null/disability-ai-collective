# Current Work Checkpoint

Update this after every meaningful commit, not at the end of a session. A
fresh session should need this file (~500 words), not conversation
archaeology.

## GOAL
Article-quality repair blueprint — rebuild cripminds' article-generation
prompt system around its true purpose (see project memory
`project_cripminds_editorial_blueprint.md` / `project_cripminds_true_purpose.md`),
not as ten isolated style fixes.

## ACTIVE PHASE
**Roadmap** (do not reorder without a stated reason):

- **DONE** — Phase 0 (reliability + canonical baseline).
- **DONE** — Phase 1, WHY WE WRITE → **KEEP** (`## FINAL 4-PERSONA DECISION`
  below).
- **DONE** — Phase 1.5A, Persona Architecture Audit (design/audit only,
  no code changes, no generations) → `.claude/persona-architecture-audit.md`.
- **NEXT** — Phase 1.5B, Fable model-seat ROI A/B (`## MODEL-SEAT ROI
  EXPERIMENT` below) — Fable review+Fable rewrite vs Fable review+Opus
  rewrite. Not started. Sequenced before Phase 2 deliberately: if Fable can
  be cheaply removed from the rewrite seat, every later experiment
  (including Phase 2 and Phase 3's testing loops) gets cheaper.
- **THEN** — Phase 2, brevity + evidence budget + testimony. Sequenced
  before Phase 3 deliberately (per the original locked order — this insert
  does NOT move Phase 2 after Phase 3): article length/evidence-overload/
  testimony-handling were identified as major structural variables before
  the persona-architecture question existed; fixing those first means
  Phase 3's persona experiment gets evaluated inside the cleaner article
  architecture, not against a prompt system already slated for
  dismantling.
- **THEN** — Phase 3, persona architecture implementation (perceptual
  engines, motives, soft affinities, remove hard territories/prohibitions —
  informed by 1.5A's findings). Not started.
- **THEN** — same-source/four-persona probe (validates whatever Phase 3
  produces).
- **THEN** — Phases 4-8 (correction/repetition/readability/ending/final
  audit), original blueprint order, unaffected by this insert.

## HEAD / PROVENANCE
- **WHY WE WRITE doctrine commit**: `01339ce` — the SYSTEM-prompt swap in
  `automation/orchestrator/llm.py`, now the permanent/frozen shared doctrine.
- **3-topic experiment (sauna/hiring_tool/curb_cuts)**: generated from
  `01339ce` exactly (verified in each sample's own `metrics.json`).
- **Pixel Nova supplemental (museum_labels)**: control from commit `bfbc017`
  (branch `pixel-validation/control` — harness identical to `main`, only
  `llm.py` reverted to pre-`01339ce`), v1 from commit `a1522c7` (on `main`).
  Both verified byte-identical trees except `llm.py`; both consumed the
  identical frozen Fable brief (verified from run provenance, not repo
  state — see the INVALID RUN section below for why that distinction
  mattered here).
- **CURRENT MAIN HEAD**: whatever `git rev-parse HEAD` says after the latest
  checkpoint commit — always AHEAD of `01339ce`/`a1522c7` by docs-only
  commits. A session seeing a different HEAD than what's cited above is
  not a bug; those commits are what generated the data, checkpoint commits
  layer on top without touching generation code.

## PHASE 0 — DONE
- 0B fail-loud/degraded-run handling; 0C plan-follow N/A invariant (both `e4922e6`)
- `automation/engagement.db` incident: fully recovered/closed (`4ffb4c9`, `a37b169`) — full report `.claude/2026-08-10-engagement-db-incident.md`
- `automation/phase_probe.py` built: dry-run harness, `--freeze-briefs`, `--preflight`, `--retry-failed`, zero production-state mutation (proven repeatedly, including under real provider failure)
- **Canonical baseline frozen**: `automation/probe_out/baseline/` — 9/9 `status=ok`, 9/9 `degraded_stages=[]`, 3 topics (sauna/Siri Sage, hiring_tool/Zen Circuit, curb_cuts/Maya Flux) × 3 samples, same frozen brief hash per topic, commit `dcca441`, temperature 0.9, register wry, article_type essay, target 1000 words. Post-batch zero-mutation proof passed. An earlier attempt (`baseline-attempt-1/`, 2 ok + 7 rejected_degraded) is preserved as Phase 0B regression evidence, NOT part of the baseline — real mid-run outage (OpenRouter billing limit + a separate CLIProxyAPI internal fault, both fixed; see INFRASTRUCTURE BACKLOG).

## NEXT STEP — WHY WE WRITE v1 (in progress, do not touch mid-run)
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

**Run completed** 2026-08-10 ~18:43 CET: `python3 automation/phase_probe.py --run whywewrite-v1 --samples 3` on trident. Output pulled to local `automation/probe_out/whywewrite-v1/` (not yet committed — pending the KEEP/REVISE/REJECT decision below; commit it alongside that decision, not before).

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

**VERDICT (3-topic, superseded by the 4-persona decision below): was
PROVISIONAL KEEP** pending Pixel Nova — see `## FINAL 4-PERSONA DECISION`
further down for the resolved KEEP.

**NEXT: Pixel Nova supplemental validation (in progress)** — see below.

## PIXEL NOVA SUPPLEMENTAL VALIDATION — 4th persona, in progress
The canonical 3-topic probe (sauna/Siri, hiring_tool/Zen, curb_cuts/Maya) never
covered Pixel Nova. Rather than rebuild the whole baseline as 4 topics × 3,
added a targeted supplemental set for exactly this one persona.

**Harness change** (`automation/phase_probe.py`, not yet committed): added
`SUPPLEMENTAL_TOPICS` (currently one entry — `signage`, Pixel Nova, a fixture
about a transit authority replacing tactile/Braille platform signage with an
audio-first "adaptive" digital display system, equivalent info gated behind
an untested phone app — chosen to sit in Pixel's actual territory
(legibility/information-architecture/interfaces) without being a softball;
a generic tech columnist could plausibly write "AI signage raises
accessibility questions" — the test is whether WHY WE WRITE makes Pixel
supply something a generic take wouldn't, or pushes her toward exactly that
generic take). `PROBE_TOPICS` (the original 3) is byte-unchanged — confirmed
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
3-topic finding). Output pulled locally to `probe_out/pixel-validation-
control-r2/` and `probe_out/pixel-validation-whywewrite-v1-r2/` (not yet
committed — pending the blind-scoring decode). Strict blind scoring done
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
strongest essay is grounded in a distinct, genuinely embodied perceptual
mechanism (Siri's heat-gradient substitution, Zen's stillness-as-
concentration misread as disengagement, Maya's Antwi cross-cutting access
claim, Pixel's signed-poem reading rhythm) — WHY WE WRITE is not flattening
personas toward generic disability commentary. Vocabulary smoke test clean
across all 4 topics (no leakage of the doctrine's own words). Implementation
verified clean (single-variable, tree-isolated) for both the 3-topic and
Pixel experiments — the Pixel one only after catching and fixing a real
mixed-brief bug, which is itself now a recorded methodology lesson.

**FROZEN as of this decision**: `automation/orchestrator/llm.py`'s WHY WE
WRITE doctrine (commit `01339ce`) is the shared publication doctrine going
forward. Do not reopen this decision by drift — a future session finding
Zen Circuit weak should go to the queued Persona Architecture Audit (1.5),
not back to relitigating WHY WE WRITE.

**Next, in order** (do not mix these together — each is its own controlled
experiment): (1) Persona Architecture Audit (1.5) — design/audit only, see
below. (2) Fable model-seat ROI experiment (A vs B: Fable-review+Fable-
rewrite vs Fable-review+Opus-rewrite) — queued section below. Both were
explicitly waiting on this decision landing.

## PERSONA ARCHITECTURE / TERRITORY AUDIT — Phase 1.5A DONE (design/audit
only — no `personas.py`/`generate.py` edits, no generations, per this
document; implementation is Phase 3, not started)

**Historical persona territories are hypotheses, not canon.** Pixel's
museum-label validation tested WHY WE WRITE under Pixel's existing
configuration; it did not establish museum labels/information architecture
as Pixel-owned territory. Future architecture replaces hard territories
with perceptual engines + soft affinities. A source belongs to whichever
persona can reveal the strongest evidenced hidden mechanism through their
particular way of perceiving.

Full audit: **`.claude/persona-architecture-audit.md`** — six-category
matrix (core person / perceptual engine / motive / affinity / risk /
texture) for all four personas, extracted from `persona_canon/*.md` +
`personas.py` + `generate.py`'s routing logic. Headline findings, confirmed
by direct code read (not inference):
1. Siri Sage's VOICE ANCHOR (`personas.py`) contains a literal ownership
   sentence — "Not spatial legibility. Not wayfinding systems. Not
   information architecture. Those belong to Pixel Nova." **Still present
   in code as of this audit — an earlier note in this file calling this
   bug "found and fixed" was wrong; it was only found. Not fixed here
   either (Phase 3 work) — corrected so a future session doesn't assume
   it's already handled.**
2. `generate.py`'s global FORBIDDEN DEFAULTS (bans ramp/curb-cut/grab-rail/
   tactile-paving/accessible-toilet/lift as "the central concrete example")
   collides almost entirely with Maya Flux's canon — her wound, fixed
   beliefs, and evidentiary vocabulary are built on exactly those objects.
   **A different bug CLASS than #1** — not an ownership claim, a
   cross-persona SUPPRESSION rule that happens to disable one persona's
   most load-bearing material. Phase 3 needs a different fix for each
   class, not one rewrite (see audit doc's taxonomy section).
3. `generate.py`'s topic→persona routing (lines 161-168) is a hard
   keyword map (art/design/visual→Pixel, tech/science/system→Zen,
   culture/social/entertainment→Siri, else→Maya) — topic assignment, not
   affinity: the second OWNERSHIP mechanism, alongside #1. Maya is the
   default/else bucket, and has the LOWEST 60-day published count of the
   four (Zen 14, Pixel 9, Siri 7, Maya 4, per `generate.py`'s own comment)
   — **an interesting discrepancy, not a confirmed causal chain**: static
   code can't tell us whether she's routed often and lost downstream, or
   routed rarely because most real sources happen to match an art/tech/
   culture keyword. Cheap diagnostic identified, not yet run: count persona
   assignment at every funnel stage (keyword-preferred → Fable-preferred →
   `_balance_agent` final → generated → published) before attributing the
   low count to #2 or to Fable-override behavior specifically.
4. All four personas are missing an explicit MOTIVE sentence ("what I
   want to give the reader") — confirmed absent in all four
   `prompt_block`s, not persona-specific.
5. Zen Circuit (scrutinized hardest per the WHY WE WRITE data — her
   "why writer"/"give me" scores dipped even as her doctrine-leak improved
   the MOST of any persona) has real perceptual material in her canon
   (pattern-recognition-as-expertise, diagnostic-authority-as-power) but it
   stays list-shaped/argued rather than condensed into one stated
   question the way Siri's is, and her ONLY dedicated brief section
   (`WRITING VOICE`) is entirely structural (how to write) with nothing
   about what she's for. Candidate explanation for the dip, not a
   diagnosis — the shared publication doctrine has less to attach to when
   a persona's own engine isn't load-bearing in the brief. **Do not revise
   WHY WE WRITE over this — the fix, if confirmed, belongs in Phase 3.**
6. Every persona-pair relationship in canon already states a distinct,
   self-aware axis of disagreement (not redundant on paper). Whether that
   holds in actual generated prose is exactly what the future same-source/
   four-persona probe tests — correctly deferred, not answerable from
   static text.

**The four personas should NOT own subject territories.** Existing
territory labels are historical/model-generated assumptions and must be
audited, not treated as settled. Target architecture for the eventual
persona-prompt rewrite (NOT now):
- **CORE PERSON** — biography/wound/desire, where causally useful.
- **PERCEPTUAL ENGINE** — what this mind notices/questions before others do.
- **MOTIVE** — what they want to recover/bring back/give the reader.
- **AFFINITIES** — soft routing priors only; never ownership boundaries.
- **RISKS** — the cliché/groove this persona tends to collapse into.
- **TEXTURE** — habits/tics/passions, used optionally, never checklist
  behavior (test for wound/passion/tic: does it generate perception, or is
  it an obligatory anecdote every essay reaches for? Keep the former, cut
  the latter).

A persona succeeds when their perceptual engine makes the SAME WORLD OBJECT
become a different thing, not merely when they write competently inside an
assigned topic category. No TERRITORY category survives as a hard field —
"territory" becomes "affinity."

**Revised repair sequence** (supersedes the plain 9/10-step list further
below in scope, not in order — Phase numbers below refer to the FINAL
LOCKED ORDER in project memory `project_cripminds_editorial_blueprint.md`):
0. Reliability/baseline — DONE.
1. WHY WE WRITE — DONE, KEEP (see `## FINAL 4-PERSONA DECISION`).
1.5A. **Persona architecture audit — DONE, design/audit only, no code.**
   → `.claude/persona-architecture-audit.md`.
1.5B. **Fable model-seat ROI A/B — NEXT.** See `## MODEL-SEAT ROI
   EXPERIMENT` below. Sequenced here (before Phase 2) because a cheap win
   here reduces the cost of every later experiment.
2. Brevity + evidence budget + testimony (unchanged from prior plan) —
   sequenced BEFORE Phase 3 deliberately, not after: evaluate Phase 3's
   persona rewrite inside the cleaner article architecture, not against a
   prompt system already slated for dismantling.
3. **Persona motive + perceptual engine + soft affinities + removal of hard
   territorial ownership** (broadened from the prior "persona motive +
   opening identity" — this is where the actual `personas.py` code change
   belongs, informed by 1.5A's audit), followed by the same-source/
   four-persona probe to validate it.
4-8. Correction discipline / repetition / readability / ending / final
   anti-cliché audit — unchanged from prior plan.

**The real territory experiment (future, after 1.5, separate from anything
running now)**: not "one persona + one suitable topic, is v1 better" (that's
what the Pixel supplemental test already does) but "same real-world object,
four different minds — what does each notice?" Give ONE genuinely rich,
non-disability source to all four personas, deliberately chosen OUTSIDE
their assumed territories (a supermarket pricing system, a school timetable,
a heatwave policy, a queue, a sports stadium — NOT "Pixel→interface,
Maya→architecture, Zen→employment algorithm, Siri→sensory environment",
which would just confirm the taxonomy already assumed). Score: WHAT DID THIS
MIND NOTICE (a mechanism the other three missed?), CATEGORY JUMP (did their
lens change what KIND of thing the source turned out to be?), IRREDUCIBILITY
(could another persona's name be swapped onto the essay without
fundamentally changing it?), OVERLAP (did two+ personas converge on the same
mechanism?), LORE LEAKAGE (did the writer just import their disability
biography into an unrelated story instead of actually perceiving something?).
If a persona is only distinctive inside their assumed topic, they don't yet
have a perceptual engine — they have a beat.

**Downstream consequence for CJ-2** (not scheduled now, recorded so it isn't
lost): routing should stop being "which persona is appropriate for this
topic" and become "what does each persona's perceptual engine expose about
this source, then which reframe is strongest/least generic/best evidenced"
— competitive reframing, not topic assignment. Affinities survive only as
small priors (e.g. "+small prior" for Pixel on information-form stories),
never as a gate — a strong Siri reframe of a software-interface story should
beat a mediocre Pixel reframe of the same story.

**Why this strengthens the candidate explanation for Zen Circuit's
WHY-WE-WRITE softness**: see finding #5. Two levels, kept distinct — the
ARCHITECTURAL ASYMMETRY is confirmed by direct code read (implicit engine,
missing motive, structure-only `WRITING VOICE` section, unlike Siri's
explicit VOICE ANCHOR). Its CAUSAL ROLE in Zen's score dip is NOT
confirmed — that requires either the Phase 3 rewrite + re-test, or the
same-source/four-persona probe showing Zen specifically underperforms.
**Do not repair Zen by revising WHY WE WRITE either way** — if the
hypothesis holds, the fix is persona-level (Phase 3), not doctrine-level.

**Explicit ordering constraint**: do not change `personas.py`, broaden
Pixel's prompt, or modify any persona rule before the Pixel control/v1
generations (in flight) are scored — doing so now would test "WHY WE WRITE +
a new Pixel concept" simultaneously and destroy the causal result for both
questions at once.

## DO NOT TOUCH YET (until their own dedicated experiment)
`_LENGTHS`/evidence-budget restructure, testimony extraction/weighting,
Siri Sage's VOICE ANCHOR / any other persona prompt, thesis-timing /
correction-discipline rules.

## MODEL-SEAT ROI EXPERIMENT (Phase 1.5B) — PIVOTED, harness built, not yet run
Originally recorded 2026-08-10 as "Fable review + Fable rewrite vs Fable
review + Opus rewrite" (see git history of this section for the original
A/B/C framing). **Pivoted the same day, before spending anything**, after
three cheap checks — see `## INFRASTRUCTURE BACKLOG` above for the
production-outage finding surfaced by the same investigation:

1. `probe_out/*.md` files are FINAL pipeline output (post-review/rewrite/
   gate) — `_run_one_sample()` only reads `drafts_dir` AFTER
   `_run_production_automation_locked()` returns. They are NOT raw
   pre-review drafts; reusing them as fresh review input would have been a
   biased test (already-polished text → mostly pass).
2. `_fable_polish_rewrite` already passes `prefer_opus=True` (commit
   `26f5e77`, landed 12:19 today, for a documented truncation-risk reason
   unrelated to this experiment). Across every real+probe sample logged in
   `automation.log` since, Opus won the rewrite on the FIRST attempt 100%
   of the time (0/36 Fable fallback). The rewrite seat is not currently a
   meaningful cost center to A/B test — production already made this call,
   just not for a quality-ROI reason.
3. Fable's REVIEW call fires on every real production run and has NEVER
   once returned `publish_as_is` (0/39 logged, real or probe, spanning
   2026-08-09 through today). This is the actual recurring, load-bearing,
   expensive seat — and the 0/39 pattern is itself a hypothesis worth
   testing (structural over-editing bias, vs. drafts genuinely always
   needing work), not assumed proof of either.

**Corrected experiment**: does Fable's editorial JUDGMENT (not its prose
execution) earn its price, or is Opus just as good at deciding what's
wrong with a draft? Design (locked):
```
ONE raw Opus draft, captured live (never reused from probe_out)
                |
         /              \
    Fable review      Opus review
 (byte-identical prompt/schema, forced model, no fallback chain)
         |                  |
    verdict+notes      verdict+notes
         |                  |
 if revise: Opus executes   if revise: Opus executes
 (same executor template,   (same executor template,
  authorship-agnostic)       authorship-agnostic)
 else: final = raw          else: final = raw
```
`publish_as_is` is a LEGITIMATE, first-class outcome for either branch —
NOT a skip condition (the decision not to intervene is part of the seat
being tested). No downstream rewrite/gate runs after the branch point —
the harness aborts the real pipeline immediately after capturing the raw
draft (a sentinel exception from the review-capture stub), so no extra
real spend happens beyond the draft-generation call itself.

**8 cases planned**: 2 raw drafts each for Siri/sauna, Zen/hiring_tool,
Maya/curb_cuts, Pixel/museum_labels — the 4 already-frozen topics/briefs,
no new topic work needed.

**Harness built**: `automation/fable_review_roi_probe.py`. `--preflight`
passes locally (frozen briefs readable, zero API calls). Per case, persists
`raw_draft.md`, `review_fable.json`, `review_opus.json`,
`final_from_fable_review.md`, `final_from_opus_review.md`, `provenance.json`
(models, prompt hash, draft hash, review-response hashes, token
usage/latency/errors for every call — `cost_usd` deliberately left `null`,
no verified per-token pricing for the Fable alias, not fabricated). Reuses
`snapshot_test.py`'s `_isolate_paths`/`_patch_methods` exactly like
`phase_probe.py` — zero production-state mutation by construction. Draft
generation is temperature-pinned at 0.9 (matching every other probe this
session), via the same `_call_openai_compat_api` patch pattern.

**Pre-run corrections (before spending anything), then RUN — 8/8 cases
valid.** Three checks before `--run`, all fixed then verified clean:
1. Parser failure semantics: malformed JSON/API errors/missing-or-invalid
   verdict now return distinct `api_error`/`parse_error`/`invalid_verdict`
   status, never silently collapsed into `publish_as_is` or `revise` (the
   0/39 finding must not be contaminated by parser artifacts). Same parser
   for both models. Downstream execution gated strictly on `status=="ok"`.
2. Explicit sampling settings, both recorded in `provenance.json`:
   `REVIEW_TEMPERATURE=None` (matches production's own unset-default
   convention for the real review seat — deliberate, not accidental,
   applied identically to both forced review calls); `EXECUTOR_TEMPERATURE
   =0.2` (deliberately pinned low so final-output differences trace to
   notes content, not independent Opus sampling noise). Also fixed a real
   `max_tokens` asymmetry (1600 vs 1200) to match production's real 3200
   review budget for both models.
3. Mocked offline branch test (`--test-mock`, zero network calls): 21/21
   checks pass — `publish_as_is` byte-identical final output, executor
   called exactly once per case, all 6 artifacts present, and (the
   parser-semantics scenario) simulated API/parse failures produce
   distinct non-executing statuses rather than silent defaults.

**Run completed, commit `b99d379`, mechanical acceptance passed**: trident
stayed on `b99d379` the entire run (verified `git rev-parse HEAD` + `git
status --short` before pulling results — only expected pre-existing
untracked leftovers). Exactly 8 cases (2 per persona × 4 personas), all 6
artifacts present per case, `review_prompt_hash` confirms byte-identical
review prompts sent to both models per case. Full mutation proof clean
(same backup-vs-backup DB method as every prior check this session —
`disability_findings.db`/`engagement.db` hashes identical to the pre-run
backup, persona-state mtimes all predate the run, `_drafts/`(17)/`assets/`
(588) counts unchanged). Run-level `run_manifest.json` added recording the
generating commit (provenance.json didn't carry it per-case yet — also
fixed the harness itself, `_git_commit_hash()` now threaded into every
future run's per-case provenance).

**Headline result before any blind judging**: all 8 cases `status=="ok"`
for BOTH models, zero execution failures — every case valid for both
comparisons, nothing to exclude. **Fable: revise 8/8. Opus: revise 8/8.**
Both models, independently, request revision on every single case under
these conditions. This is informative against the 0/39 production
`publish_as_is` pattern: Opus showing the identical intervention rate
leans toward "these raw drafts genuinely have real issues most of the
time" rather than "Fable specifically has a bias" — but does NOT rule out
both models sharing one, or Fable's notes being more/less justified than
Opus's even at equal intervention rates. Exactly why the blind
review-quality judging (below) still has to happen before concluding
either way — the revise-rate alone answers nothing about the FINANCIALLY
significant question (does Fable's judgment earn its price).

**Next**: two independent blind evaluations, not yet run (see design
below, unchanged from the pre-run plan) — review quality (one anonymous
review at a time against the raw draft, same-problem classification only
after both are scored) and result quality (RAW/X/Y, no reviewer
attribution).

**Two separate evaluations once cases exist** (do not conflate):
1. **Review quality** (blind the reviewer identity, judge against the raw
   draft): problem validity, importance (real defect vs. nitpick),
   coverage of the most important structural issue, specificity/
   actionability, false-positive pressure (demanding a rewrite of
   something already working) — this last axis is where the 0/39
   `publish_as_is` finding becomes testable.
2. **Result quality** (blind RAW / FINAL-A / FINAL-B, no reviewer
   attribution): better than raw? worse than raw? was the real structural
   problem solved? collateral damage? persona preserved? unsupported
   claims introduced? Also classify, per case: did Fable and Opus
   independently flag the SAME underlying problem (same / partially
   overlapping / different-but-both-valid / one-only-valid / both weak) —
   if they converge repeatedly, paying Fable's premium for judgment may be
   unnecessary even where Fable phrases the note better.

**Intervention-rate tracking, first-class**: Fable revise-rate vs Opus
revise-rate across the 8 cases, then independently: of the revisions each
one requested, how many were genuinely justified vs marginal vs false
positive (per blind result-quality judging). If Fable requests revision
8/8 and blind judging finds several raw drafts were already as good or
better, that's an editorial intervention bias, not just an expensive model.
If Fable requests revision 8/8 and all eight demonstrably improve, the
0/39 production pattern may simply mean these drafts consistently need
editorial work — a different, equally real finding.

**Explicitly separate from this experiment, still untested**: the
planning/brief seat (frozen briefs are held constant by design — no
finding here generalizes to "should Fable write the plan").

## INFRASTRUCTURE BACKLOG (not blocking Phase 1)
CLIProxyAPI's dead Codex/ChatGPT-Plus OAuth account (expired 2026-07-20)
can apparently poison routing for ALL requests, not just its own — a
`systemctl --user restart cliproxyapi` fixed it same-day. Fix later:
remove/refresh the dead account, or file upstream that per-account refresh
failures shouldn't affect other accounts.

**Real production article shipped degraded on 2026-08-10 09:03:24** (found
while checking Phase 1.5B's premises against `automation.log` on trident,
not investigated further — do not fix now, just don't lose it). At that
exact timestamp: `_fable_editorial_review` returned `revise` (3 notes), then
ALL FOUR rewrite attempts failed with `HTTP 403: Forbidden`
(Fable/CLIProxy, Opus/CLIProxy, Fable/OpenRouter-direct, Opus/OpenRouter-
direct — root cause logged moments later: `"Key limit exceeded (monthly
limit)"` on the OpenRouter key), `_opus_targeted_revision`'s own fallback
also failed (`HTTP 500`), so the article shipped completely unrevised
despite Fable having flagged 3 real notes. In the SAME run: accessibility
check failed (403), editorial check failed (500), pre-commit gate's own LLM
call failed (403) though the gate then logged `PASS (FRE=70.2,
violations=2)` on deterministic checks alone, and image generation failed
outright (`"Key limit exceeded (monthly limit)"` again) — no images on
today's article. **Open question, not answered here**: was this run
stamped `pipeline_degraded` in frontmatter, and if so with which stage(s)?
Phase 0B's `_degraded_stages` tracking (per its own design) should have
appended `editorial_revision` (verdict was revise, notes existed, content
came back byte-identical to pre-revision — exactly the condition
`_should_block`/degradation-stamping checks for). But image-generation
failure does NOT appear to be tracked by `_degraded_stages` at all from a
read of `generate.py`'s Step 3b logic — if true, two separate user-visible
failures (no editorial revision AND no images) may be collapsing into at
most one stamped degraded stage, undercounting the real failure surface.
Do not fix or investigate further now — record the exact timestamp
(2026-08-10 09:03:24) so this doesn't get lost, and check it against the
actual published article's frontmatter + `_degraded_stages` code path when
someone next has reliability-focused capacity.

## DECISION LEDGER (settled, do not reopen)
- Production `temperature` stays unset/`None`; only the probe pins it (0.9).
- Baseline = 3 topics × 3 samples, same fixed type/register/length — format variation is a separate future probe.
- Testimony: extraction/preservation ships with the block-budget work; weighted *selection* stays shadow-only.
- Repetition judge (Phase 5) and ending judge (Phase 7): shadow-only first, backtested, never auto-block/auto-rewrite until real false-positive data justifies it.
- Rest of cripminds' backlog (judge-panel generation, persona evolution, shadow-check promotion, CJ-2, Stage B/D-E) stays in `.claude/audience-engagement-tasklist.md`, untouched.
- `engagement.db`/`disability_findings.db` living inside the repo checkout is a known, mitigated risk (safe sync wrapper + daily backups); moving them out is deferred infrastructure hardening.
- `--retry-failed` exists as general phase_probe infrastructure but was deliberately NOT used to patch baseline-attempt-1 — a contiguous clean run was required instead, to avoid mixing external-condition windows in data meant to detect subtle writing differences.

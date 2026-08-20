# Publication Selection / Cadence — Read-Only Audit

Prompted by an owner correction. **Read-only: no code, cron, capture or production change.**
Phase-2 passive capture left running and enabled throughout.

## The owner's recollection is correct

Generate candidates regularly; publish **one** best eligible article roughly **every two
days**, chosen from candidates of roughly the **last seven days**. That is exactly what the
code does. Daily generation is not daily publication.

## The mechanism

**`automation/publish_best.py`**, run by cron on Trident:

```
0 8 */2 * *  cd /srv/data/hermes/workspace/disability-ai-collective
             && git pull origin main && python3 automation/publish_best.py
```

Generation is a separate job: `0 9 * * *  cripminds-daily.sh article`.

### Cadence — a precision the docstring rounds off

`*/2` in the **day-of-month** field steps from the field's first legal value, which is `1` —
so it fires on **odd days: 1, 3, 5 … 31**, not "every 48 hours".

Confirmed against the actual promotion commits: 08-01, 08-03, 08-05, 08-07, 08-09, 08-11,
08-13, 08-15, 08-17, 08-19 — every one an odd day.

Consequence worth noting: across a 31-day month the boundary runs land on the 31st and then
the 1st — **two consecutive days**. In a 30-day month the boundary gap is a normal 2 days. So
the cadence is "approximately every two days" with one tighter interval per 31-day month.

### Selection, as pseudo-expression

```
candidate_window = drafts in _drafts/*.md where (now - draft_date).days < 7      # AGE_WINDOW_DAYS
expired          = drafts where (now - draft_date).days >= 7                      -> archived to _drafts/_archive/

eligible = candidate_window AND
           fm.fact_check_status == "verified"                 # explicit literal; missing/typo/blocked all fail
           AND int(fm.publication_safety_version or 0) >= 1    # REQUIRED_SAFETY_VERSION

score = draft_score(default 7.0) * 0.6
      + topic_freshness * 10 * 0.25      # 1.0 if no published title in 14d shares >=2 keywords, else 0.5
      + persona_rotation * 10 * 0.15     # 0.0 if same as most recent post; 0.5 if in last 2;
                                         # 0.75 if in last 5 but not last 2; 1.0 otherwise
      + min(publish_attempts * 0.15, 0.6)  # aging bonus for repeatedly-losing drafts

rank_order = score DESC
publish    = first(rank_order)   # exactly one, or none
```

Max per run: **one**. When nothing qualifies it prints *"No scoreable drafts in the last 7
days"*, publishes nothing, and still archives expired drafts (which is why archive-only
commits exist).

### What "best" currently means — and mostly does not

On paper the editorial score dominates at 60%. In practice it is nearly always the constant
`DEFAULT_SCORE = 7.0`: `draft_score` is only written when the conditional Opus editorial pass
fires. **Live evidence: 2 of 7 current drafts carry it.** The script's own docstring flags
this ("this term is DEFAULT_SCORE for the large majority of real candidates, so
freshness/rotation/aging usually do the actual deciding despite the 60% weight on paper").

So "best" in practice ≈ **topic freshness + persona rotation + aging**, not editorial quality.

---

## Why nothing has published — and a correction to Phase 0

### Correction first

Phase 0 recorded *"nothing published since 2026-08-11"*. That is **wrong**, and it was my
error: it read filenames. A draft keeps its **write-date filename** and `set_publish_date`
rewrites only the front-matter `date:`. The file `_posts/2026-08-11-reached-by-boat-or-plane.md`
carries `date: 2026-08-15`.

**The last actual publication was 2026-08-15**, in commit `50c1a2d`. The gap is 5 days and
two missed cycles, not 9 days.

### Promotion runs since the last publication

| Date | Ran? | Published | Archived | Evidence |
|---|---|---|---|---|
| 2026-08-15 | YES | **`2026-08-11-reached-by-boat-or-plane`** | 3 | commit `50c1a2d` |
| 2026-08-17 | YES | none | 2 | commit `ba64e77` (archive-only) |
| 2026-08-19 | YES | none | 1 | commit `11826e4` (archive-only) |
| 2026-08-21 | upcoming | — | — | — |

**The selector fired on schedule every time.** It is not broken and it is not failing to run.

### The eligible pool is structurally empty

A live `--dry-run` on Trident today (documented as write-free) gives the mechanism exactly:

```
2026-08-13 what-the-word-modular-quietly-removes     HELD  publication_safety_version=None
2026-08-14 modular-means-it-comes-apart…             HELD  publication_safety_version=None
2026-08-15 hand-hammered-edge…                       SKIPPED  fact_check_status: blocked
2026-08-16 sniff-it-out…                             HELD  publication_safety_version=None
2026-08-17 7-000-rooms…                              SKIPPED  fact_check_status: blocked
2026-08-17 galaxy-h1…                                SKIPPED  fact_check_status: blocked
2026-08-20 surovell…                                 SKIPPED  fact_check_status: blocked
→ No scoreable drafts in the last 7 days.
→ Would archive: 2026-08-13-what-the-word-modular-quietly-removes.md
```

Two independent causes, compounding:

**Cause 1 — a hard cutover with no migration path.** Commit `667633f` (2026-08-16 11:55) added
*both* halves of the publication-safety contract at once: `publish_best.py` began requiring
`publication_safety_version >= 1`, and `generate.py` began stamping it. Every draft written
before that commit reached Trident lacks the stamp permanently. There is no backfill path, so
the three otherwise-eligible drafts (08-13, 08-14, 08-16 — all `fact_check_status: verified`,
one scoring 9/10) are **HELD until they age out at 7 days and are archived unpublished**.
08-13 is being archived today; 08-14 and 08-16 follow on 08-21 and 08-23.

**Cause 2 — every post-cutover run has been blocked.** The 08-17 (×2) and 08-20 runs all
carry `fact_check_status: blocked` with `pipeline_degraded` of
`persona_biography_unresolved`, `gate_llm + persona_biography_unresolved`, and `fable_brief`
respectively. So no newly-generated draft has earned a stamp either.

### The stamp has never once been written

**0 of 142 `_posts`, 0 of 7 `_drafts`, 0 of 16 `_archive` articles carry
`publication_safety_version`.** Not one, ever.

`_maybe_stamp_publication_safety_version` requires `should_block` falsy **and**
`fact_check_status: verified` re-read from disk. Since it went live, no run has satisfied both.
So **the stamper's correctness is unproven in production** — it has never had the opportunity
to fire. That is a finding in its own right, and Phase-2's captures may be its first real
observation.

### Classification

**WORKING-BUT-NO-ELIGIBLE-CANDIDATE**, with the caveat that the empty pool is not incidental:
it is caused by a fail-closed gate that currently excludes 100% of articles. Closest to the
brief's option **D** (blocking policy excludes everything), reached via a cutover with no
backfill, not by the selector malfunctioning.

The gate is behaving exactly as designed — the design just has no path for in-flight drafts,
and no alarm for "pool empty across multiple consecutive cycles".

---

## Generation vs publication cadence — recorded explicitly

**Daily generation is intentional and should stay daily.** It exists to build a candidate pool
for a less frequent selector; selection is only meaningful with several candidates to choose
between. The article cron should **not** become every-two-days.

Target: **daily candidate creation + every-~2-days publication selection.**

## Target architecture, completed

```
SOURCE
 → DISCOVERY
 → ARTICLE FORM
 → WRITER
 → WRITER GROUNDING
 → ACCEPT / HOLD
 → ACCEPTED CANDIDATE POOL          (drafts, ~7-day window, aging + archive on expiry)
 → PERIODIC SELECTOR                 (~every 2 days: eligibility gate, then rank)
 → PUBLISH ONE / PUBLISH NONE
 → publication stages                (date rewrite, images, social, git commit + push)
```

**ACCEPT means "eligible candidate" — YES, not "publish now".** The existing system already
separates these correctly; the target must preserve that editorial scarcity. CripMinds should
not auto-publish every ACCEPTed article.

## Selector inputs under the target architecture

| Input | Source today | Fate |
|---|---|---|
| `fact_check_status` | web fact-check (`fact_check.py`) — KEEP in target | **SURVIVES** |
| `publication_safety_version` | stamped from `_should_block` (`fable_brief` / `gate_llm` / `persona_biography_unresolved`) | **REPLACED_BY_TARGET_STAGE** — `gate_llm` disappears with the LLM rule-judge; `fable_brief` becomes DISCOVERY; the contract must be re-derived from **ACCEPT/HOLD**, which is the natural replacement |
| `draft_score` | conditional Opus editorial pass | **REMOVE or REPLACE — owner decision.** Already inert in practice (2 of 7 drafts). If the legacy editorial pass goes, either drop the 60% term or feed it from a target-stage signal |
| `title` → topic freshness | article content | **SURVIVES** |
| `author` → persona rotation | byline, governed by PRF1 | **SURVIVES** |
| `publish_attempts` → aging | selector-internal front matter | **SURVIVES** |
| draft filename date → window/expiry | filename | **SURVIVES** |
| `date:` rewrite on promotion | `set_publish_date` | **SURVIVES** |

**Existing selector: ADAPT.** Cadence, 7-day window, one-per-run, aging, rotation and
freshness all carry over unchanged. Two inputs need work: the safety stamp (re-derive from
ACCEPT) and `draft_score` (decide its fate). Nothing here argues for replacing the selector.

## Phase-2 implication

**Do not change the pre-registered sample.** It remains the first 3 complete eligible daily
runs after capture enablement, and it tests candidate generation / ACCEPT-HOLD.

**A selector observation is also needed — YES**, because the migration changes one of the
selector's two gate inputs. One naturally-occurring decision is enough; do not expand Phase 2
further.

**Is current capture sufficient? NO for the selector.** `shadow_capture.py` hooks only
`generate.py`; it never sees a promotion cycle.

**But the minimum missing capture may be zero code.** `publish_best.py` already prints its
full scoring table and gate verdicts, and the cron already appends stdout to `automation.log`
— today's dry-run reproduced exactly that output. The only real gaps are that those lines are
**untimestamped** (they are `print()`, not logger calls) and live in a rotating log.

Smallest sufficient options, in order of preference — **not implemented**:

1. **Zero code change**: at the next odd-day run, copy the relevant `automation.log` slice
   into the capture root as the selector observation.
2. Redirect that one cron job's stdout to a dated file under
   `/srv/data/cripminds-shadow-capture/selector/` — a cron-line change, no code.
3. Only if structured data proves necessary: a `--json` flag on `publish_best.py`.

Recommended: option 1 or 2. Option 3 is more than the question needs.

## Not changed

No code, no cron, no capture code, no AR3, no production behaviour. Phase-2 capture remains
enabled, sample still 0/3, next eligible run 2026-08-21 09:00 CEST.

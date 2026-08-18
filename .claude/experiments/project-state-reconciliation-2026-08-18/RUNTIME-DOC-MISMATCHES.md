# RUNTIME-DOC-MISMATCHES.md

Production/runtime/code evidence outranks docs. Everything below was checked
against actual code or a live system, read-only, on 2026-08-18.

## Confirmed MATCHES (docs correctly describe runtime — listed so they aren't re-litigated)

- **CJ2_INTEGRATION_MODE = OFF** — confirmed at every level on trident: code default (`generate.py:550`, `cj2_shadow.py` docstring), crontab, `/srv/secrets/reef/reef-bot.env` (no override anywhere in the autonomous run path). Matches WORK.md §6 and LOGBOOK's 08-17 explicit re-verification.
- **Story Rejection V1/V1.1 live, unconditional** — `STORY_REJECTION_CONTRACT_VERSION = "sr1"` used directly in `discovery.py`/`news_fetcher.py`, no env-var gate. Matches WORK.md §3/PROJECT-MAP claiming it's RELEASED.
- **Scout / Sofa — zero code in production** — confirmed via full-tree grep for `SCOUT`/`SOFA` across all `.py` files (production + tests): zero matches. WORK.md/LOGBOOK.md correctly describe this as future/next work, not yet built — no mismatch, but flags that the entire 2026-08-18 Sofa engineering day (audit, architecture proposal, shadow code) is local-only and has not touched production in any way.
- **`cripminds-daily.sh` git-pull-first fix is live** — confirmed the fix from commit `0eae145` is deployed and running (`article`/`news` cron entries both `git pull origin main` before running).
- **Production code mtimes are consistent with git history** — spot-checked 6 key pipeline files; no evidence of uncommitted hand-edits diverging production from git.

## Confirmed MISMATCHES / DEGRADATIONS

### RDM-1 — Sofa pipeline runtime contradicts SOFA-METHOD.md's own canonical rule (P0)
`SOFA-METHOD.md` §4 (canonical, 2026-08-18, uncommitted): "The persona/lens owns
discovery... the prose writer owns writing... **Byline ≠ prose persona**."
`sofa-pipeline-audit-current-runtime-2026-08-18.md` found the live
`automation/` writer prompt does the opposite: injects `prompt_block`, `wound`,
`AUTHORIZED PERSONAL HISTORY`, "WRITE LIKE THIS PERSON," "You are the author" —
byline, persona, and writer are one entity, "precisely what canonical §4
forbids." Rated P0. **Not yet remediated** (Architecture B proposal exists,
not implemented). Note this audit is itself uncommitted/local-only — the
mismatch has been *found* but not yet acted on or even recorded anywhere
durable.

### RDM-2 — Validated discovery never reaches the writer (P0)
Same audit: `hidden_mechanism`/`source_anchor_examined`/
`why_disability_knowledge_changes_subject` are validated for gate-keeping
inside `llm.py`/`grounding.py`, then dropped before the writer stage. Nothing
validates that published prose's mechanism matches the one that earned
commission. Not remediated.

### RDM-3 — No Reader Contract or Evidence Hierarchy stage exists at runtime
Zero grep hits for `reader_contract` anywhere in `automation/`. Article form
(`_pick_article_type`) is randomized *before* material is examined (structural
collision risk: `portrait` requires a real named person the grounding rules
may forbid inventing). SOFA-METHOD.md §6-7 describes both as required stages.
Rated P1 (×7 total P1 degraders found; see the audit doc for the full list).

### RDM-4 — Calibration-runner systemd service is live but erroring
`cripminds-calibration-runner.service` — enabled, active/running since
2026-08-13, `Restart=always`. Latest journal line (2026-08-18 11:27:14):
`claim failed: {'error': 'internal_error'}`. Not mentioned as a known/tracked
issue in any canonical doc checked. Flagged for owner triage — status unknown
(transient vs. persistent failure not established by this audit).

### RDM-5 — `automation/README.md` names a defunct image stack
WORK.md §7 itself already flags this as stale and uncorrected: README still
says "Pollinations FLUX API"; the real stack is OpenRouter + Recraft V4.1.
Listed here because it is a live, uncorrected doc/runtime mismatch, not new —
carried forward from the canonical docs' own self-audit.

### RDM-6 — `project-manifest.json` and its `active_prototypes` field are stale
Generated 2026-08-17T16:56 UTC at HEAD `3225ea1` — one commit behind current
HEAD `9f9bf35`. Its `active_prototypes` entry for Story Rejection V1 still
reads `"FROZEN — AWAITING PRFV1"`, generated before PRFV-M1 was accepted;
actual status is RELEASED (both V1 and V1.1). Machine-generated snapshot,
regenerate via `scripts/cripminds_project_inventory.py` when next convenient —
not urgent, but currently misleading if read in isolation from WORK.md.

### RDM-7 — Two independently-drafted staged-pipeline schemes, never reconciled
WORK.md §2(A) explicitly states a DISCOVERY→SOURCE→SUBJECT→MECHANISM→LENS→VOICE
staged architecture is "STILL UNCONFIRMED, do not assume live" (written
2026-08-17, after searching and not finding such a named scheme anywhere in
the repo). `SOFA-METHOD.md` (mtime one day later, 2026-08-18, uncommitted)
introduces a differently-named but conceptually similar staged pipeline
(WORLD/SOURCE → DISTURBANCE → PERCEPTUAL LENS → DISCOVERY → READER CONTRACT →
RESEARCH/EVIDENCE → ARTICLE FORM → WRITER/PROSE → BYLINE) as canonical. Neither
document cites the other. Not a direct contradiction (different stage names/
order), but unreconciled — does SOFA-METHOD.md's pipeline supersede,
formalize, or coincidentally duplicate the scheme WORK.md flagged as
unconfirmed? Genuinely unresolved by the evidence gathered.

## Convergent (not contradictory) evidence worth surfacing together

Three independent sources converge on "persona should be a soft lens/affinity,
not an ownership/roleplay boundary," via three different lines of evidence
that never cite each other: WORK.md §2(B) (2026-08-10 design history — AFFINITY
replaces "territory," never an ownership gate), `SOFA-METHOD.md` §4 (2026-08-18
canonical rule), and the sofa-pipeline-audit's RDM-1 finding (2026-08-18
runtime observation, framed as a violation of the same principle). This is
real convergent support for one architectural direction, currently scattered
across one committed doc and two uncommitted docs from a different day —
worth consolidating into a single reconciled statement once SOFA-METHOD.md is
committed.

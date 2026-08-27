READ CURRENT STATE FIRST: `.claude/WORK.md` — doctrine, current production safety state (with
exact SHA), active/next work, parked work, historical corrections, document index. An older
research/audit document is NOT current authority when WORK.md marks its conclusion superseded.

Inside `WORK.md`, two sections answer "where are we": **`## ENGINE STATE`** (which engine is
default, what the cron runs, what legacy means, what rollback is) and **`## CURRENT PHASE`** (the
one thing being worked on, and the next action). Read both before starting anything. Note that the
resume prompt further down THIS file is older background — where it and `WORK.md` disagree,
`WORK.md` wins.

FOR HISTORY: `.claude/LOGBOOK.md` — chronological, compact entries (what changed, when, why,
commit SHA, what it superseded).

FOR EVIDENCE: follow the linked research/audit documents from WORK.md's document index — do not
re-derive conclusions those documents already establish.

FOR PHYSICAL PROJECT/WORKTREE/EVIDENCE TOPOLOGY: `.claude/PROJECT-MAP.md` — where worktrees,
branches, and preserved evidence physically live and their lifecycle status. Machine-generated
manifest: `.claude/project-manifest.json` (regenerate: `python3 scripts/cripminds_project_inventory.py`).

---

Resume prompt — cripminds.com session continuation

  Project: cripminds.com — Jekyll publication, disability-led AI editorial, 4 AI personas (Pixel Nova/Deaf, Siri Sage/Blind, Maya
  Flux/Mobility, Zen Circuit/Neurodivergent). GitHub: spac-null/disability-ai-collective (PUBLIC repo). Deploys via GitHub Actions
  on push to main — confirm live with `gh run list --workflow="Deploy to GitHub Pages"`, a landed push is not proof it's live.
  SSH: /usr/bin/ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes jascha@trident
  Repo on server: /srv/data/hermes/workspace/disability-ai-collective/ (checked out fresh by cripminds-daily.sh via `git pull`
    before each run — NOT the older /srv/data/openclaw/workspaces/ops/... path, which is stale/pre-migration)
  Orchestrator: automation/production_orchestrator.py (the only orchestrator file as of 2026-08-09 — root-level manual copy and
    opus_rewrite.py were both confirmed dead and deleted that day)
  Rule: always git push origin main after every commit.

  ---
  Cron schedule (verified directly against trident's crontab 2026-08-09 — do not trust older doc claims about schedule times):
  - 06:05 daily: cripminds-daily.sh news       → automation/news_fetcher.py (RSS + keyword scoring → news_seeds table)
  - 09:00 daily: cripminds-daily.sh article     → automation/production_orchestrator.py (writes article, images, Bluesky, deploy)
  - 10:30 daily: cripminds-daily.sh stale-check → alerts if no article in 4+ days
  - Sunday 03:00: automation/link_pool_crawler.py
  - Saturday 10:15: automation/bsky_outreach_auto.py
  - Sunday 10:30: newsletter-weekly-digest.py
  - every 2 days 08:00: automation/publish_best.py
  run_discovery.py and opus_rewrite.py are NOT in the crontab — both deleted 2026-08-09, see git log.

  ---
  Key paths:
  - DB: /srv/data/hermes/workspace/disability-ai-collective/disability_findings.db
    Tables: news_seeds (live, written by news_fetcher.py), findings (dead since 2026-05-02, was run_discovery.py's — kept for
    production_orchestrator.py's fallback read path, never repopulated), article_beats, link_pool, citation_ledger
  - Style rules: automation/style_rules.py (single source of truth, added 2026-08-09) + automation/check_rule_drift.py (linter —
    run before touching any style-rule text)
  - Social URIs: _social/*.json (bsky_uri + agent)
  - Reviews: _reviews/*.md (citation check sidecars)
  - Engage state: automation/bsky_engage_seen.json
  - Secrets: /srv/secrets/openclaw.env (BSKY_*, TELEGRAM_*, OPENROUTER_API_KEY), /srv/secrets/tumblr.env
  - Model routing: Claude Opus 4.8 via OpenRouter primary; CLIProxy (http://127.0.0.1:8317/v1) is a fallback path only, not
    primary — see automation/README.md for detail, this drifted in older docs before

  ---
  Ongoing work (see project memory `project-cripminds-fabrication-sweep-2026-08-09` for full detail):
  - Style-rules migration: registry + drift-detector shipped; incremental convergence of the ~12 hand-copied rule locations to
    the registry is in progress, one rule per commit.
  - Known gap: writer prompt's "ONE IDEA PER SENTENCE" rule has no downstream gate/review check — advisory-only in prompt text.

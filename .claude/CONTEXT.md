Resume prompt — cripminds.com session continuation

  Project: cripminds.com — Jekyll publication, disability-led AI editorial, 4 AI personas (Pixel Nova/Deaf, Siri Sage/Blind, Maya
  Flux/Mobility, Zen Circuit/Neurodivergent). GitHub: spac-null/disability-ai-collective. Deploys via GitHub Actions on push to
  main.
  SSH: /usr/bin/ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes jascha@trident
  Repo on server: /srv/data/openclaw/workspaces/ops/disability-ai-collective/
  Orchestrator: automation/production_orchestrator.py
  Rule: always git push origin main after every commit.

  ---
  Cron schedule (all on trident jascha crontab):
  - 7am: run_discovery.py
  - 9am: production_orchestrator.py (daily article)
  - 10:30am: opus_rewrite.py
  - 11am: bsky_engage.py + Sunday link-audit
  - 7pm: bsky_engage.py
  - 2am Monday: link_pool_crawler.py (3,631 links in disability_findings.db)
  - 10:30am Sunday: newsletter-weekly-digest.py

  ---
  Key paths:
  - DB: /srv/data/openclaw/workspaces/ops/disability-ai-collective/disability_findings.db (findings, article_beats, link_pool)
  - Social URIs: _social/*.json (bsky_uri + agent)
  - Reviews: _reviews/*.md (citation check sidecars)
  - Engage state: automation/bsky_engage_seen.json
  - Secrets: /srv/secrets/openclaw.env (BSKY_*, ANTHROPIC_API_KEY, TELEGRAM_*), /srv/secrets/tumblr.env
  - CLIProxy: http://172.19.0.1:8317/v1 (all Claude API calls route here)
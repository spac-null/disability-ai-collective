# Automation — Crip Minds

## Daily Pipeline (fully automated)

```
07:00  run_discovery.py           → finds topics, fills disability_findings.db
09:00  automation/production_orchestrator.py → picks topic, writes article,
                                               generates images, posts Bluesky,
                                               commits + deploys to GH Pages
```

No manual intervention needed. Cron runs on trident host.

## Manual Override

To force a specific article, add a brief to `QUEUE = []` at the top of
`automation/production_orchestrator.py`, then run:
```bash
./run python3 automation/production_orchestrator.py
```

Leave QUEUE empty for fully automatic topic selection from DB.

## Active Scripts

### `automation/production_orchestrator.py`
Main article pipeline. Self-loads `/srv/secrets/openclaw.env`.

**Key settings:**
- `max_tokens`: 4000 (do NOT lower — causes truncation)
- Provider: Claude Opus 4.6 via CLIProxy at http://172.19.0.1:8317
- Images: Pollinations FLUX API (key from openclaw.env)
- Bluesky: auto-posts after each article (creds from openclaw.env)
- Gold standard: `2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md`

### `run_discovery.py`
Discovers disability/tech topics, writes to `disability_findings.db`.
Runs at 07:00 daily. Self-loads openclaw.env.

### `opus_rewrite.py`
Rewrites weak articles to De Correspondent quality.
```bash
./run python3 opus_rewrite.py   # add filenames to TARGETS = [] first
```

### `scene_image_generator.py`
Image generation library used by orchestrator. Self-loads openclaw.env.

### `regen_images.py`
Regenerates images for existing articles.
```bash
./run python3 regen_images.py
```

## `./run` Wrapper
Pre-loads openclaw.env for any command:
```bash
./run python3 <script>.py
./run bash some-script.sh
```

## Env Loading Rule
ALL Python scripts self-load `/srv/secrets/openclaw.env` via `_ENV_FILE` parser
at the top of the file. New scripts must include this block — copy from any
existing script. openclaw.env has NO export statements.

## Article Front Matter
```yaml
---
layout: post
title: "Title"
author: "Siri Sage"   # Must match exactly — case sensitive, affects RSS feeds
date: 2026-03-14
categories: [Category]
excerpt: "One sentence."
image: /assets/<slug>_setting_1.jpg
---
```

## Personas
- **Pixel Nova** — Deaf · Visual Language
- **Siri Sage** — Blind · Acoustic Culture
- **Maya Flux** — Mobility · Adaptive Systems
- **Zen Circuit** — Neurodivergent · Pattern Recognition

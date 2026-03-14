# Automation — Crip Minds

## Active Scripts

### `production_orchestrator.py`
Main article pipeline. Self-contained — loads `/srv/secrets/openclaw.env` internally.

**Usage:**
```python
# Edit QUEUE at top of file, then:
python3 production_orchestrator.py
```

**What it does:**
1. Generates article via Claude Opus 4.6 (CLIProxy at http://172.19.0.1:8317)
2. Generates 3 images via Pollinations FLUX API
3. Writes Jekyll post to `_posts/`
4. Commits + pushes to GitHub (auto-deploys via GH Pages)

**Key settings:**
- `max_tokens`: 4000 (do NOT lower — causes truncation)
- Image paths: auto-corrected to `/assets/<slug>_setting_1.jpg`
- Captions: `*em*` on line after every `![img](url)`
- Gold standard: `2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md`

### `opus_rewrite.py`
Rewrites weak articles to De Correspondent quality.

**Usage:**
```bash
set -a; source /srv/secrets/openclaw.env; set +a
python3 opus_rewrite.py
```
Add filenames to `TARGETS = []` at top of file.

## Article Front Matter
```yaml
---
layout: post
title: "Title"
author: "Siri Sage"        # Must match exactly: Siri Sage / Pixel Nova / Maya Flux / Zen Circuit
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

## Environment
- `openclaw.env` has NO export statements — scripts must load file directly
- Pollinations key: in `/srv/secrets/openclaw.env` as `POLLINATIONS_API_KEY`
- CLIProxy: `http://172.19.0.1:8317` (gateway IP — host.docker.internal doesn't work on Linux)

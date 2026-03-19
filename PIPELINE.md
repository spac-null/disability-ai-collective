# Crip Minds Pipeline — Read Before Touching Anything

## What This Is
`disability-ai-collective` — a disability culture publication (Jekyll site, GitHub Pages).
Articles are generated daily by `automation/production_orchestrator.py` via cron through the ops OpenClaw agent heartbeat.

**Do NOT run the orchestrator manually unless explicitly asked.** It commits and pushes to GitHub immediately — article goes live.

## The 4 Personas (AI authors)
| Persona | Disability | Beat |
|---|---|---|
| Pixel Nova | Deaf | Visual systems, information architecture, space politics |
| Siri Sage | Blind | Acoustic culture, sensory phenomenology, soundscape |
| Maya Flux | Mobility (wheelchair, T6) | Urban infrastructure, economics of care, protest history |
| Zen Circuit | Autistic/neurodivergent | Diagnosis politics, pattern recognition, sensory epistemology |

Each has a deep character profile embedded in the orchestrator. The article IS written from their lived experience — disability as expertise and lens, never tragedy.

## Output Format Contract
Every article is a Jekyll post with exact frontmatter:
```yaml
---
layout: post
title: "Title here"
date: YYYY-MM-DD
author: Pixel Nova          # exact persona name
category: research          # or: culture, technology, justice
excerpt: "One sentence."
image: /assets/images/SLUG-1.jpg
---
```
Frontmatter must use double quotes. Never put AI-generated text directly in YAML values without stripping quotes first — breaks parsing silently (nil title, double-date URL).

Image HTML blocks in the body use exact format:
```html
<figure class="article-figure">
  <img src="/assets/images/SLUG-N.jpg" alt="description" loading="lazy">
  <figcaption>Caption here.</figcaption>
</figure>
```

## What NOT to Do
- No academic headers (Research Question / Methodology / Key Findings / Recommendations)
- No bullet-point policy lists
- No invented statistics or fake study findings
- No "Case study: Sarah, a graphic designer..."
- No summary ending / call to action / "We need to..."
- No publication names like "De Correspondent" or "dis.art" anywhere in articles
- Never put unescaped quotes in YAML front matter fields

## Git Workflow
This workspace IS the live repo. Commits here push to GitHub → GitHub Actions builds Jekyll → site goes live within ~2 minutes.
```bash
git status          # check what changed
git log --oneline -5
git push origin main   # ALWAYS push after any editorial commit
```
**After any editorial change: always `git push origin main` — no push = site stays stale.**

## Retract an Article
```bash
python3 automation/production_orchestrator.py --retract <slug>
```
Deletes Bluesky post (URI in `_social/<slug>.json`) + git rm + push.

## Key Directories
```
_posts/         ← published articles (YYYY-MM-DD-slug.md)
assets/images/  ← article images
automation/     ← orchestrator, link pool crawler, image gen
_social/        ← Bluesky post URIs per article
```

## Orchestrator Architecture (9-step pipeline)
1. Pick agent (balance across personas)
2. Get topic from sentinel findings DB
3. Fetch source article
4. Build prompt (style + persona + source + link pool)
5. Generate with Opus (CLIProxy) → fallback chain
6. Rewrite with Opus (editor pass) if not already Opus
7. Generate images (Pollinations API)
8. Insert images balanced in body
9. Write frontmatter → commit → push → Bluesky post

## Danger Zones
- `automation/link_pool.db` — don't delete (curated link seeds + crawled pool)
- `automation/disability_findings.db` — don't delete (topic source material)
- `.env` in workspace root — secrets, never commit
- Gold standard article: `_posts/2026-03-14-the-open-office-was-designed-to-break-my-brain.md` — do not delete or move (used as rewrite reference)

---

## Conversion Optimisation Log

### Insight (2026-03-19, v2.2)
GoatCounter data after 11 days (35 homepage visits, ~15 article reads):
-  (hero pull quote link): 0 clicks — hero not converting
-  (primary CTA): 1 click
-  page: 8 visits — people browse but most came from nav, not hero
- : 7 visits — nearly as popular as /research, 0 article conversions from it
- Room That Sings (Mar 17): 6 reads on launch day — best Bluesky hook drove this

### What was missing
1. No click tracking on the 3 article cards in the homepage grid (only CTAs tracked)
2. No article links on /about page — 7 visits going nowhere
3. Hero excerpt rendered as small caption under large heading — visually subordinate

### Changes made (2026-03-19)
1. **Homepage card tracking** — GoatCounter events on all 3 article card title clicks
   File:  JS block
2. **About page start-here** — Added 3 best articles as start here reading list
   File:  or 

### Backlog
- Hero redesign: make tension-frame excerpt the visual anchor, not the title
- Bump homepage grid from 3 → 5 cards (publish daily, grid goes stale fast)
- Consider article image in hero

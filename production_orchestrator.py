#!/usr/bin/env python3
"""
production_orchestrator.py — Article generation pipeline for Crip Minds.

Pipeline per article:
  1. Write article body via Claude Opus (CLIProxy)
  2. Generate 3 images via scene_image_generator
  3. Save _posts/<slug>.md + assets/<slug>_*.jpg
  4. Git add + commit + push

Provider: Claude Opus 4.6 via CLIProxy at http://172.19.0.1:8317
Secrets:  ANTHROPIC_API_KEY from /srv/secrets/openclaw.env
"""
import json, re, os, time, subprocess, textwrap, logging
import urllib.request
from pathlib import Path
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

REPO     = Path(__file__).parent
POSTS    = REPO / "_posts"
ASSETS   = REPO / "assets"
API_URL  = "http://172.19.0.1:8317/v1/chat/completions"
API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL    = "claude-opus-4-6"

PERSONAS = {
    "Pixel Nova": {
        "disability": "Deaf · Visual Language",
        "voice": "deaf interface designer who navigates the world through visual structure. Writes from inside deaf culture and Deaf gain — deafness as perceptual expertise, not loss.",
        "categories_default": ["Visual Design", "Deaf Culture"],
    },
    "Siri Sage": {
        "disability": "Blind · Acoustic Culture",
        "voice": "blind researcher who builds spatial maps through sound. Writes from lived echolocation and auditory culture — blindness as a different relationship with space, not absence of it.",
        "categories_default": ["Acoustic Culture", "Accessibility Innovation"],
    },
    "Maya Flux": {
        "disability": "Mobility · Adaptive Systems",
        "voice": "wheelchair user and urban researcher who maps mobility barriers. Writes from crip time and the physics of inaccessible infrastructure — the city as an obstacle course it refuses to admit it built.",
        "categories_default": ["Urban Design", "Accessibility Innovation"],
    },
    "Zen Circuit": {
        "disability": "Neurodivergent · Pattern Recognition",
        "voice": "autistic software designer who sees systems as patterns. Writes from inside autistic perception — not broken processing but different processing, and what that difference reveals about design.",
        "categories_default": ["Neurodiversity", "Interface Design"],
    },
}

SYSTEM = """You are writing for Crip Minds — a disability-led editorial arts platform in the tradition of De Correspondent and dis.art. You write as a specific AI persona with a distinct disability perspective. Disability is expertise, culture, and lens — never tragedy, never limitation, never inspiration.

DE CORRESPONDENT VOICE RULES (non-negotiable):
1. Open with ONE specific concrete moment, scene, or sharp claim — never a question, never statistics, never "In today's world"
2. First-person throughout — lived expertise, not detached analysis
3. NO academic section headers (Research Question / Methodology / Key Findings / Recommendations)
4. NO bullet-point policy lists — weave all argument into prose
5. NO "Case study: Sarah, a graphic designer..." — use real narrative flow
6. Long paragraphs with rhythm — vary short punchy sentences with longer development
7. Bold sparingly — only for the sharpest single claims, never as structural markers
8. End on a resonant image or question, NOT a call-to-action, NOT "What do you think?"
9. 800-1000 words body — substantial but not padded
10. Author's disability is their EXPERTISE and LENS, never obstacle or tragedy
11. Crip culture references (Sins Invalid, crip time, disability justice, DeafBlind, Protactile) only when they fit naturally

OUTPUT FORMAT — return ONLY this, no preamble, no commentary:
---
layout: post
title: "<title>"
date: <YYYY-MM-DD>
author: <persona name>
categories: [<categories>]
excerpt: "<one-sentence excerpt that opens with a scene or sharp claim>"
image: /assets/<slug>_setting_1.jpg
---

<article body>"""

def slugify(title):
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80]

def call_opus(persona_name, angle, categories, today):
    p = PERSONAS[persona_name]
    slug_hint = slugify(angle)
    user_msg = f"""Write a Crip Minds article as {persona_name}.

PERSONA: {persona_name} — {p['disability']}
VOICE: {p['voice']}

ARTICLE ANGLE: {angle}

CATEGORIES: {json.dumps(categories)}
DATE: {today}
SLUG (use for image path): {slug_hint}

Write the full article following the De Correspondent rules exactly. Return only the frontmatter + body, no preamble."""

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 3000,
        "messages": [{"role": "user", "content": user_msg}],
        "system": SYSTEM,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"].lstrip("\n")

def extract_slug_from_frontmatter(content, today):
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    title = m.group(1) if m else "article"
    return f"{today}-{slugify(title)}"

def generate_article(persona_name, angle, categories=None, today=None):
    today = today or str(date.today())
    cats = categories or PERSONAS[persona_name]["categories_default"]

    log.info(f"[Opus] Writing: {angle[:60]} ({persona_name})")
    content = call_opus(persona_name, angle, cats, today)

    if "---" not in content[:200]:
        log.error(f"  Missing frontmatter, got: {content[:200]}")
        return None

    slug = extract_slug_from_frontmatter(content, today)
    post_path = POSTS / f"{slug}.md"

    # Generate images
    log.info(f"  Generating images for {slug}...")
    try:
        from scene_image_generator import generate_article_images
        images = generate_article_images(content, angle, slug, num_images=3)
        for img in images:
            out = ASSETS / img["filename"]
            out.write_bytes(img["data"])
            log.info(f"  Image: {img['filename']} ({len(img['data'])} bytes)")
    except Exception as e:
        log.warning(f"  Image generation failed: {e} — continuing without images")
        images = []

    # Save post
    post_path.write_text(content)
    log.info(f"  Saved: {post_path.name}")

    return slug

def git_push(slugs):
    files = []
    for slug in slugs:
        files.append(f"_posts/{slug}.md")
    # Also add any new assets
    result = subprocess.run(
        ["git", "status", "--porcelain", "assets/"],
        cwd=REPO, capture_output=True, text=True
    )
    new_assets = [line[3:].strip() for line in result.stdout.splitlines() if line.strip()]
    files += new_assets

    subprocess.run(["git", "add"] + files, cwd=REPO, check=True)
    msg = f"publish: {len(slugs)} new article(s) — {', '.join(s.split('-', 3)[-1][:30] for s in slugs)}"
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=True)
    log.info(f"Pushed: {msg}")

# ── Article queue ──────────────────────────────────────────────────────────────
# Add briefs here: (persona, angle, [optional categories])
QUEUE = [
],
    },
    {
        "persona": "Maya Flux",
        "angle": "The Accessible Entrance Is Around the Back: On the Architecture of Separate and Unequal",
        "categories": ["Urban Design", "Accessibility Innovation", "Spatial Design"],
    },
    {
        "persona": "Zen Circuit",
        "angle": "The Open Office Was Designed to Break My Brain",
        "categories": ["Neurodiversity", "Interface Design", "Sensory Processing"],
    },
    {
        "persona": "Siri Sage",
        "angle": "The City Forgot to Sound-Design Its Streets: On Acoustic Wayfinding and Who Gets Left Behind",
        "categories": ["Acoustic Culture", "Urban Design", "Accessibility Innovation"],
    },
]

if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    if not QUEUE:
        raise SystemExit("QUEUE is empty — add article briefs before running")

    today = str(date.today())
    published = []

    for item in QUEUE:
        persona = item["persona"]
        angle   = item["angle"]
        cats    = item.get("categories", PERSONAS[persona]["categories_default"])
        try:
            slug = generate_article(persona, angle, cats, today)
            if slug:
                published.append(slug)
                time.sleep(3)
        except Exception as e:
            log.error(f"FAILED {angle[:40]}: {e}")

    if published:
        git_push(published)
        log.info(f"\nDone — {len(published)} article(s) published.")
    else:
        log.warning("No articles published.")

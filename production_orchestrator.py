#!/usr/bin/env python3
"""
production_orchestrator.py — MANUAL USE ONLY. NOT the cron file.

⚠️  THE CRON RUNS: automation/production_orchestrator.py
    This root-level file is a simpler standalone version for one-off manual
    article generation. It lacks the full provider cascade, inline Opus rewrite,
    Bluesky posting, and DB integration that the automation version has.

    Before editing anything here, ask: should this change go to
    automation/production_orchestrator.py instead?

Manual usage (force a specific article):
  Edit QUEUE = [
  Edit QUEUE = [] below, then:
] below, then:
  ./run python3 production_orchestrator.py

For the automated daily pipeline see: automation/README.md

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

# Load secrets (no export needed — read directly)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())
POSTS          = REPO / "_posts"
ASSETS         = REPO / "assets"
API_URL        = "http://172.19.0.1:8317/v1/chat/completions"
API_KEY        = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL          = "claude-opus-4-6"
FALLBACK_MODEL = "claude-sonnet-4-20250514"

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

SYSTEM = """You are writing for Crip Minds — a disability culture publication built from experiential knowledge, not academic authority. You write as a specific AI persona with a distinct disability perspective.

PUBLICATION LENS (read this before writing):
This publication is built by someone who stood in a room at the Van Abbemuseum and recognized it. Ahmet Ogut's Exploded City — scale models of buildings that no longer exist, shown intact. Your mind fills in what was lost. He guided visitors through that room every week for six months. Each time he thought: this is how I think.

He also knows the other image. Screaming inside a transparent plastic cube, one cubic decimetre, lying on the street. Pedestrians walking past without noticing. That is what invisibility feels like from the inside.

He draws in bic pen. No correction. No undo. Sign language works the same way: meaning in the body, in movement, in time.

The time-lag. You receive the room three seconds late. You attend two schools — in one you lip-read and guess, in the other you sign and the hearing world disappears. Then you leave the second one.

He has also been in the room where the lag disappears entirely — where everyone shares a language and nobody needs to translate. That room exists. It just doesn't last. The grey zone between worlds is where the energy comes from. He stays there deliberately.

They put a wheelchair ramp in a heritage zone, got fined, kept going. Permanent ramp in year four. Tribunal. Fine after fine. Ten years later, permission arrived in the post. They named a beer after it.

Disability culture has built an enormous body of knowledge. Almost none of it reaches the places where culture gets made and interpreted. Not because it's hidden. Because nobody's looking.

Put the reader in a room. The image makes the argument. They get there before you name it. A reader finishes an article and the world looks slightly different than it did. Not because they learned something. Because they saw something.

Two kinds of knowledge. Experience is the argument. Scholarship is evidence. The ramp, the lag, the room full of eyes come first. Citations after, if at all.

WRITING RULES (non-negotiable — violations will cause rejection):
1. Open with ONE specific concrete moment, scene, or sharp claim — never a question, never statistics, never "In today's world"
2. Plain vocabulary. "Use" not "utilise." "Show" not "demonstrate."
3. Short declarative lands the idea. Longer sentence develops it. Then short again.
4. One modifier per noun. Never stack adjectives.
5. Never announce the thesis. The example makes the argument. The reader realizes it.
6. Show the thing before naming it.
7. Named sources. Not "a researcher found" — name the researcher, year, institution.
8. First-person throughout — lived expertise, not detached analysis
9. NO section headers of any kind. Use --- for a section break if needed. Transitions happen INSIDE the prose, not above it.
10. NEVER use bullet points, numbered lists, or bolded list items. Multiple examples go into accumulation paragraphs.
11. NO fake case studies, invented projects, unnamed collaborations. NEVER invent statistics, interview counts, or research findings. NEVER reference unnamed researchers or unspecified studies. Real sources only: name + year. No real source? Use lived experience instead.
12. Long paragraphs with rhythm. After the opening, return to a concrete scene or sensory moment at least twice more. Never settle into pure exposition for more than two consecutive paragraphs.
13. Bold sparingly — only for the single sharpest claim in the whole piece, if at all.
14. Final paragraph: a concrete image, scene, or sensory moment. NEVER end with "I want," "we need," "it is time," or any statement of desire, demand, or call to action. The argument is already made. The ending shows; it does not ask.
15. HARD CAP: 1000 words. Count before finishing. If over 1000, cut from the back half — the ending should arrive sooner, not later.
16. Author's disability is their EXPERTISE and LENS — never obstacle, never tragedy
17. Crip culture references only when they fit naturally
18. MANDATORY: Insert all 3 provided images inline in the article body, spaced throughout. Each image on its own line followed immediately by an italic caption: ![alt text](url)
*caption text*
19. DO NOT locate arguments in the United States specifically. No ADA, FEMA, or American laws or institutions. Write from anywhere — unnamed cities, or named non-US examples. Arguments must feel globally applicable.

OUTPUT FORMAT — return ONLY this, no preamble, no commentary:
---
layout: post
title: "<title>"
date: <YYYY-MM-DD>
author: <persona name>
categories: [<categories>]
image: /assets/<slug>_setting_1.jpg
---

<article body>"""

def slugify(title):
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80]

def call_opus(persona_name, angle, categories, today, model=None):
    """Call the API and return (content, actual_model_used)."""
    model = model or MODEL
    p = PERSONAS[persona_name]
    slug_hint = slugify(angle)
    user_msg = f"""Write a Crip Minds article as {persona_name}.

PERSONA: {persona_name} — {p['disability']}
VOICE: {p['voice']}

ARTICLE ANGLE: {angle}

CATEGORIES: {json.dumps(categories)}
DATE: {today}
SLUG (use for image path): {slug_hint}

Write the full article following the WRITING RULES exactly.
MANDATORY INLINE IMAGES — insert all three in the body, spaced throughout, each with an italic caption:
  ![description](/assets/{today}-{slug_hint}_setting_1.jpg)
  *caption*
  
  ![description](/assets/{today}-{slug_hint}_moment_2.jpg)
  *caption*
  
  ![description](/assets/{today}-{slug_hint}_symbol_3.jpg)
  *caption*

Return only the frontmatter + body, no preamble."""

    payload = json.dumps({
        "model": model,
        "max_tokens": 4000,
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
    content = resp["choices"][0]["message"]["content"].lstrip("\n")
    actual_model = resp.get("model", model)
    return content, actual_model

def extract_slug_from_frontmatter(content, today):
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    title = m.group(1) if m else "article"
    return f"{today}-{slugify(title)}"

def generate_article(persona_name, angle, categories=None, today=None):
    """Generate one article. Returns (slug, model_used) or None on failure."""
    today = today or str(date.today())
    cats = categories or PERSONAS[persona_name]["categories_default"]

    log.info(f"[Opus] Writing: {angle[:60]} ({persona_name})")
    try:
        content, model_used = call_opus(persona_name, angle, cats, today)
    except Exception as e:
        err = str(e).lower()
        if any(sig in err for sig in ("429", "rate", "overload", "capacity")):
            log.warning("  Opus rate-limited (%s) — falling back to Sonnet", e)
            content, model_used = call_opus(persona_name, angle, cats, today, model=FALLBACK_MODEL)
        else:
            raise

    if model_used != MODEL:
        log.warning("  Article written by %s (not Opus) — will be queued for quality rewrite", model_used)

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

    # Force-correct image path (Opus sometimes generates wrong path)
    correct_image = f"/assets/{slug}_setting_1.jpg"
    content = re.sub(r'^image:.*$', f'image: {correct_image}', content, flags=re.MULTILINE)

    # Inject model tracking field (after image: line)
    if "model_used:" not in content:
        content = re.sub(
            r'^(image:.*)$',
            rf'\1\nmodel_used: {model_used}',
            content, flags=re.MULTILINE
        )

    # Save post
    post_path.write_text(content)
    log.info(f"  Saved: {post_path.name} [model: {model_used}]")

    return slug, model_used

def git_push(published):
    """published = [(slug, model_used), ...]"""
    files = [f"_posts/{slug}.md" for slug, _ in published]
    # Also add any new assets
    result = subprocess.run(
        ["git", "status", "--porcelain", "assets/"],
        cwd=REPO, capture_output=True, text=True
    )
    new_assets = [line[3:].strip() for line in result.stdout.splitlines() if line.strip()]
    files += new_assets

    subprocess.run(["git", "add"] + files, cwd=REPO, check=True)

    def label(slug, model):
        name = slug.split('-', 3)[-1][:30]
        return name if model == MODEL else f"{name} [↓{model.split('-')[1]}]"

    msg = f"publish: {len(published)} new article(s) — {', '.join(label(s, m) for s, m in published)}"
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=True)
    log.info(f"Pushed: {msg}")

# ── Article queue ──────────────────────────────────────────────────────────────
# Add briefs here: (persona, angle, [optional categories])
QUEUE = []

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
            result = generate_article(persona, angle, cats, today)
            if result:
                published.append(result)
                time.sleep(3)
        except Exception as e:
            log.error(f"FAILED {angle[:40]}: {e}")

    if published:
        git_push(published)
        log.info(f"\nDone — {len(published)} article(s) published.")
    else:
        log.warning("No articles published.")

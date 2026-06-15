#!/usr/bin/env python3
"""
Generate cripminds article images via OpenRouter (Recraft V4.1).

Three images per article:
  {slug}_setting_1.jpg  — confronting: screen-print protest poster
  {slug}_moment_2.jpg   — intimate: gouache on textured paper
  {slug}_symbol_3.jpg   — abstract: linocut relief print

Usage:
    OPENROUTER_API_KEY=sk-... python3 automation/gen_images.py
    OPENROUTER_API_KEY=sk-... python3 automation/gen_images.py --slug the-upgrade-assumes-a-body-that-was-working-before
    python3 automation/gen_images.py --dry-run
    python3 automation/gen_images.py --model recraft/recraft-v3

After running:
    git add assets/ _posts/ && git commit -m "feat: generate images" && git push
"""

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import time
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).parent.parent
POSTS_DIR  = REPO_ROOT / "_posts"
ASSETS_DIR = REPO_ROOT / "assets"

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "recraft/recraft-v4.1"

# image type → (filename_suffix, aspect_ratio, style_key)
IMAGE_TYPES = [
    ("setting_1", "16:9", "CONFRONTING"),
    ("moment_2",  "1:1",  "INTIMATE"),
    ("symbol_3",  "1:1",  "ABSTRACT"),
]

# Per-persona visual language — 3 sub-styles per persona, rotated by slug hash
# so consecutive articles by the same persona look genuinely different
PERSONA_STYLES = {
    "Pixel Nova": [
        {   # sub-style 0: gallery / risograph
            "CONFRONTING": (
                "Contemporary art publication cover. Risograph or silkscreen print. "
                "Gallery poster energy — striking, culturally specific, no text. "
                "Subject: {summary}. "
                "References: Dutch graphic design, Werkplaats Typografie aesthetic without the typography. "
                "Color as argument, not decoration."
            ),
            "INTIMATE": (
                "Artist's sketchbook page or study. Ink wash, dry media, or printmaking process. "
                "The texture of thinking — a close observation, not a finished illustration. "
                "Subject: {summary}. "
                "Feels like a working drawing for an artwork that exists in the same world as the article."
            ),
            "ABSTRACT": (
                "Exhibition catalogue detail. Geometric abstraction rendered as pure image — "
                "no letterforms, no legible text. Concept: {summary}. "
                "A surface, a pattern, a structural fragment from a larger work. "
                "Precise, intentional, art-world literate."
            ),
        },
        {   # sub-style 1: collage / cut-and-paste
            "CONFRONTING": (
                "Photographic collage, magazine cut-up aesthetic. Bold, layered, no text. "
                "Subject: {summary}. "
                "References: Barbara Kruger without the words, Dadaist photomontage energy. "
                "High contrast fragments assembled into argument."
            ),
            "INTIMATE": (
                "Detail from a handmade artist's book or zine. Layered paper, torn edges, "
                "rubber-stamp marks — without legible stamps. Subject: {summary}. "
                "The closeness of something made by hand, slowly, for someone specific."
            ),
            "ABSTRACT": (
                "Colour field painting or abstract expressionist composition. "
                "Large areas of flat or gestural colour, no figures, no text. "
                "Concept: {summary}. "
                "The emotional logic of the concept translated into pure colour relationship."
            ),
        },
        {   # sub-style 2: screen-print / activist graphic
            "CONFRONTING": (
                "Two-colour screen print. Bold flat graphic, high contrast, no text. "
                "Subject: {summary}. "
                "Corita Kent energy — joyful and political at once. "
                "Strong silhouette, unexpected colour pairing."
            ),
            "INTIMATE": (
                "Monoprint or linocut close-up. A single gestural mark or small repeated pattern "
                "filling the frame. Subject: {summary}. "
                "The scale of a handprint. Tactile, immediate, made in one sitting."
            ),
            "ABSTRACT": (
                "Geometric screen-print pattern. Repeat or near-repeat structure that breaks "
                "unexpectedly. No text, no figures. Concept: {summary}. "
                "The pattern is the argument — regularity interrupted by the thing it cannot contain."
            ),
        },
    ],
    "Zen Circuit": [
        {   # sub-style 0: blueprint / circuit diagram
            "CONFRONTING": (
                "Technical blueprint or circuit diagram charged with political tension. No text, no labels. "
                "Subject: {summary}. "
                "Precision used to expose rather than conceal. Cold palette, high contrast."
            ),
            "INTIMATE": (
                "Detail from a technical manual — stippling or cross-hatching technique. "
                "Something clinical made human by close attention. Subject: {summary}. "
                "Monochrome or very limited palette. The intimacy of documentation."
            ),
            "ABSTRACT": (
                "Network topology or flow diagram as pure composition. No labels, no text. "
                "Concept: {summary}. "
                "The structure of a system made visible as form. Precise, geometric, cold."
            ),
        },
        {   # sub-style 1: constructivist / Soviet poster without text
            "CONFRONTING": (
                "Soviet constructivist poster aesthetic — diagonal geometry, stark contrast, "
                "no text, no typography. Subject: {summary}. "
                "El Lissitzky or Rodchenko visual language applied to contemporary systems critique. "
                "Strong geometric composition."
            ),
            "INTIMATE": (
                "Mechanical engraving or technical etching. Fine parallel lines, "
                "cross-hatched shadow, the precision of 19th-century scientific illustration "
                "applied to contemporary subject matter. Subject: {summary}. "
                "Dense, careful, reveals more the longer you look."
            ),
            "ABSTRACT": (
                "Isometric diagram or exploded view — a system taken apart and laid flat. "
                "No labels, no text, no numbers. Concept: {summary}. "
                "The logic of assembly visible as composition."
            ),
        },
        {   # sub-style 2: data visualization / mapping
            "CONFRONTING": (
                "Statistical chart or data visualization turned into confrontational image. "
                "No axes labels, no numbers, no text — just the shape of the data. "
                "Subject: {summary}. "
                "The visual argument of a graph stripped of its academic framing."
            ),
            "INTIMATE": (
                "Topographic map detail or close section of a technical survey. "
                "Contour lines, measurement marks — without the numbers. "
                "Subject: {summary}. "
                "The landscape of a problem rendered as terrain."
            ),
            "ABSTRACT": (
                "Wiring diagram or schematic as abstract composition. "
                "Nodes, paths, connections — no text, no component labels. "
                "Concept: {summary}. "
                "A system's skeleton visible as pure line drawing."
            ),
        },
    ],
    "Siri Sage": [
        {   # sub-style 0: natural history / specimen
            "CONFRONTING": (
                "Natural history illustration — detailed, observational, but the subject is social. "
                "No text. Subject: {summary}. "
                "Anna Atkins, specimen illustration aesthetics. "
                "Unexpected colour relationships. Careful and disturbing at once."
            ),
            "INTIMATE": (
                "Naturalist's field notebook detail. Pencil or watercolour wash. "
                "Observational, patient, slightly obsessive. Subject: {summary}. "
                "The feeling of someone who has been looking very closely for a long time."
            ),
            "ABSTRACT": (
                "Scientific data visualization abstracted — cell structure, seismic wave, "
                "spectral analysis, neural mapping — as image not diagram. "
                "No labels, no axes, no text. Concept: {summary}. "
                "Measurement made decorative and strange."
            ),
        },
        {   # sub-style 1: medical / anatomical illustration
            "CONFRONTING": (
                "Medical or anatomical illustration style — cross-section, diagram, "
                "but charged with the thing it's depicting. No text, no labels. "
                "Subject: {summary}. "
                "Vesalius or Gray's Anatomy visual language applied to a contemporary argument."
            ),
            "INTIMATE": (
                "Microscopy aesthetic — the view through a lens, grain included. "
                "Close, specific, slightly uncanny. Subject: {summary}. "
                "The scale where familiar things stop looking familiar."
            ),
            "ABSTRACT": (
                "Cyanotype or photogram aesthetic — white forms on deep blue or dark ground. "
                "Botanical or structural silhouette, no text. Concept: {summary}. "
                "Anna Atkins's method: the object pressed against the surface and exposed."
            ),
        },
        {   # sub-style 2: acoustic / sensory diagram
            "CONFRONTING": (
                "Sound wave, acoustic diagram, or frequency visualisation as image. "
                "No labels, no numbers. Subject: {summary}. "
                "The shape of something heard — or designed not to be heard."
            ),
            "INTIMATE": (
                "Sonogram or oscilloscope trace as intimate image. "
                "A waveform that belongs to one specific moment. Subject: {summary}. "
                "The signature of a sound, not a sound in general."
            ),
            "ABSTRACT": (
                "Interference pattern or standing wave rendered as abstract composition. "
                "No text, no scale. Concept: {summary}. "
                "Physics made visual — the structure of a phenomenon, not its measurement."
            ),
        },
    ],
    "Maya Flux": [
        {   # sub-style 0: street documentary / zine
            "CONFRONTING": (
                "Street-level documentary energy. Photocopied or high-contrast photography-derived graphic. "
                "Urgency, immediacy, no text. Subject: {summary}. "
                "Flyered walls, protest banners, community notice boards. "
                "Gritty texture. Colors of the city, not the gallery."
            ),
            "INTIMATE": (
                "Urban detail study. A texture, surface, or found pattern from built environment. "
                "Photography-derived, specific place, specific light. Subject: {summary}. "
                "Ground level — cracked pavement, worn signage, shadow on concrete."
            ),
            "ABSTRACT": (
                "Urban infrastructure abstracted — transit map fragment, zoning grid, "
                "crowd density — as pure visual field. No text, no labels. "
                "Concept: {summary}. The geometry of cities without human scale."
            ),
        },
        {   # sub-style 1: protest graphic / activist print
            "CONFRONTING": (
                "Activist screen print or woodcut. Bold, handmade energy, no text. "
                "Subject: {summary}. "
                "The visual tradition of labour organizing, tenant rights, disability justice movements — "
                "direct, confrontational, made to be reproduced."
            ),
            "INTIMATE": (
                "Photocopied flyer or community newsletter detail — the texture of "
                "self-published, distributed by hand. Subject: {summary}. "
                "Slightly misregistered, slightly worn. Made by someone who needed to make it."
            ),
            "ABSTRACT": (
                "Crowd or assembly rendered as abstract pattern. "
                "Many bodies becoming a field, a texture, a force. No faces, no text. "
                "Concept: {summary}. The visual weight of collective presence."
            ),
        },
        {   # sub-style 2: urban texture / material
            "CONFRONTING": (
                "Material texture of the built environment as confrontational image. "
                "Concrete, tile, glass, steel — the surfaces that decide who moves freely. "
                "No text. Subject: {summary}. "
                "Close, almost abstract, but recognisably urban."
            ),
            "INTIMATE": (
                "Found object or worn surface — a handrail, a threshold, a kerb edge. "
                "The material where policy meets body. Subject: {summary}. "
                "Specific. The thing itself, not a symbol of the thing."
            ),
            "ABSTRACT": (
                "Aerial view of city block, street grid, or building footprint — "
                "rendered as flat graphic composition. No labels, no text. "
                "Concept: {summary}. "
                "Planning as image: who the city was designed for, visible from above."
            ),
        },
    ],
}

# Fallback for unknown personas
DEFAULT_STYLE = [
    {
        "CONFRONTING": (
            "Bold editorial illustration. Strong graphic composition, no text. "
            "Subject: {summary}. "
            "The visual language specific to this subject — not generic, not decorative. "
            "High contrast. Colors and medium chosen for the argument."
        ),
        "INTIMATE": (
            "Close editorial illustration. Intimate, human-scale, no text. "
            "Subject: {summary}. "
            "A specific moment or detail, rendered with care. "
            "Medium and palette fitting the mood — not imposed from outside."
        ),
        "ABSTRACT": (
            "Conceptual image — pure form, no figures, no text. "
            "Concept: {summary}. "
            "The idea made visual in a way specific to this concept. "
            "Medium and color chosen for meaning, not convention."
        ),
    },
]

ALT_TEMPLATES = {
    "CONFRONTING": "{title} — editorial illustration",
    "INTIMATE":    "{title} — detail illustration",
    "ABSTRACT":    "{title} — conceptual image",
}


def _sub_style_index(slug: str, persona: str, num_styles: int) -> int:
    """Pick sub-style deterministically from slug so same article always gets same style."""
    h = sum(ord(c) for c in (slug + persona))
    return h % num_styles


def get_prompt(style_key: str, persona: str, summary: str, slug: str = "") -> str:
    style_list = PERSONA_STYLES.get(persona, DEFAULT_STYLE)
    idx = _sub_style_index(slug, persona, len(style_list))
    return style_list[idx][style_key].format(summary=summary)

RETRY_DELAYS = [5, 15, 45]  # seconds between retries


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def has_image_field(text: str) -> bool:
    return bool(re.search(r"^image:", text, re.MULTILINE))


def inject_image_fields(post_path: pathlib.Path, image_rel: str, alt_text: str) -> None:
    text = post_path.read_text()
    if has_image_field(text):
        return
    # Insert image fields at end of frontmatter block, before closing ---
    m = re.match(r"^(---\n.*?)(\n---\n)", text, re.DOTALL)
    if not m:
        print(f"  [warn] could not locate frontmatter in {post_path.name}", file=sys.stderr)
        return
    new_text = (
        m.group(1)
        + f'\nimage: {image_rel}\nimage_alt: "{alt_text}"'
        + m.group(2)
        + text[m.end():]
    )
    post_path.write_text(new_text)


# ---------------------------------------------------------------------------
# Slug / summary
# ---------------------------------------------------------------------------

def slug_from_path(p: pathlib.Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)


def build_summary(fm: dict) -> str:
    parts = []
    if fm.get("title"):
        parts.append(fm["title"])
    if fm.get("excerpt"):
        parts.append(fm["excerpt"][:150])
    if fm.get("keywords"):
        kw_raw = fm["keywords"].strip("[]").replace('"', "").replace("'", "")
        kw = [k.strip() for k in kw_raw.split(",") if k.strip()][:5]
        if kw:
            parts.append(", ".join(kw))
    return ". ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def call_openrouter(prompt: str, aspect_ratio: str, model: str, api_key: str) -> bytes:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image"],
        "image_config": {
            "aspect_ratio": aspect_ratio,
            "image_size": "1K",
        },
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cripminds.com",
            "X-Title": "cripminds image generator",
        },
        method="POST",
    )

    for attempt, delay in enumerate([0] + RETRY_DELAYS, 1):
        if delay:
            print(f"    retry {attempt} in {delay}s...", file=sys.stderr)
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
            return _extract_image_bytes(result)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 429 or e.code >= 500:
                print(f"    HTTP {e.code}: {body[:200]}", file=sys.stderr)
                if attempt > len(RETRY_DELAYS):
                    raise
                continue
            raise RuntimeError(f"HTTP {e.code}: {body[:400]}") from e

    raise RuntimeError("All retries exhausted")


def _extract_image_bytes(result: dict) -> bytes:
    try:
        msg = result["choices"][0]["message"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected response shape: {json.dumps(result)[:300]}") from e

    # Format 1: images array (Recraft, most models)
    images = msg.get("images") or []
    if images:
        data_url = images[0]["image_url"]["url"]
        b64 = data_url.split(",", 1)[1] if "," in data_url else data_url
        return base64.b64decode(b64)

    # Format 2: embedded in content as data URL
    content = msg.get("content") or ""
    m = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", content)
    if m:
        return base64.b64decode(m.group(1))

    raise ValueError(f"No image found in response: {json.dumps(result)[:400]}")


# ---------------------------------------------------------------------------
# Save image
# ---------------------------------------------------------------------------

def save_image(data: bytes, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.save(path, "JPEG", quality=90, optimize=True)
    except ImportError:
        # PIL not available — write raw bytes (PNG content, .jpg ext — fine for browsers)
        path.write_bytes(data)


# ---------------------------------------------------------------------------
# Process posts
# ---------------------------------------------------------------------------

def find_posts_needing_images(target_slug: str | None = None, force: bool = False) -> list[pathlib.Path]:
    posts = sorted(POSTS_DIR.glob("*.md"))
    result = []
    for p in posts:
        if target_slug and slug_from_path(p) != target_slug:
            continue
        text = p.read_text()
        if has_image_field(text) and not force:
            continue
        slug = slug_from_path(p)
        setting1 = ASSETS_DIR / f"{slug}_setting_1.jpg"
        if setting1.exists() and not target_slug and not force:
            # Images exist but frontmatter wasn't updated — fix that
            fm = parse_frontmatter(text)
            alt = ALT_TEMPLATES["CONFRONTING"].format(title=fm.get("title", slug))
            inject_image_fields(p, f"/assets/{slug}_setting_1.jpg", alt)
            print(f"[fixed] frontmatter for {p.name}")
            continue
        result.append(p)
    return result


def process_post(post_path: pathlib.Path, model: str, api_key: str, dry_run: bool) -> bool:
    text = post_path.read_text()
    fm = parse_frontmatter(text)
    slug = slug_from_path(post_path)
    summary = build_summary(fm)
    title = fm.get("title", slug)
    persona = fm.get("author", "")

    print(f"\n[{post_path.name}]")
    print(f"  title:   {title[:80]}")
    print(f"  persona: {persona or '(default)'}")
    print(f"  summary: {summary[:100]}...")

    if dry_run:
        for suffix, ratio, style_key in IMAGE_TYPES:
            dest = ASSETS_DIR / f"{slug}_{suffix}.jpg"
            print(f"  would generate: {dest.name} ({ratio}, {style_key})")
        return True

    success = True
    for suffix, ratio, style_key in IMAGE_TYPES:
        dest = ASSETS_DIR / f"{slug}_{suffix}.jpg"
        if dest.exists():
            print(f"  skip (exists): {dest.name}")
            continue

        prompt = get_prompt(style_key, persona, summary, slug)
        print(f"  generating {dest.name} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            data = call_openrouter(prompt, ratio, model, api_key)
            save_image(data, dest)
            print(f"ok ({time.time()-t0:.1f}s, {len(data)//1024}KB)")
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)
            success = False
            continue

        time.sleep(1.5)  # be polite between images

    if success:
        # Update frontmatter with setting_1 as the article hero image
        alt = ALT_TEMPLATES["CONFRONTING"].format(title=title)
        inject_image_fields(post_path, f"/assets/{slug}_setting_1.jpg", alt)
        print(f"  frontmatter updated")

    return success


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cripminds article images via OpenRouter")
    parser.add_argument("--slug", help="Process only this article slug")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run, don't call API")
    parser.add_argument("--force", action="store_true", help="Process even if image: already in frontmatter (use with --slug)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenRouter model (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key and not args.dry_run:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    posts = find_posts_needing_images(args.slug, force=getattr(args, 'force', False))

    if not posts:
        print("All posts have images. Nothing to do.")
        return

    print(f"Found {len(posts)} post(s) needing images")
    if not args.dry_run:
        cost_est = len(posts) * 3 * 0.04
        print(f"Estimated cost: ~${cost_est:.2f} at $0.04/image ({args.model})")
        print()

    failed = []
    for post_path in posts:
        ok = process_post(post_path, args.model, api_key, args.dry_run)
        if not ok:
            failed.append(post_path.name)

    print(f"\n{'[dry-run] ' if args.dry_run else ''}Done. {len(posts)-len(failed)}/{len(posts)} succeeded.")
    if failed:
        print("Failed:", ", ".join(failed))
        sys.exit(1)

    if not args.dry_run:
        print("\nNext: git add assets/ _posts/ && git commit -m 'feat: generate article images' && git push")


if __name__ == "__main__":
    main()

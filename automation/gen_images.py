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

# Cripminds palette: crimson · near-black · warm cream
# Recraft rgb_colors constrains the palette used in generation
PALETTE = [[220, 38, 38], [22, 22, 22], [240, 234, 220]]

# image type → (filename_suffix, aspect_ratio, style_key)
IMAGE_TYPES = [
    ("setting_1", "16:9", "CONFRONTING"),
    ("moment_2",  "1:1",  "INTIMATE"),
    ("symbol_3",  "1:1",  "ABSTRACT"),
]

PROMPTS = {
    "CONFRONTING": (
        "Screen-print protest poster. Bold flat graphic silhouette. Halftone dot texture. "
        "8-bit pixel grid overlay. High contrast. No text, no typography. "
        "Topic: {summary}. "
        "Aesthetic: Corita Kent meets disability justice activism. "
        "Crimson, near-black, warm cream. Strong confrontational composition."
    ),
    "INTIMATE": (
        "Gouache illustration on textured watercolour paper. "
        "Pixel scan-line overlay at edges, 8-bit color banding. "
        "Close-up intimate scene, no text. Topic: {summary}. "
        "Hand-painted warmth. Flat illustration, muted palette with one accent color. "
        "Soft grain texture throughout."
    ),
    "ABSTRACT": (
        "Linocut relief print. Bold hand-cut marks on textured paper. "
        "Abstract geometric symbol or pattern evoking: {summary}. "
        "Pixel art border pattern. Pure graphic abstraction — no faces, no text, no figures. "
        "Black marks on warm cream ground with crimson accent."
    ),
}

ALT_TEMPLATES = {
    "CONFRONTING": "{title} — screen-print protest poster illustration",
    "INTIMATE":    "{title} — intimate gouache illustration on textured paper",
    "ABSTRACT":    "{title} — abstract linocut symbol",
}

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
            "rgb_colors": PALETTE,
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

    print(f"\n[{post_path.name}]")
    print(f"  title:   {title[:80]}")
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

        prompt = PROMPTS[style_key].format(summary=summary)
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

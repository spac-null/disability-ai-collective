#!/usr/bin/env python3
"""
Inject moment_2 and symbol_3 images into article bodies for all posts
that have image files but no <figure> tags in the body yet.

Usage:
    python3 automation/inject_body_images.py
    python3 automation/inject_body_images.py --dry-run
    python3 automation/inject_body_images.py --slug the-upgrade-assumes-a-body-that-was-working-before
"""

import argparse
import pathlib
import re
import sys

REPO_ROOT  = pathlib.Path(__file__).parent.parent
POSTS_DIR  = REPO_ROOT / "_posts"
ASSETS_DIR = REPO_ROOT / "assets"

ALT_TEMPLATES = {
    "moment_2":  "{title} — intimate gouache illustration on textured paper",
    "symbol_3":  "{title} — abstract linocut symbol",
}


def slug_from_path(p: pathlib.Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)


def parse_title(text: str) -> str:
    m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    return m.group(1).strip('"\'') if m else ""


def split_frontmatter(text: str):
    """Return (frontmatter_block, body) where frontmatter_block includes both --- delimiters."""
    m = re.match(r"^(---\n.*?\n---\n)", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def has_body_images(body: str) -> bool:
    return "article-figure" in body


def target_paragraph(paragraphs: list, pct: float) -> int:
    total = len(paragraphs)
    idx = int(total * pct)
    for offset in range(0, min(5, total - idx)):
        p = paragraphs[idx + offset].strip()
        if p and not p.startswith('#') and not p.startswith('!') and not p.startswith('<'):
            return idx + offset
    return min(idx, total - 1)


def build_figure(slug: str, suffix: str, alt: str) -> str:
    fname = f"{slug}_{suffix}.jpg"
    caption = f'\n<figcaption>{alt}</figcaption>' if alt else ''
    return (
        f'<figure class="article-figure">\n'
        f'<img src="{{{{ site.baseurl }}}}/assets/{fname}" alt="{alt}" '
        f'width="800" height="450" loading="lazy" decoding="async">{caption}\n'
        f'</figure>'
    )


def inject_images(post_path: pathlib.Path, dry_run: bool) -> bool:
    text = post_path.read_text()
    fm, body = split_frontmatter(text)
    if not fm:
        print(f"  [skip] no frontmatter: {post_path.name}", file=sys.stderr)
        return False

    if has_body_images(body):
        return False  # already done

    slug = slug_from_path(post_path)
    title = parse_title(fm)

    # Determine which images exist
    inserts = []
    for suffix, pct in [("moment_2", 0.40), ("symbol_3", 0.75)]:
        img_path = ASSETS_DIR / f"{slug}_{suffix}.jpg"
        if img_path.exists():
            alt = ALT_TEMPLATES[suffix].format(title=title)
            inserts.append((pct, suffix, alt))

    if not inserts:
        return False  # no images to inject

    if dry_run:
        print(f"  would inject: {[s for _, s, _ in inserts]}")
        return True

    paragraphs = body.split('\n\n')

    # Insert in reverse order so earlier inserts don't shift later positions
    for pct, suffix, alt in sorted(inserts, key=lambda x: x[0], reverse=True):
        idx = target_paragraph(paragraphs, pct)
        fig = build_figure(slug, suffix, alt)
        paragraphs.insert(idx + 1, fig)

    new_body = '\n\n'.join(paragraphs)
    post_path.write_text(fm + new_body)
    return True


def main():
    parser = argparse.ArgumentParser(description="Inject body images into articles that have image files but no figure tags")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--slug", help="Process only this article slug")
    args = parser.parse_args()

    posts = sorted(POSTS_DIR.glob("*.md"))
    if args.slug:
        posts = [p for p in posts if slug_from_path(p) == args.slug]

    updated = 0
    skipped_no_images = 0
    skipped_already_done = 0

    for post_path in posts:
        text = post_path.read_text()
        _, body = split_frontmatter(text)
        slug = slug_from_path(post_path)

        if has_body_images(body):
            skipped_already_done += 1
            continue

        has_any = any(
            (ASSETS_DIR / f"{slug}_{s}.jpg").exists()
            for s in ("moment_2", "symbol_3")
        )
        if not has_any:
            skipped_no_images += 1
            continue

        print(f"{'[dry-run] ' if args.dry_run else ''}inject: {post_path.name}")
        if inject_images(post_path, args.dry_run):
            updated += 1

    print(f"\nDone: {updated} updated, {skipped_already_done} already had images, {skipped_no_images} no image files yet.")
    if updated and not args.dry_run:
        print("\nNext: git add _posts/ && git commit -m 'feat: inject body images into articles' && git push origin main")


if __name__ == "__main__":
    main()

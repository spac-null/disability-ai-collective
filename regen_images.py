#!/usr/bin/env python3
"""
Regenerate all article images using the updated SceneImageGenerator
(vibrant dis.art aesthetic — no dark noir)
"""

import os
import re
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Run from workspace root
WORKSPACE = Path('/srv/data/openclaw/workspaces/ops/disability-ai-collective')
os.chdir(WORKSPACE)
sys.path.insert(0, str(WORKSPACE))

from scene_image_generator import SceneImageGenerator

# Auto-load API key if not set
if not os.environ.get("POLLINATIONS_API_KEY"):
    secrets_path = "/srv/secrets/openclaw.env"
    try:
        with open(secrets_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("POLLINATIONS_API_KEY=") and not line.startswith("#"):
                    os.environ["POLLINATIONS_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                    logger.info("Loaded POLLINATIONS_API_KEY from %s", secrets_path)
                    break
    except Exception as e:
        logger.warning("Could not load API key from %s: %s", secrets_path, e)


def extract_title(content):
    m = re.search(r'''(?m)^title:\s*"([^"]+)"''', content)
    if not m:
        m = re.search(r"""(?m)^title:\s+'([^']+)'""", content)
    if not m:
        m = re.search(r'''(?m)^title:\s*(.+)''', content)
    if m:
        return m.group(1).strip()
    return "Article"

def update_article_images(post_path, slug, new_images):
    """Update frontmatter image: and body ![...] refs in article."""
    with open(post_path, 'r') as f:
        content = f.read()

    # Update frontmatter image: field
    if new_images:
        first_filename = new_images[0]['filename']
        content = re.sub(
            r'^(image:\s*/assets/)[\S]+',
            f'image: /assets/{first_filename}',
            content,
            flags=re.MULTILINE
        )

    # Update body image references — match by label (setting, moment, symbol)
    label_map = {'setting': 0, 'moment': 1, 'symbol': 2}
    for label, idx in label_map.items():
        if idx < len(new_images):
            new_filename = new_images[idx]['filename']
            # Replace any existing ref with old slug_label pattern
            content = re.sub(
                r'(\{\{ site\.baseurl \}\}/assets/)[^\)]+_' + label + r'_\d+\.(jpg|png)',
                r'\g<1>' + new_filename,
                content
            )

    with open(post_path, 'w') as f:
        f.write(content)
    logger.info(f"  Updated image refs in {post_path.name}")

def main():
    gen = SceneImageGenerator()
    posts_dir = WORKSPACE / '_posts'
    assets_dir = WORKSPACE / 'assets'
    assets_dir.mkdir(exist_ok=True)

    post_files = sorted(posts_dir.glob('2026-03-*.md'))
    logger.info(f"Found {len(post_files)} articles to process")

    results = []
    for post_path in post_files:
        logger.info(f"\nProcessing: {post_path.name}")
        try:
            with open(post_path, 'r') as f:
                content = f.read()

            title = extract_title(content)
            # Derive slug from filename (strip date prefix + .md)
            slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', post_path.stem)
            logger.info(f"  Title: {title}")
            logger.info(f"  Slug: {slug}")

            images = gen.generate_content_aware_images(content, title, slug, num_images=3)

            saved = []
            for img in images:
                filepath = assets_dir / img['filename']
                with open(filepath, 'wb') as f:
                    f.write(img['data'])
                size_kb = len(img['data']) / 1024
                logger.info(f"  Saved {img['filename']} ({size_kb:.0f}KB, score={img.get('score',0)})")
                saved.append(img)

            # Update article references
            update_article_images(post_path, slug, saved)
            results.append({'article': post_path.name, 'images': len(saved), 'ok': True})

        except Exception as e:
            logger.error(f"  FAILED {post_path.name}: {e}")
            results.append({'article': post_path.name, 'ok': False, 'error': str(e)})

    print("\n--- SUMMARY ---")
    for r in results:
        status = "OK" if r['ok'] else f"FAILED: {r.get('error','?')}"
        images = r.get('images', 0)
        print(f"  {r['article']}: {status} ({images} images)")

if __name__ == '__main__':
    main()

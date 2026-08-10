"""
images.py — article image generation and body-image insertion.

Extracted 2026-08-09 (module-split, Stage 3 continued). Three methods moved
together because they form one real unit: generate_images() produces the
files, _pick_by_suffix() looks them up by filename suffix (not list position
-- see its own docstring for why), and _insert_images_balanced() places two of
the three into the article body. Zero behavior change -- bodies copied verbatim,
confirmed via direct substring containment against git HEAD.
"""
import re
import sys


class ImagesMixin:
    def generate_images(self, content, slug, num_images=3, title=None, persona=None,
                         excerpt=None, keywords=None, image_briefs=None):
        """Generate article images via OpenRouter (Recraft V4.1).

        Three images per article:
          {slug}_setting_1.jpg — confronting screen-print, 16:9 (hero)
          {slug}_moment_2.jpg  — intimate gouache, 1:1 (body 40%)
          {slug}_symbol_3.jpg  — abstract linocut, 1:1 (body 75%)

        Requires OPENROUTER_API_KEY in environment.
        Returns (image_filenames, image_descriptions).
        Skips files that already exist (safe to re-run).

        excerpt/keywords/image_briefs (added 2026-08-10): this used to try rebuilding
        frontmatter by re-scanning `content` for "---" lines, but at this pipeline
        stage `content` is the article BODY ONLY (frontmatter is assembled later, in
        create_article_file) -- the scan hit the body's own first horizontal rule and
        stopped, so every prompt reached the model with nothing but the title.
        Callers now pass the real excerpt/keywords (already generated for the
        frontmatter -- see generate.py) and image_briefs (three concrete,
        article-specific visual details -- see _generate_image_briefs in
        content_checks.py) so prompts are actually grounded in the piece.
        """
        import os as _os
        import time as _time
        import pathlib as _pathlib
        sys.path.insert(0, str(_pathlib.Path(__file__).parent))
        try:
            from gen_images import (
                call_openrouter, save_image,
                IMAGE_TYPES, ALT_TEMPLATES, build_summary, get_prompt,
            )
        except ImportError as e:
            self.logger.error(f"Could not import gen_images: {e}")
            return [], []

        api_key = _os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            self.logger.error("OPENROUTER_API_KEY not set — skipping image generation")
            return [], []

        title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', content)
        title = title or (title_match.group(1).strip('"\'') if title_match else slug)
        persona = persona or ''

        fallback_summary = build_summary({
            "title": title,
            "excerpt": excerpt or "",
            "keywords": ", ".join(keywords) if keywords else "",
        })

        # Each slot gets its own role-appropriate concrete detail instead of the
        # same generic summary three times -- see _generate_image_briefs's
        # docstring for why the three roles are thing/gesture/mechanism. Falls
        # back to the title+excerpt+keywords summary per-slot if brief extraction
        # failed or came back empty for that role, so a partial/failed extraction
        # degrades gracefully rather than blocking image generation.
        image_briefs = image_briefs or {}
        SLOT_BRIEF_KEY = {"CONFRONTING": "thing", "INTIMATE": "gesture", "ABSTRACT": "mechanism"}

        image_filenames = []
        image_descriptions = []

        for suffix, ratio, style_key in IMAGE_TYPES[:num_images]:
            fname = f"{slug}_{suffix}.jpg"
            dest = self.assets_dir / fname
            alt = ALT_TEMPLATES[style_key].format(title=title)

            if dest.exists():
                self.logger.info(f"Image exists, skipping: {fname}")
                image_filenames.append(fname)
                image_descriptions.append(alt)
                continue

            brief = image_briefs.get(SLOT_BRIEF_KEY.get(style_key, ""))
            summary = f"{title}. {brief}" if brief else fallback_summary

            # slug is required for get_prompt's deterministic per-article sub-style
            # pick (gen_images._sub_style_index) — omitting it collapses the index to
            # sum(ord(c) for c in persona) % 3, a per-persona CONSTANT, silently
            # nullifying the "3 sub-styles per persona" feature (38b1535): every
            # article from a given persona got the exact same sub-style.
            prompt = get_prompt(style_key, persona, summary, slug)
            self.logger.info(f"Generating {fname} via OpenRouter...")
            try:
                data = call_openrouter(prompt, ratio, "recraft/recraft-v4.1", api_key)
                save_image(data, dest)
                image_filenames.append(fname)
                image_descriptions.append(alt)
                self.logger.info(f"Generated {fname} ({len(data)//1024}KB)")
            except Exception as e:
                self.logger.error(f"Image generation failed for {fname}: {e}")
            _time.sleep(1.5)

        return image_filenames, image_descriptions

    @staticmethod
    def _pick_by_suffix(image_filenames, image_descriptions, suffix):
        """Find the (filename, description) pair whose filename carries this suffix
        (e.g. "_setting_1"), regardless of position in the list.

        generate_images() only appends filenames for images that actually succeeded
        — if generation partially fails, the list can be any subset in any order
        (e.g. just [..._moment_2.jpg, ..._symbol_3.jpg] if setting_1 alone failed).
        Code that indexed image_filenames[0]/[1]/[2] as if they were always
        hero/40%/75% would silently promote the wrong image to hero and shift the
        rest into the wrong body slots whenever one generation failed.
        """
        if not image_descriptions:
            image_descriptions = [''] * len(image_filenames)
        for i, fname in enumerate(image_filenames):
            if suffix in fname:
                return fname, (image_descriptions[i] if i < len(image_descriptions) else '')
        return None, ''

    def _insert_images_balanced(self, content, image_filenames, image_descriptions=None):
        """Insert body images at ~40% and ~75% of article content.

        _setting_1 = hero — already in frontmatter, not repeated here.
        _moment_2  = inserted at ~40%, if present.
        _symbol_3  = inserted at ~75%, if present.
        Each looked up by filename suffix, not list position — see _pick_by_suffix.
        """
        moment_fname, moment_desc = self._pick_by_suffix(image_filenames, image_descriptions, '_moment_2')
        symbol_fname, symbol_desc = self._pick_by_suffix(image_filenames, image_descriptions, '_symbol_3')
        if not moment_fname and not symbol_fname:
            return content

        paragraphs = content.split('\n\n')
        total = len(paragraphs)

        def target_idx(pct):
            idx = int(total * pct)
            for offset in range(0, min(5, total - idx)):
                p = paragraphs[idx + offset].strip()
                if p and not p.startswith('#') and not p.startswith('!'):
                    return idx + offset
            return min(idx, total - 1)

        inserts = []
        if moment_fname:
            inserts.append((target_idx(0.40), moment_fname, moment_desc))
        if symbol_fname:
            inserts.append((target_idx(0.75), symbol_fname, symbol_desc))

        for idx, fname, desc in sorted(inserts, key=lambda t: t[0], reverse=True):
            caption = f'\n<figcaption>{desc}</figcaption>' if desc else ''
            img_tag = f'<figure class="article-figure">\n<img src="{{{{ site.baseurl }}}}/assets/{fname}" alt="{desc}" width="800" height="450" loading="lazy" decoding="async">{caption}\n</figure>'
            paragraphs.insert(idx + 1, img_tag)

        return '\n\n'.join(paragraphs)

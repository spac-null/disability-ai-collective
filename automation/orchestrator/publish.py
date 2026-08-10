"""
publish.py — write the article file to disk and commit/push it to git.

Extracted 2026-08-09 (module-split, Stage 3 continued). Three methods that form
one real pipeline stage: create_article_file() assembles front matter + body
and writes _drafts/<file>.md, commit_to_git() stages and commits it (plus any
generated images and the review sidecar), _git_push_safe() does the actual
push with a stash/pull-rebase/pop dance to survive a diverged remote. Zero
behavior change -- bodies copied verbatim, confirmed via direct substring
containment against git HEAD.
"""
import json
import os
import subprocess

import yaml


class PublishMixin:
    def _pipeline_version(self):
        """Read the site's current pipeline version/codename from _config.yml.

        Stamped into each article's own frontmatter at creation time (see
        create_article_file below) so it survives future version bumps as a
        permanent per-article record -- lets quality/approach be compared
        across time as the pipeline evolves, instead of every article only
        ever reflecting whatever _config.yml says today.
        """
        try:
            with open(self.repo_root / "_config.yml", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            return cfg.get("version"), cfg.get("codename")
        except Exception as e:
            self.logger.debug("Could not read pipeline version from _config.yml: %s", e)
            return None, None

    def create_article_file(self, metadata, content, image_filenames, image_descriptions=None):
        """Create properly formatted article file in _drafts/ (publish-best.py promotes to _posts/)."""
        filename = metadata['filename']
        filepath = self.drafts_dir / filename

        # Reuse excerpt/keywords if the caller already computed them (generate.py does,
        # so image generation can see them too -- see its Step 4c) rather than paying
        # for the same two LLM calls again.
        excerpt = metadata.get('excerpt') or self._generate_card_excerpt(metadata['title'], content, metadata.get('author', ''))
        keywords = metadata.get('keywords') or self._generate_keywords(metadata['title'], content, metadata.get('author', ''), metadata['categories'])

        _source_fields = ""
        if metadata.get('source_url'):
            _source_fields += f"\nsource_url: {json.dumps(str(metadata['source_url']))}"
        if metadata.get('source_title'):
            _source_fields += f"\nsource_title: {json.dumps(str(metadata['source_title']))}"
        if metadata.get('source_outlet'):
            _source_fields += f"\nsource_outlet: {json.dumps(str(metadata['source_outlet']))}"

        _score_field = ""
        if metadata.get('editorial_score') is not None:
            _score_field = f"\ndraft_score: {metadata['editorial_score']}"

        _pipeline_version, _pipeline_codename = self._pipeline_version()
        _version_field = ""
        if _pipeline_version:
            _version_field += f"\npipeline_version: {json.dumps(str(_pipeline_version))}"
        if _pipeline_codename:
            _version_field += f"\npipeline_codename: {json.dumps(str(_pipeline_codename))}"

        # Hero is _setting_1 by suffix, not image_filenames[0] by position — the
        # list only contains whichever images actually succeeded, so if setting_1
        # specifically failed, [0] would silently be a 1:1 body image used as the
        # 16:9 hero. Fall back to whatever did generate, then to the site's
        # existing generic OG card (default.png was referenced here but was never
        # a real file in this repo — a guaranteed 404 the day all three fail).
        hero_fname, hero_desc = self._pick_by_suffix(image_filenames, image_descriptions, '_setting_1')
        if not hero_fname and image_filenames:
            hero_fname = image_filenames[0]
            hero_desc = image_descriptions[0] if image_descriptions else ''
        if not hero_fname:
            hero_fname, hero_desc = 'og-card.png', 'Crip Minds'

        front_matter = f"""---
layout: post
title: {json.dumps(str(metadata['title']))}
date: {metadata['date']}
author: {json.dumps(str(metadata['author']))}
category: {metadata['categories'][0].lower() if metadata['categories'] else 'research'}
image: /assets/{hero_fname}
image_alt: {json.dumps(hero_desc or 'Article illustration')}
excerpt: {json.dumps(excerpt)}
keywords: [{', '.join(keywords)}]{_source_fields}{_score_field}{_version_field}
---

"""

        # Insert body images at balanced positions (hero image[0] is frontmatter only)
        body = self._insert_images_balanced(content, image_filenames, image_descriptions)
        body = self.smart_inject_links(body)
        body = self.inject_canonical_links(body)  # canonical fallback

        # Append source note at end of article (not as excerpt/subtitle)
        if metadata.get('source_note'):
            body = body.rstrip() + '\n\n---\n\n' + metadata['source_note'] + '\n'

        full_content = front_matter + body

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        self.logger.info(f"Article file created: {filepath}")
        return filepath

    def commit_to_git(self, article_file, image_filenames, review_file=None):
        """Commit changes to git repository."""
        try:
            # Change to repo directory
            os.chdir(self.repo_root)
            
            # Add files
            if not article_file.exists():
                raise FileNotFoundError(f"Article file missing before commit: {article_file}")
            subprocess.run(['git', 'add', str(article_file)], check=True)
            
            # Add image files (if they exist)
            for img in image_filenames:
                img_path = self.assets_dir / img
                if img_path.exists():
                    subprocess.run(['git', 'add', str(img_path)], check=True)
            if review_file and review_file.exists():
                subprocess.run(['git', 'add', str(review_file)], check=True)
            
            # Commit
            commit_msg = f"Add new article: {article_file.stem}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push (pull --rebase first to avoid rejection if remote diverged)
            self._git_push_safe()

            self.logger.info("Successfully committed and pushed to repository")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e}")
            return False


    def _git_push_safe(self, cwd=None):
        """Pull --rebase before pushing to avoid rejection when remote has diverged."""
        wd = str(cwd or self.repo_root)
        stashed = False
        try:
            result = subprocess.run(['git', 'stash', '--include-untracked'], check=True, cwd=wd, capture_output=True, text=True)
            stashed = 'No local changes' not in result.stdout
            subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], check=True, cwd=wd)
            if stashed:
                subprocess.run(['git', 'stash', 'pop'], check=True, cwd=wd)
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, cwd=wd)
        except subprocess.CalledProcessError as e:
            if stashed:
                subprocess.run(['git', 'stash', 'pop'], cwd=wd)
            raise e

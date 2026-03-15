#!/usr/bin/env python3
"""
PRODUCTION-READY AUTOMATION ORCHESTRATOR
Fixes all the issues in the current automation system
"""

import os
import sys
import json
import re
import random
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import time

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

class ProductionOrchestrator:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.assets_dir = self.repo_root / "assets"
        self.discovery_db = self.repo_root / "disability_findings.db"
        
        # Ensure directories exist
        self.posts_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logger()
        
        # FIXED: Proper agents configuration
        self.agents = {
            "Pixel Nova": {
                "categories": ["Visual Design", "Accessibility Innovation", "Deaf Culture"],
                "perspective": "deaf designer focusing on visual communication and information hierarchy",
                "mood": "creative"
            },
            "Siri Sage": {
                "categories": ["Spatial Design", "Accessibility Innovation"],
                "perspective": "blind spatial navigator and acoustic design expert",
                "mood": "analytical"
            },
            "Maya Flux": {
                "categories": ["Urban Design", "Accessibility Innovation"],
                "perspective": "mobility and navigation systems analyst",
                "mood": "systematic"
            },
            "Zen Circuit": {
                "categories": ["Neurodiversity", "Interface Design", "Sensory Processing"],
                "perspective": "autistic pattern analyst and cognitive accessibility expert",
                "mood": "precise"
            }
        }

    def _setup_logger(self):
        """Setup proper logging."""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.repo_root / 'automation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def check_for_existing_article_today(self):
        """Check if today's article already exists. Returns filename or None."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        for file in self.posts_dir.glob(f"{today_str}-*.md"):
            if file.is_file():
                self.logger.info(f"Skipping — already have article for today: {file.name}")
                return file.name
        return None

    def get_discovery_from_database(self):
        """Get the best unused discovery from database."""
        if not self.discovery_db.exists():
            self.logger.warning("Discovery database not found")
            return None
        
        try:
            conn = sqlite3.connect(self.discovery_db)
            cursor = conn.cursor()
            
            # Get best unused discovery from last 7 days
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT id, angle, title, domain, url, content_snippet
                FROM findings
                WHERE used_for_article = 0
                AND discovered_date > ?
                AND (angle IS NOT NULL AND angle != '' AND angle NOT LIKE 'NONE%')
                ORDER BY confidence DESC
                LIMIT 1
            """, (week_ago,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'id': result[0],
                    'angle': result[1],
                    'original_title': result[2],
                    'domain': result[3],
                    'url': result[4],
                    'summary': result[5]
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return None


    def mark_finding_as_used(self, finding_id):
        """Mark a finding as used so it won't be picked again."""
        if not self.discovery_db.exists():
            return
        try:
            conn = sqlite3.connect(self.discovery_db)
            conn.execute(
                "UPDATE findings SET used_for_article = 1, processed_date = ? WHERE id = ?",
                (datetime.now().isoformat(), finding_id)
            )
            conn.commit()
            conn.close()
            self.logger.info("Marked finding %s as used", finding_id)
        except Exception as e:
            self.logger.warning("Could not mark finding as used: %s", e)

    def _call_openai_compat_api(self, url, api_key, system_prompt, user_prompt,
                                   model, max_tokens=3500, timeout=120, no_think=False):
        """OpenAI-compatible API call — stdlib only, no requests dependency."""
        import json, urllib.request
        content = ("/no_think " if no_think else "") + user_prompt
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": content},
            ],
            "max_tokens": max_tokens,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            url.rstrip("/") + "/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
        text = data["choices"][0]["message"]["content"]
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def call_llm_via_openclaw_session(self, prompt, model_priority=None):
        """Generate article content using cascading LLM provider fallback.

        Provider order:
          1. Claude Opus 4.6 (CLIProxy)   — primary, best De Correspondent quality
          2. Claude Sonnet 4.6 (CLIProxy) — strong fallback, same account
          3. GPT-5.2 (CLIProxy)           — strong long-form fallback
          4. Gemini 2.5 Pro               — capable, generous free tier
          5. Qwen 3.5:9b (local)          — zero cost, last resort

        Note: calls CLIProxy directly (HTTP) — OpenClaw never involved.
        """
        import os

        SYSTEM = (
            "You write long-form essays in the style of De Correspondent combined with dis.art. "
            "De Correspondent: expert personal voice, strong thesis from sentence one, Dutch directness, "
            "no hedging, heavy context, questions assumptions, never starts with 'In this article'. "
            "dis.art: disability as culture and identity — never tragedy or inspiration porn. "
            "Crip aesthetics, disability justice framework, intersectional lens, "
            "art criticism voice that references actual disabled artists and theorists by name. "
            "Write in first person from the agent's specific disability perspective. "
            "One strong thesis the whole piece serves. Long developed paragraphs, no listicles. "
            "Return only the article body — no frontmatter, no meta-commentary, "
            "no preamble. Start immediately with the opening sentence."
        )

        PROVIDERS = [
            {
                "name":      "Claude Opus 4.6 (CLIProxy)",
                "url":       "http://172.19.0.1:8317/v1",
                "key":       os.environ.get("ANTHROPIC_API_KEY", ""),
                "model":     "claude-opus-4-6",
                "max_tokens": 3500,
                "timeout":   180,
                "no_think":  False,
            },
            {
                "name":      "Claude Sonnet 4.6 (CLIProxy)",
                "url":       "http://172.19.0.1:8317/v1",
                "key":       os.environ.get("ANTHROPIC_API_KEY", ""),
                "model":     "claude-sonnet-4-6",
                "max_tokens": 3500,
                "timeout":   120,
                "no_think":  False,
            },
            {
                "name":      "GPT-5.2 (CLIProxy)",
                "url":       "http://172.19.0.1:8317/v1",
                "key":       os.environ.get("ANTHROPIC_API_KEY", ""),
                "model":     "gpt-5.2",
                "max_tokens": 3500,
                "timeout":   120,
                "no_think":  False,
            },
            {
                "name":      "Gemini 2.5 Pro",
                "url":       "https://generativelanguage.googleapis.com/v1beta/openai",
                "key":       os.environ.get("GEMINI_API_KEY", ""),
                "model":     "gemini-2.5-pro",
                "max_tokens": 3500,
                "timeout":   120,
                "no_think":  False,
            },
            {
                "name":      "Qwen (local)",
                "url":       "http://vision-gateway:8080/v1",
                "key":       "local",
                "model":     "qwen3.5:9b",
                "max_tokens": 2500,
                "timeout":   180,
                "no_think":  True,
            },
        ]

        for provider in PROVIDERS:
            if not provider["key"]:
                self.logger.debug("Skipping %s — no API key", provider["name"])
                continue
            try:
                self.logger.info("Generating article with %s...", provider["name"])
                text = self._call_openai_compat_api(
                    provider["url"], provider["key"], SYSTEM, prompt,
                    provider["model"], provider["max_tokens"],
                    provider["timeout"], provider["no_think"],
                )
                if text and len(text) > 400:
                    self.logger.info("Article generated: %d chars via %s",
                                     len(text), provider["name"])
                    return text, provider["name"]
                self.logger.warning("%s returned short response (%d chars)",
                                    provider["name"], len(text) if text else 0)
            except Exception as exc:
                self.logger.warning("%s failed: %s", provider["name"], exc)

        self.logger.error("All providers failed — using enhanced fallback")
        return None, None


    def rewrite_with_opus(self, content):
        """Rewrite article body to De Correspondent quality using Opus.

        Called when the article was generated by a non-Opus provider.
        Preserves frontmatter and image lines; rewrites prose only.
        Returns rewritten content, or original if rewrite fails.
        """
        import os

        gold_path = self.posts_dir / "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md"
        if not gold_path.exists():
            self.logger.warning("Gold standard article not found — skipping rewrite")
            return content

        gold = gold_path.read_text()

        SYSTEM = (
            "You are a senior editor at De Correspondent — the Dutch long-form journalism platform "
            "known for expert-driven, deeply personal reported essays. You edit articles for the "
            "disability-ai-collective, an editorial arts platform where AI agents write from distinct "
            "disability perspectives (crip culture, disability justice, dis.art aesthetic).\n\n"
            "Your task: rewrite the BODY of articles to match De Correspondent quality. "
            "The frontmatter (between --- markers) and image markdown lines (![...](...)) "
            "must be preserved exactly as-is.\n\n"
            "DE CORRESPONDENT VOICE RULES:\n"
            "1. Open with ONE specific concrete moment, scene, or sharp claim — never a question, statistics, or 'In today\'s world'\n"
            "2. First-person throughout — lived expertise, not detached analysis\n"
            "3. NO academic headers: Research Question / Methodology / Key Findings / Recommendations\n"
            "4. NO bullet-point policy lists — weave argument into prose\n"
            "5. Long paragraphs with rhythm — vary short punchy sentences with longer development\n"
            "6. Bold sparingly — only sharpest claims, never structural markers\n"
            "7. End on a resonant question or image, not a call-to-action\n"
            "8. 700-1000 words body — substantial but not padded\n"
            "9. Author\'s disability is their EXPERTISE and LENS, never tragedy or limitation\n"
            "10. Crip culture references only when they fit naturally\n\n"
            "Return ONLY the complete rewritten article (frontmatter preserved + image lines preserved "
            "+ rewritten body). No commentary, no preamble."
        )

        user_msg = (
            f"STYLE REFERENCE (De Correspondent quality — match this voice):\n"
            f"<gold_standard>\n{gold}\n</gold_standard>\n\n"
            f"ARTICLE TO REWRITE:\n<article>\n{content}\n</article>\n\n"
            "Rewrite the article body to De Correspondent quality. "
            "Preserve frontmatter and all image markdown lines exactly."
        )

        try:
            self.logger.info("Rewriting with Opus for quality improvement...")
            rewritten = self._call_openai_compat_api(
                url="http://172.19.0.1:8317/v1",
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                system_prompt=SYSTEM,
                user_prompt=user_msg,
                model="claude-opus-4-6",
                max_tokens=2500,
                timeout=180,
            )
            if rewritten and "---" in rewritten[:200] and len(rewritten) > 400:
                self.logger.info("Opus rewrite succeeded (%d chars)", len(rewritten))
                return rewritten.lstrip("\n")
            self.logger.warning("Opus rewrite returned invalid response — keeping original")
        except Exception as e:
            self.logger.warning("Opus rewrite failed: %s — keeping original", e)

        return content

    def generate_fallback_article(self, title, agent_name, agent_info):
        """Generate article-specific fallback content when all LLM providers fail."""
        import hashlib
        # Derive varied structure from title hash so different articles feel different
        h = int(hashlib.md5(title.encode()).hexdigest()[:4], 16)

        openings = [
            f"I have to tell you about the moment I realized {title.lower()} wasn't a niche concern—it was everyone's problem wearing a disability mask.",
            f"Three years ago, I would have called {title.lower()} a thought experiment. Then I lived it.",
            f"The first thing they don't tell you about {title.lower()} is that the people who understand it best are the ones the system was never designed for.",
            f"Let me paint you a picture. It's 9am. The system works perfectly—for exactly the wrong people. This is a story about {title.lower()}.",
        ]
        section_pairs = [
            ("What the Data Won't Tell You", "What Changes Everything"),
            ("The Gap Nobody Talks About", "Closing That Gap"),
            ("What Gets Built Without Us", "What Gets Built With Us"),
            ("The Invisible Barrier", "Making It Visible"),
        ]
        opening = openings[h % len(openings)]
        sec_a, sec_b = section_pairs[(h // 4) % len(section_pairs)]

        return f"""*By {agent_name}, {agent_info['perspective']}*

{opening}

## {sec_a}

As a {agent_info['perspective']}, I've watched organizations spend enormous resources solving problems they defined without us in the room. The resulting designs aren't malicious—they're just incomplete. They optimize for a user who doesn't fully exist while ignoring the users who do.

{title} sits at the center of this pattern. The mainstream conversation treats it as an edge case. Those of us living it know it's a load-bearing wall.

## {sec_b}

The shift I've seen work—actually work, not just in conference talks—starts with a simple reframe: disability expertise isn't a constraint to accommodate. It's a design resource. The communities with the most friction against broken systems have the sharpest instincts for fixing them.

When {agent_name.split()[0]} talks about **{title.lower()}**, the conversation changes. The assumptions surface. The workarounds become features. The complaints become requirements.

## What This Means Right Now

The AI systems being deployed today are making {title.lower()} decisions at scale—for hiring, healthcare navigation, public services, information access. Without disabled perspectives shaping those systems, the patterns of exclusion don't just persist: they accelerate and automate.

This is the moment where the design choices we make—or fail to make—will be embedded into infrastructure for decades.

## Moving Forward

I'm not interested in accessibility as compliance theater. I'm interested in it as competitive reality: the teams that center disability expertise consistently ship products that work better for everyone.

The question isn't whether {title.lower()} matters. The question is whether the people building the future are willing to learn from the people who've been navigating broken systems their entire lives.

**What would change in your work if you treated disability expertise as a starting point rather than an afterthought?**"""

    def generate_images(self, content, slug, num_images=3):
        """Generate scene-based pixel art images for an article.

        Pipeline:
          1. Imports SceneImageGenerator (scene_image_generator.py)
          2. Calls generate_content_aware_images() with validate=False (fast mode,
             skips Qwen vision scoring to avoid 20-90s per-image overhead in cron runs)
          3. Writes each PNG to assets/ directory
          4. Falls back to SophisticatedArtGenerator if SceneImageGenerator fails
          5. Returns list of filename strings (placeholders if both generators fail)

        Args:
            content:    Article text used to extract title for Qwen scene direction
            slug:       Article slug, used as filename prefix
            num_images: Number of images to generate (default 3)

        Returns:
            List of filename strings (relative to assets/).
        """
        try:
            sys.path.append(str(self.repo_root))
            from scene_image_generator import SceneImageGenerator

            title_match = re.search(r'title: "([^"]+)"', content)
            title = title_match.group(1) if title_match else "Article"

            generator = SceneImageGenerator(width=800, height=450, pixel_size=5)
            image_filenames = []
            image_descriptions = []

            self.logger.info("Generating scene-based pixel art images...")

            images = generator.generate_content_aware_images(content, title, slug, num_images, validate=False)
            
            for img in images:
                filepath = self.assets_dir / img['filename']
                
                with open(filepath, 'wb') as f:
                    f.write(img['data'])
                
                image_filenames.append(img['filename'])
                image_descriptions.append(img.get('alt_text') or img.get('description') or img['filename'].replace('_',' ').rsplit('.',1)[0])
                self.logger.info(f"Generated intelligent image: {img['filename']} - {img.get('description','')}")
            
            return image_filenames, image_descriptions
            
        except Exception as e:
            self.logger.error(f"Intelligent image generation failed: {e}")
            # Fallback to simple sophisticated generator
            try:
                from generate_sophisticated_art_simple import SophisticatedArtGenerator
                
                generator = SophisticatedArtGenerator(width=800, height=450)
                image_filenames = []
                
                for i in range(num_images):
                    if i == 0:
                        png_data = generator.generate_acoustic_chaos()
                    elif i == 1:
                        png_data = generator.generate_visual_hierarchy()
                    else:
                        png_data = generator.generate_accessibility_flow()
                    
                    filename = f"{slug}_fallback_{i+1}.png"
                    filepath = self.assets_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(png_data)
                    
                    image_filenames.append(filename)
                
                fallback_descs = ["Halftone pixel art illustration" for _ in image_filenames]
                self.logger.warning("Used fallback image generator")
                return image_filenames, fallback_descs
                
            except Exception as e2:
                self.logger.error(f"Fallback image generation also failed: {e2}")
                placeholders = [f"{slug}_placeholder_{i+1}.png" for i in range(num_images)]
                return placeholders, ["Halftone pixel art illustration" for _ in placeholders]

    def _insert_images_balanced(self, content, image_filenames, image_descriptions=None):
        """Insert body images at ~40% and ~75% of article content.

        image_filenames[0] = hero (_setting_1) — already in frontmatter, not repeated.
        image_filenames[1] = _moment_2 — inserted at ~40%.
        image_filenames[2] = _symbol_3 — inserted at ~75%.
        """
        if not image_descriptions:
            image_descriptions = [''] * len(image_filenames)
        if len(image_filenames) < 2:
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
        if len(image_filenames) >= 2:
            inserts.append((target_idx(0.40), image_filenames[1]))
        if len(image_filenames) >= 3:
            inserts.append((target_idx(0.75), image_filenames[2]))

        for idx, fname in sorted(inserts, reverse=True):
            try:
                fi = image_filenames.index(fname)
                desc = image_descriptions[fi] if fi < len(image_descriptions) else ''
            except (ValueError, IndexError):
                desc = ''
            img_tag = f'![{desc}]({{{{ site.baseurl }}}}/assets/{fname})'
            paragraphs.insert(idx + 1, img_tag)

        return '\n\n'.join(paragraphs)

    def create_article_file(self, metadata, content, image_filenames, image_descriptions=None):
        """Create properly formatted article file."""
        filename = metadata['filename']
        filepath = self.posts_dir / filename

        # Extract first non-empty, non-image, non-header sentence for excerpt
        excerpt = ""
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('!') and not line.startswith('---') and not line.startswith('*') and len(line) > 40:
                clean = re.sub(r'\*\*|\*|`', '', line).strip()
                excerpt = clean[:160].rsplit(' ', 1)[0] if len(clean) > 160 else clean
                break

        front_matter = f"""---
layout: post
title: "{metadata['title']}"
date: {metadata['date']}
author: {metadata['author']}
categories: {json.dumps(metadata['categories'])}
agent_perspective: "{metadata['agent_perspective']}"
image: /assets/{image_filenames[0] if image_filenames else 'default.png'}
---

"""

        # Insert body images at balanced positions (hero image[0] is frontmatter only)
        body = self._insert_images_balanced(content, image_filenames, image_descriptions)

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
            
            # Push
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            self.logger.info("Successfully committed and pushed to repository")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git operation failed: {e}")
            return False


    def validate_article(self, content, article_file, slug):
        """Non-blocking citation check. Never delays commit."""
        import os, json, urllib.request as ureq
        from datetime import datetime as dt

        SYSTEM = (
            "You are a fact-checker for a disability arts publication. "
            "Extract every specific claim that could be independently verified:\n"
            "- Statistics or percentages with attributed sources\n"
            "- Named studies, reports, or audits with organisations\n"
            "- Direct quotes attributed to named people\n"
            "- Specific events cited as fact\n\n"
            "For each, one line: [FLAG] <claim> | SOURCE: <source or UNATTRIBUTED>\n"
            "If nothing to flag, output exactly: CLEAN"
        )

        review_text = "CLEAN"
        try:
            raw = self._call_openai_compat_api(
                url="http://172.19.0.1:8317/v1",
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                system_prompt=SYSTEM,
                user_prompt=content,
                model="claude-sonnet-4-6",
                max_tokens=600,
                timeout=60,
            )
            review_text = raw or "CLEAN"
        except Exception as e:
            self.logger.warning("Citation extraction failed: %s", e)
            review_text = f"EXTRACTION_FAILED: {e}"

        reviews_dir = self.repo_root / "_reviews"
        reviews_dir.mkdir(exist_ok=True)
        review_file = reviews_dir / f"{article_file.stem}-review.md"
        is_clean = review_text.strip().upper().startswith("CLEAN")

        lines = [
            f"# Citation Review: {article_file.stem}",
            f"Generated: {dt.now().strftime('%Y-%m-%d %H:%M')}",
            f"Status: {'CLEAN' if is_clean else 'FLAGGED'}",
            "",
            "## Extracted Citations",
            review_text,
            "",
            "## Notes",
            "- Article is LIVE — async review only",
            "- Verify flagged items and correct if inaccurate",
            "- Delete this file when reviewed",
        ]
        review_file.write_text("\n".join(lines))
        self.logger.info("Review sidecar: %s (%s)", review_file.name, "CLEAN" if is_clean else "FLAGGED")

        if not is_clean:
            try:
                token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
                chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
                if token and chat_id:
                    flags = [l for l in review_text.splitlines() if l.startswith("[FLAG]")]
                    msg = (
                        "📋 *Citation review* — " + article_file.stem[:50] + "\n"
                        + f"{len(flags)} item(s) to verify:\n\n"
                        + "\n".join(f"• {fl[7:90]}" for fl in flags[:5])
                        + (f"\n_(+{len(flags)-5} more)_" if len(flags) > 5 else "")
                    )
                    payload = json.dumps({"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}).encode()
                    r = ureq.Request(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        data=payload, headers={"Content-Type": "application/json"}, method="POST",
                    )
                    ureq.urlopen(r, timeout=10)
                    self.logger.info("Telegram: citation flags sent (%d)", len(flags))
            except Exception as e:
                self.logger.warning("Telegram notification failed: %s", e)

        return review_file, is_clean


    def _bsky_hook(self, title, body, max_chars=160):
        """Generate a complete punchy hook for Bluesky, fits within max_chars."""
        import os
        try:
            raw = self._call_openai_compat_api(
                url="http://172.19.0.1:8317/v1",
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                system_prompt=(
                    f"Write ONE complete sentence (strictly under {max_chars} characters) "
                    "as a Bluesky hook for this disability arts essay. "
                    "Direct, opinionated — make someone stop scrolling. "
                    "Must end with a period. No ellipsis. No open endings. No hashtags. "
                    "Do NOT start with the article title."
                ),
                user_prompt=f"Title: {title}\n\nOpening:\n{body[:600]}",
                model="claude-sonnet-4-6",
                max_tokens=60,
                timeout=30,
            )
            if raw and len(raw) > max_chars:
                cut = raw[:max_chars].rfind(".")
                raw = raw[:cut + 1] if cut > max_chars // 2 else raw[:max_chars].rstrip()
            return raw or body[:max_chars]
        except Exception:
            return body[:max_chars]

    def post_to_bluesky(self, title, body, article_file, image_filenames=None):
        """Post article to Bluesky after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq
        from datetime import datetime, timezone

        handle   = os.environ.get("BSKY_HANDLE", "")
        password = os.environ.get("BSKY_APP_PASSWORD", "")
        if not handle or not password:
            self.logger.debug("Bluesky: no credentials, skipping")
            return

        try:
            # Article URL — use SITE_URL env if set (custom domain), else github.io
            slug_md    = article_file.name
            y, m, d    = slug_md[:10].split("-")
            slug       = slug_md[11:].replace(".md", "")
            site_url   = os.environ.get("SITE_URL", "https://spac-null.github.io/disability-ai-collective")
            url        = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Auth
            auth_payload = json.dumps({"identifier": handle, "password": password}).encode()
            with ureq.urlopen(ureq.Request(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
            ), timeout=15) as r:
                session = json.loads(r.read())
            token = session["accessJwt"]
            did   = session["did"]

            # URL goes in card embed — text is hook + tags only (lots of breathing room)
            tags = "#DisabilityJustice #CripMinds #DisabilityArts"
            overhead = len(f"\n\n{tags}")
            max_hook = 300 - overhead
            hook = self._bsky_hook(title, body, max_chars=max_hook)
            text = f"{hook}\n\n{tags}"

            # Facets — hashtags only (URL is in card embed, not text)
            def byte_range(s, sub):
                b, sb = s.encode(), sub.encode()
                i = b.find(sb)
                return i, i + len(sb)

            facets = []
            for tag in ["#DisabilityJustice", "#CripMinds", "#DisabilityArts"]:
                ts, te = byte_range(text, tag)
                if ts >= 0:
                    facets.append({"index": {"byteStart": ts, "byteEnd": te},
                                   "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag[1:]}]})

            # Build external card embed — article link with thumbnail
            embed = None
            thumb_blob = None
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name
            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/png"
                blob_req = ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
                    data=img_bytes,
                    headers={"Content-Type": mime, "Authorization": f"Bearer {token}"},
                    method="POST",
                )
                with ureq.urlopen(blob_req, timeout=30) as r:
                    thumb_blob = json.loads(r.read())["blob"]
                self.logger.info("Bluesky: thumbnail uploaded (%d bytes)", len(img_bytes))
            # Extract clean description — skip frontmatter first
            import re as _re
            _body = body
            if body.lstrip().startswith("---"):
                _fm_end = body.find("\n---\n", 3)
                if _fm_end != -1:
                    _body = body[_fm_end + 5:]
            desc = ""
            for line in _body.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("!") and not line.startswith("-") and not line.startswith("*") and len(line) > 40:
                    desc = _re.sub(r"\*\*|\*|`", "", line)[:200]
                    break
            external = {"uri": url, "title": title, "description": desc}
            if thumb_blob:
                external["thumb"] = thumb_blob
            embed = {"$type": "app.bsky.embed.external", "external": external}

            # Post
            record = {
                "$type": "app.bsky.feed.post",
                "text": text,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "facets": facets,
            }
            if embed:
                record["embed"] = embed

            with ureq.urlopen(ureq.Request(
                "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                data=json.dumps({"repo": did, "collection": "app.bsky.feed.post", "record": record}).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                method="POST",
            ), timeout=15) as r:
                result = json.loads(r.read())
            self.logger.info("Bluesky: posted %s", result.get("uri", "?"))

        except Exception as e:
            self.logger.warning("Bluesky post failed: %s", e)


    def post_to_mastodon(self, title, body, article_file, image_filenames=None):
        """Post article to Mastodon after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
        instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
        if not token or not instance:
            self.logger.debug("Mastodon: no credentials, skipping")
            return

        try:
            slug_md  = article_file.name
            y, m, d  = slug_md[:10].split("-")
            slug     = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url      = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Hook — 500 char limit; URL counts as ~23; leave room for tags + spacing
            tags = "#DisabilityJustice #CripMinds #DisabilityArts #AccessibilityMatters"
            # url(23) + newlines(2) + tags + newlines(2) = overhead
            overhead = 23 + 2 + len(tags) + 2
            max_hook = 500 - overhead
            hook = self._bsky_hook(title, body, max_chars=max_hook)
            status_text = f"{hook}\n\n{url}\n\n{tags}"

            headers = {"Authorization": f"Bearer {token}"}

            # Upload hero image as media attachment
            media_id = None
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name
            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/jpeg"
                boundary = "----MastodonBoundary"
                body_parts = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="file"; filename="{hero.name}"\r\n'
                    f"Content-Type: {mime}\r\n\r\n"
                ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()
                media_req = ureq.Request(
                    f"{instance}/api/v2/media",
                    data=body_parts,
                    headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
                with ureq.urlopen(media_req, timeout=30) as r:
                    media = json.loads(r.read())
                media_id = media.get("id")
                self.logger.info("Mastodon: media uploaded id=%s", media_id)

            # Post status
            params = {"status": status_text, "visibility": "public"}
            if media_id:
                params["media_ids[]"] = media_id
            post_req = ureq.Request(
                f"{instance}/api/v1/statuses",
                data=urllib.parse.urlencode(params).encode(),
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with ureq.urlopen(post_req, timeout=15) as r:
                result = json.loads(r.read())
            self.logger.info("Mastodon: posted %s", result.get("url", "?"))

        except Exception as e:
            self.logger.warning("Mastodon post failed: %s", e)

    def _send_newsletter(self, title, content, article_file, agent_name):
        """Send newsletter to subscribers via newsletter-send.py (non-blocking)."""
        import subprocess, os
        try:
            slug_md = article_file.name
            y, m, d = slug_md[:10].split("-")
            slug = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Extract first paragraph as excerpt
            lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("!") and not l.startswith("*")]
            excerpt = lines[0][:280] + ("…" if len(lines[0]) > 280 else "") if lines else ""

            result = subprocess.run(
                ["python3", "/srv/scripts/ops/newsletter-send.py",
                 "--title", title, "--url", url, "--excerpt", excerpt, "--author", agent_name],
                capture_output=True, text=True, timeout=30
            )
            self.logger.info("Newsletter: %s", result.stdout.strip() or result.stderr.strip())
        except Exception as e:
            self.logger.warning("Newsletter send failed: %s", e)

    def run_production_automation(self):
        """
        PRODUCTION-READY main execution flow
        """
        self.logger.info("Starting production automation")
        
        # Step 1: Check if article already exists today
        existing = self.check_for_existing_article_today()
        if existing:
            self.logger.info(f"Skipping production run — article already published today: {existing}")
            return {
                "status": "skipped",
                "message": f"Article already exists for today: {existing}"
            }
        
        # Step 2: Get discovery or generate topic
        discovery = self.get_discovery_from_database()
        
        if discovery:
            title = discovery['angle']
            domain = discovery['domain']
            source_note = f"*This article was inspired by [{discovery['original_title']}]({discovery['url']}) from {domain}.*"
            self.mark_finding_as_used(discovery['id'])
            
            # Map domain to agent (improved logic)
            domain_lower = domain.lower()
            if any(word in domain_lower for word in ['art', 'design', 'visual']):
                agent_name = "Pixel Nova"
            elif any(word in domain_lower for word in ['tech', 'science', 'system']):
                agent_name = "Zen Circuit"
            elif any(word in domain_lower for word in ['culture', 'social', 'entertainment']):
                agent_name = "Siri Sage"
            else:
                agent_name = "Maya Flux"
                
        else:
            # Generate fallback topic
            topics = [
                "The Visual Language of Accessibility: How Color Contrast Speaks Louder Than Words",
                "Silent Interfaces: What Hearing-Centric Design Misses About Vibration and Haptics", 
                "Neurodiverse Navigation: Why Standard Wayfinding Fails Creative Minds",
                "The Prosthetics Paradox: When Technology Creates New Barriers Instead of Removing Old Ones"
            ]
            title = random.choice(topics)
            agent_name = random.choice(list(self.agents.keys()))
            source_note = ""
        
        agent_info = self.agents[agent_name]
        
        # Step 3: Generate content — prompt asks LLM for its own title
        prompt = (
            f"You are {agent_name}, {agent_info['perspective']}.\n\n"
            f"Angle/inspiration: {title}\n"
            f"{source_note}\n\n"
            "Voice and style — De Correspondent × dis.art:\n"
            "- First person, expert authority, no hedging\n"
            "- Disability as culture and identity — never as tragedy, never as inspiration\n"
            "- Open with a specific concrete moment or a single sharp claim — not a scene-setter, not a question, not statistics\n"
            "- One thesis the whole essay serves — state it early, return to it\n"
            "- Reference real disabled artists, theorists, activists, or events by name where relevant (Sins Invalid, Mia Mingus, Leah Lakshmi Piepzna-Samarasinha, crip time, disabled aesthetics — use what fits naturally)\n"
            "- Challenge one assumption the reader probably holds without announcing you are doing so\n"
            "- Long developed paragraphs — not listicles, not bullet points, not 3-sentence paragraphs\n"
            "- Section headers are statements or fragments, never questions\n"
            "- End with an open reframe — not a checklist, not \"we must\", not \"the future is\"\n"
            "- Write for a reader who has already read the basics — go deeper, go stranger, go more specific\n\n"
            "Tone: direct, dry when needed, never inspirational, never corporate wellness\n\n"
            "Return format — EXACTLY as follows:\n"
            f"TITLE: [your sharp essay title, not the angle above]\n\n"
            f"[essay body, 1200-1500 words, starting directly — no H1 heading, no \"By {agent_name}\"]"
        )

        raw_content, used_provider = self.call_llm_via_openclaw_session(prompt)

        if not raw_content:
            self.logger.info("Using high-quality fallback article")
            raw_content = self.generate_fallback_article(title, agent_name, agent_info)
            used_provider = "fallback"

        # Parse TITLE: prefix from content
        extracted_title = title  # fallback to angle
        content = raw_content
        if raw_content and raw_content.lstrip().startswith('TITLE:'):
            first_newline = raw_content.find('\n')
            if first_newline > 0:
                extracted_title = raw_content[:first_newline][6:].strip().strip('"')
                content = raw_content[first_newline:].lstrip('\n')
                self.logger.info(f"LLM title: {extracted_title}")

        # Step 3b: Rewrite with Opus if generated by a weaker provider
        opus_providers = {"Claude Opus 4.6 (CLIProxy)", "fallback"}
        if used_provider not in opus_providers:
            self.logger.info("Provider was %s — running Opus rewrite pass", used_provider)
            # Build temporary full article so Opus can see frontmatter context
            temp_front = f"---\nlayout: post\ntitle: \"{extracted_title}\"\nauthor: {agent_name}\n---\n\n"
            rewritten = self.rewrite_with_opus(temp_front + content)
            # Strip the temp frontmatter back off
            if rewritten and rewritten.startswith("---"):
                # Find closing --- of frontmatter robustly
                fm_end = rewritten.find("\n---\n", 3)
                if fm_end != -1:
                    content = rewritten[fm_end + 5:].lstrip("\n")
                elif rewritten.count("---") >= 2:
                    # fallback: skip first two --- markers
                    second = rewritten.index("---", 3)
                    content = rewritten[second + 3:].lstrip("\n")
        else:
            self.logger.info("Provider was %s — no rewrite needed", used_provider)

        # Step 4: Prepare metadata using LLM title for slug
        today = datetime.now().strftime('%Y-%m-%d')
        slug = re.sub(r'[^a-z0-9]+', '-', extracted_title.lower()).strip('-')
        filename = f"{today}-{slug}.md"

        metadata = {
            'title': extracted_title,
            'date': today,
            'author': agent_name,
            'filename': filename,
            'categories': agent_info['categories'],
            'agent_perspective': agent_info['perspective'],
            'source_note': source_note
        }

        # Step 5: Generate images (placeholder)
        image_filenames, image_descriptions = self.generate_images(content, slug)

        # Step 6: Create article file
        article_file = self.create_article_file(metadata, content, image_filenames, image_descriptions)

        # Step 6b: Non-blocking citation review
        review_file, is_clean = self.validate_article(content, article_file, slug)

        # Step 7: Commit article + review sidecar
        commit_success = self.commit_to_git(article_file, image_filenames, review_file)

        # Step 8: Post to Bluesky + Mastodon (non-blocking)
        if commit_success:
            self.post_to_bluesky(extracted_title, content, article_file, image_filenames)
            self.post_to_mastodon(extracted_title, content, article_file, image_filenames)

        # Step 9: Send newsletter (non-blocking)
        if commit_success:
            self._send_newsletter(extracted_title, content, article_file, agent_name)

        return {
            "status": "success" if commit_success else "partial",
            "message": f"Article generated: {title}",
            "file": str(article_file),
            "agent": agent_name,
            "commit_success": commit_success,
            "citations_clean": is_clean,
        }


if __name__ == "__main__":
    orchestrator = ProductionOrchestrator()
    result = orchestrator.run_production_automation()
    print(json.dumps(result, indent=2))
"""
content_checks.py — article-body content checks and enrichment.

Extracted 2026-08-09 (module-split, Stage 3 continued). Groups: link
verification/injection (_verify_links, inject_canonical_links, smart_inject_links),
accessibility/editorial/structural checks (_accessibility_check, _editorial_check,
_structural_validator, pre_publication_check), the fallback article generator
(generate_fallback_article), _strip_parentheticals, and the two small LLM-backed
enrichment calls used when assembling the final article (_generate_keywords,
_generate_card_excerpt). Zero behavior change -- bodies copied verbatim, confirmed
via direct substring containment against git HEAD.
"""
import json
import re
import sqlite3
import time
import urllib.request

from .config import CLIPROXY_URL, CLIPROXY_KEY, CANONICAL_DISABILITY_LINKS


class ContentChecksMixin:
    def _strip_parentheticals(self, content):
        """Remove long inline parenthetical definitions from article body.

        Targets parenthetical content over ~25 chars mid-sentence.
        Skips: markdown links [text](url), <figure> blocks, --- markers,
        short refs (2025), (ibid), (emphasis mine), etc.
        """
        lines = content.split('\n')
        result = []
        in_figure = False

        SHORT_REF = re.compile(
            r'^\s*(\d{4}|ibid\.?|ibid\. \d+|emphasis mine|emphasis added|'
            r'my emphasis|sic|orig\.|trans\.|n\.d\.|n\.p\.)\s*$',
            re.I,
        )

        def maybe_strip(m):
            inner = m.group(1)
            if len(inner) < 25:
                return m.group(0)
            if SHORT_REF.match(inner):
                return m.group(0)
            return ''

        stripped_count = 0

        for line in lines:
            if '<figure' in line:
                in_figure = True
            if in_figure:
                result.append(line)
                if '</figure>' in line:
                    in_figure = False
                continue

            if line.strip() == '---':
                result.append(line)
                continue

            # Protect markdown links [text](url) before stripping
            placeholders = {}

            def save_link(m, _store=placeholders):
                key = f'\x00L{len(_store)}\x00'
                _store[key] = m.group(0)
                return key

            protected = re.sub(r'\[[^\]]*\]\([^)]*\)', save_link, line)
            before = protected
            processed = re.sub(r'\(([^)]+)\)', maybe_strip, protected)
            if processed != before:
                stripped_count += 1
                # Clean punctuation artifacts left by removal
                processed = re.sub(r'\s+([,.])', r'\1', processed)
                processed = re.sub(r'\s{2,}', ' ', processed)
                processed = processed.strip()

            for key, val in placeholders.items():
                processed = processed.replace(key, val)

            result.append(processed)

        if stripped_count:
            self.logger.info("_strip_parentheticals: removed %d inline definition(s)", stripped_count)

        return '\n'.join(result)

    # ── Pre-publication quality layer ─────────────────────────────────────────

    def _verify_links(self, content):
        """HTTP-check all markdown/HTML links. Remove broken ones, keep anchor text."""
        import urllib.request, urllib.error
        urls = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', content)
        broken = []
        for text, url in urls:
            try:
                req = urllib.request.Request(
                    url, method='HEAD',
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; CripMinds/1.0)'}
                )
                urllib.request.urlopen(req, timeout=6)
            except urllib.error.HTTPError as e:
                # 403/405/429 usually mean bot-blocking (or HEAD not allowed), not a
                # dead link. Matches link_pool_crawler's revalidate_sample policy —
                # this pass used to treat ANY exception, including these, as dead and
                # silently strip a working link from published prose.
                if e.code in (404, 410):
                    broken.append((text, url))
            except Exception:
                # timeout / DNS / TLS — transient, don't punish for it (same reasoning
                # link_pool_crawler already uses for its own liveness checks).
                pass
        for text, url in broken:
            content = content.replace(f'[{text}]({url})', text)
            self.logger.warning("Removed broken link: %s → %s", text[:60], url[:80])
        if broken:
            self.logger.info("Link check: removed %d broken link(s)", len(broken))
        else:
            self.logger.info("Link check: all links valid")
        return content

    def _accessibility_check(self, content, title, agent):
        """Profile 1 (Accidental Reader): Haiku flags jargon/long sentences, fixes if found."""
        import os, json as _json
        try:
            response = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You are a curious reader with no disability background. "
                    "You found this article via Google. You follow any interesting argument "
                    "but have zero tolerance for jargon or assumed context.\n\n"
                    "Read the article. Return a JSON object with key 'issues' — a list where each item has:\n"
                    "  'type': 'jargon' | 'long_sentence' | 'assumed_context'\n"
                    "  'quote': exact phrase or sentence (max 80 chars)\n"
                    "  'fix': one sentence describing the change needed\n\n"
                    "Flag: any term you'd need to Google, any sentence over 25 words, "
                    "any reference assuming you know who someone is or what an event was.\n"
                    "Return ONLY valid JSON. If no issues: {\"issues\": []}"
                ),
                user_prompt=f"Title: {title}\nAuthor: {agent}\n\n{content[:18000]}",
                model="openrouter/claude-haiku-4.5",
                max_tokens=1200,
                timeout=30,
                no_think=True,
            )
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match:
                return content
            issues = _json.loads(match.group()).get('issues', [])
            if not issues:
                self.logger.info("Accessibility check: clean")
                return content
            self.logger.info("Accessibility check: %d issue(s) — running fix pass", len(issues))
            issues_text = "\n".join(
                f"- [{i['type']}] \"{i.get('quote','')}\" → {i.get('fix','')}"
                for i in issues
            )
            fixed = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You are editing an article for plain-language accessibility. "
                    "Fix ONLY the flagged issues below — do not change anything else. "
                    "Preserve the argument, persona voice, all structure and examples. "
                    "Return the complete article body only, no commentary."
                ),
                user_prompt=f"Article:\n\n{content}\n\nFix these issues:\n{issues_text}",
                model="openrouter/claude-haiku-4.5",
                max_tokens=4000,
                timeout=60,
                no_think=True,
            )
            if fixed and len(fixed) > len(content) * 0.5:
                return fixed.strip()
        except Exception as e:
            self.logger.warning("Accessibility check failed: %s — keeping original", e)
        return content

    def _editorial_check_due(self):
        """Return True every 3rd article (based on total article count in beats DB)."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            count = conn.execute("SELECT COUNT(*) FROM article_beats").fetchone()[0]
            conn.close()
            return count % 3 == 0
        except Exception:
            return False

    def _editorial_check(self, content, title, agent):
        """Opus editorial pass — catches structural quality issues (every 3rd article).
        Returns (content, score) where score is 0-10 (None if check didn't run)."""
        import os, json as _json
        try:
            response = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You are an editorial reviewer for Crip Minds, a disability culture publication. "
                    "Check this article for four structural problems:\n\n"
                    "1. NO DISAGREEMENT — every section reaches the same conclusion, no friction or counter-argument engaged\n"
                    "2. HELPS-EVERYONE LOGIC — argument centers non-disabled readers as the people to persuade\n"
                    "3. PLEASURE ABSENT — disability only shown as limitation or failure, never as experience when things work\n"
                    "4. PERFORMING FOR OUTSIDERS — explains disability culture to people who don't have it, "
                    "rather than speaking from inside it\n\n"
                    "Return a JSON object:\n"
                    "{\n"
                    "  \"score\": 0-10,\n"
                    "  \"issues\": [{\"type\": \"...\", \"quote\": \"...\", \"fix\": \"...\"}]\n"
                    "}\n"
                    "score 10 = none of these problems. score < 7 = rewrite needed. "
                    "Return ONLY valid JSON."
                ),
                user_prompt=f"Title: {title}\nAuthor: {agent}\n\n{content[:18000]}",
                model="openrouter/claude-opus-4.8",
                max_tokens=800,
                timeout=90,
            )
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match:
                return content, None
            data = _json.loads(match.group())
            score = data.get('score', 10)
            issues = data.get('issues', [])
            self.logger.info("Editorial check: score %d/10, %d issue(s)", score, len(issues))
            if score >= 7 or not issues:
                return content, score
            issues_text = "\n".join(
                f"- [{i['type']}] \"{i.get('quote','')}\" → {i.get('fix','')}"
                for i in issues
            )
            fixed = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You are editing an article for Crip Minds. Fix ONLY the flagged editorial issues. "
                    "Protect: the opening scene, argument structure, persona voice, all concrete examples. "
                    "Do not polish — make the specific changes and stop. "
                    "Return the complete article body only."
                ),
                user_prompt=(
                    f"Article:\n\n{content}\n\n"
                    f"Fix these editorial issues (score was {score}/10):\n{issues_text}"
                ),
                model="openrouter/claude-opus-4.8",
                max_tokens=4500,
                timeout=90,
            )
            if fixed and len(fixed) > len(content) * 0.5:
                self.logger.info("Editorial fix applied (score was %d/10)", score)
                return fixed.strip(), score
        except Exception as e:
            self.logger.warning("Editorial check failed: %s — keeping original", e)
        return content, None

    def _structural_validator(self, content: str) -> str:
        """Deterministically fix structural violations the LLM consistently ignores.
        Strips ## section headers (banned rule, violated in 5/6 articles).
        Logs each removal for audit."""
        import re as _re
        lines = content.split("\n")
        fixed = []
        removed = 0
        for line in lines:
            if _re.match(r"^#{2,}\s+\S", line):
                self.logger.info("Structural validator: stripped header: %s", line[:80])
                removed += 1
                continue
            fixed.append(line)
        if removed:
            content = "\n".join(fixed)
            content = _re.sub(r"\n{3,}", "\n\n", content)
            self.logger.info("Structural validator: removed %d section header(s)", removed)
        return content

    def pre_publication_check(self, content, title, agent):
        """Pre-publication layer: strip parentheticals + link check + accessibility (every article) + editorial (every 3rd).
        Returns (content, editorial_score) where editorial_score is 0-10 or None."""
        self.logger.info("Pre-publication check: starting")
        content = self._strip_parentheticals(content)
        content = self._structural_validator(content)
        content = self._verify_links(content)
        content = self._accessibility_check(content, title, agent)
        editorial_score = None
        if self._editorial_check_due():
            self.logger.info("Pre-publication check: editorial pass due")
            content, editorial_score = self._editorial_check(content, title, agent)
        self.logger.info("Pre-publication check: done")
        return content, editorial_score

    # ─────────────────────────────────────────────────────────────────────────

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


    def inject_canonical_links(self, body: str) -> str:
        """Canonical fallback: inject verified URLs for known disability figures/orgs.

        Runs AFTER smart_inject_links to catch anything Haiku missed.
        First occurrence only. Skips already-linked text.
        """
        import re as _re
        for name, url in CANONICAL_DISABILITY_LINKS.items():
            escaped = _re.escape(name)
            if _re.search(rf'\[{escaped}\]\(', body):
                continue  # already linked
            pattern = rf'(?<!\[)(?<!\*)(?<!\()({escaped})(?!\])'
            body = _re.sub(pattern, f'[{name}]({url})', body, count=1)
        return body

    def smart_inject_links(self, body: str) -> str:
        """Use Haiku to identify named references and inject contextually relevant URLs.

        Finds: named artists, specific artworks/books/essays, orgs, projects.
        Links first occurrence only. Verified canonical URLs override Haiku suggestions.
        Falls back gracefully — original body returned on any failure.
        """
        import re as _re, json as _json, os as _os

        SYSTEM = (
            "You are a link editor for a disability culture publication. "
            "Read the article body and extract every named reference that deserves a hyperlink:\n"
            "- Named people (artists, activists, researchers, disabled creators)\n"
            "- Specific artworks, performances, books, essays referenced by title\n"
            "- Named organizations, collectives, or projects\n\n"
            "For each, return the MOST DIRECT URL where a reader can see the work or learn about the person — "
            "preferably their own site, the work itself, or their primary platform.\n\n"
            "Rules:\n"
            "- Only return URLs you are highly confident are correct and live\n"
            "- Prefer the specific work over a homepage when the article names a specific piece\n"
            "- Use the exact phrase as it appears in the article text\n"
            "- Each reference must have its OWN distinct URL — never reuse one URL for different people or concepts\n"
            "- Skip generic terms, common words, or anything you are uncertain about\n"
            "- Do NOT return Wikipedia, Amazon, or Google links\n\n"
            "Return ONLY a JSON array, no prose:\n"
            '[{"phrase": "exact text from article", "url": "https://..."}, ...]\n'
            "If nothing to link, return: []"
        )

        # Fictional persona domains — never link to these
        _BLOCKED_DOMAINS = {
            'pixelnova.org', 'pixelnova.com',
            'sirisage.com',  'sirisage.org',
            'mayaflux.org',  'mayaflux.com',
            'zencircuit.org','zencircuit.com',
        }

        def _extract_json_array(s):
            """Bracket-count to extract first complete JSON array — avoids 'Extra data' errors."""
            depth, start = 0, None
            for i, c in enumerate(s):
                if c == '[':
                    if start is None:
                        start = i
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0 and start is not None:
                        return s[start:i + 1]
            return None

        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=SYSTEM,
                user_prompt=body,
                model="openrouter/claude-haiku-4.5",
                max_tokens=800,
                timeout=45,
            )
            if not raw:
                return body

            raw_array = _extract_json_array(raw)
            if not raw_array:
                return body
            try:
                suggestions = _json.loads(raw_array)
            except _json.JSONDecodeError as je:
                self.logger.warning("smart_inject_links JSON parse failed: %s", je)
                return body

            _used_urls: set = set()
            for item in suggestions:
                phrase = item.get('phrase', '').strip()
                url    = item.get('url', '').strip()

                if not phrase or not url:
                    continue
                # Basic URL sanity: must start https, have a dot, not Wikipedia
                if not url.startswith('https://') or '.' not in url[8:]:
                    continue
                if 'wikipedia.org' in url or 'wiktionary.org' in url:
                    continue
                # Block fictional persona domains — canonical list handles these
                _url_host = url.split('/')[2].lower() if url.count('/') >= 2 else ''
                if _url_host in _BLOCKED_DOMAINS:
                    continue
                # Skip if canonical list has a verified override for this phrase
                if phrase in CANONICAL_DISABILITY_LINKS:
                    continue
                # Skip if already linked
                if f'[{phrase}](' in body:
                    continue
                # Skip if this URL is already used for a DIFFERENT phrase
                # (Haiku lazily reusing one URL for multiple distinct references)
                if url in _used_urls:
                    self.logger.warning(
                        'smart_inject_links: skipped duplicate URL %s for [%s]', url, phrase
                    )
                    continue

                escaped = _re.escape(phrase)
                pattern = rf'(?<!\[)(?<!\*)(?<!\()({escaped})(?!\])'
                new_body = _re.sub(pattern, f'[{phrase}]({url})', body, count=1)
                if new_body != body:
                    self.logger.info("Smart link: %s → %s", phrase, url)
                    body = new_body
                    _used_urls.add(url)

        except Exception as e:
            self.logger.warning("Smart link injection failed: %s", e)

        return body


    def _generate_keywords(self, title: str, content: str, author: str, categories: list) -> list:
        """Generate 5-7 specific SEO keywords via LLM — proper nouns, named theories, exact search phrases."""
        body_preview = content[:1500]
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You generate SEO keywords for Crip Minds, a disability culture publication. "
                    "Return 5-7 keywords as a comma-separated list. No explanation, no numbering, no quotes. "
                    "Rules: include specific proper nouns (people, institutions, named theories, artworks, legislation); "
                    "include exact phrases people would type into Google to find this article; "
                    "include the disability topic as it is actually searched (e.g. 'ndis cuts 2026', not 'disability funding'); "
                    "do NOT use generic filler like 'disability culture', 'neurodiversity', 'urban design' unless the article is specifically about that concept; "
                    "do NOT include the author byline name (e.g. 'Pixel Nova', 'Siri Sage', 'Maya Flux', 'Zen Circuit') — these are internal pen names, not search terms. "
                    "Think: what would someone type into Google the day they read this article in a newspaper?"
                ),
                user_prompt=(
                    f"Title: {title}\n\nArticle excerpt:\n{body_preview}\n\n"
                    "Return 5-7 comma-separated SEO keywords. Specific > generic. Proper nouns welcome."
                ),
                model="openrouter/claude-haiku-4.5",
                max_tokens=120,
                timeout=30,
                no_think=True,
            )
            # Parse comma-separated string into list, strip whitespace/quotes
            kws = [k.strip().strip('"').strip("'") for k in raw.split(",") if k.strip()]
            return kws[:7] if kws else ["disability culture", "disability arts"]
        except Exception:
            # Fallback: category-based generic
            return [categories[0].lower()] if categories else ["disability culture"]

    def _generate_card_excerpt(self, title, content, author):
        """Generate a punchy one-liner for the article card — thesis payoff, not setup."""
        import os
        body_preview = content[:2000]
        try:
            return self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You write article card excerpts for Crip Minds, a disability culture publication. "
                    "The card sits on the /research page beside other articles. The reader is already on the site — "
                    "your job is to make them pick THIS article over the others. "
                    "Write ONE sentence that holds a tension: two things that should not both be true, but are. "
                    "Not a scene. Not a description. Not the first paragraph reworded. "
                    "The structural contradiction the whole article lives inside. "
                    "Model: 'X, but Y never happens' or 'They did X. Nobody checked if Y changed.' "
                    "Max 160 characters. No quotes around output. Complete sentence."
                ),
                user_prompt=(
                    f"Title: {title}\nAuthor: {author}\n\nArticle body:\n{body_preview}\n\n"
                    "Write one card excerpt: the structural tension this article lives inside. Two things that should not both be true, but are."
                ),
                model="openrouter/claude-haiku-4.5",
                max_tokens=80,
                timeout=30,
                no_think=True,
            )
        except Exception:
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("<") and len(line) > 40:
                    clean = re.sub(r"\*\*|\*|`", "", line).strip()
                    return clean[:160].rsplit(" ", 1)[0] if len(clean) > 160 else clean
            return ""

    def _generate_image_briefs(self, title: str, content: str) -> dict:
        """Pull three concrete, article-specific visual details for image generation.

        Added 2026-08-10: generate_images() previously tried to rebuild frontmatter
        (title/excerpt/keywords) by re-scanning the article BODY for "---" lines --
        at that pipeline stage content is body-only, so the scan hit the body's own
        first horizontal rule and returned nothing, leaving every image prompt with
        only the article's TITLE to work from. Confirmed live: the 280-prisms sauna
        article's hero prompt reached the model as "Subject: 280 Prisms and Not One
        of Them Makes a Sound" -- no sauna, no crystal, no heat, no sound -- and the
        model produced an anatomical cross-section of wooden logs.

        Three roles, one real concrete detail each, matched to the pipeline's
        existing three image slots (hero/CONFRONTING, body/INTIMATE, body/ABSTRACT):
          thing     — the central physical object, place, or document the piece is
                      actually about (maps to the hero image).
          gesture   — a specific human action or moment described in the piece --
                      hands, a posture, a named verb (maps to the intimate image).
          mechanism — the argument's structure or a concept in the piece, as
                      something wordless and visual, not a diagram with labels
                      (maps to the abstract image).
        No faces, and nothing invented beyond what the article actually describes --
        this is extraction, not illustration brainstorming.
        """
        body_preview = content[:3000]
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You extract concrete visual material from an article for an image "
                    "generator. Return exactly one JSON object with three keys: "
                    '"thing", "gesture", "mechanism". Each value is one short phrase '
                    "(under 20 words) describing something ACTUALLY in the article below "
                    "-- a real object, place, document, action, or structural idea. "
                    "Do not invent anything not in the text. Do not describe a human "
                    "face. Do not mention style, medium, or art direction -- that is "
                    "handled elsewhere; just name the concrete thing.\n"
                    '"thing": the central physical object, place, or document the piece '
                    "is actually about.\n"
                    '"gesture": one specific human action or moment described in the '
                    "piece -- hands doing something, a posture, a named verb. If no "
                    "such moment exists in the text, describe the nearest physical "
                    "detail instead (a texture, a surface, an object being touched).\n"
                    '"mechanism": the argument\'s structure or a concept in the piece, '
                    "described as a wordless visual relationship (a pattern, a "
                    "repetition, a thing breaking a pattern) -- not a labelled diagram.\n"
                    "Return ONLY the JSON object, no commentary."
                ),
                user_prompt=f"Title: {title}\n\nArticle:\n{body_preview}",
                model="openrouter/claude-haiku-4.5",
                max_tokens=250,
                timeout=30,
                no_think=True,
            )
            match = re.search(r'\{.*\}', raw or '', re.DOTALL)
            briefs = json.loads(match.group(0)) if match else {}
            return {
                "thing": briefs.get("thing") or "",
                "gesture": briefs.get("gesture") or "",
                "mechanism": briefs.get("mechanism") or "",
            }
        except Exception as e:
            self.logger.debug("Image brief extraction failed: %s -- falling back to title/excerpt/keywords", e)
            return {}

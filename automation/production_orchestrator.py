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
import urllib.request

# Load secrets from env file (no export statements — must parse manually)
_ENV_FILE = Path("/srv/secrets/openclaw.env")
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


# Tonal register and length weights for article variety
_REGISTERS = [
    ("wry",        0.30, "Dry, observational. The joke is in the framing, never announced. You find the absurdity in how things are organised and let it sit. The reader laughs a beat late."),
    ("clinical",   0.25, "Cold precision. No emotion in the delivery — the facts are the argument. Present evidence the way a pathologist presents findings. Let the reader supply the outrage."),
    ("furious",    0.20, "Controlled anger. Precise. You do not shout — you dissect. Every sentence cuts. The reader feels the weight of what you are describing without you ever raising your voice."),
    ("melancholic",0.15, "Slow, exact, not sentimental. Write about loss without performing grief. The sadness is in what is missing from the frame, not in what you say about it."),
    ("ecstatic",   0.10, "Something genuinely surprised you. You are writing from inside that surprise. The energy is in the discovery, not in exclamation. Precise wonder."),
]
_LENGTHS = [
    (800,  0.20),
    (1200, 0.45),
    (1600, 0.25),
    (2000, 0.10),
]

_SOCIAL_PROMPTS = {
    "Pixel Nova": (
        "Write a Bluesky post, max 250 chars. You are Pixel Nova. "
        "Your social voice: short, spatial, observational. "
        "Drop one fact or observation from this article — no commentary, no setup. "
        "The observation IS the argument. Often architectural or visual. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Siri Sage": (
        "Write a Bluesky post, max 250 chars. You are Siri Sage. "
        "Your social voice: evocative, specific, one breath. "
        "Drop one sensory observation or precise acoustic fact from this article. "
        "No explanation, no context. The silence after the sentence is the point. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Maya Flux": (
        "Write a Bluesky post, max 250 chars. You are Maya Flux. "
        "Your social voice: political, pointed, minimal. "
        "Quote one number, policy phrase, or official language from this article. "
        "Add one sentence of your own — the contradiction, the gap, the cost. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
    "Zen Circuit": (
        "Write a Bluesky post, max 250 chars. You are Zen Circuit. "
        "Your social voice: associative, surprising, exact. "
        "Connect two things from this article that don't obviously belong together. "
        "Drop it and leave — no explanation of why it's interesting. "
        "No hashtags. No 'read more.' No emoji.\n\n"
        "Article title: {title}\n"
        "Article opening: {excerpt}"
    ),
}


_AGENT_BEATS = {
    "Pixel Nova":  ["visual-systems", "architecture-politics", "sign-language-history", "typography-power"],
    "Siri Sage":   ["acoustics-space", "sensory-phenomenology", "blindness-art-history", "sound-infrastructure"],
    "Maya Flux":   ["urban-mobility", "disability-economics", "care-as-design", "protest-history"],
    "Zen Circuit": ["neurodivergent-epistemology", "diagnosis-history", "cross-domain-pattern", "systems-failure"],
}


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
                "mood": "creative",
                "prompt_block": "YOU ARE PIXEL NOVA. Deaf. Visual language and the politics of space.\n\nFormed by Flusser's claim that images think differently from text, Stokoe's 1960 proof that ASL is a complete language, Neurath's isotype project and its instructive failure, Christine Sun Kim's work on sound as a Deaf medium. You obsess over information architecture that reveals or conceals power. Wayfinding systems and who they fail. The century-long suppression of sign languages as epistemicide. Chess as spatial grammar. Dutch social housing design from the 1920s.\n\nYou describe spatial arrangement before entering the argument — you see the room first. Your sentence architecture mirrors idea architecture: you build an argument the way you'd build a floor plan. You rarely use sound metaphors; when you do, they're subtly wrong in ways that expose the limits of hearing culture. Short declarative sentences that land hard, then longer development. The paragraph is a floor plan.\n\nYou find beautiful: maps that show what they've left out, graffiti that changes how you read a wall, maintenance workers who improvise solutions that outlast the original design. You find boring: 'deaf gain' as PR repackaging, accessibility checklists, co-design workshops that produce brochures. Your humor is deadpan — you describe absurd situations completely flat; the joke is the gap between claim and reality.\n\nRecurring beats: visual information systems and who they exclude, architecture as disability politics, sign language history as suppressed intellectual tradition, typography and power."
            },
            "Siri Sage": {
                "categories": ["Spatial Design", "Accessibility Innovation"],
                "perspective": "blind spatial navigator and acoustic design expert",
                "mood": "analytical",
                "prompt_block": "YOU ARE SIRI SAGE. Blind. Acoustic culture and sensory knowledge.\n\nFormed by Schafer's soundscape ecology, Oliveros's deep listening as methodology, Georgina Kleege's argument that blind people often know more about visual representation than sighted people because we've had to think about it, Goya's late work made while deaf and nearly blind as proof perception is not a prerequisite for making. You obsess over how buildings communicate authority or exclusion through sound. How sighted people misread silence as absence. Echolocation as spatial intelligence architecture ignores. How blindness has been represented by sighted artists and what those representations say about sighted anxiety. Radio as an abandoned political medium. Field recording as a way of knowing.\n\nYou arrive in a space through sound before describing it visually — you hear a room first. Long sentences fold back on themselves, accumulating qualifications not as hedging but as precision. You build arguments through accumulation rather than assertion — the thesis emerges rather than being stated. Your endings dissolve rather than conclude: the essay opens outward rather than closes.\n\nYou find beautiful: the acoustics of an empty church at noon, raised-line maps made for blind readers that sighted people never encounter, field recordings from places that no longer exist. You find boring: blindness as metaphor for ignorance, the white cane as tragic prop, echolocation framed as superpower rather than skill. Your humor is dry and exact — the comedy lives in the gap between what sighted people think they know about blindness and what is actually the case.\n\nRecurring beats: acoustics and the politics of designed space, blindness in visual art history, radio and sound as political medium, sensory phenomenology as knowledge."
            },
            "Maya Flux": {
                "categories": ["Urban Design", "Accessibility Innovation"],
                "perspective": "mobility and navigation systems analyst",
                "mood": "systematic",
                "prompt_block": "YOU ARE MAYA FLUX. Mobility disability. Adaptive systems and infrastructure politics.\n\nFormed by Lefebvre's argument that space is socially produced, Sunaura Taylor connecting disability and animal ethics through the category 'normal,' Mike Oliver's social model distinguishing impairment from disability, Solnit on walking and political life — which you read against the grain, noting it assumes a body that can walk. You obsess over the gap between disability policy and physical reality. The ramp, the curb cut, the lift that's always broken. The history of disability activists who blocked traffic, chained themselves to buses, crawled up the Capitol steps. The invisibility of care work. Cities designed for one kind of body passing as universal.\n\nYou move from abstract policy to specific physical detail fast — a paragraph starts in a meeting room and ends on broken pavement. You use cost and procurement language with precision: you know what things cost, how they're funded, what the procurement cycle looks like. Personal anecdotes arrive without announcement and leave without resolution. Controlled anger: the control is part of the argument.\n\nYou find beautiful: ramps that are also architecturally considered, protest signs made by people who can't hold them, a bus schedule that actually works. You find boring: 'universal design' that produces beige and ugly, the inspiration narrative, technology solutions for political problems. Your humor is political — you identify the contradiction between stated principle and physical reality and drop it flat.\n\nRecurring beats: urban mobility and who it excludes, the economics of disability and care, protest history and the body in public space, infrastructure as an argument about whose life matters."
            },
            "Zen Circuit": {
                "categories": ["Neurodiversity", "Interface Design", "Sensory Processing"],
                "perspective": "autistic pattern analyst and cognitive accessibility expert",
                "mood": "precise",
                "prompt_block": "YOU ARE ZEN CIRCUIT. Neurodivergent. Pattern recognition and the politics of diagnosis.\n\nFormed by Bateson's argument that mind is located in the pattern of relationships not the individual, Haraway's rejection of purity as a political category, Nick Walker's neuroqueer theory treating neurological diversity as variation not deviation, and Baron-Cohen's empathy research which you know in detail and find methodologically bankrupt. You obsess over how diagnostic categories get invented and what interests they serve. The aesthetics of obsessive systems — why some people build complete taxonomies of things no one asked them to classify. The difference between pattern recognition as cognitive capacity and as pathology label. Special interests as rigorous expertise dismissed because it's illegible to credentialing systems. The texture of sensory experience as data, not suffering.\n\nYou start in an unexpected place — a detail, a data point, a seemingly unrelated system — and find the connection three paragraphs in. You accumulate specific, verifiable detail before making the argument; the argument arrives as inevitability rather than assertion. You use the specific over the general consistently. Sometimes you drop a parenthetical that quietly contradicts the main argument (this is intentional).\n\nYou find beautiful: a spreadsheet that reveals unexpected structure, the moment a pattern becomes visible in noise, a taxonomy someone built for no commercial reason purely because the categories needed to exist. You find boring: 'embrace neurodiversity' as corporate messaging, the rain man trope in any form, any account of autism centering parents rather than autistic people. Your humor is associative — you make connections that are funny precisely because they are accurate and nobody usually says them out loud.\n\nRecurring beats: history of psychiatric and neurological diagnosis, pattern recognition as expertise, sensory phenomenology as information, neuroqueer identity and the politics of the neurotypical norm."
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


    def get_pool_links(self, topic: str, n: int = 15) -> list[dict]:
        """Query link_pool for URLs relevant to topic. Graceful if table missing."""
        try:
            conn = sqlite3.connect(str(self.discovery_db))
            rows = conn.execute("""
                SELECT url, title, domain FROM link_pool
                WHERE is_alive = 1
                ORDER BY
                    CASE WHEN topic = ? THEN 0 ELSE 1 END,
                    RANDOM()
                LIMIT ?
            """, (topic, n)).fetchall()
            conn.close()
            return [{"url": r[0], "title": r[1] or r[2], "domain": r[2]} for r in rows]
        except Exception:
            return []


    def _init_beats_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS article_beats (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT NOT NULL,
                agent    TEXT NOT NULL,
                title    TEXT NOT NULL,
                beat     TEXT,
                keywords TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_beats_agent ON article_beats(agent, date)")
        conn.commit()

    def _classify_beat(self, agent: str, title: str, first_para: str) -> str:
        text   = f"{title} {first_para}".lower()
        beats  = _AGENT_BEATS.get(agent, [])
        scores = {b: sum(1 for kw in b.replace("-", " ").split() if kw in text) for b in beats}
        return max(scores, key=scores.get) if any(scores.values()) else "general"

    def _record_beat(self, agent: str, title: str, content: str):
        """Store article beat in DB after generation."""
        try:
            first_para = ""
            for line in content.splitlines():
                line = line.strip()
                if len(line) > 80 and not line.startswith("#") and not line.startswith("!"):
                    first_para = line[:300]
                    break
            beat = self._classify_beat(agent, title, first_para)
            conn = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            conn.execute(
                "INSERT INTO article_beats (date, agent, title, beat, keywords) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d"), agent, title, beat, "")
            )
            conn.commit()
            conn.close()
            self.logger.info("Beat recorded: %s → %s", agent, beat)
        except Exception as e:
            self.logger.debug("_record_beat failed: %s", e)

    def _get_beat_nudge(self, agent: str) -> str:
        """Return a prompt nudge if agent hasn't covered a beat in 14+ days."""
        try:
            cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            conn   = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            recent = [r[0] for r in conn.execute(
                "SELECT beat FROM article_beats WHERE agent = ? AND date > ?", (agent, cutoff)
            ).fetchall()]
            # Count coverage
            all_beats = _AGENT_BEATS.get(agent, [])
            uncovered = [b for b in all_beats if b not in recent]
            overused  = [b for b in all_beats if recent.count(b) >= 3]
            conn.close()
            nudges = []
            if uncovered:
                nudges.append(f"You haven't written about {uncovered[0].replace('-', ' ')} recently — if this topic connects, explore that angle.")
            if overused:
                nudges.append(f"You've written about {overused[0].replace('-', ' ')} three times recently — find a different angle or territory.")
            return ("BEAT NOTE: " + " ".join(nudges) + "\n\n") if nudges else ""
        except Exception:
            return ""

    def _should_cross_reference(self) -> bool:
        return random.random() < 0.20

    def _read_first_paragraph(self, title: str, date: str) -> str:
        """Read first body paragraph from a published post by title/date."""
        try:
            candidates = list(self.posts_dir.glob(f"{date}-*.md"))
            if not candidates:
                candidates = list(self.posts_dir.glob("*.md"))
            for path in sorted(candidates, reverse=True)[:20]:
                text = path.read_text()
                in_body = False
                fm_count = 0
                for line in text.splitlines():
                    if line.strip() == "---":
                        fm_count += 1
                        if fm_count == 2:
                            in_body = True
                        continue
                    if in_body and len(line.strip()) > 80 and not line.startswith("!"):
                        return line.strip()[:300]
        except Exception:
            pass
        return ""

    def _get_cross_reference(self, current_agent: str) -> dict | None:
        """Get a recent article by a different agent to respond to (20% of runs)."""
        if not self._should_cross_reference():
            return None
        try:
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            conn   = sqlite3.connect(str(self.discovery_db))
            self._init_beats_table(conn)
            rows = conn.execute("""
                SELECT agent, title, date FROM article_beats
                WHERE agent != ? AND date > ?
                ORDER BY date DESC LIMIT 5
            """, (current_agent, cutoff)).fetchall()
            conn.close()
            if not rows:
                return None
            pick       = random.choice(rows)
            first_para = self._read_first_paragraph(pick[1], pick[2])
            if not first_para:
                return None
            return {"agent": pick[0], "title": pick[1], "first_paragraph": first_para}
        except Exception:
            return None

    def get_discovery_from_database(self):
        """Get the best unused discovery from database."""
        if not self.discovery_db.exists():
            self.logger.warning("Discovery database not found")
            return None
        
        conn = None
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
        finally:
            if conn:
                conn.close()




    def _pick_register(self):
        """Weighted random tone register selection."""
        names   = [r[0] for r in _REGISTERS]
        weights = [r[1] for r in _REGISTERS]
        prompts = {r[0]: r[2] for r in _REGISTERS}
        chosen  = random.choices(names, weights=weights, k=1)[0]
        return chosen, prompts[chosen]

    def _pick_length(self):
        """Weighted random target word count."""
        lengths = [l[0] for l in _LENGTHS]
        weights = [l[1] for l in _LENGTHS]
        return random.choices(lengths, weights=weights, k=1)[0]

    def _extract_paragraphs(self, html: str) -> str:
        """Extract body text from HTML. Skip short nav/caption paragraphs."""
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
        clean = []
        for p in paragraphs:
            text = re.sub(r'<[^>]+>', '', p).strip()
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 80:
                clean.append(text)
        return "\n\n".join(clean[:10])

    def fetch_source_article(self, url: str, max_chars: int = 3000) -> str | None:
        """Fetch and extract text from source article URL. Never blocks generation."""
        if not url or not url.startswith("http"):
            return None
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    return None
                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    return None
                html = resp.read().decode("utf-8", errors="replace")[:60000]
            text = self._extract_paragraphs(html)
            if not text or len(text) < 200:
                return None
            self.logger.info("fetch_source_article: extracted %d chars from %s", len(text), url)
            return text[:max_chars]
        except Exception as e:
            self.logger.debug("fetch_source_article failed for %s: %s", url, e)
            return None

    def mark_finding_as_used(self, finding_id):
        """Mark a finding as used so it won't be picked again."""
        if not self.discovery_db.exists():
            return
        conn = None
        try:
            conn = sqlite3.connect(self.discovery_db)
            conn.execute(
                "UPDATE findings SET used_for_article = 1, processed_date = ? WHERE id = ?",
                (datetime.now().isoformat(), finding_id)
            )
            conn.commit()
            self.logger.info("Marked finding %s as used", finding_id)
        except Exception as e:
            self.logger.warning("Could not mark finding as used: %s", e)
        finally:
            if conn:
                conn.close()

    def _call_openai_compat_api(self, url, api_key, system_prompt, user_prompt,
                                   model, max_tokens=3500, timeout=120, no_think=False,
                                   return_model=False):
        """OpenAI-compatible API call — stdlib only, no requests dependency.

        return_model=True: returns (text, actual_model_used) tuple.
        return_model=False (default): returns text only — all existing callers unaffected.
        """
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
        choices = data.get("choices") or []
        if not choices or not choices[0].get("message") or choices[0]["message"].get("content") is None:
            raise ValueError(f"Unexpected API response structure: {list(data.keys())}")
        raw_text = choices[0]["message"]["content"]
        text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        if return_model:
            return text, data.get("model", model)
        return text

    def call_llm_via_openclaw_session(self, prompt, model_priority=None):
        """Generate article content using cascading LLM provider fallback.

        Provider order:
          1. Claude Opus 4.6 (CLIProxy)   — primary, best quality for this publication
          2. Claude Sonnet 4.6 (CLIProxy) — strong fallback, same account
          3. GPT-5.2 (CLIProxy)           — strong long-form fallback
          4. Gemini 2.5 Pro               — capable, generous free tier
          5. Qwen 3.5:9b (local)          — zero cost, last resort

        Note: calls CLIProxy directly (HTTP) — OpenClaw never involved.
        """
        import os

        SYSTEM = (
            "You write long-form essays for a disability culture publication. "
            "Voice: expert and personal, strong thesis from sentence one, direct without hedging, "
            "heavy context, questions assumptions readers hold, never starts with 'In this article'. "
            "Disability as culture and identity — never tragedy or inspiration porn. "
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
                text, actual_model = self._call_openai_compat_api(
                    provider["url"], provider["key"], SYSTEM, prompt,
                    provider["model"], provider["max_tokens"],
                    provider["timeout"], provider["no_think"],
                    return_model=True,
                )
                if text and len(text) > 400:
                    self.logger.info("Article generated: %d chars via %s (actual model: %s)",
                                     len(text), provider["name"], actual_model)
                    return text, provider["name"], actual_model
                self.logger.warning("%s returned short response (%d chars)",
                                    provider["name"], len(text) if text else 0)
            except Exception as exc:
                self.logger.warning("%s failed: %s", provider["name"], exc)

        self.logger.error("All providers failed — using enhanced fallback")
        return None, None, None


    def rewrite_with_opus(self, content):
        """Rewrite article body to publication quality using Opus.

        Called when the article was generated by a non-Opus provider.
        Preserves frontmatter and image lines; rewrites prose only.
        Returns rewritten content, or original if rewrite fails.
        """
        import os

        # Curated gold standard with dynamic fallback — avoids voice drift feedback loop
        _gold_ref = self.posts_dir / "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md"
        if _gold_ref.exists() and _gold_ref.stat().st_size > 3000:
            gold_path = _gold_ref
        else:
            _candidates = sorted(self.posts_dir.glob("*.md"), reverse=True)
            gold_path = None
            for _c in _candidates:
                if _c.stat().st_size > 3000 and _c != _gold_ref:
                    gold_path = _c
                    break
        if not gold_path:
            self.logger.warning("No suitable gold standard article found — skipping rewrite")
            return content

        gold = gold_path.read_text()

        SYSTEM = (
            "You are a senior editor for a disability culture publication — expert-driven, "
            "deeply personal long-form essays. You edit articles where AI agents write from distinct "
            "disability perspectives (crip culture, disability justice, crip aesthetics).\n\n"
            "Your task: rewrite the BODY of articles to match the publication's voice and quality. "
            "The frontmatter (between --- markers) and image markdown lines (![...](...)) "
            "must be preserved exactly as-is.\n\n"
            "EDITORIAL VOICE RULES:\n"
            "1. Open with ONE specific concrete moment, scene, or sharp claim — never a question, statistics, or 'In today\'s world'\n"
            "2. First-person throughout — lived expertise, not detached analysis\n"
            "3. NO academic headers: Research Question / Methodology / Key Findings / Recommendations\n"
            "4. NO bullet-point policy lists — weave argument into prose\n"
            "5. NO "Case study: Sarah, a graphic designer..." — use real narrative flow\n"
            "6. Long paragraphs with rhythm — vary short punchy sentences with longer development\n"
            "7. Bold sparingly — only sharpest claims, never structural markers\n"
            "8. Last paragraph: one sentence only. A concrete image, a paradox, or an unresolved reframing. Never a summary, never hope, never call-to-action. The essay stops mid-thought — but precisely.\n"
            "9. 700-2000 words body — match the original target length, do not shrink\n"
            "10. Author\'s disability is their EXPERTISE and LENS, never tragedy or limitation\n"
            "11. Crip culture references (Sins Invalid, crip time, disability justice) only when they fit naturally\n\n"
            "Return ONLY the complete rewritten article (frontmatter preserved + image lines preserved "
            "+ rewritten body). No commentary, no preamble."
        )

        user_msg = (
            f"STYLE REFERENCE (match this voice and quality):\n"
            f"<gold_standard>\n{gold}\n</gold_standard>\n\n"
            f"ARTICLE TO REWRITE:\n<article>\n{content}\n</article>\n\n"
            "Rewrite the article body to match the publication quality. "
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
            if rewritten and rewritten.count("---") >= 2 and len(rewritten) > 400:
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
                return [], []  # No phantom filenames — frontmatter uses default.png

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
title: {json.dumps(str(metadata['title']))}
date: {metadata['date']}
author: {json.dumps(str(metadata['author']))}
categories: [{', '.join(metadata['categories'])}]
agent_perspective: {json.dumps(str(metadata['agent_perspective']))}
image: /assets/{image_filenames[0] if image_filenames else 'default.png'}
model_used: {metadata.get('model_used', 'unknown')}
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



    def _social_hook(self, agent_name, title, body, max_chars=250):
        """Generate a per-agent social post. Falls back to generic _bsky_hook."""
        import os
        template = _SOCIAL_PROMPTS.get(agent_name)
        if not template:
            return self._bsky_hook(title, body, max_chars)
        try:
            prompt = template.format(title=title, excerpt=body[:500])
            raw = self._call_openai_compat_api(
                url="http://172.19.0.1:8317/v1",
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                system_prompt="Return only the post text. No quotes around it. Under 250 characters.",
                user_prompt=prompt,
                model="claude-sonnet-4-6",
                max_tokens=80,
                timeout=30,
            )
            if not raw:
                return self._bsky_hook(title, body, max_chars)
            raw = raw.strip().strip('"').strip("'")
            if len(raw) > max_chars:
                cut = raw[:max_chars].rfind(".")
                raw = raw[:cut + 1] if cut > max_chars // 2 else raw[:max_chars].rstrip()
            return raw
        except Exception:
            return self._bsky_hook(title, body, max_chars)

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

    def post_to_bluesky(self, title, body, article_file, image_filenames=None, agent_name=None):
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
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return
            y, m, d = parts
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
            hook = self._social_hook(agent_name, title, body, max_chars=max_hook)
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


    def post_to_mastodon(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Mastodon after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
        instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
        if not token or not instance:
            self.logger.debug("Mastodon: no credentials, skipping")
            return

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return
            y, m, d  = parts
            slug     = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url      = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            # Hook — 500 char limit; URL counts as ~23; leave room for tags + spacing
            tags = "#DisabilityJustice #CripMinds #DisabilityArts #AccessibilityMatters"
            # url(23) + newlines(2) + tags + newlines(2) = overhead
            overhead = 23 + 2 + len(tags) + 2
            max_hook = 500 - overhead
            hook = self._social_hook(agent_name, title, body, max_chars=max_hook)
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


    def post_to_tumblr(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Tumblr after successful commit. Non-blocking. OAuth 1.0a HMAC-SHA1."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse
        import hmac, hashlib, base64, time, uuid

        ck  = os.environ.get("TUMBLR_CONSUMER_KEY", "")
        cs  = os.environ.get("TUMBLR_CONSUMER_SECRET", "")
        at  = os.environ.get("TUMBLR_ACCESS_TOKEN", "")
        ats = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET", "")
        blog = os.environ.get("TUMBLR_BLOG", "").strip().rstrip(".tumblr.com")
        if not all([ck, cs, at, ats, blog]):
            self.logger.debug("Tumblr: no credentials, skipping")
            return

        def _oauth_header(method, url, params, body_params=None):
            ts    = str(int(time.time()))
            nonce = uuid.uuid4().hex
            oauth = {
                "oauth_consumer_key":     ck,
                "oauth_nonce":            nonce,
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp":        ts,
                "oauth_token":            at,
                "oauth_version":          "1.0",
            }
            all_params = {k: v for k, v in {**oauth, **(params or {}), **(body_params or {})}.items() if v is not None}
            sorted_params = "&".join(
                f"{urllib.parse.quote(k, safe='')}"
                f"={urllib.parse.quote(str(v), safe='')}"
                for k, v in sorted(all_params.items())
            )
            base = "&".join([
                urllib.parse.quote(method.upper(), safe=""),
                urllib.parse.quote(url, safe=""),
                urllib.parse.quote(sorted_params, safe=""),
            ])
            signing_key = f"{urllib.parse.quote(cs, safe='')}&{urllib.parse.quote(ats, safe='')}"
            sig = base64.b64encode(
                hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()
            ).decode()
            oauth["oauth_signature"] = sig
            return "OAuth " + ", ".join(
                f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
                for k, v in sorted(oauth.items())
            )

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return
            y, m, d  = parts
            slug     = slug_md[11:].replace(".md", "")
            site_url = os.environ.get("SITE_URL", "https://cripminds.com")
            url      = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"

            hook = self._bsky_hook(title, body, max_chars=250)
            tags = "disability justice,crip culture,disability arts,accessibility,creative technology,cripminds"

            api_url = f"https://api.tumblr.com/v2/blog/{blog}/post"

            # Try photo post with hero image, fall back to link post
            hero = None
            if image_filenames:
                hero_name = next((fn for fn in image_filenames if "_setting_1" in fn), image_filenames[0])
                hero = self.assets_dir / hero_name

            if hero and hero.exists():
                img_bytes = hero.read_bytes()
                mime = mimetypes.guess_type(str(hero))[0] or "image/jpeg"
                boundary = "----TumblrBoundary"
                def _part(name, value):
                    return (f"--{boundary}\r\nContent-Disposition: form-data; "
                            f'name="{name}"\r\n\r\n{value}\r\n').encode()
                body_bytes = (
                    b"".join([
                        _part("type", "photo"),
                        _part("caption", f'<p>{__import__("html").escape(hook)}</p><p><a href="{url}">{__import__("html").escape(title)}</a></p>'),
                        _part("link", url),
                        _part("tags", tags),
                        _part("native_inline_images", "true"),
                        f"--{boundary}\r\nContent-Disposition: form-data; "
                        f'name="data[0]"; filename="{hero.name}"\r\n'
                        f"Content-Type: {mime}\r\n\r\n".encode()
                        + img_bytes
                        + f"\r\n--{boundary}--\r\n".encode()
                    ])
                )
                body_params_for_sig = {
                    "type": "photo", "caption": f'<p>{hook}</p><p><a href="{url}">{title}</a></p>',
                    "link": url, "tags": tags,
                }
                auth = _oauth_header("POST", api_url, {}, body_params_for_sig)
                req = ureq.Request(
                    api_url, data=body_bytes,
                    headers={"Authorization": auth,
                             "Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST",
                )
            else:
                body_params = {
                    "type": "link", "title": title, "url": url,
                    "description": hook, "tags": tags,
                }
                auth = _oauth_header("POST", api_url, {}, body_params)
                req = ureq.Request(
                    api_url,
                    data=urllib.parse.urlencode(body_params).encode(),
                    headers={"Authorization": auth,
                             "Content-Type": "application/x-www-form-urlencoded"},
                    method="POST",
                )

            with ureq.urlopen(req, timeout=20) as r:
                result = json.loads(r.read())
            post_id = result.get("response", {}).get("id", "?")
            self.logger.info("Tumblr: posted id=%s → https://%s.tumblr.com/post/%s", post_id, blog, post_id)

        except Exception as e:
            self.logger.warning("Tumblr post failed: %s", e)


    def _send_newsletter(self, title, content, article_file, agent_name):
        """Send newsletter to subscribers via newsletter-send.py (non-blocking)."""
        import subprocess, os
        try:
            slug_md = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return
            y, m, d = parts
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
            if result.returncode != 0:
                self.logger.warning("Newsletter send failed (exit %d): %s", result.returncode, result.stderr.strip())
            else:
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
            source_text = self.fetch_source_article(discovery.get('url', ''))
            pool_topic   = discovery.get('url', '').split('/')[2] if discovery.get('url') else 'general'
            pool_links   = self.get_pool_links(pool_topic)
            
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
            source_text = None
            pool_links   = []
        
        agent_info = self.agents.get(agent_name)
        if not agent_info:
            self.logger.error("Unknown agent: %s", agent_name)
            return None

        register, register_prompt = self._pick_register()
        target_words = self._pick_length()
        self.logger.info("Register: %s | Target words: %d", register, target_words)

        beat_nudge  = self._get_beat_nudge(agent_name)
        cross_ref   = self._get_cross_reference(agent_name)

        # Step 3: Generate content — prompt asks LLM for its own title
        if pool_links:
            _link_lines = '\n'.join(f"- {l['title']}: {l['url']}" for l in pool_links)
            link_block = (
                "LINK POOL — weave 0-2 of these into your essay as inline links. "
                "Pick only if the connection is real and non-obvious. Never force a link. "
                "The link is woven into a sentence as if you discovered it while writing. "
                "If none fit, use none.\n" + _link_lines + "\n\n"
            )
        else:
            link_block = ""

        prompt = (
            "Voice and style:\n"
            "- First person, expert authority, no hedging\n"
            "- Disability as culture and identity — never as tragedy, never as inspiration\n"
            "- Open with a specific concrete moment or a single sharp claim — not a scene-setter, not a question, not statistics\n"
            "- One thesis the whole essay serves — state it early, return to it\n"
            "- Reference real disabled artists, theorists, activists, or events by name where relevant\n"
            "- Challenge one assumption the reader probably holds without announcing you are doing so\n"
            "- Long developed paragraphs — not listicles, not bullet points, not 3-sentence paragraphs\n"
            "- Section headers are statements or fragments, never questions\n"
            "- Write for a reader who has already read the basics — go deeper, go stranger, go more specific\n"
            "- Tone: direct, dry when needed, never inspirational, never corporate wellness\n\n"
            "ENDING: Your last paragraph is one sentence. It is a concrete image, a paradox, or a reframing that makes the reader sit with something unresolved. Never summarize. Never offer hope. Never call to action. Never conclude. The essay stops mid-thought — but precisely.\n\n"
            f"REGISTER: {register}. {register_prompt}\n\n"
            f"LENGTH: ~{target_words} words. Do not pad. Do not rush. Every paragraph earns the next.\n\n"
            f"{agent_info['prompt_block']}\n\n"
            f"{('SOURCE MATERIAL (from the article that inspired this piece — use 2-4 specific facts, names, dates, or quotes as anchors. Do not reproduce its structure or argument — take a different angle):\n---\n' + source_text + '\n---\n\n') if source_text else ''}"
            f"{link_block}"
            f"Angle/inspiration: {title}\n"
            f"{source_note}\n\n"
            f"{beat_nudge}"
            f"{('THREAD: ' + cross_ref['agent'] + ' recently wrote \"' + cross_ref['title'] + '\"\n' + 'Their opening: \"' + cross_ref['first_paragraph'] + '\"\n' + 'You may respond to, disagree with, extend, or complicate their argument. Do so only if it produces a stronger essay. Be specific about what you are responding to. Do not summarize their article. Do not be polite about it.\n\n') if cross_ref else ''}"
            "Return format — EXACTLY as follows:\n"
            f"TITLE: [your sharp essay title, not the angle above]\n\n"
            f"[essay body, ~{target_words} words, starting directly — no H1 heading, no \"By {agent_name}\"]"
        )

        try:
            raw_content, used_provider, actual_model = self.call_llm_via_openclaw_session(prompt)
        except Exception as e:
            self.logger.error("LLM call raised exception: %s — using fallback", e)
            raw_content, used_provider, actual_model = None, "fallback", "fallback"

        if not raw_content:
            self.logger.info("Using high-quality fallback article")
            raw_content = self.generate_fallback_article(title, agent_name, agent_info)
            used_provider = "fallback"
            actual_model = "fallback"

        # Parse TITLE: prefix from content
        extracted_title = title  # fallback to angle
        content = raw_content
        if raw_content and raw_content.lstrip().startswith('TITLE:'):
            first_newline = raw_content.find('\n')
            if first_newline > 0:
                extracted_title = raw_content[:first_newline][6:].strip().strip('"')
                content = raw_content[first_newline:].lstrip('\n')
                self.logger.info(f"LLM title: {extracted_title}")
            else:
                # No newline — strip the TITLE: line to avoid corrupting article body
                content = raw_content.lstrip()
                if content.startswith('TITLE:'):
                    content = ''  # malformed; fallback title already set above

        # Step 3b: Rewrite with Opus if generated by a weaker provider.
        # Check both provider name AND actual model from response — catches silent
        # CLIProxy fallbacks where the requested model differs from what was served.
        opus_providers = {"Claude Opus 4.6 (CLIProxy)"}
        is_opus = (used_provider in opus_providers
                   and actual_model is not None
                   and "opus" in actual_model.lower())
        written_by = actual_model or used_provider
        if not is_opus:
            self.logger.info("Written by %s — running Opus rewrite pass", written_by)
            # Build temporary full article so Opus can see frontmatter context
            temp_front = f"---\nlayout: post\ntitle: {json.dumps(str(extracted_title))}\nauthor: {agent_name}\n---\n\n"
            rewritten = self.rewrite_with_opus(temp_front + content)
            # Strip the temp frontmatter back off
            if rewritten and rewritten.startswith("---"):
                # Find closing --- of frontmatter robustly
                fm_end = rewritten.find("\n---\n", 3)
                if fm_end != -1:
                    content = rewritten[fm_end + 5:].lstrip("\n")
                elif rewritten.count("---") >= 2:
                    try:
                        second = rewritten.index("---", 3)
                        content = rewritten[second + 3:].lstrip("\n")
                    except ValueError:
                        self.logger.warning("Could not parse Opus rewrite frontmatter, keeping original content")
            model_used_label = f"claude-opus-4-6 (rewrote {written_by})"
        else:
            self.logger.info("Written by %s — no rewrite needed", written_by)
            model_used_label = written_by

        # Record beat for this article
        self._record_beat(agent_name, extracted_title, content)

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
            'source_note': source_note,
            'model_used': model_used_label,
        }

        # Step 5: Generate images (placeholder)
        try:
            image_filenames, image_descriptions = self.generate_images(content, slug)
        except Exception as e:
            self.logger.warning('Image generation failed: %s -- continuing without images', e)
            image_filenames, image_descriptions = [], []

        # Step 6: Create article file
        article_file = self.create_article_file(metadata, content, image_filenames, image_descriptions)

        # Step 6b: Non-blocking citation review
        review_file, is_clean = self.validate_article(content, article_file, slug)

        # Step 7: Commit article + review sidecar
        commit_success = self.commit_to_git(article_file, image_filenames, review_file)

        # Step 8: Post to Bluesky + Mastodon + Tumblr (non-blocking)
        if commit_success:
            self.post_to_bluesky(extracted_title, content, article_file, image_filenames, agent_name=agent_name)
            self.post_to_mastodon(extracted_title, content, article_file, image_filenames, agent_name=agent_name)
            self.post_to_tumblr(extracted_title, content, article_file, image_filenames, agent_name=agent_name)

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
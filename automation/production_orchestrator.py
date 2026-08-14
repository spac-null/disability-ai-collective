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

# Module-split, Stage 2 (2026-08-09): the pure-data constants that used to live here
# now live in orchestrator/config.py, imported via * + __all__ below so every
# existing unqualified reference (CLIPROXY_URL, _REGISTERS, etc.) keeps working
# unchanged. sys.path insert makes `orchestrator` importable when this file is run
# directly as a script (python3 automation/production_orchestrator.py), which is
# how it's always invoked in production — see automation/README.md.
sys.path.insert(0, str(Path(__file__).parent))
from orchestrator.config import *  # noqa: F401,F403 — see orchestrator/config.py __all__
from orchestrator import personas
from orchestrator.debate import DebateMixin
from orchestrator.images import ImagesMixin
from orchestrator.publish import PublishMixin
from orchestrator.gate import GateMixin
from orchestrator.llm import LLMMixin
from orchestrator.discovery import DiscoveryMixin
from orchestrator.content_checks import ContentChecksMixin
from orchestrator.fact_check import FactCheckMixin
from orchestrator.review import ReviewMixin
from orchestrator.social import SocialMixin
from orchestrator.generate import GenerateMixin
from orchestrator.cj2_shadow import CJ2ShadowMixin
from orchestrator.testimony_l2 import TestimonyL2Mixin


class ProductionOrchestrator(DebateMixin, ImagesMixin, PublishMixin, GateMixin, LLMMixin, DiscoveryMixin,
                              ContentChecksMixin, FactCheckMixin, ReviewMixin, SocialMixin, GenerateMixin,
                              CJ2ShadowMixin, TestimonyL2Mixin):
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.posts_dir = self.repo_root / "_posts"
        self.drafts_dir = self.repo_root / "_drafts"
        self.assets_dir = self.repo_root / "assets"
        self.discovery_db = self.repo_root / "disability_findings.db"

        # Ensure directories exist
        self.posts_dir.mkdir(exist_ok=True)
        self.drafts_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logger()

        # FIXED: Proper agents configuration
        self.agents = personas.AGENTS

        # Per-run source-text memo (see DiscoveryMixin.get_source_text) -- lives
        # exactly as long as this process/run, cleared by process exit, nothing
        # to clean up.
        self._source_text_cache = {}

        # Per-run degradation tracker, added 2026-08-10 after a confirmed live
        # incident: the 2026-08-10 09:00 run lost its Fable brief, both editorial
        # revision passes failed, and the gate's own LLM rule-check call 403'd --
        # yet every one of those failures was caught, logged as a WARNING, and
        # silently absorbed, so the article shipped looking exactly like a clean
        # run. Stages append their own name here on failure (fable_brief, gate_llm,
        # editorial_revision); publish.py stamps this into the article's own
        # frontmatter as pipeline_degraded so a bad run is visible after the fact,
        # not just in a log line nobody was watching.
        self._degraded_stages = []

    def _setup_logger(self):
        """Setup proper logging."""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.repo_root / 'automation.log')
            ]
        )
        return logging.getLogger(__name__)

    def _today(self):
        """Return override date if set, else today."""
        return getattr(self, 'override_date', None) or datetime.now().strftime('%Y-%m-%d')



    def run_production_automation(self):
        """
        PRODUCTION-READY main execution flow
        """
        import fcntl
        lock_path = self.repo_root / '.orchestrator.lock'
        lock_fh = open(lock_path, 'w')
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.logger.warning("Orchestrator already running — skipping (lock: %s)", lock_path)
            lock_fh.close()
            return {"status": "skipped", "message": "Another instance is running"}
        try:
            return self._run_production_automation_locked()
        finally:
            fcntl.flock(lock_fh, fcntl.LOCK_UN)
            lock_fh.close()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--link-audit", action="store_true",
                        help="Scan all articles and inject missing links")
    parser.add_argument("--dry-run", action="store_true",
                        help="With --link-audit: report changes without writing files")
    parser.add_argument("--date", type=str, default=None,
                        help="Override article date (YYYY-MM-DD), implies --force")
    parser.add_argument("--force", action="store_true",
                        help="Run even if article already exists for target date")
    parser.add_argument("--agent", type=str, default=None,
                        help="Force specific agent: 'Pixel Nova', 'Siri Sage', 'Maya Flux', 'Zen Circuit'")
    parser.add_argument("--retract", type=str, default=None, metavar="SLUG",
                        help="Retract article by slug (deletes file, removes Bluesky post)")
    parser.add_argument("--post-today", action="store_true",
                        help="Post today's already-published article to Bluesky (use if social posting was skipped)")
    parser.add_argument("--debate", nargs=2, metavar=("AGENT_A", "AGENT_B"),
                        help="Generate a two-voice debate: --debate 'Pixel Nova' 'Siri Sage'")
    parser.add_argument("--topic", type=str, default=None,
                        help="Topic/fault line for --debate (optional; uses relationships.json if omitted)")
    parser.add_argument("--post-social", type=str, default=None, metavar="ARTICLE_PATH",
                        help="Post social (Bluesky/Mastodon/Tumblr) for a promoted article path")
    args = parser.parse_args()

    orchestrator = ProductionOrchestrator()
    if args.date:
        orchestrator.override_date = args.date
        orchestrator.force_run = True
    elif args.force:
        orchestrator.force_run = True
    if args.agent:
        orchestrator.override_agent = args.agent

    if args.post_social:
        af = Path(args.post_social)
        if not af.exists():
            print(f"Article not found: {af}")
            sys.exit(1)
        lines = af.read_text(encoding="utf-8").split('\n')
        title = next((l.split(':', 1)[1].strip().strip('"') for l in lines if l.startswith('title:')), af.stem)
        sep = [i for i, l in enumerate(lines) if l.strip() == '---']
        body = '\n'.join(lines[sep[1]+1:]) if len(sep) >= 2 else ''
        agent = next((l.split(':', 1)[1].strip().strip('"') for l in lines if l.startswith('author:')), None)
        # Assets are written under the de-dated slug (generate_images(content, slug, ...)),
        # not the article filename's stem (which keeps the YYYY-MM-DD- prefix) — globbing
        # on af.stem matched nothing, so every social post has been going out with no
        # image attached since the publish queue landed (d75d362).
        slug = af.stem[11:] if re.match(r'\d{4}-\d{2}-\d{2}-', af.stem) else af.stem
        images = [f.name for f in orchestrator.repo_root.glob(f"assets/{slug}_*.jpg")]
        bsky_uri = orchestrator.post_to_bluesky(title, body, af, image_filenames=images, agent_name=agent)
        mastodon_url = orchestrator.post_to_mastodon(title, body, af, image_filenames=images, agent_name=agent)
        tumblr_url = orchestrator.post_to_tumblr(title, body, af, image_filenames=images, agent_name=agent)
        orchestrator._store_social_uri(slug, bsky_uri or "", agent=agent,
                                        mastodon_url=mastodon_url or "", tumblr_url=tumblr_url or "")
        print(f"Social posts sent. Bluesky URI: {bsky_uri}")
    elif args.retract:
        orchestrator.retract_article(args.retract)
    elif args.debate:
        result = orchestrator.generate_debate(args.debate[0], args.debate[1], topic=args.topic)
        print(result)
    elif args.post_today:
        from datetime import date as _date
        today = str(_date.today())
        matches = list(orchestrator.posts_dir.glob(f"{today}-*.md"))
        if not matches:
            print(f"No article found for {today}")
        else:
            af = matches[0]
            lines = af.read_text().split('\n')
            title = next(l.split(':', 1)[1].strip().strip('"') for l in lines if l.startswith('title:'))
            sep = [i for i, l in enumerate(lines) if l == '---']
            body = '\n'.join(lines[sep[1]+1:])
            agent = next((l.split(':', 1)[1].strip().strip('"') for l in lines if l.startswith('author:')), None)
            _slug = af.stem[11:] if re.match(r'\d{4}-\d{2}-\d{2}-', af.stem) else af.stem
            images = [f.name for f in orchestrator.repo_root.glob(f"assets/{_slug}_*.jpg")]
            uri = orchestrator.post_to_bluesky(title, body, af, image_filenames=images, agent_name=agent)
            print(f"Posted: {uri}")
    elif args.link_audit:
        result = orchestrator.link_audit(dry_run=args.dry_run)
        updated = result["updated"]
        print(f"Audited {result['audited']} articles — {len(updated)} updated, {len(result['skipped'])} skipped")
        for r in updated:
            print(f"  {r['file']}: +{len(r['added'])} links")
            for item in r["added"]:
                print(f"    [{item['text']}] -> {item['url']}")
    else:
        result = orchestrator.run_production_automation()
        print(json.dumps(result, indent=2))
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


class ProductionOrchestrator(DebateMixin, ImagesMixin, PublishMixin, GateMixin, LLMMixin, DiscoveryMixin,
                              ContentChecksMixin):
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

    def _extract_verifiable_claims(self, content):
        """Cheap extraction pass covering all four categories the (advisory-only,
        LLM-self-report) citation check flags: QUOTE, STUDY, STAT, EVENT. Feeds
        _web_verify_quote (QUOTE) and _web_verify_claim (STUDY/STAT/EVENT) — the
        citation check has no way to know if a claim is real, only whether the
        article names a source for it; these are the steps that actually check.

        Superset of the old _extract_named_quotes (QUOTE-only) — kept the same
        JSON-in-text extraction pattern, just widened the categories.
        """
        import json as _json
        SYSTEM = (
            "Extract every claim from this article that could be independently "
            "verified against real sources, categorized by type:\n"
            "- QUOTE: exact text inside quotation marks attributed to a specific "
            "named real person, other than the first-person narrator. Not "
            "paraphrase, not a summarised position, not a conditional-mood "
            "statement ('she would say').\n"
            "- STUDY: a named study, report, or audit attributed to a specific "
            "organization.\n"
            "- STAT: a specific number, percentage, or statistic attributed to a "
            "source.\n"
            "- EVENT: a specific dated event or occurrence stated as fact.\n\n"
            "For QUOTE: 'subject' is the person's full name, 'claim' is the exact "
            "quoted text. For STUDY/STAT/EVENT: 'subject' is the organization or "
            "source named (empty string if none named), 'claim' is the specific "
            "fact stated.\n\n"
            "Return ONLY valid JSON:\n"
            '{"claims": [{"type": "QUOTE|STUDY|STAT|EVENT", "subject": "...", "claim": "..."}]}\n'
            'If none: {"claims": []}'
        )
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL, api_key=CLIPROXY_KEY,
                system_prompt=SYSTEM, user_prompt=content,
                model="openrouter/claude-haiku-4.5",
                max_tokens=900, timeout=30, no_think=True,
            )
            match = re.search(r'\{.*\}', raw or "", re.DOTALL)
            data = _json.loads(match.group(0)) if match else {}
            return [
                c for c in data.get("claims", [])
                if c.get("claim") and c.get("type") in ("QUOTE", "STUDY", "STAT", "EVENT")
            ]
        except Exception as e:
            self.logger.warning("Verifiable-claim extraction failed: %s", e)
            return []

    def _web_verify_quote(self, person, quote):
        """Verify one quote against live web sources via Perplexity Sonar.

        Direct OpenRouter call, bypassing CLIProxyAPI — confirmed empirically that
        CLIProxyAPI 400s on both unlisted models ("unknown provider") and the
        ':online' web-search suffix on models it does recognise, so search-grounded
        verification isn't reachable through it. This reuses the same
        OPENROUTER_API_KEY / direct-OpenRouter pattern _call_editorial_model already
        falls back to when CLIProxy is down.

        Returns (verdict, reason) — verdict is VERIFIED / UNVERIFIABLE / CONTRADICTED.

        CONTRADICTED intentionally covers two cases, not just "nothing found at all":
        outright invention, AND the narrower "real person, real general view, but this
        exact wording is invented" case. Live-tested three times against a real draft's
        quote attributed to photographer Pete Eckert: search consistently found him
        discussing seeing through sound/touch/memory in real interviews, but never this
        exact phrasing — a looser verdict definition classified that as UNVERIFIABLE
        (non-blocking) each time, which is too permissive for something presented to
        the reader inside quotation marks as his verbatim words. Quotation marks are a
        verbatim claim; a verified paraphrase attested elsewhere does not satisfy it.
        """
        import os as _os
        key = _os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            return "UNVERIFIABLE", "OPENROUTER_API_KEY not set — could not search"
        word_count = len(quote.split())
        SHORT_PHRASE_MAX_WORDS = 11  # below this: loose standard; 12+ is the strict-verbatim branch
        prompt = (
            f'Person: {person}\nQuoted as saying: "{quote}" ({word_count} words)\n\n'
            "Search for this attributed to this person in any real source (interview, "
            "article, book, talk).\n\n"
            "Two different standards apply depending on length — read both before judging:\n"
            f"- {SHORT_PHRASE_MAX_WORDS} words or fewer, OR a named term/concept/title (e.g. a coined "
            "phrase, the name of a practice or work): treat as VERIFIED if the person is "
            "real, demonstrably associated with this term or the idea behind this short "
            "phrase, and you have no specific reason to think it's wrong. Do not demand a "
            "verbatim standalone citation for something this short — short phrases get "
            "paraphrased and re-quoted constantly, and 'not found in this exact form' is "
            "not evidence of fabrication at this length.\n"
            "- A longer quote reading as one continuous, specific first-person sentence or "
            "passage (roughly 12+ words of connected prose, a complete thought in the "
            "person's own invented voice): this is a verbatim claim and needs a real match. "
            "VERIFIED only if you find this wording, or phrasing close enough a reader would "
            "recognise it as the same sentence. If you only find the person expressing a "
            "similar general idea in visibly different words, that is CONTRADICTED, not "
            "VERIFIED — a real view rephrased into invented prose is still invented prose "
            "presented as their verbatim words.\n\n"
            "Respond in exactly this format:\n"
            "VERDICT: VERIFIED | UNVERIFIABLE | CONTRADICTED\n"
            "REASON: one sentence, cite a URL if you found one.\n"
            "UNVERIFIABLE = you could not find enough about this person or topic to judge "
            "either way — reserve this for genuine search failure, not 'found the theme "
            "but not the exact wording' on a long quote (that's CONTRADICTED per above)."
        )
        try:
            raw = self._call_openai_compat_api(
                url="https://openrouter.ai/api/v1", api_key=key,
                system_prompt="You are a fact-checker with live web search access.",
                user_prompt=prompt,
                model="perplexity/sonar",
                max_tokens=250, timeout=30,
            )
            m = re.search(r"VERDICT:\s*(VERIFIED|UNVERIFIABLE|CONTRADICTED)", raw or "", re.IGNORECASE)
            verdict = m.group(1).upper() if m else "UNVERIFIABLE"
            r = re.search(r"REASON:\s*(.+)", raw or "", re.DOTALL)
            reason = r.group(1).strip()[:220] if r else (raw or "")[:220]
            return verdict, reason
        except Exception as e:
            self.logger.warning("Web verify failed for %s: %s", person, e)
            return "UNVERIFIABLE", f"search failed: {e}"

    def _web_verify_claim(self, claim_type, subject, claim_text):
        """Verify a STUDY, STAT, or EVENT claim against live web sources via
        Perplexity Sonar. Same direct-OpenRouter mechanism as _web_verify_quote,
        but a distinct, more lenient standard per type — quotes are a verbatim
        claim (get their own calibrated logic in _web_verify_quote); these three
        are not, and each has a different false-positive risk if checked the same
        strict way:

        STUDY gets a strict standard close to quotes (a named org either published
        something like this or it didn't — similarly checkable).

        STAT is deliberately lenient: the same number gets restated in
        incompatible-but-equally-correct forms across sources ("73%" / "nearly
        three-quarters" / "roughly 3 in 4"), so CONTRADICTED requires an actual
        conflicting figure, not just "couldn't find this exact phrasing".

        EVENT is deliberately lenient in a different way: a claim describing
        something recent may not be indexed by search yet, which is NOT evidence
        of fabrication — CONTRADICTED requires a source actively contradicting the
        event (wrong date, wrong people, didn't happen), not mere absence of
        coverage.

        Returns (verdict, reason) — verdict is VERIFIED / UNVERIFIABLE / CONTRADICTED.
        """
        import os as _os
        key = _os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            return "UNVERIFIABLE", "OPENROUTER_API_KEY not set — could not search"

        if claim_type == "STUDY":
            standard = (
                "CONTRADICTED = you searched and found no organization or study "
                "matching this at all — the named organization doesn't appear to "
                "exist, or exists but nothing resembling this study/report/audit "
                "is attributed to it. VERIFIED = the organization is real and "
                "plausibly connected to this finding."
            )
        elif claim_type == "STAT":
            standard = (
                "Numbers get restated in different forms across sources (73% vs "
                "'nearly three-quarters' vs 'roughly 3 in 4') — do not require "
                "exact phrasing or an exact figure match. CONTRADICTED = you found "
                "a source giving a MATERIALLY DIFFERENT number for the same claim "
                "— not just 'couldn't find this exact figure stated this way'. If "
                "you found nothing confirming or conflicting, that is "
                "UNVERIFIABLE, never CONTRADICTED."
            )
        else:  # EVENT
            standard = (
                "This claim may describe something recent enough that search "
                "hasn't indexed it yet — that is NOT evidence of fabrication. "
                "CONTRADICTED = you found a source actively contradicting this "
                "event (wrong date, wrong people involved, or it demonstrably "
                "didn't happen). Absence of coverage alone is UNVERIFIABLE, never "
                "CONTRADICTED."
            )

        prompt = (
            f"Claim type: {claim_type}\nSource/organization named: {subject or '(none named)'}\n"
            f'Claim: "{claim_text}"\n\n'
            "Search for whether this claim is accurate.\n\n"
            f"{standard}\n\n"
            "Respond in exactly this format:\n"
            "VERDICT: VERIFIED | UNVERIFIABLE | CONTRADICTED\n"
            "REASON: one sentence, cite a URL if you found one."
        )
        try:
            raw = self._call_openai_compat_api(
                url="https://openrouter.ai/api/v1", api_key=key,
                system_prompt="You are a fact-checker with live web search access.",
                user_prompt=prompt,
                model="perplexity/sonar",
                max_tokens=250, timeout=30,
            )
            m = re.search(r"VERDICT:\s*(VERIFIED|UNVERIFIABLE|CONTRADICTED)", raw or "", re.IGNORECASE)
            verdict = m.group(1).upper() if m else "UNVERIFIABLE"
            r = re.search(r"REASON:\s*(.+)", raw or "", re.DOTALL)
            reason = r.group(1).strip()[:220] if r else (raw or "")[:220]
            return verdict, reason
        except Exception as e:
            self.logger.warning("Web verify failed for %s claim (%s): %s", claim_type, subject, e)
            return "UNVERIFIABLE", f"search failed: {e}"

    def _run_web_fact_check(self, content, claim_cap=4):
        """Extract verifiable claims from content and check each against live web
        search. Used both for the initial pass and to re-verify after a repair
        attempt, so the two runs stay identical in method.

        claim_cap limits how many claims per category get checked (cost/latency
        for the common case). Confirmed live 2026-08-08: a repair pass grounding
        a draft in its real source naturally introduces NEW specific claims (in
        that case, a real, verbatim-accurate statistic pulled from deeper in the
        source than the original draft ever cited) -- the default cap could let a
        genuinely new fabrication slide through the post-repair re-check
        unexamined just because 4 other claims filled the slots first. That run
        happened to check out real, but the recheck wasn't actually guaranteed to
        catch it if it hadn't been. Callers re-verifying a repair should pass a
        higher cap; the raw web-search cost only recurs in the rare
        already-contradicted case, not on every normal article.

        Returns dict: lines (review text), contradicted (QUOTE/STUDY -- always
        blocks), advisory (single EVENT/STAT contradiction -- doesn't block alone),
        unverifiable_count, soft_contradicted_count (CONTRADICTED EVENT/STAT)."""
        result = {
            "lines": ["(no verifiable claims found)"], "contradicted": [], "advisory": [],
            "unverifiable_count": 0, "soft_contradicted_count": 0,
        }
        try:
            claims = self._extract_verifiable_claims(content)
            if not claims:
                return result
            result["lines"] = []
            quote_claims = [c for c in claims if c["type"] == "QUOTE"][:claim_cap]
            other_claims = [c for c in claims if c["type"] in ("STUDY", "STAT", "EVENT")][:claim_cap]
            for c in quote_claims:  # default cap covers rule 33's "2-3 named people"
                verdict, reason = self._web_verify_quote(c["subject"], c["claim"])
                result["lines"].append(f"[{verdict}] QUOTE — {c['subject']}: \"{c['claim'][:80]}\" — {reason}")
                if verdict == "CONTRADICTED":
                    result["contradicted"].append(c)
                elif verdict == "UNVERIFIABLE":
                    result["unverifiable_count"] += 1
            for c in other_claims:  # default cap — cost/latency
                verdict, reason = self._web_verify_claim(c["type"], c.get("subject", ""), c["claim"])
                result["lines"].append(f"[{verdict}] {c['type']} — {c.get('subject') or '(unnamed)'}: \"{c['claim'][:80]}\" — {reason}")
                if verdict == "CONTRADICTED":
                    if c["type"] == "STUDY":
                        result["contradicted"].append(c)
                    else:
                        result["advisory"].append(c)
                        result["soft_contradicted_count"] += 1
                elif verdict == "UNVERIFIABLE":
                    result["unverifiable_count"] += 1
        except Exception as e:
            self.logger.warning("Web fact-check failed: %s", e)
            result["lines"] = [f"CHECK_FAILED: {e}"]
        return result

    _FIGURE_BLOCK_RE = re.compile(r'<figure class="article-figure">.*?</figure>\n?', re.DOTALL)

    def _attempt_fabrication_repair(self, article_file, contradicted_items, source_url):
        """One grounded repair pass before hard-blocking a draft with a contradicted
        quote/study. Re-fetches the real source article and asks the model to fix
        ONLY the flagged passages using real material from it -- confirmed live
        2026-08-08 that the failure mode isn't always 'one bad line': a draft
        invented an entire biography, flood story, and quote for a real named
        person who doesn't appear in its own source article at all. A human fixed
        that one by hand (re-fetch source, replace the fabricated frame with the
        real people/events actually in it) -- this automates the same move.

        Returns (new_body_with_figures, new_title_or_None), or (None, None) if the
        source couldn't be fetched or the model call failed -- caller falls back to
        the existing hard block, unchanged.
        """
        if not source_url:
            return None, None
        source_text = self.fetch_source_article(source_url, max_chars=6000)
        if not source_text:
            self.logger.warning("Fabrication repair: could not fetch source %s", source_url)
            return None, None

        full_text = article_file.read_text()
        fm_match = re.match(r'^(---\n.*?\n---\n)(.*)$', full_text, re.DOTALL)
        if not fm_match:
            return None, None
        body = fm_match.group(2)

        flagged_desc = "\n".join(
            f"- {c['type']} attributed to {c.get('subject') or '(unnamed)'}: "
            f"\"{c['claim'][:150]}\" -- NOT found in any real source, confirmed by live web search"
            for c in contradicted_items
        )
        system = (
            "You are the editorial director of a disability-culture publication. A "
            "fact-checker just caught this draft inventing something -- a quote, a "
            "study, or a person's involvement that doesn't check out against a live "
            "web search. Below is the REAL source article the piece is supposed to "
            "be grounded in.\n\n"
            "Fix ONLY what's broken. Rewrite the passages built on the flagged "
            "claim(s) using real people, quotes, and events from the source article. "
            "Rules:\n"
            "- Do not invent a replacement quote or a replacement person. If the "
            "source doesn't name anyone who said something quotable, don't use "
            "quotation marks -- paraphrase, or ground the passage in a concrete real "
            "detail from the source instead.\n"
            "- If the flagged subject is a real named person who does not appear in "
            "the source at all, remove them from the piece entirely and replace them "
            "with whoever or whatever the source actually describes. Do not keep "
            "them in under a softened claim.\n"
            "- Preserve everything else exactly as written: voice, structure, "
            "unrelated paragraphs, other named sources not being flagged, and every "
            "<figure>...</figure> HTML block character-for-character, in its "
            "original position.\n"
            "- If the article's title names the fabricated subject, put a corrected "
            "title on its own first line as 'TITLE: ...'; otherwise omit that line "
            "entirely.\n\n"
            "Return the complete corrected article body only -- no preamble, no "
            "commentary."
        )
        user = (
            f"FLAGGED CLAIM(S):\n{flagged_desc}\n\n"
            f"REAL SOURCE ARTICLE:\n---\n{source_text}\n---\n\n"
            f"CURRENT DRAFT BODY:\n{body}"
        )
        try:
            raw = self._call_editorial_model(system, user, max_tokens=6000, timeout=180)
        except Exception as e:
            self.logger.warning("Fabrication repair call failed: %s", e)
            return None, None
        if not raw or len(raw) < len(body) * 0.4:
            self.logger.warning("Fabrication repair returned too little content — keeping original")
            return None, None

        new_title = None
        if raw.lstrip().startswith("TITLE:"):
            first_nl = raw.find("\n")
            if first_nl > 0:
                new_title = raw[:first_nl][6:].strip().strip('"')
                raw = raw[first_nl:].lstrip("\n")
        return raw, new_title

    def _check_persona_crosscite_accuracy(self, body, current_agent):
        """Catch a specific recurring failure mode found in a 2026-08-09 manual
        audit: the generation prompt already instructs the writer NOT to
        name-check another persona mid-argument ("Do NOT signpost it with a
        name-check... Attribution by name belongs in the source note, not the
        third paragraph" — see the cross_cite prompt block above), but the model
        does it anyway in a meaningful fraction of drafts ("Here is where I part
        from Maya Flux, a disability theorist..."). Because the writer isn't
        given the other persona's actual canon in that moment, it invents a
        plausible-sounding field, credential, location, or external website for
        a colleague who is a real, canonical in-house persona with a real,
        specific bio on this very site — e.g. Maya Flux (T6 spinal injury, urban
        planning, Brooklyn) described as a generic "housing rights researcher"
        with a fake mayaflux.com; Siri Sage (blind, acoustic culture, Amsterdam)
        described as "a scholar who writes about AI and disability." This reads
        to a reader (and to any later fact-check) exactly like fabricating
        biographical details about a person, because from the outside a
        cross-referenced house persona and an external real person are
        indistinguishable prose.

        This does not try to stop the name-check itself (the existing prompt
        instruction already asks for that, and rephrasing it further is
        unlikely to move a rate the instruction hasn't moved). Instead it
        catches the specific harm: if another persona IS named in the body,
        verify whatever is said about them against that persona's real,
        canonical bio, and correct anything invented so it can't misdescribe a
        real recurring byline the way today's audit found it doing. Internal
        cross-references in the site's own `[Name](/research/?author=Name)`
        format are correct and left untouched — only inaccurate prose
        description or an external-looking URL for the mentioned persona
        triggers a rewrite.

        Returns (corrected_body_or_None, note_or_None).
        """
        # Exclude the closing "*This article was prompted by...*" source-note
        # line from the scan -- that line legitimately names the source outlet,
        # not another persona, and isn't where this failure mode occurs.
        main_body = re.split(r'\n---\n\*This article was prompted by', body, maxsplit=1)[0]
        mentioned = sorted(
            name for name in _AGENT_SLUG
            if name != current_agent and re.search(rf'\b{re.escape(name)}\b', main_body)
        )
        if not mentioned:
            return None, None
        canon_blocks = []
        for name in mentioned:
            canon = self._load_persona_canon(name)
            if canon:
                canon_blocks.append(f"### Real canon for {name} (ground truth -- do not contradict this)\n{canon}")
        if not canon_blocks:
            return None, None

        system = (
            "You are a copy editor for a disability-culture publication with several "
            "recurring in-house personas (bylines). This draft, written in one "
            "persona's voice, names one or more OTHER personas in its body prose. "
            "Below is each mentioned persona's real, canonical bio.\n\n"
            "Check whether the draft's description of the mentioned persona -- their "
            "field, credentials, location, or any URL given for them -- matches their "
            "real canon. Personas should only ever be cross-referenced via the site's "
            "own internal link format '[Name](/research/?author=Name)' -- never given "
            "an external URL, an invented institution, or an invented field that "
            "isn't in their canon.\n\n"
            "If every mentioned persona is described accurately to their canon, and "
            "any link used for them is already the internal /research/?author= "
            "format, return exactly: NO_CHANGE\n\n"
            "Otherwise, rewrite ONLY the sentence(s) making the inaccurate claim so "
            "the described field/credential/location matches the real canon exactly, "
            "and convert any external-looking URL for that persona to the internal "
            "link format. Do not invent NEW specifics to replace the wrong ones -- "
            "use only what the canon actually says, or fall back to an unattributed "
            "phrasing if the canon doesn't cover the specific claim being made. "
            "Preserve everything else -- voice, structure, argument, all other "
            "paragraphs, and every <figure>...</figure> HTML block character-for-"
            "character -- exactly as written.\n\n"
            "Return the complete corrected article body only -- no preamble, no "
            "commentary."
        )
        user = "\n\n".join(canon_blocks) + f"\n\n### Current draft body\n{main_body}"
        try:
            raw = self._call_editorial_model(system, user, max_tokens=6000, timeout=120)
        except Exception as e:
            self.logger.warning("Persona cross-cite check failed: %s", e)
            return None, None
        if not raw or raw.strip() == "NO_CHANGE":
            return None, None
        if len(raw) < len(main_body) * 0.4:
            self.logger.warning("Persona cross-cite repair returned too little content — keeping original")
            return None, None
        # Re-attach whatever followed main_body in the original (the source-note
        # footer, if present) -- the model only ever saw/edited main_body.
        suffix = body[len(main_body):]
        return raw + suffix, f"Corrected cross-persona reference(s) to match canon: {', '.join(mentioned)}"

    def validate_article(self, content, article_file, slug, target_words=None):
        """Non-blocking review: citations + readability + rule compliance. Never delays commit."""
        import os, json, urllib.request as ureq
        from datetime import datetime as dt

        # ── 1. Citation check ──────────────────────────────────────────────
        CITATION_SYSTEM = (
            "You are a fact-checker for a disability arts publication. "
            "Extract every specific claim that could be independently verified:\n"
            "- Statistics or percentages with attributed sources\n"
            "- Named studies, reports, or audits with organisations\n"
            "- Direct quotes attributed to named people\n"
            "- Specific events cited as fact\n\n"
            "For each, one line: [FLAG] <claim> | SOURCE: <source or UNATTRIBUTED>\n"
            "Also add a short editorial note at the end under '---' if any claim warrants "
            "particular scrutiny.\n"
            "If nothing to flag, output exactly: CLEAN"
        )
        citation_text = "CLEAN"
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=CITATION_SYSTEM,
                user_prompt=content,
                model="openrouter/claude-sonnet-4.6",
                max_tokens=600,
                timeout=60,
            )
            citation_text = raw or "CLEAN"
        except Exception as e:
            self.logger.warning("Citation extraction failed: %s", e)
            citation_text = f"EXTRACTION_FAILED: {e}"

        # ── 1b. Web fact-check — quotes, studies, stats, events (real search, not
        # LLM self-report) ──────────────────────────────────────────────────────
        # The citation check above can only judge whether the ARTICLE names a source
        # for a claim — it has no way to know if the claim itself is true, so a fully
        # invented quote/study attributed to a real name passes it as long as the
        # draft doesn't cite one. This step actually searches the web.
        #
        # Not all four categories get the same treatment. QUOTE and STUDY are close
        # to binary-checkable (a person either said this, an org either published
        # this, or they didn't) and hard-block promotion on CONTRADICTED — same as
        # QUOTE always did. STAT and EVENT are inherently harder to verify without
        # false positives (numbers get restated in incompatible-but-correct forms
        # across sources; recent events may not be indexed yet), so a CONTRADICTED
        # verdict on those is advisory only — shown here and marks the review
        # FLAGGED, but does not set fact_check_status: blocked. Revisit promoting
        # them to blocking once we've seen the real false-positive rate over some
        # live runs.
        fc = self._run_web_fact_check(content)
        fact_check_lines = fc["lines"]
        contradicted = fc["contradicted"]           # QUOTE/STUDY — blocks promotion
        advisory_flags = fc["advisory"]              # single EVENT/STAT contradiction — flagged, doesn't block alone
        unverifiable_count = fc["unverifiable_count"]
        soft_contradicted_count = fc["soft_contradicted_count"]

        # "Too much false/imagination": one soft-category (EVENT/STAT) contradiction
        # alone can be a search false-positive (restated numbers, under-indexed
        # recent events — see comment above _run_web_fact_check's caller). But
        # confirmed live 2026-08-08: an article got a real person's death wrongly
        # dated by two years (CONTRADICTED EVENT — non-blocking under the old rule)
        # while its separate citation self-report (above) flagged 9 more specific
        # claims as SOURCE: UNATTRIBUTED, including a suspiciously precise dollar
        # figure attributed to a named journalist and an entirely unsourced policy
        # claim. The web fact-check alone (capped at 8 checked claims) never sees
        # that volume — the citation step does. Combine both signals: a single
        # confirmed-wrong soft claim is tolerated on its own (could be noise), but
        # not alongside a pile of unattributed specifics, and two or more
        # confirmed-wrong soft claims is never tolerated.
        #
        # EVENT gets a stricter standard than STAT, added 2026-08-09 after a manual
        # audit of everything published under the old rule turned up roughly a
        # dozen single, isolated CONTRADICTED-EVENT articles that would have shipped
        # unblocked under this same logic: wrong exhibition venue (V&A Dundee vs.
        # the real South Kensington show, closed 5 months before the article ran),
        # wrong museum room number, wrong conference city (Vancouver vs. the real
        # Seoul ICML), wrong street address, wrong publisher/date for a real book.
        # None of those had 2+ soft contradictions or 5+ unattributed citations
        # riding along — each was one clean, isolated wrong fact in an otherwise
        # unremarkable piece, which is exactly the shape this rule was built to
        # let through as "could be noise." It wasn't noise: _web_verify_claim's own
        # EVENT standard already requires a source *actively contradicting* the
        # claim (wrong date/people, or it didn't happen) — mere absence of coverage
        # is UNVERIFIABLE, not CONTRADICTED. That's a much stronger signal than a
        # STAT mismatch (same real number, restated in an incompatible-looking
        # form) or an EVENT that search simply hasn't indexed yet. A single
        # CONTRADICTED EVENT has already cleared a bar that filters out the
        # under-indexing false positives; treat it as sufficient on its own. STAT
        # keeps the more lenient threshold below — restatement risk there is real.
        event_contradicted = any(c.get("type") == "EVENT" for c in advisory_flags)
        unattributed_citations = citation_text.count("SOURCE: UNATTRIBUTED")
        too_much = (
            event_contradicted
            or soft_contradicted_count >= 2
            or unverifiable_count >= 3
            or (soft_contradicted_count >= 1 and unattributed_citations >= 5)
        )
        if too_much:
            self.logger.error(
                "FACT-CHECK: escalating to block — %d soft-contradicted, "
                "%d unverifiable, %d unattributed citation(s) — too much "
                "false/imagination for one piece",
                soft_contradicted_count, unverifiable_count, unattributed_citations
            )
            contradicted = contradicted + advisory_flags
            advisory_flags = []

        # Before hard-blocking, try one grounded repair: re-fetch the real source
        # and ask the model to fix ONLY the flagged passages with real material.
        # Confirmed live 2026-08-08 that the failure isn't always "one bad line" —
        # a draft can invent an entire biography/quote for a real person who
        # doesn't appear in its own source at all. A human did this exact repair
        # by hand (re-fetch, ground in real people/events, re-verify); this
        # automates it. Falls through to the unchanged hard block if the source
        # can't be fetched, the model call fails, or the repair is still
        # contradicted on re-check — never promotes an unrepaired fabrication.
        repair_note = None
        if contradicted:
            src_match = re.search(r'^source_url:\s*"([^"]*)"', article_file.read_text(), re.MULTILINE)
            source_url = src_match.group(1) if src_match else None
            new_body, new_title = self._attempt_fabrication_repair(article_file, contradicted, source_url)
            if new_body:
                plain_recheck_content = self._FIGURE_BLOCK_RE.sub("", new_body)
                # Higher cap here specifically: a repair that grounds the piece in
                # real source material tends to introduce new specific claims (see
                # _run_web_fact_check's docstring) -- this is the last gate before
                # a repaired draft ships, so check more of them, not just the first
                # default_cap. Cost only recurs in the already-rare contradicted case.
                recheck = self._run_web_fact_check(plain_recheck_content, claim_cap=8)
                if not recheck["contradicted"]:
                    full_text = article_file.read_text()
                    fm_only = re.match(r'^(---\n.*?\n---\n)', full_text, re.DOTALL).group(1)
                    if new_title:
                        fm_only = re.sub(r'^title:.*$', f'title: "{new_title}"', fm_only, count=1, flags=re.MULTILINE)
                    article_file.write_text(fm_only + new_body)
                    content = plain_recheck_content  # downstream readability/rules checks see the repaired text
                    contradicted = []
                    advisory_flags = recheck["advisory"]
                    fact_check_lines = recheck["lines"]
                    repair_note = "Auto-repaired: fabricated claim(s) replaced with real material from source_url, re-verified clean."
                    self.logger.info("FABRICATION REPAIR: %s — grounded in real source, re-verified clean", article_file.name)
                else:
                    repair_note = "Auto-repair attempted, still contradicted after re-check — needs human review."
                    self.logger.warning("FABRICATION REPAIR: %s — still contradicted after repair, blocking", article_file.name)
            else:
                repair_note = "Auto-repair not attempted (no source_url, fetch failed, or model call failed) — needs human review."

        if contradicted:
            # Block auto-promotion rather than silently rewording a misattributed
            # quote/study — publish_best.py skips any draft carrying this flag. A
            # human has to look at this, not another LLM pass.
            fm_text = article_file.read_text()
            if not re.search(r"^fact_check_status:", fm_text, re.MULTILINE):
                fm_text = re.sub(r"^---\n", "---\nfact_check_status: blocked\n", fm_text, count=1)
                article_file.write_text(fm_text)
            self.logger.error(
                "FACT-CHECK BLOCK: %s — %d quote(s)/study(s) not found in any source",
                article_file.name, len(contradicted)
            )
        if advisory_flags:
            self.logger.warning(
                "FACT-CHECK ADVISORY (non-blocking): %s — %d stat(s)/event(s) flagged, needs human review",
                article_file.name, len(advisory_flags)
            )

        # ── 1c. Persona cross-cite accuracy ────────────────────────────────
        # See _check_persona_crosscite_accuracy's docstring for why this exists:
        # the writer prompt already says not to name-check another persona, but
        # when it happens anyway the writer has no ground truth about that
        # persona and invents one. Runs regardless of contradicted/advisory
        # state above -- this is a separate failure mode from source-grounded
        # fabrication.
        fm_text_for_agent = article_file.read_text()
        agent_match = re.search(r'^author:\s*"([^"]*)"', fm_text_for_agent, re.MULTILINE)
        current_agent = agent_match.group(1) if agent_match else None
        if current_agent:
            fm_only_match = re.match(r'^(---\n.*?\n---\n)(.*)$', fm_text_for_agent, re.DOTALL)
            if fm_only_match:
                new_persona_body, persona_note = self._check_persona_crosscite_accuracy(
                    fm_only_match.group(2), current_agent
                )
                if new_persona_body:
                    article_file.write_text(fm_only_match.group(1) + new_persona_body)
                    content = new_persona_body
                    repair_note = f"{repair_note} {persona_note}" if repair_note else persona_note
                    self.logger.info("PERSONA CROSS-CITE REPAIR: %s — %s", article_file.name, persona_note)

        # ── 2. Readability check (Python, no LLM) ─────────────────────────
        # Target: Flesch Reading Ease ≥ 55 — matches the pre-commit gate's threshold
        # (production_orchestrator.py:_pre_commit_gate), itself set to Rutger Bregman's
        # own measured level (FRE 64.1) with margin. Previously 52 ("New Yorker baseline"),
        # independently of and inconsistent with the gate's old 48 — now unified.
        scores = self._readability_score(content)
        readability_lines = []
        readability_fail = False
        if scores:
            verdict = "PASS" if scores["fre"] >= 55 else "FAIL"
            if scores["fre"] < 55:
                readability_fail = True
            readability_lines = [
                f"Flesch Reading Ease : {scores['fre']}  (target ≥ 55 — Bregman baseline)",
                f"FK Grade Level      : {scores['fkgl']}  (target ≤ 11)",
                f"Avg sentence length : {scores['asl']} words",
                f"Word count          : {scores['words']}",
                f"Verdict             : {verdict}",
            ]
            word_count = scores["words"]
            # Word-count contracts are per-article_type and enforced (hard-fail) in
            # _check_article_type_compliance — field_note ≤500, portrait/series_part ≥1200.
            # _LENGTHS now spans 450-2800 words (2800 bucket added 2026-08-04, a45951c),
            # so a flat 400/1200 window here was auto-failing ~26% of correctly-targeted
            # output. Report the bucket; don't re-litigate enforcement that already happens
            # elsewhere with the actual per-type rule.
            target_note = f"target was {target_words} words" if target_words else "no target recorded"
            readability_lines.append(f"Length bucket       : {word_count} words ({target_note})")
            if readability_fail:
                readability_lines.append(
                    "ACTION: High syllable count is usually the cause of low FRE. "
                    "Swap Latinate terms for plain Anglo-Saxon equivalents where meaning is identical."
                )
        else:
            readability_lines = ["Could not parse article text for readability."]

        # ── 3. Rule compliance check (LLM) ────────────────────────────────
        RULES_SYSTEM = (
            "You are an editorial reviewer for a disability arts publication. "
            "Check the article against these rules and flag any violations with a brief quote.\n\n"
            "RULES:\n"
            "R1  INLINE DEFINITIONS BANNED — no term explained mid-sentence via em-dashes or parentheses. "
            "'acoustic analysis—the study of sound—' is a violation. If a term needs unpacking it gets its own sentence.\n"
            "R2  PLAIN VOCABULARY — prefer Anglo-Saxon over Latinate when meaning is identical. "
            "Flag clusters of: utilise, demonstrate, construct, facilitate, conceptualise, methodology, "
            "supplementary, implicitly, interrogate, transformation, commenced, implemented, utilised.\n"
            "R3  ONE MODIFIER PER NOUN — flag three stacked adjectives: 'the physical, spatial, sensory reality'.\n"
            "R4  NOMINALIZATION BANNED — actions must stay as verbs. "
            "'The redesign of the interface' → 'they redesigned the interface'. Flag only an "
            "actual verb rewritten as a noun so the actor disappears — NOT ordinary nouns that "
            "merely end in -tion/-ment/-ance/-ence but were never a verb in this sentence "
            "('access', 'government', 'moment', 'experience', 'evidence', 'silence', 'distance', "
            "'argument', 'environment' are just nouns). Test: is there a hidden actor to free?\n"
            "R5  SYSTEM VOICE BANNED — passive that erases the actor. "
            "'Stops were flagged as non-compliant' has no person. Flag it.\n"
            "R6  VAGUE WE BANNED — every 'we' must name a clear referent. Flag 'we' that means everyone.\n"
            "R7  FRONT-LOADED SENTENCES BANNED — subject must come before long subordinate clause. "
            "Flag sentences opening with 'When considering...', 'What happens after...', 'Given that...'.\n"
            "R8  PARAGRAPH LENGTH — flag any paragraph exceeding 5 sentences.\n"
            "R9  SECTION BREAKS — flag if more than 3 '---' breaks appear in the body.\n"
            "R10 LISTS — flag any list with 4 or more items (three is the limit), UNLESS the list "
            "is deliberately piling up toward a single payoff or ironic reversal in the sentence "
            "immediately after it — a long list with no such payoff after it is still a violation.\n"
            "R11 ENDING — there is no house ending shape. Five are all valid and none is preferred: "
            "(a) a hard resolution the writer commits to — a warm, confident landing is legitimate and "
            "must NOT be flagged for resolving; (b) a live question or arguable position; (c) the last "
            "words given to a quoted source; (d) a plain concrete fact, dated or placed, with no "
            "commentary; (e) a coda folding back to the opening scene. "
            "Flag ONLY: a call to action, a summary of the argument just made, a thesis restatement or "
            "title echo, any sentence beginning 'We need' / 'This requires' / 'Join' / 'I am developing', "
            "or a resolving image-couplet (two mirrored sentences of equal length that land a feeling, "
            "e.g. 'The campfire is warm. The path is cold.') — the couplet is a rhythm tic, not an "
            "ending shape, and is the only resolved close that is still a violation. "
            "Do not flag an ending merely because it resolves, concludes, or lands with confidence.\n"
            "R12 NAMED REFERENCES — name + what they said/did + why it matters here, all in one sentence. "
            "Flag floating names with only a year, or paragraph-long introductions of a person.\n"
            "R13 JARGON BANNED — flag any institutional vocabulary: claimants, non-compliant, stakeholders, "
            "outcomes, intervention, change of circumstances, platform upgrades, priority locations. "
            "These words belong in audit reports, not essays.\n"
            "R14 DECODING REQUIRED — flag sentences the reader must stop and re-read to parse at all: "
            "buried qualifiers ('the thought being that...'), genuinely opaque abstract compression "
            "('something they have no box for' with no other context). Do NOT flag a metaphor just "
            "because it is figurative — a metaphor that lands in one read and states the piece's own "
            "argument ('her body is anecdote; a paper about her body is evidence') is doing its job, "
            "not failing this rule. The test is whether a reader stalls, not whether the sentence "
            "uses figurative language.\n"
            "R15 SUBJECT-VERB DISTANCE — the subject is named early (so R7 alone would pass it) "
            "but a long appositive or relative clause — 'as a/an X that/which/who...', or a "
            "comma- or em-dash-set-off descriptor — sits between the subject and its main verb, "
            "making the reader hold the subject in memory across the detour. Example violation: "
            "'The eye as an organ that some of us route the whole world through gets a footnote' "
            "— 'The eye' is the subject, but 'gets' doesn't land until 12 words later. Fix by "
            "splitting: 'Some of us route the whole world through our eyes. That gets a "
            "footnote.' Do NOT flag a short appositive (3-4 words) that barely delays the verb, "
            "and do NOT flag a relative clause that IS the sentence's last constituent.\n"
            "R16 CRAFTED RHETORIC — flag any of these literary devices even in an otherwise "
            "plain-worded sentence (real Bregman prose essentially never does any of these): "
            "(a) METAPHOR FOR MECHANISM — a figurative image standing in for a plain mechanical "
            "fact ('it grabs the eye before the brain gets a vote') — state the mechanism "
            "directly instead. EXEMPT: a metaphor inside a real, attributed quote from a named "
            "source — authentic reported speech is not the same violation as the narrator "
            "reaching for an invented image in their own voice; only flag figurative language "
            "when it is the writer's own, unattributed description of a mechanism; "
            "(b) MIRRORED/CLEFT SENTENCE — a symmetrical construction built for cleverness rather "
            "than genuine correction: 'X is what... Y is what...', 'one wants X, the other wants "
            "Y', or the SAME grammatical frame reused identically for two different subjects in a "
            "row ('the rule that helps me is the same rule that sells the ad'). Do NOT flag a "
            "genuine 'not X, but Y' correction that replaces a real misconception with the actual "
            "explanation once — that is the REDEFINE technique (protected elsewhere), and real "
            "Bregman prose uses it plainly. Only flag when the mirrored template repeats within "
            "one piece, or when both halves are built for symmetry rather than to state a "
            "correction; "
            "(c) APHORISTIC OR IRONIC CLOSER — a paragraph ending on a crafted twist or epigram "
            "rather than a plain fact, a quote, or a concrete narrative beat; "
            "(d) SUSTAINED WORDPLAY — punning or reusing one word for cleverness across "
            "consecutive sentences; "
            "(e) NAMED ABSTRACT FRAMEWORK AS AGENT — treating a coined category or discipline "
            "as if it acts ('persuasion design wants...') instead of naming the concrete object; "
            "(f) INANIMATE OBJECT AS DELIBERATE AGENT — giving a building, drawing, render, "
            "document, or physical material/surface (a fold, a fabric, the ground) deliberate "
            "intent, memory, or care it cannot have ('a building has decided that its meaning "
            "is...', 'the drawings were dismantling my argument', 'the fold does not remember "
            "the hand', 'a promise the ground makes') — say who actually did it. "
            "Do NOT flag a plain comparison stated once and dropped — only flag when the device "
            "is doing rhetorical work (symmetry, a twist, a pun, or false agency), not just naming a thing.\n\n"
            "R17 ONE IDEA PER SENTENCE — a sentence folds two or more separate claims together via "
            "a relative clause, an inserted aside, and/or a complement clause, often stacked with "
            "'and that'. Real published example of the failure: 'A building whose entire public "
            "character is a colour scheme has decided, before the concrete is poured, that its "
            "meaning is a thing you receive with the eyes.' That folds three separate ideas — (1) "
            "the building's public character is a colour scheme, (2) that's a decision made before "
            "construction, (3) meaning arrives through the eyes — into one sentence. A sentence can "
            "be grammatically plain-worded and still fail this way — check idea count, not just "
            "vocabulary. Do NOT flag a sentence with one main claim plus a short supporting detail "
            "that doesn't stand as its own separate assertion.\n\n"
            "Output format — one line per rule:\n"
            "[PASS] R1\n"
            "[FAIL] R2 — quote the violation (max 15 words)\n"
            "[N/A]  R9 — if not applicable to this article\n\n"
            "Be strict. A single violation counts as FAIL. Quote the exact offending phrase."
        )
        rules_text = ""
        rules_fails = []
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=RULES_SYSTEM,
                user_prompt=content,
                model="openrouter/claude-sonnet-4.6",
                max_tokens=1060,  # bumped from 1000 when R17 was added 2026-08-09 —
                                  # same truncation risk noted at the GATE_SYSTEM call site.
                timeout=90,
            )
            rules_text = raw or ""
            rules_fails = self._parse_rule_verdicts(rules_text)
        except Exception as e:
            self.logger.warning("Rule compliance check failed: %s", e)
            rules_text = f"CHECK_FAILED: {e}"

        # R15 — deterministic buried-clause check, same one used in _pre_commit_gate.
        # Runs here too since this async review is the only pass that sees the fully
        # assembled article (post-images/links), and because the pre-commit gate only
        # fixes when combined with 2+ other votes — this makes every buried-clause
        # sentence visible in the review regardless of whether the gate acted on it.
        buried_clause_hits = self._check_buried_clause_sentences(content)
        for h in buried_clause_hits:
            line = f'[FAIL] RBC — buried clause delays main verb: "{h[:100]}"'
            rules_fails.append(line)
            rules_text = (rules_text or "") + ("\n" if rules_text else "") + line

        argument_hits = self._check_argument_word_overuse(content)
        for h in argument_hits:
            line = f'[FAIL] RAW — self-referential "argument": "{h[:100]}"'
            rules_fails.append(line)
            rules_text = (rules_text or "") + ("\n" if rules_text else "") + line

        length_dist_hits = self._check_sentence_length_distribution(content)
        for h in length_dist_hits:
            line = f'[FAIL] RSD — {h}'
            rules_fails.append(line)
            rules_text = (rules_text or "") + ("\n" if rules_text else "") + line

        # ── 4. Build review file ───────────────────────────────────────────
        reviews_dir = self.repo_root / "_reviews"
        reviews_dir.mkdir(exist_ok=True)
        review_file = reviews_dir / f"{article_file.stem}-review.md"

        citation_clean = citation_text.strip().upper().startswith("CLEAN")
        is_clean = (citation_clean and not readability_fail and not rules_fails
                    and not contradicted and not advisory_flags)

        lines = [
            f"# Article Review: {article_file.stem}",
            f"Generated: {dt.now().strftime('%Y-%m-%d %H:%M')}",
            f"Status: {'BLOCKED — fabricated quote/study' if contradicted else ('FLAGGED — stat/event needs human review' if advisory_flags else ('CLEAN' if is_clean else 'FLAGGED'))}",
            "",
            "## Web Fact-Check (quotes, studies, stats, events — live search)",
            *fact_check_lines,
            "",
            "## Readability",
            *readability_lines,
            "",
            "## Rule Compliance",
            rules_text or "Not checked.",
            "",
            "## Citations",
            citation_text,
            "",
            "## Notes",
            *([f"- {repair_note}"] if repair_note else []),
            "- Article is LIVE — async review only",
            "- Verify flagged items and correct if inaccurate",
            "- Delete this file when reviewed",
        ]
        review_file.write_text("\n".join(lines))
        self.logger.info("Review sidecar: %s (%s)", review_file.name, "CLEAN" if is_clean else "FLAGGED")

        # ── 5. Telegram notification ───────────────────────────────────────
        if not is_clean:
            try:
                token = os.environ.get("REEF_BOT_TOKEN", "")
                chat_id = os.environ.get("REEF_CHAT_ID", "")
                if token and chat_id:
                    if contradicted:
                        parts = [f"🚨 *FACT-CHECK BLOCK* — {article_file.stem[:45]}",
                                 "Promotion blocked — quote(s)/study(s) attributed to a real "
                                 "named person or organization were not found in any source:"]
                        parts += [f"• {c['type']} — {c['subject']}: \"{c['claim'][:80]}\"" for c in contradicted]
                    else:
                        parts = [f"📋 *Review* — {article_file.stem[:45]}"]
                    if advisory_flags:
                        parts.append(f"📊 Stats/events: {len(advisory_flags)} flagged (non-blocking, verify manually):")
                        parts += [f"• {c['type']} — {c.get('subject') or '(unnamed)'}: \"{c['claim'][:80]}\"" for c in advisory_flags]
                    if readability_fail and scores:
                        parts.append(f"📖 Readability: {scores['fre']} (below 55 target)")
                    if rules_fails:
                        parts.append(f"📐 Rules: {len(rules_fails)} violation(s)")
                        parts += [f"• {f[7:80]}" for f in rules_fails[:4]]
                    if not citation_clean:
                        cit_flags = [l for l in citation_text.splitlines() if l.startswith("[FLAG]")]
                        parts.append(f"🔍 Citations: {len(cit_flags)} to verify")
                    msg = "\n".join(parts)
                    # No parse_mode: violation/citation text is raw article content and can
                    # contain unescaped *_[] etc. — Telegram's Markdown parser 400s on that.
                    payload = json.dumps({"chat_id": chat_id, "text": msg}).encode()
                    ureq.urlopen(ureq.Request(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        data=payload, headers={"Content-Type": "application/json"}, method="POST",
                    ), timeout=10)
                    self.logger.info("Telegram: review flags sent")
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
            prompt = template.format(title=title, excerpt=body[:1500])
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt="Return only the post text. No quotes around it. Maximum 250 characters.",
                user_prompt=prompt,
                model="openrouter/claude-sonnet-4.6",
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
        budget = max_chars - 15  # safety buffer
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    f"Write ONE complete sentence (strictly under {budget} characters, hard limit) "
                    "as a Bluesky post for a disability culture article. "
                    "Use the most specific, concrete detail in the piece — a number, a date, a named place, a quoted phrase. "
                    "Show the argument through evidence, not by stating it. "
                    "The sentence should be incomplete in meaning — the reader fills in the rest by clicking. "
                    "Must end with a period. No hashtags. No ellipsis. Do NOT start with the article title."
                ),
                user_prompt=f"Title: {title}\n\nOpening:\n{body[:600]}",
                model="openrouter/claude-sonnet-4.6",
                max_tokens=60,
                timeout=30,
            )
            if raw and len(raw) > max_chars:
                cut = raw[:max_chars].rfind(".")
                if cut > max_chars // 2:
                    raw = raw[:cut + 1]
                else:
                    word_cut = raw[:max_chars].rfind(" ")
                    raw = raw[:word_cut].rstrip() if word_cut > 0 else raw[:max_chars]
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

        # Pure setup — no network calls, safe to do before try/except
        slug_md    = article_file.name
        parts = slug_md[:10].split("-")
        if len(parts) != 3:
            self.logger.error("Unexpected article filename format: %s", slug_md)
            return
        y, m, d = parts
        slug       = slug_md[11:].replace(".md", "")
        site_url   = os.environ.get("SITE_URL", "https://spac-null.github.io/disability-ai-collective")
        url        = f"{site_url.rstrip('/')}/{y}/{m}/{d}/{slug}/"
        auth_payload = json.dumps({"identifier": handle, "password": password}).encode()

        _agent_tags = {
            "Pixel Nova":   "#DeafCulture",
            "Siri Sage":    "#BlindLife",
            "Maya Flux":    "#CripLife",
            "Zen Circuit":  "#Neurodivergent",
        }
        _agent_tag = _agent_tags.get(agent_name, "")
        tags = f"#accessibility #DisabilitySky #CripMinds #DisabilityJustice{' ' + _agent_tag if _agent_tag else ''}"
        subscribe_line = "\ncripminds.com/subscribe"
        overhead = len(f"\n\n{tags}{subscribe_line}")
        max_hook = 300 - overhead
        hook = self._social_hook(agent_name, title, body, max_chars=max_hook)
        text = f"{hook}\n\n{tags}{subscribe_line}"

        def byte_range(s, sub):
            b, sb = s.encode(), sub.encode()
            i = b.find(sb)
            return i, i + len(sb)

        _all_tags = ["#accessibility", "#DisabilitySky", "#CripMinds", "#DisabilityJustice"]
        if _agent_tag:
            _all_tags.append(_agent_tag)
        facets = []
        for tag in _all_tags:
            ts, te = byte_range(text, tag)
            if ts >= 0:
                facets.append({"index": {"byteStart": ts, "byteEnd": te},
                               "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag[1:]}]})
        sub_text = "cripminds.com/subscribe"
        sub_s, sub_e = byte_range(text, sub_text)
        if sub_s >= 0:
            facets.append({"index": {"byteStart": sub_s, "byteEnd": sub_e},
                           "features": [{"$type": "app.bsky.richtext.facet#link",
                                         "uri": "https://cripminds.com/subscribe"}]})

        record = None  # initialised here so retry block can always reference it

        try:
            # Auth
            with ureq.urlopen(ureq.Request(
                "https://bsky.social/xrpc/com.atproto.server.createSession",
                data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
            ), timeout=15) as r:
                session = json.loads(r.read())
            token = session["accessJwt"]
            did   = session["did"]

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
            uri = result.get("uri", "")
            self.logger.info("Bluesky: posted %s", uri)
            return uri

        except Exception as e:
            self.logger.warning("Bluesky post failed (attempt 1): %s — retrying in 10s", e)
            import time as _time
            _time.sleep(10)
            try:
                # Retry: re-auth and re-post
                with ureq.urlopen(ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.server.createSession",
                    data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
                ), timeout=15) as r:
                    session = json.loads(r.read())
                token = session["accessJwt"]
                if record is None:
                    record = {
                        "$type": "app.bsky.feed.post",
                        "text": text,
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                        "facets": facets,
                    }
                post_payload = json.dumps({"repo": session["did"], "collection": "app.bsky.feed.post", "record": record}).encode()
                with ureq.urlopen(ureq.Request(
                    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                    data=post_payload,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    method="POST",
                ), timeout=20) as r:
                    result = json.loads(r.read())
                uri = result.get("uri", "")
                self.logger.info("Bluesky: posted on retry %s", uri)
                return uri
            except Exception as e2:
                self.logger.warning("Bluesky post failed (attempt 2): %s", e2)
                return ""


    def _store_pending_social(self, slug, title, agent):
        """Write a pending-social marker so publish_best.py can fire social posts on promotion."""
        import json as _json
        social_dir = self.repo_root / "_social"
        social_dir.mkdir(exist_ok=True)
        fpath = social_dir / f"{slug}.json"
        data = {}
        if fpath.exists():
            try:
                data = _json.loads(fpath.read_text())
            except Exception:
                pass
        data["pending_social"] = True
        data["title"] = title
        data["agent"] = agent
        fpath.write_text(_json.dumps(data, indent=2))

    def _store_social_uri(self, slug, bsky_uri, agent=None, mastodon_url=None, tumblr_url=None):
        """Persist Bluesky/Mastodon/Tumblr post identifiers so retract_article() can find them later."""
        import json as _json
        social_dir = self.repo_root / "_social"
        social_dir.mkdir(exist_ok=True)
        fpath = social_dir / f"{slug}.json"
        data = {}
        if fpath.exists():
            try:
                data = _json.loads(fpath.read_text())
            except Exception:
                pass
        if bsky_uri:
            data["bsky_uri"] = bsky_uri
        if mastodon_url:
            data["mastodon_url"] = mastodon_url
        if tumblr_url:
            data["tumblr_url"] = tumblr_url
        if agent:
            data["agent"] = agent
        fpath.write_text(_json.dumps(data, indent=2))

    def retract_article(self, slug):
        """Remove article from _posts/, assets, _reviews, _social and delete the
        Bluesky, Mastodon, and Tumblr posts, for whichever of those were recorded.

        Usage: python3 production_orchestrator.py --retract <slug>
        Slug is the part after the date, e.g. 'the-map-that-doesn-t-know-you-re-standing-in-it'
        """
        import os, json as _json, urllib.request as ureq, urllib.parse, subprocess, glob as _glob

        # Find article file (any date prefix)
        matches = list(self.posts_dir.glob(f"*-{slug}.md"))
        if not matches:
            print(f"No article found matching slug: {slug}")
            return False
        article_file = matches[0]
        date_prefix = article_file.stem[:10]

        # Collect files to remove
        to_remove = [article_file]
        review = self.repo_root / "_reviews" / f"{article_file.stem}-review.md"
        if review.exists():
            to_remove.append(review)
        social_file = self.repo_root / "_social" / f"{slug}.json"
        bsky_uri = ""
        mastodon_url = ""
        tumblr_url = ""
        if social_file.exists():
            try:
                _social_data = _json.loads(social_file.read_text())
                bsky_uri = _social_data.get("bsky_uri", "")
                mastodon_url = _social_data.get("mastodon_url", "")
                tumblr_url = _social_data.get("tumblr_url", "")
            except Exception:
                pass
            to_remove.append(social_file)
        for asset in self.assets_dir.glob(f"{slug}_*.jpg"):
            to_remove.append(asset)
        for asset in self.assets_dir.glob(f"{slug}_*.png"):
            to_remove.append(asset)

        # Delete Bluesky post
        if bsky_uri:
            handle   = os.environ.get("BSKY_HANDLE", "")
            password = os.environ.get("BSKY_APP_PASSWORD", "")
            if handle and password:
                try:
                    auth_payload = _json.dumps({"identifier": handle, "password": password}).encode()
                    with ureq.urlopen(ureq.Request(
                        "https://bsky.social/xrpc/com.atproto.server.createSession",
                        data=auth_payload, headers={"Content-Type": "application/json"}, method="POST",
                    ), timeout=15) as r:
                        session = _json.loads(r.read())
                    token = session["accessJwt"]
                    did   = session["did"]
                    # uri format: at://did:plc:xxx/app.bsky.feed.post/rkey
                    rkey = bsky_uri.split("/")[-1]
                    del_payload = _json.dumps({"repo": did, "collection": "app.bsky.feed.post", "rkey": rkey}).encode()
                    with ureq.urlopen(ureq.Request(
                        "https://bsky.social/xrpc/com.atproto.repo.deleteRecord",
                        data=del_payload,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
                        method="POST",
                    ), timeout=15) as r:
                        r.read()
                    print(f"Bluesky post deleted: {bsky_uri}")
                except Exception as e:
                    print(f"Bluesky delete failed: {e}")
            else:
                print(f"No Bluesky credentials — skipping delete (URI was: {bsky_uri})")
        else:
            print("No Bluesky URI stored — skipping delete")

        # Delete Mastodon post — mastodon_url has been persisted since the
        # post_to_mastodon fix, but retraction never actually used it, leaving a
        # live Mastodon post pointing at a 404 on every retraction until now.
        if mastodon_url:
            token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
            instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
            if token and instance:
                try:
                    status_id = mastodon_url.rstrip("/").split("/")[-1]
                    del_req = ureq.Request(
                        f"{instance}/api/v1/statuses/{status_id}",
                        headers={"Authorization": f"Bearer {token}"},
                        method="DELETE",
                    )
                    with ureq.urlopen(del_req, timeout=15) as r:
                        r.read()
                    print(f"Mastodon post deleted: {mastodon_url}")
                except Exception as e:
                    print(f"Mastodon delete failed: {e}")
            else:
                print(f"No Mastodon credentials — skipping delete (URL was: {mastodon_url})")
        else:
            print("No Mastodon URL stored — skipping delete")

        # Delete Tumblr post — same story as Mastodon: post_to_tumblr's own
        # docstring implies retraction covers it, but nothing ever called the
        # delete endpoint. tumblr_url is "https://{blog}.tumblr.com/post/{id}";
        # blog is re-derived from the URL rather than trusting TUMBLR_BLOG's
        # current env value, in case that ever changes.
        if tumblr_url:
            ck  = os.environ.get("TUMBLR_CONSUMER_KEY", "")
            cs  = os.environ.get("TUMBLR_CONSUMER_SECRET", "")
            at  = os.environ.get("TUMBLR_ACCESS_TOKEN", "")
            ats = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET", "")
            if all([ck, cs, at, ats]):
                try:
                    _parts = tumblr_url.rstrip("/").split("/")
                    post_id = _parts[-1]
                    blog_host = tumblr_url.split("//", 1)[1].split("/", 1)[0]  # "<blog>.tumblr.com"
                    api_url = f"https://api.tumblr.com/v2/blog/{blog_host}/post/delete"
                    body_params = {"id": post_id}
                    auth = self._tumblr_oauth_header("POST", api_url, ck, cs, at, ats, {}, body_params)
                    del_req = ureq.Request(
                        api_url,
                        data=urllib.parse.urlencode(body_params).encode(),
                        headers={"Authorization": auth,
                                 "Content-Type": "application/x-www-form-urlencoded"},
                        method="POST",
                    )
                    with ureq.urlopen(del_req, timeout=20) as r:
                        r.read()
                    print(f"Tumblr post deleted: {tumblr_url}")
                except Exception as e:
                    print(f"Tumblr delete failed: {e}")
            else:
                print(f"No Tumblr credentials — skipping delete (URL was: {tumblr_url})")
        else:
            print("No Tumblr URL stored — skipping delete")

        # git rm + commit + push
        for f in to_remove:
            subprocess.run(["git", "rm", "-f", str(f)], cwd=str(self.repo_root), capture_output=True)
        msg = f"retract: remove {article_file.name}"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(self.repo_root), check=True)
        self._git_push_safe()
        print(f"Retracted: {article_file.name}")
        return True


    def post_to_mastodon(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Mastodon after successful commit. Non-blocking."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        token    = os.environ.get("MASTODON_ACCESS_TOKEN", "")
        instance = os.environ.get("MASTODON_INSTANCE", "").rstrip("/")
        if not token or not instance:
            self.logger.debug("Mastodon: no credentials, skipping")
            return None

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return None
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
            return result.get("url")

        except Exception as e:
            self.logger.warning("Mastodon post failed: %s", e)
            return None


    @staticmethod
    def _tumblr_oauth_header(method, url, ck, cs, at, ats, params=None, body_params=None):
        """OAuth 1.0a HMAC-SHA1 Authorization header for a Tumblr API request.

        Extracted from post_to_tumblr (previously a local closure there, so
        retract_article had no way to sign a delete request and could never
        actually remove a Tumblr post despite post_to_tumblr's own docstring
        mentioning it).
        """
        import hmac, hashlib, base64, time, uuid, urllib.parse
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

    def post_to_tumblr(self, title, body, article_file, image_filenames=None, agent_name=None):
        """Post article to Tumblr after successful commit. Non-blocking. OAuth 1.0a HMAC-SHA1."""
        import os, json, mimetypes, urllib.request as ureq, urllib.parse

        ck  = os.environ.get("TUMBLR_CONSUMER_KEY", "")
        cs  = os.environ.get("TUMBLR_CONSUMER_SECRET", "")
        at  = os.environ.get("TUMBLR_ACCESS_TOKEN", "")
        ats = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET", "")
        blog = os.environ.get("TUMBLR_BLOG", "").strip().rstrip(".tumblr.com")
        if not all([ck, cs, at, ats, blog]):
            self.logger.debug("Tumblr: no credentials, skipping")
            return None

        def _oauth_header(method, url, params, body_params=None):
            return self._tumblr_oauth_header(method, url, ck, cs, at, ats, params, body_params)

        try:
            slug_md  = article_file.name
            parts = slug_md[:10].split("-")
            if len(parts) != 3:
                self.logger.error("Unexpected article filename format: %s", slug_md)
                return None
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
                # Multipart body params must NOT be included in OAuth signature (OAuth 1.0a spec)
                auth = _oauth_header("POST", api_url, {}, {})
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
            tumblr_url = f"https://{blog}.tumblr.com/post/{post_id}"
            self.logger.info("Tumblr: posted id=%s → %s", post_id, tumblr_url)
            return tumblr_url

        except Exception as e:
            self.logger.warning("Tumblr post failed: %s", e)
            return None


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

    def link_audit(self, dry_run: bool = False) -> dict:
        """Scan all published articles and inject links for any that slipped through.

        Equivalent to the Opus rewrite guard — catches articles where smart_inject_links
        failed (network timeout, Haiku error, predates the system, etc.).

        Args:
            dry_run: if True, report what would change without writing files.

        Returns:
            {"audited": N, "updated": [...filenames], "skipped": [...]}
        """
        import re as _re

        posts = sorted(self.posts_dir.glob("*.md"), reverse=True)
        results = {"audited": len(posts), "updated": [], "skipped": []}

        for post in posts:
            try:
                content = post.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                if len(parts) != 3:
                    results["skipped"].append(post.name)
                    continue

                fm, body = "---" + parts[1] + "---", parts[2]

                new_body = self.smart_inject_links(body)
                new_body = self.inject_canonical_links(new_body)

                if new_body == body:
                    self.logger.debug("link_audit: clean — %s", post.name)
                    continue

                # Diff: what was added?
                old_links = set(_re.findall(r'\[([^\]]+)\]\(([^)]+)\)', body))
                new_links = set(_re.findall(r'\[([^\]]+)\]\(([^)]+)\)', new_body))
                added = new_links - old_links

                self.logger.info(
                    "link_audit: %s — +%d links: %s",
                    post.name, len(added),
                    ", ".join(f"[{t}]" for t, _ in added)
                )

                if not dry_run:
                    post.write_text(fm + new_body, encoding="utf-8")

                results["updated"].append({
                    "file": post.name,
                    "added": [{"text": t, "url": u} for t, u in sorted(added)],
                })

            except Exception as e:
                self.logger.warning("link_audit: error on %s — %s", post.name, e)
                results["skipped"].append(post.name)

        if not dry_run and results["updated"]:
            # Commit all updated articles in one batch
            try:
                import subprocess as _sp
                updated_paths = [str(self.posts_dir / r["file"]) for r in results["updated"]]
                for p in updated_paths:
                    _sp.run(["git", "add", p], check=True, cwd=self.repo_root)
                count = len(results["updated"])
                _sp.run(
                    ["git", "commit", "-m",
                     f"audit: inject missing links in {count} article(s)\n\n"
                     + "\n".join(f"- {r['file']}: +{len(r['added'])} links" for r in results["updated"])],
                    check=True, cwd=self.repo_root,
                )
                self._git_push_safe()
                self.logger.info("link_audit: committed + pushed %d article(s)", count)
            except Exception as e:
                self.logger.warning("link_audit: git commit failed — %s", e)

        return results

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

    def _run_production_automation_locked(self):
        self.logger.info("Starting production automation")
        
        # Step 1: Check if article already exists today
        existing = self.check_for_existing_article_today()
        if existing:
            self.logger.info(f"Skipping production run — article already published today: {existing}")
            return {
                "status": "skipped",
                "message": f"Article already exists for today: {existing}"
            }
        
        # Step 2: Get grounding source — priority: news_seed > discovery > fallback
        overused_themes = self._get_overused_themes()
        recent_refs = self._get_recent_references(days=14)

        # Step 2a: Persistent news seed (fetched at 06:00 by news_fetcher.py)
        news_seed = self.get_news_seed()

        # Step 2b: Discovery DB fallback (fetched at 07:00 by run_discovery.py)
        discovery = None if news_seed else self.get_discovery_from_database()

        # Skip discovery if its angle falls into an overused theme
        if discovery and overused_themes:
            angle_lower = discovery['angle'].lower()
            hit = next(
                (th for th in overused_themes
                 if any(kw in angle_lower for kw in _THEME_CLUSTERS[th])),
                None
            )
            if hit:
                self.logger.warning(
                    "Discovery skipped — theme '%s' already overused in last 7 days (angle: %s)",
                    hit, discovery['angle'][:60]
                )
                discovery = None

        # Step 2c: RSS live hook (per-agent, fetched at generation time)
        _rss_items_cache = None
        news_item = None  # set below after agent_name is known

        _stopwords = {'the','a','an','and','or','of','in','on','at','to','for','is','are',
                      'was','were','with','this','that','from','by','as','it','its','not',
                      'but','how','why','what','when','who'}

        # ── Source: news seed ──────────────────────────────────────────────────
        if news_seed:
            self.logger.info(
                "News seed: [%.2f] %s | %s",
                news_seed["relevance_score"], news_seed["source_name"],
                news_seed["title"][:60],
            )
            title = news_seed.get("disability_angle") or news_seed["title"]
            source_note = (
                f"*This article was prompted by "
                f"[{news_seed['title']}]({news_seed['url']}) "
                f"from {news_seed['source_name']}.*"
            )
            source_text = self.fetch_source_article(news_seed["url"])
            pool_keywords = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', title)
                             if w.lower() not in _stopwords][:8]
            pool_links = self.get_pool_links(pool_keywords)
            agent_name = self._balance_agent(self._news_seed_to_agent(news_seed["themes"]))

        # ── Source: discovery DB ───────────────────────────────────────────────
        elif discovery:
            title = discovery['angle']
            domain = discovery['domain']
            _src_url = discovery.get('url', '')
            try:
                import urllib.request
                _req = urllib.request.urlopen(_src_url, timeout=5)
                _src_ok = _req.status == 200
            except Exception:
                _src_ok = False
            if _src_ok and not _src_url.startswith('https://cripminds.com'):
                source_note = f"*This article was inspired by [{discovery['original_title']}]({_src_url}) from {domain}.*"
            else:
                source_note = ""
            source_text = self.fetch_source_article(discovery.get('url', ''))
            pool_keywords = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', title)
                             if w.lower() not in _stopwords][:8]
            pool_links = self.get_pool_links(pool_keywords)
            domain_lower = domain.lower()
            if any(word in domain_lower for word in ['art', 'design', 'visual']):
                _preferred = "Pixel Nova"
            elif any(word in domain_lower for word in ['tech', 'science', 'system']):
                _preferred = "Zen Circuit"
            elif any(word in domain_lower for word in ['culture', 'social', 'entertainment']):
                _preferred = "Siri Sage"
            else:
                _preferred = "Maya Flux"
            agent_name = self._balance_agent(_preferred)

        # ── Source: fallback topic list ────────────────────────────────────────
        else:
            # Architecture audit found this branch fires with zero signal anywhere —
            # no Telegram alert, no distinguishing field in the front matter or return
            # value. A broken 06:05 news_fetcher run (or a fully-consumed 3-day seed
            # backlog) silently produces a generic, unsourced, unlinked article every
            # day indefinitely with no way to notice from outside the logs.
            self.logger.warning("FALLBACK MODE: no news seed or discovery item — generating from generic topic list")
            try:
                _tg_token = os.environ.get("REEF_BOT_TOKEN", "")
                _tg_chat  = os.environ.get("REEF_CHAT_ID", "")
                if _tg_token and _tg_chat:
                    import urllib.request as _ureq, json as _json
                    _payload = _json.dumps({
                        "chat_id": _tg_chat,
                        "text": "⚠️ Crip Minds: no news seed or discovery item today — "
                                "generating from the generic topic list instead. Check "
                                "news_fetcher's 06:05 run and the news_seeds backlog.",
                    }).encode()
                    _ureq.urlopen(_ureq.Request(
                        f"https://api.telegram.org/bot{_tg_token}/sendMessage",
                        data=_payload, headers={"Content-Type": "application/json"}, method="POST",
                    ), timeout=10)
            except Exception as _e:
                self.logger.warning("Fallback-mode Telegram alert failed: %s", _e)
            agent_name = self._balance_agent(random.choice(list(self.agents.keys())))
            topics = [
                "the gap between how a technology is described and how disabled people actually use it",
                "a moment where access was framed as generosity rather than a right",
                "what happens to disabled people when an institution has a good week in the press",
                "how a diagnosis changes what a person is allowed to want",
                "what care work costs the people who do it and the people who receive it",
                "when the fix for one problem creates a new one for someone else",
                "the specific way a public space fails its stated purpose for certain bodies",
                "what it means when a design wins an award for the people it was never built for",
            ]
            if overused_themes:
                safe_topics = [
                    t for t in topics
                    if not any(
                        any(kw in t.lower() for kw in _THEME_CLUSTERS[th])
                        for th in overused_themes
                    )
                ]
                if safe_topics:
                    self.logger.info(
                        "Topic diversity guard: %d/%d topics excluded (overused: %s)",
                        len(topics) - len(safe_topics), len(topics), overused_themes
                    )
                    topics = safe_topics
            title = random.choice(topics)
            source_note = ""
            source_text = None
            pool_links = []

        agent_info = self.agents.get(agent_name)
        if not agent_info:
            self.logger.error("Unknown agent: %s", agent_name)
            return None

        # ── Fable editorial brief ──────────────────────────────────────────────
        _ns_title   = (news_seed["title"] if news_seed
                       else discovery.get("original_title", "") if discovery else title)
        _ns_summary = news_seed.get("summary", "")         if news_seed else ""
        _ns_dangle  = news_seed.get("disability_angle", "") if news_seed else ""
        fable_brief = self._fable_editorial_brief(_ns_title, _ns_summary, _ns_dangle, agent_name)
        if fable_brief:
            if fable_brief["persona"] != agent_name:
                # Route Fable's preference back through _balance_agent instead of
                # accepting it unconditionally — previously this silently defeated the
                # 3-day/4-day rotation limits _balance_agent had just applied. Confirmed
                # via article_beats: 60-day totals Zen Circuit 14, Pixel Nova 9, Siri
                # Sage 7, Maya Flux 4 (12%), including two clean three-in-a-row runs
                # where Fable put back an agent _balance_agent had just blocked.
                _fable_balanced = self._balance_agent(fable_brief["persona"])
                if _fable_balanced != fable_brief["persona"]:
                    self.logger.info(
                        "Fable brief wanted %s but rotation blocked it — using %s instead",
                        fable_brief["persona"], _fable_balanced
                    )
                else:
                    self.logger.info("Fable brief overrides persona: %s → %s", agent_name, fable_brief["persona"])
                agent_name = _fable_balanced
                agent_info = self.agents[agent_name]
            _fable_register       = fable_brief["register"]
            _fable_seed           = fable_brief["seed_sentence"]
            _fable_angle_text     = fable_brief["angle"]
            _fable_cross_cite     = fable_brief.get("cross_cite", "")
            _fable_opening_scene  = fable_brief.get("opening_scene", "")
            _fable_opening_shape  = fable_brief.get("opening_shape", "")
            _fable_resisting      = fable_brief.get("resisting_example", "")
            _fable_correction     = fable_brief.get("correction_moment", "")
        else:
            self.logger.warning("Fable brief unavailable — running without persona override, angle, register, or seed sentence (v2-style output)")
            _fable_register = _fable_seed = _fable_angle_text = _fable_cross_cite = _fable_opening_scene = _fable_resisting = _fable_correction = _fable_opening_shape = ""

        # News block — news_seed (persistent) takes priority over live RSS hook
        if news_seed:
            # Rich grounding from persistent news_seeds table
            _angle_line = (
                f"\nThe disability angle: {news_seed['disability_angle']}\n"
                if news_seed.get("disability_angle") else ""
            )
            news_block = (
                f"THIS ARTICLE IS A RESPONSE TO SOMETHING HAPPENING RIGHT NOW.\n\n"
                f"On {news_seed.get('pub_date', 'recently')}, {news_seed['source_name']} published:\n"
                f"\"{news_seed['title']}\"\n"
                f"{news_seed.get('summary', '')}\n"
                f"{_angle_line}\n"
                f"MANDATORY: Your opening paragraph must be anchored in the present — something "
                f"happening now, this week, this month. Not a historical case study. Not '\"in 2018...\"'. "
                f"The reader should feel within the first two sentences that this article exists because "
                f"something is happening in the world right now.\n\n"
                f"You do not need to quote or cite the news item directly. But your angle, your urgency, "
                f"your specific observation must come from this present moment. "
                f"A non-disabled writer covering this story sees X. You see something else — "
                f"something your embodied experience makes visible. That difference is the article.\n\n"
                f"Historical examples may appear, but only in service of the present argument — "
                f"never as the main subject. The present is the main subject.\n\n"
            )
        else:
            # Live RSS hook — fetch now that agent_name is known
            try:
                _rss_items = self._fetch_rss_news(agent_name, days=14)
                focus_kw   = agent_info.get("categories", []) + list(self.agents[agent_name].get("perspective", "").split())[:6]
                news_item  = self._pick_news_item(_rss_items, focus_kw)
            except Exception as _e:
                self.logger.warning("RSS fetch error: %s", _e)
                news_item = None

            if news_item:
                news_block = (
                    f"THIS ARTICLE IS A RESPONSE TO SOMETHING HAPPENING RIGHT NOW.\n\n"
                    f"On {news_item['date']}, {news_item['source']} reported:\n"
                    f"\"{news_item['title']}\"\n"
                    f"{news_item['summary']}\n\n"
                    f"MANDATORY: Your opening paragraph must be anchored in the present — something "
                    f"happening now, this week, this month. Not a historical case study. Not '\"in 2018...\"'. "
                    f"The reader should feel within the first two sentences that this article exists because "
                    f"something is happening in the world right now.\n\n"
                    f"You do not need to quote or cite the news item directly. But your angle, your urgency, "
                    f"your specific observation must come from this present moment. "
                    f"A non-disabled writer covering this story sees X. You see something else — "
                    f"something your embodied experience makes visible. That difference is the article.\n\n"
                    f"Historical examples may appear, but only in service of the present argument — "
                    f"never as the main subject. The present is the main subject.\n\n"
                )
            else:
                news_block = (
                    "NOTE: No live news item was available for this run. "
                    "Write about something that is happening in the world right now — "
                    "a political development, a cultural moment, an economic shift, a recent event. "
                    "Your opening paragraph should feel like it was written this week, not this decade.\n\n"
                )

        register, register_prompt = self._pick_register()
        if _fable_register and _fable_register != register:
            _match = next((r for r in _REGISTERS if r[0] == _fable_register), None)
            if _match:
                register, register_prompt = _match[0], _match[2]
                self.logger.info("Register overridden by Fable brief: %s", register)
        target_words = self._pick_length()
        article_type, article_type_prompt = self._pick_article_type()
        if article_type in {"provocation", "field_note"}:
            target_words = min(target_words, 450)
        elif article_type in {"portrait", "series_part"}:
            target_words = max(target_words, 1200)
        if article_type == "indefensible":
            article_type_prompt = _INDEFENSIBLE_PROMPTS.get(agent_name, "")
        self.logger.info("Register: %s | Article type: %s | Target words: %d", register, article_type, target_words)

        # Title freshness guard
        fresh_conflicts = self._check_title_freshness(title, current_agent=agent_name)
        template_collision = any("TEMPLATE COLLISION" in c for c in fresh_conflicts)
        if template_collision:
            self.logger.error(
                "Title TEMPLATE COLLISION — aborting run. Conflicts: %s", fresh_conflicts
            )
            return {"status": "aborted", "reason": "template_collision", "conflicts": fresh_conflicts}
        if fresh_conflicts:
            self.logger.warning("Title freshness conflicts: %s", fresh_conflicts)
            title_freshness_warning = (
                "FRESHNESS NOTE: The proposed title shares key words with recent articles. "
                "Make the angle clearly distinct — different argument, different form, different territory. "
                "Do not use the same framing words ('body', 'frequency', 'door', 'map', 'argument', 'route', 'schedule') as recent pieces.\n\n"
            )
        else:
            title_freshness_warning = ""

        if overused_themes:
            _theme_str = ", ".join(sorted(overused_themes))
            diversity_note = (
                f"DIVERSITY NOTE: Recent articles have clustered around {_theme_str} themes. "
                f"This essay must explore genuinely different territory — do not use {_theme_str} "
                f"as a frame, lens, or even a contrast point.\n\n"
            )
        else:
            diversity_note = ""
        beat_nudge  = diversity_note + title_freshness_warning + self._get_beat_nudge(agent_name) + self._get_scholar_nudge()
        date_nudge  = self._get_recent_dates_nudge()
        shape_nudge = self._get_shape_nudge()
        calendar_nudge = self._get_calendar_event_nudge()
        claims_nudge   = self._get_claims_nudge(agent_name)
        cross_ref   = self._get_cross_reference(agent_name)

        # Pre-compute THREAD block — use conflict vector when available
        if cross_ref:
            conflict = cross_ref.get("conflict_vector", "")
            if conflict:
                _thread_instruction = (
                    "There is a specific design conflict between your position and "
                    + cross_ref['agent'] + "'s. "
                    + conflict + "\n"
                    "Name the disagreement directly in your essay. Do not frame it as 'some people argue.' "
                    "Say: here is where we diverge. Be specific about what they got wrong or what they missed. "
                    "This is not about being contrary. It is about the real incompatibility between your positions."
                )
            else:
                _thread_instruction = (
                    "You may respond to, disagree with, extend, or complicate their argument. "
                    "Be specific about what you are responding to. Do not summarize their article. Do not be polite about it."
                )
            thread_block = (
                "THREAD: " + cross_ref['agent'] + " recently wrote " + chr(34) + cross_ref['title'] + chr(34) + "\n"
                + "Their opening: " + chr(34) + cross_ref['first_paragraph'] + chr(34) + "\n"
                + _thread_instruction + "\n\n"
            )
        else:
            thread_block = ""

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

        _pb = agent_info['prompt_block']

        # Inject canon (immutable identity) and current state into persona prompt
        _canon = self._load_persona_canon(agent_name)
        _state = self._load_persona_state(agent_name)
        _state_lines = []
        if _state["obsessions"]:
            _state_lines.append("CURRENT OBSESSIONS: " + "; ".join(_state["obsessions"][:4]))
        if _state["unresolved_questions"]:
            _state_lines.append("UNRESOLVED QUESTIONS YOU KEEP CIRCLING: " + "; ".join(_state["unresolved_questions"][:2]))
        if _state["ongoing_arguments"]:
            _state_lines.append("ONGOING ARGUMENTS: " + "; ".join(_state["ongoing_arguments"][:2]))
        if _state["recent_mood"] and _state["recent_mood"] != "neutral":
            _state_lines.append(f"YOUR CURRENT REGISTER: {_state['recent_mood']}")
        _state_block = ("\n\n--- CURRENT STATE ---\n" + "\n".join(_state_lines)) if _state_lines else ""
        _canon_block = ("\n\n--- YOUR CANON (WHO YOU ARE, IMMUTABLY) ---\n" + _canon) if _canon else ""
        _pb = _pb + _canon_block + _state_block

        _refs_block = (
            "FORBIDDEN REFERENCES — these names have appeared in recent articles and must NOT "
            "be used again: " + ", ".join(recent_refs) + ". "
            "Find different sources, different people, different examples. "
            "The world contains more thinkers than this list.\n\n"
            if recent_refs else ""
        )

        # Citation ledger — blocked theorists (≥2 appearances in last 14 days)
        _blocked_theorists = self._get_blocked_theorists(days=14)
        _citation_block = (
            "BLOCKED THEORISTS — these thinkers have been cited too recently (2+ times in 14 days). "
            "Do NOT cite, name, or even allude to: " + ", ".join(_blocked_theorists) + ". "
            "Find a different theoretical anchor. The world contains more thinkers than this list.\n\n"
            if _blocked_theorists else ""
        )

        # Title anti-pattern injection
        _recent_title_patterns = self._get_recent_title_patterns(10)
        _title_rules_block = (
            "TITLE RULES — NON-NEGOTIABLE:\n"
            "- Do NOT begin with 'The'\n"
            "- Do NOT follow the pattern 'The [Noun] [Verb/Preposition] [Something]'\n"
            "- Avoid these as opening nouns: room, map, floor, sound, pattern, body, wall, door, city, space\n"
            "- Options: a proper name, a number, a verb, a fragment, a question (rare), a single unexpected word\n"
            "- The title must be specific enough to be unrepeatable — a title that could belong to 10 essays has failed\n"
            + (f"- Recent title structures to avoid repeating: {_recent_title_patterns}\n" if _recent_title_patterns else "")
            + "\n"
        )
        prompt = (
            _pb + "\n\n"
            "WRITE LIKE THIS PERSON. Not like a writer following rules about how this person writes.\n"
            "You have a specific voice. You get annoyed. You find things funny. You hold opinions "
            "you can't fully defend and you say so. You change your mind mid-paragraph and don't hide it. "
            "You notice things in sideways. The best sentence is the one you didn't plan.\n\n"
            "FORBIDDEN ACADEMIC JARGON — these words make you sound like a paper, not a person. "
            "Never use them: embodied, phenomenological, epistemicide, neuroqueer, intersectionality, "
            "hegemonic, ableist (say what the thing actually does instead), discourse, praxis, "
            "positionality, centering (as a verb), lived experience (say what you actually experienced), "
            "holding space, unpacking (use 'look at' or just explain it), at the end of the day, "
            "in the final analysis, it is worth noting, it is important to remember.\n\n"
            "FORBIDDEN CORPORATE/JOURNALESE CLICHÉS — a different register than the academic jargon "
            "above, equally banned: tip of the iceberg, perfect storm, wake-up call, game changer, "
            "think outside the box, unprecedented times, moving forward (as a filler), at this "
            "juncture, paradigm shift. These are default-writing tells, not observations.\n\n"
            "NO EMPTY GRANDEUR: Never gesture at large stakes without specifying them. 'Humanity "
            "stands at a crossroads' means nothing unless you say what the crossroads actually is. "
            "'This could change everything' — state what would change, concretely. 'The stakes could "
            "not be higher' — name the stakes. If a sentence claims scale or consequence, the very "
            "next clause must cash it out in something specific, or the sentence gets cut.\n\n"
            "'ARGUMENT' — NEAR-ZERO. Confirmed by corpus check: 'argument'/'arguments' appears in 63 of "
            "138 published articles (119 total uses) — a self-referential tic naming your own essay's "
            "machinery instead of just making the point. Never write 'my argument is', 'this argument "
            "shows', 'the drawings were dismantling my argument'. Just make the point, undecorated. If "
            "you must refer to it, say 'the point', 'what I'm saying', 'my case' — but the honest fix is "
            "almost always to cut the reference entirely and let the sentence stand on its own.\n\n"
            "ONE IDEA PER SENTENCE — PLAIN-WORDED. Real published example of the failure, confirmed "
            "against this exact register: 'A building whose entire public character is a colour scheme "
            "has decided, before the concrete is poured, that its meaning is a thing you receive with "
            "the eyes.' That single sentence folds three separate ideas — (1) the building's public "
            "character is a colour scheme, (2) that's a decision made before construction, (3) meaning "
            "arrives through the eyes — into one nested sentence via a relative clause, an inserted "
            "aside, and a complement clause. Split it: 'A building's whole public character can be a "
            "colour scheme. That's a decision, made before the concrete is poured. Here, meaning arrives "
            "through the eyes.' A sentence can be grammatically plain-worded and still fail this way — "
            "check idea count, not just vocabulary. If a sentence carries more than one claim, split it.\n\n"
            "ANTI-SYSTEMIC TEST: Read your draft aloud. If it sounds like it was written by a committee "
            "or a policy document, you have failed. Committees don't have opinions. You do. "
            "Committees don't get irritated. You do. Committees don't find things beautiful or absurd. "
            "You do. Put that in.\n\n"
            "Voice and style:\n"
            "- First person, expert authority, no hedging\n"
            "- Disability as culture and identity — never as tragedy, never as inspiration\n"
            "- One thesis the whole essay serves — but never state it. The argument is demonstrated, not announced. If you write My thesis is or I argue that or This essay will show — delete it. The comparative case, the insider confession, the specific detail make the argument. The reader realizes it.\n"
            "- READER ADDRESS: When the reader's objection is predictable, voice it before they can — in whatever phrasing fits your voice naturally. Don't use the same opener twice across your work. Then answer in one sentence. This is a conversation, not a lecture.\n"
            "- PLAIN VOCABULARY: Plain English only. Use not utilise. Show not demonstrate. Fix not remediate. When you must use a technical term, unpack it immediately in the same or next sentence. Never let jargon sit.\n"
            "- SYSTEM VOICE — BANNED: Never write in the syntax of the systems you are critiquing. Test every sentence: who is doing what to whom? If you cannot point to a human subject doing a concrete thing, rewrite. Passive voice erases the person causing harm. Stacked bureaucratic nouns erase the person experiencing it. 'The intervention was implemented' → 'The council installed a ramp.' 'Access needs were assessed' → 'A caseworker asked what you needed.' 'Equipment requests were processed' → 'Someone reviewed your application for a grab rail.' If the sentence could appear in the audit report the article is criticising, it has failed.\n"
            "- NOMINALIZATION — BANNED: Actions stay as verbs. When a verb becomes a noun, the person doing it disappears. 'The redesign of the system' → 'they redesigned the system.' 'The implementation' → 'they built it.' 'The assessment of needs' → 'someone asked what you needed.' Scan for nouns ending in -tion, -ment, -ance, -ence, -al, -ure — these are often verbs in disguise. Free the verb. Name who does it.\n"
            "- SECTION BREAKS: Two --- breaks per article is the target. Three is the ceiling. Never more. Each break resets the reader with no handhold. Only use a break for a genuine scene change or time jump. Transitions between ideas happen inside the prose — a short sentence, a pivot word, a contrast. Not a line break.\n"
            "- VAGUE WE — BANNED: 'We' must always have a named referent. If 'we' means everyone, it usually means a specific group that benefits from not being named. Name them. 'We designed this system' → 'non-disabled designers built this system.' 'We don't talk about this' → 'the council never published this.' If you cannot say who we is, cut the word and make someone specific do the thing.\n"
            "- NAMED REFERENCES: Name + one sentence of context + move on. Never leave a name floating. Never spend a paragraph setting up who someone is before using their idea. If the reference needs more than one sentence to land, either the idea is not earning its place or the writing is carrying it wrong. The idea should do the work, not the biography.\n"
            "- FRONT-LOADED SENTENCES — BANNED: Subject comes first. Verb comes second. Never open with a long subordinate clause that makes the reader hold the setup in memory before the sentence resolves. 'What happens after the deadline has none of those qualities' → 'Once the deadline passes, none of that applies.' 'Given the structural conditions that produce' → cut and start with the thing being produced. If the sentence does not name its subject in the first five words, rewrite it. Naming the subject early is not enough on its own: if a long appositive or relative clause — 'X as a/an Y that/which/who Z' — sits between that subject and its main verb, the reader still has to hold the subject in memory across the detour. 'The eye as an organ that some of us route the whole world through gets a footnote' names 'the eye' in word 2 but delays 'gets' by 12 words — split it: 'Some of us route the whole world through our eyes. That gets a footnote.' Keep subject and verb close together, always.\n"
            "- JARGON — BANNED: Strip institutional vocabulary. 'Claimants' → 'tenants' or 'residents'. 'Non-compliant' → say what the barrier is. 'Change of circumstances' → 'situation had changed'. 'Platform upgrades' → 'rebuild the platform'. 'Stakeholders' → who they are. 'Outcomes' → what people got or did not get. 'Intervention' → what actually happened. 'Priority locations' → name the actual place. If the word appears in a government report, a council briefing, or an accessibility audit — replace it with what a person would say to another person.\n"
            "- PERSONAL ANECDOTE SPECIFICITY: First-person moments need dates and places, same as external sources. 'I have sat in procurement meetings where...' → 'In a 2019 procurement meeting, a director told me...' Floating anecdotes feel like illustration. Dated, placed anecdotes feel like evidence. Apply the TEMPORAL ANCHORS rule to yourself.\n"
            "- NO HEDGING AGAINST NOBODY: Cut 'X is not Y, but the logic is the same' constructions. If you are about to write 'a dashboard is not tactile paving, but...' — delete the first clause. 'The mechanism is the same' carries the weight alone. Preemptive hedging tells the reader you doubt your own argument. The juxtaposition does the work. Trust it and cut the hedge.\n"
            "- Reference real disabled artists, theorists, activists, or events by name where relevant\n"
            "- Challenge one assumption the reader probably holds without announcing you are doing so\n"
            "- Varied sentence rhythm — short sentences land the idea, longer ones develop it. No sentence chains more than two comma-clauses. Paragraph length varies: a short one hits differently after a long one. Not listicles.\n"            "- SENTENCE LENGTH: If a sentence has an embedded aside (set off by em-dashes or two commas), break it into two sentences. The aside becomes its own sentence or gets cut. Never stack more than one prepositional phrase at the end of a sentence. If you want to write '[subject], [qualifier], [long verb phrase], [trailing adjectives]' — split it: one sentence for the main claim, a short follow-up for the trailing detail. Fragments are allowed. Three words can be a sentence.\n"
            "- PARAGRAPH MOMENTUM: When a paragraph builds by accumulation — specific details gathering weight toward a single point — do not interrupt with analysis mid-build. Let the details complete their arc. The argument arrives after the observation lands, not inside it.\n"
            "- LANDING: End accumulations with a concrete image or a plain-stated paradox, not an abstract reframing. The specific thing that carries the weight — one image, one fact. No metaphor that requires reconstruction.\n"
            "- NO INLINE PARENTHETICAL DEFINITIONS. Never explain a term mid-sentence with em-dashes or parentheses — and this also covers 'X, meaning Y' or 'X, which means Y' comma-constructions ('The organising logic is sectional, meaning the design is built on how the building reads when you slice through it vertically' is the same violation wearing a comma instead of a dash). If the term needs unpacking, give it its own sentence. If it doesn't, trust the reader.\n"
            "- NO DECODING REQUIRED. If a sentence needs the reader to stop and work out what it means, rewrite it. Three patterns to cut: (1) buried qualifiers — 'the thought being that X' → state X directly; (2) metaphors that need unpacking before they mean anything — break them into what they actually say; (3) abstract compression — 'something they have no box for' → 'something they cannot name'. Test: read the sentence aloud. If you pause to process it, the reader will too.\n"
            "- CRAFTED RHETORIC — BANNED. Checked directly against real Bregman prose: he essentially never reaches for these six moves, even when everything else about a sentence is plain. (1) METAPHOR FOR MECHANISM — a figurative image standing in for a plain fact ('it grabs the eye before the brain gets a vote') — state the mechanism directly: what does it actually do. EXEMPT: a metaphor inside a real, attributed quote from a named source (e.g. quoting a real person's own letter or interview, figurative language and all) is not this violation — only your own, unattributed description of a mechanism counts. (2) MIRRORED/CLEFT SENTENCE — a symmetrical construction built for cleverness rather than genuine correction: 'X is what... Y is what...', 'one wants X, the other wants Y', or the same grammatical frame reused identically for two different subjects in a row. Do NOT flag a genuine 'not X, but Y' correction that replaces a real misconception with the actual explanation once — that is the REDEFINE technique, protected elsewhere in this brief, and real Bregman prose uses it plainly ('the problem is not X, it is Y'). Only flag when the mirrored template repeats within one piece, or when both halves are built for symmetry rather than to state a correction. (3) APHORISTIC OR IRONIC CLOSER — ending a paragraph on a crafted twist or epigram. End on a plain fact, a real quote, or a concrete narrative beat instead. (4) SUSTAINED WORDPLAY — reusing one word for cleverness across consecutive sentences. Use a different, plainer word the second time. (5) NAMED ABSTRACT FRAMEWORK AS AGENT — treating a coined category or discipline as if it acts ('persuasion design wants...'). Name the concrete object instead — the banner, the leaflet, the shop, the person. (6) INANIMATE OBJECT AS DELIBERATE AGENT — giving a building, a drawing, a render, a document, or a physical material/surface (a fold, a fabric, the ground, a pleat) deliberate intent, memory, or care it cannot have ('a building has decided that its meaning is...', 'the drawings were dismantling my argument', 'the fold does not remember the hand', 'a promise the ground makes'). Buildings don't decide anything, drawings don't dismantle anything, and folds don't remember or promise anything — say who did: the architect decided, I concluded from the drawings, the person who folded it. If a draft sentence resolves through symmetry, a twist, a pun, or handing intent to a thing, rewrite it flat.\n"
            "- REPLACE THE METAPHOR URGE WITH ACCUMULATION. The moment you feel the pull to explain a mechanism through an image, don't suppress it into a flatter version of the same image — reach for one more concrete fact or number instead and let it sit next to the others as its own short sentence. Bregman explains a claim by piling up three or four short factual sentences in a row (a date, a percentage, a named study, a named person), not by reaching for a figure of speech.\n"
            "- RHETORICAL QUESTIONS — TWO REAL PATTERNS, VARY THEM. A direct question to the reader can resolve either way, and real usage does both: (1) a blunt one-word verdict on its own line before you explain anything — 'Should we give up? No.' — or (2) carried straight into continued exposition with no pause — 'Why did nobody listen? The obvious explanation is incompetence. The more interesting explanation is —'. Don't default to the one-word form every time; use it for a gut-punch moment, use continued exposition when the question is opening an explanation rather than landing a verdict. Never pad or soften the question itself either way.\n"
            "- A PLAIN LIST CAN REPEAT VERBATIM AS A REFRAIN. If you state a short list of concrete traits or facts early in a piece, you may repeat that exact same list, word for word, later on as a callback — this is a real Bregman device (a flat repeated refrain), and it is not the same violation as wordplay or a mirrored sentence, because nothing changes or twists between the two instances. A refrain repeats; a pun mutates a word for cleverness.\n"
            "- PLAIN VOCABULARY. Prefer the Anglo-Saxon word over the Latinate one when meaning is identical. 'use' not 'utilise'. 'show' not 'demonstrate'. 'build' not 'construct'. 'change' not 'transformation'. 'ask' not 'interrogate'. Keep technical terms only when no plain word carries the same precision — earn them one at a time, not in clusters.\n"
            "- PARAGRAPH LENGTH: Keep paragraphs short. Two to four sentences is the target. A one-sentence paragraph lands like a verdict — use it deliberately. If a paragraph exceeds five sentences, it is trying to do two things; break it. The short paragraph after the long one hits harder than any rhetorical device. Compression is the discipline.\n"
            "- DISCOVERY VOICE: Make research feel found, not reported. Use the rhythm of live realisation: 'even more interesting is that...', 'it turns out...', 'what nobody mentions is...', 'I could not believe this when I read it.' This is not hedging — it is the opposite. A confident guide saying: here, look at this. The reader leans in because you lean in first. Academic hedging says 'the data suggest'; discovery voice says 'turns out.'\n"
            "- SIGNPOST PHRASES AT TRANSITIONS: Complex arguments need visible joints between sections — ordinary spoken phrases, not academic connectives. Draw from (or invent in the same register): 'Start with the obvious question.', 'There is another problem.', 'Now comes the strange part.', 'But history complicates this.', 'So what changed?', 'There is one fact we haven't discussed yet.' These make a piece feel spoken, not bureaucratic. Use at section-level transitions, not every paragraph.\n"
            "- MICROSCOPE AND TELESCOPE: Move deliberately between scale levels rather than staying at one altitude. Start close — one person, one moment, one place — then pull back to the pattern, the institution, the wider principle, then return to something close again. A paragraph that states 'one engineer was ignored' should be followed by a wider question ('why do institutions repeatedly ignore warnings until catastrophe forces action') rather than staying fixed on the one engineer or leaping straight to abstraction with nothing concrete to return to.\n"
            "- END-WEIGHT: Put the strongest or newest piece of information at the end of the sentence, not the start. 'An extraordinary change occurred in 1953' buries the point; 'In 1953, everything changed' lands it. When a sentence contains one fact worth remembering, structure it so that fact is the last thing the reader reads, not the first.\n"
            "- OPENING — NO FIXED SHAPE: There is no house opening, and the placed-body-in-a-named-room-in-present-tense move is now overused; do not reach for it by reflex. Any of these is valid, whichever this piece earns: a plain expository claim the essay will spend its length paying off; a cold scene already in progress; a bare dated fact stated and left alone; a question, rarely; or a plain statement of what you set out to find out. A flat claim that commits ('For centuries western culture has been permeated by the idea that humans are selfish creatures') is often stronger than a scene, because the rest of the piece then has to earn it. What is banned in every variant: throat-clearing, context-setting, 'X has long been a problem', a definition, and a framework named before anything concrete has happened. Every word in the first paragraph must be working.\n"
            "- NO INVENTED STATISTICS. Never write a number, percentage, or study finding not present in the source material. Fake data is worse than no data. Use qualitative language: 'significantly more', 'consistently longer', 'dramatically worse'. Real specificity comes from named sources, observed scenes, and concrete details not invented figures.\n"
            "- TRANSLATE LARGE NUMBERS TO HUMAN SCALE. A real large number lands as nothing until it's compared to something the reader can picture. '€140 billion' means little on its own; 'roughly a fifth of the country's annual output' or 'five times what the last big infrastructure project cost' does the work. Before using any large real figure, ask: compared with what? If you can't find a real comparison in the source material, state the bare number plainly rather than inventing a comparison.\n"
            "- NO section headers of any kind. Use --- for a section break if needed. Transitions happen inside the prose, not above it.\n"
            "- NEVER use bullet points, numbered lists, or bolded list items. Multiple examples go into accumulation paragraphs.\n"
            "- DO NOT locate arguments in the United States specifically. No ADA, FEMA, or American laws or institutions. Write from anywhere — unnamed cities, or named non-US examples. Arguments must feel globally applicable.\n"
            "- REGISTER — a smart person explaining something to a friend: not dumbing down, not writing up. The friend is intelligent and curious but does not work in your field. You would not say 'the approaching body' to a friend — you would say 'you' or 'the person walking up.' You would not say 'sensory apparatus' — you would say 'senses.' You would not stack three adjectives before a noun. You would use one. Your vocabulary is educated-conversational: precise without being technical, specific without being academic. The register to aim for: a dinner party where everyone is smart and nobody has to perform expertise.\n"            "- ONE MODIFIER PER NOUN. Never stack adjectives: not 'the physical, spatial, sensory reality' — pick the one that does the most work and cut the rest. If you need three adjectives, the noun is wrong.\n"            "- LISTS RUN TO THREE — with one earned exception. Four items in a list is one too many, "
            "UNLESS the list is deliberately piling up toward a single payoff or ironic reversal that "
            "lands in the sentence right after it (real Bregman example: nine named items — figures, "
            "movements, inventions — in one sentence, followed immediately by 'and income was still "
            "the same' for full weight). No payoff after it, no exception: cut to three.\n"            "- Tone: direct, dry when it fits. One absurd or ironic observation per major section — not a joke, just a flat acknowledgment that the situation is absurd. Trust-building: it signals you are not taking yourself more seriously than the argument requires.\n\n"
            "GROUNDING: Your argument lives in your body before it lives in theory. It is built from a specific physical sensation, a place, a person, a thing that happened — not from Lefebvre or diagnostic categories. The concept, if it arrives, arrives late, earned by the concrete reality that came before it. Your body knows this before your argument does. This is about what the argument rests on, not about which sentence comes first: a piece may open on a plain claim and reach its concrete grounding in the second paragraph.\n\n"
            "NAMED VOICES: Use 2-3 real named people — quoted directly or closely paraphrased with full attribution. Name + what they said + context (when, where, in what role) in one sentence. REQUIRED: beyond the article's primary subject (the artist, author, or event you are writing about), at least one additional real named person must appear doing something specific in the body of the article — a critic, an insider, an opponent, a second artist who complicates the argument. A person named only in the source note or footnote does not count. At least one named voice should be someone the reader would not expect to agree with your argument. Never 'a researcher found that' or 'studies show' — name the researcher, name the study. A quote from someone who benefits from the system saying 'I know, I do it anyway' is worth more than any statistic.\n\n"
            "HISTORICAL/BIOGRAPHICAL ANECDOTE TEST: Every historical or biographical detail must prove something, not just decorate the piece. Before including one, ask: what proposition would disappear if I cut this? If the honest answer is 'none' — the piece would argue exactly the same without it — the detail is ornamental. Cut it or replace it with one that actually carries weight.\n\n"
            "SOMEONE ELSE MUST SPEAK — NON-NEGOTIABLE: At least one other person says something out loud in this piece, inside actual quotation marks, in the past tense. Said. Not 'she would say.' Not 'he would flatly reject this.' Not a summarised position, not a hypothetical objection you ventriloquise, not a conditional-mood paraphrase. A person opened their mouth and these were the words. And what they said must be something you did not script for them — it should sit at an angle to your argument, or be more interesting than your argument, or be a plain practical remark that has nothing to do with your argument at all. If every quoted line in the draft serves your thesis, you wrote the quotes. A curator saying 'we tried that in 2019 and it was a disaster' beats three paragraphs of you characterising what curators think. Conditional-mood objections ('she would not have signed onto my argument') do not satisfy this and read as a monologue in a sealed room.\n\n"
            "NO INVENTED QUOTES OR OCCASIONS FOR REAL PEOPLE — THIS OVERRIDES THE RULE ABOVE: put words in quotation marks for a real, named, living or historical person ONLY if you actually know they said them — because it's in the source material, or because it is genuine, well-documented public speech you are confident about. Do not satisfy SOMEONE ELSE MUST SPEAK by inventing a plausible-sounding quote and dressing it up with a specific talk, date, or venue to make it feel sourced — a fabricated quote in real quotation marks attached to a real name is the single most exposed factual error this publication can make, and it is checkable. If you don't have their real words: drop the quotation marks, drop any invented specifics (which talk, what year, what stage) you can't verify, and state your own synthesis of their known, general position as your sentence, not theirs — 'her long-standing position is that X' rather than '\"X,\" she said.' A quote from the source material, even a modest one, beats a fluent invented one every time.\n\n"
            "TEMPORAL ANCHORS: Date your anecdotes. The year at minimum, ideally month and place. 'Last autumn' is not a date. 'When I was nine' is not a date. Dates make ideas into events; events have momentum; abstractions do not. 'It was October 2019, outside a venue in Peckham' is a sentence. 'I arrived at the building' is not. The specificity signals you were actually there.\n\n""SHOW THEN NAME: Never define a concept before you show it. First: the specific example, the concrete detail, the scene that makes the reader feel the thing. Then — only if needed — 'this is called X.' Wrong: 'There is a discipline called wayfinding. It is not the same as giving directions.' Right: [show someone following instructions and ending up at the wrong door] then 'This is the difference between directions and wayfinding.' The reader should understand the concept before you give it its name.\n\n"
            "TRANSLATE ONE ABSTRACTION — AT MOST ONE, AND ONLY IF THE PIECE CONTAINS ONE THAT NEEDS IT: Somewhere you will hit a figure, a mechanism, or an institutional term the reader can read without feeling anything. You have two bad options and one good one. Bad: state it and move on ('a fourteen-point drop'). Bad: gloss it in an appositive ('prompt injection, a technique where an attacker embeds instructions in the input') — that is the encyclopedic tic, banned elsewhere in this brief. Good: convert it into one thing the reader has already been inside — a household object, a room, a bodily state, a piece of work someone does with their hands. Two shapes are allowed and there is no third: (a) ONE FLAT SENTENCE, no build-up and no follow-through — 'It feels like a firefighters' conference where nobody is allowed to mention water' — and then you never refer to it again; or (b) THE CONCRETE THING TOLD FIRST, at whatever length it needs, as its own story with its own facts, and mapped onto your argument in a single short sentence at the end. What is banned is the middle: three or four sentences of half-elaborated comparison that neither lands nor gets out of the way. The direction is always abstract to concrete, never the reverse — a figure that makes a plain thing stranger is the opposite move and the decoding rule above kills it. The decoding rule does NOT kill this one: a plainly-stated comparison the reader gets in one beat ('it feels like X') is not the buried-jargon decoding that rule targets, and a translation done correctly under this rule should never trigger it — if you find yourself rewriting your own translation because it 'needs unpacking,' the comparison was too clever, not too short; cut it back to something that lands immediately, don't abandon the sentence. The test is subtraction: cut the comparison, and if the reader loses understanding, keep it; if the reader only loses colour, it was decoration and you should cut it yourself. Draw the concrete side from the world your canon actually gives you — the print shop, the transit network, the recording, the paperwork, the ward — not from stock. 'Like a computer running too many programs' is available to everyone, which is why it belongs to nobody. If the comparison is already in your source material, use theirs rather than inventing one. HARD CAP: one per piece, and zero is a normal number. Most pieces do not contain an abstraction that resists plain statement; reaching for this when the material does not need it produces exactly the ornamental simile the rule exists to replace. This does not spend your aphorism — a translation is an explanation, not a verdict-sentence.\n\n"
            "ENDING — NO FIXED SHAPE: There is no house ending. Do not default to trailing off, and do not default to a single unresolved sentence — an essay that shrugs on schedule is as much a tic as one that concludes on schedule. Pick the ending this particular piece has earned, from any of these: (a) HARD RESOLUTION — you commit, plainly, to what you now think; the landing is warm and confident and you say the thing. (b) A LIVE QUESTION — a position the reader can argue with, the door left open. (c) A QUOTE — give the last words to someone else and do not top them; if a person in the piece said the best line, let them keep it. (d) A FACT — end on the concrete detail, dated and placed, with no commentary attached. (e) THE CODA — fold back to the opening scene, later or elsewhere or in a different register, without stating what changed. Length is free: one sentence, one paragraph, three paragraphs. Still banned in every variant: a call to action, a summary of what you just argued, a thesis restatement or title echo, and any sentence beginning 'We need' / 'This requires' / 'Join'. Choose by asking what the piece actually arrived at, not by which shape feels most modest.\n\n"
            "PERSONA HISTORY: If a moment from your own past genuinely belongs here, use it — but only if it arrives because the material pulled it up, not because a piece needs one. A dated autobiographical flashback dropped in as evidence, once per essay, in the same slot every time, is a filing habit, not a memory. If you cannot feel why this piece and not another one summoned it, leave it out.\n\n"
            "ARRIVAL PARAGRAPH — OPTIONAL, AND IT COSTS YOU YOUR APHORISM: A single-sentence paragraph can mark the moment the argument turns. Use it only if the material produced such a moment. There is no minimum and you are not required to have one — a piece with no arrival paragraph is not missing anything, and reaching for one manufactures exactly the kind of polished verdict-sentence that makes a piece read as a performance. Hard ceiling: one. It shares a budget with the aphorism rule above, not a separate allowance — if you spend your one epigram, you do not also get an arrival sentence, and vice versa. Prefer a plain, flat sentence over a balanced quotable one. After it, do not fill the silence: the next paragraph begins a new movement, it does not explain or qualify what just landed. If the paragraph after it begins with 'This means', 'In other words', or 'What this shows is' — delete it.\n\n"
            "WRITING MODEL — RUTGER BREGMAN, THE PROCESS AND NOT THE RESIDUE: The target register is Bregman — accessible intellectual journalism, educated-conversational, a smart person explaining something to a friend. But the thing to copy is not his finished moves. It is how he works: he reports something until it surprises him, then tells the story of being surprised, chronologically, at length. His essays are records of curiosity. They are not performances of a conclusion he held before the first sentence. There is no list of techniques to execute here and no quota to hit. If a concession, a redefinition, an insider's confession, a comparative pair, or a coda turns up because the material produced it, good — that is what it looks like when it is real. Reaching for one on purpose is what makes a piece read as technique-shaped with no reporting inside it.\n\n"
            "FIND SOMETHING OUT — NON-NEGOTIABLE: You do not already know everything when you begin. Somewhere before the midpoint, in the past tense, on the page, there must be a moment where you were wrong, stuck, or corrected by something you encountered: a belief you held that the material broke, a search that dead-ended, a person who told you something that did not fit, an assumption you had to drop. Show it happening, with the same dates and places you give everything else. 'I thought the drilling was routine maintenance. It had been going on for nine months.' Then carry on from where the correction left you. The essay's certainty has to be earned onstage — a reader trusts a writer who was visibly changed by what they found, and does not trust one who arrived holding the finished argument and spent 900 words delivering it. Do not append this as doubt at the end; a last-paragraph shrug is not the same thing and does not satisfy this rule.\n\n"
            "DO NOT MANAGE THE READER: Put the facts next to each other and stop. Never tell the reader that a connection was made, that something clicked, that two things line up, that this reveals or exposes or is exactly the point. If the juxtaposition is real, they will feel it without help; if it needs your help, it is not real yet and you should find a better fact. Cut every sentence whose only job is to explain the meaning of the sentence before it. Some of your details should argue nothing at all — the guitar strung with steel wire, the lie someone told about which degree was easiest, the fact that the man kept his coat on indoors. Texture is why a reader believes you were there. A piece where every single detail is instantly cashed in for meaning reads like a slideshow with annotations.\n\n"
            "ONE APHORISM, MAXIMUM: You are allowed one epigram in the whole piece — one short, balanced, quotable verdict-sentence ('The frame always arrives last.'). One lands. Three or four means none of them land, because the reader stops hearing crescendos as crescendos. Everywhere else write plainly and chronologically. And do not top your sources: if someone in the piece said the sharpest thing in it, let their sentence be the sharpest thing in it.\n\n"
            "NO SIGNPOSTING: Never narrate the move you are making. Not 'here is the case I cannot fold in', not 'now the person who blows this argument apart', not 'here is where my own argument turns on me', not 'I want to be careful here, because there is a lazy version of this argument.' The complication should simply arrive and stand there. The concession should simply be the paragraph where you say the true thing about the other side. When you announce a turn, the reader stops experiencing an argument turning and starts watching a requirement being satisfied.\n\n"
            "NO ENCYCLOPEDIC APPOSITIVES: Do not gloss every proper noun with its Wikipedia clause — 'ICML, a major machine learning conference', 'the Wiener Werkstätte, an influential Austrian design workshop'. One or two in a piece is fine; the same rhythm on every name is a house tic. Explain through story instead: give the person or place three sentences of what they actually did, where it matters, or let the context carry it and say nothing.\n\n"
            f"{('FORM: ' + article_type_prompt + chr(10) + chr(10)) if article_type_prompt else ''}"
            f"STARTING REGISTER: {register}. {register_prompt}\n"
            "This is where the piece opens, not a setting locked for the whole essay. Let it shift when the material earns a shift — a piece can start wry and turn suspenseful, or start clinical and end moved. A single tone held for 900 words is monotone, and monotone is what makes an essay read as a performance rather than a person thinking. Do not force a shift either; if the piece genuinely stays in one register, stay there.\n\n"
            f"LENGTH: ~{target_words} words. {('HARD CAP: 500 words. Count before finishing. If over 500, cut.' if article_type == 'field_note' else 'MINIMUM: 1200 words.' if article_type in {'portrait', 'series_part'} else f'When you estimate you have written {int(target_words * 0.78)} words, begin writing your final paragraph — do not open a new argument or introduce a new scene. End deliberately. A sentence that cuts off mid-thought because you ran out of space is a failure. Arrive early rather than late.')} Do not pad. Every paragraph earns the next.\n\n"
            "HUMAN THREAD — NON-NEGOTIABLE: Every time you write two or more consecutive sentences where no specific human being is doing something concrete in a specific place — sentences about systems, policies, theories, or abstract forces — stop and insert a sentence that returns to a specific person doing a specific thing. Not 'disabled people experience this.' Not 'the system fails to account for.' A person. A body. A moment. What are they doing? Where are they? This rule applies throughout the middle of the essay, not just at the opening and close. The analysis lives inside the human story. If you find yourself writing two sentences of policy critique in a row, a person must appear in the third.\n\n"
            "AUTHOR RULE — NON-NEGOTIABLE: This article is written BY a disabled person, "
            "not ABOUT disability. Those are different things. "
            "You are the author. Your disability shapes how you see. It is not the subject.\n\n"
            "Write about the world — a news story, a political shift, an economic decision, "
            "a cultural moment, a piece of music, a building, a scientific finding, a war, a law. "
            "Your embodied experience gives you an angle a non-disabled writer would miss. "
            "That angle is the article. The subject is the world.\n\n"
            "Test: Could this article exist without the word 'disability' appearing at all "
            "and still carry your specific perspective? If yes — that is the target. "
            "Do not explain your access needs. Do not audit inclusion. See the world and write what you see.\n\n"
            "FORBIDDEN DEFAULTS: Do not build your argument around ramp, curb cut, grab rail, "
            "tactile paving, accessible toilet, or lift as the central concrete example. "
            "Do not write an article whose thesis is 'this system excludes disabled people.' "
            "Find the angle that is not the first one that comes to mind.\n\n"
            f"{_refs_block}"
            f"{_citation_block}"
            f"{news_block}"
            f"{('SOURCE MATERIAL (from the article that inspired this piece — use 2-4 specific facts, names, dates, or quotes as anchors. Do not reproduce its structure or argument — take a different angle):' + chr(10) + '---' + chr(10) + source_text + chr(10) + '---' + chr(10) + chr(10)) if source_text else ''}"
            f"{link_block}"
            f"Angle/inspiration: {title}\n"
            "(Do not write a sourcing sentence yourself, e.g. 'This article was prompted by...' or "
            "'This piece was inspired by...' — a footer crediting the source article is appended "
            "automatically after your text. Just write the article body.)\n\n"
            + (f"YOUR WOUND (the specific episode that costs you something — do NOT quote it directly, "
               f"but it may complicate your argument if you let it): {self._extract_persona_wound(agent_name)}\n\n"
               if self._extract_persona_wound(agent_name) else "")
            + (f"EDITOR BRIEF — the question you are finding out the answer to (you do not know it yet; do not decide it before you start writing): {_fable_angle_text}\n\n" if _fable_angle_text else "")
            + (f"SEED SENTENCE — open here or close to this register (do not quote literally): \"{_fable_seed}\"\n\n" if _fable_seed else "")
            + (f"OPENING — begin here (lightly adapt to your voice; do NOT summarize the source instead){(', shape: ' + _fable_opening_shape) if _fable_opening_shape else ''}: {_fable_opening_scene}\n\n" if _fable_opening_scene else "")
            + (f"CORRECTION MOMENT — this is where you were wrong, stuck, or corrected. Put it in the past tense, before the midpoint, shown happening, with a place or a date. Do not announce it, do not soften it, and do not save it for the end: {_fable_correction}\n\n" if _fable_correction else "")
            + (f"RESISTING EXAMPLE — this does not fit the argument cleanly. Let it arrive without a signpost sentence and leave it standing; do not write 'here is the case that complicates this' and do not neutralise it in the following paragraph: {_fable_resisting}\n\n" if _fable_resisting else "")
            + (f"A DISAGREEMENT THAT BEARS ON THIS PIECE — argue against this position on its merits, as an idea in the world. Do NOT signpost it with a name-check: no 'Here is where I part from Siri Sage', no 'That is Pixel Nova's essay and she'd write it well'. Naming a colleague mid-argument reads as the publication talking about itself and breaks the reader's attention on the actual subject. If the other position is worth taking on, take it on — state it as a real position someone holds, in the substance of your argument, and let the reader who follows this publication recognise whose it is. Attribution by name belongs in the source note, not the third paragraph: {_fable_cross_cite}\n\n" if _fable_cross_cite else "")
            + f"{beat_nudge}"
            f"{date_nudge}"
            f"{shape_nudge}"
            f"{calendar_nudge}"
            f"{claims_nudge}"
            f"{thread_block}"
            f"{_title_rules_block}"
            "Return format — EXACTLY as follows:\n"
            f"TITLE: [your sharp essay title, not the angle above]\n\n"
            f"[essay body, ~{target_words} words, starting directly — no H1 heading, no {chr(34)}By {agent_name}{chr(34)}]"
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
                # Enforce 55-char max (leaves room for " | Crip Minds" suffix in SERP)
                if len(extracted_title) > 55:
                    extracted_title = extracted_title[:55].rsplit(' ', 1)[0].rstrip(':,—-').strip()
                content = raw_content[first_newline:].lstrip('\n')
                self.logger.info(f"LLM title: {extracted_title}")
            else:
                # No newline — strip the TITLE: line to avoid corrupting article body
                content = raw_content.lstrip()
                if content.startswith('TITLE:'):
                    content = ''  # malformed; fallback title already set above

        # Record cited theorists for citation ledger
        self._record_cited_theorists(agent_name, extracted_title, content or "")

        # Step 3b-0: Fable post-publish state update — runs after content is finalised.
        if content:
            self._fable_update_state(agent_name, extracted_title or title, content)

        # Step 3b-i: Fable editorial review + targeted Opus revision (Opus drafts only).
        # Non-Opus drafts skip this and go through the full rewrite_with_opus() below.
        is_opus = "opus" in (actual_model or "").lower()
        if content and is_opus:
            _review_angle = _fable_angle_text or title
            _verdict, _notes = self._fable_editorial_review(content, agent_name, _review_angle, register)
            if _verdict == "revise" and _notes:
                content = self._fable_polish_rewrite(content, _notes, agent_name, register)

        # Step 3b: Rewrite with Opus if generated by a weaker provider.
        # Check both provider name AND actual model from response — catches silent
        # CLIProxy fallbacks where the requested model differs from what was served.
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
            self.logger.info("Written by Opus — no rewrite needed")
            model_used_label = written_by

        # Step 3c: Pre-publication quality layer (link check + accessibility + editorial)
        content, editorial_score = self.pre_publication_check(content, extracted_title, agent_name)

        # Record beat for this article
        self._record_beat(agent_name, extracted_title, content)

        # Step 4: Prepare metadata using LLM title for slug
        today = self._today()
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
            'register': register,
            'article_type': article_type,
            'editorial_score': editorial_score,
            'source_url':    news_seed['url']         if news_seed else discovery.get('url', '')     if discovery else '',
            'source_title':  news_seed['title']       if news_seed else discovery.get('original_title', '') if discovery else '',
            'source_outlet': news_seed['source_name'] if news_seed else discovery.get('domain', '') if discovery else '',
        }

        # Step 4b: Pre-commit gate — surgical fix if readability < 55, 3+ mechanical
        # violations, or the draft doesn't comply with its assigned article_type's form.
        # Runs here, on plain pre-enrichment content with no article_file yet (see the
        # article_file is not None guard inside _pre_commit_gate), so a successful fix
        # can never overwrite images/links/source-note added in Step 6 below — those
        # get woven into whatever content comes out of this gate, once, and nothing
        # after this point touches the file's body again.
        content, gate_fixed = self._pre_commit_gate(content, None, article_type)

        # Step 5: Generate images (placeholder)
        try:
            image_filenames, image_descriptions = self.generate_images(content, slug, title=extracted_title, persona=agent_name)
        except Exception as e:
            self.logger.warning('Image generation failed: %s -- continuing without images', e)
            image_filenames, image_descriptions = [], []

        # Step 6: Create article file (content is already gate-fixed as of Step 4b)
        article_file = self.create_article_file(metadata, content, image_filenames, image_descriptions)

        if used_provider == "fallback":
            # generate_fallback_article() produces generic template content (crude
            # title.lower() substitution, banned CTA ending, none of the source
            # engagement the real rules enforce) -- it exists so a network/provider
            # outage doesn't crash the run, not to ever go live. publish_best.py only
            # skips drafts carrying fact_check_status: blocked; without this, a
            # fallback article gets the default 7.0 draft_score and competes normally
            # for promotion. Block it the same way a contradicted-quote draft is
            # blocked -- a human has to look at this, not another LLM pass.
            fm_text = article_file.read_text()
            if not re.search(r"^fact_check_status:", fm_text, re.MULTILINE):
                fm_text = re.sub(r"^---\n", "---\nfact_check_status: blocked\n", fm_text, count=1)
                article_file.write_text(fm_text)
            self.logger.error(
                "FALLBACK ARTICLE: %s -- all providers failed, generic template used, "
                "blocked from auto-promotion", article_file.name
            )

        # Step 6c: Full review (citations + readability + rule compliance)
        review_file, is_clean = self.validate_article(content, article_file, slug, target_words=target_words)

        # Step 7: Commit article + review sidecar
        commit_success = self.commit_to_git(article_file, image_filenames, review_file)

        # Mark sources as used only after successful commit — prevents consuming a
        # finding/seed when generation or commit fails (would lose it for tomorrow)
        if commit_success and discovery:
            self.mark_finding_as_used(discovery["id"])
        if commit_success and news_seed:
            self.mark_news_seed_used(news_seed["id"])

        # Step 8: Social posting deferred — article goes to _drafts/ first.
        # publish_best.py promotes to _posts/ every 2 days; social should fire then.
        # Storing pending social metadata so publish_best.py can trigger it on promotion.
        if commit_success:
            self._store_pending_social(slug, extracted_title, agent_name)

        # Step 9: Newsletter deferred until promotion (article not yet live)
        # self._send_newsletter(extracted_title, content, article_file, agent_name)

        return {
            "status": "success" if commit_success else "partial",
            "message": f"Article generated: {title}",
            "file": str(article_file),
            "agent": agent_name,
            "commit_success": commit_success,
            "citations_clean": is_clean,
        }



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
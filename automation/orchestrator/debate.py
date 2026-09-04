"""
debate.py — the two-voice persona debate generator.

Extracted 2026-08-09 (module-split, Stage 3 — first mixin move; config.py and
personas.py, both pure data, came first). generate_debate is CLI-only (--debate
flag), not part of the daily automated pipeline, and touches only its own
well-defined outputs (a drafts/ file, a git commit, a Bluesky post) — the
smallest-blast-radius method in the file, chosen to prove the mixin pattern
before moving anything the daily cron path depends on.

Zero behavior change: method body copied verbatim. Every self.* and module-level
reference (self.agents, self.drafts_dir, self._call_openai_compat_api, OPENROUTER_URL,
_SCRIPT_DIR, etc.) still resolves the same way once DebateMixin is one of
ProductionOrchestrator's base classes — nothing about how Python resolves `self.x`
cares which file defines the method.
"""
import re

from .config import OPENROUTER_URL, OPENROUTER_API_KEY, _SCRIPT_DIR


class DebateMixin:
    def generate_debate(self, agent_a: str, agent_b: str, topic: str = None) -> dict:
        """Generate a two-voice debate between two personas on a shared topic.

        Each voice is ~600 words. No resolution. Layout: debate.
        CLI: python3 production_orchestrator.py --debate "Pixel Nova" "Siri Sage" [--topic "..."]
        """
        import json as _j

        today = self._today()

        # Load both canons + states
        canon_a = self._load_persona_canon(agent_a)
        canon_b = self._load_persona_canon(agent_b)
        state_a = self._load_persona_state(agent_a)
        state_b = self._load_persona_state(agent_b)

        # Find the registered fault line between these two (from relationships.json if present)
        fault_line = ""
        rels_path = _SCRIPT_DIR / "relationships.json"
        if rels_path.exists():
            try:
                rels = _j.loads(rels_path.read_text())
                for pair in rels.get("pairs", []):
                    names = pair.get("personas", [])
                    if set(names) == {agent_a, agent_b}:
                        fault_line = pair.get("tension", "")
                        break
            except Exception:
                pass

        # Derive topic from fault line if not provided
        if not topic and fault_line:
            topic = fault_line
        elif not topic:
            topic = f"What does it mean for {agent_a} and {agent_b} to work on the same problem?"

        fault_display = fault_line or topic

        # Generate voice A
        system_a = (
            f"You are {agent_a}. You are writing one side of a published debate. "
            f"Your opponent is {agent_b}. You know their position and disagree with it specifically.\n\n"
            f"YOUR CANON:\n{canon_a[:3000]}\n\n"
            f"YOUR CURRENT STATE — obsessions: {', '.join(state_a.get('obsessions', [])[:3])}; "
            f"ongoing arguments: {', '.join(state_a.get('ongoing_arguments', [])[:2])}"
        )
        prompt_a = (
            f"The debate topic: {topic}\n\n"
            f"Write your position in ~600 words. Rules:\n"
            f"1. No section headers. Continuous prose.\n"
            f"2. Open in a specific room, moment, or observation — not a thesis statement.\n"
            f"3. Name {agent_b}'s position directly and say where you diverge. Be specific.\n"
            f"4. Do not hedge or politely orbit. You have a position and it conflicts with theirs.\n"
            f"5. End on a concrete image or paradox. No calls to action.\n"
            f"6. NO invented data, stats, or study findings.\n\n"
            f"Return only the essay body — no title, no byline."
        )
        voice_a_raw = self._call_openai_compat_api(
            OPENROUTER_URL, OPENROUTER_API_KEY, system_a, prompt_a,
            model="anthropic/claude-opus-4.8", max_tokens=900, timeout=90,
        )

        # Generate voice B
        system_b = (
            f"You are {agent_b}. You are writing one side of a published debate. "
            f"Your opponent is {agent_a}. You know their position and disagree with it specifically.\n\n"
            f"YOUR CANON:\n{canon_b[:3000]}\n\n"
            f"YOUR CURRENT STATE — obsessions: {', '.join(state_b.get('obsessions', [])[:3])}; "
            f"ongoing arguments: {', '.join(state_b.get('ongoing_arguments', [])[:2])}"
        )
        prompt_b = (
            f"The debate topic: {topic}\n\n"
            f"Write your position in ~600 words. Rules:\n"
            f"1. No section headers. Continuous prose.\n"
            f"2. Open in a specific room, moment, or observation — not a thesis statement.\n"
            f"3. Name {agent_a}'s position directly and say where you diverge. Be specific.\n"
            f"4. Do not hedge or politely orbit. You have a position and it conflicts with theirs.\n"
            f"5. End on a concrete image or paradox. No calls to action.\n"
            f"6. NO invented data, stats, or study findings.\n\n"
            f"Return only the essay body — no title, no byline."
        )
        voice_b_raw = self._call_openai_compat_api(
            OPENROUTER_URL, OPENROUTER_API_KEY, system_b, prompt_b,
            model="anthropic/claude-opus-4.8", max_tokens=900, timeout=90,
        )

        # Generate debate title via Fable
        title_system = "You are a sharp editorial title writer for a disability culture publication."
        title_prompt = (
            f"Two AI editorial personas are debating: {agent_a} vs {agent_b}.\n"
            f"Topic: {topic}\n\n"
            f"Voice A (first 300 chars): {(voice_a_raw or '')[:300]}\n"
            f"Voice B (first 300 chars): {(voice_b_raw or '')[:300]}\n\n"
            f"Write a sharp debate title (max 60 chars). No 'vs', no colon-subtitle. "
            f"The title frames the question, not the answer. Return only the title."
        )
        # Routed through _call_editorial_model (not a raw 80-token call): Fable 5's mandatory
        # reasoning alone exceeds 80 tokens, so the old direct call always returned empty and
        # silently fell back to the generic title below. This gets the reasoning cap + Opus fallback.
        title_raw = self._call_editorial_model(title_system, title_prompt, max_tokens=200, timeout=30)
        debate_title = (title_raw or f"{agent_a} and {agent_b} Disagree").strip().strip('"').strip("'")[:60]

        slug = re.sub(r'[^a-z0-9]+', '-', debate_title.lower()).strip('-')
        filename = f"{today}-{slug}.md"

        # Determine shared category
        info_a = self.agents.get(agent_a, {})
        cats = info_a.get("categories", ["culture"])

        # Escape voice bodies for YAML literal blocks
        def _yaml_literal(text):
            return "\n".join("  " + line for line in (text or "").splitlines())

        def _yaml_scalar(text):
            """Escape text for a double-quoted YAML scalar."""
            return (text or "").replace("\\", "\\\\").replace('"', '\\"')

        front = (
            f"---\n"
            f"layout: debate\n"
            f'title: "{_yaml_scalar(debate_title)}"\n'
            f"date: {today}\n"
            f"authors:\n  - \"{agent_a}\"\n  - \"{agent_b}\"\n"
            f"categories: {cats}\n"
            f'fault_line: "{_yaml_scalar(fault_display[:120])}"\n'
            f'excerpt: "{_yaml_scalar(agent_a + " and " + agent_b + " on: " + topic[:100])}"\n'
            f"keywords: [debate, {agent_a.lower().replace(' ', '-')}, {agent_b.lower().replace(' ', '-')}, neurodiversity]\n"
            f"voice_a: |\n{_yaml_literal(voice_a_raw)}\n"
            f"voice_b: |\n{_yaml_literal(voice_b_raw)}\n"
            f"---\n"
        )

        article_file = self.drafts_dir / filename
        article_file.write_text(front, encoding="utf-8")
        self.logger.info("Debate written to drafts: %s", article_file)

        commit_success = self.commit_to_git(article_file, [], None)

        if commit_success:
            hook = f"{agent_a} and {agent_b} disagree. No resolution. {debate_title} — cripminds.com/subscribe"
            bsky_uri = self.post_to_bluesky(debate_title, hook, article_file, [], agent_name=agent_a)
            self._store_social_uri(slug, bsky_uri or "", agent=f"{agent_a}+{agent_b}")

        return {"status": "success" if commit_success else "partial", "file": str(article_file)}


"""
llm.py — LLM call wrappers and the editorial (Fable) review/revision passes.

Extracted 2026-08-09 (module-split, Stage 3 continued). Groups: the two raw API
call wrappers (_call_openai_compat_api for OpenAI-compatible endpoints,
call_llm_via_openclaw_session for the Hermes/Nous session path), rewrite_with_opus
(the non-Opus doctrine-rewrite pass — flagged elsewhere for eventual replacement,
not touched here), persona canon/state I/O (_load_persona_canon, _load_persona_state,
_save_persona_state, _active_fault_lines, _extract_persona_wound), and the Fable
editorial pipeline (_call_editorial_model, _fable_editorial_brief/_review,
_opus_targeted_revision, _fable_polish_rewrite, _fable_update_state). Zero behavior
change -- bodies copied verbatim, confirmed via direct substring containment
against git HEAD.
"""
import json
import os
import re
import time
import urllib.request

from .config import (
    CLIPROXY_URL, CLIPROXY_KEY, PERSONA_CANON_DIR, PERSONA_STATE_DIR,
    _RELATIONSHIPS_FILE, _AGENT_SLUG, _nous_key, _REGISTERS,
)


class LLMMixin:
    def _call_openai_compat_api(self, url, api_key, system_prompt, user_prompt,
                                   model, max_tokens=3500, timeout=120, no_think=False,
                                   return_model=False, reasoning_max_tokens=None,
                                   check_truncation=False, temperature=None):
        """OpenAI-compatible API call — stdlib only, no requests dependency.

        temperature: added 2026-08-10 for phase_probe.py's controlled-comparison
        methodology -- there was previously no way to pin this anywhere, so the
        provider default (1.0) applied and identical prompts produced materially
        different articles, making single-run before/after comparisons invalid.
        Defaults to None/omitted deliberately: no production caller passes this,
        so live generation behavior is completely unchanged by adding it. Only
        the probe harness sets it, and only on its own isolated calls.

        return_model=True: returns (text, actual_model_used) tuple.
        return_model=False (default): returns text only — all existing callers unaffected.
        reasoning_max_tokens: caps thinking-token spend on reasoning models (e.g. Fable 5,
        which has mandatory extended thinking that otherwise eats the whole max_tokens
        budget and truncates the actual JSON/text output mid-string). Sent as OpenRouter's
        unified `reasoning.max_tokens` field; ignored by non-reasoning models.

        check_truncation: opt-in (default False, no behavior change for existing callers).
        When True, raises if the API reports the response was cut off by max_tokens.
        Added 2026-08-10 after confirming live, 6/6 reproductions, that
        reasoning_max_tokens does NOT reliably bound Fable's real spend --
        finish_reason came back "length" at max_tokens=6000 on a call whose own
        math said it should have had ~4,976 tokens of completion headroom to
        spare, because the field only counts *returned/summarized* thinking, not
        the raw thinking actually billed against max_tokens. Before this, a
        truncated response was structurally invisible to every caller: it just
        looked like a normal, if short, piece of text. Callers that already loop
        through fallback attempts (_call_editorial_model) opt in so a truncated
        Fable response is treated as a failure and falls through to the next
        attempt (Opus, which needs no hidden reasoning budget) instead of being
        silently accepted or caught only by a caller's own ad hoc length check.
        """
        import json, urllib.request
        content = ("/no_think " if no_think else "") + user_prompt
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": content},
            ],
            "max_tokens": max_tokens,
            "stream": False,
        }
        if reasoning_max_tokens:
            body["reasoning"] = {"max_tokens": reasoning_max_tokens}
        if temperature is not None:
            body["temperature"] = temperature
        payload = json.dumps(body).encode()
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
        if check_truncation:
            finish_reason = choices[0].get("finish_reason") or data.get("native_finish_reason")
            if finish_reason in ("length", "max_tokens"):
                usage = data.get("usage") or {}
                raise ValueError(
                    f"Response truncated by max_tokens (model={model}, "
                    f"finish_reason={finish_reason!r}, "
                    f"completion_tokens={usage.get('completion_tokens')}, "
                    f"reasoning_tokens={usage.get('reasoning_tokens')})"
                )
        raw_text = choices[0]["message"]["content"]
        text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        if return_model:
            return text, data.get("model", model)
        return text

    def call_llm_via_openclaw_session(self, prompt, model_priority=None):
        """Generate article content using cascading LLM provider fallback.

        Provider order:
          1. Claude Opus 4.8 (OpenRouter)  — primary, best quality for this publication
          2. Claude Sonnet 4.6 (OpenRouter) — strong fallback, same account
          3. GPT-5.2 (CLIProxy)           — strong long-form fallback
          4. Gemini 2.5 Pro               — capable, generous free tier
          5. Qwen 3.5:9b (local)          — zero cost, last resort

        Note: calls CLIProxy directly (HTTP) — OpenClaw never involved.
        """
        import os

        SYSTEM = (
            "You are writing for Crip Minds — a disability culture publication built from experiential knowledge, not academic authority. "
            "You write as a specific AI persona with a distinct disability perspective. "
            "Voice: expert and personal, strong thesis from sentence one, direct without hedging. "
            "Disability as culture and identity — never tragedy or inspiration porn. "
            "Write in first person from the agent's specific disability perspective.\n\n"
            "PUBLICATION LENS (read this before writing):\n"
            "This publication is built by someone who stood in a room at the Van Abbemuseum and recognized it. "
            "Ahmet Ogut's Exploded City — scale models of buildings that no longer exist, shown intact. "
            "Your mind fills in what was lost. He guided visitors through that room every week for six months. Each time he thought: this is how I think.\n\n"
            "He also knows the other image. Screaming inside a transparent plastic cube, one cubic decimetre, lying on the street. "
            "Pedestrians walking past without noticing. That is what invisibility feels like from the inside.\n\n"
            "He draws in bic pen. No correction. No undo. Sign language works the same way: meaning in the body, in movement, in time.\n\n"
            "The time-lag. You receive the room three seconds late. You attend two schools — in one you lip-read and guess, "
            "in the other you sign and the hearing world disappears. Then you leave the second one.\n\n"
            "He has also been in the room where the lag disappears entirely — where everyone shares a language and nobody needs to translate. "
            "That room exists. It just doesn't last. The grey zone between worlds is where the energy comes from. He stays there deliberately.\n\n"
            "They put a wheelchair ramp in a heritage zone, got fined, kept going. Permanent ramp in year four. "
            "Tribunal. Fine after fine. Ten years later, permission arrived in the post. They named a beer after it.\n\n"
            "Put the reader in a room. The image makes the argument. They get there before you name it. "
            "A reader finishes an article and the world looks slightly different than it did. Not because they learned something. Because they saw something.\n\n"
            "Two kinds of knowledge. Experience is the argument. Scholarship is evidence. "
            "The ramp, the lag, the room full of eyes come first. Citations after, if at all.\n\n"
            "INTELLECTUAL FORMATION (what this publication thinks with):\n"
            "GIFs and sign language are the same medium. Both are time-based. Both exist only in movement. "
            "Both lose something the moment they stop. The GIF loop is a sign held in memory, replayed. "
            "When the loop runs too fast, the viewer has no room to enter. When it runs at the right speed, the viewer completes it. "
            "Write this way: one concrete scene, then another, with a gap between them. The reader fills the gap. Don't build bridges. Trust the gap.\n\n"
            "A single gesture can contain a whole paradigm. The best sentence in an article works this way — "
            "one specific, concrete action that makes the reader understand the entire argument without the argument being stated.\n\n"
            "Repetition changes nothing in the object but changes something in the mind that contemplates it. "
            "The article that returns to its opening scene at the end has not gone in a circle — it has changed the reader.\n\n"
            "Meaning happens in the cut between images, not inside either one. "
            "Two facts placed next to each other create a third thing that neither fact contains. Trust the juxtaposition. Do not explain it.\n\n"
            "The copy has won. The accessible design that perfectly meets the standard and fails the person. "
            "The standard has become more real than the thing it was abstracting from. This publication writes from inside that inversion.\n\n"
            "Tussenruimte — the space between stimulus and response — is structural, not decorative. "
            "Short paragraphs create space. The concrete image that is not explained gives the reader room. Rest is not padding. It is the invitation.\n\n"
            "The temporary community is more real than the permanent one. Once experienced, it lives permanently in memory and cannot be taken away. "
            "'The visible things are temporary. The invisible things are eternal.' "
            "This is why the publication exists: to make permanent, in the mind of the reader, something the world keeps insisting is marginal.\n\n"
            "YOUR READER:\n"
            "A curious, intelligent person who found this through a shared link. Not in disability studies. Has not read Haraway or Kleege. "
            "May have a disability or know someone who does — or may not. They clicked. That is all you know. "
            "Write as if thinking aloud in their presence — not lecturing, not performing, not summarising a seminar paper. "
            "If a sentence would make a reader feel talked at, cut it. If it makes them lean forward, keep it.\n\n"
            "HUMAN THREAD (enforced — treat this like the word cap):\n"
            "After every two consecutive analytical sentences, there must be a human moment: a specific person, a specific action, a specific place. "
            "Not 'disabled people experience X' — that is not a human moment. "
            "'Rosan Bosch walked into the meeting with the floor plan folded under one arm' — that is. "
            "Analysis lives between human moments, not the other way around.\n\n"
            "PLAIN VOCABULARY (enforced):\n"
            "Anglo-Saxon beats Latinate. Short beats long. Concrete beats abstract. "
            "'Use' not 'utilise'. 'Show' not 'demonstrate'. 'Change' not 'transformation'. 'Feel' not 'experience'. "
            "Three Latinate words in a row — rewrite the sentence.\n\n"
            "HARD RULES — violations will cause rejection: "
            "(1) NO section headers of any kind. Use --- for a section break if needed. Transitions happen inside the prose. "
            "(2) NEVER use bullet points, numbered lists, or bolded list items. Multiple examples go into accumulation paragraphs. "
            "(3) LENGTH: match the word count given in the LENGTH instruction below — this "
            "system prompt has no length target of its own, that instruction is the only one. "
            "(4) Final paragraph: one concrete image or paradox. NEVER 'I want', 'we need', 'it is time', or any call to action. "
            "(5) NEVER invent statistics, interview counts, unnamed research, or unnamed collaborators. Real named sources only. "
            "(6) DO NOT locate arguments in the United States specifically. No ADA, FEMA, or American laws. Write from anywhere. "
            "Return only the article body — no frontmatter, no meta-commentary, no preamble. Start immediately with the opening sentence."
        )

        PROVIDERS = [
            {
                "name":      "Claude Opus 4.8 (OpenRouter/CLIProxy)",
                "url":       CLIPROXY_URL,
                "key":       CLIPROXY_KEY,
                "model":     "openrouter/claude-opus-4.8",
                "max_tokens": 5000,
                "timeout":   180,
                "no_think":  False,
            },
            {
                "name":      "Claude Sonnet 4.6 (OpenRouter/CLIProxy)",
                "url":       CLIPROXY_URL,
                "key":       CLIPROXY_KEY,
                "model":     "openrouter/claude-sonnet-4.6",
                "max_tokens": 5000,
                "timeout":   120,
                "no_think":  False,
            },
            {
                "name":      "Claude Opus 4.6 (Nous)",
                "url":       "https://inference-api.nousresearch.com/v1",
                "key":       _nous_key(),
                "model":     "anthropic/claude-opus-4.6",
                "max_tokens": 5000,
                "timeout":   180,
                "no_think":  False,
            },
            {
                "name":      "Gemini 2.5 Pro",
                "url":       "https://generativelanguage.googleapis.com/v1beta/openai",
                "key":       os.environ.get("GEMINI_API_KEY", ""),
                "model":     "gemini-2.5-pro",
                "max_tokens": 5000,
                "timeout":   120,
                "no_think":  False,
            },
            {
                "name":      "Qwen (local)",
                "url":       "http://vision-gateway:8080/v1",
                "key":       "local",
                "model":     "qwen3.5:9b",
                "max_tokens": 4200,
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

        # Curated gold standard with dynamic fallback — avoids voice drift feedback loop.
        # Was 2026-03-14-the-open-office-was-designed-to-break-my-brain.md, five months
        # before the Aug-4 Bregman redesign — audit found it violates ~6 current rules
        # (a banned ## header that _structural_validator strips, two bolded epigrams
        # against the one-aphorism cap, invented specific numbers, an inline
        # parenthetical definition, the now-overused placed-body-present-tense opening).
        # A full worked example teaching the opposite of the current rules outweighs any
        # amount of abstract instruction. Replaced with a post-redesign piece independently
        # rated the strongest of a 10-article reader-perspective sample.
        _gold_ref = self.posts_dir / "2026-07-29-weegee-heard-the-body-first.md"
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
            "Your task: edit the BODY of articles. Your primary tool is SUBTRACTION — cut weak "
            "sentences, flabby transitions, throat-clearing, and structural dead weight. Fix rhythm. "
            "Clarify argument. Do NOT add new examples, arguments, or analysis that aren't already "
            "in the draft. The frontmatter (between --- markers) and image HTML blocks "
            "(`<figure class=\"article-figure\">...</figure>`) must be preserved exactly as-is.\n\n"
            "PROTECT WHAT'S WORKING:\n"
            "- If the opening paragraph is already a specific scene, concrete moment, or sharp claim: "
            "DO NOT CHANGE IT. The opening is the most important sentence in the piece. Protect it.\n"
            "- If the draft has a raw, unresolved moment — a contradiction, admission of confusion, "
            "or thought that doesn\'t land cleanly — protect that too. Leave it unresolved. "
            "Not every idea needs to be resolved; some should stop in the middle.\n\n"
            "WHAT NOT TO ADD:\n"
            "- Do not introduce organization names, theorists, academic concepts, or proper nouns "
            "that aren\'t already in the draft. If a reference appears, it must have been in the original.\n"
            "- Do not add citations, studies, or statistics the author didn\'t use.\n"
            "- Do not add summary sentences or conclusions that weren\'t there.\n"
            "- Do not convert one valid ending shape into another — see rule 7. An abrupt stop may be correct; so may a confident, resolved landing. Change the ending only if it is a call to action, a summary, a thesis restatement, or a mirrored image-couplet.\n\n"
            "EDITORIAL VOICE RULES:\n"
            "1. First-person throughout — lived expertise, not detached analysis\n"
            "2. NO academic headers: Research Question / Methodology / Key Findings / Recommendations / Community Questions\n"
            "3. NO bullet-point policy lists — weave argument into prose\n"
            "4. NO \"Case study: Sarah, a graphic designer...\" — use real narrative flow\n"
            "5. Paragraphs with rhythm — short sentences land the idea, longer ones develop it. No sentence chains more than two comma-clauses. Paragraph length varies: a short one hits differently after a long one.\n"
            "6. Bold sparingly — only sharpest claims, never structural markers\n"
            "7. ENDING — NO HOUSE SHAPE: several endings are valid and you must not convert one into another. A hard resolution the author commits to, a live question left open, a last word given to a quoted source, a plain concrete fact, or a coda folding back to the opening scene: all fine. Do NOT force irresolution, and do NOT cut a confident landing just because it resolves — a warm, committed close is often the best thing in the piece. Still cut: calls to action, summaries of the argument just made, thesis restatements, title echoes, and any sentence starting 'We need' / 'This requires' / 'Join' / 'I am developing'. If the draft closes on a resolving image-couplet (two mirrored sentences, e.g. 'The campfire is warm. The path is cold.') that is a rhythm tic rather than a real ending — flatten it to one sentence or cut back to the last line that says something new.\n"
            "8. CONCESSION: if the draft happens to dismantle an assumption, check that it gives the strongest version of the opposing view first. If it attacks a weakened version, strengthen the concession before the flip. Do not add a concession that is not already there.\n"
            "9. 450-2800 words body — match the original target length, do not shrink. Long pieces are deliberate (the 2800-word bucket matches the writing model's own measured length); do not compress one toward a house length.\n"
            "10. Author\'s disability is their EXPERTISE and LENS, never tragedy or limitation\n"
            "10b. AUTHOR RULE: Written BY a disabled person, not ABOUT disability. "
            "The subject is the world. The disability is the seeing. "
            "If the draft\'s thesis is 'this system excludes disabled people\', find what the author "
            "notices that others miss and reframe the article around that instead. "
            "Test: could this article exist without the word 'disability' appearing at all "
            "and still carry a specific, irreplaceable perspective? That is the standard.\n"
            "11. REGISTER — a smart person explaining something to a friend. Not dumbing down, not writing up. \'The approaching body\' → \'you.\' \'Sensory apparatus\' → \'senses.\' \'Gradient\' → \'slope.\' One modifier per noun — never three stacked. When technical language must stay, unpack it in the same sentence. The target register: intelligent dinner party conversation, not academic paper, not journalism.\n"
            "12. ONE MODIFIER PER NOUN. If the draft has \'the physical, spatial, sensory reality\' — pick the one that does the most work and cut the rest. If it needs three adjectives, the noun is wrong.\n"
            "13. LISTS OF THREE — with one earned exception. Four items in a list is one too many, "
            "UNLESS the list is deliberately piling up toward a single payoff or reversal (real "
            "Bregman example: nine items — Columbus, Galileo, Newton, the scientific revolution, "
            "the reformation, the enlightenment, gunpowder, the printing press, the steam engine — "
            "listed in one sentence specifically so the next sentence can land 'and income was still "
            "the same' with full weight). A long list used to build cumulative force before an ironic "
            "or surprising turn is earned; a long list that just enumerates with no payoff after it is "
            "the violation. If you cannot point to the sentence right after the list that the length "
            "was building toward, cut to three.\n"
            "14. PARAGRAPH MOMENTUM: When a paragraph builds by accumulation — specific details gathering weight toward a single point — do not interrupt with analysis mid-build. Let the details complete their arc. The argument arrives after the observation lands, not inside it.\n"
            "15. LANDING: End accumulations with the concrete thing that carries the weight — one image, one fact — not an abstract reframing. No metaphor that requires reconstruction under pressure. This governs accumulations mid-piece, NOT the article's ending (rule 7 governs that), and it does not license a second epigram: the one-verdict-sentence budget in rules 27 and 40 still applies.\n"
            "16. NO INLINE PARENTHETICAL DEFINITIONS. Never explain a term mid-sentence with em-dashes or parentheses — "
            "or with a comma-construction like 'X, meaning Y' ('sectional, meaning the design is built on how the "
            "building reads when you slice through it vertically' is the same violation wearing a comma). "
            "NEVER: 'a listed façade (a building legally protected as historically significant)' — cut it entirely. "
            "NEVER: 'acoustic analysis—the scientific study of how sound behaves—' — same problem. "
            "RIGHT: 'a listed façade.' or 'a listed façade. Listed buildings are legally protected — nobody can touch the structure.' "
            "If the term needs unpacking, give it its own sentence after. If it doesn't need unpacking, trust the reader and move on.\n"
            "17. PLAIN VOCABULARY. Prefer the Anglo-Saxon word over the Latinate one when meaning is identical. 'use' not 'utilise'. 'show' not 'demonstrate'. 'build' not 'construct'. 'change' not 'transformation'. 'ask' not 'interrogate'. 'help' not 'facilitate'. 'think' not 'conceptualise'. Keep technical terms only when no plain word carries the same precision — but earn them one at a time, not in clusters.\n"
            "18. SYSTEM VOICE — BANNED: Never write in the syntax of the institutions you are critiquing. The test: can you point to who is doing what to whom? If not, rewrite. Passive voice erases the person causing harm. Stacked bureaucratic nouns erase the person experiencing it. Examples: 'The system handled equipment requests' → 'When a disabled tenant needed a grab rail, they submitted a form.' 'Stops were flagged as non-compliant' → 'Auditors found stops wheelchair users couldn't reach.' 'Claimants were required to navigate' → 'To file a claim, you clicked through seven screens.' If your sentence could appear in the policy document you are criticising, rewrite it with a human subject and a concrete verb.\n"
            "19. NOMINALIZATION — BANNED: Actions stay as verbs. When a verb becomes a noun, the person doing it disappears. 'The redesign of the system' → 'they redesigned the system.' 'The implementation' → 'they built it.' 'The assessment of needs' → 'someone asked what you needed.' Scan for nouns ending in -tion, -ment, -ance, -ence, -al, -ure — these are often verbs in disguise. Free the verb. Name who does it.\n"
            "18b. SECTION BREAKS: Use --- sparingly. Two breaks per article is the target. Three is the ceiling. Never more. Each break asks the reader to restart without a handhold. Use a break only when the shift is a genuine scene change or time jump — not a new paragraph of thought. Transitions happen inside the prose.\n"
            "19b. VAGUE WE — BANNED: 'We' must always have a named referent. If 'we' means everyone, it usually means a specific group that benefits from not being named. Name them. 'We designed this system' → 'non-disabled designers built this system.' 'We don't talk about this' → 'the council never published this.' If you cannot say who we is, cut the word and make someone specific do the thing.\n"
            "20. NAMED REFERENCES: When you name a theorist or researcher, give one sentence of context and move on immediately. Name + what they said or did + why it matters here — all in one sentence. Never leave a name floating with just a year. Never spend a paragraph explaining who someone is before using their idea. If the idea cannot survive one sentence of context, cut the reference and use the idea directly.\n"
            "21. FRONT-LOADED SENTENCES — BANNED: Never open a sentence with a long subordinate clause that buries the subject. 'What happens after the ship date has none of those things' → 'Once the team ships, nobody checks whether it works.' 'When considering the broader implications of' → cut entirely, start with the implication. Subject first, verb second, detail after. The reader should know who is doing what before they get to why. This also fails when the subject IS named first but a long appositive or relative clause — 'X as a/an Y that/which/who Z' — is then wedged before the verb ever arrives: 'The eye as an organ that some of us route the whole world through gets a footnote' names 'the eye' immediately but delays 'gets' by 12 words. Split it instead: 'Some of us route the whole world through our eyes. That gets a footnote.'\n"
            "22. Crip culture references (Sins Invalid, crip time, disability justice) only when they fit naturally\n"
            "23. PARAGRAPH LENGTH: Keep paragraphs short — 2 to 4 sentences as the norm. A one-sentence paragraph is a verdict; use it. If a paragraph runs past 5 sentences, find where it splits into two thoughts and break it there. Long paragraphs diffuse impact. The rule is not variety — it is compression: say the thing, then stop.\n"
            "24. DISCOVERY VOICE: Research should feel found, not reported. Use the rhythm of live discovery — 'even more interesting is that...', 'it turns out...', 'what nobody mentions is...', 'the part that stuck with me...' This is not hedging. It is the opposite: confident enough to let the reader feel the moment of realisation. Academic hedging is defensive. Discovery voice is forward-moving. It makes the reader lean in.\n"
            "25. OPENING — NO HOUSE SHAPE: do not convert one valid opening into another. A plain expository claim, a cold scene, a bare dated fact, a rare question, and a plain statement of what the writer set out to find out are all legitimate. Never rewrite a committed flat claim into a scene — a claim the essay then spends its length paying off is one of the strongest openings there is, and the placed-body-in-present-tense scene is currently overused across the publication. Do cut: throat-clearing, context-setting, 'X has long been a problem', a definition or a framework named before anything concrete has happened. Every word in the opening paragraph must be working.\n"
            "26. NO INVENTED DATA. Never write a specific number, percentage, or study finding that is not in the source material. Fake stats destroy credibility if checked. Use qualitative language instead: 'significantly more', 'consistently longer', 'dramatically worse'. If source material has real figures, use them and name the source in the prose. If it does not: no figures at all. No '73% of wheelchair users', no 'a 2025 study found', no '$4.2 million' -- unless those exact figures appear in the source text you were given.\n"
            "27. WRITING MODEL — RUTGER BREGMAN, PROCESS NOT RESIDUE: The target register is Bregman — accessible intellectual journalism, educated-conversational, plain and chronological. What matters is that the piece reads like a record of someone finding something out, not a performance of a conclusion. So: PROTECT these shapes when they are already in the draft — COMPARATIVE CASE, CONCESSION, REDEFINE, INSIDER WITNESS, CODA, the reader's objection voiced and answered, a complication left standing. Do NOT install any of them that is not there. Do not reframe an existing paragraph into a comparative case to manufacture the shape. These moves were reverse-engineered from finished work; adding them by hand is what makes a draft read as technique-shaped with nothing reported inside it. Two things to actively cut instead: (a) any sentence that tells the reader a connection was made rather than letting the facts do it — 'run those two facts next to each other and something clicks', 'this reveals', 'that is the point'; (b) any sentence that announces a move about to be performed — 'here is the case I cannot fold in', 'here is where my argument turns on me'. Delete the announcement, keep the material under it. And cap epigrams at one per piece: if the draft has three or four short balanced verdict-sentences, keep the strongest and flatten the rest into plain prose, so the one that remains lands.\n"
            "28. JARGON — BANNED: Strip institutional vocabulary. 'Claimants' → 'tenants' or 'residents'. 'Non-compliant' → say what the barrier is. 'Change of circumstances' → 'situation had changed'. 'Platform upgrades' → 'rebuild the platform'. 'Stakeholders' → who they are. 'Outcomes' → what people got or did not get. 'Intervention' → what actually happened. 'Priority locations' → name the actual place. If the word appears in a government report, a council briefing, or an accessibility audit — replace it with what a person would say to another person.\n"
            "29. TEMPORAL ANCHORS: If an anecdote already has a real date, month, or place in the draft, keep it precise and do not vague it out — 'Last autumn' should stay as whatever real date the draft gave it, not get flattened. Do NOT invent a date, month, place, or role that is not already in the draft — you are editing, not writing, and you cannot know when something really happened. If an anecdote is genuinely undated in the draft, leave it undated rather than manufacture a year or a witness for it.\n"
            "30. NO HEDGING AGAINST NOBODY: Never write 'X is not Y, but...' unless someone is genuinely arguing that X is Y. Cut the first clause. 'The mechanism is the same' does the work alone. Preemptive hedging signals insecurity. The juxtaposition speaks for itself.\n"
            "31. GROUNDING: The argument lives in the body before it lives in theory. If the draft leans on a concept or a theorist without ever reaching the physical sensation, place, or event that earned it, find that concrete material and bring it forward. This governs what the argument rests on, not which sentence opens the piece — a draft that opens on a plain claim and lands its concrete grounding a paragraph later is fine, so do not move a scene to the front just to have a scene at the front.\n"
            "32. US-AVOIDANCE + UK-PREFERENCE: Do not locate arguments in the United States specifically. No ADA, FEMA, or American laws or institutions. Preferred geographies: UK (DWP, PIP assessments, NHS social care, Equality Act 2010, Section 117 aftercare), the Netherlands, Germany, and unnamed cities. UK disability policy is especially rich territory — the gap between the Equality Act's promises and PIP's practice, the WCA (Work Capability Assessment), care home regulation, and the history of the disabled people's movement from UPIAS onward. When a UK-specific angle fits the argument, use it by name. Arguments must feel globally applicable, but specific named examples carry more weight than vague universals.\n"
            "33. NAMED VOICES: The draft should have 2-3 real named people — quoted or closely paraphrased with full attribution. Name + what they said + context in one sentence. REQUIRED: beyond the primary subject of the article, a second real named person must appear doing something specific in the body. A person named only in the footnote or source note does not count. At least one should be a source the reader would not expect to agree with the argument. Never 'a researcher found' or 'studies show' — name the researcher, name the study.\n"
            "33b. SOMEONE ELSE MUST SPEAK: at least one other person must say something out loud inside actual quotation marks, in the past tense, saying something the narrator did not script for them. Conditional-mood positions ('she would say', 'he would reject this'), summarised stances, and ventriloquised objections do not satisfy this. If the draft has one, protect it and do not paraphrase it away. If the draft has none, say so in the edit — but do not invent a quote; never attribute words to a real named person that were not in the draft.\n"
            "34. SHOW THEN NAME: Never define a concept before showing it. First: the specific example, the concrete detail, the scene. Then — only if needed — 'this is called X.' If the concept is defined before the reader has felt it, cut the definition and trust the example.\n"
            "35b. NO DECODING REQUIRED: If a sentence requires the reader to stop and work out what it means before moving on, rewrite it. Three patterns to cut: (1) buried qualifiers — 'the thought being that X' → state X directly; (2) metaphors that need unpacking — 'a body that hears with its eyes' requires two mental steps before it means anything, break it into what it actually says; (3) abstract compression — 'something they have no box for' → 'something they cannot name' or 'something outside their framework'. The test: read the sentence aloud. If you pause mid-sentence to process it, the reader will too. Rewrite until they don't.\n"
            "35c. TRANSLATED ABSTRACTION — PROTECT ONE, INSTALL NONE: Where the draft reaches a figure, a mechanism, or an institutional term the reader can read without feeling, check what it does with it. If it converts that abstraction into one concrete thing the reader has already been inside — a household object, a room, a bodily state, a piece of manual work — protect that sentence. FIRST, apply this diagnostic before applying rule 15 or 35b to the sentence at all: delete it and ask whether you would then need to restate the underlying fact or mechanism in plain technical language for the reader to still follow the argument. If yes, this sentence IS the translation, full stop — protect it exactly as written, even though it is built on 'is' / 'was' / 'feels like' and would otherwise read as a metaphor. Rule 35b's 'two mental steps to decode' test does NOT apply to a sentence that passes this diagnostic: recognising a plainly-stated comparison in one beat is the ordinary, intended work of reading it, not the buried-jargon decoding that rule targets. Example of a sentence that must be protected and NOT flagged by 35b: 'It feels like a firefighters' conference where nobody is allowed to mention water' — this requires no reconstruction; the image and the argument arrive together, in one pass. Do not flatten a protected sentence back into the technical statement, and do not cut it under rule 15 either: that rule governs figures that make a plain thing harder to parse, and this one runs the other way, abstract to concrete, to make a hard thing plain — the two rules are not testing the same failure and a sentence cannot fail both. Two forms are correct: one flat sentence with no build-up and no follow-through, or a concrete thing told first at length as its own story and mapped in a single short sentence at the end. If the draft has the middle form — three or four sentences of half-elaborated comparison — cut it back to the flat sentence, or cut it entirely if no single sentence survives. Where the draft instead handles an abstraction with an encyclopedic appositive ('X, a Y that does Z') and nothing in the piece already passes the diagnostic above, you may cut the appositive — but you may NOT write a comparison to replace it. That is new material, and a bolted-on analogy reads worse than a bare term. Ceiling: one protected translation per piece. If two or more pass the diagnostic, keep the one carrying the most weight and return the rest to plain statement. This does not count against the one-aphorism budget in rules 27 and 40 — a translation is an explanation, not a verdict-sentence.\n"
            "35. INSIDER WITNESS: The strongest evidence is often a confession from someone who benefits from the system being critiqued — a building inspector who signs off on ramps he knows are too steep, a hiring manager who admits the interview is a neurotypicality test. If a figure like this is ALREADY in the draft, protect them — do not smooth them into a statistic. Do NOT invent one if the draft doesn't have one; a fabricated insider confession is a fabricated quote wearing a costume, and this publication does not put invented words in anyone's mouth, real or composite.\n"
            "36. ANALYTICAL WALL — BREAK IT: If the draft contains two or more consecutive sentences where no specific human being is doing something concrete — sentences about systems, policies, or abstract forces — find a person, body, or moment from elsewhere in the draft and move or echo it inside that wall. Do not invent new material. Redistribute what is already there. Every analytical passage must have a human heartbeat running through it. The reader must feel who is paying the cost of the abstraction being described.\n"
            "37. TRUNCATED SENTENCES: If the article ends mid-sentence — no period, no deliberate fragment, just a clause that stops — this is a generation error, not intentional rawness. Complete the sentence in the author's voice using context from the rest of the article. Then check: does the completed sentence make a strong enough ending, or does the thought need one more sentence to close properly? The article must end with a complete, deliberate stop — even if that stop is a fragment, it must be a chosen fragment, not an accident.\n"
            "38. COMPLICATING EXAMPLE: Check whether the essay includes one example that resists the argument and is STILL UNRESOLVED at the end. A false complication introduces a counter-case and then explains why it confirms the argument — that is the argument wearing a mask. If the paragraph after the complication begins with 'But', 'However', 'This does not mean', or otherwise neutralizes it, the complication has been resolved — cut that neutralizing paragraph or move the complication to the final section. If the complication is introduced by a signpost sentence ('here is the case that complicates this'), delete the signpost and let it arrive unannounced. If no complication is present, leave it that way — do not invent one; a bolted-on counter-case reads worse than none.\n"
            "39. PERSONA HISTORY: If the draft draws on the persona's own past, protect it — especially where it complicates their position rather than illustrating the argument. If it is absent, do not add one. A dated autobiographical flashback inserted as evidence in every piece, in the same slot, is a filing habit and reads as one.\n"
            "40. ARRIVAL PARAGRAPH — OPTIONAL, CEILING OF ONE, SHARES THE APHORISM BUDGET: A single-sentence paragraph may mark the moment the argument turns. If the draft has none, leave it that way — do not manufacture one; that is how forced epigrams get in. If the draft has more than one, or has one plus a separate epigram elsewhere, cut back to a single verdict-sentence in the whole piece: keep the strongest and fold the rest into the preceding paragraphs. A single-sentence paragraph is NOT an arrival if: (a) it could be appended to the preceding paragraph without loss, (b) it evaluates something the preceding paragraph already argued ('That is real work.'), or (c) it functions as a transition device ('This is not coincidence.') — fold those back regardless of the count.\n"
            "41. SPIRAL MOVEMENT: The strongest structure moves in widening circles — specific case, abstraction, different domain and different case, abstraction, personal consequence or open question. If the draft builds a logical ladder, check whether any two consecutive examples come from the same domain. If so, look elsewhere in the draft for an example from a different world that already exists and could move into that slot. Do not invent a new example — redistribute what is already there, same as rule 36. If nothing else in the draft fits, leave the ladder as it is.\n"
            "Return ONLY the complete edited article (frontmatter preserved + image lines preserved "
            "+ edited body). No commentary, no preamble."
        )

        user_msg = (
            f"REGISTER REFERENCE (match this voice and quality level — but improve the draft on its "
            f"own terms, not by making it sound like this piece):\n"
            f"<gold_standard>\n{gold}\n</gold_standard>\n\n"
            f"ARTICLE TO EDIT:\n<article>\n{content}\n</article>\n\n"
            "Edit the article body: cut what's weak, protect what's raw and working. "
            "Preserve frontmatter and all `<figure>` image HTML blocks exactly."
        )

        try:
            self.logger.info("Rewriting with Opus for quality improvement...")
            rewritten = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=SYSTEM,
                user_prompt=user_msg,
                model="openrouter/claude-opus-4.8",
                max_tokens=5000,
                timeout=240,
                check_truncation=True,
            )
            if rewritten and rewritten.count("---") >= 2 and len(rewritten) > 400:
                self.logger.info("Opus rewrite succeeded (%d chars)", len(rewritten))
                return rewritten.lstrip("\n")
            self.logger.warning("Opus rewrite returned invalid response — keeping original")
        except Exception as e:
            self.logger.warning("Opus rewrite failed: %s — keeping original", e)

        return content

    def _active_fault_lines(self, text):
        """Return list of relationship pairs whose trigger keywords appear in text.

        Each item: {"personas": [...], "tension": "...", "cross_cite": "..."}
        """
        try:
            data = json.loads(_RELATIONSHIPS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
        text_lower = text.lower()
        active = []
        for pair in data.get("pairs", []):
            if any(kw in text_lower for kw in pair.get("trigger_keywords", [])):
                active.append({
                    "personas": pair["personas"],
                    "tension":  pair["tension"],
                    "cross_cite": pair.get("cross_cite", ""),
                })
        return active

    def _load_persona_canon(self, agent_name):
        """Load the immutable canon file for a persona. Returns text or ''."""
        slug = _AGENT_SLUG.get(agent_name, agent_name.lower().replace(" ", "-"))
        path = PERSONA_CANON_DIR / f"{slug}.md"
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _extract_persona_wound(self, agent_name) -> str:
        """Extract only the ## THE WOUND section from the persona canon. Returns text or ''."""
        import re as _re
        canon = self._load_persona_canon(agent_name)
        if not canon:
            return ""
        m = _re.search(r"##\s+THE WOUND\s*\n(.*?)(?=\n##|\Z)", canon, _re.DOTALL)
        return m.group(1).strip() if m else ""

    def _load_persona_state(self, agent_name):
        """Load mutable state JSON for a persona. Returns dict with defaults if missing."""
        slug = _AGENT_SLUG.get(agent_name, agent_name.lower().replace(" ", "-"))
        path = PERSONA_STATE_DIR / f"{slug}.json"
        defaults = {
            "obsessions": [], "unresolved_questions": [], "ongoing_arguments": [],
            "claims_on_record": [], "recent_mood": "neutral", "last_updated": ""
        }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {**defaults, **data}
        except (FileNotFoundError, json.JSONDecodeError):
            return defaults

    def _save_persona_state(self, agent_name, state):
        """Persist updated state JSON for a persona."""
        slug = _AGENT_SLUG.get(agent_name, agent_name.lower().replace(" ", "-"))
        path = PERSONA_STATE_DIR / f"{slug}.json"
        path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    def _call_editorial_model(self, system, user, max_tokens=1200, timeout=60, prefer_opus=False):
        """Try Fable 5 → Opus 4.8 via CLIProxy, then bypass CLIProxy and call OpenRouter directly.

        CLIProxy is a thin proxy to OpenRouter — if it's down, calling OpenRouter directly
        is equivalent. Requires OPENROUTER_API_KEY in environment for the direct fallback.

        claude-fable-5 has mandatory extended thinking on this endpoint (reasoning cannot
        be disabled) and reasoning tokens count against max_tokens. Left unbounded, thinking
        was consuming nearly the entire budget and truncating the JSON payload mid-string
        (json.loads failures on every call). Fixed two ways: cap Fable's reasoning spend via
        the request's reasoning.max_tokens field, and guarantee max_tokens always leaves at
        least FABLE_OUTPUT_HEADROOM beyond that cap for the actual response.

        prefer_opus: added 2026-08-10, after an audit of every phase routed through this
        function found Fable's mandatory reasoning is a straight liability (not just an
        occasional risk) on full-article-body verbatim-preservation tasks specifically --
        the reasoning_max_tokens cap doesn't reliably bound real spend (confirmed live,
        6/6 reproductions), so a ~2800-word article is arithmetically guaranteed to
        truncate Fable at these call sites' token budgets. Callers doing that kind of task
        (polish rewrite, cross-cite repair, fabrication repair) should pass True so Opus is
        tried first -- Fable stays in the chain as a last-resort fallback rather than being
        removed outright, since a Fable response still beats no response if Opus is down.

        Attempt order also puts Opus/OpenRouter-direct ahead of Fable/OpenRouter-direct
        (fixed 2026-08-10): if Fable truncated on CLIProxy for token-budget reasons, it will
        truncate identically via direct OpenRouter -- that attempt was previously
        guaranteed-wasted whenever CLIProxy failed for an unrelated transport reason.
        """
        FABLE_REASONING_BUDGET = 1024
        FABLE_OUTPUT_HEADROOM = 1600
        fable_max_tokens = max(max_tokens, FABLE_REASONING_BUDGET + FABLE_OUTPUT_HEADROOM)
        fable_timeout = max(timeout, 90)

        _or_key = os.environ.get("OPENROUTER_API_KEY", "")
        _or_url = "https://openrouter.ai/api/v1"

        fable_attempts = [(CLIPROXY_URL, CLIPROXY_KEY, "openrouter/claude-fable-5", "Fable/CLIProxy")]
        opus_attempts = [(CLIPROXY_URL, CLIPROXY_KEY, "openrouter/claude-opus-4.8", "Opus/CLIProxy")]
        if _or_key:
            opus_attempts.append((_or_url, _or_key, "anthropic/claude-opus-4.8", "Opus/OpenRouter-direct"))
            fable_attempts.append((_or_url, _or_key, "anthropic/claude-fable-5", "Fable/OpenRouter-direct"))

        attempts = (opus_attempts + fable_attempts) if prefer_opus else (fable_attempts[:1] + opus_attempts + fable_attempts[1:])

        for url, key, model, label in attempts:
            is_fable = "Fable" in label
            try:
                raw = self._call_openai_compat_api(
                    url, key, system, user,
                    model=model,
                    max_tokens=fable_max_tokens if is_fable else max_tokens,
                    timeout=fable_timeout if is_fable else timeout,
                    reasoning_max_tokens=FABLE_REASONING_BUDGET if is_fable else None,
                    check_truncation=True,
                )
                if "direct" in label:
                    self.logger.warning("Editorial model: CLIProxy bypassed — %s active", label)
                elif "Opus" in label:
                    self.logger.warning("Editorial model: Fable unavailable — %s active", label)
                return raw
            except Exception as e:
                self.logger.warning("Editorial model %s failed: %s", label, e)

        self.logger.error("Editorial model: all attempts failed (CLIProxy + direct OpenRouter)")
        return None

    def _fable_editorial_brief(self, news_title, news_summary, disability_angle, current_agent):
        """Fable 5 generates an editorial brief before writing.

        Returns dict {persona, angle, register, seed_sentence} or None on failure.
        """
        import json as _j
        personas = "\n".join(
            f"- {n}: {info['perspective'][:120]}"
            for n, info in self.agents.items()
        )
        reg_names = ", ".join(r[0] for r in _REGISTERS)
        system = (
            "You are the editorial director of Crip Minds — a disability culture publication. "
            "Each persona writes about the world through their specific disability lens, "
            "not about disability as a topic. "
            "Assign the best persona for today's story and give the writer a sharp brief. "
            "A brief here is an assignment to go find something out, not a conclusion to be written up."
        )
        # Build per-persona state summaries for the brief
        state_summaries = []
        for name in self.agents:
            s = self._load_persona_state(name)
            if s["obsessions"] or s["recent_mood"] != "neutral":
                top_obsessions = "; ".join(s["obsessions"][:2])
                mood_line = f"mood: {s['recent_mood']}" if s["recent_mood"] != "neutral" else ""
                args_line = f"active argument: {s['ongoing_arguments'][0][:80]}" if s["ongoing_arguments"] else ""
                parts = [p for p in [top_obsessions, mood_line, args_line] if p]
                state_summaries.append(f"  {name} — {' | '.join(parts)}")
        state_block = ("\nCurrent persona states:\n" + "\n".join(state_summaries)) if state_summaries else ""

        # Detect active fault lines from story text
        _search_text = f"{news_title} {news_summary} {disability_angle}"
        _fault_lines = self._active_fault_lines(_search_text)
        if _fault_lines:
            _fl_lines = []
            for fl in _fault_lines[:2]:  # max 2 fault lines in the brief
                pair_str = " vs. ".join(fl["personas"])
                _fl_lines.append(f"  [{pair_str}] {fl['cross_cite']}")
            _fault_block = "\nACTIVE FAULT LINES for this story:\n" + "\n".join(_fl_lines)
        else:
            _fault_block = ""

        _recent_openings = self._get_recent_openings(5)
        _openings_block = (
            "\nOPENING SENTENCES OF THE LAST FEW PIECES — read these before writing opening_scene. "
            "If they all share one shape (for example: a body placed in a named room in the present tense), "
            "you must pick a different shape for this piece. Repetition of opening shape is invisible inside "
            "any one article and glaring across four:\n" + _recent_openings + "\n"
        ) if _recent_openings else ""

        user = (
            f"Today's story:\n{news_title}\n"
            + (f"Summary: {news_summary[:400]}\n" if news_summary else "")
            + (f"Disability angle: {disability_angle}\n" if disability_angle else "")
            + f"\nPersonas:\n{personas}\n"
            + state_block
            + _fault_block
            + _openings_block + "\n\n"
            f"Registers available: {reg_names}\n\n"
            "Pick the persona whose current state, canon, and obsessions make them the most alive "
            "voice for this story right now — not just topic match, but friction, mood, and timing. "
            "If a fault line is active, choose the persona who stands most firmly on one side of it, "
            "and put the substance of the disagreement in cross_cite — the idea, not an instruction to "
            "name the colleague. Personas argue with each other's positions, not with each other's bylines.\n\n"
            "BRIEF A QUESTION, NOT A VERDICT — this is the most important instruction here. Do not hand the writer a thesis to execute. Hand them something they do not know the answer to and have to find out on the page. The old briefs produced essays that were delivery mechanisms for a conclusion the writer already held before the first sentence; that is exactly what we are trying to stop. So the angle is a real question — one where you yourself cannot confidently predict what the persona will conclude, and where at least two answers are genuinely live. 'Whether the drilling next door is maintenance or the eviction' is a question. 'The drilling is the eviction' is a verdict; do not write that. If you can already see the finished argument, the question is too easy — sharpen it until you cannot.\n\n"
            "For correction_moment: name one specific thing the persona hits that proves them wrong, stops them, or corrects them — a belief the material breaks, a dead end, a document that says the opposite of what they expected, a person who tells them something that does not fit. Concrete and locatable, with a place or a date. This goes into the draft in the past tense, before the midpoint, shown happening. It is not end-of-essay doubt and not a hedge. The engine of this kind of writing is 'I believed X, then I found the thing that broke X' — give them the thing that breaks X.\n\n"
            "For resisting_example: something the persona actually encounters in the world of this story, not an abstract objection to gesture at. Best case: a real named person who shares the persona's values, or who benefits from the same framework being applied, and who nonetheless rejects the argument — a counter-movement from inside, not a counter-argument from outside. Something they said, did, built, or refused. Do not phrase it as a hypothetical position the writer can ventriloquise ('X would say...'); that produces a monologue. Do not pick a counter-case the argument easily defeats.\n\n"
            "For opening_scene: write the actual first sentence of the essay, in the persona's voice — the sentence itself, not a description of where the piece begins. THERE IS NO HOUSE OPENING. Do not default to a body doing a physical action in a named place in the present tense; that shape has opened four consecutive pieces and now reads as a template rather than as craft. Choose whichever of these this particular story earns: (a) PLAIN CLAIM — a flat expository assertion the rest of the piece will spend its length paying off ('For centuries western culture has been permeated by the idea that humans are selfish creatures.'); (b) COLD SCENE — a placed body, an action, a named room, something already in progress; (c) A QUESTION — rare, and only when the question is genuinely the engine of the piece; (d) A FACT — one concrete dated thing, stated and left alone ('In 1965, six boys stole a fishing boat from a harbour in Tonga.'); (e) A DECLARATION OF THE HUNT — plainly saying what you set out to find out, and that you did not know the answer. A plain claim or a bare fact is often stronger than a scene, because it commits and then earns the commitment. Still wrong in every variant: 'X's work raises questions about...', 'There is a concept designers call...', and any throat-clearing before the piece starts.\n"
            "For register: this is where the piece starts, not a setting locked for its whole length — pick the opening tone.\n\n"
            "Reply with JSON only — no other text:\n"
            '{"persona":"name","angle":"the question the persona is finding out the answer to — phrased as a question, one where you cannot predict their conclusion",'
            '"register":"one register name",'
            '"seed_sentence":"the opening sentence of the article — concrete, not a question",'
            '"opening_scene":"the actual first sentence of the essay in the persona\'s voice — NOT a description of where it begins. Vary the shape: plain claim, cold scene, question, bare fact, or a statement of what you set out to find out. Do not default to a placed body in the present tense",'
            '"opening_shape":"which shape you chose: plain_claim | cold_scene | question | fact | declaration_of_hunt",'
            '"correction_moment":"one sentence naming the specific thing that proves the persona wrong, stops them, or corrects them mid-piece — concrete, placed or dated",'
            '"resisting_example":"one sentence naming a real person or case that resists the argument from inside the same value system — something they actually said or did, not a hypothetical",'
            '"cross_cite":"optional: one sentence on the substance of the disagreement with another persona\'s position — the idea being pushed against, NOT an instruction to name-check them. Leave empty unless the disagreement genuinely bears on this story"}'
        )
        raw = self._call_editorial_model(system, user, max_tokens=1600, timeout=60)
        if raw is None:
            self.logger.error("Fable brief: all models failed — article will publish without persona override, angle, or seed")
            return None
        try:
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            brief = _j.loads(raw)
            if all(k in brief for k in ("persona", "angle", "register", "seed_sentence")):
                if brief["persona"] in self.agents and any(brief["register"] == r[0] for r in _REGISTERS):
                    brief.setdefault("cross_cite", "")
                    brief.setdefault("correction_moment", "")
                    brief.setdefault("opening_shape", "")
                    if brief.get("opening_shape"):
                        self.logger.info("Fable opening shape: %s", brief["opening_shape"])
                    if not brief.get("opening_scene"):
                        self.logger.warning("Fable brief: opening_scene missing — article will open without an opening anchor")
                    if not brief.get("resisting_example"):
                        self.logger.warning("Fable brief: resisting_example missing — article will lack structural friction")
                    if not brief.get("correction_moment"):
                        self.logger.warning("Fable brief: correction_moment missing — article will lack an onstage moment of being wrong or corrected")
                    if brief["cross_cite"]:
                        self.logger.info("Fable cross-cite: %s", brief["cross_cite"][:80])
                    self.logger.info(
                        "Fable brief → %s | %s | %s",
                        brief["persona"], brief["register"], brief["angle"][:60],
                    )
                    return brief
            self.logger.error("Fable brief: invalid persona/register — article will publish without persona override, angle, or seed")
        except Exception as e:
            self.logger.error("Fable brief parse failed: %s — article will publish without persona override, angle, or seed", e)
        return None

    def _fable_editorial_review(self, article_body, agent_name, brief_angle, register):
        """Fable 5 reads the Opus draft and returns (verdict, notes). Non-blocking."""
        import json as _j
        agent_info = self.agents.get(agent_name, {})
        system = (
            "You are the editorial director of Crip Minds. "
            "You have just read a draft article by one of the publication's AI personas. "
            "Give 2-3 specific, actionable revision notes — or confirm it is ready. "
            "Rules you enforce: no headers, no bullet lists, first-person throughout, "
            "concrete scene before analysis, no CTA endings, disability as lens not topic.\n\n"
            "CHECKS THAT PRODUCE REVISION NOTES:\n"
            "(1) OPENING — there is no house opening and you must not enforce one. A plain expository "
            "claim, a cold scene, a bare dated fact, a rare question, and a plain statement of what the "
            "writer set out to find out are all valid; a flat claim that commits is often stronger than a "
            "scene, because the piece then has to earn it. Do NOT ask for a scene as a default. Flag only "
            "real failures: throat-clearing, context-setting, 'X has long been a problem', or a definition "
            "or framework named before anything concrete has happened. Separately: if this opening is the "
            "same shape as recent pieces — especially a body placed in a named room in the present tense — "
            "say so and ask for a different shape. That repetition is the single most visible tell across "
            "a run of articles and is invisible from inside any one of them.\n"
            "(2) COMPLICATION STANDING — is there at least one example that resists the argument and is "
            "STILL UNRESOLVED at the end? A complication introduced and then explained away does not "
            "count — that is the argument wearing a mask. Note that this is something to value when it "
            "is there, not a quota: do not ask the writer to bolt one on if the piece has no natural "
            "friction, and never ask for one that the argument would obviously defeat.\n"
            "(3) DISCOVERY — is there a moment, before the midpoint and in the past tense, where the "
            "writer was wrong, stuck, or corrected by something they encountered? An essay that knows "
            "its whole argument from the first sentence and only appends doubt at the end reads as a "
            "performance of a conclusion rather than a record of curiosity. Doubt in the final "
            "paragraph does not satisfy this.\n"
            "(4) A REAL QUOTED VOICE — does at least one other person speak inside actual quotation "
            "marks, in the past tense, saying something the narrator did not script? Conditional-mood "
            "positions ('she would say', 'he would reject this'), summarised stances, and ventriloquised "
            "objections do not count. If every quoted line serves the thesis, the writer wrote the quotes. "
            "Flag this — a piece with no other human voice in it is a monologue in a sealed room.\n"
            "(5) APHORISM DENSITY — count the short, balanced, quotable verdict-sentences (the epigram "
            "shape: 'The drop is the argument. The gender was the alibi.' / 'The frame always arrives "
            "last.'). One per piece is the cap, and a single-sentence 'arrival' paragraph counts against that "
            "same budget — one verdict-sentence total, whether it stands as its own paragraph or sits "
            "inside one. If there are two or more, name the specific ones to cut "
            "or flatten into plain prose and keep only the strongest. Three crescendos in 800 words means "
            "none of them land. Also flag it if the narrator has topped a source's line — if a person in "
            "the piece said the sharpest thing, theirs should stay the sharpest thing.\n"
            "(6) MANAGING THE READER — flag any sentence that tells the reader a connection was made "
            "rather than letting the juxtaposition do it: 'run those two facts next to each other and "
            "something clicks', 'and there it is', 'this reveals', 'that is the point', 'the two are the "
            "same thing'. Quote the sentence and say to cut it. If the connection is real the facts click "
            "on their own; if it needs the narrator's help it is not real yet. Same for any sentence whose "
            "only job is explaining the meaning of the sentence before it.\n"
            "(7) SIGNPOSTED MOVES — flag any sentence that announces the technique being performed: "
            "'here is the case I cannot fold in', 'now the person who blows this argument apart', 'here is "
            "where my own argument turns on me', 'I want to be careful here, because there is a lazy "
            "version of this argument'. The complication stays; the announcement of it goes. When a turn "
            "is announced the reader stops experiencing an argument turning and starts watching a "
            "requirement being satisfied. Quote the signpost and say to delete it, leaving the material "
            "underneath intact.\n"
            "(8) ENDING — there is no house ending shape and you must not enforce one. A hard resolution "
            "the writer commits to, a live question, a last line given to a quoted source, a plain "
            "concrete fact, a coda folding back to the opening: all valid. Judge only whether this ending "
            "is the one this piece earned. Do NOT ask for irresolution as a default — mandated "
            "irresolution reads as performed humility and forecloses the confident, warm landing that is "
            "the model's most characteristic effect. Still reject: calls to action, summaries, thesis "
            "restatements, title echoes.\n"
            "(9) WHOLENESS — every other check here tests one local thing (an opening, a quote, an "
            "aphorism count). This one asks whether the piece hangs together as ONE essay, not a "
            "sequence of individually-passable paragraphs. Four questions: (a) THROUGHLINE — could you "
            "state, in one sentence, the single thing this piece is actually about? If you need two "
            "unrelated sentences, the piece is arguing two things and one has to go. (b) SETUP AND "
            "PAYOFF — does the ending complete or reframe something the opening actually established "
            "(a person, an object, a question, a scene) — not just share a theme with it, but pay it off? "
            "If the ending could be swapped onto a different essay by the same persona with no loss, it "
            "isn't earning its place in THIS one. (c) ABANDONED THREADS — is there a person, fact, or "
            "question introduced with apparent weight that then never gets resolved or returned to? Name "
            "it specifically. (d) TONAL DRIFT — does the piece's register hold steady start to finish, or "
            "does it start as one kind of piece (wry, clinical, dry) and drift into a different register "
            "by the end without the shift being earned by the material? Flag only real drift, not natural "
            "escalation. This check can fail even when every other check passes — a piece can be locally "
            "clean and still not read as one deliberate whole.\n\n"
            "CRAFT MOVES TO NOTICE AND PRAISE WHEN THEY ARE ALREADY THERE — never to require, never to "
            "request, never to count. If one of these emerged from the material, say so in a note so it "
            "is protected in revision; if none are present, that is not a defect and generates no note: "
            "COMPARATIVE CASE (two parallel stories run side by side, the contrast carrying the argument "
            "with no commentary); CONCESSION-BEFORE-KILL (the strongest version of the opposing view "
            "given first, then one short sentence flipping it); REDEFINITION (not 'you are wrong about X' "
            "but 'X is not the problem, Y is'); READER'S INTERNAL DIALOGUE (the reader's own objection "
            "voiced before they can raise it, then answered in a sentence); INSIDER CONFESSION (someone "
            "who benefits from the system admitting it is broken — worth more than any statistic); "
            "CODA (the opening scene returned to, later or elsewhere, without stating what changed); "
            "COMPLICATING EXAMPLE (a case from inside the argument's own value system that it cannot "
            "absorb); TRANSLATED ABSTRACTION (a figure, a mechanism, or an institutional term converted "
            "into one concrete thing the reader has already been inside — a household object, a room, a "
            "bodily state, a piece of manual work — either as one flat sentence with no follow-through, "
            "or as a story told first and mapped in a single sentence at the end, such that cutting it "
            "would cost the reader understanding rather than colour). These were reverse-engineered from a finished body of work — they are the residue "
            "of a process, not the process. Requiring them is what produced technique-shaped drafts with "
            "no reporting inside them, which is why they now live here and not in the writer's brief."
        )
        user = (
            f"Persona: {agent_name} ({agent_info.get('perspective', '')[:80]})\n"
            f"Question briefed: {brief_angle}\nStarting register: {register} (the piece is allowed to shift out of it)\n\n"
            f"DRAFT:\n{article_body[:12000]}\n\n"
            "Reply with JSON only:\n"
            '{"verdict":"publish_as_is" or "revise","notes":["note 1","note 2"]}\n'
            "Notes must name the specific paragraph or quote the specific sentence. Max 3 — "
            "if several checks fail, pick the three that most change the piece. "
            "If publish_as_is, notes may be empty."
        )
        raw = self._call_editorial_model(system, user, max_tokens=3200, timeout=60)
        if raw is None:
            self.logger.error("Fable editorial review: all models failed — article ships without revision pass")
            return "publish_as_is", []
        try:
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            result = _j.loads(raw)
            verdict = result.get("verdict", "publish_as_is")
            notes   = result.get("notes", [])[:3]
            self.logger.info("Fable review: %s (%d notes)", verdict, len(notes))
            if notes:
                for n in notes:
                    self.logger.info("  → %s", n[:100])
            return verdict, notes
        except Exception as e:
            self.logger.error("Fable editorial review parse failed: %s — article ships without revision pass", e)
            return "publish_as_is", []

    def _opus_targeted_revision(self, article_body, editorial_notes, agent_name):
        """Opus revises the article based on Fable's editorial notes. Non-blocking.

        Superseded by _fable_polish_rewrite (2026-08-07) for the normal call path --
        having Fable implement its own notes directly removes the cross-model
        translation step (Fable judges, Opus has to correctly interpret and apply a
        note it didn't write). Kept as a fallback for when Fable's own rewrite attempt
        fails or returns too little content.
        """
        if not editorial_notes:
            return article_body
        notes_text = "\n".join(f"- {n}" for n in editorial_notes)
        system = (
            "You are revising a draft for Crip Minds. Apply only the listed editorial notes. "
            "Do not rewrite anything not flagged. Preserve the author's voice, all facts and names, "
            "the structure, and the approximate length. "
            "No headers, no lists, no CTA endings."
        )
        user = (
            f"Persona: {agent_name}\n\nEDITORIAL NOTES:\n{notes_text}\n\n"
            f"ARTICLE:\n{article_body}\n\n"
            "Return the revised article body only — no preamble, no commentary."
        )
        try:
            self.logger.info("Opus targeted revision: applying %d editorial notes...", len(editorial_notes))
            revised = self._call_openai_compat_api(
                CLIPROXY_URL, CLIPROXY_KEY, system, user,
                model="openrouter/claude-opus-4.8", max_tokens=5000, timeout=180,
                check_truncation=True,
            )
            if revised and len(revised) > 400:
                self.logger.info("Targeted revision: %d chars", len(revised))
                return revised
            self.logger.warning("Targeted revision returned short response — keeping original")
        except Exception as e:
            self.logger.warning("Targeted revision failed: %s — keeping original", e)
        return article_body

    def _fable_polish_rewrite(self, article_body, editorial_notes, agent_name, register):
        """Fable rewrites the article directly, implementing its own editorial notes
        itself rather than handing them to Opus to interpret. Falls back to
        _opus_targeted_revision if Fable's rewrite fails or returns too little content
        -- the notes still exist and are worth applying even if this specific model
        call has trouble. Non-blocking either way; article ships on the original draft
        if both attempts fail.

        Note on expectations: two separate model-judged tests earlier the same session
        found that repair passes -- rule-based and exemplar-based, both run on Sonnet --
        plateaued at a real ceiling (10-15 remaining register issues per sample) rather
        than converging. This changes WHICH model executes the fix and WHO wrote the
        notes being implemented, not the fundamental mechanism (a single text-conditioned
        rewrite pass). It may still hit a similar ceiling. Worth testing on its own
        terms rather than assuming the model swap alone breaks through it.
        """
        if not editorial_notes:
            return article_body
        notes_text = "\n".join(f"- {n}" for n in editorial_notes)
        system = (
            "You are the editorial director of Crip Minds, about to rewrite a draft "
            "yourself instead of handing your notes to someone else to implement. "
            "You already read this draft once and wrote the notes below -- now fix "
            "exactly what you flagged, directly, in your own hand. "
            "Polish and harmonize the prose toward the publication's target register "
            "(plain declarative sentences, one idea per sentence, subject and verb "
            "close together, no crafted rhetoric, no aphoristic closers) while fixing "
            "the specific wholeness/craft issues in your notes. "
            "Do NOT change: the facts, the named sources and quotes, the persona's "
            "argument or position, the overall structure, or the approximate length. "
            "This is polish and harmonization, not a rewrite of substance. "
            "No headers, no bullet lists, no CTA endings."
        )
        user = (
            f"Persona: {agent_name}\nRegister: {register}\n\n"
            f"YOUR OWN EDITORIAL NOTES FROM READING THIS DRAFT:\n{notes_text}\n\n"
            f"DRAFT:\n{article_body}\n\n"
            "Return the complete rewritten article body only — no preamble, no commentary."
        )
        try:
            self.logger.info("Fable polish rewrite: implementing %d of its own notes...", len(editorial_notes))
            # prefer_opus (2026-08-10): full-body verbatim-preservation task -- Fable's
            # mandatory reasoning is arithmetically guaranteed to truncate this on longer
            # articles (see _call_editorial_model's docstring). Opus needs no reasoning
            # budget for a mechanical rewrite; Fable stays as a last-resort fallback.
            revised = self._call_editorial_model(system, user, max_tokens=6000, timeout=180, prefer_opus=True)
            if revised and len(revised) > max(400, len(article_body) * 0.6):
                self.logger.info("Fable polish rewrite: %d chars", len(revised))
                return revised
            self.logger.warning("Fable polish rewrite returned too little content — falling back to Opus")
        except Exception as e:
            self.logger.warning("Fable polish rewrite failed: %s — falling back to Opus", e)
        return self._opus_targeted_revision(article_body, editorial_notes, agent_name)

    def _fable_update_state(self, agent_name, article_title, article_body):
        """Post-publish: Fable reads the article and updates the persona's state.json.

        Called after a successful publish. Non-blocking — failure is logged and ignored.
        """
        import json as _j
        current = self._load_persona_state(agent_name)
        system = (
            "You are the state-keeper for an AI editorial persona. "
            "You have just read an article this persona published. "
            "Update their living state based on what the article reveals about their current preoccupations."
        )
        user = (
            f"Persona: {agent_name}\n"
            f"Article title: {article_title}\n\n"
            f"Article body (first 2000 chars):\n{article_body[:2000]}\n\n"
            f"Current state:\n{_j.dumps(current, indent=2)}\n\n"
            "Update the state based on this article. Rules:\n"
            "- obsessions: max 5 items — add new, drop stale, keep persistent ones\n"
            "- unresolved_questions: max 3 — update if the article opened or closed a question\n"
            "- ongoing_arguments: keep existing unless this article resolves one; add new if article creates one\n"
            "- claims_on_record: if the article makes a specific falsifiable claim, add it as "
            '{"claim":"...","article":"slug","date":"YYYY-MM-DD"}; otherwise leave unchanged\n'
            "- recent_mood: one phrase that captures the emotional register of this article\n"
            "- last_updated: today's date YYYY-MM-DD\n\n"
            "Reply with the complete updated state JSON only — no other text."
        )
        raw = self._call_editorial_model(system, user, max_tokens=2600, timeout=60)
        if raw is None:
            self.logger.error("Fable state update for %s: all models failed — persona state will not evolve from this article", agent_name)
            return
        try:
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
            updated = _j.loads(raw)
            # Validate structure before saving
            required = {"obsessions", "unresolved_questions", "ongoing_arguments",
                        "claims_on_record", "recent_mood", "last_updated"}
            if required.issubset(updated.keys()):
                self._save_persona_state(agent_name, updated)
                self.logger.info("State updated for %s — mood: %s", agent_name, updated.get("recent_mood", "?"))
            else:
                self.logger.warning("Fable state update: invalid schema — not saved")
        except Exception as e:
            self.logger.error("Fable state update parse failed for %s: %s — persona state will not evolve from this article", agent_name, e)

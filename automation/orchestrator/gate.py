"""
gate.py — the pre-commit gate and its deterministic (non-LLM) checks.

Extracted 2026-08-09 (module-split, Stage 3 continued). This is the file that
runs BEFORE an article gets written to disk — the one check in the whole
pipeline that can still stop something bad from shipping. Grouped together:
_check_article_type_compliance (word-count caps/floors, portrait-subject rule),
four deterministic regex/statistics checks (buried-clause sentences, argument-
word overuse, sentence-length distribution, rule-verdict parsing), the gate
itself (_pre_commit_gate — readability + LLM rule check + surgical fix), and
_readability_score (Flesch-Kincaid, also used by validate_article for the
same threshold). Zero behavior change -- bodies copied verbatim, confirmed via
direct substring containment against git HEAD.

NOTE for the parallel style-rules convergence work (see automation/style_rules.py
and check_rule_drift.py): GATE_SYSTEM's rule text lives inside _pre_commit_gate
below, unchanged by this move. This file is the natural eventual home for
wiring style_rules.render_gate() in, once that migration is far enough along —
not done as part of this extraction, which is a pure relocation.
"""
import re

from .config import CLIPROXY_URL, CLIPROXY_KEY


class GateMixin:
    def _check_article_type_compliance(self, content, article_type):
        """Check a draft against its assigned article_type's form rules.

        Word-count caps/floors are checked in plain Python (exact, free — LLMs count
        words unreliably). The portrait/series_part 'one real named person as sustained
        subject' rule needs semantic judgment, so that one check uses Opus specifically
        (matching the crontab's original 'opus rewrite pass' naming — this is what that
        was meant to be before it was never actually wired up).

        Returns a list of violation strings (empty if compliant).
        """
        violations = []
        word_count = len(re.findall(r"\S+", content))

        if article_type == "field_note" and word_count > 500:
            violations.append(
                f"WORD CAP — field_note must be ≤500 words, this is {word_count}. Cut it down."
            )
        elif article_type in {"portrait", "series_part"} and word_count < 1200:
            violations.append(
                f"WORD MINIMUM — {article_type} must be ≥1200 words, this is only {word_count}. Expand it."
            )

        if article_type == "portrait":
            SUBJECT_SYSTEM = (
                "You are a strict editor checking whether an article actually delivers "
                "on its assigned form: a PORTRAIT, which requires ONE real, named, "
                "external person as the sustained subject throughout — not a source "
                "citation in passing, and not a fellow staff writer at this publication "
                "(Pixel Nova, Siri Sage, Maya Flux, Zen Circuit are personas of this same "
                "publication — citing one of them as a disagreement or reference point "
                "does not count as a portrait subject).\n\n"
                "Reply with exactly one line: either 'PASS' or "
                "'FAIL: <one sentence reason>'."
            )
            try:
                verdict = self._call_openai_compat_api(
                    url=CLIPROXY_URL, api_key=CLIPROXY_KEY,
                    system_prompt=SUBJECT_SYSTEM, user_prompt=content,
                    model="openrouter/claude-opus-4.8", max_tokens=100, timeout=60,
                )
                if verdict.strip().upper().startswith("FAIL"):
                    violations.append(f"SUSTAINED SUBJECT — {verdict.strip()}")
            except Exception as e:
                self.logger.warning("Portrait subject check failed: %s", e)

        return violations

    @staticmethod
    def _check_buried_clause_sentences(content):
        """Deterministic (no LLM) check for a specific delayed-main-verb shape:
        '<subject> as a/an <noun phrase> that/which/who <clause>, <rest of sentence>'.

        Naming the subject in the first few words (what R6/R7 already check) is not
        the same as reaching the verb quickly — a real published example passed R6/R7
        cleanly while still needing a reread: 'The eye as an organ that some of us
        route the whole world through gets a footnote' names its subject ('The eye')
        in word 2, then wedges a 9-word appositive-relative clause before the verb
        ('gets') ever arrives. This is a narrow, specific construction ('X as a/an Y
        that/which/who Z, <still more sentence>') that is cheap and reliable to catch
        with a regex — unlike a general 'is this sentence hard to read' judgment,
        which is why R6/R7/R14's LLM checks miss it: none of them test the distance
        from subject to verb, only whether a clause precedes the subject (R6/R7) or
        whether the whole sentence is abstractly compressed (R14).

        Returns a list of the offending sentences (empty if none).
        """
        text = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        pattern = re.compile(
            r'\bas\s+(?:a|an)\s+(?:\w+\s+){1,6}?(?:that|which|who)\b',
            re.IGNORECASE,
        )
        hits = []
        for s in sentences:
            m = pattern.search(s)
            if not m:
                continue
            # Words left after the relative-clause opener to the end of the sentence.
            # A short tail means the clause was the sentence's last constituent (fine,
            # nothing left waiting behind it); a long tail means a main verb and more
            # is still pending past the buried clause — the actual defect.
            tail_words = re.findall(r"[A-Za-z']+", s[m.end():])
            if len(tail_words) >= 4:
                hits.append(s.strip())
        return hits

    @staticmethod
    def _check_argument_word_overuse(content):
        """Deterministic count of self-referential 'argument'/'arguments' — a real,
        corpus-confirmed tic (119 uses across 63 of 138 published articles, 2026-08-07
        audit) naming the essay's own rhetorical machinery instead of just making the
        point. Near-zero tolerance: flag if the word appears at all. Returns a list of
        the offending sentences (empty if none)."""
        text = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if re.search(r"\bargument[s]?\b", s, re.IGNORECASE)]

    @staticmethod
    def _check_sentence_length_distribution(content):
        """Deterministic check for suspiciously uniform sentence-length rhythm — a
        different axis from every other check here (pattern-matching vs. distribution-
        matching). Real baseline measured 2026-08-07 against 919 sentences across three
        full Bregman books (Het water komt, De geschiedenis van de vooruitgang, Gratis
        geld voor iedereen): mean 16.6 words, stdev 12.6, with roughly a quarter of all
        sentences at 8 words or fewer and under 4% over 45 words. Every real sample
        checked showed real variance — no real Bregman text was flat. This flags the
        opposite failure: a draft where every sentence runs roughly the same length,
        which reads as monotone regardless of what any individual sentence says.
        Small-sample noise means thresholds here are deliberately loose — only flags
        genuinely flat rhythm, not minor deviation from the aggregate. Returns a list
        of violation strings (empty if none)."""
        text = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if len(s.strip()) > 3]
        lengths = [len(re.findall(r"[A-Za-z']+", s)) for s in sentences]
        lengths = [l for l in lengths if l >= 2]
        if len(lengths) < 8:
            return []  # too few sentences for distribution stats to mean anything
        n = len(lengths)
        mean = sum(lengths) / n
        variance = sum((l - mean) ** 2 for l in lengths) / n
        stdev = variance ** 0.5
        short_pct = sum(1 for l in lengths if l <= 8) / n
        violations = []
        if stdev < 5:
            violations.append(
                f"sentence-length stdev is {stdev:.1f} across {n} sentences (real Bregman "
                f"baseline: ~12.6) — sentences are running suspiciously uniform in length"
            )
        if short_pct == 0 and n >= 15:
            violations.append(
                f"zero sentences at 8 words or fewer across {n} sentences (real baseline: "
                f"~24%) — no short punch sentences anywhere in the piece"
            )
        if mean > 26:
            violations.append(
                f"average sentence length is {mean:.1f} words (real Bregman texts measured "
                f"14.1-19.2) — sentences are running long throughout"
            )
        return violations

    # The fixed rule set GATE_SYSTEM asks the model to evaluate (R1..R17,
    # see the prompt text in _pre_commit_gate below) — used by
    # _missing_rule_ids to detect a rule that never got a recognized
    # verdict at all, as opposed to one that was explicitly judged PASS.
    _EXPECTED_GATE_RULE_IDS = frozenset(f"R{i}" for i in range(1, 18))

    @staticmethod
    def _parse_rule_verdicts(raw):
        """Last verdict per rule id wins. The rule-checker model (Sonnet 4.6) sometimes
        emits reasoning inside a [FAIL] line and then reverses itself on the next line
        ('[FAIL] R3 — ...none found with certainty' / '[PASS] R3') — a naive
        startswith("[FAIL]") scan counted both, which made the pre-commit gate fire on
        every article regardless of actual violations (automation.log, 2026-08-02..06)."""
        verdicts = {}
        for line in (raw or "").splitlines():
            m = re.match(r"\[(FAIL|PASS|N/A)\]\s*(R\d+)", line.strip())
            if m:
                verdicts[m.group(2)] = (m.group(1), line)
        return [line for status, line in verdicts.values() if status == "FAIL"]

    @classmethod
    def _missing_rule_ids(cls, raw, expected=None):
        """Which of the expected rule ids never appear with a recognized
        [FAIL|PASS|N/A] verdict anywhere in raw — added 2026-08-14 (A-M
        reconciliation, item I). A rule the model silently skips (truncated
        response, malformed line, or simply omitted) previously contributed
        NEITHER a PASS nor a FAIL to _parse_rule_verdicts's own violations
        list — indistinguishable from that rule having passed. This function
        does not change _parse_rule_verdicts's own return shape (still just
        the FAIL lines, so existing snapshot fixtures stay byte-identical);
        it is a separate, additive completeness check callers must consult
        themselves. Duplicate rule mentions, unrecognized extra rule ids
        (RBC/RAW/RSD, or a stray R99), and PASS/N/A verdicts are all handled
        correctly by construction: this only ever looks at which of
        `expected`'s OWN ids were seen, never at what else was in the text."""
        if expected is None:
            expected = cls._EXPECTED_GATE_RULE_IDS
        seen = set()
        for line in (raw or "").splitlines():
            m = re.match(r"\[(FAIL|PASS|N/A)\]\s*(R\d+)", line.strip())
            if m:
                seen.add(m.group(2))
        return frozenset(expected) - seen

    def _pre_commit_gate(self, content, article_file, article_type=None):
        """Pre-commit loop: readability + mechanical rule check + article_type
        compliance → surgical fix if needed. Max 1 iteration. Returns (content, changed)."""
        import os, re

        scores = self._readability_score(content)
        if not scores:
            return content, False

        # Trigger 1: readability hard fail. 55 targets Bregman's own measured level
        # (FRE 64.1 on a representative sample) with margin, not a lower bar — the old
        # 48 sat well under Bregman's floor and let harder-than-Bregman outliers through.
        readability_fail = scores["fre"] < 55

        # Trigger 2: mechanical rule violations (fast LLM check, R1-R10 only)
        GATE_SYSTEM = (
            "You are a copy editor. Check this article for mechanical rule violations only. "
            "For each rule below, output one line.\n\n"
            "R1  INLINE DEFINITIONS — term explained mid-sentence via em-dashes or parentheses\n"
            "R2  LATINATE CLUSTERS — 3+ high-syllable Latinate words in one paragraph "
            "(utilise, demonstrate, facilitate, methodology, supplementary, conceptualise, etc.)\n"
            "R3  STACKED MODIFIERS — three adjectives before one noun\n"
            "R4  NOMINALIZATION — an actual verb rewritten as a noun so the actor disappears "
            "('the redesign of the interface' should be 'they redesigned the interface'). "
            "Do NOT flag ordinary nouns that merely end in -tion/-ment/-ance/-ence but were "
            "never a verb in this sentence — 'access', 'government', 'moment', 'experience', "
            "'evidence', 'silence', 'distance', 'argument', 'environment' are just nouns, not "
            "violations. The test: could you name who did the verb? If there's no hidden actor "
            "to free, it isn't a nominalization.\n"
            "R5  VAGUE WE — 'we' with no named referent\n"
            "R6  FRONT-LOADED SENTENCE — long subordinate clause before the subject. "
            "Flag sentences opening with 'When considering...', 'What happens after...', "
            "'Given that...'.\n"
            "R7  LONG PARAGRAPH — more than 5 sentences in one paragraph\n"
            "R8  LONG LIST — 4 or more items in a list, UNLESS the list is deliberately piling up "
            "toward a single payoff/reversal in the sentence right after it (real Bregman example: "
            "nine named items in one sentence, immediately followed by an ironic 'and nothing had "
            "changed' punchline). A long list with no such payoff after it is still a violation.\n"
            "R9  TOO MANY SECTION BREAKS — more than 3 '---' in the body\n"
            "R10 JARGON — institutional words: claimants, non-compliant, stakeholders, outcomes, "
            "intervention, change of circumstances, platform upgrades, priority locations\n"
            "R11 LONG SENTENCE — any single sentence over 30 words\n"
            "R12 CULTURAL STUDIES VOCAB — words that signal academic drift: liminal, embodied, visceral, "
            "resonant (used metaphorically), apparatus, legibility, interrogate (metaphorical), "
            "curated (metaphorical), centering, unpack (metaphorical), navigate (metaphorical), "
            "negotiate (metaphorical), uplift, foregrounding, praxis, positionality\n"
            "R13 RHYTHMIC MONOTONY — 3 or more consecutive sentences opening with the same word "
            "or the same grammatical pattern (e.g. 'The X...', 'The X...', 'The X...' "
            "or 'It was...', 'It was...', 'It was...'). EXCEPTION — checked directly against "
            "real Bregman prose, which does this deliberately: a short, tight run of 2-3 "
            "sentences that repeats its opening word specifically to build escalating emphasis "
            "toward one point ('Never before did so many young people see a therapist. Never "
            "before did so many young workers burn out. Never before were so many "
            "antidepressants prescribed.') is a real device (anaphora), not a monotony tic. "
            "Only flag the pattern when it runs LONGER than 3 sentences, or when the repeated "
            "opener is not building toward a single escalating point (i.e. it reads as an "
            "unintentional habit rather than a deliberate rhetorical build).\n"
            "R14 SUBJECT-VERB DISTANCE — the subject is named early (so R6 alone would pass it) "
            "but a long appositive or relative clause — 'as a/an X that/which/who...', or a "
            "comma- or em-dash-set-off descriptor — is wedged between the subject and its main "
            "verb, forcing the reader to hold the subject in memory across the detour. Example "
            "violation: 'The eye as an organ that some of us route the whole world through gets "
            "a footnote' — 'The eye' is the subject, but 'gets' doesn't land until 12 words "
            "later. Do NOT flag a short appositive (3-4 words) that barely delays the verb, and "
            "do NOT flag a relative clause that IS the sentence's last constituent with nothing "
            "waiting behind it.\n"
            "R15 CRAFTED RHETORIC — flag any of these literary devices, even when the sentence "
            "is otherwise grammatical and plain-worded (real Bregman prose, checked directly "
            "against his published work, essentially never does any of these): "
            "(a) METAPHOR FOR MECHANISM — a figurative image standing in for a plain mechanical "
            "fact ('it grabs the eye before the brain gets a vote', 'the same banner turns into "
            "a magnet for the eye') — state the mechanism directly instead. EXEMPT: a metaphor "
            "inside a real, attributed quote from a named source (real Bregman example: a "
            "biblical image inside a real person's own letter — 'not one camel, but a whole herd "
            "of elephants went through the eye of the needle', quoted, not the narrator's own "
            "line). Authentic reported speech is not the same violation as the narrator reaching "
            "for an invented image in their own voice; only flag figurative language when it is "
            "the writer's own, unattributed description of a mechanism; "
            "(b) MIRRORED/CLEFT SENTENCE — a symmetrical construction built for cleverness rather "
            "than genuine correction: 'X is what... Y is what...', 'one wants X, the other wants "
            "Y', or the SAME grammatical frame reused identically for two different subjects in a "
            "row ('the size rule that helps me read the ad is the same size rule that sells the "
            "ad'). Do NOT flag a genuine 'not X, but Y' correction that replaces a real "
            "misconception with the actual explanation once — that is the REDEFINE technique "
            "(protected elsewhere: 'not X, but Y', 'the problem is not X, it is Y'), and real "
            "Bregman prose uses it plainly. Only flag when the mirrored template repeats within "
            "one piece, or when both halves are built for symmetry rather than to state a "
            "correction; "
            "(c) APHORISTIC OR IRONIC CLOSER — a paragraph or piece ending on a crafted twist or "
            "epigram ('that's the trap: the fix for exclusion and the tool for manipulation "
            "turned out to be the same X') rather than a plain fact, a quote, or a concrete "
            "narrative beat; "
            "(d) SUSTAINED WORDPLAY — punning or reusing one word for cleverness across "
            "consecutive sentences ('pop is blind to who it's popping for'); "
            "(e) NAMED ABSTRACT FRAMEWORK AS AGENT — treating a coined category or discipline "
            "as if it acts ('persuasion design wants...', 'clear print rules and persuasion "
            "design want the same thing') instead of naming the concrete object (a banner, a "
            "leaflet, a shop); "
            "(f) INANIMATE OBJECT AS DELIBERATE AGENT — giving a building, a drawing, a render, "
            "a document, or a physical material or surface (a fold, a fabric, the ground, a "
            "pleat) deliberate intent, memory, or care it cannot have ('a building has decided "
            "that its meaning is...', 'the drawings were dismantling my argument', 'the fold "
            "does not remember the hand', 'a promise the ground makes') — say who actually did "
            "it: the architect decided, I concluded from the drawings, the person who folded it. "
            "Do NOT flag a plain, unadorned comparison stated once and dropped "
            "('the room reads it like a spreadsheet') — only flag when the device is doing "
            "rhetorical work (symmetry, a twist, a pun, or false agency) rather than just naming a thing.\n\n"
            "R16 ONE IDEA PER SENTENCE — a sentence folds two or more separate claims together via "
            "a relative clause, an inserted aside, and/or a complement clause, often stacked with "
            "'and that'. Real published example of the failure: 'A building whose entire public "
            "character is a colour scheme has decided, before the concrete is poured, that its "
            "meaning is a thing you receive with the eyes.' That folds three separate ideas — (1) "
            "the building's public character is a colour scheme, (2) that's a decision made before "
            "construction, (3) meaning arrives through the eyes — into one sentence. A sentence can "
            "be grammatically plain-worded and still fail this way — check idea count, not just "
            "vocabulary. Do NOT flag a sentence with one main claim plus a short supporting detail "
            "that doesn't stand as its own separate assertion.\n\n"
            "R17 SYSTEM VOICE — passive or bureaucratic-noun construction that erases who did the "
            "thing. Test every sentence: who is doing what to whom? 'Stops were flagged as "
            "non-compliant' has no person — flag it. 'The intervention was implemented' → 'The "
            "council installed a ramp.' 'Access needs were assessed' → 'A caseworker asked what "
            "you needed.' If the sentence could appear in the audit report the article is "
            "criticising, it has failed.\n\n"
            "Format: [FAIL] R1 — \"quoted phrase\" | [PASS] R2 | [N/A] R9\n"
            "Be strict. Quote the exact offending phrase. Max 15 words per quote."
        )
        violations = []
        gate_llm_ok = True
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=GATE_SYSTEM,
                user_prompt=content,
                model="openrouter/claude-sonnet-4.6",
                max_tokens=1010,  # was 400 — a rule-verdict list at ~25+ tokens/rule plus
                                 # preamble routinely truncated before the tail rules, and
                                 # truncation was indistinguishable from "passed" to the
                                 # parser. Bumped again 2026-08-09 when R16 was added —
                                 # keep this ahead of R-count * ~25 + ~150 preamble.
                timeout=45,
                # Added 2026-08-14 (A-M reconciliation, item I): this call was the one
                # remaining production caller of _call_openai_compat_api NOT already
                # opted into the truncation-detection llm.py added 2026-08-10 (see that
                # function's own docstring) — a response cut off by max_tokens raises
                # here instead of silently returning a partial rule list. Reuses
                # already-proven code (llm.py:486/673/1251), zero new mechanism.
                check_truncation=True,
            )
            violations = self._parse_rule_verdicts(raw)
            # Added 2026-08-14 (A-M reconciliation, item I): check_truncation above only
            # catches the API's OWN finish_reason report — this catches every other way a
            # rule can end up silently absent (a model that stops mid-list without the
            # provider reporting truncation, a malformed/unparseable line for one rule,
            # any other omission) by checking directly whether every expected rule id got
            # a recognized verdict at all, not just whether the ones that did were FAIL.
            missing_rules = self._missing_rule_ids(raw)
            if missing_rules:
                gate_llm_ok = False
                self.logger.error(
                    "Pre-commit gate LLM rule-check response is INCOMPLETE — expected "
                    "rule(s) %s never received a recognized [FAIL|PASS|N/A] verdict "
                    "(response omitted them without the API reporting truncation). "
                    "Mechanical rule violations for those rules are UNKNOWN, not zero.",
                    ", ".join(sorted(missing_rules)),
                )
                if hasattr(self, "_degraded_stages"):
                    self._degraded_stages.append("gate_llm")
        except Exception as e:
            # Added 2026-08-10 after a confirmed live incident: this call 403'd, the
            # except left violations=[], and the code below logged a bare
            # "Pre-commit gate: PASS" -- indistinguishable from a real clean pass on
            # a 2530-word article that shipped with a fabricated quote and a banned
            # thesis-restatement ending. gate_llm_ok=False makes that state visible
            # to the log line below and to the caller's pipeline_degraded stamp,
            # instead of silently reading as "checked, passed."
            gate_llm_ok = False
            self.logger.error("Pre-commit gate LLM rule-check call FAILED (violations unknown, not zero): %s", e)
            if hasattr(self, "_degraded_stages"):
                self._degraded_stages.append("gate_llm")

        # Trigger 2b: buried-clause sentences (deterministic, R15 — see
        # _check_buried_clause_sentences docstring). Folded into the same violations
        # list/3-vote threshold as the LLM rule check, not a hard-fail on its own —
        # kept consistent with how the LLM violations are weighted, but unlike them
        # this signal has zero false-positive risk from model sampling/truncation.
        buried_clause_hits = self._check_buried_clause_sentences(content)
        if buried_clause_hits:
            violations.extend(
                f'[FAIL] RBC — buried clause delays main verb: "{h[:100]}"'
                for h in buried_clause_hits
            )

        argument_hits = self._check_argument_word_overuse(content)
        if argument_hits:
            violations.extend(
                f'[FAIL] RAW — self-referential "argument": "{h[:100]}"'
                for h in argument_hits
            )

        length_dist_hits = self._check_sentence_length_distribution(content)
        if length_dist_hits:
            violations.extend(f'[FAIL] RSD — {h}' for h in length_dist_hits)

        # Opening-paragraph escalation, added 2026-08-09: a register violation
        # (crafted rhetoric, buried clause, etc.) in the article's OPENING
        # PARAGRAPH is far more damaging than the same violation on page 2 --
        # it's the first thing every reader sees, and the brief-generation
        # prompt elsewhere in this file already treats the opening as a
        # specially-engineered spot worth its own instructions. The >=3-total
        # threshold below assumes a single register hit is forgivable
        # stylistic color; that assumption breaks exactly here. Confirmed
        # live 2026-08-09: "A ramp is a promise the ground makes" -- a
        # textbook R15(a) metaphor-for-mechanism violation -- was the
        # article's own opening sentence, was correctly caught by this exact
        # LLM check, and still shipped unfixed because it was the piece's
        # ONLY register violation (count=1, below the >=3 bar). The reader
        # who flagged it caught it immediately; the gate built to catch this
        # didn't, because a hit in sentence one was never weighted any
        # differently from a hit in paragraph eight.
        opening_para = content.strip().split("\n\n", 1)[0]
        opening_register_hit = False
        for v in violations:
            if not any(f"] {p}" in v or f"]  {p}" in v for p in ("R14", "R15", "RBC", "RAW", "RSD")):
                continue
            m = re.search(r'"([^"]{3,150})"', v)
            if m and m.group(1)[:60] in opening_para:
                opening_register_hit = True
                break

        rule_fail = len(violations) >= 3 or opening_register_hit

        # Trigger 3: article_type compliance (word cap/floor + portrait subject rule).
        # Always fails the gate on its own — this is a hard requirement, not one vote
        # among many, unlike the style rules above which need 3+ to matter.
        type_violations = self._check_article_type_compliance(content, article_type) if article_type else []
        type_fail = bool(type_violations)

        if not readability_fail and not rule_fail and not type_fail:
            if gate_llm_ok:
                self.logger.info("Pre-commit gate: PASS (FRE=%.1f, violations=%d)", scores["fre"], len(violations))
            else:
                # Deliberately not "PASS" in any form -- deterministic checks (readability,
                # article-type) came back clean, but the LLM rule check never ran, so
                # mechanical rule violations are UNKNOWN, not zero. "gate_llm" is already
                # in self._degraded_stages (appended above); generate.py's promotion-block
                # logic reads that, not this return value -- this log line only has to
                # stop a human skimming it from reading "PASS" as "checked and clean."
                self.logger.error(
                    "Pre-commit gate: INCOMPLETE — deterministic checks passed, but the LLM "
                    "rule check FAILED and did not run (FRE=%.1f). Mechanical rule violations "
                    "are UNKNOWN, not zero.", scores["fre"]
                )
            return content, False

        self.logger.info(
            "Pre-commit gate: FAIL (FRE=%.1f, violations=%d [%d buried-clause], "
            "opening_hit=%s, type_violations=%d) — running surgical fix",
            scores["fre"], len(violations), len(buried_clause_hits), opening_register_hit, len(type_violations)
        )

        # Register violations (RBC, R14, R15) are pervasive-register symptoms, not
        # isolated errors — validated 2026-08-07: a real test generated 3 full articles,
        # ran them through this exact gate, applied the surgical fix, and rejudged
        # against real Bregman excerpts. All 3 still failed afterward (13-15 remaining
        # issues each, barely down from 15-24 pre-fix) because a "patch only the quoted
        # phrase, change nothing else" fix cannot touch a whole-document habit — nearly
        # every paragraph landing on a crafted epigram, or citing 4-5 named figures where
        # Bregman uses at most one. Any single register violation gets a full rewrite
        # pass instead of a per-quote patch; mechanical-only violations (jargon, passive
        # voice, nominalization — genuinely isolated, patchable spots) keep the narrow
        # surgical fix unchanged.
        register_prefixes = ("R14", "R15", "RBC", "RAW", "RSD")
        register_violations = [v for v in violations if any(f"] {p}" in v or f"]  {p}" in v for p in register_prefixes)]
        mechanical_violations = [v for v in violations if v not in register_violations]
        register_rewrite_needed = bool(register_violations)

        fix_lines = []
        if readability_fail:
            fix_lines.append(
                f"- Flesch Reading Ease is {scores['fre']} (target ≥ 55). "
                "Swap Latinate words for shorter Anglo-Saxon equivalents where meaning is identical. "
                "Do not change proper nouns or topic-essential technical terms."
            )
        for v in mechanical_violations[:6]:
            fix_lines.append(f"- Fix: {v[7:]}")
        for v in register_violations:
            fix_lines.append(f"- Fix: {v[7:]}")
        for v in type_violations:
            fix_lines.append(f"- Fix: {v}")

        if register_rewrite_needed:
            FIX_SYSTEM = (
                "You are revising a published article to fix its overall register — this is a "
                "whole-piece problem, not a handful of isolated bad sentences, so you may "
                "restructure sentences and paragraphs as needed. The specific violations listed "
                "below are symptoms; fix the underlying habit everywhere it appears in the "
                "piece, not just in the quoted examples. Concretely: (1) if paragraphs tend to "
                "land on a crafted epigram or twist, rewrite those endings as plain facts, real "
                "quotes, or concrete narrative beats instead — check every paragraph, not just "
                "the ones quoted below; (2) if the piece names more than 2 real people/figures, "
                "cut it back to at most 2, keeping whichever carry the most argumentative "
                "weight; (3) if sentences run long with a subject held apart from its verb by a "
                "relative clause or appositive, split them into shorter sentences with subject "
                "and verb close together; (4) cut any metaphor standing in for a plain mechanical "
                "fact — state the mechanism directly. Keep the persona's voice, the core "
                "argument, the real named sources, and the facts intact — this governs sentence "
                "construction and paragraph rhythm, not the substance. "
                "Return the complete article with the fix applied throughout. "
                "No commentary, no preamble."
            )
        elif type_violations:
            FIX_SYSTEM = (
                "You are a copy editor bringing a published article into compliance with "
                "its assigned form. Fix the specific issues listed below — this may require "
                "cutting length, expanding length, or restructuring around a single named "
                "subject, as instructed. Keep the voice, persona, and core argument intact "
                "wherever the fix doesn't require changing them. "
                "Return the complete article with the fixes applied. "
                "No commentary, no preamble."
            )
        else:
            FIX_SYSTEM = (
                "You are a copy editor making surgical fixes to a published article. "
                "Fix ONLY the specific issues listed below. "
                "Change nothing else — not the structure, not the argument, not the voice, not the examples. "
                "Return the complete article with only those changes applied. "
                "No commentary, no preamble."
            )
        fix_prompt = "ISSUES TO FIX:\n" + "\n".join(fix_lines) + "\n\nARTICLE:\n" + content

        try:
            fixed = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=FIX_SYSTEM,
                user_prompt=fix_prompt,
                model="openrouter/claude-sonnet-4.6",
                max_tokens=5000,
                timeout=120,
            )
            if not fixed or len(fixed) < len(content) * 0.7:
                self.logger.warning("Surgical fix returned too little content — discarding")
                return content, False

            # Verify the fix actually resolved what it was meant to fix. Readability
            # improvement is the bar for style-rule fixes; for type_violations, a
            # word-count/structural fix might not move FRE at all — check compliance
            # directly instead of gating solely on readability. For register rewrites,
            # Flesch Reading Ease doesn't measure any of the target violations (mirrored
            # sentences, citation density, aphoristic closers are invisible to a
            # syllable-count metric) — requiring FRE to improve would reject a
            # well-executed register fix that legitimately doesn't move that number.
            # Use the free deterministic buried-clause recheck instead: accept if that
            # count didn't increase and FRE didn't get meaningfully worse.
            new_scores = self._readability_score(fixed)
            readability_improved = bool(new_scores and new_scores["fre"] > scores["fre"])
            type_now_compliant = True
            if type_violations:
                remaining = self._check_article_type_compliance(fixed, article_type)
                type_now_compliant = not remaining
                if remaining:
                    self.logger.warning("Surgical fix did not resolve type violations: %s", remaining)
            register_now_better = True
            if register_rewrite_needed:
                remaining_buried = self._check_buried_clause_sentences(fixed)
                readability_not_worse = bool(new_scores and new_scores["fre"] >= scores["fre"] - 3)
                register_now_better = len(remaining_buried) <= len(buried_clause_hits) and readability_not_worse
                if not register_now_better:
                    self.logger.warning(
                        "Register rewrite did not clear the bar (buried_clause %d→%d, FRE %.1f→%s)",
                        len(buried_clause_hits), len(remaining_buried), scores["fre"],
                        new_scores["fre"] if new_scores else "N/A"
                    )

            if readability_improved or (type_violations and type_now_compliant) or (register_rewrite_needed and register_now_better):
                if new_scores:
                    self.logger.info("Surgical fix: FRE %.1f → %.1f", scores["fre"], new_scores["fre"])
                if type_violations:
                    self.logger.info("Surgical fix: type compliance resolved (%s)", article_type)
                # Update article file on disk, if one exists yet — preserve front matter.
                # article_file is None when this gate runs pre-assembly (before
                # generate_images/create_article_file), which is now the normal call
                # order: fixing here on plain content, before images/links/source-note
                # get woven in by create_article_file, means there is no later file
                # write to overwrite them with content that never saw that enrichment.
                # Previously the gate ran post-assembly and wrote fixed-but-unenriched
                # content straight over the assembled file, silently deleting every
                # body image, injected link, and the source note on every successful fix.
                if article_file is not None:
                    existing = article_file.read_text()
                    fm_end = existing.find('\n---\n', 3)
                    if fm_end != -1:
                        front_matter = existing[:fm_end + 5]  # includes closing ---\n
                        article_file.write_text(front_matter + fixed)
                    else:
                        article_file.write_text(fixed)
                return fixed, True
            else:
                self.logger.info("Surgical fix did not improve readability or resolve type violations — discarding")
                return content, False
        except Exception as e:
            self.logger.warning("Surgical fix failed: %s", e)
            return content, False

    def _readability_score(self, content):
        """Flesch-Kincaid metrics. Returns dict or None."""
        import re
        text = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[*_`#\[\]{}]', '', text)
        text = re.sub(r'---', '', text)
        text = text.strip()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        if not words or not sentences:
            return None
        syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]+', w))) for w in words)
        asl = len(words) / len(sentences)
        asw = syllables / len(words)
        fre  = round(206.835 - (1.015 * asl) - (84.6 * asw), 1)
        fkgl = round((0.39 * asl) + (11.8 * asw) - 15.59, 1)
        return {"fre": fre, "fkgl": fkgl, "asl": round(asl, 1), "words": len(words)}

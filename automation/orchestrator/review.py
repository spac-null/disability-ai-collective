"""
review.py — validate_article, the non-blocking post-publish review pass.

Extracted 2026-08-09 (module-split, Stage 3 continued). Single method, but a
big one (~445 lines): citation check, web fact-check orchestration, persona
cross-cite repair, readability, and the LLM rule check (RULES_SYSTEM), writing
a _reviews/<slug>-review.md sidecar and optionally alerting Telegram. Never
blocks the commit that already happened — this runs after the fact. Zero
behavior change -- body copied verbatim, confirmed via direct substring
containment against git HEAD.
"""
import json
import re
import urllib.request as ureq
from datetime import datetime as dt

from .config import CLIPROXY_URL, CLIPROXY_KEY


class ReviewMixin:
    def _engagement_read(self, content, title, agent_name):
        """A holistic 'would a real reader keep going' read — deliberately NOT a
        mechanical rule check. Every other check in this pipeline (readability,
        jargon, buried clauses, nominalization...) asks 'did this trip a known
        failure pattern.' None of them ask the one question that actually
        determines whether a piece is worth reading: is the underlying
        observation interesting. Added 2026-08-09 per an explicit editorial
        conversation about whether more mechanical rules make writing better —
        conclusion was no: rules are a floor against confirmed failures, not a
        ceiling that produces something worth a stranger's attention. This is a
        first attempt at checking for the ceiling, not the floor.

        Advisory only — logged to the review sidecar, never affects is_clean,
        never blocks. No observation window exists yet for this kind of
        subjective judgment the way there is for the mechanical rules; treat
        its output as a data point to read, not a gate to enforce, until enough
        real output accumulates to know if it's a signal worth acting on."""
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "You are a sharp, busy reader scrolling on your phone. You have no "
                    "obligation to finish anything. You've read a lot of good essays and "
                    "you know good writing when you see it — not because it followed "
                    "rules, but because it made you want to keep going.\n\n"
                    "Read the article below once, the way a real reader would. Then "
                    "answer, briefly, in exactly this format:\n"
                    "VERDICT: would you actually finish this, or stop? If you'd stop, at "
                    "roughly what point, and why?\n"
                    "HOOK: what's the single most interesting, surprising, or true thing "
                    "in this piece — the one observation that earns a stranger's time? If "
                    "there isn't one, say so plainly — do not invent a hook that isn't "
                    "really there.\n"
                    "DRAG: what's the one thing most likely to make a reader put this "
                    "down — not a grammar issue (that's checked elsewhere), a genuine "
                    "'why should I care' problem.\n\n"
                    "Do not evaluate grammar, sentence structure, jargon, or rule "
                    "compliance — all of that is checked elsewhere in this pipeline. Only "
                    "evaluate whether this specific piece is actually worth a stranger's "
                    "attention, the way you'd judge anything you read outside of work."
                ),
                user_prompt=f"Title: {title}\nAuthor persona: {agent_name}\n\n{content[:6000]}",
                model="openrouter/claude-sonnet-4.6",
                max_tokens=300,
                timeout=45,
            )
            return (raw or "").strip() or "(no response)"
        except Exception as e:
            self.logger.warning("Engagement read failed: %s", e)
            return None

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
        title_match = re.search(r'^title:\s*"?([^"\n]+)"?', fm_text_for_agent, re.MULTILINE)
        article_title = title_match.group(1).strip() if title_match else article_file.stem
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

        # ── 1d. Engagement read (advisory, non-mechanical) ─────────────────
        # See _engagement_read's own docstring. Runs on final content, after any
        # persona-crosscite repair above, so it's judging what actually shipped.
        engagement_read = self._engagement_read(content, article_title, current_agent)

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
            "## Engagement Read (advisory — not a rule check, not gated on)",
            "Would a real reader actually finish this? Never blocks, never affects the",
            "status above — logged as a data point, not enforced. See _engagement_read's",
            "docstring in review.py for why this exists.",
            "",
            engagement_read or "(engagement read unavailable this run)",
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

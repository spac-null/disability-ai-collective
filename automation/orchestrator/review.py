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

from .config import CLIPROXY_URL, CLIPROXY_KEY, _ARTICLE_TYPES
from .grounding import evidence_text


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
        real output accumulates to know if it's a signal worth acting on.

        WHOLE-ARTICLE, not sampled (fixed 2026-08-14, A-M reconciliation item
        H): previously truncated to content[:6000] with no explanation on
        record for that number, and no technical reason found for it either —
        the model here (Sonnet 4.6) has a context window several orders of
        magnitude larger than any article this pipeline produces (the longest
        deliberate length bucket, config.py's _LENGTHS 2800-word tier, is
        roughly 16,000 characters). At 6000 characters, this check's own
        VERDICT question ('would you actually finish this, or stop') could
        never see anything past roughly the first 1000-1200 words of a piece —
        for the 2800-word tier specifically (config.py's own '~once every 10
        days' bucket) that's under half the article, silently. A check that
        asks whether a reader would finish the piece needs to have read the
        piece. check_truncation=True added alongside, for the same reason
        gate.py's rule check gained it this pass — a response cut short by
        max_tokens now raises instead of silently returning a partial read."""
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
                user_prompt=f"Title: {title}\nAuthor persona: {agent_name}\n\n{content}",
                model="openrouter/claude-sonnet-4.6",
                max_tokens=300,
                timeout=45,
                check_truncation=True,
            )
            return (raw or "").strip() or "(no response)"
        except Exception as e:
            self.logger.warning("Engagement read failed: %s", e)
            return None

    # ── Shadow checks (2026-08-09 — observation only, do not act on) ──────────
    # These are deterministic checks for rules the writer prompt already states
    # but that NOTHING downstream has ever verified — same class of gap as
    # system-voice/one-idea-per-sentence found earlier this session (see
    # check_rule_drift.py's tracked fixes), except those had confirmed real
    # violations shipping live before being promoted straight to BLOCKING. These
    # don't have that track record yet, so they start here instead: logged to the
    # review sidecar as pure observation, never gating anything. DO NOT promote
    # any of these to ADVISORY-in-the-registry or BLOCKING without at least a
    # 2-week observation window AND documented false-positive data in hand — a
    # session doing that without both is guessing on a live production system.
    # Minimum review date for each check is noted in its own docstring.

    @staticmethod
    def _check_bullet_points_shadow(content):
        """SHADOW MODE, added 2026-08-09 — do not promote before 2026-08-23 at the
        earliest, and only with real false-positive data in hand.

        The writer prompt bans bullet points, numbered lists, and bolded list
        items ("Multiple examples go into accumulation paragraphs") but nothing
        downstream has ever checked for a violation. Deterministic and cheap:
        a line starting with '-'/'*'/'•' followed by a space and content, or a
        number followed by '.'/')' and a space, is a list marker. Markdown
        section breaks ('---' with no trailing space+content) do not match.
        Returns list of offending lines (empty if none)."""
        body = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        hits = []
        for line in body.splitlines():
            stripped = line.strip()
            if re.match(r'^[-*•]\s+\S', stripped) or re.match(r'^\d+[.)]\s+\S', stripped):
                hits.append(stripped[:100])
        return hits

    # These two word lists are copied from the writer prompt's own FORBIDDEN
    # ACADEMIC JARGON / FORBIDDEN CORPORATE-JOURNALESE CLICHÉS bullets
    # (generate.py) — kept here rather than in config.py since they're specific
    # to this shadow check, not shared elsewhere. If the writer prompt's lists
    # change, update both together.
    _SHADOW_ACADEMIC_JARGON = [
        "embodied", "phenomenological", "epistemicide", "neuroqueer",
        "intersectionality", "hegemonic", "ableist", "discourse", "praxis",
        "positionality", "centering", "lived experience", "holding space",
        "unpacking", "at the end of the day", "in the final analysis",
        "it is worth noting", "it is important to remember",
    ]
    _SHADOW_CORPORATE_CLICHES = [
        "tip of the iceberg", "perfect storm", "wake-up call", "game changer",
        "think outside the box", "unprecedented times", "moving forward",
        "at this juncture", "paradigm shift",
    ]

    @staticmethod
    def _check_truncated_ending_shadow(content):
        """SHADOW MODE, added 2026-08-09 — do not promote before 2026-08-23 at the
        earliest, and only with real false-positive data in hand.

        No existing rule bans this; it's a different risk class entirely.
        Several LLM calls in this pipeline (the writer's own generation call,
        rewrite_with_opus, the editorial passes) run under a max_tokens cap —
        if a real article happened to need more room than budgeted, the output
        gets cut off mid-sentence with no error raised anywhere; the truncated
        text just gets published as-is. Checks whether the last non-empty line
        of the article ends in real sentence-final punctuation, after
        stripping trailing markdown wrapping (closing '*'/'_' for emphasis,
        closing quote marks, closing brackets) so a correctly-ended sentence
        inside italics or a quote isn't misread as truncated purely because of
        the wrapping character. Confirmed against 3 real published endings
        (plain prose, and the appended source-note footer, which is itself a
        complete italicized sentence) — all correctly pass. Returns the
        offending tail (up to 150 chars) if the ending looks cut off, else
        None. Known limitation: a piece that deliberately ends on an em-dash
        or ellipsis for effect would be flagged as a false positive — exactly
        the kind of case this observation window exists to surface."""
        body = content.strip()
        if not body:
            return None
        last_line = body.splitlines()[-1].strip()
        cleaned = re.sub(r'[*_"’”)\]]+$', '', last_line).rstrip()
        if cleaned and not re.search(r'[.!?]$', cleaned):
            return last_line[-150:]
        return None

    _SEAM_PHRASES = [
        "as i said", "as i mentioned", "to return to", "returning to",
        "this brings me back", "brings us back", "coming back to",
        "as noted above", "as noted earlier", "here is where i", "here's where i",
        "let me come back", "let me return", "back to the", "again, the",
        "which brings me to", "which brings us to", "as i noted",
    ]

    @classmethod
    def _check_seam_shadow(cls, content):
        """SHADOW MODE, added 2026-08-09 — Stage C of the anchor-architecture
        blueprint (see .claude/audience-engagement-tasklist.md). Do not
        promote before 2026-08-23 at the earliest, and only with real
        false-positive data in hand.

        Deterministic detector for a specific failure mode: a sentence that
        ANNOUNCES a callback to earlier material ('as I said', 'to return
        to', 'this brings me back') instead of just making the callback. This
        is the instrument for a risk identified before it exists in this
        pipeline: if a future anchor/refrain instruction (Stage D/E, not yet
        built) asks the writer to return to something, the predictable
        failure mode is the writer announcing the seam instead of writing
        through it — 'nothing detects that today because nothing has ever
        asked for a return before.' Built now, in shadow, specifically so the
        instrument exists BEFORE the mechanism that could trigger it ships.
        Deliberately narrower than general transition signposting (this
        pipeline's writer prompt already sanctions some transition phrases
        elsewhere — 'Now comes the strange part.' — that is a different,
        allowed device; this check targets only the callback-announcing
        pattern, not transitions in general). Case-insensitive substring
        match. Returns list of matched phrases (empty if none)."""
        body = re.sub(r'^---.*?---', '', content, flags=re.DOTALL).lower()
        return [p for p in cls._SEAM_PHRASES if p in body]

    # Minimal stopword set for _check_repetition_shadow, same style/purpose as
    # generate.py's own _stopwords set (deliberate divergence: kept separate,
    # not shared, since this one is tuned for content-word overlap detection,
    # not keyword-pool generation -- if generate.py's list changes, there is
    # no reason this one must change with it).
    _REPETITION_STOPWORDS = frozenset({
        "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
        "is", "are", "was", "were", "with", "this", "that", "these", "those",
        "from", "by", "as", "it", "its", "not", "but", "how", "why", "what",
        "when", "who", "which", "be", "been", "being", "has", "have", "had",
        "will", "would", "could", "should", "can", "do", "does", "did", "no",
        "so", "than", "then", "there", "their", "they", "them", "he", "she",
        "his", "her", "you", "your", "i", "we", "our", "if", "into", "out",
        "up", "down", "about", "still", "just", "one", "also",
    })

    @classmethod
    def _check_repetition_shadow(cls, content, min_content_words=8, similarity_threshold=0.35):
        """G SHADOW V0, added 2026-08-14 (A-M reconciliation, item G) — SHADOW
        MODE ONLY, same discipline as every other check in this section: do
        not promote before 2026-08-28 at the earliest, and only with real
        false-positive data in hand. This is a CANDIDATE DETECTOR, not a
        verdict — it flags paragraph pairs worth a human or future semantic
        judge's attention, and explicitly does not, and cannot, distinguish:
          BAD    — the same claim restated in cosmetic paraphrase, two
                   paragraphs doing the same argumentative job, or a repeated
                   example with no progression
          NOT BAD — a deliberate refrain, a callback whose meaning has
                   genuinely changed, a necessary reorientation after a
                   correction, or an intentional introduction/conclusion echo
        Telling these apart needs the piece's actual argument, which no
        deterministic lexical measure can read — see this check's own module
        docstring section header for why this stays a candidate list, never
        a fake final verdict. A genuinely semantic repetition judge is future
        work this check exists to gather evidence for, not a stand-in for one.

        Deterministic method: split into paragraphs, extract each paragraph's
        content words (lowercased, alphabetic, stopwords removed via
        _REPETITION_STOPWORDS), skip any paragraph under min_content_words
        (too short to mean anything by overlap alone), then Jaccard-compare
        every remaining pair's content-word sets. A pair at or above
        similarity_threshold is a candidate. The one deterministic exception
        this check DOES encode, because it is common and usually deliberate
        by design rather than a judgment call: the (first, last) paragraph
        pair (introduction/conclusion echo) is never flagged.

        similarity_threshold=0.35 is a first, uncalibrated guess, not a
        validated cutoff — exactly the number this observation window exists
        to inform before any promotion decision. Returns a list of
        {"paragraph_pair": [i, j], "similarity": float (rounded to 2 places),
        "shared_terms": [...] (top 8 by simple frequency-independent overlap,
        for a human to scan quickly, not a ranked/weighted list),
        "reason": str, "shadow_only": True} — empty if none found."""
        body = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        body = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body)  # markdown links -> link text
        body = re.sub(r'<[^>]+>', '', body)  # strip HTML (figure/image blocks)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

        def content_words(paragraph):
            words = re.findall(r"[a-z']+", paragraph.lower())
            return {w for w in words if w not in cls._REPETITION_STOPWORDS and len(w) > 2}

        word_sets = [content_words(p) for p in paragraphs]
        candidates = []
        last_index = len(paragraphs) - 1
        for i in range(len(paragraphs)):
            if len(word_sets[i]) < min_content_words:
                continue
            for j in range(i + 1, len(paragraphs)):
                if (i, j) == (0, last_index):
                    continue  # intro/conclusion echo -- not flagged, see docstring
                if len(word_sets[j]) < min_content_words:
                    continue
                intersection = word_sets[i] & word_sets[j]
                union = word_sets[i] | word_sets[j]
                if not union:
                    continue
                similarity = len(intersection) / len(union)
                if similarity >= similarity_threshold:
                    candidates.append({
                        "paragraph_pair": [i, j],
                        "similarity": round(similarity, 2),
                        "shared_terms": sorted(intersection)[:8],
                        "reason": "high content-word overlap -- candidate only, not a verdict; "
                                  "may be a deliberate refrain, an intentional callback, or "
                                  "necessary reorientation, not restated content",
                        "shadow_only": True,
                    })
        return candidates

    # Absolute word-count contracts for the two article_types gate.py's
    # _check_article_type_compliance already hard-enforces (field_note ≤500,
    # portrait/series_part ≥1200). Mirrored here verbatim, not re-derived, so
    # this shadow check's classification for those two types can never disagree
    # with the real enforcement it does not replace or duplicate authority over.
    _LENGTH_ADHERENCE_ABSOLUTE = {
        "field_note":  {"max": 500},
        "portrait":    {"min": 1200},
        "series_part": {"min": 1200},
    }
    _ARTICLE_TYPE_NAMES = frozenset(t[0] for t in _ARTICLE_TYPES)

    @classmethod
    def _check_length_adherence_shadow(cls, article_type, word_count, target_words):
        """E SHADOW V0, added 2026-08-14 (A-M reconciliation, item E) — SHADOW
        MODE ONLY, same discipline as every other check in this section: do
        not promote before 2026-08-28 at the earliest, and only with real
        false-positive data in hand.

        The reconciliation confirmed a real gap: _LENGTHS draws a continuous
        450-2800 target per run, generate.py tells the writer "arrive early
        rather than late," and nothing downstream ever checks whether the
        final word count actually landed near that target for the dominant
        article_type ("essay", 35% weight) or any of pleasure/fury/confusion/
        indefensible -- only field_note (≤500) and portrait/series_part
        (≥1200) have real deterministic enforcement, in gate.py, unchanged by
        this check and not touched here.

        Two distinct classification paths, not one universal cap:
        - field_note/portrait/series_part: absolute contract from
          _LENGTH_ADHERENCE_ABSOLUTE (the same numbers gate.py already hard-
          enforces) -- IN_RANGE or HARD_DEVIATION, no soft tier, because the
          real rule itself is a binary cap/floor, not a band.
        - every other known article_type: relative to the per-run target_words
          actually drawn for this article (there is no fixed range for these
          types -- target_words is a continuous weighted-random draw, see
          config.py's _LENGTHS) -- IN_RANGE (0.7-1.3x target), SOFT_DEVIATION
          (0.5-0.7x or 1.3-1.6x), HARD_DEVIATION (<0.5x or >1.6x). These
          ratios are a first, uncalibrated guess, not a validated cutoff --
          exactly the number this observation window exists to inform before
          any promotion decision, same as G's similarity_threshold.
        - UNKNOWN_FORMAT: article_type absent, not one of config.py's known
          _ARTICLE_TYPES, or (for the relative path) target_words missing/zero
          -- there is nothing to check adherence against.

        Never raises, never blocks, never feeds _should_block -- this is
        observation only. Returns a dict: {"state": one of the four states
        above, "article_type": ..., "word_count": ..., "target_words": ...,
        "ratio": float or None (relative path only), "shadow_only": True}."""
        result = {
            "article_type": article_type,
            "word_count": word_count,
            "target_words": target_words,
            "ratio": None,
            "shadow_only": True,
        }

        if not article_type or article_type not in cls._ARTICLE_TYPE_NAMES:
            result["state"] = "UNKNOWN_FORMAT"
            return result

        absolute = cls._LENGTH_ADHERENCE_ABSOLUTE.get(article_type)
        if absolute:
            if "max" in absolute and word_count > absolute["max"]:
                result["state"] = "HARD_DEVIATION"
            elif "min" in absolute and word_count < absolute["min"]:
                result["state"] = "HARD_DEVIATION"
            else:
                result["state"] = "IN_RANGE"
            return result

        if not target_words:
            result["state"] = "UNKNOWN_FORMAT"
            return result

        ratio = word_count / target_words
        result["ratio"] = round(ratio, 2)
        if 0.7 <= ratio <= 1.3:
            result["state"] = "IN_RANGE"
        elif 0.5 <= ratio < 0.7 or 1.3 < ratio <= 1.6:
            result["state"] = "SOFT_DEVIATION"
        else:
            result["state"] = "HARD_DEVIATION"
        return result

    @classmethod
    def _check_forbidden_word_lists_shadow(cls, content):
        """SHADOW MODE, added 2026-08-09 — do not promote before 2026-08-23 at the
        earliest, and only with real false-positive data in hand.

        The writer prompt bans two word lists — academic jargon (embodied,
        praxis, positionality, etc.) and corporate/journalese clichés (perfect
        storm, paradigm shift, etc.) — but nothing downstream has ever checked
        for either. Deterministic, case-insensitive substring match. Known
        limitation, exactly why this starts in shadow mode: several terms
        ("centering", "discourse", "unpacking") have legitimate literal uses
        outside the banned register ('centering a lens', 'unpacking a box') —
        a naive substring match cannot distinguish literal from banned-register
        use, which is precisely the false-positive data this observation
        window exists to collect before anyone decides whether this check is
        worth keeping at all. Returns dict {"academic_jargon": [...], "corporate_cliches": [...]}
        of matched terms (empty lists if none)."""
        body = re.sub(r'^---.*?---', '', content, flags=re.DOTALL).lower()
        return {
            "academic_jargon": [t for t in cls._SHADOW_ACADEMIC_JARGON if t in body],
            "corporate_cliches": [t for t in cls._SHADOW_CORPORATE_CLICHES if t in body],
        }

    def _persist_review_signals(self, slug, agent_name, engagement_read,
                                 shadow_bullet_hits, shadow_word_hits, shadow_truncated_ending,
                                 plan_follow_read=None, shadow_seam_hits=None,
                                 pre_rewrite_plan_follow_read=None, shadow_repetition_hits=None,
                                 shadow_length_adherence=None):
        """Log _engagement_read's verdict, the 4 shadow checks' output, and
        (added 2026-08-09, Stage B of the anchor-architecture blueprint)
        _plan_follow_read's verdict, to a queryable table (audience-
        engagement tasklist item 2). Before this, the only record was the
        _reviews/<slug>-review.md sidecar — readable one file at a time, not
        queryable as a pattern ("does Zen Circuit systematically get worse
        engagement-read verdicts than Maya Flux" required opening dozens of
        files by hand). Writes to the same automation/engagement.db that
        engagement_fetch.py writes real reader-engagement data to (GoatCounter/
        GSC/Bluesky/Mastodon/Tumblr) — same file, different table, so a future
        correlation between "did the judge guess this was good" and "did
        readers actually stick around" is a plain JOIN on slug, not a
        cross-database query.

        pre_rewrite_plan_follow_read (added 2026-08-09 continuation, blocker
        #4 fix): the same check's verdict on the pristine first draft, before
        rewrite_with_opus/_fable_polish_rewrite/_pre_commit_gate ran. Stored
        alongside plan_follow_read (the post-rewrite verdict already computed
        above) so a future query can tell "the writer never committed to the
        plan" (both columns agree it failed) apart from "a downstream pass
        undid it" (pre-rewrite says executed, post-rewrite says not) — the
        two failure modes were previously indistinguishable.

        shadow_length_adherence (added 2026-08-14, A-M reconciliation item E):
        the dict returned by _check_length_adherence_shadow -- state, article_type,
        word_count, target_words, ratio. Stored as JSON like the other shadow
        signals, same 2026-08-28 no-promotion discipline.

        Never raises -- a failure here must never affect validate_article's
        own return value or block anything; this is pure logging."""
        import sqlite3
        try:
            db_dir = self.repo_root / "automation"
            db_dir.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_dir / "engagement.db")
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_signals (
                        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                        slug                   TEXT NOT NULL,
                        agent                  TEXT,
                        reviewed_at            TEXT NOT NULL,
                        engagement_verdict     TEXT,
                        shadow_bullet_hits     INTEGER,
                        shadow_academic_jargon TEXT,
                        shadow_corporate_cliches TEXT,
                        shadow_truncated_ending TEXT,
                        UNIQUE(slug, reviewed_at)
                    )
                """)
                # Migration-safe: the table already exists in production from a prior
                # commit without this column. ALTER TABLE ADD COLUMN has no "IF NOT
                # EXISTS" in SQLite -- catch the duplicate-column error instead.
                for _col in ("plan_follow_read TEXT", "shadow_seam_hits TEXT",
                             "pre_rewrite_plan_follow_read TEXT", "shadow_repetition_hits TEXT",
                             "shadow_length_adherence TEXT"):
                    try:
                        conn.execute(f"ALTER TABLE review_signals ADD COLUMN {_col}")
                    except sqlite3.OperationalError:
                        pass  # column already exists
                conn.execute(
                    "INSERT OR REPLACE INTO review_signals "
                    "(slug, agent, reviewed_at, engagement_verdict, shadow_bullet_hits, "
                    "shadow_academic_jargon, shadow_corporate_cliches, shadow_truncated_ending, "
                    "plan_follow_read, shadow_seam_hits, pre_rewrite_plan_follow_read, "
                    "shadow_repetition_hits, shadow_length_adherence) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        slug, agent_name, dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                        engagement_read, len(shadow_bullet_hits),
                        json.dumps(shadow_word_hits.get("academic_jargon", [])),
                        json.dumps(shadow_word_hits.get("corporate_cliches", [])),
                        shadow_truncated_ending, plan_follow_read,
                        json.dumps(shadow_seam_hits or []),
                        pre_rewrite_plan_follow_read,
                        json.dumps(shadow_repetition_hits or []),
                        json.dumps(shadow_length_adherence or {}),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            self.logger.warning("Review-signal persistence failed (non-fatal): %s", e)

    def _load_article_plan(self, slug):
        """Read back the _fable_editorial_brief JSON persisted by
        _persist_article_plan (generate.py) for this slug, if any. Returns the
        most recent plan dict, or None. None is the normal case for any
        article generated before 2026-08-09 (Stage 0 of the anchor-
        architecture blueprint) or whenever the brief itself failed that day —
        _plan_follow_read below must treat every field as N/A when this
        returns None, not skip the check silently in a way that could be
        confused with 'checked and passed'."""
        import sqlite3
        try:
            db_path = self.repo_root / "automation" / "engagement.db"
            if not db_path.exists():
                return None
            conn = sqlite3.connect(db_path)
            try:
                row = conn.execute(
                    "SELECT plan_json FROM article_plans WHERE slug = ? "
                    "ORDER BY planned_at DESC LIMIT 1",
                    (slug,),
                ).fetchone()
            finally:
                conn.close()
            if not row:
                return None
            return json.loads(row[0])
        except Exception as e:
            self.logger.warning("Article-plan lookup failed (non-fatal): %s", e)
            return None

    def _plan_follow_read(self, content, plan):
        """SHADOW MODE, added 2026-08-09 — Stage B of the anchor-architecture
        blueprint (see .claude/audience-engagement-tasklist.md and this
        session's design-agent transcript). Do not promote before real
        calibration data exists (see below) AND a minimum 6-week observation
        window from whenever calibration passes.

        Checks whether commitments _fable_editorial_brief made BEFORE writing
        (opening_shape, correction_moment, resisting_example) were actually
        executed in the finished article. These three fields are fed into the
        writer prompt (generate.py) and have run daily for a long time —
        NOTHING has ever verified any of them before this check. Deliberately
        scoped to these 3 fields only: `anchor`/`anchor_returns`/`refrain`
        don't exist as brief fields yet (that's Stage D, not built).

        CALIBRATION STATUS, stated honestly rather than faked: this check's
        own design calls for hand-labelling 20 real (article, plan) pairs and
        requiring >=80% agreement with a human before trusting any number
        from it. That data does not exist yet — _persist_article_plan
        (generate.py) only started saving real plans today, so there is no
        historical plan data to calibrate against; the fields existed and ran
        for a long time, but their actual outputs were never recorded before
        now. This check ships in shadow now so real (article, plan) pairs
        start accumulating from today's generation runs forward — calibrate
        once ~20 have accumulated, not before. Until then, treat every verdict
        this produces as informal, not evidence for anything.

        Never raises. Returns a string verdict or None on failure — same
        contract as _engagement_read.

        has_plan=False short-circuits to a deterministic N/A answer rather than
        asking the model, added 2026-08-10 after a confirmed real failure: given
        the full article text plus a rubric describing what a real correction/
        resisting moment looks like, the model answered CORRECTION: YES and
        RESISTING: YES -- quoting real passages -- for an article that had NO
        persisted plan at all (the Fable brief failed to parse that run). It
        only obeyed the "answer N/A, do not guess" instruction for
        OPENING_SHAPE, not the other two fields. A check meant to verify
        commitments were kept cannot be trusted if it also happily verifies
        commitments that were never made -- this makes the failure structurally
        impossible instead of asking the model not to do it."""
        if not plan:
            return "CORRECTION: N/A\nRESISTING: N/A\nOPENING_SHAPE: N/A\n(no plan recorded for this article -- not evaluated)"
        try:
            raw = self._call_openai_compat_api(
                url=CLIPROXY_URL,
                api_key=CLIPROXY_KEY,
                system_prompt=(
                    "Before this article was written, an editor committed the writer to "
                    "specific things. You are checking, strictly, whether each one actually "
                    "happened on the page. You are not judging whether the article is good, "
                    "well written, or correct — only whether it did what it said it would do.\n\n"
                    "Be hard to satisfy. A commitment is EXECUTED only if you can quote the "
                    "text that executes it. A commitment the article gestures at, implies, or "
                    "half-does is NOT executed. If unsure, the answer is PARTIAL, not YES.\n\n"
                    "Answer in exactly this format, EXACTLY one line per commitment, nothing "
                    "else. Do not reconsider or output a field a second time -- decide once, "
                    "commit to it, move on. If a decision is close, PARTIAL is always the "
                    "right call, not a reason to write the field twice:\n"
                    "CORRECTION: YES | PARTIAL | NO | N/A — is there a moment, in the past "
                    "tense, before the midpoint, where the writer was wrong, stuck, or "
                    "corrected by something they encountered, shown happening rather than "
                    "stated? Quote it, max 15 words. A last-paragraph hedge is NO.\n"
                    "RESISTING: YES | PARTIAL | NO | N/A — does the committed resisting "
                    "example actually appear, standing unresolved? A hypothetical objection "
                    "the writer voices and then answers is NO.\n"
                    "OPENING_SHAPE: MATCH | MISMATCH | N/A — then, in a few words, the shape "
                    "the article's actual first sentence is (plain claim, cold scene, "
                    "question, fact, declaration of a hunt, or other)."
                ),
                user_prompt=(
                    "WHAT THE EDITOR COMMITTED THE WRITER TO:\n"
                    # Phase 1.6: correction_moment/resisting_example may be either a
                    # legacy flat string (pre-Phase-1.6 rows already in engagement.db)
                    # or the new structured evidence-candidate object -- evidence_text()
                    # handles both and collapses status="not_found" to "" so it falls
                    # through to the N/A default below, same as the old missing/empty-
                    # string case did.
                    f"correction moment: {evidence_text(plan.get('correction_moment')) or '(none committed — answer N/A)'}\n"
                    f"resisting example: {evidence_text(plan.get('resisting_example')) or '(none committed — answer N/A)'}\n"
                    f"opening shape: {plan.get('opening_shape') or '(none committed — answer N/A)'}\n\n"
                    "Anything marked '(none committed...)' is N/A — do not invent a commitment.\n\n"
                    f"THE FINISHED ARTICLE:\n{content[:20000]}"
                ),
                model="openrouter/claude-sonnet-4.6",
                max_tokens=700,  # 300 wasn't enough -- confirmed via a real positive-control
                                 # calibration run 2026-08-09: the model second-guessed itself
                                 # on one field (emitted two lines before settling), burning
                                 # its budget before ever reaching RESISTING/OPENING_SHAPE.
                timeout=60,
            )
            return (raw or "").strip() or "(no response)"
        except Exception as e:
            self.logger.warning("Plan-follow read failed: %s", e)
            return None

    def validate_article(self, content, article_file, slug, target_words=None,
                          pre_rewrite_content=None, article_type=None):
        """Non-blocking review: citations + readability + rule compliance. Never delays commit.

        pre_rewrite_content (added 2026-08-09 continuation, blocker #4 fix
        from .claude/bregman-anchor-corpus.md Section 7): the PRISTINE first
        draft, captured by generate.py before any rewrite/gate pass ran.
        None for any caller that doesn't supply it (e.g. snapshot_test.py) —
        never required, never blocks anything. When given, this method
        checks it against the SAME loaded article_plan used for the final
        verdict below and only pays for a second _plan_follow_read call if
        the draft actually changed and a real plan exists to check against
        — otherwise it reuses the verdict it already computed, so an
        unmodified draft (e.g. an Opus draft the editorial pass approved as-
        is) never costs a duplicate LLM call. Persisting both under the same
        loaded plan (rather than pre-rewrite using generate.py's in-memory
        fable_brief and post-rewrite using a separate DB read, as an earlier
        version of this fix did) is what makes the two verdicts genuinely
        comparable — a regression attributable to a specific stage instead
        of an artifact of comparing against two different plan records.

        article_type (added 2026-08-14, A-M reconciliation item E): the
        picked article_type, if the caller has it, so _check_length_adherence_shadow
        can classify length adherence per-format. None for callers that don't
        supply it (e.g. snapshot_test.py) -- the shadow check reports
        UNKNOWN_FORMAT in that case, never raises, never blocks."""
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
        else:
            # Explicit "verified" (added 2026-08-10), not just the absence of
            # "blocked" -- every live article already passed this gate
            # (publish_best.py skips fact_check_status: blocked drafts), so this
            # is a true, reusable signal for a reader-facing "sources checked"
            # note, not an inferred one that could also mean the check never ran.
            fm_text = article_file.read_text()
            if not re.search(r"^fact_check_status:", fm_text, re.MULTILINE):
                fm_text = re.sub(r"^---\n", "---\nfact_check_status: verified\n", fm_text, count=1)
                article_file.write_text(fm_text)
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

        # Shadow checks — observation only, see the class-level comment above
        # _check_bullet_points_shadow for the rules and the no-promotion guardrail.
        shadow_bullet_hits = self._check_bullet_points_shadow(content)
        shadow_word_hits = self._check_forbidden_word_lists_shadow(content)
        shadow_truncated_ending = self._check_truncated_ending_shadow(content)
        shadow_seam_hits = self._check_seam_shadow(content)
        shadow_repetition_hits = self._check_repetition_shadow(content)
        _length_adherence_word_count = len(re.findall(r"\S+", content))
        shadow_length_adherence = self._check_length_adherence_shadow(
            article_type, _length_adherence_word_count, target_words
        )

        # Stage B of the anchor-architecture blueprint, 2026-08-09 — see
        # _plan_follow_read's own docstring for calibration status (none yet;
        # real (article, plan) pairs only start accumulating from today).
        article_plan = self._load_article_plan(slug)
        plan_follow_read = self._plan_follow_read(content, article_plan)

        # See this method's docstring: only make a second call if the draft
        # actually changed and there's a real plan to re-check it against —
        # otherwise the pre- and post-rewrite verdicts are the same thing.
        pre_rewrite_plan_follow_read = plan_follow_read
        if article_plan and pre_rewrite_content and pre_rewrite_content != content:
            pre_rewrite_plan_follow_read = self._plan_follow_read(pre_rewrite_content, article_plan)

        self._persist_review_signals(slug, current_agent, engagement_read,
                                      shadow_bullet_hits, shadow_word_hits, shadow_truncated_ending,
                                      plan_follow_read, shadow_seam_hits,
                                      pre_rewrite_plan_follow_read=pre_rewrite_plan_follow_read,
                                      shadow_repetition_hits=shadow_repetition_hits,
                                      shadow_length_adherence=shadow_length_adherence)

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
            "R5  SYSTEM VOICE BANNED — passive or bureaucratic-noun construction that erases who "
            "did the thing. Test every sentence: who is doing what to whom? 'Stops were flagged "
            "as non-compliant' has no person — flag it. 'The intervention was implemented' → 'The "
            "council installed a ramp.' 'Access needs were assessed' → 'A caseworker asked what "
            "you needed.' If the sentence could appear in the audit report the article is "
            "criticising, it has failed.\n"
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
            "Do NOT flag a plain, unadorned comparison stated once and dropped ('the room reads "
            "it like a spreadsheet') — only flag when the device is doing rhetorical work "
            "(symmetry, a twist, a pun, or false agency), not just naming a thing.\n\n"
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
            "R18 META-LANGUAGE COMMENTARY — the sentence describes or analyzes how something was "
            "phrased/worded (word frequency, word choice, tone-of-delivery) as its own observation, "
            "rather than the writer simply stating the underlying fact in their own words. "
            "'The word rolling appeared twice, both times as praise' is commentary ABOUT a word "
            "instead of just using the word. Reads as clinical and distancing rather than direct.\n\n"
            "R19 STACKED TEMPORAL CLAUSES — a scene-setting sentence uses two nested subordinate "
            "clauses (typically 'after X and before Y') purely to indicate rough timing, rather "
            "than a flat list or a single clean clause ('after I'd checked my tire pressure and "
            "before I'd finished the plantains'). Hard to parse in one read even when each clause "
            "alone is simple.\n\n"
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
                max_tokens=1110,  # bumped from 1000->1060 when R17 was added, now ->1110 for
                                  # R18/R19 — same truncation risk noted at the GATE_SYSTEM call site.
                timeout=90,
                # Added 2026-08-14 (A-M reconciliation, item I): this call was the other
                # remaining production caller of _call_openai_compat_api not yet opted into
                # llm.py's truncation detection (see gate.py's _pre_commit_gate for the
                # first fix and its own comment) -- a response cut off by max_tokens raises
                # here instead of silently returning a partial R1-R19 rule list.
                check_truncation=True,
            )
            rules_text = raw or ""
            rules_fails = self._parse_rule_verdicts(rules_text)
            # Added 2026-08-14 (A-M reconciliation, item I): this check has its OWN rule
            # set (R1-R19, not gate.py's R1-R17 -- includes R18/R19 above) and, until now,
            # its own independent copy of the exact same invisible-rule gap: a rule the
            # model silently never mentions contributes neither a PASS nor a FAIL to
            # rules_fails, previously indistinguishable from that rule having passed. This
            # check is advisory-only (never blocks the commit, see this file's own module
            # docstring) -- fixing it here does not make review.py newly authoritative, it
            # only stops the CLEAN/FLAGGED report itself from silently mischaracterizing an
            # incomplete rule pass as a complete one.
            expected_review_rule_ids = frozenset(f"R{i}" for i in range(1, 20))  # R1..R19
            missing_review_rules = self._missing_rule_ids(rules_text, expected=expected_review_rule_ids)
            if missing_review_rules:
                line = (
                    f"[FAIL] RULE_CHECK_INCOMPLETE — expected rule(s) "
                    f"{', '.join(sorted(missing_review_rules))} never received a recognized "
                    f"verdict (response omitted them without the API reporting truncation)"
                )
                rules_fails.append(line)
                rules_text = (rules_text or "") + ("\n" if rules_text else "") + line
                self.logger.warning(
                    "Post-publish RULES_SYSTEM check is INCOMPLETE — expected rule(s) %s "
                    "never evaluated; report will show FLAGGED, not CLEAN, for this reason.",
                    ", ".join(sorted(missing_review_rules)),
                )
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
            "## Shadow Checks (observation only, added 2026-08-09 — do not act on before "
            "2026-08-23, and only with real false-positive data)",
            "Deterministic checks for rules the writer prompt states but nothing has ever "
            "verified. Never blocks, never affects the status above.",
            f"- Bullet points / numbered lists in body: {len(shadow_bullet_hits)} found"
            + ("" if not shadow_bullet_hits else " — " + " | ".join(shadow_bullet_hits[:5])),
            f"- Forbidden academic jargon: {len(shadow_word_hits['academic_jargon'])} found"
            + ("" if not shadow_word_hits["academic_jargon"] else " — " + ", ".join(shadow_word_hits["academic_jargon"])),
            f"- Forbidden corporate/journalese clichés: {len(shadow_word_hits['corporate_cliches'])} found"
            + ("" if not shadow_word_hits["corporate_cliches"] else " — " + ", ".join(shadow_word_hits["corporate_cliches"])),
            "- Ending looks truncated: " + ("YES — " + shadow_truncated_ending if shadow_truncated_ending else "no"),
            f"- Seam phrases (announcing a callback instead of just making it): {len(shadow_seam_hits)} found"
            + ("" if not shadow_seam_hits else " — " + ", ".join(shadow_seam_hits)),
            f"- Repetition candidates (G SHADOW V0, added 2026-08-14 — CANDIDATE LIST ONLY, "
            f"not a verdict, see _check_repetition_shadow's own docstring): {len(shadow_repetition_hits)} found"
            + ("" if not shadow_repetition_hits else " — " + " | ".join(
                f"paragraphs {h['paragraph_pair'][0]}&{h['paragraph_pair'][1]} "
                f"(similarity={h['similarity']}, shared: {', '.join(h['shared_terms'][:5])})"
                for h in shadow_repetition_hits[:5]
            )),
            f"- Length adherence (E SHADOW V0, added 2026-08-14 — observation only, "
            f"see _check_length_adherence_shadow's own docstring): "
            f"{shadow_length_adherence.get('state', 'UNKNOWN_FORMAT')}"
            f" ({shadow_length_adherence.get('word_count')} words, "
            f"article_type={shadow_length_adherence.get('article_type')}, "
            f"target={shadow_length_adherence.get('target_words')}"
            + (f", ratio={shadow_length_adherence['ratio']}" if shadow_length_adherence.get('ratio') is not None else "")
            + ")",
            "",
            "## Plan-Follow Read (advisory, added 2026-08-09 — Stage B of the anchor-"
            "architecture blueprint. NO CALIBRATION DATA YET — real (article, plan) pairs "
            "only started accumulating today; treat this verdict as informal until ~20 have "
            "built up and been checked against a human. Never blocks, never affects the "
            "status above.)",
            "Checks whether _fable_editorial_brief's pre-generation commitments "
            "(correction_moment, resisting_example, opening_shape) were actually executed.",
            plan_follow_read or "(plan-follow read unavailable this run, or no plan was "
                                 "recorded for this article)",
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

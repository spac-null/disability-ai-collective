"""
fact_check.py — claim extraction and live web fact-verification.

Extracted 2026-08-09 (module-split, Stage 3 continued). Groups: claim
extraction (_extract_verifiable_claims), live web verification via Perplexity
Sonar (_web_verify_quote, _web_verify_claim — direct OpenRouter calls,
bypassing CLIProxyAPI, see their own docstrings for why), the orchestrating
pass (_run_web_fact_check), the one-shot grounded repair attempt before
hard-blocking a contradicted draft (_attempt_fabrication_repair), and
cross-persona citation accuracy checking (_check_persona_crosscite_accuracy).
Zero behavior change -- bodies copied verbatim, confirmed via direct substring
containment against git HEAD.
"""
import json
import re
import time
import urllib.request

from .config import CLIPROXY_URL, CLIPROXY_KEY, _AGENT_SLUG


# ── strict CURRENT_ENGINE fact-check contract ──────────────────────────────────
# The legacy path swallows an extraction failure and returns [], which makes
# "extraction blew up" indistinguishable from "checked the world, found nothing
# contradicted". That collapse is exactly what let the 2026-08-25 first natural
# CURRENT_ENGINE run stamp fact_check_status: verified on an article whose claim
# extraction had raised `Extra data: line 15 column 1 (char 394)` moments earlier.
# CURRENT_ENGINE therefore uses the strict variant below, which reports extraction
# status and claim count explicitly so the publication-safety bridge can fail closed.
EXTRACTION_OK = "ok"
EXTRACTION_ERROR = "error"


class ClaimExtractionError(ValueError):
    """A provider reply that cannot be read as exactly one claims payload.

    Distinct from "the extractor read the reply and it contained no claims". That
    distinction is the whole point: `{"claims": []}` is a successful extraction of
    zero claims and must reach the bridge as NO_VERIFIABLE_CLAIMS, while an empty,
    truncated, prose-only, malformed or ambiguous reply is an EXTRACTION_ERROR
    because nothing was actually read.
    """


def _scan_json_objects(text: str):
    """Balanced-brace scan for top-level JSON objects. String-literal aware.

    Returns (objects, truncated): the balanced `{...}` regions in order, and whether
    the text ends inside an unclosed one. Braces and quotes inside JSON strings do
    not affect depth, so a claim whose text contains a brace cannot corrupt the scan.
    """
    objs, depth, start = [], 0, None
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            if depth > 0:                      # a quote in surrounding prose is not JSON
                in_str = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                objs.append(text[start:i + 1])
                start = None
    return objs, depth > 0


def parse_claims_payload(raw) -> dict:
    r"""Read ONE claims payload out of a provider reply, or raise. Deterministic.

    Replaces a greedy `\{.*\}` match that ran from the first brace to the last. That
    match had two failure modes, both observed:
      * two JSON objects -- the shape a self-correcting model actually returns -- were
        spanned as one string, so json.loads raised `Extra data` (the 2026-08-25 first
        natural CURRENT_ENGINE run);
      * prose after a single valid object that merely contained a later `}` was
        swallowed into the match, corrupting a reply that was fine.

    Fails closed instead of guessing. It never concatenates objects and never merges
    claims from more than one payload: if the reply carries more than one top-level
    object there is no principled way to know which one the model meant, so that is
    an error, not a choice to be made here.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ClaimExtractionError(
            "empty provider response (type=%s)" % type(raw).__name__)
    objs, truncated = _scan_json_objects(raw)
    if truncated:
        raise ClaimExtractionError(
            "truncated provider response: unterminated JSON object (%d chars)" % len(raw))
    if not objs:
        raise ClaimExtractionError(
            "no JSON object in provider response (%d chars)" % len(raw))
    if len(objs) > 1:
        raise ClaimExtractionError(
            "ambiguous provider response: %d top-level JSON objects; refusing to "
            "guess which one is the claims payload" % len(objs))
    try:
        data = json.loads(objs[0])
    except ValueError as e:
        raise ClaimExtractionError("malformed JSON payload: %s" % e)
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ClaimExtractionError(
            "provider response carries no 'claims' list")
    return data


# ── the publication fact-check budget (2026-09-03) ────────────────────────────
#
# Until PR #56 the strict path truncated to four claims per category and let the
# unchecked remainder pass. #56 stopped the pass; this sets a bound the checker can
# actually meet, and makes exceeding it an explicit outcome rather than a silent one.
#
# 16, from measurement, not preference. Seven production runs with recorded extraction
# counts came in at 0, 1, 5, 8, 13, 13 and 13 claims -- median 8, maximum 13, nothing
# above it. A bound of 12 would have held three otherwise ordinary articles for being
# one claim over; 16 covers every run observed with room above the maximum.
#
# Cost is one call per claim plus one for extraction. Measured across those runs, a
# call takes 2.4-4.9 seconds wall clock, so 17 calls is roughly 65-85 seconds against
# the 30-45 seconds nine calls take today. On a daily 09:00 cron with no competing
# deadline that is affordable, and it needs no batching -- which would have changed
# prompts, response shape, failure coupling and per-claim evidence identity all at
# once, for an article that fits comfortably without it.
FACT_CHECK_MAX_CLAIMS = 16
# The tail, which the per-call timeout alone does not bound: seventeen calls each
# allowed 30 seconds is eight and a half minutes, and before this there was no total
# bound at all. 180s is a little over twice the slowest observed full pass, so a normal
# run never meets it and a stalling provider cannot run the stage indefinitely.
# Exhausting it is a TECHNICAL incomplete, never a partial pass.
FACT_CHECK_TOTAL_SECONDS = 180
# The per-call timeout this stage has always used. Still the ceiling for any one call;
# the total deadline can only ever lower it.
PER_CALL_TIMEOUT = 30
# A call is not STARTED with less than this left. Two reasons, and the second is the
# one that matters: a call given a fraction of a second will fail, and its failure is
# reported as UNVERIFIABLE -- a VERDICT, which does not block, and which would let a
# claim nobody could check contribute to a PASS. Deadline exhaustion has to stay a
# failure to check. Observed calls take 2.4-4.9s, so 5 is the measured floor.
FACT_CHECK_MIN_CALL_SECONDS = 5
MAX_CLAIMS_EXCEEDED = "max_claims_exceeded"
TOTAL_DEADLINE_EXHAUSTED = "total_deadline_exhausted"


class FactCheckMixin:
    def _extract_verifiable_claims_raw(self, content, timeout=PER_CALL_TIMEOUT):
        """Strict extraction: RAISES on provider/parse failure instead of returning [].

        Body is the legacy extraction verbatim; the only difference is that the
        exception is allowed to escape. `_extract_verifiable_claims` keeps the
        historical swallow-and-return-empty behaviour for legacy/advisory callers.

        Cheap extraction pass covering all four categories the (advisory-only,
        LLM-self-report) citation check flags: QUOTE, STUDY, STAT, EVENT. Feeds
        _web_verify_quote (QUOTE) and _web_verify_claim (STUDY/STAT/EVENT) — the
        citation check has no way to know if a claim is real, only whether the
        article names a source for it; these are the steps that actually check.

        Superset of the old _extract_named_quotes (QUOTE-only) — same categories as
        before; the reply is now read by `parse_claims_payload`, which fails closed on
        an unreadable reply instead of letting it look like zero claims.
        """
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
        raw = self._call_openai_compat_api(
            url=CLIPROXY_URL, api_key=CLIPROXY_KEY,
            system_prompt=SYSTEM, user_prompt=content,
            model="openrouter/claude-haiku-4.5",
            max_tokens=900, timeout=timeout, no_think=True,
            # Extraction, not composition. Left unpinned this ran at the provider
            # default (1.0), and the same article returned different claim counts
            # from one call to the next -- which put a publication gate downstream of
            # sampling noise.
            temperature=0,
        )
        data = parse_claims_payload(raw)
        return [
            c for c in data.get("claims", [])
            if c.get("claim") and c.get("type") in ("QUOTE", "STUDY", "STAT", "EVENT")
        ]

    def _extract_verifiable_claims(self, content):
        """LEGACY/ADVISORY wrapper. Unchanged semantics: an extraction failure is
        logged and reported as "no claims found".

        This is safe ONLY for advisory callers, where an empty result downgrades a
        diagnostic. It is NOT safe as publication evidence, because the caller cannot
        tell an empty article from a failed extractor. CURRENT_ENGINE publication
        safety must call `_run_web_fact_check(..., strict=True)` instead.
        """
        try:
            return self._extract_verifiable_claims_raw(content)
        except Exception as e:
            self.logger.warning("Verifiable-claim extraction failed: %s", e)
            return []

    def _web_verify_quote(self, person, quote, timeout=PER_CALL_TIMEOUT):
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
                max_tokens=250, timeout=timeout,
            )
            m = re.search(r"VERDICT:\s*(VERIFIED|UNVERIFIABLE|CONTRADICTED)", raw or "", re.IGNORECASE)
            verdict = m.group(1).upper() if m else "UNVERIFIABLE"
            r = re.search(r"REASON:\s*(.+)", raw or "", re.DOTALL)
            reason = r.group(1).strip()[:220] if r else (raw or "")[:220]
            return verdict, reason
        except Exception as e:
            self.logger.warning("Web verify failed for %s: %s", person, e)
            return "UNVERIFIABLE", f"search failed: {e}"

    def _web_verify_claim(self, claim_type, subject, claim_text,
                          timeout=PER_CALL_TIMEOUT):
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
                max_tokens=250, timeout=timeout,
            )
            m = re.search(r"VERDICT:\s*(VERIFIED|UNVERIFIABLE|CONTRADICTED)", raw or "", re.IGNORECASE)
            verdict = m.group(1).upper() if m else "UNVERIFIABLE"
            r = re.search(r"REASON:\s*(.+)", raw or "", re.DOTALL)
            reason = r.group(1).strip()[:220] if r else (raw or "")[:220]
            return verdict, reason
        except Exception as e:
            self.logger.warning("Web verify failed for %s claim (%s): %s", claim_type, subject, e)
            return "UNVERIFIABLE", f"search failed: {e}"

    def _run_web_fact_check(self, content, claim_cap=4, strict=False,
                            max_claims=None, total_seconds=None,
                            min_call_seconds=None):
        """Extract verifiable claims from content and check each against live web
        search. Used both for the initial pass and to re-verify after a repair
        attempt, so the two runs stay identical in method.

        strict=False (default, LEGACY/ADVISORY) is byte-for-byte the historical
        behaviour, including the returned key set.

        strict=True is the CURRENT_ENGINE publication-safety contract. It adds four
        keys that let a caller distinguish outcomes the legacy shape collapses:
          extraction_status     "ok" | "error"
          extraction_error      provider/parse error string, when status is "error"
          claims_extracted      how many verifiable claims extraction actually yielded
          fact_check_completed  True only when verification ran to completion
        A failed extraction returns extraction_status="error" and does NOT masquerade
        as a clean check. A successful extraction that yields zero claims returns
        extraction_status="ok" with claims_extracted=0 -- also not a pass, because
        nothing was checked against the world. Deciding what those mean for publication
        is the bridge's job (publication_safety_bridge check 9); this method's job is
        to report them truthfully rather than erase them.

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
            # ── per-claim record (2026-09-03) ─────────────────────────────────
            # Twice on 2026-09-03 the publication-safety bridge blocked an article on
            # contradicted=1 and nothing anywhere recorded WHICH claim, or why. The
            # verdict and the reason existed here, in the formatted `lines` and in the
            # claim dicts, and were thrown away one layer up. So they are recorded
            # structurally as well, in the order they were checked.
            #
            # Nothing here decides anything. The blocking lists above are still what
            # the bridge reads, built by the same code from the same verdicts.
            "findings": [],
            # Claims extraction found and the cap did not check. Not a verdict --
            # they were never asked -- but a real thing to know when 13 claims are
            # extracted and 8 are checked.
            "not_checked": [],
        }
        # ── the total wall clock, taken at ENTRY ─────────────────────────────
        # Before extraction, not after: extraction is a provider call like any other,
        # and a deadline that starts once it returns is a deadline the stage can
        # already have overrun by 30 seconds before it begins.
        deadline = None
        min_call = (FACT_CHECK_MIN_CALL_SECONDS if min_call_seconds is None
                    else min_call_seconds)
        if strict:
            deadline = time.monotonic() + (FACT_CHECK_TOTAL_SECONDS
                                           if total_seconds is None else total_seconds)
            result.update({"extraction_status": None, "extraction_error": None,
                           "claims_extracted": 0, "fact_check_completed": False})

        def call_budget():
            """What any one call may be given: its ordinary ceiling, or whatever is
            left of the total, whichever is smaller. The total can only lower it."""
            if deadline is None:
                return PER_CALL_TIMEOUT
            return min(PER_CALL_TIMEOUT, deadline - time.monotonic())

        try:
            if strict:
                try:
                    claims = self._extract_verifiable_claims_raw(
                        content, timeout=max(0.0, call_budget()))
                except Exception as e:
                    # Explicit failure state. Never [] -- see EXTRACTION_ERROR above.
                    self.logger.warning(
                        "Verifiable-claim extraction failed (strict, fail-closed): %s", e)
                    result["extraction_status"] = EXTRACTION_ERROR
                    result["extraction_error"] = str(e)[:300]
                    result["lines"] = ["EXTRACTION_FAILED: %s" % str(e)[:200]]
                    return result
                result["extraction_status"] = EXTRACTION_OK
                result["claims_extracted"] = len(claims)
            else:
                claims = self._extract_verifiable_claims(content)
            if not claims:
                if strict:
                    # Extraction worked and found nothing. Reported honestly; the
                    # bridge treats it as NO_VERIFIABLE_CLAIMS and fails closed.
                    result["lines"] = ["NO_VERIFIABLE_CLAIMS"]
                    result["fact_check_completed"] = True
                return result
            result["lines"] = []
            # ── which claims get checked ─────────────────────────────────────
            # STRICT (the publication contract) checks EVERY extracted claim, or
            # refuses the article. There is no per-category truncation here any more:
            # under the old scheme a fifth quote went unchecked while a fourth
            # statistic was checked, purely because of the category it landed in and
            # the order it was emitted in, and #56 turned that into a hold rather than
            # a pass. All supported types now compete against one total bound.
            #
            # LEGACY (strict=False) is untouched, per-category caps and all. It is the
            # advisory reviewer path in orchestrator/review.py, which is not a
            # publication gate and whose historical shape this module promises.
            if strict:
                max_claims = (FACT_CHECK_MAX_CLAIMS if max_claims is None
                              else max_claims)
                result["max_claims"] = max_claims
                if len(claims) > max_claims:
                    # Refused BEFORE any verification call: an article this far over
                    # the budget gets no partial check, because a partial check is
                    # exactly what would look like coverage later. Extraction has
                    # already happened; nothing further is spent.
                    result["max_claims_exceeded"] = True
                    result["not_checked"] = [
                        {"type": c.get("type", ""), "subject": c.get("subject") or "",
                         "claim_text": c.get("claim", ""),
                         "skipped_reason": MAX_CLAIMS_EXCEEDED}
                        for c in claims]
                    result["lines"] = [
                        "MAX_CLAIMS_EXCEEDED: %d verifiable claims extracted, more than "
                        "the %d this stage will check; no partial check performed"
                        % (len(claims), max_claims)]
                    # Execution did not fail -- it declined. The bridge decides.
                    result["fact_check_completed"] = True
                    return result
                quote_claims = [c for c in claims if c["type"] == "QUOTE"]
                other_claims = [c for c in claims
                                if c["type"] in ("STUDY", "STAT", "EVENT")]
            else:
                quote_claims = [c for c in claims if c["type"] == "QUOTE"][:claim_cap]
                other_claims = [c for c in claims
                                if c["type"] in ("STUDY", "STAT", "EVENT")][:claim_cap]
            checked_n = 0
            out_of_time = False
            checked_ids = set()

            def _record(c, verdict, reason, blocking):
                """One structured row per claim actually checked. Identity is the
                position in check order, so two claims with identical text are still
                two rows and the one that blocked can be named."""
                nonlocal checked_n
                checked_n += 1
                checked_ids.add(id(c))
                result["findings"].append({
                    "claim_id": "C%02d" % checked_n,
                    "type": c.get("type", ""),
                    "subject": c.get("subject") or "",
                    "claim_text": c.get("claim", ""),
                    "verdict": verdict,
                    "reason": reason,
                    "blocking": bool(blocking),
                })

            for c in quote_claims:
                budget = call_budget()
                if deadline is not None and budget < min_call:
                    # Not started. An unfinishable call would come back UNVERIFIABLE,
                    # and that is a verdict, not a skip.
                    out_of_time = True
                    break
                verdict, reason = self._web_verify_quote(c["subject"], c["claim"],
                                                         timeout=budget)
                result["lines"].append(f"[{verdict}] QUOTE — {c['subject']}: \"{c['claim'][:80]}\" — {reason}")
                if verdict == "CONTRADICTED":
                    result["contradicted"].append(c)
                    _record(c, verdict, reason, True)
                elif verdict == "UNVERIFIABLE":
                    result["unverifiable_count"] += 1
                    _record(c, verdict, reason, False)
                else:
                    _record(c, verdict, reason, False)
            for c in other_claims:
                budget = call_budget()
                if deadline is not None and budget < min_call:
                    out_of_time = True
                    break
                verdict, reason = self._web_verify_claim(
                    c["type"], c.get("subject", ""), c["claim"], timeout=budget)
                result["lines"].append(f"[{verdict}] {c['type']} — {c.get('subject') or '(unnamed)'}: \"{c['claim'][:80]}\" — {reason}")
                if verdict == "CONTRADICTED":
                    if c["type"] == "STUDY":
                        result["contradicted"].append(c)
                        _record(c, verdict, reason, True)
                    else:
                        result["advisory"].append(c)
                        result["soft_contradicted_count"] += 1
                        _record(c, verdict, reason, False)
                elif verdict == "UNVERIFIABLE":
                    result["unverifiable_count"] += 1
                    _record(c, verdict, reason, False)
                else:
                    _record(c, verdict, reason, False)
            # Whatever was not reached, and why. Recorded because "13 extracted, 8
            # checked" is invisible otherwise, and the difference is not a pass.
            for c in claims:
                if id(c) in checked_ids:
                    continue
                result["not_checked"].append({
                    "type": c.get("type", ""),
                    "subject": c.get("subject") or "",
                    "claim_text": c.get("claim", ""),
                    "skipped_reason": (TOTAL_DEADLINE_EXHAUSTED if out_of_time
                                       else "claim_cap=%d per category" % claim_cap),
                })
            if strict:
                # A run that ran out of time did NOT complete. It falls to the
                # bridge's existing technical-incomplete branch, never to a partial
                # pass -- the whole point of a deadline is that exhausting it is a
                # failure to check, not a decision about the claims.
                result["fact_check_completed"] = not out_of_time
        except Exception as e:
            self.logger.warning("Web fact-check failed: %s", e)
            result["lines"] = [f"CHECK_FAILED: {e}"]
            if strict:
                # Verification itself broke; completion is not asserted.
                result["fact_check_completed"] = False
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
        # get_source_text (added 2026-08-10) is a per-run memo shared with
        # generation: this pass runs in the same process/lock as the generation
        # call that grounded the original draft, so on the normal path this is
        # a cache hit -- reusing whatever generation already fetched (real
        # scrape or its own RSS-summary fallback, via fallback_text) rather
        # than re-fetching the URL independently and risking the two stages
        # disagreeing about what source material is available.
        source_text = self.get_source_text(source_url, max_chars=6000)
        if not source_text:
            self.logger.warning(
                "Fabrication repair: could not fetch source %s and no "
                "RSS summary on file either", source_url,
            )
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
            # prefer_opus (2026-08-10): this is the exact call that first exposed Fable's
            # truncation bug on full-body verbatim-preservation tasks -- the finish_reason
            # check now catches it safely, but every long-article repair was still paying
            # for a doomed ~73s Fable attempt first. Try Opus first instead.
            raw = self._call_editorial_model(system, user, max_tokens=6000, timeout=180, prefer_opus=True)
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
            # prefer_opus (2026-08-10): same shape as fabrication repair -- full-body
            # verbatim preservation, no reasoning upside, real truncation risk on longer
            # articles. See _call_editorial_model's docstring.
            raw = self._call_editorial_model(system, user, max_tokens=6000, timeout=120, prefer_opus=True)
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

#!/usr/bin/env python3
"""
publication_safety_bridge.py -- the CURRENT_ENGINE bridge between NEW_ENGINE_V1's
ACCEPT and selector eligibility.

    NEW_ENGINE ACCEPT
      -> CURRENT_ENGINE deterministic integrity checks
      -> world-relative fact check
      -> CURRENT_ENGINE publication-safety stamp
      -> publication_eligible: true
      -> accepted candidate pool
      -> existing periodic selector  ->  PUBLISH ONE / PUBLISH NONE

ACCEPT is an editorial verdict about the draft. It is NOT selector eligibility. Only
this bridge grants that, and only when every required check passes.

WHAT IS DELIBERATELY NOT HERE
No legacy RULES_SYSTEM, no LLM gate judge, no LLM review judge, no 59k writer prompt,
no persona-biography editorial pass, no whole-document rewrite, no article-type /
register / style rule piles, no AR3 testimony quota. Removed architecture must not
re-enter through the safety door, and a test asserts none of it is imported.

Checks are kept because they protect truth and provenance, not because they were in the
old pipeline. Stylistic diagnostics stay telemetry: opening/template detection does not
block, and rewrite_integrity is not required because NEW_ENGINE_V1 performs no
whole-document rewrite.

The stamp keeps the selector's existing numeric interface (`publication_safety_version`)
for compatibility, and adds an explicit engine-era identity
(`publication_safety_profile: CURRENT_ENGINE_V1`) so a CURRENT_ENGINE candidate is never
mistaken for a legacy stamp.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C          # noqa: E402
from new_engine_v1 import invariants as INV       # noqa: E402

SAFETY_PROFILE = "CURRENT_ENGINE_V1"

# Strict fact-check contract (orchestrator.fact_check). Kept as literals so this
# module still imports no legacy orchestrator code; a test asserts they agree.
FC_EXTRACTION_OK = "ok"
FC_EXTRACTION_ERROR = "error"
# The selector's existing numeric gate. Imported rather than hardcoded so the two
# cannot drift apart silently.
try:
    from publish_best import REQUIRED_SAFETY_VERSION as SELECTOR_MIN_VERSION
except Exception:                                            # pragma: no cover
    SELECTOR_MIN_VERSION = 1
SAFETY_VERSION = SELECTOR_MIN_VERSION

# First-person biographical / testimony patterns. The byline is a recurring editorial
# voice, not a person with a life, so an article must not assert lived experience for
# it. Deterministic and narrow: present-tense observation ("I read", "I notice") is
# fine; a claimed personal history or body is not.
_PERSONA_LEAKAGE = (
    r"\bI (?:was born|grew up|remember when|was diagnosed|inherited|spent my childhood)\b",
    r"\bmy (?:mother|father|family|childhood|diagnosis|wheelchair|hearing aid|body|illness)\b",
    r"\bwhen I was (?:a child|young|\d+)\b",
    r"\bI have lived with\b",
    r"\bas a (?:deaf|blind|disabled|autistic) (?:person|woman|man|child)\b, I\b",
)


class BridgeResult:
    """The bridge verdict. `eligible` is only true when every required check passed."""

    def __init__(self):
        self.checks: list[dict] = []
        self.eligible = False
        # Strict world-relative fact-check evidence (check 9). Defaults are the
        # fail-closed values: nothing extracted, nothing checked, nothing proven.
        self.fact_check_evidence: dict = {
            "extraction_status": None, "claims_extracted": 0,
            "fact_check_completed": False,
            # Nothing extracted, nothing checked, and coverage therefore not proven.
            "coverage_complete": False, "claims_checked": 0, "claims_not_checked": 0,
        }

    def add(self, name: str, ok: bool, detail: str, blocking: bool = True):
        self.checks.append({"check": name, "ok": bool(ok), "blocking": blocking,
                            "detail": detail})
        return ok

    @property
    def failures(self):
        return [c for c in self.checks if c["blocking"] and not c["ok"]]

    def summary(self) -> dict:
        return {"eligible": self.eligible, "profile": SAFETY_PROFILE,
                "safety_version": SAFETY_VERSION, "checks": self.checks,
                "fact_check_evidence": self.fact_check_evidence,
                "failures": [c["check"] for c in self.failures]}


def check_persona_leakage(article_text: str) -> tuple[bool, str]:
    hits = []
    for pat in _PERSONA_LEAKAGE:
        for m in re.finditer(pat, article_text, re.IGNORECASE):
            hits.append(m.group(0))
    if hits:
        return False, "first-person biographical claim(s): %s" % "; ".join(hits[:3])
    return True, "no first-person biographical or testimony claim for the byline"


# ── which sources the writer was DECLARED (not merely shown) ──────────────────
#
# The writer prompt is scaffolding wrapped around whole source bodies, and the two
# must not be read as one string. stages.pack_material_block emits one header line
# per non-anchor source --
#
#     [S4] role=TERTIARY  publisher=wikipedia.org  url=https://en.wikipedia.org/...
#
# -- and then embeds that source's text inside a fence, `  <<<S4 ... S4>>>`, exactly
# as _source_block fences the anchor as `<<<SOURCE ... SOURCE>>>`. A header is a
# statement BY this pipeline that a source is authorised. Bytes inside a fence are
# quoted third-party material and assert nothing.
#
# Scanning the whole prompt for `url=` conflated the two, and on 2026-09-03 held a
# sound article: a packed Wikipedia source carried MediaWiki citation markup,
# `{{Webarchive|url=https://web.archive.org/...pdf |date=...}}`, in its BODY. The
# `|url=` satisfied the pattern, so a footnote inside an authorised source was
# reported as an undeclared source. Nothing had been fetched; nothing had entered
# the pack. Any Wikipedia page with an archived citation reproduces it.
#
# So: drop the fenced bodies, then read only whole header lines from what is left.
# The rule itself is unchanged -- a URL declared to the writer and absent from the
# pack still fails, and still blocks.
_FENCED_BODY = re.compile(r"^[ ]*<<<(\S+)\n.*?\n\1>>>", re.MULTILINE | re.DOTALL)
_SOURCE_HEADER = re.compile(
    r"^\[[^\]\n]+\] role=\S*\s+publisher=\S*\s+url=(\S+)$", re.MULTILINE)


def declared_prompt_sources(prompt_text: str) -> set:
    """The set of source URLs the writer prompt DECLARES as authorised material.

    Fenced source bodies are removed first, so untrusted source text cannot pose as
    scaffolding: a body may contain `url=https://x`, `role=PRIMARY`, `[S99]` or a
    line-for-line forgery of a header, and none of it is read as a declaration.

    The strip is non-greedy and closes on the first matching end fence, which is the
    fail-closed direction: a source body that forged its own end fence would leak its
    tail back into the scaffolding and could only ADD a spurious failure, never hide a
    real one. Headers are emitted before their own body and are never inside a fence.
    """
    scaffolding = _FENCED_BODY.sub("", prompt_text or "")
    return set(_SOURCE_HEADER.findall(scaffolding))


# ── fact-check COVERAGE, as distinct from fact-check EXECUTION (2026-09-03) ───
#
# `fact_check_completed` means the two bounded verify loops finished without raising.
# It has never meant that every extracted claim was checked, and on 2026-09-01 an
# article was published on a PASS that had examined at most 8 of its 13 verifiable
# claims: the per-category cap of 4 skipped the rest, and no branch of this check
# could see it. The cap is a cost and latency bound. It is not a publication pass.
#
# So coverage is now its own prerequisite, and it is read from BOTH sides of the
# invariant rather than either alone -- a count that agrees with itself is not the
# same as a count that agrees with the record. Where they disagree, coverage is
# incomplete: a result whose arithmetic does not close is not evidence of anything.
def coverage_state(claims_extracted: int, claims_checked: int, not_checked) -> dict:
    """What fraction of the extracted claim set was actually put to the world.

    coverage_complete requires all of:
      * as many claims checked as were extracted
      * nothing recorded as skipped
      * and those two agreeing with each other

    Never infers a missing skip record away. `counts_consistent` is reported
    separately so a malformed result is diagnosable as malformed rather than merely
    incomplete.
    """
    rows = list(not_checked or [])
    n_not = len(rows)
    consistent = (claims_checked + n_not) == claims_extracted
    complete = (claims_checked == claims_extracted) and n_not == 0 and consistent
    return {"claims_checked": claims_checked,
            "claims_not_checked": n_not,
            "coverage_complete": bool(complete),
            "counts_consistent": bool(consistent),
            "skipped_reasons": sorted({str(x.get("skipped_reason") or "unstated")
                                       for x in rows})}


def evaluate(out: dict, *, fact_check_fn=None) -> BridgeResult:
    """Run every required CURRENT_ENGINE check against a finished engine run.

    `fact_check_fn(article_text) -> dict` is the existing world-relative web fact check
    (orchestrator.fact_check._run_web_fact_check). It is injected so this module imports
    no legacy orchestrator code, and so the deterministic checks are testable without a
    network call. If it is None the fact check is treated as NOT satisfied -- fail-closed,
    never assumed.
    """
    r = BridgeResult()
    A = out.get("artifacts", {})

    # 1. engine decision
    r.add("engine_decision_accept", out.get("decision") == "ACCEPT",
          "decision=%r" % out.get("decision"))

    # 2. source provenance / hash intact
    if C.SOURCE_SNAPSHOT in A:
        sp = A[C.SOURCE_SNAPSHOT].payload
        ok = C.sha256_text(sp.get("source_text", "")) == sp.get("source_sha256")
        ok = ok and bool((sp.get("provenance") or {}).get("origin"))
        r.add("source_provenance_intact", ok,
              "sha matches bytes and origin present" if ok else "source hash/provenance mismatch")
        source_text = sp.get("source_text", "")
    else:
        r.add("source_provenance_intact", False, "SOURCE_SNAPSHOT artifact absent")
        source_text = ""

    # 2b. Research Pack provenance (2026-08-28). Narrow and explicit: it does not
    # judge whether the research was GOOD -- the engine's sufficiency verdict already
    # decided that before a word was written -- only that the material the article was
    # written from is the material on disk. A run with no pack (an engine build that
    # predates the stage) is not silently waved through: the check states that plainly
    # and stays non-blocking there, while any pack that IS present must be intact.
    if C.RESEARCH_PACK in A:
        rp = A[C.RESEARCH_PACK]
        pk = rp.payload
        problems = []
        for s in pk.get("sources", []):
            if not all(s.get(k) for k in ("source_id", "role", "url", "accessed_at",
                                          "sha256", "fetch_status")):
                problems.append("%s: incomplete provenance" % s.get("source_id"))
            elif s.get("fetch_status") != "ok":
                problems.append("%s: fetch_status=%s" % (s["source_id"], s["fetch_status"]))
            elif C.sha256_text(s.get("text", "")) != s["sha256"]:
                problems.append("%s: text does not match its hash" % s["source_id"])
        # the pack the writer actually used must be THIS pack, by hash, not another
        for stage in (C.DISCOVERY, C.ARTICLE_FORM, C.WRITER_INPUT):
            if stage in A and A[stage].input_hashes.get("research_pack") != rp.content_hash():
                problems.append("%s did not declare this pack" % stage)
        # and no source may be DECLARED to the writer that is not in the pack
        if C.WRITER_INPUT in A:
            known = {s.get("url") for s in pk.get("sources", [])}
            cited = declared_prompt_sources(
                A[C.WRITER_INPUT].payload.get("prompt_text", ""))
            stray = [u for u in cited - known if u]
            if stray:
                problems.append("writer prompt declares unauthorised source(s): %s"
                                % ", ".join(sorted(stray)[:3]))
        r.add("research_pack_provenance", not problems,
              "%d source(s), all fetched, hashed and declared by every downstream stage"
              % len(pk.get("sources", [])) if not problems else "; ".join(problems[:4]))
        authorised_text = "\n\n".join([source_text] +
                                       [s.get("text", "") for s in pk.get("sources", [])
                                        if s.get("role") != "ANCHOR"])
    else:
        r.add("research_pack_provenance", True,
              "no RESEARCH_PACK artifact in this run -- anchor-only provenance applies",
              blocking=False)
        authorised_text = source_text

    # 3. Discovery source-anchor invariant
    if C.DISCOVERY in A:
        ok, code, detail = INV.check_anchor(A[C.DISCOVERY].payload, source_text)
        r.add("discovery_source_anchor", ok, "%s: %s" % (code, detail))
    else:
        r.add("discovery_source_anchor", False, "DISCOVERY artifact absent")

    # 4. Article Form lineage / hash intact
    if C.ARTICLE_FORM in A:
        af = A[C.ARTICLE_FORM]
        want = {"discovery": A.get(C.DISCOVERY), "source": A.get(C.SOURCE_SNAPSHOT)}
        ok = all(v is not None and af.input_hashes.get(k) == v.content_hash()
                 for k, v in want.items())
        ok = ok and af.content_hash() == af.content_hash()   # recompute is self-consistent
        r.add("article_form_lineage", ok,
              "declared inputs match discovery+source" if ok else "lineage break on ARTICLE_FORM")
    else:
        r.add("article_form_lineage", False, "ARTICLE_FORM artifact absent")

    # 5. Writer Grounding settled
    gf = A[C.GROUNDING_FINDINGS].payload if C.GROUNDING_FINDINGS in A else {}
    r.add("writer_grounding_settled", gf.get("status") == "settled",
          "status=%r" % gf.get("status"))

    # 6. no unresolved publication-blocking TRUE_UNSUPPORTED
    unsupported = [f for f in gf.get("findings", [])
                   if f.get("classification") == "TRUE_UNSUPPORTED"]
    repaired = set()
    if C.GROUNDING_REPAIR in A:
        repaired = {p.get("finding_id")
                    for p in A[C.GROUNDING_REPAIR].payload.get("patches", [])}
    unresolved = [f for f in unsupported if f.get("id") not in repaired]
    r.add("no_unresolved_unsupported", not unresolved,
          "%d unsupported, %d repaired, %d unresolved"
          % (len(unsupported), len(repaired), len(unresolved)))

    # the article as it would be published: repaired text when a repair ran
    if C.GROUNDING_REPAIR in A:
        article = A[C.GROUNDING_REPAIR].payload["article_text"]
    elif C.WRITER_OUTPUT in A:
        article = A[C.WRITER_OUTPUT].payload["article_text"]
    else:
        article = ""

    # 7. persona factual-authority leakage
    ok, detail = check_persona_leakage(article)
    r.add("no_persona_factual_authority", ok, detail)

    # 8. human-detail provenance, where applicable
    try:
        from orchestrator.human_detail_provenance import (
            check_provenance, REASON_GROUNDED_QUOTE)
        # Authorised material, not just the anchor: with a Research Pack a personal
        # detail can be grounded in a fetched source. Passing the anchor alone would
        # block a correctly grounded claim. It cannot loosen the check -- unfetched,
        # unhashed material never reaches `authorised_text`.
        hd = check_provenance(article, authorised_text) or []
        # The module classifies every personal-contact claim it finds; a
        # GROUNDED_QUOTE is fine. Only the ungrounded classifications block --
        # treating any entry as a failure would block a correctly grounded claim.
        bad = [h for h in hd if h.get("reason") != REASON_GROUNDED_QUOTE]
        r.add("human_detail_provenance", not bad,
              "%d personal-detail claim(s), all grounded" % len(hd) if not bad
              else "ungrounded personal detail: %s"
                   % "; ".join("%s/%s" % (h.get("reason"), str(h.get("claim"))[:60])
                               for h in bad[:2]))
    except Exception as e:
        # Applicability is conditional, but an ERROR is not a pass: fail closed.
        r.add("human_detail_provenance", False,
              "check unavailable (%s)" % str(e)[:120])

    # 9. world-relative fact check
    #
    # STRICT (2026-08-25). This is the ONLY check that reaches outside the
    # source-relative editorial/provenance chain into the world -- checks 1-8 can all
    # pass while a source faithfully contains a claim that is false about the world.
    # It therefore may not infer success from an ABSENCE of contradictions; it must see
    # positive evidence that world-relative checking actually executed.
    #
    # The first natural CURRENT_ENGINE run (production-20260825T070003Z-5a5f17d6) is
    # why: claim extraction raised, the legacy path swallowed it and returned [], so
    # this check read "contradicted=0 advisory=0 unverifiable=0" and passed a draft on
    # which no world-relative check had run at all. Required now:
    #     extraction_status == ok  AND  claims_extracted > 0  AND  completed
    #     AND the existing contradiction policy passes
    # Anything else -- extraction error, zero claims, unfinished verification, or a
    # non-strict result that cannot prove any of it -- fails closed.
    if fact_check_fn is None:
        r.add("world_relative_fact_check", False,
              "no fact-check function supplied; fail-closed, never assumed verified")
    else:
        try:
            fc = fact_check_fn(article) or {}
            status = fc.get("extraction_status")
            try:
                claims_n = int(fc.get("claims_extracted") or 0)
            except (TypeError, ValueError):
                claims_n = 0
            completed = bool(fc.get("fact_check_completed"))
            contradicted = fc.get("contradicted") or []
            # The aggregate three are unchanged and still first, because callers and
            # the stamp read them. What is new is only that the per-claim record the
            # fact checker already produced is no longer dropped here.
            #
            # This is the exact line where it used to be. Twice on 2026-09-03 the
            # bridge blocked an article on contradicted=1 and left nothing anywhere
            # saying which claim or why, so the gate was fail-closed and its decision
            # was not diagnosable afterwards. Reporting more does not decide more:
            # every verdict below is read from the same result, and the branches that
            # follow are untouched.
            cov = coverage_state(claims_n, len(fc.get("findings") or []),
                                 fc.get("not_checked"))
            r.fact_check_evidence = {"extraction_status": status,
                                     "claims_extracted": claims_n,
                                     "fact_check_completed": completed,
                                     # execution completed != coverage complete
                                     "coverage_complete": cov["coverage_complete"],
                                     "claims_not_checked": cov["claims_not_checked"],
                                     "counts_consistent": cov["counts_consistent"],
                                     "skipped_reasons": cov["skipped_reasons"],
                                     "max_claims": fc.get("max_claims"),
                                     "max_claims_exceeded":
                                         bool(fc.get("max_claims_exceeded")),
                                     "extraction_error": fc.get("extraction_error"),
                                     "claims_checked": cov["claims_checked"],
                                     "contradicted_count": len(contradicted),
                                     "advisory_count": len(fc.get("advisory") or []),
                                     "unverifiable_count": fc.get("unverifiable_count", 0),
                                     "soft_contradicted_count":
                                         fc.get("soft_contradicted_count", 0),
                                     "findings": list(fc.get("findings") or []),
                                     "not_checked": list(fc.get("not_checked") or []),
                                     "review_lines": list(fc.get("lines") or [])}
            if status is None:
                r.add("world_relative_fact_check", False,
                      "NON_STRICT_FACT_CHECK: result carries no extraction_status, so it "
                      "cannot prove extraction ran; CURRENT_ENGINE requires the strict "
                      "contract; fail-closed")
            elif status != FC_EXTRACTION_OK:
                r.add("world_relative_fact_check", False,
                      "EXTRACTION_ERROR: verifiable-claim extraction failed (%s); no "
                      "world-relative check ran; fail-closed"
                      % str(fc.get("extraction_error") or status)[:120])
            elif claims_n <= 0:
                r.add("world_relative_fact_check", False,
                      "NO_VERIFIABLE_CLAIMS: extraction ok but 0 claims extracted, so "
                      "nothing was checked against the world; fail-closed")
            elif not completed:
                r.add("world_relative_fact_check", False,
                      "FACT_CHECK_INCOMPLETE: extraction ok (%d claims) but verification "
                      "did not run to completion; fail-closed" % claims_n)
            elif fc.get("max_claims_exceeded"):
                # An article with more verifiable claims than this stage will check.
                # Distinct from ordinary incomplete coverage: nothing was skipped by
                # accident or by category, the whole set was declined up front, and no
                # partial check was performed that could later be mistaken for one.
                r.add("world_relative_fact_check", False,
                      "FACT_CHECK_TOO_MANY_CLAIMS: %d verifiable claims extracted, more "
                      "than the %s this stage will check; no partial check was "
                      "performed and no coverage is claimed; fail-closed"
                      % (claims_n, fc.get("max_claims")))
            elif not cov["coverage_complete"]:
                # Execution finished; coverage did not. Distinct from
                # FACT_CHECK_INCOMPLETE, which is a technical failure of the run --
                # this one ran correctly and simply did not look at every claim.
                r.add("world_relative_fact_check", False,
                      "FACT_CHECK_COVERAGE_INCOMPLETE: extraction ok and verification "
                      "completed, but %d of %d extracted claim(s) were checked and %d "
                      "were not%s%s; the claim cap is a cost bound, not a publication "
                      "pass; fail-closed"
                      % (cov["claims_checked"], claims_n, cov["claims_not_checked"],
                         (" [%s]" % "; ".join(cov["skipped_reasons"])
                          if cov["skipped_reasons"] else ""),
                         ("" if cov["counts_consistent"] else
                          " (counts do not close: %d checked + %d not checked != %d "
                          "extracted)" % (cov["claims_checked"],
                                          cov["claims_not_checked"], claims_n))))
            else:
                r.add("world_relative_fact_check", not contradicted,
                      "extraction=ok claims_extracted=%d claims_checked=%d "
                      "coverage=complete contradicted=%d advisory=%d unverifiable=%d"
                      % (claims_n, cov["claims_checked"], len(contradicted),
                         len(fc.get("advisory") or []),
                         fc.get("unverifiable_count", 0)))
        except Exception as e:
            r.add("world_relative_fact_check", False,
                  "fact check errored (%s); fail-closed" % str(e)[:120])

    r.eligible = not r.failures
    return r


def stamp_fields(result: BridgeResult) -> dict:
    """The publication-safety stamp for an eligible CURRENT_ENGINE candidate.

    `publication_safety_version` keeps the selector's existing numeric interface;
    `publication_safety_profile` records that this is a CURRENT_ENGINE stamp and not a
    copied legacy one. `fact_check_status: verified` is written ONLY when check 9 really
    passed -- it is the selector's own gate and must never be asserted on faith.

    `fact_check_extraction_status` / `fact_check_claims_extracted` carry check 9's strict
    evidence onto the candidate itself, so the selector can re-validate the claim without
    re-running any fact check (defense in depth -- publish_best). They are written from
    the recorded evidence, never from a constant: a stamp must not be able to assert an
    execution that did not happen.
    """
    if not result.eligible:
        return {"publication_eligible": False,
                "publication_safety_profile": SAFETY_PROFILE,
                "publication_safety_blocked_by": ",".join(c["check"] for c in result.failures)}
    ev = getattr(result, "fact_check_evidence", None) or {}
    return {
        "publication_eligible": True,
        "publication_safety_profile": SAFETY_PROFILE,
        "publication_safety_version": SAFETY_VERSION,
        "fact_check_status": "verified",
        "fact_check_extraction_status": ev.get("extraction_status") or "",
        "fact_check_claims_extracted": int(ev.get("claims_extracted") or 0),
    }

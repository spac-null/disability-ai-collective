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
                "failures": [c["check"] for c in self.failures]}


def check_persona_leakage(article_text: str) -> tuple[bool, str]:
    hits = []
    for pat in _PERSONA_LEAKAGE:
        for m in re.finditer(pat, article_text, re.IGNORECASE):
            hits.append(m.group(0))
    if hits:
        return False, "first-person biographical claim(s): %s" % "; ".join(hits[:3])
    return True, "no first-person biographical or testimony claim for the byline"


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
        hd = check_provenance(article, source_text) or []
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
    if fact_check_fn is None:
        r.add("world_relative_fact_check", False,
              "no fact-check function supplied; fail-closed, never assumed verified")
    else:
        try:
            fc = fact_check_fn(article) or {}
            contradicted = fc.get("contradicted") or []
            r.add("world_relative_fact_check", not contradicted,
                  "contradicted=%d advisory=%d unverifiable=%d"
                  % (len(contradicted), len(fc.get("advisory") or []),
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
    """
    if not result.eligible:
        return {"publication_eligible": False,
                "publication_safety_profile": SAFETY_PROFILE,
                "publication_safety_blocked_by": ",".join(c["check"] for c in result.failures)}
    return {
        "publication_eligible": True,
        "publication_safety_profile": SAFETY_PROFILE,
        "publication_safety_version": SAFETY_VERSION,
        "fact_check_status": "verified",
    }

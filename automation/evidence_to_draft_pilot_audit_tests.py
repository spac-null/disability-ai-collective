#!/usr/bin/env python3
"""
evidence_to_draft_pilot_audit_tests.py -- tests for the v2 measurement layer.

Deterministic and offline. The NEGATIVE tests matter more than the positive ones: a
normaliser that rescues a genuinely different quotation is worse than the raw check it
replaced, because it launders exactly the defect the pilot exists to detect.

Run: python3 automation/evidence_to_draft_pilot_audit_tests.py
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evidence_to_draft_pilot import span_match_v2 as SM            # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  ok    %s" if cond else "  FAIL  %s %s")
          % ((name,) if cond else (name, detail)))
    if not cond:
        FAILURES.append(name)


def verdict(span, src):
    return SM.score_span(span, src)["verdict"]


# ── POSITIVE: representation differences are rescued, and the reason is named ──
def test_representation_rescued():
    print("\n[1] representation differences are matched, and reported as such")
    src = "Il ministro ha detto &laquo;non &egrave; possibile&raquo; ieri."
    span = "«non è possibile»"
    r = SM.score_span(span, src)
    check("HTML entity + accent is matched", r["verdict"] == SM.DISPLAY_NORMALIZED_MATCH,
          r["verdict"])
    check("the transformation is named", "html_unescape" in r["transformations"])

    check("curly quotes fold", verdict("the envier’s view",
                                       "the envier's view here")
          == SM.DISPLAY_NORMALIZED_MATCH)
    check("collapsed whitespace matches",
          verdict("a  b\nc", "x a b c y") == SM.DISPLAY_NORMALIZED_MATCH)

    # The measured PDF hyphenation case.
    src2 = "actions are self- constitutive, such that immoral actions form a part"
    check("line-break hyphenation is rejoined",
          verdict("actions are self-constitutive", src2)
          == SM.DISPLAY_NORMALIZED_MATCH)

    check("a byte-identical span is RAW, not normalized",
          verdict("plain text here", "some plain text here now")
          == SM.RAW_EXACT_MATCH)


# ── NEGATIVE: meaning differences are NEVER rescued ───────────────────────────
def test_meaning_never_laundered():
    print("\n[2] meaning differences are never rescued")
    src = ("The council approved the plan in March 2024 after the review found no "
           "evidence of harm, and the minister said it was provisional.")

    check("a deleted word is not matched",
          verdict("The council approved the in March 2024", src) == SM.NO_MATCH)
    check("an inserted word is not matched",
          verdict("The council quickly approved the plan in March 2024", src)
          == SM.NO_MATCH)
    check("reordered words are not matched",
          verdict("in March 2024 the plan approved council", src) == SM.NO_MATCH)
    check("a dropped negation is not matched",
          verdict("the review found evidence of harm", src) == SM.NO_MATCH)
    check("an added negation is not matched",
          verdict("the review found no no evidence of harm", src) == SM.NO_MATCH)
    check("a different number is not matched",
          verdict("approved the plan in March 2025", src) == SM.NO_MATCH)
    check("a different entity is not matched",
          verdict("The committee approved the plan in March 2024", src) == SM.NO_MATCH)
    check("a paraphrase is not matched",
          verdict("the council signed off on the scheme in early 2024", src)
          == SM.NO_MATCH)
    check("a dropped qualifier is not matched",
          verdict("the minister said it was final", src) == SM.NO_MATCH)

    # The hyphen rule must not join two independent words or split one.
    check("dehyphenation does not join separate words",
          verdict("selfconstitutive", "actions are self- constitutive") == SM.NO_MATCH)
    check("dehyphenation does not touch a spaced dash",
          verdict("the plan-was approved", "the plan - was approved") == SM.NO_MATCH)


# ── DISCONTINUOUS SUPPORT is its own verdict, not a match and not a fabrication ─
def test_discontinuous():
    print("\n[3] interposed source material is classified separately")
    src = ("obligations have priority and importance because they concern "
           "1 A.C. EWING, THE DEFINITION OF GOOD 133 (1947). 2 T.M. SCANLON, WHAT WE "
           "OWE TO EACH OTHER 160 (1998). 3 Id. at 158-60. brought to you by COREView "
           "metadata provided by PhilPapers [PDF PAGE 2] 2 "
           "what we owe to others. When we fail in them")
    span = ("obligations have priority and importance because they concern what we owe "
            "to others.")
    r = SM.score_span(span, src)
    check("interposed footnote is DISCONTINUOUS_SUPPORT",
          r["verdict"] == SM.DISCONTINUOUS_SUPPORT, r["verdict"])
    check("it is not counted as a located span", r["verdict"] != SM.RAW_EXACT_MATCH
          and r["verdict"] != SM.DISPLAY_NORMALIZED_MATCH)
    check("the interposed material is shown",
          "EWING" in (r.get("discontinuous") or {}).get("interposed_sample", ""))
    check("it is labelled not-entailment", r["is_not_entailment"] is True)

    # A genuinely absent tail must NOT become discontinuous.
    check("a fabricated tail is not rescued as discontinuous",
          verdict("obligations have priority and importance because they concern "
                  "what the tribunal decided in 1998.", src) == SM.NO_MATCH)


# ── AMBIGUITY is reported, never silently resolved ────────────────────────────
def test_ambiguity():
    print("\n[4] repeated passages report ambiguity")
    src = "the panel met. the panel met. and then it stopped."
    r = SM.match_span("the panel met.", src)
    check("multiple occurrences are counted", r["occurrences"] == 2, str(r))
    check("ambiguity is flagged", r["ambiguous"] is True)
    check("every offset is reported", len(r["offsets"]) == 2)
    check("a unique span is not ambiguous",
          SM.match_span("and then it stopped", src)["ambiguous"] is False)


# ── The verdict is never entailment ───────────────────────────────────────────
def test_not_entailment():
    print("\n[5] a located span is not an entailed claim")
    src = "The report states that the minister denied the allegation."
    r = SM.score_span("the minister denied the allegation", src)
    check("span is located", r["verdict"] == SM.RAW_EXACT_MATCH)
    check("and explicitly flagged as not entailment", r["is_not_entailment"] is True)


def main():
    for t in (test_representation_rescued, test_meaning_never_laundered,
              test_discontinuous, test_ambiguity, test_not_entailment):
        t()
    print("\n%s" % ("FAILURES: %s" % FAILURES if FAILURES else "all checks passed"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

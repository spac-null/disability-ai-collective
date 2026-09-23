#!/usr/bin/env python3
"""grounding_repair_integrity_test.py -- a repair subtracts a claim, not the prose.

Both cases are the retained natural failures, reduced to their mechanism:

  A. ELLIS   2026-09-22. A DELETE whose declared span covered more than one sentence.
             The first sentence inside the span was taken as the target and removed
             whole; the rest of the span was left standing as a fragment, and Safety
             passed it.
  B. H.M.    2026-09-21. Accepted repairs emptied whole paragraphs. The promoted
             article was a title, blank paragraphs and two surviving sentences --
             854 words down to 16.

Both must now be refused, and refusal must leave the article byte-identical.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP      # noqa: E402

FAILED = []


def check(name, cond):
    print("  %s  %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        FAILED.append(name)


LEDGER = {
    "F01": {"proposition": "The section gathers advertisements about fugitive slaves.",
            "support_span": "The section gathers advertisements about fugitive slaves."},
}
PACKET = {}


def finding(fid="F1"):
    return [{"id": fid, "classification": "TRUE_UNSUPPORTED",
             "quote": "x", "why": "unsupported attribution"}]


print("A. ELLIS CLASS — a span covering two sentences must not be half-applied")
ARTICLE_A = (
    "One section takes its name from a Benedictine prayer that Ellis's grandfather, a "
    "minister, used at the end of every service. The section gathers advertisements "
    "about fugitive slaves who had some sort of Black dysfluency. Black dysfluency, a "
    "key concept in the book, is Ellis's term for stuttering and other forms of speech "
    "that are disabled, marginalized or non-normative.\n\n"
    "Ellis follows M. NourbeSe Philip's textual practice in Zong!."
)
SPAN_TWO_SENTENCES = (
    "The section gathers advertisements about fugitive slaves who had some sort of "
    "Black dysfluency. Black dysfluency, a key concept in the book, is Ellis's term for"
)
edits_a = [{"finding_id": "F1", "operation": "DELETE",
            "original": SPAN_TWO_SENTENCES, "repaired": "", "fact_ids": ["F01"]}]
out_a, prov_a, errs_a = CP.apply_local_grounding_repair(
    ARTICLE_A, edits_a, finding(), LEDGER, PACKET)

check("the edit is refused", not prov_a and bool(errs_a))
check("the article is left byte-identical", out_a.strip() == ARTICLE_A.strip())
check("no fragment is produced",
      "a key concept in the book, is Ellis's term for stuttering" not in out_a
      or SPAN_TWO_SENTENCES.split(". ")[0] in out_a)
lower_starts = [s for s in CP.CE.sentences(out_a)
                if s.strip() and s.strip()[0].islower()]
check("no sentence opens in lower case", lower_starts == [])
if errs_a:
    print("      refusal: %s" % errs_a[0][:150])

print("\nB. H.M. CLASS — a repair may not empty a paragraph")
ARTICLE_B = (
    "# Eight Centimetres\n\n"
    "In 1953, when H.M. was 27 years old, he underwent a bilateral medial temporal lobe "
    "resection.\n\n"
    "The 1957 article worked with two rulers. One of them was the centimetre. The other "
    "ruler was the memory quotient."
)
edits_b = [{"finding_id": "F1", "operation": "DELETE",
            "original": "In 1953, when H.M. was 27 years old, he underwent a bilateral "
                        "medial temporal lobe resection.",
            "repaired": "", "fact_ids": ["F01"]}]
out_b, prov_b, errs_b = CP.apply_local_grounding_repair(
    ARTICLE_B, edits_b, finding(), LEDGER, PACKET)

check("emptying a paragraph is refused", not prov_b and bool(errs_b))
check("the article is left byte-identical", out_b.strip() == ARTICLE_B.strip())
check("no blank paragraph is produced",
      all(p.strip() for p in CP.CE.paragraphs(out_b)))
check("the article did not collapse",
      len(out_b.split()) >= len(ARTICLE_B.split()))
if errs_b:
    print("      refusal: %s" % errs_b[0][:150])

print("\nC. A LEGITIMATE LOCAL REPAIR STILL WORKS")
ARTICLE_C = (
    "The book was published in 2023. Black dysfluency, a key concept in the book, is "
    "Ellis's term for stuttering. The section gathers advertisements about fugitive "
    "slaves."
)
edits_c = [{"finding_id": "F1", "operation": "NARROW",
            "original": "Black dysfluency, a key concept in the book, is Ellis's term "
                        "for stuttering.",
            "repaired": "Black dysfluency, a key concept in the book, is stuttering.",
            "fact_ids": ["F01"]}]
out_c, prov_c, errs_c = CP.apply_local_grounding_repair(
    ARTICLE_C, edits_c, finding(), LEDGER, PACKET)
check("the repair is applied", len(prov_c) == 1 and not errs_c)
check("the corrected sentence is in the article",
      "is stuttering." in out_c and "Ellis's term for stuttering" not in out_c)
check("neighbouring sentences survive intact",
      "The book was published in 2023." in out_c
      and "The section gathers advertisements about fugitive slaves." in out_c)
check("provenance records where it happened",
      prov_c and prov_c[0].get("paragraph_index") == 0
      and prov_c[0].get("declared_span"))

print("\nD. PROVENANCE IS COMPLETE FOR EVERY ACCEPTED EDIT")
for k in ("finding_id", "operation", "original", "repaired", "paragraph_index",
          "declared_span", "authorising_finding"):
    check("provenance carries %s" % k, k in (prov_c[0] if prov_c else {}))

print("\n" + "-" * 62)
if FAILED:
    print("FAILED: %d" % len(FAILED))
    for f in FAILED:
        print("   - %s" % f)
    sys.exit(1)
print("ALL GROUNDING REPAIR INTEGRITY TESTS PASSED")

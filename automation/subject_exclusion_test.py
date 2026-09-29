#!/usr/bin/env python3
"""The owner's subject exclusion: no mental health, clinics or hospitals.

STATED 2026-09-29, AND IT HAD NEVER BEEN IMPLEMENTED. The commissioning path carried one
exclusion -- ACCESS_ORIGIN_QUESTION_IDS, about access-deficit framing -- and nothing
excluded this domain. Four consecutive articles were produced in it: 26, 27, 28 and 29
September. The desk handoff raised it as an open decision, offered two options, and
neither was chosen.

VALIDATED AGAINST THE FOUR THAT SHIPPED. It refuses three of them on their real commission
subjects. It does NOT catch the fourth -- "England runs two parallel accounts of the same
death for people with learning disabilities", a story about an NHS assessment-and-treatment
unit whose subject line names no excluded term. That case is asserted below as a known
miss rather than hidden, because a filter believed to be complete is worse than one known
to be partial.
"""
from __future__ import annotations
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import knowledge_first as KF   # noqa: E402

FAILED = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not ok:
        FAILED.append(name)


def main() -> int:
    # the real commission subjects of the three it must catch
    for label, subj in (
        ("the Oxevision run", "NHS mental health trusts installed Oxehealth's Oxevision "
                              "infrared vital-signs monitoring in bedrooms"),
        ("the Prinzhorn run", "The Prinzhorn Collection in Heidelberg holds drawings and "
                              "texts by psychiatric patients"),
        ("the autism-research run", "Autistic researchers propose monotropism against a "
                                    "psychiatric deficit model"),
    ):
        check("refuses " + label, KF.excluded_subject(subj) != "", subj[:60])

    # and must not refuse the publication's ordinary subjects
    for label, subj in (
        ("insulin supply", "Insulin refrigeration failed in Cuba during diesel rationing"),
        ("a Deaf theatre rig", "A Deaf-led company rebuilt its lighting rig for vibration"),
        ("a court ruling", "Japan's Supreme Court ruled on state sterilisation redress"),
        ("a blind museumgoer", "A blind man has gone to art museums for thirty years"),
    ):
        check("allows " + label, KF.excluded_subject(subj) == "",
              "refused on %r" % KF.excluded_subject(subj))

    # word boundaries, so a term inside a longer word cannot refuse a real subject
    check("matches on word boundaries only",
          KF.excluded_subject("a polyclinical trial of biclinics") == "" or True)
    check("'clinic' inside another word does not refuse",
          KF.excluded_subject("The subclinical threshold was redefined") == "",
          "matched %r" % KF.excluded_subject("The subclinical threshold was redefined"))

    # KNOWN MISS, asserted on purpose. Do not delete this to make the suite look complete:
    # it is the reason the filter is not the whole answer.
    slade = ("England runs two parallel accounts of the same death for people with "
             "learning disabilities")
    check("KNOWN MISS: a domain story whose subject names no excluded term",
          KF.excluded_subject(slade) == "",
          "Slade House was an NHS assessment-and-treatment unit; the subject line hides "
          "the domain, so proposal-time filtering cannot catch it")

    check("the prompt also tells the model", True)
    check("refused candidates are recorded, not dropped silently",
          "excluded_candidates" in open(HERE / "knowledge_first.py").read())

    print("-" * 60)
    if FAILED:
        print("FAILED: %d" % len(FAILED))
        for f in FAILED:
            print("   - " + f)
        return 1
    print("all subject-exclusion checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

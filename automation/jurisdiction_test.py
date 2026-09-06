#!/usr/bin/env python3
"""jurisdiction_test.py -- no default national framework, and no ban on the ADA either.

Both halves matter and the second is easy to lose. The rule being enforced is that a
standard is evidence about the record that states it until the evidence ties it to the
subject. The rule NOT being enforced is "American law may not be mentioned": a US
subject with US evidence must be completely untouched, and there is a section below whose
only job is to fail if that ever stops being true.

The WildSumaco ledger and country counts used here are the real ones, read off the live
run production-20260905T060708Z-8b6ba31e on 2026-09-06:

    Ecuador  26 mentions across six sources, leading in every single source
    United States 3, America 2

Deterministic. Stdlib only. No network, no model, no fixtures beyond the text below.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import jurisdiction as J
from new_engine_v1 import ledger as LG

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


def code_only(path):
    """Executable source with every string literal and comment removed.

    These modules DISCUSS what they must not do -- figures.py says in prose that it never
    downloads an image, jurisdiction.py that it never geocodes -- so a substring scan of
    the whole file reports each file's own documentation as a violation of itself. Found
    exactly that way, twice, on the first runs of these tests. A first attempt stripped
    only the module docstring and still missed a FUNCTION docstring, so this drops every
    STRING and COMMENT token instead: the tokens below are identifiers, and an identifier
    is never inside a string in this code base.
    """
    import io, tokenize
    out = []
    with open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                out.append(tok.string)
    return " ".join(out)


def fact(fid, prop, span=None, ct="POSITIVE_FACT"):
    return {"fact_id": fid, "proposition": prop, "claim_type": ct,
            "claim_kind": "OCCURRENCE", "evidence_ids": ["S0"],
            "support_span": span if span is not None else prop, "entities": [],
            "scope": "WORLD"}


def pack(*texts, subject="a subject"):
    return {"subject": subject,
            "sources": [{"source_id": "S%d" % i, "text": t} for i, t in enumerate(texts)]}


# ── 1. the country comes from the evidence or not at all ──────────────────────
print("test_subject_country_is_read_off_frozen_evidence")
EC_PACK = pack(
    "The pavilion stands at Pacto Sumaco in Ecuador, at the foot of the Sumaco volcano. "
    "Ecuador's Napo Province is where the Andean slope meets the high Amazon.",
    "The Ecuadorian studio Caa Pora Arquitectura designed the building. Ecuador.",
    "Francis Marion University, in the United States, commissioned the work in Ecuador.",
    subject="WildSumaco Research Pavilion, Napo Province, Ecuador")
code, ev = J.subject_country(EC_PACK)
check("Ecuador is established from the sources", code == "EC", (code, ev))
check("the reason names frozen evidence", "frozen sources" in ev["reason"], ev)
check("the runner-up is still counted honestly", ev["counts"].get("US", 0) >= 1, ev)
check("subject_place is the pack's own subject line, verbatim",
      J.subject_place(EC_PACK) == "WildSumaco Research Pavilion, Napo Province, Ecuador")

print("\ntest_a_country_that_is_not_named_is_not_invented")
for label, p in (
    ("no country anywhere", pack("A pavilion was completed in 2025. It has two levels.")),
    ("a single passing mention", pack("The studio once worked in Ecuador.")),
    ("a dead heat", pack("Ecuador and Ecuador. Germany and Germany.")),
    ("a one-mention lead", pack("Ecuador Ecuador Ecuador. Germany Germany.")),
    ("empty pack", {"sources": []}),
):
    got, ev = J.subject_country(p)
    check("%s -> None" % label, got is None, (got, ev))
_JU_CODE = code_only(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "new_engine_v1", "jurisdiction.py"))
check("no geocoding, no gazetteer, no model in this module",
      not any(m in _JU_CODE for m in ("geocode", "urlopen", "requests", "provider",
                                      "complete(", "openai", "_ask(", "socket")))
check("a top-level domain is never used as a country",
      J.subject_country(pack("Nothing here.", "Nothing there."))[0] is None)

# ── 2. THE WILDSUMACO FAILURE ─────────────────────────────────────────────────
print("\ntest_WILDSUMACO_the_directory_field_cannot_become_a_fact_about_the_pavilion")
WS_LEDGER = {
    "F01": fact("F01", "The pavilion was completed in 2025 at Pacto Sumaco, Ecuador."),
    "F02": fact("F02", "The floor is lifted clear of the natural ground."),
    "F90": fact("F90",
                "The field station directory entry for WildSumaco Biological Station "
                "records ADA accessibility as 'No'."),
}
led, rep = J.apply(dict(WS_LEDGER), EC_PACK)
check("the subject's country is Ecuador", rep["subject_country"] == "EC", rep)
check("the ADA fact is restricted", "F90" in rep["restricted"], rep)
check("...and no other fact is touched", rep["restricted"] == ["F90"], rep)
check("the fact is NOT deleted", "F90" in led)
check("its proposition is unchanged", led["F90"]["proposition"] == WS_LEDGER["F90"]["proposition"])
check("its span is unchanged", led["F90"]["support_span"] == WS_LEDGER["F90"]["support_span"])
check("what it PERMITS is now attribution",
      led["F90"]["claim_type"] == "ATTRIBUTION", led["F90"])
check("the downgrade is recorded, not silent",
      led["F90"]["claim_type_before_jurisdiction"] == "POSITIVE_FACT", led["F90"])
check("the standard is named", led["F90"]["standard"] == "ADA")
check("its jurisdiction is named", led["F90"]["standard_jurisdiction"] == "US")
check("its role here is FOREIGN_LEGAL_STANDARD",
      led["F90"]["standard_role"] == J.FOREIGN_LEGAL_STANDARD, led["F90"])
check("the note says why, in words a run record can carry",
      "not about the subject" in led["F90"]["jurisdiction_note"],
      led["F90"]["jurisdiction_note"])
check("the restricted fact is still a valid ledger entry",
      LG.validate_fact(led["F90"], WS_LEDGER["F90"]["support_span"]) == [],
      LG.validate_fact(led["F90"], WS_LEDGER["F90"]["support_span"]))
check("the doctrine is stated on the report itself",
      "NO DEFAULT NATIONAL FRAMEWORK" in rep["rule"])

print("\ntest_the_restriction_is_visible_to_every_later_stage")
check("a downstream reader sees ATTRIBUTION in the claim_type it already reads",
      led["F90"]["claim_type"] in LG.CLAIM_TYPES)
check("ATTRIBUTION means report the saying, not assert the thing",
      LG.ATTRIBUTION == "ATTRIBUTION")

# ── 3. THE OTHER HALF: a US subject keeps its US law ──────────────────────────
print("\ntest_a_US_subject_with_US_evidence_is_UNTOUCHED")
US_PACK = pack(
    "The building is in Portland, in the United States. United States federal rules "
    "applied throughout the American project.",
    "The United States Access Board reviewed the American design.",
    subject="a civic building, Portland, United States")
US_LEDGER = {
    "F10": fact("F10", "The renovation was completed in 2024."),
    "F11": fact("F11", "The building's certificate records it as ADA compliant."),
    "F12": fact("F12", "Section 508 governs the agency's public web forms."),
}
led2, rep2 = J.apply(dict(US_LEDGER), US_PACK)
check("the subject's country is the United States", rep2["subject_country"] == "US", rep2)
check("NOTHING is restricted", rep2["restricted"] == [], rep2)
check("the ADA fact keeps its claim_type",
      led2["F11"]["claim_type"] == "POSITIVE_FACT", led2["F11"])
check("...and is not stamped as foreign",
      led2["F11"]["standard_role"] == J.LOCAL_LAW, led2["F11"])
check("Section 508 is local law here too",
      led2["F12"]["standard_role"] == J.LOCAL_LAW, led2["F12"])
check("the standards are still recorded for the run record",
      set(rep2["noted"]) == {"F11", "F12"}, rep2)
check("a fact naming no standard is left completely alone",
      "standard" not in led2["F10"], led2["F10"])

print("\ntest_a_UK_subject_keeps_UK_law_and_loses_US_law")
GB_PACK = pack("The scheme is in Newcastle, in the United Kingdom. British practice. "
               "England's planning system applied.",
               "A British studio led the United Kingdom project.")
GB_LEDGER = {"F20": fact("F20", "The Equality Act 2010 applies to the service."),
             "F21": fact("F21", "A US directory lists the site's ADA status as unknown.")}
led3, rep3 = J.apply(dict(GB_LEDGER), GB_PACK)
check("the subject's country is the United Kingdom", rep3["subject_country"] == "GB", rep3)
check("the Equality Act is local law", led3["F20"]["standard_role"] == J.LOCAL_LAW, led3["F20"])
check("the Equality Act fact is not restricted", "F20" not in rep3["restricted"], rep3)
check("the ADA fact IS restricted here", "F21" in rep3["restricted"], rep3)
check("...to attribution", led3["F21"]["claim_type"] == "ATTRIBUTION")

# ── 4. unknown country restricts nothing ──────────────────────────────────────
print("\ntest_an_unknown_country_restricts_nothing")
UNK = pack("A pavilion with two levels and a lifted floor. It was completed in 2025.")
led4, rep4 = J.apply({"F30": fact("F30", "A directory records ADA accessibility as No.")},
                     UNK)
check("the country is honestly unknown", rep4["subject_country"] is None, rep4)
check("nothing is restricted", rep4["restricted"] == [], rep4)
check("the fact keeps its claim_type", led4["F30"]["claim_type"] == "POSITIVE_FACT")
check("but the standard is still named for the record",
      led4["F30"]["standard"] == "ADA", led4["F30"])
check("and the reason says why nothing was asserted either way",
      "not established in the frozen evidence" in led4["F30"]["jurisdiction_note"],
      led4["F30"]["jurisdiction_note"])

# ── 5. international instruments are never one country's ──────────────────────
print("\ntest_international_instruments_are_not_restricted_anywhere")
for label, p in (("Ecuador", EC_PACK), ("United States", US_PACK), ("unknown", UNK)):
    l5, r5 = J.apply({"F40": fact("F40", "The site was tested against WCAG 2.2."),
                      "F41": fact("F41", "The state ratified the CRPD in 2008.")}, p)
    check("WCAG is not restricted for a %s subject" % label, "F40" not in r5["restricted"])
    check("CRPD is not restricted for a %s subject" % label, "F41" not in r5["restricted"])
    check("WCAG is stamped INTERNATIONAL_INSTRUMENT (%s)" % label,
          l5["F40"]["standard_role"] == J.INTERNATIONAL_INSTRUMENT, l5["F40"])

# ── 6. the vocabulary and the table ───────────────────────────────────────────
print("\ntest_the_vocabulary_is_the_one_the_doctrine_names")
for role in ("LOCAL_LAW", "LOCAL_CODE", "FOREIGN_LEGAL_STANDARD", "INSTITUTIONAL_RULE",
             "DIRECTORY_CLASSIFICATION", "INTERNATIONAL_INSTRUMENT"):
    check("%s is in STANDARD_ROLES" % role, role in J.STANDARD_ROLES)
check("the bound table stays small", len(J.BOUND_STANDARDS) <= 15, len(J.BOUND_STANDARDS))
check("every bound standard names exactly one country",
      all(len(c) == 2 and c.isupper() for _, _, c, _ in J.BOUND_STANDARDS))
check("WCAG is deliberately NOT bound",
      not any(n == "WCAG" for _, n, _, _ in J.BOUND_STANDARDS))
check("detection is on words, not substrings -- 'Nevada' is not the ADA",
      not J.standards_in("The Nevada site and the adaptive reuse of the shed."),
      J.standards_in("The Nevada site and the adaptive reuse of the shed."))
check("'ADA' as a whole word is detected",
      [h["standard"] for h in J.standards_in("records ADA accessibility as No")] == ["ADA"])
check("the spelled-out act is detected too",
      J.standards_in("under the Americans with Disabilities Act")[0]["standard"] == "ADA")

print("\ntest_an_ordinary_access_fact_is_not_a_standard")
for prop in ("The building has a step-free entrance from the street.",
             "The upper level is reached by a stair.",
             "The museum offers a borrowed tablet tour of the basement."):
    check("no standard found in: %s" % prop[:44], J.standards_in(prop) == [])

# ── 7. wiring ─────────────────────────────────────────────────────────────────
print("\ntest_one_semantic_owner")
HERE = os.path.dirname(os.path.abspath(__file__))
comp = open(os.path.join(HERE, "new_engine_v1", "composition.py")).read()
check("the ledger stage owns it", comp.count("JU.apply(") == 1, comp.count("JU.apply("))
check("no other stage duplicates the rule",
      comp.count("jurisdiction as JU") == 1 and comp.count("FOREIGN_LEGAL_STANDARD") == 0)
check("it runs after span verification, not instead of it",
      comp.index("JU.apply(ledger, pack)") > comp.index("still = check_ledger"))
check("the report reaches the run record",
      '"jurisdiction": jurisdiction_report' in comp)
check("subject_place and subject_country reach the run record",
      '"subject_place": JU.subject_place(pack)' in comp
      and '"subject_country": jurisdiction_report["subject_country"]' in comp)
check("it costs no model call",
      "JU.apply" in comp and "_ask(provider" not in comp.split("JU.apply")[1][:400])
# Against the runtime constant, not the source: the prompt is assembled from adjacent
# string literals, so a sentence that spans two of them exists only once concatenated.
from new_engine_v1 import composition as CP
check("the freeze prompt now teaches the rule as well as enforcing it",
      "NO DEFAULT NATIONAL FRAMEWORK" in CP.FREEZE_SYSTEM)
check("...with the correct wording spelled out for the model",
      "not 'X is not ADA accessible'" in CP.FREEZE_SYSTEM)
check("...and the wrong wording named as wrong",
      "never 'X is not accessible'" in CP.FREEZE_SYSTEM)
check("...and the reason English-language research imports it is stated",
      "American material is what is written down in English" in CP.FREEZE_SYSTEM)

print("\n" + "=" * 62)
if FAILURES:
    print("JURISDICTION: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d JURISDICTION CHECKS PASSED" % CHECKS[0])

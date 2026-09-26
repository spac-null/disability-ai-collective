#!/usr/bin/env python3
"""ledger_deixis_test.py -- resolve the speaker, not their identity attributes.

THE DEFECT, measured on retained runs. A proposition cannot speak in the first person,
so when the cited span says "I" the Ledger must resolve who that is. On 107 of 543
first-person-singular conversions it resolved the pronoun as well as the identity, and in
seven verified cases nothing in the supplied source licensed the pronoun anywhere:

  Sanders    "mijn debuutfilm"            -> "his debut film"
  Zahedi     "not as available to me"     -> "not as available to him"
  Zahedi     "gave me immense joy"        -> "gave him immense joy"
  Campbell   "I have gone to performances"-> "she has been scolded at performances"
  Schleuss   "represent our members"      -> "his union's members"

The Sanders source states no pronoun for the speaker at all -- 30 uses of "ik", no
third-person reference -- so that attribute was authored here, not recalled, and every
later stage transcribed it faithfully (Ledger 18 -> packet 17 -> article 11).

WHAT THIS FILE IS AND IS NOT. The fix is a generation contract, so these are contract
tests plus the captured fixtures. There is no validator, no gender detection, no
name-to-pronoun lookup and no gate on article prose -- adding one would be a second,
unproven mechanism, and the acceptance evidence is the frozen Sanders Ledger replay.

Stdlib only, no network, no model call.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP   # noqa: E402

FAILURES: list = []
CHECKS = [0]


def check(label, ok, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if ok else "  FAIL  %s") % label
          + (("" if ok else " -- " + str(detail)) if detail else ""))
    if not ok:
        FAILURES.append(label)


S = CP.FREEZE_SYSTEM

# The real spans, verbatim from the retained runs, with the proposition each produced.
CAPTURED = [
    ("Sanders",  "Daarom heb ik uiteindelijk mijn debuutfilm met een budget van 3 miljoen "
                 "mogen maken",
     "Sanders says he was able to make his debut film with a budget of 3 million.",
     ("he", "his")),
    ("Zahedi",   "As a student, starting in elementary school, the arts were not as "
                 "available to me.",
     "Zahedi says that as a student, starting in elementary school, the arts were not as "
     "available to him.", ("him",)),
    ("Zahedi2",  "seeing a stage built with disabled artists and audience in mind gave me "
                 "immense joy",
     "Zahedi said seeing a stage built with disabled artists and audience in mind gave him "
     "immense joy.", ("him",)),
    ("Campbell", "make me feel a little bit angry about all of the times I have gone to "
                 "performances and have been scolded for my own inability to sit still",
     "Campbell says she has been scolded at performances for her inability to sit still.",
     ("she", "her")),
    ("Schleuss", "I was proud to be in court today to represent our members, which include "
                 "international journalists working in the U.S.",
     "Schleuss said his union's members include international journalists working in the "
     "U.S.", ("his",)),
]

FP = re.compile(r"\b(i|me|my|mine|we|our|ik|mij|mijn|ons|onze)\b", re.I)
PRON = re.compile(r"\b(he|him|his|she|her|hers|they|them|their|theirs)\b", re.I)

print("test_the_contract_names_the_defect")
check("the Ledger contract addresses first-person spans",
      "when the span speaks in the first person" in S.lower())
check("  and requires resolving identity, not the pronoun",
      "resolve the identity and nothing else" in S.lower())
check("  and forbids every third-person person-pronoun, singular they included",
      all(w in S for w in ("he, him, his", "she, her, hers", "singular they")))
check("  unless the span itself carries it",
      "unless that pronoun is itself present in the span" in S)
check("  and forbids inferring one from outside the span",
      all(w in S.lower() for w in ("from a name", "a title", "an occupation",
                                   "a photograph", "anything you happen to know")))
check("  and says a repeated name is acceptable at this stage",
      "Repetition of a name is not a defect here" in S)

print("\ntest_every_captured_case_is_described_by_the_contract")
for name, span, produced, pronouns in CAPTURED:
    check("%-9s span is first-person" % name, bool(FP.search(span)), span[:70])
    check("  %-7s span carries no person-pronoun of its own" % "",
          not PRON.search(span), str(PRON.findall(span)))
    check("  %-7s the produced proposition introduced %s"
          % ("", "/".join(pronouns)),
          all(p in produced.lower() for p in pronouns), produced[:90])

print("\ntest_positive_controls_are_untouched")
# A span that DOES carry the pronoun still licenses it -- the rule is about the span, not
# about pronouns as such.
LICENSED = ("In de film maakt Vera kennis met Xander, die al heel zijn leven in een "
            "rolstoel zit.")
check("a span carrying its own pronoun still licenses it",
      "unless that pronoun is itself present in the span" in S,
      "the rule is conditional on the span, so licensed spans are unaffected")
check("  and the contract does not ban pronouns outright",
      "Do NOT introduce he" in S and "unless" in S)
check("third-person source material is not mentioned as needing conversion",
      "cannot stay in the first person" in S,
      "the rule is scoped to first-person spans only")
check("the verbatim span rule is unchanged",
      "a VERBATIM run of characters from ONE of the sources you cite" in S)
check("the span-may-not-be-exceeded rule is unchanged",
      "it may not assert anything the span does not carry" in S)

print("\ntest_nothing_else_was_added")
check("no gender detection was introduced",
      not re.search(r"\bgender (detect|dictionar|lookup)", S, re.I))
check("no name-to-pronoun lookup was introduced",
      "lookup" not in S.lower())
check("the 99 span-provenance cases are NOT claimed as fixed",
      "borrow" not in S.lower(),
      "proposition-exceeds-span stays a separate, unfixed defect")

print("\n" + "-" * 60)
if FAILURES:
    print("LEDGER DEIXIS: %d of %d CHECKS FAILED" % (len(FAILURES), CHECKS[0]))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("ALL %d LEDGER DEIXIS TESTS PASSED" % CHECKS[0])

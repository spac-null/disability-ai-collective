#!/usr/bin/env python3
"""package_quotation_test.py -- quotation marks are paired before they are measured.

The screen exists to refuse a quotation the article does not contain. It must keep doing
that. What it must NOT do is invent one out of the package's own connective prose, which
is what happened whenever a field quoted two short terms.
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


def quotes(field, article):
    return [e for e in CP.package_additions(field, article) if "quotation" in e]


ARTICLE = (
    'A gap sits between the word "stoppage" and the word "thence". Ellis asks what it '
    'would mean to "aster" a stutter rather than master it. He offers the phrase: '
    '"I speak with an Aster. My speech is home to a hundred blooms." The advertisements '
    'name men who reportedly "stutter" or speak with "blockages".'
)

print("THE BUG: connective prose between two quoted terms is not a quotation")
BUG = ('A gap sits between "stoppage" and "thence" in Ellis\'s 144-page book, whose pages '
       'carry musical scores, and he asks what it means to "aster" a stutter.')
check("a field quoting two short terms reports nothing", quotes(BUG, ARTICLE) == [])
check("three quoted terms in one field also report nothing",
      quotes('He uses "stutter", "blockages" and "aster" throughout the collection here.',
             ARTICLE) == [])

print("\nTHE SCREEN STILL DOES ITS JOB")
check("a long quotation the article does not contain is still refused",
      len(quotes('He wrote "this sentence appears nowhere in the article at all" here.',
                 ARTICLE)) == 1)
check("a long quotation the article does contain passes",
      quotes('He offers the phrase: "I speak with an Aster. My speech is home to a '
             'hundred blooms."', ARTICLE) == [])
check("an invented quotation alongside two real short ones is still caught",
      len(quotes('Between "stoppage" and "thence" he wrote "a line the article never '
                 'contains anywhere".', ARTICLE)) == 1)

print("\nEDGES")
check("short quoted terms stay unchecked, as before",
      quotes('The word "aster" matters.', ARTICLE) == [])
check("no quotation marks at all", quotes("A plain sentence, nothing quoted.",
                                          ARTICLE) == [])
check("an unbalanced trailing quote reports nothing",
      quotes('He said "something long enough to be measured here', ARTICLE) == [])
check("empty field", quotes("", ARTICLE) == [])
check("curly quotes behave the same",
      quotes('He wrote “this sentence appears nowhere in the article at all”.',
             ARTICLE) != [])

print("\n" + "-" * 60)
if FAILED:
    print("FAILED: %d" % len(FAILED))
    for f in FAILED:
        print("   - %s" % f)
    sys.exit(1)
print("ALL PACKAGE QUOTATION TESTS PASSED")

#!/usr/bin/env python3
"""pull_quote_test.py -- the pull quote is the article's own sentence, or it is nothing.

The contract has two halves and both are tested here:

  1. a quote that is NOT verbatim never reaches the page, at either of the two places
     that could let it through -- the package's own check and the publisher's;
  2. a missing or refused quote never costs an article its publication.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import publish_best as PUB                          # noqa: E402
from new_engine_v1 import composition as CP         # noqa: E402

FAILED = []


def check(name, cond):
    print("  %s  %s" % ("PASS" if cond else "FAIL", name))
    if not cond:
        FAILED.append(name)


ARTICLE = (
    "# The staff that bends around its own notes\n\n"
    "On the eighth floor of the Whitney, oversized musical staff lines undulate across "
    "several long expanses of white gallery wall.\n\n"
    "The staff lines the reader met as a witty drawing are a measuring notation, and the "
    "notes hover below or above the lines that would give them their value.\n\n"
    "Kim has described the staff lines as stand-ins for standard operating procedures.\n"
)
TURN = ("The staff lines the reader met as a witty drawing are a measuring notation, and "
        "the notes hover below or above the lines that would give them their value.")

print("VERBATIM IS THE CONTRACT")
check("the article's own sentence is accepted",
      CP.pull_quote_failure(TURN, ARTICLE) == "")
check("a tightened rewrite is refused",
      CP.pull_quote_failure(
          "The staff lines are a measuring notation, and the notes hover below or above.",
          ARTICLE) == "not a verbatim sentence of the article")
check("a plausible invention is refused",
      CP.pull_quote_failure(
          "Kim has said the notation itself is the disability, not the hearing.",
          ARTICLE) == "not a verbatim sentence of the article")
check("two sentences welded together are refused",
      CP.pull_quote_failure(
          "Kim has described the staff lines as stand-ins for standard operating "
          "procedures, and the notes hover below or above the lines.",
          ARTICLE) == "not a verbatim sentence of the article")
check("punctuation and whitespace differences are tolerated",
      CP.pull_quote_failure(TURN.replace(", and", ",  and"), ARTICLE) == "")
check("empty is reported as empty", CP.pull_quote_failure("", ARTICLE) == "empty")
check("a fragment is refused", "under the" in CP.pull_quote_failure("a notation.",
                                                                    ARTICLE))

print("\nAN UNUSABLE QUOTE IS DROPPED, NEVER ESCALATED")
good = {"title": "T", "dek": "d", "homepage_excerpt": "h",
        "meta_description": "m", "social_hook": "s", "pull_quote": TURN}
bad = dict(good, pull_quote="A sentence the article never contained at all, invented.")
check("a valid quote survives cleaning",
      CP._clean_package(good, ARTICLE).get("pull_quote") == TURN)
cleaned = CP._clean_package(bad, ARTICLE)
check("an invalid quote is removed", "pull_quote" not in cleaned)
check("and the reason is recorded", "not a verbatim" in cleaned.get(
    "pull_quote_rejected", ""))
check("the five required lines are untouched either way",
      all(cleaned.get(f) for f in CP.PACKAGE_FIELDS))
check("pull_quote is NOT a required field",
      CP.PACKAGE_OPTIONAL_FIELD not in CP.PACKAGE_FIELDS)
check("a package with no pull quote still passes check_package",
      CP.check_package({k: v for k, v in good.items() if k != "pull_quote"},
                       ARTICLE) == CP.check_package(good, ARTICLE))
check("an invented pull quote does NOT make check_package fail the package",
      CP.check_package(bad, ARTICLE) == CP.check_package(good, ARTICLE))

print("\nTHE PUBLISHER PLACES IT, OR LEAVES THE ARTICLE ALONE")
body = ARTICLE
out, note = PUB.place_pull_quote(body, TURN)
MARK = PUB.PULLQUOTE_OPEN + TURN + PUB.PULLQUOTE_CLOSE
check("the quote is repeated as a pull quote", MARK in out)
check("it is marked decorative for assistive technology",
      'aria-hidden="true"' in out)
check("it is an aside, not a quotation element -- the words are the article's own",
      "<aside" in MARK and "<blockquote" not in out and "\n> " not in out)
check("it lands after the paragraph it came from", out.index(MARK) > out.index(TURN))
check("the original paragraph is untouched", TURN in out.split(MARK)[0])
check("the sentence appears exactly twice in the source", out.count(TURN) == 2)
check("a note says where it went", "placed after paragraph" in note)
check("the body is otherwise unchanged", out.replace("\n\n" + MARK, "") == body)

out2, note2 = PUB.place_pull_quote(body, "not in this article at all, nowhere")
check("a non-verbatim quote is not inserted", out2 == body)
check("and says so", "not found verbatim" in note2)
out3, note3 = PUB.place_pull_quote(body, "")
check("an empty quote changes nothing", out3 == body and note3 == "none offered")
out4, note4 = PUB.place_pull_quote(
    body, "Kim has described the staff lines as stand-ins for standard operating "
          "procedures.")
check("a final-paragraph sentence is skipped", out4 == body)
check("and says why", "final paragraph" in note4)
already = body + "\n\n" + PUB.PULLQUOTE_OPEN + "x" + PUB.PULLQUOTE_CLOSE + "\n"
out5, note5 = PUB.place_pull_quote(already, TURN)
check("an article that already carries a pull quote is left alone", out5 == already)
check("and says why", "already carries" in note5)

ARTICLE_HTML = ARTICLE.replace(TURN, "A & B " + TURN)
out6, _ = PUB.place_pull_quote(ARTICLE_HTML, "A & B " + TURN)
check("an ampersand in the sentence is escaped, not injected",
      "A &amp; B" in out6.split(PUB.PULLQUOTE_OPEN)[1])

# A real body quotation must still be left alone by the styling contract: the publisher
# never converts one, and never treats one as an existing pull quote.
with_bq = body + "\n\n> a real quotation from a source\n"
out7, note7 = PUB.place_pull_quote(with_bq, TURN)
check("a genuine blockquote elsewhere does not block the pull quote",
      PUB.PULLQUOTE_OPEN in out7)
check("and that blockquote is untouched", "> a real quotation from a source" in out7)

print("\n" + "-" * 60)
if FAILED:
    print("FAILED: %d" % len(FAILED))
    for f in FAILED:
        print("   - %s" % f)
    sys.exit(1)
print("ALL PULL QUOTE TESTS PASSED")

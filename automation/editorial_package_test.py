#!/usr/bin/env python3
"""editorial_package_test.py -- the five lines a reader meets before the article.

The first Story Architecture publication shipped with no excerpt, so the homepage card fell
back to Jekyll's automatic excerpt: the article's literal first paragraph, written to be
read second. This stage exists for that gap.

WHAT THIS SUITE IS ABOUT is the thing that makes packaging dangerous rather than merely
absent. A title, a dek and a card are PUBLIC EDITORIAL PROSE, quoted onward by search
engines and social clients, and they can be wrong in the way an article can be wrong: not
by using a word the evidence never granted, but by putting two granted words into a
relation it never asserted. So the deterministic screen is a cheap first pass and the real
check is that the package travels INSIDE the publication bundle, through the gates that
already exist.

Stdlib only, no network.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from new_engine_v1 import composition as CP
import new_engine_candidate as CAND

FAILURES = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    print(("  PASS  %s" if cond else "  FAIL  %s") % label
          + (("" if cond else " -- " + str(detail)) if detail else ""))
    if not cond:
        FAILURES.append(label)


ARTICLE = (
    "The classroom and bird observatory on the upper level of the WildSumaco Research "
    "Pavilion have no locks, and the architects describe them as open to all. The "
    "pavilion is 280 square metres, completed in 2025, at the foot of the Sumaco "
    "volcano.\n\n"
    "The field station directory entry records its ADA accessibility as No. The building "
    "is reached on foot, up a slope, and the upper level is reached by stair.\n\n"
    "Caa Pora Arquitectura ran the construction as a workshop. Community members brought "
    "their understanding of the forest. The site taught while it was still being built.")

GOOD = {"title": "The Upper Room With No Lock And No Ramp",
        "dek": "The architects describe the classroom as open to all. The directory entry "
               "for the same building records its accessibility as No, and the upper "
               "level is reached by stair.",
        "homepage_excerpt": "A research pavilion in the forest was built without locks, "
                            "and its architects call the upper room open to all. Its own "
                            "directory entry records accessibility as No. Openness and "
                            "arrival turn out to be two different questions, and only one "
                            "of them was designed.",
        "meta_description": "A pavilion described as open to all records its own "
                            "accessibility as No, and the upper level is reached by "
                            "stair.",
        "social_hook": "The architects say the upper room is open to all. The directory "
                       "entry for the building records accessibility as No."}


class Prov:
    model = "test"
    url = "http://127.0.0.1:0/v1"

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls.append({"system": system, "user": user})
        if not self.replies:
            raise AssertionError("more calls than the script allows")
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r

        class R:
            text = r if isinstance(r, str) else json.dumps(r)

            def identity(self_):
                return {"provider": "scripted"}
        return R()


print("test_the_screen_is_a_first_pass_and_says_so")
check("a package of the article's own material passes the screen",
      CP.check_package(GOOD, ARTICLE) == [], CP.check_package(GOOD, ARTICLE))
for label, field, value, marker in (
        ("an invented name", "dek", "The pavilion was designed by Goldstein and the "
                                    "directory entry records its accessibility as No.",
         "name"),
        ("an invented number", "dek", "The pavilion is 280 square metres and cost "
                                      "1400000 dollars to build and to equip.", "number"),
        ("an invented quotation", "social_hook",
         'The architect said "we never thought about the stair" when asked.',
         "quotation")):
    errs = CP.check_package(dict(GOOD, **{field: value}), ARTICLE)
    check(label + " is refused", any(marker in e for e in errs), errs)
check("title case is not an addition",
      CP.package_additions("The Upper Room At Wildsumaco", ARTICLE) == [])
check("a possessive is not an addition",
      CP.package_additions("WildSumaco's upper room", ARTICLE) == [])

print("\ntest_an_unsupported_RELATION_survives_the_screen_and_must_be_caught_downstream")
# Every word is in the article. The relation is not: the article says the entry records
# accessibility as No and that the architects call the room open to all. It never says one
# is a lie, and it never says the station's record is a claim about the pavilion.
RELATION = dict(GOOD,
                dek="The architects lied: the pavilion has no accessibility because the "
                    "directory entry records the field station as No.")
check("the cheap screen does NOT catch it",
      CP.check_package(RELATION, ARTICLE) == [], CP.check_package(RELATION, ARTICLE))
bundle = CP.bundle_text(ARTICLE, RELATION)
check("so the bundle carries the dek to the gates", RELATION["dek"] in bundle)
check("and every other surface too",
      all(v in bundle for v in RELATION.values()))
check("the article is still in the bundle", "Caa Pora Arquitectura" in bundle)
check("the furniture is delimited from the article", "---" in bundle
      and "PUBLICATION FURNITURE" in bundle)
check("a finding quoting the dek is attributed to DEK",
      CP.surface_of(RELATION["dek"][:60], RELATION) == "DEK")
check("a finding quoting the article is attributed to ARTICLE",
      CP.surface_of("Community members brought their understanding", RELATION)
      == CP.ARTICLE_SURFACE)
art, pkg = CP.split_by_surface(
    [{"quote": RELATION["dek"][:60], "classification": "TRUE_UNSUPPORTED"},
     {"quote": "Community members brought their understanding", "classification": "X"}],
    RELATION)
check("findings split by surface", len(art) == 1 and len(pkg) == 1)
check("and each one is stamped", pkg[0]["surface"] == "DEK")

print("\ntest_the_stage_writes_a_package_and_one_repair_at_most")
p = Prov({"package": GOOD})
out = CP.editorial_package(p, ARTICLE, {"story_spine": "who may pass"},
                           {"lens_claim": "the record contradicts the description"})
check("it passes", out["status"] == CP.PASS, out.get("reason"))
check("status OK", out["package_status"] == CP.PACKAGE_OK)
check("one model call, no repair", out["model_calls"] == 1 and out["repairs"] == 0)
check("it was given the finished article",
      "THE FINISHED ARTICLE" in p.calls[0]["user"] and "no locks" in p.calls[0]["user"])
check("and the lens it stands on", "contradicts the description" in p.calls[0]["user"])
check("the prompt forbids new relations, not just new words",
      "adjacency into contradiction" in p.calls[0]["system"]
      and "widen scope" in p.calls[0]["system"])

bad = dict(GOOD, dek="Goldstein designed it and the entry records No.")
p = Prov({"package": bad}, {"package": GOOD})
out = CP.editorial_package(p, ARTICLE, {}, {})
check("a refused package is repaired once", out["status"] == CP.PASS, out.get("reason"))
check("two model calls", out["model_calls"] == 2 and out.get("repaired") is True)

p = Prov({"package": bad}, {"package": bad})
out = CP.editorial_package(p, ARTICLE, {}, {})
check("a second failure gives up on the package, not the article",
      out["status"] == CP.SKIPPED and out["package"] is None)
check("and is REFUSED, not a technical failure",
      out["package_status"] == CP.PACKAGE_REFUSED)

print("\ntest_a_technical_failure_is_not_an_editorial_rejection")
p = Prov("not json", "still not json")
out = CP.editorial_package(p, ARTICLE, {}, {})
check("an unparseable reply does not raise", out["status"] == CP.SKIPPED)
check("it is TECHNICAL_FAILURE", out["package_status"] == CP.PACKAGE_TECHNICAL_FAILURE)
check("it is not a HOLD", out["status"] != CP.HOLD)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "new_engine_production.py")).read()
check("and production withholds publication rather than shipping a fallback card",
      "_pkg_missing" in src and "publication withheld for owner review" in src)
check("the run reports it for the owner",
      '"owner_review": bool(failure_stage is None and not package_out)'
      in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "new_engine_v1", "composition.py")).read())

print("\ntest_placement_and_version_coherence")
comp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "new_engine_v1", "composition.py")).read()
check("the package is written before the factual gates",
      CP.STAGES.index(CP.PACKAGE) < CP.STAGES.index(CP.SAFETY)
      < CP.STAGES.index(CP.GROUNDING) < CP.STAGES.index(CP.FACT_CHECK), CP.STAGES)
check("and after the prose finish, so it sells the text that ships",
      CP.STAGES.index(CP.PROSE_FINISH) < CP.STAGES.index(CP.PACKAGE))
check("the grounder reads the bundle, not the bare article",
      "ground_candidate(P, bundle_text(final, pkg)" in comp)
check("the fact check reads the bundle too",
      "(fact_check_fn or fact_check_unavailable)(bundle_text(final, pkg))" in comp)
i_fc = comp.index("fc = record(FACT_CHECK,")
tail = comp[i_fc:comp.index("return out(article=final")]
check("NO ARTICLE REWRITE HAPPENS AFTER THE FACT CHECK",
      "prose_finish(" not in tail and "grounding_repair(" not in tail
      and "write_article(" not in tail and "continuity_pass(" not in tail)
check("a discarded polish discards its package with it",
      "pkg = make_package(final)" in comp.split("polish_discarded_at_safety")[0]
      .split("st[PROSE_FINISH][\"discarded_at_safety\"]")[-1])
check("and the surface that published is recorded",
      '"article_surface": article_surface' in comp
      and CP.PRE_POLISH_FALLBACK in comp)
check("with a hash of each half of the bundle",
      '"article_sha256"' in comp and '"bundle_sha256"' in comp)

print("\ntest_the_package_reaches_the_front_matter")
meta = {"generated_at": "2026-09-06T10:00:00", "decision": "ACCEPT", "run": "r",
        "source_sha256": "abc", "discovery_hash": "d", "article_form_hash": "",
        "grounding_status": "settled", "grounding_unsupported": 0,
        "provider_model": "claude-opus-5"}
fm = CAND.build_frontmatter(title=GOOD["title"], author="Maya Flux", engine_meta=meta,
                            rehearsal=False, safety={"publication_eligible": True},
                            package=GOOD)
check("the homepage excerpt is written as `excerpt`",
      ("excerpt: %s" % json.dumps(GOOD["homepage_excerpt"])) in fm, fm[:400])
check("the dek is written", "dek: " in fm)
check("the meta description and the social hook are written",
      "meta_description: " in fm and "social_hook: " in fm)
check("the title is the package's", ('title: %s' % json.dumps(GOOD["title"])) in fm)
fm_none = CAND.build_frontmatter(title="A Title", author="Maya Flux", engine_meta=meta,
                                 rehearsal=False, safety={"publication_eligible": True},
                                 package=None)
check("no package means no invented fields",
      "excerpt:" not in fm_none and "dek:" not in fm_none)

layout = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "_layouts", "post.html")).read()
check("the dek renders as the article's standfirst", "page.dek" in layout)
home = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "index.html")).read()
check("the homepage card consumes the explicit excerpt", "post.excerpt" in home)

print("\n" + "-" * 60)
if FAILURES:
    print("%d FAILURE(S):" % len(FAILURES))
    for f in FAILURES:
        print("  - " + f)
    sys.exit(1)
print("ALL %d EDITORIAL PACKAGE TESTS PASSED" % CHECKS[0])

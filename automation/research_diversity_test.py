"""
research_diversity_test.py -- the fetch order, the budget's publisher reserve, and the
diagnosis page.

WHY. On 2026-09-30 two of the morning's three pitches held at HOLD_INSUFFICIENT_RESEARCH
with `independent=0`, and neither was scarce. The Franklin/Inuit run found an Archaeology
magazine feature, four papers in the journal Arctic and a Cambridge Polar Record PDF, and
fetched none of them: the first five candidates were the anchor's own sibling pages and
five is MAX_FETCHED_SOURCES. The Istat run found the Italian statute databases at
candidates 11 and 12 and fetched three istat.it pages instead.

These tests run against BOTH real frozen packs, so they fail if the ordering ever stops
protecting the property the sufficiency gate requires.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import research as RS            # noqa: E402

FAILURES: list = []

# The two runs this change exists for. Skipped, loudly, if the evidence is gone.
INUIT = pathlib.Path("/srv/data/cripminds-new-engine-v1/"
                     "production-20260930T070306Z-54ca6694")
ISTAT = pathlib.Path("/srv/data/cripminds-new-engine-v1/"
                     "production-20260930T070704Z-d2be4737")


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def pack_of(d: pathlib.Path):
    p = d / "RESEARCH_PACK.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))["payload"]


def test_round_robin_is_stable_and_lossless() -> None:
    c = ["https://a.com/1", "https://a.com/2", "https://b.org/1",
         "https://a.com/3", "https://c.net/1"]
    out = RS.by_publisher_diversity(c)
    check("no candidate is lost", sorted(out) == sorted(c), out)
    check("none is duplicated", len(out) == len(set(out)), out)
    check("the first candidate of the first publisher still leads",
          out[0] == "https://a.com/1", out)
    check("every publisher is reached before any second",
          [RS.registrable(u) for u in out[:3]] == ["a.com", "b.org", "c.net"],
          [RS.registrable(u) for u in out])
    check("order inside a publisher is preserved",
          [u for u in out if RS.registrable(u) == "a.com"]
          == ["https://a.com/1", "https://a.com/2", "https://a.com/3"], out)
    check("an empty list is handled", RS.by_publisher_diversity([]) == [])
    single = ["https://a.com/1", "https://a.com/2"]
    check("a single-publisher list is returned unchanged",
          RS.by_publisher_diversity(single) == single)


def test_the_inuit_run_would_have_reached_independent_sources() -> None:
    p = pack_of(INUIT)
    if p is None:
        check("INUIT evidence present", False, str(INUIT))
        return
    cands = p["candidates_considered"]
    anchor_pub = "canada.ca"
    old = cands[:RS.MAX_FETCHED_SOURCES]
    new = RS.by_publisher_diversity(cands)[:RS.MAX_FETCHED_SOURCES]
    old_ind = {RS.registrable(u) for u in old} - {anchor_pub}
    new_ind = {RS.registrable(u) for u in new} - {anchor_pub}
    check("what actually happened: zero independent publishers in the first five",
          not old_ind, sorted(old_ind))
    check("with the fix the first five reach independent publishers",
          len(new_ind) >= 2, sorted(new_ind))
    check("the journal Arctic is now reached",
          any("ucalgary" in u for u in new), new)
    check("the candidate SET is unchanged -- only the order",
          sorted(RS.by_publisher_diversity(cands)) == sorted(cands))


def test_the_istat_run_would_have_reached_the_statute_databases() -> None:
    p = pack_of(ISTAT)
    if p is None:
        check("ISTAT evidence present", False, str(ISTAT))
        return
    cands = p["candidates_considered"]
    new = RS.by_publisher_diversity(cands)[:RS.MAX_FETCHED_SOURCES]
    pubs = [RS.registrable(u) for u in new]
    check("what actually happened: 10 of 12 candidates were the anchor's publisher",
          sum(1 for u in cands if RS.registrable(u) == "istat.it") == 10)
    check("with the fix the statute databases are reached in the first three",
          {"normattiva.it", "gazzettaufficiale.it"} <= set(pubs[:3]), pubs)


def test_a_repeat_publisher_yields_budget_to_an_unseen_one() -> None:
    """The second half of the same defect: ordering gets an independent source FETCHED,
    and the pack budget could still drop it in favour of a publisher already present."""
    # Real words, because excerpts are verified verbatim against the text the pack
    # CARRIES -- a fixture of "yyyy" would be dropped by verified_excerpts and the
    # independence count would be zero for a reason that has nothing to do with budget.
    gov = ("The department published its own account of the survey. " * 300)[:12000]
    jrn = ("An independent review of the survey reached a different conclusion. " * 100)
    EXCERPT = "An independent review of the survey reached a different conclusion."
    anchor = {"url": "https://anchor.gov/a", "text": gov[:7000], "accessed_at": "t",
              "title": "", "canonical_url": ""}
    fetched = [
        {"source_id": "S1", "url": "https://anchor.gov/b", "text": gov,
         "publisher": "anchor.gov", "status": "ok", "accessed_at": "t", "title": "",
         "canonical_url": "", "sha256": ""},
        {"source_id": "S2", "url": "https://anchor.gov/c", "text": gov,
         "publisher": "anchor.gov", "status": "ok", "accessed_at": "t", "title": "",
         "canonical_url": "", "sha256": ""},
        {"source_id": "S3", "url": "https://journal.org/x", "text": jrn[:6000],
         "publisher": "journal.org", "status": "ok", "accessed_at": "t", "title": "",
         "canonical_url": "", "sha256": ""},
    ]
    assessment = {"sources": [
        {"source_id": "S1", "role": "PRIMARY", "relation": "extends",
         "excerpts": ["The department published its own account of the survey."]},
        {"source_id": "S2", "role": "PRIMARY", "relation": "extends",
         "excerpts": ["The department published its own account of the survey."]},
        {"source_id": "S3", "role": "INDEPENDENT", "relation": "complicates",
         "excerpts": [EXCERPT]},
    ]}
    pack = RS.build_pack(anchor=anchor, scoped={}, fetched=fetched,
                         assessment=assessment,
                         searched={"queries": [], "candidates": [], "failures": []})
    pubs = [s["publisher"] for s in pack["sources"]]
    check("the independent publisher survives the budget", "journal.org" in pubs, pubs)
    check("it carries usable text",
          next(s["content_length"] for s in pack["sources"]
               if s["publisher"] == "journal.org") >= 1000,
          [(s["source_id"], s["content_length"]) for s in pack["sources"]])
    check("the pack reports it as independent",
          pack["coverage"]["independent_publishers"] >= 1, pack["coverage"])
    check("the total still respects the budget",
          sum(s["content_length"] for s in pack["sources"]) <= RS.PACK_TEXT_BUDGET,
          sum(s["content_length"] for s in pack["sources"]))


def test_search_backend_selection_fails_closed() -> None:
    check("the default backend is unchanged",
          RS.current_search_backend({}) == RS.SEARCH_BACKEND_SONAR)
    check("sonar still resolves",
          RS.current_search_backend({"CRIPMINDS_SEARCH_BACKEND": "sonar"})
          == RS.SEARCH_BACKEND_SONAR)
    check("the search backend resolves when set",
          RS.current_search_backend({"CRIPMINDS_SEARCH_BACKEND": "perplexity_search"})
          == RS.SEARCH_BACKEND_PERPLEXITY)
    try:
        RS.current_search_backend({"CRIPMINDS_SEARCH_BACKEND": "perplexity"})
        check("an unknown backend fails closed", False, "no raise")
    except RS.ResearchError:
        check("an unknown backend fails closed", True)


def test_perplexity_results_yield_urls_only() -> None:
    """Snippets and titles must not cross the boundary: only fetched bytes carry facts."""
    calls = []

    def fake_post(url, key, payload, timeout):
        calls.append({"url": url, "payload": payload})
        return {"id": "x", "results": [
            {"title": "A", "url": "https://a.org/1", "snippet": "text we must not keep",
             "date": "2024-01-01", "last_updated": None},
            {"title": "B", "url": "https://b.org/2", "snippet": "nor this"},
            {"title": "dupe", "url": "https://a.org/1", "snippet": "nor this"},
            {"title": "junk", "url": "not-a-url", "snippet": ""},
        ]}

    real = RS._post_to
    RS._post_to = fake_post
    try:
        out = RS.perplexity_search_urls("a query", api_key="test-key")
    finally:
        RS._post_to = real

    check("it posts to the documented search endpoint",
          calls[0]["url"] == "https://api.perplexity.ai/search", calls[0]["url"])
    check("no path is appended to it", not calls[0]["url"].endswith("/chat/completions"))
    check("the request carries the documented parameter names",
          set(calls[0]["payload"]) == {"query", "max_results", "search_type"},
          calls[0]["payload"])
    check("max_results is inside the documented 1-50 range",
          1 <= calls[0]["payload"]["max_results"] <= 50,
          calls[0]["payload"]["max_results"])
    check("search_type is a documented value",
          calls[0]["payload"]["search_type"] in ("web", "fast", "people"))
    check("only URLs are returned", out == ["https://a.org/1", "https://b.org/2"], out)
    check("no snippet or title survives the call",
          not any("must not keep" in x or x == "A" for x in out), out)
    check("a malformed entry is dropped rather than raising", "not-a-url" not in out)


def test_the_two_backends_share_one_contract() -> None:
    """search_urls returns a plain list of URLs whichever backend served it, so nothing
    downstream -- the cap, the diversity ordering, the fetch, the pack -- can tell."""
    def fake_pplx(query, *, api_key="", timeout=60):
        return ["https://x.org/1", "https://y.org/2"]

    real_b, real_f = RS.current_search_backend, RS.perplexity_search_urls
    RS.current_search_backend = lambda env=None: RS.SEARCH_BACKEND_PERPLEXITY
    RS.perplexity_search_urls = fake_pplx
    try:
        out = RS.search_urls("q", api_key="an-openrouter-key")
    finally:
        RS.current_search_backend, RS.perplexity_search_urls = real_b, real_f
    check("the search backend is used when selected",
          out == ["https://x.org/1", "https://y.org/2"], out)
    check("it is a plain list of strings",
          isinstance(out, list) and all(isinstance(u, str) for u in out))


def test_no_single_query_owns_the_candidate_list() -> None:
    """The Search API returns up to PERPLEXITY_MAX_RESULTS a query; without interleaving
    the first query alone would fill MAX_CANDIDATE_URLS -- the same first-come defect as
    the fetch order, one stage earlier."""
    q1 = ["https://one.org/%d" % i for i in range(10)]
    q2 = ["https://two.org/%d" % i for i in range(10)]
    q3 = ["https://three.org/%d" % i for i in range(10)]
    out = RS.round_robin([q1, q2, q3])
    check("nothing is lost", sorted(out) == sorted(q1 + q2 + q3))
    check("the first twelve cover all three queries",
          {RS.registrable(u) for u in out[:12]} == {"one.org", "two.org", "three.org"},
          out[:12])
    check("each query contributes equally to the first twelve",
          [RS.registrable(u) for u in out[:12]].count("one.org") == 4,
          [RS.registrable(u) for u in out[:12]])
    check("uneven groups are handled",
          RS.round_robin([["a"], ["b", "c", "d"]]) == ["a", "b", "c", "d"])
    check("an empty group is skipped", RS.round_robin([[], ["a"]]) == ["a"])
    check("no groups at all is empty", RS.round_robin([]) == [])


def test_the_budget_is_shared_not_taken_first_come() -> None:
    """production-20260930T073754Z-54ca6694 fetched seven sources and carried three."""
    budget = 32_709                         # 40,000 less that run's 7,291-char anchor
    want = [("S%d" % i, 12_000) for i in range(1, 8)]
    give, dropped = RS.allocate_budget(want, budget, 1_000)
    check("every one of the seven is carried", not dropped, dropped)
    check("none is below the useful floor", all(v >= 1_000 for v in give.values()), give)
    check("the budget is not exceeded", sum(give.values()) <= budget, sum(give.values()))
    # Equal to within the rounding remainder, and the remainder goes to the most valuable
    # source rather than being lost -- so the spread is never more than budget % n.
    check("they share it evenly to within the rounding remainder",
          max(give.values()) - min(give.values()) <= budget % len(want), give)
    check("the remainder goes to the highest-ranked source",
          give["S1"] == max(give.values()), give)
    check("three carried becomes seven", len(give) == 7, give)

    # A source that wants less than its share returns the rest rather than hoarding it.
    give2, _ = RS.allocate_budget([("A", 500), ("B", 40_000)], 10_000, 100)
    check("a small source takes only what it needs", give2["A"] == 500, give2)
    check("and the remainder goes to the one that can use it",
          give2["B"] == 9_500, give2)

    # When it truly cannot fit, the LEAST valuable is dropped, not the last fetched.
    give3, dropped3 = RS.allocate_budget([("keep", 5_000)] + [("drop%d" % i, 5_000)
                                                              for i in range(9)],
                                         6_000, 1_000)
    check("something is dropped when the budget cannot carry everyone", bool(dropped3))
    check("the most valuable survives", "keep" in give3 and give3["keep"] >= 1_000,
          (give3, dropped3))


def test_a_short_source_is_not_mistaken_for_a_starved_one() -> None:
    """The floor is about TRUNCATION, not about length.

    The first version of allocate_budget dropped any source whose whole text was under
    MIN_USEFUL_CHARS. It emptied four suites at once, and in production it would have
    thrown away the 889-char Calgary page the Franklin rescue legitimately carried -- a
    real source, complete, discarded for being short.
    """
    give, dropped = RS.allocate_budget([("tiny", 200), ("small", 640), ("big", 9_000)],
                                       40_000, 1_000)
    check("nothing is dropped when the budget can carry everything", not dropped, dropped)
    check("a 200-char source is carried whole", give["tiny"] == 200, give)
    check("a 640-char source is carried whole", give["small"] == 640, give)
    check("the long one is carried too", give["big"] == 9_000, give)

    # And a source that IS truncated below the floor is still dropped.
    give2, dropped2 = RS.allocate_budget([("a", 50_000), ("b", 50_000)], 1_500, 1_000)
    check("a genuinely starved source is still dropped", bool(dropped2), dropped2)
    check("and the survivor clears the floor",
          all(v >= 1_000 for v in give2.values()), give2)

    # Every source short: all carried, none dropped.
    give3, dropped3 = RS.allocate_budget([("x", 100), ("y", 100)], 150, 1_000)
    check("a budget smaller than the floor still carries what it can",
          not dropped3 or sum(give3.values()) <= 150, (give3, dropped3))


def test_value_rank_prefers_what_tests_the_claim() -> None:
    counter = RS.source_value_rank(RS.ROLE_COUNTERWEIGHT, "complicates", 9)
    fourth_agreement = RS.source_value_rank(RS.ROLE_CONTEXT, "corroborates", 0)
    check("a counterweight that complicates outranks a fourth corroboration",
          counter < fourth_agreement, (counter, fourth_agreement))
    check("an independent source outranks context at the same relation",
          RS.source_value_rank(RS.ROLE_INDEPENDENT, "extends", 5)
          < RS.source_value_rank(RS.ROLE_CONTEXT, "extends", 0))
    check("fetch order breaks ties and nothing else",
          RS.source_value_rank(RS.ROLE_PRIMARY, "extends", 1)
          < RS.source_value_rank(RS.ROLE_PRIMARY, "extends", 2))
    check("a reprint of the anchor ranks last",
          RS.source_value_rank(RS.ROLE_PRIMARY, "duplicate_of_anchor", 0)
          > RS.source_value_rank(RS.ROLE_CONTEXT, "background", 99))


def test_the_claim_steers_the_queries() -> None:
    """The disconfirming shape had never once been turned into a search."""
    inst = {"mechanism": "Institutions certify authority, not knowledge.",
            "disconfirming_shape": "Show the institution has a route by which "
                                   "uncertified knowledge enters the record.",
            "carriers": "A court transcript beside the hearing.",
            "false_move": "Treating every omission as deliberate erasure."}
    block = RS.instrument_scope_block(inst)
    check("the claim reaches the scope prompt", inst["mechanism"] in block)
    check("the refutation reaches it", inst["disconfirming_shape"] in block)
    check("carriers reach it", inst["carriers"] in block)
    check("the false move reaches it", inst["false_move"] in block)
    check("the first angle is refutation", "would REFUTE the claim" in block)
    check("it asks for a primary document", "PRIMARY document" in block)
    check("it asks for a participant voice", "PARTICIPANT" in block)
    check("it asks for material outside the institution",
          "OUTSIDE the institution" in block)
    check("it warns that the anchor's own pages are not a second source",
          "its other pages are not a second source" in block)
    check("a run with no instrument sends nothing extra",
          RS.instrument_scope_block(None) == ""
          and RS.instrument_scope_block({"carriers": "x"}) == "")


def test_scope_prompt_is_unchanged_without_an_instrument() -> None:
    """Byte-identical for every run that carries no claim."""
    seen = {}

    class P:
        def complete(self, system, user, max_tokens=1200, **kw):
            seen["user"] = user

            class C:
                text = '{"subject":"s","queries":["q"],"named_entities":[],' \
                       '"subject_span":"","anchor_subject_words":1}'

                def identity(self):
                    return {}
            return C()

    RS.scope(P(), "an anchor about a thing", "sha")
    check("no instrument block appears", "THIS RUN EXISTS TO TEST A CLAIM"
          not in seen["user"])
    check("it is exactly the scope prompt",
          seen["user"] == RS.scope_prompt("an anchor about a thing", "sha"))


def test_diagnosis_renders_and_names_the_cause() -> None:
    p = pack_of(INUIT)
    if p is None:
        check("INUIT evidence present", False, str(INUIT))
        return
    txt = RS.render_diagnosis(p)
    for needle in ("RESEARCH DIAGNOSIS", "HOLD_INSUFFICIENT_RESEARCH",
                   "CANDIDATES FOUND", "FETCH ORDER", "PACK TEXT BUDGET",
                   "WHAT DECIDED THE VERDICT"):
        check("diagnosis has section %r" % needle, needle in txt)
    check("it names the anchor's own publisher",
          "the anchor's own publisher" in txt)
    check("it says the material existed and was never read",
          "SELECTION failure, not scarcity" in txt, txt[-400:])
    check("it lists the unread independent sources",
          "ucalgary" in txt or "archaeology.org" in txt)
    check("it is readable, not a json dump", "{" not in txt.split("SUBJECT")[0])
    print("\n----- RESEARCH_DIAGNOSIS.txt (Inuit run) -----")
    print(txt)


def main() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            print("\n%s" % name)
            fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        sys.exit(1)
    print("ALL RESEARCH DIVERSITY TESTS PASSED")


if __name__ == "__main__":
    main()

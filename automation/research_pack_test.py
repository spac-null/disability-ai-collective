#!/usr/bin/env python3
"""
research_pack_test.py -- the Research Pack boundary.

The failure this whole stage exists to prevent is concrete and dated: on 2026-08-28 a
1,245-word roundup whose subject-relevant material was 118 words of promotional copy
produced a 637-word interpretive feature, because one fact read five ways looks like
five paragraphs of thinking. These tests hold the line at every point where that could
happen again -- and at every point where a pack could look researched without being it.

No network. Every fetch and search is stubbed; the pack contract, the duplicate
collapse and the sufficiency rule are all deterministic and testable offline.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C                      # noqa: E402
from new_engine_v1 import research as RS                      # noqa: E402
from new_engine_v1 import runner as R                         # noqa: E402
from new_engine_v1 import stages as S                         # noqa: E402
from research_pack_fixture import stub_pack                   # noqa: E402

FAILURES: list = []
AT = "2026-08-28T00:00:00+00:00"


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:200]))
    if not ok:
        FAILURES.append(label)


def _src(text, sid, role="INDEPENDENT", url=None, excerpts=None, cluster=None):
    return {"source_id": sid, "role": role, "url": url or "https://%s.example/x" % sid.lower(),
            "canonical_url": "", "publisher": "%s.example" % sid.lower(), "title": "",
            "accessed_at": AT, "fetch_status": "ok", "sha256": C.sha256_text(text),
            "content_length": len(text), "relation": "corroborates",
            "duplicate_cluster": cluster if cluster is not None else int(sid[1:]),
            "why_relevant": "", "text": text, "excerpts": excerpts or [],
            "excerpts_dropped": []}


def _pack(sources, **cov):
    coverage = {"fetched_ok": len(sources) - 1, "fetch_failures": [],
                "roles_present": sorted({s["role"] for s in sources}),
                "distinct_publishers": len({s["publisher"] for s in sources}),
                "duplicate_clusters": len({s["duplicate_cluster"] for s in sources}),
                "independent_clusters": 0, "subject_relevant_words": 0}
    coverage.update(cov)
    p = {"subject": "a crossing", "questions": [], "queries": [],
         "candidates_considered": [], "anchor_kind": "news_report",
         "anchor_subject_words": 40, "narrower_subject": "", "sources": sources,
         "coverage": coverage}
    p["sufficiency"] = RS.sufficiency(p)
    p["pack_sha256"] = "x"
    return p


def _validate(pack):
    C.validate(C.Artifact(stage=C.RESEARCH_PACK, created_at=AT, payload=pack))


# ── PACK CONTRACT ─────────────────────────────────────────────────────────────
def test_pack_contract():
    anchor = _src("The council report records the crossing.", "S0", role="ANCHOR")
    good = _pack([anchor, _src("A second, independent account of the crossing.", "S1")])
    try:
        _validate(good)
        check("a well-formed pack validates", True)
    except C.ContractViolation as e:
        check("a well-formed pack validates", False, e)

    for label, mutate in (
        ("source without source_id is rejected", lambda p: p["sources"][1].pop("source_id")),
        ("source without url is rejected", lambda p: p["sources"][1].pop("url")),
        ("source without sha256 is rejected", lambda p: p["sources"][1].pop("sha256")),
        ("source without accessed_at is rejected", lambda p: p["sources"][1].pop("accessed_at")),
        ("sha that does not match the text is rejected",
         lambda p: p["sources"][1].update(sha256_text := {"sha256": "0" * 64})),
        ("unknown role is rejected", lambda p: p["sources"][1].update({"role": "HEARSAY"})),
        ("two anchors are rejected", lambda p: p["sources"][1].update({"role": "ANCHOR"})),
        ("duplicate source_id is rejected",
         lambda p: p["sources"][1].update({"source_id": "S0"})),
    ):
        import copy
        p = copy.deepcopy(good)
        mutate(p)
        try:
            _validate(p)
            check(label, False, "validated when it should not have")
        except C.ContractViolation:
            check(label, True)


def test_excerpt_must_be_verbatim_span_of_fetched_bytes():
    """The search-result-is-not-a-source rule, made structural. A span that is not in
    the fetched text cannot be carried, whatever produced it."""
    text = "The inspection found the audible warning inoperative for eleven weeks."
    anchor = _src("anchor text about the crossing", "S0", role="ANCHOR")
    ok_pack = _pack([anchor, _src(text, "S1", excerpts=["the audible warning inoperative"])])
    try:
        _validate(ok_pack)
        check("a verbatim excerpt is carried", True)
    except C.ContractViolation as e:
        check("a verbatim excerpt is carried", False, e)

    bad = _pack([anchor, _src(text, "S1",
                              excerpts=["the warning had been broken for three months"])])
    try:
        _validate(bad)
        check("an excerpt that is not in the source is rejected", False)
    except C.ContractViolation as e:
        check("an excerpt that is not in the source is rejected", "verbatim" in str(e))

    kept, dropped = RS.verified_excerpts(
        ["The inspection found the audible warning inoperative for eleven weeks.",
         "The inspection found the warning broken for three months."], text)
    check("verified_excerpts keeps the real span and drops the invented one",
          len(kept) == 1 and len(dropped) == 1, (kept, dropped))


def test_unfetched_and_failed_sources_supply_nothing():
    anchor = _src("anchor", "S0", role="ANCHOR")
    for status in ("http_403", "empty_or_blocked", "TimeoutError",
                   "unsupported_content_type:application/pdf"):
        s = _src("some text", "S1")
        s["fetch_status"] = status
        try:
            _validate(_pack([anchor, s]))
            check("fetch_status=%s cannot sit in the pack" % status, False)
        except C.ContractViolation:
            check("fetch_status=%s cannot sit in the pack" % status, True)

    rec = RS.fetch_source("https://example.invalid/nothing", timeout=1)
    check("an unreachable URL returns a non-ok record with no text",
          rec["status"] != "ok" and rec["text"] == "" and rec["sha256"] == "", rec["status"])


def test_search_result_is_not_a_source():
    """A URL that search named, and nothing fetched, contributes no material and
    appears only as a considered candidate."""
    pack = _pack([_src("anchor", "S0", role="ANCHOR")])
    pack["candidates_considered"] = ["https://named-but-never-fetched.example/a"]
    _validate(pack)
    ids = {s["source_id"] for s in pack["sources"]}
    check("a named-but-unfetched URL is not a source", ids == {"S0"}, ids)
    block = S.pack_material_block(pack)
    check("the writer is never shown an unfetched candidate",
          "named-but-never-fetched" not in block)


def test_writer_input_references_the_exact_pack_and_replays_from_disk():
    import json
    with tempfile.TemporaryDirectory() as d:
        import new_engine_v1_test as T                       # reuse the stub provider
        out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "t", AT,
                    mode=R.MODE_LIVE, research_fn=stub_pack)
        A = out["artifacts"]
        pack_hash = A[C.RESEARCH_PACK].content_hash()
        for stage in (C.DISCOVERY, C.ARTICLE_FORM, C.WRITER_INPUT, C.GROUNDING_FINDINGS):
            check("%s declares the exact pack hash" % stage,
                  A[stage].input_hashes.get("research_pack") == pack_hash)
        prompt = A[C.WRITER_INPUT].payload["prompt_text"]
        check("pack material reached the writer prompt", "RESEARCH PACK" in prompt)
        check("every pack source is identified in the prompt",
              all("[%s]" % s["source_id"] in prompt
                  for s in A[C.RESEARCH_PACK].payload["sources"] if s["role"] != "ANCHOR"))
        # replay: the persisted artifact rehydrates to the same hash
        disk = json.loads((pathlib.Path(d) / "t" / "RESEARCH_PACK.json").read_text())
        art = C.Artifact(stage=disk["stage"], created_at=disk["created_at"],
                         payload=disk["payload"], input_hashes=disk["input_hashes"])
        check("the pack replays from disk to the same hash",
              art.content_hash() == pack_hash)
        C.validate(art)
        check("the replayed pack still satisfies the contract", True)


# ── DUPLICATES ────────────────────────────────────────────────────────────────
def test_duplicates_collapse_and_cannot_buy_independence():
    release = ("The university today announced a gravity-powered mountain trike "
               "designed to extend mountain tourism beyond the ski season, developed "
               "with input from ski-resort operators and refined through iterative "
               "testing towards a fully functional prototype.")
    syndicated = release.replace("today announced", "has announced")
    check("a syndicated copy is detected as a near-duplicate",
          RS.near_duplicate(release, syndicated))
    check("an unrelated text is not a duplicate",
          not RS.near_duplicate(release, "A council report on a pedestrian crossing "
                                         "records that the audible warning failed."))

    anchor = {"url": "https://anchor.example/story", "text": release, "title": "",
              "accessed_at": AT}
    fetched = [dict(source_id="S%d" % i, url="https://mirror%d.example/story" % i,
                    publisher="mirror%d.example" % i, text=syndicated, status="ok",
                    accessed_at=AT, title="", canonical_url="")
               for i in (1, 2, 3)]
    assessment = {"sources": [{"source_id": s["source_id"], "role": "INDEPENDENT",
                               "relation": "duplicate_of_anchor",
                               "excerpts": [syndicated[:120]]} for s in fetched]}
    pack = RS.build_pack(anchor=anchor, scoped={"subject": "a trike", "anchor_kind":
                                                "press_release", "anchor_subject_words": 60},
                         fetched=fetched, assessment=assessment,
                         searched={"queries": ["trike"], "candidates": [], "failures": []})
    check("three mirrors collapse into one cluster with the anchor",
          pack["coverage"]["duplicate_clusters"] == 1, pack["coverage"])
    check("duplicates buy no independence",
          pack["coverage"]["independent_clusters"] == 0)
    check("anchor + copies is not enough to write from",
          pack["sufficiency"]["verdict"] == RS.HOLD, pack["sufficiency"])


# ── SUFFICIENCY ───────────────────────────────────────────────────────────────
def test_sufficiency_rules():
    anchor = _src("anchor", "S0", role="ANCHOR")
    thin = _pack([anchor], independent_clusters=0, subject_relevant_words=0)
    check("anchor-only thin blurb HOLDs",
          thin["sufficiency"]["verdict"] == RS.HOLD, thin["sufficiency"])

    one = _pack([anchor, _src("x", "S1")], independent_clusters=1,
                subject_relevant_words=200)
    check("one independent source with real material gives SHORT_ARTICLE",
          one["sufficiency"]["verdict"] == RS.SHORT_ARTICLE, one["sufficiency"])

    full = _pack([anchor, _src("x", "S1", role="PRIMARY"), _src("y", "S2")],
                 independent_clusters=2, subject_relevant_words=500)
    check("primary + independent + real material gives ARTICLE",
          full["sufficiency"]["verdict"] == RS.ARTICLE, full["sufficiency"])

    starved = _pack([anchor, _src("x", "S1", role="PRIMARY"), _src("y", "S2")],
                    independent_clusters=2, subject_relevant_words=120)
    check("two sources with almost no subject material do not reach ARTICLE",
          starved["sufficiency"]["verdict"] != RS.ARTICLE, starved["sufficiency"])

    rich = _pack([anchor], independent_clusters=0, subject_relevant_words=0)
    rich["anchor_kind"] = "paper"
    rich["anchor_subject_words"] = 4000
    rich["sufficiency"] = RS.sufficiency(rich)
    check("a genuinely rich primary anchor supports a narrow SHORT_ARTICLE",
          rich["sufficiency"]["verdict"] == RS.SHORT_ARTICLE, rich["sufficiency"])

    roundup = _pack([anchor], independent_clusters=0, subject_relevant_words=0)
    roundup["anchor_kind"] = "roundup_entry"
    roundup["anchor_subject_words"] = 118
    roundup["sufficiency"] = RS.sufficiency(roundup)
    check("the real 28 Aug shape (118-word roundup entry, nothing else) HOLDs",
          roundup["sufficiency"]["verdict"] == RS.HOLD, roundup["sufficiency"])

    narrower = _pack([anchor, _src("x", "S1")], independent_clusters=1,
                     subject_relevant_words=200)
    narrower["narrower_subject"] = "one exhibit, not the whole programme"
    narrower["sufficiency"] = RS.sufficiency(narrower)
    check("a narrower supportable subject is reported as NARROW",
          narrower["sufficiency"]["verdict"] == RS.NARROW, narrower["sufficiency"])

    check("a counterweight is noted, not demanded, when the pack is otherwise strong",
          any("counterweight" in r for r in full["sufficiency"]["reasons"]))


def test_context_only_material_cannot_buy_an_article():
    """Straight from the live 28 August regression: research on a roundup entry
    returned four university programme pages -- fetched, hashed, genuinely independent
    of the publisher, and about the SCHOOL rather than the subject. Role-blind counting
    turned that boilerplate into a publishable verdict."""
    anchor = _src("anchor", "S0", role="ANCHOR")
    ctx = _pack([anchor] + [_src("course page %d" % i, "S%d" % i, role="CONTEXT")
                            for i in (1, 2, 3, 4)],
                independent_clusters=0, subject_relevant_words=0,
                context_only_words=296)
    check("four independent CONTEXT pages do not make an article",
          ctx["sufficiency"]["verdict"] == RS.HOLD, ctx["sufficiency"])
    check("the HOLD says what was actually found",
          "background/context" in " ".join(ctx["sufficiency"]["what_is_missing"]))

    # build_pack must not count CONTEXT toward independence in the first place
    anchor_in = {"url": "https://anchor.example/roundup", "text": "roundup text",
                 "title": "", "accessed_at": AT}
    fetched = [dict(source_id="S%d" % i, url="https://school%d.example/course" % i,
                    publisher="school%d.example" % i,
                    text="The programme runs over three years and covers design.",
                    status="ok", accessed_at=AT, title="", canonical_url="")
               for i in (1, 2)]
    assessment = {"sources": [{"source_id": s["source_id"], "role": "CONTEXT",
                               "relation": "background",
                               "excerpts": ["The programme runs over three years"]}
                              for s in fetched]}
    pack = RS.build_pack(anchor=anchor_in,
                         scoped={"subject": "a booklet", "anchor_kind": "roundup_entry",
                                 "anchor_subject_words": 118},
                         fetched=fetched, assessment=assessment,
                         searched={"queries": [], "candidates": [], "failures": []})
    check("CONTEXT sources count as context, not independence",
          pack["coverage"]["independent_clusters"] == 0
          and pack["coverage"]["context_only_words"] > 0, pack["coverage"])
    check("and the verdict is HOLD", pack["sufficiency"]["verdict"] == RS.HOLD)


def test_one_publisher_cannot_corroborate_itself():
    """From the live Minnie Evans regression: two Whitney pages and two High Museum
    pages are four documents, four duplicate clusters -- and two institutions."""
    anchor_in = {"url": "https://paper.example/feature", "text": "feature text",
                 "title": "", "accessed_at": AT}
    texts = ["The exhibition gathers ninety drawings made after 1940.",
             "Press release: the exhibition opens in October and tours next year.",
             "The organising museum describes the artist's decades at the gardens.",
             "Season announcement listing the artist's show among others."]
    pubs = ["whitney.example", "whitney.example", "high.example", "high.example"]
    fetched = [dict(source_id="S%d" % (i + 1), url="https://%s/p%d" % (pubs[i], i),
                    publisher=pubs[i], status="ok", accessed_at=AT, title="",
                    canonical_url="", text=texts[i]) for i in range(4)]
    assessment = {"sources": [{"source_id": s["source_id"], "role": "PRIMARY",
                               "relation": "corroborates", "excerpts": [t]}
                              for s, t in zip(fetched, texts)]}
    pack = RS.build_pack(anchor=anchor_in,
                         scoped={"subject": "the exhibition", "anchor_kind": "feature",
                                 "anchor_subject_words": 900, "subject_span": ""},
                         fetched=fetched, assessment=assessment,
                         searched={"queries": [], "candidates": [], "failures": []})
    cov = pack["coverage"]
    check("four documents are four duplicate clusters", cov["independent_clusters"] == 4)
    check("but only two publishers", cov["independent_publishers"] == 2, cov)
    check("sufficiency counts the smaller of the two",
          "independent=2" in pack["sufficiency"]["reasons"][0],
          pack["sufficiency"]["reasons"][0])


def test_insufficient_research_holds_the_run_before_discovery():
    import new_engine_v1_test as T

    def thin_pack(_p, *, anchor, now_iso, **_k):
        pack = _pack([_src(anchor["text"], "S0", role="ANCHOR", url=anchor["url"])],
                     independent_clusters=0, subject_relevant_words=0)
        pack["anchor_kind"] = "roundup_entry"
        pack["anchor_subject_words"] = 118
        pack["sufficiency"] = RS.sufficiency(pack)
        return pack

    with tempfile.TemporaryDirectory() as d:
        out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "thin", AT,
                    mode=R.MODE_LIVE, research_fn=thin_pack)
    check("the run HOLDs", out["decision"] == "HOLD", out["reasons"])
    check("the reason code names insufficient research",
          out.get("reason_code") == RS.HOLD, out.get("reason_code"))
    check("no article was written", C.WRITER_OUTPUT not in out["artifacts"])
    check("Discovery never ran", C.DISCOVERY not in out["artifacts"])
    check("the pack is still persisted with the HOLD",
          C.RESEARCH_PACK in out["artifacts"])


# ── FAILURE ───────────────────────────────────────────────────────────────────
def test_research_failure_fails_closed():
    import new_engine_v1_test as T

    def boom(_p, *, anchor, now_iso, **_k):
        raise RS.ResearchError("search failed: URLError")

    with tempfile.TemporaryDirectory() as d:
        out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "boom", AT,
                    mode=R.MODE_LIVE, research_fn=boom)
    check("a research failure HOLDs the run", out["decision"] == "HOLD")
    check("it is reported as an infrastructure failure, not an editorial one",
          (out.get("run_status") or {}).get("status") == "PROVIDER_FAILURE",
          out.get("run_status"))
    check("no pack artifact is invented from a failure",
          C.RESEARCH_PACK not in out["artifacts"])
    check("nothing downstream ran", C.WRITER_OUTPUT not in out["artifacts"])


def test_bounds_are_finite():
    for name, value, ceiling in (("MAX_QUERIES", RS.MAX_QUERIES, 8),
                                 ("MAX_CANDIDATE_URLS", RS.MAX_CANDIDATE_URLS, 30),
                                 ("MAX_FETCHED_SOURCES", RS.MAX_FETCHED_SOURCES, 12),
                                 ("PER_SOURCE_CHARS", RS.PER_SOURCE_CHARS, 40_000),
                                 ("PACK_TEXT_BUDGET", RS.PACK_TEXT_BUDGET, 120_000),
                                 ("FETCH_TIMEOUT", RS.FETCH_TIMEOUT, 60)):
        check("%s is bounded (%s)" % (name, value), 0 < value <= ceiling)
    src = (HERE / "new_engine_v1" / "research.py").read_text()
    check("there is no retry loop around fetching",
          "while True" not in src and "for _retry" not in src)


# ── PURITY ────────────────────────────────────────────────────────────────────
def test_writer_still_has_no_network():
    import ast
    src = (HERE / "new_engine_v1" / "stages.py").read_text()
    tree = ast.parse(src)
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    check("stages.py imports nothing that can reach the network",
          not (imports & {"urllib", "http", "socket", "requests"}), imports)
    for fn in ("write", "build_writer_input"):
        check("stages.%s takes no search or fetch argument" % fn,
              "search" not in src.split("def %s(" % fn)[1].split("\n\n")[0])
    rtree = ast.parse((HERE / "new_engine_v1" / "research.py").read_text())
    rimports = set()
    for n in ast.walk(rtree):
        if isinstance(n, ast.Import):
            rimports |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            rimports.add(n.module)
    check("research does not import the downstream verifier",
          not any("fact_check" in m or m.startswith("orchestrator") for m in rimports),
          rimports)


def test_grounding_sees_authorised_material_only():
    pack = _pack([_src("anchor text", "S0", role="ANCHOR"),
                  _src("Independent account of the crossing.", "S1",
                       excerpts=["Independent account"])])
    prompt = S.ground_prompt("draft text", "anchor text", "0" * 64, pack)
    check("grounding is shown the pack material", "[S1]" in prompt)
    check("grounding is shown the anchor", "anchor text" in prompt)
    for forbidden in ("route", "arrival", "burden", "dominant_reading",
                      "perceptual_instrument"):
        check("grounding is not shown the Form/Discovery field %r" % forbidden,
              forbidden not in prompt)
    writer_prompt = S.build_writer_input(
        {"motion": "m", "route": ["r"], "arrival": "a", "burden": "b",
         "target_words": [500, 650]},
        {"source_anchor_quote": "q", "what_becomes_knowable": "k",
         "grounding_boundaries": "g"}, "anchor text", "0" * 64, "Maya Flux",
        pack)["prompt_text"]
    check("the writer and the grounder are shown the same pack spans",
          all(("[%s]" % s["source_id"]) in writer_prompt
              for s in pack["sources"] if s["role"] != "ANCHOR"))


def test_bridge_checks_pack_provenance():
    import publication_safety_bridge as B
    import new_engine_v1_test as T
    with tempfile.TemporaryDirectory() as d:
        out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "b", AT,
                    mode=R.MODE_LIVE, research_fn=stub_pack)
    res = B.evaluate(out, fact_check_fn=lambda a: {
        "status": "verified", "extraction_status": "ok", "claims_extracted": 2,
        "contradicted": [], "advisory": [], "unverifiable": []})
    names = {c["check"]: c for c in res.summary()["checks"]}
    check("the bridge runs a research-pack provenance check",
          "research_pack_provenance" in names)
    check("it passes on an intact pack",
          names.get("research_pack_provenance", {}).get("ok") is True,
          names.get("research_pack_provenance"))
    check("it is a blocking check",
          names.get("research_pack_provenance", {}).get("blocking") is True)

    # tamper: the persisted pack no longer matches what the writer used
    out["artifacts"][C.RESEARCH_PACK].payload["sources"][1]["text"] += " tampered"
    res2 = B.evaluate(out, fact_check_fn=lambda a: {
        "status": "verified", "extraction_status": "ok", "claims_extracted": 2,
        "contradicted": [], "advisory": [], "unverifiable": []})
    n2 = {c["check"]: c for c in res2.summary()["checks"]}
    check("a tampered pack source fails the check",
          n2.get("research_pack_provenance", {}).get("ok") is False,
          n2.get("research_pack_provenance"))
    check("and the run is not publication-eligible", not res2.eligible)



# ── TERTIARY ──────────────────────────────────────────────────────────────────
def test_tertiary_carries_material_but_buys_no_independence():
    """An encyclopaedia entry summarises other people's reporting. It is often accurate
    and worth writing from, and it is not a second witness. The Minnie Evans pack is the
    real case: Wikipedia was carried as INDEPENDENT and counted toward the ARTICLE
    threshold alongside two museum sources."""
    anchor = _src("anchor about the artist", "S0", role="ANCHOR")
    tert = _pack([anchor, _src("x", "S1", role="TERTIARY")],
                 independent_clusters=0, subject_relevant_words=300, tertiary_words=300)
    check("TERTIARY alone does not reach SHORT_ARTICLE",
          tert["sufficiency"]["verdict"] == RS.HOLD, tert["sufficiency"])

    with_primary = _pack([anchor, _src("x", "S1", role="PRIMARY"),
                          _src("y", "S2", role="TERTIARY")],
                         independent_clusters=1, subject_relevant_words=500,
                         tertiary_words=250)
    check("TERTIARY does not supply the second independent cluster",
          with_primary["sufficiency"]["verdict"] == RS.SHORT_ARTICLE,
          with_primary["sufficiency"])

    check("TERTIARY is not a substitute for a PRIMARY source",
          RS.ROLE_TERTIARY not in RS.SUPPORTING_ROLES
          and RS.ROLE_TERTIARY in RS.MATERIAL_ROLES)

    # build_pack must classify the counting, not the domain
    anchor_in = {"url": "https://paper.example/feature", "text": "feature text",
                 "title": "", "accessed_at": AT}
    fetched = [dict(source_id="S1", url="https://encyclopaedia.example/subject",
                    publisher="encyclopaedia.example", status="ok", accessed_at=AT,
                    title="", canonical_url="",
                    text="The artist worked at the gardens from 1948 until 1974."),
               dict(source_id="S2", url="https://museum.example/exhibition",
                    publisher="museum.example", status="ok", accessed_at=AT,
                    title="", canonical_url="",
                    text="The museum's exhibition gathers ninety drawings made after 1940.")]
    assessment = {"sources": [
        {"source_id": "S1", "role": "TERTIARY", "relation": "corroborates",
         "excerpts": ["The artist worked at the gardens from 1948 until 1974."]},
        {"source_id": "S2", "role": "PRIMARY", "relation": "extends",
         "excerpts": ["The museum's exhibition gathers ninety drawings made after 1940."]}]}
    pack = RS.build_pack(anchor=anchor_in,
                         scoped={"subject": "the artist", "anchor_kind": "feature",
                                 "anchor_subject_words": 900, "subject_span": ""},
                         fetched=fetched, assessment=assessment,
                         searched={"queries": [], "candidates": [], "failures": []})
    cov = pack["coverage"]
    check("a tertiary source contributes verified subject words",
          cov["tertiary_words"] > 0 and cov["subject_relevant_words"] > cov["tertiary_words"],
          cov)
    check("only the non-tertiary source counts as an independent cluster",
          cov["independent_clusters"] == 1, cov)
    check("no publisher or domain is named in the sufficiency rule",
          "wikipedia" not in
          (HERE / "new_engine_v1" / "research.py").read_text().lower().split(
              "def sufficiency")[1])
    _validate(pack)
    check("a pack carrying a TERTIARY role validates", True)


# ── ROUNDUP SUBJECT SCOPING ───────────────────────────────────────────────────
ROUNDUP = """Design School Shows: projects from the Academy

Cargo Bench by Ada Moreno
"Cargo Bench is a public seat that folds into a delivery trolley for market traders.
"It was developed with three market cooperatives and tested over one winter season."
Student: Ada Moreno

Reading Rail by Bo Lindqvist
"Reading Rail is a tactile handrail that carries route information in raised profile.
"It was developed through workshops with blind and partially sighted commuters."
Student: Bo Lindqvist
"""
CARGO_SPAN = ('Cargo Bench by Ada Moreno\n"Cargo Bench is a public seat that folds into '
              'a delivery trolley for market traders.\n"It was developed with three '
              'market cooperatives and tested over one winter season."')
CARGO_QUOTE = ("It was developed with three market cooperatives and tested over one "
               "winter season.")
RAIL_QUOTE = ("It was developed through workshops with blind and partially sighted "
              "commuters.")


def test_roundup_subject_span_binds_discovery():
    """Two unrelated projects in one anchor. Researching the bench and then writing
    about the handrail is the 28 August failure exactly, and it must not be reachable."""
    from new_engine_v1 import invariants as INV
    ok, code, detail = INV.check_subject_scope({"source_anchor_quote": CARGO_QUOTE},
                                               CARGO_SPAN, ROUNDUP)
    check("an anchor quote inside the researched subject passes", ok, (code, detail))

    ok, code, detail = INV.check_subject_scope({"source_anchor_quote": RAIL_QUOTE},
                                               CARGO_SPAN, ROUNDUP)
    check("an anchor quote from the OTHER roundup item is rejected", not ok, detail)
    check("the rejection has a deterministic reason code",
          code == INV.SUBJECT_SCOPE_MISMATCH, code)

    ok, _, _ = INV.check_subject_scope({"source_anchor_quote": RAIL_QUOTE}, "", ROUNDUP)
    check("a single-subject anchor (no span) is not constrained", ok)
    ok, _, _ = INV.check_subject_scope({"source_anchor_quote": RAIL_QUOTE},
                                       "a span that was never in the anchor", ROUNDUP)
    check("an unverifiable span binds nothing rather than binding the wrong region", ok)


def test_researched_and_written_subject_cannot_diverge():
    """End to end through the runner: the pack is built for the bench, Discovery
    grounds itself in the handrail, and the run HOLDs before Article Form."""
    import copy
    import new_engine_v1_test as T

    def roundup_pack(_p, *, anchor, now_iso, **_k):
        support = ("The cooperative reported that the bench carried 40kg loads across "
                   "the market square through the winter trial.")
        pack = {
            "subject": "Cargo Bench by Ada Moreno", "questions": [],
            "queries": ["Cargo Bench Ada Moreno market cooperative"],
            "candidates_considered": [], "anchor_kind": "roundup_entry",
            "anchor_subject_words": 40, "subject_span": CARGO_SPAN,
            "narrower_subject": "",
            "sources": [_src(anchor["text"], "S0", role="ANCHOR", url=anchor["url"]),
                        _src(support, "S1", role="INDEPENDENT",
                             excerpts=["The cooperative reported that the bench carried "
                                       "40kg loads across the market square"])],
            "coverage": {"fetched_ok": 1, "fetch_failures": [], "budget_dropped": [],
                         "roles_present": ["ANCHOR", "INDEPENDENT"],
                         "distinct_publishers": 2, "duplicate_clusters": 2,
                         "independent_clusters": 1, "subject_relevant_words": 200,
                         "tertiary_words": 0, "context_only_words": 0},
            "pack_sha256": "x"}
        pack["sufficiency"] = RS.sufficiency(pack)
        return pack

    payload = {"source_text": ROUNDUP, "source_sha256": C.sha256_text(ROUNDUP),
               "provenance": {"origin": "fetched_article",
                              "url": "https://example.org/roundup"}}

    def _provider_quoting(quote):
        disc = dict(T.DISCOVERY_REPLY, source_anchor_quote=quote)
        return T.StubProvider(discovery=disc)

    with tempfile.TemporaryDirectory() as d:
        out = R.run(copy.deepcopy(payload), pathlib.Path(d), _provider_quoting(RAIL_QUOTE),
                    "diverge", AT, mode=R.MODE_LIVE, research_fn=roundup_pack)
    check("a run that switches roundup item HOLDs", out["decision"] == "HOLD", out["reasons"])
    check("the reason names the scope mismatch",
          out.get("reason_code") == "DISCOVERY_SUBJECT_OUTSIDE_RESEARCHED_SCOPE",
          out.get("reason_code"))
    check("no Article Form was built", C.ARTICLE_FORM not in out["artifacts"])
    check("no article was written", C.WRITER_OUTPUT not in out["artifacts"])
    check("the pack that was actually built is still on record",
          out["artifacts"][C.RESEARCH_PACK].payload["subject"] == "Cargo Bench by Ada Moreno")

    with tempfile.TemporaryDirectory() as d:
        out2 = R.run(copy.deepcopy(payload), pathlib.Path(d),
                     _provider_quoting(CARGO_QUOTE), "aligned", AT,
                     mode=R.MODE_LIVE, research_fn=roundup_pack)
    check("staying on the researched subject proceeds normally",
          out2["decision"] == "ACCEPT", out2["reasons"])
    check("Discovery records that the scope was verified",
          out2["artifacts"][C.DISCOVERY].payload.get("subject_scope_verified") is True)
    prompt = out2["artifacts"][C.WRITER_INPUT].payload["prompt_text"]
    check("the writer is told which subject was researched",
          "SUBJECT RESEARCHED: Cargo Bench by Ada Moreno" in prompt)
    check("and is told the other roundup items have no research behind them",
          "is not on offer" in prompt)


def test_subject_span_must_be_verbatim_in_the_anchor():
    anchor = _src(ROUNDUP, "S0", role="ANCHOR")
    good = _pack([anchor, _src("support", "S1")])
    good["subject_span"] = CARGO_SPAN
    _validate(good)
    check("a verbatim subject span validates", True)
    bad = _pack([anchor, _src("support", "S1")])
    bad["subject_span"] = "Cargo Bench, a folding public seat for market traders"
    try:
        _validate(bad)
        check("a paraphrased subject span is rejected", False)
    except C.ContractViolation as e:
        check("a paraphrased subject span is rejected", "verbatim" in str(e))


def main() -> None:
    for fn in (test_pack_contract,
               test_excerpt_must_be_verbatim_span_of_fetched_bytes,
               test_unfetched_and_failed_sources_supply_nothing,
               test_search_result_is_not_a_source,
               test_writer_input_references_the_exact_pack_and_replays_from_disk,
               test_duplicates_collapse_and_cannot_buy_independence,
               test_sufficiency_rules,
               test_context_only_material_cannot_buy_an_article,
               test_one_publisher_cannot_corroborate_itself,
               test_insufficient_research_holds_the_run_before_discovery,
               test_research_failure_fails_closed,
               test_tertiary_carries_material_but_buys_no_independence,
               test_roundup_subject_span_binds_discovery,
               test_researched_and_written_subject_cannot_diverge,
               test_subject_span_must_be_verbatim_in_the_anchor,
               test_bounds_are_finite,
               test_writer_still_has_no_network,
               test_grounding_sees_authorised_material_only,
               test_bridge_checks_pack_provenance):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL RESEARCH-PACK TESTS PASSED")


if __name__ == "__main__":
    main()

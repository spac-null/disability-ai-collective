#!/usr/bin/env python3
"""art_director_wiring_test.py -- the wiring, not the doctrine.

art_director.py's own contract is proved by art_director_test.py. What is proved HERE is
the seam publish_best now sits on: that the art director is asked exactly once per
canonical publication, that its brief reaches gen_images, that ZERO IMAGES IS AN ANSWER
rather than a failure, and that every path where it cannot answer -- no run, no provider,
a refused brief -- lands on the image path that existed before it did.

Stdlib only. No provider, no network, no image generation, no repo mutation: gen_images
and art_director are both replaced by recorders, and the publisher is driven over a
temporary repo.

USAGE: python3 automation/art_director_wiring_test.py
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import shutil
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FAILURES = []


def check(name, cond, detail=""):
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name,
                        "" if cond else "  -- %s" % detail))
    if not cond:
        FAILURES.append(name)


# ── fixtures ────────────────────────────────────────────────────────────────────────
RUN_ID = "production-20260906T000000Z-deadbeef"
OTHER_RUN_ID = "production-20260901T000000Z-cafebabe"

BODY = ("The pavilion stands on six columns.\n\n"
        "Water passes beneath it, and the timber remains exposed across the spans.\n")

LEDGER = {"F1": {"fact_id": "F1", "proposition": "The pavilion stands on six columns.",
                 "support_span": "six columns", "source_id": "S1"}}
ARCH = {"article_type": "field_note", "story_spine": "a pavilion above the forest floor",
        "opening_object_or_event": "six columns", "reader_initial_state": "unfamiliar",
        "beats": [{"beat_id": "B1", "happens": "the pavilion is described",
                   "concrete_carrier": "six columns", "facts_allowed": ["F1"],
                   "concept_introduced": "", "must_not_say_yet": ""}],
        "turn": "", "crip_turn": "", "ending_move": "", "use_facts": ["F1"],
        "definitions": {}, "prohibitions": []}
CUT_REPORT = {"terms": {}, "prohibitions": [], "cut_without_distinctive_terms": []}
PACKET = {"article_type": "field_note", "story_spine": ARCH["story_spine"],
          "opening": "six columns", "reader_initial_state": "unfamiliar",
          "beats": [{"beat_id": "B1", "happens": "the pavilion is described",
                     "carrier": "six columns", "facts": [LEDGER["F1"]],
                     "concept": "", "withhold": ""}],
          "turn": "", "crip_turn": "", "lens": "", "ending_move": "",
          "facts": [LEDGER["F1"]], "quotes": [], "definitions": {}, "prohibitions": []}
SIDECAR = {"status": "NON_CLAIM_BEARING",
           "observations": [{"objects_and_materials": ["exposed timber", "six columns"],
                             "spatial_relationships": ["the deck sits above sloping ground"],
                             "printed_labels": []}]}
OTHER_SIDECAR = {"status": "NON_CLAIM_BEARING",
                 "observations": [{"objects_and_materials": ["a brick chimney"],
                                   "spatial_relationships": [], "printed_labels": []}]}

CURRENT_POST = """---
layout: "post"
title: "A pavilion on six columns"
author: "Maya Flux"
date: 2026-09-06
engine_generation: "CURRENT_ENGINE"
editorial_engine: "NEW_ENGINE_V1"
engine_version: "v1.0"
engine_decision: "ACCEPT"
engine_run: "%s"
source_url: "https://example.invalid/pavilion"
source_sha256: "%s"
provider_model: "claude-opus-5"
fact_check_status: "verified"
fact_check_extraction_status: "ok"
fact_check_claims_extracted: 2
publication_eligible: true
publication_safety_version: 1
dek: "Six columns, and the water goes under."
excerpt: "A pavilion above the forest floor."
---

%s""" % (RUN_ID, "0" * 64, BODY)

# No engine_generation, no engine_run: the era that has no run to resolve. It is eligible
# under the ordinary gates and must publish exactly as it did before this wiring existed.
LEGACY_POST = """---
layout: "post"
title: "An older pavilion"
author: "Maya Flux"
date: 2026-09-06
fact_check_status: "verified"
publication_eligible: true
publication_safety_version: 1
dek: "From before there were runs."
excerpt: "An older pavilion."
---

%s""" % BODY


def build_run(root: pathlib.Path, run_id=RUN_ID, sidecar=None) -> pathlib.Path:
    d = root / run_id
    d.mkdir(parents=True)

    def j(name, obj):
        (d / name).write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))

    j("WRITER_PACKET.json", PACKET)
    j("ARCHITECTURE.json", ARCH)
    j("LEDGER.json", LEDGER)
    j("CUT_REPORT.json", CUT_REPORT)
    j("NEGATIVE_LINEAGE.json", {})
    j("SAFETY_AUDIT.json", {"blocking": [], "audits": {}})
    j("RESEARCH_PACK.json", {"stage": "RESEARCH_PACK"})
    j("SOURCE_SNAPSHOT.json", {"stage": "SOURCE_SNAPSHOT"})
    j("GROUNDING_FINDINGS.json", {"status": "settled", "findings": []})
    j("FACT_CHECK.json", {"findings": []})
    (d / "WRITER_DRAFT.md").write_text(BODY)
    (d / "ARTICLE_FINAL.md").write_text(BODY)
    if sidecar is not None:
        j("VISUAL_OBSERVATIONS.json", sidecar)
    return d


def brief(n=2):
    img = {"function": "ESTABLISH_PLACE", "register": "ATMOSPHERIC_OBSERVATIONAL",
           "editorial_purpose": "see the ground the structure stands on",
           "factual_anchors": ["a raised timber structure on six columns"],
           "visual_anchors": [], "must_not_invent": ["signage"], "people": "NONE",
           "composition_note": "low horizon", "alt_text": "A raised timber structure.",
           "placement": "HERO"}
    return {"schema_version": 1, "image_count": n, "count_reasoning": "reasoned",
            "images": [dict(img) for _ in range(n)], "visual_context_used": False}


# ── recorders ───────────────────────────────────────────────────────────────────────
class ADRecorder:
    """Stands in for the art_director MODULE. Counts calls; makes no model call."""

    def __init__(self, result):
        self.result, self.calls = result, []

    def as_module(self):
        m = types.ModuleType("art_director")
        m.art_direct = self._art_direct
        return m

    def _art_direct(self, provider, article_text, title="", dek="", arch=None,
                    persona="", visual_sidecar=None, max_tokens=3000):
        self.calls.append({"article_text": article_text, "title": title, "dek": dek,
                           "arch": arch, "persona": persona,
                           "visual_sidecar": visual_sidecar})
        return self.result


class ImagesRecorder:
    """Stands in for gen_images. Records whether a brief was forwarded."""

    def __init__(self):
        self.calls = []

    def as_module(self):
        m = types.ModuleType("gen_images")
        m.has_image_field = lambda _t: False
        m.illustrate_post = self._illustrate
        return m

    def _illustrate(self, post_path, **kw):
        self.calls.append(kw)
        return {"ok": True, "assets": [], "figures": 0}

    @property
    def briefs(self):
        return [c.get("brief") for c in self.calls]


def publish_once(post_text, ad_result, *, sidecar=None, run_id=RUN_ID):
    """Drive the REAL publisher over a temp repo. Returns (rc, ad, images, stderr)."""
    import publish_best as PB

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="adwiring-"))
    saved = (PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess)
    env_before = dict(os.environ)
    ad = ADRecorder(ad_result)
    images = ImagesRecorder()
    sys.modules["gen_images"] = images.as_module()
    sys.modules["art_director"] = ad.as_module()
    try:
        ev, store = tmp / "evidence", tmp / "store"
        build_run(ev, run_id=run_id, sidecar=sidecar)
        PB.REPO, PB.DRAFTS, PB.POSTS = tmp, tmp / "_drafts", tmp / "_posts"
        PB.ARCHIVE = PB.DRAFTS / "_archive"
        PB.DRAFTS.mkdir()
        PB.POSTS.mkdir()
        PB.subprocess = types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(returncode=0),
            CalledProcessError=Exception)
        os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(ev)
        os.environ["CRIPMINDS_PUBLICATION_AUDIT_ROOT"] = str(store)
        draft = PB.DRAFTS / "2026-09-06-a-pavilion.md"
        draft.write_text(post_text)
        # HOW AN ARTICLE PUBLISHES DEPENDS ON WHICH ENGINE WROTE IT (2026-09-07). A
        # CURRENT_ENGINE article is published directly by the run that composed it, by
        # path, with no pool; a legacy/manual one still goes through the backlog
        # selector. The art-direction seam is the same for both -- promote_candidate --
        # which is exactly what these tests are about.
        if PB.PA.is_current_engine(PB.parse_frontmatter(post_text)):
            rc = PB.publish_candidate(draft)
        else:
            rc = PB.main()
        published = (PB.POSTS / draft.name).is_file()
        return rc, ad, images, published
    finally:
        PB.REPO, PB.DRAFTS, PB.POSTS, PB.ARCHIVE, PB.subprocess = saved
        sys.modules.pop("gen_images", None)
        sys.modules.pop("art_director", None)
        os.environ.clear()
        os.environ.update(env_before)
        shutil.rmtree(tmp, ignore_errors=True)


# ── 1. the wired path ───────────────────────────────────────────────────────────────
def test_current_engine_publication_is_art_directed():
    print("\ntest_1_a_current_engine_publication_is_art_directed")
    b = brief(2)
    rc, ad, images, published = publish_once(
        CURRENT_POST, {"ok": True, "brief": b, "reason": ""}, sidecar=SIDECAR)
    check("the article published", rc == 0 and published)
    check("the art director was asked exactly once", len(ad.calls) == 1,
          "%d call(s)" % len(ad.calls))
    check("gen_images was called exactly once", len(images.calls) == 1)
    check("the brief it returned is the brief gen_images received",
          images.briefs == [b])
    check("the run's architecture went with it", images.calls[0].get("arch") == ARCH)


# ── 2. failure falls back, it does not block ────────────────────────────────────────
def test_a_refused_brief_falls_back_to_the_legacy_path():
    print("\ntest_2_a_refused_or_absent_brief_falls_back")
    for label, result in (("refused", {"ok": False, "brief": None, "reason": "rejected"}),
                          ("None", None),
                          ("no brief object", {"ok": True, "brief": None, "reason": ""})):
        rc, ad, images, published = publish_once(CURRENT_POST, result, sidecar=SIDECAR)
        check("a %s answer still publishes the article" % label, rc == 0 and published)
        check("...on the legacy image path, with no brief (%s)" % label,
              len(images.calls) == 1 and "brief" not in images.calls[0],
              str(images.calls))
    # A provider that throws is the transport case, and it is the same answer.
    class _Boom(ADRecorder):
        def _art_direct(self, *a, **k):
            self.calls.append(k)
            raise RuntimeError("subscription refused")
    import publish_best as PB
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="adboom-"))
    try:
        ev = tmp / "evidence"
        build_run(ev)
        post = tmp / "post.md"
        post.write_text(CURRENT_POST)
        boom = _Boom(None)
        sys.modules["art_director"] = boom.as_module()
        env_before = dict(os.environ)
        os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(ev)
        try:
            b, arch, note = PB.art_direct_for(post)
        finally:
            os.environ.clear()
            os.environ.update(env_before)
            sys.modules.pop("art_director", None)
        check("a transport failure returns no brief rather than raising", b is None)
        check("...and says so", "legacy image path" in note, note)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3. ZERO IS AN ANSWER ────────────────────────────────────────────────────────────
def test_zero_images_is_a_valid_brief_not_a_failure():
    print("\ntest_3_a_valid_zero_image_brief_is_success")
    b = brief(0)
    b["images"] = []
    rc, ad, images, published = publish_once(
        CURRENT_POST, {"ok": True, "brief": b, "reason": ""}, sidecar=SIDECAR)
    check("the article published", rc == 0 and published)
    check("the zero-image brief was forwarded", images.briefs == [b])
    check("it was NOT read as an art-director failure",
          len(images.calls) == 1 and images.calls[0].get("brief") is not None)
    check("the fixed three-image recipe was NOT invoked instead",
          all("brief" in c for c in images.calls),
          "a call without a brief is the old recipe")


# ── 4. nothing to resolve, nothing to ask ───────────────────────────────────────────
def test_a_non_current_engine_publication_is_untouched():
    print("\ntest_4_a_legacy_publication_never_reaches_the_art_director")
    rc, ad, images, published = publish_once(
        LEGACY_POST, {"ok": True, "brief": brief(3), "reason": ""})
    check("the legacy article published", rc == 0 and published)
    check("the art director was never called", ad.calls == [], str(ad.calls))
    check("the legacy image path ran, with no brief",
          len(images.calls) == 1 and "brief" not in images.calls[0])

    # A CURRENT_ENGINE article naming a run that does not resolve is the same answer.
    rc2, ad2, images2, _ = publish_once(
        CURRENT_POST, {"ok": True, "brief": brief(1), "reason": ""},
        run_id=OTHER_RUN_ID)
    check("an unresolvable run is asked for no art direction", ad2.calls == [])
    # The direct publisher REFUSES it rather than silently doing nothing: the exact run
    # is part of the terminal contract, and a candidate that cannot name a retainable
    # run is not publishable. rc 1, no images, nothing promoted.
    check("...and is refused by the retention assertion, not published unauditable",
          rc2 == 1 and not images2.calls)


# ── 5 & 6. same run only, and optional ──────────────────────────────────────────────
def test_context_comes_from_the_exact_run_and_only_from_it():
    print("\ntest_5_architecture_and_visual_context_come_from_the_exact_run")
    import publish_best as PB
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="adrun-"))
    env_before = dict(os.environ)
    try:
        ev = tmp / "evidence"
        # The article's own run, and a DIFFERENT, NEWER run beside it carrying other
        # context. A "latest run" search would take the wrong one; nothing here searches.
        build_run(ev, run_id=RUN_ID, sidecar=SIDECAR)
        other = build_run(ev, run_id=OTHER_RUN_ID, sidecar=OTHER_SIDECAR)
        (other / "ARCHITECTURE.json").write_text(json.dumps({"beats": [{"beat_id": "XX"}]}))
        os.environ["NEW_ENGINE_EVIDENCE_ROOT"] = str(ev)
        post = tmp / "post.md"
        post.write_text(CURRENT_POST)

        ad = ADRecorder({"ok": True, "brief": brief(1), "reason": ""})
        sys.modules["art_director"] = ad.as_module()
        b, arch, _ = PB.art_direct_for(post)
        sys.modules.pop("art_director", None)
        call = ad.calls[0]
        check("the architecture is the one this article's run holds", call["arch"] == ARCH)
        check("the visual sidecar is the one this article's run holds",
              call["visual_sidecar"] == SIDECAR)
        check("no other run's architecture leaked in", call["arch"] != {"beats": [{"beat_id": "XX"}]})
        check("no other run's sidecar leaked in", call["visual_sidecar"] != OTHER_SIDECAR)
        check("the settled article is what it read, not a draft or a reconstruction",
              call["article_text"].strip() == BODY.strip())
        check("title, dek and persona come from the published front matter",
              call["title"] == "A pavilion on six columns"
              and call["dek"].startswith("Six columns")
              and call["persona"] == "Maya Flux")

        print("\ntest_6_missing_architecture_or_sidecar_is_nonblocking")
        # The sidecar is the ordinary absence: most runs have none.
        shutil.rmtree(ev / RUN_ID)
        build_run(ev, run_id=RUN_ID)                       # no VISUAL_OBSERVATIONS.json
        ad2 = ADRecorder({"ok": True, "brief": brief(1), "reason": ""})
        sys.modules["art_director"] = ad2.as_module()
        b2, _a2, _n2 = PB.art_direct_for(post)
        sys.modules.pop("art_director", None)
        check("a run with no sidecar is still art-directed", b2 is not None)
        check("...with no visual context", ad2.calls[0]["visual_sidecar"] is None)

        (ev / RUN_ID / "ARCHITECTURE.json").write_text("{ not json")
        ad3 = ADRecorder({"ok": True, "brief": brief(1), "reason": ""})
        sys.modules["art_director"] = ad3.as_module()
        b3, a3, _n3 = PB.art_direct_for(post)
        sys.modules.pop("art_director", None)
        check("an unreadable architecture is absent, not fatal",
              b3 is not None and a3 is None and ad3.calls[0]["arch"] is None)
    finally:
        sys.modules.pop("art_director", None)
        os.environ.clear()
        os.environ.update(env_before)
        shutil.rmtree(tmp, ignore_errors=True)


# ── 7. text only, always ────────────────────────────────────────────────────────────
def test_no_image_bytes_or_paths_are_sent():
    print("\ntest_7_the_art_director_receives_text_only")
    rc, ad, images, _ = publish_once(
        CURRENT_POST, {"ok": True, "brief": brief(1), "reason": ""}, sidecar=SIDECAR)
    call = ad.calls[0]
    flat = json.dumps(call, default=str)
    check("no argument is a filesystem path",
          not any(isinstance(v, pathlib.PurePath) for v in call.values()))
    check("no argument is raw bytes",
          not any(isinstance(v, (bytes, bytearray)) for v in call.values()))
    check("no asset reference reaches it", "/assets/" not in flat)
    check("no image file name reaches it",
          not any(ext in flat for ext in (".jpg", ".png", ".jpeg", ".webp")))
    # Read from the source too: the recorder only sees what THIS fixture passed, and the
    # prohibition is on the argument list itself.
    tree = ast.parse((HERE / "publish_best.py").read_text())
    site = next(n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "art_direct")
    names = sorted(k.arg for k in site.keywords)
    check("the wiring passes only the text-only arguments",
          names == ["arch", "dek", "persona", "title", "visual_sidecar"], str(names))
    check("...and one positional article text, not a file",
          len(site.args) == 2 and getattr(site.args[1].func, "id", "") == "article_body",
          ast.dump(site.args[1]) if len(site.args) > 1 else "")


# ── 8. one call, structurally ───────────────────────────────────────────────────────
def test_one_art_director_call_per_canonical_publication():
    print("\ntest_8_one_call_per_canonical_publication_at_most")
    src = (HERE / "publish_best.py").read_text()
    tree = ast.parse(src)
    sites = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "art_direct_for"]
    check("there is exactly one call site", len(sites) == 1, "%d found" % len(sites))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "art_direct_for")
    inner = [n for n in ast.walk(fn)
             if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "art_direct"]
    check("art_direct_for makes one model call and does not retry", len(inner) == 1)
    check("...and no loop wraps it",
          not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(fn)))
    # ONE mechanics function holds the move, and both callers -- the direct
    # CURRENT_ENGINE publisher and the legacy backlog selector -- go through it once
    # per run, so the call site above runs at most once either way.
    check("the promotion move exists in exactly one place",
          src.count("shutil.move(str(draft), str(dest))") == 1)
    fn_promote = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "promote_candidate")
    check("the art-direction call site is inside that one function, exactly once",
          len([n for n in ast.walk(fn_promote) if isinstance(n, ast.Call)
               and getattr(n.func, "id", "") == "art_direct_for"]) == 1)
    # The only loop in promote_candidate is the rollback that unlinks this run's own
    # generated assets. Nothing loops over the art director or over candidates.
    check("no loop in promote_candidate contains the art-direction call",
          not any(any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "art_direct_for"
                      for c in ast.walk(n))
                  for n in ast.walk(fn_promote) if isinstance(n, (ast.For, ast.While))))
    for caller in ("publish_candidate", "main"):
        f = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == caller)
        calls = [n for n in ast.walk(f) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "promote_candidate"]
        check("%s promotes at most one candidate per run" % caller, len(calls) == 1,
              "%d call(s)" % len(calls))
    check("no derivative edition generates its own images",
          "illustrate_post" not in (HERE / "translate_publication.py").read_text(),
          "a translation reuses the canonical asset set")
    # And measured, not only read: a full publication makes exactly one.
    _rc, ad, _images, _p = publish_once(
        CURRENT_POST, {"ok": True, "brief": brief(2), "reason": ""}, sidecar=SIDECAR)
    check("a full publication made exactly one art-direction call", len(ad.calls) == 1)


def main() -> int:
    test_current_engine_publication_is_art_directed()
    test_a_refused_brief_falls_back_to_the_legacy_path()
    test_zero_images_is_a_valid_brief_not_a_failure()
    test_a_non_current_engine_publication_is_untouched()
    test_context_comes_from_the_exact_run_and_only_from_it()
    test_no_image_bytes_or_paths_are_sent()
    test_one_art_director_call_per_canonical_publication()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED (%d): %s" % (len(FAILURES), "; ".join(FAILURES)))
        return 1
    print("art director wiring: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

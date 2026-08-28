#!/usr/bin/env python3
"""
grounding_v2_shadow_test.py -- the shadow grounder's coverage and powerlessness.

Two things are under test and they matter equally. First, that no article sentence can
be lost: a model failure, a truncated reply, a missing id or an invalid schema must all
produce UNRESOLVED_BOUNDARY, never silence and never a verdict against the writer.
Second, that this whole path has no authority -- it cannot set GROUNDING_FINDINGS, move
a decision, or make a held article publishable, and it does not run at all unless
someone turns it on.

No network. Every model call is stubbed.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import claims as CL                       # noqa: E402
from new_engine_v1 import contracts as C                     # noqa: E402
from new_engine_v1 import evidence as EV                     # noqa: E402
from new_engine_v1 import grounding_v2 as GV2                # noqa: E402
from new_engine_v1 import runner as R                        # noqa: E402
from new_engine_v1.provider import Completion, ProviderError  # noqa: E402
from research_pack_fixture import stub_pack                  # noqa: E402
import new_engine_v1_test as T                               # noqa: E402

FAILURES: list = []
AT = "2026-08-28T00:00:00+00:00"

ARTICLE = ("The museum opened the retrospective in 1975. It gathers nearly 100 pieces "
           "and travels next year. The eyes in the foliage are the reason to look.")

PACK = {"sources": [
    {"source_id": "S0", "role": "ANCHOR", "url": "https://anchor.example/a",
     "publisher": "anchor.example", "accessed_at": AT, "fetch_status": "ok",
     "content_length": 0, "sha256": "", "excerpts": [],
     "text": ("The museum first showed her work to New York in 1975. The retrospective "
              "gathers nearly 100 pieces covering the entirety of the artist's output. "
              "Eyes recur throughout the foliage of the later drawings.")},
    {"source_id": "S3", "role": "INDEPENDENT", "url": "https://museum.example/b",
     "publisher": "museum.example", "accessed_at": AT, "fetch_status": "ok",
     "content_length": 0, "sha256": "", "excerpts": [],
     "text": ("The touring retrospective brings together more than 100 of her "
              "fantastical drawings and opens in October.")}]}


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:200]))
    if not ok:
        FAILURES.append(label)


class StubProvider:
    """Scripted typing + classification. `typing` may be a string (raw reply) to
    simulate truncation or malformed output."""

    def __init__(self, typing=None, classification=None, fail_typing=False,
                 fail_classify=False):
        self.typing, self.classification = typing, classification
        self.fail_typing, self.fail_classify = fail_typing, fail_classify
        self.typing_calls = self.classify_calls = 0

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        if "label sentences" in system:
            self.typing_calls += 1
            if self.fail_typing:
                raise ProviderError("stub: typing provider failure")
            body = self.typing if isinstance(self.typing, str) else json.dumps(
                self.typing if self.typing is not None else _auto_typing(user))
        else:
            self.classify_calls += 1
            if self.fail_classify:
                raise ProviderError("stub: classifier provider failure")
            body = json.dumps(self.classification or {
                "classification": "SUPPORTED", "supporting_source_ids": ["S0"],
                "supporting_exact_quotes": ["The museum first showed her work to New York in 1975."],
                "unsupported_residue": "", "conflict_description": ""})
        return Completion(text=body, requested_model="m", actual_model="m",
                          provider_label="StubProvider")


def _auto_typing(user):
    ids = [ln.split('"')[3] for ln in user.splitlines() if '"sentence_id"' in ln]
    return {"sentences": [{"sentence_id": i, "type": "EMPIRICAL",
                           "atoms": [{"claim": "atom for %s" % i, "verbatim": False,
                                      "claim_type": "EMPIRICAL"}]} for i in ids]}


# ── coverage backbone ─────────────────────────────────────────────────────────
def test_every_sentence_survives():
    sents = CL.segment(ARTICLE)
    check("segmentation is deterministic", [s["exact_span"] for s in CL.segment(ARTICLE)]
          == [s["exact_span"] for s in sents])
    check("offsets and hashes verify against the article",
          CL.verify_backbone(ARTICLE, sents) == [])
    check("every sentence is covered", len(sents) == 3, [s["exact_span"] for s in sents])

    p = StubProvider()
    out = CL.identify(p, ARTICLE, sents)
    check("one record per sentence", len(out["records"]) == len(sents))
    check("record ids match the backbone exactly",
          [r["sentence_id"] for r in out["records"]] == [s["sentence_id"] for s in sents])


def test_model_failures_become_unresolved_never_silence():
    sents = CL.segment(ARTICLE)
    for label, provider in (
            ("provider failure", StubProvider(fail_typing=True)),
            ("truncated reply", StubProvider(typing='{"sentences": [{"sentence_id": "S001"')),
            ("prose instead of JSON", StubProvider(typing="I think these are all fine")),
            ("invalid type value", StubProvider(typing={"sentences": [
                {"sentence_id": "S001", "type": "PROBABLY", "atoms": [{"claim": "x"}]}]})),
            ("missing sentence_id", StubProvider(typing={"sentences": [
                {"sentence_id": "S001", "type": "EMPIRICAL",
                 "atoms": [{"claim": "x", "claim_type": "EMPIRICAL"}]}]})),
            ("unknown sentence_id invented", StubProvider(typing={"sentences": [
                {"sentence_id": "S999", "type": "EMPIRICAL",
                 "atoms": [{"claim": "x", "claim_type": "EMPIRICAL"}]}]})),
            ("no atoms returned", StubProvider(typing={"sentences": [
                {"sentence_id": s["sentence_id"], "type": "EMPIRICAL", "atoms": []}
                for s in sents]}))):
        out = CL.identify(provider, ARTICLE, sents)
        check("%s: no sentence is dropped" % label,
              len(out["records"]) == len(sents))
        unresolved = [r for r in out["records"] if r["type"] == CL.UNRESOLVED]
        check("%s: unresolved rather than absent" % label, len(unresolved) >= 1,
              [r["type"] for r in out["records"]])
        check("%s: unresolved carries its parent span" % label,
              all(r["parent_exact_span"] for r in unresolved))
        check("%s: unresolved claims are never classified" % label,
              all(u["sentence_id"] not in
                  {c["parent_sentence_id"] for c in CL.claims_for_classification(out["records"])}
                  for u in unresolved))


def test_derived_atoms_keep_their_parent_span():
    sents = CL.segment(ARTICLE)
    p = StubProvider(typing={"sentences": [
        {"sentence_id": sents[1]["sentence_id"], "type": "EMPIRICAL", "atoms": [
            {"claim": "It gathers nearly 100 pieces", "verbatim": True,
             "claim_type": "EMPIRICAL"},
            {"claim": "The retrospective travels next year", "verbatim": False,
             "claim_type": "EMPIRICAL"}]}]})
    out = CL.identify(p, ARTICLE, [sents[1]])
    atoms = out["records"][0]["atoms"]
    check("a literal atom is marked VERBATIM", atoms[0]["derivation"] == "VERBATIM")
    check("a rewritten atom is marked DERIVED", atoms[1]["derivation"] == "DERIVED",
          atoms[1])
    check("both atoms keep the parent sentence id",
          all(a["parent_sentence_id"] == sents[1]["sentence_id"] for a in atoms))
    check("the parent span is preserved verbatim",
          out["records"][0]["parent_exact_span"] == sents[1]["exact_span"])
    check("the derived atom is not passed off as article text",
          atoms[1]["atomic_claim"] not in ARTICLE)


def test_interpretation_cannot_hide_an_empirical_component():
    sents = CL.segment(ARTICLE)
    p = StubProvider(typing={"sentences": [
        {"sentence_id": sents[0]["sentence_id"], "type": "MIXED", "atoms": [
            {"claim": "The museum opened the retrospective in 1975", "verbatim": False,
             "claim_type": "EMPIRICAL"},
            {"claim": "the opening was overdue", "verbatim": False,
             "claim_type": "INTERPRETIVE"}]}]})
    out = CL.identify(p, ARTICLE, [sents[0]])
    to_classify = CL.claims_for_classification(out["records"])
    interp = CL.interpretation_candidates(out["records"])
    check("the empirical half of a MIXED sentence is still classified",
          len(to_classify) == 1 and to_classify[0]["claim_type"] == CL.EMPIRICAL)
    check("the interpretive half is recorded separately", len(interp) == 1)
    check("marking a sentence INTERPRETIVE is not a way past classification",
          to_classify[0]["parent_type"] == CL.MIXED)


# ── evidence retrieval ────────────────────────────────────────────────────────
def test_retrieval_finds_evidence_and_never_invents_absence():
    idx = EV.PackIndex(PACK)
    ev = idx.retrieve("The museum opened the retrospective in 1975")
    check("a well-signalled claim retrieves ranked evidence", ev["status"] == EV.RETRIEVED)
    check("the retrieved block carries source id, span and score",
          all(k in ev["blocks"][0] for k in ("source_id", "exact_span", "score", "position")))
    check("the right source was found", any("1975" in b["exact_span"] for b in ev["blocks"]))

    short = idx.retrieve("She was self-taught.")
    check("a short low-signal claim escalates instead of returning nothing",
          short["status"] in (EV.FALLBACK_SOURCE, EV.FALLBACK_PACK), short)
    check("escalation still supplies real source text", bool(short["blocks"]))
    check("escalation is never UNSUPPORTED", short["status"] != GV2.UNSUPPORTED)

    empty = EV.PackIndex({"sources": []}).retrieve("anything at all")
    check("an unusable pack reports EVIDENCE_RETRIEVAL_INCOMPLETE",
          empty["status"] == EV.INCOMPLETE)
    result = GV2.classify(StubProvider(), "anything at all", empty)
    check("an incomplete retrieval is not sent to the classifier",
          result["classification"] == EV.INCOMPLETE)
    check("and it is NOT recorded as unsupported",
          result["classification"] != GV2.UNSUPPORTED)


def test_conflicting_sources_are_both_retrieved():
    idx = EV.PackIndex(PACK)
    ev = idx.retrieve("The retrospective gathers nearly 100 pieces")
    ids = {b["source_id"] for b in ev["blocks"]}
    check("both sides of a genuine conflict are supplied", ids >= {"S0", "S3"}, ids)


# ── focused classifier ────────────────────────────────────────────────────────
def test_classifier_structure_is_validated_not_repaired():
    idx = EV.PackIndex(PACK)
    ev = idx.retrieve("The museum opened the retrospective in 1975")
    good = {"classification": "SUPPORTED", "supporting_source_ids": ["S0"],
            "supporting_exact_quotes": ["The museum first showed her work to New York in 1975."],
            "unsupported_residue": "", "conflict_description": ""}
    check("a well-formed SUPPORTED reply validates", GV2.validate(good, ev) == [])
    for label, reply, needle in (
            ("SUPPORTED with residue", dict(good, unsupported_residue="the date"), "residue"),
            ("SUPPORTED without a quote", dict(good, supporting_exact_quotes=[]), "without a supporting quote"),
            ("UNSUPPORTED without residue",
             dict(good, classification="UNSUPPORTED", unsupported_residue=""), "unsupported_residue"),
            ("unknown source id", dict(good, supporting_source_ids=["S99"]), "not supplied"),
            ("quote that is not in the evidence",
             dict(good, supporting_exact_quotes=["the museum opened in 1971"]), "verbatim"),
            ("TRUE_UNCERTAIN without a conflict description",
             dict(good, classification="TRUE_UNCERTAIN", conflict_description=""), "conflict_description"),
            ("bad enum", dict(good, classification="PROBABLY_FINE"), "not in")):
        errs = GV2.validate(reply, ev)
        check("rejected: %s" % label, any(needle in e for e in errs), errs)

    bad = GV2.classify(StubProvider(classification=dict(good, unsupported_residue="x")),
                       "claim", ev)
    check("an invalid reply becomes SHADOW_CLASSIFIER_ERROR",
          bad["classification"] == GV2.CLASSIFIER_ERROR)
    check("and it is never auto-repaired into a verdict",
          bad["classification"] not in (GV2.SUPPORTED, GV2.UNSUPPORTED))
    err = GV2.classify(StubProvider(fail_classify=True), "claim", ev)
    check("a provider failure is an error, not an unsupported claim",
          err["classification"] == GV2.CLASSIFIER_ERROR)


# ── no authority ──────────────────────────────────────────────────────────────
def test_shadow_is_off_by_default_and_cannot_touch_the_decision():
    os.environ.pop(GV2.SHADOW_ENV, None)
    check("shadow is OFF when the variable is unset", GV2.enabled() is False)
    for v in ("0", "off", "false", "", "no", "maybe"):
        os.environ[GV2.SHADOW_ENV] = v
        check("shadow stays OFF for %r" % v, GV2.enabled() is False)
    os.environ.pop(GV2.SHADOW_ENV, None)

    with tempfile.TemporaryDirectory() as d:
        out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "off", AT,
                    mode=R.MODE_LIVE, research_fn=stub_pack)
        files = {p.name for p in (pathlib.Path(d) / "off").glob("*")}
        check("no shadow artifact is written when OFF",
              "GROUNDING_V2_SHADOW.json" not in files, sorted(files))
        check("the production decision is unaffected", out["decision"] == "ACCEPT",
              out["reasons"])
        baseline_stages = set(out["artifacts"])

    os.environ[GV2.SHADOW_ENV] = "1"
    try:
        with tempfile.TemporaryDirectory() as d:
            out2 = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "on", AT,
                         mode=R.MODE_LIVE, research_fn=stub_pack)
            files = {p.name for p in (pathlib.Path(d) / "on").glob("*")}
            check("shadow writes its own artifact when ON",
                  "GROUNDING_V2_SHADOW.json" in files, sorted(files))
            check("the artifact map is unchanged by the shadow",
                  set(out2["artifacts"]) == baseline_stages)
            check("the shadow artifact is not an engine stage",
                  GV2.ARTIFACT not in C.STAGE_ORDER)
            check("decision.py never sees it",
                  GV2.ARTIFACT not in out2["artifacts"])
            check("the decision is identical with the shadow running",
                  out2["decision"] == "ACCEPT", out2["reasons"])
            payload = json.loads((pathlib.Path(d) / "on" / "GROUNDING_V2_SHADOW.json").read_text())
            check("the artifact declares it has no authority",
                  payload.get("shadow") is True and "NONE" in payload.get("authority", ""))
    finally:
        os.environ.pop(GV2.SHADOW_ENV, None)


def test_shadow_failure_cannot_break_a_production_run():
    os.environ[GV2.SHADOW_ENV] = "1"
    real = GV2.run_shadow
    GV2.run_shadow = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("shadow exploded"))
    try:
        with tempfile.TemporaryDirectory() as d:
            out = R.run(T._source_payload(), pathlib.Path(d), T.StubProvider(), "boom", AT,
                        mode=R.MODE_LIVE, research_fn=stub_pack)
            check("a shadow crash does not change the decision", out["decision"] == "ACCEPT")
            payload = json.loads((pathlib.Path(d) / "boom" / "GROUNDING_V2_SHADOW.json").read_text())
            check("the crash is recorded in the shadow artifact", "error" in payload)
    finally:
        GV2.run_shadow = real
        os.environ.pop(GV2.SHADOW_ENV, None)


def test_production_modules_are_untouched():
    import inspect
    from new_engine_v1 import decision, stages, research
    check("decision.py does not know the shadow exists",
          "grounding_v2" not in inspect.getsource(decision)
          and "GROUNDING_V2" not in inspect.getsource(decision))
    check("stages.py (Writer/Form/grounder) does not import it",
          "grounding_v2" not in inspect.getsource(stages))
    check("research.py is untouched by it", "grounding_v2" not in inspect.getsource(research))
    bridge = (HERE / "publication_safety_bridge.py").read_text()
    check("the safety bridge never reads the shadow artifact",
          "GROUNDING_V2" not in bridge and "grounding_v2" not in bridge)
    check("the shadow module cannot reach the network",
          not ({"urllib", "socket", "requests", "http"} &
               {n.split(".")[0] for n in _imports(HERE / "new_engine_v1" / "grounding_v2.py")}))
    check("claims.py cannot reach the network",
          not ({"urllib", "socket", "requests", "http"} &
               {n.split(".")[0] for n in _imports(HERE / "new_engine_v1" / "claims.py")}))
    check("evidence.py cannot reach the network",
          not ({"urllib", "socket", "requests", "http"} &
               {n.split(".")[0] for n in _imports(HERE / "new_engine_v1" / "evidence.py")}))


def _imports(path):
    import ast
    names = set()
    for n in ast.walk(ast.parse(path.read_text())):
        if isinstance(n, ast.Import):
            names |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            names.add(n.module)
    return names


def test_bounds_are_declared_and_finite():
    for name, value, ceiling in (("MAX_SENTENCES_PER_BATCH", CL.MAX_SENTENCES_PER_BATCH, 20),
                                 ("MAX_BATCH_CHARS", CL.MAX_BATCH_CHARS, 20_000),
                                 ("BATCH_MAX_TOKENS", CL.BATCH_MAX_TOKENS, 4_000),
                                 ("MAX_BATCHES_PER_ARTICLE", CL.MAX_BATCHES_PER_ARTICLE, 20),
                                 ("MAX_CLAIMS_CLASSIFIED", GV2.MAX_CLAIMS_CLASSIFIED, 100),
                                 ("FULL_PACK_CHARS", EV.FULL_PACK_CHARS, 40_000)):
        check("%s is bounded (%s)" % (name, value), 0 < value <= ceiling)
    src = (HERE / "new_engine_v1" / "claims.py").read_text()
    check("identification has no retry loop", "while True" not in src)


def main():
    for fn in (test_every_sentence_survives,
               test_model_failures_become_unresolved_never_silence,
               test_derived_atoms_keep_their_parent_span,
               test_interpretation_cannot_hide_an_empirical_component,
               test_retrieval_finds_evidence_and_never_invents_absence,
               test_conflicting_sources_are_both_retrieved,
               test_classifier_structure_is_validated_not_repaired,
               test_shadow_is_off_by_default_and_cannot_touch_the_decision,
               test_shadow_failure_cannot_break_a_production_run,
               test_production_modules_are_untouched,
               test_bounds_are_declared_and_finite):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL GROUNDER-V2 SHADOW TESTS PASSED")


if __name__ == "__main__":
    main()

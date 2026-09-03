#!/usr/bin/env python3
"""
grounding_v2_batch_test.py -- batched focused classification, and the shadow's clock.

One claim per call was 40 calls, ~$0.85-1.10 and 65-85s per article, and that cost is
the recorded reason V2 has never run as a production shadow. Batching groups claims that
have ALREADY been identified; it never hands the model an article and asks which claims
matter, because that combined task is the instability V2 exists to avoid.

So these tests are mostly about what batching must not be allowed to cost: a claim may
not vanish because another shared its request, a result may not cite a neighbour's
evidence, and a malformed batch may not become verdicts. Every existing per-claim
validation rule still applies to every record.

No provider. The frozen real-model benchmark lives in the PR description.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import claims as CL                               # noqa: E402
from new_engine_v1 import evidence as EV                             # noqa: E402
from new_engine_v1 import grounding_v2 as GV2                        # noqa: E402
from grounding_v2_shadow_test import CONFLICT_PACK, _auto_typing     # noqa: E402

FAILURES: list = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


IDX = EV.PackIndex(CONFLICT_PACK)
GOOD_CLAIM = "A work titled Temple by the Sea dates from 1955."


def ev_for(claim=GOOD_CLAIM):
    return IDX.retrieve(claim)


def a_quote(ev):
    return ev["blocks"][0]["exact_span"]


def a_source(ev):
    return ev["blocks"][0]["source_id"]


class Recorder:
    """Counts calls and returns a canned batch payload built from the request."""

    def __init__(self, shape="ok", sleep=0.0, evidence=None):
        self.calls, self.deadlines, self.timeouts = [], [], []
        self.shape, self.sleep = shape, sleep
        # per-claim evidence, so a well-behaved stub cites only its own claim's blocks
        self.evidence = evidence or {}

    def complete(self, system, user, max_tokens=3000, timeout=180,
                 temperature=None, deadline=None):
        self.calls.append(user)
        self.deadlines.append(deadline)
        self.timeouts.append(timeout if deadline is None
                             else min(timeout, deadline - time.monotonic()))
        if self.sleep:
            time.sleep(self.sleep)
        ids = [l.split("CLAIM_ID: ")[1].strip()
               for l in user.splitlines() if l.startswith("CLAIM_ID: ")]
        if not ids:                                    # identification call
            # the shadow test's own generator, so this stub cannot drift from the
            # schema claims.identify actually parses
            return _C(json.dumps(_auto_typing(user)))
        def rec(cid):
            ev = self.evidence.get(cid) or ev_for()
            return {"claim_id": cid, "classification": "SUPPORTED",
                    "supporting_source_ids": [a_source(ev)],
                    "supporting_exact_quotes": [a_quote(ev)],
                    "unsupported_residue": "", "conflict_description": ""}
        rs = [rec(i) for i in ids]
        if self.shape == "missing":
            rs = rs[:-1]
        elif self.shape == "duplicate":
            rs[-1] = dict(rs[0])
        elif self.shape == "unknown":
            rs[-1] = rec("C99")
        elif self.shape == "extra":
            rs.append(rec("C99"))
        elif self.shape == "one_invalid":
            rs[1]["unsupported_residue"] = "x"          # SUPPORTED with a residue
        elif self.shape == "cross_claim":
            rs[0]["supporting_exact_quotes"] = ["a quote nobody supplied for C01"]
        elif self.shape == "unparsable":
            return _C("not json at all")
        return _C(json.dumps({"results": rs}))


class _C:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"actual_model": "stub", "usage": {}}


def items_for(ids):
    ev = ev_for()
    return [(i, GOOD_CLAIM, EV.render(ev)) for i in ids], {i: ev for i in ids}


# ── A / B / C / J: batching arithmetic and order ──────────────────────────────
def test_batching_is_deterministic_and_covers_every_claim():
    for n, expect in ((4, 1), (5, 2), (40, 10), (1, 1), (8, 2), (11, 3)):
        groups = GV2.batches(list(range(n)))
        check("%d claims -> %d batch(es)" % (n, expect), len(groups) == expect,
              [len(g) for g in groups])
        flat = [x for g in groups for x in g]
        check("  every claim exactly once, in order", flat == list(range(n)), flat)
    check("batch size is the declared constant", GV2.CLASSIFY_BATCH_SIZE == 4)
    check("batch ceiling matches the claim ceiling",
          GV2.MAX_CLASSIFY_BATCHES * GV2.CLASSIFY_BATCH_SIZE >= GV2.MAX_CLAIMS_CLASSIFIED
          and GV2.MAX_CLASSIFY_BATCHES == 10)
    # behavioural, not a prose scan: shuffled input comes back in ITS OWN order,
    # so nothing is ranked or re-sorted inside batches()
    odd = ["C07", "C01", "C99", "C03"]
    check("no ranking or re-sorting happens in batches()",
          [x for g in GV2.batches(odd, 2) for x in g] == odd,
          GV2.batches(odd, 2))


# ── D: one record per requested id ───────────────────────────────────────────
def test_four_claims_one_call_four_records():
    ids = ["C01", "C02", "C03", "C04"]
    items, evs = items_for(ids)
    p = Recorder()
    out = GV2.classify_batch(p, items, evs)
    check("one provider call", len(p.calls) == 1, len(p.calls))
    check("four records", sorted(out) == ids, sorted(out))
    check("each is a real verdict",
          all(out[i]["classification"] in GV2.ENUM for i in ids),
          {i: out[i]["classification"] for i in ids})
    check("each records its batch size", all(out[i]["batch_size"] == 4 for i in ids))
    check("the prompt carries one labelled capsule per claim",
          all(("CLAIM_ID: %s" % i) in p.calls[0] for i in ids))
    check("and says evidence is not shared between claims",
          "NOT evidence for another" in GV2.BATCH_SYSTEM)


# ── E / F / G: the batch contract ────────────────────────────────────────────
def test_a_broken_batch_contract_errors_every_claim_in_it():
    ids = ["C01", "C02", "C03", "C04"]
    items, evs = items_for(ids)
    for shape, needle in (("missing", "results for"), ("duplicate", "repeated"),
                          ("unknown", "do not match"), ("extra", "results for"),
                          ("unparsable", "Error")):
        out = GV2.classify_batch(Recorder(shape), items, evs)
        check("%s -> every claim is a classifier error" % shape,
              all(out[i]["classification"] == GV2.CLASSIFIER_ERROR for i in ids),
              {i: out[i]["classification"] for i in ids})
        check("  no verdict was manufactured",
              not any(out[i]["classification"] in GV2.ENUM for i in ids))
        check("  and the reason is recorded",
              any(needle.lower() in (out["C01"].get("detail", "")
                                     + " ".join(out["C01"]["errors"])).lower()
                  for _ in [0]),
              out["C01"].get("detail") or out["C01"]["errors"])
    check("no retry path exists",
          "for attempt in range" not in
          (HERE / "new_engine_v1" / "grounding_v2.py").read_text())


# ── H: cross-claim evidence ──────────────────────────────────────────────────
def test_a_result_may_not_cite_a_neighbours_evidence():
    ids = ["C01", "C02"]
    ev_a, ev_b = IDX.retrieve(GOOD_CLAIM), IDX.retrieve("The artist was self-taught.")
    items = [("C01", GOOD_CLAIM, EV.render(ev_a)),
             ("C02", "The artist was self-taught.", EV.render(ev_b))]
    evs = {"C01": ev_a, "C02": ev_b}
    out = GV2.classify_batch(Recorder("cross_claim", evidence=evs), items, evs)
    check("the offending claim is a classifier error",
          out["C01"]["classification"] == GV2.CLASSIFIER_ERROR, out["C01"])
    check("and says the quote was not in ITS evidence",
          any("verbatim" in e for e in out["C01"]["errors"]), out["C01"]["errors"])
    check("the innocent claim is unaffected",
          out["C02"]["classification"] in GV2.ENUM, out["C02"]["classification"])
    # a source id belonging only to the other claim is also rejected
    only_b = {b["source_id"] for b in ev_b["blocks"]} - {b["source_id"] for b in ev_a["blocks"]}
    if only_b:
        errs = GV2.validate({"classification": "SUPPORTED",
                             "supporting_source_ids": [sorted(only_b)[0]],
                             "supporting_exact_quotes": [a_quote(ev_a)],
                             "unsupported_residue": "", "conflict_description": ""}, ev_a)
        check("a neighbour's source id is rejected",
              any("not supplied" in e for e in errs), errs)


# ── I: one invalid record does not spoil the valid ones ──────────────────────
def test_one_invalid_record_is_an_error_and_the_rest_stand():
    ids = ["C01", "C02", "C03", "C04"]
    items, evs = items_for(ids)
    out = GV2.classify_batch(Recorder("one_invalid"), items, evs)
    check("the invalid record is a classifier error",
          out["C02"]["classification"] == GV2.CLASSIFIER_ERROR, out["C02"])
    check("no verdict was manufactured for it",
          out["C02"]["classification"] not in GV2.ENUM)
    check("the other three keep their verdicts",
          all(out[i]["classification"] in GV2.ENUM for i in ("C01", "C03", "C04")),
          {i: out[i]["classification"] for i in ids})


# ── 17: the F1-shape protections survive batching ───────────────────────────
def test_the_validation_rules_that_stop_the_f1_shape_still_apply():
    ev = ev_for()
    base = {"classification": "SUPPORTED", "supporting_source_ids": [a_source(ev)],
            "supporting_exact_quotes": [a_quote(ev)],
            "unsupported_residue": "", "conflict_description": ""}
    for label, reply, needle in (
            ("UNSUPPORTED with no residue",
             dict(base, classification="UNSUPPORTED"), "unsupported_residue"),
            ("SUPPORTED with no quote",
             dict(base, supporting_exact_quotes=[]), "without a supporting quote"),
            ("SUPPORTED with a residue",
             dict(base, unsupported_residue="x"), "residue"),
            ("TRUE_UNCERTAIN with no conflict",
             dict(base, classification="TRUE_UNCERTAIN"), "conflict_description"),
            ("LEGITIMATE_INTERPRETATION with no basis quote",
             dict(base, classification="LEGITIMATE_INTERPRETATION",
                  supporting_exact_quotes=[]), "factual basis"),
            ("bad enum", dict(base, classification="PROBABLY_FINE"), "not in")):
        check("still rejected in a batch: %s" % label,
              any(needle in e for e in GV2.validate(reply, ev)),
              GV2.validate(reply, ev))
    check("batch results are validated by the SAME function",
          "errs = validate(r, ev)" in
          (HERE / "new_engine_v1" / "grounding_v2.py").read_text())
    check("no free-text explanation field is introduced",
          '"why"' not in GV2.batch_prompt([("C01", "c", "e")]))


# ── K / L / M: the shadow clock ─────────────────────────────────────────────
def test_the_deadline_starts_first_and_bounds_every_call():
    src = (HERE / "new_engine_v1" / "grounding_v2.py").read_text()
    body = src.split("def run_shadow(")[1]
    check("the deadline is taken before identification",
          body.index("deadline = started +") < body.index("CL.identify("), body[:0])
    check("identification receives it", "CL.identify(provider, article_text, sentences, "
          "deadline=deadline)" in body)
    check("classification receives it", "deadline=deadline)" in
          src.split("def classify_batch(")[1])
    check("provider.complete clamps each leg to what is left",
          "leg_timeout = max(1, int(min(timeout, remaining)))" in
          (HERE / "new_engine_v1" / "provider.py").read_text())
    check("the totals are explicit constants",
          GV2.GROUNDING_V2_TOTAL_SECONDS == 120 and GV2.MIN_CALL_SECONDS == 10)

    ids = ["C01", "C02"]
    items, evs = items_for(ids)
    p = Recorder()
    dl = time.monotonic() + 5
    GV2.classify_batch(p, items, evs, deadline=dl)
    check("the batch call is given the shared deadline", p.deadlines[0] == dl)
    check("and its effective timeout is <= what remained",
          p.timeouts[0] <= 5.01, p.timeouts[0])


def test_a_deadline_reached_mid_run_is_recorded_never_a_verdict():
    pack = CONFLICT_PACK
    art = ("The museum opened the retrospective in 1975. The artist was self-taught. "
           "A work dates from 1955. The gardens grew vegetables. "
           "A depiction dates from 1954. The count is disputed.")
    # exhausted before anything: identification still runs (its own calls are clamped),
    # classification cannot start
    out = GV2.run_shadow(Recorder(), article_text=art, pack=pack, total_seconds=0.0)
    m = out["metrics"]
    check("the run reports the deadline was exhausted", m["deadline_exhausted"] is True, m)
    check("no classification call was made", m["classification_calls"] == 0, m)
    states = {f["result"]["classification"] for f in out["findings"]}
    check("unreached claims are SHADOW_DEADLINE_EXHAUSTED",
          states <= {GV2.DEADLINE_EXHAUSTED, GV2.NOT_CLASSIFIED_RETRIEVAL}, states)
    check("and none of them is a verdict", not (states & set(GV2.ENUM)), states)
    check("every identified claim is marked exhausted, not left blank",
          m["claims_identified"] >= 1
          and m["deadline_exhausted_claims"] == m["claims_identified"], m)
    check("and none was classified", m["claims_classified"] == 0, m)
    check("elapsed and the bound are both recorded",
          "elapsed_seconds" in m and m["total_seconds_bound"] == 0.0, m)

    # identification affordable, classification not: the claims exist and are marked
    # the stub must consume wall clock, or nothing can run out of it: identification
    # burns the budget and classification is then below the minimum start window
    mid = GV2.run_shadow(Recorder(sleep=0.7), article_text=art, pack=pack,
                         total_seconds=1.0, min_call_seconds=0.5)
    mm = mid["metrics"]
    check("mid-run exhaustion is reported", mm["deadline_exhausted"] is True, mm)
    check("identification ran", mm["identification_calls"] >= 1, mm)
    check("classification did not", mm["classification_calls"] == 0, mm)
    check("and every unreached claim is counted",
          mm["deadline_exhausted_claims"] == mm["claims_identified"]
          and mm["claims_identified"] >= 1, mm)
    check("none of them became a verdict",
          not ({f["result"]["classification"] for f in mid["findings"]} & set(GV2.ENUM)),
          mm["classification_distribution"])

    # a call is not STARTED below the minimum window
    out2 = GV2.run_shadow(Recorder(), article_text=art, pack=pack,
                          total_seconds=GV2.MIN_CALL_SECONDS - 1,
                          min_call_seconds=GV2.MIN_CALL_SECONDS)
    check("no classification starts below the minimum window",
          out2["metrics"]["classification_calls"] == 0, out2["metrics"])


# ── P / Q / R: authority, off-by-default, and the bound ─────────────────────
def test_the_shadow_still_has_no_authority_and_no_calls_when_off():
    import os
    from new_engine_v1 import runner as R
    prev = os.environ.pop(GV2.SHADOW_ENV, None)
    try:
        check("OFF by default", GV2.enabled() is False)
        p = Recorder()
        R._shadow_grounding_v2(p, HERE, {"article_text": "x"}, "src", CONFLICT_PACK)
        check("zero model calls when OFF", p.calls == [], p.calls)
    finally:
        if prev is not None:
            os.environ[GV2.SHADOW_ENV] = prev
    dec = (HERE / "new_engine_v1" / "decision.py").read_text()
    brg = (HERE / "publication_safety_bridge.py").read_text()
    check("decision.py never sees the shadow artefact", "GROUNDING_V2" not in dec)
    check("the safety bridge never sees it", "GROUNDING_V2" not in brg)
    rsrc = (HERE / "new_engine_v1" / "runner.py").read_text()
    check("the shadow runs after the decision is persisted",
          rsrc.index("_persist(A, run_root") < rsrc.index("_shadow_grounding_v2(provider"))
    check("its failures are swallowed", "never reaches the caller" in rsrc)


def test_the_call_ceiling_is_structural():
    # PR #60 halved the identification ceiling to 4 while DOUBLING the batch to 16, so
    # the sentence coverage ceiling this test was written to protect is the same 64
    # (8x8 then, 16x4 now) and the call bound is strictly lower: 14, was 18.
    check("identification <= 4", CL.MAX_BATCHES_PER_ARTICLE == 4)
    check("classification <= 10", GV2.MAX_CLASSIFY_BATCHES == 10)
    check("total <= 14", CL.MAX_BATCHES_PER_ARTICLE + GV2.MAX_CLASSIFY_BATCHES == 14)
    check("the sentence coverage ceiling is unchanged at 64",
          CL.MAX_SENTENCES_PER_BATCH * CL.MAX_BATCHES_PER_ARTICLE == 64,
          CL.MAX_SENTENCES_PER_BATCH * CL.MAX_BATCHES_PER_ARTICLE)
    src = (HERE / "new_engine_v1" / "grounding_v2.py").read_text()
    body = src.split("def run_shadow(")[1]
    check("the batch loop is sliced by the ceiling",
          "[:MAX_CLASSIFY_BATCHES]" in body)
    check("the claim list is sliced by the claim ceiling",
          "[:MAX_CLAIMS_CLASSIFIED]" in body)
    check("no retry or fallback loop can exceed it",
          "while True" not in src and "for attempt" not in src)
    # exactly one provider.complete per batch, and one per identification batch
    tree = ast.parse(src)
    sites = [x for x in ast.walk(tree) if isinstance(x, ast.Call)
             and isinstance(x.func, ast.Attribute) and x.func.attr == "complete"]
    check("every provider call site is temperature-pinned and deadline-aware",
          all(any(k.arg == "temperature" for k in x.keywords)
              and any(k.arg == "deadline" for k in x.keywords) for x in sites),
          len(sites))
    # run_shadow must reach the BATCH path only: the one-claim primitive stays for the
    # existing shadow tests, but the article path may not spend a call per claim.
    body = src.split("def run_shadow(")[1]
    check("run_shadow uses classify_batch, never classify() per claim",
          "classify_batch(" in body and "= classify(provider" not in body
          and "classify(provider," not in body)
    p = Recorder()
    art = " ".join("Sentence number %d states a fact." % i for i in range(40))
    out = GV2.run_shadow(p, article_text=art, pack=CONFLICT_PACK)
    m = out["metrics"]
    check("a 40-sentence article stays inside the bound",
          m["model_calls"] <= 18, m["model_calls"])
    check("  and its parts are reported separately",
          m["identification_calls"] + m["classification_calls"] == m["model_calls"], m)
    check("evidence identity is persisted", len(out.get("evidence_identity", "")) == 64)


def main() -> None:
    for fn in (test_batching_is_deterministic_and_covers_every_claim,
               test_four_claims_one_call_four_records,
               test_a_broken_batch_contract_errors_every_claim_in_it,
               test_a_result_may_not_cite_a_neighbours_evidence,
               test_one_invalid_record_is_an_error_and_the_rest_stand,
               test_the_validation_rules_that_stop_the_f1_shape_still_apply,
               test_the_deadline_starts_first_and_bounds_every_call,
               test_a_deadline_reached_mid_run_is_recorded_never_a_verdict,
               test_the_shadow_still_has_no_authority_and_no_calls_when_off,
               test_the_call_ceiling_is_structural):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL GROUNDING-V2 BATCH TESTS PASSED")


if __name__ == "__main__":
    main()

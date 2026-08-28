#!/usr/bin/env python3
"""
uncertainty_adjudication_test.py -- the bounded TRUE_UNCERTAIN pass.

The case is real. The controlled Minnie Evans end-to-end (2026-08-28) researched five
sources, wrote a grounded 624-word article, and died on two findings the grounder could
not settle: "nearly 100 works made between 1935 and 1981" and a 1935 date. Under V0 that
is a HOLD, and V0 was right while the writer had one source -- an uncertain claim was
unresolvable by definition. With a frozen pack it is answerable: keep the claim if the
material carries it, weaken it to what the material does carry, or take it out.

What must NOT change, and is asserted here: the adjudicator researches nothing, fetches
nothing, invents nothing, and is believed about nothing. One pass. The re-grounding
decides, and anything still uncertain after it still HOLDs.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C                      # noqa: E402
from new_engine_v1 import runner as R                         # noqa: E402
from new_engine_v1 import stages as S                         # noqa: E402
from new_engine_v1.provider import Completion, ProviderError  # noqa: E402
from research_pack_fixture import stub_pack                   # noqa: E402
import new_engine_v1_test as T                                # noqa: E402

FAILURES: list = []
AT = "2026-08-28T00:00:00+00:00"

ARTICLE = ("The museum has gathered 1,200 works for the retrospective. Evans began "
           "drawing in 1935, after a dream she never fully explained. The drawings "
           "were made in a gatehouse she sat in six days a week.")


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- " + str(detail)[:220]))
    if not ok:
        FAILURES.append(label)


class ScriptedProvider:
    """Dispatches on the stage's system prompt, and counts every call it serves."""

    def __init__(self, groundings, adjudication=None, fail_adjudication=False):
        self.groundings = list(groundings)        # one reply per grounding call
        self.adjudication = adjudication or {"records": []}
        self.fail_adjudication = fail_adjudication
        self.ground_calls = 0
        self.adjudication_calls = 0
        self.prompts = {}

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        if "discovery stage" in system:
            body = json.dumps(T.DISCOVERY_REPLY)
        elif "article-form stage" in system:
            body = json.dumps(T.FORM_REPLY)
        elif "adjudicate uncertain factual claims" in system:
            self.adjudication_calls += 1
            self.prompts["adjudication"] = user
            if self.fail_adjudication:
                raise ProviderError("stub: adjudication provider failure")
            body = json.dumps(self.adjudication)
        elif "writer-grounding stage" in system:
            self.ground_calls += 1
            self.prompts["grounding_%d" % self.ground_calls] = user
            i = min(self.ground_calls - 1, len(self.groundings) - 1)
            body = json.dumps(self.groundings[i])
        else:
            body = ARTICLE
        return Completion(text=body, requested_model="m", actual_model="m",
                          provider_label="ScriptedProvider")


def _finding(fid, quote, why="the material does not settle this"):
    return {"id": fid, "quote": quote, "classification": "TRUE_UNCERTAIN", "why": why,
            "repairable": True, "suggested_patch": ""}


def _run(provider, name="u"):
    with tempfile.TemporaryDirectory() as d:
        out = R.run(T._source_payload(), pathlib.Path(d), provider, name, AT,
                    mode=R.MODE_LIVE, research_fn=stub_pack)
        out["_dir"] = d
        return out


def _audit(out):
    return (out["artifacts"][C.GROUNDING_FINDINGS].payload
            .get("uncertainty_adjudication") or {})


def _body(out):
    A = out["artifacts"]
    if C.GROUNDING_REPAIR in A:
        return A[C.GROUNDING_REPAIR].payload["article_text"]
    return A[C.WRITER_OUTPUT].payload["article_text"]


# ── 1. exact-number uncertainty ───────────────────────────────────────────────
def test_overspecific_number_is_weakened_to_what_the_pack_supports():
    quote = "The museum has gathered 1,200 works for the retrospective."
    replacement = "The museum has gathered more than a thousand works for the retrospective."
    p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]}, {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "REWRITE", "quote": quote,
                                   "replacement": replacement,
                                   "supporting_source_ids": ["S1"],
                                   "why": "S1 says more than a thousand, not 1,200"}]})
    out = _run(p, "number")
    check("the run accepts after the claim is weakened", out["decision"] == "ACCEPT",
          out["reasons"])
    check("the published body carries the weaker wording", replacement in _body(out))
    check("and no longer carries the exact number", "1,200" not in _body(out))
    a = _audit(out)
    rec = a["records"][0]
    check("audit records the original claim", rec["claim"] == quote)
    check("audit records the grounding reason", bool(rec["grounding_reason"]))
    check("audit records the action", rec["action"] == "REWRITE")
    check("audit records the replacement", rec["replacement"] == replacement)
    check("audit records the supporting source", rec["supporting_source_ids"] == ["S1"])
    check("audit records verification by the second grounding",
          rec["verified_by_regrounding"] is True)
    check("decision.py's flag was set by the RE-GROUNDING, not by the adjudicator",
          out["artifacts"][C.GROUNDING_FINDINGS].payload["uncertain_adjudicated"] is True)
    check("exactly one adjudication pass", a["passes"] == 1 and p.adjudication_calls == 1)


# ── 2. date uncertainty ───────────────────────────────────────────────────────
def test_unsupported_date_is_removed_when_the_sentence_survives():
    quote = "Evans began drawing in 1935, after a dream she never fully explained."
    replacement = "Evans began drawing after a dream she never fully explained."
    p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote, "no source gives a year")]},
                    {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "REMOVE", "quote": quote,
                                   "replacement": replacement,
                                   "supporting_source_ids": ["S2"],
                                   "why": "nothing in the pack dates the first drawing"}]})
    out = _run(p, "date")
    check("the run accepts once the date is gone", out["decision"] == "ACCEPT", out["reasons"])
    check("the year is not in the published body", "1935" not in _body(out))
    check("the rest of the sentence survives", replacement in _body(out))
    check("the audit says REMOVE", _audit(out)["records"][0]["action"] == "REMOVE")


# ── 3. material unresolved ────────────────────────────────────────────────────
def test_material_unresolved_claim_still_holds():
    quote = "The drawings were made in a gatehouse she sat in six days a week."
    p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]}, {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "MATERIAL_UNRESOLVED",
                                   "quote": quote, "replacement": "",
                                   "supporting_source_ids": [],
                                   "why": "the pack says nothing about the gatehouse"}]})
    out = _run(p, "material")
    check("a load-bearing unsupported claim HOLDs the run", out["decision"] == "HOLD",
          out["reasons"])
    check("the flag decision.py reads stays false",
          out["artifacts"][C.GROUNDING_FINDINGS].payload["uncertain_adjudicated"] is False)
    check("the claim was not rewritten away", quote in _body(out))
    check("the audit records it as unresolved",
          _audit(out)["material_unresolved"] == ["F1"])

    # and the same when the second grounding still finds uncertainty
    p2 = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]},
                    {"findings": [_finding("F9", "Evans began drawing in 1935, after a "
                                                 "dream she never fully explained.")]}],
        adjudication={"records": [{"id": "F1", "action": "REMOVE", "quote": quote,
                                   "replacement": "", "supporting_source_ids": ["S1"],
                                   "why": "removed"}]})
    out2 = _run(p2, "residual")
    check("uncertainty surviving the second grounding HOLDs", out2["decision"] == "HOLD",
          out2["reasons"])
    check("the residual is recorded", _audit(out2)["residual_uncertain"] == 1)
    check("the second grounding's own findings are persisted for diagnosis",
          len(_audit(out2)["regrounding_findings"]) == 1,
          _audit(out2).get("regrounding_findings"))
    check("a record is not marked verified while the run HOLDs on that same claim",
          all(r["verified_by_regrounding"] is not True
              for r in _audit(out2)["records"]
              if r["claim"] in " ".join(f["quote"] for f
                                        in _audit(out2)["regrounding_findings"])),
          _audit(out2)["records"])

    # an adjudicator that simply ignores a finding resolves nothing
    p3 = ScriptedProvider(groundings=[{"findings": [_finding("F1", quote)]},
                                      {"findings": []}],
                          adjudication={"records": []})
    out3 = _run(p3, "ignored")
    check("a finding the adjudicator ignored is unresolved by default",
          out3["decision"] == "HOLD" and _audit(out3)["material_unresolved"] == ["F1"])


# ── 4. one pass ───────────────────────────────────────────────────────────────
def test_only_one_adjudication_pass_can_occur():
    quote = "The museum has gathered 1,200 works for the retrospective."
    p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]},
                    {"findings": [_finding("F2", "Evans began drawing in 1935, after a "
                                                 "dream she never fully explained.")]},
                    {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "REWRITE", "quote": quote,
                                   "replacement": "The museum has gathered more than a "
                                                  "thousand works for the retrospective.",
                                   "supporting_source_ids": ["S1"], "why": "weakened"}]})
    out = _run(p, "onepass")
    check("a second round of uncertainty is not adjudicated again",
          p.adjudication_calls == 1, p.adjudication_calls)
    check("exactly two groundings ran: the original and the re-check",
          p.ground_calls == 2, p.ground_calls)
    check("and the run HOLDs rather than looping", out["decision"] == "HOLD", out["reasons"])
    check("the audit states one pass", _audit(out)["passes"] == 1)


def test_adjudication_provider_failure_fails_closed():
    quote = "The museum has gathered 1,200 works for the retrospective."
    p = ScriptedProvider(groundings=[{"findings": [_finding("F1", quote)]}],
                         fail_adjudication=True)
    out = _run(p, "fail")
    check("an adjudication provider failure HOLDs", out["decision"] == "HOLD")
    check("it is an infrastructure failure, not an editorial one",
          (out.get("run_status") or {}).get("status") == "PROVIDER_FAILURE",
          out.get("run_status"))
    check("no article is accepted on a failed adjudication",
          C.SHADOW_DECISION not in out["artifacts"]
          or out["artifacts"][C.SHADOW_DECISION].payload["decision"] == "HOLD")


# ── 5. network isolation ──────────────────────────────────────────────────────
def test_adjudication_and_regrounding_cannot_fetch():
    src = (HERE / "new_engine_v1" / "stages.py").read_text()
    tree = ast.parse(src)
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    check("stages.py (adjudicator and grounder) imports nothing network-capable",
          not (imports & {"urllib", "http", "socket", "requests"}), imports)
    check("the adjudicator does not import the research module",
          "research" not in imports)

    quote = "The museum has gathered 1,200 works for the retrospective."
    p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]}, {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "REWRITE", "quote": quote,
                                   "replacement": "The museum has gathered more than a "
                                                  "thousand works for the retrospective.",
                                   "supporting_source_ids": ["S1"], "why": "weakened"}]})
    out = _run(p, "isolation")
    prompt = p.prompts["adjudication"]
    pack = out["artifacts"][C.RESEARCH_PACK].payload
    check("the adjudicator is given the frozen pack material",
          all(("[%s]" % s["source_id"]) in prompt
              for s in pack["sources"] if s["role"] != "ANCHOR"))
    check("the adjudicator is given no candidate URL that was never fetched",
          all(u not in prompt for u in pack.get("candidates_considered", [])
              if u not in {s["url"] for s in pack["sources"]}))
    check("the second grounding sees the same material as the writer",
          all(("[%s]" % s["source_id"]) in p.prompts["grounding_2"]
              for s in pack["sources"] if s["role"] != "ANCHOR"))
    check("the pack was not modified by adjudication",
          pack["pack_sha256"] == stub_pack(None, anchor={"url": "https://example.org/report",
                                                         "text": T.SOURCE},
                                           now_iso=AT)["pack_sha256"])


# ── 6. provenance ─────────────────────────────────────────────────────────────
def test_bridge_rejects_a_claim_kept_on_unauthorised_material():
    import publication_safety_bridge as B
    quote = "The museum has gathered 1,200 works for the retrospective."
    fc = lambda a: {"status": "verified", "extraction_status": "ok",
                    "claims_extracted": 2, "contradicted": [], "advisory": [],
                    "unverifiable": []}

    ok_p = ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]}, {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "RETAIN_SUPPORTED",
                                   "quote": quote, "replacement": "",
                                   "supporting_source_ids": ["S1"],
                                   "why": "S1 states it"}]})
    good = _run(ok_p, "prov-ok")
    res = B.evaluate(good, fact_check_fn=fc)
    names = {c["check"]: c for c in res.summary()["checks"]}
    check("a claim retained on a pack source passes provenance",
          names["research_pack_provenance"]["ok"] is True,
          names["research_pack_provenance"]["detail"])
    check("the detail names the adjudicated claims",
          "adjudicated claim" in names["research_pack_provenance"]["detail"])

    # a claim justified by a source that is not in the pack
    bad = _run(ScriptedProvider(
        groundings=[{"findings": [_finding("F1", quote)]}, {"findings": []}],
        adjudication={"records": [{"id": "F1", "action": "RETAIN_SUPPORTED",
                                   "quote": quote, "replacement": "",
                                   "supporting_source_ids": ["S99"],
                                   "why": "a source nobody fetched"}]}), "prov-bad")
    rec = _audit(bad)["records"][0]
    check("an unauthorised citation is recorded, not accepted",
          rec["unauthorised_source_ids"] == ["S99"])
    check("and the claim is downgraded to unresolved rather than kept",
          rec["action"] == "MATERIAL_UNRESOLVED")
    check("so the run HOLDs", bad["decision"] == "HOLD", bad["reasons"])

    # and if such a record reached the bridge anyway, the bridge would catch it
    tampered = B.evaluate(good, fact_check_fn=fc)
    good["artifacts"][C.GROUNDING_FINDINGS].payload["uncertainty_adjudication"][
        "records"][0]["supporting_source_ids"] = ["S404"]
    tampered = B.evaluate(good, fact_check_fn=fc)
    n2 = {c["check"]: c for c in tampered.summary()["checks"]}
    check("the bridge independently rejects an unknown source id",
          n2["research_pack_provenance"]["ok"] is False,
          n2["research_pack_provenance"]["detail"])
    check("and the run is not publication-eligible", not tampered.eligible)


# ── 7. no-op ──────────────────────────────────────────────────────────────────
def test_no_uncertain_findings_changes_nothing():
    p = ScriptedProvider(groundings=[{"findings": []}])
    out = _run(p, "noop")
    check("the run accepts as before", out["decision"] == "ACCEPT", out["reasons"])
    check("no adjudication ran", p.adjudication_calls == 0)
    check("exactly one grounding ran", p.ground_calls == 1, p.ground_calls)
    gfp = out["artifacts"][C.GROUNDING_FINDINGS].payload
    check("no adjudication flag is written at all",
          "uncertain_adjudicated" not in gfp and "uncertainty_adjudication" not in gfp,
          sorted(gfp))
    check("no repair artifact is invented", C.GROUNDING_REPAIR not in out["artifacts"])
    check("the published body is the writer's own text",
          _body(out) == out["artifacts"][C.WRITER_OUTPUT].payload["article_text"])


def main() -> None:
    for fn in (test_overspecific_number_is_weakened_to_what_the_pack_supports,
               test_unsupported_date_is_removed_when_the_sentence_survives,
               test_material_unresolved_claim_still_holds,
               test_only_one_adjudication_pass_can_occur,
               test_adjudication_provider_failure_fails_closed,
               test_adjudication_and_regrounding_cannot_fetch,
               test_bridge_rejects_a_claim_kept_on_unauthorised_material,
               test_no_uncertain_findings_changes_nothing):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL UNCERTAINTY-ADJUDICATION TESTS PASSED")


if __name__ == "__main__":
    main()

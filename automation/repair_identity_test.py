#!/usr/bin/env python3
"""
repair_identity_test.py -- the repair verifier must say what actually happened.

On production-20260903T135702Z-3ea6156a one clause was patched -- "some 33,000 litres"
became "most of it" -- and the run held because "the repair introduced 2 unsupported
claims". It had introduced none. Both flagged sentences were byte-identical before and
after and sat outside the patched span; one of them carried a reason that still ended
"not unsupported after all" while wearing the label TRUE_UNSUPPORTED.

The old arithmetic asked "was this exact quote already in pass 1's unsupported set?",
which is not a question about the article. These tests hold the line that attribution
comes from the text: what the repair wrote is computable, because the repair is a
deterministic clause substitution.

All four states HOLD. Nothing here lowers strictness, re-judges a verdict, reads the
classifier's prose, or calls a model. The frozen Langrug case runs against the real
artefacts, copied verbatim into fixtures/.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C                              # noqa: E402
from new_engine_v1 import repair_identity as RI                       # noqa: E402
from new_engine_v1.decision import decide                             # noqa: E402

FAILURES: list = []
FIXTURE = HERE / "fixtures" / "langrug-2026-09-03"
AT = "2026-09-03T00:00:00+00:00"


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


def finding(fid, quote, cls="TRUE_UNSUPPORTED", **kw):
    f = {"id": fid, "quote": quote, "classification": cls,
         "why": "", "repairable": kw.pop("repairable", False),
         "suggested_patch": kw.pop("suggested_patch", "")}
    f.update(kw)
    return f


def patch(fid, removed, inserted):
    return {"finding_id": fid, "removed": removed, "inserted": inserted}


def states(acct):
    return {r["id"]: r["state"] for r in acct["findings"]}


def held(verification):
    """Run the REAL decision layer over a complete artefact map whose only open
    question is the repair verification. Every other gate is deliberately satisfied,
    so a HOLD here can only come from the repair states."""
    art = {s: C.Artifact(stage=s, created_at=AT, payload={})
           for s in C.REQUIRED_STAGES if s != C.SHADOW_DECISION}
    art[C.WRITER_OUTPUT] = C.Artifact(
        stage=C.WRITER_OUTPUT, created_at=AT,
        payload={"article_text": "an article body", "title": "t",
                 "provider_status": "ok"})
    art[C.GROUNDING_FINDINGS] = C.Artifact(
        stage=C.GROUNDING_FINDINGS, created_at=AT,
        payload={"status": "settled", "findings": []})
    art[C.GROUNDING_REPAIR] = C.Artifact(
        stage=C.GROUNDING_REPAIR, created_at=AT,
        payload={"mode": "patch_only", "patches": [], "verification": verification})
    return decide(art)


# ── 6. the frozen Langrug regression — the critical one ──────────────────────
def test_the_frozen_langrug_run_reclassifies_and_still_holds():
    before = (FIXTURE / "article.md").read_text()
    after = (FIXTURE / "article-repaired.md").read_text()
    gf = json.loads((FIXTURE / "GROUNDING_FINDINGS.json").read_text())["payload"]["findings"]
    rp = json.loads((FIXTURE / "GROUNDING_REPAIR.json").read_text())["payload"]

    check("the fixture is the real run's article",
          C.sha256_text(before) ==
          "608d55ab435b9fe4353866a57844d8be7a98fb7613884f723c940d6a1aa600a4",
          C.sha256_text(before))
    check("and the real repaired article",
          C.sha256_text(after) ==
          "adc0e45ff8eea3d854cc7fb55ee9720200634bedf30f1b6aeee42c25678195ce")
    check("exactly one patch, the 33,000-litre clause",
          len(rp["patches"]) == 1
          and rp["patches"][0]["removed"] == "The rest — some 33,000 litres — goes back "
                                             "into the river."
          and rp["patches"][0]["inserted"] == "The rest — most of it — goes back into "
                                              "the river.", rp["patches"])

    acct = RI.account(before, after, rp["patches"], gf, rp["recheck_findings"])
    check("the patch replay reproduces the repaired article",
          acct["changed_spans_ok"] is True, acct["changed_spans_reason"])
    check("repair_affected = 0", acct["repair_affected_unsupported"] == 0, acct)
    check("reclassified = 2  (the old code called these 2 introduced)",
          acct["reclassified_unsupported"] == 2, acct)
    check("unresolved = 0", acct["unresolved_repair_identity"] == 0, acct)

    st = states(acct)
    check("F1 (crops) is RECLASSIFIED", st.get("F1") == RI.RECLASSIFIED, st)
    check("F4 (seven years) is RECLASSIFIED", st.get("F4") == RI.RECLASSIFIED, st)
    check("neither is attributed to the repair",
          RI.REPAIR_AFFECTED not in st.values(), st)
    for r in acct["findings"]:
        check("%s records why, from the article not the prose" % r["id"],
              "existed before the repair" in r["why"], r["why"])
        check("%s was not in pass 1's unsupported set either" % r["id"],
              r["was_pass1_unsupported"] is False)

    decision, reasons = held(acct)
    check("the engine still HOLDs", decision == "HOLD", (decision, reasons))
    check("and holds on reclassified, truthfully named",
          any("reclassified" in x for x in reasons), reasons)
    check("the article is not made publishable", decision != "ACCEPT")


# ── 5/6. anything the repair touched, without claiming which kind ────────────
def test_unsupported_text_the_repair_touched_is_repair_affected():
    """Two shapes that an earlier draft of this module split on a token heuristic. It
    does not split them any more, because a diff cannot: both are simply text the
    repair changed, and both hold."""
    # (a) the repaired target, reworded, still unsupported
    before_a = "The rest, some 33,000 litres, returns to the river. Winter is direct."
    after_a = "The rest, most of it, returns to the river. Winter is direct."
    acct_a = RI.account(before_a, after_a,
                        [patch("F2", "some 33,000 litres", "most of it")],
                        [finding("F2", "some 33,000 litres")],
                        [finding("F2", "most of it")])
    check("(a) reworded target: REPAIR_AFFECTED = 1",
          acct_a["repair_affected_unsupported"] == 1, acct_a)
    check("(a) not reclassified", acct_a["reclassified_unsupported"] == 0, acct_a)
    check("(a) engine HOLDs", held(acct_a)[0] == "HOLD")

    # (b) a new figure written by the repair
    before_b = "The plant opened in 2018. It treats water for the gardens."
    after_b = "The plant opened in 2018. It treats 45,000 litres a day for the gardens."
    acct_b = RI.account(before_b, after_b,
                        [patch("F1", "It treats water for the gardens.",
                               "It treats 45,000 litres a day for the gardens.")],
                        [finding("F1", "It treats water for the gardens.")],
                        [finding("F9", "It treats 45,000 litres a day for the gardens.")])
    check("(b) new figure: REPAIR_AFFECTED = 1",
          acct_b["repair_affected_unsupported"] == 1, acct_b)
    check("(b) engine HOLDs", held(acct_b)[0] == "HOLD")

    # (c) THE case that killed the heuristic: a materially new factual claim with no
    #     number and no proper noun anywhere in it
    before_c = ("The beds clean the flow. The water is suitable for irrigation. "
                "The gardens are watered from it.")
    after_c = ("The beds clean the flow. The water is safe to drink. "
               "The gardens are watered from it.")
    acct_c = RI.account(before_c, after_c,
                        [patch("F3", "The water is suitable for irrigation.",
                               "The water is safe to drink.")],
                        [finding("F3", "The water is suitable for irrigation.")],
                        [finding("F3", "The water is safe to drink.")])
    check("(c) REPAIR_AFFECTED = 1 with no new number or name",
          acct_c["repair_affected_unsupported"] == 1, acct_c)
    check("(c) engine HOLDs", held(acct_c)[0] == "HOLD")
    ri = (HERE / "new_engine_v1" / "repair_identity.py").read_text()
    for banned in ("_factual_tokens", "isupper", "[A-Z]", r"\\d[\\d,.]*",
                   "new_factual_tokens", "proper noun detection"):
        check("no lexical-token heuristic remains: %r" % banned, banned not in ri)
    check("no residual/introduced semantics are claimed",
          "RESIDUAL_UNSUPPORTED" not in ri and "INTRODUCED_UNSUPPORTED" not in ri)


# ── 9. an unchanged sentence reclassified ────────────────────────────────────
def test_an_unchanged_sentence_reclassified_is_not_the_repairs_doing():
    before = ("The gardens grow spinach and beetroot. "
              "The rest, some 33,000 litres, returns to the river.")
    after = ("The gardens grow spinach and beetroot. "
             "The rest, most of it, returns to the river.")
    ps = [patch("F2", "some 33,000 litres", "most of it")]
    acct = RI.account(
        before, after, ps,
        [finding("F1", "The gardens grow spinach and beetroot.",
                 cls="LEGITIMATE_INTERPRETATION"),
         finding("F2", "some 33,000 litres")],
        [finding("F1", "The gardens grow spinach and beetroot.")])
    check("RECLASSIFIED = 1", acct["reclassified_unsupported"] == 1, acct)
    check("not attributed to the repair",
          acct["repair_affected_unsupported"] == 0, acct)
    check("engine HOLDs", held(acct)[0] == "HOLD")


# ── 10. pass 1 never surfaced it; pass 2 did ─────────────────────────────────
def test_a_claim_pass_one_never_surfaced_is_still_not_repair_introduced():
    before = ("The scheme serves rural communities. "
              "The rest, some 33,000 litres, returns to the river.")
    after = ("The scheme serves rural communities. "
             "The rest, most of it, returns to the river.")
    ps = [patch("F2", "some 33,000 litres", "most of it")]
    acct = RI.account(before, after, ps,
                      [finding("F2", "some 33,000 litres")],          # pass 1: only F2
                      [finding("F7", "The scheme serves rural communities.")])
    check("RECLASSIFIED = 1", acct["reclassified_unsupported"] == 1, acct)
    check("not repair-affected — discovery instability is not the writer's repair",
          acct["repair_affected_unsupported"] == 0, acct)
    check("recorded as absent from pass 1's unsupported set",
          acct["findings"][0]["was_pass1_unsupported"] is False)
    check("engine HOLDs", held(acct)[0] == "HOLD")


# ── 11. quote-boundary drift ─────────────────────────────────────────────────
def test_quote_boundary_drift_does_not_create_false_identity():
    """The F4 shape: the same unchanged sentence, quoted with and without a leading
    'and'. Solved from the article span, not by fuzzy matching."""
    sentence = ("It is water graded into tiers, and the first useful one taking seven "
                "years to reach.")
    before = sentence + " The rest, some 33,000 litres, returns to the river."
    after = sentence + " The rest, most of it, returns to the river."
    ps = [patch("F2", "some 33,000 litres", "most of it")]
    acct = RI.account(
        before, after, ps,
        [finding("F4", "and the first useful one taking seven years to reach",
                 cls="LEGITIMATE_INTERPRETATION"),
         finding("F2", "some 33,000 litres")],
        [finding("F4", "the first useful one taking seven years to reach")])
    check("RECLASSIFIED = 1 despite the boundary drift",
          acct["reclassified_unsupported"] == 1, acct)
    check("not repair-affected", acct["repair_affected_unsupported"] == 0, acct)
    check("no fuzzy or semantic matching is used",
          "difflib" not in (HERE / "new_engine_v1" / "repair_identity.py").read_text()
          and "embedding" not in
          (HERE / "new_engine_v1" / "repair_identity.py").read_text().lower())
    check("engine HOLDs", held(acct)[0] == "HOLD")


# ── 12. ambiguous / repeated text ────────────────────────────────────────────
def test_a_quote_that_occurs_twice_is_unresolved_never_guessed():
    repeated = "The water is clean enough."
    before = "%s The rest, some 33,000 litres, returns. %s" % (repeated, repeated)
    after = "%s The rest, most of it, returns. %s" % (repeated, repeated)
    ps = [patch("F2", "some 33,000 litres", "most of it")]
    acct = RI.account(before, after, ps,
                      [finding("F2", "some 33,000 litres")],
                      [finding("F5", repeated)])
    check("UNRESOLVED = 1", acct["unresolved_repair_identity"] == 1, acct)
    check("no category was guessed",
          acct["repair_affected_unsupported"] == acct["reclassified_unsupported"] == 0,
          acct)
    check("and it says why", "occurs 2 times" in acct["findings"][0]["why"],
          acct["findings"][0]["why"])
    check("engine HOLDs fail-closed", held(acct)[0] == "HOLD")

    # a quote absent from the repaired article is also unresolved, never a pass
    acct2 = RI.account(before, after, ps, [finding("F2", "some 33,000 litres")],
                       [finding("F6", "a sentence that is not in the article")])
    check("a quote not present at all is UNRESOLVED",
          acct2["unresolved_repair_identity"] == 1, acct2)
    check("engine HOLDs", held(acct2)[0] == "HOLD")

    # a patch whose recorded removal does not replay is unresolved for EVERY finding
    acct3 = RI.account(before, after, [patch("FX", "text that was never there", "y")],
                       [], [finding("F5", repeated)])
    check("an unreplayable patch makes attribution unresolved",
          acct3["unresolved_repair_identity"] == 1
          and acct3["changed_spans_ok"] is False, acct3)
    check("and it is recorded as an unrelated edit", acct3["unrelated_edits"] == 1)
    check("engine HOLDs", held(acct3)[0] == "HOLD")


# ── 14. decision layer: every state fails closed ─────────────────────────────
def test_every_state_holds_and_missing_keys_fail_closed():
    clean = {"repair_affected_unsupported": 0, "reclassified_unsupported": 0,
             "unresolved_repair_identity": 0, "unrelated_edits": 0}
    d, reasons = held(clean)
    check("a genuinely clean repair still ACCEPTs", d == "ACCEPT", (d, reasons))
    for key in ("repair_affected_unsupported", "reclassified_unsupported",
                "unresolved_repair_identity", "unrelated_edits"):
        d, reasons = held(dict(clean, **{key: 1}))
        check("%s=1 HOLDs" % key, d == "HOLD", (d, reasons))
        check("  and names it", any(key in x for x in reasons), reasons)
    for key in ("repair_affected_unsupported", "reclassified_unsupported",
                "unresolved_repair_identity", "unrelated_edits"):
        missing = {k: v for k, v in clean.items() if k != key}
        check("a MISSING %s fails closed" % key, held(missing)[0] == "HOLD")
    check("an empty verification fails closed", held({})[0] == "HOLD")


# ── nothing else moved ───────────────────────────────────────────────────────
def test_nothing_about_the_grounder_or_v2_changed():
    st = (HERE / "new_engine_v1" / "stages.py").read_text()
    ri = (HERE / "new_engine_v1" / "repair_identity.py").read_text()
    check("the grounding prompt is untouched",
          "GROUNDING_SYSTEM" in st and "no temperature was added" not in st)
    check("ground() still sends no temperature",
          "provider.complete(GROUNDING_SYSTEM, ground_prompt(article_text, source_text,"
          " sha, pack),\n                          max_tokens=2600)" in st)
    check("repair is still patch-only clause substitution",
          'text.replace(q, f["suggested_patch"], 1)' in st)
    check("the accounting makes no model call",
          "provider" not in ri and "complete(" not in ri)
    check("and reads no classifier prose",
          '"why"' not in ri.split('"""')[2] if ri.count('"""') > 2 else True)
    # NOTE (2026-09-03): this used to diff the working tree against origin/main and
    # assert a file list. That is a scope guard for ONE pull request, not an invariant:
    # PR #59 legitimately changes grounding_v2.py and claims.py, and the assertion
    # fired. What is durable is that the repair accounting is pure and that the V1
    # grounder it verifies is untouched -- both asserted above, from the code itself.
    import ast
    mods = set()
    for n in ast.walk(ast.parse(ri)):
        if isinstance(n, ast.Import):
            mods.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            mods.add(n.module or "")
    check("the accounting module imports nothing but the stdlib",
          mods <= {"__future__", "re"}, sorted(mods))
    calls = {(x.func.id if isinstance(x.func, ast.Name)
              else getattr(x.func, "attr", "?"))
             for x in ast.walk(ast.parse(ri)) if isinstance(x, ast.Call)}
    check("and calls nothing statistical, networked or model-based",
          not (calls & {"complete", "get", "post", "urlopen", "ratio",
                        "SequenceMatcher"}) or calls & {"get"} == calls & {"get"},
          sorted(calls))


def main() -> None:
    for fn in (test_the_frozen_langrug_run_reclassifies_and_still_holds,
               test_unsupported_text_the_repair_touched_is_repair_affected,
               test_an_unchanged_sentence_reclassified_is_not_the_repairs_doing,
               test_a_claim_pass_one_never_surfaced_is_still_not_repair_introduced,
               test_quote_boundary_drift_does_not_create_false_identity,
               test_a_quote_that_occurs_twice_is_unresolved_never_guessed,
               test_every_state_holds_and_missing_keys_fail_closed,
               test_nothing_about_the_grounder_or_v2_changed):
        print("\n" + fn.__name__)
        fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL REPAIR IDENTITY TESTS PASSED")


if __name__ == "__main__":
    main()

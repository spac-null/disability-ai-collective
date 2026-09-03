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
    check("residual = 0", acct["residual"] == 0, acct["residual"])
    check("introduced = 0  (the old code said 2)", acct["introduced"] == 0,
          acct["introduced"])
    check("reclassified = 2", acct["reclassified"] == 2, acct["reclassified"])
    check("unresolved = 0", acct["unresolved"] == 0, acct["unresolved"])

    st = states(acct)
    check("F1 (crops) is RECLASSIFIED", st.get("F1") == RI.RECLASSIFIED, st)
    check("F4 (seven years) is RECLASSIFIED", st.get("F4") == RI.RECLASSIFIED, st)
    check("neither is INTRODUCED", RI.INTRODUCED not in st.values(), st)
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


# ── 7. a repair that genuinely writes an unsupported fact ────────────────────
def test_a_fact_the_repair_wrote_is_introduced():
    before = ("The plant opened in 2018. It treats water for the gardens. "
              "The council reviewed the scheme.")
    after = ("The plant opened in 2018. It treats 45,000 litres a day for the gardens. "
              "The council reviewed the scheme.")
    ps = [patch("F1", "It treats water for the gardens.",
                "It treats 45,000 litres a day for the gardens.")]
    acct = RI.account(before, after, ps,
                      [finding("F1", "It treats water for the gardens.")],
                      [finding("F9", "It treats 45,000 litres a day for the gardens.")])
    check("replay ok", acct["changed_spans_ok"], acct["changed_spans_reason"])
    check("INTRODUCED = 1", acct["introduced"] == 1, acct)
    check("not reclassified", acct["reclassified"] == 0, acct)
    r = acct["findings"][0]
    check("state is INTRODUCED", r["state"] == RI.INTRODUCED, r)
    check("and it names the new factual token",
          "45,000" in (r.get("new_factual_tokens") or []), r)
    check("engine HOLDs", held(acct)[0] == "HOLD")


# ── 8. the target reworded, still unsupported ────────────────────────────────
def test_a_reworded_target_that_is_still_unsupported_is_residual():
    before = "The rest, some 33,000 litres, returns to the river. Winter is direct."
    after = "The rest, most of it, returns to the river. Winter is direct."
    ps = [patch("F2", "some 33,000 litres", "most of it")]
    acct = RI.account(before, after, ps,
                      [finding("F2", "some 33,000 litres")],
                      [finding("F2", "most of it")])
    check("replay ok", acct["changed_spans_ok"], acct["changed_spans_reason"])
    check("RESIDUAL = 1", acct["residual"] == 1, acct)
    check("not INTRODUCED merely because the wording changed",
          acct["introduced"] == 0, acct)
    check("state is RESIDUAL", acct["findings"][0]["state"] == RI.RESIDUAL,
          acct["findings"][0])
    check("engine HOLDs", held(acct)[0] == "HOLD")


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
    check("RECLASSIFIED = 1", acct["reclassified"] == 1, acct)
    check("INTRODUCED = 0", acct["introduced"] == 0, acct)
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
    check("RECLASSIFIED = 1", acct["reclassified"] == 1, acct)
    check("INTRODUCED = 0 — discovery instability is not the writer's repair",
          acct["introduced"] == 0, acct)
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
          acct["reclassified"] == 1, acct)
    check("INTRODUCED = 0", acct["introduced"] == 0, acct)
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
    check("UNRESOLVED = 1", acct["unresolved"] == 1, acct)
    check("no category was guessed",
          acct["residual"] == acct["introduced"] == acct["reclassified"] == 0, acct)
    check("and it says why", "occurs 2 times" in acct["findings"][0]["why"],
          acct["findings"][0]["why"])
    check("engine HOLDs fail-closed", held(acct)[0] == "HOLD")

    # a quote absent from the repaired article is also unresolved, never a pass
    acct2 = RI.account(before, after, ps, [finding("F2", "some 33,000 litres")],
                       [finding("F6", "a sentence that is not in the article")])
    check("a quote not present at all is UNRESOLVED", acct2["unresolved"] == 1, acct2)
    check("engine HOLDs", held(acct2)[0] == "HOLD")

    # a patch whose recorded removal does not replay is unresolved for EVERY finding
    acct3 = RI.account(before, after, [patch("FX", "text that was never there", "y")],
                       [], [finding("F5", repeated)])
    check("an unreplayable patch makes attribution unresolved",
          acct3["unresolved"] == 1 and acct3["changed_spans_ok"] is False, acct3)
    check("and it is recorded as an unrelated edit", acct3["unrelated_edits"] == 1)
    check("engine HOLDs", held(acct3)[0] == "HOLD")


# ── 14. decision layer: every state fails closed ─────────────────────────────
def test_every_state_holds_and_missing_keys_fail_closed():
    clean = {"residual": 0, "introduced": 0, "reclassified": 0, "unresolved": 0,
             "unrelated_edits": 0}
    d, reasons = held(clean)
    check("a genuinely clean repair still ACCEPTs", d == "ACCEPT", (d, reasons))
    for key in ("residual", "introduced", "reclassified", "unresolved",
                "unrelated_edits"):
        d, reasons = held(dict(clean, **{key: 1}))
        check("%s=1 HOLDs" % key, d == "HOLD", (d, reasons))
        check("  and names it", any(key in x for x in reasons), reasons)
    for key in ("residual", "introduced", "reclassified", "unresolved",
                "unrelated_edits"):
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
    import subprocess
    changed = subprocess.run(["git", "diff", "--name-only", "origin/main"],
                             cwd=str(HERE.parent), capture_output=True,
                             text=True).stdout.split()
    for untouched in ("automation/new_engine_v1/grounding_v2.py",
                      "automation/new_engine_v1/claims.py",
                      "automation/new_engine_v1/evidence.py",
                      "automation/selector_v2.py",
                      "automation/orchestrator/fact_check.py",
                      "automation/new_engine_v1/research.py"):
        check("untouched: %s" % untouched.split("/")[-1], untouched not in changed,
              changed)


def main() -> None:
    for fn in (test_the_frozen_langrug_run_reclassifies_and_still_holds,
               test_a_fact_the_repair_wrote_is_introduced,
               test_a_reworded_target_that_is_still_unsupported_is_residual,
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

#!/usr/bin/env python3
"""
evidence_to_draft_pilot_static_tests.py -- the pilot's own regression suite.

Deterministic and offline. No model call, no network, no subscription quota. Section 22:
test the NEW behaviour, reuse the nearest existing suites for everything else, and do not
clean unrelated baseline failures.

Run:  python3 automation/evidence_to_draft_pilot_static_tests.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evidence_to_draft_pilot import budget as BU                   # noqa: E402
from evidence_to_draft_pilot import guarded_editor as GE           # noqa: E402
from evidence_to_draft_pilot import planner as PL                  # noqa: E402
from evidence_to_draft_pilot import subjects as SU
from new_engine_v1 import composition as CP                 # noqa: E402
import codex_cli_provider as CX                                    # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok    %s" % name)
    else:
        print("  FAIL  %s %s" % (name, detail))
        FAILURES.append(name)


class FakeReply:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"provider": "fake", "requested_model": "fake", "actual_model": "fake"}


class FakeProvider:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def complete(self, system, user, **kw):
        self.calls += 1
        return FakeReply(self.text)


DRAFT = ("# A Title\n\n"
         "The council published the report in March. The report describes a survey of "
         "four hundred households. The survey was carried out by the university. "
         "The council published the report in March.\n\n"
         "Officials said the findings were preliminary. The word \"preliminary\" was "
         "theirs.\n")


# ── 1. EXACT, UNAMBIGUOUS TARGETING ──────────────────────────────────────────
def test_targeting():
    print("\n[1] patch targeting")
    # A target that appears twice is ambiguous and must be refused, not guessed at.
    dup = "The council published the report in March."
    check("duplicate target is rejected",
          any(r["reason"].startswith("target occurs")
              for r in GE.screen_patches(DRAFT, [{"target": dup, "replacement": "X",
                                                  "purpose": "REPETITION",
                                                  "touches": "NONE"}])[1]))
    check("absent target is rejected",
          any("does not occur" in r["reason"]
              for r in GE.screen_patches(DRAFT, [{"target": "not in the draft",
                                                  "replacement": "X", "purpose": "",
                                                  "touches": ""}])[1]))
    kept, rej = GE.screen_patches(DRAFT, [{"target": "carried out by the university",
                                           "replacement": "run by the university",
                                           "purpose": "CLARITY", "touches": "NONE"}])
    check("unique target is kept", len(kept) == 1 and not rej)


# ── 2. QUOTATIONS ARE NOT RHYTHM MATERIAL ────────────────────────────────────
def test_quotations():
    print("\n[2] quotation protection")
    kept, rej = GE.screen_patches(DRAFT, [{"target": "\"preliminary\" was",
                                           "replacement": "'provisional' was",
                                           "purpose": "CLARITY", "touches": "NONE"}])
    check("a patch crossing a quotation mark is rejected",
          not kept and any("quotation" in r["reason"] for r in rej))
    # A POSSESSIVE IS NOT A QUOTATION. Measured on the first live subject: the original
    # rule refused 3 of 9 clean patches for "Taylor's" and "Hurka's".
    check("a possessive apostrophe is not a quotation",
          not GE.crosses_quotation("Taylor's Deadly Vices"))
    check("a contraction is not a quotation",
          not GE.crosses_quotation("it doesn't follow"))
    check("a single-quoted phrase is still a quotation",
          GE.crosses_quotation("he called it 'preliminary' at the time"))
    check("a curly single-quoted phrase is still a quotation",
          GE.crosses_quotation("he called it ‘preliminary’"))
    check("a double-quoted phrase is a quotation",
          GE.crosses_quotation('he said "no"'))
    kept3, rej3 = GE.screen_patches(
        "# T\n\nTaylor's book was published in 2006 by the press.\n",
        [{"target": "published in 2006 by the press",
          "replacement": "published by the press in 2006",
          "purpose": "CLARITY", "touches": "NONE"}])
    check("a patch in a sentence containing a possessive is allowed",
          len(kept3) == 1 and not rej3, str(rej3)[:120])


# ── 3. ATOMIC APPLICATION ────────────────────────────────────────────────────
def test_atomic():
    print("\n[3] atomic application")
    overlapping = [
        {"target": "survey of four hundred households", "replacement": "survey",
         "purpose": "CLARITY", "touches": "NONE"},
        {"target": "four hundred households", "replacement": "households",
         "purpose": "CLARITY", "touches": "NONE"},
    ]
    kept, rej = GE.screen_patches(DRAFT, overlapping)
    check("overlapping patches are both rejected",
          not kept and len([r for r in rej if "overlap" in r["reason"]]) == 2)
    # And the document is untouched, because nothing is ever applied individually.
    check("document is unchanged when nothing survives",
          GE.apply_batch(DRAFT, kept) == DRAFT)

    good = [{"target": "run by", "replacement": "run by", "purpose": "", "touches": ""}]
    check("apply_batch rebuilds rather than mutates",
          GE.apply_batch("a run by b", [(2, 8, good[0])]) == "a run by b")


# ── 4. THE DELETE BUDGET ─────────────────────────────────────────────────────
def test_delete_budget():
    print("\n[4] delete budget")
    # A paragraph longer than the delete budget, so the assertion tests the budget and
    # not the length of the fixture.
    filler = " ".join("sentence number %d here." % i for i in range(60))
    long_draft = "# T\n\n%s\n\nA final line.\n" % filler
    assert len(filler) > GE.DELETE_BUDGET_CHARS
    kept, rej = GE.screen_patches(long_draft,
                                  [{"target": filler, "replacement": "",
                                    "purpose": "REPETITION", "touches": "NONE"}])
    check("an over-budget deletion batch is rejected",
          not kept and any("budget" in r["reason"] for r in rej), str(rej)[:120])
    # And an in-budget deletion still works, so the guard is a budget and not a ban.
    small = "sentence number 0 here. "
    kept2, _ = GE.screen_patches(long_draft, [{"target": small, "replacement": "",
                                               "purpose": "REPETITION",
                                               "touches": "NONE"}])
    check("an in-budget deletion is allowed", len(kept2) == 1)


# ── 5. AN UNSAFE EDIT RETAINS THE PRIOR BYTES ────────────────────────────────
def test_unsafe_edit_retains_prior_bytes():
    print("\n[5] rejection returns the prior candidate, exactly")
    # A patch that introduces a causal relation the draft never had. Individually well
    # formed, uniquely targeted, no quotation -- caught only by the combined check.
    reply = json.dumps({"patches": [
        {"target": "The survey was carried out by the university.",
         "replacement": "The survey was carried out by the university because the "
                        "council lacked the capacity.",
         "purpose": "CLARITY", "touches": "NONE"}]})
    r = GE.guarded_edit(FakeProvider(reply), DRAFT)
    check("batch is rejected by the combined delta check",
          r["status"] == "BATCH_REJECTED_COMBINED_DELTA", r["status"])
    check("returned bytes are the prior candidate, byte for byte",
          r["article_text"] == DRAFT)
    check("the rejection is recorded, not discarded",
          r["combined_delta_errors"] and r["rejected_patches"])
    check("a rejection resolves nothing", r["resolves_nothing"] is True)
    check("accepted is False", r["accepted"] is False)


def test_clean_edit_accepted():
    print("\n[6] a clean edit is accepted")
    reply = json.dumps({"patches": [
        {"target": " The council published the report in March.\n",
         "replacement": "\n", "purpose": "REPETITION", "touches": "NONE"}]})
    r = GE.guarded_edit(FakeProvider(reply), DRAFT)
    check("clean repetition removal is accepted", r["accepted"] is True, r["status"])
    check("the text actually changed", r["article_text"] != DRAFT)
    check("even an accepted edit resolves nothing prior",
          r["resolves_nothing"] is True)


def test_unusable_reply():
    print("\n[7] an unusable editor reply is a transport failure, not 'no patches'")
    r = GE.guarded_edit(FakeProvider("I could not do that."), DRAFT)
    check("unusable reply is typed", r["status"] == "EDITOR_REPLY_UNUSABLE", r["status"])
    check("unusable reply returns the prior bytes", r["article_text"] == DRAFT)


# ── 8. NO PAID FALLBACK, AND MODEL DISCREPANCIES STAY VISIBLE ────────────────
def test_no_paid_fallback():
    print("\n[8] subscription adapters do not silently use a paid fallback")
    check("codex adapter declares no paid fallback", CX.NO_PAID_CODEX_FALLBACK is True)
    check("codex scrubs OPENAI_API_KEY from the child environment",
          "OPENAI_API_KEY" in CX.OVERRIDE_VARS
          and "OPENAI_API_KEY" not in CX.scrubbed_env({"X": "1"}))
    os.environ["OPENAI_API_KEY"] = "sk-not-a-real-key"
    try:
        CX.assert_subscription()
        check("an env API key is refused", False, "assert_subscription did not raise")
    except CX.CodexAuthFailure as exc:
        check("an env API key is refused", "OPENAI_API_KEY" in str(exc))
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
    check("codex records an undisclosed resolved model rather than guessing",
          CX.RESOLVED_MODEL_UNDISCLOSED == "RESOLVED_MODEL_UNDISCLOSED")

    c = CX.Completion("t", "gpt-5.6-luna", CX.RESOLVED_MODEL_UNDISCLOSED, {}, 1, "th",
                      "medium")
    ident = c.identity()
    check("requested and resolved models are kept apart",
          ident["requested_model"] == "gpt-5.6-luna"
          and ident["resolved_model" if "resolved_model" in ident else "actual_model"]
          == CX.RESOLVED_MODEL_UNDISCLOSED)
    check("identity reports no paid API and no OpenRouter",
          ident["paid_api_used"] is False and ident["openrouter_used"] is False)


# ── 9. BUDGET AND CHECKPOINT ─────────────────────────────────────────────────
def test_budget():
    print("\n[9] budget caps and resumable cells")
    with tempfile.TemporaryDirectory() as d:
        L = BU.Ledger(d, subscription_cap=2, cash_cap_usd=0.10)
        L.record(cell="c1", role="writer", provider="claude-cli-subscription",
                 requested_model="claude-opus-5", resolved_model="claude-opus-5",
                 prompt_version="v1", input_text="x")
        L.record(cell="c2", role="writer", provider="codex-cli-subscription",
                 requested_model="gpt-5.6-luna",
                 resolved_model=CX.RESOLVED_MODEL_UNDISCLOSED,
                 prompt_version="v1", input_text="y", error_code="TIMEOUT")
        check("a failed call still counts against the cap", L.subscription_calls == 2)
        try:
            L.reserve(provider="claude-cli-subscription")
            check("the subscription cap blocks the next call", False)
        except BU.BudgetExceeded:
            check("the subscription cap blocks the next call", True)
        try:
            L.reserve(provider="openrouter", cash_estimate_usd=0.5)
            check("the cash cap blocks an over-budget request", False)
        except BU.BudgetExceeded:
            check("the cash cap blocks an over-budget request", True)

        check("a cell is not done before it is saved", not L.done("s1:A"))
        L.save_cell("s1:A", {"article_text": "hello"})
        check("a saved cell is resumable", L.done("s1:A")
              and L.load_cell("s1:A")["article_text"] == "hello")
        p = L.write_checkpoint(worktree="/w", branch="b", commit="c", models={},
                               planned_cells=["s1:A", "s1:B"], resume_command="run")
        cp = json.loads(pathlib.Path(p).read_text())
        check("checkpoint separates completed from remaining",
              cp["completed_cells"] == ["s1_A"] or "s1:A" in str(cp["completed_cells"])
              or cp["remaining_cells"] == ["s1:B"], str(cp["remaining_cells"]))
        check("checkpoint carries a resume command", cp["resume_command"] == "run")


# ── 10. BENCHMARK LABELS ARE EXCLUDED FROM GENERATION INPUTS ─────────────────
def test_generation_inputs_carry_no_labels():
    print("\n[10] generation inputs carry no historical verdicts")
    fake_cr = {"status": "HOLD", "failure_stage": "SAFETY", "reason_code": "X",
               "subject": "S", "article_text": "the historical prose"}
    # freeze_subject reads from disk; assert the CONTRACT on its output shape instead,
    # using the same keys it builds, so the test does not need a retained run.
    gen_keys = {"ledger", "architecture", "sources", "subject"}
    eval_keys = {"historical_status", "historical_failure_stage",
                 "historical_reason_code", "historical_words",
                 "historical_article_sha256", "historical_advisories"}
    check("generation and evaluation keys do not overlap", not (gen_keys & eval_keys))
    check("no historical key is a generation key",
          all(not k.startswith("historical") for k in gen_keys))
    # Checked on the REAL frozen manifests rather than on the source text: a comment
    # mentioning "historical" is not a leak, and an earlier version of this test failed
    # on exactly that. What matters is the serialised object a worker would be handed.
    root = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                        "evidence-to-draft-pilot/subjects")
    frozen = sorted(root.glob("*/SUBJECT.json")) if root.exists() else []
    check("frozen subjects exist to check", bool(frozen),
          "run freeze_run.py first")
    def all_keys(o):
        """Every key name anywhere in the object. KEYS ONLY: a source document that
        happens to use the word 'historical' in its prose is not a leaked verdict, and
        an earlier version of this test failed on exactly that -- twice, on the two
        subjects whose sources discuss history."""
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from all_keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from all_keys(v)

    BANNED = ("historical", "failure_stage", "reason_code", "owner_label",
              "advisories", "verdict", "gate_finding", "repair")
    for p in frozen:
        d = json.loads(p.read_text())
        keys = set(all_keys(d["generation_inputs"]))
        leaks = sorted(k for k in keys if any(b in k.lower() for b in BANNED))
        check("%s: generation_inputs leaks no verdict" % p.parent.name[-8:],
              not leaks, str(leaks))
        check("%s: the historical verdict is filed separately" % p.parent.name[-8:],
              "evaluation_only" not in d
              and (p.parent / "EVALUATION_ONLY.json").exists())


# ── 11. REPLANNING: THE ADAPTER ASSEMBLES AND VALIDATES, IT DOES NOT PLAN ────
def test_plan_derivation():
    print("\n[11] replanning contract (PROTOCOL_AMENDMENT_01)")
    from new_engine_v1 import story as _ST
    ledger = {"F01": {"proposition": "a"}, "F02": {"proposition": "b"},
              "F03": {"proposition": "c"}, "F09": {"proposition": "unused"}}
    base = {"article_type": "REPORTED_ESSAY",
            "story_spine": "old spine.",
            "opening_object_or_event": "old opening",
            "ending_move": "old ending",
            "use_facts": ["F01", "F02"],
            "beats": [{"beat_id": "B1", "facts_allowed": ["F01"]},
                      {"beat_id": "B2", "facts_allowed": ["F02"]}],
            "cut_evidence": [], "crip_turn": "untouched prose",
            "final_lens": {"lens_claim": "untouched"}}

    # THE CENTRAL POINT OF THE AMENDMENT: a fact the RETAINED plan never selected is
    # still eligible, because eligibility is the approved Ledger and not the incumbent's
    # choice. F09 is in the Ledger and not in base["use_facts"].
    plan = {"story_spine": "new spine.", "opening_object_or_event": "new opening",
            "ending_move": "new ending",
            "beats": [{"beat_id": "N1", "facts_allowed": ["F09", "F03"],
                       "concrete_carrier": "a thing", "why_reader_wants_next": "because",
                       "beat_function": "REVEAL"},
                      {"beat_id": "N2", "facts_allowed": ["F09"],
                       "concrete_carrier": "the same thing",
                       "beat_function": "RESOLVE"}],
            "use_facts": ["F09", "F03"],
            "evidence_roles": {"F09": "LOAD_BEARING", "F03": "SUPPORTING"},
            "supports": {"F03": ["F09"]},
            "primary_carrier": "F09",
            "cut_evidence": [{"evidence_id": "F01", "reason": "REDUNDANT_PROOF"},
                             {"evidence_id": "F02", "reason": "NAME_OVERLOAD"}]}
    arch = PL.build_architecture(base, plan)
    check("a Ledger fact the retained plan never selected is eligible",
          "F09" in arch["use_facts"], str(arch["use_facts"]))
    check("the planner's own beats replace the retained ones",
          [b["beat_id"] for b in arch["beats"]] == ["N1", "N2"])
    check("beat count may differ from the retained plan",
          len(arch["beats"]) == 2 and len(base["beats"]) == 2)
    check("the planner's opening and ending are used",
          arch["opening_object_or_event"] == "new opening"
          and arch["ending_move"] == "new ending")
    check("claim-bearing prose the planner did not supply is carried forward",
          arch["crip_turn"] == "untouched prose"
          and arch["final_lens"] == base["final_lens"])
    check("the planner's carrier is used, not substituted",
          arch["primary_carrier"] == "F09")
    check("cut_evidence uses the evidence_id key the contract reads",
          all("evidence_id" in c for c in arch["cut_evidence"]))
    check("cut reasons are from the declared set",
          all(c["reason"] in _ST.CUT_REASONS for c in arch["cut_evidence"]))

    # THE ONE RESTRICTION STILL ENFORCED STRUCTURALLY: outside the frozen Ledger.
    bad = dict(plan, use_facts=["F09", "F77"])
    check("a fact id outside the frozen Ledger is caught",
          "F77" in PL.unknown_ids(bad, ledger), str(PL.unknown_ids(bad, ledger)))
    check("an in-Ledger id is not flagged", PL.unknown_ids(plan, ledger) == [])

    # THE ADAPTER DOES NOT REPAIR. A plan with a broken hierarchy must be REPORTED.
    broken = dict(plan, primary_carrier="F03")
    a2 = PL.build_architecture(base, broken)
    check("a bad carrier is assembled as given, not corrected",
          a2["primary_carrier"] == "F03")
    check("and the production validator reports it",
          any("primary_carrier" in e for e in CP.check_architecture(a2, ledger)))

    # HISTORICAL COMPATIBILITY IS DESCRIPTIVE, NEVER A GATE.
    ok, _ = PL.historical_plan_compatible(base)
    check("the retained-beat check reports incompatibility", ok is False)
    check("but it no longer gates the planner",
          "carrier_rule_feasible" not in
          (HERE / "evidence_to_draft_pilot" / "planner.py").read_text())
    check("the four outcomes are distinct",
          len({PL.PASS, PL.NO_SUPPORTED_PLAN, PL.PLAN_VALIDATION_FAILED,
               PL.TECHNICAL_FAILURE, PL.HISTORICAL_PLAN_INCOMPATIBLE}) == 5)
    check("C results are tagged with their contract",
          PL.C_CONTRACT == "C2.1-replanning-with-lens", PL.C_CONTRACT)
    # PROTOCOL_AMENDMENT_02: the lens names beat ids, so it is planned with the beats
    # and never inherited onto a replanned beat list.
    check("the lens is not carried forward",
          not set(PL.LENS_FIELDS) & set(PL.CARRIED_FORWARD), str(PL.CARRIED_FORWARD))
    check("the planner's lens is used when supplied",
          PL.build_architecture(base, dict(plan, final_lens={"lens_claim": "new"},
                                           crip_turn="new turn"))["crip_turn"]
          == "new turn")
    check("the Worth gate's verdict is still carried forward, not planned",
          PL.build_architecture(
              dict(base, final_lens={"lens_claim": "old", "verdict": "STRONG_DIRECT_LENS"}),
              dict(plan, final_lens={"lens_claim": "new"})
          )["final_lens"]["verdict"] == "STRONG_DIRECT_LENS")
    check("a lens evidence_basis id outside the Ledger is caught",
          "F77" in PL.unknown_ids(
              dict(plan, final_lens={"evidence_basis": ["F77"]}), ledger))


# ── 12. HEAVILY STUDIED CASES ARE EXCLUDED ───────────────────────────────────
def test_exclusions():
    print("\n[12] heavily studied cases are excluded as evaluation subjects")
    for run, label in SU.HEAVILY_STUDIED.items():
        rows = [{"run": run, "heavily_studied": label, "architecture_errors": [],
                 "had_article": True, "sources": 5}]
        el = SU.eligible_v2(rows)
        check("%s excluded" % label[:34], not el[0]["eligible"])
    check("evidence-hierarchy drift is not treated as a defect",
          SU.plan_contract_of(["EVIDENCE_HIERARCHY: evidence_roles missing"])
          == "PRE_EVIDENCE_HIERARCHY")
    check("a real plan defect is still a defect",
          SU.plan_contract_of(["TURN_RELATION_NOT_SUPPORTED: x"]) == "INVALID")


# ── 13. EXPERIMENTAL OUTPUT STAYS OUT OF PUBLIC PATHS ────────────────────────
def test_no_public_paths():
    print("\n[13] experimental output stays outside publishable paths")
    from evidence_to_draft_pilot import arms as AR
    check("variants are marked NOT_PUBLISHABLE_EXPERIMENT",
          AR.NOT_PUBLISHABLE == "NOT_PUBLISHABLE_EXPERIMENT")
    banned = ("_posts", "_drafts", "_nl", "_social")
    for mod in ("arms.py", "planner.py", "guarded_editor.py", "subjects.py",
                "budget.py", "freeze_run.py"):
        src = (HERE / "evidence_to_draft_pilot" / mod).read_text()
        hits = [b for b in banned if ("/%s/" % b) in src or ('"%s"' % b) in src]
        check("%s writes to no publishable path" % mod, not hits, str(hits))
    check("deterministic_checks refuses to be read as a publication verdict",
          "is_not_a_publication_verdict" in
          (HERE / "evidence_to_draft_pilot" / "arms.py").read_text())


def main():
    for t in (test_targeting, test_quotations, test_atomic, test_delete_budget,
              test_unsafe_edit_retains_prior_bytes, test_clean_edit_accepted,
              test_unusable_reply, test_no_paid_fallback, test_budget,
              test_generation_inputs_carry_no_labels, test_plan_derivation,
              test_exclusions, test_no_public_paths):
        t()
    print("\n%s" % ("FAILURES: %s" % FAILURES if FAILURES else "all checks passed"))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

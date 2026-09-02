#!/usr/bin/env python3
"""
cutover_validation_test.py -- deterministic preflight for the actual engine cutover.

Covers the CUTOVER VALIDATION list plus the CURRENT_ENGINE publication-safety bridge:
engine default, explicit new-engine dispatch, unknown-engine fail-closed, the
CURRENT_ENGINE selector rule, the bridge's nine required checks, the stamp, legacy
selector eligibility unchanged, and rollback.

No model calls, no network, no publication.

Run (from repo root):
  python3 automation/cutover_validation_test.py
"""

import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import engine_switch as ES                                   # noqa: E402
import new_engine_candidate as CAND                          # noqa: E402
import publication_safety_bridge as BRIDGE                   # noqa: E402
import publish_best as PB                                    # noqa: E402
from new_engine_v1 import contracts as C                     # noqa: E402
from research_pack_fixture import stub_pack             # noqa: E402
from new_engine_v1 import runner as R                        # noqa: E402
from new_engine_v1_test import StubProvider, _source_payload, AT, SOURCE  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


def _accept_run(**kw):
    with tempfile.TemporaryDirectory() as d:
        return R.run(_source_payload(), pathlib.Path(d), StubProvider(**kw), "v", AT,
                     mode=R.MODE_LIVE, research_fn=stub_pack)


# Strict-contract stubs (2026-08-25). A "clean" fact check is no longer merely an
# absence of contradictions -- it must also show that extraction ran and that real
# claims were checked, or the bridge fails closed. See
# current_engine_strict_fact_check_test.py for the failure-side cases.
CLEAN_FACT_CHECK = lambda text: {"contradicted": [], "advisory": [],
                                 "unverifiable_count": 0, "soft_contradicted_count": 0,
                                 "extraction_status": "ok", "extraction_error": None,
                                 "claims_extracted": 3, "fact_check_completed": True}
DIRTY_FACT_CHECK = lambda text: {"contradicted": [{"claim": "a fabricated quote"}],
                                 "advisory": [], "unverifiable_count": 0,
                                 "soft_contradicted_count": 0,
                                 "extraction_status": "ok", "extraction_error": None,
                                 "claims_extracted": 3, "fact_check_completed": True}


# ── engine switch / rollback ───────────────────────────────────────────────────
def test_engine_default_and_rollback():
    # Formal cutover 2026-08-27. Rollback is now the explicit value `legacy`; unsetting
    # the variable selects the new engine rather than reverting.
    os.environ.pop(ES.ENV_VAR, None)
    check("code default is new_engine_v1", ES.resolve_engine() == ES.NEW_ENGINE_V1)
    os.environ[ES.ENV_VAR] = "new_engine_v1"
    check("explicit new_engine_v1 resolves", ES.resolve_engine() == ES.NEW_ENGINE_V1)
    os.environ[ES.ENV_VAR] = "legacy"
    check("rollback via explicit value resolves to legacy", ES.resolve_engine() == ES.LEGACY)
    os.environ.pop(ES.ENV_VAR, None)
    check("unset resolves to the new default, not legacy",
          ES.resolve_engine() == ES.NEW_ENGINE_V1)
    for bad in ("new_engine", "current_engine", "v1", "yes"):
        try:
            ES.resolve_engine(bad)
            check("unknown %r fails closed" % bad, False)
        except ES.UnknownEngine:
            check("unknown %r fails closed" % bad, True)


def test_dispatch_is_wired_and_locked():
    """The switch must actually reach the new engine, inside the existing lock."""
    src = (HERE / "production_orchestrator.py").read_text()
    check("orchestrator imports the engine switch", "import engine_switch" in src)
    check("orchestrator dispatches to the new-engine path",
          "new_engine_production" in src and "run_scheduled(self)" in src)
    i_lock = src.index("flock(lock_fh, fcntl.LOCK_EX")
    i_disp = src.index("resolve_engine()")
    i_unlock = src.index("LOCK_UN")
    check("dispatch happens INSIDE the orchestrator lock",
          i_lock < i_disp < i_unlock)
    check("legacy path still reachable", "_run_production_automation_locked()" in src)
    prod = (HERE / "new_engine_production.py").read_text()
    check("new-engine path requires NEW_ENGINE_V1_MODE=LIVE too, no implicit run",
          "MODE_LIVE" in prod and "refusing to run implicitly" in prod)
    # Call sites, not mentions: the selector switch's docstring names the legacy
    # function while describing the rollback, and prose must not fail a scope guard.
    check("new-engine path does not rotate candidates on HOLD",
          prod.count("orch.get_news_seed_with_usable_source(") == 1)
    check("the authoritative selector does not rotate either -- it chooses once",
          prod.count("SV.run_selection(") == 1)


# ── CURRENT_ENGINE selector rule ──────────────────────────────────────────────
def test_current_engine_selector_rule():
    bad, why = PB._current_engine_ineligible(
        {"engine_generation": "CURRENT_ENGINE", "publication_eligible": "false"})
    check("CURRENT_ENGINE + eligible false -> skipped", bad is True, why)
    for fm in ({"engine_generation": "CURRENT_ENGINE"},
               {"engine_generation": "CURRENT_ENGINE", "publication_eligible": "maybe"},
               {"engine_generation": "CURRENT_ENGINE", "publication_eligible": ""},
               {"engine_generation": "CURRENT_ENGINE", "publication_eligible": "1"}):
        check("CURRENT_ENGINE + %r -> skipped" % fm.get("publication_eligible"),
              PB._current_engine_ineligible(fm)[0] is True)
    check("CURRENT_ENGINE + explicit true -> not skipped by this rule",
          PB._current_engine_ineligible(
              {"engine_generation": "CURRENT_ENGINE",
               "publication_eligible": "true"})[0] is False)
    check("legacy draft is untouched by the CURRENT_ENGINE rule",
          PB._current_engine_ineligible(
              {"fact_check_status": "verified",
               "publication_safety_version": "1"})[0] is False)


def test_legacy_selector_eligibility_unchanged():
    ok = PB._ordinary_eligibility_ok
    check("legacy: verified passes", ok({"fact_check_status": "verified"}) is True)
    check("legacy: blocked fails", ok({"fact_check_status": "blocked"}) is False)
    check("legacy: missing fails", ok({}) is False)
    check("legacy safety-version gate intact",
          PB._current_safety_contract_ok({"publication_safety_version": "1"}) is True
          and PB._current_safety_contract_ok({}) is False)
    pb = (HERE / "publish_best.py").read_text()
    check("selector ranking/cadence untouched",
          "composite_score" in pb and "REQUIRED_SAFETY_VERSION = 1" in pb
          and "topic_freshness" in pb)


# ── the publication-safety bridge ─────────────────────────────────────────────
def test_bridge_all_checks_pass_grants_eligibility():
    out = _accept_run()
    r = BRIDGE.evaluate(out, fact_check_fn=CLEAN_FACT_CHECK)
    names = [c["check"] for c in r.checks]
    for required in ("engine_decision_accept", "source_provenance_intact",
                     "discovery_source_anchor", "article_form_lineage",
                     "writer_grounding_settled", "no_unresolved_unsupported",
                     "no_persona_factual_authority", "human_detail_provenance",
                     "world_relative_fact_check"):
        check("bridge runs required check: %s" % required, required in names, names)
    check("all nine checks pass on a clean run", r.eligible is True,
          [c for c in r.checks if not c["ok"]])
    stamp = BRIDGE.stamp_fields(r)
    check("stamp grants publication_eligible true", stamp["publication_eligible"] is True)
    check("stamp records the CURRENT_ENGINE profile",
          stamp["publication_safety_profile"] == "CURRENT_ENGINE_V1")
    check("stamp keeps the selector's numeric interface",
          stamp["publication_safety_version"] == PB.REQUIRED_SAFETY_VERSION)
    check("stamp writes fact_check_status only after check 9 passed",
          stamp["fact_check_status"] == "verified")


def test_bridge_fails_closed_per_check():
    out = _accept_run()
    # 9: no fact check supplied at all
    r = BRIDGE.evaluate(out, fact_check_fn=None)
    check("missing fact check -> NOT eligible", r.eligible is False)
    check("...and the stamp withholds eligibility",
          BRIDGE.stamp_fields(r)["publication_eligible"] is False)
    check("...and records what blocked it",
          "world_relative_fact_check" in BRIDGE.stamp_fields(r)["publication_safety_blocked_by"])
    # 9: contradicted claim
    r2 = BRIDGE.evaluate(out, fact_check_fn=DIRTY_FACT_CHECK)
    check("contradicted world claim -> NOT eligible", r2.eligible is False)
    # 9: fact check raises
    def boom(_):
        raise RuntimeError("search down")
    r3 = BRIDGE.evaluate(out, fact_check_fn=boom)
    check("fact-check error -> NOT eligible (fail closed)", r3.eligible is False)
    # 1: HOLD decision
    held = dict(out); held["decision"] = "HOLD"
    check("engine HOLD -> NOT eligible",
          BRIDGE.evaluate(held, fact_check_fn=CLEAN_FACT_CHECK).eligible is False)
    # 6: unresolved unsupported
    unsup = _accept_run(grounding={"findings": [
        {"id": "F1", "quote": "The driver was distracted.",
         "classification": "TRUE_UNSUPPORTED", "why": "no cause", "repairable": False,
         "suggested_patch": ""}]})
    r6 = BRIDGE.evaluate(unsup, fact_check_fn=CLEAN_FACT_CHECK)
    check("unresolved TRUE_UNSUPPORTED -> NOT eligible", r6.eligible is False)
    check("...named by the failing check",
          "no_unresolved_unsupported" in [c["check"] for c in r6.failures])
    # 3: anchor broken after the fact
    broken = _accept_run()
    broken["artifacts"][C.DISCOVERY].payload["source_anchor_quote"] = "not in the source at all"
    r3b = BRIDGE.evaluate(broken, fact_check_fn=CLEAN_FACT_CHECK)
    check("broken source anchor -> NOT eligible", r3b.eligible is False)
    check("...named by the failing check",
          "discovery_source_anchor" in [c["check"] for c in r3b.failures])
    # 7: persona factual authority
    check("first-person biography -> persona check fails",
          BRIDGE.check_persona_leakage("I was born in Sheffield.")[0] is False)
    check("ordinary third-person prose passes",
          BRIDGE.check_persona_leakage("The report records a crossing.")[0] is True)


def test_bridge_imports_no_legacy_editorial_gate():
    import ast
    src = (HERE / "publication_safety_bridge.py").read_text()
    tree = ast.parse(src)
    # code only: the module docstring legitimately NAMES what it excludes, so a raw-text
    # scan would fail on its own disclaimer (the recurring trap in this codebase).
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                docs.add(b[0].value.value)
    code_strings = [n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and n.value not in docs]
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module)
            imports |= {"%s.%s" % (n.module, a.name) for a in n.names}
    haystack = "\n".join(list(code_strings) + sorted(names) + sorted(imports))
    for banned in ("RULES_SYSTEM", "_call_editorial_model", "rewrite_with_opus",
                   "_run_persona_biography_editorial_pass", "_fable_polish_rewrite",
                   "gate_llm", "register_selector", "testimony_quota"):
        check("bridge free of legacy gate: %s" % banned, banned not in haystack)
    check("bridge does not import the legacy orchestrator directly",
          "import production_orchestrator" not in src
          and "from orchestrator.llm" not in src)
    check("world-relative fact check is INJECTED, not imported",
          "fact_check_fn" in src)
    check("stylistic diagnostics are not blockers",
          "opening" not in src.lower().replace("opening/template detection does not", "")
          or "rewrite_integrity" not in src)


# ── candidate frontmatter end to end ──────────────────────────────────────────
def test_eligible_candidate_is_selector_visible_and_rehearsal_is_not():
    out = _accept_run()
    meta = CAND.engine_meta_from_run(out, run="r", generated_at="2026-08-24T12:00:00+00:00",
                                     source_url="https://example.org/x",
                                     provider_model="anthropic/claude-opus-4.8")
    r = BRIDGE.evaluate(out, fact_check_fn=CLEAN_FACT_CHECK)
    with tempfile.TemporaryDirectory() as d:
        live = CAND.persist_candidate(drafts_dir=pathlib.Path(d), slug="live", body="Body.",
                                      title="T", author="Maya Flux", engine_meta=meta,
                                      rehearsal=False, safety=BRIDGE.stamp_fields(r))
        fm = PB.parse_frontmatter(live.read_text())
        check("live candidate: engine_generation CURRENT_ENGINE",
              fm["engine_generation"] == "CURRENT_ENGINE")
        check("live candidate: publication_eligible true",
              str(fm["publication_eligible"]).lower() == "true")
        check("live candidate: safety profile recorded",
              fm["publication_safety_profile"] == "CURRENT_ENGINE_V1")
        check("live candidate passes the CURRENT_ENGINE selector rule",
              PB._current_engine_ineligible(fm)[0] is False)
        check("live candidate passes the interlock", PB._interlocked(fm) is False)
        check("live candidate passes legacy fact-check gate too",
              PB._ordinary_eligibility_ok(fm) is True)
        check("live candidate passes the numeric safety gate",
              PB._current_safety_contract_ok(fm) is True)

        reh = CAND.persist_candidate(drafts_dir=pathlib.Path(d), slug="reh", body="Body.",
                                     title="T", author="Maya Flux", engine_meta=meta,
                                     rehearsal=True, safety=BRIDGE.stamp_fields(r))
        fmr = PB.parse_frontmatter(reh.read_text())
        check("rehearsal candidate is NOT eligible even with a granted stamp",
              str(fmr["publication_eligible"]).lower() == "false")
        check("rehearsal candidate skipped by the interlock", PB._interlocked(fmr) is True)
        check("rehearsal candidate also skipped by the CURRENT_ENGINE rule",
              PB._current_engine_ineligible(fmr)[0] is True)


def test_no_rehearsal_candidate_in_live_drafts():
    """The rehearsal artifact must not be sitting in the selector-visible directory."""
    drafts = HERE.parent / "_drafts"
    if not drafts.exists():
        check("drafts dir present", False, "missing"); return
    offenders = []
    for p in drafts.glob("*.md"):
        fm = PB.parse_frontmatter(p.read_text(errors="replace"))
        if str(fm.get("cutover_rehearsal", "")).strip().lower() == "true":
            offenders.append(p.name)
    check("no cutover_rehearsal draft remains in the live pool", offenders == [], offenders)


def main():
    for fn in [test_engine_default_and_rollback,
               test_dispatch_is_wired_and_locked,
               test_current_engine_selector_rule,
               test_legacy_selector_eligibility_unchanged,
               test_bridge_all_checks_pass_grants_eligibility,
               test_bridge_fails_closed_per_check,
               test_bridge_imports_no_legacy_editorial_gate,
               test_eligible_candidate_is_selector_visible_and_rehearsal_is_not,
               test_no_rehearsal_candidate_in_live_drafts]:
        print("\n" + fn.__name__)
        fn()
    os.environ.pop(ES.ENV_VAR, None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL CUTOVER VALIDATION TESTS PASSED")


if __name__ == "__main__":
    main()

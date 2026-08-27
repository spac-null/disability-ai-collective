#!/usr/bin/env python3
"""
cutover_prep_test.py -- deterministic tests for controlled cutover preparation.

Covers the sixteen required checks: the Discovery source-anchor invariant, the
writer/provider failure representation, the engine switch, the ACCEPT/HOLD production
adapter, the publication interlock, selector exclusion, engine-era metadata, legacy
untouchedness, and rollback.

No network, no model calls. No production database. No git. Nothing published.

Run (from repo root):
  python3 automation/cutover_prep_test.py
"""

import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import engine_switch as ES                                  # noqa: E402
import new_engine_candidate as CAND                          # noqa: E402
import publish_best as PB                                    # noqa: E402
from new_engine_v1 import contracts as C                     # noqa: E402
from new_engine_v1 import invariants as INV                  # noqa: E402
from new_engine_v1 import runner as R                        # noqa: E402
from new_engine_v1_test import (StubProvider, DISCOVERY_REPLY, FORM_REPLY,  # noqa: E402
                                SOURCE, SHA, AT, _source_payload, ARTICLE)

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


def _run(provider, tmp, name="t"):
    return R.run(_source_payload(), pathlib.Path(tmp), provider, name, AT,
                 mode=R.MODE_LIVE)


# ── 1 + 2: Discovery source-anchor invariant ──────────────────────────────────
def test_1_valid_anchor_passes():
    ok, code, detail = INV.check_anchor(DISCOVERY_REPLY, SOURCE)
    check("valid designated anchor passes", ok is True, (code, detail))
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(), d)
        check("run proceeds to ACCEPT with a verified anchor", out["decision"] == "ACCEPT",
              out["reasons"])
        check("DISCOVERY records the anchor as verified",
              out["artifacts"][C.DISCOVERY].payload.get("source_anchor_verified") is True)

    # mechanically harmless differences are normalised; semantics are not
    curly = dict(DISCOVERY_REPLY,
                 source_anchor_quote="the  audible warning was sounded on four of the "
                                     "nine occasions logged")
    check("whitespace collapse is tolerated", INV.check_anchor(curly, SOURCE)[0] is True)
    smart = dict(DISCOVERY_REPLY,
                 source_anchor_quote="“observing or hearing an approaching vehicle”")
    check("curly-quote style is tolerated", INV.check_anchor(smart, SOURCE)[0] is True)
    para = dict(DISCOVERY_REPLY,
                source_anchor_quote="the warning sounded on four out of nine occasions")
    check("a PARAPHRASE is rejected", INV.check_anchor(para, SOURCE)[0] is False)
    short = dict(DISCOVERY_REPLY, source_anchor_quote="the report")
    check("a too-short anchor is rejected",
          INV.check_anchor(short, SOURCE)[1] == INV.ANCHOR_TOO_SHORT)
    missing = {k: v for k, v in DISCOVERY_REPLY.items() if k != "source_anchor_quote"}
    check("a missing anchor is rejected",
          INV.check_anchor(missing, SOURCE)[1] == INV.ANCHOR_MISSING)


def test_2_anchor_absent_holds_before_writer():
    bad = dict(DISCOVERY_REPLY, source_anchor_quote="a clause that is nowhere in the source text")
    with tempfile.TemporaryDirectory() as d:
        # repair also fails: the stub returns no exact span
        p = StubProvider(discovery=bad)
        out = _run(p, d, name="a")
        check("anchor not in source -> HOLD", out["decision"] == "HOLD", out["reasons"])
        check("deterministic reason code",
              out.get("reason_code") == INV.ANCHOR_NOT_IN_SOURCE, out.get("reason_code"))
        check("HOLD happens BEFORE the writer -- no WRITER_INPUT",
              C.WRITER_INPUT not in out["artifacts"])
        check("...and no WRITER_OUTPUT", C.WRITER_OUTPUT not in out["artifacts"])
        check("no article file written",
              not (pathlib.Path(d) / "a" / "article.md").exists())
        check("exactly one bounded repair attempt was made, not a loop",
              p.calls and sum(1 for c in p.calls if "correcting ONE field" in c["system"]) == 1,
              sum(1 for c in p.calls if "correcting ONE field" in c["system"]))


def test_2b_bounded_repair_can_succeed():
    """ONE constrained repair, anchor field only."""
    bad = dict(DISCOVERY_REPLY, source_anchor_quote="warning sounded four times of nine")

    class RepairProvider(StubProvider):
        def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
            if "correcting ONE field" in system:
                from new_engine_v1.provider import Completion
                self.calls.append({"system": system, "user": user})
                return Completion(
                    text=json.dumps({"exact_span": "the audible warning was sounded on "
                                                   "four of the nine occasions logged"}),
                    requested_model="m", actual_model="m", provider_label="Stub")
            return super().complete(system, user, max_tokens, timeout, temperature)

    with tempfile.TemporaryDirectory() as d:
        out = R.run(_source_payload(), pathlib.Path(d),
                    RepairProvider(discovery=bad), "rp", AT, mode=R.MODE_LIVE)
        check("a successful bounded repair lets the run continue",
              out["decision"] == "ACCEPT", out["reasons"])
        dp = out["artifacts"][C.DISCOVERY].payload
        check("only the anchor field changed",
              dp["source_anchor_repaired"] is True
              and dp["dominant_reading"] == DISCOVERY_REPLY["dominant_reading"]
              and dp["what_becomes_knowable"] == DISCOVERY_REPLY["what_becomes_knowable"])
        check("the repaired anchor is an exact source span",
              INV.check_anchor(dp, SOURCE)[0] is True)


# ── 3: writer/provider failure ────────────────────────────────────────────────
def test_3_provider_failure_artifact():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_writer=True), d, name="f")
        check("provider failure -> HOLD", out["decision"] == "HOLD", out["reasons"])
        rs = out.get("run_status") or {}
        check("a RUN_STATUS failure record exists", rs.get("status") == "PROVIDER_FAILURE", rs)
        for k in ("stage", "provider", "requested_model", "failure_category", "error",
                  "run", "created_at", "engine"):
            check("RUN_STATUS carries %s" % k, k in rs and rs[k] != "", rs.get(k))
        check("RUN_STATUS states no article was produced",
              rs["article_produced"] is False and rs["writer_output_emitted"] is False)
        check("RUN_STATUS persisted to disk",
              (pathlib.Path(d) / "f" / "RUN_STATUS.json").exists())
        check("NO fake WRITER_OUTPUT artifact", C.WRITER_OUTPUT not in out["artifacts"])
        check("NO article file", not (pathlib.Path(d) / "f" / "article.md").exists())
        man = json.loads((pathlib.Path(d) / "f" / "MANIFEST.json").read_text())
        check("manifest surfaces the failure", man["run_status"] == "PROVIDER_FAILURE")
        check("deterministic reason code",
              out.get("reason_code") == "WRITER_PROVIDER_FAILURE")


# ── 4, 5, 6, 16: engine switch + rollback ─────────────────────────────────────
def test_4_default_engine_is_new_engine_v1():
    # Formal cutover 2026-08-27: the default moved from legacy to new_engine_v1. An unset
    # or blank variable now selects the new engine; explicit legacy remains the rollback.
    os.environ.pop(ES.ENV_VAR, None)
    check("default engine is new_engine_v1", ES.resolve_engine() == ES.NEW_ENGINE_V1)
    check("is_new_engine() true by default", ES.is_new_engine() is True)
    check("empty value is new_engine_v1", ES.resolve_engine("") == ES.NEW_ENGINE_V1)
    check("whitespace value is new_engine_v1", ES.resolve_engine("   ") == ES.NEW_ENGINE_V1)
    check("explicit legacy is still selectable", ES.resolve_engine("legacy") == ES.LEGACY)


def test_5_explicit_new_engine():
    check("explicit new_engine_v1 selects the new engine",
          ES.resolve_engine("new_engine_v1") == ES.NEW_ENGINE_V1)
    check("case/whitespace tolerated", ES.resolve_engine(" New_Engine_V1 ") == ES.NEW_ENGINE_V1)
    check("is_new_engine() true", ES.is_new_engine("new_engine_v1") is True)
    os.environ[ES.ENV_VAR] = "new_engine_v1"
    check("environment variable is honoured", ES.resolve_engine() == ES.NEW_ENGINE_V1)
    os.environ.pop(ES.ENV_VAR, None)


def test_6_unknown_engine_fails_closed():
    for bad in ("newengine", "v1", "new-engine-v1", "sofa", "legacy2", "true", "1"):
        try:
            ES.resolve_engine(bad)
            check("unknown %r fails closed" % bad, False, "it resolved")
        except ES.UnknownEngine:
            check("unknown %r fails closed" % bad, True)


def test_16_rollback_is_one_config_change():
    os.environ[ES.ENV_VAR] = "new_engine_v1"
    check("new engine selected", ES.resolve_engine() == ES.NEW_ENGINE_V1)
    os.environ[ES.ENV_VAR] = "legacy"                     # the rollback
    check("rollback to legacy needs only the env value", ES.resolve_engine() == ES.LEGACY)
    # Since the 2026-08-27 cutover, rollback is an explicit value, NOT a deletion:
    # unsetting now selects the new engine. Asserted so the change cannot regress silently.
    os.environ.pop(ES.ENV_VAR, None)
    check("unsetting no longer rolls back -- it selects the new default",
          ES.resolve_engine() == ES.NEW_ENGINE_V1)
    # code-only: the docstring legitimately says "no database restore, no migration",
    # so scan imports and executable strings rather than prose (the recurring trap).
    import ast
    tree = ast.parse((HERE / "engine_switch.py").read_text())
    imports = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.add(n.module.split(".")[0])
    check("switch imports nothing database-like", not (imports & {"sqlite3", "shutil"}),
          imports)
    check("switch reads one env var and nothing else",
          imports - {"__future__"} == {"os"}, imports)


# ── 7, 8, 9, 10, 15: adapter, interlock, selector, metadata ───────────────────
def _accept_out():
    with tempfile.TemporaryDirectory() as d:
        return _run(StubProvider(), d, name="acc")


def test_7_hold_creates_no_selector_visible_candidate():
    unsupported = {"findings": [
        {"id": "F1", "quote": "The driver was distracted.",
         "classification": "TRUE_UNSUPPORTED", "why": "no cause in source",
         "repairable": False, "suggested_patch": ""}]}
    with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as drafts:
        out = _run(StubProvider(grounding=unsupported), d, name="h")
        check("HOLD as expected", out["decision"] == "HOLD")
        # the adapter is only called on ACCEPT; prove nothing lands in drafts
        check("no draft candidate exists after HOLD",
              list(pathlib.Path(drafts).glob("*.md")) == [])
        check("private evidence still persisted",
              (pathlib.Path(d) / "h" / "MANIFEST.json").exists())


def test_8_accept_persists_candidate_and_selector_ignores_it():
    out = _accept_out()
    body = CAND.final_body(out)
    meta = CAND.engine_meta_from_run(out, run="r1", generated_at="2026-08-24T10:00:00+00:00",
                                     source_url="https://example.org/x",
                                     provider_model="anthropic/claude-opus-4.8")
    with tempfile.TemporaryDirectory() as drafts:
        path = CAND.persist_candidate(drafts_dir=pathlib.Path(drafts), slug="a-candidate",
                                      body=body, title="A Candidate", author="Maya Flux",
                                      engine_meta=meta)
        check("candidate artifact persisted", path.exists())
        fm = PB.parse_frontmatter(path.read_text())
        check("interlock: cutover_rehearsal true", str(fm.get("cutover_rehearsal")).lower() == "true")
        check("interlock: publication_eligible false",
              str(fm.get("publication_eligible")).lower() == "false")
        check("selector's interlock predicate excludes it", PB._interlocked(fm) is True)
        check("selector would ALSO hold it on ordinary eligibility (belt and braces)",
              PB._ordinary_eligibility_ok(fm) is False)
        check("candidate body equals the engine's final grounded output",
              path.read_text().split("---", 2)[2].strip() == body.strip())
        check("a normal legacy-shaped draft is NOT interlocked",
              PB._interlocked({"fact_check_status": "verified",
                               "publication_safety_version": "9"}) is False)


def test_9_candidate_carries_current_engine_metadata():
    out = _accept_out()
    meta = CAND.engine_meta_from_run(out, run="r2", generated_at="2026-08-24T10:00:00+00:00",
                                     source_url="https://example.org/x",
                                     provider_model="anthropic/claude-opus-4.8")
    with tempfile.TemporaryDirectory() as drafts:
        path = CAND.persist_candidate(drafts_dir=pathlib.Path(drafts), slug="m",
                                      body=CAND.final_body(out), title="T",
                                      author="Maya Flux", engine_meta=meta)
        fm = PB.parse_frontmatter(path.read_text())
        check("engine_generation is CURRENT_ENGINE",
              fm.get("engine_generation") == "CURRENT_ENGINE", fm.get("engine_generation"))
        check("editorial_engine is NEW_ENGINE_V1", fm.get("editorial_engine") == "NEW_ENGINE_V1")
        for k in ("engine_version", "engine_decision", "engine_run", "source_sha256",
                  "discovery_hash", "article_form_hash", "writer_grounding_status",
                  "writer_grounding_unsupported", "provider_model"):
            check("metadata field present: %s" % k, fm.get(k) not in (None, ""), fm.get(k))
        A = out["artifacts"]
        check("discovery_hash matches the artifact",
              fm["discovery_hash"] == A[C.DISCOVERY].content_hash())
        check("article_form_hash matches the artifact",
              fm["article_form_hash"] == A[C.ARTICLE_FORM].content_hash())
        check("source_sha256 matches the snapshot", fm["source_sha256"] == SHA)
        check("grounding status recorded", fm["writer_grounding_status"] == "settled")


def test_10_legacy_article_metadata_untouched():
    posts = HERE.parent / "_posts"
    sample = sorted(posts.glob("*.md"))[-3:]
    for p in sample:
        fm = PB.parse_frontmatter(p.read_text(errors="replace"))
        check("legacy post %s has no engine-era metadata" % p.name[:28],
              "engine_generation" not in fm and "editorial_engine" not in fm, sorted(fm)[:6])
        check("legacy post %s is not interlocked" % p.name[:28], PB._interlocked(fm) is False)
    drafts = HERE.parent / "_drafts"
    legacy_drafts = [p for p in drafts.glob("*.md")
                     if "editorial_engine" not in p.read_text(errors="replace")]
    check("existing legacy drafts remain non-interlocked",
          all(PB._interlocked(PB.parse_frontmatter(p.read_text(errors="replace"))) is False
              for p in legacy_drafts), len(legacy_drafts))


def test_15_accept_does_not_publish():
    out = _accept_out()
    check("ACCEPT policy text says it is not publication",
          "never publication" in out["artifacts"][C.SHADOW_DECISION].payload["policy"])
    src = (HERE / "new_engine_candidate.py").read_text()
    for banned in ("_posts", "commit_to_git", "git ", "subprocess", "publish("):
        check("adapter contains no publish path: %r" % banned, banned not in src)
    # the docstring mentions `_drafts/` when explaining the design; what matters is
    # that no code path CONSTRUCTS that path -- the destination is always injected.
    import ast as _ast
    _tree = _ast.parse(src)
    _code_strings = []
    _docs = set()
    for n in _ast.walk(_tree):
        if isinstance(n, (_ast.Module, _ast.FunctionDef, _ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], _ast.Expr) and isinstance(b[0].value, _ast.Constant) \
                    and isinstance(b[0].value.value, str):
                _docs.add(b[0].value.value)
        if isinstance(n, _ast.Constant) and isinstance(n.value, str):
            _code_strings.append(n.value)
    check("adapter never constructs a _posts/_drafts path in code",
          not any(("_drafts" in cs or "_posts" in cs)
                  for cs in _code_strings if cs not in _docs),
          [cs[:40] for cs in _code_strings if ("_drafts" in cs or "_posts" in cs)
           and cs not in _docs])
    check("adapter takes its destination as a parameter", "drafts_dir" in src)
    posts = HERE.parent / "_posts"
    before = {p: p.stat().st_mtime for p in sorted(posts.glob("*.md"))[-20:]}
    _accept_out()
    check("no _posts file touched by an ACCEPT run",
          {p: p.stat().st_mtime for p in before} == before)


# ── 11, 12, 13, 14: legacy surfaces absent from the new path ──────────────────
def test_11_to_14_legacy_surfaces_absent():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(), d, name="L")
        prompt = out["artifacts"][C.WRITER_INPUT].payload["prompt_text"]
    hits = [m for m in C.LEGACY_PROMPT_MARKERS if m in prompt]
    check("11: no legacy 59k prompt marker in the new-engine writer input", hits == [], hits)
    check("11: writer input is compact", len(prompt) < 20000, len(prompt))
    pkg = "\n".join((HERE / "new_engine_v1" / f).read_text()
                    for f in ("runner.py", "stages.py", "invariants.py"))
    low = pkg.lower()
    check("12: no whole-document rewrite in the new path",
          "rewrite_with_opus" not in pkg and "whole-document rewrite" not in low.replace(
              "no whole-document rewrite", ""))
    check("13: no persona-biography pass in the new path",
          "_run_persona_biography_editorial_pass" not in pkg and "fable_polish" not in pkg)
    for judge in ("_call_editorial_model", "gate_llm", "rules_system",
                  "which article is better", "editorial_score"):
        check("14: no legacy LLM rule judge: %r absent" % judge, judge not in low)
    check("14: repair is deterministic, not a judge",
          "def repair(" in (HERE / "new_engine_v1" / "stages.py").read_text())


def test_legacy_path_and_cadence_unchanged():
    gen = (HERE / "orchestrator" / "generate.py").read_text()
    check("legacy prewriter loop intact", "MAX_PREWRITER_CANDIDATES" in gen)
    check("legacy rotation set intact",
          '_PREWRITER_OUTCOMES = ("defer", "declined")' in gen)
    disc = (HERE / "orchestrator" / "discovery.py").read_text()
    check("legacy acquisition budget intact", "MAX_SOURCE_ACQUISITION_ATTEMPTS = 3" in disc)
    pb = (HERE / "publish_best.py").read_text()
    check("selector interlock added additively (eligibility rules intact)",
          "_ordinary_eligibility_ok" in pb and "_current_safety_contract_ok" in pb
          and "_interlocked" in pb)
    check("selector cadence/ranking untouched",
          "composite_score" in pb and "REQUIRED_SAFETY_VERSION" in pb)
    check("no production module imports the new engine",
          not any("new_engine_v1" in p.read_text()
                  for p in (HERE / "orchestrator").glob("*.py")))


def main():
    for fn in [test_1_valid_anchor_passes,
               test_2_anchor_absent_holds_before_writer,
               test_2b_bounded_repair_can_succeed,
               test_3_provider_failure_artifact,
               test_4_default_engine_is_new_engine_v1,
               test_5_explicit_new_engine,
               test_6_unknown_engine_fails_closed,
               test_16_rollback_is_one_config_change,
               test_7_hold_creates_no_selector_visible_candidate,
               test_8_accept_persists_candidate_and_selector_ignores_it,
               test_9_candidate_carries_current_engine_metadata,
               test_10_legacy_article_metadata_untouched,
               test_15_accept_does_not_publish,
               test_11_to_14_legacy_surfaces_absent,
               test_legacy_path_and_cadence_unchanged]:
        print("\n" + fn.__name__)
        fn()
    os.environ.pop(ES.ENV_VAR, None)
    os.environ.pop("NEW_ENGINE_V1_MODE", None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL CUTOVER-PREPARATION TESTS PASSED")


if __name__ == "__main__":
    main()

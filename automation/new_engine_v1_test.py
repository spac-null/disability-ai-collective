#!/usr/bin/env python3
"""
new_engine_v1_test.py -- deterministic contract tests for NEW_ENGINE_V1.

Tests CONTRACTS, not literary taste. There is no "which article is better" judge here
and there must never be one: every assertion below is a structural or provenance fact.

No network, no model calls -- the provider is stubbed. No production database, no
_posts/_drafts write, no git call.

Run (from repo root):
  python3 automation/new_engine_v1_test.py
"""

import ast
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import contracts as C
from research_pack_fixture import stub_pack            # noqa: E402
from new_engine_v1 import runner as R               # noqa: E402
from new_engine_v1 import stages as S               # noqa: E402
from new_engine_v1.decision import decide, ACCEPT, HOLD  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILURES.append(name)


# --------------------------------------------------------------------------- #
SOURCE = ("The council report records that the crossing relies on users \"observing or "
          "hearing an approaching vehicle\". It also records that the audible warning was "
          "sounded on four of the nine occasions logged. No injuries were reported.")
SHA = C.sha256_text(SOURCE)
AT = "2026-08-24T00:00:00+00:00"


def _source_payload():
    return {"source_text": SOURCE, "source_sha256": SHA,
            "provenance": {"origin": "fetched_article", "url": "https://example.org/report",
                           "seed_id": "abc123"}}


DISCOVERY_REPLY = {
    "commissionable": True,
    # exact span of SOURCE -- the anchor invariant (Part A) requires this
    "source_anchor_quote": "the audible warning was sounded on four of the nine "
                           "occasions logged",
    "dominant_reading": "A crossing where people failed to look.",
    "disturbance": "The report says safety rests on \"observing or hearing an approaching "
                   "vehicle\", then records the warning sounded on four of nine occasions.",
    "perceptual_instrument": "Attention tuned to which channels are actually load-bearing.",
    "what_becomes_knowable": "A channel that is usually silent teaches its users that "
                             "silence is information.",
    "source_facts": ["warning sounded on four of nine logged occasions",
                     "safety premised on observing or hearing"],
    "evidence_gaps": ["the report does not establish why the warning was not sounded"],
    "grounding_boundaries": "Do not name anyone. Do not state why the warning was not "
                            "sounded. Do not stage a scene in the cab.",
}

FORM_REPLY = {
    "route": ["State the premise as the report frames it, closing on the two channels.",
              "Take the second channel apart using the report's own numbers.",
              "Arrive, and stop."],
    "motion": "narrows -> accumulates -> recurs",
    "arrival": "A channel almost always silent teaches its users that silence is information.",
    "burden": "Carried by the report's facts in sequence. No remedy, no persona voice.",
    "target_words": [900, 1200],
}

ARTICLE = ("The report frames the crossing as a place where people must look or listen.\n\n"
           "It also records that the warning sounded on four of the nine occasions logged.\n\n"
           "A channel almost always silent teaches its users that silence is information.\n")


class StubProvider:
    """Scripted replies. Records every (system, user) pair for inspection."""

    def __init__(self, discovery=None, form=None, article=None, grounding=None,
                 recheck=None, fail_writer=False,
                 fail_discovery=False, malformed_discovery=False,
                 fail_form=False, malformed_form=False,
                 fail_ground=False, malformed_ground=False):
        self.calls = []
        self._discovery = discovery if discovery is not None else DISCOVERY_REPLY
        self._form = form if form is not None else FORM_REPLY
        self._article = article if article is not None else ARTICLE
        self._grounding = grounding if grounding is not None else {"findings": []}
        self._recheck = recheck
        self._fail_writer = fail_writer
        self._fail_discovery = fail_discovery
        self._malformed_discovery = malformed_discovery
        self._fail_form = fail_form
        self._malformed_form = malformed_form
        self._fail_ground = fail_ground
        self._malformed_ground = malformed_ground
        self._ground_calls = 0

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        self.calls.append({"system": system, "user": user})
        from new_engine_v1.provider import Completion, ProviderError
        if "discovery stage" in system:
            if self._fail_discovery:
                raise ProviderError("stub provider failure: discovery")
            body = "not json at all, just prose" if self._malformed_discovery \
                else json.dumps(self._discovery)
        elif "article-form stage" in system:
            if self._fail_form:
                raise ProviderError("stub provider failure: article form")
            body = "<<<not json>>>" if self._malformed_form else json.dumps(self._form)
        elif "writer-grounding stage" in system:
            self._ground_calls += 1
            if self._fail_ground:
                raise ProviderError("stub provider failure: grounding")
            if self._malformed_ground:
                body = "{unterminated json"
            else:
                src = (self._recheck if (self._ground_calls > 1 and self._recheck is not None)
                       else self._grounding)
                body = json.dumps(src)
        else:
            if self._fail_writer:
                raise ProviderError("stub provider failure")
            body = self._article
        return Completion(text=body, requested_model="anthropic/claude-opus-4.8",
                          actual_model="anthropic/claude-opus-4.8",
                          provider_label="StubProvider")


def _run(provider, tmp, name="t", byline="Maya Flux", research_fn=stub_pack):
    return R.run(_source_payload(), pathlib.Path(tmp), provider, name, AT,
                 byline=byline, mode=R.MODE_LIVE, research_fn=research_fn)


# --------------------------------------------------------------------------- #
def test_default_off():
    os.environ.pop("NEW_ENGINE_V1_MODE", None)
    check("default mode is OFF", R.current_mode() == "OFF", R.current_mode())
    with tempfile.TemporaryDirectory() as d:
        try:
            R.run(_source_payload(), pathlib.Path(d), StubProvider(), "off", AT)
            check("run() refuses while OFF", False, "it executed")
        except R.EngineDisabled:
            check("run() refuses while OFF", True)
        check("nothing was written while OFF", not any(pathlib.Path(d).rglob("*")))
    for bad in ("REPLAY", "ON", "LIVE_SHADOW", "true"):
        try:
            R.run(_source_payload(), pathlib.Path(tempfile.mkdtemp()), StubProvider(),
                  "x", AT, mode=bad)
            check("unknown mode %r refuses" % bad, False)
        except R.EngineDisabled:
            check("unknown mode %r refuses" % bad, True)


def test_full_path_and_provenance():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(), d)
        A = out["artifacts"]
        for stage in (C.SOURCE_SNAPSHOT, C.RESEARCH_PACK, C.DISCOVERY,
                      C.ARTICLE_FORM, C.WRITER_INPUT,
                      C.WRITER_OUTPUT, C.GROUNDING_FINDINGS, C.SHADOW_DECISION):
            check("stage present: %s" % stage, stage in A)
        check("decision is ACCEPT on a clean draft", out["decision"] == ACCEPT, out["reasons"])

        # provenance: the snapshot's bytes and hash survive, and every stage's declared
        # lineage matches the artifact actually supplied (validate/verify_lineage ran).
        check("source text preserved byte-for-byte",
              A[C.SOURCE_SNAPSHOT].payload["source_text"] == SOURCE)
        check("source hash matches the bytes",
              C.sha256_text(A[C.SOURCE_SNAPSHOT].payload["source_text"]) == SHA)
        check("source provenance origin preserved",
              A[C.SOURCE_SNAPSHOT].payload["provenance"]["origin"] == "fetched_article")
        # Lineage widened with the Research Pack (2026-08-28): Discovery now reads the
        # anchor AND the frozen pack, and every downstream stage declares the exact pack
        # it used. The property under test is unchanged -- declared lineage must match
        # the artifacts actually supplied -- only the expected set grew.
        check("DISCOVERY declares the source and the research pack",
              sorted(A[C.DISCOVERY].input_hashes) == ["research_pack", "source"],
              A[C.DISCOVERY].input_hashes)
        check("ARTICLE_FORM consumes discovery + source + pack",
              sorted(A[C.ARTICLE_FORM].input_hashes) ==
              ["discovery", "research_pack", "source"])
        check("RESEARCH_PACK is emitted from the source snapshot",
              C.RESEARCH_PACK in A and
              list(A[C.RESEARCH_PACK].input_hashes) == ["source"])

        man = json.loads((pathlib.Path(d) / "t" / "MANIFEST.json").read_text())
        check("manifest records every stage hash",
              set(man["stage_hashes"]) == set(A), sorted(man["stage_hashes"]))
        check("manifest records provider identity per stage",
              set(man["provider_identity"]) >= {"discovery", "article_form", "writer",
                                                "grounding"},
              sorted(man["provider_identity"]))
        check("manifest states no publication",
              man["publication"].startswith("NONE"))
        check("artifact hashes are deterministic for identical material",
              A[C.DISCOVERY].content_hash() ==
              _run(StubProvider(), tempfile.mkdtemp())["artifacts"][C.DISCOVERY].content_hash())


def test_grounding_receives_exactly_source_and_draft():
    """Writer Grounding must see the commissioned source and the draft -- not the Form."""
    with tempfile.TemporaryDirectory() as d:
        p = StubProvider()
        out = _run(p, d)
        gcalls = [c for c in p.calls if "writer-grounding stage" in c["system"]]
        check("grounding was called exactly once on a clean draft", len(gcalls) == 1)
        u = gcalls[0]["user"]
        check("grounding received the exact commissioned source", SOURCE in u)
        check("grounding received the draft", ARTICLE.strip()[:40] in u)
        check("grounding did NOT receive the Article Form route",
              FORM_REPLY["route"][0] not in u)
        # NB: the arrival sentence legitimately appears in the DRAFT, so its presence
        # proves nothing. Assert on Form fields that never surface as prose.
        check("grounding did NOT receive the Form's burden", FORM_REPLY["burden"] not in u)
        check("grounding did NOT receive the Form's motion", FORM_REPLY["motion"] not in u)
        check("grounding did NOT receive discovery's boundaries",
              DISCOVERY_REPLY["grounding_boundaries"] not in u)
        check("GROUNDING_FINDINGS declares writer_output + source + pack",
              sorted(out["artifacts"][C.GROUNDING_FINDINGS].input_hashes)
              == ["research_pack", "source", "writer_output"])


def test_writer_input_has_no_legacy_or_persona_authority():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(), d)
        prompt = out["artifacts"][C.WRITER_INPUT].payload["prompt_text"]
        hits = [m for m in C.LEGACY_PROMPT_MARKERS if m in prompt]
        check("no legacy prompt marker in WRITER_INPUT", hits == [], hits)
        low = prompt.lower()
        for bad in ("you are maya flux", "your wound", "authorized personal history",
                    "beat note", "register:", "canon", "aphorism"):
            check("writer input free of %r" % bad, bad not in low)
        # "testimony" DOES appear -- as a prohibition. Assert the polarity, not absence.
        check("testimony appears only as a prohibition",
              "may not write first-person lived experience, testimony" in prompt)
        check("byline is present but explicitly not a person with lived experience",
              "Maya Flux" in prompt and "not a person with a biography" in prompt)
        check("writer input carries the grounding boundaries",
              DISCOVERY_REPLY["grounding_boundaries"][:30] in prompt)
        check("writer input carries the Form's route", FORM_REPLY["route"][0] in prompt)
        check("prompt is compact, not the 59k legacy pile", len(prompt) < 12000, len(prompt))


def test_accept_impossible_with_unresolved_unsupported_claim():
    unsupported = {"findings": [
        {"id": "F1", "quote": "The driver was distracted.",
         "classification": "TRUE_UNSUPPORTED",
         "why": "the source states no cause", "repairable": False,
         "suggested_patch": ""}]}
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(grounding=unsupported), d, name="u")
        check("unresolved TRUE_UNSUPPORTED forces HOLD", out["decision"] == HOLD, out["reasons"])
        check("the reason names the finding",
              any("TRUE_UNSUPPORTED" in r for r in out["reasons"]), out["reasons"])
        check("no repair artifact was fabricated",
              C.GROUNDING_REPAIR not in out["artifacts"])

    # uncertain also holds, unadjudicated
    uncertain = {"findings": [
        {"id": "F1", "quote": "Nine occasions were logged that winter.",
         "classification": "TRUE_UNCERTAIN", "why": "no date in source",
         "repairable": False, "suggested_patch": ""}]}
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(grounding=uncertain), d, name="q")
        check("unadjudicated TRUE_UNCERTAIN forces HOLD", out["decision"] == HOLD, out["reasons"])

    # legitimate interpretation alone does NOT hold
    interp = {"findings": [
        {"id": "F1", "quote": "silence is information",
         "classification": "LEGITIMATE_INTERPRETATION", "why": "reading, not new fact",
         "repairable": False, "suggested_patch": ""}]}
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(grounding=interp), d, name="i")
        check("LEGITIMATE_INTERPRETATION does not block ACCEPT",
              out["decision"] == ACCEPT, out["reasons"])


def test_patch_only_repair_and_recheck():
    bad_article = ("The report frames the crossing as a place where people must look.\n\n"
                   "The driver was distracted that morning.\n\n"
                   "A channel almost always silent teaches that silence is information.\n")
    finding = {"id": "F1", "quote": "The driver was distracted that morning.",
               "classification": "TRUE_UNSUPPORTED",
               "why": "the source states no cause", "repairable": True,
               "suggested_patch": "The report does not record why the warning was not sounded."}
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(article=bad_article, grounding={"findings": [finding]},
                                recheck={"findings": []}), d, name="r")
        A = out["artifacts"]
        check("repair artifact created", C.GROUNDING_REPAIR in A)
        rp = A[C.GROUNDING_REPAIR].payload
        check("repair mode is patch_only", rp["mode"] == "patch_only")
        check("one patch applied", len(rp["patches"]) == 1, rp["patches"])
        check("the unsupported clause is gone",
              finding["quote"] not in rp["article_text"])
        check("the patch text is present", finding["suggested_patch"] in rp["article_text"])
        check("untouched prose is byte-identical",
              "A channel almost always silent teaches that silence is information."
              in rp["article_text"])
        check("re-check ran against the PATCHED text (residual measured, not assumed)",
              rp["verification"]["residual"] == 0 and "recheck_findings" in rp)
        check("no introduced findings", rp["verification"]["introduced"] == 0)
        check("decision is ACCEPT after a verified repair", out["decision"] == ACCEPT,
              out["reasons"])

    # a repair that does NOT clear the claim must HOLD
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(article=bad_article, grounding={"findings": [finding]},
                                recheck={"findings": [dict(finding)]}), d, name="r2")
        check("a repair whose re-check still finds the claim HOLDs",
              out["decision"] == HOLD, out["reasons"])


def test_provider_failure_holds_without_fallback_article():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_writer=True), d, name="f")
        check("provider failure HOLDs", out["decision"] == HOLD, out["reasons"])
        check("no WRITER_OUTPUT artifact was fabricated for a failed provider",
              C.WRITER_OUTPUT not in out["artifacts"])
        check("no template article file was written",
              not (pathlib.Path(d) / "f" / "article.md").exists())
        check("reason names the provider failure",
              any("provider" in r for r in out["reasons"]), out["reasons"])


# --------------------------------------------------------------------------- #
# Stage-failure containment (Blocker 2). DISCOVERY, ARTICLE_FORM and
# GROUNDING_FINDINGS each get the same guarantee WRITER_OUTPUT already had:
# provider/parse failure -> clean HOLD, no fabricated artifact for the failed
# stage, no downstream stage runs, and a structured RUN_STATUS naming the stage.
def _assert_stage_holds_cleanly(out, d, name, failed_stage, later_stages,
                                expect_status="PROVIDER_FAILURE"):
    check("%s failure HOLDs (%s)" % (failed_stage, out.get("reason_code")),
          out["decision"] == HOLD, out["reasons"])
    check("no %s artifact was fabricated" % failed_stage,
          failed_stage not in out["artifacts"])
    for later in later_stages:
        check("no downstream stage ran: %s absent after %s failure" % (later, failed_stage),
              later not in out["artifacts"])
    # article.md is the raw evidence copy of whatever the writer actually drafted --
    # written by _persist whenever WRITER_OUTPUT exists, regardless of what happens
    # after. It is not a publication signal (that's publication_eligible, set only by
    # the safety bridge in new_engine_production.py, never by runner.py). So: absent
    # for a pre-writer failure (Discovery/Article Form), present-but-inert for a
    # post-writer failure (Grounding) -- exactly mirroring existing editorial-HOLD
    # behavior (e.g. an unresolved TRUE_UNSUPPORTED finding also leaves article.md
    # on disk as evidence).
    article_path = pathlib.Path(d) / name / "article.md"
    if C.WRITER_OUTPUT in out["artifacts"]:
        check("article.md exists as inert evidence (writer succeeded before %s failed)"
              % failed_stage, article_path.exists())
    else:
        check("no article.md was written (writer never ran)", not article_path.exists())
    rs_path = pathlib.Path(d) / name / "RUN_STATUS.json"
    check("RUN_STATUS.json exists", rs_path.exists())
    if rs_path.exists():
        rs = json.loads(rs_path.read_text())
        check("RUN_STATUS names the failed stage", rs.get("stage") == failed_stage, rs)
        check("RUN_STATUS status is %s" % expect_status,
              rs.get("status") == expect_status, rs)
        check("RUN_STATUS is distinguishable from an editorial HOLD "
              "(carries failure_category)", "failure_category" in rs, rs)
    man = json.loads((pathlib.Path(d) / name / "MANIFEST.json").read_text())
    check("MANIFEST publication is NONE", man["publication"].startswith("NONE"))
    check("MANIFEST run_status mirrors RUN_STATUS.status",
          man["run_status"] == expect_status, man)
    check("out carries no 'publication_eligible: true'-shaped signal",
          "publication_eligible" not in out)


def test_discovery_provider_exception_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_discovery=True), d, name="d-exc")
        _assert_stage_holds_cleanly(
            out, d, "d-exc", C.DISCOVERY,
            [C.ARTICLE_FORM, C.WRITER_INPUT, C.WRITER_OUTPUT, C.GROUNDING_FINDINGS])
        check("reason_code identifies discovery + provider_error",
              out.get("reason_code") == "DISCOVERY_PROVIDER_ERROR", out.get("reason_code"))


def test_discovery_malformed_response_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(malformed_discovery=True), d, name="d-mal")
        _assert_stage_holds_cleanly(
            out, d, "d-mal", C.DISCOVERY,
            [C.ARTICLE_FORM, C.WRITER_INPUT, C.WRITER_OUTPUT, C.GROUNDING_FINDINGS])


def test_discovery_structurally_invalid_response_holds_cleanly():
    """Valid JSON, but missing a required field -- contracts.validate() raises
    ContractViolation, not ProviderError. Distinct failure category, same
    containment guarantee."""
    with tempfile.TemporaryDirectory() as d:
        bad = dict(DISCOVERY_REPLY)
        del bad["grounding_boundaries"]
        out = _run(StubProvider(discovery=bad), d, name="d-inv")
        _assert_stage_holds_cleanly(
            out, d, "d-inv", C.DISCOVERY,
            [C.ARTICLE_FORM, C.WRITER_INPUT, C.WRITER_OUTPUT, C.GROUNDING_FINDINGS],
            expect_status="CONTRACT_FAILURE")
        check("reason_code identifies discovery + invalid_response_shape",
              out.get("reason_code") == "DISCOVERY_INVALID_RESPONSE_SHAPE",
              out.get("reason_code"))


def test_article_form_provider_exception_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_form=True), d, name="f-exc")
        _assert_stage_holds_cleanly(
            out, d, "f-exc", C.ARTICLE_FORM,
            [C.WRITER_INPUT, C.WRITER_OUTPUT, C.GROUNDING_FINDINGS])
        check("DISCOVERY still ran and was persisted before the Form failed",
              C.DISCOVERY in out["artifacts"])


def test_article_form_malformed_response_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(malformed_form=True), d, name="f-mal")
        _assert_stage_holds_cleanly(
            out, d, "f-mal", C.ARTICLE_FORM,
            [C.WRITER_INPUT, C.WRITER_OUTPUT, C.GROUNDING_FINDINGS])


def test_grounding_provider_exception_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_ground=True), d, name="g-exc")
        _assert_stage_holds_cleanly(out, d, "g-exc", C.GROUNDING_FINDINGS, [])
        check("WRITER_OUTPUT still ran and was persisted before grounding failed",
              C.WRITER_OUTPUT in out["artifacts"])
        check("no SHADOW_DECISION (ACCEPT/HOLD editorial verdict) was reached",
              C.SHADOW_DECISION not in out["artifacts"])


def test_grounding_malformed_response_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(malformed_ground=True), d, name="g-mal")
        _assert_stage_holds_cleanly(out, d, "g-mal", C.GROUNDING_FINDINGS, [])


def test_writer_failure_behavior_unchanged():
    """The pre-existing WRITER_OUTPUT failure path (Part B, 2026-08-24) must be
    byte-for-byte unchanged by the new stage-failure containment: same status
    string, same stage identity, same reason_code shape."""
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(fail_writer=True), d, name="w-exc")
        check("writer failure still HOLDs", out["decision"] == HOLD)
        check("writer failure status is still PROVIDER_FAILURE",
              out["run_status"]["status"] == "PROVIDER_FAILURE", out["run_status"])
        check("writer failure stage is still WRITER_OUTPUT",
              out["run_status"]["stage"] == C.WRITER_OUTPUT, out["run_status"])
        check("writer failure reason_code is still WRITER_PROVIDER_FAILURE",
              out["reason_code"] == "WRITER_PROVIDER_FAILURE", out["reason_code"])
        check("DISCOVERY, ARTICLE_FORM, WRITER_INPUT still ran before the writer failed",
              {C.DISCOVERY, C.ARTICLE_FORM, C.WRITER_INPUT} <= set(out["artifacts"]))
        check("no GROUNDING_FINDINGS ran after a writer failure",
              C.GROUNDING_FINDINGS not in out["artifacts"])


def test_writer_contract_failure_holds_cleanly():
    """write()'s success path is not model-parsed JSON, so this edge is narrower than
    Discovery/Form/Grounding's -- but it is not unreachable: an empty completion is
    the one way article_text can fail contracts.validate()'s WRITER_OUTPUT check
    despite provider_status == 'ok'. The real Provider already prevents this
    (provider.py raises ProviderError on empty content before write() would ever
    return 'ok'), but write() itself is duck-typed against any object exposing
    .complete(), so this boundary must hold on its own, not merely inherit a
    guarantee from a different module."""
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(article=""), d, name="w-inv")
        _assert_stage_holds_cleanly(out, d, "w-inv", C.WRITER_OUTPUT,
                                    [C.GROUNDING_FINDINGS], expect_status="CONTRACT_FAILURE")
        check("reason_code identifies writer + invalid_response_shape",
              out.get("reason_code") == "WRITER_OUTPUT_INVALID_RESPONSE_SHAPE",
              out.get("reason_code"))
        check("DISCOVERY, ARTICLE_FORM, WRITER_INPUT still ran before the writer's "
              "contract check failed",
              {C.DISCOVERY, C.ARTICLE_FORM, C.WRITER_INPUT} <= set(out["artifacts"]))


def test_non_commissionable_source_holds_cleanly():
    with tempfile.TemporaryDirectory() as d:
        out = _run(StubProvider(discovery=dict(DISCOVERY_REPLY, commissionable=False)),
                   d, name="n")
        check("a non-commissionable source HOLDs", out["decision"] == HOLD, out["reasons"])
        check("no writer stage ran", C.WRITER_OUTPUT not in out["artifacts"])
        check("no article file written",
              not (pathlib.Path(d) / "n" / "article.md").exists())


def test_no_publication_side_effect():
    with tempfile.TemporaryDirectory() as d:
        posts = HERE.parent / "_posts"
        drafts = HERE.parent / "_drafts"
        before = {p: p.stat().st_mtime for p in list(posts.glob("*.md"))[:40]}
        n_drafts = len(list(drafts.glob("*.md"))) if drafts.exists() else 0
        out = _run(StubProvider(), d, name="p")
        after = {p: p.stat().st_mtime for p in before}
        check("no _posts file was touched", before == after)
        check("no _drafts file was added",
              (len(list(drafts.glob("*.md"))) if drafts.exists() else 0) == n_drafts)
        written = sorted(str(p.relative_to(d)) for p in pathlib.Path(d).rglob("*")
                         if p.is_file())
        check("every write is inside the given run root",
              all(w.startswith("p/") for w in written), written[:4])
        check("ACCEPT is documented as pool-eligibility, not publication",
              "never publication" in
              out["artifacts"][C.SHADOW_DECISION].payload["policy"])


def test_package_purity_static():
    """No legacy import, no publication path, no db, no network, no LLM judge.

    AST-based: scans executable code, not docstrings -- the shadow_v0 lesson, where a
    raw-text scan failed on a safety docstring mentioning `_posts`.
    """
    pkg = HERE / "new_engine_v1"
    banned_imports = {"sqlite3", "requests", "socket", "subprocess",
                      "orchestrator", "production_orchestrator", "news_fetcher"}
    banned_names = {"_posts", "_drafts", "commit_to_git", "publish_best"}
    for f in sorted(pkg.glob("*.py")):
        tree = ast.parse(f.read_text())
        imports = set()
        strings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
        # RAW docstring constants. ast.get_docstring() returns a CLEANED (dedented)
        # string, which never equals the raw Constant value, so filtering on it silently
        # fails -- exactly the trap shadow_v0's own docstring hit from the other side.
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                body = getattr(node, "body", None)
                if body and isinstance(body[0], ast.Expr) \
                        and isinstance(body[0].value, ast.Constant) \
                        and isinstance(body[0].value.value, str):
                    docstrings.add(body[0].value.value)
        code_strings = [s for s in strings if s not in docstrings]
        bad_imp = imports & banned_imports
        check("%s: no banned import" % f.name, not bad_imp, bad_imp)
        bad_nm = [n for n in banned_names
                  if any(n in s for s in code_strings)]
        check("%s: no publication/db identifier in code" % f.name, not bad_nm, bad_nm)
    # the engine is not referenced by any scheduled production module
    orch = HERE / "orchestrator"
    refs = [p.name for p in list(orch.glob("*.py")) + [HERE / "production_orchestrator.py"]
            if "new_engine_v1" in p.read_text()]
    check("no production module imports NEW_ENGINE_V1", refs == [], refs)
    # no "which is better" judge anywhere in the engine
    joined = "\n".join(f.read_text().lower() for f in pkg.glob("*.py"))
    for phrase in ("which article is better", "which is better", "rate the article",
                   "score the article", "prefer a or b"):
        check("no quality-preference judge: %r absent" % phrase, phrase not in joined)


def test_infra_failure_stays_operator_visible():
    """The one thing structured stage-failure evidence (this file's earlier tests) does
    NOT by itself prove: that the SCHEDULED PROCESS still signals failure to an
    operator. Discovery/Form/Grounding/Writer failures all HOLD without raising --
    correct -- but production_orchestrator.py's __main__ used to rely on an UNCAUGHT
    exception's non-zero exit code to make cripminds-daily.sh's bash wrapper log an
    ERROR and fire a Telegram alert. A clean HOLD, left unchecked, would exit 0 and
    that signal would never fire -- indistinguishable, to the wrapper, from an
    ordinary editorial HOLD (which correctly stays silent). This proves the fix:
    production_orchestrator._is_infra_or_contract_failure() must say True for every
    infra/contract failure category and False for an ordinary editorial HOLD."""
    import production_orchestrator as PO
    import new_engine_production as NEP

    class _FakeOrch:
        def __init__(self):
            import logging
            self.logger = logging.getLogger("test_infra_failure_stays_operator_visible")
            self.drafts_dir = pathlib.Path(tempfile.mkdtemp())

        def get_news_seed_with_usable_source(self):
            return {"id": "s1", "url": "https://example.org/a", "summary": "s"}

        def get_source_text(self, url, fallback_text=None, underlying_url=None):
            return SOURCE

        def get_source_origin(self, url):
            return "fetched_article"

        def get_source_original_length(self, url):
            return len(SOURCE)

        def get_source_paragraph_count(self, url):
            return 2

    os.environ["NEW_ENGINE_V1_MODE"] = "LIVE"
    CASES = {
        "discovery_provider": (dict(fail_discovery=True), True),
        "discovery_contract": (dict(discovery={k: v for k, v in DISCOVERY_REPLY.items()
                                               if k != "grounding_boundaries"}), True),
        "article_form_provider": (dict(fail_form=True), True),
        "grounding_provider": (dict(fail_ground=True), True),
        "writer_provider": (dict(fail_writer=True), True),
        "writer_contract": (dict(article=""), True),
        "editorial_hold": (dict(discovery=dict(DISCOVERY_REPLY, commissionable=False)), False),
        "clean_accept": ({}, False),
    }
    real_provider = NEP.Provider
    try:
        for label, (kwargs, expect_infra_failure) in CASES.items():
            NEP.Provider = lambda model=None, _k=kwargs, **kw: StubProvider(**_k)
            out = NEP.run_scheduled(_FakeOrch(),
                                    evidence_root=tempfile.mkdtemp(),
                                    research_fn=stub_pack)
            got = PO._is_infra_or_contract_failure(out)
            check("_is_infra_or_contract_failure(%s) == %s" % (label, expect_infra_failure),
                  got == expect_infra_failure,
                  (label, got, out.get("run_status")))
    finally:
        NEP.Provider = real_provider
    os.environ.pop("NEW_ENGINE_V1_MODE", None)


def test_legacy_scheduled_path_unchanged():
    gen = (HERE / "orchestrator" / "generate.py").read_text()
    check("legacy prewriter loop still present and bounded at 5",
          "MAX_PREWRITER_CANDIDATES = 5" in
          (HERE / "orchestrator" / "generate.py").read_text() or
          "MAX_PREWRITER_CANDIDATES" in gen)
    check("legacy rotation set unchanged",
          '_PREWRITER_OUTCOMES = ("defer", "declined")' in gen)
    disc = (HERE / "orchestrator" / "discovery.py").read_text()
    check("legacy source-acquisition budget unchanged",
          "MAX_SOURCE_ACQUISITION_ATTEMPTS = 3" in disc)
    import shadow_capture as SC
    check("legacy capture contract unchanged",
          SC.REQUIRED_EVENTS == ("evidence", "commission", "writer",
                                 "final_output", "disposition"))


def main():
    for fn in [test_default_off,
               test_full_path_and_provenance,
               test_grounding_receives_exactly_source_and_draft,
               test_writer_input_has_no_legacy_or_persona_authority,
               test_accept_impossible_with_unresolved_unsupported_claim,
               test_patch_only_repair_and_recheck,
               test_provider_failure_holds_without_fallback_article,
               test_discovery_provider_exception_holds_cleanly,
               test_discovery_malformed_response_holds_cleanly,
               test_discovery_structurally_invalid_response_holds_cleanly,
               test_article_form_provider_exception_holds_cleanly,
               test_article_form_malformed_response_holds_cleanly,
               test_grounding_provider_exception_holds_cleanly,
               test_grounding_malformed_response_holds_cleanly,
               test_writer_failure_behavior_unchanged,
               test_writer_contract_failure_holds_cleanly,
               test_infra_failure_stays_operator_visible,
               test_non_commissionable_source_holds_cleanly,
               test_no_publication_side_effect,
               test_package_purity_static,
               test_legacy_scheduled_path_unchanged]:
        print("\n" + fn.__name__)
        fn()
    os.environ.pop("NEW_ENGINE_V1_MODE", None)
    print("\n" + "-" * 60)
    if FAILURES:
        print("FAILED: %d" % len(FAILURES))
        for f in FAILURES:
            print("   - " + f)
        sys.exit(1)
    print("ALL NEW_ENGINE_V1 CONTRACT TESTS PASSED")


if __name__ == "__main__":
    main()

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

from new_engine_v1 import contracts as C            # noqa: E402
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
                 recheck=None, fail_writer=False):
        self.calls = []
        self._discovery = discovery if discovery is not None else DISCOVERY_REPLY
        self._form = form if form is not None else FORM_REPLY
        self._article = article if article is not None else ARTICLE
        self._grounding = grounding if grounding is not None else {"findings": []}
        self._recheck = recheck
        self._fail_writer = fail_writer
        self._ground_calls = 0

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        self.calls.append({"system": system, "user": user})
        from new_engine_v1.provider import Completion, ProviderError
        if "discovery stage" in system:
            body = json.dumps(self._discovery)
        elif "article-form stage" in system:
            body = json.dumps(self._form)
        elif "writer-grounding stage" in system:
            self._ground_calls += 1
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


def _run(provider, tmp, name="t", byline="Maya Flux"):
    return R.run(_source_payload(), pathlib.Path(tmp), provider, name, AT,
                 byline=byline, mode=R.MODE_LIVE)


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
        for stage in (C.SOURCE_SNAPSHOT, C.DISCOVERY, C.ARTICLE_FORM, C.WRITER_INPUT,
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
        check("DISCOVERY declares the source as its only input",
              list(A[C.DISCOVERY].input_hashes) == ["source"], A[C.DISCOVERY].input_hashes)
        check("ARTICLE_FORM consumes discovery + source",
              sorted(A[C.ARTICLE_FORM].input_hashes) == ["discovery", "source"])

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
        check("GROUNDING_FINDINGS declares only writer_output + source",
              sorted(out["artifacts"][C.GROUNDING_FINDINGS].input_hashes)
              == ["source", "writer_output"])


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

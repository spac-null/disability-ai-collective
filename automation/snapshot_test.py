#!/usr/bin/env python3
"""
snapshot_test.py — regression harness for production_orchestrator.py's pre-commit
gate / post-publish review pipeline.

WHY THIS EXISTS: a planned module split (2026-08-09 design discussion — see this
repo's git log around this date) moves ~95 methods out of one 6,101-line class into
per-concern files. "The method body didn't change" is currently an eyeball claim on
a live, unattended, daily-publishing pipeline with zero test coverage. This tool
makes it a verified one, for the two risk classes that actually matter here:

  1. DETERMINISTIC CHECKS — _readability_score, _check_buried_clause_sentences,
     _check_argument_word_overuse, _check_sentence_length_distribution,
     _parse_rule_verdicts. Pure functions (none read self), real published articles
     as input, exact-value snapshots. One misplaced character during a move changes
     the fixture diff.

  2. LLM CALL CONSTRUCTION — _pre_commit_gate's GATE_SYSTEM prompt, validate_article's
     RULES_SYSTEM/CITATION_SYSTEM prompts, and their model/max_tokens/timeout. These
     are 100+ line string literals embedded in methods — exactly the kind of thing
     that drifted across 12 hand-copied locations before (see check_rule_drift.py).
     This harness NEVER calls the network: it monkeypatches _call_openai_compat_api,
     _web_verify_quote, and _web_verify_claim to safe recorders/stubs, so a
     byte-for-byte diff of what WOULD have been sent (not the LLM's non-deterministic
     response) survives any refactor. All file writes are redirected into a throwaway
     temp directory (orch.repo_root is overridden) — this never touches _posts/,
     _reviews/, or any real file.

USAGE:
    python3 automation/snapshot_test.py --record   # (re)generate fixtures. Run this
                                                     # once now, before any extraction,
                                                     # and again ONLY when you deliberately
                                                     # change what a rule/prompt should say.
    python3 automation/snapshot_test.py --check     # diff current behavior against
                                                     # recorded fixtures. Run after every
                                                     # mixin-extraction commit.

Exit code 0 = match (or fixtures written). Exit code 1 = drift detected, or no
fixtures recorded yet.
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AUTOMATION_DIR = Path(__file__).parent
FIXTURES_DIR = AUTOMATION_DIR / ".snapshot_fixtures"

# A small, deliberately diverse set of real published articles — different personas,
# lengths, and ages, so the deterministic checks exercise real variation rather than
# one narrow style. Update this list only if one of these files is deleted/renamed;
# adding more is fine and only strengthens coverage.
FIXTURE_ARTICLES = [
    "_posts/2026-08-07-one-in-twelve-and-no-surprises.md",
    "_posts/2026-07-31-injected-since-birth.md",
    "_posts/2026-07-26-vally-wieselthier-fired-her-kiln-while-josef-hoffmann.md",
    "_posts/2026-07-22-fourteen-nodes-on-nicholson-street.md",
    "_posts/2026-07-29-weegee-heard-the-body-first.md",
    "_posts/2026-08-07-a-stack-of-colours-has-not-made-a-single-sound-yet.md",
]

# Synthetic raw LLM-verdict text for _parse_rule_verdicts — this one isn't
# article-dependent, so real published text doesn't exercise its actual edge cases.
# "reversal_bug_case" reproduces the exact failure fixed 2026-08-02..06 (see the
# method's own docstring): a [FAIL] line followed by a [PASS] reversal for the same
# rule id must resolve to PASS, not count as a violation.
SYNTHETIC_VERDICT_RAWS = {
    "normal_mixed": (
        '[PASS] R1\n[FAIL] R2 — "some quoted phrase here"\n[N/A] R9\n'
        '[FAIL] R14 — "another one"'
    ),
    "reversal_bug_case": (
        "[FAIL] R3 — reasoning text, none found with certainty\n[PASS] R3"
    ),
    "all_pass": "\n".join(f"[PASS] R{i}" for i in range(1, 18)),
    "malformed_noise": (
        "some preamble text\n[FAIL]R5 no space before rule\n"
        "[FAIL] R6 — real one\nnot a verdict line at all"
    ),
}


def _import_orchestrator():
    sys.path.insert(0, str(AUTOMATION_DIR))
    import production_orchestrator as po
    return po


def _load_fixture_texts():
    texts = {}
    for rel in FIXTURE_ARTICLES:
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"WARNING: fixture article missing, skipping: {rel}", file=sys.stderr)
            continue
        texts[rel] = path.read_text(encoding="utf-8")
    return texts


def _snapshot_deterministic(po, fixture_texts):
    out = {}
    for name, content in fixture_texts.items():
        out[name] = {
            "readability_score": po.ProductionOrchestrator._readability_score(
                po.ProductionOrchestrator.__new__(po.ProductionOrchestrator), content
            ),
            "buried_clause_hits": po.ProductionOrchestrator._check_buried_clause_sentences(content),
            "argument_hits": po.ProductionOrchestrator._check_argument_word_overuse(content),
            "length_dist_hits": po.ProductionOrchestrator._check_sentence_length_distribution(content),
            "shadow_bullet_hits": po.ProductionOrchestrator._check_bullet_points_shadow(content),
        }
    out["_parse_rule_verdicts"] = {
        key: po.ProductionOrchestrator._parse_rule_verdicts(raw)
        for key, raw in SYNTHETIC_VERDICT_RAWS.items()
    }
    return out


def _make_recorder():
    calls = []

    def fake_call_openai_compat_api(self, url, api_key, system_prompt, user_prompt,
                                     model, max_tokens=3500, timeout=120, no_think=False,
                                     return_model=False, reasoning_max_tokens=None):
        calls.append({
            "system_prompt": system_prompt,
            "model": model,
            "max_tokens": max_tokens,
            "timeout": timeout,
        })
        # Safe dummy response: enough [PASS] Rn lines to satisfy any parser up through
        # R30 (current max in use is R17), plus CLEAN for citation-style checks, so
        # every calling method proceeds down its "nothing wrong" path instead of
        # crashing on the absence of a real network response.
        text = "CLEAN\n" + "\n".join(f"[PASS] R{i}" for i in range(1, 30))
        return (text, model) if return_model else text

    return calls, fake_call_openai_compat_api


def _fake_web_verify_quote(self, person, quote):
    return ("UNVERIFIABLE", "stubbed by snapshot_test.py — no live web calls in this harness")


def _fake_web_verify_claim(self, claim_type, subject, claim_text):
    return ("UNVERIFIABLE", "stubbed by snapshot_test.py — no live web calls in this harness")


def _snapshot_llm_calls(po, fixture_texts):
    orig_call = po.ProductionOrchestrator._call_openai_compat_api
    orig_verify_quote = po.ProductionOrchestrator._web_verify_quote
    orig_verify_claim = po.ProductionOrchestrator._web_verify_claim
    calls, fake_call = _make_recorder()
    po.ProductionOrchestrator._call_openai_compat_api = fake_call
    po.ProductionOrchestrator._web_verify_quote = _fake_web_verify_quote
    po.ProductionOrchestrator._web_verify_claim = _fake_web_verify_claim

    out = {}
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = po.ProductionOrchestrator()
            # Redirect ALL file writes (review files, article-file patches) into a
            # throwaway directory — validate_article/_pre_commit_gate derive their
            # write paths from self.repo_root at call time, so this alone is enough
            # to guarantee _posts/, _reviews/, and _drafts/ in the real repo are
            # never touched by this harness.
            orch.repo_root = Path(tmpdir)
            (orch.repo_root / "_reviews").mkdir(exist_ok=True)

            for name, content in fixture_texts.items():
                tmp_article = Path(tmpdir) / (Path(name).stem + ".md")
                tmp_article.write_text(content, encoding="utf-8")

                calls.clear()
                try:
                    gate_content, gate_changed = orch._pre_commit_gate(
                        content, tmp_article, article_type=None
                    )
                    gate_error = None
                except Exception as e:
                    gate_content, gate_changed, gate_error = None, None, f"{type(e).__name__}: {e}"
                gate_calls = [dict(c) for c in calls]

                calls.clear()
                try:
                    review_file, is_clean = orch.validate_article(
                        content, tmp_article, slug="snapshot-test"
                    )
                    review_error = None
                except Exception as e:
                    is_clean, review_error = None, f"{type(e).__name__}: {e}"
                review_calls = [dict(c) for c in calls]

                out[name] = {
                    "gate_calls": gate_calls,
                    "gate_changed": gate_changed,
                    "gate_error": gate_error,
                    "review_calls": review_calls,
                    "review_is_clean": is_clean,
                    "review_error": review_error,
                }
    finally:
        po.ProductionOrchestrator._call_openai_compat_api = orig_call
        po.ProductionOrchestrator._web_verify_quote = orig_verify_quote
        po.ProductionOrchestrator._web_verify_claim = orig_verify_claim

    return out


def _fixture_path(name):
    return FIXTURES_DIR / f"{name}.json"


def record():
    po = _import_orchestrator()
    fixture_texts = _load_fixture_texts()
    if not fixture_texts:
        print("ERROR: no fixture articles could be loaded — nothing to record.", file=sys.stderr)
        return 1
    FIXTURES_DIR.mkdir(exist_ok=True)

    deterministic = _snapshot_deterministic(po, fixture_texts)
    _fixture_path("deterministic").write_text(json.dumps(deterministic, indent=2, sort_keys=True))

    llm_calls = _snapshot_llm_calls(po, fixture_texts)
    _fixture_path("llm_calls").write_text(json.dumps(llm_calls, indent=2, sort_keys=True))

    print(f"Recorded fixtures for {len(fixture_texts)} article(s) to {FIXTURES_DIR}/")
    return 0


def check():
    if not FIXTURES_DIR.exists() or not any(FIXTURES_DIR.glob("*.json")):
        print("ERROR: no fixtures recorded yet. Run with --record first.", file=sys.stderr)
        return 1

    po = _import_orchestrator()
    fixture_texts = _load_fixture_texts()
    problems = []

    deterministic_expected = json.loads(_fixture_path("deterministic").read_text())
    deterministic_actual = _snapshot_deterministic(po, fixture_texts)
    if deterministic_actual != deterministic_expected:
        for key in set(deterministic_expected) | set(deterministic_actual):
            if deterministic_expected.get(key) != deterministic_actual.get(key):
                problems.append(f"[DRIFT] deterministic checks changed for: {key}")

    llm_expected = json.loads(_fixture_path("llm_calls").read_text())
    llm_actual = _snapshot_llm_calls(po, fixture_texts)
    if llm_actual != llm_expected:
        for key in set(llm_expected) | set(llm_actual):
            if llm_expected.get(key) != llm_actual.get(key):
                problems.append(f"[DRIFT] gate/review LLM-call construction changed for: {key}")

    if problems:
        print("Snapshot drift detected:\n")
        for p in problems:
            print(p)
        print(
            "\nRe-run with a diff tool against automation/.snapshot_fixtures/*.json to see "
            "exactly what changed. If the change was deliberate (a real rule-text or logic "
            "fix, not a refactor accident), re-run --record to update the baseline."
        )
        return 1

    print(f"No drift — {len(fixture_texts)} article(s) match recorded fixtures.")
    return 0


if __name__ == "__main__":
    if "--record" in sys.argv:
        sys.exit(record())
    elif "--check" in sys.argv:
        sys.exit(check())
    else:
        print(__doc__)
        sys.exit(1)

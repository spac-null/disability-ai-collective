#!/usr/bin/env python3
"""
rewrite_integrity_test.py — regression suite for rewrite_integrity.py and its
wiring into all three rewrite/revision acceptance paths in llm.py
(rewrite_with_opus, _opus_targeted_revision, _fable_polish_rewrite).

Morning-stabilization follow-up, 2026-08-14. See rewrite_integrity.py's own
module docstring for the full incident this closes:
`_posts/2026-03-31-the-floor-plan-of-disappearance.md` published with its own
body duplicated, from its very first commit, traced to rewrite_with_opus's
old acceptance check being trivially satisfiable by its own synthetic
frontmatter wrapper alone.

The historical fixture below is SYNTHETIC (a constructed ferry-schedule
article, not the live floor-plan content) so this suite never depends on
that published article remaining broken, while reproducing the exact
structural shape of the real failure: N distinct paragraphs, a leaked line
of model self-commentary, then the same N paragraphs again with small
wording differences.

Zero network, zero model calls -- all three llm.py functions are exercised
via _patch_methods, same harness as executor_guard_test.py.

USAGE: python3 automation/rewrite_integrity_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from snapshot_test import _import_orchestrator, _patch_methods  # noqa: E402
from orchestrator.grounding import build_evidence_packet  # noqa: E402
from orchestrator.rewrite_integrity import (  # noqa: E402
    validate_rewrite_integrity, find_duplicated_block,
    REASON_DUPLICATED_BODY, REASON_MALFORMED_ARTICLE,
)

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def _orch():
    po = _import_orchestrator()
    return po, po.ProductionOrchestrator()


# ── Synthetic historical-shape fixture ─────────────────────────────────────

_PARA_A = ("The harbor authority replaced its ferry schedule system in March. "
           "The new interface removed the printed timetable from every dock. "
           "Travelers now needed a smartphone app to find departure times, "
           "and the app required a login that many elderly residents could not manage.")
_PARA_B = ("A dockworker named Thomas Reyes kept a paper copy of the schedule "
           "taped inside the ticket booth. He handed printed copies to anyone "
           "who asked. He did this quietly for months before a supervisor told "
           "him company policy required only the app.")
_PARA_C = ("The city called this modernization. The old system took two "
           "minutes to read. The new system required an account, a working "
           "phone, and cellular signal at a dock where signal was famously "
           "unreliable.")
_PARA_D = ("Reyes said the schedule had not changed, only the way you were "
           "allowed to see it. People who could not use the app simply "
           "stopped showing up on time, and nobody counted them as a "
           "failure of the system.")
_PARA_E = ("This is not a technical problem. It is a choice about who counts "
           "as a normal user, made by people who never once tried finding a "
           "ferry without a phone in their pocket.")

_ORIGINAL_BODY = "\n\n".join([_PARA_A, _PARA_B, _PARA_C, _PARA_D, _PARA_E])

# Small wording differences per paragraph, same shape as the real historical
# diff (a clause swapped, a word changed) -- not byte-identical.
_PARA_A2 = _PARA_A.replace("The new interface removed", "New typeface, new layout — the redesign removed")
_PARA_B2 = _PARA_B.replace("He did this quietly for months", "He kept doing this for months")
_PARA_C2 = _PARA_C.replace("famously unreliable", "known to drop constantly")
_PARA_D2 = _PARA_D.replace("nobody counted them as a failure of the system", "the system never once counted them")
_PARA_E2 = _PARA_E.replace("in their pocket", "at all")

_LEAKED_LINE = "I need to stop and return the correct article. Let me apply only the listed fixes precisely."

_DUPLICATED_BODY_WITH_LEAK = "\n\n".join([
    _PARA_A, _PARA_B, _PARA_C, _PARA_D, _PARA_E,
    _LEAKED_LINE,
    _PARA_A2, _PARA_B2, _PARA_C2, _PARA_D2, _PARA_E2,
])

_DUPLICATED_BODY_NO_LEAK = "\n\n".join([
    _PARA_A, _PARA_B, _PARA_C, _PARA_D, _PARA_E,
    _PARA_A2, _PARA_B2, _PARA_C2, _PARA_D2, _PARA_E2,
])

_FRONTMATTER = '---\nlayout: post\ntitle: "The Ferry Nobody Could Find"\nauthor: Test\n---\n'


# ── 1. Historical reproduction: prove the OLD logic would have accepted it ─

def case_historical_old_rewrite_with_opus_check_would_have_accepted():
    full = _FRONTMATTER + _DUPLICATED_BODY_WITH_LEAK
    old_check_passes = full.count("---") >= 2 and len(full) > 400
    check("OLD rewrite_with_opus check (count('---')>=2 and len>400) WOULD HAVE "
          "ACCEPTED the historical corruption shape -- proves the gap existed "
          "(the frontmatter's own 2 delimiters satisfy this regardless of body)",
          old_check_passes is True)


def case_historical_old_fabrication_guard_alone_would_have_accepted():
    po, orch = _orch()
    packet = build_evidence_packet(None)
    # The REAL, unmodified guard -- introduces no new fact, so it must return
    # the duplicated content unchanged (not None), proving it alone (without
    # the new integrity guard ahead of it) would have accepted this.
    guarded = orch._reject_if_unsupported_specifics(
        _ORIGINAL_BODY, _DUPLICATED_BODY_WITH_LEAK, packet, "historical reproduction test",
    )
    check("OLD fabrication guard (_reject_if_unsupported_specifics) alone WOULD HAVE "
          "ACCEPTED the duplicated content -- a verbatim repeat introduces no new "
          "unsupported fact, proving _opus_targeted_revision/_fable_polish_rewrite's "
          "pre-existing guard could not have caught this failure class either",
          guarded == _DUPLICATED_BODY_WITH_LEAK)


# ── 2/3. New guard rejects the historical shape, with and without the leak ─

def case_new_guard_rejects_historical_shape_with_leak():
    result = validate_rewrite_integrity(_ORIGINAL_BODY, _DUPLICATED_BODY_WITH_LEAK)
    check("NEW guard REJECTS the exact historical corruption shape (with leaked line)",
          result["ok"] is False and REASON_DUPLICATED_BODY in result["reasons"])


def case_new_guard_rejects_historical_shape_without_leak():
    result = validate_rewrite_integrity(_ORIGINAL_BODY, _DUPLICATED_BODY_NO_LEAK)
    check("NEW guard REJECTS the same duplication with the leaked commentary line "
          "removed -- the duplication-run signal alone is sufficient, doesn't "
          "depend on catching the leaked sentence",
          result["ok"] is False and REASON_DUPLICATED_BODY in result["reasons"])


def case_duplicated_block_with_small_wording_changes_rejected():
    # This IS case 2/3's fixture (small wording diffs per paragraph) -- an
    # explicit, separately-named assertion per the test matrix's own item 3.
    run = find_duplicated_block(_DUPLICATED_BODY_NO_LEAK)
    check("duplicated block with small per-paragraph wording changes -> "
          "a consecutive run is still found (near-duplicate, not byte-identical)",
          run is not None and len(run) >= 3)


# ── 4-9. Legitimate content must ACCEPT; malformed/empty must REJECT ───────

def case_legitimate_long_rewrite_accepted():
    long_body = "\n\n".join([_PARA_A, _PARA_B, _PARA_C, _PARA_D, _PARA_E] * 1)
    result = validate_rewrite_integrity(_ORIGINAL_BODY, long_body)
    check("a legitimate rewrite with no internal duplication -> ACCEPT",
          result["ok"] is True)


def case_intro_conclusion_callback_accepted():
    # First and last paragraph deliberately echo each other -- a real,
    # intentional device -- but nothing else in the piece repeats.
    middle = "\n\n".join([_PARA_B, _PARA_C, _PARA_D])
    callback_body = "\n\n".join([_PARA_A, middle, _PARA_A2])
    result = validate_rewrite_integrity(_ORIGINAL_BODY, callback_body)
    check("a single intro/conclusion callback pair (not a multi-paragraph run) -> ACCEPT",
          result["ok"] is True)


def case_deliberate_repeated_phrase_accepted():
    # A short, distinctive rhetorical phrase reused a few times inside
    # otherwise-different paragraphs -- common intentional device, must not
    # be mistaken for catastrophic duplication.
    refrain = "That is the whole point of the redesign, and nobody said it out loud."
    body = "\n\n".join([
        _PARA_A + " " + refrain,
        _PARA_B,
        _PARA_C + " " + refrain,
        _PARA_D,
        _PARA_E + " " + refrain,
    ])
    result = validate_rewrite_integrity(_ORIGINAL_BODY, body)
    check("a short deliberate refrain repeated across otherwise-distinct paragraphs -> ACCEPT",
          result["ok"] is True)


def case_similar_figure_captions_do_not_trigger():
    fig1 = ('<figure class="article-figure">\n'
            '<img src="a.jpg" alt="Ferry dock at dawn — wide illustration">\n'
            '<figcaption>Ferry dock at dawn — wide illustration</figcaption>\n'
            '</figure>')
    fig2 = ('<figure class="article-figure">\n'
            '<img src="b.jpg" alt="Ferry dock at dawn — narrow illustration">\n'
            '<figcaption>Ferry dock at dawn — narrow illustration</figcaption>\n'
            '</figure>')
    body = "\n\n".join([_PARA_A, fig1, _PARA_B, _PARA_C, fig2, _PARA_D, _PARA_E])
    run = find_duplicated_block(body)
    check("two similar figure captions alone -> does NOT trigger catastrophic-body "
          "rejection (figure blocks stripped entirely before comparison)",
          run is None)


def case_normal_frontmatter_and_body_accepted():
    full = _FRONTMATTER + _ORIGINAL_BODY
    result = validate_rewrite_integrity(_FRONTMATTER + _ORIGINAL_BODY, full, require_frontmatter=True)
    check("normal frontmatter + valid, non-duplicated body -> ACCEPT",
          result["ok"] is True)


def case_frontmatter_only_empty_body_rejected():
    empty = _FRONTMATTER
    result = validate_rewrite_integrity(_FRONTMATTER + _ORIGINAL_BODY, empty, require_frontmatter=True)
    check("frontmatter block with an empty/near-empty body -> REJECT (MALFORMED_ARTICLE)",
          result["ok"] is False and REASON_MALFORMED_ARTICLE in result["reasons"])


# ── 10/11. Integration: _opus_targeted_revision / _fable_polish_rewrite reject ──

def case_opus_targeted_revision_rejects_duplicated_content():
    po, orch = _orch()
    packet = build_evidence_packet(None)
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: _DUPLICATED_BODY_WITH_LEAK,
    )
    try:
        result = orch._opus_targeted_revision(_ORIGINAL_BODY, ["fix the opening"], "Test Persona", packet)
    finally:
        restore()
    check("_opus_targeted_revision: duplicated-content response is REJECTED, "
          "falls back to the ORIGINAL article body unchanged",
          result == _ORIGINAL_BODY)


def case_fable_polish_rewrite_rejects_duplicated_content_falls_back_to_opus():
    po, orch = _orch()
    packet = build_evidence_packet(None)
    clean_fallback = "\n\n".join([_PARA_A, _PARA_B, _PARA_C, _PARA_D, _PARA_E])
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_editorial_model=lambda self, *a, **k: _DUPLICATED_BODY_WITH_LEAK,
        _call_openai_compat_api=lambda self, *a, **k: clean_fallback,
    )
    try:
        result = orch._fable_polish_rewrite(_ORIGINAL_BODY, ["fix the opening"], "Test Persona", "wry", packet)
    finally:
        restore()
    check("_fable_polish_rewrite: primary attempt duplicates content -> REJECTED -> "
          "falls through to Opus fallback's clean revision",
          result == clean_fallback)


def case_rewrite_with_opus_rejects_duplicated_content():
    po, orch = _orch()
    corrupted_full = _FRONTMATTER + _DUPLICATED_BODY_WITH_LEAK
    restore = _patch_methods(
        po.ProductionOrchestrator,
        _call_openai_compat_api=lambda self, *a, **k: corrupted_full,
    )
    try:
        result = orch.rewrite_with_opus(_FRONTMATTER + _ORIGINAL_BODY)
    finally:
        restore()
    check("rewrite_with_opus: duplicated-content full-article response is REJECTED, "
          "falls back to the ORIGINAL input unchanged",
          result == _FRONTMATTER + _ORIGINAL_BODY)


# ── 12/13. Clean paths through all three functions stay unchanged ─────────

def case_all_three_paths_unchanged_for_clean_output():
    po, orch = _orch()
    packet = build_evidence_packet(None)
    clean = "\n\n".join([_PARA_A2, _PARA_B2, _PARA_C2, _PARA_D2, _PARA_E2])

    restore = _patch_methods(po.ProductionOrchestrator, _call_openai_compat_api=lambda self, *a, **k: clean)
    try:
        r1 = orch._opus_targeted_revision(_ORIGINAL_BODY, ["fix the opening"], "Test Persona", packet)
    finally:
        restore()
    check("_opus_targeted_revision: clean, non-duplicated, non-fabricating rewrite -> ACCEPTED unchanged",
          r1 == clean)

    restore = _patch_methods(po.ProductionOrchestrator, _call_editorial_model=lambda self, *a, **k: clean)
    try:
        r2 = orch._fable_polish_rewrite(_ORIGINAL_BODY, ["fix the opening"], "Test Persona", "wry", packet)
    finally:
        restore()
    check("_fable_polish_rewrite: clean rewrite -> ACCEPTED unchanged (no fallback triggered)",
          r2 == clean)

    clean_full = _FRONTMATTER + clean
    restore = _patch_methods(po.ProductionOrchestrator, _call_openai_compat_api=lambda self, *a, **k: clean_full)
    try:
        r3 = orch.rewrite_with_opus(_FRONTMATTER + _ORIGINAL_BODY)
    finally:
        restore()
    check("rewrite_with_opus: clean full-article rewrite -> ACCEPTED (frontmatter stripped, "
          "matches the clean body)",
          r3.strip() == clean_full.lstrip("\n").strip())


if __name__ == "__main__":
    case_historical_old_rewrite_with_opus_check_would_have_accepted()
    case_historical_old_fabrication_guard_alone_would_have_accepted()
    case_new_guard_rejects_historical_shape_with_leak()
    case_new_guard_rejects_historical_shape_without_leak()
    case_duplicated_block_with_small_wording_changes_rejected()
    case_legitimate_long_rewrite_accepted()
    case_intro_conclusion_callback_accepted()
    case_deliberate_repeated_phrase_accepted()
    case_similar_figure_captions_do_not_trigger()
    case_normal_frontmatter_and_body_accepted()
    case_frontmatter_only_empty_body_rejected()
    case_opus_targeted_revision_rejects_duplicated_content()
    case_fable_polish_rewrite_rejects_duplicated_content_falls_back_to_opus()
    case_rewrite_with_opus_rejects_duplicated_content()
    case_all_three_paths_unchanged_for_clean_output()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)

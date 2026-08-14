#!/usr/bin/env python3
"""
opening_quality_shadow_test.py — regression suite for
ReviewMixin._extract_opening_quality_shadow (B/C, article-quality evidence
pass, 2026-08-14) and the wiring of ReviewMixin._check_opening_template_shadow
into validate_article. Zero network, zero model calls.

Test matrix covers instruction items A-J (engagement schema) and Q/R
(authority -- neither signal can reach _should_block or any blocking path).

USAGE: python3 automation/opening_quality_shadow_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import inspect
import logging
import sys
import tempfile
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402
from orchestrator.generate import GenerateMixin  # noqa: E402
from orchestrator.gate import GateMixin  # noqa: E402


class _FakeOrch(ReviewMixin):
    def __init__(self, posts_dir):
        self.posts_dir = Path(posts_dir)
        self.logger = logging.getLogger("opening_quality_shadow_test")

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def extract(text):
    return ReviewMixin._extract_opening_quality_shadow(text)


# ── A-D. author-presence enum values ────────────────────────────────────────

def case_A_fused_author_presence():
    r = extract("AUTHOR_PRESENCE: fused — a specific echolocation-based reading of the room is at work from sentence one")
    check("A. fused parses correctly with reason", r["author_presence"] == "fused" and r["author_presence_reason"])


def case_B_generic_opening():
    r = extract("AUTHOR_PRESENCE: generic_or_delayed — reads as a journalistic explainer, no perceptual position until much later")
    check("B. generic_or_delayed parses correctly", r["author_presence"] == "generic_or_delayed")


def case_C_explicit_clunky_self_introduction():
    r = extract("AUTHOR_PRESENCE: explicit_clunky — stops to announce a diagnosis via a dedicated backstory section instead of showing the position")
    check("C. explicit_clunky parses correctly", r["author_presence"] == "explicit_clunky")


def case_D_absent_author_presence():
    r = extract("AUTHOR_PRESENCE: absent — no specific perceptual position discernible anywhere in the piece")
    check("D. absent parses correctly", r["author_presence"] == "absent")


def case_author_presence_unclear():
    r = extract("AUTHOR_PRESENCE: unclear — genuinely cannot tell from this draft")
    check("author_presence unclear parses correctly", r["author_presence"] == "unclear")


# ── E-H. question-timing enum values ────────────────────────────────────────

def case_E_early_natural_question():
    r = extract("QUESTION_TIMING: early_natural — the reader understands the investigation by paragraph two, organically")
    check("E. early_natural parses correctly", r["question_timing"] == "early_natural")


def case_F_early_mechanical_question():
    r = extract("QUESTION_TIMING: early_mechanical — arrives early but via the same templated turn of phrase seen elsewhere")
    check("F. early_mechanical parses correctly", r["question_timing"] == "early_mechanical")


def case_G_delayed_justified():
    r = extract("QUESTION_TIMING: delayed_justified — the reveal is held back deliberately to land after a two-case contrast")
    check("G. delayed_justified parses correctly", r["question_timing"] == "delayed_justified")


def case_H_too_late():
    r = extract("QUESTION_TIMING: too_late — the reader has no idea why they are reading until the final paragraph, no justification")
    check("H. too_late parses correctly", r["question_timing"] == "too_late")


# ── I. missing shadow field never manufactures a failure ───────────────────

def case_I_missing_fields_no_failure():
    r = extract("VERDICT: yes.\nHOOK: interesting.\nDRAG: a bit slow.")
    check("I. no AUTHOR_PRESENCE/QUESTION_TIMING lines at all -> both None, "
          "never raises, never looks like a failure",
          r["author_presence"] is None and r["question_timing"] is None)
    r = extract(None)
    check("I. engagement_read=None -> both None, never raises",
          r["author_presence"] is None and r["question_timing"] is None)
    r = extract("(no response)")
    check("I. engagement_read failure sentinel -> both None",
          r["author_presence"] is None and r["question_timing"] is None)


def case_unrecognized_enum_value_treated_as_missing():
    # A value the model invents that isn't one of the defined enums must be
    # treated exactly like an absent field, not silently accepted -- same
    # discipline as _extract_stop_risk_shadow rejecting out-of-range scores.
    r = extract("AUTHOR_PRESENCE: extremely_fused_and_great — not a real enum value")
    check("an unrecognized AUTHOR_PRESENCE value is treated as missing, not accepted",
          r["author_presence"] is None)
    r = extract("QUESTION_TIMING: sort_of_ok — not a real enum value")
    check("an unrecognized QUESTION_TIMING value is treated as missing, not accepted",
          r["question_timing"] is None)


# ── J. truncation handling unchanged ────────────────────────────────────────

def case_J_engagement_read_still_uses_check_truncation():
    src = inspect.getsource(ReviewMixin._engagement_read)
    check("J. _engagement_read still passes check_truncation=True (unchanged by "
          "this pass's prompt extension)", "check_truncation=True" in src)
    check("J. max_tokens bumped to keep ahead of the longer combined response",
          "max_tokens=600" in src)


# ── Q/R. authority -- neither signal can reach blocking paths ─────────────

def case_Q_opening_quality_never_reaches_should_block():
    src = inspect.getsource(GenerateMixin._compute_should_block)
    check("Q. _compute_should_block's source never references author_presence/"
          "question_timing/opening_quality",
          "author_presence" not in src.lower()
          and "question_timing" not in src.lower()
          and "opening_quality" not in src.lower())


def case_R_opening_template_never_reaches_publication_blocking():
    src_should_block = inspect.getsource(GenerateMixin._compute_should_block)
    check("R. _compute_should_block's source never references opening_template",
          "opening_template" not in src_should_block.lower())
    src_gate = inspect.getsource(GateMixin._pre_commit_gate)
    check("R. gate.py's _pre_commit_gate (the one mechanism that can still stop "
          "something from shipping) never references opening_template or "
          "author_presence/question_timing",
          "opening_template" not in src_gate.lower()
          and "author_presence" not in src_gate.lower()
          and "question_timing" not in src_gate.lower())


def case_extract_opening_quality_shadow_shadow_only_flag():
    r = extract("AUTHOR_PRESENCE: fused — x\nQUESTION_TIMING: early_natural — y")
    check("shadow_only flag is always True", r["shadow_only"] is True)


# ── _check_opening_template_shadow instance-method wiring ──────────────────

_TEMPLATE_A = (
    "---\nlayout: post\ntitle: A\n---\n"
    "A scene about weather in Rotterdam entirely its own. "
    "This building was designed by someone who thinks acoustics is decoration. "
    "But I design spaces with my hands. And let me tell you what they're missing."
)
_TEMPLATE_B = (
    "---\nlayout: post\ntitle: B\n---\n"
    "A totally different scene about a museum visit in December. "
    "This building was designed by someone who thinks acoustics is decoration. "
    "But I design spaces with my hands. And let me tell you what they're missing."
)
_UNRELATED = (
    "---\nlayout: post\ntitle: C\n---\n"
    "A plain article about municipal budget allocations and nothing else "
    "resembling either of the other two pieces in any way whatsoever."
)


def case_opening_template_shadow_detects_real_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        posts = Path(tmpdir)
        (posts / "2026-01-01-article-b.md").write_text(_TEMPLATE_B)
        (posts / "2026-01-02-article-c-unrelated.md").write_text(_UNRELATED)
        orch = _FakeOrch(posts)
        result = orch._check_opening_template_shadow(
            _TEMPLATE_A[_TEMPLATE_A.index("\n---\n") + 5:], "article-a"
        )
        check("_check_opening_template_shadow finds the real template match "
              "against the on-disk posts_dir window",
              result["matched_slug"] == "2026-01-01-article-b" and result["shared_count"] >= 3)


def case_opening_template_shadow_excludes_self():
    with tempfile.TemporaryDirectory() as tmpdir:
        posts = Path(tmpdir)
        (posts / "2026-01-01-article-a.md").write_text(_TEMPLATE_A)
        orch = _FakeOrch(posts)
        result = orch._check_opening_template_shadow(
            _TEMPLATE_A[_TEMPLATE_A.index("\n---\n") + 5:], "article-a"
        )
        check("_check_opening_template_shadow excludes the current article's own "
              "file from the comparison window (would trivially self-match otherwise)",
              result["matched_slug"] is None)


def case_opening_template_shadow_no_match_returns_safe_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        posts = Path(tmpdir)
        (posts / "2026-01-02-unrelated.md").write_text(_UNRELATED)
        orch = _FakeOrch(posts)
        result = orch._check_opening_template_shadow("Some plain unrelated opening content here.", "new-article")
        check("no match in the window -> safe default dict, not None/crash",
              result == {"matched_slug": None, "shared_count": 0, "shared_phrases": []})


def case_opening_template_shadow_never_raises_on_bad_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        posts = Path(tmpdir)
        bad = posts / "2026-01-01-bad.md"
        bad.write_bytes(b"\xff\xfe not valid utf-8 \x00")
        orch = _FakeOrch(posts)
        try:
            result = orch._check_opening_template_shadow("Some content.", "slug")
            raised = False
        except Exception:
            raised = True
        check("a malformed/unreadable sibling file never crashes the shadow check", raised is False)


if __name__ == "__main__":
    case_A_fused_author_presence()
    case_B_generic_opening()
    case_C_explicit_clunky_self_introduction()
    case_D_absent_author_presence()
    case_author_presence_unclear()
    case_E_early_natural_question()
    case_F_early_mechanical_question()
    case_G_delayed_justified()
    case_H_too_late()
    case_I_missing_fields_no_failure()
    case_unrecognized_enum_value_treated_as_missing()
    case_J_engagement_read_still_uses_check_truncation()
    case_Q_opening_quality_never_reaches_should_block()
    case_R_opening_template_never_reaches_publication_blocking()
    case_extract_opening_quality_shadow_shadow_only_flag()
    case_opening_template_shadow_detects_real_match()
    case_opening_template_shadow_excludes_self()
    case_opening_template_shadow_no_match_returns_safe_default()
    case_opening_template_shadow_never_raises_on_bad_files()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)

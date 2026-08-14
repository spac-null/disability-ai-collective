#!/usr/bin/env python3
"""
length_adherence_shadow_test.py — static test suite for
ReviewMixin._check_length_adherence_shadow (A-M reconciliation, item E,
2026-08-14).

E SHADOW V0 -- do not promote before 2026-08-28. The reconciliation confirmed
essay (35% weight) and pleasure/fury/confusion/indefensible have zero
deterministic post-hoc length-adherence check, unlike field_note (≤500,
hard-enforced in gate.py) and portrait/series_part (≥1200, hard-enforced in
gate.py). This suite proves the new shadow classifier: absolute contract for
the two already-enforced types (mirrors gate.py's real numbers exactly, never
disagrees with it), relative-to-target_words bands for every other known
type, UNKNOWN_FORMAT when there's nothing to check against, and that this
check never touches _should_block or any blocking path -- pure observation.

Zero network, zero model calls, zero article generation.

USAGE: python3 automation/length_adherence_shadow_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.review import ReviewMixin  # noqa: E402
from orchestrator.generate import GenerateMixin  # noqa: E402

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def classify(article_type, word_count, target_words):
    return ReviewMixin._check_length_adherence_shadow(article_type, word_count, target_words)


# ── essay/other relative-target types ──────────────────────────────────────

def case_essay_in_range():
    r = classify("essay", 950, 950)
    check("essay at exactly target -> IN_RANGE", r["state"] == "IN_RANGE")
    r = classify("essay", 700, 950)  # ratio 0.74
    check("essay at 0.74x target -> IN_RANGE (inside 0.7-1.3 band)", r["state"] == "IN_RANGE")


def case_essay_short_underflow():
    r = classify("essay", 550, 950)  # ratio ~0.58
    check("essay at 0.58x target -> SOFT_DEVIATION (0.5-0.7 band)", r["state"] == "SOFT_DEVIATION")
    r = classify("essay", 300, 950)  # ratio ~0.32
    check("essay at 0.32x target -> HARD_DEVIATION (<0.5)", r["state"] == "HARD_DEVIATION")


def case_essay_long_overflow():
    r = classify("essay", 1250, 950)  # ratio ~1.32
    check("essay at 1.32x target -> SOFT_DEVIATION (1.3-1.6 band)", r["state"] == "SOFT_DEVIATION")
    r = classify("essay", 1600, 950)  # ratio ~1.68
    check("essay at 1.68x target -> HARD_DEVIATION (>1.6)", r["state"] == "HARD_DEVIATION")


def case_deliberate_longform():
    # The 2800-word bucket, drawn deliberately for ~10% of runs. If the writer
    # lands near ITS OWN target (2800, not some smaller default), it must
    # classify as IN_RANGE, not get penalized for being a long article.
    r = classify("essay", 2750, 2800)
    check("deliberate 2800-word longform landing near its own target -> IN_RANGE, "
          "not penalized for being long", r["state"] == "IN_RANGE")


def case_boundary_values():
    r = classify("essay", 665, 950)  # exactly ratio 0.7 (665/950 = 0.7)
    check("exactly ratio 0.70 -> IN_RANGE (boundary is inclusive)", r["state"] == "IN_RANGE")
    r = classify("essay", 1235, 950)  # exactly ratio 1.3
    check("exactly ratio 1.30 -> IN_RANGE (boundary is inclusive)", r["state"] == "IN_RANGE")
    r = classify("essay", 475, 950)  # exactly ratio 0.5
    check("exactly ratio 0.50 -> SOFT_DEVIATION (boundary is inclusive to SOFT, not HARD)",
          r["state"] == "SOFT_DEVIATION")
    r = classify("essay", 1520, 950)  # exactly ratio 1.6
    check("exactly ratio 1.60 -> SOFT_DEVIATION (boundary is inclusive to SOFT, not HARD)",
          r["state"] == "SOFT_DEVIATION")


def case_other_relative_types_same_mechanism():
    for t in ("pleasure", "fury", "confusion", "indefensible"):
        r = classify(t, 700, 700)
        check(f"{t} at exactly target -> IN_RANGE (same relative mechanism as essay)",
              r["state"] == "IN_RANGE")


# ── field_note / portrait / series_part absolute contract ──────────────────

def case_field_note_absolute_contract():
    r = classify("field_note", 480, 450)  # under the 500 cap even though target_words was only 450
    check("field_note at 480 words (over its 450 draw but under the real 500 cap) -> "
          "IN_RANGE (absolute contract ignores target_words, mirrors gate.py exactly)",
          r["state"] == "IN_RANGE")
    r = classify("field_note", 501, 450)
    check("field_note at 501 words -> HARD_DEVIATION (matches gate.py's >500 hard-fail exactly)",
          r["state"] == "HARD_DEVIATION")
    r = classify("field_note", 500, 450)
    check("field_note at exactly 500 words -> IN_RANGE (gate.py's rule is word_count > 500, "
          "so 500 itself passes)", r["state"] == "IN_RANGE")


def case_portrait_absolute_contract():
    r = classify("portrait", 1199, 1600)
    check("portrait at 1199 words -> HARD_DEVIATION (matches gate.py's <1200 hard-fail exactly)",
          r["state"] == "HARD_DEVIATION")
    r = classify("portrait", 1200, 1600)
    check("portrait at exactly 1200 words -> IN_RANGE", r["state"] == "IN_RANGE")
    r = classify("portrait", 2800, 1600)
    check("portrait at 2800 words (way over target_words but no ceiling exists for portraits) "
          "-> IN_RANGE (absolute contract has no upper bound, matches gate.py)",
          r["state"] == "IN_RANGE")


def case_series_part_same_as_portrait():
    r = classify("series_part", 1100, 1600)
    check("series_part at 1100 words -> HARD_DEVIATION (same 1200 floor as portrait)",
          r["state"] == "HARD_DEVIATION")


def case_gate_agreement_never_disagrees_with_real_enforcement():
    # Structural cross-check: for every word count where gate.py's own
    # _check_article_type_compliance would append a violation, this shadow
    # check must report HARD_DEVIATION, and vice versa for a clean pass.
    import re as _re

    # _check_article_type_compliance's word-count branch is pure (doesn't touch self)
    # but the method itself isn't a staticmethod, so its exact word-count predicate is
    # replicated here rather than instantiating GateMixin just for this cross-check.
    for article_type, over_count, under_count in [
        ("field_note", 501, 400),
        ("portrait", 1600, 1100),
        ("series_part", 1600, 1100),
    ]:
        for wc in (over_count, under_count):
            content = " ".join(["word"] * wc)
            word_count = len(_re.findall(r"\S+", content))
            gate_would_fail = (
                (article_type == "field_note" and word_count > 500)
                or (article_type in {"portrait", "series_part"} and word_count < 1200)
            )
            shadow_state = classify(article_type, word_count, 1600)["state"]
            check(f"{article_type} @ {word_count} words: gate_would_fail={gate_would_fail} "
                  f"<-> shadow_state={shadow_state} agree",
                  gate_would_fail == (shadow_state == "HARD_DEVIATION"))


# ── UNKNOWN_FORMAT ──────────────────────────────────────────────────────────

def case_unknown_article_type():
    r = classify("not_a_real_type", 900, 950)
    check("unrecognized article_type -> UNKNOWN_FORMAT", r["state"] == "UNKNOWN_FORMAT")
    r = classify(None, 900, 950)
    check("article_type=None -> UNKNOWN_FORMAT", r["state"] == "UNKNOWN_FORMAT")
    r = classify("", 900, 950)
    check("article_type='' -> UNKNOWN_FORMAT", r["state"] == "UNKNOWN_FORMAT")


def case_missing_target_words_for_relative_type():
    r = classify("essay", 900, None)
    check("essay with target_words=None -> UNKNOWN_FORMAT (nothing to check adherence against)",
          r["state"] == "UNKNOWN_FORMAT")
    r = classify("essay", 900, 0)
    check("essay with target_words=0 -> UNKNOWN_FORMAT", r["state"] == "UNKNOWN_FORMAT")


def case_missing_target_words_does_not_affect_absolute_types():
    r = classify("field_note", 400, None)
    check("field_note with target_words=None still classifies via the absolute contract "
          "-> IN_RANGE, not UNKNOWN_FORMAT", r["state"] == "IN_RANGE")


# ── never touches blocking policy ──────────────────────────────────────────

def case_never_feeds_should_block():
    check("shadow_only flag is always True (never a promotion decision)",
          classify("essay", 900, 950)["shadow_only"] is True)
    # Structural check mirroring should_block_policy_test.py's own convention:
    # _compute_should_block's source never references length adherence at all.
    import inspect
    src = inspect.getsource(GenerateMixin._compute_should_block)
    check("_compute_should_block's source never references length/word-count adherence "
          "(this shadow check cannot silently gain blocking authority)",
          "length" not in src.lower() and "word_count" not in src.lower())


if __name__ == "__main__":
    case_essay_in_range()
    case_essay_short_underflow()
    case_essay_long_overflow()
    case_deliberate_longform()
    case_boundary_values()
    case_other_relative_types_same_mechanism()
    case_field_note_absolute_contract()
    case_portrait_absolute_contract()
    case_series_part_same_as_portrait()
    case_gate_agreement_never_disagrees_with_real_enforcement()
    case_unknown_article_type()
    case_missing_target_words_for_relative_type()
    case_missing_target_words_does_not_affect_absolute_types()
    case_never_feeds_should_block()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)

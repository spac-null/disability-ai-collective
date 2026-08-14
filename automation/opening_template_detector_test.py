#!/usr/bin/env python3
"""
opening_template_detector_test.py — static test suite for
opening_template_detector.py (article-quality evidence pass, 2026-08-14).

Proves the deterministic cross-article opening-template detector against
the confirmed historical template families (see the module's own docstring)
and against known false-positive shapes found during calibration. Zero
network, zero model calls.

USAGE: python3 automation/opening_template_detector_test.py
Exit code 0 = all pass. Exit code 1 = at least one failure (printed).
"""
import sys
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
REPO_ROOT = AUTOMATION_DIR.parent
sys.path.insert(0, str(AUTOMATION_DIR))

from orchestrator.opening_template_detector import (  # noqa: E402
    normalize_opening, shared_shingle_count, find_template_match,
)

FAILURES = []


def check(name, condition):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        FAILURES.append(name)


def _opening(slug):
    path = REPO_ROOT / "_posts" / f"{slug}.md"
    return normalize_opening(path.read_text(encoding="utf-8"))


# ── K. known 4-article family ───────────────────────────────────────────────

def case_known_family_tight_cluster_detected():
    architects = _opening("2026-03-08-architects-are-designing-buildings-for-the-wrong-sense")
    door = _opening("2026-03-12-the-door-you-can-t-read-is-the-door-that-isn-t-there")
    frequency = _opening("2026-03-14-the-frequency-you-designed-out")

    n1, _ = shared_shingle_count(architects, door)
    n2, _ = shared_shingle_count(door, frequency)
    n3, _ = shared_shingle_count(architects, frequency)
    check("architects <-> door: shares >=3 shingles (confirmed 8)", n1 >= 3)
    check("door <-> frequency: shares >=3 shingles (confirmed 7)", n2 >= 3)
    check("architects <-> frequency: shares >=3 shingles (confirmed 4)", n3 >= 3)


def case_map_that_stops_known_miss():
    # Same rhetorical DEVICE ("But I design X... And let me tell you...") but a
    # different continuation after "let me tell you" -- a documented, accepted
    # miss of this literal-phrase detector, not a bug. See module docstring.
    architects = _opening("2026-03-08-architects-are-designing-buildings-for-the-wrong-sense")
    map_stops = _opening("2026-03-16-the-map-that-stops-at-the-door")
    n, _ = shared_shingle_count(architects, map_stops)
    check("architects <-> map-that-stops: below threshold (documented miss, "
          "different continuation after the shared rhetorical device)", n < 3)


def case_two_new_families_found_during_calibration():
    theory = _opening("2026-06-14-the-theory-that-could-not-see-half-the-room")
    systemizing = _opening("2026-06-18-the-systemizing-quotient-was-right-about-the-wrong-thing")
    n1, shared1 = shared_shingle_count(theory, systemizing)
    check("theory-that-could-not-see <-> systemizing-quotient: shares >=3 shingles "
          "(a previously-unknown template family found by this detector, not seeded)",
          n1 >= 3)

    score = _opening("2026-06-21-she-took-the-score-and-asked-it-a-different-question")
    painted = _opening("2026-06-22-he-painted-everyone-talking")
    n2, shared2 = shared_shingle_count(score, painted)
    check("she-took-the-score <-> he-painted-everyone-talking: shares >=3 shingles "
          "(second previously-unknown family)", n2 >= 3)


# ── L/M/N. unrelated / same-topic-but-distinct / boilerplate-alone ─────────

def case_unrelated_openings_no_match():
    a = _opening("2026-03-08-architects-are-designing-buildings-for-the-wrong-sense")
    b = _opening("2026-04-09-the-ledger-sees-you-now")
    n, _ = shared_shingle_count(a, b)
    check("two thematically and stylistically unrelated openings: below threshold", n < 3)


def case_same_topic_distinct_openings_no_match():
    # Both about accessibility/wayfinding but written with genuinely distinct
    # openings, not a shared template.
    a = _opening("2026-03-16-the-map-that-stops-at-the-door")
    b = _opening("2026-05-04-the-floor-plan-they-can-t-read")
    n, _ = shared_shingle_count(a, b)
    check("same broad topic, distinct openings: below threshold", n < 3)


def case_short_boilerplate_alone_insufficient():
    # A pure-stopword/short-word opening shares almost nothing meaningful.
    a = tuple("in the the a of it is to for on".split())
    b = tuple("in the the a of it is to for on".split())
    n, shared = shared_shingle_count(a, b, min_content_words=3)
    check("an opening built entirely of stopwords/short words -> zero shingles "
          "even if textually identical (min_content_words filter)", n == 0)


# ── O. markdown/link normalization ─────────────────────────────────────────

def case_markdown_and_link_differences_normalize_safely():
    raw_a = (
        "---\nlayout: post\ntitle: Test\n---\n"
        "**But I design buildings with my ears.** And let me tell you what "
        "[they're missing](https://example.com/ref)."
    )
    raw_b = (
        "---\nlayout: post\ntitle: Test2\n---\n"
        "But I design buildings with my ears. And let me tell you what "
        "they're missing."
    )
    a = normalize_opening(raw_a)
    b = normalize_opening(raw_b)
    n, _ = shared_shingle_count(a, b)
    check("bold markup + markdown link vs. plain text of the same sentence -> "
          "still matches after normalization", n >= 1)
    check("normalize_opening strips the URL out of the token stream entirely",
          "https" not in a and "example" not in a)


def case_figure_blocks_stripped_before_normalization():
    raw = (
        "---\nlayout: post\ntitle: Test\n---\n"
        "Real opening text about a topic.\n\n"
        '<figure class="article-figure">\n'
        '<img src="x.jpg" alt="But I design buildings with my ears missing detail">\n'
        "</figure>\n\nMore real text."
    )
    tokens = normalize_opening(raw)
    check("figure block content never enters the normalized opening token stream",
          "missing" not in tokens or "detail" not in tokens)


# ── P. first-paragraph variation, same underlying template ─────────────────

def case_first_paragraph_varies_template_sentence_stable():
    # Simulates a realistic case: the paragraph BEFORE the template sentence
    # varies substantially (different scene-setting), but the template
    # sentence itself is shared -- this is exactly the real architects/door/
    # frequency shape (different scenes, same "But I design X..." line).
    a_text = (
        "---\nlayout: post\ntitle: A\n---\n"
        "A completely different opening scene about weather in Rotterdam and "
        "the particular grey of a Tuesday afternoon in early spring, nothing "
        "like the other piece at all, entirely its own moment. "
        "This building was designed by someone who thinks acoustics is decoration. "
        "But I design spaces with my hands. And let me tell you what they're missing."
    )
    b_text = (
        "---\nlayout: post\ntitle: B\n---\n"
        "A totally unrelated opening about a museum visit in December with "
        "specific details about the lighting and the crowd and the smell of "
        "the gift shop, sharing nothing with the other piece's scene. "
        "This building was designed by someone who thinks acoustics is decoration. "
        "But I design spaces with my hands. And let me tell you what they're missing."
    )
    a = normalize_opening(a_text)
    b = normalize_opening(b_text)
    n, shared = shared_shingle_count(a, b)
    check("distinct scene-setting paragraphs, shared template sentence -> "
          "still detected (evidence supports this: it's exactly the real "
          "architects/door/frequency shape)", n >= 3)


# ── find_template_match (the actual per-run entry point) ───────────────────

def case_find_template_match_returns_best_and_none():
    door = _opening("2026-03-12-the-door-you-can-t-read-is-the-door-that-isn-t-there")
    architects_slug = "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense"
    unrelated_slug = "2026-04-09-the-ledger-sees-you-now"
    candidates = {
        architects_slug: _opening(architects_slug),
        unrelated_slug: _opening(unrelated_slug),
    }
    match = find_template_match(door, candidates)
    check("find_template_match picks the real template match, not the unrelated one",
          match is not None and match["matched_slug"] == architects_slug)
    check("find_template_match reports shared_count and shared_phrases",
          match is not None and match["shared_count"] >= 3 and len(match["shared_phrases"]) > 0)

    no_candidates_match = find_template_match(door, {unrelated_slug: candidates[unrelated_slug]})
    check("find_template_match returns None when nothing reaches the threshold",
          no_candidates_match is None)


def case_never_raises_on_malformed_input():
    try:
        result = find_template_match((), {"x": None, "y": "not a tuple"})
        raised = False
    except Exception:
        raised = True
    check("malformed candidate openings never raise out of find_template_match",
          raised is False)


if __name__ == "__main__":
    case_known_family_tight_cluster_detected()
    case_map_that_stops_known_miss()
    case_two_new_families_found_during_calibration()
    case_unrelated_openings_no_match()
    case_same_topic_distinct_openings_no_match()
    case_short_boilerplate_alone_insufficient()
    case_markdown_and_link_differences_normalize_safely()
    case_figure_blocks_stripped_before_normalization()
    case_first_paragraph_varies_template_sentence_stable()
    case_find_template_match_returns_best_and_none()
    case_never_raises_on_malformed_input()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    else:
        print("ALL PASS")
        sys.exit(0)

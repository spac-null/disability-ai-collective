#!/usr/bin/env python3
"""
check_rule_drift.py — catches the exact failure mode found 2026-08-09: a rule fix
applied to one hand-copied location and missed in the others.

This does NOT replace style_rules.py wiring into the actual prompts (that's a
separate, higher-risk migration, tracked as an ongoing /loop task — see
.claude/bregman-anchor-corpus.md Section 5 and this file's own git log for why a
big-bang prompt rewrite was deliberately deferred). This is a read-only linter:
it checks that the CONTENT of style_rules.py's canonical rule text is actually
present, verbatim, everywhere it currently needs to be in
automation/production_orchestrator.py — the same kind of check a human did by
hand on 2026-08-09 to find the jargon-wordlist and metaphor-exemption drift.

Exit code 0 = no drift found. Exit code 1 = drift found, prints exactly what's
missing and where. Safe to run in a cron/CI step; makes no changes.

HOW TO EXTEND: when you fix a rule in style_rules.py, add or update its entry in
EXPECTED_OCCURRENCES below with the distinguishing phrase that should now be
identical everywhere, and how many places it should appear. This file will not
guess that number for you — a wrong count here is a false sense of safety.
"""
import re
import sys
from pathlib import Path

ORCH_FILE = Path(__file__).parent / "production_orchestrator.py"

# Each entry: rule id -> (distinguishing phrase, expected minimum occurrence count,
# human note on WHERE those occurrences currently live, so a failure is actionable).
# Counts reflect the 2026-08-09 registry-extraction pass; update the count only when
# you deliberately add or remove a location that carries this text.
EXPECTED_OCCURRENCES = {
    "crafted-rhetoric-quote-exemption": (
        "a metaphor inside a real, attributed quote from a named source",
        3,
        "gate GATE_SYSTEM R15(a), validate_article RULES_SYSTEM R16(a), writer "
        "generation prompt's CRAFTED RHETORIC bullet (1)",
    ),
    "long-list-payoff-exemption": (
        "piling up toward a single payoff",
        4,
        "rewrite_with_opus rule 13, gate GATE_SYSTEM R8, validate_article "
        "RULES_SYSTEM R10, writer generation prompt's LISTS RUN TO THREE bullet",
    ),
    "nominalization-rewrite-with-opus": (
        "these are often verbs in disguise",
        1,
        "rewrite_with_opus rule 19 — converged to registry canonical text in the "
        "/loop migration, 2026-08-09 (was independently worded before, no drift "
        "risk from other copies since this phrase is unique to the registry's "
        "current nominalization.imperative text).",
    ),
    "vague-we-rewrite-with-opus": (
        "cut the word and make someone specific do the thing",
        1,
        "rewrite_with_opus rule 19b — converged to registry canonical text in the "
        "/loop migration, 2026-08-09.",
    ),
    "jargon-priority-locations": (
        "priority locations",
        4,
        "validate_article RULES_SYSTEM R13, rewrite_with_opus rule 28, writer "
        "generation prompt's own JARGON bullet, and _pre_commit_gate's GATE_SYSTEM "
        "R10 — all 4 locations converged to the full 8-term canonical list in the "
        "/loop migration, 2026-08-09.",
    ),
    "one-idea-per-sentence-enforcement": (
        "A building whose entire public character is a colour scheme has decided",
        3,
        "writer generation prompt (pre-existing, generative only), "
        "_pre_commit_gate's GATE_SYSTEM R16 (blocking, added 2026-08-09), "
        "validate_article's RULES_SYSTEM R17 (advisory, added 2026-08-09). Closes "
        "the gap found at the end of the 2026-08-09 editing session: this rule "
        "existed in the writer's own prompt but had zero downstream enforcement, "
        "and a real 3-claim-stacked sentence shipped live as a result. "
        "Deliberately NOT added to rewrite_with_opus — that function is the "
        "non-Opus doctrine-rewrite pass already flagged for replacement (branch on "
        "measured register score instead of provider identity), not worth more "
        "rule investment ahead of that change.",
    ),
}


def _flatten_adjacent_string_literals(text):
    """Python joins adjacent string literals ('"...a " \n "b..."') with nothing added
    between them at runtime -- but the raw file has a real newline + indentation +
    quote characters sitting between them at the SOURCE level. A naive grep over the
    raw file can miss a phrase that's genuinely present at runtime just because the
    source happens to wrap the literal across two lines in one location and not
    another (confirmed 2026-08-09: this produced a false positive on the very first
    real run of this checker). Collapse '"<whitespace incl. newline><indent>"' down
    to nothing, simulating what Python's parser does, before searching."""
    return re.sub(r'"\s*\n\s*"', '', text)


def check():
    raw = ORCH_FILE.read_text(encoding="utf-8")
    text = _flatten_adjacent_string_literals(raw)
    problems = []
    for rule_id, (phrase, expected_min, where) in EXPECTED_OCCURRENCES.items():
        # Case-insensitive: the same term legitimately appears capitalized in one
        # rendering style ('Priority locations' -> ...) and lowercase mid-list in
        # another (..., platform upgrades, priority locations.) -- confirmed
        # 2026-08-09, both are the registry's real content, not drift.
        actual = len(re.findall(re.escape(phrase), text, re.IGNORECASE))
        if actual < expected_min:
            problems.append(
                f"[DRIFT] {rule_id}: found {actual}/{expected_min} occurrences of "
                f"{phrase!r}. Expected in: {where}."
            )
    if problems:
        print("Rule drift detected:\n")
        for p in problems:
            print(p)
        print(
            "\nThis means a fix that should be in multiple hand-copied locations is "
            "missing from at least one. Cross-reference automation/style_rules.py for "
            "the canonical text and patch the missing location(s) by hand — see "
            "commit history around 2026-08-09 for the pattern (the same fix applied "
            "identically across all copies in one commit)."
        )
        return 1
    print(f"No drift found — checked {len(EXPECTED_OCCURRENCES)} known fix(es) against {ORCH_FILE.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(check())

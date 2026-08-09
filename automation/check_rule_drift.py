#!/usr/bin/env python3
"""
check_rule_drift.py — catches the exact failure mode found 2026-08-09: a rule fix
applied to one hand-copied location and missed in the others.

This does NOT replace style_rules.py wiring into the actual prompts (that's a
separate, higher-risk migration, tracked as an ongoing /loop task — see
.claude/bregman-anchor-corpus.md Section 5 and this file's own git log for why a
big-bang prompt rewrite was deliberately deferred). This is a read-only linter:
it checks that the CONTENT of style_rules.py's canonical rule text is actually
present, verbatim, everywhere it currently needs to be — the same kind of check
a human did by hand on 2026-08-09 to find the jargon-wordlist and metaphor-
exemption drift.

Scans production_orchestrator.py AND every automation/orchestrator/*.py mixin
module (updated 2026-08-09 when the module-split extraction moved GATE_SYSTEM
out of production_orchestrator.py into orchestrator/gate.py — a rule-text
location moving files is not the same as it disappearing, and this checker
would have false-alarmed on every future extraction if it only ever looked at
the original monolith).

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

AUTOMATION_DIR = Path(__file__).parent
ORCH_FILE = AUTOMATION_DIR / "production_orchestrator.py"
SCANNED_FILES = [ORCH_FILE] + sorted((AUTOMATION_DIR / "orchestrator").glob("*.py"))

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
    "nominalization-distance-exemption": (
        "'evidence', 'silence', 'distance', 'argument', 'environment'",
        2,
        "_pre_commit_gate's GATE_SYSTEM R4 (already had 'distance', canonical — "
        "matches style_rules.py's nominalization exemptions) and validate_article's "
        "RULES_SYSTEM R4 (found missing 'distance' — 8 of 9 exempted nouns — during "
        "the 2026-08-09 /loop convergence pass and fixed to match). Confirmed count "
        "of 2 via _flatten_adjacent_string_literals; a naive raw-text search "
        "undercounts to 1 because GATE_SYSTEM wraps this exact phrase across two "
        "adjacent string literals at the source level.",
    ),
    "system-voice-gate-coverage": (
        "If the sentence could appear in the audit report the article is criticising, it has failed",
        3,
        "gate GATE_SYSTEM R17 (added — was completely absent from the blocking gate "
        "before this fix, a real 2026-08-09 /loop finding: style_rules.py's own "
        "'system-voice' rule rationale field already documented this exact gap and "
        "said 'Moved to BLOCKING here', but the actual GATE_SYSTEM prompt text was "
        "never updated to match), validate_article's RULES_SYSTEM R5 (converged from "
        "a terse one-liner to match), and the writer generation prompt (already had "
        "this exact wording — confirmed, not touched).",
    ),
    "meta-language-commentary-wired": (
        "The word rolling appeared twice, both times as praise",
        2,
        "validate_article's RULES_SYSTEM R18 (added — this rule existed ONLY in "
        "style_rules.py's registry with zero wiring anywhere in the actual "
        "pipeline, despite being tagged stages={REVIEW, GENERATE}) and the writer "
        "generation prompt (added). Not added to the blocking gate — registry "
        "severity is ADVISORY, not BLOCKING, so this convergence matches the "
        "registry's own stated intent rather than promoting it.",
    ),
    "stacked-temporal-clauses-wired": (
        "after I'd checked my tire pressure and before I'd finished the plantains",
        2,
        "validate_article's RULES_SYSTEM R19 (added) and the writer generation "
        "prompt (added) — same gap and same reasoning as "
        "meta-language-commentary-wired above; both rules were registry-only "
        "with zero real wiring until this fix.",
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
    # Concatenated across all scanned files, not per-file — a rule's canonical
    # phrase can legitimately live in production_orchestrator.py AND a mixin
    # module post-extraction; EXPECTED_OCCURRENCES counts total occurrences
    # across the whole codebase, not occurrences-per-file.
    text = "".join(
        _flatten_adjacent_string_literals(f.read_text(encoding="utf-8"))
        for f in SCANNED_FILES
    )
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
    print(
        f"No drift found — checked {len(EXPECTED_OCCURRENCES)} known fix(es) against "
        f"{len(SCANNED_FILES)} file(s): {', '.join(f.name for f in SCANNED_FILES)}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(check())

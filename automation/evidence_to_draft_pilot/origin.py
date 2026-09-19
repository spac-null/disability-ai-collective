"""
origin.py -- where did each reported defect actually come from? (Task 3)

Section 9 of the brief and Task 3 of the completion pass ask the same question in two
places: for a reported failure, find the EARLIEST actual text containing it, rather than
inferring its origin from the gate that reported it.

Here that is answerable deterministically, because arms A and B start from the SAME
Writer bytes. A reviewer's factual objection carries an exact article span. So:

    the span is present in the pre-edit Writer draft   -> WRITER
    present only in A                                  -> CURRENT_EDITING
    present only in B                                  -> GUARDED_EDITING
    present in neither, under normalisation            -> UNRESOLVED

No model is asked to adjudicate this and no judgement is involved: it is substring
presence over three texts the pilot already holds.

MATCHING. `composition.normalize_span` is production's own normaliser -- whitespace,
quote and dash shape, and the space markup leaves before punctuation. It can remove no
word and reorder nothing, so a normalised match is still the same words in the same
order. A reviewer quoting loosely (an ellipsis, a truncated tail) will not match, and
that case is reported as UNRESOLVED rather than guessed at; a fuzzy match here would
manufacture exactly the false attribution this module exists to prevent.

WHAT THIS DOES NOT DECIDE. Whether the objection is correct. A reviewer can quote a real
span and be wrong about it; that is what `DETECTOR_FALSE_POSITIVE` is for, and only the
owner can assign it. This module says WHERE a span came from, never whether the
complaint about it is justified.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import composition as CP                        # noqa: E402

WRITER = "WRITER"
CURRENT_EDITING = "CURRENT_EDITING"
GUARDED_EDITING = "GUARDED_EDITING"
PLAN_OR_EVIDENCE = "PLAN_OR_EVIDENCE"
DETECTOR_FALSE_POSITIVE = "DETECTOR_FALSE_POSITIVE"
UNRESOLVED = "UNRESOLVED"

ORIGINS = (WRITER, CURRENT_EDITING, GUARDED_EDITING, PLAN_OR_EVIDENCE,
           DETECTOR_FALSE_POSITIVE, UNRESOLVED)


def classify_span(span: str, *, draft: str, a_text: str, b_text: str) -> str:
    """Earliest text containing this span. Presence only; no judgement."""
    if not span or not span.strip():
        return UNRESOLVED
    if CP.span_in(span, draft or ""):
        return WRITER
    in_a = CP.span_in(span, a_text or "")
    in_b = CP.span_in(span, b_text or "")
    if in_a and not in_b:
        return CURRENT_EDITING
    if in_b and not in_a:
        return GUARDED_EDITING
    if in_a and in_b:
        # Present in both post-edit texts but not the draft. Both arms edited the same
        # sentence into the same shape, or the draft wording differs only outside this
        # module's normalisation. Not attributable to one arm.
        return UNRESOLVED
    return UNRESOLVED


def objections_of(review: dict, arm: str) -> list:
    """Every located factual objection a reviewer raised against one arm."""
    v = ((review or {}).get("by_arm") or {}).get(arm) or {}
    out = []
    for c in v.get("located_material_objections") or []:
        out.append({"kind": "material_unsupported_claim",
                    "span": c.get("article_span"), "why": c.get("why"),
                    "source_passage": c.get("source_passage")})
    for k, kind in (("attribution_or_qualifier_losses", "attribution_or_qualifier_loss"),
                    ("quotation_problems", "quotation_change"),
                    ("relationship_problems", "relation_change")):
        for c in v.get(k) or []:
            out.append({"kind": kind, "span": c.get("article_span"),
                        "why": c.get("why"), "source_passage": None})
    return out


def classify_subject(*, draft: str, a_text: str, b_text: str,
                     reviews: dict) -> dict:
    """All reviewers x both arms, with per-origin counts and the findings themselves."""
    findings, counts = [], {o: 0 for o in ORIGINS}
    for who, review in reviews.items():
        for arm in ("A", "B"):
            for ob in objections_of(review, arm):
                origin = classify_span(ob["span"], draft=draft, a_text=a_text,
                                       b_text=b_text)
                counts[origin] += 1
                findings.append(dict(ob, reviewer=who, arm=arm, origin=origin))

    # THE PRODUCTION QUESTION, stated as its own number: how many reported problems
    # appeared only AFTER the Writer draft, and which editing strategy produced them.
    introduced = {
        "by_current_editing": counts[CURRENT_EDITING],
        "by_guarded_editing": counts[GUARDED_EDITING],
        "inherited_from_writer": counts[WRITER],
        "unresolved": counts[UNRESOLVED],
    }
    return {"counts": counts, "introduced": introduced, "findings": findings,
            "note": "Origin is substring presence across the pre-edit draft and the two "
                    "variants, under composition.normalize_span. It says where a span "
                    "came from, never whether the objection to it is correct."}

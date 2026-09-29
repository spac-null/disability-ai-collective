"""Joins between frozen facts, licensed the way the facts themselves are.

WHY THIS EXISTS, AND IT IS NOT A STYLE FEATURE.

An essay is a set of ASSERTED RELATIONS between facts. "This happened, and therefore
that" -- the facts are often ordinary and the joins are the argument. A report is the
same facts with the joins removed.

This engine freezes PROPOSITIONS and licenses nothing else. The Writer may state a
licensed fact and may not assert a relation the evidence does not carry. A writer
permitted only to state facts and never to join them can only produce a report: not as a
style failure, as the only thing structurally available to it.

That is measured, not supposed. The owner's most-pressed reaction across ten reading
sessions is SOUNDS_LIKE_REPORT, seven times, ahead of LIST_OF_FACTS at four and NO_STORY
at three. And on 2026-09-29 the same unlicensed join came back through five independent
controls -- a plan that asserted it, a plan that forbade it, a plan that omitted it, a
plan whose facts were cut, and a changed writer system. It kept returning because the
Writer was reaching for an argument in a system that licenses only a report.

So the fix is not looser fact gates, which give fabrication, and not another instruction,
which the engine already has forty-five of. It is that a JOIN CAN BE EVIDENCE TOO.

WHAT A LICENSED RELATION IS

    {"relation_id": "R01",
     "subject": "F12", "object": "F18",      both must exist in the ledger
     "kind": "CAUSE",                        one of RELATION_KINDS
     "evidence_ids": ["S5"],                 the source the span is FROM
     "support_span": "..."}                  VERBATIM from a cited source

It gets exactly the guarantee a fact gets and no more: the span is real source text, it
comes from a source the relation cites, and both endpoints exist. Whether the span
genuinely asserts THAT join between THOSE two facts is the freezing model's judgement,
the same way the faithfulness of a proposition to its span is. This module does not
pretend to verify entailment; it refuses everything it can refuse deterministically.

WHAT IT DELIBERATELY DOES NOT DO

It does not infer relations. Nothing here reads two propositions and decides they are
connected -- that is precisely the invention the engine spent the day blocking. A
relation exists only when a source says so and the span proves the source said it.

THE OWNER'S OWN FORMULATION, 2026-09-25, which this implements:

    "Planning decides what the story is trying to do.
     Evidence decides what the story is allowed to claim while doing it."
"""

from __future__ import annotations

import re

from . import story as ST

# Reused, not invented: these are the classes `turn_relations` already detects, so a
# licensed relation and a detected one speak the same vocabulary and can be compared.
RELATION_KINDS = tuple(k for k, _ in ST.TURN_RELATION_SHAPES)

RELATION_ID = re.compile(r"^R\d{2,}$")

# The shortest span that can carry a join. Below this a "span" is a fragment that cannot
# be checked against anything, and the check would pass by accident.
MIN_SPAN_CHARS = 25


def _norm(text: str) -> str:
    return " ".join(str(text or "").split())


def validate_relations(relations, ledger: dict, srcs: dict) -> dict:
    """{relation_id: [failures]} for the relations that are not usable.

    Mirrors check_ledger's shape deliberately: same failure-per-id dict, same
    span-binding rule -- the span must appear in a source the relation CITES, not merely
    somewhere in the corpus. A span quoted from S1 and attributed to S5 is a provenance
    error, and it is the one this engine has been bitten by before.
    """
    failures: dict[str, list] = {}

    def add(rid, msg):
        failures.setdefault(rid, []).append(msg)

    seen = set()
    for r in (relations or []):
        if not isinstance(r, dict):
            add("<relations>", "a relation is not an object: %r" % (r,))
            continue
        rid = str(r.get("relation_id") or "")
        if not RELATION_ID.match(rid):
            add(rid or "<relations>", "relation_id must look like R01, got %r" % rid)
            continue
        if rid in seen:
            add(rid, "duplicate relation_id")
            continue
        seen.add(rid)

        for end in ("subject", "object"):
            fid = str(r.get(end) or "")
            if fid not in ledger:
                add(rid, "%s %r is not a fact in this ledger" % (end, fid))
        if r.get("subject") and r.get("subject") == r.get("object"):
            add(rid, "subject and object are the same fact")

        kind = r.get("kind")
        if kind not in RELATION_KINDS:
            add(rid, "kind %r is not one of %s" % (kind, ", ".join(RELATION_KINDS)))

        cited = [s for s in (r.get("evidence_ids") or []) if s]
        if not cited:
            add(rid, "cites no source")
        unknown = [s for s in cited if s not in srcs]
        if unknown:
            add(rid, "cites sources that are not in the pack: %s" % sorted(unknown))

        span = _norm(r.get("support_span"))
        if len(span) < MIN_SPAN_CHARS:
            add(rid, "support_span is too short to carry a join (%d chars, floor %d)"
                % (len(span), MIN_SPAN_CHARS))
            continue
        # SPAN BINDING, to the CITED source only.
        if not any(span in _norm(srcs.get(s, "")) for s in cited if s in srcs):
            elsewhere = [s for s, t in srcs.items() if span in _norm(t)]
            add(rid, "support_span is not in the source(s) it cites%s"
                % ("; it appears in %s" % sorted(elsewhere) if elsewhere else ""))
    return failures


def usable(relations, ledger: dict, srcs: dict) -> list:
    """The relations that pass. Rejected ones are dropped, never repaired here.

    Same direction as the ledger's own rule: a relation that cannot be supported is
    refused, and the run continues without it. A story that needed it will fail later, in
    a stage that can say so about the article rather than about the evidence.
    """
    bad = validate_relations(relations, ledger, srcs)
    return [r for r in (relations or [])
            if isinstance(r, dict) and str(r.get("relation_id") or "") not in bad
            and RELATION_ID.match(str(r.get("relation_id") or ""))]


def for_facts(relations, fact_ids) -> list:
    """Relations whose BOTH endpoints are in `fact_ids`.

    Both, not either: a join to a fact the Writer was not given is not a join the Writer
    can make, and showing it would be an invitation to reach for material outside the
    packet.
    """
    want = set(fact_ids or ())
    return [r for r in (relations or [])
            if r.get("subject") in want and r.get("object") in want]


def render(relations, ledger: dict) -> str:
    """The block the Writer sees. Propositions, not ids: ids are machine identity.

    Phrased as a permission rather than an instruction. The engine's measured failure mode
    is instruction accumulation -- forty-five imperatives in the writer system -- so this
    says what MAY be joined and leaves whether to join it to the writing.
    """
    if not relations:
        return ""
    lines = ["JOINS YOU MAY ASSERT",
             "  These connections are carried by the evidence, not by you. You may state",
             "  any of them outright, in your own words. You may also leave one unused.",
             "  Any OTHER connection between facts is yours to imply at most, never to",
             "  assert: place the material and let the reader draw it."]
    for r in relations:
        subj = (ledger.get(r.get("subject")) or {}).get("proposition") or r.get("subject")
        obj = (ledger.get(r.get("object")) or {}).get("proposition") or r.get("object")
        lines.append("  - %s" % str(subj)[:150])
        lines.append("    %s" % str(r.get("kind") or "").lower().replace("_", " "))
        lines.append("    %s" % str(obj)[:150])
    return "\n".join(lines)

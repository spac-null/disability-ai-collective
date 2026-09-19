#!/usr/bin/env python3
"""
c21_semantic_audit.py -- audit the EXPLANATION of C2.1's failures, not the plans.

The operational result is FROZEN and unchanged: 0 of 6 C2.1 plans passed the unchanged
production validator, and no C2.1 article exists. Nothing here reruns, patches,
regenerates or retrospectively accepts a plan, and no production validator is modified.

WHAT IS BEING CORRECTED. Evaluation v1 reported "unsupported relational strengthening in
5 of 6" as though the validator's keyword trigger were itself a semantic finding. A
trigger word proves a RELATION WAS ASSERTED. It does not prove the assertion is about the
world, nor that the frozen evidence fails to carry it. Those are separate questions and
v1 never asked them.

Each complaint is classified as exactly one of:

  SCHEMA_FAILURE                      a contract/shape violation, no factual claim at issue
  EVIDENCE_RELATION_VIOLATION         a relation ABOUT THE WORLD that the Ledger does not carry
  EDITORIAL_INTERPRETATION            a claim about an interpretation's merits, not a
                                      worldly ranking -- its premises still need support
  LEXICAL_OR_NORMALIZATION_FALSE_POSITIVE  the trigger fired on a form, not a claim
  UNRESOLVED                          cannot be settled from the stored artefacts

An EDITORIAL_INTERPRETATION is NOT thereby valid: "best understood" still needs supported
premises. The classification separates WHY a plan was refused from WHETHER its content
was invented.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import story as ST                              # noqa: E402

V1 = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                  "evidence-to-draft-pilot")
OUT = pathlib.Path("/srv/data/cripminds-new-engine-v1/experiments/"
                   "evidence-to-draft-pilot-audit-v2")

SCHEMA = "SCHEMA_FAILURE"
EVIDENCE = "EVIDENCE_RELATION_VIOLATION"
EDITORIAL = "EDITORIAL_INTERPRETATION"
LEXICAL = "LEXICAL_OR_NORMALIZATION_FALSE_POSITIVE"
# The relation IS in the frozen evidence -- just not in the facts the plan declared as
# licensing it. The plan under-cited its own basis. That is a real contract failure and
# the refusal is correct, but the validator's MESSAGE ("the relation is the turn's own
# invention") is not: nothing was invented.
BASIS_UNDER_CITED = "RELATION_CARRIED_BY_EVIDENCE_BUT_NOT_BY_CITED_BASIS"
UNRESOLVED = "UNRESOLVED"

# A relation trigger inside these frames is a claim about how to READ the material, not a
# claim that one worldly thing exceeds another. "The theft is best understood through the
# security arrangements" ranks explanations; "the largest theft in Italian history" ranks
# events. The production validator's lexical channel cannot tell them apart.
_INTERPRETIVE_FRAME = re.compile(
    r"\b(?:best|better|most) (?:understood|read|seen|grasped|approached)\b"
    r"|\bis best (?:understood|read|seen)\b"
    r"|\bmakes (?:most|more) sense\b", re.I)


def classify(err: str, plan: dict, ledger: dict) -> dict:
    """One validator complaint -> one classification, with its evidence."""
    out = {"error": err, "classification": UNRESOLVED, "why": "", "evidence": {}}

    # ── entity minting: is the base name actually absent from the evidence? ──
    m = re.search(r"asserts entities no approved fact carries: \[(.+?)\]", err)
    if m:
        names = re.findall(r"[\"']([^\"']+)[\"']", m.group(1))
        blob = " ".join(
            (f.get("proposition") or "") + " " + (f.get("support_span") or "")
            for f in ledger.values() if isinstance(f, dict))
        details = {}
        for n in names:
            base = re.sub(r"[’']s$", "", n)
            details[n] = {"flagged_form": n, "base_name": base,
                          "base_present_in_ledger": base.lower() in blob.lower()}
        out["evidence"] = details
        if all(d["base_present_in_ledger"] for d in details.values()):
            out["classification"] = LEXICAL
            out["why"] = ("the flagged token is a POSSESSIVE of a name the frozen "
                          "evidence does carry; the entity channel reads the inflected "
                          "form as a new identity. This does not license every claim "
                          "made ABOUT that entity.")
        else:
            out["classification"] = EVIDENCE
            out["why"] = "the base name is absent from the frozen evidence"
        return out

    # ── turn relation: is the trigger ranking the world or a reading? ──
    m = re.search(r"(crip_turn|final_lens\.\w+) asserts (\w+) \('([^']+)'\)", err)
    if m:
        field, relation, trigger = m.group(1), m.group(2), m.group(3)
        text = (plan.get(field) if "." not in field
                else (plan.get("final_lens") or {}).get(field.split(".")[1])) or ""
        out["evidence"] = {"field": field, "relation": relation, "trigger": trigger,
                           "text": text[:400]}
        if _INTERPRETIVE_FRAME.search(text):
            out["classification"] = EDITORIAL
            out["why"] = ("the trigger sits in an interpretive frame -- a claim about "
                          "which reading explains the material, not a ranking of "
                          "worldly things. Its PREMISES still require support; this is "
                          "not a finding that the claim is valid.")
            return out

        # DOES THE EVIDENCE CARRY THIS RELATION AT ALL? Section 9 asks for the premises
        # to be inspected, not only the trigger token. Production's own relation
        # detector is used, on the same field it reads: the fact's proposition.
        basis = ((plan.get("final_lens") or {}).get("evidence_basis")
                 or plan.get("use_facts") or [])
        cited_carry = sorted({f for f in basis
                              if relation in ST.turn_relations(
                                  (ledger.get(f) or {}).get("proposition") or "")})
        ledger_carry = sorted({f for f, fact in ledger.items()
                               if isinstance(fact, dict)
                               and relation in ST.turn_relations(
                                   fact.get("proposition") or "")})
        out["evidence"].update({
            "declared_basis": list(basis),
            "cited_facts_carrying_%s" % relation: cited_carry,
            "ledger_facts_carrying_%s" % relation: ledger_carry[:10],
            "ledger_facts_carrying_count": len(ledger_carry)})
        if cited_carry:
            out["classification"] = LEXICAL
            out["why"] = ("a cited fact (%s) does carry a %s relation, so the refusal "
                          "is a detector false positive" % (cited_carry[:3], relation))
        elif ledger_carry:
            out["classification"] = BASIS_UNDER_CITED
            out["why"] = ("the frozen evidence DOES carry this %s relation (%d facts, "
                          "e.g. %s) but the plan did not cite any of them as its lens "
                          "basis. The refusal is correct under the contract; the "
                          "validator's wording -- 'the relation is the turn\'s own "
                          "invention' -- is not. Nothing was invented; the basis was "
                          "under-declared."
                          % (relation, len(ledger_carry), ledger_carry[:3]))
        else:
            out["classification"] = EVIDENCE
            out["why"] = ("no fact anywhere in the frozen ledger carries a %s relation, "
                          "so the turn asserts one the evidence does not grant"
                          % relation)
        return out

    # ── final_lens shape complaints ──
    if "what_changes_for_the_reader does not describe a change" in err:
        fl = plan.get("final_lens") or {}
        txt = fl.get("what_changes_for_the_reader") or ""
        before, after = fl.get("before_reading") or "", fl.get("after_reading") or ""
        contrast = bool(re.search(r"\b(?:from|instead of|rather than|no longer|"
                                  r"previously|had (?:been|seemed)|now)\b", txt, re.I))
        out["evidence"] = {"what_changes_for_the_reader": txt[:300],
                           "before_reading": before[:160],
                           "after_reading": after[:160],
                           "contains_contrast_language": contrast,
                           "before_and_after_differ": before.strip() != after.strip()}
        out["classification"] = SCHEMA
        out["why"] = ("a shape/heuristic complaint about one field. The stored record "
                      "does%s carry contrast language and before_reading and "
                      "after_reading do%s differ, so this is a contract-heuristic "
                      "failure, not evidence of a fabricated relationship."
                      % ("" if contrast else " NOT",
                         "" if out["evidence"]["before_and_after_differ"] else " NOT"))
        return out

    if err.startswith("EVIDENCE_HIERARCHY") or err.startswith("FINAL_LENS") \
            or err.startswith("PACKET") or "cut reason" in err:
        out["classification"] = SCHEMA
        out["why"] = "a contract/shape rule; no claim about the world is at issue"
        return out

    if err.startswith("ARCHITECT_PROSE"):
        out["classification"] = UNRESOLVED
        out["why"] = "architect-prose complaint not matching the entity pattern"
        return out
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cells = V1 / "ledger" / "cells"
    man = json.loads((V1 / "EXPERIMENT_MANIFEST.json").read_text())
    report = {"evaluation_version": 2,
              "operational_result_unchanged": "0 of 6 C2.1 plans passed; no C article",
              "what_this_corrects": "the EXPLANATION of the failures, not the plans",
              "subjects": []}
    counts = {}
    for run in man["development_subjects"] + man["held_out_subjects"]:
        f = cells / ("%s_plan.json" % run)
        if not f.exists():
            continue
        cell = json.loads(f.read_text())
        r = cell.get("result") or {}
        if r.get("c_contract") != "C2.1-replanning-with-lens":
            continue
        plan = r.get("plan") or {}
        subj = json.loads((V1 / "subjects" / run / "SUBJECT.json").read_text())
        ledger = subj["generation_inputs"]["ledger"]
        rows = [classify(e, plan, ledger) for e in (r.get("architecture_errors") or [])]
        for row in rows:
            counts[row["classification"]] = counts.get(row["classification"], 0) + 1
        report["subjects"].append({
            "subject_id": run, "plan_status": r.get("status"),
            "beats": len(plan.get("beats") or []),
            "use_facts": len(plan.get("use_facts") or []),
            "cut_evidence": len(plan.get("cut_evidence") or []),
            "complaints": rows})
        print("=" * 76)
        print("%s  beats=%d use_facts=%d cuts=%d"
              % (run[-8:], len(plan.get("beats") or []),
                 len(plan.get("use_facts") or []),
                 len(plan.get("cut_evidence") or [])))
        for row in rows:
            print("  [%s] %s" % (row["classification"], row["error"][:104]))
            if row["why"]:
                print("        -> %s" % row["why"][:150])
    report["classification_counts"] = counts
    (OUT / "C21_FAILURE_CLASSIFICATION_V2.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False))
    print()
    print("CLASSIFICATION TOTALS:", json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())

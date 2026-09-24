"""obligation_policy.py -- which material a repair endangers, and must therefore oblige.

WRITTEN AND COMMITTED BEFORE THE COHORT RAN. That ordering is the whole point: this policy is
deterministic code with no model call, derived only from artifacts the pipeline already
produces -- the Claim Support Shadow's per-span statuses and the repair's own edit plan -- so
it cannot be fitted to results it has not seen. If it selects badly, that is the finding.

WHY THESE THREE RULES AND NOT OTHERS. Each one is a branch that already failed:

  O1 EXPLANATORY.  Branch B regenerated the definition freely and deleted
                   "the long-wavelength edge of what the detector material will register" --
                   a span the same shadow had marked NON_FACTUAL_OR_NOT_CHECKABLE, i.e.
                   explicitly not the defect. The article became "the wavelength specified for
                   the instrument". Explanatory material is the first thing a rewrite loses.

  O2 ADJACENT SUPPORTED.  What a rewrite swallows is what borders the thing it is rewriting.
                   In the bandgap gloss the destroyed clause sat immediately before the
                   flagged span, sharing one grammatical construction with it. Supported
                   material further away survived every branch untouched.

  O3 DISPLACED FACT.  Branch E forbade a relation and the Writer complied by dropping the
                   concept entirely; branch D had already moved that fact to another beat.
                   A fact the repair moves or removes is a fact nothing else is holding.

NOTHING ELSE. In particular NOT every SUPPORTED commitment and NOT every facts_allowed entry.
The failure mode that matters now is OVER-obligation: a Writer handed a checklist writes a
checklist, and Crip Minds prose dies. Obligations are for material the repair ENDANGERS, which
is a small set by construction -- most of a plan is nowhere near the edit.

A definition with no flagged commitment yields no obligations, no prohibition and no repair,
and costs no model call.
"""
from __future__ import annotations

from . import definition_repair_compiler as DRC

EXPLANATORY = "EXPLANATORY"
ADJACENT_SUPPORTED = "ADJACENT_SUPPORTED"
DISPLACED_FACT = "DISPLACED_FACT"

# Declared in advance, as a DIAGNOSTIC and not a tuning knob: if a policy obliges every
# commitment a definition makes, it has not selected anything. Exceeding this does not change
# what the policy emits -- it is reported as OVER_OBLIGATION so the cohort can be judged on it.
MAX_OBLIGATION_SHARE = 0.5


def select(ir: dict, target: dict, edit_plan: dict | None = None,
           ledger: dict | None = None) -> dict:
    """The obligation set for one flagged commitment. Deterministic; no model involved.

    `ir`        the definition partition from definition_repair_compiler.build_ir
    `target`    the one REPAIRABLE unit being repaired
    `edit_plan` the repair's own reply, read ONLY for facts it moved or removed
    """
    units = [u for u in ir.get("units", []) if u["role"] != DRC.GLUE]
    try:
        i = units.index(target)
    except ValueError:
        i = -1
    neighbours = set()
    if i >= 0:
        if i > 0:
            neighbours.add(units[i - 1]["unit_id"])
        if i + 1 < len(units):
            neighbours.add(units[i + 1]["unit_id"])

    obligations, seen = [], set()

    for u in units:
        if u["role"] != DRC.PROTECTED:
            continue
        why = None
        if u.get("status") == DRC.NON_FACTUAL:
            why = EXPLANATORY
        elif u.get("status") == DRC.SUPPORTED and u["unit_id"] in neighbours:
            why = ADJACENT_SUPPORTED
        if why and u["unit_id"] not in seen:
            seen.add(u["unit_id"])
            obligations.append({"id": u["unit_id"], "source": "definition", "why": why,
                                "must_realize": u["text"].strip()})

    for f in ((edit_plan or {}).get("facts") or []):
        if not isinstance(f, dict) or f.get("operation") not in ("MOVE", "REMOVE"):
            continue
        fid = str(f.get("fact_id"))
        prop = str(((ledger or {}).get(fid) or {}).get("proposition", "")).strip()
        if not prop or fid in seen:
            continue
        seen.add(fid)
        obligations.append({"id": fid, "source": "displaced_fact", "why": DISPLACED_FACT,
                            "evidence": [fid], "must_realize": prop})

    total = len([u for u in units]) + len([f for f in ((edit_plan or {}).get("facts") or [])
                                           if isinstance(f, dict)
                                           and f.get("operation") in ("MOVE", "REMOVE")])
    share = (len(obligations) / float(total)) if total else 0.0
    return {"obligations": obligations,
            "commitments_considered": total,
            "obligation_share": round(share, 3),
            "over_obligation": share > MAX_OBLIGATION_SHARE,
            "policy": "obligation-policy-v1"}


def architecture_field(selection: dict) -> list:
    """The `required_commitments` value, with ids and reasons stripped -- the Writer is handed
    sentences, never machine language."""
    return [{"id": o["id"], "evidence": o.get("evidence") or [],
             "must_realize": o["must_realize"]}
            for o in selection.get("obligations") or []]


def for_plan(arch: dict, ledger: dict, shadow: dict) -> list:
    """Every definition in a plan that would produce obligations, and what they would be.

    A clean definition appears NOWHERE in the result -- not as an empty entry. That is the
    positive control: no flagged commitment, no obligation, no prohibition, no call.
    """
    out = []
    defs = (arch or {}).get("definitions") or {}
    for d in (shadow or {}).get("definitions") or []:
        term = d.get("term")
        gloss = defs.get(term)
        if gloss is None:
            continue
        ir = DRC.build_ir(term, gloss, d.get("claims") or [])
        reps = [u for u in ir.get("units", []) if u["role"] == DRC.REPAIRABLE]
        if ir.get("anchoring") != "OK" or not reps:
            continue
        for t in reps:
            out.append({"term": term, "repairable": t["unit_id"], "flagged": t["text"],
                        "ir": ir, "selection": select(ir, t)})
    return out

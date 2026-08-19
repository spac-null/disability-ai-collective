#!/usr/bin/env python3
"""FINAL REPLAY repair-input builder. Carried verbatim from WG-6B/build_repair_inputs.py
except: (1) reads the CORRECTED router's pre-phase arbitration, (2) FAILCLASS is
extended for the synthesised NEGATIVE_SOURCE_CLAIM type and any unknown type,
declared in PRE-REGISTRATION.md before the run. Gold is never opened."""
import json, re, collections
from pathlib import Path

R = Path(__file__).resolve().parent.parent
I = R / "inputs"
ART = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}

FAILCLASS = {
    "PROPER_NOUN":       "UNSUPPORTED_PROPER_NOUN",
    "TEMPORAL_MODIFIER": "UNSUPPORTED_TEMPORAL_SPECIFICITY",
    "HUMAN_STATE":       "UNSUPPORTED_HUMAN_STATE",
    "QUANTIFIER":        "UNSUPPORTED_QUANTIFIER_SCOPE",
    "BASE_STATE":        "UNSUPPORTED_WORLD_STATE",
    "CAUSAL_RELATION":   "UNSUPPORTED_CAUSAL_CLAIM",
    "SOURCE_META":       "UNPROVEN_NEGATIVE_SOURCE_CLAIM",
    "NEGATIVE_SOURCE_CLAIM": "UNPROVEN_NEGATIVE_SOURCE_CLAIM",   # P3 synthesised unit
}
failclass = lambda t: FAILCLASS.get(t, "UNSUPPORTED_" + str(t))

arb = json.loads((R / "score" / "pre-ARBITRATION.json").read_text())["arbitrated"]
ex = {t: {p["ID"]: p for p in (lambda d: d["propositions"] if isinstance(d, dict) else d)(
      json.loads((R / "pre" / f"{t}-extract-raw.json").read_text()))} for t in ART}
text = {t: (I / f).read_text() for t, f in ART.items()}


def sentence_of(body, span):
    i = body.find(span)
    if i < 0:
        return None, 0
    n = body.count(span)
    start = 0
    for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z“"])|\n\n', body):
        if m.end() <= i:
            start = m.end()
        else:
            break
    rest = body[i + len(span):]
    m = re.search(r'[.!?](?=\s+[A-Z“"]|\s*\n\n|\s*$)', rest)
    end = i + len(span) + (m.end() if m else len(rest))
    return body[start:end].strip(), n


uns = [a for a in arb if a["arbitrated_verdict"] == "UNSUPPORTED"]
findings = collections.defaultdict(list)
for a in uns:
    tag = a["tag"]
    p = ex[tag][a["parent"]]
    span = p["EXACT_SPAN"]
    sent, occ = sentence_of(text[tag], span)
    assert sent is not None, f"span not found in article: {tag} {span!r}"
    n = len(findings[tag]) + 1
    findings[tag].append({
        "FINDING_ID": f"{tag.upper()}-F{n}",
        "EXACT_OFFENDING_SPAN": span,
        "SPAN_OCCURRENCES_IN_ARTICLE": occ,
        "ATOMIC_UNSUPPORTED_COMMITMENT": a["proposition"],
        "PARENT_SENTENCE": sent,
        "SOURCE_ANCHOR": p.get("SOURCE_ANCHOR") or "(none — extraction anchor empty)",
        "PROOF_STATE": ("NEGATIVE SOURCE CLAIM. Proof type NONE: no explicit statement in "
                        "the source and no bounded, enumerable region of the source can settle "
                        "it. Scope that would be required: " + str(a["wg4b_scope"]))
                       if a["class"] == "NEGATIVE_SOURCE" else
                       "ORDINARY FACTUAL COMMITMENT. Not supported by the anchor above.",
        "FAILURE_CLASS": failclass(a["commitment_type"]),
        "_detector_provenance": {"parent": a["parent"], "commitment": a["commitment_id"],
                                 "commitment_type": a["commitment_type"], "owner": a["owner"],
                                 "routing_path": a["routing_path"]},
    })

(R / "repair" / "REPAIR-INPUTS.json").write_text(json.dumps(dict(findings), indent=2, ensure_ascii=False))
for tag, fs in findings.items():
    print(f"=== {tag}: {len(fs)} findings ===")
    for f in fs:
        print(f'  {f["FINDING_ID"]} [{f["FAILURE_CLASS"]}] occ={f["SPAN_OCCURRENCES_IN_ARTICLE"]}')
        print(f'    span     : {f["EXACT_OFFENDING_SPAN"]}')
        print(f'    sentence : {f["PARENT_SENTENCE"][:200]}')
print(f"\ntotal findings: {sum(len(v) for v in findings.values())}")
print("gold opened: NO")

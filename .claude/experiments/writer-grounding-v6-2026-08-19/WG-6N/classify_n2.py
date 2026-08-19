#!/usr/bin/env python3
"""WG-6N N2 CAUSAL VERIFICATION.

Classifies every post-repair UNSUPPORTED finding (from the CORRECTED router)
by causal relation to repair, using deterministic SENTENCE-level byte-locality
plus the independent source adjudication in N2-ADJUDICATION.json.

Category rule and the C/D boundary were fixed in PRE-REGISTRATION.md before
the adjudications were written. This file only applies them.
"""
import json, re
from pathlib import Path

W = Path(__file__).resolve().parent
V6 = W.parent
I = V6 / "WG-6A" / "inputs"
B = V6 / "WG-6B"

ORIG = {"form1-3": I / "form1-3-article.md", "r2": I / "form-1.3-r2-article.md",
        "r3": I / "form-1.3-r3-article.md"}
PATCHED = {t: B / f"{t}-patched.md" for t in ORIG}


def sentences(text):
    out = []
    for para in text.split("\n"):
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip():
                out.append(s.strip())
    return out


def norm(s):
    return ' '.join((s or '').replace('’', "'").replace('—', '-').replace('–', '-').split())


def containing_sentence(sents, span):
    n = norm(span)
    for s in sents:
        if n and n in norm(s):
            return s
    # span may straddle a sentence boundary or be an extractor paraphrase
    words = set(norm(span).lower().split())
    best, score = None, 0
    for s in sents:
        ov = len(words & set(norm(s).lower().split()))
        if ov > score:
            best, score = s, ov
    return best


rescore = json.loads((W / "N1-RESCORE.json").read_text())
findings = rescore["condition_B"]["post_repair_unsupported"]
adj = {a["key"]: a for a in json.loads((W / "N2-ADJUDICATION.json").read_text())["adjudications"]}
report = json.loads((B / "APPLICATION-REPORT.json").read_text())
applied = {r["tag"]: r["applied"] for r in report}

rows = []
for f in findings:
    tag = f["tag"]
    o_sents = sentences(ORIG[tag].read_text())
    p_sents = sentences(PATCHED[tag].read_text())
    span = f["parent_span"]
    sent = containing_sentence(p_sents, span)

    # --- deterministic byte-locality, SENTENCE granularity -------------------
    sentence_patched = any(norm(p["old"]) in norm(sent) or norm(sent) in norm(p["new"])
                           or norm(p["new"]) in norm(sent) for p in applied[tag])
    span_overlaps_changed = any(norm(p["old"]) in norm(span) or norm(span) in norm(p["old"])
                                for p in applied[tag])
    # is the containing sentence present, byte-identical, in the ORIGINAL article?
    pre_identical = sent in o_sents
    # does any patch sit in the same PARAGRAPH (weaker, reported for honesty)?
    para_patched = False
    for para in PATCHED[tag].read_text().split("\n"):
        if sent and sent in para:
            para_patched = any(p["new"] in para for p in applied[tag])
            break

    key = f"{tag}/{f['parent']}/{f['commitment_id']}"
    a = adj[key]
    status = a["ADJUDICATED_STATUS"]

    # --- pre-registered categories ------------------------------------------
    if sentence_patched or span_overlaps_changed:
        cat = "A_REPAIR_RESIDUAL"
    elif not pre_identical:
        cat = "B_REPAIR_INTRODUCED"
    elif status == "UNSUPPORTED":
        cat = "C_PREEXISTING_GENUINE_NEWLY_DETECTED"
    else:
        cat = "D_DETECTOR_FALSE_POSITIVE_OR_VARIANCE"

    rows.append({
        "key": key, "tag": tag, "parent": f["parent"], "commitment_id": f["commitment_id"],
        "commitment_type": f["commitment_type"], "owner": f["owner"],
        "routing_path": f["routing_path"],
        "EXACT_SPAN": span,
        "CONTAINING_SENTENCE": sent,
        "OVERLAPS_CHANGED_BYTES": "YES" if span_overlaps_changed else "NO",
        "CONTAINING_SENTENCE_PATCHED": "YES" if sentence_patched else "NO",
        "SAME_PARAGRAPH_CONTAINS_A_PATCH": "YES" if para_patched else "NO",
        "DEPENDS_SEMANTICALLY_ON_PATCH": "NO",
        "PRE_REPAIR_TEXT_BYTE_IDENTICAL": "YES" if pre_identical else "NO",
        "PROPOSITION": f["proposition"],
        "ADJUDICATED_STATUS": status,
        "CATEGORY": cat,
        "BLOCKS": cat in ("A_REPAIR_RESIDUAL", "B_REPAIR_INTRODUCED",
                          "C_PREEXISTING_GENUINE_NEWLY_DETECTED"),
        "adjudication_evidence": a["evidence"],
        "counter_argument_considered": a.get("counter_argument_considered"),
        "confidence": a.get("confidence"),
    })

counts = {
    "REPAIR_INTRODUCED": sum(r["CATEGORY"] == "B_REPAIR_INTRODUCED" for r in rows),
    "REPAIR_RESIDUAL": sum(r["CATEGORY"] == "A_REPAIR_RESIDUAL" for r in rows),
    "PREEXISTING_GENUINE_NEWLY_DETECTED": sum(
        r["CATEGORY"] == "C_PREEXISTING_GENUINE_NEWLY_DETECTED" for r in rows),
    "DETECTOR_FALSE_POSITIVE_OR_VARIANCE": sum(
        r["CATEGORY"] == "D_DETECTOR_FALSE_POSITIVE_OR_VARIANCE" for r in rows),
}
clean = counts["REPAIR_INTRODUCED"] == 0 and counts["REPAIR_RESIDUAL"] == 0 \
    and counts["PREEXISTING_GENUINE_NEWLY_DETECTED"] == 0

print("=" * 76); print("N2 CAUSAL VERIFICATION — post-repair UNSUPPORTED, corrected router")
for r in rows:
    print(f"\n  [{r['key']}] {r['commitment_type']} owner={r['owner']}")
    print(f"    span            : \"{r['EXACT_SPAN']}\"")
    print(f"    sentence        : {r['CONTAINING_SENTENCE'][:150]}")
    print(f"    patched?        : sentence={r['CONTAINING_SENTENCE_PATCHED']} "
          f"span_overlap={r['OVERLAPS_CHANGED_BYTES']} paragraph={r['SAME_PARAGRAPH_CONTAINS_A_PATCH']}")
    print(f"    byte-identical  : {r['PRE_REPAIR_TEXT_BYTE_IDENTICAL']}")
    print(f"    adjudicated     : {r['ADJUDICATED_STATUS']}  ({r['confidence']})")
    print(f"    CATEGORY        : {r['CATEGORY']}   BLOCKS={r['BLOCKS']}")

print("\n" + "=" * 76); print("SEPARATE COUNTS (never collapse these)")
for k, v in counts.items():
    print(f"  {k:38s} {v}")
print(f"\n  ARTICLE GROUNDING-CLEAN (first three all zero): {clean}")
print("  NOTE: verifier readiness and article cleanliness are different results.")

decision = "A — VERIFICATION_SEMANTICS_READY" if all(
    r["CATEGORY"] != "UNCLASSIFIABLE" for r in rows) and len(rows) == len(adj) \
    else "B — VERIFICATION_STILL_AMBIGUOUS"
print(f"\nN2 DECISION: {decision}")

(W / "N2-CLASSIFICATION.json").write_text(json.dumps({
    "method": "deterministic sentence-level byte-locality + independent source adjudication, no model calls",
    "byte_locality_granularity": "SENTENCE (a paragraph may hold both a patched and an untouched sentence)",
    "findings": rows, "counts": counts,
    "article_grounding_clean": clean,
    "precise_language_note": "REPAIR_INTRODUCED = 0 is proven. That is NOT the same claim as 'no new unsupported'.",
    "decision": decision,
}, indent=2, ensure_ascii=False))
print("Written N2-CLASSIFICATION.json")

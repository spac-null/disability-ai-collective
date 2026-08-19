#!/usr/bin/env python3
"""FINAL REPLAY GATE 2 — post-repair verification.

(1) gold V2.1 UNSUPPORTED remaining, by the span-containment rule carried
    verbatim from WG-6B/postaudit/score_postaudit.py
(2) WG-6N N2 causal classification of every post-repair UNSUPPORTED finding:
    sentence-level byte-locality + independent source adjudication
(3) gold UNCERTAIN / reclassified-INTERPRETATION items untouched by patches

Category rule fixed in PRE-REGISTRATION.md before the run. This applies it.
"""
import json, re
from pathlib import Path

R = Path(__file__).resolve().parent.parent
I = R / "inputs"
TAGS = {"FORM-1.3": "form1-3", "FORM-1.3-R2": "r2", "FORM-1.3-R3": "r3"}
ORIG = {"form1-3": I / "form1-3-article.md", "r2": I / "form-1.3-r2-article.md",
        "r3": I / "form-1.3-r3-article.md"}
PATCHED = {t: R / "repair" / f"{t}-patched.md" for t in ORIG}


def sentences(text):
    out = []
    for para in text.split("\n"):
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip():
                out.append(s.strip())
    return out


def norm(s):
    return ' '.join((s or '').replace('’', "'").replace('—', '-').replace('–', '-').split())


def gnorm(s):
    return ' '.join((s or '').lower().replace('’', "'").replace('—', '-').replace('–', '-').split())


def containing_sentence(sents, span):
    n = norm(span)
    for s in sents:
        if n and n in norm(s):
            return s
    words = set(norm(span).lower().split())
    best, score = None, 0
    for s in sents:
        ov = len(words & set(norm(s).lower().split()))
        if ov > score:
            best, score = s, ov
    return best


gold = json.loads((I / "gold-ledger-V2.1-FROZEN.json").read_text())
findings_gold = {f["id"]: (art, f) for art, a in gold["articles"].items()
                 for f in a["unsupported_findings"]}
arb = json.loads((R / "score" / "post-ARBITRATION.json").read_text())["arbitrated"]
uns = [a for a in arb if a["arbitrated_verdict"] == "UNSUPPORTED"]
report = {r["tag"]: r for r in json.loads((R / "repair" / "APPLICATION-REPORT.json").read_text())}
applied = {t: r.get("applied", []) for t, r in report.items()}

adjfile = R / "score" / "N2-ADJUDICATION.json"
adj = {a["key"]: a for a in json.loads(adjfile.read_text())["adjudications"]} if adjfile.exists() else {}

# ---- (1) gold unsupported remaining ----------------------------------------
gold_remaining, new_uns = [], []
for a in uns:
    ps = gnorm(a["parent_span"]); pw = set(ps.split())
    hit = None
    for gid, (art, f) in findings_gold.items():
        if TAGS[art] != a["tag"]:
            continue
        gs = gnorm(f["span"]); gw = set(gs.split())
        if ps and (ps in gs or gs in ps or len(gw & pw) >= max(3, int(.4 * len(gw)))):
            hit = gid; break
    (gold_remaining if hit else new_uns).append({**a, "gold_id": hit})

# ---- (2) causal classification ---------------------------------------------
rows = []
for f in uns:
    tag = f["tag"]
    o_sents = sentences(ORIG[tag].read_text())
    p_sents = sentences(PATCHED[tag].read_text())
    span = f["parent_span"]
    sent = containing_sentence(p_sents, span)
    sentence_patched = any(norm(p["old"]) in norm(sent) or norm(sent) in norm(p["new"])
                           or norm(p["new"]) in norm(sent) for p in applied[tag])
    span_overlaps = any(norm(p["old"]) in norm(span) or norm(span) in norm(p["old"])
                        for p in applied[tag])
    pre_identical = sent in o_sents
    para_patched = False
    for para in PATCHED[tag].read_text().split("\n"):
        if sent and sent in para:
            para_patched = any(p["new"] and p["new"] in para for p in applied[tag])
            break

    key = f"{tag}/{f['parent']}/{f['commitment_id']}"
    a = adj.get(key)
    status = a["ADJUDICATED_STATUS"] if a else "NOT_YET_ADJUDICATED"
    if sentence_patched or span_overlaps:
        cat = "A_REPAIR_RESIDUAL"
    elif not pre_identical:
        cat = "B_REPAIR_INTRODUCED"
    elif status == "UNSUPPORTED":
        cat = "C_PREEXISTING_GENUINE_NEWLY_DETECTED"
    elif status == "NOT_YET_ADJUDICATED":
        cat = "UNCLASSIFIABLE_PENDING_ADJUDICATION"
    else:
        cat = "D_DETECTOR_FALSE_POSITIVE_OR_VARIANCE"
    rows.append({
        "key": key, "tag": tag, "parent": f["parent"], "commitment_id": f["commitment_id"],
        "commitment_type": f["commitment_type"], "owner": f["owner"],
        "routing_path": f["routing_path"],
        "EXACT_SPAN": span, "CONTAINING_SENTENCE": sent,
        "OVERLAPS_CHANGED_BYTES": "YES" if span_overlaps else "NO",
        "CONTAINING_SENTENCE_PATCHED": "YES" if sentence_patched else "NO",
        "SAME_PARAGRAPH_CONTAINS_A_PATCH": "YES" if para_patched else "NO",
        "DEPENDS_SEMANTICALLY_ON_PATCH": "YES" if (sentence_patched or span_overlaps) else "NO",
        "PRE_REPAIR_TEXT_BYTE_IDENTICAL": "YES" if pre_identical else "NO",
        "PROPOSITION": f["proposition"], "DETECTOR_REASON": f.get("reason"),
        "ADJUDICATED_STATUS": status, "CATEGORY": cat,
        "BLOCKS": cat in ("A_REPAIR_RESIDUAL", "B_REPAIR_INTRODUCED",
                          "C_PREEXISTING_GENUINE_NEWLY_DETECTED",
                          "UNCLASSIFIABLE_PENDING_ADJUDICATION"),
        "adjudication_evidence": a["evidence"] if a else None,
        "confidence": a.get("confidence") if a else None,
    })

counts = {
    "REPAIR_INTRODUCED": sum(r["CATEGORY"] == "B_REPAIR_INTRODUCED" for r in rows),
    "REPAIR_RESIDUAL": sum(r["CATEGORY"] == "A_REPAIR_RESIDUAL" for r in rows),
    "PREEXISTING_GENUINE_NEWLY_DETECTED": sum(
        r["CATEGORY"] == "C_PREEXISTING_GENUINE_NEWLY_DETECTED" for r in rows),
    "DETECTOR_FALSE_POSITIVE_OR_VARIANCE": sum(
        r["CATEGORY"] == "D_DETECTOR_FALSE_POSITIVE_OR_VARIANCE" for r in rows),
    "UNCLASSIFIABLE_PENDING_ADJUDICATION": sum(
        r["CATEGORY"] == "UNCLASSIFIABLE_PENDING_ADJUDICATION" for r in rows),
}

# ---- (3) protected items untouched by patches -------------------------------
protected = []
for u in gold["articles"]["FORM-1.3-R2"]["uncertain_findings"]:
    touched = any(u["span"] in p["old"] or p["old"] in u["span"] for p in applied["r2"])
    protected.append({"kind": "UNCERTAIN", "span": u["span"], "patched": touched})
for e in gold["reclassified_to_interpretation_v2"]:
    tag = TAGS[e["article"]]
    touched = any(e["span"] in p["old"] or p["old"] in e["span"] for p in applied[tag])
    protected.append({"kind": "RECLASSIFIED_INTERPRETATION", "id": e["id"], "tag": tag,
                      "span": e["span"], "patched": touched})

clean = (counts["REPAIR_INTRODUCED"] == 0 and counts["REPAIR_RESIDUAL"] == 0
         and counts["PREEXISTING_GENUINE_NEWLY_DETECTED"] == 0
         and counts["UNCLASSIFIABLE_PENDING_ADJUDICATION"] == 0)
gate2 = clean and len(gold_remaining) == 0 and not any(p["patched"] for p in protected)

print("=" * 78); print("GATE 2 — POST-REPAIR VERIFICATION")
print(f"  post-repair UNSUPPORTED total : {len(uns)}")
print(f"  gold V2.1 UNSUPPORTED remaining: {len(gold_remaining)} "
      f"{[g['gold_id'] for g in gold_remaining]}")
for r in rows:
    print(f"\n  [{r['key']}] {r['commitment_type']} owner={r['owner']} path={r['routing_path']}")
    print(f"    span      : \"{r['EXACT_SPAN']}\"")
    print(f"    sentence  : {str(r['CONTAINING_SENTENCE'])[:150]}")
    print(f"    commitment: {r['PROPOSITION']}")
    print(f"    patched?  : sentence={r['CONTAINING_SENTENCE_PATCHED']} span={r['OVERLAPS_CHANGED_BYTES']} "
          f"para={r['SAME_PARAGRAPH_CONTAINS_A_PATCH']}  byte-identical={r['PRE_REPAIR_TEXT_BYTE_IDENTICAL']}")
    print(f"    adjudicated: {r['ADJUDICATED_STATUS']}   CATEGORY {r['CATEGORY']}  BLOCKS={r['BLOCKS']}")

print("\n" + "=" * 78); print("SEPARATE COUNTS (never collapse these)")
for k, v in counts.items():
    print(f"  {k:40s} {v}")
print("\n  protected items:")
for p in protected:
    print(f"    {p['kind']:28s} patched={p['patched']}  \"{p['span'][:60]}\"")
print(f"\n  GATE 2: {'PASS' if gate2 else 'FAIL'}")

(R / "score" / "GATE2-POST-REPAIR-VERIFICATION.json").write_text(json.dumps({
    "gate": "GATE 2 — post-repair verification",
    "byte_locality_granularity": "SENTENCE",
    "post_repair_unsupported_total": len(uns),
    "gold_unsupported_remaining": len(gold_remaining),
    "gold_unsupported_remaining_detail": gold_remaining,
    "findings": rows, "counts": counts,
    "protected_items": protected,
    "article_grounding_clean": clean, "gate2_pass": gate2,
    "precise_language_note": "REPAIR_INTRODUCED = 0 is not the same claim as 'no new unsupported'.",
}, indent=2, ensure_ascii=False))
print("Written score/GATE2-POST-REPAIR-VERIFICATION.json")

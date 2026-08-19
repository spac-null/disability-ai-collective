#!/usr/bin/env python3
"""WG-6B deterministic fail-closed patcher. WG-0B/WG-5 principles verbatim
(exact OLD_TEXT match, no ambiguity, no overlap, no change outside approved spans)
PLUS the WG-6B containment assertion: each patch's OLD_TEXT must lie inside the
PARENT_SENTENCE of the finding it clears, since WG-6B grants repair a bounded
licence to widen beyond the flagged span for semantic closure."""
import json, hashlib
from pathlib import Path

R = Path(__file__).resolve().parent.parent
W = R / "repair"
I = R / "inputs"
ART = {"form1-3": "form1-3-article.md", "r2": "form-1.3-r2-article.md", "r3": "form-1.3-r3-article.md"}
FIND = json.loads((W / "REPAIR-INPUTS.json").read_text())

def apply(tag):
    art = (I / ART[tag]).read_text(encoding="utf-8")
    raw = (W / f"{tag}-patches-raw.json").read_text(encoding="utf-8").strip()
    if raw.startswith("```"):
        raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```"))
    patches = json.loads(raw)
    P = patches["patches"] if isinstance(patches, dict) else patches
    sent = {f["FINDING_ID"]: f["PARENT_SENTENCE"] for f in FIND[tag]}

    spans, containment = [], []
    for p in P:
        old = p["OLD_TEXT"]; n = art.count(old)
        if n == 0:
            return {"tag": tag, "status": "FAIL_CLOSED", "reason": f"OLD_TEXT not found: {old[:60]!r}"}
        if n > 1:
            return {"tag": tag, "status": "FAIL_CLOSED", "reason": f"OLD_TEXT ambiguous ({n}x): {old[:60]!r}"}
        fid = p.get("FINDING_ID")
        ps = sent.get(fid)
        if ps is None:
            return {"tag": tag, "status": "FAIL_CLOSED", "reason": f"unknown FINDING_ID {fid!r}"}
        inside = old in ps
        containment.append({"PATCH_ID": p.get("PATCH_ID"), "FINDING_ID": fid,
                            "old_text_inside_parent_sentence": inside,
                            "old_len": len(old), "parent_sentence_len": len(ps)})
        if not inside:
            return {"tag": tag, "status": "FAIL_CLOSED",
                    "reason": f"OLD_TEXT for {fid} escapes its PARENT_SENTENCE: {old[:70]!r}"}
        i = art.index(old); spans.append((i, i + len(old), p))

    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if a[1] > b[0]:
            return {"tag": tag, "status": "FAIL_CLOSED", "reason": "overlapping patches"}

    out, prev, applied = [], 0, []
    for s, e, p in spans:
        new = "" if p.get("OPERATION", "REPLACE").upper() == "DELETE" else p["NEW_TEXT"]
        out.append(art[prev:s]); out.append(new); prev = e
        applied.append({"PATCH_ID": p.get("PATCH_ID"), "FINDING_ID": p.get("FINDING_ID"),
                        "op": p.get("OPERATION", "REPLACE"), "removed": len(art[s:e]),
                        "added": len(new), "old": art[s:e], "new": new,
                        "TARGET_COMMITMENT": p.get("TARGET_COMMITMENT"),
                        "SEMANTIC_CLOSURE_EXPLANATION": p.get("SEMANTIC_CLOSURE_EXPLANATION")})
    out.append(art[prev:]); patched = "".join(out)

    # every changed byte must belong to an approved span
    ok = (patched.startswith(art[:spans[0][0]]) and patched.endswith(art[spans[-1][1]:])) if spans else patched == art
    # independent reconstruction check
    recon = art
    for s, e, p in reversed(spans):
        recon = recon[:s] + ("" if p.get("OPERATION", "REPLACE").upper() == "DELETE" else p["NEW_TEXT"]) + recon[e:]
    (W / f"{tag}-patched.md").write_text(patched, encoding="utf-8")
    return {"tag": tag, "status": "APPLIED", "patches": len(P), "applied": applied,
            "containment": containment,
            "orig_sha256": hashlib.sha256(art.encode()).hexdigest(),
            "patched_sha256": hashlib.sha256(patched.encode()).hexdigest(),
            "chars_removed": sum(a["removed"] for a in applied),
            "chars_added": sum(a["added"] for a in applied),
            "word_delta": len(patched.split()) - len(art.split()),
            "paragraph_delta": len([x for x in patched.split("\n\n") if x.strip()])
                               - len([x for x in art.split("\n\n") if x.strip()]),
            "boundary_assert_ok": ok, "reconstruction_matches": recon == patched}

if __name__ == "__main__":
    res = [apply(t) for t in ("form1-3", "r2", "r3")]
    (W / "APPLICATION-REPORT.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    for r in res:
        print(json.dumps({k: v for k, v in r.items() if k not in ("applied", "containment")}, indent=1))
        for a in r.get("applied", []):
            print(f'   {a["PATCH_ID"]} {a["op"]:7s} -{a["removed"]}/+{a["added"]}  {a["FINDING_ID"]}')
            print(f'      old: {a["old"][:120]!r}')
            print(f'      new: {a["new"][:120]!r}')

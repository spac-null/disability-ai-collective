#!/usr/bin/env python3
"""Normalise a replicate's raw audit into the standard shape + checksums."""
import json, sys, hashlib
from pathlib import Path
ITER = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/sofa-real-ab-1-2026-08-18/iterations")
rep = sys.argv[1]; low = rep.lower(); out = ITER / rep
raw = json.load(open(out / f"{low}-grounding-audit-raw.json"))
claims = raw.get("claims", raw)
u = [c for c in claims if c["verdict"] == "UNSUPPORTED"]
un = [c for c in claims if c["verdict"] == "UNCERTAIN"]
art = (out / f"{low}-article.md").read_text(encoding="utf-8")
flags = json.load(open(out / f"{low}-audit-prescan.json"))
res = {"status": "FAIL" if u else ("REVIEWABLE_WITH_UNCERTAINTY" if un else "GROUNDED"),
       "deterministic_flags": flags, "claims": claims,
       "unsupported_count": len(u), "uncertain_count": len(un),
       "word_count": len(art.split()),
       "auditor_note": ("Prompt construction byte-identical to FORM-1/1.1/1.2/1.3. Auditor MODEL "
                        "is the local Claude subscription, not the production review/audit chain. "
                        "Verdicts are evidence, not authority; independent adjudication applied.")}
(out / f"{low}-grounding-audit.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{rep}: {res['status']} | unsupported {len(u)} | uncertain {len(un)} | words {res['word_count']}")
for c in claims:
    print(f"  [{c['verdict']}] {c['claim'][:160]}")

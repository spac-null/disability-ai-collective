#!/usr/bin/env python3
"""WG-5 stage 1: faithful extraction. WG-3A design UNCHANGED — the system prompt
is read verbatim from the frozen WG-3A file, not retyped. Blind to Gold V2.1."""
import hashlib, json, re
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")
SYSTEM = (W/"inputs/WG3A-EXTRACTION-SYSTEM-FROZEN.txt").read_text(encoding="utf-8")

def split_sentences(article):          # identical splitter to WG-1B / WG-3A
    out=[]
    for para in [p for p in article.strip().split("\n\n") if p.strip()]:
        if len(out)==0: out.append(para.strip()); continue
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip(): out.append(s.strip())
    return out

def main(tag, art_file):
    art=(W/"inputs"/art_file).read_text(encoding="utf-8")
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    sents=split_sentences(art)
    numbered="\n".join(f"[{i}] {s}" for i,s in enumerate(sents,1))
    user=(f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
          f"ARTICLE, SPLIT INTO {len(sents)} NUMBERED SENTENCES. Enumerate every assertion in every "
          f"one of them, in order, sentence ids 1 to {len(sents)}:\n---\n{numbered}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"stage1-extract"/f"{tag}-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"stage1-extract"/f"{tag}-user.txt").write_text(user,encoding="utf-8")
    (W/"stage1-extract"/f"{tag}-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"stage":"WG-5 STAGE 1 FAITHFUL EXTRACTION","component_version":"WG-3A, unchanged",
      "tag":tag,"sentences":len(sents),"system_sha256":sha(SYSTEM),"user_sha256":sha(user),
      "prompt_sha256":sha(rendered),"article_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
      "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
      "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","blind_to_gold":True,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"stage1-extract"/f"{tag}-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(sents)} sentences  system_sha={meta["system_sha256"][:16]}  prompt_sha={meta["prompt_sha256"][:16]}')

for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
    main(t,f)

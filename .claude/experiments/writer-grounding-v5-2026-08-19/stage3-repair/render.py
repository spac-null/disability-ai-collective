#!/usr/bin/env python3
"""WG-5 stage 3: PATCH-ONLY REPAIR. Fed ONLY the detector's own UNSUPPORTED
findings — no gold ids, no gold verdicts. Deliberately contains NO voice or
narrator-position guidance: per the task, the repair prompt must not be changed
in advance to chase WG-0B's old 'on the reading offered here' regression.
Voice is checked afterwards in verification only."""
import hashlib, json
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")
ART={"form1-3":"form1-3-article.md","r2":"form-1.3-r2-article.md","r3":"form-1.3-r3-article.md"}

SYSTEM = """You are the repair stage of a source-fidelity process at a disability-led publication. An audit has found specific spans of an article that assert content the SOURCE TEXT does not support. Your job is to remove exactly that unsupported content and nothing else.

YOU PRODUCE PATCH OPERATIONS ONLY.

Not a rewrite. Not a restructure. Not a polish. You are not improving the prose, tightening it, or making it flow better. Every character you change must be a character that carries unsupported content, or the minimum grammar needed to keep the sentence well-formed after that content is gone.

HARD CONSTRAINTS
  * NO full rewrite of any sentence that can be fixed by a smaller edit.
  * NO paragraph restructuring, splitting, joining or reordering.
  * NO prose polishing, no style changes, no word substitutions for taste.
  * Do NOT touch anything you were not given as a finding.
  * Do NOT add new factual content. The replacement must be licensed by the SOURCE TEXT or must
    simply assert less than the original did.
  * Do NOT add a hedge to rescue a claim ("perhaps", "it seems", "arguably", "on this reading").
    Removing the unsupported content is the repair. Hedging it is not.
  * Prefer the SMALLEST possible edit. Deleting an unsupported modifier is usually better than
    rewriting the clause around it.

FOR EACH FINDING, choose one operation:
  DELETE   remove the offending text (plus only the connecting words that would otherwise leave the
           sentence ungrammatical).
  REPLACE  substitute text that says only what the source licenses.

OLD_TEXT MUST BE COPIED CHARACTER-FOR-CHARACTER FROM THE ARTICLE and must occur EXACTLY ONCE in it. If the offending span alone is not unique, widen OLD_TEXT with just enough surrounding text to make it unique — and carry that surrounding text through unchanged into NEW_TEXT. Patches must not overlap.

OUTPUT
Reply with JSON only, no markdown fences, no commentary:
{"patches":[{"PATCH_ID":"...","FINDING_ID":"...","OPERATION":"DELETE|REPLACE","OLD_TEXT":"...","NEW_TEXT":"...","SOURCE_ANCHOR":"...","WHY_GROUNDED":"..."}]}

NEW_TEXT is "" for DELETE. SOURCE_ANCHOR is a verbatim quote from the SOURCE TEXT supporting what remains, or "" if the repair is a pure removal. WHY_GROUNDED states in one sentence why the repaired text no longer asserts anything the source does not support. Emit one patch per finding, in the order given."""

def main(tag):
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    art=(W/"inputs"/ART[tag]).read_text(encoding="utf-8")
    V=json.loads((W/"stage2-verdict"/f"{tag}-raw.json").read_text(encoding="utf-8"))
    P=V["propositions"] if isinstance(V,dict) else V
    finds=[]
    for p in P:
        for c in p.get("COMMITMENTS",[]):
            if c.get("VERDICT")=="UNSUPPORTED":
                finds.append({"FINDING_ID":c["COMMITMENT_ID"],
                  "OFFENDING_SPAN":c.get("OFFENDING_SPAN",""),
                  "SENTENCE_CONTEXT":p.get("EXACT_SPAN",""),
                  "WHAT_IS_UNSUPPORTED":c.get("PROPOSITION",""),
                  "WHY":c.get("REASON","")})
    lines="\n".join(json.dumps(f,ensure_ascii=False) for f in finds)
    user=(f"SOURCE TEXT (the only evidence):\n---\n{src}\n---\n\n"
          f"ARTICLE (patch against this exact text):\n---\n{art}\n---\n\n"
          f"{len(finds)} AUDIT FINDINGS. Produce exactly one patch per finding, in this order:\n---\n{lines}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"stage3-repair"/f"{tag}-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"stage3-repair"/f"{tag}-user.txt").write_text(user,encoding="utf-8")
    (W/"stage3-repair"/f"{tag}-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"stage":"WG-5 STAGE 3 PATCH-ONLY REPAIR","tag":tag,"findings":len(finds),
      "finding_ids":[f["FINDING_ID"] for f in finds],
      "fed_gold":False,"gold_ids_withheld":True,
      "voice_guidance_in_prompt":False,
      "system_sha256":sha(SYSTEM),"user_sha256":sha(user),"prompt_sha256":sha(rendered),
      "article_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
      "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
      "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","phase":"PRESERVED_PRE_EXECUTION"}
    (W/"stage3-repair"/f"{tag}-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(finds)} findings {[f["FINDING_ID"] for f in finds]}  prompt_sha={meta["prompt_sha256"][:16]}')

for t in ("form1-3","r2","r3"): main(t)

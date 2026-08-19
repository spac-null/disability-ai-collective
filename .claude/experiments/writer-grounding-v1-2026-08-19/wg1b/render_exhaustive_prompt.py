#!/usr/bin/env python3
"""WG-1B: renders the ONE experimental detector prompt variant — exhaustive
sentence-by-sentence claim enumeration. Same frozen source, same grounding
principles, same four verdicts. The auditor is BLIND to the gold ledger."""
import hashlib, json, re, sys
from pathlib import Path
W=Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v1-2026-08-19")

SYSTEM = """You are a source-fidelity auditor for a disability-led publication. You did not write this article and you do not get to fix it.

Your task is EXHAUSTIVE INSPECTION. You are NOT choosing which claims matter. You must walk the article sentence by sentence, in order, and account for EVERY sentence. Omitting a sentence is a failure of the task.

THE ONLY QUESTION IS SOURCE FIDELITY:
"Does the supplied SOURCE TEXT support this proposition?"
NEVER "could this be true in the world?" A statement can be perfectly true in reality and still UNSUPPORTED here, because the source does not establish it. Do not use outside knowledge to support anything.

PROCEDURE
For each numbered sentence you are given:
1. Identify every source-relative factual or specific proposition it asserts. A sentence may contain several; enumerate each separately.
   Source-relative propositions include: named people, places, venues, organizations, works; dates, times, durations, intervals, numbers, quantities; quoted or paraphrased source wording; attributions of speech, opinion, intent or position to anyone; assertions about what a person knew, felt, or experienced; causal claims; comparative claims; qualifiers and their scope.
2. If the sentence asserts no source-relative proposition — pure connective tissue, or the article's own argument making no factual assertion — return exactly one entry for it with CLAIM_ID "NO_CHECKABLE_CLAIM" and VERDICT "INTERPRETATION".
3. Otherwise give each proposition a verdict:
   SUPPORTED     — the source establishes it (quote the anchor).
   UNSUPPORTED   — the source does not establish it and the article states it as settled. Includes: invented specifics (names, venues, times, durations, numbers); a source qualifier dropped so a partial claim becomes absolute; an opinion, vocabulary or position reassigned to someone who did not express it; the article's own interpretation asserted as though it were source fact.
   INTERPRETATION — the article's own reading, visibly offered as such, asserting no new fact.
   UNCERTAIN     — plausible but not resolvable from what you were given; say what would resolve it.

Be careful in both directions. Do not flag ordinary narrative connective language. Do not flag the article's argument merely for being an argument — only when it is dressed as reported fact. Equally, do not wave through an invented detail because it sounds plausible.

OUTPUT
Reply with JSON only, no markdown fences:
{"sentences":[{"ARTICLE_SENTENCE_ID":1,"claims":[{"CLAIM_ID":"S1-C1","EXACT_SPAN":"...","CLAIM":"...","VERDICT":"SUPPORTED|UNSUPPORTED|INTERPRETATION|UNCERTAIN","SOURCE_ANCHOR":"...","REASON":"..."}]}]}

EXACT_SPAN must be copied character-for-character from the sentence. SOURCE_ANCHOR must be a verbatim quote from the SOURCE TEXT, or "" when there is none. Every sentence id you were given must appear exactly once in your output."""

def split_sentences(article):
    out=[]
    for para in [p for p in article.strip().split("\n\n") if p.strip()]:
        if len(out)==0:
            out.append(para.strip()); continue          # title
        for s in re.split(r'(?<=[.!?])\s+', para.strip()):
            if s.strip(): out.append(s.strip())
    return out

def main(tag, art_file):
    art=(W/"inputs"/art_file).read_text(encoding="utf-8")
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    sents=split_sentences(art)
    numbered="\n".join(f"[{i}] {s}" for i,s in enumerate(sents,1))
    user=(f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
          f"ARTICLE, SPLIT INTO {len(sents)} NUMBERED SENTENCES. Account for every one of them, "
          f"in order, ids 1 to {len(sents)}:\n---\n{numbered}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"wg1b"/f"{tag}-exhaustive-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"wg1b"/f"{tag}-exhaustive-user.txt").write_text(user,encoding="utf-8")
    (W/"wg1b"/f"{tag}-exhaustive-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"tag":tag,"sentences":len(sents),"system_sha256":sha(SYSTEM),
          "user_sha256":sha(user),"prompt_sha256":sha(rendered),
          "article_sha256":hashlib.sha256(art.encode()).hexdigest(),
          "blind_to_gold":True,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"wg1b"/f"{tag}-exhaustive-meta.json").write_text(json.dumps(meta,indent=2))
    print(json.dumps(meta,indent=2))

if __name__=="__main__":
    for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
        main(t,f)

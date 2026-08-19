#!/usr/bin/env python3
"""WG-4B: NEGATIVE META-SOURCE PROOF. Consumes the frozen WG-3A extraction.
Tests whether a claim ABOUT THE SOURCE can be licensed only by EXPLICIT negative
support or BOUNDED textual absence — never by 'I scanned and found nothing'.
BLIND to the gold ledger."""
import hashlib, json
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v4-2026-08-19")

SYSTEM = """You are the meta-source verification stage of a source-fidelity audit for a disability-led publication. Propositions have ALREADY been faithfully extracted from an article. Do not re-extract and do not edit the article.

SCOPE — SELECT SEMANTICALLY, NOT BY KEYWORD

You judge only propositions whose object is THE SOURCE ITSELF or its reviewer: what the source says, does not say, does, does not do, ranks, does not rank, comments on, does not comment on, centres, omits, believes or intends. Include claims about where something appears in the source, or how often.

Decide this by what the proposition COMMITS TO, not by which words appear in it. A proposition that merely mentions "the review" while asserting something about the world is not in scope. A proposition that asserts something about the source's behaviour IS in scope even if it never uses the word "review".

For every proposition you are given, set IN_SCOPE to YES or NO. If NO, output only the ID and IN_SCOPE:"NO" and move on. Do not verdict out-of-scope propositions.

THE INFERENCE YOU MUST NOT MAKE

Failing to find X in the source is NOT proof that the source does not do X.

  "I searched the source and did not find a ranking"
  does NOT establish
  "the review does not rank them"

That inference is invalid in general. Ranking, emphasis, centring and preference can be implicit, distributed, qualitative or carried by tone. The absence of an explicit sentence proves nothing about a semantic property of the whole text.

STARTING POSITION. If the extraction returned SOURCE_ANCHOR = "" (empty), a proposition that requires factual source support begins as UNPROVEN. You may not silently manufacture a replacement anchor and treat the claim as settled. You may look at the source — but if you do, you must produce an explicit proof object under the rules below, and it must survive them.

TWO ALLOWED PROOF TYPES — THERE IS NO THIRD

  EXPLICIT
    The source explicitly states the relevant negation, or states something that directly entails it.
    Quote it.

  BOUNDED_ABSENCE
    The proposition concerns a PRECISELY DEFINED, FINITE, TEXTUAL property whose absence can actually
    be demonstrated across a scope you can state and exhaust. You must be able to say what the scope
    is, why that scope is the right one, and why you have covered all of it.
    Example of a boundable claim: whether a specific named quantity is accompanied by any remark in
    the passage where it occurs — the scope is one identifiable passage and the property is textual.
    Example of a claim that is NOT boundable: whether the review ranks two artists above the rest of
    the festival — ranking is semantic, can be implicit or distributed across the whole text, and
    carried by evaluative tone. Absence of an explicit ranking sentence does not demonstrate it.

  "I scanned the source and found nothing contrary" is NOT a proof type. If your reasoning reduces to
  that, the proposition is UNSUPPORTED, however plausible it seems.

Be honest about which one you have. If a claim feels bounded but you cannot state a finite scope and
justify its completeness, it is not bounded.

DO NOT BAN NEGATIVE SOURCE CLAIMS. The goal is discrimination. A negative claim about the source that
IS explicitly supported, or that IS genuinely bounded and demonstrated, is legitimate and must keep a
SUPPORTED or INTERPRETATION verdict. Rejecting every negative claim is as much a failure as accepting
every one. Positive meta-source claims ("the review says X") are judged normally against their anchor
and do not need a proof object — set PROOF_TYPE "N/A" and NEGATIVE "NO".

VERDICTS
  SUPPORTED      licensed by the source: a real anchor for a positive claim, or a surviving
                 EXPLICIT / BOUNDED_ABSENCE proof for a negative one.
  INTERPRETATION the article's analysis of source-grounded material, asserting no new factual state
                 about the source's behaviour.
  UNSUPPORTED    asserts a factual property of the source that is not licensed — including any
                 negative claim whose only support is failure to find contrary text.
  UNCERTAIN      unresolvable from what you were given; say what would resolve it.

OUTPUT
Reply with JSON only, no markdown fences, no commentary:
{"results":[{"ID":"P1","IN_SCOPE":"YES|NO","NEGATIVE":"YES|NO","NEGATIVE_CLAIM":"...","SCOPE":"...","PROOF_TYPE":"EXPLICIT|BOUNDED_ABSENCE|N/A|NONE","EVIDENCE_OR_METHOD":"...","WHY_SCOPE_IS_COMPLETE":"...","EXTRACTION_ANCHOR_WAS_EMPTY":"YES|NO","VERDICT":"SUPPORTED|INTERPRETATION|UNSUPPORTED|UNCERTAIN","REASON":"..."}]}

For IN_SCOPE "NO" emit only ID and IN_SCOPE. Use PROOF_TYPE "NONE" when a negative claim has no
surviving proof. Process every ID you are given, exactly once, in order."""

def main(tag, art_file):
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    art=(W/"inputs"/art_file).read_text(encoding="utf-8")
    ex=json.loads((W/"inputs"/f"{tag}-extract-raw.json").read_text(encoding="utf-8"))
    P=ex["propositions"] if isinstance(ex,dict) else ex
    lines="\n".join(json.dumps({k:p.get(k,"") for k in
        ("ID","SENTENCE_ID","EXACT_SPAN","ATOMIC_PROPOSITION","SUBJECT","PREDICATE",
         "OBJECT_OR_COMPLEMENT","CLAIM_OBJECT_TYPE","SOURCE_ANCHOR")}, ensure_ascii=False) for p in P)
    user=(f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
          f"{len(P)} FAITHFULLY EXTRACTED PROPOSITIONS. Decide IN_SCOPE for every one, in order, and\n"
          f"fully evaluate those in scope. CLAIM_OBJECT_TYPE is an earlier stage's hypothesis, not\n"
          f"authority — judge scope yourself from what each proposition commits to.\n"
          f"EXACT_SPAN is the article's own words and is authoritative. SOURCE_ANCHOR is what the\n"
          f"extraction returned; \"\" means it found none.\n---\n{lines}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"WG-4B"/f"{tag}-negproof-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"WG-4B"/f"{tag}-negproof-user.txt").write_text(user,encoding="utf-8")
    (W/"WG-4B"/f"{tag}-negproof-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"experiment":"WG-4B NEGATIVE META-SOURCE PROOF","tag":tag,"input_propositions":len(P),
      "system_sha256":sha(SYSTEM),"user_sha256":sha(user),"prompt_sha256":sha(rendered),
      "article_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
      "input_extraction_sha256":hashlib.sha256((W/"inputs"/f"{tag}-extract-raw.json").read_bytes()).hexdigest(),
      "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
      "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","blind_to_gold":True,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"WG-4B"/f"{tag}-negproof-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(P)} props  prompt_sha={meta["prompt_sha256"][:16]}')

if __name__=="__main__":
    for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
        main(t,f)

#!/usr/bin/env python3
"""WG-4A: COMMITMENT DECOMPOSITION. Consumes the frozen WG-3A extraction.
Splits each faithfully extracted proposition into independently verdictable
factual commitments, then verdicts each separately. BLIND to the gold ledger."""
import hashlib, json
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v4-2026-08-19")

SYSTEM = """You are the commitment-decomposition stage of a source-fidelity audit for a disability-led publication. Propositions have ALREADY been faithfully extracted from an article. Do not re-extract, do not look for new claims, do not edit the article.

THE PROBLEM YOU EXIST TO SOLVE

A single proposition can carry a GROUNDED CORE plus an UNSUPPORTED MODIFIER. If it is judged as one unit, the grounded core licenses the whole thing and the invented modifier rides in free.

  "the visitor did not know the work existed an hour ago"

carries at least two independent factual commitments:
  A. the visitor was unfamiliar with the work        <- the source may support this
  B. that state held ONE HOUR earlier                <- the source may not support this at all

A source-supported base commitment MUST NOT transfer its support to an independent modifier. Judge every commitment on its own evidence.

THE ONLY QUESTION IS SOURCE FIDELITY — never world truth. A statement can be true in reality and still UNSUPPORTED, because the supplied SOURCE TEXT does not establish it. Never use outside knowledge.

STEP 1 — DECOMPOSE

For each proposition, split EXACT_SPAN into its independent factual commitments. Where present, always separate out:
  time · date · duration · interval · quantity · proper noun · human knowledge or state ·
  negation · qualifier and its scope · causal clause · meta-source proposition

DO NOT OVER-FRAGMENT. This publication's work is interpretation, and complex syntax is not the same as multiple factual claims. If a span is a single analytic reading — an evaluation, a metaphor, a comparison of source-given material, a synthesis — emit exactly ONE commitment for it. Do not manufacture separate "factual" commitments out of the parts of an argument. A sentence being long, subordinated or causal is NOT a reason to split it. Split only where there is a genuinely independent factual commitment that could be true or false on its own evidence.

If a proposition carries exactly one indivisible commitment, emit exactly one. That is the normal case.

COMMITMENT_TYPE — use ONLY these:
  BASE_STATE         the core state or event asserted
  TEMPORAL_MODIFIER  a time, date, duration or interval attached to it
  QUANTIFIER         a quantity, number, or scope word ("most", "all", "thousands")
  PROPER_NOUN        a named person, place, venue, organisation or work
  HUMAN_STATE        what a person knew, felt, believed, intended, expected or brought
  CAUSAL_RELATION    an asserted because/therefore link
  SOURCE_META        an assertion about what the source or reviewer says, does, or does not do
  OTHER              analysis, metaphor, evaluation, connective tissue

STEP 2 — VERDICT EACH COMMITMENT SEPARATELY

For each commitment independently, against the SOURCE TEXT alone:
  SUPPORTED      the source entails or directly licenses THIS commitment. Quote the anchor.
  INTERPRETATION the article's analysis of source-grounded material; asserts no new factual state.
  UNSUPPORTED    asserts factual content the source does not license, stated as settled.
  UNCERTAIN      unresolvable from what you were given; say what would resolve it.

Rules that decide nothing on their own — do not use them as shortcuts: absence of a hedge word; comparative form; causal form; vocabulary; confidence of tone. Interpretation does not need "perhaps" to be legitimate.

When a modifier is attached to a grounded base, ask specifically: does the source license THE MODIFIER? An anchor establishing that someone is unfamiliar with an artist does NOT establish how long they were unfamiliar. An anchor saying "MOST of the work" does NOT license a claim about ALL the work.

STEP 3 — AGGREGATE

PARENT_AGGREGATE rules:
  If ANY factual commitment is UNSUPPORTED, the parent proposition CANNOT be SUPPORTED — set UNSUPPORTED.
  Otherwise if any commitment is UNCERTAIN, set UNCERTAIN.
  Otherwise if all commitments are INTERPRETATION or OTHER-type analysis, set INTERPRETATION.
  Otherwise set SUPPORTED.

Also set SURGICALLY_REMOVABLE: YES if deleting the unsupported commitment would leave the rest of the span intact and grounded; NO otherwise. You are producing grounding findings, NOT judging literary quality. A parent marked UNSUPPORTED because of one removable modifier is a precise finding, not a condemnation of the sentence.

OUTPUT
Reply with JSON only, no markdown fences, no commentary:
{"propositions":[{"PARENT_CLAIM_ID":"P1","EXACT_SPAN":"...","COMMITMENTS":[{"COMMITMENT_ID":"P1-C1","PROPOSITION":"...","COMMITMENT_TYPE":"BASE_STATE","SOURCE_ANCHOR":"...","SUPPORT_STATUS":"SUPPORTED|UNSUPPORTED|INTERPRETATION|UNCERTAIN","REASON":"..."}],"PARENT_AGGREGATE":"...","SURGICALLY_REMOVABLE":"YES|NO|N/A"}]}

SOURCE_ANCHOR must be a verbatim quote from the SOURCE TEXT, or "" when there is none. An empty anchor is a legitimate answer — do not invent or stretch one. Process every PARENT_CLAIM_ID you are given, exactly once, in order."""

def main(tag, art_file):
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    art=(W/"inputs"/art_file).read_text(encoding="utf-8")
    ex=json.loads((W/"inputs"/f"{tag}-extract-raw.json").read_text(encoding="utf-8"))
    P=ex["propositions"] if isinstance(ex,dict) else ex
    lines="\n".join(json.dumps({k:p.get(k,"") for k in
        ("ID","SENTENCE_ID","EXACT_SPAN","ATOMIC_PROPOSITION","SUBJECT","PREDICATE",
         "OBJECT_OR_COMPLEMENT","CLAIM_OBJECT_TYPE","SOURCE_ANCHOR")}, ensure_ascii=False) for p in P)
    user=(f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
          f"{len(P)} FAITHFULLY EXTRACTED PROPOSITIONS. Decompose and verdict every one, in order.\n"
          f"EXACT_SPAN is the article's own words and is authoritative. ATOMIC_PROPOSITION is a\n"
          f"grammatical normalisation, an aid only. SOURCE_ANCHOR is what the extraction returned;\n"
          f"it may be empty, wrong, or too weak for the commitment it is attached to.\n---\n{lines}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"WG-4A"/f"{tag}-decomp-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"WG-4A"/f"{tag}-decomp-user.txt").write_text(user,encoding="utf-8")
    (W/"WG-4A"/f"{tag}-decomp-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"experiment":"WG-4A COMMITMENT DECOMPOSITION","tag":tag,"input_propositions":len(P),
      "system_sha256":sha(SYSTEM),"user_sha256":sha(user),"prompt_sha256":sha(rendered),
      "article_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
      "input_extraction_sha256":hashlib.sha256((W/"inputs"/f"{tag}-extract-raw.json").read_bytes()).hexdigest(),
      "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
      "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","blind_to_gold":True,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"WG-4A"/f"{tag}-decomp-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(P)} props  prompt_sha={meta["prompt_sha256"][:16]}  extract_in={meta["input_extraction_sha256"][:16]}')

if __name__=="__main__":
    for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
        main(t,f)

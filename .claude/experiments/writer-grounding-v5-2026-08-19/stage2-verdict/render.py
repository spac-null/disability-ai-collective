#!/usr/bin/env python3
"""WG-5 stage 2: COMPOSED VERDICT. Merges three already-calibrated components in
one call — WG-4A commitment decomposition, WG-3B object-aware semantics, WG-4B
negative meta-source proof. No new taxonomy. Blind to Gold V2.1."""
import hashlib, json
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v5-2026-08-19")

SYSTEM = """You are the grounding-verdict stage of a source-fidelity audit for a disability-led publication. Propositions have ALREADY been faithfully extracted from an article. Do not re-extract, do not look for new claims, do not edit the article.

THE ONLY QUESTION IS SOURCE FIDELITY — never world truth. A statement can be perfectly true in reality and still UNSUPPORTED here, because the supplied SOURCE TEXT does not establish it. Never use outside knowledge to support anything.

WHAT THIS PUBLICATION IS FOR

The article is narrative nonfiction and interpretation is its legitimate work. The publication exists to make new meaning from its material. It is ALLOWED to say things the source never says. Your job is NOT to suppress analysis. Your job is to stop unsupported factual invention from passing as source-grounded fact.

The boundary is NOT "does the source literally say this?"
The boundary is: "Is this new meaning derived from source-grounded material, or does it add a new factual state about the world, about a person, or about the source itself?"

You will apply three checks in order.

=== CHECK A — DECOMPOSE FACTUAL COMMITMENTS ===

A single proposition can carry a GROUNDED CORE plus an UNSUPPORTED MODIFIER. Judged as one unit, the grounded core licenses the whole thing and the invented modifier rides in free.

  "the visitor did not know the work existed an hour ago"
    A. the visitor was unfamiliar with the work   <- the source may support this
    B. that state held ONE HOUR earlier            <- the source may not support this at all

A source-supported base commitment MUST NOT transfer its support to an independent modifier. Split where present: time · date · duration · interval · quantity · proper noun · human knowledge or state · negation · qualifier and its scope · causal factual clause · meta-source proposition.

DO NOT OVER-FRAGMENT. Complex syntax is not multiple factual claims. If a span is a single analytic reading — an evaluation, a metaphor, a comparison of source-given material, a synthesis — emit exactly ONE commitment. Do not manufacture separate "factual" commitments out of the parts of an argument. Length, subordination and causal form are NOT reasons to split. Most propositions yield exactly one commitment; that is the normal case.

COMMITMENT_TYPE — use ONLY: BASE_STATE · TEMPORAL_MODIFIER · QUANTIFIER · PROPER_NOUN · HUMAN_STATE · CAUSAL_RELATION · SOURCE_META · OTHER

=== CHECK B — OBJECT-AWARE SEMANTICS ===

Decide by WHAT the commitment is about. CLAIM_OBJECT_TYPE from the extraction is a hypothesis; correct it in your REASON if you judge it wrong.

  SUBJECT_MATTER — the article reasoning about material the piece discusses: evaluation, comparison,
      synthesis, metaphor, causal reading, drawing out what grounded facts imply together.
      >>> May legitimately be INTERPRETATION EVEN WHEN THE SOURCE NEVER STATES THE COMPARISON,
          SYNTHESIS, METAPHOR OR EVALUATIVE RELATION, and even when no single source sentence states
          the article's conclusion. An article-level reading may combine several grounded facts.
      >>> Becomes UNSUPPORTED only if it SMUGGLES IN a new concrete fact.
  HUMAN_STATE — what a person, visitor, viewer or reader knew, felt, believed, intended, expected,
      brought or was prepared for. >>> REQUIRES SOURCE SUPPORT for the state asserted.
  SOURCE_OR_REVIEW — what the source or reviewer says, ranks, omits, centres, intends, believes, does
      or does not do; where something appears in it; how often. >>> REQUIRES SOURCE SUPPORT.
  CONCRETE_WORLD_DETAIL — name, venue, date, time, duration, number, quantity, place.
      >>> REQUIRES SOURCE SUPPORT.
  OTHER — connective tissue, headings, rhetorical framing. Normally INTERPRETATION.

ANCHOR OBLIGATION — apply ONLY to HUMAN_STATE, SOURCE_OR_REVIEW and CONCRETE_WORLD_DETAIL, NEVER to SUBJECT_MATTER. For those three ask: is there an anchor, and does it license THE SPECIFIC THING CLAIMED — not merely touch the same topic or person? An anchor establishing that someone is unfamiliar with an artist does NOT establish how long they were unfamiliar, or what they brought to an encounter. An anchor saying "MOST of the work" does NOT license a claim about ALL the work. Requiring one source sentence to license an article-level SUBJECT_MATTER reading would destroy legitimate interpretation — do not do it.

=== CHECK C — NEGATIVE META-SOURCE PROOF ===

Applies to any commitment that asserts the source/review does NOT do something.

Failing to find X in the source is NOT proof that the source does not do X. "I searched and found no ranking" does NOT establish "the review does not rank them". That inference is invalid in general: ranking, emphasis, centring and preference can be implicit, distributed, qualitative or carried by tone.

If the extraction returned SOURCE_ANCHOR = "" a factual claim begins as UNPROVEN. You may not silently manufacture a replacement anchor and treat the claim as settled.

TWO ALLOWED PROOF TYPES — THERE IS NO THIRD:
  EXPLICIT         the source explicitly states the negation, or states something directly entailing
                   it. Quote it.
  BOUNDED_ABSENCE  the claim concerns a PRECISELY DEFINED, FINITE, TEXTUAL property whose absence can
                   be demonstrated across a scope you can state and exhaust. You must say what the
                   scope is and why you have covered all of it.
"I scanned and found nothing contrary" is NOT a proof type. If your reasoning reduces to that, the commitment is UNSUPPORTED however plausible it seems.

DO NOT BAN NEGATIVE SOURCE CLAIMS. A negative claim that IS explicitly supported, or IS genuinely bounded and demonstrated, is legitimate and keeps its support. Rejecting every negative claim is as much a failure as accepting every one.

=== THINGS THAT DECIDE NOTHING ===
Absence of a hedge ("perhaps", "it seems", "on this reading" are NOT required — good prose states its readings directly) · comparative form · causal form · vocabulary · confident tone. Judge semantically.

=== VERDICTS ===
  SUPPORTED      the source entails or licenses THIS commitment. Quote the anchor.
  INTERPRETATION the article's analysis of source-grounded material; asserts no new factual state.
  UNSUPPORTED    asserts factual content the evidence does not license, stated as settled.
  UNCERTAIN      plausible but unresolvable from what you were given; say what would resolve it.
                 Use this honestly. Do NOT round an unresolved case up to SUPPORTED or down to
                 UNSUPPORTED to look decisive.

=== SMALLEST OFFENDING SPAN ===
For every UNSUPPORTED commitment, set OFFENDING_SPAN to the SMALLEST exact contiguous substring of the article that carries the unsupported content — copied character-for-character. If only a modifier is bad, the offending span is the modifier, NOT the whole sentence. For "it is happening to a person who did not know the work existed an hour ago" where only the interval is unsupported, OFFENDING_SPAN is "an hour ago".

=== AGGREGATE ===
PARENT_AGGREGATE: UNSUPPORTED if any factual commitment is UNSUPPORTED; else UNCERTAIN if any is UNCERTAIN; else INTERPRETATION if all are interpretation/analysis; else SUPPORTED.
SURGICALLY_REMOVABLE: YES if deleting the unsupported commitment leaves the rest intact and grounded.

OUTPUT
Reply with JSON only, no markdown fences, no commentary:
{"propositions":[{"PARENT_CLAIM_ID":"P1","EXACT_SPAN":"...","COMMITMENTS":[{"COMMITMENT_ID":"P1-C1","PROPOSITION":"...","COMMITMENT_TYPE":"BASE_STATE","CLAIM_OBJECT_TYPE":"SUBJECT_MATTER","NEGATIVE":"YES|NO","PROOF_TYPE":"EXPLICIT|BOUNDED_ABSENCE|N/A|NONE","SCOPE":"...","WHY_SCOPE_IS_COMPLETE":"...","SOURCE_ANCHOR":"...","VERDICT":"SUPPORTED|INTERPRETATION|UNSUPPORTED|UNCERTAIN","OFFENDING_SPAN":"...","REASON":"..."}],"PARENT_AGGREGATE":"...","SURGICALLY_REMOVABLE":"YES|NO|N/A"}]}

SOURCE_ANCHOR must be verbatim from the SOURCE TEXT or "". OFFENDING_SPAN is "" unless the verdict is UNSUPPORTED. Process every PARENT_CLAIM_ID exactly once, in order."""

def main(tag, art_file):
    src=(W/"inputs/source-snapshot.txt").read_text(encoding="utf-8")
    art=(W/"inputs"/art_file).read_text(encoding="utf-8")
    ex=json.loads((W/"stage1-extract"/f"{tag}-raw.json").read_text(encoding="utf-8"))
    P=ex["propositions"] if isinstance(ex,dict) else ex
    lines="\n".join(json.dumps({k:p.get(k,"") for k in
        ("ID","SENTENCE_ID","EXACT_SPAN","ATOMIC_PROPOSITION","SUBJECT","PREDICATE",
         "OBJECT_OR_COMPLEMENT","CLAIM_OBJECT_TYPE","SOURCE_ANCHOR")}, ensure_ascii=False) for p in P)
    user=(f"SOURCE TEXT (the only evidence — nothing outside it counts):\n---\n{src}\n---\n\n"
          f"FULL ARTICLE (for locating exact offending spans only — do not audit it afresh):\n---\n{art}\n---\n\n"
          f"{len(P)} FAITHFULLY EXTRACTED PROPOSITIONS. Apply checks A, B and C to every one, in order.\n"
          f"EXACT_SPAN is the article's own words and is authoritative. ATOMIC_PROPOSITION is a\n"
          f"grammatical normalisation, an aid only. SOURCE_ANCHOR is what the extraction returned;\n"
          f"it may be empty, wrong, or too weak for the commitment it is attached to.\n---\n{lines}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"stage2-verdict"/f"{tag}-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"stage2-verdict"/f"{tag}-user.txt").write_text(user,encoding="utf-8")
    (W/"stage2-verdict"/f"{tag}-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"stage":"WG-5 STAGE 2 COMPOSED VERDICT",
      "component_versions":{"decomposition":"WG-4A","object_aware":"WG-3B","negative_proof":"WG-4B"},
      "tag":tag,"input_propositions":len(P),"system_sha256":sha(SYSTEM),"user_sha256":sha(user),
      "prompt_sha256":sha(rendered),"article_sha256":hashlib.sha256(art.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
      "input_extraction_sha256":hashlib.sha256((W/"stage1-extract"/f"{tag}-raw.json").read_bytes()).hexdigest(),
      "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
      "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","blind_to_gold":True,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"stage2-verdict"/f"{tag}-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(P)} props  prompt_sha={meta["prompt_sha256"][:16]}')

if __name__=="__main__":
    for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
        main(t,f)

#!/usr/bin/env python3
"""WG-3A: renders the ONE new extraction prompt variant — exhaustive enumeration
with a CONTENT-PRESERVATION invariant and semantic CLAIM_OBJECT_TYPE.
No verdicts. The extractor is BLIND to the gold ledger.
Sentence splitter is identical to WG-1B's so counts stay comparable."""
import hashlib, json, re
from pathlib import Path
W = Path("/Users/stargatesgx/code/disability-collective-ai/.claude/experiments/writer-grounding-v3-2026-08-19")

SYSTEM = """You are an extraction engine for a source-fidelity audit at a disability-led publication. You did not write this article. You are NOT judging it. You produce no verdicts.

Your single job: walk the article sentence by sentence, in order, and enumerate EVERY assertion each sentence makes, preserving its factual commitments EXACTLY. A later stage will judge them. If you soften, generalise or summarise an assertion, that later stage will judge something the article never said, and the audit fails. Omitting a sentence is a failure of the task.

THE CARDINAL RULE — CONTENT PRESERVATION

EXACT_SPAN is authoritative. ATOMIC_PROPOSITION exists only to make the span easier to reason about. It may normalise grammar. It may NEVER delete factual content that is present in the span.

You must never drop any of these when they appear in the span:
  * negation ("not", "never", "without", "nothing")
  * quantifiers and their scope ("most", "all", "some", "any", "thousands")
  * comparison ("harder", "more than", "above the rest", "the one that presses")
  * causal relation ("because", "so that", "which means")
  * time, date, duration, interval ("an hour ago", "in August", "midway")
  * proper nouns (people, places, venues, galleries, organisations, works)
  * what a person knew, felt, believed, intended, expected, brought or was prepared for
  * what the source/review/reviewer says, ranks, omits, centres, intends, believes, does or does not do
  * institutional attribution (who is being credited with a position or act)

WORKED EXAMPLE — this is the exact failure mode you must avoid.

  EXACT_SPAN: "without the visitor having brought anything to the encounter except the willingness to walk in"

  FORBIDDEN ATOMIC_PROPOSITION: "the encounter was unprepared"
  FORBIDDEN ATOMIC_PROPOSITION: "the festival experience consists of unprepared encounters"
      Both delete the actual commitment — what the visitor DID and DID NOT BRING. "Unprepared"
      is a summary. The assertion was about the visitor's preparation state. It is gone.

  REQUIRED ATOMIC_PROPOSITION: "The visitor brought nothing to the encounter except a willingness to walk in."
      Grammar normalised. Factual commitment intact.

If a single span makes several separable commitments, emit several entries for that span rather than merging them into one weaker sentence.

CLAIM_OBJECT_TYPE — classify WHAT the assertion is about. Judge this semantically, from what the assertion commits to. Do NOT classify by vocabulary, by which nouns appear, or by sentence shape.

  SUBJECT_MATTER          The article reasoning about material the piece is discussing: evaluation,
                          comparison, synthesis, metaphor, drawing out what grounded facts imply.
                          e.g. "the second side is the one that presses"
  HUMAN_STATE             An assertion about what a person, visitor, viewer or reader knew, felt,
                          believed, intended, expected, brought, or was prepared for.
                          e.g. "the visitor brought nothing except willingness to walk in"
  SOURCE_OR_REVIEW        An assertion about the source text or its reviewer: what it says, ranks,
                          omits, centres, intends, believes, does or does not do; where something
                          appears in it; how often it does something.
                          e.g. "the review does not rank them"
  CONCRETE_WORLD_DETAIL   A specific fact about the world: a name, venue, date, time, duration,
                          number, quantity, or place. e.g. "City Art Centre"
  OTHER                   Connective tissue, headings, or rhetorical framing asserting nothing.

A sentence may produce entries of several different types. Attribution wrappers ("the review says X")
usually yield TWO entries: one SOURCE_OR_REVIEW entry for the attribution, and one entry for X itself,
typed by what X is about.

SOURCE_ANCHOR: a verbatim quote from the SOURCE TEXT that bears on this assertion, or "" if there is
none. Do NOT invent one. Do NOT stretch a loosely related sentence into an anchor — if the source does
not speak to this assertion, return "". An empty anchor is a legitimate and useful answer. You are not
being scored on how many anchors you find.

OUTPUT
Reply with JSON only. No markdown fences, no commentary before or after.
{"propositions":[{"ID":"P1","SENTENCE_ID":1,"EXACT_SPAN":"...","ATOMIC_PROPOSITION":"...","SUBJECT":"...","PREDICATE":"...","OBJECT_OR_COMPLEMENT":"...","CLAIM_OBJECT_TYPE":"SUBJECT_MATTER|HUMAN_STATE|SOURCE_OR_REVIEW|CONCRETE_WORLD_DETAIL|OTHER","SOURCE_ANCHOR":"..."}]}

EXACT_SPAN must be copied character-for-character from the sentence you were given — a contiguous
substring, not a paraphrase and not stitched from separate parts. IDs run P1, P2, P3... in order.
Every sentence id you were given must appear at least once."""

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
          f"ARTICLE, SPLIT INTO {len(sents)} NUMBERED SENTENCES. Enumerate every assertion in every "
          f"one of them, in order, sentence ids 1 to {len(sents)}:\n---\n{numbered}\n---\n")
    rendered="=== SYSTEM ===\n"+SYSTEM+"\n\n=== USER ===\n"+user
    sha=lambda s: hashlib.sha256(s.encode()).hexdigest()
    (W/"wg3a"/f"{tag}-extract-system.txt").write_text(SYSTEM,encoding="utf-8")
    (W/"wg3a"/f"{tag}-extract-user.txt").write_text(user,encoding="utf-8")
    (W/"wg3a"/f"{tag}-extract-prompt.txt").write_text(rendered,encoding="utf-8")
    meta={"experiment":"WG-3A EXTRACTION FIDELITY","tag":tag,"sentences":len(sents),
          "system_sha256":sha(SYSTEM),"user_sha256":sha(user),"prompt_sha256":sha(rendered),
          "article_sha256":hashlib.sha256(art.encode()).hexdigest(),
          "source_sha256":hashlib.sha256(src.encode()).hexdigest(),
          "model_identity":"claude-opus-5[1m] via local Claude subscription, fresh-context subagent",
          "execution_mode":"LOCAL_CLAUDE_SUBSCRIPTION","blind_to_gold":True,
          "emits_verdicts":False,"phase":"PRESERVED_PRE_EXECUTION"}
    (W/"wg3a"/f"{tag}-extract-meta.json").write_text(json.dumps(meta,indent=2))
    print(f'{tag}: {len(sents)} sentences  prompt_sha={meta["prompt_sha256"][:16]}  article_sha={meta["article_sha256"][:16]}')

if __name__=="__main__":
    for t,f in [("form1-3","form1-3-article.md"),("r2","form-1.3-r2-article.md"),("r3","form-1.3-r3-article.md")]:
        main(t,f)

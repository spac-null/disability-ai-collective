"""
stages.py -- the live model-backed stage producers for NEW_ENGINE_V1.

Each function takes the artifacts its stage is allowed to consume and returns a payload
for `contracts.validate`. The stage boundaries are the point of the architecture, so
they are expressed as function signatures: `ground()` cannot see the Article Form
because it is not passed it.

WHAT IS DELIBERATELY ABSENT
No persona canon, no roleplay instruction, no forbidden-word list, no register or
article-type selector, no testimony quota, no R-number rule system, no whole-document
rewrite instruction. `contracts.WRITER_INPUT` validation rejects 29 legacy markers, so
a regression here fails closed rather than quietly reintroducing the 59k prompt.

THE THREE KINDS OF STATEMENT, kept apart
  SOURCE FACT            -- traceable to the snapshot bytes
  EDITORIAL INTERPRETATION -- what a disability-informed reading makes knowable
  EDITORIAL GUIDANCE     -- instruction to the writer
Discovery emits all three in separate fields. Nothing merges them, because the whole
failure mode this architecture exists to remove is interpretation arriving downstream
wearing the authority of fact.
"""
from __future__ import annotations

import re

from .provider import parse_json_object

# ── Shared doctrine ────────────────────────────────────────────────────────────
# The prose principle the project has settled on, stated once, in plain terms.
PROSE_DOCTRINE = (
    "Make the thinking sophisticated; make the reading easy. Plain vocabulary. One "
    "modifier where one will do. Short sentences carry the hard turns. Do not announce "
    "a thesis, do not summarise at the end, and do not explain the point after making it.\n"
    "  Concrete before abstract. Name the thing -- the object, the project, the person, "
    "what was made or done -- and say what it is before you say what it means. No framing "
    "device standing in front of the subject, no throat-clearing.\n"
    "  The opening does three jobs, and normally does them inside the first two to four "
    "sentences: it names the concrete subject, it says what is unusual or particular about "
    "it, and it makes clear why this article is looking at it. There is no set pattern for "
    "doing that and you should not write to one. What matters is that a reader never has to "
    "reach the third or fourth paragraph to find out why the piece exists.\n"
    "  One claim to a sentence. Build sentences out of a concrete noun and an active verb, "
    "and give each one a single idea to carry. Where two ideas both matter, write two "
    "sentences. Distrust any long sentence with clauses hanging off it: most are two "
    "sentences that have not been separated yet, and most of their abstract nouns can be "
    "replaced by the thing itself. Never add a clause to explain something the reader has "
    "already understood.\n"
    "  Keep naming the thing. When the argument comes back to a point, bring the object "
    "back with it rather than a conceptual noun standing in for it -- an article about a "
    "booklet should still be talking about the booklet. If the same handful of abstract "
    "words is carrying sentence after sentence, the writing has drifted off the material "
    "and needs to come back down to it.\n"
    "  Say the point once, and say it well. The argument gets one clear statement. "
    "Restating it in different abstract vocabulary is not development: a paragraph earns "
    "its place by adding evidence, a new implication, a necessary qualification, or a real "
    "step forward, and by nothing else.\n"
    "  Keep one idea moving at a time. Do not stack several layers of abstraction before "
    "coming back to the thing itself, and do not pile conceptual nouns and metaphors into "
    "one passage. One job to a paragraph, and make the move from one paragraph to the next "
    "obvious: the reader should never have to work out why a paragraph follows the one "
    "before it.\n"
    "  Let the facts do the arguing. Where the material gives you a person, an object, a "
    "date, a number, a decision, a document's own wording or a real example, put it on the "
    "page and let it carry the point. A concrete detail is worth more than a sentence "
    "about what the detail means. Active verbs. Cut any conceptual noun that only renames "
    "something the reader already has.\n"
    "  Explain what the reader needs, at once, in ordinary words, in a sentence. Do not "
    "leave a term to be decoded from context and do not send the reader back over a "
    "sentence to find out what it was doing.\n"
    "  If the material will not carry the length, write a shorter piece. Do not manufacture "
    "depth by turning the same few facts over again from another angle: one fact read three "
    "ways is one fact, not three paragraphs of thinking, and a reader feels the difference "
    "immediately.\n"
    "  Before you finish, read the whole thing once as someone who has not yet decided to "
    "keep reading, and cut. Of every paragraph: does it add information or movement; could "
    "a concrete fact do the work this abstraction is doing; is the point already clear "
    "without this sentence; would an ordinary intelligent reader have to read it twice. "
    "Delete rather than explain twice. If a paragraph makes the same point in different "
    "words as an earlier one, delete it. The arrival is stated once. No paragraph before it is a "
    "preview of it, and nothing after it is a reprise.\n"
    "  Get from evidence to meaning with a plain sentence that does the explaining. Do not "
    "jump the gap and leave the reader to reconstruct it.\n"
    "  No sentence should need rereading before its main claim is clear. Vary sentence "
    "length; keep the syntax straight. Use the ordinary word wherever it carries the same "
    "meaning as the specialist or theoretical one.\n"
    "  Mark a limit where the claim is made, in a clause or a sentence, and then move on. "
    "What the source does not establish is worth one plain statement in ordinary words. It "
    "is not worth a paragraph about what you are not claiming: state the boundary, do not "
    "perform it.\n"
    "  When the point has landed, the article is over. Stop there, or add one genuinely new "
    "thing -- a further consequence, a detail that changes what the arrival means. Do not "
    "write a closing paragraph because articles are expected to have one, and never end by "
    "saying the arrival again in other words.\n"
    "  Metaphor and personality belong here, used sparingly, and never after the point has "
    "already landed."
)

_NO_FABRICATION = (
    "You may not invent a factual state about the world, a person, the source, or an "
    "event. You may not write first-person lived experience, testimony, or biography for "
    "anyone. Interpretation may go beyond what the source concludes; it may never add "
    "facts the source does not contain.\n"
    "  A reading of how something works is not a finding about how the world works. When "
    "you say what a design, an object or an arrangement makes visible, keep the claim "
    "about that thing. Do not let it widen, in the next sentence, into a general truth "
    "about cognition, perception, behaviour, institutions or outcomes -- that the mind "
    "does X, that people generally do Y, that an institution always Z. Watch the grammar: "
    "\"this design sequences composition then detail\" is a claim about the design, and "
    "\"perception runs that sequence too fast to notice\" is a claim about everyone, and "
    "the second does not follow from the first. Where such a general claim is doing real "
    "work in the argument, the source must support it, or you must mark it as a reading "
    "rather than an established fact, or it must go."
)


def _source_block(source_text: str, sha: str) -> str:
    """The anchor. Before the Research Pack this was the whole authorised corpus; it is
    now the first source in it, and the one Discovery's anchor quote must come from."""
    return ("ANCHOR SOURCE (sha256 %s):\n"
            "<<<SOURCE\n%s\nSOURCE>>>\n" % (sha[:16], source_text))


PACK_SOURCE_CHARS = 3000        # per non-anchor source, per prompt


def pack_material_block(pack: dict | None, per_source_chars: int = PACK_SOURCE_CHARS) -> str:
    """Render the authorised material a pack adds beyond the anchor.

    ONE renderer on purpose: the Writer and the grounder are given the same spans, so
    the grounder can never mark as unsupported a fact it was not shown. Every block
    carries its source_id, role, publisher and URL, so a claim in the finished article
    can be traced to bytes that were fetched and hashed. Verified excerpts come first
    because they are the spans the pack vouches for; the window after them is context.
    """
    if not pack:
        return ""
    others = [s for s in pack.get("sources", []) if s.get("role") != "ANCHOR"]
    if not others:
        return ("\nRESEARCH PACK\n  No source beyond the anchor was fetched. The anchor "
                "is the only authorised material.\n")
    suff = (pack.get("sufficiency") or {}).get("verdict", "")
    out = ["\nRESEARCH PACK -- authorised material, each span traceable to fetched bytes"]
    if pack.get("subject"):
        out.append("  SUBJECT RESEARCHED: %s" % pack["subject"])
    if pack.get("subject_span"):
        out.append("  The anchor covers more than one subject. Only the subject above "
                   "was researched, and it is the only one available: this passage of "
                   "the anchor, and nothing around it --\n    \"%s\"\n  Ground the "
                   "reading inside that passage. Another item in the same source may "
                   "look more promising; it has no research behind it and is not on "
                   "offer." % pack["subject_span"][:600])
    if suff in ("SHORT_ARTICLE", "NARROW"):
        out.append("  RESEARCH VERDICT: %s -- the material supports a short, narrow "
                   "piece. Keep the route small and the target range low; do not reach "
                   "for the length a fuller pack would have earned." % suff)
    elif suff:
        out.append("  RESEARCH VERDICT: %s" % suff)
    for s in others:
        out.append("\n[%s] role=%s  publisher=%s  url=%s\n  %s"
                   % (s["source_id"], s["role"], s.get("publisher", ""), s["url"],
                      s.get("why_relevant", "")))
        for ex in (s.get("excerpts") or []):
            out.append("  EXCERPT [%s]: %s" % (s["source_id"], ex))
        text = (s.get("text") or "")[:per_source_chars]
        if text:
            out.append("  <<<%s\n%s\n%s>>>" % (s["source_id"], text, s["source_id"]))
    out.append("\nA fact may come from the anchor or from any source above, and must "
               "carry its source's identity in your reasoning. Nothing outside these "
               "blocks is authorised material: not a search result, not a summary, not "
               "your own knowledge of the subject.")
    return "\n".join(out) + "\n"


# ── DISCOVERY ──────────────────────────────────────────────────────────────────
DISCOVERY_SYSTEM = (
    "You are the discovery stage of an editorial engine. You read one source and "
    "establish what a disability-informed way of perceiving makes knowable about the "
    "subject that the dominant framing misses.\n\n"
    "The commissioning question is NOT 'find a disability angle'. It is: what does this "
    "way of perceiving reveal about how the thing actually works?\n\n"
    "Keep three kinds of statement strictly apart and never let one borrow the authority "
    "of another:\n"
    "  SOURCE FACT -- traceable to the supplied bytes\n"
    "  EDITORIAL INTERPRETATION -- what the reading reveals\n"
    "  EDITORIAL GUIDANCE -- what the writer must and must not do\n\n"
    + _NO_FABRICATION +
    "\n\nIf the source carries no such mechanism, say so plainly in `disturbance` and set "
    "`commissionable` false. A refusal is a valid, useful outcome; a forced angle is not."
)


def discovery_prompt(source_text: str, sha: str, pack: dict | None = None) -> str:
    return (
        _source_block(source_text, sha) +
        pack_material_block(pack) +
        "\nReply with JSON only:\n"
        '{\n'
        '  "commissionable": true|false,\n'
        '  "dominant_reading": "how this subject is normally understood -- the framing a '
        'general reader would arrive with",\n'
        '  "source_anchor_quote": "ONE clause or sentence copied CHARACTER-FOR-CHARACTER '
        'from the source above -- the exact span this whole reading rests on. It is '
        'checked against the source programmatically and the run is rejected if it is '
        'not an exact span, so do not paraphrase, do not merge two places, and do not '
        'tidy the punctuation.",\n'
        '  "disturbance": "the specific detail IN THE SOURCE where that reading stops '
        'holding, in your own words. This is prose and may paraphrase -- the exact span '
        'lives in source_anchor_quote.",\n'
        '  "perceptual_instrument": "the disability-informed way of perceiving used as an '
        'instrument here -- what it is tuned to notice. Name a capacity, not a persona '
        'and not an identity claim.",\n'
        '  "what_becomes_knowable": "the mechanism that instrument reveals, stated as a '
        'claim about how the thing works. This is EDITORIAL INTERPRETATION.",\n'
        '  "source_facts": ["the specific facts from the source the argument depends on, '
        'each traceable to the bytes above"],\n'
        '  "evidence_gaps": ["what the source does NOT establish, that a reader might '
        'assume it does"],\n'
        '  "grounding_boundaries": "EDITORIAL GUIDANCE, binding on the writer: what may '
        'not be named, asserted, characterised or staged because the source does not '
        'support it. Be specific and concrete."\n'
        '}\n'
    )


def discover(provider, source_text: str, sha: str, pack: dict | None = None) -> dict:
    c = provider.complete(DISCOVERY_SYSTEM, discovery_prompt(source_text, sha, pack),
                          max_tokens=2200)
    p = parse_json_object(c.text)
    p["_provider"] = c.identity()
    return p


# ── ARTICLE FORM ───────────────────────────────────────────────────────────────
# FORM-1.3 is evidence about structural discipline, not a universal geometry. The
# principles below are what transferred; the Edinburgh route did not, and must not be
# reproduced as a template.
FORM_SYSTEM = (
    "You are the article-form stage. You decide the SHAPE of one article from the "
    "material you are given. You do not write prose.\n\n"
    "Form follows material. There is no house structure and no template to fill: the "
    "route must be the one this material needs, and a different source should produce a "
    "different route.\n\n"
    "Binding principles:\n"
    "  - Counter-material is placed by FUNCTION, where it does work, not parked in a "
    "balance paragraph.\n"
    "  - Ownership is clear: every movement states whose claim it is carrying.\n"
    "  - The arrival is TERMINAL. The article stops there.\n"
    "  - No post-arrival explanation. Nothing after the arrival unless genuinely new "
    "material changes what the arrival means.\n"
    "  - The burden is carried by the material in sequence, not by assertion.\n"
    "  - A movement carried only by a re-reading of the previous movement's material is "
    "not a movement. Movements are separated by material -- a different fact, person, "
    "object, document, date or example -- not by a different angle on the same one. If the "
    "material supports three movements, build three; if it supports two, build two, and "
    "set target_words to match.\n"
    "  - Every movement does work no other movement does. If two movements would make "
    "the same point in different words, they are one movement. A route that circles a "
    "single insight several times is a route with one movement in it, not several, and "
    "the writer downstream cannot fix that -- it must follow the shape you decide, so "
    "restatement you build in is restatement that gets written.\n"
    "  - The article opens on the thing itself. The first movement establishes what the "
    "concrete subject is -- the object, the project, the person, what was made or done -- "
    "before any movement interprets it.\n"
    "  - No movement exists to restate the arrival. A movement that previews the "
    "conclusion, and a movement that repeats it afterwards in other words, are both "
    "movements that should not be in the route.\n"
    "  - The jobs a route usually has to do, in the order they usually fall: establish "
    "the concrete subject; show how it works; name what that makes visible; develop that "
    "consequence; mark what the source does and does not establish; arrive. This is the "
    "work, NOT a template -- form follows material, so where this material needs fewer "
    "movements use fewer, and where it genuinely needs a different sequence use that "
    "instead. What is binding is that no movement duplicates another's job.\n"
    "  - Write the route, the arrival and the burden in plain, concrete language, naming "
    "the actual thing each movement works on. The writer downstream inherits your "
    "vocabulary: a route written in conceptual nouns produces an article written in "
    "conceptual nouns.\n"
    "  - The last movement of the route IS the arrival. They are one act, not two. Do not "
    "place a movement after it, and do not write an arrival that says again what a movement "
    "already said.\n"
    "  - target_words is the smallest range in which this argument actually completes, "
    "not a house length. Judge it from the material: a claim that resolves in six hundred "
    "words gets six hundred. For a single source of ordinary richness the honest range is "
    "usually somewhere near 500 to 650 words; going higher needs material you actually "
    "have, not another pass over the same idea. Never widen it to make room for "
    "restatement."
)


def form_prompt(discovery: dict, source_text: str, sha: str,
                pack: dict | None = None) -> str:
    return (
        _source_block(source_text, sha) +
        pack_material_block(pack) +
        "\nMATERIAL FROM DISCOVERY:\n"
        "  dominant reading   : %s\n"
        "  source anchor      : %s\n"
        "  disturbance        : %s\n"
        "  instrument         : %s\n"
        "  what becomes knowable: %s\n"
        "  source facts       : %s\n"
        "  evidence gaps      : %s\n"
        % (discovery.get("dominant_reading", ""),
           discovery.get("source_anchor_quote", ""), discovery.get("disturbance", ""),
           discovery.get("perceptual_instrument", ""),
           discovery.get("what_becomes_knowable", ""),
           "; ".join(discovery.get("source_facts", [])[:8]),
           "; ".join(discovery.get("evidence_gaps", [])[:6])) +
        "\nReply with JSON only:\n"
        '{\n'
        '  "route": ["each movement of the article, in order, as an instruction about '
        'what that movement does with which material -- not prose"],\n'
        '  "motion": "the shape of the argument in three words, e.g. narrows -> '
        'accumulates -> recurs",\n'
        '  "arrival": "the terminal claim the article arrives at. The article stops '
        'here.",\n'
        '  "burden": "what carries the argument, and what is deliberately excluded "'
        '(no remedy, no second arrival, no persona voice, and so on)",\n'
        '  "target_words": [min, max]  // smallest range in which this argument completes; do not pad\n'
        '}\n'
    )


def make_form(provider, discovery: dict, source_text: str, sha: str,
              pack: dict | None = None) -> dict:
    c = provider.complete(FORM_SYSTEM, form_prompt(discovery, source_text, sha, pack),
                          max_tokens=1800)
    p = parse_json_object(c.text)
    if isinstance(p.get("target_words"), list) and len(p["target_words"]) == 2:
        p["target_words"] = [int(p["target_words"][0]), int(p["target_words"][1])]
    p["_provider"] = c.identity()
    return p


# ── WRITER INPUT ───────────────────────────────────────────────────────────────
def build_writer_input(article_form: dict, discovery: dict,
                       source_text: str, sha: str, byline: str,
                       pack: dict | None = None) -> dict:
    """Assemble the writer's instruction. Deterministic -- no model call.

    Contains ONLY: the source, the Form, the grounding boundaries, the byline, and the
    prose doctrine. The Form owns sequence, so the writer is not asked to choose a
    structure; and no persona material is present at all, because persona does not own
    prose architecture in this design.
    """
    route = "\n".join("  %d. %s" % (i, m) for i, m in enumerate(article_form["route"], 1))
    prompt = (
        "Write one article. Follow the form exactly; the shape is already decided.\n\n"
        + _source_block(source_text, sha) + pack_material_block(pack) +
        "\nFORM\n"
        "  motion : %s\n"
        "  route  :\n%s\n"
        "  arrival: %s\n"
        "           (the last movement of the route and this arrival are the same act, not "
        "two: write it once, there, and stop)\n"
        "  burden : %s\n"
        "  length : %s-%s words\n"
        % (article_form.get("motion", ""), route, article_form["arrival"],
           article_form["burden"],
           article_form.get("target_words", [900, 1200])[0],
           article_form.get("target_words", [900, 1200])[1]) +
        "\nSOURCE ANCHOR (verified verbatim in the source; the argument rests on it)\n"
        "  %s\n" % discovery.get("source_anchor_quote", "") +
        "\nWHAT THE READING MAKES KNOWABLE (the article's argument)\n  %s\n"
        % discovery.get("what_becomes_knowable", "") +
        "\nGROUNDING BOUNDARIES (binding)\n%s\n" % discovery.get("grounding_boundaries", "") +
        "\n" + _NO_FABRICATION +
        "\n\nBYLINE\n  %s -- a recurring editorial voice of this publication. Write in "
        "its register. It is not a person with a biography, and you must not give it "
        "lived experience, memories, or a body.\n" % byline +
        "\nUSING THE MATERIAL\n"
        "  Write from the material above and from nothing else. Where a source gives you "
        "a person, a date, a number, a mechanism, a decision or its own wording, use it: "
        "that is what the material is for, and an article carried by facts is the point "
        "of having gathered them. Do not name a source in the prose merely to show it "
        "was read, and do not add a fact you happen to know that is not in these blocks. "
        "If the material does not establish something the argument needs, the argument "
        "changes -- the material does not.\n"
        "\nPROSE\n  %s\n" % PROSE_DOCTRINE +
        "\nHEADLINE\n"
        "  Begin your output with one line in exactly this form:\n"
        "    TITLE: <headline>\n"
        "  It names what THIS article is about -- the subject given to you above, the one "
        "you are actually writing on. The source may be a roundup or list covering several "
        "unrelated items, and its own headline may name a different one; that headline is "
        "provenance metadata, not yours. Do not copy it. Ordinary words, and no padded "
        "subtitle after a colon.\n"
        "\nArrive at the arrival and stop. Stop when the argument is complete: the word "
        "range above is the form's estimate and an upper bound, never a quota. If the "
        "argument finishes in six hundred words then six hundred words is the right "
        "length, and coming in under the range is a good outcome, not a failure. A "
        "shorter article that has finished beats a longer one that restates itself, and "
        "no paragraph is ever added to reach a number. After the TITLE line and one "
        "blank line, output the article body only: no frontmatter, no notes.\n"
    )
    from .contracts import sha256_text
    return {"prompt_text": prompt, "prompt_sha256": sha256_text(prompt),
            "byline": byline}


WRITER_SYSTEM = (
    "You write one article to an already-decided form. You do not redesign the "
    "structure, you do not add a summary, and you do not explain the article after it "
    "arrives. " + _NO_FABRICATION
)


# Case-insensitive: the instruction asks for "TITLE:", but a model that returns
# "Title:" has still complied, and treating that as prose would put the headline
# into the article body.
_TITLE_LINE = re.compile(r"^\s*TITLE\s*:\s*(.+?)\s*$", re.IGNORECASE)


def split_title(text: str) -> tuple[str, str]:
    """Split a leading `TITLE: ...` line off a completion.

    The title is REMOVED from the returned body, so grounding, the invariants and the
    candidate all see exactly the prose they saw before the writer was asked for a
    headline -- this adds a field, it does not change what the article text is. A
    completion without the line is returned unchanged with an empty title, which keeps
    an older or non-compliant model reply a valid WRITER_OUTPUT rather than a failure.
    """
    stripped = text.lstrip("\n")
    lines = stripped.splitlines()
    if not lines:
        return "", text
    m = _TITLE_LINE.match(lines[0])
    if not m:
        return "", text
    return m.group(1).strip(), "\n".join(lines[1:]).lstrip("\n")


def write(provider, writer_input: dict) -> dict:
    from .contracts import sha256_text
    try:
        c = provider.complete(WRITER_SYSTEM, writer_input["prompt_text"], max_tokens=4000)
    except Exception as e:                                   # provider failure HOLDs
        return {"article_text": "", "article_sha256": sha256_text(""),
                "provider_status": "failed", "provider_error": str(e)[:300]}
    title, body = split_title(c.text)
    return {"article_text": body, "article_sha256": sha256_text(body),
            "title": title, "provider_status": "ok", "_provider": c.identity()}


# ── WRITER GROUNDING ───────────────────────────────────────────────────────────
# Receives writer output + source ONLY. Not the Form: grounding cannot change shape.
GROUNDING_SYSTEM = (
    "You are the writer-grounding stage. You compare a finished draft against the one "
    "authorised source and classify every factual claim the draft makes.\n\n"
    "Three classifications, and the distinction is the whole job:\n"
    "  SUPPORTED               -- the source establishes it. Do not report these.\n"
    "  LEGITIMATE_INTERPRETATION -- goes beyond what the source concludes, but invents "
    "no new factual state about the world, a person, the source or an event. This is "
    "ALLOWED. Report it only when it is worth recording.\n"
    "  TRUE_UNCERTAIN          -- you cannot tell from the source alone.\n"
    "  TRUE_UNSUPPORTED        -- the draft asserts a factual state the source does not "
    "contain: a name, number, date, quotation, event, causal claim, or an attributed "
    "motive or feeling.\n\n"
    "Interpretation is not a defect. Invented fact is. Judge the claim, never the prose."
)


def ground_prompt(article_text: str, source_text: str, sha: str,
                  pack: dict | None = None) -> str:
    return (
        _source_block(source_text, sha) +
        pack_material_block(pack) +
        "\nDRAFT UNDER REVIEW:\n<<<DRAFT\n%s\nDRAFT>>>\n" % article_text +
        "\nReply with JSON only:\n"
        '{\n'
        '  "findings": [\n'
        '    {"id": "F1",\n'
        '     "quote": "the exact sentence or clause from the DRAFT, verbatim",\n'
        '     "classification": "TRUE_UNSUPPORTED" | "TRUE_UNCERTAIN" | '
        '"LEGITIMATE_INTERPRETATION",\n'
        '     "why": "what the source does or does not establish",\n'
        '     "repairable": true|false,\n'
        '     "suggested_patch": "a minimal replacement for that clause that the source '
        'DOES support, or empty if not repairable"}\n'
        '  ]\n'
        '}\n'
        "Report every TRUE_UNSUPPORTED and TRUE_UNCERTAIN claim. An empty findings list "
        "means the draft is fully grounded.\n"
    )


def ground(provider, article_text: str, source_text: str, sha: str,
           pack: dict | None = None) -> dict:
    c = provider.complete(GROUNDING_SYSTEM, ground_prompt(article_text, source_text, sha, pack),
                          max_tokens=2600)
    p = parse_json_object(c.text)
    findings = p.get("findings") or []
    for i, f in enumerate(findings, 1):
        f.setdefault("id", "F%d" % i)
    return {"status": "settled", "findings": findings, "_provider": c.identity()}


# ── PATCH-ONLY REPAIR ──────────────────────────────────────────────────────────
def repair(article_text: str, findings: list) -> dict | None:
    """Apply suggested patches by exact clause substitution. Deterministic, no model.

    Patch-only by construction: each patch replaces one quoted clause with its
    suggested replacement. There is no rewrite path here, and `verification` counts
    what actually happened rather than asserting success.
    """
    from .contracts import sha256_text
    targets = [f for f in findings
               if f.get("classification") == "TRUE_UNSUPPORTED"
               and f.get("repairable") and (f.get("suggested_patch") or "").strip()
               and f.get("quote")]
    if not targets:
        return None
    text = article_text
    applied, failed = [], []
    for f in targets:
        q = f["quote"]
        if q in text:
            text = text.replace(q, f["suggested_patch"], 1)
            applied.append({"finding_id": f["id"], "removed": q,
                            "inserted": f["suggested_patch"]})
        else:
            failed.append(f["id"])
    if not applied:
        return None
    residual = sum(1 for f in targets if f["quote"] in text)
    return {
        "mode": "patch_only",
        "patches": applied,
        "article_text": text,
        "article_sha256": sha256_text(text),
        "unpatched_finding_ids": failed,
        # Placeholder only. runner.py replaces this wholesale with the measured
        # account once the recheck has run; the defaults here are the fail-closed
        # shape for a repair whose verification never happened.
        "verification": {
            "residual": residual,
            "introduced": 0,
            "reclassified": 0,
            "unresolved": 0,
            # every edit is one recorded substitution; nothing else was touched
            "unrelated_edits": 0,
        },
    }

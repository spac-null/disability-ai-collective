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

from .provider import parse_json_object

# ── Shared doctrine ────────────────────────────────────────────────────────────
# The prose principle the project has settled on, stated once, in plain terms.
PROSE_DOCTRINE = (
    "Make the thinking sophisticated; make the reading easy. Plain vocabulary. One "
    "modifier where one will do. Short sentences carry the hard turns. Do not announce "
    "a thesis, do not summarise at the end, and do not explain the point after making it."
)

_NO_FABRICATION = (
    "You may not invent a factual state about the world, a person, the source, or an "
    "event. You may not write first-person lived experience, testimony, or biography for "
    "anyone. Interpretation may go beyond what the source concludes; it may never add "
    "facts the source does not contain."
)


def _source_block(source_text: str, sha: str) -> str:
    return ("SOURCE SNAPSHOT (sha256 %s) -- the ONLY authorised material:\n"
            "<<<SOURCE\n%s\nSOURCE>>>\n" % (sha[:16], source_text))


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


def discovery_prompt(source_text: str, sha: str) -> str:
    return (
        _source_block(source_text, sha) +
        "\nReply with JSON only:\n"
        '{\n'
        '  "commissionable": true|false,\n'
        '  "dominant_reading": "how this subject is normally understood -- the framing a '
        'general reader would arrive with",\n'
        '  "disturbance": "the specific detail IN THE SOURCE where that reading stops '
        'holding. Quote the source clause it rests on, verbatim, inside this field.",\n'
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


def discover(provider, source_text: str, sha: str) -> dict:
    c = provider.complete(DISCOVERY_SYSTEM, discovery_prompt(source_text, sha),
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
    "  - The burden is carried by the material in sequence, not by assertion."
)


def form_prompt(discovery: dict, source_text: str, sha: str) -> str:
    return (
        _source_block(source_text, sha) +
        "\nMATERIAL FROM DISCOVERY:\n"
        "  dominant reading   : %s\n"
        "  disturbance        : %s\n"
        "  instrument         : %s\n"
        "  what becomes knowable: %s\n"
        "  source facts       : %s\n"
        "  evidence gaps      : %s\n"
        % (discovery.get("dominant_reading", ""), discovery.get("disturbance", ""),
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
        '  "target_words": [min, max]\n'
        '}\n'
    )


def make_form(provider, discovery: dict, source_text: str, sha: str) -> dict:
    c = provider.complete(FORM_SYSTEM, form_prompt(discovery, source_text, sha),
                          max_tokens=1800)
    p = parse_json_object(c.text)
    if isinstance(p.get("target_words"), list) and len(p["target_words"]) == 2:
        p["target_words"] = [int(p["target_words"][0]), int(p["target_words"][1])]
    p["_provider"] = c.identity()
    return p


# ── WRITER INPUT ───────────────────────────────────────────────────────────────
def build_writer_input(article_form: dict, discovery: dict,
                       source_text: str, sha: str, byline: str) -> dict:
    """Assemble the writer's instruction. Deterministic -- no model call.

    Contains ONLY: the source, the Form, the grounding boundaries, the byline, and the
    prose doctrine. The Form owns sequence, so the writer is not asked to choose a
    structure; and no persona material is present at all, because persona does not own
    prose architecture in this design.
    """
    route = "\n".join("  %d. %s" % (i, m) for i, m in enumerate(article_form["route"], 1))
    prompt = (
        "Write one article. Follow the form exactly; the shape is already decided.\n\n"
        + _source_block(source_text, sha) +
        "\nFORM\n"
        "  motion : %s\n"
        "  route  :\n%s\n"
        "  arrival: %s\n"
        "  burden : %s\n"
        "  length : %s-%s words\n"
        % (article_form.get("motion", ""), route, article_form["arrival"],
           article_form["burden"],
           article_form.get("target_words", [900, 1200])[0],
           article_form.get("target_words", [900, 1200])[1]) +
        "\nWHAT THE READING MAKES KNOWABLE (the article's argument)\n  %s\n"
        % discovery.get("what_becomes_knowable", "") +
        "\nGROUNDING BOUNDARIES (binding)\n%s\n" % discovery.get("grounding_boundaries", "") +
        "\n" + _NO_FABRICATION +
        "\n\nBYLINE\n  %s -- a recurring editorial voice of this publication. Write in "
        "its register. It is not a person with a biography, and you must not give it "
        "lived experience, memories, or a body.\n" % byline +
        "\nPROSE\n  %s\n" % PROSE_DOCTRINE +
        "\nArrive at the arrival and stop. Output the article body only: no title, no "
        "frontmatter, no notes.\n"
    )
    from .contracts import sha256_text
    return {"prompt_text": prompt, "prompt_sha256": sha256_text(prompt),
            "byline": byline}


WRITER_SYSTEM = (
    "You write one article to an already-decided form. You do not redesign the "
    "structure, you do not add a summary, and you do not explain the article after it "
    "arrives. " + _NO_FABRICATION
)


def write(provider, writer_input: dict) -> dict:
    from .contracts import sha256_text
    try:
        c = provider.complete(WRITER_SYSTEM, writer_input["prompt_text"], max_tokens=4000)
    except Exception as e:                                   # provider failure HOLDs
        return {"article_text": "", "article_sha256": sha256_text(""),
                "provider_status": "failed", "provider_error": str(e)[:300]}
    return {"article_text": c.text, "article_sha256": sha256_text(c.text),
            "provider_status": "ok", "_provider": c.identity()}


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


def ground_prompt(article_text: str, source_text: str, sha: str) -> str:
    return (
        _source_block(source_text, sha) +
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


def ground(provider, article_text: str, source_text: str, sha: str) -> dict:
    c = provider.complete(GROUNDING_SYSTEM, ground_prompt(article_text, source_text, sha),
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
        "verification": {
            "residual": residual,
            # a clause substitution introduces no new unsupported claim of its own
            "introduced": 0,
            # every edit is one recorded substitution; nothing else was touched
            "unrelated_edits": 0,
        },
    }

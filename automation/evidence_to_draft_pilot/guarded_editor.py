"""
guarded_editor.py -- ONE bounded, reversible editing pass over a Writer draft.

WHAT IT IS FOR. Section 11 of the brief: an optional editor that improves the opening,
the order, the repetition, the sentence clarity and the referents of a draft, WITHOUT
touching the evidence or the article's substantive question. It proposes a batch of
patches, not a replacement essay, so that a single bad idea costs one patch instead of
the whole improvement.

HOW IT DIFFERS FROM PRODUCTION CONTINUITY. Production's Continuity stage is ALREADY
fail-safe -- `composition.run_story_architecture_composition` discards a semantically
dirty continuity edit whole and carries the Writer draft forward (see the CONTINUITY IS
FAIL-SAFE block there), and Prose Finish is fail-safe in the same way. So section 12's
requirement is not missing from production and this module does not duplicate it. What it
adds is GRANULARITY: production's unit of acceptance is the entire rewritten article, so
one invented relation loses every good sentence in the same pass. Here the unit is the
patch, and the batch is then re-checked IN COMBINATION before anything is accepted.

THE FOUR INVARIANTS, each with its own test:

  1. EXACT, UNAMBIGUOUS TARGETING. A patch names a literal substring of the document. If
     it occurs zero times, or more than once, the patch is REJECTED -- never
     fuzzy-matched, never applied to a guess. "Mechanical matching must be unambiguous."

  2. ATOMIC APPLICATION. Patches are validated, de-overlapped and sorted first; the
     document is rebuilt once from the surviving set. A rejected or overlapping patch
     cannot leave the document half-edited, because no patch is ever written into the
     document individually.

  3. THE WHOLE BATCH IS RE-CHECKED IN COMBINATION. Individually clean patches can add a
     relation together that neither adds alone, so the accepted text is compared against
     the PRE-EDIT text with the production semantic-delta validator
     (`new_engine_v1.continuity.validate_semantic_delta`) -- the same check production
     applies to Continuity, reused rather than reinvented. If the combined text fails,
     the ENTIRE batch is rejected.

  4. REJECTION RETURNS THE PRIOR BYTES, EXACTLY. On any rejection the result carries the
     unmodified input text and `accepted=False`. Section 12: rejecting an edit is not
     approving a draft -- so the result also carries `resolves_nothing=True` to make it
     impossible for a caller to read a rejection as a clean bill of health.

WHAT IT MAY NOT DO, enforced here rather than requested in the prompt:
  * no new sources and no outside factual knowledge -- a patch that introduces a number,
    entity or relation absent from the pre-edit draft is rejected by the delta check;
  * no quotation changes for rhythm -- a patch whose target or replacement crosses a
    quotation mark is rejected outright, before the model's purpose is even read;
  * no removal of an unresolved material fact to empty the article -- a patch that only
    deletes is capped, and a batch may not delete more than DELETE_BUDGET_CHARS.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUTOMATION = HERE.parent
if str(AUTOMATION) not in sys.path:
    sys.path.insert(0, str(AUTOMATION))

from new_engine_v1 import continuity as CE                        # noqa: E402

PROMPT_VERSION = "guarded-editor-v1"

# A batch may not delete more than this many characters in total. An editor that empties
# a paragraph to make an unresolved fact go away is doing the one thing section 11 bans.
DELETE_BUDGET_CHARS = 400

# Patches per batch. A bounded batch is the point; an editor that wants forty changes is
# rewriting the essay.
MAX_PATCHES = 14

# WHAT COUNTS AS A QUOTATION, and what is merely an apostrophe.
#
# The first version of this rule treated every ' and ’ as a quotation mark. Measured on
# the first live subject, that refused 3 of 9 otherwise-clean patches -- every one of
# them for an ORDINARY POSSESSIVE ("Taylor's", "Hurka's"), not for a quotation. The rule
# was protecting nothing and costing the editor a third of its work.
#
# So: a double quote of any shape is always a quotation boundary. A single quote is one
# ONLY when it is not sitting between two word characters -- which is exactly the
# difference between «he said 'no'» and «Taylor's». Contractions and possessives pass;
# a real single-quoted phrase still does not.
_DOUBLE_QUOTE = re.compile(r"[\"“”]")
_SINGLE_QUOTE_NOT_APOSTROPHE = re.compile(r"(?<![\w])['‘’]|['‘’](?![\w])")


def crosses_quotation(text: str) -> bool:
    return bool(_DOUBLE_QUOTE.search(text or "")
                or _SINGLE_QUOTE_NOT_APOSTROPHE.search(text or ""))

EDITOR_SYSTEM = """You are a line editor working on ONE draft article.

You do not have the sources. You may not add facts, names, numbers, dates, places,
causes, intentions, comparisons or negations. You may not change what the article
claims. You may not touch anything inside quotation marks.

What you MAY improve:
  - the opening, if it buries the real subject
  - the order of material, if a later passage needs an earlier one
  - repetition, including source-bookkeeping prose ("the report states", "according to
    the document") where the attribution is already clear
  - sentence clarity: length, subordination, a verb that does more work
  - unclear referents: a pronoun or "the study" with no nearby antecedent

Propose a BOUNDED BATCH of patches. Each patch replaces one exact, literal, UNIQUE
substring of the article. Copy the target text character for character from the article,
including punctuation. If a phrase appears more than once, extend the target until it is
unique, or leave it alone.

Reply with JSON only, no prose around it:

{"patches": [
  {"target": "<exact literal substring of the article>",
   "replacement": "<the text that replaces it; may be empty to delete>",
   "purpose": "OPENING|ORDER|REPETITION|CLARITY|REFERENT",
   "touches": "<any fact, attribution or qualifier this patch touches, or NONE>"}
]}

If the draft does not need editing, reply {"patches": []}. That is a valid answer and a
better one than an invented improvement."""


def editor_prompt(article_text: str) -> str:
    return ("THE DRAFT\n\n" + article_text
            + "\n\nPropose at most %d patches. JSON only." % MAX_PATCHES)


def parse_patches(reply: str) -> tuple:
    """(patches, errors). A reply that is not usable JSON is a transport-shaped failure,
    reported as such rather than silently treated as 'no patches'."""
    txt = (reply or "").strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```\s*$", "", txt)
    i, j = txt.find("{"), txt.rfind("}")
    if i < 0 or j <= i:
        return [], ["the editor reply carries no JSON object"]
    try:
        obj = json.loads(txt[i:j + 1])
    except Exception as exc:                                       # noqa: BLE001
        return [], ["the editor reply is not valid JSON: %s" % exc]
    pat = obj.get("patches")
    if not isinstance(pat, list):
        return [], ["the editor reply carries no 'patches' list"]
    out, errs = [], []
    for n, p in enumerate(pat):
        if not isinstance(p, dict):
            errs.append("patch %d is not an object" % n)
            continue
        t = p.get("target")
        r = p.get("replacement", "")
        if not isinstance(t, str) or not t:
            errs.append("patch %d has no target" % n)
            continue
        if not isinstance(r, str):
            errs.append("patch %d has a non-string replacement" % n)
            continue
        out.append({"target": t, "replacement": r,
                    "purpose": str(p.get("purpose") or "")[:40],
                    "touches": str(p.get("touches") or "")[:200]})
    return out, errs


def screen_patches(article_text: str, patches: list) -> tuple:
    """Per-patch mechanical screening. Returns (kept, rejected).

    Nothing here consults the model's stated purpose: a patch earns its place by being
    exactly locatable and by not crossing a quotation, both of which are properties of
    the text rather than claims about intent.
    """
    kept, rejected = [], []
    if len(patches) > MAX_PATCHES:
        for p in patches[MAX_PATCHES:]:
            rejected.append(dict(p, reason="batch exceeds %d patches" % MAX_PATCHES))
        patches = patches[:MAX_PATCHES]

    spans = []
    for p in patches:
        t = p["target"]
        n = article_text.count(t)
        if n == 0:
            rejected.append(dict(p, reason="target does not occur in the article"))
            continue
        if n > 1:
            rejected.append(dict(p, reason="target occurs %d times -- ambiguous" % n))
            continue
        if crosses_quotation(t) or crosses_quotation(p["replacement"]):
            rejected.append(dict(p, reason="patch crosses a quotation mark"))
            continue
        start = article_text.index(t)
        spans.append((start, start + len(t), p))

    # OVERLAP. Two patches that touch the same characters cannot both be honoured, and
    # applying one of them silently would make the batch order-dependent. Both go.
    spans.sort(key=lambda s: s[0])
    overlapping = set()
    for a in range(len(spans)):
        for b in range(a + 1, len(spans)):
            if spans[b][0] < spans[a][1]:
                overlapping.add(a)
                overlapping.add(b)
    for idx, (s, e, p) in enumerate(spans):
        if idx in overlapping:
            rejected.append(dict(p, reason="patch overlaps another patch"))
        else:
            kept.append((s, e, p))

    deleted = sum((e - s) - len(p["replacement"]) for s, e, p in kept)
    if deleted > DELETE_BUDGET_CHARS:
        for s, e, p in kept:
            rejected.append(dict(p, reason="batch deletes %d chars, over the %d budget"
                                 % (deleted, DELETE_BUDGET_CHARS)))
        kept = []
    return kept, rejected


def apply_batch(article_text: str, kept: list) -> str:
    """Rebuild the document ONCE from the surviving patches. Never mutates in place, so a
    rejected patch cannot leave a partial edit behind."""
    out, cursor = [], 0
    for s, e, p in sorted(kept, key=lambda x: x[0]):
        out.append(article_text[cursor:s])
        out.append(p["replacement"])
        cursor = e
    out.append(article_text[cursor:])
    return "".join(out)


def guarded_edit(provider, article_text: str, *, allow_relation_growth=()) -> dict:
    """One editor call, screened, applied atomically and re-checked in combination.

    The returned dict ALWAYS carries usable article bytes in `article_text`: the edited
    text when the batch was accepted, the unmodified input when it was not.
    """
    reply = provider.complete(EDITOR_SYSTEM, editor_prompt(article_text))
    ident = reply.identity() if hasattr(reply, "identity") else {}
    patches, parse_errs = parse_patches(reply.text)

    result = {
        "prompt_version": PROMPT_VERSION,
        "provider": ident,
        "model_calls": 1,
        "proposed": len(patches),
        "parse_errors": parse_errs,
        "article_text": article_text,
        "pre_edit_text": article_text,
        "accepted": False,
        "accepted_patches": [],
        "rejected_patches": [],
        "combined_delta_errors": [],
        # Section 12, stated on the object so no caller can forget it: a rejected edit
        # resolves nothing. Whatever was wrong with the prior draft is still wrong.
        "resolves_nothing": True,
    }
    if parse_errs and not patches:
        result["status"] = "EDITOR_REPLY_UNUSABLE"
        return result

    kept, rejected = screen_patches(article_text, patches)
    result["rejected_patches"] = rejected
    if not kept:
        result["status"] = "NO_PATCH_SURVIVED_SCREENING"
        return result

    edited = apply_batch(article_text, kept)

    # THE COMBINATION CHECK. Production's own validator, on the production question:
    # did editing add factual surface or a relation class? Reused, not reimplemented.
    delta_errs = CE.validate_semantic_delta(article_text, edited,
                                            allow_relation_growth=allow_relation_growth)
    result["semantic_delta"] = CE.semantic_delta(article_text, edited)
    if delta_errs:
        # THE WHOLE BATCH GOES. The prior candidate is returned byte-for-byte.
        result["combined_delta_errors"] = delta_errs
        result["rejected_patches"] = rejected + [
            dict(p, reason="whole batch rejected by the combined semantic-delta check")
            for _, _, p in kept]
        result["status"] = "BATCH_REJECTED_COMBINED_DELTA"
        return result

    result["article_text"] = edited
    result["accepted"] = True
    result["accepted_patches"] = [p for _, _, p in kept]
    result["status"] = "ACCEPTED"
    # An accepted edit still resolves nothing that was already wrong: it is a linguistic
    # improvement over prose whose factual standing is decided elsewhere.
    return result

"""
claims.py -- the claim-coverage backbone for GROUNDER V2 (SHADOW ONLY).

WHY THIS EXISTS
The production grounder asks one model call to decide BOTH what counts as a claim and
how it relates to the evidence, and the measurements say the instability lives in the
first half: on byte-identical input, findings appeared and disappeared (one claim was
present in 3 of 10 trials), finding counts drifted 2-5, and classifications flipped --
at temperature 0 as well as at the provider default.

So the claim list is taken away from the model. Sentences are segmented
deterministically and that list is the COVERAGE BACKBONE: a model may split or type a
sentence, and it may never erase one. Anything the model fails to resolve becomes
UNRESOLVED_BOUNDARY, which is a recorded state, not a silent omission and never a
finding against the writer.

Deliberately NOT here: any source, any support judgement, any prose repair. This module
never sees the Research Pack.
"""
from __future__ import annotations

import json
import re

from .contracts import sha256_text
from .provider import parse_json_object

# ── bounds (reported, not implicit) ───────────────────────────────────────────
MAX_SENTENCES_PER_BATCH = 8      # a whole-article pass truncated 2 of 5 times in probe D
MAX_BATCH_CHARS = 6_000
BATCH_MAX_TOKENS = 1_600
MAX_BATCHES_PER_ARTICLE = 8      # hard ceiling: 64 sentences typed per article

EMPIRICAL = "EMPIRICAL"
INTERPRETIVE = "INTERPRETIVE"
MIXED = "MIXED"
UNRESOLVED = "UNRESOLVED_BOUNDARY"
TYPES = (EMPIRICAL, INTERPRETIVE, MIXED)

# Same construction as the repository's existing splitter in orchestrator/gate.py,
# re-expressed here because new_engine_v1 may not import the orchestrator (the package
# purity test forbids it, and that boundary is worth more than the shared line).
_ABBR = r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bSt)(?<!\bNo)"
_SPLIT = re.compile(_ABBR + r"(?<=[.!?])\s+(?=[\"'“‘(]?[A-Z0-9])")


def segment(article_text: str) -> list:
    """Deterministic sentence backbone. Exact spans, stable ids, offsets into the
    ORIGINAL text -- replayable, and verifiable by substring alone."""
    text = article_text or ""
    out, pos, n = [], 0, 0
    for para in text.split("\n"):
        if not para.strip():
            pos += len(para) + 1
            continue
        start_para = text.index(para, pos)
        cursor = start_para
        for piece in _SPLIT.split(para):
            if not piece.strip():
                continue
            start = text.index(piece, cursor)
            end = start + len(piece)
            cursor = end
            n += 1
            out.append({"sentence_id": "S%03d" % n, "exact_span": piece,
                        "start": start, "end": end,
                        "sha256": sha256_text(piece)})
        pos = start_para + len(para) + 1
    return out


def verify_backbone(article_text: str, sentences: list) -> list:
    """Every span must still be exactly where it says it is. Cheap, deterministic,
    and it makes a silently rewritten backbone impossible."""
    bad = []
    for s in sentences:
        if article_text[s["start"]:s["end"]] != s["exact_span"]:
            bad.append("%s offsets do not match its span" % s["sentence_id"])
        if sha256_text(s["exact_span"]) != s["sha256"]:
            bad.append("%s hash does not match its span" % s["sentence_id"])
    return bad


# ── narrow type + atomicity pass ──────────────────────────────────────────────
TYPING_SYSTEM = (
    "You label sentences from one article. You are given no sources, you judge nothing "
    "true or false, and you never rewrite the article.\n\n"
    "For each sentence, two jobs and no others:\n"
    "  1. TYPE it: EMPIRICAL (it asserts a state of the world -- a fact, a date, a "
    "number, an attribution, a quotation), INTERPRETIVE (it offers a reading, a "
    "judgement or an implication rather than a state of the world), or MIXED (it does "
    "both in one sentence).\n"
    "  2. SPLIT it, only where the sentence asserts several materially independent "
    "things. 'A few pieces break the pattern -- the 1955 Temple by the Sea, the 1954 "
    "depiction of the Airlie oak -- but the density is the rule' asserts that each work "
    "exists with that title and date, AND that they are in the show: those are separate "
    "propositions and must be separate atoms. A sentence carrying one proposition gets "
    "exactly one atom, unchanged.\n\n"
    "An atom may resolve a pronoun so it stands alone. It is then a DERIVED "
    "proposition, not a quotation of the article, and you must say so. Never present a "
    "rewritten sentence as the article's own words, and never drop a sentence: every "
    "sentence_id you are given must come back."
)


def typing_prompt(batch: list) -> str:
    items = "\n".join('  {"sentence_id": "%s", "sentence": %s}'
                      % (s["sentence_id"], json.dumps(s["exact_span"]))
                      for s in batch)
    return (
        "SENTENCES:\n%s\n\nReply with JSON only, one entry per sentence_id above:\n"
        '{"sentences": [\n'
        '  {"sentence_id": "S001",\n'
        '   "type": "EMPIRICAL|INTERPRETIVE|MIXED",\n'
        '   "atoms": [{"claim": "one proposition", "verbatim": true|false,\n'
        '              "claim_type": "EMPIRICAL|INTERPRETIVE"}]}\n'
        "]}\n"
        "`verbatim` is true only when `claim` is a literal substring of the sentence.\n"
        % items)


def _batches(sentences: list) -> list:
    out, cur, size = [], [], 0
    for s in sentences:
        if cur and (len(cur) >= MAX_SENTENCES_PER_BATCH
                    or size + len(s["exact_span"]) > MAX_BATCH_CHARS):
            out.append(cur)
            cur, size = [], 0
        cur.append(s)
        size += len(s["exact_span"])
    if cur:
        out.append(cur)
    return out[:MAX_BATCHES_PER_ARTICLE]


def _unresolved(sentence: dict, why: str) -> dict:
    return {"sentence_id": sentence["sentence_id"],
            "parent_exact_span": sentence["exact_span"],
            "type": UNRESOLVED, "atoms": [], "unresolved_reason": why}


def identify(provider, article_text: str, sentences: list | None = None,
             deadline: float | None = None) -> dict:
    """Type and (where needed) split every sentence. Coverage is guaranteed by
    construction: the result has exactly one record per sentence_id, and a batch that
    fails for ANY reason -- provider error, truncation, invalid schema, a missing or
    unknown sentence_id, an atom that cannot be tied to its parent -- yields
    UNRESOLVED_BOUNDARY records rather than absent ones.

    `deadline` (2026-09-03) is plumbing only, optional and None by default so nothing
    about this function's behaviour changes when it is absent: provider.complete clamps
    each leg to what is left of it. It exists so identification counts toward the
    shadow's total wall clock rather than sitting outside it. Typing model, prompt,
    batching, atomicity and coverage semantics are untouched."""
    sentences = sentences if sentences is not None else segment(article_text)
    by_id = {s["sentence_id"]: s for s in sentences}
    records, calls, provider_ids = {}, 0, []
    for batch in _batches(sentences):
        calls += 1
        try:
            c = provider.complete(TYPING_SYSTEM, typing_prompt(batch),
                                  max_tokens=BATCH_MAX_TOKENS, temperature=0,
                                  deadline=deadline)
            provider_ids.append(c.identity())
            payload = parse_json_object(c.text)
            seen = {}
            for entry in (payload.get("sentences") or []):
                sid = entry.get("sentence_id")
                if sid not in by_id:
                    continue                       # unknown id: ignored, never invented
                seen[sid] = entry
            for s in batch:
                entry = seen.get(s["sentence_id"])
                if not entry:
                    records[s["sentence_id"]] = _unresolved(s, "sentence_id absent from reply")
                    continue
                records[s["sentence_id"]] = _record(s, entry)
        except Exception as e:                     # provider, truncation, schema
            for s in batch:
                records[s["sentence_id"]] = _unresolved(
                    s, "%s: %s" % (type(e).__name__, str(e)[:120]))
    for s in sentences:                            # batches past the ceiling
        records.setdefault(s["sentence_id"],
                           _unresolved(s, "batch ceiling reached (%d)" % MAX_BATCHES_PER_ARTICLE))
    ordered = [records[s["sentence_id"]] for s in sentences]
    return {"sentences": sentences, "records": ordered, "calls": calls,
            "coverage": {"sentences": len(sentences), "records": len(ordered),
                         "unresolved": sum(1 for r in ordered if r["type"] == UNRESOLVED),
                         "atoms": sum(len(r["atoms"]) for r in ordered)},
            "_provider": provider_ids}


def _record(sentence: dict, entry: dict) -> dict:
    stype = entry.get("type")
    if stype not in TYPES:
        return _unresolved(sentence, "type %r not in %s" % (stype, ", ".join(TYPES)))
    atoms_in = entry.get("atoms") or []
    if not atoms_in:
        return _unresolved(sentence, "no atoms returned")
    span_norm = " ".join(sentence["exact_span"].split()).lower()
    atoms = []
    for i, a in enumerate(atoms_in, 1):
        claim = (a.get("claim") or "").strip()
        if not claim:
            return _unresolved(sentence, "empty atom")
        ctype = a.get("claim_type") if a.get("claim_type") in (EMPIRICAL, INTERPRETIVE) \
            else (INTERPRETIVE if stype == INTERPRETIVE else EMPIRICAL)
        literal = " ".join(claim.split()).lower() in span_norm
        atoms.append({
            "atomic_id": "%s-A%d" % (sentence["sentence_id"], i),
            "atomic_claim": claim,
            "claim_type": ctype,
            "parent_sentence_id": sentence["sentence_id"],
            # The parent span is the authoritative article evidence. An atom that is not
            # a literal substring is DERIVED and must never be quoted as the writer's.
            "derivation": "VERBATIM" if literal else "DERIVED",
        })
    return {"sentence_id": sentence["sentence_id"],
            "parent_exact_span": sentence["exact_span"],
            "type": stype, "atoms": atoms}


def claims_for_classification(records: list) -> list:
    """EMPIRICAL atoms, plus the empirical half of MIXED. INTERPRETIVE atoms are routed
    elsewhere and UNRESOLVED_BOUNDARY sentences are never classified -- an identification
    failure must not become a verdict about the writer."""
    out = []
    for r in records:
        if r["type"] == UNRESOLVED:
            continue
        for a in r["atoms"]:
            if a["claim_type"] == EMPIRICAL:
                out.append(dict(a, parent_exact_span=r["parent_exact_span"],
                                parent_type=r["type"]))
    return out


def interpretation_candidates(records: list) -> list:
    return [dict(a, parent_exact_span=r["parent_exact_span"], parent_type=r["type"])
            for r in records if r["type"] != UNRESOLVED
            for a in r["atoms"] if a["claim_type"] == INTERPRETIVE]

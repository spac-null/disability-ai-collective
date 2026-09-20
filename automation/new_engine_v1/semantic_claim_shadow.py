#!/usr/bin/env python3
"""Semantic claim enrichment -- SHADOW ONLY.

WHAT THIS IS. A non-authoritative layer that sits AFTER the Claim Mapper has produced
its verified backbone and describes, in structured form, what the ARTICLE asserts:
attribution, qualifiers, relations, event referents, and which referents the article
does and does not settle. It was earned by a research pilot (2026-09-19/20) in which a
Claimify-style representation anchored 425/425 claims to exact article text and an
INDEPENDENT Codex audit found one genuine semantic error in 360 body assertions.

WHAT THIS IS NOT. It has no publication, Safety, Grounding, Fact Check, materiality or
repair authority, and nothing downstream reads it. It cannot cause a HOLD. If the
provider fails, times out, returns junk, or the validator rejects the artifact, the
article pipeline continues EXACTLY as it would have without this module -- that is the
whole contract, and the tests pin it.

WHY A SEPARATE LAYER. The current Claim Mapper already carries what it is good at:
exact offsets, exact spans, per-sentence hashes, verify_backbone, VERBATIM/DERIVED, and
EMPIRICAL/INTERPRETIVE/MIXED separation. Those strengths are not replaced or re-derived
here. This module consumes them and adds only what they cannot express.

DEFAULT OFF. With CRIPMINDS_SEMANTIC_CLAIM_SHADOW unset the module makes zero model
calls and produces no artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata

FLAG = "CRIPMINDS_SEMANTIC_CLAIM_SHADOW"
PROMPT_VERSION = "semantic-claim-shadow/2"
ARTIFACT_VERSION = 1

# A constrained enum rather than free text: an open vocabulary is unreviewable, and the
# research pilot showed the useful relations are a small closed set.
RELATION_TYPES = (
    "ATTRIBUTION", "QUALIFIER", "CAUSE", "CONSEQUENCE", "TEMPORAL", "COMPARISON",
    "CONDITION", "CONTAINMENT_SUBSET", "EVENT_IDENTITY", "COREFERENCE", "NEGATION",
    "OTHER",
)

# The one genuine semantic error the independent audit found was deictic
# over-resolution: "That is the perspective typical of ..." became "The floor of the
# house is the perspective ...", turning a demonstrative into an identity assertion.
# These are the surface forms that must be left unresolved unless the article settles
# them; the prompt names them explicitly and a fixture pins the exact failure.
# Forms whose CROSS-SENTENCE resolution is forbidden by default. These refer to
# propositions, situations, perspectives and other discourse units at least as often
# as they refer to a preceding noun phrase, so a confident-looking antecedent is
# frequently the wrong kind of thing. "That is the perspective typical of ..." became
# "The floor of the house is the perspective ...": a vantage point silently promoted
# into an identity predication. Entity pronouns are NOT in this set -- see
# ENTITY_PRONOUNS -- because "Maria entered. She sat down." is ordinary and safe.
DEICTIC_FORMS = ("this", "that", "these", "those", "such",
                 "the former", "the latter")

# Cross-sentence resolution is allowed for these when an exact antecedent span is
# anchored. The validator checks structure only; it never tries to prove the
# antecedent is semantically right, and it does not need to -- the layer is advisory.
ENTITY_PRONOUNS = ("he", "she", "they", "it", "him", "her", "them",
                   "his", "hers", "their", "theirs", "its")

RESOLUTION_TYPES = ("SAME_SENTENCE_EXPLICIT", "CROSS_SENTENCE_ENTITY_PRONOUN",
                    "CROSS_SENTENCE_NOMINAL_REPEAT", "OTHER_EXPLICIT")

CROSS_SENTENCE_DEICTIC_UNSAFE = "CROSS_SENTENCE_DEICTIC_UNSAFE"
UNRESOLVED_REFERENT_DROPPED = "UNRESOLVED_REFERENT_DROPPED_FROM_CLAIM"

# AN UNRESOLVED REFERENT MAY NOT BE RESOLVED IN THE CLAIM TEXT INSTEAD (2026-09-20).
# The deictic policy closed the `resolved_referents` route and the defect came straight
# back through the prose. Replay 3, draft 8a0dab48, sentence S021:
#
#   article      "That is the perspective typical of where wheelchair and accessibility
#                 seating is located in a theater."
#   unresolved   {"surface_form": "That", "reason_unresolved": "Demonstrative pointing
#                 outside this sentence; no identity construction inside the sentence
#                 supplies its target..."}
#   claim_text   "The floor of the house is the perspective typical of where wheelchair
#                 and accessibility seating is located in a theater.
#                 [DERIVED: pronoun 'that' resolved, not the article's wording]"
#   claim_type   EMPIRICAL
#
# The record contradicts itself: the referent is declared unresolvable and the resolution
# is performed anyway, one field along, where no rule looked. 22 of 443 semantic claims in
# that replay declared a referent unresolved whose surface form is absent from their own
# claim_text.
#
# The rule below is provenance only. It asks whether an explicitly unresolved surface form
# DISAPPEARED from the derived claim -- never whether the replacement means the same
# thing. A DERIVED atom may still rewrite freely around the referent; it may not delete
# the one token it has just said it cannot resolve.
_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
           "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00ab": '"',
           "\u00bb": '"', "\u2032": "'", "\u2033": '"'}


def _canon(text: str) -> str:
    """NFC, canonical quotes, collapsed whitespace, casefolded. Nothing else -- no
    stemming, no synonyms, no fuzzy matching. See the note above."""
    t = unicodedata.normalize("NFC", text or "")
    for a, b in _QUOTES.items():
        t = t.replace(a, b)
    return " ".join(t.split()).casefold()


def _contains_surface(haystack: str, surface: str) -> bool:
    """Whole-token occurrence of `surface` in `haystack`, both canonicalised.

    Word-bounded so "it" is not found inside "its" and "that" is not found inside
    "thatch"; a multi-word form ("the former") is matched as the phrase it is.
    """
    h, s = _canon(haystack), _canon(surface)
    if not s:
        return False
    return re.search(r"(?<![\w']){0}(?![\w'])".format(re.escape(s)), h) is not None


def enabled() -> bool:
    """OFF unless explicitly switched on. No other value counts as on."""
    return os.environ.get(FLAG, "").strip() == "1"


def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


SYSTEM = (
    "You describe what ONE article asserts. You are given no sources. You judge nothing "
    "true or false. You never rewrite the article and you never repair it.\n\n"
    "You receive a verified sentence backbone: exact spans with offsets and hashes, and "
    "the current atomization with each atom already typed EMPIRICAL or INTERPRETIVE and "
    "marked VERBATIM or DERIVED. Those judgements are authoritative. Do not overturn "
    "them. Your job is to add structure they cannot express.\n\n"
    "For each claim, where the article actually supports it, record:\n"
    "  attribution      - who the article says asserts this, the cue, and the content.\n"
    "  qualifiers       - restricting phrases, each bound to what it restricts.\n"
    "  relations        - typed, from the closed list, each with the article words that "
    "assert it.\n"
    "  event_referents  - the specific event/object/time the claim is bound to.\n"
    "  resolved_referents   - only where the article licenses the identity.\n"
    "  unresolved_referents - everywhere else.\n\n"
    "RULES THAT MATTER MORE THAN COVERAGE:\n"
    "* AMBIGUITY BEATS GUESSING, AND DEICTICS ARE THE HARD CASE. For this, that, these, "
    "those, such, the former, the latter: you may resolve ONLY when the SAME sentence "
    "contains an explicit identity construction that supplies the target. If the target "
    "would come from a different sentence, do NOT resolve it -- record an "
    "unresolved_referent instead. These words point at propositions, situations and "
    "perspectives as often as at nouns, so a plausible antecedent in the previous "
    "sentence is not enough. Turning a demonstrative into an identity assertion is the "
    "worst error you can make here.\n"
    "* AN UNRESOLVED REFERENT STAYS IN THE CLAIM TEXT. If you record a surface form as "
    "an unresolved_referent, claim_text MUST still contain that exact word. Writing "
    "\"That is the perspective ...\" as \"The floor of the house is the perspective ...\" "
    "performs the resolution you just said you could not make, and labelling it DERIVED "
    "does not license it. Rewrite everything else you need to; leave that word alone.\n"
    "* ENTITY PRONOUNS ARE DIFFERENT. he, she, they, it, his, her, their, its MAY be "
    "resolved across sentences when you can point at the exact antecedent words in the "
    "article. If you cannot, record an unresolved_referent.\n"
    "* EVERY RESOLUTION IS ANCHORED AT BOTH ENDS. A resolved_referent must give the "
    "surface form with its sentence and offsets, AND the target with its sentence and "
    "offsets, and target_text must be exactly the article substring at those offsets. A "
    "target you paraphrased is not a target.\n"
    "* SUBSET COUNTS STAY SUBSET COUNTS. 'eight of the most interesting pavilions' is a "
    "count of a SELECTION. Record it as CONTAINMENT_SUBSET with the subset, the count "
    "and the container. It must never become a total for the container.\n"
    "* QUALIFIERS STAY ON THEIR TARGET. 'by non-licensed resellers' restricts the claim "
    "it attaches to and must not drift.\n"
    "* ATTRIBUTION SURVIVES. 'The report says X caused Y' is a claim about the report. "
    "Never reduce it to 'X caused Y'.\n"
    "* INTERPRETATION STAYS INTERPRETIVE. 'best understood as', 'more important', "
    "'prediction is the mechanism of speech itself' describe a reading. Keep the atom's "
    "INTERPRETIVE type. Never restate a reading as an established worldly fact, and "
    "never mark a comparative unsupported merely for being comparative.\n"
    "* NO FORCED RELATIONS. If the article asserts no relation, return none.\n\n"
    "PROVENANCE IS NON-NEGOTIABLE. Every structured item cites the sentence_id(s) it "
    "rests on and quotes the exact article substring supporting it. Discontinuous "
    "evidence is allowed as separate fragments, each an exact substring. Text you "
    "composed yourself is DERIVED and must be marked so; never present it as a quote."
)


def build_items(sentences: list, records: list) -> list:
    """The model sees the authoritative backbone verbatim, nothing re-derived."""
    by_id = {r.get("sentence_id"): r for r in (records or [])}
    items = []
    for s in sentences:
        r = by_id.get(s["sentence_id"]) or {}
        items.append({
            "sentence_id": s["sentence_id"],
            "exact_span": s["exact_span"],
            "start_offset": s["start"],
            "end_offset": s["end"],
            "sentence_sha256": s["sha256"],
            "sentence_type": r.get("type"),
            "current_atomization": [
                {"atomic_id": a.get("atomic_id"), "atomic_claim": a.get("atomic_claim"),
                 "claim_type": a.get("claim_type"), "derivation": a.get("derivation")}
                for a in (r.get("atoms") or [])
            ],
        })
    return items


def user_prompt(items: list) -> str:
    return (
        "VERIFIED SENTENCE BACKBONE (authoritative; offsets index the frozen article):\n"
        + json.dumps(items, ensure_ascii=False, indent=0)
        + "\n\nReply with JSON only:\n"
        '{"semantic_claims":[{\n'
        '  "semantic_id":"SC001",\n'
        '  "sentence_id":"S001",\n'
        '  "atomic_id":"S001-A1" or null,\n'
        '  "claim_text":"what the article asserts here",\n'
        '  "claim_type":"EMPIRICAL|INTERPRETIVE",\n'
        '  "derivation":"VERBATIM|DERIVED",\n'
        '  "attribution":null or {"source_actor":"","attribution_cue":"",'
        '"attributed_content":"","evidence_span":""},\n'
        '  "qualifiers":[{"qualifier_text":"","qualifier_type":"",'
        '"applies_to":"CLAIM|RELATION","evidence_span":""}],\n'
        '  "relations":[{"relation_type":"' + "|".join(RELATION_TYPES) + '",'
        '"subject":"","object":"","evidence_span_ids":["S001"],"evidence_span":"",'
        '"status":"ASSERTED_BY_ARTICLE"}],\n'
        '  "event_referents":[{"event_id":"E1","event_text":"","evidence_span":""}],\n'
        '  "resolved_referents":[{"surface_form":"","surface_sentence_id":"S001",'
        '"surface_start_offset":0,"surface_end_offset":0,'
        '"target_text":"","target_sentence_id":"S001",'
        '"target_start_offset":0,"target_end_offset":0,'
        '"resolution_type":"SAME_SENTENCE_EXPLICIT|CROSS_SENTENCE_ENTITY_PRONOUN|CROSS_SENTENCE_NOMINAL_REPEAT|OTHER_EXPLICIT","resolution_basis_span_ids":["S001"]}],\n'
        '  "unresolved_referents":[{"surface_form":"","reason_unresolved":""}]\n'
        "}]}\n"
        "Every evidence_span must be an exact substring of its sentence's exact_span.\n"
    )


def _empty(article_id, article_sha, claim_map_sha, status, **extra):
    art = {"version": ARTIFACT_VERSION, "article_id": article_id,
           "article_sha": article_sha, "claim_map_sha": claim_map_sha,
           "prompt_version": PROMPT_VERSION, "status": status,
           "calls": 0, "latency_s": 0.0, "semantic_claims": [],
           "warnings": [], "unresolved_referents": [], "validation_result": None,
           "provider": None, "model": None}
    art.update(extra)
    return art


def enrich(provider, article_id: str, article_text: str, sentences: list,
           records: list, timeout: int = 600, allow_one_retry: bool = True) -> dict:
    """Produce the shadow artifact. NEVER raises: every failure path returns an artifact
    whose status says what went wrong, because the caller must be able to ignore it and
    continue. A technical zero-result may be retried exactly once with the identical
    input, and the retry is recorded rather than hidden."""
    article_sha = sha256_text(article_text)
    claim_map_sha = sha256_text(json.dumps(records, sort_keys=True, ensure_ascii=False))
    items = build_items(sentences, records)
    prompt = user_prompt(items)
    calls, t0, retried, last_err = 0, time.monotonic(), False, None
    parsed = None
    for attempt in (1, 2):
        if attempt == 2:
            if not (allow_one_retry and last_err):
                break
            retried = True
        try:
            calls += 1
            c = provider.complete(SYSTEM, prompt, max_tokens=16000, temperature=0,
                                  timeout=timeout)
            raw = getattr(c, "text", None) or str(c)
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                last_err = "no JSON object in reply"
                continue
            parsed = json.loads(raw[start:end + 1])
            last_err = None
            break
        except Exception as ex:                       # provider, transport, JSON, all
            last_err = "%s: %s" % (type(ex).__name__, ex)
            parsed = None
    latency = round(time.monotonic() - t0, 2)
    if parsed is None:
        art = _empty(article_id, article_sha, claim_map_sha, "SHADOW_UNAVAILABLE")
        art.update({"calls": calls, "latency_s": latency, "retried": retried,
                    "error": last_err,
                    "provider": getattr(provider, "__class__", type(provider)).__name__,
                    "model": getattr(provider, "model", None)})
        return art
    art = _empty(article_id, article_sha, claim_map_sha, "SHADOW_PRODUCED")
    art.update({
        "calls": calls, "latency_s": latency, "retried": retried,
        "provider": getattr(provider, "__class__", type(provider)).__name__,
        "model": getattr(provider, "model", None),
        "semantic_claims": parsed.get("semantic_claims") or [],
        "input_chars": len(prompt),
    })
    art["unresolved_referents"] = [
        dict(u, sentence_id=sc.get("sentence_id"))
        for sc in art["semantic_claims"] for u in (sc.get("unresolved_referents") or [])
    ]
    return art


def validate(artifact: dict, article_text: str, sentences: list, records: list) -> dict:
    """Deterministic. Nothing here consults a model. An artifact that fails is marked
    SHADOW_INVALID and discarded; the article is untouched either way."""
    errs: list[str] = []
    sent_by = {s["sentence_id"]: s for s in sentences}
    atom_types = {a.get("atomic_id"): a.get("claim_type")
                  for r in (records or []) for a in (r.get("atoms") or [])}
    atom_deriv = {a.get("atomic_id"): a.get("derivation")
                  for r in (records or []) for a in (r.get("atoms") or [])}

    if artifact.get("article_sha") != sha256_text(article_text):
        errs.append("article_sha mismatch")
    seen_ids = set()
    for sc in artifact.get("semantic_claims") or []:
        sid = sc.get("sentence_id")
        sem = sc.get("semantic_id")
        if sem in seen_ids:
            errs.append("duplicate semantic_id %r" % sem)
        seen_ids.add(sem)
        sent = sent_by.get(sid)
        if sent is None:
            errs.append("unknown sentence_id %r" % sid)
            continue
        if article_text[sent["start"]:sent["end"]] != sent["exact_span"]:
            errs.append("%s offsets do not match the article" % sid)
        if sha256_text(sent["exact_span"]) != sent["sha256"]:
            errs.append("%s hash does not match its span" % sid)
        aid = sc.get("atomic_id")
        if aid is not None and aid not in atom_types:
            errs.append("unknown atomic_id %r" % aid)
        # An INTERPRETIVE atom silently retyped EMPIRICAL is the interpretation-safety
        # failure this whole layer is supposed not to commit.
        if aid in atom_types and atom_types[aid] == "INTERPRETIVE" \
                and sc.get("claim_type") == "EMPIRICAL":
            errs.append("%s retypes an INTERPRETIVE atom as EMPIRICAL" % aid)
        if aid in atom_deriv and atom_deriv[aid] == "DERIVED" \
                and sc.get("derivation") == "VERBATIM":
            errs.append("%s marks DERIVED content VERBATIM" % aid)
        span = sent["exact_span"]

        def frag_ok(frag):
            # Discontinuous evidence is allowed; each fragment must stand on its own.
            if not frag:
                return True
            return all(f.strip() in span for f in str(frag).split("...") if f.strip())

        for q in sc.get("qualifiers") or []:
            if not frag_ok(q.get("evidence_span")):
                errs.append("%s qualifier evidence not in span: %r"
                            % (sid, (q.get("evidence_span") or "")[:60]))
        for rel in sc.get("relations") or []:
            rt = rel.get("relation_type")
            if rt not in RELATION_TYPES:
                errs.append("%s illegal relation_type %r" % (sid, rt))
            if not frag_ok(rel.get("evidence_span")):
                errs.append("%s relation evidence not in span: %r"
                            % (sid, (rel.get("evidence_span") or "")[:60]))
            for ev in rel.get("evidence_span_ids") or []:
                if ev not in sent_by:
                    errs.append("%s relation cites unknown sentence %r" % (sid, ev))
        # An event bound to words the sentence does not contain is the "right fact,
        # wrong event" shape; it has to fail here or the binding means nothing.
        for ev in sc.get("event_referents") or []:
            if not frag_ok(ev.get("evidence_span")):
                errs.append("%s event referent evidence not in span: %r"
                            % (sid, (ev.get("evidence_span") or "")[:60]))
        att = sc.get("attribution")
        if att and not frag_ok(att.get("evidence_span")):
            errs.append("%s attribution evidence not in span" % sid)
        # Resolved referents are anchored at BOTH ends, and an unsafe cross-sentence
        # deictic is downgraded to an unresolved referent rather than failing the whole
        # artifact: one over-confident pronoun should cost that pronoun, not the article.
        kept, downgraded = [], []
        for rr in sc.get("resolved_referents") or []:
            surf = (rr.get("surface_form") or "").strip()
            ssid = rr.get("surface_sentence_id")
            tsid = rr.get("target_sentence_id")
            rtype = rr.get("resolution_type")
            local = []
            if rtype not in RESOLUTION_TYPES:
                local.append("illegal resolution_type %r" % rtype)
            # OFFSETS ARE DERIVED HERE, NOT TRUSTED. Asking a language model to count
            # characters into a 6KB article is a known-unreliable instruction, and the
            # first replay proved it: 79 of 80 validation errors were offset mismatches
            # on referents whose TEXT was perfectly correct. What matters for the
            # anchoring guarantee is that the words exist exactly where the model says
            # they do -- which sentence -- so the validator locates the text inside the
            # named sentence itself and computes the article offsets deterministically.
            # A referent whose text is not in its named sentence is still rejected.
            for which, s_id, txt in (("surface", ssid, surf),
                                     ("target", tsid, rr.get("target_text"))):
                if s_id not in sent_by:
                    local.append("%s referent cites unknown sentence %r" % (which, s_id))
                    continue
                if not txt:
                    local.append("%s referent text is empty" % which)
                    continue
                host = sent_by[s_id]
                idx = host["exact_span"].find(txt)
                if idx < 0:
                    local.append("%s referent text %r is not in %s"
                                 % (which, txt[:40], s_id))
                    continue
                a = host["start"] + idx
                b = a + len(txt)
                if article_text[a:b] != txt:            # belt and braces
                    local.append("%s referent offset derivation failed" % which)
                    continue
                rr[which + "_start_offset"] = a
                rr[which + "_end_offset"] = b
                rr["offsets_derived"] = True
            for b_id in rr.get("resolution_basis_span_ids") or []:
                if b_id not in sent_by:
                    local.append("resolution basis cites unknown sentence %r" % b_id)
            if local:
                errs.extend("%s %s" % (sid, m) for m in local)
                continue
            if surf.lower() in DEICTIC_FORMS and tsid != ssid:
                downgraded.append({"surface_form": rr.get("surface_form"),
                                   "reason_unresolved": CROSS_SENTENCE_DEICTIC_UNSAFE,
                                   "attempted_target": rr.get("target_text"),
                                   "attempted_target_sentence_id": tsid})
                continue
            kept.append(rr)
        if downgraded:
            sc["resolved_referents"] = kept
            sc["unresolved_referents"] = list(sc.get("unresolved_referents") or []) \
                + downgraded
            artifact.setdefault("warnings", []).append(
                "%s: %d cross-sentence deictic resolution(s) downgraded to unresolved"
                % (sid, len(downgraded)))
        for ur in sc.get("unresolved_referents") or []:
            if not isinstance(ur, dict) or not ur.get("surface_form"):
                errs.append("%s malformed unresolved_referent record" % sid)
                continue
            # THE PROVENANCE RULE. Only fires when the surface form is a real token of
            # the parent sentence: a model that describes a referent rather than quoting
            # it ('implicit subject of "Generated"') is not making the claim this rule
            # is about, and the IF clause simply does not apply.
            surf = ur.get("surface_form") or ""
            if not _contains_surface(sent["exact_span"], surf):
                continue
            if not _contains_surface(sc.get("claim_text") or "", surf):
                errs.append(
                    "%s %s: %r is declared unresolved but does not appear in claim_text "
                    "-- the claim resolved it anyway (%r)"
                    % (sid, UNRESOLVED_REFERENT_DROPPED, surf,
                       (sc.get("claim_text") or "")[:80]))
    # Rebuilt after the downgrade pass so the artifact's own list reflects what the
    # validator actually decided, not what the model originally proposed.
    artifact["unresolved_referents"] = [
        dict(u, sentence_id=sc.get("sentence_id"))
        for sc in (artifact.get("semantic_claims") or [])
        for u in (sc.get("unresolved_referents") or [])
    ]
    ok = not errs
    artifact["validation_result"] = {"ok": ok, "errors": errs[:50],
                                     "error_count": len(errs)}
    if not ok:
        artifact["status"] = "SHADOW_INVALID"
    return artifact["validation_result"]


def run_shadow(provider_factory, article_id, article_text, sentences, records,
               timeout: int = 600):
    """The only entry point a pipeline should call.

    Returns None when the flag is off -- no artifact, no provider constructed, no call.
    Returns an artifact otherwise, valid or not. It never raises, so a caller can invoke
    it without a try/except and cannot be broken by it.
    """
    if not enabled():
        return None
    try:
        provider = provider_factory()
    except Exception as ex:
        return _empty(article_id, sha256_text(article_text),
                      sha256_text(json.dumps(records, sort_keys=True,
                                             ensure_ascii=False)),
                      "SHADOW_UNAVAILABLE",
                      error="provider construction failed: %s: %s"
                            % (type(ex).__name__, ex))
    art = enrich(provider, article_id, article_text, sentences, records, timeout=timeout)
    if art.get("status") == "SHADOW_PRODUCED":
        try:
            validate(art, article_text, sentences, records)
        except Exception as ex:                        # a validator bug must not escape
            art["status"] = "SHADOW_INVALID"
            art["validation_result"] = {"ok": False,
                                        "errors": ["validator raised: %s: %s"
                                                   % (type(ex).__name__, ex)],
                                        "error_count": 1}
    return art

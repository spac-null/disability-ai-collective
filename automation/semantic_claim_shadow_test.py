#!/usr/bin/env python3
"""Deterministic regression for the segmentation fix and the semantic claim shadow.

No network, no subscription: every provider here is a fake. The point of the suite is
that a shadow failure -- any shadow failure -- leaves the authoritative pipeline exactly
where it was, and that the two shapes the research pilot earned (subset/containment and
qualifier binding) plus the one error it found (deictic over-resolution) are pinned.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for p in (str(HERE), str(HERE / "new_engine_v1")):
    if p not in sys.path:
        sys.path.insert(0, p)

from new_engine_v1 import claims as CM                              # noqa: E402
from new_engine_v1 import semantic_claim_shadow as SH               # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else " <- %r" % detail))
    if not ok:
        FAILURES.append(label)


def seg(text):
    return [s["exact_span"] for s in CM.segment(text)]


# ── A. segmentation ──────────────────────────────────────────────────────────
print("A. segmentation")
GU = ("Law 27 February 2026, n. 26, published in the Gazzetta Ufficiale of "
      "28 February 2026, n. 49. This is the Milleproroghe.")
parts = seg(GU)
check("Gazzetta 'n. 49.' stays in one sentence", len(parts) == 2 and "n. 49." in parts[0], parts)
check("the following sentence still splits", parts[-1] == "This is the Milleproroghe.", parts)
check("Dr. does not split", seg("Dr. Smith arrived early. The room was full.") ==
      ["Dr. Smith arrived early.", "The room was full."])
check("Mr./Mrs./St. do not split",
      seg("Mr. Jones and Mrs. Lee met at St. Anne's College. They talked.") ==
      ["Mr. Jones and Mrs. Lee met at St. Anne's College.", "They talked."])
check("No. does not split", seg("See No. 4 below. It explains everything.") ==
      ["See No. 4 below.", "It explains everything."])
check("ordinary sentences still split",
      seg("The show opened. Nobody came. It closed.") ==
      ["The show opened.", "Nobody came.", "It closed."])
check("decimals not merged across a real boundary",
      seg("The value was 3.5 per cent. That is high.") ==
      ["The value was 3.5 per cent.", "That is high."])
check("version numbers survive", seg("Version 2.1 shipped. Users noticed.") ==
      ["Version 2.1 shipped.", "Users noticed."])
check("year-final sentence still splits",
      seg("It happened on 28 February 2026. Nobody noticed.") ==
      ["It happened on 28 February 2026.", "Nobody noticed."])

ART = ("The report says the delay caused the backlog. "
       "The fair showed eight of the most interesting pavilions. "
       "The ban applies to resale by non-licensed resellers. "
       "That is the perspective typical of where wheelchair seating is located. "
       "The piece is best understood as a refusal.")
sents = CM.segment(ART)
check("backbone offsets verify", CM.verify_backbone(ART, sents) == [], CM.verify_backbone(ART, sents))
check("five sentences segmented", len(sents) == 5, [s["exact_span"] for s in sents])

RECORDS = [
    {"sentence_id": "S001", "parent_exact_span": sents[0]["exact_span"], "type": "EMPIRICAL",
     "atoms": [{"atomic_id": "S001-A1", "atomic_claim": sents[0]["exact_span"],
                "claim_type": "EMPIRICAL", "derivation": "VERBATIM"}]},
    {"sentence_id": "S002", "parent_exact_span": sents[1]["exact_span"], "type": "EMPIRICAL",
     "atoms": [{"atomic_id": "S002-A1", "atomic_claim": sents[1]["exact_span"],
                "claim_type": "EMPIRICAL", "derivation": "VERBATIM"}]},
    {"sentence_id": "S003", "parent_exact_span": sents[2]["exact_span"], "type": "EMPIRICAL",
     "atoms": [{"atomic_id": "S003-A1", "atomic_claim": sents[2]["exact_span"],
                "claim_type": "EMPIRICAL", "derivation": "VERBATIM"}]},
    {"sentence_id": "S004", "parent_exact_span": sents[3]["exact_span"], "type": "EMPIRICAL",
     "atoms": [{"atomic_id": "S004-A1", "atomic_claim": sents[3]["exact_span"],
                "claim_type": "EMPIRICAL", "derivation": "VERBATIM"}]},
    {"sentence_id": "S005", "parent_exact_span": sents[4]["exact_span"], "type": "INTERPRETIVE",
     "atoms": [{"atomic_id": "S005-A1", "atomic_claim": sents[4]["exact_span"],
                "claim_type": "INTERPRETIVE", "derivation": "VERBATIM"}]},
]


class Fake:
    """One canned reply, no network. `model` mirrors the real provider surface."""
    model = "fake"

    def __init__(self, payload, raises=None):
        self.payload, self.raises, self.calls = payload, raises, 0

    def complete(self, system, user, **kw):
        self.calls += 1
        if self.raises:
            raise self.raises
        class C:
            text = self.payload if isinstance(self.payload, str) \
                else json.dumps(self.payload)
        return C()


def sc(sid, aid, text, **kw):
    base = {"semantic_id": "SC" + sid, "sentence_id": sid, "atomic_id": aid,
            "claim_text": text, "claim_type": "EMPIRICAL", "derivation": "VERBATIM",
            "attribution": None, "qualifiers": [], "relations": [],
            "event_referents": [], "resolved_referents": [], "unresolved_referents": []}
    base.update(kw)
    return base


def run(payload, raises=None):
    f = Fake(payload, raises)
    art = SH.enrich(f, "ART", ART, sents, RECORDS)
    if art["status"] == "SH.PRODUCED" or art["status"] == "SHADOW_PRODUCED":
        SH.validate(art, ART, sents, RECORDS)
    return art, f


# ── D. attributed causality ──────────────────────────────────────────────────
print("D. attributed causality")
good_attr = {"semantic_claims": [sc(
    "S001", "S001-A1", "The report says the delay caused the backlog.",
    attribution={"source_actor": "The report", "attribution_cue": "says",
                 "attributed_content": "the delay caused the backlog",
                 "evidence_span": "The report says"},
    relations=[{"relation_type": "ATTRIBUTION", "subject": "The report",
                "object": "the delay caused the backlog",
                "evidence_span_ids": ["S001"], "evidence_span": "The report says",
                "status": "ASSERTED_BY_ARTICLE"},
               {"relation_type": "CAUSE", "subject": "the delay",
                "object": "the backlog", "evidence_span_ids": ["S001"],
                "evidence_span": "caused the backlog",
                "status": "ASSERTED_BY_ARTICLE"}])]}
art, _ = run(good_attr)
check("attributed causality validates", art["validation_result"]["ok"], art["validation_result"])
check("attribution retained as structure",
      art["semantic_claims"][0]["attribution"]["source_actor"] == "The report")

# ── B. subset containment ────────────────────────────────────────────────────
print("B. subset containment")
subset = {"semantic_claims": [sc(
    "S002", "S002-A1", "The fair showed eight of the most interesting pavilions.",
    qualifiers=[{"qualifier_text": "eight of the most interesting",
                 "qualifier_type": "SUBSET_COUNT", "applies_to": "CLAIM",
                 "evidence_span": "eight of the most interesting pavilions"}],
    relations=[{"relation_type": "CONTAINMENT_SUBSET",
                "subject": "eight interesting pavilions",
                "object": "the pavilions at the fair",
                "evidence_span_ids": ["S002"],
                "evidence_span": "eight of the most interesting pavilions",
                "status": "ASSERTED_BY_ARTICLE"}])]}
art, _ = run(subset)
check("subset containment validates", art["validation_result"]["ok"], art["validation_result"])
rel = art["semantic_claims"][0]["relations"][0]
check("subset is CONTAINMENT_SUBSET, not a container total",
      rel["relation_type"] == "CONTAINMENT_SUBSET" and "of the most interesting" in rel["evidence_span"])

# ── C. qualifier attachment ──────────────────────────────────────────────────
print("C. qualifier attachment")
qual = {"semantic_claims": [sc(
    "S003", "S003-A1", "The ban applies to resale by non-licensed resellers.",
    qualifiers=[{"qualifier_text": "by non-licensed resellers",
                 "qualifier_type": "AGENT_RESTRICTION", "applies_to": "CLAIM",
                 "evidence_span": "by non-licensed resellers"}])]}
art, _ = run(qual)
check("qualifier attachment validates", art["validation_result"]["ok"], art["validation_result"])
check("qualifier bound to its claim",
      art["semantic_claims"][0]["qualifiers"][0]["qualifier_text"] == "by non-licensed resellers")

# ── E. deictic ambiguity (the one real audit error) ──────────────────────────
print("E. deictic ambiguity")
unresolved = {"semantic_claims": [sc(
    "S004", "S004-A1", "That is the perspective typical of where wheelchair seating is located.",
    unresolved_referents=[{"surface_form": "That",
                           "reason_unresolved": "the article does not name what 'That' is"}])]}
art, _ = run(unresolved)
check("leaving 'That' unresolved validates", art["validation_result"]["ok"], art["validation_result"])
check("unresolved referent surfaces on the artifact",
      any(u["surface_form"] == "That" for u in art["unresolved_referents"]), art["unresolved_referents"])
# The REAL failure, reproduced exactly. The earlier version of this fixture only
# tested a model that cited OUT-OF-SPAN evidence, which is the easy case; the live
# replay then produced a resolution whose evidence WAS in span and sailed through.
# Here both ends are perfectly anchored to real article offsets -- the shape that
# previously survived -- and it must still not survive.
DEICTIC_ART = (
    "The video projection content was designed by Maag, also a wheelchair user, to be "
    "visually and emotionally felt from the floor of the house. "
    "That is the perspective typical of where wheelchair and accessibility seating is "
    "located in a theater.")
dsents = CM.segment(DEICTIC_ART)
assert len(dsents) == 2, dsents
D_RECORDS = [{"sentence_id": x["sentence_id"], "parent_exact_span": x["exact_span"],
              "type": "EMPIRICAL",
              "atoms": [{"atomic_id": x["sentence_id"] + "-A1",
                         "atomic_claim": x["exact_span"], "claim_type": "EMPIRICAL",
                         "derivation": "VERBATIM"}]} for x in dsents]
t_start = DEICTIC_ART.index("the floor of the house")
t_end = t_start + len("the floor of the house")
s_start = DEICTIC_ART.index("That", dsents[1]["start"])
s_end = s_start + len("That")
check("fixture anchors are real article offsets",
      DEICTIC_ART[t_start:t_end] == "the floor of the house"
      and DEICTIC_ART[s_start:s_end] == "That")

over = {"semantic_claims": [{
    "semantic_id": "SC1", "sentence_id": "S002", "atomic_id": "S002-A1",
    # claim_text keeps the article's own wording. The variant that rewrites it is a
    # SEPARATE defect with its own fixture -- see "L. an unresolved referent may not be
    # resolved in the claim text instead".
    "claim_text": "That is the perspective typical of where "
                  "wheelchair and accessibility seating is located in a theater.",
    "claim_type": "EMPIRICAL", "derivation": "DERIVED",
    "attribution": None, "qualifiers": [], "relations": [], "event_referents": [],
    "resolved_referents": [{
        "surface_form": "That", "surface_sentence_id": "S002",
        "surface_start_offset": s_start, "surface_end_offset": s_end,
        "target_text": "the floor of the house", "target_sentence_id": "S001",
        "target_start_offset": t_start, "target_end_offset": t_end,
        "resolution_type": "CROSS_SENTENCE_NOMINAL_REPEAT",
        "resolution_basis_span_ids": ["S001"]}],
    "unresolved_referents": []}]}
f = Fake(over)
art = SH.enrich(f, "D", DEICTIC_ART, dsents, D_RECORDS)
SH.validate(art, DEICTIC_ART, dsents, D_RECORDS)
scd = art["semantic_claims"][0]
check("fully-anchored cross-sentence 'That' does NOT survive as resolved",
      scd["resolved_referents"] == [], scd["resolved_referents"])
check("it is downgraded to an unresolved referent",
      any(u.get("surface_form") == "That" for u in scd["unresolved_referents"]),
      scd["unresolved_referents"])
check("downgrade reason is CROSS_SENTENCE_DEICTIC_UNSAFE",
      any(u.get("reason_unresolved") == SH.CROSS_SENTENCE_DEICTIC_UNSAFE
          for u in scd["unresolved_referents"]), scd["unresolved_referents"])
check("the article is not invalidated by one unsafe pronoun",
      art["validation_result"]["ok"] and art["status"] == "SHADOW_PRODUCED",
      (art["status"], art["validation_result"]))
check("the downgrade is recorded as a warning", bool(art.get("warnings")), art.get("warnings"))
check("artifact-level unresolved list reflects the downgrade",
      any(u.get("reason_unresolved") == SH.CROSS_SENTENCE_DEICTIC_UNSAFE
          for u in art["unresolved_referents"]), art["unresolved_referents"])

# Positive control: an ordinary entity pronoun across sentences is legitimate and
# must NOT be swept up by the deictic rule.
ENT_ART = "Maria entered the room. She sat down."
esents = CM.segment(ENT_ART)
E_RECORDS = [{"sentence_id": x["sentence_id"], "parent_exact_span": x["exact_span"],
              "type": "EMPIRICAL",
              "atoms": [{"atomic_id": x["sentence_id"] + "-A1",
                         "atomic_claim": x["exact_span"], "claim_type": "EMPIRICAL",
                         "derivation": "VERBATIM"}]} for x in esents]
m_start = ENT_ART.index("Maria"); m_end = m_start + len("Maria")
sh_start = ENT_ART.index("She"); sh_end = sh_start + len("She")
ent = {"semantic_claims": [{
    "semantic_id": "SC1", "sentence_id": "S002", "atomic_id": "S002-A1",
    "claim_text": "Maria sat down.", "claim_type": "EMPIRICAL", "derivation": "DERIVED",
    "attribution": None, "qualifiers": [], "relations": [], "event_referents": [],
    "resolved_referents": [{
        "surface_form": "She", "surface_sentence_id": "S002",
        "surface_start_offset": sh_start, "surface_end_offset": sh_end,
        "target_text": "Maria", "target_sentence_id": "S001",
        "target_start_offset": m_start, "target_end_offset": m_end,
        "resolution_type": "CROSS_SENTENCE_ENTITY_PRONOUN",
        "resolution_basis_span_ids": ["S001"]}],
    "unresolved_referents": []}]}
f = Fake(ent)
art = SH.enrich(f, "E", ENT_ART, esents, E_RECORDS)
SH.validate(art, ENT_ART, esents, E_RECORDS)
check("cross-sentence entity pronoun survives", art["validation_result"]["ok"]
      and len(art["semantic_claims"][0]["resolved_referents"]) == 1,
      (art["validation_result"], art["semantic_claims"][0]["resolved_referents"]))

# Anchoring is mandatory: a paraphrased target with no real offsets is rejected.
bad_anchor = json.loads(json.dumps(ent))
bad_anchor["semantic_claims"][0]["resolved_referents"][0]["target_text"] = "the woman"
f = Fake(bad_anchor)
art = SH.enrich(f, "E", ENT_ART, esents, E_RECORDS)
SH.validate(art, ENT_ART, esents, E_RECORDS)
check("a paraphrased (unanchored) target is rejected",
      not art["validation_result"]["ok"], art["validation_result"])
bad_type = json.loads(json.dumps(ent))
bad_type["semantic_claims"][0]["resolved_referents"][0]["resolution_type"] = "VIBES"
f = Fake(bad_type)
art = SH.enrich(f, "E", ENT_ART, esents, E_RECORDS)
SH.validate(art, ENT_ART, esents, E_RECORDS)
check("illegal resolution_type is rejected",
      not art["validation_result"]["ok"], art["validation_result"])

# ── F. interpretation safety ─────────────────────────────────────────────────

# ── L. AN UNRESOLVED REFERENT MAY NOT BE RESOLVED IN THE CLAIM TEXT INSTEAD ──
# Replay 3 (2026-09-20) reproduced the original defect through a different field: the
# referent record said "That" was unresolvable and claim_text resolved it anyway. 22 of
# 443 semantic claims in that replay dropped a surface form they had just declared
# unresolved. The rule is provenance only -- it asks whether the word disappeared, never
# whether the replacement means the same thing.
print("\nL. an unresolved referent may not be resolved in the claim text instead")


def _shadow_over(claim_text, unresolved, resolved=None, sid="S002", aid="S002-A1"):
    return {"semantic_claims": [{
        "semantic_id": "SC1", "sentence_id": sid, "atomic_id": aid,
        "claim_text": claim_text, "claim_type": "EMPIRICAL", "derivation": "DERIVED",
        "attribution": None, "qualifiers": [], "relations": [], "event_referents": [],
        "resolved_referents": resolved or [],
        "unresolved_referents": unresolved}]}


def _run(article, sents, records, over):
    a = SH.enrich(Fake(over), "L", article, sents, records)
    SH.validate(a, article, sents, records)
    return a


# A. THE KNOWN BAD CASE, verbatim from replay 3 draft 8a0dab48 S021.
bad = _run(DEICTIC_ART, dsents, D_RECORDS, _shadow_over(
    "The floor of the house is the perspective typical of where wheelchair and "
    "accessibility seating is located in a theater. "
    "[DERIVED: pronoun 'that' resolved, not the article's wording]",
    [{"surface_form": "That", "reason_unresolved": "Demonstrative pointing outside "
      "this sentence; no identity construction inside the sentence supplies it."}]))
check("A. the known 'That' case FAILS validation",
      not bad["validation_result"]["ok"] and bad["status"] == "SHADOW_INVALID",
      (bad["status"], bad["validation_result"]))
check("A. and it is named as the dropped-referent error",
      any(SH.UNRESOLVED_REFERENT_DROPPED in e
          for e in bad["validation_result"]["errors"]),
      str(bad["validation_result"]["errors"])[:200])

# B. SAFE UNRESOLVED -- the same referent, the article's own wording kept.
safe = _run(DEICTIC_ART, dsents, D_RECORDS, _shadow_over(
    "That is the perspective typical of where wheelchair and accessibility seating is "
    "located in a theater.",
    [{"surface_form": "That", "reason_unresolved": "Demonstrative; not settled here."}]))
check("B. keeping the unresolved surface form PASSES",
      safe["validation_result"]["ok"] and safe["status"] == "SHADOW_PRODUCED",
      (safe["status"], safe["validation_result"]))
check("B. sentence-initial casing does not defeat the match",
      _run(DEICTIC_ART, dsents, D_RECORDS, _shadow_over(
          "that is the perspective typical of where wheelchair and accessibility "
          "seating is located in a theater.",
          [{"surface_form": "That", "reason_unresolved": "x"}]
      ))["validation_result"]["ok"])

# C. A VALID RESOLUTION IS UNTOUCHED. "Maria entered the room. She sat down." -- an
#    anchored entity pronoun, so the claim may name Maria and nothing is unresolved.
m_t0 = ENT_ART.index("Maria")
m_s0 = ENT_ART.index("She")
ok_res = _run(ENT_ART, esents, E_RECORDS, _shadow_over(
    "Maria sat down.", [],
    [{"surface_form": "She", "surface_sentence_id": "S002",
      "target_text": "Maria", "target_sentence_id": "S001",
      "resolution_type": "CROSS_SENTENCE_ENTITY_PRONOUN",
      "resolution_basis_span_ids": ["S001"]}]))
check("C. an anchored entity-pronoun resolution still PASSES and may name Maria",
      ok_res["validation_result"]["ok"]
      and ok_res["semantic_claims"][0]["resolved_referents"],
      (ok_res["status"], ok_res["validation_result"]))

# D. AN UNRESOLVED PERSONAL PRONOUN GETS NO SPECIAL TREATMENT.
pron = _run(ENT_ART, esents, E_RECORDS, _shadow_over(
    "The investigators sat down.",
    [{"surface_form": "She", "reason_unresolved": "No anchored antecedent."}]))
check("D. an unresolved 'She' replaced by a name FAILS",
      not pron["validation_result"]["ok"], (pron["status"], pron["validation_result"]))
keep = _run(ENT_ART, esents, E_RECORDS, _shadow_over(
    "She sat down.", [{"surface_form": "She", "reason_unresolved": "No antecedent."}]))
check("D. keeping 'She' PASSES", keep["validation_result"]["ok"],
      keep["validation_result"])

# E. INTERPRETIVE. A demonstrative must not become a named empirical subject.
INT_ART = ("The tribunal moved the case to a different list. "
           "That is best understood as a change in classification.")
isents = CM.segment(INT_ART)
I_RECORDS = [{"sentence_id": x["sentence_id"], "parent_exact_span": x["exact_span"],
              "type": "INTERPRETIVE",
              "atoms": [{"atomic_id": x["sentence_id"] + "-A1",
                         "atomic_claim": x["exact_span"],
                         "claim_type": "INTERPRETIVE", "derivation": "VERBATIM"}]}
             for x in isents]
interp = _run(INT_ART, isents, I_RECORDS, {"semantic_claims": [{
    "semantic_id": "SC1", "sentence_id": "S002", "atomic_id": "S002-A1",
    "claim_text": "The move to a different list is best understood as a change in "
                  "classification.",
    "claim_type": "INTERPRETIVE", "derivation": "DERIVED", "attribution": None,
    "qualifiers": [], "relations": [], "event_referents": [], "resolved_referents": [],
    "unresolved_referents": [{"surface_form": "That",
                              "reason_unresolved": "Demonstrative."}]}]})
check("E. an interpretive demonstrative cannot become a named subject",
      not interp["validation_result"]["ok"], interp["validation_result"])

# THE RULE DOES NOT OVERREACH.
desc = _run(DEICTIC_ART, dsents, D_RECORDS, _shadow_over(
    "The video projection content was designed to be felt from the floor of the house.",
    [{"surface_form": 'implicit subject of "designed"',
      "reason_unresolved": "Described, not quoted."}], sid="S001", aid="S001-A1"))
check("a DESCRIBED referent that is not a token of the sentence does not trigger it",
      desc["validation_result"]["ok"], desc["validation_result"])
check("token matching: 'it' is not found inside 'Its'",
      not SH._contains_surface("Its legs gave way.", "it"))
check("token matching: 'that' is not found inside 'thatch'",
      not SH._contains_surface("The thatch was old.", "that"))
check("token matching: a multi-word form is matched as a phrase",
      SH._contains_surface("The former was cheaper.", "the former")
      and not SH._contains_surface("A formerly cheap seat.", "the former"))
check("token matching: curly and straight quotes are the same text",
      SH._contains_surface("the \u201cfloor\u201d of the house", '"floor"'))


print("F. interpretation safety")
retyped = {"semantic_claims": [sc(
    "S005", "S005-A1", "The piece is a refusal.", claim_type="EMPIRICAL")]}
art, _ = run(retyped)
check("retyping an INTERPRETIVE atom EMPIRICAL is rejected",
      not art["validation_result"]["ok"] and
      any("INTERPRETIVE" in e for e in art["validation_result"]["errors"]),
      art["validation_result"])
kept = {"semantic_claims": [sc("S005", "S005-A1",
                               "The piece is best understood as a refusal.",
                               claim_type="INTERPRETIVE")]}
art, _ = run(kept)
check("keeping it INTERPRETIVE validates", art["validation_result"]["ok"], art["validation_result"])

# ── G. event identity ────────────────────────────────────────────────────────
print("G. event identity")
misbound = {"semantic_claims": [sc(
    "S002", "S002-A1", "The fair showed eight of the most interesting pavilions.",
    event_referents=[{"event_id": "E1", "event_text": "a different fair entirely",
                      "evidence_span": "a different fair entirely"}])]}
art, _ = run(misbound)
check("an event bound to text absent from the span is rejected",
      not art["validation_result"]["ok"], art["validation_result"])

# ── J. invalid evidence span ─────────────────────────────────────────────────
print("J. invalid evidence span / bad enum")
bad = {"semantic_claims": [sc("S001", "S001-A1", "x", relations=[
    {"relation_type": "TELEPATHY", "subject": "a", "object": "b",
     "evidence_span_ids": ["S001"], "evidence_span": "The report says",
     "status": "ASSERTED_BY_ARTICLE"}])]}
art, _ = run(bad)
check("illegal relation enum invalidates the artifact",
      not art["validation_result"]["ok"] and
      any("illegal relation_type" in e for e in art["validation_result"]["errors"]),
      art["validation_result"])
check("invalid shadow marks SHADOW_INVALID, not a pipeline error",
      art["status"] == "SHADOW_INVALID", art["status"])
ghost = {"semantic_claims": [sc("S099", None, "from nowhere")]}
art, _ = run(ghost)
check("unknown sentence_id invalidates", not art["validation_result"]["ok"])
dupe = {"semantic_claims": [sc("S001", "S001-A1", "a"), sc("S001", "S001-A1", "b")]}
art, _ = run(dupe)
check("duplicate semantic_id invalidates",
      any("duplicate semantic_id" in e for e in art["validation_result"]["errors"]),
      art["validation_result"])

# ── H. malformed shadow output ───────────────────────────────────────────────
print("H. malformed output never blocks")
art, f = run("this is not JSON at all")
check("garbage reply yields SHADOW_UNAVAILABLE", art["status"] == "SHADOW_UNAVAILABLE", art["status"])
check("garbage reply retried exactly once", f.calls == 2, f.calls)
check("no exception escaped", True)

# ── I. provider failure ──────────────────────────────────────────────────────
print("I. provider failure never blocks")
art, f = run(None, raises=RuntimeError("subscription limit"))
check("provider raise yields SHADOW_UNAVAILABLE", art["status"] == "SHADOW_UNAVAILABLE", art["status"])
check("error recorded, not swallowed", "subscription limit" in (art.get("error") or ""), art.get("error"))
check("retried exactly once, no loop", f.calls == 2, f.calls)


class Boom:
    model = "boom"
    def complete(self, *a, **k):
        raise RuntimeError("down")


def factory_boom():
    return Boom()


os.environ[SH.FLAG] = "1"
art = SH.run_shadow(factory_boom, "ART", ART, sents, RECORDS)
check("run_shadow swallows provider failure", art is not None and
      art["status"] == "SHADOW_UNAVAILABLE", art)


def factory_raises():
    raise RuntimeError("cannot construct")


art = SH.run_shadow(factory_raises, "ART", ART, sents, RECORDS)
check("run_shadow survives provider construction failure",
      art["status"] == "SHADOW_UNAVAILABLE", art)

# ── K. flag off = zero difference, zero calls ────────────────────────────────

# ── M. THE ACTIVE-PATH CALL SITE ─────────────────────────────────────────────
# The shadow was merged with no caller, so the flag could not produce a canary.
# composition.run_semantic_claim_shadow is the one call site; these pin the three
# properties that let it sit inside a production run.

# ── N. VERBATIM IS COMPUTED FROM THE SPAN, NOT ASKED OF THE MODEL ────────────
# The check compared the shadow's derivation against the BACKBONE ATOM's, a statement
# about a different string. Of 11 provenance errors across the six-draft replay and the
# canary, 9 had a claim_text that IS the article's contiguous wording; all 11 had a
# non-literal atomic_claim, which is what the check was reading.
print("\nN. derivation is computed from the anchored span")
from new_engine_v1 import claims as _CL                            # noqa: E402

PARENT = "The streets around the museum were unusually quiet, and the men capitalised on that."
CASES = [
    # (claim, span, expected, why)
    (PARENT, PARENT, "VERBATIM", "the whole sentence"),
    ("The men capitalised on that.", PARENT, "VERBATIM",
     "a contiguous substring, sentence-initial capital folded"),
    ("Both numbers come from a project page.",
     "Both numbers come from a project page presenting an interactive comparison.",
     "DERIVED", "a truncation closed with a full stop is not the article's wording"),
    ("Maria sat down.", "She sat down.", "DERIVED", "a resolved pronoun"),
    ("The room was empty.", "Nobody was in the room.", "DERIVED", "a paraphrase"),
    ("no service existed the trust knew",
     "The report states that no service existed, and that the trust knew.",
     "DERIVED", "two fragments that exist only separately"),
    ('"unrealistic"', "the coroner said \u201cunrealistic\u201d here", "DERIVED",
     "quote shape is NOT folded -- existing policy, unchanged"),
    ("the  men   capitalised on that", PARENT, "VERBATIM",
     "whitespace IS collapsed -- existing policy, unchanged"),
]
for claim, span, want, why in CASES:
    got = _CL.derivation_of(claim, span)
    check("%s -> %s (%s)" % (claim[:34], want, why), got == want, got)

# The shadow must now report the computed value, whatever the model said, and must fail
# only when the model claimed the article's words for text that is not.
N_ART = ("The streets around the museum were unusually quiet, and the men capitalised "
         "on that. She sat down.")
nsents = CM.segment(N_ART)
N_RECORDS = [{"sentence_id": x["sentence_id"], "parent_exact_span": x["exact_span"],
              "type": "EMPIRICAL",
              "atoms": [{"atomic_id": x["sentence_id"] + "-A1",
                         # the backbone atom is DERIVED -- a resolved pronoun, exactly the
                         # case that used to condemn a verbatim claim_text
                         "atomic_claim": "The men capitalised on the quiet streets.",
                         "claim_type": "EMPIRICAL", "derivation": "DERIVED"}]}
             for x in nsents]


def _n(claim_text, said, sid="S001"):
    a = SH.enrich(Fake({"semantic_claims": [{
        "semantic_id": "SC1", "sentence_id": sid, "atomic_id": sid + "-A1",
        "claim_text": claim_text, "claim_type": "EMPIRICAL", "derivation": said,
        "attribution": None, "qualifiers": [], "relations": [], "event_referents": [],
        "resolved_referents": [], "unresolved_referents": []}]}),
        "N", N_ART, nsents, N_RECORDS)
    SH.validate(a, N_ART, nsents, N_RECORDS)
    return a


ok = _n("The men capitalised on that.", "VERBATIM")
check("a verbatim claim_text VALIDATES even though its backbone atom is DERIVED",
      ok["validation_result"]["ok"], ok["validation_result"])
check("and the recorded derivation is the computed one",
      ok["semantic_claims"][0]["derivation"] == "VERBATIM"
      and ok["semantic_claims"][0]["derivation_source"] == "COMPUTED_FROM_SPAN",
      ok["semantic_claims"][0].get("derivation"))

bad = _n("The men capitalised on the unusual quiet.", "VERBATIM")
check("a paraphrase labelled VERBATIM still FAILS",
      not bad["validation_result"]["ok"], bad["validation_result"])
check("and the error names the span, not the atom",
      any("contiguous wording" in e
          for e in bad["validation_result"]["errors"]),
      str(bad["validation_result"]["errors"])[:160])

conservative = _n("The men capitalised on the unusual quiet.", "DERIVED")
check("a paraphrase honestly labelled DERIVED passes and stays DERIVED",
      conservative["validation_result"]["ok"]
      and conservative["semantic_claims"][0]["derivation"] == "DERIVED",
      conservative["validation_result"])

pron = _n("Maria sat down.", "VERBATIM", sid="S002")
check("a resolved pronoun claimed VERBATIM still FAILS",
      not pron["validation_result"]["ok"], pron["validation_result"])


print("\nM. active-path invocation")
from new_engine_v1 import composition as _CP                       # noqa: E402

_prev = os.environ.pop(SH.FLAG, None)


class _Boom:
    model = "claude-opus-5"
    calls = 0

    def complete(self, *a, **k):
        _Boom.calls += 1
        raise RuntimeError("provider is down")


_Boom.calls = 0
check("OFF: returns None",
      _CP.run_semantic_claim_shadow(_Boom(), "Some prose.", [], "sha") is None)
check("OFF: zero provider calls", _Boom.calls == 0, _Boom.calls)

os.environ[SH.FLAG] = "1"
try:
    _Boom.calls = 0
    r = _CP.run_semantic_claim_shadow(_Boom(), "Some prose. And more.", [], "sha")
    check("ON: a provider that raises never propagates an exception", True)
    check("ON: the result is either nothing or a marked-unusable artifact",
          r is None or r.get("status") in ("SHADOW_UNAVAILABLE", "SHADOW_INVALID"),
          str((r or {}).get("status")))
    check("ON: and it is stamped NON_AUTHORITATIVE",
          r is None or r.get("authority") == "NON_AUTHORITATIVE",
          str((r or {}).get("authority")))
    check("ON: the failure was reached, not skipped", _Boom.calls >= 1, _Boom.calls)
finally:
    os.environ.pop(SH.FLAG, None)
    if _prev is not None:
        os.environ[SH.FLAG] = _prev

src = open(_CP.__file__, encoding="utf-8").read()
check("the call site sits after the authoritative claim map is recorded",
      src.index('wr["claim_map_article_sha256"]')
      < src.index("run_semantic_claim_shadow(P, final"))
check("nothing in composition READS the shadow's return value",
      "= run_semantic_claim_shadow(" not in src)
consumers = [n for n in ("safety_audit", "ground_candidate", "reader_gate",
                         "safety_materiality", "validate_claim_map")
             if "semantic_claim_shadow" in src.split("def %s" % n)[-1][:4000]]
check("no gate function mentions the shadow", consumers == [], str(consumers))


print("K. flag OFF")
before = json.dumps(CM.segment(ART), sort_keys=True)
os.environ.pop(SH.FLAG, None)
check("enabled() False when unset", SH.enabled() is False)


class Counting:
    model = "counting"
    calls = 0
    def complete(self, *a, **k):
        Counting.calls += 1
        raise AssertionError("must not be called when the flag is off")


check("run_shadow returns None when OFF",
      SH.run_shadow(lambda: Counting(), "ART", ART, sents, RECORDS) is None)
check("zero provider calls when OFF", Counting.calls == 0, Counting.calls)
os.environ[SH.FLAG] = "0"
check("flag '0' is still OFF", SH.enabled() is False)
check("run_shadow still None at '0'",
      SH.run_shadow(lambda: Counting(), "ART", ART, sents, RECORDS) is None)
os.environ.pop(SH.FLAG, None)
check("authoritative backbone byte-identical across shadow activity",
      json.dumps(CM.segment(ART), sort_keys=True) == before)

print()
if FAILURES:
    print("FAILED %d: %s" % (len(FAILURES), ", ".join(FAILURES)))
    sys.exit(1)
print("ALL PASS")

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
    "claim_text": "The floor of the house is the perspective typical of where "
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

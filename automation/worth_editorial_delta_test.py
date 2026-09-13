#!/usr/bin/env python3
"""Small, offline contract test for Worth's source-baseline/editorial-delta fields."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from new_engine_v1 import composition as CP
from new_engine_v1 import story as ST


class Reply:
    def __init__(self, value): self.text = json.dumps(value)
    def identity(self): return {"provider": "scripted", "actual_model": "test"}


class Provider:
    model = "test"
    def __init__(self, lens): self.lens = lens
    def complete(self, **_):
        return Reply({"worth_gate": self.lens, "story_candidate": CAND})


LEDGER = {
    "F01": {"proposition": "The source reports event X.", "support_span": "event X",
            "claim_kind": "OCCURRENCE", "entities": ["Subject"], "evidence_ids": ["S1"]},
    "F02": {"proposition": "Research shows mechanism Y specific to Subject.",
            "support_span": "mechanism Y", "claim_kind": "DISPOSITION",
            "entities": ["Subject"], "evidence_ids": ["S1"]},
}
CAND = {"story_id": "delta", "carrier_type": "event", "opening_possibility": "event X",
        "real_event_or_change": "event X occurred", "tension": "X and Y",
        "reader_first_sees": "X", "reader_later_discovers": "Y",
        "causal_chain": [], "evidence_ids": ["F01", "F02"]}


BASE = {"verdict": ST.STRONG_DIRECT_LENS, "lens_claim": "Subject-specific mechanism Y changes what event X means.",
        "changes_meaning_how": "The reader sees Y rather than only X.", "evidence_ids": ["F01", "F02"],
        "lens_particulars": ["F02"], "lens_carrier": "mechanism Y", "can_carry_article": "YES"}


def run(extra):
    return CP.worth_gate(Provider(dict(BASE, **extra)), LEDGER, "Subject")


def held(extra):
    try:
        run(extra)
    except CP.CompositionHold as e:
        return " ".join(e.reasons)
    return ""


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok: raise SystemExit(1)


check("same story/no delta holds", "HOLD_INSUFFICIENT_EDITORIAL_DELTA" in held({
    "source_baseline": "The source already explains X.", "crip_minds_delta": "X, restated clearly.",
    "editorial_delta_status": "INSUFFICIENT"}))
check("distinct mechanism may pass", run({
    "source_baseline": "The source reports X but does not explain Y.",
    "crip_minds_delta": "Research-supported mechanism Y changes how this subject operates.",
    "editorial_delta_status": "SUFFICIENT"})["status"] == CP.PASS)
check("paraphrase holds", "HOLD_INSUFFICIENT_EDITORIAL_DELTA" in held({
    "source_baseline": "The source says X.", "crip_minds_delta": "The same X in different words.",
    "editorial_delta_status": "INSUFFICIENT"}))
check("disability fact alone holds", "HOLD_INSUFFICIENT_EDITORIAL_DELTA" in held({
    "source_baseline": "The source explains X.", "crip_minds_delta": "Disabled people are affected by X.",
    "editorial_delta_status": "INSUFFICIENT"}))
check("perspective question plus subject evidence may pass", run({
    "source_baseline": "Coverage records X.", "crip_minds_delta": "The subject-specific mechanism Y is supported by F02.",
    "editorial_delta_status": "SUFFICIENT"})["status"] == CP.PASS)
try:
    CP.worth_gate(Provider({"verdict": ST.WRONG_PUBLICATION, "lens_claim": "A real story for elsewhere.",
                             "changes_meaning_how": "", "evidence_ids": [], "lens_particulars": []}),
                  LEDGER, "Subject")
    ok = False
except CP.CompositionHold as e:
    ok = "not publishable here" in " ".join(e.reasons)
check("great general story refusal remains valid", ok)
print("ALL WORTH EDITORIAL DELTA TESTS PASS")

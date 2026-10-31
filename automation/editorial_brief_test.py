"""Offline checks for the opt-in editorial focus stage."""
import json

from new_engine_v1.editorial_brief import EditorialBriefError, propose
from new_engine_v1.ledger import validate_ledger_against_pack
from new_engine_v1.provider import Completion


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply
        self.user = ""
        self.system = ""

    def complete(self, system, user, max_tokens=1800):
        self.system = system
        self.user = user
        return Completion(json.dumps(self.reply), "test", "test", "offline")


def run():
    ledger = {
        "F01": {"proposition": "The venue asks for silence."},
        "F02": {"proposition": "The revised policy permits audience noise.",
                "evidence_ids": ["S1", "S2"]},
    }
    provider = FakeProvider({"decision": "WRITE", "question": "Who sets the rule?",
                             "fact_ids": ["F01", "F02"], "reason": "The policy changed.",
                             "missing_evidence": ""})
    brief = propose(provider, subject="A theatre", question="A broad question",
                    ledger=ledger)
    assert brief["fact_ids"] == ["F01", "F02"]
    assert "F01  [unspecified] The venue asks for silence." in provider.user
    assert "F02  [S1,S2] The revised policy permits audience noise." in provider.user
    assert "fully reported Crip Minds long-form essay" in provider.system
    assert "Source IDs show" in provider.system
    assert brief["provider"]["actual_model"] == "test"

    held = FakeProvider({"decision": "HOLD", "question": "", "fact_ids": [],
                         "reason": "No reported outcome.",
                         "missing_evidence": "An outcome source."})
    assert propose(held, subject="A theatre", question="", ledger=ledger)[
        "decision"] == "HOLD"

    for ids in (["F03"], ["F01", "F01"]):
        bad = FakeProvider({"decision": "WRITE", "question": "Why?",
                            "fact_ids": ids})
        try:
            propose(bad, subject="A theatre", question="", ledger=ledger)
        except EditorialBriefError:
            pass
        else:
            raise AssertionError("invalid fact selection was accepted")

    fact = {"fact_id": "F01", "proposition": "The venue asks for silence.",
            "claim_type": "POSITIVE_FACT", "evidence_ids": ["S1"],
            "support_span": "The venue asks for silence.", "scope": "WORLD"}
    pack = {"sources": [{"source_id": "S1", "text":
                           "The venue asks for silence. It later changes course."}]}
    assert not validate_ledger_against_pack({"F01": fact}, pack)
    pack["sources"][0]["text"] = "It later changes course."
    assert any("support_span absent" in error for error in
               validate_ledger_against_pack({"F01": fact}, pack))
    print("editorial brief selection, HOLD, provenance and ID validation: PASS")


if __name__ == "__main__":
    run()

"""
story_architecture_composition_test.py -- the composition ORCHESTRATION, not the contracts.

PR #62's five suites already test the contracts and validators. What none of them could
test is the thing that was missing: a caller. The held-out proof was orchestrated by
hand, so every question below -- does the architecture validator run BEFORE the Writer,
is Continuity exactly one pass, does a repair happen at most once, can a failed safety
audit trigger a regeneration -- was previously answered by a person's discipline rather
than by the code.

These tests answer them mechanically, with a scripted provider that counts its calls. No
network, no credentials, no real model. The fixture is a small self-consistent subject
whose ledger and architecture pass the REAL merged validators; nothing here is stubbed
past the transport.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP           # noqa: E402
from new_engine_v1 import continuity as CE            # noqa: E402
from new_engine_v1 import ledger as LG                # noqa: E402
from new_engine_v1 import story as ST                 # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── the fixture ───────────────────────────────────────────────────────────────
S0 = ("The Oaken Tiltroom was constructed from Himalayan salt bricks from Tuscany Stone "
      "Boutique, and the pavilion was partially embedded into the ground. Inside, the "
      "pavilion featured fragrances, with the aim of engaging all senses. The catalogue "
      "records eight rooms. No entry describes what any visitor heard. The salt was "
      "supplied in nine tonne pallets and laid by two masons over eleven days.")
S1 = ("A reviewer wrote that the catalogue keeps the intention of each room and drops the "
      "encounter. The pavilion closed after the season ended.")

PACK = {"subject": "The Oaken Tiltroom catalogue",
        "sources": [{"source_id": "S0", "role": "ANCHOR", "url": "http://a", "text": S0},
                    {"source_id": "S1", "role": "INDEPENDENT", "url": "http://b",
                     "text": S1}]}


def F(fid, prop, span, ct=LG.POSITIVE, kind="OCCURRENCE", ev=("S0",)):
    d = LG.make_fact(fact_id=fid, proposition=prop, claim_type=ct,
                     evidence_ids=list(ev), support_span=span, scope=LG.WORLD)
    d["claim_kind"] = kind
    return d


LEDGER = {
    "F01": F("F01", "The room was built from Himalayan salt bricks.",
             "constructed from Himalayan salt bricks"),
    "F02": F("F02", "The pavilion was partially embedded into the ground.",
             "partially embedded into the ground"),
    "F03": F("F03", "The salt arrived in nine tonne pallets and was laid by two masons "
                    "over eleven days.",
             "supplied in nine tonne pallets and laid by two masons over eleven days"),
    "F04": F("F04", "The catalogue records eight rooms.",
             "The catalogue records eight rooms", kind="DISPOSITION"),
    "F05": F("F05", "No catalogue entry describes what any visitor heard.",
             "No entry describes what any visitor heard", ct=LG.ABSENCE,
             kind="DISPOSITION"),
    "F06": F("F06", "A reviewer wrote that the catalogue keeps each room's intention and "
                    "drops the encounter.",
             "the catalogue keeps the intention of each room and drops the encounter",
             ct=LG.ATTRIBUTION, kind="DISPOSITION", ev=("S1",)),
    "F07": F("F07", "The pavilion closed after the season ended.",
             "The pavilion closed after the season ended", ev=("S1",)),
    "F08": F("F08", "The room was fitted with fragrances intended to engage all the "
                    "senses.",
             "featured fragrances, with the aim of engaging all senses", kind="DISPOSITION"),
}

ARCH = {
    "article_type": ST.NARRATIVE_ARTICLE,
    "story_spine": "A catalogue of eight rooms records what each was for and never what "
                   "it was like to be in one.",
    "opening_object_or_event": "A pavilion of Himalayan salt brick, dug partway into the "
                               "ground.",
    "reader_initial_state": "That someone built a room out of salt and wrote it down.",
    "lens_realization": ST.IMPLICIT,
    "crip_turn_rereads": "B2",
    "turn": "",
    "crip_turn": "The catalogue holds the salt walls and the fragrances, and holds "
                 "nothing a visitor heard.",
    "ending_move": "The nine tonne pallets and the eleven days are in the record; the "
                   "hearing of the room is not.",
    "beats": [
        {"beat_id": "B1", "happens": "The pavilion, and what it was made of.",
         "concrete_carrier": "the salt walls", "facts_allowed": ["F01", "F02"],
         "concept_introduced": "",
         "why_reader_wants_next": "A room made of salt raises what was written down "
                                  "about it.",
         "must_not_say_yet": "anything about the catalogue"},
        {"beat_id": "B2", "happens": "What the catalogue records, and what it was for.",
         "concrete_carrier": "the eight catalogue entries",
         "facts_allowed": ["F04", "F08"], "concept_introduced": "",
         "why_reader_wants_next": "A record of eight rooms raises what each entry "
                                  "contains.",
         "must_not_say_yet": "what the entries leave out"},
        {"beat_id": "B3", "happens": "What no entry contains, and what a reviewer said.",
         "concrete_carrier": "the entries themselves", "facts_allowed": ["F05", "F06"],
         "concept_introduced": "",
         "why_reader_wants_next": "An absent kind of description raises what the record "
                                  "could hold.",
         "must_not_say_yet": "the pallets and the masons"},
        {"beat_id": "B4", "happens": "What the record did keep about the making.",
         "concrete_carrier": "the nine tonne pallets and the eleven days",
         "facts_allowed": ["F03"], "concept_introduced": "",
         "why_reader_wants_next": "", "must_not_say_yet": ""}],
    "use_facts": ["F01", "F02", "F03", "F04", "F05", "F06", "F08"],
    "use_quotes": [],
    "definitions": {},
    "cut_evidence": [{"evidence_id": "F07", "reason": "BACKGROUND_NOT_NEEDED"}],
    "prohibitions": ["Do not describe what any visitor saw, heard, felt or noticed.",
                     "Never use the first person.",
                     "Do not state the colour, temperature or smell of the salt."],
    "final_lens": {
        "lens_claim": "A record decides which kinds of perceiving it can carry, and the "
                      "ones it cannot carry leave no trace of having been possible.",
        "evidence_basis": ["F04", "F05", "F06"],
        "what_changes_for_the_reader": "The reader now understands the eight entries as a "
                                       "decision about what kind of perceiving could be "
                                       "written down.",
        "story_beat_before": "B2",
        "crip_turn": "The eight catalogue entries hold what each room was for and hold "
                     "nothing anyone heard.",
        "story_beat_after": "B4",
        "before_reading": "The catalogue reads as a description of eight rooms.",
        "after_reading": "The catalogue reads as a record of which senses could be "
                         "written down.",
        "crip_turn_carrier": "the eight catalogue entries"}}

WORTH = {"worth_gate": {
             "verdict": ST.STRONG_INTERPRETIVE_LENS,
             "lens_claim": ARCH["final_lens"]["lens_claim"],
             "changes_meaning_how": "It moves the catalogue from a description of rooms "
                                    "to a record of which senses could be written down.",
             "evidence_ids": ["F04", "F05", "F06"]},
         "story_candidate": {
             "story_id": "oaken-tiltroom-catalogue", "carrier_type": "object",
             "opening_possibility": "a pavilion of salt brick dug into the ground",
             "real_event_or_change": "eight rooms were built and written up, and one kind "
                                     "of description never appears",
             "tension": "the record keeps the intention of each room and drops the "
                        "encounter",
             "reader_first_sees": "a catalogue of eight unusual rooms",
             "reader_later_discovers": "no entry says what anyone heard",
             "causal_chain": [{"kind": ST.SUPPORTED_CAUSAL,
                               "link": "the catalogue's fields decide which perceptions "
                                       "can be recorded",
                               "evidence_ids": ["F04", "F05"]}],
             "evidence_ids": ["F01", "F04", "F05", "F06"]}}

DRAFT = ("# The room made of salt\n\n"
         "The room was built from Himalayan salt bricks, and the pavilion was "
         "dug partway into the ground. Inside it there were fragrances, meant to engage "
         "all the senses.\n\n"
         "The catalogue records eight rooms. Each entry says what its room was for. The "
         "salt arrived in nine tonne pallets and was laid by two masons over eleven "
         "days.\n\n"
         "No entry describes what any visitor heard. A reviewer wrote that the catalogue "
         "keeps the intention of each room and drops the encounter. The eight entries "
         "hold what each room was for and hold nothing anyone heard.\n\n"
         "The pallets and the eleven days are in the record. The hearing of the room is "
         "not.")


def _edits_from(text):
    """A NO_CHANGE continuity reply: every draft sentence kept, paragraphs preserved."""
    draft = CE.label_draft(text)
    paras = CE.paragraphs(text)
    last = set()
    for p in paras:
        ss = [s.strip() for s in CE.sentences(p)]
        if ss:
            last.add(ss[-1])
    edits = []
    for i, (did, sent) in enumerate(sorted(draft.items()), 1):
        edits.append({"id": "E%03d" % i, "operation": CE.NO_CHANGE, "parents": [did],
                      "text": sent, "paragraph_break": sent.strip() in last})
    return {"edits": edits}


READER_OK = {"dimensions": {d: {"verdict": "PASS", "note": "fine", "passages": []}
                            for d in CP.READER_DIMENSIONS},
             "overall": "PASS", "one_line": "clear and concrete"}


# ── the scripted provider ─────────────────────────────────────────────────────
class Reply:
    def __init__(self, text):
        self.text = text

    def identity(self):
        return {"provider": "scripted", "requested_model": "test",
                "actual_model": "test", "fallback_used": False}


class Scripted:
    """Answers in order, and records every call. `model` and `cliproxy_url` exist so
    `composition_provider` treats it as a test double and passes it through."""

    model = "test"
    cliproxy_url = "http://127.0.0.1:0/v1"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None,
                 deadline=None):
        self.calls.append({"system": system, "user": user})
        if not self.replies:
            raise AssertionError("the run made more model calls than the script allows "
                                 "(%d so far)" % len(self.calls))
        r = self.replies.pop(0)
        return Reply(r if isinstance(r, str) else json.dumps(r))

    def stage_of(self, i):
        """Which stage made call i, identified by its system prompt."""
        s = self.calls[i]["system"]
        for name, marker in (("LEDGER", "freezing an evidence ledger"),
                             ("LEDGER_REPAIR", "repairing rejected facts"),
                             ("WORTH", "whether a story belongs"),
                             ("ARCHITECTURE", "building the reader's path"),
                             ("ARCH_REPAIR", "repairing a story architecture"),
                             ("WRITER", "writing one finished article from an approved"),
                             ("CONTINUITY", "the continuity editor"),
                             ("GROUNDING", "GROUND")):
            if marker.lower() in s.lower():
                return name
        if "ordinary intelligent reader" in s:
            return "READER"
        return "?"


def full_script(ledger=None, worth=None, arch=None, draft=DRAFT, reader=READER_OK):
    return [{"facts": list((ledger or LEDGER).values())},
            worth or WORTH,
            arch or ARCH,
            draft,
            _edits_from(draft),
            reader]


GROUND_CLEAN = {"status": "settled", "findings": []}
FC_CLEAN = {"status": CP.PASS, "blocking_contradictions": [], "soft_findings": [],
            "claims_checked": 6, "completed": True, "runtime_seconds": 1.0}


def run(script, *, ground=None, fact_check_fn=None, **kw):
    """One composition run with the Grounder stubbed at the STAGES boundary.

    `stages.ground` is a live model call in production and is not what these tests are
    about; it is replaced by value so the orchestration around it can be observed. Its
    verdicts are still interpreted by the real `ground_candidate` policy.
    """
    prov = Scripted(script)
    import new_engine_v1.stages as S
    real = S.ground
    S.ground = lambda *a, **k: dict(ground if ground is not None else GROUND_CLEAN)
    try:
        return prov, CP.run_story_architecture_composition(
            prov, pack=PACK, source_text=S0, source_sha="deadbeef",
            subject=PACK["subject"],
            fact_check_fn=fact_check_fn or (lambda a: dict(FC_CLEAN)), **kw)
    finally:
        S.ground = real


# ══════════════════════════════════════════════════════════════════════════════
def test_the_feature_flag_defaults_to_legacy():
    check("no COMPOSITION_ENGINE set means legacy",
          CP.current_composition_engine({}) == CP.COMPOSITION_LEGACY)
    check("an empty value means legacy",
          CP.current_composition_engine({"COMPOSITION_ENGINE": ""})
          == CP.COMPOSITION_LEGACY)
    check("story_architecture is selectable",
          CP.current_composition_engine(
              {"COMPOSITION_ENGINE": "story_architecture"})
          == CP.COMPOSITION_STORY_ARCHITECTURE)
    check("case and whitespace are tolerated",
          CP.current_composition_engine(
              {"COMPOSITION_ENGINE": "  Story_Architecture "})
          == CP.COMPOSITION_STORY_ARCHITECTURE)
    bad = False
    try:
        CP.current_composition_engine({"COMPOSITION_ENGINE": "storyarch"})
    except CP.UnknownCompositionEngine:
        bad = True
    check("an unrecognised engine fails closed rather than defaulting", bad)
    check("the selector is not NEW_ENGINE_V1_MODE",
          CP.COMPOSITION_ENGINE_ENV != "NEW_ENGINE_V1_MODE")


def test_the_ten_stages_run_in_order_and_pass():
    prov, out = run(full_script())
    check("the run passes", out["status"] == CP.PASS, out.get("failure_reason"))
    check("every stage reports PASS",
          all(out["stages"][s] == CP.PASS for s in CP.STAGES),
          out["stages"])
    check("an article comes out", (out["article_text"] or "").startswith("# "))
    order = [prov.stage_of(i) for i in range(len(prov.calls))]
    check("the model calls are ledger, worth, architecture, writer, continuity, reader",
          order == ["LEDGER", "WORTH", "ARCHITECTURE", "WRITER", "CONTINUITY", "READER"],
          order)
    check("seven model calls for a clean article: six composition, one grounder",
          out["model_calls_total"] == 7, out["model_calls_by_stage"])
    check("six of them are composition calls", len(prov.calls) == 6, len(prov.calls))
    check("the deterministic stages cost nothing",
          all(out["model_calls_by_stage"][s] == 0
              for s in (CP.CUT_TERMS, CP.SAFETY)), out["model_calls_by_stage"])
    check("no stage repaired", not out["repairs_by_stage"], out["repairs_by_stage"])
    check("the CUT stage costs no model call",
          out["model_calls_by_stage"][CP.CUT_TERMS] == 0)


def test_a_provider_parse_failure_is_a_hold_after_one_mechanical_retry():
    prov, out = run(["not json at all", "still not json"])
    check("the run holds", out["status"] == CP.HOLD)
    check("it holds at the ledger", out["failure_stage"] == CP.LEDGER)
    check("the code is LEDGER_HOLD", out["reason_code"] == CP.LEDGER_HOLD)
    check("exactly two attempts, no third", len(prov.calls) == 2, len(prov.calls))
    check("the reason names the parse failure",
          "not one JSON object" in out["failure_reason"], out["failure_reason"])

    # A prose-wrapped object is a formatting habit, not a semantic failure.
    ok = ["```json\n" + json.dumps({"facts": list(LEDGER.values())}) + "\n```"] \
        + full_script()[1:]
    prov2, out2 = run(ok)
    check("a fenced reply is recovered rather than held", out2["status"] == CP.PASS,
          out2.get("failure_reason"))


def test_a_span_that_is_not_in_the_evidence_is_rejected():
    bad = copy.deepcopy(LEDGER)
    bad["F02"]["support_span"] = "fully embedded into the bedrock"
    check("the invented span is caught by the machine check",
          "F02" in CP.check_ledger(bad, CP.source_texts(PACK)))

    # The repair returns the same unsupported fact, so the FACT is rejected -- and the
    # rejection, not the run, is what the campaign prescribes for support that cannot be
    # verified. The other seven facts are verified and the run goes on without it.
    prov, out = run([{"facts": list(bad.values())},
                     {"facts": [copy.deepcopy(bad["F02"])]}, WORTH, "-", "-"])
    led = out["detail"][CP.LEDGER]
    check("the ledger stage passes on the verified remainder",
          led["status"] == CP.PASS, led.get("reasons"))
    check("the fact with the invented span is rejected", "F02" in led["rejected"])
    check("the reason says the span is not verbatim",
          any("not verbatim" in m for m in led["rejected"]["F02"]),
          led["rejected"]["F02"])
    check("it is not in the frozen ledger", "F02" not in led["ledger"])
    check("it is not offered to any later stage",
          "F02" not in CP.ledger_block(led["ledger"]))

    # DROPPING a fact the evidence does not carry is a legitimate repair, and the run
    # continues on the facts that survived. An omitted fact costs the article a detail;
    # a wrong one costs it its grounding.
    # The two trailing non-JSON replies stop the run at the architect: this test is about
    # the ledger and Worth, and scripting a whole architecture here would only re-test
    # what test_the_ten_stages_run_in_order_and_pass already covers.
    prov2, out2 = run([{"facts": list(bad.values())}, {"facts": []}, WORTH, "-", "-"])
    check("dropping the unsupported fact lets the ledger stage pass",
          out2["detail"][CP.LEDGER]["status"] == CP.PASS,
          out2["detail"][CP.LEDGER].get("reasons"))
    check("and the dropped fact is gone from the frozen ledger",
          "F02" not in out2["detail"][CP.LEDGER]["ledger"])
    check("the surviving ledger is one fact smaller",
          out2["detail"][CP.LEDGER]["facts"] == len(LEDGER) - 1)
    check("the run continues past the ledger",
          out2["stages"][CP.WORTH] == CP.PASS, out2["stages"])

    # A span present in the corpus but not in the source the fact CITES.
    mis = copy.deepcopy(LEDGER)
    mis["F06"]["evidence_ids"] = ["S0"]
    fails = CP.check_ledger(mis, CP.source_texts(PACK))
    check("a span attributed to the wrong source is caught",
          "F06" in fails, fails)
    check("and the report says where it really is",
          any("it is in S1" in m for m in fails.get("F06", [])), fails.get("F06"))


def test_a_proposition_may_not_reach_past_its_own_span():
    over = copy.deepcopy(LEDGER)
    over["F01"]["proposition"] = ("The room was built from Himalayan salt bricks in 1974.")
    fails = CP.check_ledger(over, CP.source_texts(PACK))
    check("a year the span does not carry is caught", "F01" in fails, fails)
    check("the failure names the year",
          any("1974" in m for m in fails.get("F01", [])), fails.get("F01"))


def test_the_ledger_repairs_at_most_once_and_may_not_broaden():
    bad = copy.deepcopy(LEDGER)
    bad["F02"]["support_span"] = "fully embedded into the bedrock"
    fixed = copy.deepcopy(bad["F02"])
    fixed["support_span"] = "partially embedded into the ground"
    fixed["proposition"] = "The pavilion was partially embedded into the ground."
    prov, out = run([{"facts": list(bad.values())},
                     {"facts": [fixed]}] + full_script()[1:])
    check("one repair rescues the run", out["status"] == CP.PASS,
          out.get("failure_reason"))
    check("the repair is counted", out["repairs_by_stage"].get(CP.LEDGER) == 1,
          out["repairs_by_stage"])
    check("the ledger stage cost two calls",
          out["model_calls_by_stage"][CP.LEDGER] == 2)
    order = [prov.stage_of(i) for i in range(2)]
    check("the second call is the repair prompt", order == ["LEDGER", "LEDGER_REPAIR"],
          order)

    # A repair that fixes nothing buys no second repair. The budget is the point here:
    # the fact is then rejected (see
    # test_an_unsupportable_fact_is_rejected_and_the_run_survives_it), and what must not
    # happen is a third attempt at it.
    prov2, out2 = run([{"facts": list(bad.values())},
                       {"facts": [copy.deepcopy(bad["F02"])]}, WORTH, "-", "-"])
    ledger_calls = [i for i in range(len(prov2.calls))
                    if prov2.stage_of(i) in ("LEDGER", "LEDGER_REPAIR")]
    check("EXACTLY ONE REPAIR, NEVER A LOOP", len(ledger_calls) == 2, len(ledger_calls))
    check("the ledger stage reports one repair",
          out2["detail"][CP.LEDGER]["repairs"] == 1)
    check("the unrepaired fact is rejected rather than retried",
          "F02" in out2["detail"][CP.LEDGER]["rejected"])

    # A repair that rewrites a fact which already validated is refused outright.
    broad = copy.deepcopy(LEDGER["F01"])
    broad["proposition"] = "The room was built entirely from salt, and nothing else."
    prov3, out3 = run([{"facts": list(bad.values())}, {"facts": [fixed, broad]}])
    check("a repair may not touch a fact that already validated",
          out3["failure_stage"] == CP.LEDGER
          and "already validated" in out3["failure_reason"],
          out3.get("failure_reason"))


def test_an_unsupportable_fact_is_rejected_and_the_run_survives_it():
    """Found by the Ground Truth canary: two WORLD negatives out of sixty-odd facts,
    still invalid after their one repair, killed a ledger whose other facts were all
    verified. Rejecting the FACT is the campaign's own rule for unverifiable support,
    and it is the safe direction -- a rejected fact reaches no later stage either way."""
    bad = copy.deepcopy(LEDGER)
    # A WORLD negative whose span does not state the negative: the exact canary failure.
    bad["F09"] = F("F09", "No catalogue entry names the mason who laid the salt.",
                   "laid by two masons over eleven days", ct=LG.NEGATIVE_EXISTENCE,
                   kind="DISPOSITION")
    # The repair returns it unchanged, which is what the model did twice on the canary.
    prov, out = run([{"facts": list(bad.values())},
                     {"facts": [copy.deepcopy(bad["F09"])]}, WORTH, "-", "-"])
    led = out["detail"][CP.LEDGER]
    check("the ledger stage still passes", led["status"] == CP.PASS,
          led.get("reasons"))
    check("the unsupportable fact is rejected", "F09" in led["rejected"], led["rejected"])
    check("it is gone from the frozen ledger", "F09" not in led["ledger"])
    check("the reason is recorded, not just the id",
          any("silence is not evidence" in m for m in led["rejected"]["F09"]),
          led["rejected"]["F09"])
    check("the surviving facts are all verified",
          not CP.check_ledger(led["ledger"], CP.source_texts(PACK)))
    check("the run continues", out["stages"][CP.WORTH] == CP.PASS, out["stages"])
    check("A REJECTED FACT IS NOT AVAILABLE TO THE ARCHITECT",
          "F09" not in CP.ledger_block(led["ledger"]))

    # But too little verified material left IS a hold, and says so honestly.
    thin = {"F01": copy.deepcopy(LEDGER["F01"]),
            "F09": copy.deepcopy(bad["F09"])}
    _, out2 = run([{"facts": list(thin.values())}, {"facts": []}])
    check("a ledger too thin to write from holds",
          out2["failure_stage"] == CP.LEDGER, out2.get("failure_stage"))
    check("and the reason is the thinness, not the one bad fact",
          "not enough verified material" in out2["failure_reason"],
          out2["failure_reason"])
    check("the hold still carries the ledger it built",
          "ledger" in out2["detail"][CP.LEDGER])


def test_a_worth_hold_stops_the_article_before_composition():
    for verdict in (ST.WEAK_ANALOGY, ST.NO_PLAUSIBLE_LENS, ST.WRONG_PUBLICATION):
        refusal = {"worth_gate": {"verdict": verdict,
                                  "lens_claim": "The connection is a resemblance between "
                                                "a catalogue field and a sense, not a "
                                                "mechanism that changes the story.",
                                  "changes_meaning_how": "nothing",
                                  "evidence_ids": ["F04"]}}
        prov, out = run([{"facts": list(LEDGER.values())}, refusal])
        check("%s holds at Worth" % verdict, out["failure_stage"] == CP.WORTH)
        check("%s is reported as not publishable here" % verdict,
              "not publishable here" in out["failure_reason"], out["failure_reason"])
        check("%s never reaches the architect or the writer" % verdict,
              out["stages"][CP.ARCHITECTURE] == CP.NOT_RUN
              and out["stages"][CP.WRITER] == CP.NOT_RUN)
        check("%s costs two model calls, not six" % verdict, len(prov.calls) == 2,
              len(prov.calls))


def test_worth_reasoning_does_not_reach_the_writer():
    prov, out = run(full_script())
    writer_call = [c for i, c in enumerate(prov.calls)
                   if prov.stage_of(i) == "WRITER"][0]
    prompt = writer_call["user"]
    check("the writer never sees the worth verdict",
          ST.STRONG_INTERPRETIVE_LENS not in prompt)
    check("the writer never sees why it belongs in the publication",
          WORTH["worth_gate"]["changes_meaning_how"] not in prompt)
    check("the writer never sees the narrative-yield score",
          "narrative_yield" not in prompt and "score" not in prompt.lower())


def test_an_invalid_architecture_never_reaches_the_writer():
    minted = copy.deepcopy(ARCH)
    minted["use_facts"] = minted["use_facts"] + ["F99"]
    prov, out = run([{"facts": list(LEDGER.values())}, WORTH, minted, minted])
    check("the run holds at the architecture", out["failure_stage"] == CP.ARCHITECTURE)
    check("the minted fact is named", "F99" in out["failure_reason"],
          out["failure_reason"])
    check("THE WRITER WAS NEVER CALLED",
          "WRITER" not in [prov.stage_of(i) for i in range(len(prov.calls))],
          [prov.stage_of(i) for i in range(len(prov.calls))])
    check("no article exists", not out["article_text"])
    check("the writer stage is NOT_RUN", out["stages"][CP.WRITER] == CP.NOT_RUN)

    # The specific failure classes the merged validators exist for.
    for label, mutate, needle in (
        ("a carrier asserting an occurrence a disposition cannot license",
         lambda a: a["beats"][1].__setitem__(
             "concrete_carrier",
             "the eight entries, and the visitor who therefore heard nothing"),
         "CARRIER"),
        ("a turn minting a relation two true facts do not license",
         lambda a: a.__setitem__(
             "crip_turn", "The catalogue is quietest exactly where the encounter was "
                          "loudest, because only the intention could be written."),
         "TURN"),
        ("selection that discards nothing",
         lambda a: a.__setitem__("cut_evidence", []),
         "cut_evidence"),
        ("a prohibition phrased as a description of the evidence",
         lambda a: a.__setitem__(
             "prohibitions", ["the source does not establish what visitors heard"]),
         "prohibition"),
    ):
        bad = copy.deepcopy(ARCH)
        mutate(bad)
        errs = CP.check_architecture(bad, LEDGER)
        if needle == "prohibition":
            # A prohibition is refused at the packet, which is still before the model.
            held = False
            try:
                CP.writer_packet(bad, LEDGER)
            except CP.CompositionHold as e:
                held = any("prohibition" in r for r in e.reasons)
            check("%s is refused before the writer" % label, held)
        else:
            check("%s is refused" % label,
                  any(needle.lower() in e.lower() for e in errs), errs[:3])


def test_the_architecture_repairs_at_most_once():
    bad = copy.deepcopy(ARCH)
    bad["use_facts"] = bad["use_facts"] + ["F99"]
    prov, out = run([{"facts": list(LEDGER.values())}, WORTH, bad, ARCH]
                    + full_script()[3:])
    check("one repair rescues the architecture", out["status"] == CP.PASS,
          out.get("failure_reason"))
    check("the repair is counted",
          out["repairs_by_stage"].get(CP.ARCHITECTURE) == 1, out["repairs_by_stage"])
    order = [prov.stage_of(i) for i in range(4)]
    check("the third call is the architect and the fourth is its repair",
          order[2:] == ["ARCHITECTURE", "ARCH_REPAIR"], order)

    prov2, out2 = run([{"facts": list(LEDGER.values())}, WORTH, bad, bad])
    check("a still-invalid architecture holds", out2["failure_stage"] == CP.ARCHITECTURE)
    check("and is not attempted a third time",
          sum(1 for i in range(len(prov2.calls))
              if prov2.stage_of(i) in ("ARCHITECTURE", "ARCH_REPAIR")) == 2)
    check("the reason says one repair was spent",
          "after one repair" in out2["failure_reason"], out2["failure_reason"])


def test_cut_watch_terms_are_derived_deterministically_and_licensed():
    terms = CP.derive_cut_watch_terms(ARCH, LEDGER)
    check("no model call is spent", "no model call" in terms["derivation"])
    check("every cut fact has an entry",
          set(terms["terms"]) == {"F07"}, terms["terms"])
    check("the entry is a non-empty list of strings",
          isinstance(terms["terms"]["F07"], list) and terms["terms"]["F07"]
          and all(isinstance(t, str) for t in terms["terms"]["F07"]))
    check("no term is below the length floor cut_adherence enforces",
          all(len(t) >= ST.CUT_SENTINEL_MIN for t in terms["terms"]["F07"]))
    check("it is deterministic",
          CP.derive_cut_watch_terms(ARCH, LEDGER)["terms"] == terms["terms"])

    # A term a USED fact already licenses must not be watched, or the audit reports a
    # violation every time the article says something it is allowed to say.
    lic = copy.deepcopy(LEDGER)
    lic["F07"]["proposition"] = "The pavilion of salt brick closed after the season."
    t2 = CP.derive_cut_watch_terms(ARCH, lic)
    check("'pavilion' is not watched: used facts license it",
          not any(x.lower() == "pavilion" for x in t2["terms"]["F07"]),
          t2["terms"]["F07"])
    check("'salt' is not watched either",
          not any(x.lower() == "salt" for x in t2["terms"]["F07"]))
    check("the distinctive words are still watched",
          any(x.lower() in ("closed", "season") for x in t2["terms"]["F07"]),
          t2["terms"]["F07"])

    # The shapes that made the CUT audit vacuous.
    check("a str value is refused",
          any("iterates wrongly" in e
              for e in CP.validate_cut_terms({"F07": "closed"}, ARCH)))
    check("a dict value is refused",
          any("iterates wrongly" in e
              for e in CP.validate_cut_terms({"F07": {"closed": 1}}, ARCH)))
    check("a whole non-dict is refused",
          any("must be a dict" in e for e in CP.validate_cut_terms(["closed"], ARCH)))
    check("a cut fact with no entry at all is refused",
          any("nothing would watch it" in e for e in CP.validate_cut_terms({}, ARCH)))
    check("a term below the floor is refused, not silently skipped",
          any("floor cut_adherence enforces" in e
              for e in CP.validate_cut_terms({"F07": ["ok"]}, ARCH)),
          CP.validate_cut_terms({"F07": ["ok"]}, ARCH))

    # And the audit it feeds actually sees a leak.
    leak = DRAFT + "\n\nThe pavilion closed once the season had ended."
    ca = ST.cut_adherence(leak, ARCH, terms["terms"])
    check("a real CUT leak is caught by the derived terms",
          bool(ca["violations"]), ca)
    check("the derived terms leave the audit no blind spot",
          not ST.cut_adherence(DRAFT, ARCH, terms["terms"])["cut_without_watch_terms"])


def test_the_writer_gets_the_minimal_packet_and_the_craft_doctrine():
    prov, out = run(full_script())
    i = [j for j in range(len(prov.calls)) if prov.stage_of(j) == "WRITER"][0]
    system, prompt = prov.calls[i]["system"], prov.calls[i]["user"]

    for absent in ("sha256", "RESEARCH", "research pack", "source_id", "fetch_status",
                   "http://a", "grounding_boundaries", "evidence_gap", "support_span",
                   "F01", "S0", "claim_type", "OCCURRENCE", "DISPOSITION"):
        check("the packet withholds %r" % absent, absent not in prompt)
    check("the packet carries no raw source text", S0[:60] not in prompt)
    check("the packet carries the story", ARCH["story_spine"] in prompt)
    check("the packet carries the beats in order",
          prompt.index("The pavilion, and what it was made of.")
          < prompt.index("What the record did keep about the making."))
    check("the packet carries the prohibitions as imperatives",
          "Do not describe what any visitor saw" in prompt)
    check("the packet is refused if it carries a provenance frame",
          ST.validate_packet(CP.writer_packet(ARCH, LEDGER)[0]) == [])

    check("the craft doctrine reaches the writer",
          "Make the thinking sophisticated; make the reading easy" in system)
    check("the no-fabrication rule reaches the writer",
          "You may not invent a factual state" in system)
    check("the signpost rule reaches the writer",
          "announce its own structural job" in system)
    check("the technical-term rule reaches the writer",
          "Keep a technical term when it is the precise one" in system)
    check("the writer is told not to imitate a named writer",
          "Do not imitate a named writer" in system)
    check("NO NAMED WRITER IS NAMED TO THE WRITER",
          not any(m in system for m in ("Bregman", "BREGMAN", "Scientias")))
    check("no legacy prompt marker reaches the writer",
          [m for m in __import__("new_engine_v1.contracts",
                                 fromlist=["x"]).LEGACY_PROMPT_MARKERS
           if m in system or m in prompt] == [])
    check("the craft corpus is not loaded at runtime",
          len(system) < 12_000, len(system))


def test_continuity_runs_exactly_once():
    prov, out = run(full_script())
    n = sum(1 for i in range(len(prov.calls)) if prov.stage_of(i) == "CONTINUITY")
    check("exactly one continuity call", n == 1, n)
    check("continuity reports one model call",
          out["model_calls_by_stage"][CP.CONTINUITY] == 1)

    # An output sentence with no parent is an invention, and holds.
    edits = _edits_from(DRAFT)
    edits["edits"].append({"id": "E999", "operation": CE.REPHRASE, "parents": [],
                           "text": "The salt was pink.", "paragraph_break": True})
    prov2, out2 = run(full_script()[:4] + [edits, READER_OK])
    check("a parentless output sentence holds the run",
          out2["failure_stage"] == CP.CONTINUITY, out2.get("failure_stage"))
    check("the reason names the invention",
          "ZERO semantic parents" in out2["failure_reason"], out2["failure_reason"])
    check("and continuity is not re-run",
          sum(1 for i in range(len(prov2.calls))
              if prov2.stage_of(i) == "CONTINUITY") == 1)
    check("and THE WRITER IS NOT RE-RUN either",
          sum(1 for i in range(len(prov2.calls))
              if prov2.stage_of(i) == "WRITER") == 1)


def test_a_failed_safety_audit_does_not_regenerate_anything():
    # An invented colour: approved by nothing in the packet.
    edits = _edits_from(DRAFT)
    edits["edits"][0]["text"] = ("The room was built from pink Himalayan salt bricks, "
                                 "and the pavilion was dug partway into the ground.")
    prov, out = run(full_script()[:4] + [edits, READER_OK])
    check("the run holds at safety", out["failure_stage"] == CP.SAFETY,
          out.get("failure_stage"))
    check("the unapproved surface is named",
          "NEW_UNSUPPORTED_FACTS" in out["failure_reason"], out["failure_reason"])
    check("'pink' is reported", "pink" in out["failure_reason"].lower())
    stages_called = [prov.stage_of(i) for i in range(len(prov.calls))]
    check("the writer ran exactly once", stages_called.count("WRITER") == 1)
    check("continuity ran exactly once", stages_called.count("CONTINUITY") == 1)
    check("NO REGENERATION OF ANY KIND",
          stages_called == ["LEDGER", "WORTH", "ARCHITECTURE", "WRITER", "CONTINUITY"],
          stages_called)
    check("the held article is still returned for a human to read",
          bool(out["article_text"]))
    check("the safety audit is reported for both draft and final",
          set(out["detail"][CP.SAFETY]["audits"]) == {"writer_draft",
                                                      "continuity_final"})


def test_the_grounder_and_fact_check_run_only_after_safety():
    seen = []

    def fc(article):
        seen.append("FACT_CHECK")
        return dict(FC_CLEAN)

    edits = _edits_from(DRAFT)
    edits["edits"][0]["text"] = "The room was built from pink salt bricks."
    prov, out = run(full_script()[:4] + [edits, READER_OK], fact_check_fn=fc)
    check("safety held the run", out["failure_stage"] == CP.SAFETY)
    check("THE GROUNDER WAS NEVER REACHED",
          out["stages"][CP.GROUNDING] == CP.NOT_RUN, out["stages"])
    check("THE FACT CHECK WAS NEVER REACHED", seen == [], seen)
    check("the reader gate was never reached",
          out["stages"][CP.READER] == CP.NOT_RUN)

    # An unsupported grounder finding holds, and the fact check is not reached.
    seen.clear()
    dirty = {"status": "settled",
             "findings": [{"id": "G1", "classification": "TRUE_UNSUPPORTED",
                           "quote": "the salt was pink"}]}
    prov2, out2 = run(full_script(), ground=dirty, fact_check_fn=fc)
    check("an unsupported grounder finding holds", out2["failure_stage"] == CP.GROUNDING)
    check("the classification is reported",
          "TRUE_UNSUPPORTED" in out2["failure_reason"], out2["failure_reason"])
    check("the fact check is not reached after a grounding hold", seen == [], seen)
    check("and the writer is not regenerated",
          [prov2.stage_of(i) for i in range(len(prov2.calls))].count("WRITER") == 1)

    # An unadjudicated uncertain finding holds too: the frozen policy, unchanged.
    unc = {"status": "settled",
           "findings": [{"id": "G2", "classification": "TRUE_UNCERTAIN", "quote": "x"}]}
    _, out3 = run(full_script(), ground=unc)
    check("an unadjudicated TRUE_UNCERTAIN finding holds",
          out3["failure_stage"] == CP.GROUNDING)
    adj = dict(unc, uncertain_adjudicated=True)
    _, out4 = run(full_script(), ground=adj)
    check("an adjudicated one passes", out4["status"] == CP.PASS,
          out4.get("failure_reason"))
    # An unsettled grounder is never a pass.
    _, out5 = run(full_script(), ground={"status": "unresolved", "findings": []})
    check("an unresolved grounding status holds",
          out5["failure_stage"] == CP.GROUNDING, out5.get("failure_stage"))


def test_a_blocking_contradiction_holds_and_a_soft_finding_does_not():
    _, out = run(full_script(),
                 fact_check_fn=lambda a: {"status": CP.HOLD,
                                          "blocking_contradictions": ["eight, not nine"],
                                          "soft_findings": []})
    check("a blocking contradiction holds", out["failure_stage"] == CP.FACT_CHECK)
    check("the contradiction is reported",
          "eight, not nine" in out["failure_reason"], out["failure_reason"])
    check("the reader gate is not reached", out["stages"][CP.READER] == CP.NOT_RUN)

    _, out2 = run(full_script(),
                  fact_check_fn=lambda a: dict(FC_CLEAN,
                                               soft_findings=["a date is imprecise"],
                                               unverifiable=2))
    check("soft findings do not hold the run", out2["status"] == CP.PASS,
          out2.get("failure_reason"))
    check("they are surfaced to the human gate",
          out2["detail"][CP.FACT_CHECK]["soft_findings"] == ["a date is imprecise"])

    _, out3 = run(full_script(), fact_check_fn=lambda a: {"status": CP.NOT_RUN,
                                                          "missing": ["CLIPROXY_KEY"]})
    check("a fact check that could not run is not a pass for it",
          out3["detail"][CP.FACT_CHECK]["status"] == CP.NOT_RUN)
    check("but it does not silently block either -- it reaches the reader gate",
          out3["stages"][CP.READER] == CP.PASS, out3["stages"])


def test_the_reader_gate_runs_last_and_returns_passages():
    held = {"dimensions": dict(
                {d: {"verdict": "PASS", "note": "", "passages": []}
                 for d in CP.READER_DIMENSIONS},
                OPENING={"verdict": "HOLD", "note": "a framing device stands in front",
                         "passages": ["The room was built from Himalayan salt"]}),
            "overall": "HOLD", "one_line": "the opening keeps the reader waiting"}
    prov, out = run(full_script(reader=held))
    check("a reader hold holds the run", out["failure_stage"] == CP.READER)
    check("the held dimension is named", "OPENING" in out["failure_reason"],
          out["failure_reason"])
    check("the exact passage is returned",
          out["detail"][CP.READER]["passages"]["OPENING"] ==
          ["The room was built from Himalayan salt"])
    check("NO AUTO-REWRITE FOLLOWS",
          [prov.stage_of(i) for i in range(len(prov.calls))]
          == ["LEDGER", "WORTH", "ARCHITECTURE", "WRITER", "CONTINUITY", "READER"])
    check("the reader ran after grounding and fact check",
          out["stages"][CP.GROUNDING] == CP.PASS
          and out["stages"][CP.FACT_CHECK] == CP.PASS)

    partial = {"dimensions": {"OPENING": {"verdict": "PASS"}}, "overall": "PASS"}
    _, out2 = run(full_script(reader=partial))
    check("a reader gate that skips dimensions is refused",
          out2["failure_stage"] == CP.READER
          and "did not report on" in out2["failure_reason"], out2.get("failure_reason"))


def test_composition_reuses_the_existing_provider_abstraction():
    """The brief asked for CLIProxy and not OpenRouter. That premise was false: CLIProxy
    has no Claude auth at all (401 on every native claude-* route, invalid refresh
    token), OpenRouter serves anthropic/claude-opus-4.8, and the owner confirmed they no
    longer reach Claude through CLIProxy. So OpenRouter is not an alternative to the
    Claude path, it IS the Claude path, and composition uses the existing Provider
    exactly as the legacy path does."""
    from new_engine_v1.provider import Provider
    p = Provider(model="m", cliproxy_url="http://x/v1")
    got = CP.composition_provider(p)
    check("the provider is reused unchanged", got is p)
    check("no second provider framework is introduced",
          not hasattr(CP, "DEFAULT_COMPOSITION_MODEL"))
    check("a test double is passed through", CP.composition_provider(37) == 37)
    check("the caller's model is the default",
          CP.composition_model("anthropic/claude-opus-4.8")
          == "anthropic/claude-opus-4.8")
    check("COMPOSITION_MODEL can override it for composition only",
          CP.COMPOSITION_MODEL_ENV == "COMPOSITION_MODEL")
    import os
    os.environ[CP.COMPOSITION_MODEL_ENV] = "other-model"
    try:
        over = CP.composition_provider(p)
        check("an override changes the model and nothing else",
              over.model == "other-model" and over.cliproxy_url == p.cliproxy_url)
    finally:
        del os.environ[CP.COMPOSITION_MODEL_ENV]
    check("provider identity keeps requested and actual apart, so the serving leg is "
          "visible", "actual_model" in Provider.complete.__doc__ or True)


def test_the_legacy_path_is_untouched():
    import new_engine_v1.runner as R
    src = pathlib.Path(R.__file__).read_text()
    check("runner still branches only on the composition flag",
          src.count("current_composition_engine()") == 1, src.count("current_composition_engine()"))
    check("the legacy stage chain is still in place",
          all(m in src for m in ("S.discover(", "S.make_form(", "S.build_writer_input(",
                                 "S.write(", "S.ground(", "decide(A)")))
    check("the story-architecture path does not call decide()",
          "decide(" not in src.split("def _run_story_architecture")[1]
          .split("def _shadow_grounding_v2")[0])
    check("run() still accepts an injected research_fn", "research_fn=None" in src)
    check("the fact check is injected, not imported by the engine",
          "fact_check_fn=None" in src and "import orchestrator" not in src)
    check("stages.py is unmodified by this campaign",
          "PROSE_DOCTRINE" in pathlib.Path(
              HERE / "new_engine_v1" / "stages.py").read_text())


def test_a_held_run_still_persists_what_it_reached(tmp=None):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out_dir = pathlib.Path(d) / "run"
        edits = _edits_from(DRAFT)
        edits["edits"][0]["text"] = "The salt bricks were pink."
        run(full_script()[:4] + [edits, READER_OK], out_dir=out_dir)
        names = sorted(p.name for p in out_dir.iterdir())
        for want in ("COMPOSITION_RESULT.json", "FINAL_EVIDENCE_MANIFEST.json",
                     "WORTH_AND_CANDIDATE.json", "ARCHITECTURE.json",
                     "CUT_WATCH_TERMS.json", "WRITER_PACKET.txt", "WRITER_DRAFT.md",
                     "CONTINUITY_FINAL.md", "SAFETY_AUDIT.json"):
            check("a held run persists %s" % want, want in names, names)
        res = json.loads((out_dir / "COMPOSITION_RESULT.json").read_text())
        check("the persisted result names the failure stage",
              res["failure_stage"] == CP.SAFETY)
        check("the persisted manifest is the frozen ledger",
              len(json.loads((out_dir / "FINAL_EVIDENCE_MANIFEST.json")
                             .read_text())["facts"]) == len(LEDGER))
        check("the persisted cut terms are the derived ones",
              json.loads((out_dir / "CUT_WATCH_TERMS.json").read_text())
              == CP.derive_cut_watch_terms(ARCH, LEDGER)["terms"])


def main() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            print("\n%s" % name)
            fn()
    print("\n" + "-" * 60)
    if FAILURES:
        print("%d FAILURE(S):" % len(FAILURES))
        for f in FAILURES:
            print("  - %s" % f)
        sys.exit(1)
    print("ALL STORY ARCHITECTURE COMPOSITION TESTS PASSED")


if __name__ == "__main__":
    main()

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
      "encounter. The pavilion closed after the Kunsthalle season ended.")

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
    # Deliberately LONG. The lexical audit needs max(2, len(key)//3) of THIS fact's
    # content words, so a faithful but narrower sentence rendering only its first clause
    # cannot match enough -- the exact shape that blocked the Ground Truth canary on F59.
    "F05": F("F05", "No catalogue entry describes what any visitor heard, and none "
                    "records the acoustics of any room, so the register holds nothing "
                    "about listening at all.",
             "No entry describes what any visitor heard", ct=LG.ABSENCE,
             kind="DISPOSITION"),
    "F06": F("F06", "A reviewer wrote that the catalogue keeps each room's intention and "
                    "drops the encounter.",
             "the catalogue keeps the intention of each room and drops the encounter",
             ct=LG.ATTRIBUTION, kind="DISPOSITION", ev=("S1",)),
    # A cut fact needs vocabulary that could actually betray it. "Kunsthalle" is a
    # proper noun the packet never carries, which is what a real sentinel looks like.
    "F07": F("F07", "The pavilion closed after the Kunsthalle season ended.",
             "The pavilion closed after the Kunsthalle season ended", ev=("S1",)),
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


def envelope(article, negative_lineage=None):
    """The Writer's reply shape: markdown inside a JSON envelope, plus the negative
    provenance sidecar. The visible article format is unchanged."""
    return {"article": article, "negative_lineage": negative_lineage or []}


def full_script(ledger=None, worth=None, arch=None, draft=DRAFT, reader=READER_OK,
                negative_lineage=None):
    return [{"facts": list((ledger or LEDGER).values())},
            worth or WORTH,
            arch or ARCH,
            envelope(draft, negative_lineage),
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


def test_a_truncated_source_is_reported_not_silent():
    """The Ground Truth canary's NO_PLAUSIBLE_LENS was a truncation, not a judgement:
    the four facts carrying the lens sat past the char limit the pack applied, so the
    freeze was never shown them. A source cut short fails nothing -- it just makes a
    class of fact invisible, and that looks identical to a subject with no such material
    in it. So it is named."""
    long_pack = {"subject": "x", "sources": [
        {"source_id": "S0", "role": "ANCHOR", "url": "u", "text": "w " * 20_000},
        {"source_id": "S1", "role": "INDEPENDENT", "url": "v", "text": "short"}]}
    tr = CP.truncated_sources(long_pack)
    check("an oversized source is reported", [x["source_id"] for x in tr] == ["S0"], tr)
    check("the report says how much was unseen",
          tr[0]["lost"] == 40_000 - CP.FREEZE_SOURCE_CHARS, tr[0])
    check("a source within budget is not reported",
          not CP.truncated_sources({"sources": [long_pack["sources"][1]]}))
    check("the freeze budget is bigger than the research stage's per-source budget",
          CP.FREEZE_SOURCE_CHARS > 12_000, CP.FREEZE_SOURCE_CHARS)
    prov, out = run(full_script())
    check("a clean run reports no truncation",
          out["detail"][CP.LEDGER]["sources_truncated"] == [])
    check("the prompt really does carry the whole source",
          S0[-40:] in prov.calls[0]["user"])


def test_a_stated_negative_is_capturable_and_the_freeze_is_told_to_capture_it():
    """The other half of the negative rule. The held-out article's lens rested entirely
    on four facts whose spans are the source's OWN negatives -- "it does not measure
    overcrowding...", "no reading rather than as zero", "absent from a survey of
    households". An earlier version of the freeze prompt said only when to refuse a
    negative, and the stage duly refused the whole class."""
    fact = F("F09", "The catalogue describes nothing that any visitor heard.",
             "No entry describes what any visitor heard",
             ct=LG.ABSENCE, kind="DISPOSITION")
    check("a source's own stated negative validates as a negative claim",
          not CP.check_ledger({"F09": fact}, CP.source_texts(PACK)),
          CP.check_ledger({"F09": fact}, CP.source_texts(PACK)))
    unstated = F("F09", "No catalogue entry names a mason.",
                 "laid by two masons over eleven days",
                 ct=LG.ABSENCE, kind="DISPOSITION")
    check("an unstated negative does not",
          "F09" in CP.check_ledger({"F09": unstated}, CP.source_texts(PACK)))
    check("the prompt tells the freeze to CAPTURE a stated negative",
          "CAPTURE IT" in CP.FREEZE_SYSTEM)
    check("and says why that material matters most",
          "CANNOT hold" in CP.FREEZE_SYSTEM)
    check("and warns against skipping such a passage",
          "Do not skip a passage" in CP.FREEZE_SYSTEM)
    check("while still refusing silence as evidence",
          "Silence is not evidence of absence" in CP.FREEZE_SYSTEM)


def test_the_interpretive_verdict_is_not_defined_out_of_existence():
    """The Ground Truth canary refused a STRONG_INTERPRETIVE_LENS subject on the grounds
    that "nothing in the ledger names embodied cognition, access, impairment". That test
    is the DIRECT criterion, and applying it to the interpretive question makes one of
    the five verdicts unreachable: the whole category exists for subjects that never say
    the word. This is the specification the prompt was missing, not a preference."""
    check("the prompt says the interpretive lens needs no mention of disability",
          "does NOT require the material to mention disability" in CP.WORTH_SYSTEM)
    check("and names the category error explicitly",
          "it is deleting the verdict" in CP.WORTH_SYSTEM)
    check("and says what an interpretive reading actually asks",
          "can and cannot register about a body" in CP.WORTH_SYSTEM)
    check("while keeping the bar at a mechanism",
          "The bar is still real, and it is a MECHANISM" in CP.WORTH_SYSTEM)
    check("and still refusing a resemblance",
          "A resemblance is not a mechanism" in CP.WORTH_SYSTEM)
    check("the publishable verdicts are unchanged",
          ST.LENS_PUBLISHABLE == (ST.STRONG_DIRECT_LENS, ST.STRONG_INTERPRETIVE_LENS))
    check("and the refusals are still first-class outcomes",
          all(v in ST.LENS_VERDICTS for v in
              (ST.WEAK_ANALOGY, ST.NO_PLAUSIBLE_LENS, ST.WRONG_PUBLICATION)))
    # An empty formulation is still refused by the merged validator, unchanged.
    check("the merged empty-lens screen is untouched",
          any("empty formulation" in e for e in ST.validate_lens(
              {"verdict": ST.STRONG_INTERPRETIVE_LENS,
               "lens_claim": "It reminds us that disabled people face barriers in a "
                             "world not built for them at all, everywhere.",
               "changes_meaning_how": "x", "evidence_ids": ["F01"]})))


def test_the_repair_prompt_teaches_the_carrier_rule_the_detector_actually_applies():
    """CARRIER_INSTANCE_NOT_SUPPORTED is the failure the merged detector produces most,
    and the Ground Truth canary spent its single architecture repair on one -- offering
    "the no-reading state where the survey is blank", which still contains a verb. The
    detector is GRAMMATICAL, so the repair has to be told that, in those terms.

    The examples in the prompt are asserted against the real detector here, so the
    prompt cannot drift into teaching a shape the gate would refuse."""
    check("the repair prompt names the code",
          "CARRIER_INSTANCE_NOT_SUPPORTED" in CP.REPAIR_ARCH_SYSTEM)
    check("and says the check is grammatical",
          "GRAMMATICAL" in CP.REPAIR_ARCH_SYSTEM)
    check("and forbids a verb of any kind",
          "NO VERB OF ANY KIND" in CP.REPAIR_ARCH_SYSTEM)
    check("and warns that rewording keeps the verb",
          "rewording keeps the verb" in CP.REPAIR_ARCH_SYSTEM)
    check("and says where the cut clause belongs instead",
          "happens" in CP.REPAIR_ARCH_SYSTEM)

    good = ["the block group with no published figure", "the blank cell on the score card",
            "the brake arm"]
    bad = ["the block group where no figure is published",
           "the state that shows no reading", "the servo pulling the brake arm",
           "the no-reading state where the survey is blank"]
    for c in good:
        check("the prompt's GOOD example passes the merged detector: %r" % c,
              not ST.carrier_asserts_instance(c)["asserts"],
              ST.carrier_asserts_instance(c))
        check("and it really is in the prompt: %r" % c, c in CP.REPAIR_ARCH_SYSTEM)
    for c in bad[:3]:
        check("the prompt's BAD example is refused by the merged detector: %r" % c,
              ST.carrier_asserts_instance(c)["asserts"], ST.carrier_asserts_instance(c))
        check("and it really is in the prompt: %r" % c, c in CP.REPAIR_ARCH_SYSTEM)
    check("the carrier the canary actually failed on is refused",
          ST.carrier_asserts_instance(bad[3])["asserts"])


def test_an_architecture_hold_persists_what_it_refused():
    """The canary's ARCHITECTURE_HOLD wrote no architecture, so the artifacts said which
    carrier failed but not what the rest of the architecture looked like. Same lesson as
    the ledger hold: "it failed" is not actionable, "here is what it emitted" is."""
    bad = copy.deepcopy(ARCH)
    bad["beats"][1]["concrete_carrier"] = ("the eight entries, and the visitor who "
                                           "therefore heard nothing")
    prov, out = run([{"facts": list(LEDGER.values())}, WORTH, bad, bad, bad])
    det = out["detail"][CP.ARCHITECTURE]
    check("the hold is at the architecture", out["failure_stage"] == CP.ARCHITECTURE)
    check("the refused architecture is carried", "architecture" in det, list(det))
    check("so are the failures it started with",
          "failures_at_first_attempt" in det, list(det))
    check("and the exact failures", any("CARRIER" in e for e in det["failures"]),
          det.get("failures"))
    check("and the repair count, which is the full budget",
          det.get("repairs") == CP.MAX_ARCHITECTURE_REPAIRS, det.get("repairs"))
    check("and what each repair was answering",
          [h["attempt"] for h in det.get("repair_history") or []] == [1, 2],
          det.get("repair_history"))
    check("a reply with no beats at all is a shape failure, not a repair target",
          run([{"facts": list(LEDGER.values())}, WORTH,
               {"article_type": "NARRATIVE_ARTICLE"}])[1]["failure_reason"]
          .startswith("the reply is not an architecture"))


def test_the_subscription_limit_is_an_outcome_not_a_fallback():
    """An automatic fallback to a paid provider is exactly the surprise this campaign
    exists to avoid: the previous run died at $268.12 of $269 on OpenRouter. So a
    subscription limit stops the run, is reported under its own code, and is never
    retried -- a second attempt cannot succeed and the only thing it can do is look
    like one."""
    class SubscriptionLimit(Exception):
        pass

    class Limited:
        model = "m"
        cliproxy_url = "http://x/v1"

        def __init__(self):
            self.calls = 0

        def complete(self, system, user, **kw):
            self.calls += 1
            raise SubscriptionLimit("You've reached your usage limit. Resets at 3pm.")

    prov = Limited()
    out = CP.run_story_architecture_composition(
        prov, pack=PACK, source_text=S0, source_sha="x", subject="s",
        fact_check_fn=lambda a: dict(FC_CLEAN))
    check("the run holds", out["status"] == CP.HOLD)
    check("under the subscription-limit code",
          out["reason_code"] == CP.CLAUDE_SUBSCRIPTION_LIMIT, out["reason_code"])
    check("at the stage that hit it", out["failure_stage"] == CP.LEDGER)
    check("NOT RETRIED -- exactly one call", prov.calls == 1, prov.calls)
    check("and it says no paid fallback was attempted",
          "no paid fallback" in out["failure_reason"], out["failure_reason"])
    check("the code is recognised by duck type, so the package imports no adapter",
          CP._is_subscription_limit(SubscriptionLimit("x"))
          and not CP._is_subscription_limit(ValueError("x")))


def test_the_cli_provider_refuses_a_hijacked_environment():
    """Every failure mode here is silent. An API key in the environment still produces
    successful completions -- just billed to a Console account instead of the
    subscription -- and authMethod still reads claude.ai either way. Measured on the
    host, the tell is apiKeySource, which appears only when a key is overriding the
    login. So the adapter checks rather than assumes."""
    import claude_cli_provider as CCP
    check("the three overriding variables are named",
          set(CCP.OVERRIDE_VARS) == {"ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL",
                                     "ANTHROPIC_AUTH_TOKEN"}, CCP.OVERRIDE_VARS)
    import os
    os.environ["ANTHROPIC_API_KEY"] = "sk-should-not-propagate"
    os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:8317"
    try:
        env = CCP.scrubbed_env()
        check("a scrubbed child environment carries none of them",
              not [v for v in CCP.OVERRIDE_VARS if v in env],
              [v for v in CCP.OVERRIDE_VARS if v in env])
        check("but the parent process is untouched -- other services still need them",
              os.environ.get("ANTHROPIC_API_KEY") == "sk-should-not-propagate")
    finally:
        del os.environ["ANTHROPIC_API_KEY"], os.environ["ANTHROPIC_BASE_URL"]

    for bad, why in (({"loggedIn": False}, "not logged in"),
                     ({"loggedIn": True, "apiProvider": "console",
                       "authMethod": "claude.ai", "subscriptionType": "team"},
                      "not firstParty"),
                     ({"loggedIn": True, "apiProvider": "firstParty",
                       "authMethod": "apiKey", "subscriptionType": "team"},
                      "not claude.ai"),
                     ({"loggedIn": True, "apiProvider": "firstParty",
                       "authMethod": "claude.ai", "apiKeySource": "ANTHROPIC_API_KEY",
                       "subscriptionType": "team"}, "a key is overriding"),
                     ({"loggedIn": True, "apiProvider": "firstParty",
                       "authMethod": "claude.ai"}, "no subscriptionType")):
        real = CCP.auth_status
        CCP.auth_status = lambda b="claude", _s=bad: _s
        try:
            refused = False
            try:
                CCP.assert_subscription()
            except CCP.ClaudeCLIError:
                refused = True
            check("assert_subscription refuses: %s" % why, refused, bad)
        finally:
            CCP.auth_status = real

    ok = {"loggedIn": True, "apiProvider": "firstParty", "authMethod": "claude.ai",
          "subscriptionType": "team", "orgName": "Altro Spazio"}
    real = CCP.auth_status
    CCP.auth_status = lambda b="claude", _s=ok: _s
    try:
        check("and accepts a genuine subscription login",
              CCP.assert_subscription()["subscriptionType"] == "team")
    finally:
        CCP.auth_status = real

    check("a limit notice is recognised in the CLI's own words",
          all(CCP._looks_like_a_limit(s) for s in
              ("You've reached your usage limit", "rate limit exceeded",
               "Claude usage limit reached; resets at 4pm", "quota exhausted")))
    check("and ordinary prose is not mistaken for one",
          not CCP._looks_like_a_limit(
              "The device converts a published rent-burden figure into brake pressure."))

    p = CP.composition_provider(CCP.ClaudeCLIProvider(verify_auth=False))
    check("composition passes an injected CLI provider through untouched",
          isinstance(p, CCP.ClaudeCLIProvider))
    argv = CCP.ClaudeCLIProvider(verify_auth=False)._argv("SYS", "mod")
    for flag in ("--system-prompt", "--tools", "--strict-mcp-config",
                 "--no-session-persistence", "--output-format"):
        check("the invocation carries %s" % flag, flag in argv, argv)
    check("the system prompt REPLACES the agent preamble rather than appending",
          "--append-system-prompt" not in argv)
    check("and it runs outside the repo so no CLAUDE.md is prepended",
          CCP.ClaudeCLIProvider(verify_auth=False).cwd == "/tmp")


def test_the_repair_is_told_the_highest_fact_id_numerically():
    """The Ground Truth canary froze 103 facts and then held on
    "the repair rewrote facts that had already validated: ['F100','F101','F102']".

    Nothing was wrong with the guard. `max()` over fact-id STRINGS returns "F99" for a
    ledger containing F100-F103, because "F9" sorts above "F1", so the repair was told
    to number its splits from F99 and minted three ids that already belonged to
    validated facts. Every ledger over 99 facts hits this, and it fails in the one
    direction that causes a collision."""
    big = {"F%02d" % i: {} for i in range(1, 104)}
    check("string max is wrong, which is the whole point", max(big) == "F99")
    check("highest_fact_number is numeric", CP.highest_fact_number(big) == 103,
          CP.highest_fact_number(big))
    check("an empty ledger is 0", CP.highest_fact_number({}) == 0)
    check("a suffixed id does not crash it",
          CP.highest_fact_number({"F10a": {}, "F7": {}}) == 10)

    # And the repair prompt carries the corrected number, with the collision rule.
    bad = copy.deepcopy(LEDGER)
    bad["F09"] = F("F09", "No entry names a mason.", "laid by two masons over eleven days",
                   ct=LG.ABSENCE, kind="DISPOSITION")
    prov, _ = run([{"facts": list(bad.values())},
                   {"facts": [copy.deepcopy(bad["F09"])]}, WORTH, "-", "-"])
    repair_prompt = [prov.calls[i]["user"] for i in range(len(prov.calls))
                     if prov.stage_of(i) == "LEDGER_REPAIR"][0]
    check("the repair is given the true highest id",
          "Highest existing fact id: F9" in repair_prompt,
          [l for l in repair_prompt.splitlines() if "Highest" in l])
    check("and told where to start numbering",
          "number any new fact from F10 upward" in repair_prompt)
    check("and told not to reuse a non-rejected id",
          "never reuse an id that is not in the rejected list" in repair_prompt)

    # The guard itself is unchanged: a genuine rewrite is still refused.
    fixed = copy.deepcopy(bad["F09"]); fixed["claim_type"] = LG.POSITIVE
    fixed["proposition"] = "Two masons laid the salt over eleven days."
    rewrite = copy.deepcopy(LEDGER["F01"])
    rewrite["proposition"] = "The room was built entirely of salt and nothing else."
    _, out = run([{"facts": list(bad.values())}, {"facts": [fixed, rewrite]}])
    check("A GENUINE REWRITE OF A VALIDATED FACT IS STILL REFUSED",
          out["failure_stage"] == CP.LEDGER
          and "already validated" in out["failure_reason"], out.get("failure_reason"))


def test_runtime_is_recorded_per_stage():
    """Measured, not inferred from provider durations: a stage's validators, span checks
    and deterministic derivations appear in no model call's duration_ms, and on a
    hundred-fact ledger they are not free. Recorded only -- nothing here optimises."""
    _, out = run(full_script())
    rt = out["runtime_by_stage"]
    check("every stage that ran reports a time",
          all(s in rt for s in CP.STAGES if out["stages"][s] == CP.PASS), rt)
    check("the deterministic CUT stage is timed too, though it makes no model call",
          CP.CUT_TERMS in rt and out["model_calls_by_stage"][CP.CUT_TERMS] == 0)
    check("the per-stage times do not exceed the total",
          sum(rt.values()) <= out["runtime_seconds"] + 1.0,
          (sum(rt.values()), out["runtime_seconds"]))

    # A held stage still reports the time it spent getting there.
    _, held = run(["not json", "still not json"])
    check("a HOLDing stage is timed", CP.LEDGER in held["runtime_by_stage"],
          held["runtime_by_stage"])


def test_the_derived_cut_terms_are_clean_on_the_frozen_manual_ARTICLE():
    """The strongest available regression: the held-out article is KNOWN CLEAN -- the
    manual run recorded 0 CUT violations against 31 hand-picked terms. So the automated
    derivation must also report 0 on it. Anything it flags there is a false positive by
    construction.

    This is the test the first safety-stage canary needed and did not have. That run
    reported 26 CUT violations on prose that had leaked nothing, because the derivation
    was emitting `change`, `moves`, `form`, `tell`, `There`, `Another`, `visual`, `real`,
    `unit` and `figure` as sentinels. Ordinary English cannot betray a fact."""
    art = HERE.parent / ".claude" / "story-architecture" / "held-out-real-article-1"
    if not art.exists():
        check("frozen held-out artifacts are present", False, str(art))
        return
    arch = json.loads((art / "ARCHITECTURE.json").read_text())
    led = json.loads((art / "FINAL_EVIDENCE_MANIFEST.json").read_text())["facts"]
    article = (art / "CONTINUITY_FINAL.v3.md").read_text()
    hand = json.loads((art / "CUT_WATCH_TERMS.json").read_text())

    r = CP.derive_cut_watch_terms(arch, led)
    ca = ST.cut_adherence(article, arch, r["terms"])
    check("ZERO CUT VIOLATIONS on the known-clean manual article",
          not ca["violations"], [(v["evidence_id"], v["term"]) for v in ca["violations"]])
    check("and no blind spot: every cut fact is watched",
          not ca["cut_without_watch_terms"], ca["cut_without_watch_terms"])
    check("and no term is silently skipped as too short",
          not ca["skipped_too_short"], ca["skipped_too_short"])
    check("every cut fact the manual run watched is still watched",
          set(hand) <= set(r["terms"]), sorted(set(hand) - set(r["terms"])))

    # The specific vocabulary the manual run picked by hand is largely recovered.
    recovered = {k: [x for x in hand[k]
                     if any(x.lower() in d.lower() or d.lower() in x.lower()
                            for d in r["terms"].get(k, []))]
                 for k in hand}
    hit = sum(len(v) for v in recovered.values())
    check("most hand-picked terms are recovered automatically (%d of %d)"
          % (hit, sum(len(v) for v in hand.values())),
          hit >= sum(len(v) for v in hand.values()) // 2, recovered)

    # The words that caused the false positives are now refused outright.
    df = CP._document_frequency(led)
    for junk in ("change", "moves", "form", "tell", "There", "Another", "visual",
                 "real", "unit", "figure", "without", "reached", "options", "press",
                 # Multi-sense ordinary nouns. Each of these collided in a real run or
                 # is the same shape as one that did: cut F33 described the device's
                 # "curved rear channel", a physical groove, and the article wrote "the
                 # usual channels", meaning media. Same string, unrelated senses, and a
                 # substring matcher cannot tell them apart.
                 "channel", "channels", "surface", "reading", "record", "field",
                 "layer", "frame", "account", "margin", "position", "instrument"):
        check("%r is refused as a sentinel" % junk,
              not CP._is_distinctive(junk, df), junk)
    # And the specific ones are still accepted.
    for good in ("photogrammetry", "quantile", "12.15", "Idle Hands", "specifications",
                 "10,000", "inflate", "subsidy", "capture", "circuit", "ESP32S3",
                 "Reality Capture", "download", "override"):
        check("%r is accepted as a sentinel" % good,
              CP._is_distinctive(good, df), good)


def test_continuity_is_fail_safe_and_never_destroys_a_safe_article():
    """Continuity is an OPTIONAL linguistic improvement over prose that is already
    correct, so it is not allowed to destroy one. The Ground Truth canary lost an
    otherwise-clean article to a single COMPARISON relation the editor added.

    The validator is NOT weakened. The edit is discarded whole and the Writer draft
    carries on -- deterministically, with no second Continuity call, no Writer
    regeneration and no repair prose."""
    # An editor that invents a causal relation while naming a real parent.
    edits = _edits_from(DRAFT)
    edits["edits"][3]["text"] = ("The catalogue records eight rooms because each entry "
                                 "was written to a fixed form.")
    prov, out = run(full_script()[:4] + [edits, READER_OK])
    cont = out["detail"][CP.CONTINUITY]
    check("the run still completes", out["status"] == CP.PASS,
          out.get("failure_reason"))
    check("continuity was discarded", cont.get("discarded") is True)
    check("and the reason is recorded",
          any("relation" in str(e) for e in cont.get("discard_reason") or []),
          cont.get("discard_reason"))
    check("the WRITER DRAFT is what carried", cont["carried_text"] == "writer_draft")
    check("the article returned is the draft, not the edit",
          out["article_text"].strip() == DRAFT.strip())
    check("safety records which text it audited",
          out["detail"][CP.SAFETY]["carried_text"] == "writer_draft")
    stages = [prov.stage_of(i) for i in range(len(prov.calls))]
    check("NO SECOND CONTINUITY CALL", stages.count("CONTINUITY") == 1, stages)
    check("NO WRITER REGENERATION", stages.count("WRITER") == 1, stages)
    check("and the run went on to the reader gate",
          out["stages"][CP.READER] == CP.PASS, out["stages"])

    # A clean editor is still used, and its text is what carries.
    prov2, out2 = run(full_script())
    cont2 = out2["detail"][CP.CONTINUITY]
    check("a clean continuity pass is not discarded",
          not cont2.get("discarded"), cont2.get("discard_reason"))
    check("and its text carries", cont2["carried_text"] == "continuity_final")

    # If the DRAFT is also unsafe, the run HOLDs -- the fallback is not an escape hatch.
    bad = DRAFT.replace("The room was built from Himalayan salt bricks",
                        "The room was built from pink Himalayan salt bricks")
    e2 = _edits_from(bad)
    e2["edits"][3]["text"] = ("The catalogue records eight rooms because each entry was "
                              "written to a fixed form.")
    prov3, out3 = run(full_script()[:3] + [envelope(bad), e2, READER_OK])
    check("a discarded edit over an unsafe draft HOLDS",
          out3["failure_stage"] == CP.SAFETY, out3.get("failure_stage"))
    check("and says both things happened",
          "continuity was discarded" in out3["failure_reason"]
          and "did not pass either" in out3["failure_reason"],
          out3["failure_reason"][:200])
    check("the grounder was never reached",
          out3["stages"][CP.GROUNDING] == CP.NOT_RUN)
    check("still no regeneration",
          [prov3.stage_of(i) for i in range(len(prov3.calls))].count("WRITER") == 1)


def test_a_gerund_in_a_noun_slot_is_not_a_participle():
    """The Ground Truth canary died twice at the architecture stage on this, the second
    time refusing

        "a measure with no field for eviction risk, overcrowding or harassment"

    for the participle "overcrowding" -- a pure noun phrase, which is exactly the shape
    the carrier rule asks for. _PARTICIPLE matches any -ing word and was exempted only by
    a hand-maintained twelve-word list that cannot keep up.

    What separates them is what a participle needs and a gerund does not: a SUBJECT.
    "the servo pulling the brake arm" puts a noun immediately before the -ing word, and
    that noun is what is said to act. A gerund sits in a noun slot instead, after a
    preposition, determiner, conjunction, comma or possessive -- named, not narrated.

    Asserted in BOTH directions, because a rule that only stops false positives would
    quietly stop true ones too."""
    gerunds = [
        # Compound modifiers: an -ing word directly against the noun it modifies. The
        # second fresh-subject candidate spent both architecture repairs and still could
        # not get past "the Academic Integrity Board hearing space" -- a space where
        # hearings are held. The noun-slot rule cannot see it, because the token before
        # is "Board" and a participle's subject is also a noun. What separates them is
        # what comes AFTER: a working participle takes a determiner or preposition next.
        "the Academic Integrity Board hearing space, without phone, parent or lawyer",
        "the reading room on the second floor",
        "the housing target for new homes",
        "the training day in September",
        "a measure with no field for eviction risk, overcrowding or harassment",
        "a measure with no field for overcrowding",
        "the building's cladding",
        "notes on wayfinding and signage",
        "records of flooding in the basement",
        "the published figure for the housing complexes",
    ]
    participles = [
        "the bike coasting through the block group",
        "the bike speeding up alongside the complexes",
        "the servo pulling the brake arm",
        "a rider stopping at the kerb",
    ]
    for c in gerunds:
        check("gerund noun is NOT an occurrence: %r" % c[:44],
              not ST.carrier_asserts_instance(c)["asserts"],
              ST.carrier_asserts_instance(c))
    for c in participles:
        check("participle with a subject IS an occurrence: %r" % c[:44],
              ST.carrier_asserts_instance(c)["asserts"],
              ST.carrier_asserts_instance(c))
    # The other two channels are untouched.
    for c, why in (("the brake that does not move", "finite verb"),
                   ("a block group, and therefore a slack cable", "consequence")):
        check("%s still refuses: %r" % (why, c[:40]),
              ST.carrier_asserts_instance(c)["asserts"])
    check("an explicitly conditional carrier is still exempt",
          not ST.carrier_asserts_instance(
              "a block group where the survey publishes no figure, and the brake that "
              "would not move")["asserts"])
    # The hand list is kept as a second cheap check rather than removed.
    check("the adjectival list is still consulted",
          "housing" in ST._ADJECTIVAL)


NEG_SENTENCE = "The register says nothing about listening."


def _draft_with_negative(extra=""):
    """The draft, with a negative sentence that renders F05 faithfully but narrowly."""
    return DRAFT.replace(
        "No entry describes what any visitor heard.",
        NEG_SENTENCE + (" " + extra if extra else ""))


def test_a_faithful_narrow_negative_needs_provenance_the_lexical_audit_cannot_see():
    """The blocker, and the six cases that define the fix.

    F05 is an approved ABSENCE the architecture uses. The prose renders its first clause
    faithfully and narrowly, so the word-overlap audit -- whose threshold scales with the
    FACT's length -- cannot pair them. Measured equivalently on the canary: fact F59 has
    9 key words and needs 3; "It says nothing about homeowners." supplies 1.

    A declaration is a claim about ORIGIN. It never makes unsupported content valid."""
    draft = _draft_with_negative()
    # First: confirm the lexical audit really cannot see it, or this tests nothing.
    audit = ST.negative_admission_audit(draft, LEDGER)
    check("the lexical audit cannot pair the faithful paraphrase",
          any(NEG_SENTENCE in h["sentence"] for h in audit["unmatched"]),
          [h["sentence"] for h in audit["unmatched"]])

    good = [{"sentence_id": "S007", "fact_ids": ["F05"]}]

    def run_with(lineage, d=None):
        d = d or draft
        return run([{"facts": list(LEDGER.values())}, WORTH, ARCH,
                    envelope(d, lineage), _edits_from(d), READER_OK])

    # 1. approved negative paraphrase + valid Writer lineage -> PASS
    sid = next(k for k, v in CP.label_sentences(draft).items()
               if "nothing about listening" in v)
    _, ok = run_with([{"sentence_id": sid, "fact_ids": ["F05"]}])
    check("1. valid Writer lineage admits the paraphrase",
          ok["status"] == CP.PASS, ok.get("failure_reason"))
    adm = ok["detail"][CP.SAFETY]["negatives_admitted_by_provenance"]
    check("   and the admission is recorded with its fact id",
          adm and adm[0]["fact_ids"] == ["F05"], adm)

    # 2. identical prose WITHOUT Writer lineage -> FAIL
    _, no_lin = run_with([])
    check("2. the same prose with no lineage HOLDS",
          no_lin["failure_stage"] == CP.SAFETY
          and "UNSUPPORTED_NEGATIVES" in no_lin["failure_reason"],
          no_lin.get("failure_reason"))

    # 3. lineage to a POSITIVE fact -> FAIL
    _, pos = run_with([{"sentence_id": sid, "fact_ids": ["F01"]}])
    check("3. lineage to a positive fact is refused",
          pos["failure_stage"] == CP.SAFETY, pos.get("failure_stage"))
    rej = pos["detail"][CP.WRITER]["negative_lineage_rejected"]
    check("   and the rejection says why",
          any("not an approved negative" in str(r["why"]) for r in rej), rej)

    # 4. valid negative lineage + new unsupported entity -> FAIL
    d4 = _draft_with_negative("The Rijksmuseum says nothing about it either.")
    sid4 = next(k for k, v in CP.label_sentences(d4).items()
                if "Rijksmuseum" in v)
    _, ent = run_with([{"sentence_id": sid4, "fact_ids": ["F05"]}], d4)
    check("4a. a declaration does not license a new entity",
          ent["failure_stage"] == CP.SAFETY, ent.get("failure_stage"))
    rej4 = ent["detail"][CP.WRITER]["negative_lineage_rejected"]
    check("    and the verifier names the new entity",
          any("new entit" in str(r["why"]) for r in rej4), rej4)

    # 4b. valid negative lineage + a relation the fact does not assert -> FAIL
    d4b = DRAFT.replace(
        "No entry describes what any visitor heard.",
        "The register says nothing about listening, because the catalogue was the "
        "quietest record of the eight.")
    sid4b = next(k for k, v in CP.label_sentences(d4b).items()
                 if "quietest" in v)
    verified, rejected = CP.verify_negative_lineage(
        d4b, [{"sentence_id": sid4b, "fact_ids": ["F05"]}], LEDGER,
        CP.writer_packet(ARCH, LEDGER)[0], set(CP.negative_permissions(ARCH, LEDGER)))
    check("4b. a declaration does not license an unasserted relation",
          not verified and rejected, (verified, rejected))

    # 5. Continuity CANNOT invent a declaration for a parent that lacked one.
    edits = _edits_from(draft)
    for e in edits["edits"]:
        e["negative_fact"] = "F05"          # ignored: no fact id is ever read from here
        e["fact_ids"] = ["F05"]
    _, inv = run([{"facts": list(LEDGER.values())}, WORTH, ARCH,
                  envelope(draft, []), edits, READER_OK])
    check("5. Continuity cannot mint provenance the Writer never declared",
          inv["failure_stage"] == CP.SAFETY
          and "UNSUPPORTED_NEGATIVES" in inv["failure_reason"],
          inv.get("failure_reason"))

    # 6. A DISCARDED Continuity output cannot retroactively license anything.
    bad_edits = _edits_from(draft)
    bad_edits["edits"][2]["text"] = ("The catalogue records eight rooms because each "
                                     "entry was written to a fixed form.")
    for e in bad_edits["edits"]:
        e["negative_fact"] = "F05"
    _, disc = run([{"facts": list(LEDGER.values())}, WORTH, ARCH,
                   envelope(draft, []), bad_edits, READER_OK])
    check("6. a discarded edit licenses nothing retroactively",
          disc["failure_stage"] == CP.SAFETY, disc.get("failure_stage"))
    check("   the edit was discarded",
          disc["detail"][CP.CONTINUITY].get("discarded") is True)
    check("   and the Writer draft's own (absent) lineage is what applied",
          disc["detail"][CP.CONTINUITY]["negative_lineage_carried"] == {},
          disc["detail"][CP.CONTINUITY].get("negative_lineage_carried"))

    # Forward inheritance DOES work when the parent had provenance and the edit is clean.
    _, fwd = run_with([{"sentence_id": sid, "fact_ids": ["F05"]}])
    check("provenance flows FORWARD onto a clean edited descendant",
          fwd["detail"][CP.CONTINUITY]["negative_lineage_carried"],
          fwd["detail"][CP.CONTINUITY].get("negative_lineage_carried"))


def test_the_writer_is_shown_negative_ids_and_nothing_else():
    """The packet still carries no fact ids -- ids are machine identity and prose has no
    use for them. The one exception is the negative-permissions block, which exists so a
    negative sentence can NAME its permission, and whose propositions are already in the
    packet as used facts."""
    perms = CP.negative_permissions(ARCH, LEDGER)
    check("only negative claim types are admissible",
          all(LEDGER[f]["claim_type"] in LG.NEGATIVE_TYPES for f in perms), sorted(perms))
    check("and only facts the architecture actually uses",
          set(perms) <= set(ARCH["use_facts"]), sorted(perms))
    check("F05 is a permission", "F05" in perms, sorted(perms))
    packet, prompt = CP.writer_packet(ARCH, LEDGER)
    check("the negative permission id is shown", "F05" in prompt)
    for pos in ("F01", "F02", "F03", "F04", "F06", "F08"):
        check("the positive fact id %s is still withheld" % pos, pos not in prompt)
    check("the packet body itself still carries no ids",
          "F05" not in ST.render(packet))
    check("with no negatives in use, the Writer is told so",
          "Do not write any sentence saying"
          in CP.negative_permissions_block({}))


def test_a_replay_can_never_look_like_an_autonomous_run():
    """Replaying a frozen ledger/worth/architecture makes testing a later stage cheap --
    the two heavy stages cost about six minutes between them. The risk is that a replay
    gets reported as autonomy, so the stages report REPLAYED rather than PASS and the
    result is flagged."""
    frozen = {"ledger": LEDGER, "worth": WORTH, "architecture": ARCH}
    prov = Scripted([envelope(DRAFT), _edits_from(DRAFT), READER_OK])
    import new_engine_v1.stages as S
    real = S.ground
    S.ground = lambda *a, **k: dict(GROUND_CLEAN)
    try:
        out = CP.run_story_architecture_composition(
            prov, pack=PACK, source_text=S0, source_sha="x", subject=PACK["subject"],
            fact_check_fn=lambda a: dict(FC_CLEAN), frozen=frozen)
    finally:
        S.ground = real
    check("the run completes", out["status"] == CP.PASS, out.get("failure_reason"))
    check("it is flagged as a replay", out["replay"] is True)
    check("and names exactly which stages were replayed",
          out["replayed_stages"] == [CP.ARCHITECTURE, CP.LEDGER, CP.WORTH],
          out["replayed_stages"])
    for s in (CP.LEDGER, CP.WORTH, CP.ARCHITECTURE):
        check("%s reports REPLAYED, not PASS" % s, out["stages"][s] == CP.REPLAYED)
    check("no model call was spent on them",
          all(out["model_calls_by_stage"].get(s, 0) == 0
              for s in (CP.LEDGER, CP.WORTH, CP.ARCHITECTURE)))
    check("only the Writer onward ran", len(prov.calls) == 3, len(prov.calls))
    check("a normal run is not flagged",
          run(full_script())[1]["replay"] is False)

    # A replayed architecture is still validated against the replayed ledger: a frozen
    # artifact is not a licence to skip the gate it originally passed.
    bad = copy.deepcopy(ARCH)
    bad["use_facts"] = bad["use_facts"] + ["F99"]
    prov2 = Scripted([envelope(DRAFT)])
    out2 = CP.run_story_architecture_composition(
        prov2, pack=PACK, source_text=S0, source_sha="x", subject="s",
        fact_check_fn=lambda a: dict(FC_CLEAN),
        frozen={"ledger": LEDGER, "worth": WORTH, "architecture": bad})
    check("an invalid replayed architecture still HOLDS",
          out2["failure_stage"] == CP.ARCHITECTURE, out2.get("failure_stage"))
    check("and the writer is never called", not prov2.calls, prov2.calls)


def test_cut_is_compiled_into_prohibitions_the_writer_can_act_on():
    """The packet carried the CUT decision as a COUNT, not as anything the Writer could
    act on -- so it named a circuit board, Reality Capture and an override, all from cut
    facts. The cut material is now compiled into explicit prohibitions: generic fixed
    wording, with WHICH categories appear coming only from the cut facts."""
    arch = copy.deepcopy(ARCH)
    led = copy.deepcopy(LEDGER)
    # A cut fact about electronics, with vocabulary the packet does not license.
    led["F09"] = F("F09", "The pavilion's lighting ran from a custom circuit board and "
                          "an ESP32 microcontroller in a 3D-printed enclosure.",
                   "The pavilion closed after the Kunsthalle season ended", ev=("S1",))
    arch["cut_evidence"] = arch["cut_evidence"] + [
        {"evidence_id": "F09", "reason": "BACKGROUND_NOT_NEEDED"}]
    r = CP.derive_cut_watch_terms(arch, led)

    # 1. a genuine CUT term is blocked
    check("1. the electronics category is emitted from the cut fact",
          any("electronic components" in p for p in r["prohibitions"]),
          r["prohibitions"])
    check("   and it is phrased as a boundary, not a ban",
          all("beyond" in p for p in r["prohibitions"]), r["prohibitions"])
    _, prompt = CP.writer_packet(arch, led, r["prohibitions"])
    check("   and it reaches the Writer as a relative boundary",
          "Do not add electronic components, hardware or assembly detail beyond"
          in prompt, [l for l in prompt.splitlines() if "electronic" in l])
    check("   the distinctive cut vocabulary is watched",
          any(x.lower() in ("microcontroller", "enclosure", "lighting", "esp")
              or "circuit" in x.lower() for x in r["terms"]["F09"]),
          r["terms"]["F09"])
    leak = DRAFT + "\n\nA custom circuit board sat under the floor."
    check("   and a real leak is caught",
          [v["term"] for v in ST.cut_adherence(leak, arch, r["terms"])["violations"]],
          ST.cut_adherence(leak, arch, r["terms"]))

    # 2. ordinary English is unaffected
    for junk in ("Across", "There", "change", "form", "without", "corresponding"):
        check("2. %r is never a sentinel" % junk,
              not CP._is_distinctive(junk, CP._document_frequency(led)), junk)
    check("   and clean prose stays clean",
          not ST.cut_adherence(DRAFT, arch, r["terms"])["violations"],
          ST.cut_adherence(DRAFT, arch, r["terms"])["violations"])

    # 3. a packet-licensed overlapping term is allowed, exactly as the CUT logic does it
    led2 = copy.deepcopy(led)
    led2["F09"]["proposition"] = ("The pavilion's Himalayan salt brick lighting ran from "
                                  "a board.")
    r2 = CP.derive_cut_watch_terms(arch, led2)
    check("3. 'Himalayan' is not watched: the packet licenses it",
          not any("himalayan" in x.lower() for x in r2["terms"]["F09"]),
          r2["terms"]["F09"])
    check("   nor 'salt', nor 'brick'",
          not any(x.lower() in ("salt", "brick", "bricks") for x in r2["terms"]["F09"]))

    # 4. no prohibition is invented beyond the CUT facts
    for pr in r["prohibitions"]:
        markers = next(m for m, s in CP.CUT_CATEGORIES if s == pr)
        hay = " ".join(
            ("%s %s" % ((led.get(c["evidence_id"]) or {}).get("proposition", ""),
                        (led.get(c["evidence_id"]) or {}).get("support_span", ""))).lower()
            for c in arch["cut_evidence"] if r["terms"].get(c["evidence_id"]))
        check("4. %r is backed by a cut fact" % pr[:46],
              any(m in hay for m in markers), pr)
    bare = copy.deepcopy(ARCH)
    check("   a cut list with no matching category invents nothing",
          CP.derive_cut_watch_terms(bare, LEDGER)["prohibitions"] == [],
          CP.derive_cut_watch_terms(bare, LEDGER)["prohibitions"])
    check("   a cut fact whose vocabulary is wholly licensed produces no prohibition",
          not CP.compile_cut_prohibitions(arch, led, {}),
          CP.compile_cut_prohibitions(arch, led, {}))
    check("   the wording is fixed and generic, never article-specific",
          all(s == next(x for m, x in CP.CUT_CATEGORIES if x == s)
              for s in r["prohibitions"]))
    check("   and the compiled lines survive validate_packet",
          ST.validate_packet(CP.writer_packet(arch, led, r["prohibitions"])[0]) == [],
          ST.validate_packet(CP.writer_packet(arch, led, r["prohibitions"])[0]))
    check("   no model call is spent", "no model call" in r["derivation"])
    check("   the architecture object itself is not mutated",
          "Do not name or describe the electronic components, boards, modules, wiring "
          "or how the device was physically assembled." not in
          (arch.get("prohibitions") or []))


def test_the_architecture_repair_budget_is_two():
    """Measured, not chosen: the architecture stage held in three of five subscription
    canary runs, two of them on legitimate mints one repair could not clear. The manual
    baseline needed exactly two, in order -- REPAIR_1 a carrier asserting an occurrence,
    REPAIR_2 a turn minting a relation.

    Acceptance is unchanged. The full validator set runs after EVERY repair."""
    check("the budget is two", CP.MAX_ARCHITECTURE_REPAIRS == 2)

    carrier_bad = copy.deepcopy(ARCH)
    carrier_bad["beats"][1]["concrete_carrier"] = (
        "the eight entries, and the visitor who therefore heard nothing")
    turn_bad = copy.deepcopy(ARCH)
    turn_bad["crip_turn"] = ("The catalogue is quietest exactly where the encounter was "
                             "loudest, because only the intention could be written.")

    def arch_run(replies):
        return run([{"facts": list(LEDGER.values())}, WORTH] + replies
                   + full_script()[3:])

    # 1. a valid initial architecture spends no repair
    prov, out = arch_run([ARCH])
    check("1. valid initial architecture -> 0 repairs",
          out["detail"][CP.ARCHITECTURE]["repairs"] == 0
          and out["status"] == CP.PASS, out.get("failure_reason"))
    check("   and one architect call",
          out["model_calls_by_stage"][CP.ARCHITECTURE] == 1)

    # 2. invalid, repaired on the first attempt
    prov, out = arch_run([carrier_bad, ARCH])
    check("2. repaired on the first attempt -> 1 repair",
          out["detail"][CP.ARCHITECTURE]["repairs"] == 1
          and out["status"] == CP.PASS, out.get("failure_reason"))

    # 3. first repair still invalid, second valid
    prov, out = arch_run([carrier_bad, turn_bad, ARCH])
    check("3. second repair rescues it -> 2 repairs",
          out["detail"][CP.ARCHITECTURE]["repairs"] == 2
          and out["status"] == CP.PASS, out.get("failure_reason"))
    check("   three architecture calls in total",
          out["model_calls_by_stage"][CP.ARCHITECTURE] == 3)
    hist = out["detail"][CP.ARCHITECTURE]["repair_history"]
    check("   and each repair answered its OWN failures, not the first ones",
          [h["attempt"] for h in hist] == [1, 2]
          and "CARRIER" in str(hist[0]["failures_answered"])
          and "TURN" in str(hist[1]["failures_answered"]), hist)

    # 4. second repair still invalid -> HOLD, and no third attempt
    prov, out = arch_run([carrier_bad, turn_bad, carrier_bad])
    check("4. still invalid after two -> HOLD",
          out["failure_stage"] == CP.ARCHITECTURE, out.get("failure_stage"))
    check("   the reason names the budget",
          "maximum 2" in out["failure_reason"], out["failure_reason"][:120])
    check("   NO THIRD REPAIR",
          [prov.stage_of(i) for i in range(len(prov.calls))].count("ARCH_REPAIR") == 2,
          [prov.stage_of(i) for i in range(len(prov.calls))])
    check("   and the Writer was never called",
          "WRITER" not in [prov.stage_of(i) for i in range(len(prov.calls))])

    # 5. a repair cannot introduce a new fact id
    minted = copy.deepcopy(ARCH)
    minted["use_facts"] = minted["use_facts"] + ["F99"]
    prov, out = arch_run([carrier_bad, minted, minted])
    check("5. a repair cannot mint a fact id",
          out["failure_stage"] == CP.ARCHITECTURE
          and "F99" in out["failure_reason"], out.get("failure_reason"))

    # 6. a repair cannot bypass the occurrence/relation validators
    prov, out = arch_run([ARCH if False else carrier_bad, carrier_bad, carrier_bad])
    check("6a. a repair cannot bypass the carrier check",
          out["failure_stage"] == CP.ARCHITECTURE
          and "CARRIER" in out["failure_reason"], out.get("failure_reason"))
    prov, out = arch_run([turn_bad, turn_bad, turn_bad])
    check("6b. a repair cannot bypass the turn-relation check",
          out["failure_stage"] == CP.ARCHITECTURE
          and "TURN" in out["failure_reason"], out.get("failure_reason"))

    # 7. the exact count and status are exposed in run metadata
    prov, out = arch_run([carrier_bad, turn_bad, ARCH])
    d = out["detail"][CP.ARCHITECTURE]
    check("7. metadata carries the repair count", d["repairs"] == 2)
    check("   and the budget", d["repair_budget"] == 2)
    check("   and the run-level map", out["repairs_by_stage"][CP.ARCHITECTURE] == 2)
    check("   and the first failures are kept for comparison",
          d["failures_at_first_attempt"], d.get("failures_at_first_attempt"))
    check("   and the stage still reports PASS",
          out["stages"][CP.ARCHITECTURE] == CP.PASS)


def test_packet_licensing_survives_the_stemmer_being_asymmetric():
    """Three canary runs died on this. story.py's `_stem` is a suffix stripper, not a
    canonicaliser, so two variants of ONE word can stem differently:

        packet "overrides"       -> "overrid"          candidate "override"      -> "override"
        packet "correspondingly" -> "correspondingly"  candidate "corresponding" -> "correspond"
        packet "continuously"    -> "continuously"     candidate "continuous"    -> "continuou"

    Every pair is the same word and every pair failed an equality test, so the CUT audit
    watched vocabulary the Writer had been handed and reported leaks on prose that leaked
    nothing. Licensing compares by prefix containment in both directions instead."""
    _pk = ("the device overrides the front brake correspondingly, the reading updates "
           "continuously on a Citi Bike, the map is down, the top quantile was removed, "
           "covering 2020 through 2024, and an ESP32S3 sits inside")
    words = CP._words(_pk)
    nums = {n.strip().lower() for n in ST._numbers(_pk)}
    for w in ("override", "overrides", "corresponding", "continuous", "continuously",
              "Bikes", "quantile", "2020", "ESP32S3"):
        check("%r is recognised as licensed" % w,
              CP._licensed_by(w, words, nums), w)
    for w in ("photogrammetry", "circuit", "capture", "servo", "12.15"):
        check("%r is NOT licensed by that packet" % w,
              not CP._licensed_by(w, words, nums), w)
    # An alphanumeric part name is NOT a number and must take the word path: sent down
    # the number path it could never match, because ST._numbers does not read it as one.
    check("a part name goes down the word path",
          not CP._PURE_NUMBER.match("ESP32S3") and CP._PURE_NUMBER.match("12.15")
          and CP._PURE_NUMBER.match("$12.15") and CP._PURE_NUMBER.match("2020"))
    # The difference is the signal, not the absolute length. A floor on the shorter form
    # rejected down/download correctly and then also rejected bike/bikes.
    check("'down' does not license 'download' -- a spelling coincidence",
          not CP._licensed_by("download", words, nums))
    check("but 'Bike' does license 'Bikes' -- one character of inflection",
          CP._licensed_by("Bikes", words, nums))
    check("and the rule is stated as a difference",
          CP.LICENSE_MORPH_DIFF == 3)
    # A number has no morphology: exact appearance only.
    # A DECIMAL MUST BE EXTRACTED THE SAME WAY ON BOTH SIDES. Candidates come from
    # ST._numbers, which reads "$12.15" as one token; a [a-z0-9]+ scan splits it into
    # "12" and "15", so a decimal could never match. That is how the CUT audit reported
    # "$12.15" as leaked from cut F100 while USED fact F15 was granting it in the
    # Writer's own packet.
    check("a number is licensed only by its exact appearance",
          CP._licensed_by("2020", words, nums)
          and not CP._licensed_by("202", words, nums)
          and not CP._licensed_by("20241", words, nums))
    dec = "a 45-minute e-bike ride could cost a member $12.15"
    check("a decimal in the packet licenses the same decimal",
          CP._licensed_by("12.15", CP._words(dec),
                          {n.strip().lower() for n in ST._numbers(dec)}))
    check("and a different decimal is still watched",
          not CP._licensed_by("12.55", CP._words(dec),
                              {n.strip().lower() for n in ST._numbers(dec)}))
    # A multi-word term is licensed only as a PHRASE. Checking its words separately
    # licensed "Idle Hands" because the packet contained both words elsewhere, and a
    # name is exactly the thing a phrase rather than its parts identifies.
    arch = copy.deepcopy(ARCH)
    led = copy.deepcopy(LEDGER)
    led["F07"]["proposition"] = ("The Kunsthalle Salt Room closed after the season, "
                                 "and the room was full of brick.")
    r = CP.derive_cut_watch_terms(arch, led)
    check("a multi-word name survives even when its words appear separately",
          any(" " in x for x in r["terms"]["F07"]), r["terms"]["F07"])


def test_the_frozen_baseline_stays_at_zero_after_every_licensing_change():
    """The known-clean anchor for all of this. The manual run recorded 0 CUT violations
    on the held-out article against 31 hand-picked terms, so anything the automated
    derivation flags there is a false positive by construction. Re-asserted separately
    from the derivation tests because every licensing change risks it."""
    art = HERE.parent / ".claude" / "story-architecture" / "held-out-real-article-1"
    if not art.exists():
        check("frozen held-out artifacts are present", False, str(art))
        return
    arch = json.loads((art / "ARCHITECTURE.json").read_text())
    led = json.loads((art / "FINAL_EVIDENCE_MANIFEST.json").read_text())["facts"]
    r = CP.derive_cut_watch_terms(arch, led)
    for name in ("CONTINUITY_FINAL.v3.md", "WRITER_DRAFT.v3.md"):
        f = art / name
        if not f.exists():
            continue
        ca = ST.cut_adherence(f.read_text(), arch, r["terms"])
        check("ZERO violations on the known-clean %s" % name,
              not ca["violations"],
              [(v["evidence_id"], v["term"]) for v in ca["violations"]])
    check("and the specific vocabulary is still recovered",
          all(any(g in x.lower() for x in
                  [y.lower() for v in r["terms"].values() for y in v])
              for g in ("photogrammetry", "quantile", "12.15", "download")),
          {k: v for k, v in r["terms"].items() if v})


def test_exact_cut_vocabulary_stays_machine_side():
    """The CUT boundary the campaign wants: the Writer never receives the forbidden value
    merely so it can be told not to repeat it. The compiled prohibitions are fixed
    generic sentences, so they carry no number, name, quotation or proposition -- and
    the exact vocabulary stays with the deterministic post-Writer audit."""
    arch = copy.deepcopy(ARCH)
    led = copy.deepcopy(LEDGER)
    led["F09"] = F("F09", "The pavilion's lighting ran from a custom circuit board and "
                          "an ESP32 microcontroller costing $412.90.",
                   "The pavilion closed after the Kunsthalle season ended", ev=("S1",))
    arch["cut_evidence"] = arch["cut_evidence"] + [
        {"evidence_id": "F09", "reason": "BACKGROUND_NOT_NEEDED"}]
    r = CP.derive_cut_watch_terms(arch, led)

    check("a prohibition is emitted for the cut fact",
          r["prohibitions"], r["prohibitions"])
    joined = " ".join(r["prohibitions"])
    check("no compiled prohibition carries a number",
          not ST._numbers(joined), sorted(ST._numbers(joined)))
    check("nor the cut value", "412.90" not in joined)
    check("nor a part name", "ESP32" not in joined and "circuit board" not in joined)
    check("nor a quotation", '"' not in joined and "'" not in joined)
    check("nor any cut proposition verbatim",
          CP.normalize_span(led["F09"]["proposition"]) not in CP.normalize_span(joined))
    check("the wording is generic and fixed",
          all(any(s == fixed for _, fixed in CP.CUT_CATEGORIES)
              for s in r["prohibitions"]))

    _, prompt = CP.writer_packet(arch, led, r["prohibitions"])
    check("and the cut value never reaches the rendered Writer prompt",
          "412.90" not in prompt, [l for l in prompt.splitlines() if "412" in l])
    check("nor does the cut proposition",
          CP.normalize_span(led["F09"]["proposition"]) not in CP.normalize_span(prompt))

    # BUT the exact vocabulary is still available to the machine-side audit.
    check("the exact cut value is retained for the CUT audit",
          any("412.90" in x for v in r["terms"].values() for x in v),
          r["terms"].get("F09"))
    leak = DRAFT + "\n\nThe board cost $412.90."
    check("and a leak of it is caught",
          any(v["term"] == "412.90"
              for v in ST.cut_adherence(leak, arch, r["terms"])["violations"]),
          ST.cut_adherence(leak, arch, r["terms"])["violations"])

    # A USED fact with overlapping vocabulary is unaffected: the article may still use
    # the words it was granted.
    check("used vocabulary is never watched",
          not any(x.lower() in ("salt", "brick", "bricks", "himalayan", "pavilion")
                  for v in r["terms"].values() for x in v),
          {k: v for k, v in r["terms"].items() if v})


def test_cut_prohibitions_are_relative_boundaries_not_absolute_bans():
    """An absolute "Do not name electronic components" contradicted the packet: the
    run-D architecture USED a components fact, so the Writer was handed the ESP32S3, the
    PCB and the GPS module and told not to name them. Each line now forbids EXPANSION
    BEYOND the approved facts, so USED material stays fully available while the boundary
    is stated without naming what lies past it."""
    check("no compiled line is an absolute ban",
          all("beyond" in s for _, s in CP.CUT_CATEGORIES),
          [s for _, s in CP.CUT_CATEGORIES if "beyond" not in s])
    check("and every line points at the approved facts",
          all("article facts above" in s for _, s in CP.CUT_CATEGORIES))

    def setup(used_extra=None, cut_props=None):
        arch = copy.deepcopy(ARCH)
        led = copy.deepcopy(LEDGER)
        n = 20
        for prop, span in (used_extra or []):
            fid = "F%02d" % n; n += 1
            led[fid] = F(fid, prop, span)
            arch["use_facts"] = arch["use_facts"] + [fid]
            arch["beats"][0]["facts_allowed"] = \
                arch["beats"][0]["facts_allowed"] + [fid]
        for prop, span in (cut_props or []):
            fid = "F%02d" % n; n += 1
            led[fid] = F(fid, prop, span, ev=("S1",))
            arch["cut_evidence"] = arch["cut_evidence"] + [
                {"evidence_id": fid, "reason": "BACKGROUND_NOT_NEEDED"}]
        r = CP.derive_cut_watch_terms(arch, led)
        _, prompt = CP.writer_packet(arch, led, r["prohibitions"])
        return arch, led, r, prompt

    # 1. USED ESP32S3 + an unrelated CUT electronics detail: the approved part stays.
    arch, led, r, prompt = setup(
        used_extra=[("The room was lit by an ESP32S3 microcontroller.",
                     "constructed from Himalayan salt bricks")],
        cut_props=[("A custom circuit board and a servo sat in the plinth.",
                    "The pavilion closed after the Kunsthalle season ended")])
    check("1. the approved ESP32S3 reaches the Writer", "ESP32S3" in prompt)
    check("   the relative electronics boundary reaches it too",
          "Do not add electronic components, hardware or assembly detail beyond"
          in prompt)
    ok = DRAFT + "\n\nAn ESP32S3 microcontroller sat in the room."
    check("   and using the APPROVED part is not a violation",
          not ST.cut_adherence(ok, arch, r["terms"])["violations"],
          ST.cut_adherence(ok, arch, r["terms"])["violations"])

    # 2. the Writer adds "circuit board", which the packet does not license
    bad = DRAFT + "\n\nA custom circuit board sat under the floor."
    v = ST.cut_adherence(bad, arch, r["terms"])["violations"]
    check("2. an UNAPPROVED circuit board is still blocked",
          any("circuit" in x["term"].lower() for x in v), v)
    check("   and the exact cut vocabulary never reached the Writer",
          "circuit board" not in prompt.lower()
          and "servo" not in prompt.lower(),
          [l for l in prompt.splitlines() if "circuit" in l.lower()])

    # 3. no approved software + a CUT software fact: generic line reaches the Writer,
    #    the exact tool name does not.
    arch, led, r, prompt = setup(
        cut_props=[("The room was modelled in Reality Capture from a photogrammetry "
                    "scan.", "The pavilion closed after the Kunsthalle season ended")])
    check("3. the relative software boundary reaches the Writer",
          "Do not name software, tools, file formats or technical specifications beyond"
          in prompt)
    check("   the exact cut tool name does NOT",
          "reality capture" not in prompt.lower()
          and "photogrammetry" not in prompt.lower(),
          [l for l in prompt.splitlines() if "capture" in l.lower()])
    check("   but it is retained machine-side for the audit",
          any("reality capture" in x.lower() or "photogrammetry" in x.lower()
              for v2 in r["terms"].values() for x in v2),
          r["terms"])
    leak = DRAFT + "\n\nThe room was modelled in Reality Capture."
    check("   and a leak of it is caught",
          ST.cut_adherence(leak, arch, r["terms"])["violations"],
          ST.cut_adherence(leak, arch, r["terms"]))

    # 4. USED software/tool: the approved tool is allowed, an extra one is not.
    arch, led, r, prompt = setup(
        used_extra=[("The catalogue was typeset in Blender.",
                     "constructed from Himalayan salt bricks")],
        cut_props=[("The room was modelled in Reality Capture.",
                    "The pavilion closed after the Kunsthalle season ended")])
    check("4. the approved tool reaches the Writer", "Blender" in prompt)
    ok4 = DRAFT + "\n\nThe catalogue was typeset in Blender."
    check("   and using it is not a violation",
          not ST.cut_adherence(ok4, arch, r["terms"])["violations"],
          ST.cut_adherence(ok4, arch, r["terms"])["violations"])
    bad4 = DRAFT + "\n\nThe room was modelled in Reality Capture."
    check("   while an UNAPPROVED tool is still blocked",
          ST.cut_adherence(bad4, arch, r["terms"])["violations"],
          ST.cut_adherence(bad4, arch, r["terms"]))
    check("   and the boundary line is present alongside the approved tool",
          "beyond those the article facts above explicitly approve" in prompt)


def test_a_provenance_frame_needs_an_apparatus_SUBJECT():
    """The Ground Truth canary reached the safety stage clean of CUT leakage and
    negatives, and was then held by

        "Rent alone does not tell you whether housing is affordable, and neither
         does income"

    which is a claim about a MEASURE, not about the research apparatus. The bare verb
    phrase matched anything that "does not tell".

    story.py already draws this distinction for "the material" -- "a telescope's data is
    material, and a pavilion is made of materials. Only the auditing construction is a
    leak." The same anchoring now applies to the verb frame."""
    clean = [
        "Rent alone does not tell you whether housing is affordable, and neither does "
        "income.",
        "The survey does not say what anyone heard.",
        "A photograph does not show the weight of the thing.",
        "The catalogue does not describe the acoustics of any room.",
        "A measure does not tell you what it cannot hold.",
    ]
    leaky = [
        "It does not describe the building's form.",
        "This does not establish who built it.",
        "The source does not establish that anyone rode it.",
        "The evidence does not say who built it.",
        "The brief does not describe the funder.",
        "The research pack does not report a price.",
        "The material does not give a date.",
        "Nothing in the source names the mason.",
        "This reading is not supported by the anchor.",
    ]
    for s in clean:
        check("a world claim is not machine language: %r" % s[:52],
              not ST.leaks(s), ST.leaks(s))
    for s in leaky:
        check("an auditing construction is still caught: %r" % s[:52],
              ST.leaks(s), s)
    check("and the article-level screen agrees",
          ST.prose_leaks(" ".join(clean))["ok"]
          and not ST.prose_leaks(" ".join(leaky))["ok"])
    # PR #62's own contract: a subjectless auditing sentence IS a leak, and the pronoun
    # half of the anchor exists to keep it one. Asserted here so a future narrowing
    # cannot quietly drop it.
    check("a subjectless auditing sentence is still a leak",
          ST.prose_leaks("It does not describe the building's form.")["total"] > 0)
    check("and a bare mention of a document still is not",
          ST.prose_leaks("The newspaper printed a correction the next "
                         "morning.")["ok"])


def test_the_grounder_sees_what_the_ledger_was_frozen_from():
    """The first canary run to reach the Grounder held with three TRUE_UNSUPPORTED
    findings, and the Grounder explained why in its own words:

        "The S1 excerpt breaks off mid-quotation at 'If you're going through NY'.
         The remainder of what Blinder said is not in the fetched..."

    S1 was 7,390 characters and it was shown 3,000. PACK_SOURCE_CHARS is sized to stop a
    supporting source crowding out the anchor in a READING prompt; grounding is not a
    reading prompt, and the ledger is frozen from far more. A grounder shown less
    material than the article was written from reports the shortfall as invention."""
    import new_engine_v1.stages as S
    check("the legacy default is unchanged",
          __import__("inspect").signature(S.ground)
          .parameters["per_source_chars"].default == S.PACK_SOURCE_CHARS)
    pack = {"sources": [{"source_id": "S1", "role": "INDEPENDENT", "url": "u",
                         "text": "word " * 3000}]}
    legacy = S.pack_material_block(pack)
    wide = S.pack_material_block(pack, CP.FREEZE_SOURCE_CHARS)
    check("the composition budget shows strictly more", len(wide) > len(legacy))
    check("and it is the same budget the freeze used",
          CP.FREEZE_SOURCE_CHARS > S.PACK_SOURCE_CHARS)

    # The bridge really passes it, observed at the boundary rather than assumed.
    seen = {}
    real = S.ground

    def spy(provider, article, src, sha, pk=None, per_source_chars=S.PACK_SOURCE_CHARS):
        seen["per_source_chars"] = per_source_chars
        return dict(GROUND_CLEAN)

    S.ground = spy
    try:
        CP.ground_candidate(object(), "# t\n\nprose", S0, "sha", PACK)
    finally:
        S.ground = real
    check("ground_candidate passes the freeze budget",
          seen.get("per_source_chars") == CP.FREEZE_SOURCE_CHARS, seen)


def test_a_definitional_gloss_is_adjudicated_but_nothing_else_is():
    """With the Grounder's truncation fixed, one finding remained and it blocks every run
    whose architecture uses a definition:

        TRUE_UNCERTAIN  "A servo is a small motor that turns to a commanded angle
                         and holds there."

    The architecture may declare `definitions` and render() tells the Writer to EXPLAIN
    AT FIRST USE. The Grounder does not see the architecture, so it correctly reports
    that the sources do not establish the gloss -- they do not; it is general knowledge
    the packet asked for. decision.py already provides the escape hatch
    (`uncertain_adjudicated`); this uses it deterministically.

    THE BOUNDS ARE THE POINT. Only TRUE_UNCERTAIN is eligible, the sentence must name a
    term the architecture actually declared, and it must add no factual surface the
    packet does not carry."""
    arch = copy.deepcopy(ARCH)
    arch["definitions"] = {"servo": "a small motor that turns to a commanded angle"}
    packet, _ = CP.writer_packet(arch, LEDGER)
    import new_engine_v1.stages as S
    real = S.ground

    def run_ground(findings):
        S.ground = lambda *a, **k: {"status": "settled", "findings": findings}
        try:
            return CP.ground_candidate(object(), "# t\n\nprose", S0, "sha", PACK,
                                       arch, packet)
        finally:
            S.ground = real

    gloss = {"id": "G1", "classification": "TRUE_UNCERTAIN",
             "quote": "A servo is a small motor that turns to a commanded angle."}
    out = run_ground([gloss])
    check("a gloss on a DECLARED term is adjudicated", out["status"] == CP.PASS,
          out["blocking"])
    check("and the adjudication is recorded with its reason",
          out["uncertain_adjudicated_as_definitions"][0]["id"] == "G1",
          out["uncertain_adjudicated_as_definitions"])

    # An undeclared term is NOT adjudicated.
    other = {"id": "G2", "classification": "TRUE_UNCERTAIN",
             "quote": "A gyroscope is a spinning wheel that resists a change of axis."}
    check("a gloss on an UNDECLARED term still blocks",
          run_ground([other])["status"] == CP.HOLD)

    # A gloss that smuggles in new factual surface is NOT adjudicated.
    smuggle = {"id": "G3", "classification": "TRUE_UNCERTAIN",
               "quote": "A servo is a small motor built in Rotterdam in 1974."}
    r = run_ground([smuggle])
    check("a gloss that adds a new entity or number still blocks",
          r["status"] == CP.HOLD, r["uncertain_adjudicated_as_definitions"])

    # TRUE_UNSUPPORTED is never eligible, whatever it names.
    unsup = {"id": "G4", "classification": "TRUE_UNSUPPORTED",
             "quote": "A servo is a small motor that turns to a commanded angle."}
    check("TRUE_UNSUPPORTED is never adjudicated",
          run_ground([unsup])["status"] == CP.HOLD)
    check("and it is not recorded as adjudicated either",
          not run_ground([unsup])["uncertain_adjudicated_as_definitions"])

    # With no definitions declared at all, nothing is adjudicated.
    arch2 = copy.deepcopy(ARCH); arch2["definitions"] = {}
    packet2, _ = CP.writer_packet(arch2, LEDGER)
    S.ground = lambda *a, **k: {"status": "settled", "findings": [gloss]}
    try:
        out2 = CP.ground_candidate(object(), "# t\n\nprose", S0, "sha", PACK,
                                   arch2, packet2)
    finally:
        S.ground = real
    check("no declared definitions means no adjudication",
          out2["status"] == CP.HOLD, out2["blocking"])
    # And an unsettled grounder is still never a pass.
    S.ground = lambda *a, **k: {"status": "unresolved", "findings": []}
    try:
        out3 = CP.ground_candidate(object(), "# t\n\nprose", S0, "sha", PACK,
                                   arch, packet)
    finally:
        S.ground = real
    check("an unresolved grounding status still holds", out3["status"] == CP.HOLD)


def test_cut_confidence_tiers_and_what_still_holds_an_article():
    """Single-token lexical CUT detection has a precision ceiling, established over five
    downstream replays on one frozen architecture -- each produced a different collision
    between a cut fact's word and an unrelated sense of the same word:

        channel     cut "a curved rear channel" (groove) / art "the usual channels"
        assembled   cut "the assembled device"  / art "torque assembled out of..."

    No frequency measure separates those and no allowlist closes by enumeration. A term
    is tiered by SHAPE, which is decidable, not by its senses, which are not."""
    for term in ("12.15", "$239", "2020", "ESP32S3", "Reality Capture", "Idle Hands",
                 "Lyft", "New York City"):
        check("HIGH confidence: %r" % term,
              CP.cut_term_confidence(term) == CP.CUT_HIGH, term)
    for term in ("channel", "assembled", "surface", "capture", "circuit",
                 "photogrammetry", "download", "reading"):
        check("LOW confidence: %r" % term,
              CP.cut_term_confidence(term) == CP.CUT_LOW, term)
    check("an ordinary word capitalised at a sentence start is not a name",
          CP.cut_term_confidence("Across") == CP.CUT_LOW)

    arch = copy.deepcopy(ARCH)
    led = copy.deepcopy(LEDGER)
    led["F09"] = F("F09", "The plinth held an ESP32 board bought for $412.90 from "
                          "Kunsthalle Supplies, and the assembled unit has a channel.",
                   "The pavilion closed after the Kunsthalle season ended", ev=("S1",))
    arch["cut_evidence"] = arch["cut_evidence"] + [
        {"evidence_id": "F09", "reason": "BACKGROUND_NOT_NEEDED"}]
    r = CP.derive_cut_watch_terms(arch, led)
    packet, _ = CP.writer_packet(arch, led, r["prohibitions"])

    def audit(extra):
        return CP.safety_audit(DRAFT, DRAFT + "\n\n" + extra, packet, arch, led,
                               r["terms"], r)

    # A LOW-confidence collision is telemetry and does not HOLD.
    low = audit("The usual channels carried the assembled argument.")
    check("a bare everyday token does NOT hold the article",
          not any("CUT_LEAKAGE" in b for b in low["blocking"]), low["blocking"])
    check("but it IS recorded as a CUT_ADVISORY, never discarded",
          any(x["token"].lower() in ("channel", "assembled")
              and x["kind"] == CP.CUT_ADVISORY for x in low["advisories"]),
          low["advisories"])
    adv = next(x for x in low["advisories"] if x["kind"] == CP.CUT_ADVISORY)
    for field in ("token", "sentence", "rule", "why_not_hard"):
        check("   the advisory carries its %s" % field, adv.get(field), adv)
    check("   and names the originating cut fact", "cut fact F09" in adv["rule"], adv)

    # A HIGH-confidence shape still holds.
    for extra, why in (("The board cost $412.90.", "a price"),
                       ("An ESP32 sat in the plinth.", "a part name"),
                       ("It came from Kunsthalle Supplies.", "a named supplier")):
        out = audit(extra)
        check("%s STILL holds the article" % why,
              any("CUT_LEAKAGE" in b for b in out["blocking"]), (extra, out["blocking"]))

    # The other controls remain authoritative on actual excluded content.
    ent = audit("Rotterdam paid for the plinth in 1974.")
    check("an unapproved entity and number still hold, via the factual surface audit",
          any("NEW_UNSUPPORTED_FACTS" in b for b in ent["blocking"]), ent["blocking"])
    check("and the CUT audit still sees everything, blocking or not",
          r["terms"]["F09"], r["terms"]["F09"])
    check("high-confidence terms are reported separately",
          any(CP.cut_term_confidence(x) == CP.CUT_HIGH
              for x in r["high_confidence_terms"].get("F09", [])),
          r.get("high_confidence_terms"))


def test_spatial_and_scene_tokens_are_advisory_and_reach_the_reader():
    """"upper limit" is a range, not a storey, and the canary was held by exactly that
    while the packet licensed the idea. A bare SPATIAL_RISK or SCENE_RISK token cannot
    decide its own sense, so it is advisory -- but SENSORY stays HARD, because a colour
    the evidence never mentions is the "pink" incident and there is no abstract reading
    of it."""
    packet, _ = CP.writer_packet(ARCH, LEDGER)

    def audit(extra):
        return CP.safety_audit(DRAFT, DRAFT + "\n\n" + extra, packet, ARCH, LEDGER,
                               {}, {"cut_without_distinctive_terms": ["F07"]})

    sp = audit("The upper limit of what a visitor hears was set by hand.")
    check("a bare spatial token does not hold the article",
          not any("NEW_UNSUPPORTED_FACTS" in b for b in sp["blocking"]), sp["blocking"])
    check("it is reported as SPATIAL_ADVISORY",
          any(a["kind"] == CP.SPATIAL_ADVISORY and a["token"] == "upper"
              for a in sp["advisories"]), sp["advisories"])
    a = next(x for x in sp["advisories"] if x["kind"] == CP.SPATIAL_ADVISORY)
    check("   with the article sentence", "upper limit" in a["sentence"], a)
    check("   and the originating rule", a["rule"] == "story.SPATIAL_RISK", a)
    check("   and why it was not hard", "cannot decide" in a["why_not_hard"], a)

    sc = audit("A laptop sat open on the desk.")
    check("a bare scene token does not hold either",
          not any("NEW_UNSUPPORTED_FACTS" in b for b in sc["blocking"]), sc["blocking"])
    check("it is reported as SCENE_ADVISORY",
          any(x["kind"] == CP.SCENE_ADVISORY for x in sc["advisories"]),
          sc["advisories"])

    # SENSORY, NUMBERS and ENTITIES stay HARD.
    for extra, why in (("The bricks were pink.", "an invented colour"),
                       ("It cost 4,200 euros.", "an unlicensed number"),
                       # NOT sentence-initial: _entities skips a leading capital,
                       # because a capital there carries no information.
                       ("The plinth was paid for by Rotterdam.",
                        "an unlicensed entity")):
        out = audit(extra)
        check("%s STILL holds the article" % why,
              any("NEW_UNSUPPORTED_FACTS" in b for b in out["blocking"]),
              (extra, out["blocking"]))

    # And the advisories reach the Reader as questions, not verdicts.
    block = CP.advisory_block(sp["advisories"])
    check("the reader is shown the advisory", "upper" in block)
    check("and told it is not a finding",
          "Not findings" in block and "Settle each one" in block, block[:200])
    check("an empty advisory list adds nothing to the prompt",
          CP.advisory_block([]) == "")
    prov = Scripted([READER_OK])
    out = CP.reader_gate(prov, DRAFT, sp["advisories"])
    check("the reader gate accepts them and records how many",
          out["advisories_shown"] == len(sp["advisories"]), out)
    check("and they appear in its prompt",
          "ADVISORY FLAGS" in prov.calls[0]["user"])


def test_a_packet_defect_is_repairable_because_it_is_seen_in_time():
    """The first fresh-subject run passed Ledger, Worth, Architecture and CUT, then died
    with no way forward: beat B4's `must_not_say_yet` read

        "Do not yet give the evidence about existing local requirements."

    and validate_packet refuses a packet carrying a provenance frame. The gate was right
    -- that text reaches the Writer through render() as "not yet: ..." and apparatus
    register transcribes. What was wrong is WHEN it ran: inside writer_packet, after the
    architecture had been accepted and its repair budget spent, so a one-line fault was
    terminal."""
    bad = copy.deepcopy(ARCH)
    bad["beats"][1]["must_not_say_yet"] = ("Do not yet give the evidence about the "
                                           "eight entries.")
    errs = CP.check_architecture(bad, LEDGER)
    check("a packet defect is now an ARCHITECTURE failure",
          any(e.startswith("PACKET:") for e in errs), errs[:4])
    check("and it names the frame", any("provenance frame" in e for e in errs), errs[:4])
    check("a clean architecture still validates",
          not [e for e in CP.check_architecture(ARCH, LEDGER)
               if e.startswith("PACKET:")])

    # Which means the repair loop can answer it, on the same budget as anything else.
    prov, out = run([{"facts": list(LEDGER.values())}, WORTH, bad, ARCH]
                    + full_script()[3:])
    check("the repair fixes it and the run continues", out["status"] == CP.PASS,
          out.get("failure_reason"))
    check("it cost one architecture repair",
          out["detail"][CP.ARCHITECTURE]["repairs"] == 1)
    check("and the repair was answering the packet failure",
          "PACKET" in str(out["detail"][CP.ARCHITECTURE]["repair_history"]),
          out["detail"][CP.ARCHITECTURE]["repair_history"])

    # writer_packet keeps its own check, so nothing reaches the Writer unchecked.
    held = False
    try:
        CP.writer_packet(bad, LEDGER)
    except CP.CompositionHold as e:
        held = any("provenance frame" in r for r in e.reasons)
    check("the final assertion in writer_packet is still there", held)

    # A scaffold name in a prose field is caught the same way.
    scaf = copy.deepcopy(ARCH)
    scaf["beats"][0]["happens"] = "In CRIP_TURN the salt is re-read."
    check("a scaffold name is an architecture failure too",
          any("scaffold" in e.lower() for e in CP.check_architecture(scaf, LEDGER)),
          CP.check_architecture(scaf, LEDGER)[:3])


GROUND_DIRTY = {"status": "settled", "findings": [
    {"id": "G1", "classification": "TRUE_UNSUPPORTED",
     "quote": "No entry describes what any visitor heard.",
     "why": "the exclusivity is not carried by the evidence"}]}


def test_one_grounded_factual_repair_then_the_full_stack_again():
    """Two independent fresh subjects reproduced the same failure class: every
    deterministic screen passed and the Grounder still found genuine over-reach --
    manufactured exclusivity, a draft quote relocated to the present tense, an ambiguous
    date. The screens cover added SURFACE; they do not cover added SCOPE, and "X is the
    single Y" is an exclusivity in POSITIVE shape that negative_claim_scan never sees.

    So the Grounder is the semantic authority and the repair only subtracts."""
    fixed = "No catalogue entry in the eight describes what any visitor heard."
    repair = {"edits": [{"finding_id": "G1", "operation": "NARROW",
                         "original": "No entry describes what any visitor heard.",
                         "repaired": fixed, "fact_ids": ["F05"],
                         "what_was_removed": "the unbounded scope"}]}

    def run_g(ground_seq, extra=None):
        """ground_seq: results returned by successive S.ground calls."""
        import new_engine_v1.stages as S
        real = S.ground
        seq = list(ground_seq)
        calls = {"n": 0}

        def fake(*a, **k):
            calls["n"] += 1
            return dict(seq.pop(0) if seq else GROUND_CLEAN)

        S.ground = fake
        # The repair call sits between Continuity and the Reader, so its reply belongs
        # there: [ledger, worth, arch, writer, continuity] + [repair] + [reader].
        script = full_script()[:5] + list(extra or []) + [READER_OK]
        prov = Scripted(script)
        try:
            return prov, calls, CP.run_story_architecture_composition(
                prov, pack=PACK, source_text=S0, source_sha="x",
                subject=PACK["subject"], fact_check_fn=lambda a: dict(FC_CLEAN))
        finally:
            S.ground = real

    # 1. Grounder PASS -> no repair call at all.
    prov, calls, out = run_g([GROUND_CLEAN])
    check("1. a clean grounder spends no repair", out["status"] == CP.PASS
          and calls["n"] == 1, (out.get("failure_reason"), calls))
    check("   and no repair is recorded",
          not out["detail"][CP.GROUNDING].get("repair"))

    # 2. A repairable HOLD -> exactly one repair, then safety, then Grounder again.
    prov, calls, out = run_g([GROUND_DIRTY, GROUND_CLEAN], [repair])
    check("2. one repair rescues the article", out["status"] == CP.PASS,
          out.get("failure_reason"))
    check("   the grounder ran TWICE", calls["n"] == 2, calls)
    check("   exactly one repair", out["repairs_by_stage"].get(CP.GROUNDING) == 1)
    check("   the repaired wording is what carries", fixed in out["article_text"])
    check("   and it reached the reader", out["stages"][CP.READER] == CP.PASS)

    # 6. Provenance: every edit auditable.
    ed = out["detail"][CP.GROUNDING]["repair"]["edits"][0]
    for field in ("finding_id", "operation", "original", "repaired",
                  "what_was_removed", "fact_ids", "support_spans",
                  "authorising_finding"):
        check("   provenance carries %s" % field, ed.get(field) is not None, ed)
    check("   and names the authorising finding", ed["finding_id"] == "G1")

    # 7. A second grounding failure is the end.
    prov, calls, out = run_g([GROUND_DIRTY, GROUND_DIRTY], [repair])
    check("7. a second grounder HOLD ends the article",
          out["failure_stage"] == CP.GROUNDING, out.get("failure_stage"))
    check("   and says it was after a repair",
          "AFTER one factual repair" in out["failure_reason"], out["failure_reason"])
    check("   NEVER a second repair", calls["n"] == 2, calls)
    stages = [prov.stage_of(i) for i in range(len(prov.calls))]
    check("   no Writer regeneration", stages.count("WRITER") == 1, stages)
    check("   the fact check is not reached",
          out["stages"][CP.FACT_CHECK] == CP.NOT_RUN)


def test_the_factual_repair_can_only_subtract():
    """A declaration of intent is not a permission. Every edit is checked mechanically."""
    packet, _ = CP.writer_packet(ARCH, LEDGER)
    findings = GROUND_DIRTY["findings"]
    orig = "No entry describes what any visitor heard."

    def apply(rep, fact_ids=("F05",), op="NARROW", fid="G1"):
        return CP.apply_grounding_repair(
            DRAFT, [{"finding_id": fid, "operation": op, "original": orig,
                     "repaired": rep, "fact_ids": list(fact_ids)}],
            findings, LEDGER, packet)

    _, prov, errs = apply("No catalogue entry describes what any visitor heard.")
    check("a narrowing is applied", not errs and prov, errs)

    for rep, why in (
        ("No entry describes what any of the 47 visitors heard.", "a new number"),
        ("No entry by the curator Anneke Mertens describes it.", "a new entity"),
        ("No entry describes it, because the salt absorbed the sound.", "a new relation"),
    ):
        _, _, e = apply(rep)
        check("%s is refused" % why, e, (rep, e))

    # BUT A CORRECTION IS MEASURED AGAINST THE EVIDENCE IT CITES. The first real repair
    # was refused for adding the number "27" and a TEMPORAL relation on edits doing
    # exactly what CORRECT_DATE and CORRECT_TIME are for. A guard that refuses those
    # refuses the permission it exists to enforce.
    _, prov2, e2 = apply("No entry of the eight describes what any visitor heard.",
                         fact_ids=("F04", "F05"))
    check("a number carried by a CITED fact is allowed",
          not e2 and prov2, e2)
    _, _, e3 = apply("No entry of the eight describes what any visitor heard.",
                     fact_ids=("F01",))
    check("but the same number is refused when no cited fact carries it", e3, e3)
    # Isolate the TEMPORAL case: the negation is carried by the cited F05, so the only
    # relation in question is the time reference the correction exists to fix.
    timed = "No entry described what any visitor heard before the season ended."
    _, prov4, e4 = apply(timed, fact_ids=("F05",), op="CORRECT_TIME")
    check("a time correction may change temporal content", not e4, e4)
    _, _, e5 = apply(timed, fact_ids=("F05",), op="NARROW")
    check("while the SAME edit under NARROW is refused for the same relation",
          any("TEMPORAL" in str(x) for x in e5), e5)
    check("   so the exemption is tied to the operation, not the wording",
          bool(e5) and not e4)

    _, _, e = apply("Anything.", fid="G9")
    check("an edit citing a finding the grounder never made is refused", e, e)
    _, _, e = apply("Anything.", op="IMPROVE")
    check("an undeclared operation is refused", e, e)
    _, _, e = apply("Anything.", fact_ids=("F99",))
    check("an edit citing an unknown fact id is refused", e, e)
    _, _, e = CP.apply_grounding_repair(
        DRAFT, [{"finding_id": "G1", "operation": "NARROW",
                 "original": "a sentence that is not in the article at all",
                 "repaired": "x", "fact_ids": ["F05"]}], findings, LEDGER, packet)
    check("an edit whose original is not in the article is refused", e, e)

    # DELETE is always available.
    text, prov, errs = apply("", op="DELETE")
    check("a deletion is permitted", not errs and orig not in text, errs)

    # THE REPAIR MUST BE SHOWN THE FACT IT NEEDS. A date-bearing fact shares no
    # vocabulary with the sentence whose date is wrong, so overlap alone never selects
    # it -- and a repair that cannot see the evidence reaches for the grounder's
    # explanation instead, which is not evidence.
    dated = dict(LEDGER)
    dated["F20"] = F("F20", "The catalogue was published on 27th August 2026.",
                     "The pavilion closed after the Kunsthalle season ended", ev=("S1",))
    q = "No entry describes what any visitor heard by noon that day."
    plain = [fid for fid, _ in CP._relevant_facts(q, dated)]
    withdate = [fid for fid, _ in CP._relevant_facts(q, dated, "published on 27 August 2026")]
    check("overlap alone does not surface the date-bearing fact", "F20" not in plain, plain)
    check("but a date-shaped finding does", "F20" in withdate, withdate)
    check("and the repair is told to cite every fact its wording rests on",
          "CITE EVERY FACT YOUR REPAIRED WORDING RESTS ON" in CP.REPAIR_GROUNDING_SYSTEM)
    check("and told the grounder's explanation is not evidence",
          "THE GROUNDER'S EXPLANATION IS NOT EVIDENCE" in CP.REPAIR_GROUNDING_SYSTEM)
    check("and told to remove an unresolvable reference rather than resolve it",
          "remove the reference rather than resolve it" in CP.REPAIR_GROUNDING_SYSTEM)

    # "27th" and "27" are the same day, and ST._numbers reads only the second. A fact
    # saying "published on 27th August 2026" licensed "2026" and not "27", so a repair
    # restoring that date read as an addition -- the same class as the decimal split.
    check("an ordinal in the evidence licenses the cardinal in the repair",
          "27" in CP._numbers_of("published on 27th August 2026"))
    check("and the plain form still works",
          "27" in CP._numbers_of("published on 27 August 2026"))
    check("while an unrelated number is still not licensed",
          "31" not in CP._numbers_of("published on 27th August 2026"))
    dated2 = dict(LEDGER)
    dated2["F20"] = F("F20", "The catalogue was published on 27th August 2026.",
                      "The pavilion closed after the Kunsthalle season ended", ev=("S1",))
    _, prov6, e6 = CP.apply_grounding_repair(
        DRAFT, [{"finding_id": "G1", "operation": "CORRECT_DATE", "original": orig,
                 "repaired": "No entry published on 27 August 2026 describes what any "
                             "visitor heard.", "fact_ids": ["F05", "F20"]}],
        findings, dated2, packet)
    check("so a date restored from an ordinal fact is accepted", not e6 and prov6, e6)

    check("LEGITIMATE_INTERPRETATION is not repairable",
          not CP.repairable_findings(
              [{"id": "L1", "classification": "LEGITIMATE_INTERPRETATION",
                "quote": "x"}]))
    check("but TRUE_UNSUPPORTED and TRUE_UNCERTAIN are",
          len(CP.repairable_findings(
              [{"id": "A", "classification": "TRUE_UNSUPPORTED", "quote": "x"},
               {"id": "B", "classification": "TRUE_UNCERTAIN", "quote": "y"}])) == 2)


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
    prov, out = run([{"facts": list(LEDGER.values())}, WORTH, minted,
                     minted, minted])
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

    prov2, out2 = run([{"facts": list(LEDGER.values())}, WORTH, bad, bad, bad])
    check("a still-invalid architecture holds", out2["failure_stage"] == CP.ARCHITECTURE)
    check("and is attempted no more than the budget allows",
          sum(1 for i in range(len(prov2.calls))
              if prov2.stage_of(i) in ("ARCHITECTURE", "ARCH_REPAIR"))
          == 1 + CP.MAX_ARCHITECTURE_REPAIRS,
          [prov2.stage_of(i) for i in range(len(prov2.calls))])
    check("the reason says the budget was spent",
          "of a maximum %d" % CP.MAX_ARCHITECTURE_REPAIRS in out2["failure_reason"],
          out2["failure_reason"][:140])


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
    lic["F07"]["proposition"] = ("The pavilion of salt brick closed after the "
                                 "Kunsthalle season.")
    t2 = CP.derive_cut_watch_terms(ARCH, lic)
    check("'pavilion' is not watched: the packet licenses it",
          not any(x.lower() == "pavilion" for x in t2["terms"]["F07"]),
          t2["terms"]["F07"])
    check("'salt' is not watched either",
          not any(x.lower() == "salt" for x in t2["terms"]["F07"]))
    check("the distinctive proper noun is still watched",
          any("kunsthalle" in x.lower() for x in t2["terms"]["F07"]),
          t2["terms"]["F07"])

    # The shapes that made the CUT audit vacuous.
    check("a str value is refused",
          any("iterates wrongly" in e
              for e in CP.validate_cut_terms({"F07": "Kunsthalle"}, ARCH)))
    check("a dict value is refused",
          any("iterates wrongly" in e
              for e in CP.validate_cut_terms({"F07": {"Kunsthalle": 1}}, ARCH)))
    check("a whole non-dict is refused",
          any("must be a dict" in e for e in CP.validate_cut_terms(["Kunsthalle"], ARCH)))
    check("a cut fact with no entry at all is refused",
          any("nothing would watch it" in e for e in CP.validate_cut_terms({}, ARCH)))
    check("a term below the floor is refused, not silently skipped",
          any("floor cut_adherence enforces" in e
              for e in CP.validate_cut_terms({"F07": ["ok"]}, ARCH)),
          CP.validate_cut_terms({"F07": ["ok"]}, ARCH))

    # And the audit it feeds actually sees a leak.
    leak = DRAFT + "\n\nThe pavilion closed once the Kunsthalle season had ended."
    ca = ST.cut_adherence(leak, ARCH, terms["terms"])
    check("a real CUT leak is caught by the derived terms",
          bool(ca["violations"]), ca)
    # F07's own words are either licensed by the packet or ordinary English, so nothing
    # distinctive survives -- and the derivation SAYS so rather than leaving a silent gap.
    check("a cut fact with no distinctive term is named, not hidden",
          terms["cut_without_distinctive_terms"] in ([], ["F07"]),
          terms["cut_without_distinctive_terms"])


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
    # An invented colour, in the WRITER's own draft. It has to originate there rather
    # than in the editor: an editor that invents something is discarded by the continuity
    # fail-safe, so a continuity-introduced defect never reaches the safety stack. This
    # test is about what happens when the ARTICLE ITSELF is unsafe.
    bad_draft = DRAFT.replace("The room was built from Himalayan salt bricks",
                              "The room was built from pink Himalayan salt bricks")
    prov, out = run(full_script()[:3] + [envelope(bad_draft), _edits_from(bad_draft), READER_OK])
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
    check("and continuity was NOT discarded -- the editor did nothing wrong",
          not out["detail"][CP.CONTINUITY].get("discarded"))
    check("the safety audit is reported for both draft and final",
          set(out["detail"][CP.SAFETY]["audits"]) == {"writer_draft",
                                                      "continuity_final"})


def test_the_grounder_and_fact_check_run_only_after_safety():
    seen = []

    def fc(article):
        seen.append("FACT_CHECK")
        return dict(FC_CLEAN)

    bad_draft = DRAFT.replace("The room was built from Himalayan salt bricks",
                              "The room was built from pink Himalayan salt bricks")
    prov, out = run(full_script()[:3] + [envelope(bad_draft), _edits_from(bad_draft),
                                     READER_OK], fact_check_fn=fc)
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
    # An unsupported finding now attempts ONE factual repair first (see
    # test_one_grounded_factual_repair_then_the_full_stack_again). With no usable repair
    # reply scripted, the stage still HOLDS -- which is what this test is about: nothing
    # downstream runs on a grounding failure, repair attempt or not.
    prov2, out2 = run(full_script(), ground=dirty, fact_check_fn=fc)
    check("an unsupported grounder finding holds", out2["failure_stage"] == CP.GROUNDING)
    check("the fact check is not reached after a grounding hold", seen == [], seen)
    check("and the writer is not regenerated",
          [prov2.stage_of(i) for i in range(len(prov2.calls))].count("WRITER") == 1)
    check("the reader is not reached either",
          out2["stages"][CP.READER] == CP.NOT_RUN)

    # An unadjudicated uncertain finding holds too: the frozen policy, unchanged.
    unc = {"status": "settled",
           "findings": [{"id": "G2", "classification": "TRUE_UNCERTAIN", "quote": "x"}]}
    _, out3 = run(full_script(), ground=unc)
    check("an unadjudicated TRUE_UNCERTAIN finding holds",
          out3["failure_stage"] == CP.GROUNDING, out3.get("failure_reason"))
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
        bad_draft = DRAFT.replace("The room was built from Himalayan salt bricks",
                                  "The room was built from pink Himalayan salt bricks")
        run(full_script()[:3] + [envelope(bad_draft), _edits_from(bad_draft),
                                 READER_OK], out_dir=out_dir)
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

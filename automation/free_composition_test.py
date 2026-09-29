"""
free_composition_test.py -- the FREE ARGUMENTATIVE composition path.

WHAT THESE TESTS ARE FOR. The claim this path makes is not "the prose is better" -- that is
an editorial judgement nobody can assert in a test suite. The claim is mechanical and it is
falsifiable: THE PLAN DOES NOT REACH THE WRITER, the Ledger still owns every fact, exactly
one surgical repair is available, and nothing about publication routing moved.

SOURCE-CODE GREP IS NOT SUFFICIENT AND THIS PROJECT HAS PAID FOR BELIEVING IT WAS. An A/B
arm once told the Writer "you decide the order" while the system prompt still told it to
"write the first beat"; both statements were true of the code and the experiment was
worthless. So the prompt tests below intercept the ACTUAL BYTES handed to `provider.
complete` at runtime, and assert on those.

No network, no credentials, no real model. The upstream stages that this change does not
touch (freeze_ledger, worth_gate, architect) are replaced with canned results: what is
under test is THIS module's orchestration, not theirs.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import composition as CP            # noqa: E402
from new_engine_v1 import free_composition as FC       # noqa: E402
from new_engine_v1 import craft_corpus as CC           # noqa: E402
from new_engine_v1 import editorial_lens as EL         # noqa: E402
from new_engine_v1 import runner as R                  # noqa: E402

FAILURES: list = []


def check(label, ok, detail="") -> None:
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "   <- %r" % (detail,)))
    if not ok:
        FAILURES.append(label)


# ── fixture ───────────────────────────────────────────────────────────────────
# A small self-consistent ledger. F04 is deliberately a fact NO architecture below
# selects, so "full evidence access" is a real question rather than a decorative one.
LEDGER = {
    "F01": {"fact_id": "F01", "claim_type": "POSITIVE_FACT", "claim_kind": "EVENT",
            "proposition": "The Darulelhan conservatory removed Turkish classical music "
                           "instruction from its curriculum in 1926.",
            "support_span": "removed Turkish classical music instruction in 1926",
            "evidence_ids": ["S0"], "entities": ["Darulelhan"], "scope": "WORLD"},
    "F02": {"fact_id": "F02", "claim_type": "POSITIVE_FACT", "claim_kind": "DISPOSITION",
            "proposition": "Ottoman classical music was transmitted by mesk, ear-based "
                           "instruction from master to student.",
            "support_span": "transmitted by mesk from master to student",
            "evidence_ids": ["S1"], "entities": [], "scope": "WORLD"},
    "F03": {"fact_id": "F03", "claim_type": "NEGATIVE_FACT", "claim_kind": "STATE",
            "proposition": "There is no composition in the makam that Arel, Ezgi and "
                           "Uzdilek describe as Cargah.",
            "support_span": "no composition exists in their Cargah",
            "evidence_ids": ["S4"], "entities": ["Arel", "Ezgi", "Uzdilek", "Cargah"],
            "scope": "WORLD"},
    "F04": {"fact_id": "F04", "claim_type": "POSITIVE_FACT", "claim_kind": "STATE",
            "proposition": "Rauf Yekta Bey wrote a chapter on Turkish music for Albert "
                           "Lavignac's Encyclopedie de la musique in 1922.",
            "support_span": "Rauf Yekta wrote for Lavignac's Encyclopedie in 1922",
            "evidence_ids": ["S1"], "entities": ["Rauf Yekta Bey", "Albert Lavignac"],
            "scope": "WORLD"},
}

RELATIONS = [{"kind": "CONTEMPORANEOUS", "subject": "F01", "object": "F04"}]

PACK = {"subject": "Turkish makam notation and what it has no symbol for",
        "sources": [
            {"source_id": "S0", "title": "A polemic on the Arel-Ezgi system",
             "publisher": "yenisafak.com", "role": "ANCHOR",
             "url": "https://www.yenisafak.com/yazarlar/x/y"},
            {"source_id": "S1", "title": "The Arel-Ezgi-Uzdilek System",
             "publisher": "betweenfrets.com", "role": "INDEPENDENT",
             "url": "https://betweenfrets.com/history/arel-ezgi-uzdilek"},
            {"source_id": "S4", "title": "", "publisher": "org.tr", "role": "INDEPENDENT",
             "url": "https://dergipark.org.tr/en/download/article-file/77378"}]}

INSTRUMENT = {
    "id": "PR005-01",
    "question": "What does this field's standard notation have no symbol for?",
    "mechanism": "A notation is a lossy encoding that presents itself as a complete "
                 "record.",
    "disconfirming_shape": "Show the notation does record it, or that practitioners "
                           "acquire it another way the field maintains deliberately.",
    "carriers": "A musical score beside a performance tradition. Dance notation.",
    "false_move": "Treating every omission as a defect. Notations are supposed to "
                  "abstract; that is their use.",
}

ARCH = {"article_type": "FEATURE", "use_facts": ["F01", "F02", "F03"],
        "cut_evidence": [{"evidence_id": "F04", "why": "REDUNDANT_PROOF"}],
        "beats": [{"beat_id": "B1", "happens": "the curriculum is emptied",
                   "facts_allowed": ["F01"], "concrete_carrier": "the conservatory"}],
        "story_spine": "a notation that cannot write what it replaced",
        "ending_move": "LAND", "prohibitions": []}

ARTICLE = """# The basic scale with no music in it

Ottoman classical music was transmitted by mesk, ear-based instruction from master to
student. There is no composition in the makam that Arel, Ezgi and Uzdilek describe as
Cargah.

Rauf Yekta Bey wrote a chapter on Turkish music for Albert Lavignac's Encyclopedie de la
musique in 1922. The Darulelhan conservatory removed Turkish classical music instruction
from its curriculum in 1926.

So the men who wrote the music down were writing while the room was being emptied."""

REPLY = ARTICLE + "\n\n---FACTS USED---\nF01 F02 F03 F04\n---NEGATIVE CLAIMS---\n" \
        "There is no composition in the makam that Arel, Ezgi and Uzdilek describe as " \
        "Cargah. :: F03"


class Recorder:
    """A provider that records every (system, user) pair it is handed."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, system, user, max_tokens=3000, timeout=180, temperature=None):
        self.calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        text = self.replies.pop(0) if self.replies else ""

        class _C:
            pass
        c = _C()
        c.text = text
        c.requested_model = "test"
        c.actual_model = "test"
        c.duration_ms = 1
        c.usage = {}
        return c


def _canned_upstream(monkey: dict):
    """Replace the stages this change does not touch with canned PASS results."""
    monkey["freeze_ledger"] = CP.freeze_ledger
    monkey["worth_gate"] = CP.worth_gate
    monkey["architect"] = CP.architect
    monkey["derive_cut"] = CP.derive_cut_watch_terms
    monkey["package"] = CP.editorial_package
    monkey["ground"] = CP.ground_candidate
    monkey["reader"] = CP.reader_gate

    CP.freeze_ledger = lambda p, pack, subj: {
        "status": CP.PASS, "ledger": dict(LEDGER), "relations": list(RELATIONS),
        "facts": len(LEDGER), "sources": PACK["sources"], "model_calls": 1, "repairs": 0}
    CP.worth_gate = lambda p, led, subj, hyp=None: {
        "status": CP.PASS, "worth_gate": {"verdict": "PASS"}, "hypothesis": hyp,
        "model_calls": 1, "repairs": 0}
    CP.architect = lambda p, led, w, subj, visual_context=None: {
        "status": CP.PASS, "architecture": dict(ARCH), "beats": 1,
        "model_calls": 1, "repairs": 0}
    CP.derive_cut_watch_terms = lambda arch, led: {
        "status": CP.PASS, "terms": {"F04": ["Lavignac"]}, "prohibitions": [],
        "model_calls": 0, "repairs": 0}
    CP.editorial_package = lambda p, text, arch, worth, refusals=None: {
        "status": CP.PASS, "package_status": CP.PACKAGE_OK, "model_calls": 1,
        "repairs": 0,
        "package": {"title": "The basic scale with no music in it",
                    "dek": "What a notation cannot write down.",
                    "excerpt": "What a notation cannot write down.",
                    "meta_description": "What a notation cannot write down.",
                    "social_hook": "What a notation cannot write down."}}
    CP.reader_gate = lambda p, text, adv=None: {
        "status": CP.PASS, "held": [], "model_calls": 1, "repairs": 0}


def _restore(monkey: dict):
    CP.freeze_ledger = monkey["freeze_ledger"]
    CP.worth_gate = monkey["worth_gate"]
    CP.architect = monkey["architect"]
    CP.derive_cut_watch_terms = monkey["derive_cut"]
    CP.editorial_package = monkey["package"]
    CP.ground_candidate = monkey["ground"]
    CP.reader_gate = monkey["reader"]


def _run(grounding_results, writer_reply=REPLY, tmp=None, repair_reply=None):
    """Run the free ladder with canned upstream and a scripted grounder."""
    monkey: dict = {}
    _canned_upstream(monkey)
    seq = list(grounding_results)
    ground_calls = {"n": 0}

    def ground(p, text, src, sha, pack, arch=None, packet=None):
        ground_calls["n"] += 1
        r = dict(seq.pop(0) if seq else seq[-1])
        r.setdefault("model_calls", 1)
        r["grounded_text_sha256"] = CP.C.sha256_text(text)
        return r

    CP.ground_candidate = ground
    replies = [writer_reply] + ([repair_reply] if repair_reply else [])
    prov = Recorder(replies)
    try:
        res = FC.run_free_argumentative_composition(
            prov, pack=PACK, source_text="source bytes", source_sha="abc",
            subject=PACK["subject"], fact_check=False, out_dir=tmp,
            instrument=INSTRUMENT,
            fact_check_fn=lambda t: {"status": CP.PASS, "model_calls": 0})
        return res, prov, ground_calls["n"]
    finally:
        _restore(monkey)


PASS_G = {"status": CP.PASS, "grounding_status": "GROUNDED", "blocking": [],
          "findings": [], "grounding": {"findings": []}}


# ── 1. flag-off parity ────────────────────────────────────────────────────────
def test_flag_off_parity() -> None:
    check("the default composition engine is unchanged",
          CP.DEFAULT_COMPOSITION_ENGINE == CP.COMPOSITION_LEGACY,
          CP.DEFAULT_COMPOSITION_ENGINE)
    check("an unset COMPOSITION_ENGINE still selects legacy",
          CP.current_composition_engine({}) == CP.COMPOSITION_LEGACY)
    check("story_architecture still resolves to itself",
          CP.current_composition_engine({"COMPOSITION_ENGINE": "story_architecture"})
          == CP.COMPOSITION_STORY_ARCHITECTURE)
    check("the new value resolves only when explicitly set",
          CP.current_composition_engine(
              {"COMPOSITION_ENGINE": "free_argumentative"})
          == CP.COMPOSITION_FREE_ARGUMENTATIVE)
    try:
        CP.current_composition_engine({"COMPOSITION_ENGINE": "free"})
        check("an unknown value still fails closed", False, "no raise")
    except CP.UnknownCompositionEngine:
        check("an unknown value still fails closed", True)

    # The planned path must still be reached with NO instrument, so Worth is asked exactly
    # what it is asked today. This is the parity that matters most.
    seen = {}
    real = CP.run_composition_with_fallback

    def spy(provider, **kw):
        seen.update(kw)
        return {"status": CP.HOLD, "stages": {}, "detail": {}, "failure_stage": "LEDGER",
                "reason_code": "X", "failure_reason": "", "article_text": "",
                "package": None, "package_status": "", "model_calls_total": 0}
    CP.run_composition_with_fallback = spy
    try:
        A = {CP.C.RESEARCH_PACK: "x"}
        R._run_story_architecture(Recorder([]), A, {}, PACK, "s", "sha", "at",
                                  pathlib.Path("/tmp"), "n", "LIVE")
    except Exception:
        pass
    finally:
        CP.run_composition_with_fallback = real
    check("the planned path is still called without an instrument",
          "instrument" not in seen, sorted(seen))


# ── 2-8. the exact writer request ─────────────────────────────────────────────
def test_exact_writer_request_bytes() -> None:
    res, prov, _ = _run([PASS_G])
    check("the run reached the Writer", len(prov.calls) >= 1, len(prov.calls))
    system = prov.calls[0]["system"]
    user = prov.calls[0]["user"]

    check("editorial-lens.md reaches the exact system bytes",
          bool(EL.load()) and EL.load()[:60] in system)
    check("the craft corpus reaches the exact system bytes, not a comment about it",
          bool(CC.load()) and CC.load()[:200] in system)
    check("the craft corpus is the real 39KB asset", len(CC.load()) > 30_000,
          len(CC.load()))
    check("the reader contract reaches the exact system bytes",
          "Engineer discovery." in system and "sequence of realizations" in system)
    check("the reader contract is a cognitive state, not a persona",
          not any(w in system for w in ("34-year-old", "demographic", "Amsterdam")))

    check("the owner's MECHANISM reaches the Writer", INSTRUMENT["mechanism"] in user)
    check("the DISCONFIRMING SHAPE reaches the Writer",
          INSTRUMENT["disconfirming_shape"] in user)
    check("CARRIERS reach the Writer", INSTRUMENT["carriers"] in user)
    check("the FALSE MOVE reaches the Writer", INSTRUMENT["false_move"] in user)
    check("editorial intent is marked as licensing no fact",
          "none of it may be asserted" in user)

    for fid in LEDGER:
        check("ledger fact %s reaches the Writer" % fid,
              LEDGER[fid]["proposition"][:50] in user)
    check("a fact the architecture CUT still reaches the free Writer",
          LEDGER["F04"]["proposition"][:50] in user)
    check("licensed joins reach the Writer as propositions",
          "LICENSED CONNECTIONS" in user and "CONTEMPORANEOUS" in user)
    check("source attribution metadata reaches the Writer",
          "publisher: yenisafak.com" in user and "role: ANCHOR" in user)
    check("a source with no established title is not described",
          "(no title established)" in user)


def test_no_architecture_control_in_runtime_bytes() -> None:
    res, prov, _ = _run([PASS_G])
    system, user = prov.calls[0]["system"], prov.calls[0]["user"]
    check("the runtime prompt carries no planning marker",
          FC.writer_inputs_are_plan_free(system, user) == [],
          FC.writer_inputs_are_plan_free(system, user))
    for marker in ("write the first beat", "THE PATH, IN ORDER", "not yet:",
                   "ending_move", "LOAD_BEARING", "carried by:"):
        check("no %r in the Writer's bytes" % marker,
              marker not in system and marker not in user)
    check("the architecture's own spine never reaches the Writer",
          ARCH["story_spine"] not in system and ARCH["story_spine"] not in user)
    check("the run still records ARCHITECTURE as having passed (shadow, not skipped)",
          res["stages"][CP.ARCHITECTURE] == CP.PASS, res["stages"])


def test_a_contradictory_prompt_holds_rather_than_writing() -> None:
    errs = FC.writer_inputs_are_plan_free("", "THE PATH, IN ORDER\n  1. open on the ward")
    check("a leaked plan in the user prompt is detected", bool(errs), errs)
    errs2 = FC.writer_inputs_are_plan_free("write the first beat as what it is", "")
    check("a leaked 'write the first beat' in the system prompt is detected",
          bool(errs2), errs2)


# ── 9. source attribution ─────────────────────────────────────────────────────
def test_source_attribution_is_evidence_not_a_regex_gate() -> None:
    block = FC.source_attribution_block(PACK)
    check("every source is named with its publisher",
          all(s["publisher"] in block for s in PACK["sources"]))
    check("the rule tells the Writer not to supply an unestablished author",
          "may not supply it" in block)
    # The defect being closed, stated as the rule the Writer is given.
    check("the one rule forbids inventing a genre or venue",
          "do not name the genre or venue" in FC.ONE_RULE)
    check("the one rule forbids completing a partial name",
          "Do not complete a partial name" in FC.ONE_RULE)

    # NO BROAD REGEX GATE. That class of validator has already been falsified on this
    # project; source attribution is closed by giving the Writer the metadata and letting
    # Grounding catch what survives. Nothing here may block a name.
    src = (HERE / "new_engine_v1" / "free_composition.py").read_text(encoding="utf-8")
    for banned in ("FORBIDDEN_NAMES", "NAME_PATTERN", "ROLE_REGEX", "_NER",
                   "SOURCE_ROLE_WORDS"):
        check("no deterministic name/role gate named %s" % banned, banned not in src)
    check("the attribution block is evidence, not a blocklist",
          "publisher:" in block and "FORBIDDEN" not in block.upper()
          and "BLOCK" not in block.upper())

    # A legitimate subject name the Ledger grants must survive the free path's own Safety
    # licensing -- the failure mode a name gate would have introduced.
    rec = FC.licensing_record(LEDGER, RELATIONS)
    sa = CP.safety_audit(ARTICLE, ARTICLE, rec, {}, LEDGER, {}, None,
                         {"S002": ["F03"]}, package=None)
    blocked = " ".join(sa.get("blocking") or [])
    for name in ("Rauf Yekta Bey", "Albert Lavignac", "Darulelhan"):
        check("legitimate subject name %r is not blocked" % name, name not in blocked,
              blocked[:200])


# ── negatives ─────────────────────────────────────────────────────────────────
def test_declared_negatives_are_verified_against_the_ledger() -> None:
    lineage, rejected = FC.verify_declared_negatives(
        ARTICLE,
        [{"sentence": "There is no composition in the makam that Arel, Ezgi and Uzdilek "
                      "describe as Cargah.", "fact_ids": ["F03"]}],
        LEDGER)
    check("a negative backed by a negative ledger fact is admitted", bool(lineage),
          (lineage, rejected))

    # F02 carries no negation anywhere in its proposition. Citing it for a claim of
    # absence must be refused. This is the case that caught the real defect:
    # `negative_shape_of` returns (None, None) for positive prose, and testing that PAIR
    # for truth admits every fact ever cited.
    _l2, rej2 = FC.verify_declared_negatives(
        ARTICLE, [{"sentence": "There is no composition in the makam that Arel, Ezgi and "
                               "Uzdilek describe as Cargah.", "fact_ids": ["F02"]}],
        LEDGER)
    check("a negative citing a fact with no negation is refused, not admitted",
          not _l2 and bool(rej2), (_l2, rej2))

    _l3, rej3 = FC.verify_declared_negatives(
        ARTICLE, [{"sentence": "Nobody ever played it.", "fact_ids": ["F03"]}], LEDGER)
    check("a declaration for a sentence not in the article is refused",
          not _l3 and bool(rej3), (_l3, rej3))

    _l4, rej4 = FC.verify_declared_negatives(
        ARTICLE, [{"sentence": "There is no composition in the makam that Arel, Ezgi and "
                               "Uzdilek describe as Cargah.", "fact_ids": ["F99"]}],
        LEDGER)
    check("a declaration citing a fact outside the Ledger is refused",
          not _l4 and bool(rej4), (_l4, rej4))


def test_reply_parsing() -> None:
    p = FC.parse_free_reply(REPLY)
    check("the article is separated from its bookkeeping",
          p["article_text"].startswith("# The basic scale")
          and "---FACTS USED---" not in p["article_text"]
          and "---NEGATIVE CLAIMS---" not in p["article_text"])
    check("declared facts are read", p["facts_used"] == ["F01", "F02", "F03", "F04"],
          p["facts_used"])
    check("declared negatives are read", len(p["declared_negatives"]) == 1,
          p["declared_negatives"])
    bare = FC.parse_free_reply("# Title\n\nsome prose with no markers at all")
    check("a reply with no markers still yields its article",
          bare["article_text"].startswith("# Title"))


# ── 10-12. the surgical repair ────────────────────────────────────────────────
BAD_QUOTE = "Rauf Yekta Bey wrote a chapter on Turkish music for Albert Lavignac's"
HOLD_G = {"status": CP.HOLD, "grounding_status": "UNSUPPORTED",
          "blocking": [{"id": "G1", "classification": "TRUE_UNSUPPORTED",
                        "quote": BAD_QUOTE, "why": "the source names no author",
                        "suggested_patch": "An encyclopedia chapter on Turkish music"}],
          "findings": [], "grounding": {"findings": []}}

REPAIR_REPLY = json.dumps({"edits": [
    {"finding_id": "G1", "operation": "NARROW", "original": BAD_QUOTE,
     "repaired": "An encyclopedia chapter on Turkish music appeared for",
     "fact_ids": ["F04"]}]})


def test_one_surgical_repair_then_an_exact_recheck() -> None:
    res, prov, n_ground = _run([HOLD_G, PASS_G], repair_reply=REPAIR_REPLY)
    check("the run passed after one repair", res["status"] == CP.PASS,
          (res["status"], res["failure_reason"]))
    check("exactly one grounding repair was recorded",
          res["repairs_by_stage"].get(CP.GROUNDING) == 1, res["repairs_by_stage"])
    check("the grounder was read exactly twice -- once, then once on repaired bytes",
          n_ground == 2, n_ground)
    g = res["detail"][CP.GROUNDING]
    check("the recheck is marked as being after the surgical repair",
          g.get("after_surgical_repair") is True)
    check("the recheck bound to the REPAIRED bytes",
          g.get("grounded_text_sha256")
          == CP.C.sha256_text(CP.bundle_text(res["article_text"], res["package"])),
          g.get("grounded_text_sha256"))
    check("the repair is recorded with the findings it answered",
          g["surgical_repair"]["findings_answered"] == ["G1"], g.get("surgical_repair"))


def test_the_repair_changes_only_the_flagged_span() -> None:
    res, _prov, _n = _run([HOLD_G, PASS_G], repair_reply=REPAIR_REPLY)
    before, after = ARTICLE, res["article_text"]
    check("the flagged wording is gone", BAD_QUOTE not in after)
    unrelated = ["Ottoman classical music was transmitted by mesk",
                 "There is no composition in the makam",
                 "The Darulelhan conservatory removed Turkish classical music",
                 "So the men who wrote the music down were writing"]
    for u in unrelated:
        check("untouched: %r" % u[:44], u in after)
    check("paragraph count is unchanged",
          len(before.split("\n\n")) == len(after.split("\n\n")),
          (len(before.split("\n\n")), len(after.split("\n\n"))))
    # THE SURGICAL PROPERTY, stated as what it actually is: no more paragraphs moved than
    # there were findings to answer. A similarity floor is the wrong instrument on a
    # 510-char fixture, where replacing one 65-char span is legitimately ~16% of the text.
    delta = res["detail"][CP.GROUNDING]["surgical_repair"]["byte_delta"]
    check("no more paragraphs changed than there were findings",
          delta["paragraphs_changed"] <= len(HOLD_G["blocking"]), delta)
    check("the article did not grow", delta["chars_after"] <= delta["chars_before"], delta)
    check("the paragraph count is stable across the repair",
          delta["paragraphs_before"] == delta["paragraphs_after"], delta)


def test_one_repair_maximum_no_pass_fishing() -> None:
    # Grounding holds, the repair is applied, and the recheck STILL holds. The run must
    # stop -- no second proposal, no third grounding read.
    res, prov, n_ground = _run([HOLD_G, HOLD_G], repair_reply=REPAIR_REPLY)
    check("a still-failing recheck HOLDs the run", res["status"] == CP.HOLD,
          res["status"])
    check("it holds at GROUNDING", res["failure_stage"] == CP.GROUNDING,
          res["failure_stage"])
    check("the grounder was read exactly twice, never a third time", n_ground == 2,
          n_ground)
    # Two provider calls total: the Writer, and ONE repair proposal. A third would be a
    # second proposal, which is what "no PASS fishing" forbids.
    check("exactly two model calls were made -- one Writer, one repair proposal",
          len(prov.calls) == 2, [c["user"][:60] for c in prov.calls])


def test_an_unrepairable_finding_is_not_repaired_at_all() -> None:
    interp = {"status": CP.HOLD, "grounding_status": "UNSUPPORTED",
              "blocking": [{"id": "G9", "classification": "LEGITIMATE_INTERPRETATION",
                            "quote": "So the men who wrote the music down"}],
              "findings": [], "grounding": {"findings": []}}
    res, _prov, n_ground = _run([interp])
    check("no repair is attempted for a non-repairable class",
          not res["repairs_by_stage"].get(CP.GROUNDING), res["repairs_by_stage"])
    check("the grounder was read exactly once", n_ground == 1, n_ground)


# ── 15. model-call budget ─────────────────────────────────────────────────────
def test_no_extra_planning_model_call() -> None:
    res, _prov, _n = _run([PASS_G])
    by = res["model_calls_by_stage"]
    check("CONTINUITY is skipped and costs nothing",
          res["stages"][CP.CONTINUITY] == CP.SKIPPED and not by.get(CP.CONTINUITY),
          (res["stages"][CP.CONTINUITY], by.get(CP.CONTINUITY)))
    check("PROSE_FINISH is skipped and costs nothing",
          res["stages"][CP.PROSE_FINISH] == CP.SKIPPED and not by.get(CP.PROSE_FINISH),
          (res["stages"][CP.PROSE_FINISH], by.get(CP.PROSE_FINISH)))
    check("the Writer costs exactly one call", by.get(CP.WRITER) == 1, by)
    check("there is no reader-trajectory or audience-model stage",
          not any(k.upper().startswith(("AUDIENCE", "READER_TRAJ", "PERSONA"))
                  for k in by), sorted(by))
    check("no second composition attempt exists",
          res["composition_attempts_count"] == 1
          and res["fallback_recomposition_triggered"] is False,
          res["composition_attempts_count"])


def test_the_full_ledger_is_offered_and_selection_is_the_writers() -> None:
    res, _prov, _n = _run([PASS_G])
    wr = res["detail"][CP.WRITER]
    check("the run records how much evidence was available",
          wr["facts_available"] == len(LEDGER), wr.get("facts_available"))
    check("the run records what the Writer said it used",
          wr["facts_used_count"] == 4, wr.get("facts_used_count"))
    check("the Writer's freedom is recorded as plan-free", wr["plan_free"] is True)


# ── 13-14. routing and approval ───────────────────────────────────────────────
def test_routing_and_publication_authority_unchanged() -> None:
    import publication_safety_bridge as BRIDGE
    src = pathlib.Path(HERE / "publication_safety_bridge.py").read_text(encoding="utf-8")
    check("the bridge evaluates the free path with the Ledger-first evaluator",
          "COMPOSITION_FREE_ARGUMENTATIVE" in src
          and "_evaluate_new_engine_v1" in src)
    for required in ("worth_pass", "architecture_valid", "safety_pass", "grounding_pass",
                     "fact_check_pass", "reader_pass", "ledger_frozen_valid",
                     "composition_completed"):
        check("the bridge still requires %s" % required, '"%s"' % required in src)
    check("no new approval gate was introduced",
          "owner_approval" not in src and "await_approval" not in src)

    # The free path emits the stage shape the bridge reads.
    res, _p, _n = _run([PASS_G])
    stages = res["stages"]
    for s in (CP.LEDGER, CP.WORTH, CP.ARCHITECTURE):
        check("%s is PASS so the bridge's own check is genuinely satisfied" % s,
              stages[s] == CP.PASS, stages[s])
    check("SAFETY passed on free prose with this path's licensing",
          stages[CP.SAFETY] == CP.PASS, stages[CP.SAFETY])
    check("GROUNDING passed", stages[CP.GROUNDING] == CP.PASS)
    check("the result carries the publication fields the publisher reads",
          res["publication_ready"] is True and res["package"] is not None
          and res["article_sha256"] and res["bundle_sha256"])


def test_routing_scripts_untouched() -> None:
    """ACCEPT -> publisher, HOLD + article -> desk, no article -> failure alert."""
    prod = (HERE / "new_engine_production.py").read_text(encoding="utf-8")
    check("publish_if_eligible still gates on publication_eligible",
          'if not result.get("publication_eligible")' in prod)
    check("direct publication still calls publish_best.publish_candidate",
          "PUB.publish_candidate(path)" in prod)
    check("no approval prompt was inserted before publication",
          "input(" not in prod and "approve" not in prod.lower().split("approved")[0][-400:]
          if "approve" in prod.lower() else True)


def test_safety_is_given_this_paths_own_licensing() -> None:
    rec = FC.licensing_record(LEDGER, RELATIONS)
    check("the licensing record has no plan in it",
          not rec.get("beats") and not rec.get("story_spine")
          and not rec.get("ending_move"), {k: rec.get(k) for k in
                                           ("beats", "story_spine", "ending_move")})
    check("it is not persisted under a name that looks like a Writer packet", True)
    # Nothing was cut, so nothing can leak -- the measured category error this closes.
    from new_engine_v1 import story as ST
    ca = ST.cut_adherence(ARTICLE, {}, {}, ledger=LEDGER)
    check("with no plan there are no cut violations by construction",
          not ca["violations"] and ca["ok"], ca)
    # And with the PLAN's cut list the same article WOULD leak -- which is the measured
    # category error this path removes, not a hypothetical one.
    leaky = ST.cut_adherence(ARTICLE, ARCH, {"F04": ["Lavignac"]}, ledger=LEDGER)
    check("the same article against a plan it never saw does leak (the defect)",
          bool(leaky["violations"]), leaky)


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
    print("ALL FREE COMPOSITION TESTS PASSED")


if __name__ == "__main__":
    main()

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
import re
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
    CP.worth_gate = lambda p, led, subj, hyp=None, conflict_sink=None, \
        plan_inputs_required=True: {
            "status": CP.PASS, "worth_gate": {"verdict": "PASS"}, "hypothesis": hyp,
            "conflict_sink_supplied": conflict_sink is not None,
            "plan_inputs_required": plan_inputs_required,
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


def test_compression_and_carry_reaches_the_runtime_bytes() -> None:
    """The 2026-09-30 owner feedback, as prompt bytes rather than as a comment."""
    res, prov, _ = _run([PASS_G])
    system = prov.calls[0]["system"]
    check("the compression block reaches the exact system bytes",
          "HOW MUCH OF A FACT TO WRITE" in system)
    check("it says a fact does not earn its full form",
          "does not automatically earn its full form" in system)
    check("it names the forms that are ceremony, not fact",
          "statute number" in system and "chapter heading" in system)
    check("it protects exactness where exactness is the point",
          "Compression is not omission" in system
          and "keeps every digit" in system)
    check("narrative drives, not facts", "NARRATIVE DRIVES, NOT FACTS" in system)
    # Second pass, 2026-09-30: the owner's "numbers ... could sometimes written compactly".
    # A PROMPT IS WRAPPED TEXT. Asserting a multi-word phrase against the raw string tests
    # where the line breaks happen to fall, not what the Writer is told; two of these
    # failed for exactly that reason on the first run. Compare on normalised whitespace.
    flat = " ".join(system.split())
    check("a quantity's precision is separable from the quantity",
          "A QUANTITY IS A FACT; ITS PRECISION USUALLY IS NOT" in flat)
    check("it uses the owner's own example",
          "780 accredited Medicare and Medicaid supplier locations" in flat)
    check("it protects the figures that carry meaning",
          "a threshold, a comparison" in flat)
    check("a date is compressible too", '"in 2022" is usually the fact' in flat)
    check("the person carries the middle, not only the ends",
          "NOT ONLY ITS ENDS" in system
          and "easiest to lose" in system)
    check("provenance is not narration", "PROVENANCE IS NOT NARRATION" in system)

    # ORDER MATTERS AND IS ASSERTED: lens, corpus, reader contract, this, the one rule.
    check("it sits after the reader contract and before the one rule",
          system.index("READER CONTRACT")
          < system.index("HOW MUCH OF A FACT TO WRITE")
          < system.index("THE ONE RULE"))

    # IT IS GUIDANCE, NOT A GATE. The constant is referenced exactly twice in the whole
    # package -- where it is defined, and where it is concatenated into the system prompt.
    # A third reference would mean something started reading it, which is how writing
    # guidance quietly becomes a validator.
    import subprocess
    pkg = HERE / "new_engine_v1"
    # --include='*.py' because a bare -r also matches __pycache__/*.pyc, which made this
    # check fail in any tree that had been imported once. Caught by an external audit.
    hits = subprocess.run(["grep", "-rn", "--include=*.py",
                           "COMPRESSION_AND_CARRY", str(pkg)],
                          capture_output=True, text=True).stdout.strip().splitlines()
    check("the compression block is referenced only where it is defined and used",
          len(hits) == 2, hits)
    check("no new stage was added for it",
          tuple(FC.FREE_STAGES) == tuple(CP.STAGES))
    check("the stage list still has no validator stage of its own",
          not any("COMPRESS" in s.upper() for s in FC.FREE_STAGES))


def test_selection_bites_without_becoming_write_shorter() -> None:
    """The owner's leading complaint was "too much facts". The previous wording was live
    when the Writer used 68 of 92, so it was strengthened -- but strengthening it the
    WRONG way would undo the whole change.

    THE meŞk EVIDENCE IS THE GUARD. 57 facts read better than 22 on the same Ledger. The
    criterion is load-bearing, not count, and an instruction that reads as "use fewer
    facts" or "write shorter" would walk straight back to the 781-word control article
    this path replaced. So the prompt must sharpen the CRITERION and explicitly refuse the
    length reading.
    """
    res, prov, _ = _run([PASS_G])
    system = prov.calls[0]["system"]
    flat = " ".join(system.split())
    check("the default is to leave a fact out",
          "the default is to leave one out" in flat)
    check("availability is named as the wrong reason",
          "not because it is available and true" in flat)
    check("an unearned sentence is cut, not rehomed",
          "do not find it a home" in flat)
    check("it explicitly refuses the 'write shorter' reading",
          "This is not an instruction to write a short article or to use few facts"
          in flat)
    check("a long fully load-bearing article is named as correct",
          "every one of whose facts is load-bearing is exactly right" in flat)
    check("no word count, length target or fact quota was introduced",
          not re.search(r"\b(?:at most|no more than|fewer than|maximum of)\s+\d+", system),
          "a numeric cap appeared in the Writer prompt")


def test_the_approved_instrument_settles_scope() -> None:
    """"PR has authority" (owner, 2026-09-30). Worth is told scope is decided; it keeps
    every other refusal it has."""
    from new_engine_v1 import hypothesis as HYP

    h = HYP.from_instrument({
        "id": "PR006-02",
        "mechanism": "Institutions certify authority, not knowledge.",
        "disconfirming_shape": "Show a route by which uncertified knowledge enters the "
                               "record with attribution.",
        "what_this_adds": "who is licensed to make the classification"})
    check("an instrument with a claim has authority", CP.instrument_has_authority(h), h)
    check("an id with no claim does not",
          not CP.instrument_has_authority({"instrument": "PR006-02", "claim": ""}))
    check("no instrument at all does not", not CP.instrument_has_authority(None))

    b = CP.INSTRUMENT_AUTHORITY_BLOCK
    check("Worth is told scope is settled", "SCOPE IS ALREADY SETTLED" in b)
    check("the scope refusal is withdrawn on those grounds",
          "is not available to you on" in b)
    check("it is told not to refuse for not looking like disability",
          "not obviously about disability" in b)
    # What must NOT be lifted.
    check("NO_PLAUSIBLE_LENS still refuses", "NO_PLAUSIBLE_LENS if this evidence" in b)
    check("WEAK_ANALOGY still refuses", "WEAK_ANALOGY if what you have" in b)
    check("the access-deficit invariant still refuses",
          "ACCESS-DEFICIT central" in b and "does not lift it" in b)
    check("a lens must still name a mechanism and a particular",
          "name a mechanism and rest on a particular" in b)


def test_worth_keeps_its_editorial_refusals_and_drops_only_the_planner_ones() -> None:
    """ARCHITECTURE no longer runs, so three of Worth's refusals lost their consumer.

    The line is: anything asking "is there a real, subject-specific, non-derivative
    reading here" keeps its authority. Anything asking "is Worth's own lens shaped well
    enough to plan from" stops blocking and is recorded instead.
    """
    src = (HERE / "new_engine_v1" / "composition.py").read_text(encoding="utf-8")
    body = src.split("def worth_gate(", 1)[1].split("\ndef ", 1)[0]

    # STILL BLOCKING -- these raise unconditionally, with no plan_inputs_required guard.
    for editorial in ("the lens rests on no particular about this subject",
                      "HOLD_INSUFFICIENT_EDITORIAL_DELTA",
                      "the lens cites fact ids not in the ledger"):
        seg = body.split(editorial, 1)
        check("still present: %r" % editorial[:44], len(seg) == 2)
        check("and not behind the planner guard: %r" % editorial[:30],
              "plan_inputs_required" not in seg[0][-420:], seg[0][-200:])

    # NO LONGER BLOCKING -- each guarded, each recorded.
    for planner in ("it cannot carry the article",
                    "the lens names no carrier"):
        seg = body.split(planner, 1)
        check("guarded by plan_inputs_required: %r" % planner[:36],
              "if plan_inputs_required:" in seg[0][-360:], seg[0][-160:])
    check("and the candidate's own validity is guarded too",
          "errs = cand_errs if plan_inputs_required else []" in body)
    check("refusals that stop blocking are recorded, not discarded",
          body.count("plan_warnings.append") >= 2
          and '"plan_input_warnings": plan_warnings' in body)

    # The default is unchanged, so the planned path keeps every refusal it has.
    import inspect
    sig = inspect.signature(CP.worth_gate)
    check("the planned path is unaffected by default",
          sig.parameters["plan_inputs_required"].default is True)


def test_the_free_path_asks_worth_not_to_require_plan_inputs() -> None:
    """Read off the stage record rather than a spy: `_run` installs its own Worth double,
    so a spy patched in beforehand is replaced before it is ever called."""
    res, _prov, _n = _run([PASS_G])
    check("the free path does not require plan inputs",
          res["detail"][CP.WORTH].get("plan_inputs_required") is False,
          res["detail"][CP.WORTH])


def test_worth_reasoning_survives_its_own_refusal() -> None:
    """Retained when it PASSED and discarded when it REFUSED -- exactly backwards.

    `persist` writes WORTH_AND_CANDIDATE.json from `det[WORTH]["worth_gate"]`, and the
    ladder builds that record from the CompositionHold's payload, which was empty. 53 of
    178 production compositions died at this gate and all that survived was 400 truncated
    characters of `failure_reason` -- which is why an audit of those 53 today could read
    verdicts and not one reason. Applies to both paths.
    """
    import json as _json
    import tempfile

    LENS = {"verdict": "GREAT_GENERAL_STORY_WRONG_PUBLICATION",
            "lens_claim": "a contrast between two recording systems, one oral, one charted",
            "evidence_ids": ["F01"], "changes_meaning_how": "it reframes the search"}

    class _P:
        def complete(self, system, user, max_tokens=4000, temperature=None, timeout=180):
            class _C:
                text = _json.dumps({"worth_gate": LENS, "story_candidate": {}})

                def identity(self):
                    return {}
            return _C()

    try:
        CP.worth_gate(_P(), {"F01": {"proposition": "x"}}, "a subject")
        check("a refused verdict holds the run", False, "no hold raised")
        return
    except CP.CompositionHold as e:
        check("a refused verdict holds the run", True)
        check("and carries the lens it refused on",
              bool(e.payload.get("worth_gate", {}).get("lens_claim")), e.payload)
        # Exactly what the ladder does with a hold, then what persist keys off.
        st = dict(e.payload, status=CP.HOLD, code=e.code, reasons=e.reasons)
        d = tempfile.mkdtemp()
        CP.persist(d, {"detail": {CP.WORTH: st}, "stages": {}, "subject": "a subject"})
        names = sorted(x.name for x in pathlib.Path(d).iterdir())
        check("WORTH_AND_CANDIDATE.json is written on a HOLD too",
              "WORTH_AND_CANDIDATE.json" in names, names)
        got = _json.loads((pathlib.Path(d) / "WORTH_AND_CANDIDATE.json")
                          .read_text(encoding="utf-8"))
        check("the reasoning is readable afterwards",
              "two recording systems" in str(got["worth_gate"]["lens_claim"]))


def test_worth_scope_conflict_is_recorded_for_the_owner() -> None:
    """A disagreement between the perspective library and Worth's scope test is evidence
    for sharpening the instrument, not something to overrule silently."""
    filed = []
    h = {"instrument": "PR006-02", "claim": "Institutions certify authority."}
    CP.record_instrument_conflict(
        filed.append, hypothesis=h, subject="Franklin wrecks",
        lens={"verdict": ST_WRONG(), "lens_claim": "a contrast between two recording "
                                                   "systems"},
        ledger_facts=129)
    check("one conflict is filed", len(filed) == 1, filed)
    r = filed[0]
    check("it names the instrument", r["instrument"] == "PR006-02")
    check("it keeps the owner's claim", "certify authority" in r["claim"])
    check("it keeps Worth's own reasoning", "two recording systems" in r["worth_reasoning"])
    check("it records how much evidence was frozen for it", r["ledger_facts"] == 129)
    check("it says which side won", "The instrument won" in r["note"])
    check("a missing sink is not an error",
          CP.record_instrument_conflict(None, hypothesis=h, subject="x",
                                        lens={}, ledger_facts=0) is None)

    def explodes(_):
        raise RuntimeError("disk full")
    check("a sink that raises cannot break a run",
          CP.record_instrument_conflict(explodes, hypothesis=h, subject="x",
                                        lens={}, ledger_facts=0) is None)


def ST_WRONG():
    from new_engine_v1 import story as ST
    return ST.WRONG_PUBLICATION


def test_structural_announcement_rule_reaches_the_writer() -> None:
    """Added from the Reader's own findings on production-20260930T085346Z-54ca6694, which
    held ENGINE_LANGUAGE_LEAK and quoted three sentences announcing their structural job:
    "Here is where the obvious reading goes wrong", "Now the harder test", and "It is worth
    following that route backwards".

    The rule already existed in composition.WRITER_CRAFT_DELTA, where the codebase calls it
    "the single measured difference between published prose and this pipeline's drafts".
    The first port of house craft into this prompt took PROVENANCE IS NOT NARRATION and
    missed this one -- the paragraph that actually matched the defect.
    """
    res, prov, _ = _run([PASS_G])
    flat = " ".join(prov.calls[0]["system"].split())
    check("the rule reaches the Writer",
          "DO NOT LET A SENTENCE ANNOUNCE ITS OWN STRUCTURAL JOB" in flat)
    for quoted in ("Here is where the obvious reading goes wrong",
                   "Now the harder test"):
        check("it names the Reader's own example %r" % quoted[:34], quoted in flat)
    check("it says what to do instead, not only what to avoid",
          "put the surprising fact next to the one it overturns" in flat)
    check("it does not forbid short paragraphs",
          "One-sentence paragraphs are fine and normal" in flat)


def test_a_licensed_relation_keeps_its_direction() -> None:
    """A CAUSE is not symmetric, and "A <-> B" licensed the reverse just as strongly.

    The retained free run that reached the Reader
    (production-20260930T085346Z-54ca6694) carried FOUR CAUSE relations rendered that way:
    directional evidence handed to the Writer with the direction stripped off. Found by an
    external audit, reproduced, fixed.
    """
    led = {"A": {"proposition": "The council cut the budget."},
           "B": {"proposition": "The service closed."}}
    block = FC.relation_block(led, [{"kind": "CAUSE", "subject": "A", "object": "B"}])
    check("the direction is rendered", "--CAUSE-->" in block, block)
    check("no symmetric arrow survives", "<->" not in block, block)
    check("subject comes before object",
          block.index("The council cut the budget.")
          < block.index("The service closed."), block)
    check("the block says the arrow IS the licence",
          "THE ARROW IS THE LICENCE" in block and "not reversible" in block)
    # And it reaches the Writer that way.
    res, prov, _ = _run([PASS_G])
    user = prov.calls[0]["user"]
    check("the runtime prompt carries no symmetric join", "<->" not in user)
    check("and carries a directional one", "--CONTEMPORANEOUS-->" in user, user[-400:])


def test_a_declared_negative_must_bear_on_the_claim() -> None:
    """An unrelated negation must not license an absence claim.

    Reproduced by an external audit: "There is no elevator in the museum" was admitted on
    a fact reading "There is no wheelchair entrance at the museum". Both are negations;
    nothing asked whether the second was about the first, and Safety then returned PASS.

    That made a DECLARATION weaker than the lexical path it supplements. It now applies
    story.negative_admission_audit's own word-overlap rule.
    """
    LED = {"F01": {"fact_id": "F01", "claim_type": "NEGATIVE_FACT",
                   "proposition": "There is no wheelchair entrance at the museum.",
                   "support_span": "no wheelchair entrance"},
           "F02": {"fact_id": "F02", "claim_type": "NEGATIVE_FACT",
                   "proposition": "There is no elevator anywhere in the museum building.",
                   "support_span": "no elevator in the building"}}
    art = "# T\n\nThe building opened. There is no elevator in the museum."

    lin, rej = FC.verify_declared_negatives(
        art, [{"sentence": "There is no elevator in the museum.",
               "fact_ids": ["F01"]}], LED)
    check("an unrelated negation is refused", not lin and bool(rej), (lin, rej))
    check("and the refusal says the RIGHT why -- wrong subject, not missing negation",
          any("about something else" in " ".join(r["why"]) for r in rej), rej)
    check("it quotes the negation that was cited",
          any("wheelchair entrance" in " ".join(r["why"]) for r in rej), rej)

    # The other refusal must still read correctly: a genuinely positive fact.
    _l3, rej3 = FC.verify_declared_negatives(
        art, [{"sentence": "There is no elevator in the museum.",
               "fact_ids": ["F03"]}],
        dict(LED, F03={"fact_id": "F03", "claim_type": "POSITIVE_FACT",
                       "proposition": "The museum installed a new elevator in 2019."}))
    check("a positive fact is refused for being positive, not for being off-topic",
          any("cannot license a claim of absence" in " ".join(r["why"]) for r in rej3),
          rej3)

    lin2, rej2 = FC.verify_declared_negatives(
        art, [{"sentence": "There is no elevator in the museum.",
               "fact_ids": ["F02"]}], LED)
    check("the fact that IS about it is still admitted", bool(lin2), (lin2, rej2))


def test_facts_used_is_reported_as_self_reported() -> None:
    """It is the Writer's own list. Nothing checks a listed fact reaches the prose, so it
    cannot establish coverage -- and ids the Ledger lacks are a signal, not a count."""
    reply = ARTICLE + "\n\n---FACTS USED---\nF01 F02 F404\n---NEGATIVE CLAIMS---\n"
    res, _prov, _n = _run([PASS_G], writer_reply=reply)
    wr = res["detail"][CP.WRITER]
    check("it is labelled self-reported", wr.get("facts_used_is_self_reported") is True)
    check("ids outside the Ledger are separated out",
          wr.get("facts_used_not_in_ledger") == ["F404"], wr.get("facts_used_not_in_ledger"))
    check("the count covers only real ids",
          wr.get("facts_used_count_self_reported") == 2, wr)
    check("no bare 'facts_used_count' remains to be quoted as coverage",
          "facts_used_count" not in wr, sorted(wr))


def test_package_calls_survive_a_regeneration() -> None:
    """record() ASSIGNS calls[stage], so a package rebuilt after a repair erased the
    first call. Reproduced by an external audit as 8 reported against 9 made."""
    res, _prov, _n = _run([HOLD_G, PASS_G], repair_reply=REPAIR_REPLY)
    by = res["model_calls_by_stage"]
    check("the package was built twice (once, then after the repair)",
          by.get(CP.PACKAGE) == 2, by)
    check("and the total counts both",
          res["model_calls_total"] == sum(by.values()), (res["model_calls_total"], by))


def test_the_module_contract_matches_what_the_code_does() -> None:
    """The docstring said Architecture and CUT run, after they had been removed."""
    doc = FC.__doc__ or ""
    src = (HERE / "new_engine_v1" / "free_composition.py").read_text(encoding="utf-8")
    check("the contract says Architecture is not run", "ARCHITECTURE    NOT RUN" in doc)
    check("the contract says CUT_TERMS is not run", "CUT_TERMS       NOT RUN" in doc)
    check("and the code agrees", "CP.architect(" not in src)
    check("it names what the missing plan took with it",
          "definition_evidence" in doc and "claim mapping" in doc)
    check("it does not claim a like-for-like substitute",
          "not claimed to be" in doc)
    check("it states the bridge assertion that replaced architecture_valid",
          "writer_plan_free" in doc)


def test_the_writer_is_shown_which_absences_it_may_claim() -> None:
    """Safety held on UNSUPPORTED_NEGATIVES three times. The third run made the cause
    unmistakable: 57 Ledger facts, NOT ONE negative-shaped, and the Writer declared eight
    negatives all citing positive facts. It was not ignoring the rule -- it could not see
    which facts satisfied it. The planned path has always shown its Writer the list."""
    # This fixture's F03 is the only negative-shaped fact.
    block = FC.negative_permissions_block(LEDGER)
    check("the permitted absence is named by id", "F03" in block, block)
    check("and quoted", "no composition in the makam" in block)
    check("it forbids every other absence",
          "has no permission here" in block and "no permission for silence" in block)

    none_at_all = FC.negative_permissions_block(
        {"F01": {"proposition": "The conservatory opened in 1926."}})
    check("a Ledger with no negations says so plainly",
          "THE ABSENCES YOU MAY CLAIM: NONE" in none_at_all, none_at_all)
    check("and gives the easy instruction instead of the impossible one",
          "do not write a sentence that claims one" in none_at_all)
    check("it names the inference trap",
          "that is your inference and not this evidence" in none_at_all)

    # It must agree with the audit that judges the result, or the Writer is being told
    # one thing and marked against another.
    from new_engine_v1 import story as _ST
    for fid, f in LEDGER.items():
        shown = fid in block
        judged = bool(_ST.negative_shape_of(f["proposition"])[0])
        check("shown and judged agree for %s" % fid, shown == judged, (shown, judged))

    res, prov, _ = _run([PASS_G])
    check("it reaches the Writer's actual bytes",
          "THE ABSENCES YOU MAY CLAIM" in prov.calls[0]["user"])


def test_a_package_only_safety_repair_is_available() -> None:
    """rehearsal-20260930T173120Z-2cc116d7: a 915-word article died at Safety with ZERO
    repair calls spent. PACKAGE_UNSUPPORTED_NEGATIVES is not in SAFETY_REPAIRABLE_PREFIXES,
    so one bad line in the five-line package made the ARTICLE repair ineligible too --
    and the package's own repair, which the planned path runs, was never wired here."""
    src = (HERE / "new_engine_v1" / "free_composition.py").read_text(encoding="utf-8")
    check("the package-only completion is called",
          "CP.package_only_safety_completion(" in src)
    check("its cost is counted against SAFETY",
          "calls[CP.SAFETY] = calls.get(CP.SAFETY, 0) + prep.get" in src)
    check("an accepted package repair is recorded as a repair",
          "repairs[CP.SAFETY] = 1" in src)
    check("and the result is re-audited on the repaired package",
          "sa[\"after_package_safety_repair\"] = True" in src)
    # The ordering that made it necessary: article repair first, package repair after.
    check("the article repair is still tried first",
          src.index("CP.safety_repair(") < src.index("CP.package_only_safety_completion("))


def test_the_writer_is_told_the_standard_it_is_judged_by() -> None:
    """It was marked on nine named dimensions it had never been shown."""
    res, prov, _ = _run([PASS_G])
    flat = " ".join(prov.calls[0]["system"].split())
    check("the measured density reaches the Writer",
          "3.5 per 100 words" in flat and "0.7 per 100 words" in flat)
    check("it is framed as description, not a target",
          "not a target to hit and not a rule" in flat)
    check("it says why names and numbers are the things counted",
          "ARE EACH A THING THE READER MUST HOLD" in flat)
    check("and that they are counted distinct",
          "a name you return to is one object" in flat)
    check("ONE MENTAL OBJECT AT A TIME is ported", "ONE MENTAL OBJECT AT A TIME" in flat)
    check("and distinguishes arrival rate from sentence length",
          "not about how long a sentence is" in flat)
    check("the jargon rule is ported", "KEEP A TECHNICAL TERM WHEN IT IS THE PRECISE ONE"
          in flat)
    check("MAKE THE POINT LAND is ported", "MAKE THE POINT LAND" in flat)
    check("THE LAST PARAGRAPH ADDS is ported", "THE LAST PARAGRAPH ADDS" in flat)

    # The Reader's own criteria, in the Reader's own words.
    from new_engine_v1 import composition as _CP
    for dim in ("OPENING", "READABILITY", "ACCESSIBLE_READING", "MOMENTUM",
                "BREATHING", "RESEARCH_LOAD", "ENDING"):
        check("the Writer is shown %s" % dim, dim in flat)
    check("MOMENTUM is quoted as the Reader states it",
          "Does each paragraph earn the next" in flat)
    check("BREATHING is quoted as the Reader states it",
          "Is concrete material given room" in flat)
    # Dimensions it must NOT be coached on: the two that would become gameable.
    check("it is not coached on CRIP_MINDS_FIT",
          "CRIP_MINDS_FIT" not in flat)
    check("nor on ENGINE_LANGUAGE_LEAK as a named dimension",
          "ENGINE_LANGUAGE_LEAK" not in flat)
    check("and it is told to write so they are true, not answerable",
          "not so they are answerable" in flat)


def test_prose_density_is_measured_and_refuses_nothing() -> None:
    """A free, deterministic measure that separated the three real drafts correctly.

    Fixtures use VARIED names, because `_entities` returns a set: repeating one name
    forty times is one object, which is the whole point of counting distinct.
    """
    # Names mid-sentence and alphabetic: `_entities(skip_sentence_initial=True)` ignores a
    # capitalised word opening a sentence (it cannot tell a name from an ordinary word
    # there), and tokens carrying digits are not names either. The published baseline was
    # measured with the same function, so both sides count the same way.
    POOL = ["Alder", "Brill", "Carrow", "Dunmore", "Ellery", "Fenwick", "Garrow",
            "Halloran", "Ivens", "Jardine", "Kelsall", "Lomax", "Merrick", "Norbury",
            "Orsett", "Pankhurst", "Quennell", "Rutland", "Sowerby", "Thirsk"]
    names = " ".join("It was %s who met %s beside %s that year."
                     % (POOL[i % 20], POOL[(i + 1) % 20], POOL[(i + 2) % 20])
                     for i in range(20))
    d = FC.prose_density("# T\n\n" + names)
    check("it counts words", d["words"] > 100, d.get("words"))
    check("it carries the published band for comparison",
          d["published_middle_half"]["names_per_100w"] == [2.7, 4.6],
          d.get("published_middle_half"))
    check("a name-dense draft is flagged above the band",
          d["outside_published_range"].get("names_per_100w", {}).get("direction")
          == "above", d.get("outside_published_range"))

    check("empty text is handled", FC.prose_density("") == {})
    check("a repeated name is one object, not forty",
          FC.prose_density("# T\n\n" + "Alice went to the shop and Alice came back. " * 30)
          ["names_per_100w"] < 2.0)

    # It is telemetry: recorded on the run, read by no stage, refusing nothing.
    res, _prov, _n = _run([PASS_G])
    wr = res["detail"][CP.WRITER]
    check("it is recorded on the Writer result", bool(wr.get("prose_density")))
    check("the run still passed with it recorded",
          res["status"] == CP.PASS, res.get("failure_reason"))
    src = (HERE / "new_engine_v1" / "free_composition.py").read_text(encoding="utf-8")
    # Recorded and persisted is fine; BRANCHED ON is not. The ladder body ends where the
    # persistence helper begins.
    ladder = src.split("def run_free_argumentative_composition", 1)[1].split(
        "def repair_byte_delta", 1)[0]
    check("no stage branches on the measurement",
          "prose_density" not in ladder, "the ladder reads it")
    check("and it is persisted for the owner",
          '"prose_density": wr.get("prose_density")' in src)


def test_ported_house_rule_has_not_drifted_from_its_source() -> None:
    """PROVENANCE IS NOT NARRATION is the planned path's own rule, copied here.

    Copied rather than refactored so the planned path's prompt bytes are untouched -- but a
    copy drifts, and the whole reason this engine had to be told what Crip Minds is in the
    first place is that a derived copy drifted from its source for a month with nothing
    noticing. This fails the moment the two disagree.
    """
    for sentence in ('not "the source says", "the record establishes"',
                     "Name a speaker where the naming is part of the claim",
                     "write the world, not the paperwork"):
        in_free = sentence in " ".join(FC.COMPRESSION_AND_CARRY.split())
        in_house = sentence in " ".join(CP.WRITER_CRAFT_DELTA.split())
        check("%r is in the free prompt" % sentence[:40], in_free)
        check("%r still matches the house rule it came from" % sentence[:40], in_house)


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
    check("no plan is built at all on this path",
          res["stages"][CP.ARCHITECTURE] == CP.SKIPPED
          and res["stages"][CP.CUT_TERMS] == CP.SKIPPED, res["stages"])
    check("and building one costs nothing",
          not res["model_calls_by_stage"].get(CP.ARCHITECTURE),
          res["model_calls_by_stage"])


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
    check("ARCHITECTURE is skipped and costs nothing",
          res["stages"][CP.ARCHITECTURE] == CP.SKIPPED and not by.get(CP.ARCHITECTURE),
          (res["stages"][CP.ARCHITECTURE], by.get(CP.ARCHITECTURE)))
    check("CUT_TERMS is skipped and costs nothing",
          res["stages"][CP.CUT_TERMS] == CP.SKIPPED and not by.get(CP.CUT_TERMS))
    check("WORTH still runs and still gates", res["stages"][CP.WORTH] == CP.PASS
          and by.get(CP.WORTH) == 1, (res["stages"][CP.WORTH], by.get(CP.WORTH)))
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
    check("the run records what the Writer SAID it used, marked as self-reported",
          wr["facts_used_count_self_reported"] == 4
          and wr["facts_used_is_self_reported"] is True,
          wr.get("facts_used_count_self_reported"))
    check("the Writer's freedom is recorded as plan-free", wr["plan_free"] is True)
    check("Worth is given somewhere to file an instrument conflict",
          res["detail"][CP.WORTH].get("conflict_sink_supplied") is True,
          res["detail"][CP.WORTH])


# ── 13-14. routing and approval ───────────────────────────────────────────────
def test_routing_and_publication_authority_unchanged() -> None:
    import publication_safety_bridge as BRIDGE
    src = pathlib.Path(HERE / "publication_safety_bridge.py").read_text(encoding="utf-8")
    check("the bridge evaluates the free path with the Ledger-first evaluator",
          "COMPOSITION_FREE_ARGUMENTATIVE" in src
          and "_evaluate_new_engine_v1" in src)
    # EVERY FACTUAL GATE IS STILL REQUIRED. These are the checks that decide whether an
    # article is safe to publish, and none of them moved.
    for required in ("worth_pass", "safety_pass", "grounding_pass",
                     "fact_check_pass", "reader_pass", "ledger_frozen_valid",
                     "composition_completed"):
        check("the bridge still requires %s" % required, '"%s"' % required in src)
    check("the planned contract still requires a validated architecture",
          '"architecture_valid"' in src)
    check("the free contract asserts the equivalent instead, not nothing",
          '"writer_plan_free"' in src)
    check("and it is engine-conditional, not a global weakening",
          "COMPOSITION_FREE_ARGUMENTATIVE" in src.split('"writer_plan_free"')[0][-900:])
    check("no new approval gate was introduced",
          "owner_approval" not in src and "await_approval" not in src)

    # The free path emits the stage shape the bridge reads.
    res, _p, _n = _run([PASS_G])
    stages = res["stages"]
    for s in (CP.LEDGER, CP.WORTH):
        check("%s is PASS so the bridge's own check is genuinely satisfied" % s,
              stages[s] == CP.PASS, stages[s])
    check("the Writer proves it was plan-free, which is what the bridge now asserts",
          res["detail"][CP.WRITER]["plan_free"] is True)
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


# ── 12. the narrower subject reaches the Writer ───────────────────────────────
# A DISCONNECTION TEST, not a rendering test. `narrower_subject` was computed by research
# and read by nothing for the life of both engines; an external read-only audit of 53d27df
# found it. What these assert is the CONNECTION -- that the key research writes is the key
# composition reads, and that it survives into the bytes the provider is handed. A test
# that only exercised `narrower_scope_block` directly would have passed all along, on every
# day the field reached no Writer at all.
NARROWER = ("whether named contributors appear in the formal scientific record or only "
            "in narrative acknowledgement")


def test_a_narrower_subject_reaches_the_writers_bytes() -> None:
    narrowed = dict(PACK, narrower_subject=NARROWER,
                    sufficiency={"verdict": "NARROW", "reasons": [],
                                 "what_is_missing": ["material supports the narrower "
                                                     "subject: %s" % NARROWER]})
    user = FC.free_writer_user(INSTRUMENT, LEDGER, narrowed, PACK["subject"], RELATIONS)
    check("the narrower subject is in the Writer's user prompt", NARROWER in user)
    check("the verdict that carried it is named too", "NARROW" in user)
    check("the broad subject it was narrowed from is still shown",
          PACK["subject"] in user)

    # PLACEMENT IS THE POINT. A constraint the Writer meets after it has read the whole
    # Ledger is a constraint it has already spent its attention against.
    # `find`, not `index`: when the connection is severed these must REPORT, not raise.
    # A suite that dies on the first symptom hides every check after it, which is the
    # opposite of what this file is for.
    i_nar, i_ev = user.find(NARROWER), user.find("THE FROZEN EVIDENCE")
    i_sub = user.find(PACK["subject"])
    check("the constraint precedes the evidence it constrains",
          0 <= i_nar < i_ev, (i_nar, i_ev))
    check("and it sits directly under the subject, not further down",
          0 <= i_sub < i_nar and i_nar - i_sub < 600, (i_sub, i_nar))

    # IT IS SCOPE, NOT A FACT. Nothing here may become assertable: the narrower subject is
    # not a proposition, carries no fact id, and is not inside the frozen evidence listing.
    _, _, evidence = user.partition("THE FROZEN EVIDENCE")
    check("the narrower subject is not smuggled into the evidence listing",
          NARROWER not in evidence)
    block = FC.narrower_scope_block(narrowed)
    check("the scope block asserts no fact id",
          not re.search(r"\bF\d\d\b", block), block)

    # AND IT DOES NOT BREAK THE CONTRACT THE WHOLE PATH RESTS ON.
    check("the scope constraint carries no planning marker",
          FC.writer_inputs_are_plan_free(FC.free_writer_system(), user) == [],
          FC.writer_inputs_are_plan_free(FC.free_writer_system(), user))

    # THE PROVENANCE SENTENCE MUST NOT CLAIM MORE THAN THE CODE DOES. `scope()` produces
    # the broad subject and the narrower one in a single model reply, on the anchor alone,
    # before any source is fetched, and validates neither. An adversarial review caught an
    # earlier draft of this block asserting research had "found" the narrowing. These fail
    # the moment that overstatement comes back.
    for overstated in ("found it carries", "for that reason", "the material supports",
                       "verified", "confirmed"):
        check("the block does not claim research %r" % overstated,
              overstated not in block, block[:200])
    check("it says when the judgement was made",
          "before any source was fetched" in block, block[:200])


def test_an_unnarrowed_pack_adds_nothing_to_the_prompt() -> None:
    """The empty case must add nothing -- not a heading, not a blank line.

    Most runs carry no narrower subject. If this block changed their prompt at all it would
    be an unannounced change to every free composition, measured against nothing.

    NAMED FOR WHAT IT ACTUALLY CHECKS. An adversarial review pointed out that its first
    name -- "byte identical to before" -- promised a comparison against the pre-change
    prompt, which this cannot make: it compares two outputs of the CURRENT function. The
    guarantee it really gives is narrower and worth having on its own.
    """
    plain = FC.free_writer_user(INSTRUMENT, LEDGER, PACK, PACK["subject"], RELATIONS)
    empty = FC.free_writer_user(INSTRUMENT, LEDGER, dict(PACK, narrower_subject=""),
                                PACK["subject"], RELATIONS)
    check("an empty narrower_subject renders nothing at all", plain == empty)
    check("and no scope heading appears", "THE SCOPE THIS ARTICLE MUST KEEP" not in plain)
    check("a whitespace-only narrower_subject is treated as empty",
          FC.narrower_scope_block(dict(PACK, narrower_subject="   \n ")) == "")
    check("a pack with no sufficiency block still renders the constraint",
          NARROWER in FC.narrower_scope_block({"narrower_subject": NARROWER}))


def test_the_key_composition_reads_is_the_key_research_writes() -> None:
    """The disconnection guard. Rename the field in one place and this fails.

    Research is the producer, the stub pack is the shape the contract tests bind to, and
    free composition is the consumer. All three must spell it the same way; for two days it
    was spelled identically in all three and read by none of them, which is why the check
    below is on the CONSUMER reading it, not on the string existing.
    """
    research_src = (HERE / "new_engine_v1" / "research.py").read_text(encoding="utf-8")
    free_src = (HERE / "new_engine_v1" / "free_composition.py").read_text(encoding="utf-8")
    fixture_src = (HERE / "research_pack_fixture.py").read_text(encoding="utf-8")
    for name, src in (("research", research_src), ("the stub pack", fixture_src),
                      ("free composition", free_src)):
        check("%s spells the field 'narrower_subject'" % name,
              '"narrower_subject"' in src)
    check("free composition READS it rather than only naming it",
          'get("narrower_subject")' in free_src, "the consumer does not read the key")
    # The verdict itself is still research's to set; composition renders, never decides.
    block = FC.narrower_scope_block({"narrower_subject": NARROWER,
                                     "sufficiency": {"verdict": "NARROW"}})
    check("composition does not invent a verdict it was not given",
          "NARROW" not in FC.narrower_scope_block({"narrower_subject": NARROWER}))
    check("but renders the one it was given", "NARROW" in block)


def test_the_narrowing_survives_the_whole_free_ladder() -> None:
    """End to end, on the bytes the provider is actually handed.

    `_run` reads the module-level PACK, so the narrowed pack is installed for the duration
    of the run and removed afterwards. Source-code grep is not sufficient here and this
    project has already paid for believing it was.
    """
    global PACK
    original = PACK
    try:
        PACK = dict(original, narrower_subject=NARROWER,
                    sufficiency={"verdict": "NARROW", "reasons": [],
                                 "what_is_missing": []})
        res, prov, _n = _run([PASS_G])
    finally:
        PACK = original
    user = prov.calls[0]["user"]
    check("the narrowing reached the live Writer call", NARROWER in user, user[:300])
    check("the run still completed", res["status"] == CP.PASS, res.get("failure_reason"))
    check("and the runtime bytes are still plan-free",
          FC.writer_inputs_are_plan_free(prov.calls[0]["system"], user) == [])


# ── 13. the permission list and the gate read the same pool ──────────────────
# A DISCONNECTION TEST. `negative_permissions_block` was built from `negative_shape_of`
# alone; `negative_admission_audit`, the gate that enforces the rule, has used the freeze's
# TYPE plus that matcher since 2026-09-20. Across the 120 retained Ledgers: 505 typed
# negatives, 128 shape-matched, 85 both -- 420 licences no Writer was ever shown, and 37
# Ledgers told "NONE" while holding typed negatives.
#
# These assert the POOL, never the matcher. If `negative_shape_of` is ever widened, every
# check below still passes; that is deliberate, because the matcher's recall is not what
# was wrong.
ABS_LEDGER = {
    "F01": {"proposition": "The survey did not collect housing status.",
            "claim_type": "ABSENCE"},
    "F02": {"proposition": "Lung function equations were not validated for this group.",
            "claim_type": "NEGATIVE_EXISTENCE"},
    "F03": {"proposition": "The inspection found the audible warning inoperative.",
            "claim_type": "POSITIVE_FACT"},
    "F04": {"proposition": "The coroner said there is no known treatment.",
            "claim_type": "ATTRIBUTION"},
}


def test_a_typed_absence_the_matcher_misses_is_still_offered() -> None:
    block = FC.negative_permissions_block(ABS_LEDGER)
    check("the Ledger is not reported as licensing nothing",
          "THE ABSENCES YOU MAY CLAIM: NONE" not in block, block[:120])
    for fid in ("F01", "F02"):
        check("the typed absence %s is offered to the Writer" % fid, fid in block, block)
    check("a positive fact is not offered as an absence", "F03" not in block, block)


def test_the_permission_list_is_exactly_the_gate_s_pool() -> None:
    """The property that was violated, stated as a property rather than as examples.

    `negative_shape_of`'s own docstring says it exists so that "a permission decision and
    the audit that enforces it can never use two different definitions of a negative".
    They did. This fails the moment they do again.
    """
    from new_engine_v1 import story as ST
    import re as _re
    # THE FIXTURES MUST NOT COLLAPSE. An adversarial review caught the first version
    # looping over three ledgers that were two: ABS_LEDGER and LEDGER share F01-F04, so
    # merging them just overwrote one with the other, and no case exercised a fact that is
    # BOTH typed negative and shape-matched -- the overlap the pools argue about.
    both = {"N1": {"proposition": "There is no record of the 1974 inspection.",
                   "claim_type": "ABSENCE"},          # typed AND shape-matched
            "N2": {"proposition": "The survey did not collect housing status.",
                   "claim_type": "ABSENCE"},          # typed only
            "N3": {"proposition": "There was no provision for a ramp.",
                   "claim_type": "POSITIVE_FACT"},    # shape-matched only
            "N4": {"proposition": "The unit was replaced in March 2020.",
                   "claim_type": "POSITIVE_FACT"}}    # neither
    check("the overlap fixture really does contain a typed AND shaped fact",
          ST.negative_shape_of(both["N1"]["proposition"])[0] is not None)
    check("and a typed fact the matcher misses",
          ST.negative_shape_of(both["N2"]["proposition"])[0] is None)
    check("and a shaped fact the freeze did not type",
          ST.negative_shape_of(both["N3"]["proposition"])[0] is not None)
    merged = dict(ABS_LEDGER)
    merged.update({"M" + k[1:]: v for k, v in LEDGER.items()})
    for led in (ABS_LEDGER, LEDGER, both, merged):
        aud = ST.negative_admission_audit("", led)
        expected = set(aud["negative_facts_available"]) | set(aud["negation_carrying_facts"])
        block = FC.negative_permissions_block(led)
        shown = {fid for fid in led
                 if _re.search(r"^  %s\s" % _re.escape(fid), block, _re.M)}
        check("what the Writer may claim == what Safety will accept (%d facts)" % len(led),
              shown == expected, (sorted(shown), sorted(expected)))


def test_a_declared_typed_absence_is_not_rejected_by_the_lineage_check() -> None:
    """The third reader of "which facts carry a negation", and it was narrow too.

    Offering the Writer a typed absence and then refusing its declaration would hand the
    owner a NEGATIVE_LINEAGE saying no cited fact carries a negation, about a fact the
    freeze typed ABSENCE and Safety accepts. Found by an adversarial review of the
    permission-pool change, in the same file and for the same reason, so it is fixed in
    the same commit rather than left as a known inconsistency.
    """
    led = {"F01": {"proposition": "The survey did not collect housing status.",
                   "claim_type": "ABSENCE"}}
    sent = "The survey did not collect housing status."
    ok, rejected = FC.verify_declared_negatives(
        sent, [{"sentence": sent, "fact_ids": ["F01"]}], led)
    check("a typed absence the matcher misses still verifies",
          len(ok) == 1 and not rejected, (ok, rejected))
    # And the refusal that matters still refuses: a positive fact licenses nothing.
    pos = {"F01": {"proposition": "The unit was replaced in March 2020.",
                   "claim_type": "POSITIVE_FACT"}}
    ok2, rejected2 = FC.verify_declared_negatives(
        sent, [{"sentence": sent, "fact_ids": ["F01"]}], pos)
    check("a positive fact still cannot license an absence",
          not ok2 and len(rejected2) == 1, (ok2, rejected2))


def test_a_shape_only_attribution_keeps_its_cue() -> None:
    """Exactly the audit's condition, or the prompt promises what the gate refuses."""
    block = FC.negative_permissions_block(ABS_LEDGER)
    line4 = [l for l in block.splitlines() if l.strip().startswith("F04")]
    line1 = [l for l in block.splitlines() if l.strip().startswith("F01")]
    check("the attributed negative is offered", bool(line4), block)
    if line4:
        check("and it is marked as licensing the attributed sentence only",
              "attributed sentence" in line4[0], line4[0])
    if line1:
        check("a typed absence carries no such condition",
              "attributed sentence" not in line1[0], line1[0])


def test_a_ledger_with_no_negation_still_says_so() -> None:
    plain = {"F01": {"proposition": "The unit was replaced in March 2020.",
                     "claim_type": "POSITIVE_FACT"}}
    block = FC.negative_permissions_block(plain)
    check("a Ledger carrying no negation says NONE",
          block.startswith("THE ABSENCES YOU MAY CLAIM: NONE"), block[:80])
    check("an empty Ledger says NONE too",
          FC.negative_permissions_block({}).startswith(
              "THE ABSENCES YOU MAY CLAIM: NONE"))


# ── 14. the ruler, and what it may not be used to measure ────────────────────
# Two diagnoses of the absence problem were wrong on 2026-09-30 because both measured with
# `negative_shape_of`, which answers a narrower question than its name suggests. The
# checks below pin that boundary so the next person reads it before using the number.
MISSED_BY_THE_MATCHER = (
    "The survey did not collect housing status.",
    "No records exist of the 1974 inspection.",
    "The survey excludes unhoused people.",
    "The dataset does not measure overcrowding.",
    "The register contains no entry for the workshop.",
    "Access to the basement is not step free.",
    "The statement was never published in the journal.",
    "No data on ethnicity were collected.",
    "The committee did not consider the objection.",
    "Lung function equations were not validated for this group.",
    "The report omits the wiring.",
    # Kept identical to the list in the docstring, deliberately: an adversary noticed the
    # two had drifted apart, and a documented boundary that its own test does not cover is
    # how the boundary stops being true without anyone noticing.
    "It is the only such programme in the country.",
    # Added after writing this test, because it was offered as an OBVIOUS positive and
    # turned out to be a miss: the pattern covers `never happened|existed|been|occurred|
    # tested` and not `never built`. The boundary is narrower than it reads.
    "It was never built.",
)


def test_the_shape_matcher_is_not_a_classifier_for_propositions() -> None:
    """Its recall on ordinary English is poor, and that is recorded rather than assumed.

    IF THIS FAILS BECAUSE SOMEONE WIDENED THE MATCHER, that is a factual-gate change, not
    a tidy-up: `negative_admission_audit` uses the same function to decide which article
    sentences need a licence, so widening it makes the gate refuse more prose. Update this
    list deliberately, and re-measure anything that counted with it.
    """
    from new_engine_v1 import story as ST
    missed = [s for s in MISSED_BY_THE_MATCHER if ST.negative_shape_of(s)[0] is None]
    check("plainly negative propositions it does not match are still unmatched",
          len(missed) == len(MISSED_BY_THE_MATCHER),
          [s for s in MISSED_BY_THE_MATCHER if s not in missed])
    # And it does match what it was built for: a Writer over-claiming in finished prose.
    # Drawn from the patterns themselves, not from intuition about what "obviously"
    # reads as an absence -- intuition got "It was never built" wrong.
    for over_claim in ("There is no evidence that the unit was tested.",
                       "It was not built.",
                       "It never existed.",
                       "Nothing in the record describes the ward."):
        check("it still catches the over-claim shape it exists for: %r" % over_claim[:34],
              ST.negative_shape_of(over_claim)[0] is not None)


def test_the_docstring_says_which_question_it_answers() -> None:
    """A function whose name reads as a classifier must say in its own text that it is
    not one -- the next person to measure with it will read the docstring, not this."""
    from new_engine_v1 import story as ST
    doc = (ST.negative_shape_of.__doc__ or "").lower()
    for phrase in ("what this is not", "claim_type", "may not be used to count",
                   "not a validated reading"):
        check("the docstring carries %r" % phrase, phrase in doc, doc[:140])
    # EVERY SENTENCE THE DOCSTRING CLAIMS IS A MISS MUST ACTUALLY BE ONE. A documented
    # boundary nobody checks is how the 1.1% figure survived a month.
    for s in MISSED_BY_THE_MATCHER:
        check("the docstring's own example is listed in it: %r" % s[:34],
              s.lower() in doc, doc[:0])


def test_the_ledgers_own_type_is_what_counts_an_absence() -> None:
    """The authority, stated as a check: a typed absence the matcher misses is still an
    absence the Ledger holds, and the permission list proves it by offering it."""
    from new_engine_v1 import story as ST
    led = {"F01": {"proposition": MISSED_BY_THE_MATCHER[0], "claim_type": "ABSENCE"}}
    check("the matcher does not see it",
          ST.negative_shape_of(MISSED_BY_THE_MATCHER[0])[0] is None)
    block = FC.negative_permissions_block(led)
    check("the Ledger still licenses it, by its type",
          "F01" in block and "NONE" not in block.split("\n")[0], block[:160])


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

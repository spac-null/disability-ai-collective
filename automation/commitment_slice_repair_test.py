"""Static tests for commitment_slice_repair. No network, no provider, no engine run.

The plan below is the real frozen bandgap architecture, cut down to the fields these tests
need, with beat B3 and the ledger facts copied verbatim from
/srv/data/cripminds-evidence/claim-shadow-batch2-2026-09-23/run2-20260923T212313Z/.
"""
import sys, pathlib, copy, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from new_engine_v1 import commitment_slice_repair as C
from new_engine_v1 import definition_repair_compiler as DRC

FAIL = []
def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)

GLOSS = ("the long-wavelength edge of what the detector material will register, set by the "
         "bandgap energy engineered in the mercury cadmium telluride mixture — for Roman, "
         "approximately 2.5 microns, with the WFI sensitive from 0.48 to 2.3 microns.")
CLAIMS = [
    {"commitment": "the long-wavelength edge of what the detector material will register",
     "status": DRC.NON_FACTUAL, "reason": "ordinary definitional framing"},
    {"commitment": "set by the bandgap energy", "status": DRC.NOT_ESTABLISHED,
     "reason": "evidence links cadmium fraction to bandgap and separately to cutoff "
               "wavelength, but never states bandgap determines the cutoff"},
    {"commitment": "engineered in the mercury cadmium telluride mixture", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "for Roman, approximately 2.5 microns", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "the WFI sensitive from 0.48 to 2.3 microns", "status": DRC.SUPPORTED, "reason": ""},
]
B3H = ("The detectors are hybrids: because it is not possible to have both photon detection "
       "and electronic readout on the same chip, a mercury cadmium telluride layer of 4096 by "
       "4096 pixels is bonded to a silicon read-out integrated circuit, and that hybrid is "
       "connected to a mechanical mount with electrical connections as a Sensor Chip Assembly. "
       "The fraction of cadmium in the mixture can be varied to engineer a specific bandgap "
       "energy; for Roman, with a desired cutoff wavelength of approximately 2.5 microns, it "
       "was tuned to 0.445, and the WFI is sensitive from 0.48 to 2.3 microns, in infrared "
       "light of longer wavelengths than human eyes can see.")

# THE WHOLE LEDGER, not a cut-down of it. This used to be six hand-abbreviated facts, which
# was fine while nothing in the module counted documents. The dispatch classifier does: it
# asks what share of the plan's evidence a candidate word occupies, and bandgap is 1 fact in
# 117 on the wire and 1 in 6 in a cut-down -- 0.9% against 17%, opposite sides of any bound.
# A fixture that changes the answer is not a fixture, so the real file is read instead.
LEDGER = json.loads((pathlib.Path(__file__).resolve().parent / "fixtures" /
                     "relational-dispatch-2026-09-24" / "b2-run2" / "LEDGER.json")
                    .read_text(encoding="utf-8"))
if isinstance(LEDGER, dict) and "facts" in LEDGER:
    LEDGER = LEDGER["facts"]
if not isinstance(LEDGER, dict):
    LEDGER = {f["fact_id"]: f for f in LEDGER}
ARCH = {
    "definitions": {"cutoff wavelength": GLOSS},
    "definition_evidence": {"cutoff wavelength": ["F86", "F87", "F100"]},
    "use_facts": ["F78", "F86", "F87", "F100", "F09", "F24"],
    "story_spine": "unchanged", "ending_move": "unchanged",
    "beats": [
        {"beat_id": "B1", "happens": "A detector is held at 95 K and read out unilluminated.",
         "concrete_carrier": "SCA 21816", "concept_introduced": "dark current",
         "facts_allowed": ["F24"], "why_reader_wants_next": "x"},
        {"beat_id": "B3", "happens": B3H, "concrete_carrier": "the mercury-cadmium-telluride layer",
         "concept_introduced": "cutoff wavelength",
         "facts_allowed": ["F78", "F86", "F87", "F100"], "why_reader_wants_next": "x"},
        {"beat_id": "B4", "happens": "Behind the flight part sits a decade-long screening program.",
         "concrete_carrier": "the dozens of flight detectors", "concept_introduced": "",
         "facts_allowed": ["F24"], "why_reader_wants_next": "x"},
        {"beat_id": "B7", "happens": "The headline targets arrive as effects in other light.",
         "concrete_carrier": "the light of stars", "concept_introduced": "",
         "facts_allowed": ["F09"], "why_reader_wants_next": "x"},
    ],
}
SHADOW = {"definitions": [{"term": "cutoff wavelength", "claims": CLAIMS}]}
TERM = "cutoff wavelength"


def sl():
    return C.build_slice(ARCH, LEDGER, SHADOW, TERM)


print("\n== anchors: rarity ranks qualified endpoints, it does not qualify them ==")
e1, e2 = C.endpoints(TERM, "set by the bandgap energy", ARCH, LEDGER)
ok(e2 == {"bandgap"}, "the rarest tier selects 'bandgap', not 'energy' (dark energy)")
rep = C.anchor_report(TERM, "set by the bandgap energy", ARCH, LEDGER)
ok(rep["dispatch"] == C.RELATIONAL, "and the case is typed RELATIONAL")
ok(sorted(rep["qualified_endpoints"]) == ["bandgap", "energy"],
   "BOTH ends qualify on their own before rarity picks between them -- bandgap dispatches "
   "because two concepts are independently licensed, not because one word is rare")
ok({w: c["df"] for w, c in rep["candidates"].items() if "df" in c} ==
   {"bandgap": 1, "energy": 4, "set": 4},
   "every candidate and its document frequency is reported, so the heuristic is inspectable")

print("\n== a compound term does not become its own second concept ==")
ok(C._term_words("transfer-to-seat") == {"transfer-to-seat", "transfer", "seat"},
   "a hyphenated term contributes its parts as well as the whole")
_e1, _e2 = C.endpoints("transfer-to-seat", "fixed seat",
                       {"definition_evidence": {"transfer-to-seat": ["FA"]}},
                       {"FA": {"proposition": "a dedicated seat on the bottom bench"}})
ok(_e2 == set(),
   "'fixed seat' has NO second concept -- 'fixed' is absent from the evidence and 'seat' "
   "belongs to the term, so it refuses like 'minutes away' rather than inventing a relation")

print("\n== affordance is ingredients AND duty, not mere co-occurrence ==")
surf = C.affording_surfaces(ARCH, LEDGER, TERM, e1, e2)
ids = {s["surface_id"]: s["affordance"] for s in surf}
ok(ids.get("beat:B3") == "FULL", "B3 is FULL: both ideas reachable and it carries the first-use duty")
ok(ids.get("definition:%s" % TERM) == "FULL", "the gloss is FULL: it IS the first-use explanation")
ok("beat:B7" not in ids, "the dark-energy beat is not flagged -- 'energy' was never the anchor")
noduty = copy.deepcopy(ARCH)
for b in noduty["beats"]:
    if b["beat_id"] == "B3":
        b["concept_introduced"] = ""
s2 = {x["surface_id"]: x["affordance"] for x in C.affording_surfaces(noduty, LEDGER, TERM, e1, e2)}
ok(s2.get("beat:B3") == "INGREDIENTS_ONLY",
   "without the duty the same beat is INGREDIENTS_ONLY -- material may live there")

print("\n== a fact in facts_allowed affords even when the prose never says it ==")
quiet = copy.deepcopy(ARCH)
for b in quiet["beats"]:
    if b["beat_id"] == "B3":
        b["happens"] = "The detectors are hybrids. For Roman the cutoff wavelength matters."
q = {x["surface_id"]: x for x in C.affording_surfaces(quiet, LEDGER, TERM, e1, e2)}
ok(q.get("beat:B3", {}).get("affordance") == "FULL",
   "F86 alone keeps the route open -- the packet prints it under the beat")
ok("facts_allowed" in (q["beat:B3"]["where"]) and "happens" not in q["beat:B3"]["where"],
   "and the reason given is the fact, not the prose")

print("\n== the slice partitions prose losslessly ==")
S = sl()
ok(not S.get("refusals"), "the slice builds: %s" % S.get("refusals"))
b3 = next(x for x in S["surfaces"] if x.get("beat_id") == "B3")
ok("".join(u["text"] for u in b3["units"]) == B3H, "beat units reassemble to the original byte for byte")
aff = [u for u in b3["units"] if u["role"] == C.AFFORDING]
ok(len(aff) == 1 and "bandgap" in aff[0]["text"], "exactly one clause carries bandgap")
ok("cutoff wavelength" not in aff[0]["text"],
   "and it does NOT swallow the cutoff material -- splitting is on sentence/semicolon only")
ok(b3["e2_facts"] == ["F86"], "F86 is identified as the fact routing bandgap into the beat")
ok(b3["first_use_site"] is True, "B3 is marked as the first-use site")

print("\n== the model may not touch what is marked KEEP ==")
keep_id = next(u["unit_id"] for u in b3["units"] if u["role"] == C.PROTECTED and not u.get("separator"))
e = C.validate({"edits": [{"unit_id": keep_id, "operation": "DROP"}]}, S, LEDGER)
ok(e and "may not be changed" in e[0], "editing a KEEP clause is rejected")
e = C.validate({"edits": [{"unit_id": "nope", "operation": "DROP"}]}, S, LEDGER)
ok(e and "not a piece of this slice" in e[0], "editing an unknown unit is rejected")

print("\n== a new beat may not be invented ==")
PRO = ("Do not state or imply that the bandgap energy sets the cutoff wavelength; the cadmium fraction relates to each separately, and the step between them is not established.")
base = {"edits": [{"unit_id": aff[0]["unit_id"], "operation": "DROP"}], "prohibition": PRO}
e = C.validate(dict(base, facts=[{"fact_id": "F86", "operation": "MOVE", "to_beat": "B99"}]), S, LEDGER)
ok(e and "does not exist" in e[0], "MOVE to a non-existent beat is rejected")
e = C.validate(dict(base, facts=[{"fact_id": "F86", "operation": "MOVE", "to_beat": "B3"}]), S, LEDGER)
ok(e and "itself a surface being repaired" in e[0], "MOVE back into the repaired beat is rejected")
e = C.validate(dict(base, facts=[{"fact_id": "F86", "operation": "MOVE", "to_beat": "B4"}]), S, LEDGER)
ok(e == [], "MOVE to an existing untouched beat validates")

print("\n== evidence discipline on generated replacement text ==")
uid = aff[0]["unit_id"]
ok(C.validate({"edits": [{"unit_id": uid, "operation": "REPLACE",
                          "replacement": "the cadmium fraction was tuned to 0.61"}], "prohibition": PRO}, S, LEDGER) != [],
   "a number the beat's facts do not state is rejected")
ok(C.validate({"edits": [{"unit_id": uid, "operation": "REPLACE",
                          "replacement": "engineers at Teledyne chose the recipe"}], "prohibition": PRO}, S, LEDGER) != [],
   "an entity the beat's facts do not name is rejected")

print("\n== DROP the bandgap clause + MOVE the fact: the target shape ==")
DEFU = S["definition_target"]
reply = {"edits": [{"unit_id": DEFU, "operation": "DROP", "left_glue": ", ", "right_glue": ""},
                   {"unit_id": uid, "operation": "DROP"}],
         "facts": [{"fact_id": "F86", "operation": "MOVE", "to_beat": "B4"}],
         "prohibition": PRO,
         "reason": "bandgap no longer shares the beat that must explain cutoff wavelength"}
ok(C.validate(reply, S, LEDGER) == [], "the reply validates")
out = C.compile_repair(ARCH, S, reply)
pr = C.prove(ARCH, out, S, LEDGER, TERM, reply)
newb3 = next(b for b in out["beats"] if b["beat_id"] == "B3")
print("      B3 now: %s" % newb3["happens"][-150:])
ok("bandgap" not in newb3["happens"], "bandgap is gone from B3's prose")
ok("F86" not in newb3["facts_allowed"], "F86 no longer offered by B3")
ok("F86" in next(b for b in out["beats"] if b["beat_id"] == "B4")["facts_allowed"],
   "F86 is offered by B4 instead -- the material is relocated, not deleted")
ok("Sensor Chip Assembly" in newb3["happens"], "the hybrid/SCA sentence survives verbatim")
ok("for Roman, with a desired cutoff wavelength" in newb3["happens"].lower()
   or "For Roman, with a desired cutoff wavelength" in newb3["happens"],
   "the cutoff material survives")
ok(pr["TARGET_COMMITMENT_REMOVED"], "TARGET_COMMITMENT_REMOVED")
ok(pr["AFFORDANCE_REMOVED"], "AFFORDANCE_REMOVED")
ok(pr["PROTECTED_CONTENT_PRESERVED"], "PROTECTED_CONTENT_PRESERVED")
ok(pr["UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED"], "UNRELATED_FACT_PRESERVED_OR_EXPLICITLY_DROPPED")
ok(pr["second_concept_facts"]["F86"]["state"] == "OFFERED_IN_B4", "F86 disposition recorded as relocated")
ok(pr["first_use_duty_still_assigned"], "the term is still explained at first use")
ok(pr["plan_outside_slice_byte_identical"], "everything outside the slice is byte-identical")
ok("the long-wavelength edge of what the detector material will register" in out["definitions"][TERM],
   "the explanatory clause still survives byte for byte in the gloss")
ok("bandgap" not in out["definitions"][TERM], "and the gloss no longer states the bridge")
print("      orthographic adjustments: %s" % pr["orthographic_adjustments"])
ok(len(pr["orthographic_adjustments"]) <= 1,
   "at most one first-letter capitalisation, and it is recorded rather than hidden")

print("\n== deleting the concept instead is allowed, but RECORDED as a loss ==")
reply2 = {"edits": [{"unit_id": DEFU, "operation": "DROP", "left_glue": ", ", "right_glue": ""},
                    {"unit_id": uid, "operation": "DROP"}],
          "facts": [{"fact_id": "F86", "operation": "REMOVE"}],
          "prohibition": PRO, "reason": "no other beat is about detector material"}
out2 = C.compile_repair(ARCH, S, reply2)
pr2 = C.prove(ARCH, out2, S, LEDGER, TERM, reply2)
ok(pr2["AFFORDANCE_REMOVED"], "removing the fact also closes the route")
ok(pr2["second_concept_facts"]["F86"]["state"] == "IN_use_facts_BUT_NO_BEAT_OFFERS_IT",
   "and the state says plainly that no beat offers it any more")
ok(pr2["second_concept_facts"]["F86"]["explicit"], "the loss was an explicit decision, not silent")

print("\n== keeping the fact does NOT close the route ==")
reply3 = {"edits": [{"unit_id": DEFU, "operation": "DROP", "left_glue": ", ", "right_glue": ""},
                    {"unit_id": uid, "operation": "DROP"}],
          "facts": [{"fact_id": "F86", "operation": "KEEP"}], "prohibition": PRO, "reason": "x"}
out3 = C.compile_repair(ARCH, S, reply3)
pr3 = C.prove(ARCH, out3, S, LEDGER, TERM, reply3)
ok(not pr3["AFFORDANCE_REMOVED"],
   "dropping the prose while leaving F86 in the beat leaves the route OPEN -- the exact "
   "shortcut this experiment was warned against")

print("\n== the prohibition must forbid a statement, not a subject ==")
def withpro(p):
    return C.validate({"edits": [{"unit_id": uid, "operation": "DROP"}], "prohibition": p}, S, LEDGER)
ok(withpro(PRO) == [], "a well-formed prohibition validates")
ok(withpro("") != [], "a missing prohibition is rejected")
ok(withpro("Avoid linking them.") != [], "one not beginning 'Do not' is rejected")
ok(any("bans the subject" in e for e in withpro("Do not mention the bandgap energy at all.")),
   "'Do not mention <concept>' is rejected -- that is how branch E lost the concept")
ok(any("bans the subject" in e for e in withpro("Do not discuss bandgap energy here.")),
   "'Do not discuss <concept>' is rejected")
ok(any("world-falsity" in e for e in withpro(
    "Do not say the bandgap sets the cutoff wavelength; that claim is false.")),
   "asserting the relation is FALSE is rejected -- NOT_ESTABLISHED is not CONTRADICTED")
ok(any("does not name what was flagged" in e for e in withpro("Do not overstate the physics.")),
   "a prohibition that never names the flagged material is rejected")
ok(withpro("Do not " + "x" * 420) != [], "an over-long prohibition is rejected")
ok(any("provenance language" in e for e in withpro(
    "Do not say the bandgap sets the cutoff wavelength; the evidence does not reach that.")),
   "provenance framing is rejected BEFORE assembly -- the packet validator would reject it "
   "anyway, and a rule about where knowledge came from teaches the Writer to write that")
ok(withpro("Do not say the bandgap energy sets the cutoff wavelength; the cadmium fraction "
           "is tied separately to each, and nothing ties those two to one another.") == [],
   "the same rule in the material's own words passes")

print("\n== failure is always closed ==")
def boom(system, user):
    raise RuntimeError("provider exploded")
a = C.run(boom, ARCH, LEDGER, SHADOW, TERM)
ok(a["status"] == "FAILED" and "repaired_architecture" not in a, "provider failure yields no plan")
for junk in (None, [], "text", {}, {"edits": []}, {"edits": [{"unit_id": uid}]}):
    a = C.run(lambda s, u, j=junk: j, ARCH, LEDGER, SHADOW, TERM)
    ok(a["status"] in ("REFUSED", "FAILED") and "repaired_architecture" not in a,
       "malformed reply %r is refused with no plan" % (junk,))

print("\n== one call, tool owns the verdict, fails closed on an invalid plan ==")
calls = {"n": 0}
def counting(system, user):
    calls["n"] += 1
    return dict(reply, authority="FULL", status="APPROVED",
                repaired_architecture={"definitions": {}}, preservation={"x": 1})
a = C.run(counting, ARCH, LEDGER, SHADOW, TERM)
ok(calls["n"] == 1 and a["physical_model_calls"] == 1, "exactly one physical call, no retry")
ok(a["authority"] == "ZERO", "authority stays ZERO")
ok(a["status"] != "REPAIRED", "status is the tool's, not the model's APPROVED")
ok("repaired_architecture" not in a, "the model cannot supply the plan")
ok(sorted(a.get("tool_fields_ignored") or []) ==
   ["authority", "preservation", "repaired_architecture", "status"], "stolen fields recorded")
# this cut-down fixture is deliberately NOT a complete architecture, so the engine's own rules
# reject the assembled plan. That the module then refuses -- rather than returning a plan that
# only ITS checks approved -- is the property being tested.
ok(isinstance(a["engine_validation"], list) and a["engine_validation"],
   "the engine's own validators ran and objected")
ok("rejected_architecture" in a, "the rejected plan is kept for inspection, not returned as good")
ok("engine" in (a.get("error") or "").lower() or "rules" in (a.get("error") or "").lower(),
   "and the refusal says so: %r" % (a.get("error") or "")[:80])

print("\n== flag off, nothing wired ==")
ok(C.enabled({}) is False, "flag off by default")
ok(C.enabled({"CRIPMINDS_COMMITMENT_SLICE_REPAIR": "1"}) is True, "enabled explicitly")
src = pathlib.Path(__file__).resolve().parent / "new_engine_v1"
imp = [q.name for q in src.glob("*.py")
       if "commitment_slice_repair" in q.read_text(encoding="utf-8")
       and q.name != "commitment_slice_repair.py"]
ok(imp == [], "no engine module imports it (found: %s)" % imp)
ok("commitment_slice_repair" not in (src / "composition.py").read_text(encoding="utf-8"),
   "composition.py untouched")

print("\n" + ("ALL PASS" if not FAIL else "FAILURES: %d\n  - %s" % (len(FAIL), "\n  - ".join(FAIL))))
sys.exit(1 if FAIL else 0)

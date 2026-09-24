"""Static tests for the obligation-selection policy. Committed BEFORE the cohort ran.

The property under test is SPARSITY as much as correctness: a policy that obliges everything
has selected nothing, and would turn the Writer into a checklist renderer.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from new_engine_v1 import obligation_policy as OP
from new_engine_v1 import definition_repair_compiler as DRC

FAIL = []
def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)

BANDGAP = ("the long-wavelength edge of what the detector material will register, set by the "
           "bandgap energy engineered in the mercury cadmium telluride mixture — for Roman, "
           "approximately 2.5 microns, with the WFI sensitive from 0.48 to 2.3 microns.")
BG_CLAIMS = [
    {"commitment": "the long-wavelength edge of what the detector material will register",
     "status": DRC.NON_FACTUAL, "reason": ""},
    {"commitment": "set by the bandgap energy", "status": DRC.NOT_ESTABLISHED, "reason": ""},
    {"commitment": "engineered in the mercury cadmium telluride mixture", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "for Roman, approximately 2.5 microns", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "the WFI sensitive from 0.48 to 2.3 microns", "status": DRC.SUPPORTED, "reason": ""},
]
LEDGER = {"F86": {"proposition": "The precise mixture of HgCdTe, specifically the fraction of "
                                 "cadmium, can be varied to engineer a specific bandgap energy."}}

# a clean definition
CLEAN = "induced signal from thermal or quantum tunneling processes, measured in exposures taken without illumination."
CLEAN_CLAIMS = [
    {"commitment": "induced signal from thermal or quantum tunneling processes", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "measured in exposures taken without illumination", "status": DRC.SUPPORTED, "reason": ""},
]
# many supported neighbours, one flag in the middle -- the over-selection probe
MANY = "alpha one, beta two, gamma three, delta four, epsilon five, zeta six"
MANY_CLAIMS = [
    {"commitment": "alpha one", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "beta two", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "gamma three", "status": DRC.NOT_ESTABLISHED, "reason": ""},
    {"commitment": "delta four", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "epsilon five", "status": DRC.SUPPORTED, "reason": ""},
    {"commitment": "zeta six", "status": DRC.SUPPORTED, "reason": ""},
]

print("\n== the hard case: explanatory + the neighbour, and nothing further away ==")
ir = DRC.build_ir("cutoff wavelength", BANDGAP, BG_CLAIMS)
t = DRC.select_target(ir)
sel = OP.select(ir, t)
got = {o["id"]: o["why"] for o in sel["obligations"]}
print("      selected: %s" % got)
ok(got.get("U1") == OP.EXPLANATORY, "U1 the explanation is obliged -- branch B deleted exactly this")
ok(got.get("U3") == OP.ADJACENT_SUPPORTED, "U3, immediately after the flagged span, is obliged")
ok("U4" not in got and "U5" not in got,
   "U4 and U5 are supported but further away, and are NOT obliged")
ok("U2" not in got, "the flagged span itself is never an obligation")
ok(sel["obligation_share"] <= OP.MAX_OBLIGATION_SHARE and not sel["over_obligation"],
   "share %.2f is within the declared bound" % sel["obligation_share"])

print("\n== displaced facts ==")
sel2 = OP.select(ir, t, {"facts": [{"fact_id": "F86", "operation": "MOVE", "to_beat": "B4"}]}, LEDGER)
ids = [o["id"] for o in sel2["obligations"]]
ok("F86" in ids, "a MOVEd fact becomes an obligation -- branch E dropped exactly this")
ok(next(o for o in sel2["obligations"] if o["id"] == "F86")["must_realize"].startswith(
    "The precise mixture"), "and it carries the fact's own proposition")
sel3 = OP.select(ir, t, {"facts": [{"fact_id": "F86", "operation": "REMOVE"}]}, LEDGER)
ok("F86" in [o["id"] for o in sel3["obligations"]], "a REMOVEd fact is obliged too")
sel4 = OP.select(ir, t, {"facts": [{"fact_id": "F86", "operation": "KEEP"}]}, LEDGER)
ok("F86" not in [o["id"] for o in sel4["obligations"]],
   "a fact left where it was is NOT obliged -- nothing endangered it")

print("\n== sparsity: many supported neighbours must not all be obliged ==")
ir2 = DRC.build_ir("t", MANY, MANY_CLAIMS)
t2 = DRC.select_target(ir2)
s2 = OP.select(ir2, t2)
got2 = [o["id"] for o in s2["obligations"]]
print("      6 commitments, 1 flagged -> obliged: %s (share %.2f)" % (got2, s2["obligation_share"]))
ok(len(got2) == 2, "exactly the two immediate neighbours, not the other three")
ok(not s2["over_obligation"], "not flagged as over-obligation")
ok(s2["obligation_share"] < 0.5, "share stays well under the declared bound")

print("\n== a clean definition produces nothing at all ==")
irc = DRC.build_ir("dark current", CLEAN, CLEAN_CLAIMS)
ok(DRC.select_target(irc) is None, "no repairable unit")
plan = OP.for_plan({"definitions": {"dark current": CLEAN, "cutoff wavelength": BANDGAP}},
                   LEDGER,
                   {"definitions": [{"term": "dark current", "claims": CLEAN_CLAIMS},
                                    {"term": "cutoff wavelength", "claims": BG_CLAIMS}]})
ok([p["term"] for p in plan] == ["cutoff wavelength"],
   "for_plan returns only the flagged definition -- the clean one is absent, not empty")

print("\n== the Writer never sees machine language ==")
field = OP.architecture_field(sel2)
ok(all(set(f) <= {"id", "evidence", "must_realize"} for f in field), "field shape is minimal")
ok(all("why" not in f and "source" not in f for f in field), "reasons stay internal")
ok(all(f["must_realize"].strip() for f in field), "every entry carries real text")

print("\n== the policy is deterministic and model-free ==")
ok(OP.select(ir, t) == OP.select(ir, t), "same inputs, same output")
import inspect
src = inspect.getsource(OP)
ok("ask(" not in src and "provider" not in src.lower() and "complete(" not in src,
   "no model call anywhere in the policy")

print("\n" + ("ALL PASS" if not FAIL else "FAILURES: %d\n  - %s" % (len(FAIL), "\n  - ".join(FAIL))))
sys.exit(1 if FAIL else 0)

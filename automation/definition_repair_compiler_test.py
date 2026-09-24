"""Static tests for definition_repair_compiler. No network, no provider, no engine run.

The glosses, claims and evidence below are copied verbatim out of the frozen calibration
artifacts under /srv/data/cripminds-evidence/, so the cases these assert on are the ones that
actually happened rather than ones invented to be passable.
"""
import sys, os, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from new_engine_v1 import definition_repair_compiler as R

FAIL = []
def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)

# ------------------------------------------------------------------ frozen case material --
# claim-shadow-batch2-2026-09-23/run2-20260923T212313Z  -- the hard case
BANDGAP_GLOSS = ("the long-wavelength edge of what the detector material will register, set "
                 "by the bandgap energy engineered in the mercury cadmium telluride mixture "
                 "— for Roman, approximately 2.5 microns, with the WFI sensitive from "
                 "0.48 to 2.3 microns.")
BANDGAP_CLAIMS = [
    {"commitment": "the long-wavelength edge of what the detector material will register",
     "status": R.NON_FACTUAL, "reason": "ordinary definitional framing of what the term means"},
    {"commitment": "set by the bandgap energy", "status": R.NOT_ESTABLISHED,
     "reason": "evidence links cadmium fraction to bandgap and separately to cutoff "
               "wavelength, but never states bandgap determines the cutoff"},
    {"commitment": "engineered in the mercury cadmium telluride mixture", "status": R.SUPPORTED,
     "reason": "the HgCdTe mixture's cadmium fraction is varied and was tuned for Roman's cutoff"},
    {"commitment": "for Roman, approximately 2.5 microns", "status": R.SUPPORTED,
     "reason": "stated directly as Roman's desired cutoff wavelength"},
    {"commitment": "the WFI sensitive from 0.48 to 2.3 microns", "status": R.SUPPORTED,
     "reason": "matches the stated WFI sensitivity range"},
]
BANDGAP_EV = [
    ("F86", "The precise mixture of HgCdTe, specifically the fraction of cadmium, can be "
            "varied to engineer a specific bandgap energy.", ""),
    ("F87", "For Roman's desired cutoff wavelength of approximately 2.5 microns, the "
            "fraction of cadmium was tuned to 0.445.", ""),
    ("F100", "The WFI is sensitive to wavelengths from 0.48 to 2.3 microns.", ""),
]
BANDGAP_ARCH = {"definitions": {"cutoff wavelength": BANDGAP_GLOSS},
                "definition_evidence": {"cutoff wavelength": ["F86", "F87", "F100"]}}
BANDGAP_LEDGER = {f: {"proposition": p, "support_span": s} for f, p, s in BANDGAP_EV}
BANDGAP_SHADOW = {"definitions": [{"term": "cutoff wavelength", "claims": BANDGAP_CLAIMS}]}

# batch2 run1 -- the dangling-article case: DROP would break this one
SEAT_GLOSS = ("an arrangement in which a guest moves out of their own wheelchair into a fixed "
              "seat on the lowest bench before the session, and the chair is taken back out "
              "of the room by a member of staff")
SEAT_CLAIMS = [
    {"commitment": "a guest moves out of their own wheelchair into a", "status": R.SUPPORTED, "reason": ""},
    {"commitment": "fixed seat", "status": R.NOT_ESTABLISHED,
     "reason": "evidence calls the seat dedicated but does not state it is fixed"},
    {"commitment": "on the lowest bench", "status": R.SUPPORTED, "reason": ""},
    {"commitment": "before the session", "status": R.SUPPORTED, "reason": ""},
    {"commitment": "the chair is taken back out of the room", "status": R.SUPPORTED, "reason": ""},
    {"commitment": "by a member of staff", "status": R.SUPPORTED, "reason": ""},
]
SEAT_EV = [("F63", "For this Fringe the venue offers a transfer-to-seat option, with a "
                   "dedicated seat on the bottom bench that has a back rest and arm rests and "
                   "a space adjacent for a companion.", ""),
           ("F64", "Once a guest has transferred to the seat, a Sauna Host takes the "
                   "wheelchair back outside the sauna.", "")]

# batch2 run2 -- a definition with NOTHING wrong with it
CLEAN_GLOSS = ("induced signal from thermal or quantum tunneling processes, measured in "
               "exposures taken without illumination.")
CLEAN_CLAIMS = [
    {"commitment": "induced signal from thermal or quantum tunneling processes", "status": R.SUPPORTED, "reason": ""},
    {"commitment": "measured in exposures taken without illumination", "status": R.SUPPORTED, "reason": ""},
]

def ir_bandgap():
    return R.build_ir("cutoff wavelength", BANDGAP_GLOSS, BANDGAP_CLAIMS)

def ir_seat():
    return R.build_ir("transfer-to-seat", SEAT_GLOSS, SEAT_CLAIMS)


print("\n== IR: total coverage, no silent deletion ==")
ir = ir_bandgap()
ok(ir["anchoring"] == "OK", "bandgap gloss partitions cleanly")
ok("".join(u["text"] for u in ir["units"]) == BANDGAP_GLOSS,
   "every character of the gloss is inside exactly one unit")
ok([u["role"] for u in ir["units"]].count(R.REPAIRABLE) == 1, "exactly one REPAIRABLE unit")
ok(sum(1 for u in ir["units"] if u["role"] == R.PROTECTED) == 4, "four PROTECTED units")
ok(any(u["role"] == R.PROTECTED and u["status"] == R.NON_FACTUAL for u in ir["units"]),
   "the explanatory clause is PROTECTED, not repairable")
ok(R.select_target(ir)["text"] == "set by the bandgap energy", "the target is the flagged span")

print("\n== anchoring refuses rather than guesses ==")
ok(R.anchor("a b c", "zzz") is None, "a non-substring commitment is UNANCHORED")
ok(R.anchor("the seat and the seat", "the seat") is None, "an ambiguous commitment refuses")
ok(R.anchor("the seat only", "the seat") == (0, 8), "a unique commitment anchors")
bad = R.build_ir("t", "some gloss", [{"commitment": "not in here", "status": R.NOT_ESTABLISHED}])
ok(bad["anchoring"] == "UNANCHORED", "an unanchorable claim refuses the whole IR")
ovl = R.build_ir("t", "alpha beta gamma",
                 [{"commitment": "alpha beta", "status": R.SUPPORTED},
                  {"commitment": "beta gamma", "status": R.NOT_ESTABLISHED}])
ok(ovl["anchoring"] == "OVERLAP", "overlapping commitments refuse the whole IR")

print("\n== a clean definition produces no target at all ==")
cir = R.build_ir("dark current", CLEAN_GLOSS, CLEAN_CLAIMS)
ok(cir["anchoring"] == "NO_REPAIRABLE_UNIT", "clean definition has no repairable unit")
ok(R.select_target(cir) is None, "clean definition selects no target")
clean_arch = {"definitions": {"dark current": CLEAN_GLOSS, "cutoff wavelength": BANDGAP_GLOSS},
              "definition_evidence": {"dark current": ["F69"], "cutoff wavelength": ["F86"]}}
clean_shadow = {"definitions": [{"term": "dark current", "claims": CLEAN_CLAIMS},
                                {"term": "cutoff wavelength", "claims": BANDGAP_CLAIMS}]}
tg = R.plan_targets(clean_arch, clean_shadow)
ok([t["term"] for t in tg] == ["cutoff wavelength"],
   "plan_targets skips the clean definition entirely and returns only the flagged one")

def refusing_ask(*a, **k):
    raise AssertionError("a model call was made for a definition with no warning")
art = R.run(refusing_ask, {"definitions": {"dark current": CLEAN_GLOSS},
                           "definition_evidence": {"dark current": ["F69"]}},
            {}, {"definitions": [{"term": "dark current", "claims": CLEAN_CLAIMS}]}, "dark current")
ok(art["status"] == "REFUSED" and art["physical_model_calls"] == 0,
   "run() on a clean definition makes ZERO model calls and refuses")

print("\n== the hard case: DROP preserves the explanation verbatim ==")
ir = ir_bandgap(); tgt = R.select_target(ir); win = R.edit_window(ir, tgt)
drop = {"operation": "DROP", "left_glue": ", ", "right_glue": "", "reason": "unsupported"}
ok(R.validate(drop, ir, tgt, BANDGAP_EV) == [], "a plain DROP validates")
out = R.compile_repair(ir, tgt, win, drop)
proof = R.prove_preservation(ir, tgt, out)
print("      ->", out)
ok("the long-wavelength edge of what the detector material will register" in out,
   "the explanatory clause the free rewrite destroyed survives VERBATIM")
ok("set by the bandgap energy" not in out, "the unsupported bridge is gone")
ok("bandgap" not in out, "no bandgap claim remains in any form")
ok(proof["all_protected_survived"], "every protected unit survived, in order")
ok(len(proof["explanatory_survived"]) == len(proof["explanatory_units"]) == 1,
   "explanatory preservation is proven mechanically")
ok("for Roman, approximately 2.5 microns" in out and "0.48 to 2.3 microns" in out,
   "supported factual content survives")
ok(out.count("  ") == 0 and " ," not in out, "assembly leaves no doubled space or stray comma")

print("\n== preservation cannot be violated even by a hostile reply ==")
evil = {"operation": "REPLACE", "replacement": "a wavelength specified for the instrument",
        "left_glue": ", ", "right_glue": "", "reason": "x"}
errs = R.validate(evil, ir, tgt, BANDGAP_EV)
ok(errs != [], "the free-rewrite text that destroyed the article is REJECTED: %s" % (errs[:1]))
# even if such text somehow passed, the compiler cannot reach the protected regions
forced = R.compile_repair(ir, tgt, win, evil)
ok("the long-wavelength edge of what the detector material will register" in forced,
   "even an unvalidated hostile replacement cannot delete protected text -- it is copied, not generated")
ok(R.prove_preservation(ir, tgt, forced)["all_protected_survived"],
   "the proof still holds for the hostile reply")

print("\n== evidence discipline on generated replacement text ==")
ok(R.validate({"operation": "REPLACE", "replacement": "tuned to 0.61",
               "left_glue": ", ", "right_glue": " "}, ir, tgt, BANDGAP_EV) != [],
   "a number the evidence does not state is rejected")
ok(R.validate({"operation": "REPLACE", "replacement": "chosen by NASA engineers in Maryland",
               "left_glue": ", ", "right_glue": " "}, ir, tgt, BANDGAP_EV) != [],
   "named entities absent from the declared evidence are rejected")
ok(R.validate({"operation": "REPLACE", "replacement": "x" * 200,
               "left_glue": ", ", "right_glue": " "}, ir, tgt, BANDGAP_EV) != [],
   "a replacement far longer than the span it replaces is rejected")
ok(R.validate({"operation": "REPLACE", "replacement": "set by the bandgap energy of the mixture",
               "left_glue": ", ", "right_glue": " "}, ir, tgt, BANDGAP_EV) != [],
   "a replacement that still contains the unsupported span is rejected")
ok(R.validate({"operation": "DROP", "replacement": "something extra",
               "left_glue": ", ", "right_glue": ""}, ir, tgt, BANDGAP_EV) != [],
   "DROP carrying replacement text is rejected")

print("\n== the glue rule is a closed list, not a judgement ==")
ok(R.check_glue(", ") == [] and R.check_glue(" — ") == [] and R.check_glue(", with ") == [],
   "punctuation, dashes and prepositional glue are allowed")
ok(R.check_glue(" tuned for ") != [], "a verb in the glue is rejected")
ok(R.check_glue(" which means ") != [], "a relativiser + verb in the glue is rejected")
ok(R.check_glue(" 2.5 ") != [], "a number in the glue is rejected")
ok(R.check_glue(" bandgap ") != [], "a noun in the glue is rejected")
ok(R.check_glue("x" * 40) != [], "over-long glue is rejected")

print("\n== the dangling-article case: DROP must not be waved through ==")
sir = ir_seat(); stgt = R.select_target(sir); swin = R.edit_window(sir, stgt)
ok(stgt["text"] == "fixed seat", "the seat target is the flagged span")
good = {"operation": "REPLACE", "replacement": "dedicated seat", "left_glue": " ", "right_glue": " "}
ok(R.validate(good, sir, stgt, SEAT_EV) == [],
   "'dedicated seat' validates -- the word is in the declared evidence")
sout = R.compile_repair(sir, stgt, swin, good)
print("      ->", sout)
ok("into a dedicated seat on the lowest bench" in sout, "the repaired seat clause reads correctly")
ok(R.prove_preservation(sir, stgt, sout)["all_protected_survived"], "seat: protected units survive")
ok("fixed" not in sout, "the unsupported word is gone")
ok(R.validate({"operation": "REPLACE", "replacement": "immovable seat",
               "left_glue": " ", "right_glue": " "}, sir, stgt, SEAT_EV) != [],
   "a synonym the evidence does not contain is rejected")

print("\n== failure is always closed ==")
def boom(system, user):
    raise RuntimeError("provider exploded")
a = R.run(boom, BANDGAP_ARCH, BANDGAP_LEDGER, BANDGAP_SHADOW, "cutoff wavelength")
ok(a["status"] == "FAILED" and "repaired_gloss" not in a,
   "a provider failure yields no gloss")
for junk in (None, [], "text", {}, {"operation": "REWRITE"}, {"operation": "REPLACE"}):
    a = R.run(lambda s, u, j=junk: j, BANDGAP_ARCH, BANDGAP_LEDGER, BANDGAP_SHADOW, "cutoff wavelength")
    ok(a["status"] == "REFUSED" and "repaired_gloss" not in a,
       "malformed reply %r is refused with no gloss" % (junk,))

print("\n== one call, and only one ==")
calls = {"n": 0}
def counting(system, user):
    calls["n"] += 1
    return {"operation": "DROP", "left_glue": ", ", "right_glue": "", "reason": "unsupported"}
a = R.run(counting, BANDGAP_ARCH, BANDGAP_LEDGER, BANDGAP_SHADOW, "cutoff wavelength")
ok(a["status"] == "REPAIRED", "the hard case repairs end to end")
ok(calls["n"] == 1 and a["physical_model_calls"] == 1, "exactly one physical model call, no retry")
ok("the long-wavelength edge of what the detector material will register" in a["repaired_gloss"],
   "end-to-end: the explanation survives")
ok(a["preservation"]["all_protected_survived"], "end-to-end: preservation proven")

print("\n== the model cannot narrate its own authority ==")
a = R.run(lambda s, u: {"operation": "DROP", "left_glue": ", ", "right_glue": "",
                        "authority": "FULL", "status": "APPROVED",
                        "preservation": {"all_protected_survived": True},
                        "repaired_gloss": "whatever I say it is"},
          BANDGAP_ARCH, BANDGAP_LEDGER, BANDGAP_SHADOW, "cutoff wavelength")
ok(a["authority"] == "ZERO", "authority stays ZERO")
ok(a["status"] == "REPAIRED", "status is the tool's, not the model's")
ok(a["repaired_gloss"] != "whatever I say it is", "the model cannot supply the output gloss")
ok(a["preservation"]["protected_units"], "the proof is recomputed, not accepted")
ok(sorted(a.get("tool_fields_ignored") or []) ==
   ["authority", "preservation", "repaired_gloss", "status"], "stolen fields are recorded")

print("\n== flag is OFF by default and nothing is wired to production ==")
ok(R.enabled({}) is False, "disabled with no env")
ok(R.enabled({"CRIPMINDS_DEFINITION_REPAIR_COMPILER": "1"}) is True, "enabled explicitly")
src = pathlib.Path(__file__).resolve().parent / "new_engine_v1"
# The only module allowed to import this one is the other zero-authority experiment built on
# top of it. Nothing on the production path may, and composition.py is checked separately.
EXPERIMENTAL = {"commitment_slice_repair.py"}
importers = {p.name for p in src.glob("*.py")
             if "definition_repair_compiler" in p.read_text(encoding="utf-8")
             and p.name != "definition_repair_compiler.py"}
ok(importers <= EXPERIMENTAL,
   "only the sibling experiment imports the repair compiler (found: %s)" % sorted(importers))
comp = (src / "composition.py").read_text(encoding="utf-8")
ok("definition_repair_compiler" not in comp, "composition.py is untouched")

print("\n" + ("ALL PASS" if not FAIL else "FAILURES: %d\n  - %s" % (len(FAIL), "\n  - ".join(FAIL))))
sys.exit(1 if FAIL else 0)

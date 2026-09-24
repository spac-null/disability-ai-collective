"""Static tests for the relational-dispatch classifier. No network, no provider, no model.

Two halves.

  THE FROZEN SET      every hand-reviewed flagged commitment, run against the real ledger it
                      was detected in, compared with the label committed in
                      relational_dispatch_cases.py BEFORE the rule changed.

  THE STRUCTURE       the properties the rule is supposed to have, exercised on constructed
                      inputs, so that each one is tested on purpose rather than incidentally
                      by whichever real case happens to trip it.
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from new_engine_v1 import commitment_slice_repair as C   # noqa: E402
import relational_dispatch_cases as RC                   # noqa: E402

FAIL = []


def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)


# ------------------------------------------------------- the frozen hand-reviewed set --

print("\nTHE FROZEN SET -- real plans, real ledgers, labels committed before the rule changed")
CASES = RC.load()
confusion = {}
for case, term, span, arch, ledger, human, expected in CASES:
    r = C.classify(term, span, arch, ledger)
    got = r["dispatch"]
    confusion[case] = (human, expected, got)
    ok(got == expected, "%-22s expected %-14s got %-14s  [%s]" % (case, expected, got, human))

print("\n  per-case detail")
for case, term, span, arch, ledger, human, expected in CASES:
    r = C.classify(term, span, arch, ledger)
    print("    %-22s E1=%s" % (case, r["E1"]))
    print("      %-20s %s" % ("", r["reason"][:150]))
    for w, c in sorted(r["candidates"].items()):
        print("        %-14s qualified=%-5s  %s" % (w, c["qualified"], c["why"][:110]))

# The one repaired case must still dispatch, AND for the stated reason -- two term-distinct,
# independently licensed, distinctive concepts -- not because one word happened to be rare.
bg = [c for c in CASES if c[0] == "bandgap->cutoff"][0]
r = C.classify(bg[1], bg[2], bg[3], bg[4])
ok(r["dispatch"] == C.RELATIONAL, "bandgap still dispatches RELATIONAL")
ok(set(r["E2"]) == {"bandgap"}, "bandgap E2 unchanged: %s" % r["E2"])
ok(set(r["E1"]) == {"cutoff", "wavelength"}, "bandgap E1 unchanged: %s" % r["E1"])
ok(sorted(r["qualified_endpoints"]) == ["bandgap", "energy"],
   "bandgap qualified on TWO independently licensed concepts, rarity only ranked them: %s"
   % r["qualified_endpoints"])
for w in ("bandgap", "energy"):
    c = r["candidates"][w]
    ok(bool(c["licensed_independently_of_the_term"]),
       "%s is licensed by a proposition that says nothing about the term (%s)"
       % (w, c["licensed_independently_of_the_term"]))

# The ISO regression, refused for a structural reason and not by name.
iso = [c for c in CASES if c[0] == "ISO attribution"][0]
r = C.classify(iso[1], iso[2], iso[3], iso[4])
ok(r["dispatch"] == C.NON_RELATIONAL, "ISO refuses")
ok("work" in r["candidates"], "ISO: 'work' was considered, not filtered out of sight")
ok(not r["candidates"]["work"]["named_in_declared_evidence"],
   "ISO: 'work' is not NAMED in the declared evidence -- it only sits inside 'working'")
ok(not r["candidates"]["work"]["distinctive"],
   "ISO: 'work' also fails the absolute bound at df_share %.3f"
   % r["candidates"]["work"]["df_share"])

# The second Dressing for Evacuation warning: three candidates, every one of them at df 1.
bel = [c for c in CASES if c[0] == "belongings"][0]
r = C.classify(bel[1], bel[2], bel[3], bel[4])
ok(r["dispatch"] == C.NON_RELATIONAL, "belongings refuses")
ok(max(c["df"] for w, c in r["candidates"].items() if "df" in c) <= 1,
   "belongings: no candidate is above df 1 -- as distinctive as bandgap -- so no "
   "distinctiveness floor, absolute or relative, could have caught this one")
ok(r["candidates"]["limited"]["distinctive"] and
   not r["candidates"]["limited"]["licensed_independently_of_the_term"],
   "belongings: 'limited' is distinctive and still refused -- its only licence is a "
   "proposition about the term itself")

# Compound normalisation, the 606db5a correction, still holds.
seat = [c for c in CASES if c[0] == "fixed seat"][0]
r = C.classify(seat[1], seat[2], seat[3], seat[4])
ok(r["candidates"]["seat"]["in_term"] is True,
   "transfer-to-seat: the term's own head noun is still recognised as part of the term")
ok(r["dispatch"] == C.NON_RELATIONAL, "fixed seat refuses")

# Clean definitions carry no flagged commitment, so nothing reaches the classifier and
# nothing can cost a call. Asserted by driving build_slice(), not by inspecting the table.
print("\n  clean definitions never reach the classifier")
import json  # noqa: E402
for run, term in RC.CLEAN_DEFINITIONS:
    arch = json.loads((RC.FIX / run / "ARCHITECTURE.json").read_text(encoding="utf-8"))
    ok(term in (arch.get("definitions") or {}), "%s defines %r" % (run, term))
    led = RC._ledger(RC.FIX / run / ("FINAL_EVIDENCE_MANIFEST.json"
                                     if run == "held-out-block-group" else "LEDGER.json"))
    gloss = arch["definitions"][term]
    shadow = {"definitions": [{"term": term, "claims": [
        {"commitment": gloss, "status": "SUPPORTED", "reason": ""}]}]}
    sl = C.build_slice(arch, led, shadow, term)
    ok(bool(sl.get("refusals")) and "defect_type" not in sl,
       "   %r: wholly supported, so build_slice stops before the classifier is reached"
       % term)
ok(not any(term in [c[1] for c in CASES] for _, term in RC.CLEAN_DEFINITIONS),
   "no clean definition appears in the dispatch set at all")

# The repair contract itself is not part of this change. Pinned so an edit to the prompt
# cannot ride along on a classifier commit -- reproducing G depends on it byte for byte.
import hashlib  # noqa: E402
ok(hashlib.sha256(C.SYSTEM.encode()).hexdigest()[:16] == "a31d665c592c15da",
   "the repair SYSTEM prompt is unchanged")
ok(hashlib.sha256(C.SCHEMA.encode()).hexdigest()[:16] == "c0d9ad5a4ae58885",
   "the repair reply SCHEMA is unchanged")


# ------------------------------------------------------------- the structural contract --

print("\nTHE STRUCTURE -- each property exercised on purpose")

# A ledger of realistic size. The bound is a SHARE, so a toy four-fact corpus would make
# every word in it 25% of the evidence and nothing could ever qualify; real ledgers in this
# corpus run 36 to 117 facts. Forty, with one distinctive concept and one pervasive one.
LED = {"F1": {"proposition": "The kiln reaches a peak temperature during the firing."},
       "F2": {"proposition": "A slipware dish is dipped in a coloured slip before firing."},
       "F3": {"proposition": "The pottery keeps a notebook of every load."}}
for _i in range(4, 41):
    # 'pottery' pervades the corpus the way 'detectors' pervades the Roman ledger
    LED["F%d" % _i] = {"proposition": ("The pottery opens to visitors on a weekday."
                                       if _i <= 14 else
                                       "A weekday tour crosses the yard and leaves.")}


def plan(term, gloss, ev):
    return {"definitions": {term: gloss}, "definition_evidence": {term: ev}}


def share(r, w):
    return r["candidates"][w]["df_share"]


# a single surviving candidate CAN dispatch -- when it is genuinely qualified
r = C.classify("slipware dish", "fired in the kiln",
               plan("slipware dish", "a dish fired in the kiln", ["F1"]), LED)
ok(r["dispatch"] == C.RELATIONAL and set(r["E2"]) == {"kiln"},
   "control: one qualified candidate does dispatch, so refusals below are not vacuous")

# ...but not merely by being the only one left
r = C.classify("slipware dish", "fired in the kilns",
               plan("slipware dish", "a dish fired in the kilns", ["F1"]), LED)
ok(r["dispatch"] == C.NON_RELATIONAL,
   "rarest-of-one: 'kilns' is the only candidate and still refuses -- the evidence names "
   "'kiln', not 'kilns', and being alone is not a qualification")

# an inflection is not the concept
r = C.classify("slipware dish", "which the potter fires",
               plan("slipware dish", "a dish which the potter fires", ["F1"]), LED)
ok(r["dispatch"] == C.NON_RELATIONAL
   and not r["candidates"]["fires"]["named_in_declared_evidence"],
   "a word occurring only inside a longer word ('fires' in 'firing') is not named")

# a common word cannot become an endpoint by surviving evidence overlap. F3 names 'pottery'
# and says nothing about the dish, so R2 and R3 both pass and only the bound is left.
r = C.classify("slipware dish", "kept by the pottery",
               plan("slipware dish", "a dish kept by the pottery", ["F3"]), LED)
ok(r["candidates"]["pottery"]["named_in_declared_evidence"] == ["F3"],
   "the common word IS named in the declared evidence")
ok(r["candidates"]["pottery"]["licensed_independently_of_the_term"] == ["F3"],
   "and IS licensed independently of the term, so only the absolute bound can stop it")
ok(not r["candidates"]["pottery"]["distinctive"],
   "absolute distinctiveness: df_share %.3f is over the %.3f bound"
   % (share(r, "pottery"), C.MAX_ENDPOINT_DF_SHARE))
ok(r["dispatch"] == C.AMBIGUOUS,
   "and it lands in AMBIGUOUS, not silently in NON_RELATIONAL: independently licensed but "
   "corpus-generic is a different thing from having no far end at all")
ok(set(r["E2"]) == set(), "AMBIGUOUS fails closed -- no endpoints, so no slice can be built")
ok(r["blocked_only_by_distinctiveness"] == ["pottery"],
   "and the report names what the bound alone rejected")

# two low-quality candidates do not add up to a relation
r = C.classify("slipware dish", "shown to visitors by the pottery",
               plan("slipware dish", "a dish shown to visitors by the pottery", ["F3"]), LED)
ok(r["dispatch"] != C.RELATIONAL,
   "two unqualified candidates do not make a relation between them")

# the term's own vocabulary, compound parts included, can never be the far end
r = C.classify("kiln-dish", "the kiln", plan("kiln-dish", "a kiln", ["F1"]), LED)
ok(r["dispatch"] == C.NON_RELATIONAL and r["candidates"]["kiln"]["in_term"],
   "a compound term's part cannot be its own second endpoint")
r = C.classify("", "the kiln", {"definitions": {"": "x"}, "definition_evidence": {"": ["F1"]}},
               LED)
ok(r["dispatch"] == C.NON_RELATIONAL,
   "a term with no vocabulary of its own has no near end, so there is no relation")

# R3: a candidate licensed only by a proposition about the term is a description, not an end.
# 'coloured' and 'slip' are both distinctive -- df 1 of 40 -- and both still refuse.
r = C.classify("slipware dish", "dipped in a coloured slip",
               plan("slipware dish", "a dish dipped in a coloured slip", ["F2"]), LED)
ok(r["dispatch"] == C.NON_RELATIONAL,
   "R3: every licence for 'coloured'/'slip' is a statement about the dish, so there is no "
   "concept standing apart from the term")
ok(all(c["distinctive"] for w, c in r["candidates"].items() if not c["in_term"]),
   "R3 and R4 are independent: those candidates pass the distinctiveness bound and are "
   "refused anyway")
ok(all(not c["licensed_independently_of_the_term"]
       for w, c in r["candidates"].items() if not c["in_term"]),
   "R3: and the report says so per candidate")

# no declared evidence at all
r = C.classify("slipware dish", "fired in the kiln",
               {"definitions": {"slipware dish": "x"}, "definition_evidence": {}}, LED)
ok(r["dispatch"] == C.NON_RELATIONAL, "no declared evidence -> refuse, not guess")

# the classifier is pure: same inputs, same answer, and it mutates nothing
import copy  # noqa: E402
a = plan("slipware dish", "a dish fired in the kiln", ["F1"])
before = copy.deepcopy((a, LED))
r1 = C.classify("slipware dish", "fired in the kiln", a, LED)
r2 = C.classify("slipware dish", "fired in the kiln", a, LED)
ok(r1 == r2, "classify is deterministic")
ok((a, LED) == before[0:2] if False else (a == before[0] and LED == before[1]),
   "classify mutates neither the architecture nor the ledger")

# endpoints() still answers in the old shape, and only for RELATIONAL
e1, e2 = C.endpoints(bg[1], bg[2], bg[3], bg[4])
ok(e1 == {"cutoff", "wavelength"} and e2 == {"bandgap"}, "endpoints() unchanged on bandgap")
e1, e2 = C.endpoints(iso[1], iso[2], iso[3], iso[4])
ok(e2 == set(), "endpoints() returns no far end for the ISO case")


# ------------------------------------------------------------------- confusion table --

print("\nCONFUSION TABLE over the frozen reviewed cases")
print("  %-22s %-42s %-15s %-15s %s" % ("case", "human type", "expected", "got", ""))
for case, (human, exp, got) in confusion.items():
    mark = "" if exp == got else "  <-- MISMATCH"
    note = " (newly reviewed)" if case in RC.NEWLY_REVIEWED else ""
    print("  %-22s %-42s %-15s %-15s%s%s" % (case, human, exp, got, mark, note))
n_rel = sum(1 for _, e, g in confusion.values() if e == C.RELATIONAL)
print("  %d relational expected, %d got; %d non-relational expected, %d got; %d ambiguous"
      % (n_rel, sum(1 for _, _, g in confusion.values() if g == C.RELATIONAL),
         sum(1 for _, e, _ in confusion.values() if e == C.NON_RELATIONAL),
         sum(1 for _, _, g in confusion.values() if g == C.NON_RELATIONAL),
         sum(1 for _, _, g in confusion.values() if g == C.AMBIGUOUS)))

print("\n%d FAILURES" % len(FAIL) if FAIL else "\nALL PASS")
for f in FAIL:
    print("   " + f)
sys.exit(1 if FAIL else 0)

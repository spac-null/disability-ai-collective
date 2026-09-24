"""Static tests for the positive-obligation channel.

The first and most important property is INERTNESS: with the flag unset, the rendered prompt
must be byte-identical to what it is today for every plan -- including one that carries the
new field, because a model reply could invent it.
"""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from new_engine_v1 import story as ST

FAIL = []
def ok(cond, label):
    print(("  PASS  " if cond else "  FAIL  ") + label)
    if not cond:
        FAIL.append(label)

FACTS = {"F86": "The precise mixture of HgCdTe, specifically the fraction of cadmium, can be "
                "varied to engineer a specific bandgap energy.",
         "F87": "For Roman's desired cutoff wavelength of approximately 2.5 microns, the "
                "fraction of cadmium was tuned to 0.445."}
ARCH = {
    "article_type": "NARRATIVE_ARTICLE", "story_spine": "a spine", "ending_move": "an end",
    "opening_object_or_event": "an opening", "reader_initial_state": "",
    "use_facts": ["F86", "F87"], "definitions": {"cutoff wavelength": "the long-wavelength edge"},
    "prohibitions": ["Do not state or imply that the bandgap energy sets the cutoff wavelength."],
    "beats": [{"beat_id": "B1", "happens": "something happens", "concrete_carrier": "a thing",
               "facts_allowed": ["F86", "F87"], "concept_introduced": "cutoff wavelength",
               "must_not_say_yet": ""}],
}
REQ = [
    {"id": "R1", "evidence": ["F86"],
     "must_realize": "the fraction of cadmium in the mixture can be varied to engineer a "
                     "specific bandgap energy"},
    {"id": "R2", "evidence": ["F87"],
     "must_realize": "for Roman's desired cutoff wavelength of approximately 2.5 microns the "
                     "fraction of cadmium was tuned to 0.445"},
]
WITH = dict(ARCH, required_commitments=REQ)


def render(arch, flag):
    if flag:
        os.environ[ST.REQUIRED_COMMITMENTS_FLAG] = "1"
    else:
        os.environ.pop(ST.REQUIRED_COMMITMENTS_FLAG, None)
    return ST.render(ST.build_packet(arch, {}, FACTS))


print("\n== inert unless switched on ==")
ok(ST.required_commitments_enabled({}) is False, "flag off with no env")
ok(ST.required_commitments_enabled({"CRIPMINDS_REQUIRED_COMMITMENTS": "1"}) is True, "flag on explicitly")
base_off = render(ARCH, False)
with_off = render(WITH, False)
ok(base_off == with_off,
   "flag OFF: a plan CARRYING the field renders byte-identically to one without it")
ok("THESE MUST REACH THE READER" not in with_off, "flag OFF: no obligation section appears")
base_on = render(ARCH, True)
ok(base_on == base_off,
   "flag ON but no field: prompt still byte-identical -- no production plan can change")

print("\n== on, with the field ==")
with_on = render(WITH, True)
ok("THESE MUST REACH THE READER" in with_on, "the obligation section appears")
ok("the fraction of cadmium in the mixture can be varied to engineer a specific bandgap energy"
   in with_on, "R1's text reaches the prompt")
ok("for Roman's desired cutoff wavelength" in with_on, "R2's text reaches the prompt")
ok("R1" not in with_on and "F86" not in with_on,
   "no machine language leaks: ids and fact numbers stay internal")
ok(with_on.index("THESE MUST REACH THE READER") > with_on.index("EXPLAIN AT FIRST USE"),
   "it sits beside the obligation that already exists, after EXPLAIN AT FIRST USE")
ok(with_on.index("THESE MUST REACH THE READER") < with_on.index("RULES"),
   "and before the negative RULES block")
ok("Do not state or imply that the bandgap energy sets" in with_on,
   "the prohibition still renders alongside it")

print("\n== the delta is additive only ==")
extra = [l for l in with_on.splitlines() if l not in base_off.splitlines()]
ok(all(("MUST REACH" in l) or l.strip().startswith("-") or "appear in the article" in l
        or "optional background" in l or l.strip() == "" for l in extra),
   "every added line belongs to the new section: %s" % len(extra))
ok(len(base_off.splitlines()) < len(with_on.splitlines()), "nothing was removed")

print("\n== malformed entries are skipped, not rendered raw ==")
junk = dict(ARCH, required_commitments=[{"id": "R9"}, {}, None, {"must_realize": "   "}])
j = render(junk, True)
ok("R9" not in j and "None" not in j, "entries without text contribute nothing")

os.environ.pop(ST.REQUIRED_COMMITMENTS_FLAG, None)
print("\n" + ("ALL PASS" if not FAIL else "FAILURES: %d\n  - %s" % (len(FAIL), "\n  - ".join(FAIL))))
sys.exit(1 if FAIL else 0)

"""Branch F: branch E, plus positive obligations. One field is the only delta.

E asked "can a packet-scoped prohibition stop the Writer rebuilding the relation?" -- yes, by
dropping the concept. F asks the harder question:

    can the Writer keep two separately licensed facts AND the explanation, while still not
    joining the two facts into the relation the evidence does not license?

The two required facts are deliberately listed next to each other. That adjacency is what
started this whole investigation -- beat B3 had them either side of a semicolon and the Writer
bridged them. Putting them back side by side, with the prohibition standing between them, is
the actual test rather than a friendlier version of it.

Usage: required_commitments_experiment.py <out_dir>
"""
import copy, hashlib, json, os, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from new_engine_v1 import story as ST                        # noqa: E402
from new_engine_v1 import composition as CP                  # noqa: E402

E = pathlib.Path("/srv/data/cripminds-repair-compiler-2026-09-24")
BE = E / "branch-E"
TERM = "cutoff wavelength"
EXPL = "the long-wavelength edge of what the detector material will register"

# Each must_realize is a plain restatement of ONE frozen fact, or of the explanation the
# definition already carries. None of them states a relation between the two facts -- that is
# the whole point, and a static check below asserts it.
REQUIRED = [
    {"id": "R1", "evidence": ["F86"],
     "must_realize": "the fraction of cadmium in the mercury cadmium telluride mixture can be "
                     "varied to engineer a specific bandgap energy"},
    {"id": "R2", "evidence": ["F87"],
     "must_realize": "for Roman's desired cutoff wavelength of approximately 2.5 microns, the "
                     "fraction of cadmium was tuned to 0.445"},
    {"id": "R3", "explanatory": True,
     "must_realize": "what a cutoff wavelength is: the long-wavelength edge of what the "
                     "detector material will register"},
]

BRIDGE_WORDS = ("sets", "determines", "controls", "produces", "fixes", "governs",
                "and with it", "which sets", "resulting", "thereby", "so that the cutoff")


def sha(x):
    return hashlib.sha256(x.encode("utf-8") if isinstance(x, str) else x).hexdigest()


def jsha(o):
    return sha(json.dumps(o, sort_keys=True, ensure_ascii=False))


def main(out_dir):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    base = json.loads((BE / "ARCHITECTURE.json").read_text())
    led = json.loads((BE / "LEDGER.json").read_text())
    if isinstance(led, dict) and "facts" in led:
        led = led["facts"]
    manifest = json.loads((BE / "FINAL_EVIDENCE_MANIFEST.json").read_text())["facts"]

    arch = copy.deepcopy(base)
    arch["required_commitments"] = REQUIRED

    fail = False
    checks = []

    def chk(name, cond, note=""):
        nonlocal fail
        checks.append({"check": name, "pass": bool(cond), "note": note})
        if not cond:
            fail = True
        print("  %s  %-56s %s" % ("PASS" if cond else "FAIL", name, note))

    print("STATIC CHECKS (branch E -> branch F)\n")
    a2, b2 = copy.deepcopy(arch), copy.deepcopy(base)
    a2.pop("required_commitments")
    chk("1 required_commitments is the ONLY delta from E",
        json.dumps(a2, sort_keys=True) == json.dumps(b2, sort_keys=True), "sha %s" % jsha(a2)[:16])
    chk("2 the branch-E prohibition is still present",
        any("bandgap energy sets, determines" in p for p in arch.get("prohibitions") or []),
        "%d prohibitions, unchanged" % len(arch["prohibitions"]))
    chk("3 definition gloss unchanged and bridge still absent",
        arch["definitions"][TERM] == base["definitions"][TERM]
        and "bandgap" not in arch["definitions"][TERM], "gloss sha %s" % sha(arch["definitions"][TERM])[:16])
    b3 = next(b for b in arch["beats"] if b["beat_id"] == "B3")
    b4 = next(b for b in arch["beats"] if b["beat_id"] == "B4")
    chk("4 B3 repaired form and F86 still at B4",
        "bandgap" not in b3["happens"] and "F86" in (b4.get("facts_allowed") or []), "")
    ids = set(manifest.keys())
    verrs = (ST.validate_architecture(arch, ids, led) + ST.validate_definition_support(arch, led)
             + ST.validate_evidence_hierarchy(arch, ids))
    chk("5 current Architecture validators pass", not verrs, str(verrs[:2]) if verrs else "CLEAN")
    # the obligations must not smuggle the relation in themselves
    joined = [r["id"] for r in REQUIRED
              if any(w in r["must_realize"].lower() for w in BRIDGE_WORDS)
              and "bandgap" in r["must_realize"].lower() and "cutoff" in r["must_realize"].lower()]
    chk("6 no required commitment asserts the forbidden relation", not joined, str(joined))
    chk("7 R1/R2 each restate exactly one frozen fact",
        "F86" in (REQUIRED[0]["evidence"]) and "F87" in (REQUIRED[1]["evidence"]), "")
    chk("8 R3 carries the explanation verbatim", EXPL in REQUIRED[2]["must_realize"], "")

    # render the packet offline, flag ON
    os.environ[ST.REQUIRED_COMMITMENTS_FLAG] = "1"
    packet, rendered = CP.writer_packet(arch, led)
    os.environ.pop(ST.REQUIRED_COMMITMENTS_FLAG, None)
    _, without = CP.writer_packet(base, led)

    chk("9 obligations reach the packet", "THESE MUST REACH THE READER" in rendered
        and all(r["must_realize"] in rendered for r in REQUIRED), "packet sha %s" % sha(rendered)[:16])
    chk("10 prohibition still in the packet alongside them",
        "Do not state or imply that the bandgap energy sets" in rendered, "")
    chk("11 no machine language leaks",
        not any(t in rendered for t in ("R1", "R2", "R3", "must_realize", "required_commitments")),
        "no ids, no field names")
    extra = [l for l in rendered.splitlines() if l not in without.splitlines()]
    chk("12 packet delta is additive only", len(extra) == len(REQUIRED) + 3,
        "%d new lines = heading + 2 framing + %d obligations" % (len(extra), len(REQUIRED)))

    (out / "ARCHITECTURE.json").write_text(json.dumps(arch, indent=2, ensure_ascii=False))
    (out / "WRITER_PACKET_FROZEN.txt").write_text(rendered)
    for f in ("RESEARCH_PACK.json", "FINAL_EVIDENCE_MANIFEST.json",
              "WORTH_AND_CANDIDATE.json", "LEDGER.json"):
        (out / f).write_text((BE / f).read_text())
    (out / "STATIC.json").write_text(json.dumps(
        {"required_commitments": REQUIRED, "e_architecture_sha256": jsha(base),
         "f_architecture_sha256": jsha(arch), "frozen_packet_sha256": sha(rendered),
         "checks": checks, "model_calls_this_step": 0}, indent=2, ensure_ascii=False))

    print("\nTHE NEW PACKET SECTION, as the Writer will see it:")
    keep = False
    for l in rendered.splitlines():
        if l.startswith("THESE MUST REACH THE READER"):
            keep = True
        elif keep and l.strip() == "" and not l.startswith(" "):
            break
        if keep:
            print("   %s" % l)
    print("\nfrozen packet sha256: %s" % sha(rendered))
    print("F architecture sha256: %s" % jsha(arch))
    print("\n%s" % ("STOP -- a static check failed" if fail else "ALL STATIC CHECKS PASS"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/branch-F"))
